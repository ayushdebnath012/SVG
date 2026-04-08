# -*- coding: utf-8 -*-
"""
OmniSVG_Inference.py — Generate SVGs using OmniSVG (NeurIPS 2025)
Runs on Kaggle T4 GPU (16 GB VRAM) with 4-bit quantization.

Prerequisites:
  - Clone OmniSVG repo and upload as Kaggle dataset, OR
  - Have OmniSVG repo in working directory

Usage on Kaggle:
  1. Add OmniSVG repo as a Kaggle dataset
  2. Paste this script in a notebook cell
  3. Run — model weights auto-download from HuggingFace
"""

import subprocess, sys, os, gc, json, logging, re, random, shutil, time
from pathlib import Path
from typing import Optional, List

# Must be set BEFORE any torch/CUDA import
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# ── Install dependencies ─────────────────────────────────────────────────────
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-U",
    "bitsandbytes>=0.46.1", "accelerate>=0.26.0", "transformers>=4.45.0",
    "cairosvg", "open_clip_torch", "qwen-vl-utils", "einops",
    "ConfigArgParse", "shapely", "moviepy"])

import torch
import numpy as np
from PIL import Image

os.environ["TOKENIZERS_PARALLELISM"] = "false"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("OmniSVG")

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
    "local": "/tmp/omnisvg",
}[_ENV]
os.makedirs(WORKING_DIR, exist_ok=True)

# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
MODEL_SIZE = "4B"  # Use 4B for T4 compatibility
NUM_SAMPLES = 20
NUM_CANDIDATES = 4  # Generate 4 candidates per prompt, keep best
OUTPUT_DIR = os.path.join(WORKING_DIR, "omnisvg_output")

# Where to find the OmniSVG repo (cloned code + deepsvg library)
OMNISVG_REPO_CANDIDATES = [
    "/kaggle/input/datasets/rkamondal/omnisvg/OmniSVG",
    "/kaggle/input/omnisvg/OmniSVG",
    "/kaggle/input/omnisvg",
    os.path.join(WORKING_DIR, "OmniSVG"),
    "f:/SVG-20260310T151742Z-1-001/SVG/OmniSVG",
]

# ════════════════════════════════════════════════════════════════════════════
# PROMPT POOL
# ════════════════════════════════════════════════════════════════════════════
_PROMPT_POOL = [
    # Icons (simple)
    "A red heart shape with smooth curved edges, centered.",
    "A yellow star with five sharp points, simple geometric design, flat color.",
    "A blue arrow pointing to the right, thick solid shape, centered.",
    "A green circle with a white checkmark inside, centered.",
    "A black plus sign with equal length arms, thick lines, centered.",
    "A black triangle pointing downward, centrally positioned.",
    # Icons (medium)
    "An orange thermometer with a circular base represents temperature measurement",
    "A blue bookmark icon with a white plus sign in the center",
    "A blue and gray database icon is overlaid with a yellow star in the bottom right corner",
    "A computer monitor displays a bar graph with yellow orange and green bars in ascending order",
    # Illustrations
    "A cartoon character with dark blue hair and a mustache wears a blue suit against a light blue circular background",
    "A sad wilted flower with pink petals slumps over an orange cloud with a blue striped background",
    "Desert landscape: light orange sky with white circle sun, tan sand dunes as curved shapes, one green cactus with arms on the right side.",
    "Profile silhouette avatar: black side view of head with short hair and glasses outline, facing right. Simple solid shape.",
    "A running person: side view silhouette in black, dynamic pose with one leg forward, arms pumping. Motion style.",
    # More diverse prompts
    "A purple butterfly with symmetrical wings, flat design",
    "A coffee cup with steam rising, brown and white",
    "A red fire truck, side view, simple geometric shapes",
    "A green tree with brown trunk, round canopy",
    "A golden trophy cup with handles on both sides",
    "A blue whale swimming, minimal design with water drops",
    "A rainbow arc with seven color bands against a white background",
    "A black music note on a white background, centered",
    "A red and white lighthouse with light beam, simple design",
    "A pink cupcake with cherry on top, flat illustration style",
]


# ════════════════════════════════════════════════════════════════════════════
# SETUP: Find OmniSVG repo and add to path
# ════════════════════════════════════════════════════════════════════════════
def find_omnisvg_repo() -> str:
    """Find the OmniSVG repo directory."""
    for path in OMNISVG_REPO_CANDIDATES:
        if os.path.exists(path) and (
            os.path.exists(os.path.join(path, "decoder.py")) or
            os.path.exists(os.path.join(path, "tokenizer.py"))
        ):
            return path
    
    # Try cloning if not found
    clone_dir = os.path.join(WORKING_DIR, "OmniSVG")
    if not os.path.exists(clone_dir):
        log.info("OmniSVG repo not found, cloning...")
        subprocess.check_call(["git", "clone", "https://github.com/OmniSVG/OmniSVG.git", clone_dir])
    return clone_dir


def setup_omnisvg():
    """Add OmniSVG to Python path and import modules."""
    repo_dir = find_omnisvg_repo()
    log.info(f"OmniSVG repo: {repo_dir}")
    
    # Add to Python path
    if repo_dir not in sys.path:
        sys.path.insert(0, repo_dir)
    
    return repo_dir


# ════════════════════════════════════════════════════════════════════════════
# LOAD MODEL
# ════════════════════════════════════════════════════════════════════════════
def load_omnisvg(repo_dir: str):
    """Load OmniSVG model with 4-bit quantization."""
    import yaml
    from decoder import SketchDecoder
    from transformers import AutoTokenizer, AutoProcessor
    from tokenizer import SVGTokenizer
    
    config_path = os.path.join(repo_dir, "config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    model_cfg = config.get('models', {}).get(MODEL_SIZE, {})
    hf_cfg = model_cfg.get('huggingface', {})
    qwen_model = hf_cfg.get('qwen_model', 'Qwen/Qwen2.5-VL-3B-Instruct')
    omnisvg_weights = hf_cfg.get('omnisvg_model', 'OmniSVG/OmniSVG1.1_4B')
    
    log.info(f"Base model: {qwen_model}")
    log.info(f"OmniSVG weights: {omnisvg_weights}")
    
    # Clear GPU
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        free_gb = torch.cuda.mem_get_info()[0] / 1e9
        log.info(f"GPU free: {free_gb:.1f} GB")
    
    # Load tokenizer & processor
    log.info("[1/4] Loading tokenizer and processor...")
    tokenizer = AutoTokenizer.from_pretrained(qwen_model, padding_side="left", trust_remote_code=True)
    processor = AutoProcessor.from_pretrained(qwen_model, padding_side="left", trust_remote_code=True)
    processor.tokenizer.padding_side = "left"
    
    # Load SketchDecoder with 4-bit quantization
    log.info("[2/4] Loading SketchDecoder (4-bit quantization)...")
    sketch_decoder = SketchDecoder(
        config_path=config_path,
        model_path=qwen_model,
        model_size=MODEL_SIZE,
        pix_len=2048,
        text_len=config.get('text', {}).get('max_length', 200),
        torch_dtype=torch.float16,
        quantize_4bit=True,
    )
    
    # Load OmniSVG weights
    log.info("[3/4] Loading OmniSVG weights...")
    from huggingface_hub import hf_hub_download
    
    # Check if weights are local
    local_bin = os.path.join(omnisvg_weights, "pytorch_model.bin") if os.path.exists(omnisvg_weights) else None
    if local_bin and os.path.exists(local_bin):
        bin_path = local_bin
    else:
        log.info(f"Downloading weights from HuggingFace: {omnisvg_weights}")
        bin_path = hf_hub_download(repo_id=omnisvg_weights, filename="pytorch_model.bin", resume_download=True)
    
    state_dict = torch.load(bin_path, map_location='cpu')
    sketch_decoder.load_state_dict(state_dict, strict=False)
    sketch_decoder = sketch_decoder.eval()
    log.info("OmniSVG weights loaded!")
    
    # SVG tokenizer
    log.info("[4/4] Initializing SVG tokenizer...")
    svg_tokenizer = SVGTokenizer(config_path, model_size=MODEL_SIZE)
    
    if torch.cuda.is_available():
        free_gb = torch.cuda.mem_get_info()[0] / 1e9
        log.info(f"GPU free after loading: {free_gb:.1f} GB")
    
    return sketch_decoder, tokenizer, processor, svg_tokenizer, config


# ════════════════════════════════════════════════════════════════════════════
# GENERATE SVG
# ════════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """You are an expert SVG code generator. 
Generate precise, valid SVG path commands that accurately represent the described scene or object.
Focus on capturing key shapes, spatial relationships, and visual composition."""


def render_svg_to_pil(svg_str: str, size: int = 512) -> Optional[Image.Image]:
    """Render SVG string to PIL image."""
    try:
        import cairosvg, io
        png_data = cairosvg.svg2png(bytestring=svg_str.encode('utf-8'),
                                     output_width=size, output_height=size)
        img_rgba = Image.open(io.BytesIO(png_data)).convert("RGBA")
        bg = Image.new("RGB", img_rgba.size, (255, 255, 255))
        bg.paste(img_rgba, mask=img_rgba.split()[3])
        return bg
    except Exception as e:
        return None


def generate_svg(prompt: str, sketch_decoder, tokenizer, processor, svg_tokenizer, config,
                 num_candidates: int = 4, temperature: float = 0.5, max_length: int = 1536):
    """Generate SVG from text prompt using OmniSVG."""
    
    model_cfg = config.get('model', {})
    BOS_TOKEN_ID = model_cfg.get('bos_token_id', 196998)
    EOS_TOKEN_ID = model_cfg.get('eos_token_id', 196999)
    PAD_TOKEN_ID = model_cfg.get('pad_token_id', 151643)
    
    colors_cfg = config.get('colors', {})
    BLACK_COLOR_TOKEN = colors_cfg.get('black_color_token',
                                        colors_cfg.get('color_token_start', 40010) + 2)
    
    # Prepare input
    instruction = f"""Generate an SVG illustration for: {prompt}
        
Requirements:
- Create complete SVG path commands
- Include proper coordinates and colors
- Maintain visual clarity and composition"""
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [{"type": "text", "text": instruction}]}
    ]
    text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text_input], padding=True, truncation=True, return_tensors="pt")
    
    # Get model input device
    try:
        embed_device = next(sketch_decoder.transformer.model.embed_tokens.parameters()).device
    except Exception:
        embed_device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    
    input_ids = inputs['input_ids'].to(embed_device)
    attention_mask = inputs['attention_mask'].to(embed_device)
    
    # Generate
    candidates = []
    actual_samples = num_candidates + 4  # extra buffer
    
    try:
        with torch.no_grad():
            results = sketch_decoder.transformer.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_length,
                num_return_sequences=actual_samples,
                do_sample=True,
                temperature=temperature,
                top_p=0.88,
                top_k=50,
                repetition_penalty=1.05,
                use_cache=True,
                eos_token_id=EOS_TOKEN_ID,
                pad_token_id=PAD_TOKEN_ID,
                bos_token_id=BOS_TOKEN_ID,
            )
            
            input_len = input_ids.shape[1]
            generated_ids_batch = results[:, input_len:]
        
        for i in range(min(actual_samples, generated_ids_batch.shape[0])):
            try:
                current_ids = generated_ids_batch[i:i+1].cpu()
                fake_wrapper = torch.cat([
                    torch.full((1, 1), BOS_TOKEN_ID),
                    current_ids,
                    torch.full((1, 1), EOS_TOKEN_ID)
                ], dim=1)
                
                generated_xy = svg_tokenizer.process_generated_tokens(fake_wrapper)
                if len(generated_xy) == 0:
                    continue
                
                svg_tensors, color_tensors = svg_tokenizer.raster_svg(generated_xy)
                if not svg_tensors or not svg_tensors[0]:
                    continue
                
                num_paths = len(svg_tensors[0])
                while len(color_tensors) < num_paths:
                    color_tensors.append(BLACK_COLOR_TOKEN)
                
                svg = svg_tokenizer.apply_colors_to_svg(svg_tensors[0], color_tensors)
                svg_str = svg.to_str()
                
                if 'width=' not in svg_str:
                    svg_str = svg_str.replace('<svg', '<svg width="448" height="448"', 1)
                
                # Validate
                img = render_svg_to_pil(svg_str, size=512)
                if img is None:
                    continue
                img_array = np.array(img)
                if img_array.mean() > 252:
                    continue  # empty/blank
                
                candidates.append({'svg': svg_str, 'img': img, 'paths': num_paths})
                
                if len(candidates) >= num_candidates:
                    break
            except Exception as e:
                continue
    except Exception as e:
        log.error(f"Generation error: {e}")
    
    return candidates


# ════════════════════════════════════════════════════════════════════════════
# CLIP SCORING
# ════════════════════════════════════════════════════════════════════════════
def compute_clip_scores(results: list):
    """Compute CLIP scores for generated SVGs."""
    try:
        import open_clip
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "open_clip_torch"])
        import open_clip

    log.info("Loading CLIP model...")
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
            img = Image.open(r["png_path"]).convert("RGB") if isinstance(r.get("png_path"), str) else r.get("img")
            if img is None:
                continue
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
        '<title>OmniSVG — Generated SVGs</title>',
        '<style>',
        'body{background:#0f0f23;color:#eee;font-family:"Inter","Segoe UI",sans-serif;padding:20px;margin:0}',
        'h1{text-align:center;background:linear-gradient(135deg,#ff6b6b,#4ecdc4);',
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:2.5em;margin:30px 0}',
        '.stats{text-align:center;color:#888;font-size:14px;margin-bottom:30px}',
        '.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:24px;padding:0 20px}',
        '.card{background:linear-gradient(145deg,#16213e,#1a1a3e);border-radius:16px;padding:20px;',
        'text-align:center;box-shadow:0 8px 32px rgba(0,0,0,0.4);transition:transform 0.2s}',
        '.card:hover{transform:translateY(-4px)}',
        '.card img{width:200px;height:200px;border-radius:12px;background:#fff;box-shadow:0 4px 12px rgba(0,0,0,0.3)}',
        '.card .prompt{font-size:13px;margin:12px 0 6px;color:#a8d8ea;font-weight:500}',
        '.card .score{font-size:20px;font-weight:bold}',
        '.card .good{color:#4ecca3} .card .mid{color:#f0a500} .card .low{color:#e94560} .card .fail{color:#666}',
        '.card .meta{font-size:11px;color:#555;margin-top:4px}',
        '</style></head><body>',
        '<h1>🎨 OmniSVG — Generated SVGs</h1>',
    ]

    successful = [r for r in results if r.get("success")]
    clips = [r["clip"] for r in successful if r.get("clip", 0) > 0]
    if clips:
        html.append(f'<div class="stats">{len(successful)}/{len(results)} successful | '
                     f'CLIP: mean={np.mean(clips):.1f}, best={max(clips):.1f} | Model: OmniSVG {MODEL_SIZE}</div>')

    html.append('<div class="grid">')
    sorted_results = sorted(results, key=lambda x: x.get("clip", 0), reverse=True)
    for r in sorted_results:
        clip_val = r.get("clip", 0)
        cls = "good" if clip_val >= 25 else "mid" if clip_val >= 20 else "low" if r.get("success") else "fail"
        clip_str = f"{clip_val:.1f}" if r.get("success") else "FAIL"
        png_name = os.path.basename(r.get("png_path", ""))
        prompt_short = r["prompt"][:80] + ("..." if len(r["prompt"]) > 80 else "")
        html.append(f'<div class="card">')
        html.append(f'<img src="{png_name}" alt="{prompt_short}">')
        html.append(f'<div class="prompt">{prompt_short}</div>')
        html.append(f'<div class="score {cls}">CLIP: {clip_str}</div>')
        if r.get("paths"):
            html.append(f'<div class="meta">{r["paths"]} paths</div>')
        html.append(f'</div>')

    html.append('</div></body></html>')
    with open(os.path.join(output_dir, "gallery.html"), "w") as f:
        f.write("\n".join(html))
    log.info(f"Gallery saved → {os.path.join(output_dir, 'gallery.html')}")


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log.info("=" * 70)
    log.info("OmniSVG Inference — Text-to-SVG Generation")
    log.info("=" * 70)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Setup
    repo_dir = setup_omnisvg()
    
    # Load model
    sketch_decoder, tokenizer, processor, svg_tokenizer, config = load_omnisvg(repo_dir)
    
    # Select prompts
    prompts = random.sample(_PROMPT_POOL, min(NUM_SAMPLES, len(_PROMPT_POOL)))
    log.info(f"Generating SVGs for {len(prompts)} prompts...")
    
    # Generate
    results = []
    for i, prompt in enumerate(prompts):
        log.info(f"[{i+1}/{len(prompts)}] {prompt[:60]}...")
        start = time.time()
        
        try:
            candidates = generate_svg(prompt, sketch_decoder, tokenizer, processor,
                                       svg_tokenizer, config, num_candidates=NUM_CANDIDATES)
            elapsed = time.time() - start
            
            if candidates:
                best = candidates[0]  # first valid candidate
                svg_path = os.path.join(OUTPUT_DIR, f"omnisvg_{i:03d}.svg")
                png_path = os.path.join(OUTPUT_DIR, f"omnisvg_{i:03d}.png")
                with open(svg_path, "w") as f:
                    f.write(best['svg'])
                best['img'].save(png_path)
                
                results.append({
                    "prompt": prompt, "success": True, "clip": 0.0,
                    "svg_path": svg_path, "png_path": png_path,
                    "paths": best['paths'], "img": best['img'],
                })
                log.info(f"  ✓ {best['paths']} paths, {elapsed:.1f}s")
            else:
                results.append({"prompt": prompt, "success": False, "clip": 0.0, "png_path": ""})
                log.info(f"  ✗ No valid candidates ({elapsed:.1f}s)")
        except Exception as e:
            log.error(f"  ✗ Error: {e}")
            results.append({"prompt": prompt, "success": False, "clip": 0.0, "png_path": ""})
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    # Free model for CLIP scoring
    del sketch_decoder
    gc.collect()
    torch.cuda.empty_cache()
    
    # CLIP scoring
    log.info("Computing CLIP scores...")
    results = compute_clip_scores(results)
    
    # Gallery
    generate_gallery(results, OUTPUT_DIR)
    
    # Summary
    successful = [r for r in results if r["success"]]
    clips = [r["clip"] for r in successful if r["clip"] > 0]
    
    summary = {
        "model": f"OmniSVG {MODEL_SIZE}",
        "n_total": len(results),
        "n_success": len(successful),
        "clip_mean": float(np.mean(clips)) if clips else 0.0,
        "clip_median": float(np.median(clips)) if clips else 0.0,
        "clip_max": float(max(clips)) if clips else 0.0,
        "results": [{k: v for k, v in r.items() if k not in ("img",)} for r in results],
    }
    with open(os.path.join(OUTPUT_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    
    # Zip
    shutil.make_archive(os.path.join(WORKING_DIR, "omnisvg_output"), "zip", OUTPUT_DIR)
    
    log.info("=" * 70)
    log.info("COMPLETE")
    log.info("=" * 70)
    log.info(f"  Success: {len(successful)}/{len(results)}")
    if clips:
        log.info(f"  CLIP: mean={np.mean(clips):.1f}, median={np.median(clips):.1f}, best={max(clips):.1f}")
    log.info(f"  Output: {OUTPUT_DIR}")
    
    if clips:
        ranked = sorted(successful, key=lambda x: x["clip"], reverse=True)
        log.info("\n  🏆 Top 5:")
        for r in ranked[:5]:
            log.info(f"    CLIP={r['clip']:.1f}  {r['prompt'][:50]}")

    if _ENV == "kaggle":
        log.info("\n📥 Download: Output → omnisvg_output.zip")


if __name__ == "__main__":
    main()
