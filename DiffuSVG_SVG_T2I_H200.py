# -*- coding: utf-8 -*-
"""
DiffuSVG_SVG_T2I_H200.py
=========================
H200 SXM5 (141 GB HBM3e) variant of DiffuSVG SVG-T2I v8.
Runs the full pipeline in pure BF16 — no quantization required.

  Component            v8 (T4, 16 GB)              H200 (141 GB)
  ─────────────────── ─────────────────────────    ───────────────────────────
  VFM encoder         DINOv2-small (384-d)          DINOv2-large (1024-d)
  VFM scales          3 × (224/448/896 px)           4 × (224/448/896/1344 px)
  CLIP scorer         ViT-B/32                       ViT-L/14-336
  SVG generator       OmniSVG 4B, NF4               OmniSVG 8B, BF16
  Rerank candidates   N=4                             N=16
  LoRA                r=8, α=32                       r=64, α=256
  Batch / accum       1 / 8                           4 / 2
  Max SVG tokens      1 200                           4 096
  Precision           NF4 + BF16 compute              Pure BF16
  Flash Attention 2   ✗                               ✓ (SDPA fallback)
  torch.compile       ✗                               ✓ (Inductor)
  Kaggle compat       many patches                    none

Usage:
  python DiffuSVG_SVG_T2I_H200.py --no-train     # eval only (fast demo)
  python DiffuSVG_SVG_T2I_H200.py --pairs data.json --stage 0  # all stages
  CUDA_VISIBLE_DEVICES=0,1,2,3 python DiffuSVG_SVG_T2I_H200.py  # multi-GPU
"""

import subprocess, sys, os, gc, json, logging, re, random, io, math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

# ── H200 environment ──────────────────────────────────────────────────────────
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
os.environ["TOKENIZERS_PARALLELISM"]   = "false"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True,max_split_size_mb:512"
os.environ["TRANSFORMERS_NO_TF"]      = "1"
os.environ["TRANSFORMERS_NO_FLAX"]    = "1"
os.environ["USE_TF"]                  = "0"
os.environ["USE_FLAX"]                = "0"
os.environ["TORCH_COMPILE_DISABLE"]   = "0"


# ─── Dependency bootstrap ──────────────────────────────────────────────────────
def _ensure_deps():
    """
    Install packages for a clean H200 environment.
    No Kaggle mixed-install hacks needed here.
    """
    pkgs = [
        "peft>=0.14.0",
        "accelerate>=0.34.0",
        "cairosvg",
        "open_clip_torch",
        "transformers>=4.47.0",
        "einops",
        "packaging",
        "sentencepiece",
        "scipy>=1.14",
        "wandb",
    ]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + pkgs)

    # Flash-Attn 2: pre-built wheels exist for H100/H200 (CUDA 12 + PyTorch ≥ 2.1)
    try:
        import flash_attn  # already installed
    except ImportError:
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-q",
                "flash-attn", "--no-build-isolation",
            ])
            print("[H200] flash-attn installed.")
        except Exception as exc:
            print(f"[H200] flash-attn install failed ({exc}); will use SDPA.")


_ensure_deps()

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from PIL import Image

if not torch.cuda.is_available():
    raise RuntimeError("No CUDA GPU found. This script targets H200/H100/A100-80G.")
if not torch.cuda.is_bf16_supported():
    raise RuntimeError("BF16 not supported on this GPU. H200/H100/A100 required.")

try:
    import flash_attn as _fa
    _FA2 = True
    _FA2_VERSION = _fa.__version__
except ImportError:
    _FA2 = False
    _FA2_VERSION = "n/a"

DEVICE = torch.device("cuda:0")
DTYPE  = torch.bfloat16

_ATTN_IMPL = "flash_attention_2" if _FA2 else "sdpa"

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DiffuSVG-H200")
log.info(f"GPU  : {torch.cuda.get_device_name(0)}")
log.info(f"VRAM : {torch.cuda.get_device_properties(0).total_memory / 1e9:.0f} GB")
log.info(f"Attn : {_ATTN_IMPL}  (flash-attn {_FA2_VERSION})")


# ─── Repo + directory setup ───────────────────────────────────────────────────
_SVG_DIFFUSION_REPO = "https://github.com/shiml20/SVG.git"
_OMNISVG_REPO       = "https://github.com/OmniSVG/OmniSVG.git"

try:
    _SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    _SCRIPT_DIR = Path.cwd()

WORKING_DIR  = str(_SCRIPT_DIR / "h200_run")
_OMNISVG_DIR = _SCRIPT_DIR / "OmniSVG"
_SVG_DIR     = _SCRIPT_DIR
os.makedirs(WORKING_DIR, exist_ok=True)


def _git_clone(repo: str, target: Path, label: str) -> bool:
    if target.exists() and any(target.iterdir()):
        log.info(f"[{label}] Already at {target}")
        return True
    log.info(f"[{label}] Cloning {repo} → {target} …")
    r = subprocess.run(["git", "clone", "--depth", "1", repo, str(target)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        log.error(f"[{label}] Clone failed:\n{r.stderr[-400:]}")
        return False
    log.info(f"[{label}] Done.")
    return True


def _pip_req(req_file: Path, label: str):
    if req_file.exists():
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file)])


def _setup_svg_diffusion() -> Path:
    if (_SCRIPT_DIR / "svg_t2i").exists() or (_SCRIPT_DIR / "train.py").exists():
        return _SCRIPT_DIR
    cached = Path(WORKING_DIR) / "shiml20_SVG"
    if cached.exists() and any(cached.iterdir()):
        return cached
    ok = _git_clone(_SVG_DIFFUSION_REPO, cached, "SVG-Diffusion")
    if not ok:
        log.warning("[SVG-Diffusion] Clone failed — reference generation disabled.")
    else:
        _pip_req(cached / "requirements.txt", "SVG-Diffusion")
    return cached


def _setup_omnisvg() -> Path:
    local = _SCRIPT_DIR / "OmniSVG"
    if (local / "inference.py").exists():
        return local
    cached = Path(WORKING_DIR) / "OmniSVG"
    if (cached / "inference.py").exists():
        return cached
    ok = _git_clone(_OMNISVG_REPO, cached, "OmniSVG")
    if not ok:
        raise RuntimeError("[OmniSVG] Clone failed.")
    _pip_req(cached / "requirements.txt", "OmniSVG")
    return cached


_SVG_DIR     = _setup_svg_diffusion()
_OMNISVG_DIR = _setup_omnisvg()
if str(_OMNISVG_DIR) not in sys.path:
    sys.path.insert(0, str(_OMNISVG_DIR))

if "HF_TOKEN" not in os.environ:
    log.warning("[Setup] HF_TOKEN not set — private model downloads may fail.")


# ════════════════════════════════════════════════════════════════════════════════
# SVG DIFFUSION BACKEND  (optional reference-image anchor)
# ════════════════════════════════════════════════════════════════════════════════

class SVGDiffusionBackend:
    _ENTRY_POINTS = [
        ("inference", "generate"), ("inference", "sample"),
        ("generate",  "generate"), ("sample",    "sample"),
        ("infer",     "infer"),    ("t2i",        "generate"),
    ]
    _DECODER_WEIGHT_PATHS = [
        "pretrained/vfm_decoder.pt", "checkpoints/vfm_decoder.pt",
        "vfm_decoder.pt", "pretrained/autoencoder_decoder.pt",
    ]

    def __init__(self, svg_dir: Path):
        self.svg_dir = svg_dir
        self._ready  = False
        self._generate_fn = None
        self._setup()

    def _setup(self):
        if not self.svg_dir.exists() or not any(self.svg_dir.iterdir()):
            return
        svg_str = str(self.svg_dir)
        if svg_str not in sys.path:
            sys.path.insert(0, svg_str)
        _prev = os.getcwd()
        try:
            os.chdir(svg_str)
            for mod, fn in self._ENTRY_POINTS:
                try:
                    m = __import__(mod)
                    f = getattr(m, fn, None)
                    if callable(f):
                        self._generate_fn = f
                        self._ready = True
                        break
                except (ImportError, AttributeError):
                    continue
        except Exception as e:
            log.warning(f"[SVGDiffusion] {e}")
        finally:
            os.chdir(_prev)

    @property
    def available(self) -> bool:
        return self._ready

    def generate(self, prompt: str, size: int = 1024) -> Optional[Image.Image]:
        if not self._ready:
            return None
        _prev = os.getcwd()
        try:
            os.chdir(str(self.svg_dir))
            result = self._generate_fn(prompt=prompt, size=size)
            if isinstance(result, Image.Image):
                return result.convert("RGB")
            if isinstance(result, (list, tuple)) and result:
                r = result[0]
                if isinstance(r, Image.Image):
                    return r.convert("RGB")
                if isinstance(r, np.ndarray):
                    return Image.fromarray(r).convert("RGB")
        except Exception as e:
            log.warning(f"[SVGDiffusion] generate failed: {e}")
        finally:
            os.chdir(_prev)
        return None

    def load_vfm_decoder_weights(self, decoder: nn.Module) -> bool:
        for rel in self._DECODER_WEIGHT_PATHS:
            p = self.svg_dir / rel
            if p.exists():
                try:
                    state = torch.load(str(p), map_location="cpu")
                    if isinstance(state, dict) and "state_dict" in state:
                        state = state["state_dict"]
                    decoder.load_state_dict(state, strict=False)
                    log.info(f"[SVGDiffusion] Decoder weights loaded from {p}")
                    return True
                except Exception as e:
                    log.warning(f"[SVGDiffusion] Weight load failed: {e}")
        return False


_svg_diffusion_backend = SVGDiffusionBackend(_SVG_DIR)


# ════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION  (H200 values)
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class VFMConfig:
    """
    H200 upgrade: DINOv2-large (1024-d) with 4-scale analysis.
    Paper proxy: DINOv3-s16p → we use DINOv2-large for stronger features.
    """
    encoder_model: str  = "facebook/dinov2-large"
    patch_size:    int  = 14                          # DINOv2 always 14×14
    latent_dim:    int  = 1024                        # large = 1024-d (vs small = 384)
    # 4-scale analysis: adds 1344px for a tighter high-res consistency check
    resolutions: Tuple = (224, 448, 896, 1344)
    frozen_encoder: bool = True
    # Decoder channels scaled up for 1024-d input (5 stages → 512px output)
    decoder_channels:      Tuple = (2048, 1024, 512, 256, 128)
    decoder_out_channels:  int   = 3
    # Quality thresholds (DINOv2-large produces higher baseline similarity)
    threshold_high:   float = 0.90
    threshold_medium: float = 0.72
    threshold_reject: float = 0.42


@dataclass
class TrainingConfig:
    """
    H200 training config: full BF16, LoRA r=64, larger batches.
    No quantization needed — 8B model fits comfortably in 141 GB.
    """
    lora_r:       int   = 64
    lora_alpha:   int   = 256
    lora_dropout: float = 0.05
    lora_target_modules: Tuple = (
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    )
    optimizer:        str   = "adamw_torch_fused"   # fused AdamW, fastest on H200
    base_lr:          float = 2e-4
    betas:            Tuple = (0.9, 0.95)
    weight_decay:     float = 0.01
    max_grad_norm:    float = 1.0
    batch_size:       int   = 4                     # 4× vs v8's 1
    grad_accum:       int   = 2                     # effective bs=8
    warmup_ratio:     float = 0.05
    compile_model:    bool  = True                  # torch.compile (Inductor)

    STAGES: Tuple = (
        (1, "Low Complexity",     500,   224,  2, 2e-4, 0.00),
        (2, "Medium Complexity", 2000,   448,  2, 1e-4, 0.30),
        (3, "High Resolution",   4000,   896,  2, 5e-5, 0.50),
        (4, "Aesthetic HQ",      4000,  1344,  1, 2e-5, 0.72),
    )
    max_text_len_early: int = 512
    max_text_len_late:  int = 1024


@dataclass
class GenerationConfig:
    """H200: 8B model, 16 candidates, 4096 tokens, full BF16."""
    model_size:    str   = "8B"
    n_candidates:  int   = 16                       # 4× vs v8's 4
    temperature_icon:          float = 0.4
    temperature_illustration:  float = 0.55
    top_p:              float = 0.92
    repetition_penalty: float = 1.03
    max_new_tokens:     int   = 4096                # 3.4× vs v8's 1200


@dataclass
class Config:
    vfm:        VFMConfig        = field(default_factory=VFMConfig)
    training:   TrainingConfig   = field(default_factory=TrainingConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)

    training_pairs_path: str  = ""
    output_dir:          str  = os.path.join(WORKING_DIR, "output_h200")
    max_svg_chars: int = 6000
    min_svg_chars: int = 50
    val_split:   float = 0.05


cfg = Config()
os.makedirs(cfg.output_dir, exist_ok=True)


# ════════════════════════════════════════════════════════════════════════════════
# SVG UTILITIES
# ════════════════════════════════════════════════════════════════════════════════

_SVG_SYSTEM = """\
You are an SVG code generator. Given a text description, output ONLY the SVG \
elements (rect, circle, ellipse, polygon, path, etc.) that would go inside:
<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">…</svg>

Rules:
- Output ONLY SVG elements, no <svg> wrapper, no comments, no explanation.
- Start with a background <rect width="200" height="200" fill="#RRGGBB"/>.
- Use solid hex fill colors only. No gradients, filters, or blur.
- Keep shapes simple: 3–30 elements. All coordinates in the 0–200 range.
- For icons: clean, minimal, single-concept. For illustrations: richer detail.
"""

_FEW_SHOT = [
    ("a blue circle on white",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="65" fill="#1565C0"/>'),
    ("a red heart",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="75" cy="85" r="30" fill="#E53935"/>\n'
     '<circle cx="125" cy="85" r="30" fill="#E53935"/>\n'
     '<polygon points="45,100 100,165 155,100" fill="#E53935"/>'),
    ("a green tree",
     '<rect width="200" height="200" fill="#E3F2FD"/>\n'
     '<polygon points="100,20 40,110 160,110" fill="#2E7D32"/>\n'
     '<polygon points="100,50 45,130 155,130" fill="#388E3C"/>\n'
     '<rect x="85" y="140" width="30" height="45" fill="#5D4037"/>'),
    ("a yellow star on dark blue",
     '<rect width="200" height="200" fill="#0D1B2A"/>\n'
     '<polygon points="100,20 112,60 155,60 122,83 133,125 100,100 67,125 '
     '78,83 45,60 88,60" fill="#FFD600"/>'),
    ("a purple butterfly",
     '<rect width="200" height="200" fill="#F8F0FF"/>\n'
     '<ellipse cx="70" cy="90" rx="50" ry="35" fill="#7B1FA2"/>\n'
     '<ellipse cx="130" cy="90" rx="50" ry="35" fill="#7B1FA2"/>\n'
     '<ellipse cx="70" cy="115" rx="30" ry="20" fill="#AB47BC"/>\n'
     '<ellipse cx="130" cy="115" rx="30" ry="20" fill="#AB47BC"/>\n'
     '<rect x="97" y="60" width="6" height="80" rx="3" fill="#4A148C"/>'),
]


def _few_shot_block(prompt: str, n: int = 3) -> str:
    examples = random.sample(_FEW_SHOT, min(n, len(_FEW_SHOT)))
    parts = [f"Prompt: {p}\nSVG:\n{svg}\n" for p, svg in examples]
    parts.append(f"Prompt: {prompt}\nSVG:")
    return "\n".join(parts)


def _wrap_svg(body: str, size: int = 200) -> str:
    return (f'<svg viewBox="0 0 {size} {size}" '
            f'xmlns="http://www.w3.org/2000/svg">\n{body}\n</svg>')


def _render_svg(svg_str: str, size: int = 224) -> Optional[Image.Image]:
    try:
        import cairosvg
        png = cairosvg.svg2png(bytestring=svg_str.encode(),
                               output_width=size, output_height=size)
        return Image.open(io.BytesIO(png)).convert("RGB")
    except Exception:
        return None


def _complexity(svg: str) -> str:
    n = len(re.findall(r"<(rect|circle|ellipse|polygon|polyline|line|path)\b", svg))
    return "simple" if n <= 3 else ("medium" if n <= 10 else "complex")


class _DINOImageProcessorLite:
    """
    Minimal DINOv2 pre-processing — avoids AutoImageProcessor lazy import.
    Callers are responsible for resizing to the target resolution first.
    """
    image_mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    image_std  = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)

    def __call__(self, images, return_tensors: str = "pt") -> Dict[str, torch.Tensor]:
        if isinstance(images, Image.Image):
            images = [images]
        tensors = []
        for img in images:
            arr    = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
            tensor = torch.from_numpy(arr).permute(2, 0, 1)
            tensor = (tensor - self.image_mean) / self.image_std
            tensors.append(tensor)
        return {"pixel_values": torch.stack(tensors)}


# ════════════════════════════════════════════════════════════════════════════════
# VFM ENCODER  (DINOv2-large + Flash-Attn 2 / SDPA)
# ════════════════════════════════════════════════════════════════════════════════

def _load_dinov2_model(model_id: str) -> nn.Module:
    """
    Load DINOv2 in BF16 with Flash-Attention 2 (or SDPA fallback).
    No Kaggle compat patches needed in a clean H200 environment.
    """
    from transformers import Dinov2Model
    model = Dinov2Model.from_pretrained(
        model_id,
        torch_dtype=DTYPE,
        attn_implementation=_ATTN_IMPL,
    )
    return model


class VFMEncoder(nn.Module):
    """
    Frozen DINOv2-large encoder in BF16.
    latent_dim=1024 (vs 384 for small).  Patch grid: 16×16 for 224px input.
    """
    def __init__(self, config: VFMConfig):
        super().__init__()
        self.processor = _DINOImageProcessorLite()
        self.backbone  = _load_dinov2_model(config.encoder_model)
        if config.frozen_encoder:
            for p in self.backbone.parameters():
                p.requires_grad_(False)
            self.backbone.eval()
        self.latent_dim = config.latent_dim
        self.patch_size = config.patch_size

    @torch.no_grad()
    def forward(self, images: List[Image.Image],
                resolution: int = 224) -> Tuple[torch.Tensor, torch.Tensor]:
        resized = [img.resize((resolution, resolution), Image.LANCZOS)
                   for img in images]
        inputs = self.processor(images=resized)
        device = next(self.backbone.parameters()).device
        pixel_values = inputs["pixel_values"].to(device, dtype=DTYPE)
        out    = self.backbone(pixel_values=pixel_values)
        tokens = out.last_hidden_state            # (B, 1+N_patches, D)
        return tokens[:, 0, :], tokens[:, 1:, :]


class VFMDecoder(nn.Module):
    """
    CNN decoder scaled up for DINOv2-large (1024-d input → 512×512 output).
    5 transpose-conv stages: 16×16 → … → 512×512.
    """
    def __init__(self, config: VFMConfig):
        super().__init__()
        in_ch, layers = config.latent_dim, []
        for out_ch in config.decoder_channels:
            layers += [
                nn.ConvTranspose2d(in_ch, out_ch, 4, 2, 1),
                nn.GroupNorm(min(32, out_ch // 4), out_ch),
                nn.GELU(),
            ]
            in_ch = out_ch
        layers += [nn.Conv2d(in_ch, config.decoder_out_channels, 3, 1, 1),
                   nn.Sigmoid()]
        self.net = nn.Sequential(*layers)

    def forward(self, patches: torch.Tensor) -> torch.Tensor:
        B, N, D = patches.shape
        h = w = int(math.sqrt(N))
        x = patches.reshape(B, h, w, D).permute(0, 3, 1, 2)
        return self.net(x)


class VFMAutoencoder(nn.Module):
    """Full autoencoder-P: frozen DINOv2-large + learned CNN decoder."""
    def __init__(self, config: VFMConfig):
        super().__init__()
        self.encoder = VFMEncoder(config)
        self.decoder = VFMDecoder(config)
        self.config  = config

    def to(self, device):
        self.encoder.backbone = self.encoder.backbone.to(device)
        self.decoder = self.decoder.to(device)
        return self

    def reconstruct(self, images: List[Image.Image],
                    resolution: int = 224) -> Tuple[torch.Tensor, torch.Tensor]:
        cls, patches = self.encoder(images, resolution)
        return self.decoder(patches), patches

    def reconstruction_loss(self, images: List[Image.Image],
                            resolution: int = 224) -> torch.Tensor:
        targets = torch.stack([
            torch.from_numpy(
                np.asarray(img.resize((resolution, resolution), Image.LANCZOS)
                           .convert("RGB"), dtype=np.float32) / 255.0
            ).permute(2, 0, 1)
            for img in images
        ]).to(next(self.decoder.parameters()).device, dtype=DTYPE)
        recon, _ = self.reconstruct(images, resolution)
        recon_r  = F.interpolate(recon, size=targets.shape[-2:],
                                 mode="bilinear", align_corners=False)
        return F.mse_loss(recon_r.float(), targets.float())

    def load_pretrained_decoder(self) -> bool:
        return _svg_diffusion_backend.load_vfm_decoder_weights(self.decoder)


# ════════════════════════════════════════════════════════════════════════════════
# MULTI-RESOLUTION VFM GATE  (4 scales, always on GPU)
# ════════════════════════════════════════════════════════════════════════════════

class MultiResolutionVFMGate:
    """
    4-scale DINOv2-large quality gate.
    Runs at 224/448/896/1344 px — the 4th scale uses Flash-Attn 2 (9216 patches)
    and is only meaningful with _FA2=True or large SDPA.
    """

    def __init__(self, config: VFMConfig):
        self.config  = config
        self._model  = None
        self._proc   = None
        self._device = DEVICE

    def _lazy_load(self):
        if self._model is not None:
            return
        log.info(f"[VFMGate] Loading {self.config.encoder_model} ({_ATTN_IMPL})…")
        self._proc  = _DINOImageProcessorLite()
        self._model = _load_dinov2_model(self.config.encoder_model).to(DEVICE).eval()
        if cfg.training.compile_model:
            self._model = torch.compile(self._model, mode="reduce-overhead")
            log.info("[VFMGate] Compiled with torch.compile.")
        log.info("[VFMGate] Ready.")

    @torch.no_grad()
    def _cls(self, img: Image.Image, res: int) -> torch.Tensor:
        self._lazy_load()
        img_r = img.resize((res, res), Image.LANCZOS)
        pv    = self._proc(images=img_r)["pixel_values"].to(DEVICE, dtype=DTYPE)
        feat  = self._model(pixel_values=pv).last_hidden_state[:, 0, :]
        return F.normalize(feat, dim=-1)

    def multi_resolution_scores(self, image: Image.Image) -> Dict[str, float]:
        feats    = {r: self._cls(image, r) for r in self.config.resolutions}
        res_list = list(self.config.resolutions)
        return {
            f"{res_list[i]}→{res_list[i+1]}":
                float((feats[res_list[i]] @ feats[res_list[i+1]].T).item())
            for i in range(len(res_list) - 1)
        }

    def score_svg(self, svg_str: str,
                  reference: Optional[Image.Image] = None) -> Dict[str, Any]:
        img = _render_svg(svg_str, size=max(self.config.resolutions))
        if img is None:
            return {"passed": False, "mean_consistency": 0.0,
                    "tier": "invalid", "error": "render_failed"}
        sims   = self.multi_resolution_scores(img)
        mean_c = float(np.mean(list(sims.values())))
        result: Dict[str, Any] = {
            "passed": mean_c >= self.config.threshold_reject,
            "mean_consistency": mean_c,
            "resolution_sims": sims,
            "tier": ("high"   if mean_c >= self.config.threshold_high   else
                     "medium" if mean_c >= self.config.threshold_medium else "low"),
        }
        if reference is not None:
            ref_feat = self._cls(reference, self.config.resolutions[-1])
            svg_feat = self._cls(img,       self.config.resolutions[-1])
            result["svg_ref_sim"] = float((svg_feat @ ref_feat.T).item())
        return result

    def unload(self):
        del self._model, self._proc
        self._model = self._proc = None
        gc.collect()
        torch.cuda.empty_cache()
        log.info("[VFMGate] Unloaded.")


# ════════════════════════════════════════════════════════════════════════════════
# FLOW MATCHING SCORER  (SVG-T2I Eq. 1–2)
# ════════════════════════════════════════════════════════════════════════════════

class FlowMatchingScorer:
    def __init__(self):
        self._ref_mean: Optional[torch.Tensor] = None
        self._fitted = False

    def fit(self, gate: MultiResolutionVFMGate,
            images: List[Image.Image], resolution: int = 224):
        log.info(f"[FlowScore] Fitting on {len(images)} images…")
        feats    = [gate._cls(img, resolution).cpu() for img in images]
        all_f    = torch.cat(feats, dim=0)
        self._ref_mean = all_f.mean(0)
        self._fitted   = True
        log.info("[FlowScore] Done.")

    def score(self, gate: MultiResolutionVFMGate,
              image: Image.Image, resolution: int = 224) -> float:
        if not self._fitted:
            return 0.5
        feat   = gate._cls(image, resolution).cpu()
        feat_n = F.normalize(feat, dim=-1)
        mean_n = F.normalize(self._ref_mean.unsqueeze(0), dim=-1)
        cos    = float(F.cosine_similarity(feat_n, mean_n).item())
        return float(torch.sigmoid(torch.tensor(cos * 10.0)).item())

    def score_svg(self, svg_str: str, gate: MultiResolutionVFMGate,
                  resolution: int = 224) -> float:
        img = _render_svg(svg_str, size=resolution)
        return 0.0 if img is None else self.score(gate, img, resolution)


# ════════════════════════════════════════════════════════════════════════════════
# PROGRESSIVE CURRICULUM  (4 stages, H200 thresholds)
# ════════════════════════════════════════════════════════════════════════════════

class SVGProgressiveCurriculum:
    STAGE_DEFS = [
        dict(id=1, name="Low Complexity",    min_c=50,  max_c=500,
             render=224,  epochs=2, lr=2e-4, vfm_min=0.00, max_text=512),
        dict(id=2, name="Medium Complexity", min_c=50,  max_c=2000,
             render=448,  epochs=2, lr=1e-4, vfm_min=0.30, max_text=512),
        dict(id=3, name="High Resolution",   min_c=50,  max_c=4000,
             render=896,  epochs=2, lr=5e-5, vfm_min=0.50, max_text=512),
        dict(id=4, name="Aesthetic HQ",      min_c=100, max_c=6000,
             render=1344, epochs=1, lr=2e-5, vfm_min=0.72, max_text=1024),
    ]

    def __init__(self, dataset: List[Dict]):
        self.dataset = dataset

    def get_stage_data(self, stage_id: int) -> List[Dict]:
        s   = self.STAGE_DEFS[stage_id - 1]
        out = []
        for item in self.dataset:
            svg = item.get("svg", "")
            if not (s["min_c"] <= len(svg) <= s["max_c"]):
                continue
            if item.get("vfm_consistency", 0.0) < s["vfm_min"]:
                continue
            if stage_id == 4 and item.get("clip_score", 0.0) * item.get("vfm_consistency", 0.0) < 15.0:
                continue
            out.append(item)
        out.sort(key=lambda x: len(x.get("svg", "")))
        return out

    def summary(self) -> str:
        lines = ["SVG Progressive Curriculum (H200 config):"]
        for s in self.STAGE_DEFS:
            n = len(self.get_stage_data(s["id"]))
            lines.append(
                f"  Stage {s['id']}: {s['name']:22s} | "
                f"chars {s['min_c']:4d}–{s['max_c']:4d} | "
                f"render {s['render']:4d}px | lr={s['lr']:.0e} | "
                f"vfm≥{s['vfm_min']:.2f} | {n:5d} samples"
            )
        return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════════
# DATASET
# ════════════════════════════════════════════════════════════════════════════════

class SVGCausalDataset(torch.utils.data.Dataset):
    def __init__(self, pairs: List[Dict], tokenizer, max_len: int = 1024):
        self.pairs = pairs
        self.tok   = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        item   = self.pairs[idx]
        few    = _few_shot_block(item["prompt"], n=3)
        text   = f"{_SVG_SYSTEM}\n\n{few}\n{item['svg']}"
        enc    = self.tok(text, truncation=True, max_length=self.max_len,
                          return_tensors="pt")
        ids    = enc["input_ids"][0]
        labels = ids.clone()
        p_enc  = self.tok(f"{_SVG_SYSTEM}\n\n{few}",
                          return_tensors="pt")["input_ids"][0]
        labels[:len(p_enc)] = -100
        return {"input_ids": ids, "labels": labels,
                "attention_mask": enc["attention_mask"][0]}


def collate_pad(batch, pad_id):
    max_len = max(b["input_ids"].size(0) for b in batch)
    for key in ("input_ids", "labels", "attention_mask"):
        for b in batch:
            t, pad = b[key], max_len - b[key].size(0)
            fill   = pad_id if key == "input_ids" else (-100 if key == "labels" else 0)
            b[key] = F.pad(t, (0, pad), value=fill)
    return {k: torch.stack([b[k] for b in batch]) for k in batch[0]}


# ════════════════════════════════════════════════════════════════════════════════
# VFM-GUIDED OMNISVG  (8B BF16, N=16, ViT-L/14-336 CLIP)
# ════════════════════════════════════════════════════════════════════════════════

class VFMGuidedOmniSVG:
    """
    N=16 candidate generation with OmniSVG 8B (BF16) + VFM×CLIP×flow reranking.
    CLIP scorer upgraded to ViT-L/14-336 for sharper text-image alignment.
    """

    def __init__(self, vfm_gate: MultiResolutionVFMGate,
                 flow_scorer: FlowMatchingScorer,
                 gen_cfg: GenerationConfig,
                 svg_diffusion: Optional[SVGDiffusionBackend] = None):
        self.vfm_gate     = vfm_gate
        self.flow_scorer  = flow_scorer
        self.gen_cfg      = gen_cfg
        self.svg_diffusion = svg_diffusion or _svg_diffusion_backend
        self._clip_model   = None
        self._omnisvg_loaded = False
        self._inf = None

    # ── CLIP ViT-L/14-336 ──────────────────────────────────────────────────────
    def _load_clip(self):
        if self._clip_model is not None:
            return
        from transformers import CLIPModel, CLIPProcessor
        model_id = "openai/clip-vit-large-patch14-336"
        log.info(f"[CLIP] Loading {model_id}…")
        self._clip_proc  = CLIPProcessor.from_pretrained(model_id)
        self._clip_model = CLIPModel.from_pretrained(
            model_id, torch_dtype=DTYPE
        ).to(DEVICE).eval()
        if cfg.training.compile_model:
            self._clip_model = torch.compile(self._clip_model, mode="reduce-overhead")
        log.info("[CLIP] Ready.")

    @torch.no_grad()
    def _clip_score(self, image: Image.Image, text: str) -> float:
        self._load_clip()
        inputs = self._clip_proc(text=[text], images=image,
                                 return_tensors="pt", padding=True)
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
        out    = self._clip_model(**inputs)
        img_f  = F.normalize(out.image_embeds, dim=-1)
        txt_f  = F.normalize(out.text_embeds,  dim=-1)
        return float((img_f @ txt_f.T).item() * 100)

    # ── OmniSVG 8B (BF16) load ────────────────────────────────────────────────
    def _load_omnisvg(self):
        if self._omnisvg_loaded:
            return
        if not _OMNISVG_DIR.exists():
            raise RuntimeError(f"OmniSVG directory not found: {_OMNISVG_DIR}")
        log.info(f"[OmniSVG] Loading 8B BF16 inference module…")
        _prev = os.getcwd()
        try:
            os.chdir(str(_OMNISVG_DIR))
            import inference as _inf_mod
            gc.collect()
            torch.cuda.empty_cache()
            # OmniSVG load_models: model_size controls which checkpoint is loaded.
            # 8B runs without quantization on H200.
            _inf_mod.load_models(self.gen_cfg.model_size)
            self._inf = _inf_mod
            self._omnisvg_loaded = True
            log.info("[OmniSVG] 8B model ready (BF16, no quantization).")
        except Exception as e:
            log.error(f"[OmniSVG] Load failed: {e}")
            raise
        finally:
            os.chdir(_prev)

    # ── Batch generation ───────────────────────────────────────────────────────
    def _generate_batch(self, prompt: str) -> List[str]:
        inf     = self._inf
        subtype = inf.detect_text_subtype(prompt)
        task_key = f"text-to-svg-{subtype}"
        tc      = inf.TASK_CONFIGS.get(task_key, {})
        _prev   = os.getcwd()
        try:
            os.chdir(str(_OMNISVG_DIR))
            inputs  = inf.prepare_inputs("text-to-svg", prompt)
            results = inf.generate_candidates(
                inputs=inputs,
                task_type="text-to-svg",
                subtype=subtype,
                temperature=tc.get("default_temperature",
                                   self.gen_cfg.temperature_icon),
                top_p=tc.get("default_top_p", self.gen_cfg.top_p),
                top_k=tc.get("default_top_k", 50),
                repetition_penalty=tc.get("default_repetition_penalty",
                                          self.gen_cfg.repetition_penalty),
                max_length=self.gen_cfg.max_new_tokens,
                num_samples=self.gen_cfg.n_candidates,
            )
        finally:
            os.chdir(_prev)
        return [r["svg"] for r in results if r.get("svg")]

    # ── Main generate + rerank ─────────────────────────────────────────────────
    def generate(self, prompt: str,
                 subtype: str = "auto") -> Tuple[Optional[str], Dict]:
        self._load_omnisvg()
        scored: List[Dict] = []

        ref_img: Optional[Image.Image] = None
        if self.svg_diffusion is not None and self.svg_diffusion.available:
            ref_img = self.svg_diffusion.generate(prompt, size=1024)

        try:
            candidates = self._generate_batch(prompt)
        except Exception as e:
            log.error(f"[Rerank] Batch generation failed: {e}")
            candidates = []

        candidates = [s for s in candidates if s and len(s) > cfg.min_svg_chars]
        if not candidates:
            log.warning(f"[Rerank] No valid candidates for: {prompt[:60]}")
            return None, {}

        for svg in candidates:
            render_img = _render_svg(svg, size=1344)
            if render_img is None:
                scored.append({"svg": svg, "combined": 0.0})
                continue
            vfm  = self.vfm_gate.score_svg(svg, reference=ref_img)
            clip = self._clip_score(render_img, prompt)
            flow = self.flow_scorer.score_svg(svg, self.vfm_gate, resolution=224)
            vfm_val  = vfm.get("mean_consistency", 0.0)
            ref_sim  = vfm.get("svg_ref_sim")
            if ref_sim is not None:
                ref_boost = (1.0 + ref_sim) / 2.0
                combined  = vfm_val * (clip / 100.0) * flow * ref_boost
            else:
                ref_boost = None
                combined  = vfm_val * (clip / 100.0) * flow
            entry: Dict[str, Any] = {
                "svg": svg, "vfm_consistency": vfm_val,
                "vfm_tier": vfm.get("tier", "low"),
                "resolution_sims": vfm.get("resolution_sims", {}),
                "clip_score": clip, "flow_score": flow, "combined": combined,
            }
            if ref_sim is not None:
                entry["svg_ref_sim"] = ref_sim
                entry["ref_boost"]   = ref_boost
            scored.append(entry)

        best = max(scored, key=lambda x: x["combined"])
        log.info(f"[Rerank] best combined={best['combined']:.4f}  "
                 f"vfm={best.get('vfm_consistency',0):.3f}  "
                 f"clip={best.get('clip_score',0):.1f}  "
                 f"flow={best.get('flow_score',0):.3f}  "
                 f"(N={len(scored)} candidates)")
        return best["svg"], {k: v for k, v in best.items() if k != "svg"}


# ════════════════════════════════════════════════════════════════════════════════
# DATASET LOADING + VFM SCORING
# ════════════════════════════════════════════════════════════════════════════════

def load_and_score_dataset(path: str, gate: MultiResolutionVFMGate,
                           flow_scorer: FlowMatchingScorer) -> List[Dict]:
    scored_path = os.path.join(cfg.output_dir, "scored_dataset.json")
    if os.path.exists(scored_path):
        log.info(f"[Dataset] Loading cached: {scored_path}")
        with open(scored_path) as f:
            return json.load(f)

    with open(path) as f:
        raw = json.load(f)
    log.info(f"[Dataset] {len(raw)} raw pairs.")

    keep, ref_images = [], []
    for i, item in enumerate(raw):
        svg = item.get("svg", "")
        if not (cfg.min_svg_chars <= len(svg) <= cfg.max_svg_chars):
            continue
        img = _render_svg(svg, size=448)
        if img is None:
            continue
        scores = gate.score_svg(svg)
        if not scores["passed"]:
            continue
        keep.append({**item, **scores, "complexity": _complexity(svg)})
        ref_images.append(img)
        if i % 200 == 0:
            log.info(f"[Dataset]  {i}/{len(raw)}, kept {len(keep)}")

    if ref_images:
        flow_scorer.fit(gate, ref_images[:min(1000, len(ref_images))], resolution=224)

    with open(scored_path, "w") as f:
        json.dump(keep, f, indent=2)
    log.info(f"[Dataset] {len(keep)} pairs kept → {scored_path}")
    return keep


# ════════════════════════════════════════════════════════════════════════════════
# LORA TRAINING  (BF16, LoRA r=64, fused AdamW, optional torch.compile)
# ════════════════════════════════════════════════════════════════════════════════

def train_stage(stage_def: Dict, dataset: List[Dict],
                model_name: str = "Qwen/Qwen2.5-VL-7B-Instruct",
                output_dir: Optional[str] = None) -> str:
    """
    Fine-tune OmniSVG 8B (Qwen2.5-VL-7B) in pure BF16 with LoRA r=64.
    No bitsandbytes quantization needed — 7B in BF16 uses ~14 GB VRAM,
    well within the H200's 141 GB budget.
    """
    from transformers import (AutoTokenizer, AutoModelForCausalLM,
                              TrainingArguments, Trainer)
    from peft import LoraConfig, get_peft_model

    tc       = cfg.training
    stage_id = stage_def["id"]
    stage_out = output_dir or os.path.join(cfg.output_dir, f"adapter_stage{stage_id}")
    os.makedirs(stage_out, exist_ok=True)

    log.info(f"\n{'='*64}")
    log.info(f"[Train] Stage {stage_id}: {stage_def['name']}")
    log.info(f"[Train] Samples={len(dataset)}  LR={stage_def['lr']:.0e}  "
             f"Render={stage_def['render']}px  Precision=BF16")

    if not dataset:
        log.warning(f"[Train] Stage {stage_id} has 0 samples — skipping.")
        return stage_out

    max_text_len = stage_def.get("max_text", 512)

    # ── Full BF16 (no quantization) ───────────────────────────────────────────
    log.info(f"[Train] Loading {model_name} (BF16, {_ATTN_IMPL})…")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=DTYPE,
        device_map="auto",
        attn_implementation=_ATTN_IMPL,
        trust_remote_code=True,
    )
    model.enable_input_require_grads()

    # ── LoRA r=64 ─────────────────────────────────────────────────────────────
    lora_cfg = LoraConfig(
        r=tc.lora_r,
        lora_alpha=tc.lora_alpha,
        lora_dropout=tc.lora_dropout,
        target_modules=list(tc.lora_target_modules),
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()

    if tc.compile_model:
        model = torch.compile(model, mode="reduce-overhead")
        log.info("[Train] Model compiled with torch.compile.")

    # ── Dataset ───────────────────────────────────────────────────────────────
    random.shuffle(dataset)
    n_val    = max(1, int(len(dataset) * cfg.val_split))
    train_ds = SVGCausalDataset(dataset[n_val:], tokenizer, max_len=max_text_len)
    val_ds   = SVGCausalDataset(dataset[:n_val], tokenizer, max_len=max_text_len)
    pad_id   = tokenizer.pad_token_id

    n_train       = max(1, len(train_ds))
    steps_per_ep  = math.ceil(n_train / (tc.batch_size * tc.grad_accum))
    total_steps   = steps_per_ep * stage_def["epochs"]

    # ── TrainingArguments (fused AdamW, BF16) ─────────────────────────────────
    train_args = TrainingArguments(
        output_dir=stage_out,
        num_train_epochs=stage_def["epochs"],
        per_device_train_batch_size=tc.batch_size,
        per_device_eval_batch_size=tc.batch_size,
        gradient_accumulation_steps=tc.grad_accum,
        learning_rate=stage_def["lr"],
        weight_decay=tc.weight_decay,
        max_grad_norm=tc.max_grad_norm,
        warmup_ratio=tc.warmup_ratio,
        bf16=True,
        bf16_full_eval=True,
        tf32=True,                                # A100/H100/H200 tensor core perf
        optim=tc.optimizer,
        logging_steps=max(1, total_steps // 20),
        save_steps=max(1, total_steps // 4),
        eval_strategy="steps",
        eval_steps=max(1, total_steps // 4),
        load_best_model_at_end=True,
        report_to="none",
        dataloader_num_workers=4,
        dataloader_pin_memory=True,
        remove_unused_columns=False,
        gradient_checkpointing=False,             # not needed; VRAM headroom is large
    )

    trainer = Trainer(
        model=model,
        args=train_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=lambda b: collate_pad(b, pad_id),
    )
    trainer.train()
    model.save_pretrained(stage_out)
    tokenizer.save_pretrained(stage_out)
    log.info(f"[Train] Stage {stage_id} adapter → {stage_out}")

    del model, trainer
    gc.collect()
    torch.cuda.empty_cache()
    return stage_out


# ════════════════════════════════════════════════════════════════════════════════
# EVALUATION  (GenEval-style, 1344px renders)
# ════════════════════════════════════════════════════════════════════════════════

EVAL_PROMPTS: Dict[str, List[str]] = {
    "single_obj": [
        "a red apple", "a blue star", "a green leaf",
        "a yellow sun", "a purple diamond", "a silver rocket",
    ],
    "two_obj": [
        "a cat next to a tree", "a moon above clouds",
        "a boat on water", "a bird on a branch", "a kite above a hill",
    ],
    "counting": [
        "three blue circles", "five red dots",
        "two yellow stars", "four green triangles",
    ],
    "colors": [
        "an orange pumpkin", "a pink flamingo",
        "a teal wave", "a crimson dragon",
    ],
    "position": [
        "a house with a chimney on top", "a fish below a boat",
        "a flag above a pole", "a cloud to the left of a sun",
    ],
    "color_attribution": [
        "a red car on a green road", "a blue bird with yellow wings",
        "a white cat on a black mat",
    ],
    "complex_scene": [
        "a beach sunset with palm trees and ocean waves",
        "a medieval castle on a hill under a full moon",
        "a futuristic cityscape with neon lights and flying cars",
    ],
}


def evaluate(pipeline: VFMGuidedOmniSVG,
             prompts: Optional[Dict[str, List[str]]] = None,
             output_dir: Optional[str] = None) -> Dict:
    prompts  = prompts or EVAL_PROMPTS
    out_dir  = output_dir or os.path.join(cfg.output_dir, "eval")
    os.makedirs(out_dir, exist_ok=True)

    all_results: List[Dict] = []
    cat_results: Dict[str, Dict] = {}

    for category, cat_prompts in prompts.items():
        cat_scores, cat_pass = [], 0
        for prompt in cat_prompts:
            svg, scores = pipeline.generate(prompt)
            if svg is None:
                all_results.append({"prompt": prompt, "category": category,
                                    "success": False})
                continue
            safe     = re.sub(r"[^\w]+", "_", prompt)[:50]
            svg_path = os.path.join(out_dir, f"{safe}.svg")
            png_path = os.path.join(out_dir, f"{safe}.png")
            with open(svg_path, "w") as f:
                f.write(svg)
            img = _render_svg(svg, size=1344)
            if img:
                img.save(png_path)
            passed = scores.get("clip_score", 0) >= 20.0
            cat_pass += int(passed)
            cat_scores.append(scores.get("clip_score", 0))
            all_results.append({"prompt": prompt, "category": category,
                                 "success": True, "passed": passed, **scores})
        n = len(cat_prompts)
        cat_results[category] = {
            "pass_rate": cat_pass / n if n else 0.0,
            "clip_mean": float(np.mean(cat_scores)) if cat_scores else 0.0,
            "n": n,
        }
        log.info(f"[Eval] {category:22s}  pass={cat_pass}/{n}  "
                 f"clip_mean={cat_results[category]['clip_mean']:.1f}")

    clips = [r.get("clip_score", 0) for r in all_results if r.get("success")]
    vfms  = [r.get("vfm_consistency", 0) for r in all_results if r.get("success")]
    flows = [r.get("flow_score", 0) for r in all_results if r.get("success")]
    n_ok  = sum(r.get("passed", False) for r in all_results)

    summary = {
        "n_total": len(all_results),
        "n_success": sum(r.get("success", False) for r in all_results),
        "n_passed": n_ok,
        "overall_pass_rate": n_ok / len(all_results) if all_results else 0.0,
        "clip_mean":     float(np.mean(clips)) if clips else 0.0,
        "clip_std":      float(np.std(clips))  if clips else 0.0,
        "vfm_mean":      float(np.mean(vfms))  if vfms  else 0.0,
        "flow_mean":     float(np.mean(flows)) if flows else 0.0,
        "combined_mean": float(np.mean([c / 100 * v * f
                                        for c, v, f in zip(clips, vfms, flows)]))
                         if clips else 0.0,
        "per_category": cat_results,
        "results": all_results,
    }
    with open(os.path.join(out_dir, "eval_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    log.info(f"\n[Eval] ══ H200 Summary ══")
    log.info(f"       Overall pass rate : {summary['overall_pass_rate']:.2%}")
    log.info(f"       CLIP mean (L/14)  : {summary['clip_mean']:.2f}")
    log.info(f"       VFM mean (large)  : {summary['vfm_mean']:.3f}")
    log.info(f"       Flow mean         : {summary['flow_mean']:.3f}")
    log.info(f"       Combined mean     : {summary['combined_mean']:.4f}")
    return summary


# ════════════════════════════════════════════════════════════════════════════════
# HTML GALLERY
# ════════════════════════════════════════════════════════════════════════════════

def build_gallery(eval_summary: Dict, out_dir: str) -> str:
    rows = []
    for cat, meta in eval_summary.get("per_category", {}).items():
        rows.append(
            f"<tr><td colspan='3'><b>{cat}</b>  "
            f"pass={meta['pass_rate']:.0%}  clip={meta['clip_mean']:.1f}</td></tr>"
        )
        cat_items = sorted(
            [r for r in eval_summary.get("results", [])
             if r.get("category") == cat and r.get("success")],
            key=lambda x: x.get("combined", 0), reverse=True,
        )
        for r in cat_items[:8]:
            safe = re.sub(r"[^\w]+", "_", r["prompt"])[:50]
            tick = "✔" if r.get("passed") else "✗"
            rows.append(
                f"<tr>"
                f"<td><img src='{safe}.png' width='200' height='200' "
                f"style='border:1px solid #555'></td>"
                f"<td style='font-size:12px'>{r['prompt'][:70]}</td>"
                f"<td style='font-size:11px'>"
                f"{tick} clip={r.get('clip_score',0):.1f}<br>"
                f"vfm={r.get('vfm_consistency',0):.3f}<br>"
                f"flow={r.get('flow_score',0):.3f}<br>"
                f"tier={r.get('vfm_tier','?')}"
                f"</td></tr>"
            )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>DiffuSVG H200</title>"
        "<style>body{font-family:sans-serif;background:#0d0d1a;color:#eee;padding:24px}"
        "h1{color:#80d8ff}table{border-collapse:collapse;width:100%}"
        "td{padding:8px;vertical-align:top;border-bottom:1px solid #2a2a3a}"
        ".m{background:#0d47a1;padding:5px 12px;border-radius:6px;"
        "display:inline-block;margin:3px;font-size:13px}"
        "</style></head><body>"
        "<h1>DiffuSVG H200 — SVG-T2I Adaptation</h1>"
        "<p>DINOv2-large · 4-scale VFM gate · OmniSVG 8B BF16 · "
        "ViT-L/14-336 CLIP · N=16 reranking</p><div>"
        f"<span class='m'>CLIP-L mean: {eval_summary.get('clip_mean',0):.2f}</span>"
        f"<span class='m'>VFM-large: {eval_summary.get('vfm_mean',0):.3f}</span>"
        f"<span class='m'>Flow: {eval_summary.get('flow_mean',0):.3f}</span>"
        f"<span class='m'>Pass: {eval_summary.get('overall_pass_rate',0):.1%}</span>"
        "</div><br><table>"
        + "".join(rows)
        + "</table></body></html>"
    )
    path = os.path.join(out_dir, "gallery.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    log.info(f"[Gallery] → {path}")
    return path


# ════════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ════════════════════════════════════════════════════════════════════════════════

def run(training_pairs_path: str = "",
        start_stage: int = 1,
        end_stage:   int = 4,
        skip_train:  bool = False):
    log.info("╔══════════════════════════════════════════════════════╗")
    log.info("║  DiffuSVG SVG-T2I — H200 Edition (BF16, 8B, N=16)   ║")
    log.info("╚══════════════════════════════════════════════════════╝")
    log.info(f"  Flash-Attn 2 : {_FA2}  ({_FA2_VERSION})")
    log.info(f"  torch.compile: {cfg.training.compile_model}")
    log.info(f"  CLIP model   : ViT-L/14-336")
    log.info(f"  VFM encoder  : DINOv2-large (1024-d, 4 scales)")
    log.info(f"  Generator    : OmniSVG {cfg.generation.model_size} BF16, N=16")

    if _svg_diffusion_backend.available:
        log.info(f"[Init] SVG-Diffusion backend READY → reference-guided reranking ON")
    else:
        log.info("[Init] SVG-Diffusion backend unavailable → VFM×CLIP×flow only")

    # ── VFM components ────────────────────────────────────────────────────────
    log.info("\n[Init] Building VFM components…")
    gate = MultiResolutionVFMGate(cfg.vfm)
    flow = FlowMatchingScorer()
    vfm_ae = VFMAutoencoder(cfg.vfm)
    if vfm_ae.load_pretrained_decoder():
        log.info("[Init] VFMAutoencoder decoder loaded from SVG-Diffusion weights.")
    else:
        log.info("[Init] VFMAutoencoder decoder randomly initialised.")

    # ── Dataset ───────────────────────────────────────────────────────────────
    pairs_path  = training_pairs_path or cfg.training_pairs_path
    scored_data: List[Dict] = []
    if pairs_path and os.path.exists(pairs_path):
        log.info(f"\n[Stage 0] Scoring dataset: {pairs_path}")
        scored_data = load_and_score_dataset(pairs_path, gate, flow)
    else:
        log.warning("[Stage 0] No training_pairs.json — skipping training.")

    curriculum = SVGProgressiveCurriculum(scored_data)
    log.info(f"\n{curriculum.summary()}")

    # ── Progressive LoRA training ─────────────────────────────────────────────
    last_adapter: Optional[str] = None
    if scored_data and not skip_train:
        for stage_def in SVGProgressiveCurriculum.STAGE_DEFS:
            sid = stage_def["id"]
            if sid < start_stage or sid > end_stage:
                continue
            stage_data = curriculum.get_stage_data(sid)
            log.info(f"\n[Train] Stage {sid} → {len(stage_data)} samples")
            last_adapter = train_stage(stage_def, stage_data)
        gate.unload()
        gc.collect()
        torch.cuda.empty_cache()

    try:
        gate.unload()
    except Exception:
        pass
    del vfm_ae
    gc.collect()
    torch.cuda.empty_cache()

    # ── Evaluation ────────────────────────────────────────────────────────────
    log.info("\n[Eval] Building pipeline…")
    gate2    = MultiResolutionVFMGate(cfg.vfm)
    pipeline = VFMGuidedOmniSVG(gate2, flow, cfg.generation,
                                 svg_diffusion=_svg_diffusion_backend)
    eval_out = os.path.join(cfg.output_dir, "eval")
    summary  = evaluate(pipeline, output_dir=eval_out)
    gallery  = build_gallery(summary, eval_out)

    log.info(f"\n[Done] Outputs  → {cfg.output_dir}")
    log.info(f"       Gallery → {gallery}")
    if last_adapter:
        log.info(f"       Adapter → {last_adapter}")
    return summary


# ════════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="DiffuSVG SVG-T2I H200")
    p.add_argument("--pairs",      default="",  help="Path to training_pairs.json")
    p.add_argument("--stage",      type=int, default=0,
                   help="Run only stage N (1-4).  0 = all stages.")
    p.add_argument("--no-train",   action="store_true",
                   help="Skip training; run evaluation only.")
    p.add_argument("--output",     default="",  help="Override output directory.")
    p.add_argument("--model-size", default="8B", choices=["4B", "8B"],
                   help="OmniSVG model size (default 8B).")
    p.add_argument("--no-compile", action="store_true",
                   help="Disable torch.compile (useful for debugging).")
    p.add_argument("--candidates", type=int, default=0,
                   help="Override N rerank candidates (0 = use config default).")
    args, _ = p.parse_known_args()

    if args.output:
        cfg.output_dir = args.output
        os.makedirs(cfg.output_dir, exist_ok=True)
    if args.model_size:
        cfg.generation.model_size = args.model_size
    if args.no_compile:
        cfg.training.compile_model = False
    if args.candidates > 0:
        cfg.generation.n_candidates = args.candidates

    s = args.stage
    run(
        training_pairs_path=args.pairs,
        start_stage=s if s > 0 else 1,
        end_stage=s   if s > 0 else 4,
        skip_train=args.no_train,
    )
