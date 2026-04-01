# -*- coding: utf-8 -*-
"""
DiffuSVG_LoRA_Direct.py — Direct Text-to-SVG via QLoRA Fine-Tuning

Architecture shift from v3:
  v3: Text → FLUX.1 → Image → vtracer → SVG.js (JS) → Qwen2-VL-7B (VLM) → LoRA
  Direct: Text → SVG  (one fine-tuned LLM, no FLUX, no intermediate JS, no quality gate)

Model: Qwen/Qwen2.5-1.5B-Instruct (1.5 B params, ~1 GB in 4-bit NF4)
  — swap VLM_MODEL in Config for the 7B version if you want higher capacity.

Training data: 27 hand-crafted seed pairs (same as v3)
  × 5 prompt-prefix augmentations = 135 training examples.
  No HF Inference API credits needed; runs entirely offline after model download.

Runs on: Kaggle T4 GPU  OR  Google Colab T4 GPU.
"""

import subprocess, shutil, sys, os, gc, json, logging, re, io, random, tempfile
from pathlib import Path
from typing import Optional

import torch
import numpy as np
from PIL import Image

os.environ["PYTORCH_ALLOC_CONF"]   = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["CUDA_VISIBLE_DEVICES"]  = "0"


# ── Detect runtime ────────────────────────────────────────────────────────────
def _detect_env() -> str:
    try:
        import google.colab  # noqa
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
log = logging.getLogger("DiffuSVG-Direct")
log.info(f"Runtime: {_ENV}")


# ════════════════════════════════════════════════════════════════════════════
# HF TOKEN
# ════════════════════════════════════════════════════════════════════════════
def _get_hf_token() -> str:
    if os.environ.get("HF_TOKEN", "").startswith("hf_"):
        return os.environ["HF_TOKEN"]
    try:
        from kaggle_secrets import UserSecretsClient
        t = UserSecretsClient().get_secret("HF_TOKEN")
        if t and t.startswith("hf_"):
            log.info("HF_TOKEN from Kaggle Secrets.")
            return t
    except Exception:
        pass
    try:
        from google.colab import userdata
        t = userdata.get("HF_TOKEN")
        if t and t.startswith("hf_"):
            log.info("HF_TOKEN from Colab Secrets.")
            return t
    except Exception:
        pass
    return "hf_YOUR_TOKEN_HERE"


# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
class Config:
    HF_TOKEN: str        = _get_hf_token()
    _base: str           = "/content"       if _ENV == "colab" else "/kaggle/working"
    WORKING_DIR: str     = _base
    LORA_OUTPUT_DIR: str = _base + "/diffusvg_direct_lora"
    EVAL_DIR: str        = _base + "/eval_results"

    # Model — swap to "Qwen/Qwen2.5-7B-Instruct" for more capacity (needs ~4 GB 4-bit)
    VLM_MODEL: str       = "Qwen/Qwen2.5-1.5B-Instruct"

    MAX_SEQ_LEN: int     = 512
    EPOCHS: int          = 5
    BATCH_SIZE: int      = 2
    GRAD_ACCUM: int      = 4
    LEARNING_RATE: float = 2e-4
    WARMUP_RATIO: float  = 0.1
    LORA_R: int          = 16
    LORA_ALPHA: int      = 32
    LORA_DROPOUT: float  = 0.05

    CLIP_MODEL: str      = "ViT-B-32"
    GDRIVE_FOLDER_ID: str = ""


cfg = Config()
os.environ["HF_TOKEN"] = cfg.HF_TOKEN
log.info(f"HF_TOKEN: {'OK' if cfg.HF_TOKEN.startswith('hf_') else 'MISSING'}")


# ════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — teaches direct SVG output
# ════════════════════════════════════════════════════════════════════════════
_SYSTEM = (
    "You are an SVG code generator. Given a text description, output a complete valid SVG image.\n\n"
    "Rules:\n"
    "1. Output ONLY the SVG code — no explanation, no markdown fences.\n"
    "2. Always start with: <svg viewBox=\"0 0 200 200\" xmlns=\"http://www.w3.org/2000/svg\">\n"
    "3. Always end with: </svg>\n"
    "4. First element must be a white background: <rect x=\"0\" y=\"0\" width=\"200\" height=\"200\" fill=\"#ffffff\"/>\n"
    "5. Use only: rect, circle, ellipse, polygon, line, path.\n"
    "6. Keep it concise — under 20 elements."
)

# Five prompt prefixes used for data augmentation
_PREFIXES = ["", "draw ", "generate ", "create ", "make "]


# ════════════════════════════════════════════════════════════════════════════
# EVAL PROMPTS — first 20 from the standard fallback list
# ════════════════════════════════════════════════════════════════════════════
EVAL_PROMPTS = [
    "a red apple", "a yellow sun", "a blue circle", "a green tree", "a red heart",
    "a yellow star", "an orange carrot", "a pink flower", "a house with red roof",
    "a snowman", "a rocket", "a cat face", "a wifi symbol", "a battery icon",
    "a music note", "a play button", "a gear icon", "a home icon", "a mail envelope",
    "a phone icon",
]


# ════════════════════════════════════════════════════════════════════════════
# SEED PAIRS — SVG.js format (same 27 as v3 pipeline)
# Converted to direct SVG at runtime via svgjs_to_svg()
# ════════════════════════════════════════════════════════════════════════════
_SVGJS_SEED_PAIRS = [
    ("a blue circle",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.circle(120).center(100,100).fill('#1565C0');"),

    ("a red square",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.rect(120,120).move(40,40).fill('#D32F2F');"),

    ("a green triangle",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.polygon('100,30 170,170 30,170').fill('#2E7D32');"),

    ("a yellow sun",
     "canvas.rect(200,200).fill('#87CEEB');\n"
     "canvas.circle(80).center(100,100).fill('#FFD700');\n"
     "canvas.line(100,100,170,100).stroke({color:'#FFD700',width:4});\n"
     "canvas.line(100,100,150,150).stroke({color:'#FFD700',width:4});\n"
     "canvas.line(100,100,100,170).stroke({color:'#FFD700',width:4});\n"
     "canvas.line(100,100,50,150).stroke({color:'#FFD700',width:4});\n"
     "canvas.line(100,100,30,100).stroke({color:'#FFD700',width:4});\n"
     "canvas.line(100,100,50,50).stroke({color:'#FFD700',width:4});\n"
     "canvas.line(100,100,100,30).stroke({color:'#FFD700',width:4});\n"
     "canvas.line(100,100,150,50).stroke({color:'#FFD700',width:4});"),

    ("a red apple",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.circle(90).center(100,115).fill('#CC2200');\n"
     "canvas.rect(8,30).move(96,35).fill('#4a7c40').radius(3);\n"
     "canvas.ellipse(30,15).center(118,55).fill('#4a7c40');"),

    ("a green tree",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.rect(20,60).move(90,130).fill('#5D4037');\n"
     "canvas.polygon('100,30 150,130 50,130').fill('#2E7D32');\n"
     "canvas.polygon('100,55 140,120 60,120').fill('#388E3C');"),

    ("a crescent moon",
     "canvas.rect(200,200).fill('#1a1a2e');\n"
     "canvas.circle(100).center(100,100).fill('#FFD54F');\n"
     "canvas.circle(90).center(120,90).fill('#1a1a2e');"),

    ("a rainbow",
     "canvas.rect(200,200).fill('#E3F2FD');\n"
     "canvas.path('M 10 170 A 90 90 0 0 0 190 170').fill('none').stroke({color:'#F44336',width:10});\n"
     "canvas.path('M 20 170 A 80 80 0 0 0 180 170').fill('none').stroke({color:'#FF9800',width:10});\n"
     "canvas.path('M 30 170 A 70 70 0 0 0 170 170').fill('none').stroke({color:'#FFEB3B',width:10});\n"
     "canvas.path('M 40 170 A 60 60 0 0 0 160 170').fill('none').stroke({color:'#4CAF50',width:10});\n"
     "canvas.path('M 50 170 A 50 50 0 0 0 150 170').fill('none').stroke({color:'#2196F3',width:10});\n"
     "canvas.path('M 60 170 A 40 40 0 0 0 140 170').fill('none').stroke({color:'#673AB7',width:10});"),

    ("a pink flower",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.circle(42).center(135,100).fill('#E91E63');\n"
     "canvas.circle(42).center(118,130).fill('#E91E63');\n"
     "canvas.circle(42).center(82,130).fill('#E91E63');\n"
     "canvas.circle(42).center(65,100).fill('#E91E63');\n"
     "canvas.circle(42).center(82,70).fill('#E91E63');\n"
     "canvas.circle(42).center(118,70).fill('#E91E63');\n"
     "canvas.circle(30).center(100,100).fill('#FFC107');"),

    ("a snowman",
     "canvas.rect(200,200).fill('#E3F2FD');\n"
     "canvas.circle(80).center(100,150).fill('#FAFAFA').stroke({color:'#ccc',width:1});\n"
     "canvas.circle(60).center(100,95).fill('#FAFAFA').stroke({color:'#ccc',width:1});\n"
     "canvas.circle(40).center(100,55).fill('#FAFAFA').stroke({color:'#ccc',width:1});\n"
     "canvas.circle(6).center(92,50).fill('#212121');\n"
     "canvas.circle(6).center(108,50).fill('#212121');\n"
     "canvas.polygon('100,57 95,65 105,65').fill('#FF6F00');"),

    ("a red heart",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.circle(60).center(75,85).fill('#E53935');\n"
     "canvas.circle(60).center(125,85).fill('#E53935');\n"
     "canvas.polygon('45,100 100,165 155,100').fill('#E53935');"),

    ("a house with red roof",
     "canvas.rect(200,200).fill('#E3F2FD');\n"
     "canvas.rect(100,80).move(50,110).fill('#FFF9C4');\n"
     "canvas.polygon('100,40 50,110 150,110').fill('#C62828');\n"
     "canvas.rect(25,40).move(88,150).fill('#5D4037');\n"
     "canvas.rect(20,20).move(60,125).fill('#81D4FA').stroke({color:'#555',width:1});"),

    ("a yellow star",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.polygon('100,30 118,76 167,78 128,109 141,157 100,130 59,157 72,109 33,78 82,76').fill('#FDD835');"),

    ("a target",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.circle(160).center(100,100).fill('#F44336');\n"
     "canvas.circle(120).center(100,100).fill('#ffffff');\n"
     "canvas.circle(80).center(100,100).fill('#F44336');\n"
     "canvas.circle(40).center(100,100).fill('#ffffff');\n"
     "canvas.circle(15).center(100,100).fill('#F44336');"),

    ("a smiley face",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.circle(160).center(100,100).fill('#FDD835');\n"
     "canvas.circle(18).center(72,82).fill('#212121');\n"
     "canvas.circle(18).center(128,82).fill('#212121');\n"
     "canvas.path('M 65 115 Q 100 155 135 115').fill('none')"
     ".stroke({color:'#212121',width:5});"),

    ("a coffee cup",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.rect(80,90).move(50,80).fill('#795548').radius(8);\n"
     "canvas.path('M 130 100 Q 155 100 155 130 Q 155 155 130 155')"
     ".fill('none').stroke({color:'#795548',width:6});\n"
     "canvas.rect(90,8).move(45,75).fill('#5D4037').radius(4);\n"
     "canvas.path('M 70 65 Q 75 40 80 65').fill('none')"
     ".stroke({color:'#bbb',width:3});\n"
     "canvas.path('M 90 60 Q 95 35 100 60').fill('none')"
     ".stroke({color:'#bbb',width:3});"),

    ("a battery icon",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.rect(120,70).move(30,65).fill('none')"
     ".stroke({color:'#424242',width:4}).radius(8);\n"
     "canvas.rect(12,30).move(150,85).fill('#424242').radius(3);\n"
     "canvas.rect(80,50).move(40,75).fill('#4CAF50').radius(4);"),

    ("a wifi symbol",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.circle(8).center(100,150).fill('#1565C0');\n"
     "canvas.path('M 70 130 Q 100 105 130 130').fill('none')"
     ".stroke({color:'#1565C0',width:6});\n"
     "canvas.path('M 50 110 Q 100 75 150 110').fill('none')"
     ".stroke({color:'#1565C0',width:6});\n"
     "canvas.path('M 30 90 Q 100 45 170 90').fill('none')"
     ".stroke({color:'#1565C0',width:6});"),

    ("a music note",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.ellipse(40,28).center(80,145).fill('#212121').rotate(-20);\n"
     "canvas.rect(6,100).move(97,48).fill('#212121');\n"
     "canvas.path('M 100 48 Q 130 35 140 55 Q 150 75 130 70')"
     ".fill('#212121');"),

    ("a cat face",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.circle(130).center(100,115).fill('#FFA726');\n"
     "canvas.polygon('55,80 75,28 97,80').fill('#FFA726');\n"
     "canvas.polygon('103,80 125,28 145,80').fill('#FFA726');\n"
     "canvas.circle(22).center(75,105).fill('#212121');\n"
     "canvas.circle(22).center(125,105).fill('#212121');\n"
     "canvas.circle(10).center(100,128).fill('#E91E63');\n"
     "canvas.path('M 80 142 Q 100 162 120 142').fill('none').stroke({color:'#212121',width:3});"),

    ("a rocket",
     "canvas.rect(200,200).fill('#0D1B2A');\n"
     "canvas.polygon('100,20 75,90 125,90').fill('#B0BEC5');\n"
     "canvas.rect(50,90).move(75,90).fill('#CFD8DC');\n"
     "canvas.circle(30).center(100,115).fill('#81D4FA');\n"
     "canvas.polygon('75,180 55,180 75,140').fill('#E53935');\n"
     "canvas.polygon('125,180 145,180 125,140').fill('#E53935');\n"
     "canvas.polygon('85,180 100,200 115,180').fill('#FF7043');"),

    ("a mail envelope",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.rect(140,90).move(30,55).fill('#BBDEFB');\n"
     "canvas.polygon('30,55 170,55 100,105').fill('#90CAF9');\n"
     "canvas.line(30,145,100,100).stroke({color:'#5C9AC5',width:2});\n"
     "canvas.line(170,145,100,100).stroke({color:'#5C9AC5',width:2});"),

    ("a phone icon",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.rect(80,130).move(60,35).fill('#212121');\n"
     "canvas.rect(60,95).move(70,55).fill('#4FC3F7');\n"
     "canvas.circle(10).center(100,150).fill('#616161');\n"
     "canvas.rect(30,6).move(85,42).fill('#616161');"),

    ("an orange carrot",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.polygon('100,175 72,65 128,65').fill('#FF6F00');\n"
     "canvas.ellipse(28,45).center(100,42).fill('#4CAF50');\n"
     "canvas.ellipse(22,32).center(78,50).fill('#4CAF50');\n"
     "canvas.ellipse(22,32).center(122,50).fill('#4CAF50');"),

    ("a play button",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.circle(160).center(100,100).fill('#1565C0');\n"
     "canvas.polygon('78,62 78,138 152,100').fill('#ffffff');"),

    ("a gear icon",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.circle(90).center(100,100).fill('#78909C');\n"
     "canvas.rect(22,110).move(89,45).fill('#78909C');\n"
     "canvas.rect(110,22).move(45,89).fill('#78909C');\n"
     "canvas.circle(38).center(100,100).fill('#ffffff');"),

    ("a home icon",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.polygon('100,30 25,110 175,110').fill('#E53935');\n"
     "canvas.rect(110,90).move(45,110).fill('#FFF9C4');\n"
     "canvas.rect(30,50).move(85,150).fill('#795548');"),
]


# ════════════════════════════════════════════════════════════════════════════
# SVG.js → SVG CONVERTER  (reused from v3)
# ════════════════════════════════════════════════════════════════════════════
def svgjs_to_svg(js_code: str) -> str:
    """Convert SVG.js JavaScript code to a direct SVG string."""
    elements = []

    for m in re.finditer(
        r"canvas\.rect\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)"
        r"(?:\.move\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\))?"
        r"(?:\.center\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\))?"
        r"[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)",
        js_code
    ):
        w, h, fill = m.group(1), m.group(2), m.group(7)
        if m.group(3) and m.group(4):
            x, y = m.group(3), m.group(4)
        elif m.group(5) and m.group(6):
            x = str(float(m.group(5)) - float(w) / 2)
            y = str(float(m.group(6)) - float(h) / 2)
        else:
            x, y = "0", "0"
        rx_m = re.search(r"\.radius\(\s*(\d+(?:\.\d+)?)\s*\)", m.group(0))
        rx = rx_m.group(1) if rx_m else "0"
        elements.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"/>')

    for m in re.finditer(
        r"canvas\.circle\(\s*(\d+(?:\.\d+)?)\s*\)"
        r"(?:\.center\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\))?"
        r"[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)",
        js_code
    ):
        d = float(m.group(1))
        cx = m.group(2) or str(d / 2)
        cy = m.group(3) or str(d / 2)
        elements.append(f'<circle cx="{cx}" cy="{cy}" r="{d / 2}" fill="{m.group(4)}"/>')

    for m in re.finditer(
        r"canvas\.ellipse\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)"
        r"(?:\.center\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\))?"
        r"[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)",
        js_code
    ):
        w, h = float(m.group(1)), float(m.group(2))
        cx = m.group(3) or str(w / 2)
        cy = m.group(4) or str(h / 2)
        elements.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" fill="{m.group(5)}"/>')

    for m in re.finditer(
        r"canvas\.polygon\(['\"]([^'\"]+)['\"]\)"
        r"[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)",
        js_code
    ):
        elements.append(f'<polygon points="{m.group(1)}" fill="{m.group(2)}"/>')

    # path with stroke (fill:none)
    for m in re.finditer(
        r"canvas\.path\(['\"]([^'\"]+)['\"]\)"
        r"[^;]*?\.fill\(['\"]none['\"]\)"
        r"[^;]*?\.stroke\(\{[^}]*color:\s*['\"]([^'\"]+)['\"][^}]*width:\s*(\d+(?:\.\d+)?)",
        js_code
    ):
        elements.append(f'<path d="{m.group(1)}" fill="none" stroke="{m.group(2)}" stroke-width="{m.group(3)}"/>')

    # path with fill
    for m in re.finditer(
        r"canvas\.path\(['\"]([^'\"]+)['\"]\)"
        r"[^;]*?\.fill\(['\"](?!none)([^'\"]+)['\"]\)",
        js_code
    ):
        elements.append(f'<path d="{m.group(1)}" fill="{m.group(2)}"/>')

    # line with stroke
    for m in re.finditer(
        r"canvas\.line\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,"
        r"\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)"
        r"[^;]*?\.stroke\(\{[^}]*color:\s*['\"]([^'\"]+)['\"][^}]*width:\s*(\d+(?:\.\d+)?)",
        js_code
    ):
        elements.append(
            f'<line x1="{m.group(1)}" y1="{m.group(2)}" x2="{m.group(3)}" y2="{m.group(4)}"'
            f' stroke="{m.group(5)}" stroke-width="{m.group(6)}"/>'
        )

    body = "\n".join(elements)
    return f'<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n{body}\n</svg>'


# ════════════════════════════════════════════════════════════════════════════
# INSTALL
# ════════════════════════════════════════════════════════════════════════════
def install():
    log.info("Installing packages …")
    subprocess.run(["apt-get", "install", "-y", "-qq", "libcairo2"], capture_output=True)
    subprocess.run([
        sys.executable, "-m", "pip", "install", "-q",
        "transformers>=4.40", "accelerate>=0.27",
        "bitsandbytes>=0.43", "peft>=0.10", "trl>=0.8",
        "datasets", "cairosvg", "pillow", "open_clip_torch",
        "google-api-python-client", "google-auth",
    ], check=True)
    log.info("Packages installed.")

install()


# ════════════════════════════════════════════════════════════════════════════
# RENDERING
# ════════════════════════════════════════════════════════════════════════════
def render_svg_to_pil(svg_str: str, size: int = 224) -> Optional[Image.Image]:
    try:
        import cairosvg
        png = cairosvg.svg2png(bytestring=svg_str.encode(), output_width=size, output_height=size)
        return Image.open(io.BytesIO(png)).convert("RGB")
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════════
# DATA PREPARATION
# ════════════════════════════════════════════════════════════════════════════
def build_training_data() -> list[dict]:
    """Convert SVG.js seed pairs to SVG, then augment with 5 prompt prefixes."""
    from datasets import Dataset

    examples = []
    for prompt, js in _SVGJS_SEED_PAIRS:
        svg = svgjs_to_svg(js)
        for prefix in _PREFIXES:
            aug = (prefix + prompt).strip()
            examples.append({
                "messages": [
                    {"role": "system",    "content": _SYSTEM},
                    {"role": "user",      "content": f"Generate an SVG of: {aug}"},
                    {"role": "assistant", "content": svg},
                ]
            })

    random.shuffle(examples)
    log.info(f"Training examples: {len(examples)}  ({len(_SVGJS_SEED_PAIRS)} seeds × {len(_PREFIXES)} prefixes)")
    return Dataset.from_list(examples)


# ════════════════════════════════════════════════════════════════════════════
# MODEL LOADING — QLoRA (4-bit NF4)
# ════════════════════════════════════════════════════════════════════════════
def load_model_and_tokenizer():
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    log.info(f"Loading {cfg.VLM_MODEL} in 4-bit NF4 …")
    bnb_cfg = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        cfg.VLM_MODEL, trust_remote_code=True, token=cfg.HF_TOKEN,
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        cfg.VLM_MODEL,
        quantization_config=bnb_cfg,
        device_map={"": 0},       # required for 4-bit BnB
        dtype=torch.float16,       # T4 has no BF16 hardware; force FP16
        trust_remote_code=True,
        token=cfg.HF_TOKEN,
    )
    model = prepare_model_for_kbit_training(model)

    lora_cfg = LoraConfig(
        r=cfg.LORA_R,
        lora_alpha=cfg.LORA_ALPHA,
        lora_dropout=cfg.LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()
    return model, tokenizer


# ════════════════════════════════════════════════════════════════════════════
# TRAINING — SFTTrainer
# ════════════════════════════════════════════════════════════════════════════
def train_lora(dataset, model, tokenizer):
    from trl import SFTTrainer, SFTConfig

    # Apply chat template + pre-truncate to MAX_SEQ_LEN tokens (version-agnostic)
    def _format(ex):
        text = tokenizer.apply_chat_template(
            ex["messages"], tokenize=False, add_generation_prompt=False
        )
        ids = tokenizer(text, truncation=True, max_length=cfg.MAX_SEQ_LEN)["input_ids"]
        return {"text": tokenizer.decode(ids, skip_special_tokens=False)}

    formatted = dataset.map(_format, remove_columns=["messages"])

    Path(cfg.LORA_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    args = SFTConfig(
        output_dir=cfg.LORA_OUTPUT_DIR,
        num_train_epochs=cfg.EPOCHS,
        per_device_train_batch_size=cfg.BATCH_SIZE,
        gradient_accumulation_steps=cfg.GRAD_ACCUM,
        learning_rate=cfg.LEARNING_RATE,
        warmup_steps=10,                 # warmup_ratio deprecated in trl v5
        lr_scheduler_type="cosine",
        optim="paged_adamw_8bit",
        fp16=False,  # AMP conflicts with BnB 4-bit; let BnB handle precision
        logging_steps=10,
        save_steps=50,
        save_total_limit=2,
        dataset_text_field="text",
        report_to="none",
    )

    # processing_class (trl>=0.12); fall back to no tokenizer arg (trl v5+)
    try:
        trainer = SFTTrainer(
            model=model, args=args, train_dataset=formatted,
            processing_class=tokenizer,
        )
    except TypeError:
        trainer = SFTTrainer(
            model=model, args=args, train_dataset=formatted,
        )

    log.info("Starting LoRA fine-tuning …")
    trainer.train()
    log.info("Training complete.")

    adapter_dir = os.path.join(cfg.LORA_OUTPUT_DIR, "final_adapter")
    trainer.model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    log.info(f"Adapter saved → {adapter_dir}")
    return model, tokenizer


# ════════════════════════════════════════════════════════════════════════════
# INFERENCE — direct SVG generation
# ════════════════════════════════════════════════════════════════════════════
@torch.inference_mode()
def generate_svg(prompt: str, model, tokenizer, max_new_tokens: int = 400) -> str:
    """Run the fine-tuned model and return a raw SVG string."""
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user",   "content": f"Generate an SVG of: {prompt}"},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    out = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,                 # greedy — deterministic SVG output
        pad_token_id=tokenizer.eos_token_id,
    )
    # Decode only the newly generated tokens
    new_tokens = out[0][inputs["input_ids"].shape[-1]:]
    raw = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    # Extract the SVG block if the model wrapped it in extra text
    svg_m = re.search(r"(<svg[\s\S]*?</svg>)", raw)
    return svg_m.group(1) if svg_m else raw


# ════════════════════════════════════════════════════════════════════════════
# EVALUATION — CLIP ViT-B-32
# ════════════════════════════════════════════════════════════════════════════
def evaluate(model, tokenizer, prompts: list[str] = EVAL_PROMPTS) -> dict:
    import open_clip

    # Restore eval mode + KV cache after training left gradient checkpointing on
    model.eval()
    model.config.use_cache = True

    log.info("Loading CLIP …")
    clip_model, _, clip_prep = open_clip.create_model_and_transforms(
        cfg.CLIP_MODEL, pretrained="laion2b_s34b_b79k"
    )
    clip_tok = open_clip.get_tokenizer(cfg.CLIP_MODEL)
    clip_model = clip_model.float().eval()
    if torch.cuda.is_available():
        clip_model = clip_model.cuda()

    Path(cfg.EVAL_DIR).mkdir(parents=True, exist_ok=True)
    results = []

    for i, prompt in enumerate(prompts):
        try:
            svg = generate_svg(prompt, model, tokenizer)
            rendered = render_svg_to_pil(svg)
            if rendered is None:
                results.append({"prompt": prompt, "clip": 0.0, "success": False})
                continue

            rendered.save(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.png"))
            with open(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.svg"), "w") as f:
                f.write(svg)

            img_t = clip_prep(rendered).unsqueeze(0)
            txt_t = clip_tok([prompt])
            if torch.cuda.is_available():
                img_t, txt_t = img_t.cuda(), txt_t.cuda()

            with torch.no_grad():
                img_f = clip_model.encode_image(img_t)
                txt_f = clip_model.encode_text(txt_t)
                img_f /= img_f.norm(dim=-1, keepdim=True)
                txt_f /= txt_f.norm(dim=-1, keepdim=True)
                score = (img_f @ txt_f.T).item() * 100

            results.append({"prompt": prompt, "clip": round(score, 2), "success": True})
            log.info(f"  [{i+1}/{len(prompts)}] CLIP={score:.2f}  {prompt}")

            _gdrive_upload(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.png"), subfolder="output")
            _gdrive_upload(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.svg"), subfolder="output")

        except Exception as e:
            log.error(f"  Eval error [{prompt}]: {e}")
            results.append({"prompt": prompt, "clip": 0.0, "success": False})

    del clip_model
    gc.collect()
    torch.cuda.empty_cache()

    ok = [r for r in results if r["success"]]
    scores = [r["clip"] for r in ok]
    summary = {
        "model": cfg.VLM_MODEL,
        "n_total": len(results),
        "n_success": len(ok),
        "clip_mean":   round(float(np.mean(scores)),   2) if scores else 0,
        "clip_median": round(float(np.median(scores)), 2) if scores else 0,
        "clip_std":    round(float(np.std(scores)),    2) if scores else 0,
        "results": results,
    }
    out_path = os.path.join(cfg.EVAL_DIR, "eval_summary.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    log.info(f"Eval complete → {out_path}")
    if scores:
        log.info(f"  CLIP: mean={summary['clip_mean']:.2f}  median={summary['clip_median']:.2f}  std={summary['clip_std']:.2f}")
    return summary


# ════════════════════════════════════════════════════════════════════════════
# GOOGLE DRIVE UPLOAD
# ════════════════════════════════════════════════════════════════════════════
def _mount_gdrive():
    if _ENV == "colab":
        try:
            from google.colab import drive
            drive.mount("/content/drive", force_remount=False)
            log.info("Drive mounted at /content/drive")
        except Exception as e:
            log.warning(f"Drive mount failed: {e}")


def _gdrive_upload(local_path: str, remote_name: Optional[str] = None, subfolder: str = ""):
    lp = Path(local_path)
    if not lp.exists():
        return
    name = remote_name or lp.name

    # Colab: copy to mounted Drive
    if _ENV == "colab":
        base = "/content/drive/MyDrive"
        if cfg.GDRIVE_FOLDER_ID:
            base = f"/content/drive/MyDrive/{cfg.GDRIVE_FOLDER_ID}"
        if subfolder:
            base = os.path.join(base, subfolder)
        os.makedirs(base, exist_ok=True)
        shutil.copy2(lp, os.path.join(base, name))
        log.info(f"Drive ↑ {subfolder}/{name}" if subfolder else f"Drive ↑ {name}")
        return

    # Kaggle: service-account JSON from secret GDRIVE_SA_KEY
    if _ENV == "kaggle":
        try:
            from kaggle_secrets import UserSecretsClient
            sa_json = UserSecretsClient().get_secret("GDRIVE_SA_KEY")
            if not sa_json:
                return
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            creds = Credentials.from_service_account_info(
                json.loads(sa_json),
                scopes=["https://www.googleapis.com/auth/drive"],
            )
            svc = build("drive", "v3", credentials=creds, cache_discovery=False)
            meta = {"name": name}
            if cfg.GDRIVE_FOLDER_ID:
                meta["parents"] = [cfg.GDRIVE_FOLDER_ID]
            svc.files().create(
                body=meta,
                media_body=MediaFileUpload(str(lp), resumable=False),
                fields="id",
            ).execute()
            log.info(f"Drive ↑ {name}")
        except Exception as e:
            log.warning(f"Drive upload skipped ({name}): {e}")


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    # Clear any GPU memory pinned by Jupyter tracebacks
    import sys
    sys.last_traceback = sys.last_value = sys.last_type = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

    if not torch.cuda.is_available():
        log.warning("No GPU! Set accelerator to T4 in Kaggle/Colab settings.")
    else:
        free_gb = torch.cuda.mem_get_info()[0] / 1e9
        total_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        log.info(f"GPU: {torch.cuda.get_device_name(0)}  {total_gb:.1f} GB total, {free_gb:.1f} GB free")
        if free_gb < 2.0:
            raise RuntimeError(
                f"Only {free_gb:.1f} GB VRAM free — restart the session and run again."
            )

    if not cfg.HF_TOKEN.startswith("hf_"):
        raise RuntimeError("HF_TOKEN not set. Add it via Kaggle Secrets or Colab Secrets.")

    _mount_gdrive()

    # ── Build training dataset ───────────────────────────────────────────────
    dataset = build_training_data()

    # ── Load model ───────────────────────────────────────────────────────────
    model, tokenizer = load_model_and_tokenizer()

    # ── Fine-tune ────────────────────────────────────────────────────────────
    model, tokenizer = train_lora(dataset, model, tokenizer)

    # ── Evaluate ─────────────────────────────────────────────────────────────
    summary = evaluate(model, tokenizer)

    # ── Package adapter ──────────────────────────────────────────────────────
    adapter_dir = os.path.join(cfg.LORA_OUTPUT_DIR, "final_adapter")
    if Path(adapter_dir).exists():
        archive = shutil.make_archive(
            os.path.join(cfg.WORKING_DIR, "diffusvg_direct_lora"), "zip", adapter_dir
        )
        log.info(f"Archive → {archive}")
        _gdrive_upload(archive)

    _gdrive_upload(os.path.join(cfg.EVAL_DIR, "eval_summary.json"))
    log.info("Done.")


if __name__ == "__main__":
    main()
