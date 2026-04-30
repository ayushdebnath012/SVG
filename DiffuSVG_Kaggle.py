# -*- coding: utf-8 -*-
"""
DiffuSVG_Kaggle.py — Text-to-SVG pipeline, Kaggle T4 edition.

Pipeline:
  1. Mine weak/failed prompts from a prior results.json (or use built-in list)
  2. Generate images via FLUX.1-schnell HF Inference API → vtracer → SVG.js code
  3. VLM quality gate (Qwen2-VL-7B 4-bit) — skipped when only seed pairs remain
  4. Fine-tune Qwen2-VL-7B with QLoRA on (prompt → SVG.js code) pairs
  5. Evaluate with CLIP ViT-B-32, save SVGs and scores to /kaggle/working
  6. (Optional) upload checkpoints + results to Google Drive via service account

Setup on Kaggle:
  - Accelerator : GPU T4 x2
  - Internet    : ON
  - Secrets     : HF_TOKEN  (required)
                  GDRIVE_SA_KEY  (optional — JSON of a GCP service-account key)
  - Add dataset : (optional) your prior results.json as a Kaggle dataset
"""

import subprocess, shutil, sys, os, gc, json, logging, re, io, random
from pathlib import Path
from typing import Optional

import torch
import numpy as np
from PIL import Image

os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# Redirect HF cache to /kaggle/working so the ~16 GB Qwen2-VL-7B download
# does not fill the small system disk.
_HF_CACHE = "/kaggle/working/hf_cache"
os.makedirs(_HF_CACHE, exist_ok=True)
os.environ["HF_HUB_CACHE"]         = _HF_CACHE
os.environ["HUGGINGFACE_HUB_CACHE"] = _HF_CACHE
os.environ["TRANSFORMERS_CACHE"]    = _HF_CACHE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DiffuSVG")


# ════════════════════════════════════════════════════════════════════════════
# HF TOKEN — loaded from Kaggle Secrets
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
    return "hf_YOUR_TOKEN_HERE"


# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
class Config:
    HF_TOKEN: str         = _get_hf_token()

    WORKING_DIR: str      = "/kaggle/working"
    OUTPUT_DIR: str       = "/kaggle/working/dataset"
    LORA_OUTPUT_DIR: str  = "/kaggle/working/qwen2vl_svg_lora"
    EVAL_DIR: str         = "/kaggle/working/eval_results"

    # Point this at your prior results.json if you uploaded it as a dataset.
    # Leave blank to use the built-in FALLBACK_PROMPTS list instead.
    RESULTS_JSON: str     = "/kaggle/input/diffusvg-results/results.json"

    CLIP_THRESHOLD: float  = 24.0
    DINO_THRESHOLD: float  = 0.35

    SD_MODEL: str          = "black-forest-labs/FLUX.1-schnell"
    SD_STEPS: int          = 4
    SD_GUIDANCE: float     = 0.0
    SD_STYLE_PREFIX: str   = (
        "minimalist flat vector app icon, solid colors, geometric, white background, "
    )

    VEC_RESOLUTION: int      = 256
    VEC_COLOR_PRECISION: int = 6
    VEC_FILTER_SPECKLE: int  = 8
    VEC_CORNER_THRESHOLD: int = 60
    SVG_MIN_PATHS: int       = 1
    SVG_MAX_PATHS: int       = 30

    VLM_MODEL: str         = "Qwen/Qwen2-VL-7B-Instruct"
    MAX_SEQ_LEN: int       = 1536
    EPOCHS: int            = 3
    BATCH_SIZE: int        = 1
    GRAD_ACCUM: int        = 8
    LEARNING_RATE: float   = 1e-4
    WARMUP_RATIO: float    = 0.05
    VAL_SPLIT: float       = 0.1
    LORA_R: int            = 4
    LORA_ALPHA: int        = 16
    LORA_DROPOUT: float    = 0.15

    CLIP_MODEL: str        = "openai/clip-vit-base-patch32"

    # Google Drive (optional).
    # Set GDRIVE_FOLDER_ID to the folder-ID from the Drive URL (the long string
    # after /folders/). Leave empty to upload to Drive root.
    GDRIVE_FOLDER_ID: str  = ""


cfg = Config()
os.environ["HF_TOKEN"] = cfg.HF_TOKEN
log.info(f"HF_TOKEN: {'OK' if cfg.HF_TOKEN.startswith('hf_') else 'MISSING — set it in Kaggle Secrets'}")


# ════════════════════════════════════════════════════════════════════════════
# SVG.js SYSTEM PROMPT
# ════════════════════════════════════════════════════════════════════════════
_SVGJS_SYSTEM = """\
You are an SVG.js code-generation assistant.
Given a text description, output JavaScript code that uses SVG.js v3.2 to draw the described image on a 200×200 canvas.

The canvas variable is already created for you:
  const canvas = SVG().addTo('body').size(200,200);

Available shape methods on `canvas`:
  canvas.rect(width, height)        — rectangle
  canvas.circle(diameter)           — circle (pass diameter, not radius)
  canvas.ellipse(width, height)     — ellipse
  canvas.line(x1, y1, x2, y2)      — line segment
  canvas.polygon('x1,y1 x2,y2 …')  — closed polygon
  canvas.path('M… L… C… Z')        — SVG path

Styling (chainable):
  .fill('#hexcolor')                — fill colour
  .stroke({color:'#hex', width:N}) — stroke
  .opacity(0-1)                    — opacity
  .radius(r)                       — rounded corners (rect only)

Positioning (chainable):
  .move(x, y)     — set top-left position
  .center(cx, cy) — set center position
  .size(w, h)     — resize element

Rules:
1. Output ONLY valid JavaScript code, no markdown fences, no explanation.
2. Do NOT include the canvas creation line — it is pre-defined.
3. Always start with a white background: canvas.rect(200,200).fill('#ffffff');
4. Use simple geometric primitives (rect, circle, ellipse, polygon, line) when possible.
5. Use canvas.path() for complex or organic shapes.
6. Keep code concise — aim for under 30 lines.\
"""


# ════════════════════════════════════════════════════════════════════════════
# SEED PAIRS — 27 hand-crafted (prompt, SVG.js code) examples
# All use explicit coordinates — no JavaScript for-loops, so the regex
# parser in svgjs_to_svg() can handle every line.
# ════════════════════════════════════════════════════════════════════════════
SVGJS_SEED_PAIRS = [
    # ── Simple shapes ──────────────────────────────────────────────────────
    ("a blue circle",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.circle(120).center(100,100).fill('#1565C0');"),

    ("a red square",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.rect(120,120).move(40,40).fill('#D32F2F');"),

    ("a green triangle",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.polygon('100,30 170,170 30,170').fill('#2E7D32');"),

    # ── Nature ─────────────────────────────────────────────────────────────
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

    # ── Objects / Icons ────────────────────────────────────────────────────
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

    # ── New seeds for weak-scoring prompts ─────────────────────────────────
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
# DYNAMIC FEW-SHOT SELECTION
# ════════════════════════════════════════════════════════════════════════════
def _select_few_shot(prompt: str, n: int = 2) -> list[tuple[str, str]]:
    """Pick N seed examples most relevant to `prompt` by word-overlap."""
    prompt_words = set(prompt.lower().split())
    scored = []
    for p, js in SVGJS_SEED_PAIRS:
        overlap = len(prompt_words & set(p.lower().split()))
        scored.append((overlap, p, js))
    scored.sort(key=lambda x: -x[0])
    top = scored[:1]
    rest = scored[1:]
    random.shuffle(rest)
    selected = top + rest[:n - 1]
    return [(p, js) for _, p, js in selected[:n]]


def _few_shot_block(prompt: str, n: int = 2) -> str:
    examples = _select_few_shot(prompt, n=n)
    lines = ["Here are examples of SVG.js code for similar prompts:\n"]
    for i, (p, js) in enumerate(examples, 1):
        lines.append(f"Example {i} — \"{p}\":\n{js}")
    lines.append(f"\nNow generate SVG.js code for: {prompt}")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# SVG ↔ SVG.js CONVERTERS
# ════════════════════════════════════════════════════════════════════════════
def svg_to_svgjs(svg_str: str) -> str:
    """Convert raw vtracer SVG (path-only) to SVG.js canvas.path() calls."""
    lines = ["canvas.rect(200,200).fill('#ffffff');"]
    for m in re.finditer(r'<path\s+d="([^"]+)"[^>]*?fill="([^"]*)"[^>]*/?>',svg_str):
        lines.append(f"canvas.path('{m.group(1).strip()}').fill('{m.group(2).strip() or '#000000'}');")
    if len(lines) == 1:
        for m in re.finditer(r'<path[^>]*?fill="([^"]*)"[^>]*?d="([^"]+)"[^>]*/?>',svg_str):
            lines.append(f"canvas.path('{m.group(2).strip()}').fill('{m.group(1).strip() or '#000000'}');")
    return "\n".join(lines)


def svgjs_to_svg(js_code: str) -> str:
    """Convert SVG.js JS code back to SVG markup via regex (no JS execution)."""
    elements = []

    for m in re.finditer(
        r"canvas\.rect\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)"
        r"(?:\.move\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\))?"
        r"(?:\.center\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\))?"
        r"[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)", js_code,
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
        r"[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)", js_code,
    ):
        d = float(m.group(1))
        cx = m.group(2) or str(d / 2)
        cy = m.group(3) or str(d / 2)
        elements.append(f'<circle cx="{cx}" cy="{cy}" r="{d/2}" fill="{m.group(4)}"/>')

    for m in re.finditer(
        r"canvas\.ellipse\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)"
        r"(?:\.center\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\))?"
        r"[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)", js_code,
    ):
        w, h = float(m.group(1)), float(m.group(2))
        cx = m.group(3) or str(w / 2)
        cy = m.group(4) or str(h / 2)
        elements.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" fill="{m.group(5)}"/>')

    for m in re.finditer(
        r"canvas\.polygon\(['\"]([^'\"]+)['\"]\)[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)", js_code,
    ):
        elements.append(f'<polygon points="{m.group(1)}" fill="{m.group(2)}"/>')

    for m in re.finditer(
        r"canvas\.path\(['\"]([^'\"]+)['\"]\)[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)", js_code,
    ):
        elements.append(f'<path d="{m.group(1)}" fill="{m.group(2)}"/>')

    for m in re.finditer(
        r"canvas\.line\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,"
        r"\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)"
        r"[^;]*?\.stroke\(\{[^}]*color:\s*['\"]([^'\"]+)['\"][^}]*width:\s*(\d+(?:\.\d+)?)",
        js_code,
    ):
        elements.append(
            f'<line x1="{m.group(1)}" y1="{m.group(2)}" x2="{m.group(3)}" y2="{m.group(4)}"'
            f' stroke="{m.group(5)}" stroke-width="{m.group(6)}"/>'
        )

    for m in re.finditer(
        r"canvas\.path\(['\"]([^'\"]+)['\"]\)"
        r"[^;]*?\.fill\(['\"]none['\"]\)"
        r"[^;]*?\.stroke\(\{[^}]*color:\s*['\"]([^'\"]+)['\"][^}]*width:\s*(\d+(?:\.\d+)?)",
        js_code,
    ):
        elements.append(
            f'<path d="{m.group(1)}" fill="none" stroke="{m.group(2)}" stroke-width="{m.group(3)}"/>'
        )

    body = "\n".join(elements)
    return f'<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n{body}\n</svg>'


# ════════════════════════════════════════════════════════════════════════════
# STEP 0 — Install dependencies
# ════════════════════════════════════════════════════════════════════════════
def install():
    log.info("Installing system packages ...")
    subprocess.run(["apt-get", "update", "-qq"], capture_output=True)
    subprocess.run(["apt-get", "install", "-y", "-qq", "libcairo2"], capture_output=True)
    log.info("Installing Python packages ...")
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
    log.info("All packages installed.")


install()


# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — Vectorizer (raster → vtracer → colour SVG)
# ════════════════════════════════════════════════════════════════════════════
class Vectorizer:
    def __init__(self, resolution=256, color_precision=6,
                 filter_speckle=8, corner_threshold=60, max_paths=30):
        self.resolution = resolution
        self.color_precision = color_precision
        self.filter_speckle = filter_speckle
        self.corner_threshold = corner_threshold
        self.max_paths = max_paths

    def vectorize(self, image: Image.Image) -> Optional[str]:
        import vtracer
        try:
            img = image.convert("RGBA").resize((self.resolution, self.resolution), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            svg = vtracer.convert_raw_image_to_svg(
                buf.getvalue(), img_format="png", colormode="color",
                hierarchical="stacked", mode="spline",
                filter_speckle=self.filter_speckle,
                color_precision=self.color_precision,
                corner_threshold=self.corner_threshold,
                length_threshold=4.0, max_iterations=10,
                splice_threshold=45, path_precision=3,
            )
            return self._normalize(svg, self.max_paths)
        except Exception as e:
            log.warning(f"vtracer failed: {e}")
            return None

    @staticmethod
    def _normalize(svg: str, max_paths: int = 0) -> str:
        svg = re.sub(r"<svg[^>]*>",
                     '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">', svg, count=1)
        svg = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>|<!--.*?-->", "", svg, flags=re.DOTALL)
        svg = re.sub(r"\s+", " ", svg).strip()
        svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.DOTALL)
        if max_paths > 0:
            paths = re.findall(r"<path\b[^>]*/?>", svg, flags=re.DOTALL)
            if len(paths) > max_paths:
                hdr = '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
                svg = hdr + " " + " ".join(paths[:max_paths]) + " </svg>"
        return svg

    @staticmethod
    def is_valid(svg: Optional[str], min_p: int = 1, max_p: int = 500) -> bool:
        if not svg or "<path" not in svg:
            return False
        return min_p <= len(re.findall(r"<path", svg)) <= max_p


# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — SVG rendering helper
# ════════════════════════════════════════════════════════════════════════════
def render_svg_to_pil(svg_str: str, size: int = 256) -> Optional[Image.Image]:
    try:
        import cairosvg
        png = cairosvg.svg2png(bytestring=svg_str.encode(), output_width=size, output_height=size)
        return Image.open(io.BytesIO(png)).convert("RGB")
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Mine failure prompts from results.json
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
        log.info(f"Auto-found results.json → {matches[0]}")
        return str(matches[0])
    return None


def mine_failures(path: Optional[str]) -> list[str]:
    if path is None:
        log.warning("No results.json — using built-in fallback prompt list.")
        return list(FALLBACK_PROMPTS)
    with open(path) as f:
        data = json.load(f)
    records = data["results"] if isinstance(data, dict) else data
    bad = [r["prompt"] for r in records
           if not r.get("success", True)
           or r.get("clip", 0) < cfg.CLIP_THRESHOLD
           or r.get("dino", 0) < cfg.DINO_THRESHOLD]
    if not bad:
        log.warning("No failures found in results.json — using fallback prompts.")
        return list(FALLBACK_PROMPTS)
    return bad


# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — Generate dataset via FLUX HF Inference API + vtracer
# ════════════════════════════════════════════════════════════════════════════
def generate_dataset(prompts: list[str]) -> list[dict]:
    from huggingface_hub import InferenceClient

    Path(cfg.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    img_dir = Path(cfg.OUTPUT_DIR) / "images"
    img_dir.mkdir(exist_ok=True)

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
            svg = vec.vectorize(img)
            if Vectorizer.is_valid(svg, cfg.SVG_MIN_PATHS, cfg.SVG_MAX_PATHS):
                dataset.append({
                    "prompt": prompt,
                    "svg": svg,
                    "svgjs": svg_to_svgjs(svg),
                    "image_path": img_path,
                })
                log.info(f"[{i+1}/{len(prompts)}] OK  {prompt[:60]}")
            else:
                log.warning(f"[{i+1}/{len(prompts)}] invalid SVG for: {prompt[:60]}")
        except Exception as e:
            if "402" in str(e):
                log.warning(
                    "HF Inference API credits depleted (402). "
                    "Pipeline will train on seed pairs only. "
                    "Recharge at huggingface.co/settings/billing or subscribe to HF PRO."
                )
                api_credits_depleted = True
            else:
                log.error(f"[{i+1}/{len(prompts)}] error: {e}")

    # Prepend seed pairs
    seed_items = [
        {"prompt": p, "svg": svgjs_to_svg(js), "svgjs": js,
         "image_path": None, "is_seed": True}
        for p, js in SVGJS_SEED_PAIRS
    ]
    dataset = seed_items + dataset
    log.info(f"Dataset: {len(seed_items)} seed + {len(dataset)-len(seed_items)} generated = {len(dataset)} total.")
    return dataset


# ════════════════════════════════════════════════════════════════════════════
# STEP 5 — VLM Quality Gate (Qwen2-VL-7B 4-bit)
# Skipped entirely when all samples are seed pairs (saves GPU for training).
# ════════════════════════════════════════════════════════════════════════════
def vlm_quality_gate(dataset: list[dict]) -> list[dict]:
    import base64
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig

    non_seed = [item for item in dataset if not item.get("is_seed")]
    if not non_seed:
        log.info("VLM quality gate: all samples are seed pairs — skipping to preserve GPU for training.")
        return dataset

    log.info(f"Running VLM quality gate ({cfg.VLM_MODEL}, 4-bit) ...")
    bnb = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16,
    )
    processor = AutoProcessor.from_pretrained(cfg.VLM_MODEL, trust_remote_code=True)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        cfg.VLM_MODEL, quantization_config=bnb, device_map={"": 0}, trust_remote_code=True,
    )
    model.eval()

    filtered = []
    for item in dataset:
        if item.get("is_seed"):
            filtered.append(item)
            continue
        try:
            rendered = render_svg_to_pil(item["svg"], size=256)
            if rendered is None:
                continue
            buf = io.BytesIO()
            rendered.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode()
            messages = [{"role": "user", "content": [
                {"type": "image", "image": f"data:image/png;base64,{img_b64}"},
                {"type": "text", "text": (
                    f"This SVG was generated for the prompt: \"{item['prompt']}\". "
                    "Does the image accurately represent the prompt? Answer only YES or NO."
                )},
            ]}]
            text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = processor(text=[text], images=[rendered], return_tensors="pt", padding=True
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
    log.info(f"VLM gate: {len(filtered)}/{len(dataset)} samples kept.")
    return filtered


# ════════════════════════════════════════════════════════════════════════════
# STEP 6 — Fine-tune Qwen2-VL-7B with QLoRA
# ════════════════════════════════════════════════════════════════════════════
def build_chat_pair(prompt: str, svgjs_code: str, tokenizer) -> str:
    messages = [
        {"role": "system", "content": _SVGJS_SYSTEM},
        {"role": "user",   "content": _few_shot_block(prompt, n=2)},
        {"role": "assistant", "content": svgjs_code},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False)


class SVGCausalDataset(torch.utils.data.Dataset):
    def __init__(self, data: list[dict], tokenizer, max_len: int):
        self.samples = []
        skipped = 0
        for item in data:
            full_text = build_chat_pair(item["prompt"], item["svgjs"], tokenizer)
            toks = tokenizer(full_text, truncation=True, max_length=max_len,
                             padding="max_length", return_tensors="pt")
            input_ids = toks["input_ids"].squeeze()
            attn_mask = toks["attention_mask"].squeeze()
            prompt_only = tokenizer.apply_chat_template(
                [{"role": "system", "content": _SVGJS_SYSTEM},
                 {"role": "user", "content": f"Generate SVG.js code for: {item['prompt']}"}],
                tokenize=False, add_generation_prompt=True,
            )
            prompt_len = len(tokenizer(prompt_only, truncation=True, max_length=max_len)["input_ids"])
            labels = input_ids.clone()
            labels[:prompt_len] = -100
            labels[attn_mask == 0] = -100
            if (labels != -100).sum() < 20:
                skipped += 1
                continue
            self.samples.append({"input_ids": input_ids, "attention_mask": attn_mask, "labels": labels})
        log.info(f"Dataset: {len(self.samples)} usable, {skipped} skipped.")

    def __len__(self): return len(self.samples)
    def __getitem__(self, idx): return self.samples[idx]


def train_lora(dataset: list[dict]):
    from transformers import (
        AutoTokenizer, Qwen2VLForConditionalGeneration,
        BitsAndBytesConfig, EarlyStoppingCallback, TrainingArguments, Trainer,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType

    log.info("Loading Qwen2-VL-7B for fine-tuning ...")
    tokenizer = AutoTokenizer.from_pretrained(cfg.VLM_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # VRAM guard: require at least 3 GB free before attempting the ~14 GB model load.
    if torch.cuda.is_available():
        free_gb = torch.cuda.mem_get_info()[0] / 1e9
        log.info(f"GPU free before model load: {free_gb:.1f} GB")
        if free_gb < 3.0:
            log.error(
                f"Only {free_gb:.1f} GB GPU free — not enough to load Qwen2-VL-7B. "
                "A previous run likely left weights on GPU. "
                "Fix: Session → Restart & Run All, then run again."
            )
            return None, None

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
    )
    # device_map={"": 0} required for 4-bit BitsAndBytes — "auto" causes
    # ValueError when it tries to CPU-offload quantized layers.
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        cfg.VLM_MODEL, quantization_config=quant_config,
        device_map={"": 0}, trust_remote_code=True,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    lora_config = LoraConfig(
        r=cfg.LORA_R, lora_alpha=cfg.LORA_ALPHA,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
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
    val_ds   = SVGCausalDataset(val_data,   tokenizer, cfg.MAX_SEQ_LEN) if val_data else None

    if len(train_ds) == 0:
        log.error("No usable training samples. Check SVG.js lengths vs MAX_SEQ_LEN.")
        return None, None

    training_args = TrainingArguments(
        output_dir=cfg.LORA_OUTPUT_DIR,
        per_device_train_batch_size=cfg.BATCH_SIZE,
        per_device_eval_batch_size=cfg.BATCH_SIZE,
        gradient_accumulation_steps=cfg.GRAD_ACCUM,
        num_train_epochs=cfg.EPOCHS,
        learning_rate=cfg.LEARNING_RATE,
        warmup_steps=max(1, int(cfg.WARMUP_RATIO
                                * (len(dataset) // (cfg.BATCH_SIZE * cfg.GRAD_ACCUM))
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
    )

    callbacks = [GDriveCheckpointCallback()]
    if val_ds:
        callbacks.append(EarlyStoppingCallback(early_stopping_patience=1))

    trainer = Trainer(
        model=model, args=training_args,
        train_dataset=train_ds, eval_dataset=val_ds,
        callbacks=callbacks,
    )
    log.info(f"Training: {len(train_ds)} train, {len(val_ds) if val_ds else 0} val samples.")
    trainer.train()

    adapter_dir = os.path.join(cfg.LORA_OUTPUT_DIR, "final_adapter")
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    log.info(f"Adapter saved → {adapter_dir}")
    return model, tokenizer


# ════════════════════════════════════════════════════════════════════════════
# STEP 7 — Inference: prompt → SVG.js → SVG
# ════════════════════════════════════════════════════════════════════════════
@torch.inference_mode()
def generate_svg(prompt: str, model, tokenizer, max_new_tokens: int = 1500) -> str:
    messages = [
        {"role": "system", "content": _SVGJS_SYSTEM},
        {"role": "user",   "content": _few_shot_block(prompt, n=2)},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    out = model.generate(
        **inputs, max_new_tokens=max_new_tokens,
        do_sample=True, temperature=0.7, top_p=0.9, repetition_penalty=1.1,
    )
    response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    js_code = response.strip()
    js_code = re.sub(r"^```(?:javascript|js)?\s*\n?", "", js_code)
    js_code = re.sub(r"\n?```\s*$", "", js_code)
    return svgjs_to_svg(js_code)


# ════════════════════════════════════════════════════════════════════════════
# STEP 8 — Evaluate with CLIP ViT-B-32
# ════════════════════════════════════════════════════════════════════════════
def evaluate_pipeline(model, tokenizer, test_prompts: list[str], n_samples: int = 20) -> dict:
    import open_clip

    log.info("Loading CLIP for evaluation ...")
    clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )
    clip_tok = open_clip.get_tokenizer("ViT-B-32")
    clip_model = clip_model.float().eval()
    if torch.cuda.is_available():
        clip_model = clip_model.cuda()

    Path(cfg.EVAL_DIR).mkdir(parents=True, exist_ok=True)
    results = []

    for i, prompt in enumerate(test_prompts[:n_samples]):
        try:
            svg = generate_svg(prompt, model, tokenizer)
            rendered = render_svg_to_pil(svg, size=224)
            if rendered is None:
                results.append({"prompt": prompt, "clip": 0.0, "success": False})
                continue

            rendered.save(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.png"))
            with open(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.svg"), "w") as f:
                f.write(svg)

            img_t = clip_preprocess(rendered).unsqueeze(0)
            txt_t = clip_tok([prompt])
            if torch.cuda.is_available():
                img_t, txt_t = img_t.cuda(), txt_t.cuda()
            with torch.no_grad():
                img_f = clip_model.encode_image(img_t)
                txt_f = clip_model.encode_text(txt_t)
                img_f /= img_f.norm(dim=-1, keepdim=True)
                txt_f /= txt_f.norm(dim=-1, keepdim=True)
                score = (img_f @ txt_f.T).item() * 100

            results.append({"prompt": prompt, "clip": score, "success": True})
            log.info(f"  [{i+1}/{n_samples}] CLIP={score:.2f}  {prompt[:50]}")
            _gdrive_upload(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.png"))
            _gdrive_upload(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.svg"))
        except Exception as e:
            log.error(f"  Eval error for '{prompt}': {e}")
            results.append({"prompt": prompt, "clip": 0.0, "success": False})

    del clip_model
    gc.collect()
    torch.cuda.empty_cache()

    successful = [r for r in results if r["success"]]
    scores = [r["clip"] for r in successful]
    summary = {
        "n_total": len(results), "n_success": len(successful),
        "clip_mean": float(np.mean(scores)) if scores else 0,
        "clip_median": float(np.median(scores)) if scores else 0,
        "clip_std": float(np.std(scores)) if scores else 0,
        "results": results,
    }
    eval_path = os.path.join(cfg.EVAL_DIR, "eval_summary.json")
    with open(eval_path, "w") as f:
        json.dump(summary, f, indent=2)
    if scores:
        log.info(f"Eval complete — CLIP mean={summary['clip_mean']:.2f}, median={summary['clip_median']:.2f}")
    return summary


# ════════════════════════════════════════════════════════════════════════════
# GOOGLE DRIVE — optional upload via service-account key
# Setup (one-time):
#   1. Google Cloud Console → Enable Drive API → Service Accounts → Create → download JSON key
#   2. Share your Drive folder with the service-account email (editor access)
#   3. Paste the JSON content as Kaggle secret GDRIVE_SA_KEY
#   4. Set cfg.GDRIVE_FOLDER_ID to the folder ID from the Drive URL
# ════════════════════════════════════════════════════════════════════════════
_gdrive_service = None


def _init_gdrive() -> Optional[object]:
    global _gdrive_service
    if _gdrive_service is not None:
        return _gdrive_service
    try:
        from kaggle_secrets import UserSecretsClient
        sa_key_json = UserSecretsClient().get_secret("GDRIVE_SA_KEY")
    except Exception:
        sa_key_json = os.environ.get("GDRIVE_SA_KEY", "")
    if not sa_key_json:
        return None
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds = service_account.Credentials.from_service_account_info(
            json.loads(sa_key_json),
            scopes=["https://www.googleapis.com/auth/drive"],
        )
        _gdrive_service = build("drive", "v3", credentials=creds, cache_discovery=False)
        log.info(f"Google Drive ready → folder {cfg.GDRIVE_FOLDER_ID or 'root'}")
        return _gdrive_service
    except Exception as e:
        log.warning(f"Drive init failed ({e}) — uploads disabled.")
        return None


def _gdrive_upload(local_path: str, remote_name: str = None):
    """Upload a file to Google Drive. Silently skips if Drive is not configured."""
    lp = Path(local_path)
    if not lp.exists():
        return
    svc = _init_gdrive()
    if svc is None:
        return
    try:
        from googleapiclient.http import MediaFileUpload
        name = remote_name or lp.name
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
        log.info(f"Drive ↑ {name}  ({lp.stat().st_size/1024:.0f} KB)")
    except Exception as e:
        log.warning(f"Drive upload failed for {lp.name}: {e}")


from transformers import TrainerCallback

class GDriveCheckpointCallback(TrainerCallback):
    """Zip and upload each saved checkpoint to Google Drive."""
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


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    # Clear any GPU memory pinned by a previous crashed run.
    sys.last_traceback = None
    sys.last_value = None
    sys.last_type = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

    if not torch.cuda.is_available():
        log.warning("No GPU detected! Kaggle: Settings → Accelerator → GPU T4 x2.")
    else:
        free_gb  = torch.cuda.mem_get_info()[0] / 1e9
        total_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        log.info(f"GPU: {torch.cuda.get_device_name(0)}  "
                 f"VRAM: {total_gb:.1f} GB total, {free_gb:.1f} GB free")
        if free_gb < total_gb * 0.5:
            log.warning(
                f"Only {free_gb:.1f} GB free of {total_gb:.1f} GB. "
                "If training OOMs: Session → Restart & Run All."
            )

    if not cfg.HF_TOKEN.startswith("hf_"):
        raise RuntimeError(
            "HF_TOKEN not set. "
            "Kaggle: Add-ons → Secrets → add HF_TOKEN (with internet ON)."
        )

    _log_disk_space()

    results_path = find_results_json()
    bad_prompts  = mine_failures(results_path)
    log.info(f"Training on {len(bad_prompts)} prompts + {len(SVGJS_SEED_PAIRS)} seed pairs.")

    raw_dataset      = generate_dataset(bad_prompts)
    filtered_dataset = vlm_quality_gate(raw_dataset)

    dataset_path = os.path.join(cfg.OUTPUT_DIR, "training_pairs.json")
    Path(cfg.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    with open(dataset_path, "w") as f:
        json.dump(filtered_dataset, f, indent=2)
    log.info(f"Saved {len(filtered_dataset)} training pairs → {dataset_path}")
    _gdrive_upload(dataset_path)

    if not filtered_dataset:
        log.error("No training data after quality gate. Aborting.")
        return

    model, tokenizer = train_lora(filtered_dataset)
    if model is None:
        return

    eval_summary = evaluate_pipeline(model, tokenizer, bad_prompts, n_samples=20)
    eval_path = os.path.join(cfg.EVAL_DIR, "eval_summary.json")
    _gdrive_upload(eval_path)

    adapter_dir = os.path.join(cfg.LORA_OUTPUT_DIR, "final_adapter")
    if Path(adapter_dir).exists():
        archive = shutil.make_archive(
            os.path.join(cfg.WORKING_DIR, "diffusvg_lora"), "zip", adapter_dir
        )
        log.info(f"Done. Adapter → {archive}")
        _gdrive_upload(archive)
    else:
        log.warning("No adapter found to export.")

    log.info("Pipeline complete.")


def _log_disk_space():
    total, used, free = shutil.disk_usage(cfg.WORKING_DIR)
    log.info(f"Disk: {free/1e9:.1f} GB free / {total/1e9:.1f} GB total  (used {used/1e9:.1f} GB)")


if __name__ == "__main__":
    main()
