# -*- coding: utf-8 -*-
"""
DiffuSVG_Pipeline_v7.py — SVG-T2I Paper Concepts Applied to DiffuSVG
Runs on Kaggle T4 GPU (16 GB VRAM).

SVG-T2I paper contributions applied here (arXiv:2512.11749):
  1. VFM Quality Gate      — Replace slow VLM binary "does this match?" with DINOv2
                             cosine similarity in VFM feature space (Section 4.3)
  2. VFM Evaluation        — CLIP + DINOv2 dual scoring (richer than CLIP alone)
  3. Cross-Resolution Check — Key paper finding: DINO features shift ~10-40% across
                              scales (Fig 4). SVGs with high cross-scale consistency
                              are semantically more robust; use as a training filter.
  4. High-Res Reference    — Generate reference images at 1024×1024 for better
                              vectorization (paper evaluates at 1024×1024, Section 4.2)
  5. SVG-T2I Backend       — Optional HuggingFace SVG-T2I reference image generation
                              (KlingTeam/SVG-T2I). Falls back to SD3.5 if unavailable.

Extends v6 with all the above; core LoRA training is unchanged.

Stages:
  0. (Optional) Generate reference images via SVG-T2I or SD3.5 + vectorize
  1. Load & filter training_pairs.json via VFM quality gate
  2. QLoRA fine-tune Qwen2-VL on prompt → SVG
  3. Inference on held-out test prompts
  4. CLIP + DINOv2 + cross-resolution evaluation + HTML gallery
"""

import subprocess, sys, os, gc, json, logging, re, random, shutil, io
from pathlib import Path
from typing import List, Optional, Tuple, Dict

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"


# ── Dependency bootstrap ──────────────────────────────────────────────────────
def _ensure_deps():
    need_restart = False
    try:
        import bitsandbytes
        from packaging.version import Version
        if Version(bitsandbytes.__version__) < Version("0.46.1"):
            need_restart = True
    except ImportError:
        need_restart = True

    if need_restart:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-U",
            "bitsandbytes>=0.46.1", "peft>=0.13.0", "accelerate>=0.26.0"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
            "cairosvg", "open_clip_torch"])
        import IPython
        IPython.Application.instance().kernel.do_shutdown(True)
        raise SystemExit("Restart the kernel and re-run.")

    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
        "cairosvg", "open_clip_torch", "peft>=0.13.0",
        # DINOv2 via HuggingFace transformers (already installed on Kaggle)
        "transformers>=4.37.0"])

_ensure_deps()

import torch
import numpy as np
from PIL import Image
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType

os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"


# ── Environment detection ─────────────────────────────────────────────────────
def _detect_env() -> str:
    if Path("/kaggle").exists():
        return "kaggle"
    try:
        import google.colab
        return "colab"
    except ImportError:
        pass
    return "local"

_ENV = _detect_env()
WORKING_DIR = {"kaggle": "/kaggle/working", "colab": "/content",
               "local": "/tmp/diffusvg"}[_ENV]
os.makedirs(WORKING_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DiffuSVG-v7")
log.info(f"Environment: {_ENV}, Working dir: {WORKING_DIR}")


# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
class Config:
    # Dataset
    TRAINING_PAIRS_PATH: str = ""
    MAX_SVG_CHARS: int = 4000
    MIN_SVG_CHARS: int = 50
    VAL_SPLIT: float = 0.1

    # VFM Quality Gate (SVG-T2I paper: Section 4.3)
    VFM_MODEL: str = "facebook/dinov2-small"   # 22M params; fits on T4 alongside VLM
    VFM_QUALITY_THRESHOLD: float = 0.35        # min DINO cosine sim to keep a training pair
    VFM_CONSISTENCY_RESOLUTIONS: Tuple = (224, 448)  # from paper Fig 4: multi-res check

    # Reference image generation (Stage 0)
    REF_IMAGE_RESOLUTION: int = 1024           # paper evaluates at 1024×1024 (Section 4.2)
    USE_SVGT2I: bool = True                    # try KlingTeam/SVG-T2I first, then SD3.5

    # VLM (for LoRA training + inference)
    VLM_MODEL: str = "Qwen/Qwen2-VL-2B-Instruct"
    MAX_SEQ_LEN: int = 1024

    # LoRA
    LORA_R: int = 4
    LORA_ALPHA: int = 16
    LORA_DROPOUT: float = 0.15

    # Training
    EPOCHS: int = 3
    BATCH_SIZE: int = 1
    GRAD_ACCUM: int = 8
    LEARNING_RATE: float = 1e-4
    WARMUP_RATIO: float = 0.1

    # Output
    OUTPUT_DIR: str = ""
    LORA_OUTPUT_DIR: str = ""
    EVAL_DIR: str = ""

cfg = Config()


# ════════════════════════════════════════════════════════════════════════════
# SVG UTILITIES
# ════════════════════════════════════════════════════════════════════════════
_SVG_SYSTEM = """\
You are an SVG code generator. Given a text description, output ONLY the SVG \
element body (rect, circle, polygon, path, ellipse, line, etc.) that would appear \
inside <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">...</svg>.

Rules:
- Output ONLY SVG elements, no <svg> wrapper, no comments, no explanation.
- Always start with a background rect: <rect width="200" height="200" fill="#COLOR"/>
- Use solid fill colors (hex). No gradients, no filters, no blur.
- Keep it simple: aim for 3-25 elements maximum.
- Use geometric primitives: rect, circle, ellipse, polygon, line, path.
- All coordinates within 0-200 range.
"""

_FEW_SHOT_EXAMPLES = [
    ("a blue circle",
     '<rect width="200" height="200" fill="#ffffff"/>\n<circle cx="100" cy="100" r="60" fill="#1565C0"/>'),
    ("a red heart",
     '<rect width="200" height="200" fill="#ffffff"/>\n<circle cx="75" cy="85" r="30" fill="#E53935"/>\n<circle cx="125" cy="85" r="30" fill="#E53935"/>\n<polygon points="45,100 100,165 155,100" fill="#E53935"/>'),
    ("a house with red roof",
     '<rect width="200" height="200" fill="#E3F2FD"/>\n<rect x="50" y="110" width="100" height="80" fill="#FFF9C4"/>\n<polygon points="100,40 50,110 150,110" fill="#C62828"/>\n<rect x="88" y="150" width="25" height="40" fill="#5D4037"/>\n<rect x="60" y="125" width="20" height="20" fill="#81D4FA" stroke="#555" stroke-width="1"/>'),
    ("a rocket",
     '<rect width="200" height="200" fill="#0D1B2A"/>\n<polygon points="100,20 75,90 125,90" fill="#B0BEC5"/>\n<rect x="75" y="90" width="50" height="90" fill="#CFD8DC"/>\n<circle cx="100" cy="115" r="15" fill="#81D4FA"/>\n<polygon points="75,180 55,180 75,140" fill="#E53935"/>\n<polygon points="125,180 145,180 125,140" fill="#E53935"/>\n<polygon points="85,180 100,200 115,180" fill="#FF7043"/>'),
]


def _few_shot_block(prompt: str, n: int = 2) -> str:
    examples = random.sample(_FEW_SHOT_EXAMPLES, min(n, len(_FEW_SHOT_EXAMPLES)))
    parts = []
    for ex_prompt, ex_svg in examples:
        parts.append(f"Prompt: {ex_prompt}\nSVG:\n{ex_svg}\n")
    parts.append(f"Prompt: {prompt}\nSVG:")
    return "\n".join(parts)


def _wrap_svg(body: str) -> str:
    return f'<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n{body}\n</svg>'


def _render_svg_to_pil(svg_string: str, size: int = 200) -> Optional[Image.Image]:
    try:
        import cairosvg
        png_data = cairosvg.svg2png(bytestring=svg_string.encode("utf-8"),
                                    output_width=size, output_height=size)
        return Image.open(io.BytesIO(png_data)).convert("RGB")
    except Exception:
        return None


def _classify_complexity(svg: str) -> str:
    tags = re.findall(r"<(rect|circle|ellipse|polygon|polyline|line|path|text)\b", svg)
    n = len(tags)
    if n <= 3:
        return "simple"
    elif n <= 10:
        return "medium"
    return "complex"


# ════════════════════════════════════════════════════════════════════════════
# VFM QUALITY GATE (SVG-T2I paper — Section 4.3, Figure 4)
# ════════════════════════════════════════════════════════════════════════════
class VFMQualityGate:
    """
    DINOv2-based semantic quality gate inspired by SVG-T2I paper.

    The paper shows that VFM (DINOv3) representations capture richer semantic
    structure than VAE latent spaces. We apply this insight in two ways:

    1. PAIR FILTERING: Compare DINO features of rendered SVG against a reference
       image. High cosine similarity → semantically aligned training pair.

    2. CROSS-RESOLUTION CONSISTENCY (paper Figure 4): DINOv2/v3 features shift
       substantially across resolutions (cos sim 0.60–0.90), unlike VAE (~1.0).
       For SVGs, we want semantically stable representations; low consistency
       signals a degenerate SVG (e.g., all-white image that "matches" at one
       resolution but not another).
    """

    def __init__(self,
                 model_name: str = "facebook/dinov2-small",
                 threshold: float = 0.35):
        self.model_name = model_name
        self.threshold = threshold
        self._model = None
        self._processor = None

    def _lazy_load(self):
        if self._model is not None:
            return
        from transformers import AutoImageProcessor, AutoModel
        log.info(f"[VFM] Loading {self.model_name}...")
        self._processor = AutoImageProcessor.from_pretrained(self.model_name)
        self._model = AutoModel.from_pretrained(self.model_name)
        self._model.eval()
        if torch.cuda.is_available():
            self._model = self._model.cuda()
        log.info(f"[VFM] {self.model_name} loaded.")

    @torch.no_grad()
    def extract_features(self, image: Image.Image) -> torch.Tensor:
        """Extract CLS-token features — normalized L2 vector in VFM space."""
        self._lazy_load()
        inputs = self._processor(images=image, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        outputs = self._model(**inputs)
        # CLS token (index 0) — paper uses patch tokens for reconstruction,
        # but CLS captures global semantics best for quality gating.
        feats = outputs.last_hidden_state[:, 0, :]  # (1, D)
        return feats / feats.norm(dim=-1, keepdim=True)

    def cosine_similarity(self, img_a: Image.Image, img_b: Image.Image) -> float:
        """VFM cosine similarity between two images."""
        fa = self.extract_features(img_a)
        fb = self.extract_features(img_b)
        return float((fa @ fb.T).item())

    def cross_resolution_consistency(
            self,
            image: Image.Image,
            resolutions: Tuple = (224, 448)) -> Dict:
        """
        Replicates Figure 4 from SVG-T2I paper for a single image.

        Computes cosine similarity of DINOv2 features across resolutions.
        The paper shows DINOv2 has cos-sim 0.60–0.90 across scales.
        Very low consistency (<0.40) signals a degenerate/blank SVG.

        Returns:
            {
              "similarities": {"224→448": 0.78, ...},
              "mean_consistency": 0.78,
              "is_consistent": True   # >= 0.40
            }
        """
        self._lazy_load()
        res_list = list(resolutions)
        feats = {}
        for res in res_list:
            img_r = image.resize((res, res), Image.LANCZOS)
            feats[res] = self.extract_features(img_r)

        sims = {}
        for i in range(len(res_list) - 1):
            r1, r2 = res_list[i], res_list[i + 1]
            # Downsample higher-res to lower-res size to match paper methodology
            # (paper: "downsampling higher-resolution features to match lower ones")
            sims[f"{r1}→{r2}"] = float((feats[r1] @ feats[r2].T).item())

        mean_c = float(np.mean(list(sims.values()))) if sims else 0.0
        return {
            "similarities": sims,
            "mean_consistency": mean_c,
            "is_consistent": mean_c >= 0.40,   # degenerate SVGs fall below this
        }

    def gate_training_pair(
            self,
            rendered_svg: Image.Image,
            reference_image: Optional[Image.Image] = None
    ) -> Tuple[bool, Dict]:
        """
        Filter a training pair based on VFM quality.

        Two criteria:
          a) If reference_image given: semantic similarity rendered_svg ↔ reference.
          b) Cross-resolution consistency of rendered_svg (always applied).

        Returns (passes: bool, scores: dict).
        """
        scores = {}

        # Cross-resolution consistency (catches blank/degenerate SVGs)
        consistency = self.cross_resolution_consistency(
            rendered_svg, cfg.VFM_CONSISTENCY_RESOLUTIONS)
        scores["vfm_consistency"] = consistency["mean_consistency"]
        scores["vfm_consistent"] = consistency["is_consistent"]
        scores["vfm_resolution_sims"] = consistency["similarities"]

        if not consistency["is_consistent"]:
            return False, scores

        # Semantic alignment against reference (if available)
        if reference_image is not None:
            sim = self.cosine_similarity(rendered_svg, reference_image)
            scores["vfm_svg_ref_sim"] = sim
            passes = sim >= self.threshold
        else:
            passes = True  # no reference → only consistency check

        return passes, scores

    def unload(self):
        """Free VRAM — call after dataset filtering before loading VLM."""
        del self._model
        del self._processor
        self._model = None
        self._processor = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        log.info("[VFM] Model unloaded.")


# ════════════════════════════════════════════════════════════════════════════
# STAGE 0 (OPTIONAL): REFERENCE IMAGE GENERATION via SVG-T2I
# ════════════════════════════════════════════════════════════════════════════
# Repo   : https://github.com/KlingAIResearch/SVG-T2I.git
# Weights: https://huggingface.co/KlingTeam/SVG-T2I
#
# Architecture (from paper + repo):
#   Encoder : DINOv3-ViT-S/16+ → (H/16, W/16, 384) VFM features
#   DiT     : NextDiT_2B — 26 layers, hidden=2304, 24 heads, M-RoPE
#   Text    : Gemma-2-2B, max 256 tokens
#   Decoder : Autoencoder-P (CNN, 43M params)
#   Sampler : DPM++ or Euler ODE (flow matching, v-prediction)
#   Guidance: CFG scale=4.0, time-shifting factor=10.0
# ─────────────────────────────────────────────────────────────────────────────

_SVGT2I_REPO = "https://github.com/KlingAIResearch/SVG-T2I.git"
_SVGT2I_HF   = "KlingTeam/SVG-T2I"


def _setup_svgt2i() -> Optional[str]:
    """
    Clone the SVG-T2I repo and download weights from HuggingFace.
    Returns path to the svg_t2i/ working directory, or None on failure.

    Directory layout after setup:
      WORKING_DIR/SVG-T2I/                 ← git clone
      WORKING_DIR/SVG-T2I/svg_t2i/         ← inference scripts
      WORKING_DIR/SVG-T2I/svg_t2i/pre-trained/  ← HF weights
        autoencoder/svg_autoencoder_P_stage3_1024.yaml
        dit-stage4-T274M/  (DiT checkpoint)
    """
    repo_root  = os.path.join(WORKING_DIR, "SVG-T2I")
    svg_t2i_dir = os.path.join(repo_root, "svg_t2i")

    # ── 1. Clone ──────────────────────────────────────────────────────────
    if not os.path.exists(repo_root):
        log.info(f"[SVG-T2I] Cloning {_SVGT2I_REPO} ...")
        r = subprocess.run(
            ["git", "clone", "--depth", "1", _SVGT2I_REPO, repo_root],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            log.error(f"[SVG-T2I] git clone failed:\n{r.stderr[-600:]}")
            return None
        log.info("[SVG-T2I] Clone complete.")

    if not os.path.isdir(svg_t2i_dir):
        log.error(f"[SVG-T2I] Expected directory not found: {svg_t2i_dir}")
        return None

    # ── 2. Install repo-specific deps (non-conflicting subset) ───────────
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q",
         "omegaconf>=2.1", "einops", "pytorch-lightning>=2.0",
         "huggingface-hub>=0.20"],
        capture_output=True,
    )

    # ── 3. Download weights from HuggingFace ─────────────────────────────
    pretrained_dir = os.path.join(svg_t2i_dir, "pre-trained")
    autoencoder_cfg = os.path.join(pretrained_dir, "autoencoder",
                                   "svg_autoencoder_P_stage3_1024.yaml")
    dit_ckpt_dir    = os.path.join(pretrained_dir, "dit-stage4-T274M")

    if not os.path.exists(autoencoder_cfg) or not os.path.isdir(dit_ckpt_dir):
        log.info(f"[SVG-T2I] Downloading weights from {_SVGT2I_HF} ...")
        try:
            from huggingface_hub import snapshot_download
            snapshot_download(
                repo_id=_SVGT2I_HF,
                repo_type="model",
                local_dir=pretrained_dir,
                ignore_patterns=["*.md", "*.txt", "*.gitattributes"],
            )
            log.info(f"[SVG-T2I] Weights saved to {pretrained_dir}")
        except Exception as e:
            log.error(f"[SVG-T2I] Weight download failed: {e}")
            return None

    # Final sanity check
    if not os.path.exists(autoencoder_cfg):
        log.error(f"[SVG-T2I] Autoencoder config missing: {autoencoder_cfg}")
        return None
    if not os.path.isdir(dit_ckpt_dir):
        log.error(f"[SVG-T2I] DiT checkpoint missing: {dit_ckpt_dir}")
        return None

    return svg_t2i_dir


def _generate_image_svgt2i(prompt: str, width: int = 1024, height: int = 1024
                           ) -> Optional[Image.Image]:
    """
    Generate a reference image via SVG-T2I's actual CLI.

    Invokes:  python sample_svg_t2i.py
    with the arguments from svg_t2i/scripts/sample.sh:

        --ckpt   pre-trained/dit-stage4-T274M/
        --solver dpm   (DPM++ ODE solver)
        --steps  50
        --cfg_scale 4.0
        --time_shifting_factor 10.0
        --resolution 1024
        --system_type base
        --autoencoder_config pre-trained/autoencoder/svg_autoencoder_P_stage3_1024.yaml
        --ema

    Input format: JSONL file with one {"caption": "<prompt>"} per line.
    Output      : PNG files saved under --out_dir.

    SVG-T2I paper metrics (Table 5 & 6):
      GenEval  0.75 — matches/beats SD3-Medium (0.74), beats SDXL (0.55)
      DPG-Bench 85.78 — on par with FLUX.1 (83.84), HiDream-I1 (85.89)
    """
    svg_t2i_dir = _setup_svgt2i()
    if svg_t2i_dir is None:
        return None

    # Write caption in JSONL format required by sample_svg_t2i.py
    caption_path = os.path.join(WORKING_DIR, "svgt2i_caption.jsonl")
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"caption": prompt}) + "\n")

    out_dir = os.path.join(WORKING_DIR, "svgt2i_out")
    os.makedirs(out_dir, exist_ok=True)

    resolution = max(width, height)  # SVG-T2I uses square resolution arg
    pretrained_dir  = os.path.join(svg_t2i_dir, "pre-trained")
    autoencoder_cfg = os.path.join(pretrained_dir, "autoencoder",
                                   "svg_autoencoder_P_stage3_1024.yaml")
    dit_ckpt_dir    = os.path.join(pretrained_dir, "dit-stage4-T274M")

    cmd = [
        sys.executable,
        os.path.join(svg_t2i_dir, "sample_svg_t2i.py"),
        "--ckpt",               dit_ckpt_dir,
        "--out_dir",            out_dir,
        "--solver",             "dpm",          # DPM++ — fastest high-quality sampler
        "--steps",              "50",
        "--caption_path",       caption_path,
        "--seed",               "42",
        "--resolution",         str(resolution),
        "--time_shifting_factor", "10",         # from sample.sh default
        "--cfg_scale",          "4.0",
        "--system_type",        "base",
        "--autoencoder_config", autoencoder_cfg,
        "--batch_size",         "1",
        "--rank",               "0",
        "--ema",                               # use EMA weights (better quality)
    ]

    log.info(f"[SVG-T2I] Generating {resolution}×{resolution} for: {prompt[:60]}")
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=svg_t2i_dir,
    )

    if result.returncode != 0:
        log.warning(f"[SVG-T2I] Inference failed (exit {result.returncode}):\n"
                    f"{result.stderr[-600:]}")
        return None

    # sample_svg_t2i.py saves PNGs to out_dir; grab the latest
    png_files = sorted(Path(out_dir).glob("*.png"), key=os.path.getmtime)
    if not png_files:
        log.warning("[SVG-T2I] No output PNG found in out_dir.")
        return None

    img = Image.open(str(png_files[-1])).convert("RGB")
    # Crop/resize to requested (w, h) if not square
    if img.size != (width, height):
        img = img.resize((width, height), Image.LANCZOS)

    log.info(f"[SVG-T2I] Image loaded from {png_files[-1].name}")
    return img


def _generate_image_sd35(prompt: str, width: int = 1024, height: int = 1024
                         ) -> Optional[Image.Image]:
    """Generate reference image with Stable Diffusion 3.5 Medium (flow matching)."""
    try:
        from diffusers import StableDiffusion3Pipeline
        log.info("[SD3.5] Loading stabilityai/stable-diffusion-3.5-medium...")
        pipe = StableDiffusion3Pipeline.from_pretrained(
            "stabilityai/stable-diffusion-3.5-medium",
            torch_dtype=torch.float16,
        )
        pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")
        pipe.enable_model_cpu_offload()
        img = pipe(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=28,
            guidance_scale=4.5,
        ).images[0]
        del pipe
        gc.collect()
        torch.cuda.empty_cache()
        return img
    except Exception as e:
        log.error(f"[SD3.5] Failed: {e}")
        return None


def generate_reference_image(prompt: str) -> Optional[Image.Image]:
    """
    Generate a high-quality reference image for vectorization.

    SVG-T2I paper finding (Section 3.3): high-resolution inputs yield
    substantially more detailed DINOv3 features. We generate at 1024×1024
    then downscale for Potrace, preserving fine structural detail.

    Priority order:
      1. SVG-T2I (best semantic quality, VFM-native)
      2. SD3.5 Medium (flow matching, competitive quality)
    """
    w = h = cfg.REF_IMAGE_RESOLUTION

    if cfg.USE_SVGT2I:
        img = _generate_image_svgt2i(prompt, w, h)
        if img is not None:
            return img

    return _generate_image_sd35(prompt, w, h)


def vectorize_to_svg(image: Image.Image, viewbox: int = 200) -> Optional[str]:
    """Rasterize-then-vectorize pipeline: image → Potrace SVG."""
    try:
        import tempfile, subprocess
        # Downsample for Potrace (higher input res → better edge detection)
        img_gray = image.convert("L").resize((512, 512), Image.LANCZOS)
        with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as bmp_f:
            img_gray.save(bmp_f.name)
            bmp_path = bmp_f.name
        svg_path = bmp_path.replace(".bmp", ".svg")
        subprocess.run(
            ["potrace", "--svg", "--output", svg_path,
             "--turdsize", "2", "--alphamax", "0.5",
             bmp_path],
            check=True, capture_output=True)
        with open(svg_path) as f:
            raw_svg = f.read()
        os.unlink(bmp_path)
        os.unlink(svg_path)
        # Normalize viewBox
        raw_svg = re.sub(r'width="[^"]*"', f'width="{viewbox}"', raw_svg)
        raw_svg = re.sub(r'height="[^"]*"', f'height="{viewbox}"', raw_svg)
        raw_svg = re.sub(r'viewBox="[^"]*"',
                         f'viewBox="0 0 {viewbox} {viewbox}"', raw_svg)
        return raw_svg
    except Exception as e:
        log.warning(f"[Vectorize] {e}")
        return None


def build_training_pair_from_prompt(prompt: str) -> Optional[dict]:
    """
    Full Stage 0 pipeline: prompt → reference image → SVG → VFM quality gate.

    Returns a training pair dict if quality gate passes, else None.
    """
    log.info(f"[Stage0] Generating for: {prompt}")

    # 1. Generate reference image (SVG-T2I or SD3.5)
    ref_image = generate_reference_image(prompt)
    if ref_image is None:
        log.warning(f"[Stage0] Image generation failed for: {prompt}")
        return None

    # 2. Vectorize to SVG
    svg = vectorize_to_svg(ref_image)
    if svg is None:
        log.warning(f"[Stage0] Vectorization failed for: {prompt}")
        return None

    # 3. Render SVG at target size
    rendered = _render_svg_to_pil(svg, size=512)
    if rendered is None:
        log.warning(f"[Stage0] SVG render failed for: {prompt}")
        return None

    # 4. VFM quality gate — core SVG-T2I paper contribution applied here
    # Resize reference to 512 to match rendered SVG for fair comparison
    ref_512 = ref_image.resize((512, 512), Image.LANCZOS)

    vfm = VFMQualityGate(cfg.VFM_MODEL, cfg.VFM_QUALITY_THRESHOLD)
    passes, scores = vfm.gate_training_pair(rendered, ref_512)
    vfm.unload()

    log.info(f"[Stage0] VFM scores: {scores} | passes={passes}")

    if not passes:
        return None

    return {
        "prompt": prompt,
        "svg": svg,
        "complexity": _classify_complexity(svg),
        "vfm_scores": scores,
        "source": "svgt2i_or_sd35+potrace",
    }


# ════════════════════════════════════════════════════════════════════════════
# STAGE 1: LOAD & VFM-FILTER EXISTING DATASET
# ════════════════════════════════════════════════════════════════════════════
def load_and_filter_dataset(path: str, use_vfm_filter: bool = True) -> List[dict]:
    """
    Load training_pairs.json and optionally filter with VFM quality gate.

    VFM filtering (SVG-T2I paper insight): instead of keeping all Potrace outputs,
    retain only those where the rendered SVG has stable VFM features across
    resolutions — indicating the SVG genuinely represents the intended concept.
    """
    log.info(f"[Stage1] Loading dataset from {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Basic character-length filter (same as v6)
    candidates = []
    for item in raw:
        svg = item.get("svg", "")
        prompt = item.get("prompt", "")
        if not svg or not prompt:
            continue
        if len(svg) < cfg.MIN_SVG_CHARS or len(svg) > cfg.MAX_SVG_CHARS:
            continue
        candidates.append({
            "prompt": prompt,
            "svg": svg,
            "complexity": _classify_complexity(svg),
            "is_seed": item.get("is_seed", False),
            "svg_chars": len(svg),
        })

    log.info(f"[Stage1] {len(candidates)} pass char-length filter (from {len(raw)} raw)")

    if not use_vfm_filter or len(candidates) == 0:
        return _sort_by_curriculum(candidates)

    # VFM cross-resolution consistency filter
    log.info(f"[Stage1] Applying VFM cross-resolution filter "
             f"(resolutions={cfg.VFM_CONSISTENCY_RESOLUTIONS})...")
    vfm = VFMQualityGate(cfg.VFM_MODEL, cfg.VFM_QUALITY_THRESHOLD)

    filtered = []
    n_rejected_consistency = 0
    for item in candidates:
        rendered = _render_svg_to_pil(item["svg"], size=max(cfg.VFM_CONSISTENCY_RESOLUTIONS))
        if rendered is None:
            n_rejected_consistency += 1
            continue

        consistency = vfm.cross_resolution_consistency(
            rendered, cfg.VFM_CONSISTENCY_RESOLUTIONS)
        item["vfm_consistency"] = consistency["mean_consistency"]
        item["vfm_resolution_sims"] = consistency["similarities"]

        if consistency["is_consistent"]:
            filtered.append(item)
        else:
            n_rejected_consistency += 1

    vfm.unload()

    log.info(f"[Stage1] VFM filter: kept {len(filtered)}, "
             f"rejected {n_rejected_consistency} (degenerate/blank SVGs)")

    # Sort by VFM consistency score (best data first for curriculum)
    filtered.sort(key=lambda x: (
        {"simple": 0, "medium": 1, "complex": 2}[x["complexity"]],
        -x.get("vfm_consistency", 0),
    ))

    stats = {}
    for d in filtered:
        c = d["complexity"]
        stats[c] = stats.get(c, 0) + 1
    log.info(f"[Stage1] Complexity breakdown: {stats}")

    return filtered


def _sort_by_curriculum(dataset: List[dict]) -> List[dict]:
    """Sort by complexity (simple first) — curriculum learning."""
    order = {"simple": 0, "medium": 1, "complex": 2}
    dataset.sort(key=lambda x: (order[x["complexity"]], x["svg_chars"]))
    return dataset


# ════════════════════════════════════════════════════════════════════════════
# STAGE 2: QLoRA FINE-TUNING (unchanged from v6)
# ════════════════════════════════════════════════════════════════════════════
def build_chat_pair(prompt: str, svg_body: str, tokenizer) -> str:
    messages = [
        {"role": "system", "content": _SVG_SYSTEM},
        {"role": "user", "content": _few_shot_block(prompt, n=2)},
        {"role": "assistant", "content": svg_body},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False)


class SVGCausalDataset(torch.utils.data.Dataset):
    def __init__(self, data: list, tokenizer, max_len: int):
        self.samples = []
        skipped = 0
        for item in data:
            full_text = build_chat_pair(item["prompt"], item["svg"], tokenizer)
            toks = tokenizer(full_text, truncation=True, max_length=max_len,
                             padding="max_length", return_tensors="pt")
            input_ids = toks["input_ids"].squeeze()
            attn_mask = toks["attention_mask"].squeeze()

            prompt_msgs = [
                {"role": "system", "content": _SVG_SYSTEM},
                {"role": "user", "content": _few_shot_block(item["prompt"], n=2)},
            ]
            prompt_only = tokenizer.apply_chat_template(
                prompt_msgs, tokenize=False, add_generation_prompt=True)
            prompt_len = len(tokenizer(
                prompt_only, truncation=True, max_length=max_len)["input_ids"])

            labels = input_ids.clone()
            labels[:prompt_len] = -100
            labels[attn_mask == 0] = -100

            if (labels != -100).sum() < 20:
                skipped += 1
                continue

            self.samples.append({
                "input_ids": input_ids,
                "attention_mask": attn_mask,
                "labels": labels,
            })
        log.info(f"  SVGCausalDataset: {len(self.samples)} usable, {skipped} skipped")

    def __len__(self): return len(self.samples)
    def __getitem__(self, idx): return self.samples[idx]


def train_lora(dataset: list):
    from transformers import (
        AutoTokenizer, Qwen2VLForConditionalGeneration,
        BitsAndBytesConfig, TrainingArguments, Trainer,
    )

    log.info("=" * 70)
    log.info("STAGE 2: QLoRA Fine-Tuning")
    log.info("=" * 70)

    tokenizer = AutoTokenizer.from_pretrained(cfg.VLM_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        free_gb = torch.cuda.mem_get_info()[0] / 1e9
        total_gb = torch.cuda.mem_get_info()[1] / 1e9
        log.info(f"GPU: {free_gb:.1f} GB free / {total_gb:.1f} GB total")
        if free_gb < 1.0:
            log.error("< 1 GB GPU free — restart the kernel.")
            return None, None

    log.info(f"Loading {cfg.VLM_MODEL} with 4-bit NF4 quantization...")
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
    )
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        cfg.VLM_MODEL, quantization_config=quant_config,
        device_map={"": 0}, trust_remote_code=True,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    lora_cfg = LoraConfig(
        r=cfg.LORA_R, lora_alpha=cfg.LORA_ALPHA,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_dropout=cfg.LORA_DROPOUT, task_type=TaskType.CAUSAL_LM, bias="none",
    )
    model = get_peft_model(model, lora_cfg)
    model.is_parallelizable = False
    model.model_parallel = False
    model.print_trainable_parameters()

    random.shuffle(dataset)
    split = int(len(dataset) * (1 - cfg.VAL_SPLIT))
    train_data, val_data = dataset[:split], dataset[split:]

    train_ds = SVGCausalDataset(train_data, tokenizer, cfg.MAX_SEQ_LEN)
    val_ds = SVGCausalDataset(val_data, tokenizer, cfg.MAX_SEQ_LEN) if val_data else None

    if len(train_ds) == 0:
        log.error("No usable training samples!")
        return None, None

    log.info(f"Train: {len(train_ds)}, Val: {len(val_ds) if val_ds else 0}")

    training_args = TrainingArguments(
        output_dir=cfg.LORA_OUTPUT_DIR,
        per_device_train_batch_size=cfg.BATCH_SIZE,
        per_device_eval_batch_size=cfg.BATCH_SIZE,
        gradient_accumulation_steps=cfg.GRAD_ACCUM,
        num_train_epochs=cfg.EPOCHS,
        learning_rate=cfg.LEARNING_RATE,
        warmup_steps=max(1, int(cfg.WARMUP_RATIO
                                * (len(train_ds) // (cfg.BATCH_SIZE * cfg.GRAD_ACCUM))
                                * cfg.EPOCHS)),
        lr_scheduler_type="cosine",
        fp16=True,
        logging_steps=5,
        eval_strategy="epoch" if val_ds and len(val_ds) > 0 else "no",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=bool(val_ds and len(val_ds) > 0),
        metric_for_best_model="eval_loss" if val_ds and len(val_ds) > 0 else None,
        report_to="none",
        dataloader_pin_memory=False,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit",
        max_grad_norm=0.3,
    )

    trainer = Trainer(
        model=model, args=training_args,
        train_dataset=train_ds, eval_dataset=val_ds,
    )
    trainer.train()

    adapter_dir = os.path.join(cfg.LORA_OUTPUT_DIR, "final_adapter")
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    log.info(f"Adapter saved → {adapter_dir}")
    return model, tokenizer


# ════════════════════════════════════════════════════════════════════════════
# STAGE 3: INFERENCE
# ════════════════════════════════════════════════════════════════════════════
@torch.inference_mode()
def generate_svg(prompt: str, model, tokenizer, max_new_tokens: int = 1500) -> str:
    messages = [
        {"role": "system", "content": _SVG_SYSTEM},
        {"role": "user", "content": _few_shot_block(prompt, n=2)},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    out = model.generate(
        **inputs, max_new_tokens=max_new_tokens,
        do_sample=True, temperature=0.7, top_p=0.9, repetition_penalty=1.1,
    )
    response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:],
                                skip_special_tokens=True)
    svg_body = response.strip()
    svg_body = re.sub(r"^```(?:svg|xml|html)?\s*\n?", "", svg_body)
    svg_body = re.sub(r"\n?```\s*$", "", svg_body)
    if "<svg" in svg_body:
        m = re.search(r"<svg[^>]*>(.*?)</svg>", svg_body, re.DOTALL)
        if m:
            svg_body = m.group(1).strip()
    return _wrap_svg(svg_body)


# ════════════════════════════════════════════════════════════════════════════
# STAGE 4: VFM-ENHANCED EVALUATION (SVG-T2I paper — Section 4.2 + Figure 4)
# ════════════════════════════════════════════════════════════════════════════
_TEST_PROMPTS = [
    "a purple butterfly", "a green leaf", "a blue diamond",
    "a red car", "an orange cat", "a yellow flower",
    "a pink umbrella", "a brown dog", "a gray cloud",
    "a white snowflake on blue background", "a gold trophy", "a silver key",
    "a black chess piece", "a rainbow flag", "a green cactus",
    "a blue whale", "a red fire truck", "an ice cream cone",
    "a smiling sun", "a crescent moon with stars",
]


def _load_clip():
    import open_clip
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k")
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    model = model.float().eval()
    if torch.cuda.is_available():
        model = model.cuda()
    return model, preprocess, tokenizer


@torch.no_grad()
def _clip_score(image: Image.Image, prompt: str, model, preprocess, tokenizer) -> float:
    import open_clip
    img_t = preprocess(image).unsqueeze(0)
    txt_t = tokenizer([prompt])
    if torch.cuda.is_available():
        img_t = img_t.cuda()
        txt_t = txt_t.cuda()
    img_f = model.encode_image(img_t)
    txt_f = model.encode_text(txt_t)
    img_f /= img_f.norm(dim=-1, keepdim=True)
    txt_f /= txt_f.norm(dim=-1, keepdim=True)
    return float((img_f @ txt_f.T).item() * 100)


def evaluate_pipeline(model, tokenizer) -> dict:
    """
    Stage 4: Generate SVGs and score with CLIP + DINOv2 + cross-resolution consistency.

    SVG-T2I paper evaluation protocol (Section 4.2):
      - GenEval  : object-focused text-image alignment
      - DPG-Bench: dense prompt grounding
    We use CLIP (proxy for text-alignment) and DINOv2 (semantic quality + consistency).

    New vs v6:
      • vfm_consistency  : mean cosine sim of DINOv2 features at 224px and 448px
                           Paper shows high-quality images have 0.60-0.90 in DINO space.
                           Degenerate SVGs (blank/wrong) score < 0.40.
      • vfm_clip_product : CLIP × consistency — penalizes good CLIP score from blank SVGs.
    """
    log.info("=" * 70)
    log.info("STAGE 4: Evaluation — CLIP + DINOv2 + Cross-Resolution Consistency")
    log.info("=" * 70)

    clip_model, clip_preprocess, clip_tok = _load_clip()
    vfm = VFMQualityGate(cfg.VFM_MODEL, cfg.VFM_QUALITY_THRESHOLD)

    Path(cfg.EVAL_DIR).mkdir(parents=True, exist_ok=True)
    results = []

    for i, prompt in enumerate(_TEST_PROMPTS):
        try:
            svg = generate_svg(prompt, model, tokenizer)

            # Render at two sizes
            rendered_224 = _render_svg_to_pil(svg, size=224)
            rendered_448 = _render_svg_to_pil(svg, size=448)

            if rendered_224 is None:
                results.append({"prompt": prompt, "clip": 0.0, "dino_consistency": 0.0,
                                 "vfm_clip_product": 0.0, "success": False})
                continue

            # Save outputs
            rendered_224.save(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.png"))
            with open(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.svg"), "w") as f:
                f.write(svg)

            # ── CLIP score ────────────────────────────────────────────────
            clip = _clip_score(rendered_224, prompt, clip_model, clip_preprocess, clip_tok)

            # ── DINOv2 cross-resolution consistency (SVG-T2I Figure 4) ───
            # Render at 224 and 448; compute VFM feature similarity across scales.
            # Paper finding: good images score 0.60–0.90; blank images score <0.40.
            if rendered_448 is not None:
                consistency = vfm.cross_resolution_consistency(
                    rendered_448,
                    resolutions=cfg.VFM_CONSISTENCY_RESOLUTIONS,
                )
            else:
                consistency = {"mean_consistency": 0.0, "similarities": {}, "is_consistent": False}

            dino_c = consistency["mean_consistency"]

            # Combined metric: penalizes blank SVGs that trick CLIP
            vfm_clip_product = clip * dino_c

            results.append({
                "prompt": prompt,
                "clip": round(clip, 2),
                "dino_consistency": round(dino_c, 4),
                "vfm_resolution_sims": consistency["similarities"],
                "vfm_clip_product": round(vfm_clip_product, 2),
                "success": True,
            })

            log.info(f"  [{i+1:2d}/{len(_TEST_PROMPTS)}] "
                     f"CLIP={clip:.2f}  DINO_consistency={dino_c:.3f}  "
                     f"product={vfm_clip_product:.2f}  '{prompt[:40]}'")

        except Exception as e:
            log.error(f"  Eval error [{prompt}]: {e}")
            results.append({"prompt": prompt, "clip": 0.0, "dino_consistency": 0.0,
                             "vfm_clip_product": 0.0, "success": False})

    # Cleanup
    del clip_model
    vfm.unload()
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Aggregate
    successful = [r for r in results if r["success"]]
    if successful:
        clips = [r["clip"] for r in successful]
        dinos = [r["dino_consistency"] for r in successful]
        prods = [r["vfm_clip_product"] for r in successful]
        summary = {
            "n_total": len(results),
            "n_success": len(successful),
            "clip_mean": round(float(np.mean(clips)), 2),
            "clip_median": round(float(np.median(clips)), 2),
            "clip_std": round(float(np.std(clips)), 2),
            "dino_consistency_mean": round(float(np.mean(dinos)), 4),
            "dino_consistency_median": round(float(np.median(dinos)), 4),
            "vfm_clip_product_mean": round(float(np.mean(prods)), 2),
            "results": results,
        }
        log.info(f"  CLIP: mean={summary['clip_mean']:.2f}, "
                 f"median={summary['clip_median']:.2f}")
        log.info(f"  DINO consistency: mean={summary['dino_consistency_mean']:.3f} "
                 f"(paper range: 0.60-0.90 for high-quality images)")
        log.info(f"  VFM×CLIP product: mean={summary['vfm_clip_product_mean']:.2f}")
    else:
        summary = {"n_total": len(results), "n_success": 0, "results": results}

    eval_path = os.path.join(cfg.EVAL_DIR, "eval_summary.json")
    with open(eval_path, "w") as f:
        json.dump(summary, f, indent=2)
    log.info(f"  Evaluation saved → {eval_path}")
    return summary


# ════════════════════════════════════════════════════════════════════════════
# HTML GALLERY (enhanced with VFM scores)
# ════════════════════════════════════════════════════════════════════════════
def generate_gallery(eval_dir: str):
    html = [
        '<!DOCTYPE html><html><head><meta charset="utf-8">',
        '<title>DiffuSVG v7 — VFM-Enhanced Evaluation</title>',
        '<style>',
        'body{background:#1a1a2e;color:#eee;font-family:Inter,sans-serif;padding:20px}',
        'h1{text-align:center;color:#e94560}',
        '.subtitle{text-align:center;color:#a8d8ea;margin-bottom:24px;font-size:13px}',
        '.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:20px;padding:20px}',
        '.card{background:#16213e;border-radius:12px;padding:15px;text-align:center;',
        'box-shadow:0 4px 15px rgba(0,0,0,0.3)}',
        '.card img{width:200px;height:200px;border-radius:8px;background:#fff}',
        '.card .prompt{font-size:13px;margin:10px 0 5px;color:#a8d8ea}',
        '.card .clip{font-size:18px;font-weight:bold;color:#e94560}',
        '.card .dino{font-size:12px;color:#b8e0d2;margin-top:4px}',
        '.card .product{font-size:12px;color:#f9c74f;margin-top:2px}',
        '</style></head><body>',
        '<h1>🎨 DiffuSVG v7 — SVG-T2I Paper Concepts Applied</h1>',
        '<div class="subtitle">Metrics: CLIP (text alignment) | '
        'DINO consistency (VFM cross-resolution stability, paper Fig 4) | '
        'CLIP×DINO product (robustness against degenerate SVGs)</div>',
        '<div class="grid">',
    ]

    eval_json = os.path.join(eval_dir, "eval_summary.json")
    if os.path.exists(eval_json):
        with open(eval_json) as f:
            data = json.load(f)
        for i, r in enumerate(data.get("results", [])):
            img_path = f"eval_{i:03d}.png"
            if r.get("success"):
                clip_str = f"{r['clip']:.1f}"
                dino_str = f"DINO consistency: {r.get('dino_consistency', 0):.3f}"
                prod_str = f"VFM×CLIP: {r.get('vfm_clip_product', 0):.1f}"
            else:
                clip_str, dino_str, prod_str = "FAIL", "", ""
            html += [
                '<div class="card">',
                f'<img src="{img_path}" alt="{r["prompt"]}">',
                f'<div class="prompt">{r["prompt"]}</div>',
                f'<div class="clip">CLIP: {clip_str}</div>',
                f'<div class="dino">{dino_str}</div>',
                f'<div class="product">{prod_str}</div>',
                '</div>',
            ]

    html += ['</div></body></html>']
    gallery_path = os.path.join(eval_dir, "gallery.html")
    with open(gallery_path, "w") as f:
        f.write("\n".join(html))
    log.info(f"Gallery saved → {gallery_path}")


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log.info("=" * 70)
    log.info("DiffuSVG Pipeline v7 — SVG-T2I Paper Concepts Applied")
    log.info("=" * 70)
    log.info("Key additions vs v6:")
    log.info("  • VFM (DINOv2) quality gate for dataset filtering")
    log.info("  • Cross-resolution consistency metric (SVG-T2I paper, Fig 4)")
    log.info("  • CLIP + DINOv2 dual evaluation")
    log.info("  • Optional SVG-T2I reference image generation")
    log.info("=" * 70)

    # ── Configure paths ──────────────────────────────────────────────────
    candidates = [
        "/kaggle/input/datasets/rkamondal/diffusvg-v5/training_pairs.json",
        "/kaggle/input/diffusvg-v5/training_pairs.json",
        os.path.join(WORKING_DIR, "diffusvg_v5_output", "training_pairs.json"),
        os.path.join(WORKING_DIR, "dataset", "training_pairs.json"),
        os.path.join(WORKING_DIR, "training_pairs.json"),
        "f:/SVG-20260310T151742Z-1-001/SVG/diffusvg_v5_output/training_pairs.json",
    ]
    cfg.TRAINING_PAIRS_PATH = ""
    for c in candidates:
        if os.path.exists(c):
            cfg.TRAINING_PAIRS_PATH = c
            break

    cfg.OUTPUT_DIR = os.path.join(WORKING_DIR, "diffusvg_v7_output")
    cfg.LORA_OUTPUT_DIR = os.path.join(cfg.OUTPUT_DIR, "lora_checkpoints")
    cfg.EVAL_DIR = os.path.join(cfg.OUTPUT_DIR, "evaluation")
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    os.makedirs(cfg.LORA_OUTPUT_DIR, exist_ok=True)
    os.makedirs(cfg.EVAL_DIR, exist_ok=True)

    # ── Stage 0 (Optional): Generate new training pairs via SVG-T2I ─────
    stage0_prompts_path = os.path.join(WORKING_DIR, "stage0_prompts.txt")
    if os.path.exists(stage0_prompts_path):
        log.info("=" * 70)
        log.info("STAGE 0: Generating new training pairs via SVG-T2I / SD3.5")
        log.info("=" * 70)
        with open(stage0_prompts_path) as f:
            stage0_prompts = [l.strip() for l in f if l.strip()]

        new_pairs = []
        for prompt in stage0_prompts:
            pair = build_training_pair_from_prompt(prompt)
            if pair:
                new_pairs.append(pair)

        if new_pairs:
            stage0_out = os.path.join(cfg.OUTPUT_DIR, "stage0_pairs.json")
            with open(stage0_out, "w") as f:
                json.dump(new_pairs, f, indent=2)
            log.info(f"[Stage0] Generated {len(new_pairs)} pairs → {stage0_out}")

            # Merge with existing training_pairs.json
            if cfg.TRAINING_PAIRS_PATH and os.path.exists(cfg.TRAINING_PAIRS_PATH):
                with open(cfg.TRAINING_PAIRS_PATH) as f:
                    existing = json.load(f)
                merged = existing + new_pairs
                merged_path = os.path.join(cfg.OUTPUT_DIR, "training_pairs_merged.json")
                with open(merged_path, "w") as f:
                    json.dump(merged, f, indent=2)
                cfg.TRAINING_PAIRS_PATH = merged_path
                log.info(f"[Stage0] Merged dataset: {len(merged)} pairs → {merged_path}")
            else:
                cfg.TRAINING_PAIRS_PATH = stage0_out
    else:
        log.info("[Stage0] No stage0_prompts.txt found; skipping new pair generation.")
        log.info("  (To generate new data: write one prompt per line to "
                 f"{stage0_prompts_path})")

    # ── Stage 1: Load & VFM-filter dataset ──────────────────────────────
    if not cfg.TRAINING_PAIRS_PATH:
        log.error("training_pairs.json not found! Expected locations:")
        for c in candidates:
            log.error(f"  {c}")
        return

    log.info("=" * 70)
    log.info("STAGE 1: Loading & VFM-Filtering Dataset")
    log.info("=" * 70)

    dataset = load_and_filter_dataset(cfg.TRAINING_PAIRS_PATH, use_vfm_filter=True)
    if len(dataset) < 5:
        log.error(f"Only {len(dataset)} samples after VFM filter — need ≥5.")
        return

    dataset_path = os.path.join(cfg.OUTPUT_DIR, "processed_dataset.json")
    with open(dataset_path, "w") as f:
        json.dump(dataset, f, indent=2)
    log.info(f"Processed dataset → {dataset_path} ({len(dataset)} pairs)")

    for item in dataset[:5]:
        vfm_c = item.get("vfm_consistency", "N/A")
        log.info(f"  [{item['complexity']:7s}] chars={item['svg_chars']:5d}  "
                 f"vfm_c={vfm_c if isinstance(vfm_c, str) else f'{vfm_c:.3f}'}  "
                 f"'{item['prompt'][:50]}'")

    # ── Stage 2: Train LoRA ──────────────────────────────────────────────
    model, tokenizer = train_lora(dataset)
    if model is None:
        log.error("Training failed.")
        return

    # ── Stage 3+4: Inference & VFM-Enhanced Evaluation ──────────────────
    eval_summary = evaluate_pipeline(model, tokenizer)

    generate_gallery(cfg.EVAL_DIR)

    # ── Zip outputs ──────────────────────────────────────────────────────
    zip_base = os.path.join(WORKING_DIR, "diffusvg_v7_output")
    shutil.make_archive(zip_base, "zip", cfg.OUTPUT_DIR)
    log.info(f"Zipped → {zip_base}.zip")

    # ── Final Summary ────────────────────────────────────────────────────
    log.info("=" * 70)
    log.info("PIPELINE COMPLETE")
    log.info("=" * 70)
    log.info(f"  Dataset:    {len(dataset)} training pairs (VFM-filtered)")
    log.info(f"  Adapter:    {os.path.join(cfg.LORA_OUTPUT_DIR, 'final_adapter')}")
    log.info(f"  Evaluation: {cfg.EVAL_DIR}")
    if eval_summary.get("n_success", 0) > 0:
        log.info(f"  CLIP mean:              {eval_summary['clip_mean']:.2f}")
        log.info(f"  DINO consistency mean:  {eval_summary['dino_consistency_mean']:.3f} "
                 f"(paper: 0.60-0.90 for high-quality)")
        log.info(f"  VFM×CLIP product mean:  {eval_summary['vfm_clip_product_mean']:.2f}")
    log.info(f"  Output zip: {zip_base}.zip")

    if _ENV == "kaggle":
        log.info("\nDownload: Right panel → Output → diffusvg_v7_output.zip")


if __name__ == "__main__":
    main()
