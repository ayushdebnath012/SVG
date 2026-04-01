# -*- coding: utf-8 -*-
"""
DiffuSVG_Pipeline_v4.py — Direct SVG Output Pipeline
Runs on Kaggle T4 GPU  OR  Google Colab T4 GPU.

Key changes over v3:
  1. Model outputs raw SVG directly (not SVG.js JavaScript code)
  2. System prompt teaches SVG element syntax (rect, circle, ellipse, etc.)
  3. Curated seed pairs using SVG primitives (not path-only)
  4. No svg_to_svgjs / svgjs_to_svg converters needed — simpler pipeline
  5. Dynamic few-shot in-context learning at train and inference time
  6. Google Drive upload for all checkpoints and results
"""

import subprocess, shutil, sys, os, gc, json, logging, re, io, random, tempfile
from pathlib import Path
from typing import Optional

import torch
import numpy as np
from PIL import Image

os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"


# ── Detect runtime environment ───────────────────────────────────────────────
def _detect_env() -> str:
    try:
        import google.colab  # noqa: F401
        return "colab"
    except ImportError:
        pass
    if Path("/kaggle").exists():
        return "kaggle"
    return "local"

_ENV = _detect_env()

_HF_CACHE = "/content/hf_cache" if _ENV == "colab" else "/kaggle/working/hf_cache"
os.makedirs(_HF_CACHE, exist_ok=True)
os.environ["HF_HUB_CACHE"]         = _HF_CACHE
os.environ["HUGGINGFACE_HUB_CACHE"] = _HF_CACHE
os.environ["TRANSFORMERS_CACHE"]    = _HF_CACHE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DiffuSVG")
log.info(f"Runtime environment: {_ENV}")


# ════════════════════════════════════════════════════════════════════════════
# HF TOKEN
# ════════════════════════════════════════════════════════════════════════════
def _get_hf_token() -> str:
    if os.environ.get("HF_TOKEN", "").startswith("hf_"):
        return os.environ["HF_TOKEN"]
    try:
        from kaggle_secrets import UserSecretsClient
        token = UserSecretsClient().get_secret("HF_TOKEN")
        if token and token.startswith("hf_"):
            log.info("HF_TOKEN loaded from Kaggle Secrets.")
            return token
    except Exception:
        pass
    try:
        from google.colab import userdata
        token = userdata.get("HF_TOKEN")
        if token and token.startswith("hf_"):
            log.info("HF_TOKEN loaded from Colab Secrets.")
            return token
    except Exception:
        pass
    return "YOUR_HF_TOKEN"


# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
class Config:
    HF_TOKEN: str         = _get_hf_token()

    # ── Paths (auto-set per environment) ────────────────────────────────────
    _base: str            = "/content"        if _ENV == "colab" else "/kaggle/working"
    RESULTS_JSON: str     = "/kaggle/input/datasets/ayushdebnath0123/result/results.json"
    WORKING_DIR: str      = _base
    OUTPUT_DIR: str       = _base + "/dataset"
    LORA_OUTPUT_DIR: str  = _base + "/qwen2vl_svg_lora"
    EVAL_DIR: str         = _base + "/eval_results"

    CLIP_THRESHOLD: float  = 24.0
    DINO_THRESHOLD: float  = 0.35

    SD_MODEL: str          = "black-forest-labs/FLUX.1-schnell"
    SD_STEPS: int          = 4
    SD_GUIDANCE: float     = 0.0
    SD_STYLE_PREFIX: str   = "minimalist flat vector app icon, solid colors, geometric, white background, "

    VEC_RESOLUTION: int    = 256   # matches inference-API output size; fewer paths on T4
    VEC_COLOR_PRECISION: int = 6
    VEC_FILTER_SPECKLE: int = 8    # higher = fewer tiny speckle paths
    VEC_CORNER_THRESHOLD: int = 60
    SVG_MIN_PATHS: int     = 1
    SVG_MAX_PATHS: int     = 30    # keep first 30 paths to stay within MAX_SEQ_LEN

    # VLM — outputs raw SVG directly
    VLM_MODEL: str         = "Qwen/Qwen2-VL-7B-Instruct"

    MAX_SEQ_LEN: int       = 1536  # enough for ~30-path SVGs + few-shot block
    EPOCHS: int            = 5
    BATCH_SIZE: int        = 1
    GRAD_ACCUM: int        = 8
    LEARNING_RATE: float   = 1e-4
    WARMUP_RATIO: float    = 0.05
    VAL_SPLIT: float       = 0.1
    LORA_R: int            = 16
    LORA_ALPHA: int        = 32
    LORA_DROPOUT: float    = 0.05

    CLIP_MODEL: str        = "openai/clip-vit-base-patch32"

    # Google Drive
    GDRIVE_FOLDER_ID: str  = ""


cfg = Config()
os.environ["HF_TOKEN"] = cfg.HF_TOKEN
log.info(f"HF_TOKEN set: {'OK' if cfg.HF_TOKEN.startswith('hf_') else 'MISSING'}")


# ════════════════════════════════════════════════════════════════════════════
# SVG SYSTEM PROMPT — teaches the model raw SVG element syntax
# ════════════════════════════════════════════════════════════════════════════
_SVG_SYSTEM = """\
You are an SVG generation assistant.
Given a text description, output SVG elements that draw the described image inside a 200×200 viewBox.

The SVG wrapper is already provided for you:
  <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">…</svg>

Available SVG elements:
  <rect x="X" y="Y" width="W" height="H" fill="#hex"/>
  <rect x="X" y="Y" width="W" height="H" rx="R" fill="#hex"/>  (rounded corners)
  <circle cx="CX" cy="CY" r="R" fill="#hex"/>
  <ellipse cx="CX" cy="CY" rx="RX" ry="RY" fill="#hex"/>
  <line x1="X1" y1="Y1" x2="X2" y2="Y2" stroke="#hex" stroke-width="W"/>
  <polygon points="x1,y1 x2,y2 …" fill="#hex"/>
  <path d="M… L… C… Q… A… Z" fill="#hex"/>
  <path d="M… Q… …" fill="none" stroke="#hex" stroke-width="W"/>

Rules:
1. Output ONLY SVG elements, no <svg> wrapper, no explanation, no markdown.
2. Always start with a white background: <rect width="200" height="200" fill="#ffffff"/>
3. Use simple geometric primitives (rect, circle, ellipse, polygon, line) when possible.
4. Use <path> for complex or organic shapes.
5. Keep it concise — aim for under 30 elements.\
"""


# ════════════════════════════════════════════════════════════════════════════
# CURATED SEED PAIRS — primitive-based SVG examples
# These supplement the path-only data from vtracer so the model learns
# to use <circle>, <rect>, <ellipse>, <polygon>, <line> etc.
# ════════════════════════════════════════════════════════════════════════════
SVG_SEED_PAIRS = [
    # ── Simple shapes ──
    ("a blue circle",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="60" fill="#1565C0"/>'),

    ("a red square",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<rect x="40" y="40" width="120" height="120" fill="#D32F2F"/>'),

    ("a green triangle",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<polygon points="100,30 170,170 30,170" fill="#2E7D32"/>'),

    # ── Nature ──
    ("a yellow sun",
     '<rect width="200" height="200" fill="#87CEEB"/>\n'
     '<circle cx="100" cy="100" r="40" fill="#FFD700"/>\n'
     '<line x1="100" y1="100" x2="170" y2="100" stroke="#FFD700" stroke-width="4"/>\n'
     '<line x1="100" y1="100" x2="150" y2="150" stroke="#FFD700" stroke-width="4"/>\n'
     '<line x1="100" y1="100" x2="100" y2="170" stroke="#FFD700" stroke-width="4"/>\n'
     '<line x1="100" y1="100" x2="50" y2="150" stroke="#FFD700" stroke-width="4"/>\n'
     '<line x1="100" y1="100" x2="30" y2="100" stroke="#FFD700" stroke-width="4"/>\n'
     '<line x1="100" y1="100" x2="50" y2="50" stroke="#FFD700" stroke-width="4"/>\n'
     '<line x1="100" y1="100" x2="100" y2="30" stroke="#FFD700" stroke-width="4"/>\n'
     '<line x1="100" y1="100" x2="150" y2="50" stroke="#FFD700" stroke-width="4"/>'),

    ("a red apple",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="115" r="45" fill="#CC2200"/>\n'
     '<rect x="96" y="35" width="8" height="30" rx="3" fill="#4a7c40"/>\n'
     '<ellipse cx="118" cy="55" rx="15" ry="7.5" fill="#4a7c40"/>'),

    ("a green tree",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<rect x="90" y="130" width="20" height="60" fill="#5D4037"/>\n'
     '<polygon points="100,30 150,130 50,130" fill="#2E7D32"/>\n'
     '<polygon points="100,55 140,120 60,120" fill="#388E3C"/>'),

    ("a crescent moon",
     '<rect width="200" height="200" fill="#1a1a2e"/>\n'
     '<circle cx="100" cy="100" r="50" fill="#FFD54F"/>\n'
     '<circle cx="120" cy="90" r="45" fill="#1a1a2e"/>'),

    ("a rainbow",
     '<rect width="200" height="200" fill="#E3F2FD"/>\n'
     '<path d="M 10 170 A 90 90 0 0 0 190 170" fill="none" stroke="#F44336" stroke-width="10"/>\n'
     '<path d="M 20 170 A 80 80 0 0 0 180 170" fill="none" stroke="#FF9800" stroke-width="10"/>\n'
     '<path d="M 30 170 A 70 70 0 0 0 170 170" fill="none" stroke="#FFEB3B" stroke-width="10"/>\n'
     '<path d="M 40 170 A 60 60 0 0 0 160 170" fill="none" stroke="#4CAF50" stroke-width="10"/>\n'
     '<path d="M 50 170 A 50 50 0 0 0 150 170" fill="none" stroke="#2196F3" stroke-width="10"/>\n'
     '<path d="M 60 170 A 40 40 0 0 0 140 170" fill="none" stroke="#673AB7" stroke-width="10"/>'),

    ("a pink flower",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="135" cy="100" r="21" fill="#E91E63"/>\n'
     '<circle cx="118" cy="130" r="21" fill="#E91E63"/>\n'
     '<circle cx="82" cy="130" r="21" fill="#E91E63"/>\n'
     '<circle cx="65" cy="100" r="21" fill="#E91E63"/>\n'
     '<circle cx="82" cy="70" r="21" fill="#E91E63"/>\n'
     '<circle cx="118" cy="70" r="21" fill="#E91E63"/>\n'
     '<circle cx="100" cy="100" r="15" fill="#FFC107"/>'),

    ("a snowman",
     '<rect width="200" height="200" fill="#E3F2FD"/>\n'
     '<circle cx="100" cy="150" r="40" fill="#FAFAFA" stroke="#ccc" stroke-width="1"/>\n'
     '<circle cx="100" cy="95" r="30" fill="#FAFAFA" stroke="#ccc" stroke-width="1"/>\n'
     '<circle cx="100" cy="55" r="20" fill="#FAFAFA" stroke="#ccc" stroke-width="1"/>\n'
     '<circle cx="92" cy="50" r="3" fill="#212121"/>\n'
     '<circle cx="108" cy="50" r="3" fill="#212121"/>\n'
     '<polygon points="100,57 95,65 105,65" fill="#FF6F00"/>'),

    # ── Objects / Icons ──
    ("a red heart",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="75" cy="85" r="30" fill="#E53935"/>\n'
     '<circle cx="125" cy="85" r="30" fill="#E53935"/>\n'
     '<polygon points="45,100 100,165 155,100" fill="#E53935"/>'),

    ("a house with red roof",
     '<rect width="200" height="200" fill="#E3F2FD"/>\n'
     '<rect x="50" y="110" width="100" height="80" fill="#FFF9C4"/>\n'
     '<polygon points="100,40 50,110 150,110" fill="#C62828"/>\n'
     '<rect x="88" y="150" width="25" height="40" fill="#5D4037"/>\n'
     '<rect x="60" y="125" width="20" height="20" fill="#81D4FA" stroke="#555" stroke-width="1"/>'),

    ("a yellow star",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<polygon points="100,30 118,76 167,78 128,109 141,157 100,130 59,157 72,109 33,78 82,76" fill="#FDD835"/>'),

    ("a target",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="80" fill="#F44336"/>\n'
     '<circle cx="100" cy="100" r="60" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="40" fill="#F44336"/>\n'
     '<circle cx="100" cy="100" r="20" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="7" fill="#F44336"/>'),

    ("a smiley face",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="80" fill="#FDD835"/>\n'
     '<circle cx="72" cy="82" r="9" fill="#212121"/>\n'
     '<circle cx="128" cy="82" r="9" fill="#212121"/>\n'
     '<path d="M 65 115 Q 100 155 135 115" fill="none" stroke="#212121" stroke-width="5"/>'),

    ("a coffee cup",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<rect x="50" y="80" width="80" height="90" rx="8" fill="#795548"/>\n'
     '<path d="M 130 100 Q 155 100 155 130 Q 155 155 130 155" fill="none" stroke="#795548" stroke-width="6"/>\n'
     '<rect x="45" y="75" width="90" height="8" rx="4" fill="#5D4037"/>\n'
     '<path d="M 70 65 Q 75 40 80 65" fill="none" stroke="#bbb" stroke-width="3"/>\n'
     '<path d="M 90 60 Q 95 35 100 60" fill="none" stroke="#bbb" stroke-width="3"/>'),

    ("a battery icon",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<rect x="30" y="65" width="120" height="70" rx="8" fill="none" stroke="#424242" stroke-width="4"/>\n'
     '<rect x="150" y="85" width="12" height="30" rx="3" fill="#424242"/>\n'
     '<rect x="40" y="75" width="80" height="50" rx="4" fill="#4CAF50"/>'),

    ("a wifi symbol",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="150" r="4" fill="#1565C0"/>\n'
     '<path d="M 70 130 Q 100 105 130 130" fill="none" stroke="#1565C0" stroke-width="6"/>\n'
     '<path d="M 50 110 Q 100 75 150 110" fill="none" stroke="#1565C0" stroke-width="6"/>\n'
     '<path d="M 30 90 Q 100 45 170 90" fill="none" stroke="#1565C0" stroke-width="6"/>'),

    ("a music note",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<ellipse cx="80" cy="145" rx="20" ry="14" fill="#212121"/>\n'
     '<rect x="97" y="48" width="6" height="100" fill="#212121"/>\n'
     '<path d="M 100 48 Q 130 35 140 55 Q 150 75 130 70" fill="#212121"/>'),

    # ── New seeds for weak prompts ──
    ("a cat face",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="115" r="65" fill="#FFA726"/>\n'
     '<polygon points="55,80 75,28 97,80" fill="#FFA726"/>\n'
     '<polygon points="103,80 125,28 145,80" fill="#FFA726"/>\n'
     '<circle cx="75" cy="105" r="11" fill="#212121"/>\n'
     '<circle cx="125" cy="105" r="11" fill="#212121"/>\n'
     '<circle cx="100" cy="128" r="5" fill="#E91E63"/>\n'
     '<path d="M 80 142 Q 100 162 120 142" fill="none" stroke="#212121" stroke-width="3"/>'),

    ("a rocket",
     '<rect width="200" height="200" fill="#0D1B2A"/>\n'
     '<polygon points="100,20 75,90 125,90" fill="#B0BEC5"/>\n'
     '<rect x="75" y="90" width="50" height="90" fill="#CFD8DC"/>\n'
     '<circle cx="100" cy="115" r="15" fill="#81D4FA"/>\n'
     '<polygon points="75,180 55,180 75,140" fill="#E53935"/>\n'
     '<polygon points="125,180 145,180 125,140" fill="#E53935"/>\n'
     '<polygon points="85,180 100,200 115,180" fill="#FF7043"/>'),

    ("a mail envelope",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<rect x="30" y="55" width="140" height="90" fill="#BBDEFB"/>\n'
     '<polygon points="30,55 170,55 100,105" fill="#90CAF9"/>\n'
     '<line x1="30" y1="145" x2="100" y2="100" stroke="#5C9AC5" stroke-width="2"/>\n'
     '<line x1="170" y1="145" x2="100" y2="100" stroke="#5C9AC5" stroke-width="2"/>'),

    ("a phone icon",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<rect x="60" y="35" width="80" height="130" fill="#212121"/>\n'
     '<rect x="70" y="55" width="60" height="95" fill="#4FC3F7"/>\n'
     '<circle cx="100" cy="150" r="5" fill="#616161"/>\n'
     '<rect x="85" y="42" width="30" height="6" fill="#616161"/>'),

    ("an orange carrot",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<polygon points="100,175 72,65 128,65" fill="#FF6F00"/>\n'
     '<ellipse cx="100" cy="42" rx="14" ry="22" fill="#4CAF50"/>\n'
     '<ellipse cx="78" cy="50" rx="11" ry="16" fill="#4CAF50"/>\n'
     '<ellipse cx="122" cy="50" rx="11" ry="16" fill="#4CAF50"/>'),

    ("a play button",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="80" fill="#1565C0"/>\n'
     '<polygon points="78,62 78,138 152,100" fill="#ffffff"/>'),

    ("a gear icon",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="45" fill="#78909C"/>\n'
     '<rect x="89" y="45" width="22" height="110" fill="#78909C"/>\n'
     '<rect x="45" y="89" width="110" height="22" fill="#78909C"/>\n'
     '<circle cx="100" cy="100" r="19" fill="#ffffff"/>'),

    ("a home icon",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<polygon points="100,30 25,110 175,110" fill="#E53935"/>\n'
     '<rect x="45" y="110" width="110" height="90" fill="#FFF9C4"/>\n'
     '<rect x="85" y="150" width="30" height="50" fill="#795548"/>'),
]


# ════════════════════════════════════════════════════════════════════════════
# IN-CONTEXT LEARNING — dynamic few-shot example selection
# ════════════════════════════════════════════════════════════════════════════
def _select_few_shot(prompt: str, n: int = 2) -> list[tuple[str, str]]:
    """Pick N seed examples most relevant to `prompt` by word-overlap score."""
    prompt_words = set(prompt.lower().split())
    scored = []
    for p, svg in SVG_SEED_PAIRS:
        overlap = len(prompt_words & set(p.lower().split()))
        scored.append((overlap, p, svg))
    scored.sort(key=lambda x: -x[0])
    top = scored[:1]
    rest = scored[1:]
    random.shuffle(rest)
    selected = top + rest[:n - 1]
    return [(p, svg) for _, p, svg in selected[:n]]


def _few_shot_block(prompt: str, n: int = 2) -> str:
    """Return a formatted few-shot block for inclusion in the user message."""
    examples = _select_few_shot(prompt, n=n)
    lines = ["Here are examples of SVG elements for similar prompts:\n"]
    for i, (p, svg) in enumerate(examples, 1):
        lines.append(f"Example {i} — \"{p}\":\n{svg}")
    lines.append(f"\nNow generate SVG elements for: {prompt}")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# STEP 0 — Install dependencies
# ════════════════════════════════════════════════════════════════════════════
def install():
    log.info("Installing system packages …")
    subprocess.run(["apt-get", "update", "-qq"], capture_output=True)
    subprocess.run(
        ["apt-get", "install", "-y", "-qq", "libcairo2"],
        capture_output=True,
    )
    log.info("Installing Python packages …")
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q",
            "diffusers>=0.30", "transformers>=4.40", "accelerate>=0.27",
            "bitsandbytes>=0.43", "peft>=0.10", "trl>=0.8",
            "cairosvg", "pillow", "tqdm", "sentencepiece",
            "open_clip_torch", "vtracer",
            "google-api-python-client", "google-auth",
        ],
        check=True,
    )
    log.info("All packages installed (incl. vtracer).")

install()


# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — Vectorizer  (Raster → vtracer → Colour SVG)
# ════════════════════════════════════════════════════════════════════════════
class Vectorizer:
    """Convert a raster PIL image to a colour SVG string via vtracer."""

    def __init__(
        self,
        resolution: int = 256,
        color_precision: int = 6,
        filter_speckle: int = 8,
        corner_threshold: int = 60,
        max_paths: int = 30,
    ):
        self.resolution = resolution
        self.color_precision = color_precision
        self.filter_speckle = filter_speckle
        self.corner_threshold = corner_threshold
        self.max_paths = max_paths

    def vectorize(self, image: Image.Image) -> Optional[str]:
        """Convert PIL Image → colour SVG string using vtracer."""
        import vtracer

        try:
            img = image.convert("RGBA").resize(
                (self.resolution, self.resolution), Image.LANCZOS
            )
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_bytes = buf.getvalue()

            svg = vtracer.convert_raw_image_to_svg(
                png_bytes,
                img_format="png",
                colormode="color",
                hierarchical="stacked",
                mode="spline",
                filter_speckle=self.filter_speckle,
                color_precision=self.color_precision,
                corner_threshold=self.corner_threshold,
                length_threshold=4.0,
                max_iterations=10,
                splice_threshold=45,
                path_precision=3,
            )
            return self._normalize_and_minify(svg, self.max_paths)
        except Exception as e:
            log.warning(f"vtracer failed: {e}")
            return None

    @staticmethod
    def _normalize_and_minify(svg: str, max_paths: int = 0) -> str:
        svg = re.sub(
            r"<svg[^>]*>",
            '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">',
            svg, count=1,
        )
        svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
        svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg)
        svg = re.sub(r"<!--.*?-->", "", svg, flags=re.DOTALL)
        svg = re.sub(r"\s+", " ", svg).strip()
        svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.DOTALL)
        # vtracer outputs paths largest→smallest; keep first max_paths
        if max_paths > 0:
            paths = re.findall(r"<path\b[^>]*/?>", svg, flags=re.DOTALL)
            if len(paths) > max_paths:
                header = re.match(r"^(<svg[^>]*>)", svg)
                hdr = header.group(1) if header else '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
                svg = hdr + " " + " ".join(paths[:max_paths]) + " </svg>"
        return svg

    @staticmethod
    def is_valid(svg: Optional[str], min_p: int = 1, max_p: int = 500) -> bool:
        if not svg or "<path" not in svg:
            return False
        n = len(re.findall(r"<path", svg))
        return min_p <= n <= max_p


# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — SVG rendering helper
# ════════════════════════════════════════════════════════════════════════════
def render_svg_to_pil(svg_str: str, size: int = 256) -> Optional[Image.Image]:
    """Render an SVG string to a PIL Image via cairosvg."""
    try:
        import cairosvg
        png_bytes = cairosvg.svg2png(
            bytestring=svg_str.encode("utf-8"),
            output_width=size, output_height=size,
        )
        return Image.open(io.BytesIO(png_bytes)).convert("RGB")
    except Exception:
        return None


def _extract_svg_body(svg_str: str) -> str:
    """Extract just the SVG elements (body) from a full <svg>...</svg> string."""
    m = re.search(r"<svg[^>]*>(.*?)</svg>", svg_str, re.DOTALL)
    return m.group(1).strip() if m else svg_str.strip()


def _wrap_svg_body(body: str) -> str:
    """Wrap SVG elements in a proper <svg> tag for rendering."""
    body = body.strip()
    if body.startswith("<svg"):
        return body
    return f'<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n{body}\n</svg>'


# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Find & mine failure prompts from results.json
# ════════════════════════════════════════════════════════════════════════════
FALLBACK_PROMPTS = [
    "a red apple", "a yellow sun", "a blue circle", "a green tree", "a red heart",
    "a yellow star", "an orange carrot", "a pink flower", "a house with red roof",
    "a snowman", "a rocket", "a cat face", "a wifi symbol", "a battery icon",
    "a music note", "a play button", "a gear icon", "a home icon", "a mail envelope",
    "a phone icon", "a camera", "a lock", "a mountain", "a rainbow", "clouds",
    "a crescent moon", "a pizza slice", "a coffee cup", "an ice cream", "a cake",
    "a hamburger", "a donut", "a watermelon", "a banana", "a strawberry",
    "a hot air balloon", "a treasure chest", "a lighthouse", "a bicycle", "a guitar",
    "circles", "a spiral", "squares", "yin yang", "a peace sign",
    "a target", "a smiley", "thumbs up", "lightning bolt", "a car",
]


def find_results_json() -> Optional[str]:
    if Path(cfg.RESULTS_JSON).exists():
        return cfg.RESULTS_JSON
    matches = list(Path("/kaggle/input").rglob("results.json"))
    if matches:
        log.info(f"Auto-found results.json -> {matches[0]}")
        return str(matches[0])
    return None


def mine_failures(path: Optional[str]) -> list[str]:
    if path is None:
        log.warning("No results.json found -- using built-in fallback prompt list.")
        return list(FALLBACK_PROMPTS)
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
        log.warning("results.json found but no failures -- using fallback prompts.")
        return list(FALLBACK_PROMPTS)
    return bad


# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — Generate (prompt, SVG) pairs via FLUX.1 (HF Inference API) + vtracer
# ════════════════════════════════════════════════════════════════════════════
def generate_dataset(prompts: list[str]) -> list[dict]:
    """Text Prompt → FLUX.1-schnell (HF Inference API) → Image → vtracer → SVG.
    Uses the HF serverless Inference API so no model weights are downloaded locally.
    Also prepends curated SVG_SEED_PAIRS that use primitives."""
    from huggingface_hub import InferenceClient

    Path(cfg.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    img_dir = Path(cfg.OUTPUT_DIR) / "images"
    img_dir.mkdir(exist_ok=True)

    log.info("Using FLUX.1-schnell via HF Inference API (no local download) …")
    client = InferenceClient(token=cfg.HF_TOKEN)

    vec = Vectorizer(
        resolution=cfg.VEC_RESOLUTION,
        color_precision=cfg.VEC_COLOR_PRECISION,
        filter_speckle=cfg.VEC_FILTER_SPECKLE,
        corner_threshold=cfg.VEC_CORNER_THRESHOLD,
        max_paths=cfg.SVG_MAX_PATHS,
    )

    dataset = []
    api_credits_depleted = False
    for i, prompt in enumerate(prompts):
        if api_credits_depleted:
            break
        try:
            img = client.text_to_image(
                cfg.SD_STYLE_PREFIX + prompt,
                model=cfg.SD_MODEL,
                width=256, height=256,
                num_inference_steps=cfg.SD_STEPS,
            )

            img_path = str(img_dir / f"{i:05d}.png")
            img.save(img_path)

            # Vectorize → SVG (training target is the SVG body, no wrapper)
            svg = vec.vectorize(img)
            if Vectorizer.is_valid(svg, cfg.SVG_MIN_PATHS, cfg.SVG_MAX_PATHS):
                svg_body = _extract_svg_body(svg)
                dataset.append({
                    "prompt": prompt,
                    "svg": svg_body,       # raw SVG elements — training target
                    "svg_full": svg,       # full <svg>...</svg> for rendering
                    "image_path": img_path,
                })
                log.info(f"[{i+1}/{len(prompts)}] ✓  {prompt[:60]}")
            else:
                log.warning(f"[{i+1}/{len(prompts)}] ✗  invalid SVG for: {prompt[:60]}")
        except Exception as e:
            if "402" in str(e):
                log.warning(
                    "HF Inference API credits depleted (402 Payment Required). "
                    "Stopping FLUX generation — pipeline will train on seed pairs only. "
                    "To generate FLUX data: recharge credits at huggingface.co/settings/billing "
                    "or subscribe to HF PRO."
                )
                api_credits_depleted = True
            else:
                log.error(f"[{i+1}/{len(prompts)}] error: {e}")

    # ── Prepend curated seed pairs (primitives) ──
    seed_items = []
    for prompt_text, svg_body in SVG_SEED_PAIRS:
        seed_items.append({
            "prompt": prompt_text,
            "svg": svg_body,                          # SVG elements (no wrapper)
            "svg_full": _wrap_svg_body(svg_body),     # full SVG for rendering
            "image_path": None,
            "is_seed": True,
        })
    dataset = seed_items + dataset
    log.info(f"Generated {len(dataset)} total samples ({len(seed_items)} seed + {len(dataset)-len(seed_items)} generated).")
    return dataset


# ════════════════════════════════════════════════════════════════════════════
# STEP 5 — VLM Quality Gate (Qwen2-VL-7B verifies SVG ↔ prompt alignment)
# ════════════════════════════════════════════════════════════════════════════
def vlm_quality_gate(dataset: list[dict]) -> list[dict]:
    """Render each SVG, show it to Qwen2-VL-7B with the prompt, ask if it matches.
    Seed pairs are always kept (skip gate).
    If ALL items are seed pairs, skip the gate entirely to save GPU memory for training."""
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
    import base64

    non_seed = [item for item in dataset if not item.get("is_seed")]
    if not non_seed:
        log.info("VLM quality gate: all samples are seed pairs — skipping gate to preserve GPU memory for training.")
        return dataset

    log.info(f"Running VLM quality gate with {cfg.VLM_MODEL} (4-bit) …")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16,
    )
    processor = AutoProcessor.from_pretrained(cfg.VLM_MODEL, trust_remote_code=True)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        cfg.VLM_MODEL, quantization_config=bnb_config,
        device_map={"": 0}, trust_remote_code=True,
    )
    model.eval()

    filtered = []
    for item in dataset:
        if item.get("is_seed"):
            filtered.append(item)
            continue

        try:
            rendered = render_svg_to_pil(item["svg_full"], size=256)
            if rendered is None:
                continue

            buf = io.BytesIO()
            rendered.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            messages = [{"role": "user", "content": [
                {"type": "image", "image": f"data:image/png;base64,{img_b64}"},
                {"type": "text", "text": (
                    f"This SVG image was generated for the prompt: \"{item['prompt']}\". "
                    "Does the image accurately represent the prompt? Answer only YES or NO."
                )},
            ]}]

            text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = processor(
                text=[text], images=[rendered], return_tensors="pt", padding=True,
            ).to(model.device)

            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=10, do_sample=False)
            response = processor.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

            if "YES" in response.upper():
                filtered.append(item)
                log.info(f"  PASS: {item['prompt'][:60]}")
            else:
                log.info(f"  FAIL: {item['prompt'][:60]}  → {response.strip()}")
        except Exception as e:
            log.warning(f"  Gate error: {e}")
            filtered.append(item)

    del model, processor
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
    log.info(f"VLM gate: kept {len(filtered)}/{len(dataset)} samples.")
    return filtered


# ════════════════════════════════════════════════════════════════════════════
# STEP 6 — Fine-tune Qwen2-VL with QLoRA  (Text Prompt → raw SVG)
# ════════════════════════════════════════════════════════════════════════════
def build_chat_pair(prompt: str, svg_body: str, tokenizer) -> str:
    """Format as Qwen2-VL chat with dynamic few-shot examples (in-context learning).
    system=_SVG_SYSTEM, user=few-shot examples + prompt, assistant=SVG elements."""
    messages = [
        {"role": "system", "content": _SVG_SYSTEM},
        {"role": "user", "content": _few_shot_block(prompt, n=2)},
        {"role": "assistant", "content": svg_body},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False)


class SVGCausalDataset(torch.utils.data.Dataset):
    """Tokenise chat-formatted (prompt → SVG elements) pairs for causal LM training."""

    def __init__(self, data: list[dict], tokenizer, max_len: int):
        self.samples = []
        skipped = 0

        for item in data:
            full_text = build_chat_pair(item["prompt"], item["svg"], tokenizer)

            toks = tokenizer(
                full_text, truncation=True, max_length=max_len,
                padding="max_length", return_tensors="pt",
            )
            input_ids = toks["input_ids"].squeeze()
            attn_mask = toks["attention_mask"].squeeze()

            # Build prompt-only portion to find where assistant response starts
            prompt_messages = [
                {"role": "system", "content": _SVG_SYSTEM},
                {"role": "user", "content": _few_shot_block(item["prompt"], n=2)},
            ]
            prompt_only = tokenizer.apply_chat_template(
                prompt_messages, tokenize=False, add_generation_prompt=True
            )
            prompt_len = len(tokenizer(prompt_only, truncation=True, max_length=max_len)["input_ids"])

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

        log.info(f"Dataset: {len(self.samples)} usable, {skipped} skipped (SVG too long).")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


def train_lora(dataset: list[dict]):
    from transformers import (
        AutoTokenizer, Qwen2VLForConditionalGeneration,
        BitsAndBytesConfig, TrainingArguments, Trainer,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType

    log.info("Loading Qwen2-VL for fine-tuning …")

    tokenizer = AutoTokenizer.from_pretrained(cfg.VLM_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Check token lengths
    sample_lens = []
    for item in dataset[:10]:
        full = build_chat_pair(item["prompt"], item["svg"], tokenizer)
        sample_lens.append(len(tokenizer.encode(full)))
    log.info(f"Sample token lengths (first 10): {sample_lens}")
    log.info(f"Max: {max(sample_lens)}, Mean: {np.mean(sample_lens):.0f}")

    # Guard: require at least 3 GB free before attempting the ~14 GB model load.
    if torch.cuda.is_available():
        free_gb = torch.cuda.mem_get_info()[0] / 1e9
        log.info(f"GPU free before model load: {free_gb:.1f} GB")
        if free_gb < 3.0:
            log.error(
                f"Only {free_gb:.1f} GB GPU memory free — not enough to load Qwen2-VL-7B. "
                "The previous run likely left weights on GPU (Jupyter holds the traceback). "
                "Fix: Runtime → Restart runtime, then run the cell again."
            )
            return None, None

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

    lora_config = LoraConfig(
        r=cfg.LORA_R, lora_alpha=cfg.LORA_ALPHA,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=cfg.LORA_DROPOUT, task_type=TaskType.CAUSAL_LM, bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.is_parallelizable = False
    model.model_parallel = False
    model.print_trainable_parameters()

    random.shuffle(dataset)
    split = int(len(dataset) * (1 - cfg.VAL_SPLIT))
    train_data, val_data = dataset[:split], dataset[split:]

    train_ds = SVGCausalDataset(train_data, tokenizer, cfg.MAX_SEQ_LEN)
    val_ds = SVGCausalDataset(val_data, tokenizer, cfg.MAX_SEQ_LEN) if val_data else None

    if len(train_ds) == 0:
        log.error("No usable training samples! Check SVG lengths vs MAX_SEQ_LEN.")
        return None, None

    training_args = TrainingArguments(
        output_dir=cfg.LORA_OUTPUT_DIR,
        per_device_train_batch_size=cfg.BATCH_SIZE,
        per_device_eval_batch_size=cfg.BATCH_SIZE,
        gradient_accumulation_steps=cfg.GRAD_ACCUM,
        num_train_epochs=cfg.EPOCHS,
        learning_rate=cfg.LEARNING_RATE,
        warmup_steps=max(1, int(cfg.WARMUP_RATIO * (len(dataset) // (cfg.BATCH_SIZE * cfg.GRAD_ACCUM)) * cfg.EPOCHS)),
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
    )

    trainer = Trainer(
        model=model, args=training_args,
        train_dataset=train_ds, eval_dataset=val_ds,
        callbacks=[GDriveCheckpointCallback()],
    )

    log.info(f"Starting training: {len(train_ds)} train, {len(val_ds) if val_ds else 0} val")
    trainer.train()

    adapter_dir = os.path.join(cfg.LORA_OUTPUT_DIR, "final_adapter")
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    log.info(f"Adapter saved → {adapter_dir}")
    return model, tokenizer


# ════════════════════════════════════════════════════════════════════════════
# STEP 7 — Inference: Text Prompt → Qwen2-VL → raw SVG
# ════════════════════════════════════════════════════════════════════════════
@torch.inference_mode()
def generate_svg(prompt: str, model, tokenizer, max_new_tokens: int = 1500) -> str:
    """Run the fine-tuned model to produce SVG elements, then wrap in <svg> tag.
    Uses the same dynamic few-shot block as training for consistency."""
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
    response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    # Clean up the response: strip markdown fences if present
    svg_body = response.strip()
    svg_body = re.sub(r"^```(?:svg|xml|html)?\s*\n?", "", svg_body)
    svg_body = re.sub(r"\n?```\s*$", "", svg_body)

    # If the model included the <svg> wrapper, extract just the body
    if "<svg" in svg_body:
        svg_body = _extract_svg_body(svg_body)

    return _wrap_svg_body(svg_body)


# ════════════════════════════════════════════════════════════════════════════
# STEP 8 — Evaluation: CLIP & DINO scores
# ════════════════════════════════════════════════════════════════════════════
def evaluate_pipeline(model, tokenizer, test_prompts: list[str], n_samples: int = 20) -> dict:
    """Generate SVGs for test prompts and compute CLIP/DINO scores."""
    import open_clip

    log.info("Loading CLIP for evaluation …")
    clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )
    clip_tokenizer = open_clip.get_tokenizer("ViT-B-32")
    clip_model = clip_model.float().eval()
    if torch.cuda.is_available():
        clip_model = clip_model.cuda()

    Path(cfg.EVAL_DIR).mkdir(parents=True, exist_ok=True)
    results = []
    test_subset = test_prompts[:n_samples]

    for i, prompt in enumerate(test_subset):
        try:
            svg = generate_svg(prompt, model, tokenizer)
            rendered = render_svg_to_pil(svg, size=224)
            if rendered is None:
                results.append({"prompt": prompt, "clip": 0.0, "success": False})
                continue

            rendered.save(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.png"))
            with open(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.svg"), "w") as f:
                f.write(svg)

            img_tensor = clip_preprocess(rendered).unsqueeze(0)
            txt_tensor = clip_tokenizer([prompt])
            if torch.cuda.is_available():
                img_tensor = img_tensor.cuda()
                txt_tensor = txt_tensor.cuda()

            with torch.no_grad():
                img_features = clip_model.encode_image(img_tensor)
                txt_features = clip_model.encode_text(txt_tensor)
                img_features /= img_features.norm(dim=-1, keepdim=True)
                txt_features /= txt_features.norm(dim=-1, keepdim=True)
                score = (img_features @ txt_features.T).item() * 100

            results.append({"prompt": prompt, "clip": score, "success": True})
            log.info(f"  [{i+1}/{len(test_subset)}] CLIP={score:.2f}  {prompt[:50]}")
            # Upload PNG + SVG to Drive immediately
            _gdrive_upload(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.png"))
            _gdrive_upload(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.svg"))
        except Exception as e:
            log.error(f"  Eval error: {e}")
            results.append({"prompt": prompt, "clip": 0.0, "success": False})

    del clip_model
    gc.collect()
    torch.cuda.empty_cache()

    successful = [r for r in results if r["success"]]
    if successful:
        scores = [r["clip"] for r in successful]
        summary = {
            "n_total": len(results), "n_success": len(successful),
            "clip_mean": np.mean(scores), "clip_median": np.median(scores),
            "clip_std": np.std(scores), "results": results,
        }
    else:
        summary = {"n_total": len(results), "n_success": 0, "results": results}

    eval_path = os.path.join(cfg.EVAL_DIR, "eval_summary.json")
    with open(eval_path, "w") as f:
        json.dump(summary, f, indent=2)
    log.info(f"Evaluation complete → {eval_path}")
    if successful:
        log.info(f"  CLIP: mean={summary['clip_mean']:.2f}, median={summary['clip_median']:.2f}")
    return summary


def _log_disk_space():
    total, used, free = shutil.disk_usage(_HF_CACHE)
    log.info(f"Disk @ {_HF_CACHE}: {free/1e9:.1f} GB free / {total/1e9:.1f} GB total  (used {used/1e9:.1f} GB)")


def _purge_flux_cache():
    """Remove any leftover FLUX weights — we use the Inference API now, no local copy needed."""
    flux_dir = Path(_HF_CACHE) / "models--black-forest-labs--FLUX.1-schnell"
    if flux_dir.exists():
        log.info(f"Removing stale FLUX cache ({flux_dir}) to free disk space …")
        shutil.rmtree(flux_dir, ignore_errors=True)
        log.info("FLUX cache removed.")


# ════════════════════════════════════════════════════════════════════════════
# GOOGLE DRIVE — upload helper
#
# Colab  : Drive is mounted at /content/drive/MyDrive via drive.mount().
#          _gdrive_upload() simply copies the file there — no API key needed.
#          Call _mount_gdrive() once at the start (prompts browser auth once).
#
# Kaggle : Drive is NOT natively mountable. Uses a service-account JSON key
#          stored as the Kaggle secret  GDRIVE_SA_KEY.
#          Setup (one-time):
#            1. console.cloud.google.com → project → Enable Google Drive API
#            2. IAM → Service Accounts → Create → download JSON key
#            3. Share your Drive folder with the service-account email
#            4. Paste JSON content as Kaggle secret  GDRIVE_SA_KEY
#            5. Set GDRIVE_FOLDER_ID in Config above
# ════════════════════════════════════════════════════════════════════════════

_COLAB_DRIVE_ROOT = "/content/drive/MyDrive/DiffuSVG"
_gdrive_service   = None
_colab_drive_ok   = False


def _mount_gdrive():
    """Mount Google Drive on Colab (interactive browser auth, one-time per session)."""
    global _colab_drive_ok
    if _ENV != "colab":
        return
    if _colab_drive_ok:
        return
    try:
        from google.colab import drive
        drive.mount("/content/drive", force_remount=False)
        Path(_COLAB_DRIVE_ROOT).mkdir(parents=True, exist_ok=True)
        _colab_drive_ok = True
        log.info(f"Google Drive mounted → {_COLAB_DRIVE_ROOT}")
    except Exception as e:
        log.warning(f"Drive mount failed: {e} — outputs will not be saved to Drive.")


def _init_gdrive_kaggle():
    """Authenticate to Drive via service-account key (Kaggle only)."""
    global _gdrive_service
    if _gdrive_service is not None:
        return _gdrive_service
    try:
        import json as _json
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        sa_key_json = ""
        try:
            from kaggle_secrets import UserSecretsClient
            sa_key_json = UserSecretsClient().get_secret("GDRIVE_SA_KEY")
        except Exception:
            sa_key_json = os.environ.get("GDRIVE_SA_KEY", "")

        if not sa_key_json:
            log.warning("GDRIVE_SA_KEY not set — Drive upload disabled on Kaggle.")
            return None

        sa_info = _json.loads(sa_key_json)
        creds = service_account.Credentials.from_service_account_info(
            sa_info, scopes=["https://www.googleapis.com/auth/drive"]
        )
        _gdrive_service = build("drive", "v3", credentials=creds, cache_discovery=False)
        log.info(f"Google Drive (service account) ready → folder {cfg.GDRIVE_FOLDER_ID or 'root'}")
        return _gdrive_service
    except Exception as e:
        log.warning(f"Drive service-account init failed ({e}) — uploads disabled.")
        return None


def _gdrive_upload(local_path: str, remote_name: str = None):
    """Copy *local_path* to Google Drive.
    • Colab  : file-copy into the mounted Drive folder.
    • Kaggle : upload via Drive REST API using a service-account key.
    Safe to call even when Drive is not configured — silently skips."""
    lp = Path(local_path)
    if not lp.exists():
        log.warning(f"Drive upload skipped — not found: {local_path}")
        return

    name = remote_name or lp.name

    if _ENV == "colab":
        if not _colab_drive_ok:
            return
        dest = Path(_COLAB_DRIVE_ROOT) / name
        try:
            shutil.copy2(str(lp), str(dest))
            log.info(f"Drive ↑ {name}  ({lp.stat().st_size / 1024:.0f} KB)")
        except Exception as e:
            log.warning(f"Drive copy failed for {name}: {e}")
        return

    svc = _init_gdrive_kaggle()
    if svc is None:
        return
    try:
        from googleapiclient.http import MediaFileUpload
        folder = cfg.GDRIVE_FOLDER_ID or None
        meta: dict = {"name": name}
        if folder:
            meta["parents"] = [folder]

        q = f"name='{name}' and trashed=false"
        if folder:
            q += f" and '{folder}' in parents"
        existing = svc.files().list(q=q, fields="files(id)").execute().get("files", [])

        media = MediaFileUpload(str(lp), resumable=lp.stat().st_size > 5_000_000)
        if existing:
            svc.files().update(fileId=existing[0]["id"], media_body=media).execute()
        else:
            svc.files().create(body=meta, media_body=media, fields="id").execute()
        log.info(f"Drive ↑ {name}  ({lp.stat().st_size / 1024:.0f} KB)")
    except Exception as e:
        log.warning(f"Drive upload failed for {name}: {e}")


from transformers import TrainerCallback

class GDriveCheckpointCallback(TrainerCallback):
    """HuggingFace TrainerCallback that zips and uploads every saved checkpoint."""

    def on_save(self, args, state, control, **kwargs):
        ckpt_dir = os.path.join(args.output_dir, f"checkpoint-{state.global_step}")
        if not Path(ckpt_dir).exists():
            return
        zip_path = ckpt_dir + ".zip"
        shutil.make_archive(ckpt_dir, "zip", ckpt_dir)
        _gdrive_upload(zip_path, remote_name=f"checkpoint-{state.global_step}.zip")
        try:
            os.remove(zip_path)
        except OSError:
            pass


def main():
    # Clear any GPU memory left over from a previous failed run in this notebook session.
    import sys
    sys.last_traceback = None
    sys.last_value = None
    sys.last_type = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

    if not torch.cuda.is_available():
        log.warning(
            "No GPU detected! "
            "Colab: Runtime → Change runtime type → T4 GPU. "
            "Kaggle: Settings → Accelerator → GPU T4 x2."
        )
    else:
        free_gb = torch.cuda.mem_get_info()[0] / 1e9
        total_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        log.info(f"GPU: {torch.cuda.get_device_name(0)}  VRAM: {total_gb:.1f} GB total, {free_gb:.1f} GB free")
        if free_gb < total_gb * 0.5:
            log.warning(
                f"Only {free_gb:.1f} GB GPU memory free (of {total_gb:.1f} GB). "
                "A previous run may have left weights on GPU. "
                "If training OOMs: Runtime → Restart runtime, then run again."
            )

    if not cfg.HF_TOKEN.startswith("hf_"):
        raise RuntimeError(
            "HF_TOKEN not set. "
            "Colab: Tools → Secrets → add HF_TOKEN. "
            "Kaggle: Add-ons → Secrets → add HF_TOKEN."
        )

    # Mount Google Drive
    _mount_gdrive()

    # Free disk space from any previous failed FLUX download attempts
    _purge_flux_cache()
    _log_disk_space()

    # Step 3: Find failure prompts
    results_path = find_results_json()
    bad_prompts = mine_failures(results_path)
    log.info(f"Training on {len(bad_prompts)} prompts (+ {len(SVG_SEED_PAIRS)} seed pairs).")

    # Step 4: Generate dataset (includes seed pair prepending)
    raw_dataset = generate_dataset(bad_prompts)

    # Step 5: VLM quality gate
    filtered_dataset = vlm_quality_gate(raw_dataset)

    # Save dataset
    dataset_path = os.path.join(cfg.OUTPUT_DIR, "training_pairs.json")
    Path(cfg.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    with open(dataset_path, "w") as f:
        json.dump(filtered_dataset, f, indent=2)
    log.info(f"Saved {len(filtered_dataset)} training pairs → {dataset_path}")
    _gdrive_upload(dataset_path)

    if len(filtered_dataset) == 0:
        log.error("No training data after quality gate. Aborting.")
        return

    # Step 6: Fine-tune
    model, tokenizer = train_lora(filtered_dataset)

    # Step 8: Evaluate
    if model is not None:
        eval_summary = evaluate_pipeline(model, tokenizer, bad_prompts, n_samples=20)
        eval_path = os.path.join(cfg.EVAL_DIR, "eval_summary.json")
        _gdrive_upload(eval_path)

    # Step 9: Package
    adapter_dir = os.path.join(cfg.LORA_OUTPUT_DIR, "final_adapter")
    if Path(adapter_dir).exists():
        archive = shutil.make_archive(
            os.path.join(cfg.WORKING_DIR, "diffusvg_lora_v4"), "zip", adapter_dir
        )
        log.info(f"Pipeline complete. Adapter archive → {archive}")
        _gdrive_upload(archive)
    else:
        log.warning("No adapter found to export.")

    log.info("Done.")


if __name__ == "__main__":
    main()
