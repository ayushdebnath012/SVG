# -*- coding: utf-8 -*-
"""
DiffuSVG_Pipeline_v5.py — Complex Prompt + Flux Image + Clean SVG Pipeline
Runs on Kaggle T4 GPU  OR  Google Colab T4 GPU.

Key changes over v4:
  1. Complex prompt generation via Gemini API (with fallback bank)
  2. Multiple complexity levels (simple/medium/complex)
  3. Dual VLM quality gate: Gemini Vision or Qwen2-VL-7B
  4. Tuned vtracer sparsity controls for non-dense SVGs
"""

import subprocess, shutil, sys, os, gc, json, logging, re, io, random, tempfile
from pathlib import Path
from typing import Optional, List, Tuple

import torch
import numpy as np
from PIL import Image

os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"


# ── Detect runtime environment ───────────────────────────────────────────────
def _detect_env() -> str:
    # Check Kaggle FIRST (filesystem check is more reliable)
    if Path("/kaggle").exists():
        return "kaggle"
    try:
        import google.colab
        return "colab"
    except ImportError:
        pass
    return "local"

_ENV = _detect_env()
_HF_CACHE = {
    "kaggle": "/kaggle/working/hf_cache",
    "colab": "/content/hf_cache",
    "local": "/tmp/hf_cache",
}[_ENV]
os.makedirs(_HF_CACHE, exist_ok=True)
os.environ["HF_HUB_CACHE"] = _HF_CACHE
os.environ["HUGGINGFACE_HUB_CACHE"] = _HF_CACHE
os.environ["TRANSFORMERS_CACHE"] = _HF_CACHE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DiffuSVG")
log.info(f"Runtime environment: {_ENV}")


# ════════════════════════════════════════════════════════════════════════════
# TOKEN HELPERS
# ════════════════════════════════════════════════════════════════════════════
def _get_secret(name: str) -> str:
    """Try env var, Kaggle secrets, Colab secrets."""
    val = os.environ.get(name, "")
    if val:
        return val
    try:
        from kaggle_secrets import UserSecretsClient
        val = UserSecretsClient().get_secret(name)
        if val:
            log.info(f"{name} loaded from Kaggle Secrets.")
            return val
    except Exception:
        pass
    try:
        from google.colab import userdata
        val = userdata.get(name)
        if val:
            log.info(f"{name} loaded from Colab Secrets.")
            return val
    except Exception:
        pass
    return ""


# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
class Config:
    HF_TOKEN: str          = _get_secret("HF_TOKEN") or "YOUR_HF_TOKEN"
    GEMINI_API_KEY: str    = _get_secret("GEMINI_API_KEY")

    _base: str             = "/content" if _ENV == "colab" else "/kaggle/working"
    RESULTS_JSON: str      = "/kaggle/input/datasets/ayushdebnath0123/result/results.json"
    WORKING_DIR: str       = _base
    OUTPUT_DIR: str        = _base + "/dataset"
    LORA_OUTPUT_DIR: str   = _base + "/qwen2vl_svg_lora"
    EVAL_DIR: str          = _base + "/eval_results"

    # Scoring thresholds
    CLIP_THRESHOLD: float  = 24.0
    DINO_THRESHOLD: float  = 0.35

    # Flux config
    SD_MODEL: str          = "black-forest-labs/FLUX.1-schnell"
    SD_STEPS: int          = 4
    SD_GUIDANCE: float     = 0.0
    SD_STYLE_PREFIX: str   = "minimalist flat vector app icon, solid colors, geometric, white background, "

    # Vectorizer config — tuned for sparse, clean SVGs
    VEC_RESOLUTION: int    = 256
    VEC_COLOR_PRECISION: int = 6
    VEC_FILTER_SPECKLE: int = 8
    VEC_CORNER_THRESHOLD: int = 60
    SVG_MIN_PATHS: int     = 1
    SVG_MAX_PATHS: int     = 30

    # Gemini config
    GEMINI_MODEL: str      = "gemini-2.0-flash"
    PROMPTS_PER_SEED: int  = 3
    COMPLEXITY_LEVELS: list = ["simple", "medium", "complex"]

    # VLM config
    VLM_BACKEND: str       = "gemini"   # "gemini" or "qwen"
    VLM_MODEL: str         = "Qwen/Qwen2-VL-7B-Instruct"

    # Training config
    MAX_SEQ_LEN: int       = 1536
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
    GDRIVE_FOLDER_ID: str  = ""


cfg = Config()
os.environ["HF_TOKEN"] = cfg.HF_TOKEN
log.info(f"HF_TOKEN: {'OK' if cfg.HF_TOKEN.startswith('hf_') else 'MISSING'}")
log.info(f"GEMINI_API_KEY: {'OK' if cfg.GEMINI_API_KEY else 'MISSING (will use fallback prompts)'}")


# ════════════════════════════════════════════════════════════════════════════
# COMPLEX PROMPT GENERATION via Gemini
# ════════════════════════════════════════════════════════════════════════════

_PROMPT_META = """\
You are a prompt engineer for SVG icon generation.
Given a short concept, generate {n} detailed prompts for a text-to-image model.

Each prompt should describe a FLAT VECTOR icon with:
- Solid, vibrant colors (no gradients, no shadows, no textures)
- Clean geometric shapes (circles, rectangles, triangles, polygons)
- White or solid-color background
- Minimal detail — suitable for vectorization into <30 SVG elements
- Specific colors mentioned (e.g., "bright red", "sky blue", "forest green")

Complexity level: {level}
- simple: 3-5 distinct visual elements, very basic shapes
- medium: 5-15 elements, recognizable object with some details
- complex: 15-30 elements, detailed scene or multi-part object

Concept: "{seed}"

Output ONLY the prompts, one per line. No numbering, no explanation.\
"""

# ── Fallback prompt bank (used when Gemini API is unavailable) ────────────
FALLBACK_COMPLEX_PROMPTS = [
    # Simple
    "a bright red circle centered on a white background, flat vector style",
    "a sky blue square with rounded corners on white background, minimalist icon",
    "a forest green equilateral triangle on a white background, solid fill, no outline",
    "a golden yellow five-pointed star on white background, flat geometric style",
    "a coral pink heart shape centered on white, solid color, no gradient",
    "a deep purple crescent moon on a dark navy background, flat vector",
    "an orange diamond shape rotated 45 degrees on white background",
    "a turquoise oval on white background, simple flat icon",

    # Medium — Nature
    "a bright yellow sun with 8 orange rays on a light blue sky background, flat vector icon",
    "a green pine tree with a brown trunk on white background, geometric triangles, minimalist",
    "a red apple with a short brown stem and a small green leaf, white background, flat vector",
    "a pink cherry blossom flower with 5 petals and a yellow center, white background, solid colors",
    "a white snowman with three stacked circles, orange carrot nose, black dot eyes, light blue background",
    "a rainbow arc with six colored bands over a white background, flat geometric style",
    "a brown acorn with a darker brown cap on white background, simple flat illustration",
    "a blue raindrop shape with a white highlight on light gray background, minimalist icon",
    "a red mushroom with white spots and a tan stem, green grass at base, white background",
    "a bright orange autumn leaf with visible veins, white background, flat vector art",

    # Medium — Objects
    "a red coffee mug with steam wisps on white background, flat vector, solid colors",
    "a yellow light bulb with rays emanating outward, white background, minimalist icon style",
    "a blue padlock icon, locked position, metallic blue body, dark blue shackle, white background",
    "a green battery icon at 75% charge with a white lightning bolt, flat vector style",
    "a purple headphones icon with a thick band and round ear cups, white background, flat design",
    "an orange megaphone with sound waves, white background, geometric flat vector",
    "a red fire extinguisher with black nozzle on white background, flat icon style",
    "a blue compass with red north needle on white background, minimalist geometric design",
    "a yellow school bus from the side, white background, flat geometric shapes, minimal detail",
    "a green recycling symbol with three chasing arrows on white background, flat vector icon",

    # Medium — Animals
    "a orange cat face with pointed ears, green eyes, pink nose, white background, flat vector",
    "a gray elephant face with large ears, small eyes, long trunk, white background, minimalist",
    "a yellow rubber duck floating on blue water, white background, flat geometric illustration",
    "a brown owl with large yellow eyes perched on a branch, white background, flat vector art",
    "a red ladybug with black spots on a green leaf, white background, simple flat illustration",
    "a blue whale with a water spout, light blue ocean background, flat minimalist design",
    "a green frog face with big white eyes and a wide smile, white background, flat vector",
    "a pink flamingo standing on one leg, white background, geometric flat illustration",
    "a black and white panda face with round ears, white background, minimalist flat vector",
    "a golden fish swimming right with small bubbles, light blue background, flat icon style",

    # Medium — Icons / UI
    "a blue and white Wi-Fi signal icon with three arcs and a dot, white background, flat design",
    "a red notification bell with a small yellow dot, white background, flat vector icon",
    "a green checkmark inside a circle on white background, flat UI icon style",
    "a blue download arrow pointing down into a tray, white background, minimalist icon",
    "a purple microphone icon with sound waves, white background, flat geometric design",
    "an orange warning triangle with a black exclamation mark, white background, flat vector",
    "a red map pin with a white circle center, white background, flat location icon",
    "a blue camera icon with a round lens and flash, white background, minimalist flat design",
    "a green shopping cart with two wheels and handle, white background, flat e-commerce icon",
    "a yellow folder icon slightly open with documents peeking out, white background, flat vector",

    # Complex
    "a lighthouse on rocky shore with red and white stripes, yellow light beam, dark blue sky with stars, flat vector",
    "a hot air balloon with multicolored vertical stripes floating over green rolling hills, blue sky, flat illustration",
    "a colorful tropical fish tank with 3 fish, green seaweed, sandy bottom, blue water, flat geometric style",
    "a cozy house with red roof, yellow walls, green door, two blue windows, chimney with smoke, white picket fence, flat vector",
    "a space rocket launching with orange flames, dark purple starry sky, crescent moon, flat minimalist illustration",
    "a kitchen scene with a blue stove, red pot, yellow cutting board, green vegetables, white background, flat vector",
    "a winter village with 3 houses, snowy roofs, pine trees, snowflakes falling, light blue sky, flat geometric style",
    "a vintage bicycle with a brown basket of colorful flowers, red frame, green park background, flat vector art",
    "a sushi plate with 4 pieces of nigiri, chopsticks, soy sauce dish, bamboo mat, flat illustration style",
    "a music studio with a purple turntable, orange headphones, blue speakers, sound wave graphics, flat vector design",
    "a garden scene with red roses, yellow sunflowers, green stems, brown wooden fence, blue sky, flat minimalist",
    "a pizza with pepperoni, green peppers, yellow cheese, on a wooden board, white background, flat vector illustration",
    "a campfire scene with orange flames, brown logs, gray stones in a circle, dark blue sky with stars, flat design",
    "a desk workspace with a blue laptop, white coffee cup, green plant, yellow lamp, flat vector overhead view",
    "a farm scene with a red barn, white fence, green field, yellow hay bales, blue sky with one white cloud, flat art",
]

# ── Seed prompts for prompt expansion ─────────────────────────────────────
DEFAULT_SEED_PROMPTS = [
    "a cat", "a dog", "a house", "a car", "a tree", "a flower", "a sun",
    "a moon", "a star", "a heart", "a fish", "a bird", "a rocket",
    "a book", "a clock", "a key", "a crown", "a shield", "a sword",
    "a camera", "a phone", "a guitar", "a piano", "a cake", "a pizza",
    "a robot", "a ship", "a train", "a bicycle", "a butterfly",
    "a mushroom", "a mountain", "a lighthouse", "a castle", "a bridge",
    "a snowflake", "a raindrop", "a tornado", "an umbrella", "a tent",
    "a whale", "a dolphin", "a penguin", "a panda", "a cactus",
    "a compass", "a trophy", "a diamond", "a skull", "a globe",
]


def generate_complex_prompts(
    seeds: List[str] = None,
    use_fallback: bool = False,
) -> List[dict]:
    """Generate complex prompts from seed concepts via Gemini API.

    Returns list of dicts: {seed, prompt, complexity}

    Falls back to built-in bank if Gemini API is unavailable.
    """
    if seeds is None:
        seeds = DEFAULT_SEED_PROMPTS

    if use_fallback or not cfg.GEMINI_API_KEY:
        log.info(f"Using fallback prompt bank ({len(FALLBACK_COMPLEX_PROMPTS)} prompts).")
        results = []
        for i, p in enumerate(FALLBACK_COMPLEX_PROMPTS):
            complexity = "simple" if i < 8 else ("medium" if i < 50 else "complex")
            results.append({"seed": "fallback", "prompt": p, "complexity": complexity})
        return results

    try:
        import google.generativeai as genai
        genai.configure(api_key=cfg.GEMINI_API_KEY)
        model = genai.GenerativeModel(cfg.GEMINI_MODEL)
    except Exception as e:
        log.warning(f"Gemini init failed: {e} — using fallback prompts.")
        return generate_complex_prompts(seeds, use_fallback=True)

    results = []
    for seed in seeds:
        for level in cfg.COMPLEXITY_LEVELS:
            try:
                meta = _PROMPT_META.format(
                    n=cfg.PROMPTS_PER_SEED, level=level, seed=seed
                )
                response = model.generate_content(meta)
                lines = [
                    l.strip() for l in response.text.strip().split("\n")
                    if l.strip() and not l.strip().startswith("#")
                ]
                for line in lines[:cfg.PROMPTS_PER_SEED]:
                    results.append({
                        "seed": seed,
                        "prompt": line,
                        "complexity": level,
                    })
                log.info(f"  Gemini: {seed} / {level} → {len(lines)} prompts")
            except Exception as e:
                log.warning(f"  Gemini failed for '{seed}' / {level}: {e}")

    if not results:
        log.warning("Gemini produced no prompts — falling back to built-in bank.")
        return generate_complex_prompts(seeds, use_fallback=True)

    log.info(f"Generated {len(results)} complex prompts via Gemini.")
    return results


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
# CURATED SEED PAIRS — primitive-based SVG examples (same as v4)
# ════════════════════════════════════════════════════════════════════════════
SVG_SEED_PAIRS = [
    ("a blue circle",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="60" fill="#1565C0"/>'),
    ("a red square",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<rect x="40" y="40" width="120" height="120" fill="#D32F2F"/>'),
    ("a green triangle",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<polygon points="100,30 170,170 30,170" fill="#2E7D32"/>'),
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
    ("a smiley face",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="80" fill="#FDD835"/>\n'
     '<circle cx="72" cy="82" r="9" fill="#212121"/>\n'
     '<circle cx="128" cy="82" r="9" fill="#212121"/>\n'
     '<path d="M 65 115 Q 100 155 135 115" fill="none" stroke="#212121" stroke-width="5"/>'),
    ("a target",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="80" fill="#F44336"/>\n'
     '<circle cx="100" cy="100" r="60" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="40" fill="#F44336"/>\n'
     '<circle cx="100" cy="100" r="20" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="7" fill="#F44336"/>'),
    ("a snowman",
     '<rect width="200" height="200" fill="#E3F2FD"/>\n'
     '<circle cx="100" cy="150" r="40" fill="#FAFAFA" stroke="#ccc" stroke-width="1"/>\n'
     '<circle cx="100" cy="95" r="30" fill="#FAFAFA" stroke="#ccc" stroke-width="1"/>\n'
     '<circle cx="100" cy="55" r="20" fill="#FAFAFA" stroke="#ccc" stroke-width="1"/>\n'
     '<circle cx="92" cy="50" r="3" fill="#212121"/>\n'
     '<circle cx="108" cy="50" r="3" fill="#212121"/>\n'
     '<polygon points="100,57 95,65 105,65" fill="#FF6F00"/>'),
    ("a coffee cup",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<rect x="50" y="80" width="80" height="90" rx="8" fill="#795548"/>\n'
     '<path d="M 130 100 Q 155 100 155 130 Q 155 155 130 155" fill="none" stroke="#795548" stroke-width="6"/>\n'
     '<rect x="45" y="75" width="90" height="8" rx="4" fill="#5D4037"/>\n'
     '<path d="M 70 65 Q 75 40 80 65" fill="none" stroke="#bbb" stroke-width="3"/>\n'
     '<path d="M 90 60 Q 95 35 100 60" fill="none" stroke="#bbb" stroke-width="3"/>'),
    ("a rocket",
     '<rect width="200" height="200" fill="#0D1B2A"/>\n'
     '<polygon points="100,20 75,90 125,90" fill="#B0BEC5"/>\n'
     '<rect x="75" y="90" width="50" height="90" fill="#CFD8DC"/>\n'
     '<circle cx="100" cy="115" r="15" fill="#81D4FA"/>\n'
     '<polygon points="75,180 55,180 75,140" fill="#E53935"/>\n'
     '<polygon points="125,180 145,180 125,140" fill="#E53935"/>\n'
     '<polygon points="85,180 100,200 115,180" fill="#FF7043"/>'),
    ("a cat face",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="115" r="65" fill="#FFA726"/>\n'
     '<polygon points="55,80 75,28 97,80" fill="#FFA726"/>\n'
     '<polygon points="103,80 125,28 145,80" fill="#FFA726"/>\n'
     '<circle cx="75" cy="105" r="11" fill="#212121"/>\n'
     '<circle cx="125" cy="105" r="11" fill="#212121"/>\n'
     '<circle cx="100" cy="128" r="5" fill="#E91E63"/>\n'
     '<path d="M 80 142 Q 100 162 120 142" fill="none" stroke="#212121" stroke-width="3"/>'),
    ("a play button",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="80" fill="#1565C0"/>\n'
     '<polygon points="78,62 78,138 152,100" fill="#ffffff"/>'),
]


# ════════════════════════════════════════════════════════════════════════════
# IN-CONTEXT LEARNING — dynamic few-shot
# ════════════════════════════════════════════════════════════════════════════
def _select_few_shot(prompt: str, n: int = 2) -> list:
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
    examples = _select_few_shot(prompt, n=n)
    lines = ["Here are examples of SVG elements for similar prompts:\n"]
    for i, (p, svg) in enumerate(examples, 1):
        lines.append(f'Example {i} — "{p}":\n{svg}')
    lines.append(f"\nNow generate SVG elements for: {prompt}")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# INSTALL DEPENDENCIES
# ════════════════════════════════════════════════════════════════════════════
def install():
    log.info("Installing system packages …")
    subprocess.run(["apt-get", "update", "-qq"], capture_output=True)
    subprocess.run(["apt-get", "install", "-y", "-qq", "libcairo2"], capture_output=True)
    log.info("Installing Python packages …")
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q",
            "diffusers>=0.30", "transformers>=4.40", "accelerate>=0.27",
            "bitsandbytes>=0.43", "peft>=0.10", "trl>=0.8",
            "cairosvg", "pillow", "tqdm", "sentencepiece",
            "open_clip_torch", "vtracer",
            "google-api-python-client", "google-auth",
            "google-generativeai",
        ],
        check=True,
    )
    log.info("All packages installed.")

install()


# ════════════════════════════════════════════════════════════════════════════
# VECTORIZER (Raster → vtracer → Colour SVG)
# ════════════════════════════════════════════════════════════════════════════
class Vectorizer:
    """Convert a raster PIL image to a clean, sparse colour SVG via vtracer."""

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
        svg = re.sub(r"<svg[^>]*>",
            '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">', svg, count=1)
        svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
        svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg)
        svg = re.sub(r"<!--.*?-->", "", svg, flags=re.DOTALL)
        svg = re.sub(r"\s+", " ", svg).strip()
        svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.DOTALL)
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
# SVG RENDERING HELPER
# ════════════════════════════════════════════════════════════════════════════
def render_svg_to_pil(svg_str: str, size: int = 256) -> Optional[Image.Image]:
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
    m = re.search(r"<svg[^>]*>(.*?)</svg>", svg_str, re.DOTALL)
    return m.group(1).strip() if m else svg_str.strip()


def _wrap_svg_body(body: str) -> str:
    body = body.strip()
    if body.startswith("<svg"):
        return body
    return f'<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n{body}\n</svg>'


# ════════════════════════════════════════════════════════════════════════════
# FAILURE MINING from results.json
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


def mine_failures(path: Optional[str]) -> list:
    if path is None:
        log.warning("No results.json — using fallback prompts.")
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
        log.warning("No failures in results.json — using fallback prompts.")
        return list(FALLBACK_PROMPTS)
    return bad


# ════════════════════════════════════════════════════════════════════════════
# DATASET GENERATION — Complex Prompt → Flux → vtracer → SVG
# ════════════════════════════════════════════════════════════════════════════
def generate_dataset(prompts: list) -> list:
    """Complex prompts → FLUX.1-schnell (HF Inference API) → Image → vtracer → SVG.
    Prepends curated SVG_SEED_PAIRS."""
    from huggingface_hub import InferenceClient

    Path(cfg.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    img_dir = Path(cfg.OUTPUT_DIR) / "images"
    img_dir.mkdir(exist_ok=True)

    log.info("Using FLUX.1-schnell via HF Inference API …")
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

    # Handle both plain strings and dicts from complex prompt generator
    prompt_list = []
    for p in prompts:
        if isinstance(p, dict):
            prompt_list.append(p["prompt"])
        else:
            prompt_list.append(p)

    for i, prompt in enumerate(prompt_list):
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
                svg_body = _extract_svg_body(svg)
                dataset.append({
                    "prompt": prompt,
                    "svg": svg_body,
                    "svg_full": svg,
                    "image_path": img_path,
                })
                log.info(f"[{i+1}/{len(prompt_list)}] ✓  {prompt[:60]}")
            else:
                log.warning(f"[{i+1}/{len(prompt_list)}] ✗  invalid SVG for: {prompt[:60]}")
        except Exception as e:
            if "402" in str(e):
                log.warning("HF Inference API credits depleted (402). Stopping FLUX generation.")
                api_credits_depleted = True
            else:
                log.error(f"[{i+1}/{len(prompt_list)}] error: {e}")

    # Prepend curated seed pairs
    seed_items = []
    for prompt_text, svg_body in SVG_SEED_PAIRS:
        seed_items.append({
            "prompt": prompt_text,
            "svg": svg_body,
            "svg_full": _wrap_svg_body(svg_body),
            "image_path": None,
            "is_seed": True,
        })
    dataset = seed_items + dataset
    log.info(f"Generated {len(dataset)} total samples ({len(seed_items)} seed + {len(dataset)-len(seed_items)} generated).")
    return dataset


# ════════════════════════════════════════════════════════════════════════════
# VLM QUALITY GATE — Gemini Vision or Qwen2-VL-7B
# ════════════════════════════════════════════════════════════════════════════
def _vlm_gate_gemini(item: dict) -> bool:
    """Use Gemini Vision to verify SVG ↔ prompt alignment."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=cfg.GEMINI_API_KEY)
        model = genai.GenerativeModel(cfg.GEMINI_MODEL)

        rendered = render_svg_to_pil(item["svg_full"], size=256)
        if rendered is None:
            return False

        response = model.generate_content([
            rendered,
            f'This image was generated for the prompt: "{item["prompt"]}". '
            'Does the image accurately represent the prompt? Answer only YES or NO.'
        ])
        return "YES" in response.text.upper()
    except Exception as e:
        log.warning(f"Gemini gate error: {e}")
        return True  # on error, don't discard


def vlm_quality_gate(dataset: list) -> list:
    """Filter dataset by VLM quality — uses Gemini or Qwen2-VL-7B based on config."""
    non_seed = [item for item in dataset if not item.get("is_seed")]
    if not non_seed:
        log.info("VLM quality gate: all samples are seed pairs — skipping.")
        return dataset

    if cfg.VLM_BACKEND == "gemini" and cfg.GEMINI_API_KEY:
        log.info("Running VLM quality gate with Gemini Vision …")
        filtered = []
        for item in dataset:
            if item.get("is_seed"):
                filtered.append(item)
                continue
            if _vlm_gate_gemini(item):
                filtered.append(item)
                log.info(f"  PASS: {item['prompt'][:60]}")
            else:
                log.info(f"  FAIL: {item['prompt'][:60]}")
        log.info(f"Gemini gate: kept {len(filtered)}/{len(dataset)} samples.")
        return filtered

    # Qwen2-VL-7B fallback
    log.info(f"Running VLM quality gate with {cfg.VLM_MODEL} (4-bit) …")
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
    import base64

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
                    f'This SVG image was generated for the prompt: "{item["prompt"]}". '
                    'Does the image accurately represent the prompt? Answer only YES or NO.'
                )},
            ]}]
            text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = processor(text=[text], images=[rendered], return_tensors="pt", padding=True).to(model.device)
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
# FINE-TUNE Qwen2-VL with QLoRA (Text Prompt → raw SVG)
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
            prompt_messages = [
                {"role": "system", "content": _SVG_SYSTEM},
                {"role": "user", "content": _few_shot_block(item["prompt"], n=2)},
            ]
            prompt_only = tokenizer.apply_chat_template(
                prompt_messages, tokenize=False, add_generation_prompt=True)
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
        log.info(f"Dataset: {len(self.samples)} usable, {skipped} skipped.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


from transformers import TrainerCallback

class GDriveCheckpointCallback(TrainerCallback):
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


def train_lora(dataset: list):
    from transformers import (
        AutoTokenizer, Qwen2VLForConditionalGeneration,
        BitsAndBytesConfig, TrainingArguments, Trainer,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType

    log.info("Loading Qwen2-VL for fine-tuning …")
    tokenizer = AutoTokenizer.from_pretrained(cfg.VLM_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    sample_lens = []
    for item in dataset[:10]:
        full = build_chat_pair(item["prompt"], item["svg"], tokenizer)
        sample_lens.append(len(tokenizer.encode(full)))
    log.info(f"Sample token lengths (first 10): {sample_lens}")
    log.info(f"Max: {max(sample_lens)}, Mean: {np.mean(sample_lens):.0f}")

    if torch.cuda.is_available():
        free_gb = torch.cuda.mem_get_info()[0] / 1e9
        log.info(f"GPU free before model load: {free_gb:.1f} GB")
        if free_gb < 3.0:
            log.error(f"Only {free_gb:.1f} GB free — not enough for Qwen2-VL-7B.")
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
        log.error("No usable training samples!")
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
# INFERENCE: Text Prompt → Qwen2-VL → raw SVG
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
    response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    svg_body = response.strip()
    svg_body = re.sub(r"^```(?:svg|xml|html)?\s*\n?", "", svg_body)
    svg_body = re.sub(r"\n?```\s*$", "", svg_body)
    if "<svg" in svg_body:
        svg_body = _extract_svg_body(svg_body)
    return _wrap_svg_body(svg_body)


# ════════════════════════════════════════════════════════════════════════════
# EVALUATION: CLIP & DINO scores
# ════════════════════════════════════════════════════════════════════════════
def evaluate_pipeline(model, tokenizer, test_prompts: list, n_samples: int = 20) -> dict:
    import open_clip
    log.info("Loading CLIP for evaluation …")
    clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k")
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
                img_f = clip_model.encode_image(img_tensor)
                txt_f = clip_model.encode_text(txt_tensor)
                img_f /= img_f.norm(dim=-1, keepdim=True)
                txt_f /= txt_f.norm(dim=-1, keepdim=True)
                score = (img_f @ txt_f.T).item() * 100
            results.append({"prompt": prompt, "clip": score, "success": True})
            log.info(f"  [{i+1}/{len(test_subset)}] CLIP={score:.2f}  {prompt[:50]}")
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


# ════════════════════════════════════════════════════════════════════════════
# GOOGLE DRIVE HELPERS (same as v4)
# ════════════════════════════════════════════════════════════════════════════
_COLAB_DRIVE_ROOT = "/content/drive/MyDrive/DiffuSVG"
_gdrive_service = None
_colab_drive_ok = False


def _mount_gdrive():
    global _colab_drive_ok
    if _ENV != "colab" or _colab_drive_ok:
        return
    try:
        from google.colab import drive
        drive.mount("/content/drive", force_remount=False)
        Path(_COLAB_DRIVE_ROOT).mkdir(parents=True, exist_ok=True)
        _colab_drive_ok = True
        log.info(f"Google Drive mounted → {_COLAB_DRIVE_ROOT}")
    except Exception as e:
        log.warning(f"Drive mount failed: {e}")


def _init_gdrive_kaggle():
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
            return None
        sa_info = _json.loads(sa_key_json)
        creds = service_account.Credentials.from_service_account_info(
            sa_info, scopes=["https://www.googleapis.com/auth/drive"])
        _gdrive_service = build("drive", "v3", credentials=creds, cache_discovery=False)
        return _gdrive_service
    except Exception:
        return None


def _gdrive_upload(local_path: str, remote_name: str = None):
    lp = Path(local_path)
    if not lp.exists():
        return
    name = remote_name or lp.name
    if _ENV == "colab":
        if not _colab_drive_ok:
            return
        try:
            shutil.copy2(str(lp), str(Path(_COLAB_DRIVE_ROOT) / name))
            log.info(f"Drive ↑ {name}")
        except Exception:
            pass
        return
    svc = _init_gdrive_kaggle()
    if svc is None:
        return
    try:
        from googleapiclient.http import MediaFileUpload
        folder = cfg.GDRIVE_FOLDER_ID or None
        meta = {"name": name}
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
        log.info(f"Drive ↑ {name}")
    except Exception:
        pass


def _log_disk_space():
    total, used, free = shutil.disk_usage(_HF_CACHE)
    log.info(f"Disk: {free/1e9:.1f} GB free / {total/1e9:.1f} GB total")


def _purge_flux_cache():
    flux_dir = Path(_HF_CACHE) / "models--black-forest-labs--FLUX.1-schnell"
    if flux_dir.exists():
        log.info("Removing stale FLUX cache …")
        shutil.rmtree(flux_dir, ignore_errors=True)


# ════════════════════════════════════════════════════════════════════════════
# MAIN — Stages 1-3 only: Prompt → Flux Image → vtracer SVG
# ════════════════════════════════════════════════════════════════════════════
def save_and_display_results(dataset: list):
    """Save all generated PNGs and SVGs, render SVGs for comparison,
    and create an HTML gallery for visual review."""
    out_dir = Path(cfg.OUTPUT_DIR)
    svg_dir = out_dir / "svgs"
    rendered_dir = out_dir / "svg_rendered"
    svg_dir.mkdir(parents=True, exist_ok=True)
    rendered_dir.mkdir(parents=True, exist_ok=True)

    summary = []
    log.info("=" * 70)
    log.info("RESULTS SUMMARY")
    log.info("=" * 70)

    for i, item in enumerate(dataset):
        prompt = item["prompt"]
        svg_body = item["svg"]
        svg_full = item["svg_full"]
        img_path = item.get("image_path")
        is_seed = item.get("is_seed", False)

        # Count paths/elements in SVG
        n_paths = len(re.findall(r"<path", svg_full))
        n_elements = len(re.findall(r"<(rect|circle|ellipse|line|polygon|path)", svg_full))

        # Save SVG file
        svg_path = str(svg_dir / f"{i:05d}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_full)

        # Save SVG code as text file for easy viewing
        svg_code_path = str(svg_dir / f"{i:05d}_code.txt")
        with open(svg_code_path, "w", encoding="utf-8") as f:
            f.write(f"Prompt: {prompt}\n")
            f.write(f"Seed pair: {is_seed}\n")
            f.write(f"Paths: {n_paths}, Total elements: {n_elements}\n")
            f.write(f"{'─' * 50}\n")
            f.write(svg_full)

        # Render SVG → PNG for visual comparison
        rendered = render_svg_to_pil(svg_full, size=256)
        rendered_path = None
        if rendered:
            rendered_path = str(rendered_dir / f"{i:05d}_rendered.png")
            rendered.save(rendered_path)

        entry = {
            "index": i,
            "prompt": prompt,
            "is_seed": is_seed,
            "image_path": img_path,
            "svg_path": svg_path,
            "svg_rendered_path": rendered_path,
            "svg_code_path": svg_code_path,
            "n_paths": n_paths,
            "n_elements": n_elements,
            "svg_length_chars": len(svg_full),
        }
        summary.append(entry)

        # Print to log
        src = "SEED" if is_seed else "FLUX"
        log.info(
            f"  [{i:03d}] [{src}] elements={n_elements:2d}  "
            f"paths={n_paths:2d}  chars={len(svg_full):5d}  "
            f"  {prompt[:55]}"
        )

    # Save summary JSON
    summary_path = str(out_dir / "generation_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Save all SVG codes into one big JSON for easy inspection
    all_codes_path = str(out_dir / "all_svg_codes.json")
    codes = []
    for item in dataset:
        codes.append({
            "prompt": item["prompt"],
            "is_seed": item.get("is_seed", False),
            "svg_code": item["svg_full"],
        })
    with open(all_codes_path, "w", encoding="utf-8") as f:
        json.dump(codes, f, indent=2)

    # Generate HTML gallery
    gallery_path = str(out_dir / "gallery.html")
    html_parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        "<title>DiffuSVG v5 — Generation Gallery</title>",
        "<style>",
        "body{font-family:system-ui;background:#1a1a2e;color:#eee;padding:20px}",
        "h1{text-align:center;color:#e94560}",
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:20px}",
        ".card{background:#16213e;border-radius:12px;padding:16px;box-shadow:0 4px 12px rgba(0,0,0,.3)}",
        ".card h3{color:#0f3460;font-size:14px;margin:0 0 8px;color:#e94560}",
        ".images{display:flex;gap:8px;align-items:center}",
        ".images img,.images svg{width:200px;height:200px;border-radius:8px;background:#fff}",
        ".label{font-size:11px;color:#999;text-align:center;margin-top:2px}",
        ".stats{font-size:12px;color:#aaa;margin-top:8px}",
        "pre{background:#0a0a1a;color:#7ec8e3;padding:8px;border-radius:6px;",
        "font-size:11px;max-height:150px;overflow:auto;white-space:pre-wrap;word-break:break-all}",
        ".seed-badge{background:#e94560;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px}",
        ".flux-badge{background:#0f3460;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px}",
        "</style></head><body>",
        f"<h1>DiffuSVG v5 — {len(dataset)} Generated Samples</h1>",
        '<div class="grid">',
    ]

    for i, item in enumerate(dataset):
        is_seed = item.get("is_seed", False)
        badge = '<span class="seed-badge">SEED</span>' if is_seed else '<span class="flux-badge">FLUX</span>'
        n_el = len(re.findall(r"<(rect|circle|ellipse|line|polygon|path)", item["svg_full"]))
        n_p = len(re.findall(r"<path", item["svg_full"]))

        html_parts.append(f'<div class="card">')
        html_parts.append(f'<h3>{badge} {item["prompt"]}</h3>')
        html_parts.append('<div class="images">')

        # Show Flux raster image if available
        if item.get("image_path") and Path(item["image_path"]).exists():
            import base64 as b64
            with open(item["image_path"], "rb") as img_f:
                img_data = b64.b64encode(img_f.read()).decode()
            html_parts.append(f'<div><img src="data:image/png;base64,{img_data}"/>')
            html_parts.append('<div class="label">Flux Raster</div></div>')

        # Inline SVG
        html_parts.append(f'<div>{item["svg_full"]}')
        html_parts.append('<div class="label">vtracer SVG</div></div>')
        html_parts.append('</div>')

        html_parts.append(f'<div class="stats">Elements: {n_el} | Paths: {n_p} | Chars: {len(item["svg_full"])}</div>')
        # Show SVG code
        svg_escaped = item["svg_full"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html_parts.append(f'<pre>{svg_escaped}</pre>')
        html_parts.append('</div>')

    html_parts.append('</div></body></html>')
    with open(gallery_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))

    # Upload everything to Google Drive
    log.info("Uploading all outputs to Google Drive …")

    # Upload individual files
    _gdrive_upload(summary_path)
    _gdrive_upload(all_codes_path)
    _gdrive_upload(gallery_path)

    # Zip and upload image directories
    img_dir = out_dir / "images"
    if img_dir.exists() and any(img_dir.iterdir()):
        images_zip = str(out_dir / "flux_images")
        shutil.make_archive(images_zip, "zip", str(img_dir))
        _gdrive_upload(images_zip + ".zip", remote_name="v5_flux_images.zip")
        log.info(f"Drive ↑ v5_flux_images.zip")
        try:
            os.remove(images_zip + ".zip")
        except OSError:
            pass

    if svg_dir.exists() and any(svg_dir.iterdir()):
        svgs_zip = str(out_dir / "svg_files")
        shutil.make_archive(svgs_zip, "zip", str(svg_dir))
        _gdrive_upload(svgs_zip + ".zip", remote_name="v5_svg_files.zip")
        log.info(f"Drive ↑ v5_svg_files.zip")
        try:
            os.remove(svgs_zip + ".zip")
        except OSError:
            pass

    if rendered_dir.exists() and any(rendered_dir.iterdir()):
        rendered_zip = str(out_dir / "svg_rendered_pngs")
        shutil.make_archive(rendered_zip, "zip", str(rendered_dir))
        _gdrive_upload(rendered_zip + ".zip", remote_name="v5_svg_rendered.zip")
        log.info(f"Drive ↑ v5_svg_rendered.zip")
        try:
            os.remove(rendered_zip + ".zip")
        except OSError:
            pass

    # Also upload individual PNGs and SVGs for quick access (first 20)
    for i, item in enumerate(dataset[:20]):
        if item.get("image_path") and Path(item["image_path"]).exists():
            _gdrive_upload(item["image_path"], remote_name=f"v5_img_{i:03d}.png")
        svg_file = str(svg_dir / f"{i:05d}.svg")
        if Path(svg_file).exists():
            _gdrive_upload(svg_file, remote_name=f"v5_svg_{i:03d}.svg")

    log.info("All outputs uploaded to Google Drive.")

    log.info("=" * 70)
    log.info(f"Total samples: {len(dataset)}")
    log.info(f"  Seed pairs:  {sum(1 for s in summary if s['is_seed'])}")
    log.info(f"  Flux-generated: {sum(1 for s in summary if not s['is_seed'])}")
    log.info(f"Outputs saved to: {out_dir}")
    log.info(f"  PNG images:     {out_dir / 'images'}/")
    log.info(f"  SVG files:      {svg_dir}/")
    log.info(f"  SVG renders:    {rendered_dir}/")
    log.info(f"  Summary JSON:   {summary_path}")
    log.info(f"  All SVG codes:  {all_codes_path}")
    log.info(f"  HTML gallery:   {gallery_path}")
    log.info("=" * 70)

    return summary


def main():
    """Run Stages 1-3 only:
    1. Complex Prompt Generation (Gemini / fallback bank)
    2. Flux Image Generation (HF Inference API)
    3. vtracer SVG Conversion (with sparsity controls)
    Then save all PNGs and SVG codes, zip to working dir for download.
    """
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    if not cfg.HF_TOKEN.startswith("hf_"):
        raise RuntimeError(
            "HF_TOKEN not set. "
            "Kaggle: Add-ons → Secrets → add HF_TOKEN. "
            "Colab: Tools → Secrets → add HF_TOKEN."
        )

    # ── Mount Google Drive (Colab only) ──
    if _ENV == "colab":
        _mount_gdrive()

    _purge_flux_cache()
    _log_disk_space()

    # ── STAGE 1: Generate complex prompts ──
    log.info("═══ STAGE 1: Complex Prompt Generation ═══")
    complex_prompts = generate_complex_prompts()
    log.info(f"Generated {len(complex_prompts)} complex prompts.")

    # Save prompts
    prompts_path = os.path.join(cfg.OUTPUT_DIR, "complex_prompts.json")
    Path(cfg.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    with open(prompts_path, "w") as f:
        json.dump(complex_prompts, f, indent=2)
    log.info(f"Saved prompts → {prompts_path}")

    # Also mine failure prompts from any previous run
    results_path = find_results_json()
    failure_prompts = mine_failures(results_path)
    all_prompts = complex_prompts + [
        {"seed": "failure", "prompt": p, "complexity": "retry"}
        for p in failure_prompts
    ]
    log.info(f"Total prompts: {len(all_prompts)} "
             f"({len(complex_prompts)} complex + {len(failure_prompts)} failures)")

    # ── STAGE 2 + 3: Flux Image Generation + vtracer SVG Conversion ──
    log.info("═══ STAGE 2: Flux Image Generation ═══")
    log.info("═══ STAGE 3: vtracer SVG Conversion ═══")
    dataset = generate_dataset(all_prompts)

    # ── Save and display all results ──
    log.info("═══ SAVING & DISPLAYING ALL RESULTS ═══")
    summary = save_and_display_results(dataset)

    # Save the full dataset
    dataset_path = os.path.join(cfg.OUTPUT_DIR, "training_pairs.json")
    with open(dataset_path, "w") as f:
        json.dump(dataset, f, indent=2)
    log.info(f"Full dataset saved → {dataset_path}")

    # ── Zip all outputs to working directory ──
    log.info("═══ ZIPPING ALL OUTPUTS ═══")
    zip_base = os.path.join(cfg.WORKING_DIR, "diffusvg_v5_output")
    zip_path = shutil.make_archive(zip_base, "zip", cfg.OUTPUT_DIR)
    log.info(f"Zipped all outputs → {zip_path}")

    # Copy to Google Drive if on Colab
    if _ENV == "colab" and _colab_drive_ok:
        drive_dir = _COLAB_DRIVE_ROOT
        try:
            Path(drive_dir).mkdir(parents=True, exist_ok=True)
            shutil.copy2(zip_path, os.path.join(drive_dir, "diffusvg_v5_output.zip"))
            for fname in ["gallery.html", "all_svg_codes.json", "training_pairs.json", "generation_summary.json"]:
                src = os.path.join(cfg.OUTPUT_DIR, fname)
                if Path(src).exists():
                    shutil.copy2(src, os.path.join(drive_dir, fname))
            log.info(f"✅ All outputs also saved to Google Drive → {drive_dir}/")
        except Exception as e:
            log.warning(f"Could not copy to Drive: {e}")

    log.info("=" * 70)
    log.info("Pipeline complete (Stages 1-3).")
    log.info(f"  Output dir:  {cfg.OUTPUT_DIR}")
    log.info(f"  Zip file:    {zip_path}")
    if _ENV == "kaggle":
        log.info("  ─────────────────────────────────────────────────")
        log.info("  ✅ All outputs are in /kaggle/working/")
        log.info("  Open the file browser on the right side to download.")
    elif _ENV == "colab":
        log.info(f"  Drive: {_COLAB_DRIVE_ROOT}/diffusvg_v5_output.zip")
    log.info("=" * 70)

    # List what's in working dir for verification
    log.info(f"Contents of {cfg.WORKING_DIR}:")
    for item in sorted(os.listdir(cfg.WORKING_DIR)):
        fp = os.path.join(cfg.WORKING_DIR, item)
        if os.path.isfile(fp):
            size_mb = os.path.getsize(fp) / 1e6
            log.info(f"  📄 {item} ({size_mb:.1f} MB)")
        else:
            n_files = len(list(Path(fp).rglob("*")))
            log.info(f"  📁 {item}/ ({n_files} files)")


if __name__ == "__main__":
    main()
