# -*- coding: utf-8 -*-
"""
DiffuSVG_Pipeline_v3.py — SVG.js JavaScript Output Pipeline
Kaggle T4 GPU (16 GB VRAM / 30 GB RAM)

Key changes over v2:
  1. Model outputs SVG.js JavaScript code instead of raw SVG
  2. System prompt teaches the SVG.js v3.2 API (primitives + path)
  3. Curated seed pairs using circle/rect/ellipse/polygon primitives
  4. svg_to_svgjs() converts vtracer SVG → canvas.path() JS calls
  5. svgjs_to_svg() converts JS code back to SVG for rendering/eval
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DiffuSVG")


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
    return "YOUR_HF_TOKEN"


# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
class Config:
    HF_TOKEN: str         = _get_hf_token()
    RESULTS_JSON: str      = "/kaggle/input/datasets/ayushdebnath0123/result/results.json"
    WORKING_DIR: str       = "/kaggle/working"
    OUTPUT_DIR: str        = "/kaggle/working/dataset"
    LORA_OUTPUT_DIR: str   = "/kaggle/working/qwen2vl_svg_lora"
    EVAL_DIR: str          = "/kaggle/working/eval_results"

    CLIP_THRESHOLD: float  = 24.0
    DINO_THRESHOLD: float  = 0.35

    SD_MODEL: str          = "black-forest-labs/FLUX.1-schnell"
    SD_STEPS: int          = 4
    SD_GUIDANCE: float     = 0.0
    SD_STYLE_PREFIX: str   = "minimalist flat vector app icon, solid colors, geometric, white background, "

    VEC_RESOLUTION: int    = 512
    VEC_COLOR_PRECISION: int = 6
    VEC_FILTER_SPECKLE: int = 4
    VEC_CORNER_THRESHOLD: int = 60
    SVG_MIN_PATHS: int     = 1
    SVG_MAX_PATHS: int     = 500

    # VLM — outputs SVG.js JavaScript code
    VLM_MODEL: str         = "Qwen/Qwen2-VL-7B-Instruct"

    MAX_SEQ_LEN: int       = 1024
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


cfg = Config()
os.environ["HF_TOKEN"] = cfg.HF_TOKEN
log.info(f"HF_TOKEN set: {'OK' if cfg.HF_TOKEN.startswith('hf_') else 'MISSING'}")


# ════════════════════════════════════════════════════════════════════════════
# SVG.js SYSTEM PROMPT — teaches the model the SVG.js v3.2 API
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
  .stroke({color:'#hex', width:N})  — stroke
  .opacity(0-1)                     — opacity
  .radius(r) or .radius(rx, ry)    — rounded corners (rect)

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
# CURATED SEED PAIRS — primitive-based SVG.js examples
# These supplement the path-only data from vtracer so the model learns
# to use .circle(), .rect(), .ellipse(), .polygon(), .line() etc.
# ════════════════════════════════════════════════════════════════════════════
SVGJS_SEED_PAIRS = [
    # ── Simple shapes ──
    ("a blue circle",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.circle(120).center(100,100).fill('#1565C0');"),

    ("a red square",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.rect(120,120).move(40,40).fill('#D32F2F');"),

    ("a green triangle",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "canvas.polygon('100,30 170,170 30,170').fill('#2E7D32');"),

    # ── Nature ──
    ("a yellow sun",
     "canvas.rect(200,200).fill('#87CEEB');\n"
     "canvas.circle(80).center(100,100).fill('#FFD700');\n"
     "for(let i=0;i<12;i++){const a=i*Math.PI/6;\n"
     "canvas.line(100,100,100+70*Math.cos(a),100+70*Math.sin(a))"
     ".stroke({color:'#FFD700',width:4});}"),

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
     "const colors=['#F44336','#FF9800','#FFEB3B','#4CAF50','#2196F3','#673AB7'];\n"
     "for(let i=0;i<6;i++){\n"
     "  canvas.circle(180-i*20).center(100,170).fill('none')"
     ".stroke({color:colors[i],width:10});\n"
     "}"),

    ("a pink flower",
     "canvas.rect(200,200).fill('#ffffff');\n"
     "for(let i=0;i<6;i++){const a=i*Math.PI/3;\n"
     "canvas.ellipse(40,25).center(100+35*Math.cos(a),100+35*Math.sin(a))"
     ".fill('#E91E63').rotate(a*180/Math.PI,100,100);}\n"
     "canvas.circle(30).center(100,100).fill('#FFC107');"),

    ("a snowman",
     "canvas.rect(200,200).fill('#E3F2FD');\n"
     "canvas.circle(80).center(100,150).fill('#FAFAFA').stroke({color:'#ccc',width:1});\n"
     "canvas.circle(60).center(100,95).fill('#FAFAFA').stroke({color:'#ccc',width:1});\n"
     "canvas.circle(40).center(100,55).fill('#FAFAFA').stroke({color:'#ccc',width:1});\n"
     "canvas.circle(6).center(92,50).fill('#212121');\n"
     "canvas.circle(6).center(108,50).fill('#212121');\n"
     "canvas.polygon('100,57 95,65 105,65').fill('#FF6F00');"),

    # ── Objects / Icons ──
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
     "let pts=[];\n"
     "for(let i=0;i<5;i++){const a=i*Math.PI*2/5-Math.PI/2;\n"
     "pts.push((100+70*Math.cos(a))+','+(100+70*Math.sin(a)));\n"
     "const b=a+Math.PI/5;\n"
     "pts.push((100+30*Math.cos(b))+','+(100+30*Math.sin(b)));}\n"
     "canvas.polygon(pts.join(' ')).fill('#FDD835');"),

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
]


# ════════════════════════════════════════════════════════════════════════════
# SVG ↔ SVG.js CONVERTERS
# ════════════════════════════════════════════════════════════════════════════
def svg_to_svgjs(svg_str: str) -> str:
    """Convert raw SVG (from vtracer) to SVG.js JavaScript code.
    vtracer only emits <path> elements, so we parse those into
    canvas.path('...').fill('#hex'); calls."""
    lines = ["canvas.rect(200,200).fill('#ffffff');"]

    # Extract all <path ... /> elements
    for m in re.finditer(
        r'<path\s+d="([^"]+)"[^>]*?fill="([^"]*)"[^>]*/?>',
        svg_str
    ):
        d_attr = m.group(1).strip()
        fill = m.group(2).strip() or '#000000'
        lines.append(f"canvas.path('{d_attr}').fill('{fill}');")

    if len(lines) == 1:
        # Fallback: try alternate attribute order (fill before d)
        for m in re.finditer(
            r'<path[^>]*?fill="([^"]*)"[^>]*?d="([^"]+)"[^>]*/?>',
            svg_str
        ):
            fill = m.group(1).strip() or '#000000'
            d_attr = m.group(2).strip()
            lines.append(f"canvas.path('{d_attr}').fill('{fill}');")

    return "\n".join(lines)


def svgjs_to_svg(js_code: str) -> str:
    """Convert SVG.js JavaScript code back to an SVG string for rendering.
    Regex-parses common canvas.* calls into SVG elements."""
    elements = []

    # canvas.rect(w,h).move(x,y).fill('#hex')...
    for m in re.finditer(
        r"canvas\.rect\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)"
        r"(?:\.move\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\))?"
        r"(?:\.center\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\))?"
        r"[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)",
        js_code
    ):
        w, h = m.group(1), m.group(2)
        fill = m.group(7)
        if m.group(3) and m.group(4):  # .move()
            x, y = m.group(3), m.group(4)
        elif m.group(5) and m.group(6):  # .center()
            x = str(float(m.group(5)) - float(w)/2)
            y = str(float(m.group(6)) - float(h)/2)
        else:
            x, y = "0", "0"
        # Check for .radius()
        radius_m = re.search(r"\.radius\(\s*(\d+(?:\.\d+)?)\s*\)", m.group(0))
        rx = radius_m.group(1) if radius_m else "0"
        elements.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"/>')

    # canvas.circle(d).center(cx,cy).fill('#hex')
    for m in re.finditer(
        r"canvas\.circle\(\s*(\d+(?:\.\d+)?)\s*\)"
        r"(?:\.center\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\))?"
        r"[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)",
        js_code
    ):
        d = float(m.group(1))
        cx = m.group(2) or str(d/2)
        cy = m.group(3) or str(d/2)
        fill = m.group(4)
        elements.append(f'<circle cx="{cx}" cy="{cy}" r="{d/2}" fill="{fill}"/>')

    # canvas.ellipse(w,h).center(cx,cy).fill('#hex')
    for m in re.finditer(
        r"canvas\.ellipse\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)"
        r"(?:\.center\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\))?"
        r"[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)",
        js_code
    ):
        w, h = float(m.group(1)), float(m.group(2))
        cx = m.group(3) or str(w/2)
        cy = m.group(4) or str(h/2)
        fill = m.group(5)
        elements.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" fill="{fill}"/>')

    # canvas.polygon('...').fill('#hex')
    for m in re.finditer(
        r"canvas\.polygon\(['\"]([^'\"]+)['\"]\)"
        r"[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)",
        js_code
    ):
        pts = m.group(1).replace(",", " ").strip()
        # Convert "x1,y1 x2,y2" → "x1 y1 x2 y2" and back to proper pairs
        fill = m.group(2)
        elements.append(f'<polygon points="{m.group(1)}" fill="{fill}"/>')

    # canvas.path('...').fill('#hex')
    for m in re.finditer(
        r"canvas\.path\(['\"]([^'\"]+)['\"]\)"
        r"[^;]*?\.fill\(['\"]([^'\"]+)['\"]\)",
        js_code
    ):
        d = m.group(1)
        fill = m.group(2)
        elements.append(f'<path d="{d}" fill="{fill}"/>')

    # canvas.line(x1,y1,x2,y2).stroke({color:'#hex',width:N})
    for m in re.finditer(
        r"canvas\.line\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,"
        r"\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)"
        r"[^;]*?\.stroke\(\{[^}]*color:\s*['\"]([^'\"]+)['\"][^}]*width:\s*(\d+(?:\.\d+)?)",
        js_code
    ):
        x1, y1, x2, y2 = m.group(1), m.group(2), m.group(3), m.group(4)
        color, width = m.group(5), m.group(6)
        elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')

    # canvas.path('...').fill('none').stroke({color:'#hex',width:N})
    for m in re.finditer(
        r"canvas\.path\(['\"]([^'\"]+)['\"]\)"
        r"[^;]*?\.fill\(['\"]none['\"]\)"
        r"[^;]*?\.stroke\(\{[^}]*color:\s*['\"]([^'\"]+)['\"][^}]*width:\s*(\d+(?:\.\d+)?)",
        js_code
    ):
        d = m.group(1)
        color, width = m.group(2), m.group(3)
        elements.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"/>')

    body = "\n".join(elements)
    return f'<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n{body}\n</svg>'


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
        resolution: int = 512,
        color_precision: int = 6,
        filter_speckle: int = 4,
        corner_threshold: int = 60,
    ):
        self.resolution = resolution
        self.color_precision = color_precision
        self.filter_speckle = filter_speckle
        self.corner_threshold = corner_threshold

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
            return self._normalize_and_minify(svg)
        except Exception as e:
            log.warning(f"vtracer failed: {e}")
            return None

    @staticmethod
    def _normalize_and_minify(svg: str) -> str:
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
# STEP 4 — Generate (prompt, SVG.js code) pairs via FLUX.1 + vtracer + convert
# ════════════════════════════════════════════════════════════════════════════
def generate_dataset(prompts: list[str]) -> list[dict]:
    """Text Prompt → FLUX.1-schnell → Image → vtracer → SVG → svg_to_svgjs → JS code.
    Also prepends curated SVGJS_SEED_PAIRS that use primitives."""
    from diffusers import FluxPipeline

    Path(cfg.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    img_dir = Path(cfg.OUTPUT_DIR) / "images"
    img_dir.mkdir(exist_ok=True)

    log.info("Loading FLUX.1-schnell …")
    pipe = FluxPipeline.from_pretrained(
        cfg.SD_MODEL, torch_dtype=torch.bfloat16, token=cfg.HF_TOKEN,
    )
    pipe.enable_sequential_cpu_offload()
    pipe.vae.enable_slicing()
    pipe.vae.enable_tiling()

    vec = Vectorizer(
        resolution=cfg.VEC_RESOLUTION,
        color_precision=cfg.VEC_COLOR_PRECISION,
        filter_speckle=cfg.VEC_FILTER_SPECKLE,
        corner_threshold=cfg.VEC_CORNER_THRESHOLD,
    )

    dataset = []
    for i, prompt in enumerate(prompts):
        try:
            torch.cuda.empty_cache()
            img = pipe(
                cfg.SD_STYLE_PREFIX + prompt,
                num_inference_steps=cfg.SD_STEPS,
                guidance_scale=cfg.SD_GUIDANCE,
                width=256, height=256,
            ).images[0]

            img_path = str(img_dir / f"{i:05d}.png")
            img.save(img_path)

            # Vectorize → SVG → SVG.js code
            svg = vec.vectorize(img)
            if Vectorizer.is_valid(svg, cfg.SVG_MIN_PATHS, cfg.SVG_MAX_PATHS):
                svgjs_code = svg_to_svgjs(svg)
                dataset.append({
                    "prompt": prompt,
                    "svg": svg,          # keep raw SVG for quality gate rendering
                    "svgjs": svgjs_code,  # JS code is the training target
                    "image_path": img_path,
                })
                log.info(f"[{i+1}/{len(prompts)}] ✓  {prompt[:60]}")
            else:
                log.warning(f"[{i+1}/{len(prompts)}] ✗  invalid SVG for: {prompt[:60]}")
        except Exception as e:
            log.error(f"[{i+1}/{len(prompts)}] error: {e}")

    del pipe
    gc.collect()
    torch.cuda.empty_cache()

    # ── Prepend curated seed pairs (primitives) ──
    seed_items = []
    for prompt_text, js_code in SVGJS_SEED_PAIRS:
        seed_items.append({
            "prompt": prompt_text,
            "svg": svgjs_to_svg(js_code),  # reconstruct SVG for quality gate
            "svgjs": js_code,
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
    Seed pairs are always kept (skip gate)."""
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
    import base64

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
        # Always keep seed pairs
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
    log.info(f"VLM gate: kept {len(filtered)}/{len(dataset)} samples.")
    return filtered


# ════════════════════════════════════════════════════════════════════════════
# STEP 6 — Fine-tune Qwen2-VL with QLoRA  (Text Prompt → SVG.js code)
# ════════════════════════════════════════════════════════════════════════════
def build_chat_pair(prompt: str, svgjs_code: str, tokenizer) -> str:
    """Format as Qwen2-VL chat: system=_SVGJS_SYSTEM, user=prompt, assistant=JS code."""
    messages = [
        {"role": "system", "content": _SVGJS_SYSTEM},
        {"role": "user", "content": f"Generate SVG.js code for: {prompt}"},
        {"role": "assistant", "content": svgjs_code},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False)


class SVGCausalDataset(torch.utils.data.Dataset):
    """Tokenise chat-formatted (prompt → SVG.js code) pairs for causal LM training."""

    def __init__(self, data: list[dict], tokenizer, max_len: int):
        self.samples = []
        skipped = 0

        for item in data:
            full_text = build_chat_pair(item["prompt"], item["svgjs"], tokenizer)

            toks = tokenizer(
                full_text, truncation=True, max_length=max_len,
                padding="max_length", return_tensors="pt",
            )
            input_ids = toks["input_ids"].squeeze()
            attn_mask = toks["attention_mask"].squeeze()

            # Build prompt-only portion to find where assistant response starts
            prompt_messages = [
                {"role": "system", "content": _SVGJS_SYSTEM},
                {"role": "user", "content": f"Generate SVG.js code for: {item['prompt']}"},
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

        log.info(f"Dataset: {len(self.samples)} usable, {skipped} skipped (code too long).")

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
        full = build_chat_pair(item["prompt"], item["svgjs"], tokenizer)
        sample_lens.append(len(tokenizer.encode(full)))
    log.info(f"Sample token lengths (first 10): {sample_lens}")
    log.info(f"Max: {max(sample_lens)}, Mean: {np.mean(sample_lens):.0f}")

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
        log.error("No usable training samples! Check SVG.js code lengths vs MAX_SEQ_LEN.")
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
    )

    log.info(f"Starting training: {len(train_ds)} train, {len(val_ds) if val_ds else 0} val")
    trainer.train()

    adapter_dir = os.path.join(cfg.LORA_OUTPUT_DIR, "final_adapter")
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    log.info(f"Adapter saved → {adapter_dir}")
    return model, tokenizer


# ════════════════════════════════════════════════════════════════════════════
# STEP 7 — Inference: Text Prompt → Qwen2-VL → SVG.js code → SVG
# ════════════════════════════════════════════════════════════════════════════
@torch.inference_mode()
def generate_svg(prompt: str, model, tokenizer, max_new_tokens: int = 1500) -> str:
    """Run the fine-tuned model to produce SVG.js code, then convert to SVG."""
    messages = [
        {"role": "system", "content": _SVGJS_SYSTEM},
        {"role": "user", "content": f"Generate SVG.js code for: {prompt}"},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    out = model.generate(
        **inputs, max_new_tokens=max_new_tokens,
        do_sample=True, temperature=0.7, top_p=0.9, repetition_penalty=1.1,
    )
    response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    # The response should be SVG.js JavaScript code — convert to SVG for rendering
    js_code = response.strip()
    # Strip markdown fences if the model accidentally adds them
    js_code = re.sub(r"^```(?:javascript|js)?\s*\n?", "", js_code)
    js_code = re.sub(r"\n?```\s*$", "", js_code)

    svg_str = svgjs_to_svg(js_code)
    return svg_str


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


def main():
    if not torch.cuda.is_available():
        log.warning("No GPU detected! On Kaggle: Settings → Accelerator → GPU T4 x2.")
    else:
        log.info(f"GPU: {torch.cuda.get_device_name(0)}  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        log.info(f"Visible GPUs: {torch.cuda.device_count()} (forced to 1 for QLoRA compatibility)")

    if not cfg.HF_TOKEN.startswith("hf_"):
        raise RuntimeError("HF_TOKEN not set. Add it in Kaggle: Add-ons → Secrets → 'HF_TOKEN'.")

    # Step 3: Find failure prompts
    results_path = find_results_json()
    bad_prompts = mine_failures(results_path)
    log.info(f"Training on {len(bad_prompts)} prompts (+ {len(SVGJS_SEED_PAIRS)} seed pairs).")

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

    if len(filtered_dataset) == 0:
        log.error("No training data after quality gate. Aborting.")
        return

    # Step 6: Fine-tune
    model, tokenizer = train_lora(filtered_dataset)

    # Step 8: Evaluate
    if model is not None:
        evaluate_pipeline(model, tokenizer, bad_prompts, n_samples=20)

    # Step 9: Package
    adapter_dir = os.path.join(cfg.LORA_OUTPUT_DIR, "final_adapter")
    if Path(adapter_dir).exists():
        archive = shutil.make_archive(
            os.path.join(cfg.WORKING_DIR, "diffusvg_lora_v3"), "zip", adapter_dir
        )
        log.info(f"Pipeline complete. Adapter archive → {archive}")
    else:
        log.warning("No adapter found to export.")

    log.info("Done.")


if __name__ == "__main__":
    main()
