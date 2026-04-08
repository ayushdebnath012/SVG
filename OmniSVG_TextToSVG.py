# -*- coding: utf-8 -*-
"""
OmniSVG_TextToSVG.py — Text-to-SVG Generation System
=====================================================
Input:  Text prompts (list of strings)
Output: SVG files + PNG previews + HTML gallery

Uses OmniSVG (NeurIPS 2025) with 4-bit quantization on Kaggle T4.

HOW TO USE:
  1. Edit PROMPTS list below with your desired descriptions
  2. Run on Kaggle with GPU (T4)
  3. Download results from omnisvg_output.zip
"""

import subprocess, sys, os, gc, json, logging, re, random, shutil, time, io
from pathlib import Path
from typing import Optional, List

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# ── Install dependencies ─────────────────────────────────────────────────────
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-U",
    "bitsandbytes>=0.46.1", "accelerate>=0.26.0", "transformers>=4.45.0",
    "cairosvg", "qwen-vl-utils", "einops", "ConfigArgParse", "shapely"])

import torch
import numpy as np
from PIL import Image

os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("TextToSVG")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  ✏️  EDIT YOUR PROMPTS HERE                                              ║
# ╚════════════════════════════════════════════════════════════════════════════╝
PROMPTS = [
    "A red heart shape with smooth curved edges, centered.",
    "A yellow star with five sharp points, simple geometric design, flat color.",
    "A blue arrow pointing to the right, thick solid shape, centered.",
    "A green circle with a white checkmark inside, centered.",
    "A black plus sign with equal length arms, thick lines, centered.",
    "A cartoon character with dark blue hair wearing a blue suit",
    "A coffee cup with steam rising, brown and white",
    "A purple butterfly with symmetrical wings, flat design",
    "Desert landscape: orange sky, sand dunes, green cactus on the right",
    "A red fire truck, side view, simple geometric shapes",
    "A rainbow arc with seven color bands against white background",
    "A lighthouse with red and white stripes, light beam shining",
    "A golden trophy cup with handles on both sides",
    "A pink cupcake with cherry on top, flat illustration style",
    "A running person silhouette in black, dynamic pose",
]

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  CONFIG                                                                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝
MODEL_SIZE = "4B"           # "4B" for T4, "8B" for A100
NUM_CANDIDATES = 4          # Generate N candidates per prompt, keep best
MAX_SVG_TOKENS = 1536       # Max SVG token length
TEMPERATURE = 0.5           # Generation temperature (lower = more precise)
RENDER_SIZE = 512           # PNG preview size

# Paths
OMNISVG_REPO_CANDIDATES = [
    "/kaggle/input/datasets/rkamondal/omnisvg/OmniSVG",
    "/kaggle/input/omnisvg/OmniSVG",
    "/kaggle/input/omnisvg",
    "/kaggle/working/OmniSVG",
    "f:/SVG-20260310T151742Z-1-001/SVG/OmniSVG",
]

# Auto-detect environment
if Path("/kaggle").exists():
    WORK = "/kaggle/working"
else:
    WORK = "/tmp/omnisvg"
os.makedirs(WORK, exist_ok=True)
OUTPUT_DIR = os.path.join(WORK, "omnisvg_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  SYSTEM INTERNALS (no need to edit below)                                 ║
# ╚════════════════════════════════════════════════════════════════════════════╝

SYSTEM_PROMPT = """You are an expert SVG code generator. 
Generate precise, valid SVG path commands that accurately represent the described scene or object.
Focus on capturing key shapes, spatial relationships, and visual composition."""


def find_repo() -> str:
    for path in OMNISVG_REPO_CANDIDATES:
        if os.path.exists(path) and (
            os.path.exists(os.path.join(path, "decoder.py")) or
            os.path.exists(os.path.join(path, "tokenizer.py"))
        ):
            return path
    clone_dir = os.path.join(WORK, "OmniSVG")
    if not os.path.exists(clone_dir):
        log.info("Cloning OmniSVG repo...")
        subprocess.check_call(["git", "clone", "https://github.com/OmniSVG/OmniSVG.git", clone_dir])
    return clone_dir


def render_svg(svg_str: str, size: int = RENDER_SIZE) -> Optional[Image.Image]:
    try:
        import cairosvg
        png_data = cairosvg.svg2png(bytestring=svg_str.encode('utf-8'),
                                     output_width=size, output_height=size)
        img_rgba = Image.open(io.BytesIO(png_data)).convert("RGBA")
        bg = Image.new("RGB", img_rgba.size, (255, 255, 255))
        bg.paste(img_rgba, mask=img_rgba.split()[3])
        return bg
    except Exception:
        return None


class TextToSVG:
    """
    Text-to-SVG generation system using OmniSVG.
    
    Usage:
        system = TextToSVG()
        system.load_model()
        svg_string = system.generate("A red heart")
        system.generate_batch(["prompt1", "prompt2"], output_dir="./output")
    """
    
    def __init__(self, model_size: str = MODEL_SIZE):
        self.model_size = model_size
        self.sketch_decoder = None
        self.tokenizer = None
        self.processor = None
        self.svg_tokenizer = None
        self.config = None
        self._loaded = False
    
    def load_model(self):
        """Load OmniSVG model with 4-bit quantization."""
        import yaml
        
        repo_dir = find_repo()
        log.info(f"OmniSVG repo: {repo_dir}")
        if repo_dir not in sys.path:
            sys.path.insert(0, repo_dir)
        
        from decoder import SketchDecoder
        from transformers import AutoTokenizer, AutoProcessor
        from tokenizer import SVGTokenizer
        
        config_path = os.path.join(repo_dir, "config.yaml")
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        model_cfg = self.config['models'][self.model_size]
        hf_cfg = model_cfg['huggingface']
        qwen_model = hf_cfg['qwen_model']
        omnisvg_weights = hf_cfg['omnisvg_model']
        
        log.info(f"Base model: {qwen_model}")
        log.info(f"OmniSVG weights: {omnisvg_weights}")
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            free_gb = torch.cuda.mem_get_info()[0] / 1e9
            log.info(f"GPU free: {free_gb:.1f} GB")
        
        # Tokenizer + Processor
        log.info("[1/4] Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(qwen_model, padding_side="left", trust_remote_code=True)
        self.processor = AutoProcessor.from_pretrained(qwen_model, padding_side="left", trust_remote_code=True)
        self.processor.tokenizer.padding_side = "left"
        
        # SketchDecoder (4-bit)
        log.info("[2/4] Loading model (4-bit quantization)...")
        self.sketch_decoder = SketchDecoder(
            config_path=config_path,
            model_path=qwen_model,
            model_size=self.model_size,
            pix_len=2048,
            text_len=self.config.get('text', {}).get('max_length', 200),
            torch_dtype=torch.float16,
            quantize_4bit=True,
        )
        
        # Load OmniSVG weights
        log.info("[3/4] Loading OmniSVG weights...")
        from huggingface_hub import hf_hub_download
        
        local_bin = os.path.join(omnisvg_weights, "pytorch_model.bin")
        if os.path.exists(local_bin):
            bin_path = local_bin
        else:
            log.info(f"Downloading from HuggingFace: {omnisvg_weights} (~7.7 GB)")
            bin_path = hf_hub_download(repo_id=omnisvg_weights, filename="pytorch_model.bin", resume_download=True)
        
        state_dict = torch.load(bin_path, map_location='cpu')
        self.sketch_decoder.load_state_dict(state_dict, strict=False)
        self.sketch_decoder = self.sketch_decoder.eval()
        
        # SVG tokenizer
        log.info("[4/4] SVG tokenizer...")
        self.svg_tokenizer = SVGTokenizer(config_path, model_size=self.model_size)
        
        self._loaded = True
        
        if torch.cuda.is_available():
            free_gb = torch.cuda.mem_get_info()[0] / 1e9
            log.info(f"✓ Model loaded. GPU free: {free_gb:.1f} GB")
    
    def generate(self, prompt: str, num_candidates: int = NUM_CANDIDATES,
                 temperature: float = TEMPERATURE) -> Optional[str]:
        """
        Generate SVG from a text prompt.
        
        Args:
            prompt: Text description of the desired SVG
            num_candidates: How many candidates to generate (returns best)
            temperature: Sampling temperature (0.3-0.7 recommended)
        
        Returns:
            SVG string, or None if generation failed
        """
        if not self._loaded:
            raise RuntimeError("Call load_model() first")
        
        model_cfg = self.config['model']
        BOS = model_cfg['bos_token_id']
        EOS = model_cfg['eos_token_id']
        PAD = model_cfg['pad_token_id']
        
        colors_cfg = self.config['colors']
        BLACK = colors_cfg.get('black_color_token', colors_cfg['color_token_start'] + 2)
        
        # Build chat prompt
        instruction = f"""Generate an SVG illustration for: {prompt}

Requirements:
- Create complete SVG path commands
- Include proper coordinates and colors
- Maintain visual clarity and composition"""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [{"type": "text", "text": instruction}]}
        ]
        text_input = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text_input], padding=True, truncation=True, return_tensors="pt")
        
        # Get device
        try:
            device = next(self.sketch_decoder.transformer.model.embed_tokens.parameters()).device
        except Exception:
            device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        
        input_ids = inputs['input_ids'].to(device)
        attention_mask = inputs['attention_mask'].to(device)
        
        actual_n = num_candidates + 4
        
        try:
            with torch.no_grad():
                results = self.sketch_decoder.transformer.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=MAX_SVG_TOKENS,
                    num_return_sequences=actual_n,
                    do_sample=True,
                    temperature=temperature,
                    top_p=0.88,
                    top_k=50,
                    repetition_penalty=1.05,
                    use_cache=True,
                    eos_token_id=EOS,
                    pad_token_id=PAD,
                    bos_token_id=BOS,
                )
                generated = results[:, input_ids.shape[1]:]
            
            for i in range(min(actual_n, generated.shape[0])):
                try:
                    ids = generated[i:i+1].cpu()
                    wrapped = torch.cat([
                        torch.full((1, 1), BOS),
                        ids,
                        torch.full((1, 1), EOS)
                    ], dim=1)
                    
                    xy = self.svg_tokenizer.process_generated_tokens(wrapped)
                    if len(xy) == 0:
                        continue
                    
                    tensors, colors = self.svg_tokenizer.raster_svg(xy)
                    if not tensors or not tensors[0]:
                        continue
                    
                    n_paths = len(tensors[0])
                    while len(colors) < n_paths:
                        colors.append(BLACK)
                    
                    svg = self.svg_tokenizer.apply_colors_to_svg(tensors[0], colors)
                    svg_str = svg.to_str()
                    
                    if 'width=' not in svg_str:
                        svg_str = svg_str.replace('<svg', '<svg width="448" height="448"', 1)
                    
                    # Validate
                    img = render_svg(svg_str)
                    if img is None:
                        continue
                    if np.array(img).mean() > 252:
                        continue
                    
                    return svg_str
                    
                except Exception:
                    continue
        except Exception as e:
            log.error(f"Generation error: {e}")
        
        return None
    
    def generate_batch(self, prompts: List[str], output_dir: str = OUTPUT_DIR) -> List[dict]:
        """
        Generate SVGs for a batch of prompts.
        
        Args:
            prompts: List of text descriptions
            output_dir: Where to save SVG/PNG files
        
        Returns:
            List of result dicts with keys: prompt, success, svg_path, png_path, paths
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for i, prompt in enumerate(prompts):
            log.info(f"[{i+1}/{len(prompts)}] {prompt[:60]}...")
            start = time.time()
            
            svg_str = self.generate(prompt)
            elapsed = time.time() - start
            
            if svg_str:
                svg_path = os.path.join(output_dir, f"svg_{i:03d}.svg")
                png_path = os.path.join(output_dir, f"svg_{i:03d}.png")
                
                with open(svg_path, "w") as f:
                    f.write(svg_str)
                
                img = render_svg(svg_str)
                if img:
                    img.save(png_path)
                
                n_paths = svg_str.count('<path')
                results.append({
                    "prompt": prompt, "success": True,
                    "svg_path": svg_path, "png_path": png_path,
                    "paths": n_paths, "time": round(elapsed, 1),
                })
                log.info(f"  ✓ {n_paths} paths, {elapsed:.1f}s")
            else:
                results.append({
                    "prompt": prompt, "success": False,
                    "svg_path": "", "png_path": "",
                    "paths": 0, "time": round(elapsed, 1),
                })
                log.info(f"  ✗ Failed ({elapsed:.1f}s)")
            
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        return results
    
    def unload(self):
        """Free GPU memory."""
        del self.sketch_decoder
        self.sketch_decoder = None
        self._loaded = False
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        log.info("Model unloaded.")


# ════════════════════════════════════════════════════════════════════════════
# HTML GALLERY
# ════════════════════════════════════════════════════════════════════════════
def build_gallery(results: list, output_dir: str):
    html = [
        '<!DOCTYPE html><html><head><meta charset="utf-8">',
        '<title>OmniSVG — Text to SVG</title>',
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
        '.card .prompt{font-size:13px;margin:12px 0 6px;color:#a8d8ea;font-weight:500;min-height:40px}',
        '.card .meta{font-size:12px;color:#4ecca3}',
        '.card .fail{color:#e94560;font-size:14px;font-weight:bold}',
        '</style></head><body>',
        '<h1>🎨 Text → SVG (OmniSVG)</h1>',
    ]
    ok = sum(1 for r in results if r["success"])
    html.append(f'<div class="stats">{ok}/{len(results)} successful | Model: OmniSVG {MODEL_SIZE}</div>')
    html.append('<div class="grid">')
    for r in results:
        p = r["prompt"][:80] + ("..." if len(r["prompt"]) > 80 else "")
        html.append('<div class="card">')
        if r["success"]:
            png = os.path.basename(r["png_path"])
            html.append(f'<img src="{png}" alt="{p}">')
            html.append(f'<div class="prompt">{p}</div>')
            html.append(f'<div class="meta">{r["paths"]} paths · {r["time"]}s</div>')
        else:
            html.append(f'<div style="width:200px;height:200px;margin:0 auto;background:#222;border-radius:12px;'
                         f'display:flex;align-items:center;justify-content:center">❌</div>')
            html.append(f'<div class="prompt">{p}</div>')
            html.append(f'<div class="fail">FAILED</div>')
        html.append('</div>')
    html.append('</div></body></html>')
    path = os.path.join(output_dir, "gallery.html")
    with open(path, "w") as f:
        f.write("\n".join(html))
    log.info(f"Gallery → {path}")


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log.info("=" * 70)
    log.info("Text → SVG Generation System (OmniSVG)")
    log.info("=" * 70)
    
    # ── Initialize ────────────────────────────────────────────────────────
    system = TextToSVG(model_size=MODEL_SIZE)
    system.load_model()
    
    # ── Generate ──────────────────────────────────────────────────────────
    log.info(f"\nGenerating SVGs for {len(PROMPTS)} prompts...\n")
    results = system.generate_batch(PROMPTS, OUTPUT_DIR)
    
    # ── Free model ────────────────────────────────────────────────────────
    system.unload()
    
    # ── Gallery ───────────────────────────────────────────────────────────
    build_gallery(results, OUTPUT_DIR)
    
    # ── Summary ───────────────────────────────────────────────────────────
    ok = [r for r in results if r["success"]]
    summary = {
        "model": f"OmniSVG {MODEL_SIZE}",
        "total": len(results),
        "success": len(ok),
        "results": results,
    }
    with open(os.path.join(OUTPUT_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    
    shutil.make_archive(os.path.join(WORK, "omnisvg_output"), "zip", OUTPUT_DIR)
    
    log.info("\n" + "=" * 70)
    log.info(f"✅ DONE: {len(ok)}/{len(results)} SVGs generated")
    log.info(f"   Output: {OUTPUT_DIR}")
    log.info(f"   Gallery: {os.path.join(OUTPUT_DIR, 'gallery.html')}")
    log.info(f"   Zip: {os.path.join(WORK, 'omnisvg_output.zip')}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
