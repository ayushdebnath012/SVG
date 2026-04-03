# -*- coding: utf-8 -*-
"""
DiffuSVG_Inference_v6.py — Generate SVGs from random prompts using fine-tuned Qwen2-VL LoRA
Runs on Kaggle T4 GPU (16 GB VRAM).

Usage:
  1. Upload diffusvg_v6_output/ as a Kaggle dataset
  2. Paste this script in a Kaggle notebook and run
  3. Outputs: SVGs, PNGs, HTML gallery → /kaggle/working/inference_output/
"""

import subprocess, sys, os, gc, json, logging, re, random, shutil
from pathlib import Path
from typing import Optional

# Must be set BEFORE any torch/CUDA import
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

# ── Install dependencies ─────────────────────────────────────────────────────
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-U",
    "bitsandbytes>=0.46.1", "peft>=0.13.0", "accelerate>=0.26.0",
    "cairosvg", "open_clip_torch"])

import torch, numpy as np
from PIL import Image
from peft import PeftModel

os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DiffuSVG-Inference")

# ── Detect environment ───────────────────────────────────────────────────────
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
WORKING_DIR = {
    "kaggle": "/kaggle/working",
    "colab": "/content",
    "local": "/tmp/diffusvg",
}[_ENV]
os.makedirs(WORKING_DIR, exist_ok=True)

# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
BASE_MODEL = "Qwen/Qwen2-VL-7B-Instruct"
ADAPTER_PATH_CANDIDATES = [
    # Kaggle dataset input
    "/kaggle/input/datasets/rkamondal/diffusvg-v5/lora_checkpoints/final_adapter",
    "/kaggle/input/diffusvg-v6/lora_checkpoints/final_adapter",
    "/kaggle/input/diffusvg-v6-output/lora_checkpoints/final_adapter",
    "/kaggle/input/datasets/rkamondal/diffusvg-v6/lora_checkpoints/final_adapter",
    os.path.join(WORKING_DIR, "diffusvg_v6_output", "lora_checkpoints", "final_adapter"),
    # Local dev path
    "f:/SVG-20260310T151742Z-1-001/SVG/diffusvg_v6_output/lora_checkpoints/final_adapter",
]
OUTPUT_DIR = os.path.join(WORKING_DIR, "inference_output")
NUM_SAMPLES = 30  # How many SVGs to generate

# ════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT & FEW-SHOT (same as training)
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
        import cairosvg, io
        png_data = cairosvg.svg2png(bytestring=svg_string.encode("utf-8"),
                                     output_width=size, output_height=size)
        return Image.open(io.BytesIO(png_data)).convert("RGB")
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════════
# RANDOM PROMPTS (diverse categories)
# ════════════════════════════════════════════════════════════════════════════
_PROMPT_POOL = [
    # Animals
    "a red fox", "a blue penguin", "a green frog", "a yellow duck",
    "a purple octopus", "an orange goldfish", "a gray elephant",
    "a pink flamingo", "a brown bear", "a white rabbit",
    # Nature
    "a mountain with snow", "a palm tree", "a volcano erupting",
    "a rainbow over hills", "a waterfall", "a sunset over ocean",
    "a pine tree in snow", "a mushroom", "a cactus in desert",
    # Objects
    "a coffee cup", "a light bulb", "a bicycle", "a guitar",
    "a camera", "a book", "a treasure chest", "a candle",
    "a hot air balloon", "a compass", "a magnifying glass",
    # Food
    "a pizza slice", "a cupcake", "a watermelon slice",
    "a donut", "a sushi roll", "an apple", "a banana",
    # Space & Weather
    "a planet with rings", "a shooting star", "a UFO",
    "a lightning bolt", "a tornado", "a cloud with rain",
    # Buildings & Vehicles
    "a lighthouse", "a castle", "a windmill",
    "a sailboat", "a helicopter", "a submarine",
    # Symbols & Abstract
    "a peace sign", "a music note", "a heart with wings",
    "a shield with star", "an hourglass", "a yin yang symbol",
    "a crown", "a trophy", "a diamond ring",
    # Complex scenes
    "a house with garden", "a fish in a bowl",
    "a snowman with hat", "a robot face", "an alien face",
    "a pirate flag", "a skull and crossbones",
]


# ════════════════════════════════════════════════════════════════════════════
# LOAD MODEL
# ════════════════════════════════════════════════════════════════════════════
def load_model():
    from transformers import AutoTokenizer, Qwen2VLForConditionalGeneration, BitsAndBytesConfig

    # Find adapter
    adapter_path = None
    for path in ADAPTER_PATH_CANDIDATES:
        if os.path.exists(path) and os.path.exists(os.path.join(path, "adapter_config.json")):
            adapter_path = path
            break

    if adapter_path is None:
        log.error("LoRA adapter not found! Searched:")
        for p in ADAPTER_PATH_CANDIDATES:
            log.error(f"  {p}")
        log.error("Upload diffusvg_v6_output/ as a Kaggle dataset.")
        return None, None

    log.info(f"Found adapter at: {adapter_path}")

    # Clear GPU
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(adapter_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load base model with 4-bit quantization
    log.info(f"Loading base model: {BASE_MODEL} (4-bit)...")
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
    )
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        BASE_MODEL, quantization_config=quant_config,
        device_map={"": 0}, trust_remote_code=True,
    )

    # Load LoRA adapter
    log.info("Loading LoRA adapter...")
    model = PeftModel.from_pretrained(model, adapter_path)
    model.eval()

    if torch.cuda.is_available():
        free_gb = torch.cuda.mem_get_info()[0] / 1e9
        log.info(f"GPU free after model load: {free_gb:.1f} GB")

    return model, tokenizer


# ════════════════════════════════════════════════════════════════════════════
# GENERATE
# ════════════════════════════════════════════════════════════════════════════
@torch.inference_mode()
def generate_svg(prompt: str, model, tokenizer, max_new_tokens: int = 1500,
                 temperature: float = 0.7, top_p: float = 0.9) -> str:
    messages = [
        {"role": "system", "content": _SVG_SYSTEM},
        {"role": "user", "content": _few_shot_block(prompt, n=2)},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    out = model.generate(
        **inputs, max_new_tokens=max_new_tokens,
        do_sample=True, temperature=temperature, top_p=top_p,
        repetition_penalty=1.1,
    )
    response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    svg_body = response.strip()
    # Clean markdown fences
    svg_body = re.sub(r"^```(?:svg|xml|html)?\s*\n?", "", svg_body)
    svg_body = re.sub(r"\n?```\s*$", "", svg_body)
    # If model emitted full SVG, extract body
    if "<svg" in svg_body:
        m = re.search(r"<svg[^>]*>(.*?)</svg>", svg_body, re.DOTALL)
        if m:
            svg_body = m.group(1).strip()
    return _wrap_svg(svg_body)


# ════════════════════════════════════════════════════════════════════════════
# EVALUATION (CLIP)
# ════════════════════════════════════════════════════════════════════════════
def compute_clip_scores(results: list) -> list:
    """Compute CLIP scores for generated SVGs."""
    try:
        import open_clip
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "open_clip_torch"])
        import open_clip

    log.info("Loading CLIP model for scoring...")
    clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k")
    clip_tokenizer = open_clip.get_tokenizer("ViT-B-32")
    clip_model = clip_model.float().eval()
    if torch.cuda.is_available():
        clip_model = clip_model.cuda()

    for r in results:
        if not r.get("success"):
            continue
        try:
            img = Image.open(r["png_path"]).convert("RGB")
            img_tensor = clip_preprocess(img).unsqueeze(0)
            txt_tensor = clip_tokenizer([r["prompt"]])
            if torch.cuda.is_available():
                img_tensor = img_tensor.cuda()
                txt_tensor = txt_tensor.cuda()
            with torch.no_grad():
                img_f = clip_model.encode_image(img_tensor)
                txt_f = clip_model.encode_text(txt_tensor)
                img_f /= img_f.norm(dim=-1, keepdim=True)
                txt_f /= txt_f.norm(dim=-1, keepdim=True)
                r["clip"] = (img_f @ txt_f.T).item() * 100
        except Exception as e:
            log.error(f"  CLIP error for '{r['prompt']}': {e}")
            r["clip"] = 0.0

    del clip_model
    gc.collect()
    torch.cuda.empty_cache()
    return results


# ════════════════════════════════════════════════════════════════════════════
# HTML GALLERY
# ════════════════════════════════════════════════════════════════════════════
def generate_gallery(results: list, output_dir: str):
    html = [
        '<!DOCTYPE html><html><head><meta charset="utf-8">',
        '<title>DiffuSVG v6 — Inference Gallery</title>',
        '<style>',
        'body{background:#0f0f23;color:#eee;font-family:"Inter","Segoe UI",sans-serif;padding:20px;margin:0}',
        'h1{text-align:center;background:linear-gradient(135deg,#e94560,#0f3460);',
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:2.5em;margin:30px 0}',
        '.stats{text-align:center;color:#888;font-size:14px;margin-bottom:30px}',
        '.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:24px;padding:0 20px}',
        '.card{background:linear-gradient(145deg,#16213e,#1a1a3e);border-radius:16px;padding:20px;',
        'text-align:center;box-shadow:0 8px 32px rgba(0,0,0,0.4);transition:transform 0.2s}',
        '.card:hover{transform:translateY(-4px)}',
        '.card img{width:200px;height:200px;border-radius:12px;background:#fff;',
        'box-shadow:0 4px 12px rgba(0,0,0,0.3)}',
        '.card .prompt{font-size:14px;margin:12px 0 6px;color:#a8d8ea;font-weight:500}',
        '.card .score{font-size:20px;font-weight:bold}',
        '.card .good{color:#4ecca3}',
        '.card .mid{color:#f0a500}',
        '.card .low{color:#e94560}',
        '.card .fail{color:#666}',
        '</style></head><body>',
        '<h1>🎨 DiffuSVG v6 — Generated SVGs</h1>',
    ]

    successful = [r for r in results if r.get("success")]
    clips = [r["clip"] for r in successful if r.get("clip", 0) > 0]
    if clips:
        html.append(f'<div class="stats">{len(successful)}/{len(results)} successful | '
                     f'CLIP: mean={np.mean(clips):.1f}, best={max(clips):.1f}</div>')

    html.append('<div class="grid">')
    # Sort by CLIP score descending
    sorted_results = sorted(results, key=lambda x: x.get("clip", 0), reverse=True)
    for r in sorted_results:
        clip_val = r.get("clip", 0)
        if r.get("success"):
            if clip_val >= 25:
                cls = "good"
            elif clip_val >= 20:
                cls = "mid"
            else:
                cls = "low"
            clip_str = f"{clip_val:.1f}"
        else:
            cls = "fail"
            clip_str = "FAIL"
        png_name = os.path.basename(r.get("png_path", ""))
        html.append(f'<div class="card">')
        html.append(f'<img src="{png_name}" alt="{r["prompt"]}">')
        html.append(f'<div class="prompt">{r["prompt"]}</div>')
        html.append(f'<div class="score {cls}">CLIP: {clip_str}</div>')
        html.append(f'</div>')

    html.append('</div></body></html>')
    gallery_path = os.path.join(output_dir, "gallery.html")
    with open(gallery_path, "w") as f:
        f.write("\n".join(html))
    log.info(f"Gallery saved → {gallery_path}")


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log.info("=" * 70)
    log.info("DiffuSVG v6 — Inference: Generate SVGs from Random Prompts")
    log.info("=" * 70)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── Load model ───────────────────────────────────────────────────────
    model, tokenizer = load_model()
    if model is None:
        return

    # ── Select prompts ───────────────────────────────────────────────────
    prompts = random.sample(_PROMPT_POOL, min(NUM_SAMPLES, len(_PROMPT_POOL)))
    log.info(f"Generating {len(prompts)} SVGs from random prompts...")

    # ── Generate ─────────────────────────────────────────────────────────
    results = []
    for i, prompt in enumerate(prompts):
        log.info(f"  [{i+1}/{len(prompts)}] {prompt}")
        try:
            svg = generate_svg(prompt, model, tokenizer)
            rendered = _render_svg_to_pil(svg, size=224)

            svg_path = os.path.join(OUTPUT_DIR, f"gen_{i:03d}.svg")
            png_path = os.path.join(OUTPUT_DIR, f"gen_{i:03d}.png")

            with open(svg_path, "w") as f:
                f.write(svg)

            if rendered:
                rendered.save(png_path)
                results.append({
                    "prompt": prompt, "success": True, "clip": 0.0,
                    "svg_path": svg_path, "png_path": png_path,
                    "svg_chars": len(svg),
                })
                log.info(f"    ✓ {len(svg)} chars")
            else:
                results.append({"prompt": prompt, "success": False, "clip": 0.0,
                                "svg_path": svg_path, "png_path": ""})
                log.info(f"    ✗ render failed")
        except Exception as e:
            log.error(f"    ✗ {e}")
            results.append({"prompt": prompt, "success": False, "clip": 0.0,
                            "svg_path": "", "png_path": ""})

    # ── Free model, score with CLIP ──────────────────────────────────────
    del model, tokenizer
    gc.collect()
    torch.cuda.empty_cache()
    log.info("Model unloaded. Computing CLIP scores...")

    results = compute_clip_scores(results)

    # ── Summary ──────────────────────────────────────────────────────────
    successful = [r for r in results if r["success"]]
    clips = [r["clip"] for r in successful if r["clip"] > 0]

    summary = {
        "n_total": len(results),
        "n_success": len(successful),
        "clip_mean": float(np.mean(clips)) if clips else 0.0,
        "clip_median": float(np.median(clips)) if clips else 0.0,
        "clip_std": float(np.std(clips)) if clips else 0.0,
        "clip_max": float(max(clips)) if clips else 0.0,
        "results": [{k: v for k, v in r.items() if k not in ("svg_path", "png_path")}
                    for r in results],
    }

    with open(os.path.join(OUTPUT_DIR, "inference_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # ── Gallery ──────────────────────────────────────────────────────────
    generate_gallery(results, OUTPUT_DIR)

    # ── Zip ───────────────────────────────────────────────────────────────
    zip_base = os.path.join(WORKING_DIR, "inference_output")
    shutil.make_archive(zip_base, "zip", OUTPUT_DIR)
    log.info(f"Zipped → {zip_base}.zip")

    # ── Print summary ────────────────────────────────────────────────────
    log.info("=" * 70)
    log.info("INFERENCE COMPLETE")
    log.info("=" * 70)
    log.info(f"  Generated: {len(successful)}/{len(results)} successful")
    if clips:
        log.info(f"  CLIP: mean={np.mean(clips):.1f}, median={np.median(clips):.1f}, "
                 f"best={max(clips):.1f}")
    log.info(f"  Output: {OUTPUT_DIR}")
    log.info(f"  Gallery: {os.path.join(OUTPUT_DIR, 'gallery.html')}")
    log.info(f"  Zip: {zip_base}.zip")

    # Top 5
    if clips:
        ranked = sorted(successful, key=lambda x: x["clip"], reverse=True)
        log.info("\n  🏆 Top 5:")
        for r in ranked[:5]:
            log.info(f"    CLIP={r['clip']:.1f}  {r['prompt']}")

    if _ENV == "kaggle":
        log.info("\n📥 Download from Kaggle: Output → inference_output.zip")


if __name__ == "__main__":
    main()
