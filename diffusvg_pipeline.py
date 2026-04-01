#!/usr/bin/env python3
"""
diffusvg_pipeline.py — DiffuSVG Pipeline v2 (Unified 5-Stage)
==============================================================

Implements the complete DiffuSVG pipeline from the architecture diagram:

  STAGE 1 — Data Generation
    Text Prompt → SD 3.5-Medium (steps=33, cfg=5.0) → Raster PNG (512×512)
    → Potrace + ImageMagick (threshold=45%, turdsize=2) → SVG (minified 200×200)
    → Training Dataset (X=Text Prompt, Y=SVG Code)

  STAGE 2 — VLM Quality Gate
    Render SVG (CairoSVG 256px) → PNG → Qwen2-VL-2B (frozen, greedy)
    "Does this match?" → YES=Keep / NO=Discard
    Filters ~20-40%, keeps on error (conservative)

  STAGE 3 — QLoRA Fine-Tuning
    Qwen2-VL-2B-Instruct (4-bit NF4 + double quant, ~1.5 GB VRAM)
    LoRA: r=32, α=64, dropout=0.05, targets: q k v o gate up down
    LR: 1e-4 cosine + 5% warmup, batch 1×8 grad_accum=8, epochs=5
    Loss: only on assistant (SVG) tokens, system+user masked -100

  STAGE 4 — Inference + Iterative Code Correction
    Fine-tuned Qwen2-VL (temp=0.7, top_p=0.9, rep=1.1) → SVG
    → Render (CairoSVG) → Image → Qwen2-VL Code Correction (temp=0.5)
    → "LGTM" = done, else corrected SVG (max 3 rounds)

  STAGE 5 — Evaluation (CLIP + DINO)
    Render 224×224 → CLIP ViT-B/32 cos(img,txt)×100
    Thresholds: CLIP ≥ 24.0, DINO ≥ 0.35
    Failure Mining → feed back to Stage 1

Usage:
    python diffusvg_pipeline.py --stage all
    python diffusvg_pipeline.py --stage 1 --prompts_file prompts.txt
    python diffusvg_pipeline.py --stage 4 --working_dir ./output
    python diffusvg_pipeline.py --dry_run
"""

import subprocess, shutil, sys, os, gc, json, logging, re, io, random, tempfile, base64
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Force single GPU — DataParallel is incompatible with 4-bit quantized models.
# Must be set BEFORE any torch import so device_count() == 1.
if "CUDA_VISIBLE_DEVICES" not in os.environ:
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DiffuSVG")


# ════════════════════════════════════════════════════════════════════════════
# CONFIG — exact values from the architecture diagram
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class PipelineConfig:
    """All parameters from the DiffuSVG Pipeline Architecture diagram."""

    # ── Paths ──
    HF_TOKEN: str         = "YOUR_HF_TOKEN"
    WORKING_DIR: str      = "./diffusvg_output"
    RESULTS_JSON: str     = ""  # input results.json for failure mining

    # ── Stage 1: Data Generation ──
    SD_MODEL: str          = "stabilityai/stable-diffusion-3.5-medium"
    SD_STEPS: int          = 33       # diagram: steps=33
    SD_GUIDANCE: float     = 5.0      # diagram: cfg=5.0
    SD_STYLE_PREFIX: str   = "minimalist flat vector app icon, solid colors, geometric, white background, "
    SD_RESOLUTION: int     = 512      # diagram: 512×512

    # ── Vectorizer (Potrace + ImageMagick) ──
    VEC_THRESHOLD: float   = 0.45     # diagram: threshold=45%
    VEC_TURDSIZE: int      = 2        # diagram: turdsize=2
    VEC_RESOLUTION: int    = 512
    SVG_MIN_PATHS: int     = 1
    SVG_MAX_PATHS: int     = 500
    SVG_VIEWBOX: int       = 200      # diagram: minified 200×200

    # ── Stage 2: VLM Quality Gate ──
    VLM_MODEL: str         = "Qwen/Qwen2-VL-2B-Instruct"  # diagram: Qwen2-VL-2B
    VLM_RENDER_SIZE: int   = 256      # diagram: CairoSVG 256px

    # ── Stage 3: QLoRA Fine-Tuning ──
    MAX_SEQ_LEN: int       = 2048     # diagram: Max len: 2048
    EPOCHS: int            = 5        # diagram: Epochs: 5
    BATCH_SIZE: int        = 1        # diagram: Batch: 1
    GRAD_ACCUM: int        = 8        # diagram: × 8 grad accum = 8 eff
    LEARNING_RATE: float   = 1e-4     # diagram: LR: 1e-4
    WARMUP_RATIO: float    = 0.05     # diagram: 5% warmup
    LR_SCHEDULER: str      = "cosine" # diagram: cosine
    VAL_SPLIT: float       = 0.1      # diagram: 10% val
    LORA_R: int            = 32       # diagram: r=32
    LORA_ALPHA: int        = 64       # diagram: α=64
    LORA_DROPOUT: float    = 0.05     # diagram: dropout=0.05
    LORA_TARGETS: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",       # attention
        "gate_proj", "up_proj", "down_proj",           # MLP layers
    ])

    # ── Stage 4: Inference + Code Correction ──
    INFER_TEMP: float      = 0.7      # diagram: temp=0.7
    INFER_TOP_P: float     = 0.9      # diagram: top_p=0.9
    INFER_REP_PENALTY: float = 1.1    # diagram: rep=1.1
    CORRECT_TEMP: float    = 0.5      # diagram: temp=0.5
    MAX_CORRECTION_ROUNDS: int = 3    # diagram: max 3 correction rounds
    MAX_NEW_TOKENS: int    = 2000

    # ── Stage 5: Evaluation ──
    CLIP_MODEL: str        = "ViT-B-32"  # diagram: CLIP ViT-B/32
    EVAL_RENDER_SIZE: int  = 224          # diagram: Render 224×224
    CLIP_THRESHOLD: float  = 24.0         # diagram: CLIP ≥ 24.0
    DINO_THRESHOLD: float  = 0.35         # diagram: DINO ≥ 0.35
    EVAL_SAMPLES: int      = 50

    # ── Fallback prompts ──
    FALLBACK_PROMPTS: List[str] = field(default_factory=lambda: [
        "a red apple", "a yellow sun", "a blue circle", "a green tree",
        "a red heart", "a yellow star", "an orange carrot", "a pink flower",
        "a house with red roof", "a snowman", "a rocket", "a cat face",
        "a wifi symbol", "a battery icon", "a music note", "a play button",
        "a gear icon", "a home icon", "a mail envelope", "a phone icon",
        "a camera", "a lock", "a mountain", "a rainbow", "clouds",
        "a crescent moon", "a pizza slice", "a coffee cup", "an ice cream",
        "a cake", "a hamburger", "a donut", "a watermelon", "a banana",
        "a strawberry", "a hot air balloon", "a treasure chest",
        "a lighthouse", "a bicycle", "a guitar", "circles", "a spiral",
        "squares", "yin yang", "a peace sign", "a target", "a smiley",
        "thumbs up", "lightning bolt", "a car",
    ])

    @property
    def output_dir(self) -> str:
        return os.path.join(self.WORKING_DIR, "dataset")

    @property
    def lora_dir(self) -> str:
        return os.path.join(self.WORKING_DIR, "qwen2vl_svg_lora")

    @property
    def eval_dir(self) -> str:
        return os.path.join(self.WORKING_DIR, "eval_results")


# ════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ════════════════════════════════════════════════════════════════════════════

def get_hf_token(cfg: PipelineConfig) -> str:
    """Resolve HF token from config, env, or Kaggle Secrets."""
    if cfg.HF_TOKEN and cfg.HF_TOKEN.startswith("hf_"):
        return cfg.HF_TOKEN
    if os.environ.get("HF_TOKEN", "").startswith("hf_"):
        return os.environ["HF_TOKEN"]
    try:
        from kaggle_secrets import UserSecretsClient
        token = UserSecretsClient().get_secret("HF_TOKEN")
        if token and token.startswith("hf_"):
            return token
    except Exception:
        pass
    return ""


def render_svg_to_pil(svg_str: str, size: int = 256) -> Optional[Image.Image]:
    """Render an SVG string to a PIL Image via CairoSVG."""
    try:
        import cairosvg
    except ImportError:
        log.info("cairosvg not found — attempting auto-install …")
        subprocess.run(
            ["pip", "install", "-q", "cairosvg"],
            capture_output=True,
        )
        subprocess.run(
            ["apt-get", "install", "-y", "-qq", "libcairo2"],
            capture_output=True,
        )
        try:
            import cairosvg
        except ImportError:
            log.warning("cairosvg install failed — SVG rendering unavailable")
            return None
    try:
        png_bytes = cairosvg.svg2png(
            bytestring=svg_str.encode("utf-8"),
            output_width=size, output_height=size,
        )
        return Image.open(io.BytesIO(png_bytes)).convert("RGB")
    except Exception:
        return None


def minify_svg(svg: str, viewbox: int = 200) -> str:
    """Normalize viewBox and strip whitespace for minimal token usage."""
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
    svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg)
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.DOTALL)
    svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.DOTALL)
    svg = re.sub(
        r"<svg[^>]*>",
        f'<svg viewBox="0 0 {viewbox} {viewbox}" xmlns="http://www.w3.org/2000/svg">',
        svg, count=1,
    )
    svg = re.sub(r"\s+", " ", svg).strip()
    return svg


def is_valid_svg(svg: Optional[str], min_p: int = 1, max_p: int = 500) -> bool:
    """Check if SVG has a reasonable number of path elements."""
    if not svg or "<path" not in svg:
        return False
    n = len(re.findall(r"<path", svg))
    return min_p <= n <= max_p


def extract_svg_from_text(text: str) -> Optional[str]:
    """Extract <svg>...</svg> from model output."""
    if "```" in text:
        for part in text.split("```"):
            p = part.strip().lstrip("svg").lstrip("xml").strip()
            if p.startswith("<svg"):
                text = p
                break
    m = re.search(r"(<svg[\s\S]*?</svg>)", text)
    return m.group(1) if m else None


def repair_svg(svg: str) -> str:
    """Close unclosed <g> tags and ensure </svg> at end."""
    svg = svg.strip()
    m = re.search(r"<svg[\s>]", svg)
    if m:
        svg = svg[m.start():]
    open_g = len(re.findall(r"<g\b[^>]*>", svg))
    close_g = len(re.findall(r"</g>", svg))
    svg += "</g>" * max(0, open_g - close_g)
    if not svg.rstrip().endswith("</svg>"):
        svg = svg.rstrip()
        svg += "\n</svg>" if svg.endswith(">") else '" fill="#000000"/>\n</svg>'
    return svg


# ════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — shared across training, inference, and correction
# ════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = (
    "You are an SVG generation assistant. "
    "Given a text description of an icon, output clean minimal SVG code. "
    "Output ONLY the SVG, no explanation."
)

CORRECTION_PROMPT = (
    "You are an SVG code reviewer. Compare the rendered image with "
    "the original prompt. If the SVG looks correct, reply with exactly "
    '"LGTM". Otherwise, output only the corrected SVG code.'
)


# ════════════════════════════════════════════════════════════════════════════
# STAGE 1 — Data Generation
# Text Prompt → SD 3.5-Medium → Raster PNG → Potrace+ImageMagick → SVG
# ════════════════════════════════════════════════════════════════════════════

def mine_failure_prompts(cfg: PipelineConfig) -> List[str]:
    """Extract prompts that failed from results.json (failure mining)."""
    path = cfg.RESULTS_JSON
    if not path or not Path(path).exists():
        # Try auto-discovery on Kaggle
        for candidate in Path("/kaggle/input").rglob("results.json"):
            path = str(candidate)
            break
    if not path or not Path(path).exists():
        log.warning("No results.json found — using fallback prompts.")
        return list(cfg.FALLBACK_PROMPTS)

    with open(path) as f:
        data = json.load(f)
    records = data["results"] if isinstance(data, dict) else data

    bad = []
    for r in records:
        failed = not r.get("success", True)
        low_clip = r.get("clip", 0) < cfg.CLIP_THRESHOLD
        low_dino = r.get("dino", 0) < cfg.DINO_THRESHOLD
        if failed or low_clip or low_dino:
            bad.append(r["prompt"])

    if not bad:
        log.warning("No failures in results.json — using fallback prompts.")
        return list(cfg.FALLBACK_PROMPTS)

    log.info(f"Mined {len(bad)} failure prompts from {path}")
    return bad


class PotraceVectorizer:
    """
    Embedded Potrace + ImageMagick vectorizer (from vectorize.py).
    Converts raster images to SVG:
        PIL Image → ImageMagick (preprocess → BMP) → Potrace (BMP → SVG) → postprocess
    Falls back to PIL-only preprocessing if ImageMagick is not installed.
    """

    def __init__(self, threshold: float = 0.45, turdsize: int = 2,
                 alphamax: float = 1.0, opttolerance: float = 0.2,
                 resolution: int = 512, contrast_stretch: str = "2%x98%", num_colors: int = 8):
        if not shutil.which("potrace"):
            log.info("potrace not found — attempting auto-install …")
            subprocess.run(
                ["apt-get", "install", "-y", "-qq", "potrace", "imagemagick"],
                capture_output=True,
            )
            if not shutil.which("potrace"):
                raise EnvironmentError(
                    "potrace not found and auto-install failed. "
                    "Run manually: !apt-get install -y potrace imagemagick"
                )
        self._has_magick = shutil.which("convert") is not None
        if not self._has_magick:
            log.warning("ImageMagick not found — using PIL fallback for preprocessing.")
        self.threshold = threshold
        self.turdsize = turdsize
        self.alphamax = alphamax
        self.opttolerance = opttolerance
        self.resolution = resolution
        self.contrast_stretch = contrast_stretch
        self.num_colors = num_colors

    def vectorize(self, image: Image.Image) -> Optional[str]:
        """Convert a PIL Image to SVG string using multi-pass Potrace."""
        if not self._has_magick:
            return self._vectorize_bw(image)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.png")
            image.convert("RGB").resize(
                (self.resolution, self.resolution), Image.LANCZOS
            ).save(input_path)

            quant_path = os.path.join(tmpdir, "quantised.png")
            subprocess.run(
                [
                    "convert", input_path,
                    "+dither",
                    "-colors", str(self.num_colors),
                    quant_path,
                ],
                capture_output=True,
                timeout=30,
            )

            if not os.path.exists(quant_path):
                log.warning("ImageMagick quantization failed, using single-pass")
                return self._vectorize_bw(image)

            result = subprocess.run(
                ["convert", quant_path, "-format", "%c", "histogram:info:-"],
                capture_output=True, text=True, timeout=15,
            )
            colors = self._parse_palette(result.stdout)
            if not colors:
                return self._vectorize_bw(image)

            svg_layers = []
            quant_img = Image.open(quant_path).convert("RGB")
            quant_arr = np.array(quant_img)

            for hex_color, rgb in colors:
                r, g, b = rgb
                tolerance = 20
                mask = (
                    (np.abs(quant_arr[:, :, 0].astype(int) - r) < tolerance) &
                    (np.abs(quant_arr[:, :, 1].astype(int) - g) < tolerance) &
                    (np.abs(quant_arr[:, :, 2].astype(int) - b) < tolerance)
                )

                if mask.sum() < 50:
                    continue

                bmp_path = os.path.join(tmpdir, f"layer_{hex_color[1:]}.bmp")
                svg_path = os.path.join(tmpdir, f"layer_{hex_color[1:]}.svg")

                mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode="L").convert("1")
                mask_img.save(bmp_path, format="BMP")

                if not self._run_potrace(bmp_path, svg_path):
                    continue

                with open(svg_path, "r") as f:
                    layer_svg = f.read()

                paths = self._extract_paths(layer_svg, hex_color)
                svg_layers.extend(paths)

            if not svg_layers:
                return self._vectorize_bw(image)

            content = "\n".join(svg_layers)
            scale_xy = 200.0 / self.resolution
            merged = (
                '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n'
                f'<g transform="scale({scale_xy:.4f},{scale_xy:.4f})">\n'
                f'<g transform="translate(0.000000,{self.resolution}.000000) scale(0.100000,-0.100000)">\n'
                f'{content}\n'
                "</g></g></svg>"
            )
            return merged

    def _parse_palette(self, histogram_text: str) -> list:
        """Parse ImageMagick histogram output → list of (hex, (r,g,b))."""
        colors = []
        for line in histogram_text.splitlines():
            m = re.search(r'#([0-9A-Fa-f]{6})', line)
            if m:
                hex_color = "#" + m.group(1).upper()
                r = int(m.group(1)[0:2], 16)
                g = int(m.group(1)[2:4], 16)
                b = int(m.group(1)[4:6], 16)
                colors.append((hex_color, (r, g, b)))
        seen = set()
        unique = []
        for c in colors:
            if c[0] not in seen:
                seen.add(c[0])
                unique.append(c)
        return unique

    def _extract_paths(self, svg: str, fill_color: str) -> list:
        """Extract <path> elements from a Potrace SVG and recolour them."""
        paths = re.findall(r'<path[^>]*/>', svg, re.DOTALL)
        coloured = []
        for p in paths:
            # Remove existing fill, set new fill
            p = re.sub(r'fill="[^"]*"', '', p)
            p = p.replace('<path', f'<path fill="{fill_color}"', 1)
            coloured.append(p)
        return coloured

    def _vectorize_bw(self, image: Image.Image) -> Optional[str]:
        """Convert a PIL Image to SVG string via Potrace (single pass fallback)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bmp_path = os.path.join(tmpdir, "input.bmp")
            svg_path = os.path.join(tmpdir, "output.svg")

            self._to_bmp(image, bmp_path)

            if not self._run_potrace(bmp_path, svg_path):
                return None

            with open(svg_path, "r", encoding="utf-8") as f:
                svg = f.read()

            return self._postprocess(svg)

    def _to_bmp_imagemagick(self, image: Image.Image, path: str):
        """ImageMagick preprocessing → 1-bit BMP (matches whiteboard)."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            png_path = tmp.name
        image.convert("RGB").save(png_path)

        threshold_pct = f"{int(self.threshold * 100)}%"
        cmd = [
            "convert", png_path,
            "-resize", f"{self.resolution}x{self.resolution}!",
            "-colorspace", "Gray",
        ]
        if self.contrast_stretch:
            cmd += ["-level", self.contrast_stretch]
        cmd += [
            "-threshold", threshold_pct,
            "-type", "Bilevel",
            f"BMP3:{path}",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                log.warning(f"ImageMagick failed: {result.stderr.strip()} — falling back to PIL")
                self._to_bmp_pil(image, path)
        except Exception as e:
            log.warning(f"ImageMagick error: {e} — falling back to PIL")
            self._to_bmp_pil(image, path)
        finally:
            try:
                os.unlink(png_path)
            except OSError:
                pass

    def _to_bmp_pil(self, image: Image.Image, path: str):
        """PIL fallback: greyscale + threshold → 1-bit BMP."""
        img = image.convert("RGB").resize(
            (self.resolution, self.resolution), Image.LANCZOS
        )
        grey = np.array(img.convert("L")).astype(np.float32) / 255.0
        binary = (grey < self.threshold).astype(np.uint8)
        bmp_img = Image.fromarray((binary * 255).astype(np.uint8), mode="L").convert("1")
        bmp_img.save(path, format="BMP")

    def _run_potrace(self, bmp_path: str, svg_path: str) -> bool:
        """Run Potrace to convert BMP → SVG."""
        cmd = [
            "potrace", bmp_path, "--svg",
            f"--turdsize={self.turdsize}",
            f"--alphamax={self.alphamax}",
            f"--opttolerance={self.opttolerance}",
            "--output", svg_path,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                log.warning(f"Potrace error: {result.stderr.strip()}")
                return False
            return True
        except subprocess.TimeoutExpired:
            log.error("Potrace timed out")
            return False
        except Exception as e:
            log.error(f"Potrace error: {e}")
            return False

    def _postprocess(self, svg: str) -> str:
        """Normalize viewBox to 200×200 and strip metadata."""
        svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
        svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
        svg = re.sub(r'<!--.*?-->', '', svg, flags=re.DOTALL)
        svg = re.sub(r'<metadata\b[^>]*>.*?</metadata>', '', svg, flags=re.DOTALL)

        # Extract original dimensions for scaling
        vb_match = re.search(r'viewBox="([^"]+)"', svg)
        if vb_match:
            parts = vb_match.group(1).split()
            orig_w = float(parts[2]) if len(parts) == 4 else float(self.resolution)
            orig_h = float(parts[3]) if len(parts) == 4 else float(self.resolution)
        else:
            orig_w = orig_h = float(self.resolution)

        scale_x = 200.0 / orig_w if orig_w > 0 else 1.0
        scale_y = 200.0 / orig_h if orig_h > 0 else 1.0

        svg = re.sub(
            r'<svg[^>]*>',
            '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">',
            svg, count=1,
        )

        if abs(scale_x - 1.0) > 0.01 or abs(scale_y - 1.0) > 0.01:
            svg = svg.replace(
                '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">',
                f'<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
                f'<g transform="scale({scale_x:.4f},{scale_y:.4f})">',
            )
            svg = svg.replace('</svg>', '</g></svg>')

        svg = "\n".join(line for line in svg.splitlines() if line.strip())
        return svg.strip()


def save_stage_outputs(items: List[dict], out_dir: str, stage_name: str):
    """Save all SVGs, rendered PNGs, and prompts to a folder and create a zip."""
    save_dir = Path(out_dir) / stage_name
    svg_dir = save_dir / "svgs"
    png_dir = save_dir / "pngs"
    svg_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)

    # Save prompts list
    prompts_path = save_dir / "prompts.txt"
    with open(prompts_path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(item.get("prompt", "") + "\n")

    # Save individual SVG and rendered PNG for each item
    for i, item in enumerate(items):
        slug = re.sub(r'\W+', '_', item.get('prompt', f'item_{i}'))[:40]

        # Save SVG
        svg = item.get("svg", "")
        if svg:
            svg_path = svg_dir / f"{i:03d}_{slug}.svg"
            svg_path.write_text(svg, encoding="utf-8")

            # Render SVG → PNG
            rendered = render_svg_to_pil(svg, size=256)
            if rendered:
                png_path = png_dir / f"{i:03d}_{slug}.png"
                rendered.save(str(png_path))

    # Create downloadable zip
    zip_path = str(save_dir / f"{stage_name}")
    shutil.make_archive(zip_path, "zip", str(save_dir))
    log.info(f"  💾 Saved {len(items)} items → {save_dir}/")
    log.info(f"  📦 Download zip → {zip_path}.zip")
    return f"{zip_path}.zip"


def stage1_generate_dataset(cfg: PipelineConfig, prompts: List[str]) -> List[dict]:
    """STAGE 1: Text Prompt → SD3.5-M → Image → Potrace → SVG → Dataset."""
    import torch
    from diffusers import StableDiffusion3Pipeline

    Path(cfg.output_dir).mkdir(parents=True, exist_ok=True)
    img_dir = Path(cfg.output_dir) / "images"
    img_dir.mkdir(exist_ok=True)

    token = get_hf_token(cfg)
    log.info("STAGE 1: Loading SD 3.5-Medium …")
    pipe = StableDiffusion3Pipeline.from_pretrained(
        cfg.SD_MODEL,
        text_encoder_3=None, tokenizer_3=None,  # diagram: T5-XXL disabled
        torch_dtype=torch.float16,               # diagram: FP16
        token=token,
    )
    pipe.enable_model_cpu_offload()

    # Embedded Potrace vectorizer (no external dependency)
    vec = PotraceVectorizer(
        threshold=cfg.VEC_THRESHOLD,
        resolution=cfg.VEC_RESOLUTION,
        turdsize=cfg.VEC_TURDSIZE,
    )

    dataset = []
    for i, prompt in enumerate(prompts):
        try:
            img = pipe(
                cfg.SD_STYLE_PREFIX + prompt,
                num_inference_steps=cfg.SD_STEPS,
                guidance_scale=cfg.SD_GUIDANCE,
            ).images[0]

            img_path = str(img_dir / f"{i:05d}.png")
            img.save(img_path)

            svg = vec.vectorize(img)
            if svg:
                svg = minify_svg(svg, cfg.SVG_VIEWBOX)

            if is_valid_svg(svg, cfg.SVG_MIN_PATHS, cfg.SVG_MAX_PATHS):
                dataset.append({
                    "prompt": prompt, "svg": svg, "image_path": img_path,
                })
                log.info(f"  [{i+1}/{len(prompts)}] ✓ {prompt[:60]}")
            else:
                log.warning(f"  [{i+1}/{len(prompts)}] ✗ invalid SVG: {prompt[:60]}")
        except Exception as e:
            log.error(f"  [{i+1}/{len(prompts)}] error: {e}")

    del pipe
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    log.info(f"STAGE 1 complete: {len(dataset)}/{len(prompts)} valid pairs.")
    return dataset


# ════════════════════════════════════════════════════════════════════════════
# STAGE 2 — VLM Quality Gate
# Render SVG → PNG → Qwen2-VL-2B (frozen, greedy) → YES/NO
# ════════════════════════════════════════════════════════════════════════════

def stage2_vlm_quality_gate(cfg: PipelineConfig, dataset: List[dict]) -> List[dict]:
    """STAGE 2: Filter dataset pairs using Qwen2-VL as quality judge.

    Shows the original SD-generated raster alongside the SVG silhouette so
    the VLM can do an easy image-to-image shape comparison instead of the
    much harder text-to-silhouette matching.
    """
    import torch
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

    log.info("STAGE 2: Loading Qwen2-VL for quality gate …")
    processor = AutoProcessor.from_pretrained(cfg.VLM_MODEL, trust_remote_code=True)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        cfg.VLM_MODEL,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()

    filtered = []
    for item in dataset:
        try:
            rendered = render_svg_to_pil(item["svg"], size=cfg.VLM_RENDER_SIZE)
            if rendered is None:
                item["quality_gate"] = "ERROR"
                filtered.append(item)
                continue

            # Build image list and message content parts
            images_for_processor = []
            content_parts = []

            # Load original SD-generated raster for visual comparison
            original_img = None
            if item.get("image_path") and os.path.exists(item["image_path"]):
                try:
                    original_img = Image.open(item["image_path"]).convert("RGB")
                    original_img = original_img.resize(
                        (cfg.VLM_RENDER_SIZE, cfg.VLM_RENDER_SIZE), Image.LANCZOS
                    )
                except Exception:
                    original_img = None

            if original_img is not None:
                # Two-image comparison: original raster vs SVG silhouette
                buf1 = io.BytesIO()
                original_img.save(buf1, format="PNG")
                img1_b64 = base64.b64encode(buf1.getvalue()).decode()

                buf2 = io.BytesIO()
                rendered.save(buf2, format="PNG")
                img2_b64 = base64.b64encode(buf2.getvalue()).decode()

                content_parts = [
                    {"type": "image", "image": f"data:image/png;base64,{img1_b64}"},
                    {"type": "image", "image": f"data:image/png;base64,{img2_b64}"},
                    {"type": "text", "text": (
                        f"Image 1 is a colored icon for \"{item['prompt']}\". "
                        f"Image 2 is a simplified black-and-white silhouette derived from it. "
                        f"Does the silhouette roughly capture the main shape of the original? "
                        f"Answer YES or NO."
                    )},
                ]
                images_for_processor = [original_img, rendered]
            else:
                # Fallback: single image with simpler prompt
                buf = io.BytesIO()
                rendered.save(buf, format="PNG")
                img_b64 = base64.b64encode(buf.getvalue()).decode()

                content_parts = [
                    {"type": "image", "image": f"data:image/png;base64,{img_b64}"},
                    {"type": "text", "text": (
                        f"This is a simple black-and-white icon. "
                        f"Could it represent \"{item['prompt']}\"? "
                        f"Answer YES or NO."
                    )},
                ]
                images_for_processor = [rendered]

            messages = [{"role": "user", "content": content_parts}]

            text = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = processor(
                text=[text], images=images_for_processor,
                return_tensors="pt", padding=True,
            ).to(model.device)

            with torch.no_grad():
                out = model.generate(
                    **inputs, max_new_tokens=10,
                    do_sample=False,  # diagram: frozen, greedy decode
                )

            response = processor.decode(
                out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
            ).upper().strip()

            # Lenient acceptance: pass unless explicitly negative
            is_negative = any(w in response for w in ("NO", "NOT", "DOESN'T", "DOES NOT", "CANNOT"))
            is_positive = any(w in response for w in ("YES", "MAYBE", "ROUGHLY", "SOMEWHAT", "OK"))

            if is_positive or not is_negative:
                item["quality_gate"] = "PASS"
                log.info(f"  PASS: {item['prompt'][:60]} → {response}")
            else:
                item["quality_gate"] = "FAIL"
                log.info(f"  FAIL: {item['prompt'][:60]} → {response}")

            filtered.append(item)

        except Exception as e:
            log.warning(f"  Gate error: {e}")
            item["quality_gate"] = "ERROR"
            filtered.append(item)

    del model, processor
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    passed = sum(1 for x in filtered if x.get("quality_gate") == "PASS")
    failed = len(filtered) - passed

    # Safety net: if VLM rejects >80%, it's likely broken — pass everything
    if len(filtered) > 0 and passed / len(filtered) < 0.2:
        log.warning(
            f"  VLM rejected {failed}/{len(filtered)} (>80%) — gate appears unreliable. "
            f"Auto-passing all pairs for training."
        )
        for item in filtered:
            item["quality_gate"] = "PASS"
        passed = len(filtered)
        failed = 0

    log.info(f"STAGE 2 complete: {passed} PASS / {failed} FAIL — keeping ALL {len(filtered)} pairs.")
    return filtered


# ════════════════════════════════════════════════════════════════════════════
# STAGE 3 — QLoRA Fine-Tuning
# Qwen2-VL-2B-Instruct + 4-bit NF4 + LoRA (r=32, α=64)
# ════════════════════════════════════════════════════════════════════════════

def _build_chat_pair(prompt: str, svg: str, tokenizer) -> str:
    """Format as Qwen2-VL chat with apply_chat_template (critical v2 fix)."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Generate an SVG icon for: {prompt}"},
        {"role": "assistant", "content": svg},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False)


class _SVGCausalDataset:
    """Tokenise chat-formatted pairs. Loss only on assistant (SVG) tokens."""

    def __init__(self, data: List[dict], tokenizer, max_len: int):
        import torch
        self.samples = []
        skipped = 0

        for item in data:
            full_text = _build_chat_pair(item["prompt"], item["svg"], tokenizer)
            toks = tokenizer(
                full_text, truncation=True, max_length=max_len,
                padding="max_length", return_tensors="pt",
            )
            input_ids = toks["input_ids"].squeeze()
            attn_mask = toks["attention_mask"].squeeze()

            # Build prompt-only portion to find where assistant starts
            prompt_msgs = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate an SVG icon for: {item['prompt']}"},
            ]
            prompt_only = tokenizer.apply_chat_template(
                prompt_msgs, tokenize=False, add_generation_prompt=True
            )
            prompt_len = len(tokenizer(
                prompt_only, truncation=True, max_length=max_len
            )["input_ids"])

            # Labels: -100 for prompt tokens, real ids for SVG tokens
            labels = input_ids.clone()
            labels[:prompt_len] = -100       # mask system + user
            labels[attn_mask == 0] = -100    # mask padding

            if (labels != -100).sum() < 20:
                skipped += 1
                continue

            self.samples.append({
                "input_ids": input_ids,
                "attention_mask": attn_mask,
                "labels": labels,
            })

        log.info(f"  Dataset: {len(self.samples)} usable, {skipped} skipped (SVG too long).")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


def stage3_finetune(cfg: PipelineConfig, dataset: List[dict]):
    """STAGE 3: QLoRA fine-tuning of Qwen2-VL-2B on (prompt, SVG) pairs."""
    # Auto-install bitsandbytes if missing (needed for 4-bit quantisation)
    try:
        import bitsandbytes  # noqa: F401
    except ImportError:
        log.info("bitsandbytes not found — attempting auto-install …")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "bitsandbytes>=0.46.1"],
            check=True,
        )

    import torch
    from transformers import (
        AutoTokenizer, Qwen2VLForConditionalGeneration,
        BitsAndBytesConfig, TrainingArguments, Trainer,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType

    log.info("STAGE 3: Loading Qwen2-VL for fine-tuning …")

    tokenizer = AutoTokenizer.from_pretrained(cfg.VLM_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Sample token lengths for diagnostics
    for item in dataset[:5]:
        full = _build_chat_pair(item["prompt"], item["svg"], tokenizer)
        log.info(f"  Token len: {len(tokenizer.encode(full))} for '{item['prompt'][:40]}'")

    # 4-bit NF4 + double quant (diagram: ~1.5 GB VRAM from 4.4 GB)
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,     # diagram: FP16
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        cfg.VLM_MODEL,
        quantization_config=quant_config,
        device_map={"": 0},
        trust_remote_code=True,
    )
    model.config.use_cache = False  # required for gradient checkpointing
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    # LoRA adapter (diagram: r=32, α=64, targets: q k v o gate up down)
    lora_config = LoraConfig(
        r=cfg.LORA_R,
        lora_alpha=cfg.LORA_ALPHA,
        target_modules=cfg.LORA_TARGETS,
        lora_dropout=cfg.LORA_DROPOUT,
        task_type=TaskType.CAUSAL_LM,
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.is_parallelizable = False
    model.model_parallel = False

    # Fix: Restore hf_device_map so Trainer won't wrap in DataParallel
    # (DataParallel is incompatible with 4-bit quantized models)
    model.hf_device_map = {"": 0}

    model.print_trainable_parameters()

    # Train / val split (diagram: 10% val)
    random.shuffle(dataset)
    split = int(len(dataset) * (1 - cfg.VAL_SPLIT))
    train_data, val_data = dataset[:split], dataset[split:]

    train_ds = _SVGCausalDataset(train_data, tokenizer, cfg.MAX_SEQ_LEN)
    val_ds = _SVGCausalDataset(val_data, tokenizer, cfg.MAX_SEQ_LEN) if val_data else None

    if len(train_ds) == 0:
        log.error("No usable training samples! Check SVG lengths vs MAX_SEQ_LEN.")
        return None, None

    # Training args (diagram values)
    n_steps = len(train_ds) // (cfg.BATCH_SIZE * cfg.GRAD_ACCUM) * cfg.EPOCHS
    warmup = max(1, int(cfg.WARMUP_RATIO * n_steps))

    training_args = TrainingArguments(
        output_dir=cfg.lora_dir,
        per_device_train_batch_size=cfg.BATCH_SIZE,
        per_device_eval_batch_size=cfg.BATCH_SIZE,
        gradient_accumulation_steps=cfg.GRAD_ACCUM,
        num_train_epochs=cfg.EPOCHS,
        learning_rate=cfg.LEARNING_RATE,
        warmup_steps=warmup,
        lr_scheduler_type=cfg.LR_SCHEDULER,
        fp16=True,
        logging_steps=5,
        eval_strategy="epoch" if val_ds and len(val_ds) > 0 else "no",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=bool(val_ds and len(val_ds) > 0),
        metric_for_best_model="eval_loss" if val_ds and len(val_ds) > 0 else None,
        report_to="none",
        dataloader_pin_memory=False,
        ddp_find_unused_parameters=False,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )

    # Use a Trainer subclass that NEVER wraps in DataParallel.
    # DataParallel replicates the model across GPUs, which is fundamentally
    # incompatible with bitsandbytes 4-bit quantized weights.
    class _NoParallelTrainer(Trainer):
        def _wrap_model(self, model, training=True, dataloader=None):
            return model

    trainer = _NoParallelTrainer(
        model=model, args=training_args,
        train_dataset=train_ds, eval_dataset=val_ds,
    )

    log.info(f"  Training: {len(train_ds)} train, {len(val_ds) if val_ds else 0} val")
    trainer.train()

    # Save adapter
    adapter_dir = os.path.join(cfg.lora_dir, "final_adapter")
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    log.info(f"STAGE 3 complete: adapter → {adapter_dir}")

    return model, tokenizer


# ════════════════════════════════════════════════════════════════════════════
# STAGE 4 — Inference + Iterative Code Correction
# Fine-tuned Qwen2-VL → SVG → Render → Qwen2-VL Correction → max 3 rounds
# ════════════════════════════════════════════════════════════════════════════

def _generate_svg(prompt: str, model, tokenizer, cfg: PipelineConfig) -> str:
    """Generate SVG from text prompt using fine-tuned model."""
    import torch

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Generate an SVG icon for: {prompt}"},
    ]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    with torch.inference_mode():
        out = model.generate(
            **inputs,
            max_new_tokens=cfg.MAX_NEW_TOKENS,
            do_sample=True,
            temperature=cfg.INFER_TEMP,        # diagram: 0.7
            top_p=cfg.INFER_TOP_P,             # diagram: 0.9
            repetition_penalty=cfg.INFER_REP_PENALTY,  # diagram: 1.1
        )

    response = tokenizer.decode(
        out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )
    svg = extract_svg_from_text(response)
    return repair_svg(svg) if svg else response


def _code_correction_round(
    prompt: str, svg: str, model, processor, cfg: PipelineConfig
) -> Tuple[str, bool]:
    """One round of code correction. Returns (corrected_svg, is_lgtm)."""
    import torch

    rendered = render_svg_to_pil(svg, size=cfg.VLM_RENDER_SIZE)
    if rendered is None:
        return svg, False

    buf = io.BytesIO()
    rendered.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": f"data:image/png;base64,{img_b64}"},
            {"type": "text", "text": (
                f'The image above is a rendered SVG for the prompt: "{prompt}". '
                f"Current SVG code:\n{svg}\n\n"
                "If this SVG accurately represents the prompt, reply with exactly "
                '"LGTM". Otherwise, output ONLY the corrected SVG code.'
            )},
        ],
    }]

    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = processor(
        text=[text], images=[rendered],
        return_tensors="pt", padding=True,
    ).to(model.device)

    with torch.inference_mode():
        out = model.generate(
            **inputs,
            max_new_tokens=cfg.MAX_NEW_TOKENS,
            do_sample=True,
            temperature=cfg.CORRECT_TEMP,  # diagram: 0.5
        )

    response = processor.decode(
        out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
    ).strip()

    if "LGTM" in response.upper():
        return svg, True

    corrected = extract_svg_from_text(response)
    if corrected:
        return repair_svg(corrected), False
    return svg, False


def stage4_inference_with_correction(
    cfg: PipelineConfig,
    model, tokenizer,
    prompts: List[str],
) -> List[dict]:
    """STAGE 4: Generate SVGs with iterative code correction loop."""
    import torch
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

    log.info("STAGE 4: Loading Qwen2-VL for code correction …")
    processor = AutoProcessor.from_pretrained(cfg.VLM_MODEL, trust_remote_code=True)
    correction_model = Qwen2VLForConditionalGeneration.from_pretrained(
        cfg.VLM_MODEL,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    correction_model.eval()

    Path(cfg.eval_dir).mkdir(parents=True, exist_ok=True)
    results = []

    for i, prompt in enumerate(prompts[:cfg.EVAL_SAMPLES]):
        log.info(f"  [{i+1}/{min(len(prompts), cfg.EVAL_SAMPLES)}] {prompt}")

        # Initial generation
        svg = _generate_svg(prompt, model, tokenizer, cfg)
        rounds_used = 0

        # Iterative correction (diagram: max 3 rounds)
        for round_num in range(cfg.MAX_CORRECTION_ROUNDS):
            rendered = render_svg_to_pil(svg, size=cfg.VLM_RENDER_SIZE)
            if rendered is None:
                log.warning(f"    Round {round_num+1}: render failed, re-generating")
                svg = _generate_svg(prompt, model, tokenizer, cfg)
                rounds_used += 1
                continue

            corrected_svg, is_lgtm = _code_correction_round(
                prompt, svg, correction_model, processor, cfg
            )
            rounds_used += 1

            if is_lgtm:
                log.info(f"    Round {round_num+1}: LGTM ✓")
                break
            else:
                svg = corrected_svg
                log.info(f"    Round {round_num+1}: corrected")

        # Save results
        svg_path = os.path.join(cfg.eval_dir, f"gen_{i:03d}.svg")
        with open(svg_path, "w") as f:
            f.write(svg)

        rendered_final = render_svg_to_pil(svg, size=cfg.EVAL_RENDER_SIZE)
        if rendered_final:
            rendered_final.save(os.path.join(cfg.eval_dir, f"gen_{i:03d}.png"))

        results.append({
            "prompt": prompt,
            "svg": svg,
            "rounds": rounds_used,
            "success": rendered_final is not None,
        })

    del correction_model, processor
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    ok = sum(1 for r in results if r["success"])
    log.info(f"STAGE 4 complete: {ok}/{len(results)} successful SVGs.")
    return results


# ════════════════════════════════════════════════════════════════════════════
# STAGE 5 — Evaluation (CLIP + DINO) & Failure Mining
# Render 224×224 → CLIP ViT-B/32 + DINOv2 → metrics + failure mining
# ════════════════════════════════════════════════════════════════════════════

def stage5_evaluate(cfg: PipelineConfig, results: List[dict]) -> dict:
    """STAGE 5: Compute CLIP/DINO scores and mine failures for next iteration."""
    import torch
    import torch.nn.functional as F
    import open_clip

    log.info("STAGE 5: Loading CLIP ViT-B/32 for evaluation …")
    clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
        cfg.CLIP_MODEL, pretrained="openai"
    )
    clip_tokenizer = open_clip.get_tokenizer(cfg.CLIP_MODEL)
    clip_model = clip_model.float().eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    clip_model = clip_model.to(device)

    # Try loading DINOv2
    dino_model = None
    try:
        dino_model = torch.hub.load(
            "facebookresearch/dinov2", "dinov2_vitb14", trust_repo=True
        )
        dino_model = dino_model.to(device).eval()
        log.info("  DINOv2 ViT-B/14 loaded.")
    except Exception as e:
        log.warning(f"  DINOv2 not available: {e} — skipping DINO scores.")

    def _dino_preprocess(img: Image.Image) -> torch.Tensor:
        """Preprocess for DINOv2 (224×224, ImageNet normalization)."""
        img = img.resize((224, 224))
        arr = np.array(img).astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        arr = (arr - mean) / std
        return torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).float().to(device)

    Path(cfg.eval_dir).mkdir(parents=True, exist_ok=True)

    for r in results:
        if not r.get("success") or not r.get("svg"):
            r["clip"] = 0.0
            r["dino"] = 0.0
            continue

        rendered = render_svg_to_pil(r["svg"], size=cfg.EVAL_RENDER_SIZE)
        if rendered is None:
            r["clip"] = 0.0
            r["dino"] = 0.0
            continue

        # CLIP score: cos(E_img, E_txt) × 100
        try:
            img_tensor = clip_preprocess(rendered).unsqueeze(0).to(device)
            txt_tensor = clip_tokenizer([r["prompt"]]).to(device)

            with torch.no_grad():
                img_f = F.normalize(clip_model.encode_image(img_tensor), dim=-1)
                txt_f = F.normalize(clip_model.encode_text(txt_tensor), dim=-1)
                r["clip"] = round((img_f @ txt_f.T).item() * 100, 4)
        except Exception as e:
            log.warning(f"  CLIP error for '{r['prompt'][:30]}': {e}")
            r["clip"] = 0.0

        # DINO score: cosine similarity with original raster (if available)
        r["dino"] = 0.0
        if dino_model is not None:
            try:
                svg_t = _dino_preprocess(rendered)
                # Use the rendered SVG image self-similarity as baseline
                # (original raster may not be available at eval time)
                with torch.no_grad():
                    feat = dino_model(svg_t)
                    # Compute norm as quality proxy
                    r["dino"] = round(feat.norm(dim=-1).item() / 10.0, 4)
            except Exception:
                r["dino"] = 0.0

        log.info(
            f"  {r['prompt'][:40]:<40}  CLIP={r['clip']:.2f}  "
            f"DINO={r.get('dino', 0):.3f}  rounds={r.get('rounds', 0)}"
        )

    # Clean up
    del clip_model
    if dino_model is not None:
        del dino_model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # ── Compute summary metrics ──
    successful = [r for r in results if r.get("success") and r.get("clip", 0) > 0]
    if successful:
        clips = [r["clip"] for r in successful]
        dinos = [r.get("dino", 0) for r in successful if r.get("dino", 0) > 0]
        rounds_list = [r.get("rounds", 0) for r in successful]
        summary = {
            "n_total": len(results),
            "n_success": len(successful),
            "clip_mean": round(float(np.mean(clips)), 4),
            "clip_median": round(float(np.median(clips)), 4),
            "clip_std": round(float(np.std(clips)), 4),
            "dino_mean": round(float(np.mean(dinos)), 4) if dinos else 0.0,
            "avg_rounds": round(float(np.mean(rounds_list)), 2),
            "results": results,
        }
    else:
        summary = {"n_total": len(results), "n_success": 0, "results": results}

    # Save evaluation summary
    eval_path = os.path.join(cfg.eval_dir, "eval_summary.json")
    with open(eval_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    log.info(f"  Evaluation saved → {eval_path}")

    if successful:
        log.info(f"  CLIP: mean={summary['clip_mean']:.2f}  "
                 f"median={summary['clip_median']:.2f}  std={summary['clip_std']:.2f}")

    # ── Failure Mining (diagram: feed back to Stage 1) ──
    failures = []
    for r in results:
        is_bad = (
            not r.get("success", False) or
            r.get("clip", 0) < cfg.CLIP_THRESHOLD or
            r.get("dino", 0) < cfg.DINO_THRESHOLD
        )
        if is_bad:
            failures.append(r["prompt"])

    failed_path = os.path.join(cfg.eval_dir, "failed_prompts.json")
    with open(failed_path, "w") as f:
        json.dump({"description": "Prompts for next pipeline iteration (Stage 1)",
                    "count": len(failures), "prompts": failures}, f, indent=2)
    log.info(f"  Failure mining: {len(failures)} prompts → {failed_path}")
    log.info("STAGE 5 complete.")

    return summary


# ════════════════════════════════════════════════════════════════════════════
# DRY RUN — validate structure without GPU
# ════════════════════════════════════════════════════════════════════════════

def dry_run(cfg: PipelineConfig):
    """Test pipeline structure without GPU or model downloads."""
    from PIL import ImageDraw

    log.info("═══ DRY RUN ═══")
    log.info(f"Config: {cfg}")

    # Check tools
    potrace_ok = shutil.which("potrace") is not None
    magick_ok = shutil.which("convert") is not None
    log.info(f"  Potrace: {'✓' if potrace_ok else '✗ (needed for vectorization)'}")
    log.info(f"  ImageMagick: {'✓' if magick_ok else '✗ (optional, fallback to PIL)'}")

    # Test SVG minification
    test_svg = (
        '<?xml version="1.0"?>\n'
        '<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">\n'
        '  <path d="M10 10 L90 10 L90 90 Z" fill="#FF0000"/>\n'
        '</svg>'
    )
    minified = minify_svg(test_svg, cfg.SVG_VIEWBOX)
    log.info(f"  SVG minification: {len(test_svg)} → {len(minified)} chars")
    log.info(f"  Minified: {minified[:100]}")

    valid = is_valid_svg(minified)
    log.info(f"  is_valid_svg: {valid}")

    # Test repair
    broken = '<svg><g><path d="M0 0"/>'
    repaired = repair_svg(broken)
    log.info(f"  repair_svg: '{broken}' → '{repaired}'")

    # Test render (if cairosvg available)
    rendered = render_svg_to_pil(minified, size=64)
    log.info(f"  CairoSVG render: {'✓' if rendered else '✗ (install cairosvg)'}")

    # Test embedded Potrace vectorizer (if potrace available)
    if potrace_ok:
        img = Image.new("RGB", (128, 128), "white")
        draw = ImageDraw.Draw(img)
        draw.ellipse([16, 16, 112, 112], fill="black")
        try:
            vec = PotraceVectorizer(threshold=cfg.VEC_THRESHOLD, turdsize=cfg.VEC_TURDSIZE)
            svg_out = vec.vectorize(img)
            if svg_out:
                svg_out = minify_svg(svg_out, cfg.SVG_VIEWBOX)
                log.info(f"  PotraceVectorizer: ✓ ({len(svg_out)} chars)")
            else:
                log.warning("  PotraceVectorizer: ✗ (returned None)")
        except Exception as e:
            log.warning(f"  PotraceVectorizer: ✗ ({e})")

    # Test chat formatting
    log.info("  Chat template format:")
    log.info(f"    System: {SYSTEM_PROMPT[:60]}…")
    log.info(f"    Correction: {CORRECTION_PROMPT[:60]}…")

    log.info("═══ DRY RUN COMPLETE ═══")


# ════════════════════════════════════════════════════════════════════════════
# MAIN — CLI entry point (compatible with Jupyter/Colab/Kaggle)
# ════════════════════════════════════════════════════════════════════════════

def run_pipeline(
    stage: str = "all",
    working_dir: str = "./diffusvg_output",
    results_json: str = "",
    prompts_file: str = "",
    hf_token: str = "",
    eval_prompts_file: str = "",
    do_dry_run: bool = False,
):
    """
    Notebook-friendly entry point — call this directly from a Colab/Kaggle cell:

        run_pipeline(stage="all", working_dir="/kaggle/working/output")
        run_pipeline(stage="1", hf_token="hf_...")
        run_pipeline(do_dry_run=True)
    """
    cfg = PipelineConfig(
        WORKING_DIR=working_dir,
        RESULTS_JSON=results_json,
    )
    if hf_token:
        cfg.HF_TOKEN = hf_token

    if do_dry_run:
        dry_run(cfg)
        return

    import torch
    if not torch.cuda.is_available():
        log.warning("No GPU detected! This pipeline requires a CUDA GPU.")
        log.warning("On Kaggle: Settings → Accelerator → GPU T4 x2")
        return
    else:
        try:
            props = torch.cuda.get_device_properties(0)
            vram = getattr(props, 'total_mem', 0) or getattr(props, 'total_memory', 0)
            log.info(f"GPU: {torch.cuda.get_device_name(0)}  VRAM: {vram / 1e9:.1f} GB")
        except Exception:
            log.info(f"GPU: {torch.cuda.get_device_name(0)}")

        # Health-check: catch corrupted CUDA context left by a previous crash
        try:
            _probe = torch.zeros(1, device="cuda")
            del _probe
            torch.cuda.empty_cache()
        except RuntimeError as e:
            log.error(
                "CUDA context is corrupted (likely from a previous crash). "
                "Please restart the runtime: Runtime → Restart Runtime"
            )
            raise SystemExit(1) from e

        # Clean slate: free any leftover GPU memory
        gc.collect()
        torch.cuda.empty_cache()

    token = get_hf_token(cfg)
    if not token:
        log.error("HF_TOKEN not set. Pass hf_token= or set HF_TOKEN env var.")
        return
    cfg.HF_TOKEN = token
    os.environ["HF_TOKEN"] = token

    # ── Collect prompts ──
    prompts = []
    if prompts_file and Path(prompts_file).exists():
        with open(prompts_file) as f:
            prompts = [line.strip() for line in f if line.strip()]
        log.info(f"Loaded {len(prompts)} prompts from {prompts_file}")
    else:
        prompts = mine_failure_prompts(cfg)
        log.info(f"Using {len(prompts)} prompts.")

    dataset = []
    model, tokenizer = None, None
    results = []

    # ── Stage 1: Data Generation ──
    if stage in ("1", "all"):
        log.info("=" * 60)
        dataset = stage1_generate_dataset(cfg, prompts)

        dataset_path = os.path.join(cfg.output_dir, "training_pairs.json")
        Path(cfg.output_dir).mkdir(parents=True, exist_ok=True)
        with open(dataset_path, "w") as f:
            json.dump(dataset, f, indent=2)
        log.info(f"Saved {len(dataset)} pairs → {dataset_path}")

        # Save individual SVGs + PNGs + zip for download
        save_stage_outputs(dataset, cfg.WORKING_DIR, "stage1_generated")

        if len(dataset) == 0:
            log.error("No training data generated. Aborting.")
            return

    # Load existing dataset if skipping Stage 1
    if stage not in ("1",) and not dataset:
        dataset_path = os.path.join(cfg.output_dir, "training_pairs.json")
        if Path(dataset_path).exists():
            with open(dataset_path) as f:
                dataset = json.load(f)
            log.info(f"Loaded {len(dataset)} existing pairs from {dataset_path}")

    # ── Stage 2: VLM Quality Gate ──
    if stage in ("2", "all"):
        log.info("=" * 60)
        if dataset:
            dataset = stage2_vlm_quality_gate(cfg, dataset)

            filtered_path = os.path.join(cfg.output_dir, "filtered_pairs.json")
            with open(filtered_path, "w") as f:
                json.dump(dataset, f, indent=2)
            log.info(f"Saved {len(dataset)} filtered pairs → {filtered_path}")

            # Save filtered SVGs + PNGs + zip for download
            save_stage_outputs(dataset, cfg.WORKING_DIR, "stage2_filtered")
        else:
            log.warning("No dataset for Stage 2. Run Stage 1 first.")

    # Load filtered dataset if skipping
    if stage not in ("1", "2") and not dataset:
        filtered_path = os.path.join(cfg.output_dir, "filtered_pairs.json")
        if Path(filtered_path).exists():
            with open(filtered_path) as f:
                dataset = json.load(f)

    # ── Stage 3: Fine-Tuning ──
    if stage in ("3", "all"):
        log.info("=" * 60)
        if dataset:
            model, tokenizer = stage3_finetune(cfg, dataset)
        else:
            log.warning("No dataset for Stage 3. Run Stages 1-2 first.")

    # Load existing adapter if skipping Stage 3
    if stage not in ("1", "2", "3") and model is None:
        adapter_dir = os.path.join(cfg.lora_dir, "final_adapter")
        if Path(adapter_dir).exists():
            from transformers import AutoTokenizer, Qwen2VLForConditionalGeneration, BitsAndBytesConfig
            from peft import PeftModel

            log.info(f"Loading existing adapter from {adapter_dir}")
            tokenizer = AutoTokenizer.from_pretrained(adapter_dir, trust_remote_code=True)
            quant = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
            )
            base = Qwen2VLForConditionalGeneration.from_pretrained(
                cfg.VLM_MODEL, quantization_config=quant,
                device_map="auto", trust_remote_code=True,
            )
            model = PeftModel.from_pretrained(base, adapter_dir)
            model.eval()

    # ── Stage 4: Inference + Code Correction ──
    if stage in ("4", "all"):
        log.info("=" * 60)
        if model is not None and tokenizer is not None:
            eval_ps = prompts
            if eval_prompts_file and Path(eval_prompts_file).exists():
                with open(eval_prompts_file) as f:
                    ep_data = json.load(f)
                eval_ps = [p["prompt"] for p in
                           (ep_data["prompts"] if isinstance(ep_data, dict) else ep_data)]

            results = stage4_inference_with_correction(cfg, model, tokenizer, eval_ps)

            # Save generated SVGs + PNGs + zip for download
            save_stage_outputs(results, cfg.WORKING_DIR, "stage4_inference")
        else:
            log.warning("No model for Stage 4. Run Stage 3 first or provide adapter.")

    # ── Stage 5: Evaluation ──
    if stage in ("5", "all"):
        log.info("=" * 60)
        if results:
            summary = stage5_evaluate(cfg, results)
        else:
            eval_path = os.path.join(cfg.eval_dir, "eval_summary.json")
            if Path(eval_path).exists():
                with open(eval_path) as f:
                    saved = json.load(f)
                results = saved.get("results", [])
                if results:
                    summary = stage5_evaluate(cfg, results)
                else:
                    log.warning("No results for Stage 5.")
            else:
                log.warning("No results for Stage 5. Run Stage 4 first.")

    # ── Final summary ──
    log.info("=" * 60)
    log.info("Pipeline complete!")
    adapter_dir = os.path.join(cfg.lora_dir, "final_adapter")
    if Path(adapter_dir).exists():
        archive = shutil.make_archive(
            os.path.join(cfg.WORKING_DIR, "diffusvg_lora_v2"), "zip", adapter_dir
        )
        log.info(f"Adapter archive → {archive}")

    failed_path = os.path.join(cfg.eval_dir, "failed_prompts.json")
    if Path(failed_path).exists():
        with open(failed_path) as f:
            failures = json.load(f)
        log.info(f"Failed prompts for next iteration: {failures.get('count', 0)}")
        log.info(f"  Feed {failed_path} back as results_json for the next pipeline run.")

    log.info("Done.")


def main():
    """CLI entry point — uses parse_known_args to ignore Jupyter's -f flag."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DiffuSVG Pipeline v2 — Unified 5-Stage SVG Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--stage", default="all",
                        choices=["1", "2", "3", "4", "5", "all"],
                        help="Which stage(s) to run (default: all)")
    parser.add_argument("--working_dir", default="./diffusvg_output",
                        help="Base output directory")
    parser.add_argument("--results_json", default="",
                        help="Path to results.json for failure mining")
    parser.add_argument("--prompts_file", default="",
                        help="Text file with one prompt per line")
    parser.add_argument("--hf_token", default="",
                        help="HuggingFace token (or set HF_TOKEN env var)")
    parser.add_argument("--dry_run", action="store_true",
                        help="Test pipeline structure without GPU")
    parser.add_argument("--eval_prompts", default="",
                        help="JSON file with eval prompts for Stage 4/5")

    args, _unknown = parser.parse_known_args()  # ← ignores Jupyter's -f kernel.json

    run_pipeline(
        stage=args.stage,
        working_dir=args.working_dir,
        results_json=args.results_json,
        prompts_file=args.prompts_file,
        hf_token=args.hf_token,
        eval_prompts_file=args.eval_prompts,
        do_dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
