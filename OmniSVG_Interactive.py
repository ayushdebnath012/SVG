# -*- coding: utf-8 -*-
"""
OmniSVG_Interactive.py — Interactive Text-to-SVG Generator
===========================================================
Type any prompt → get an SVG instantly.
Runs as a Gradio web app on Kaggle.

Usage:
  1. Run this cell on Kaggle (GPU T4)
  2. Click the Gradio URL that appears
  3. Type any prompt → click Generate → download your SVG
"""

import subprocess, sys, os, gc, json, logging, re, io, time
from pathlib import Path
from typing import Optional

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# ── Install dependencies ─────────────────────────────────────────────────────
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-U",
    "bitsandbytes>=0.46.1", "accelerate>=0.26.0", "transformers>=4.45.0",
    "cairosvg", "qwen-vl-utils", "einops", "ConfigArgParse", "shapely",
    "gradio>=4.0"])

import torch
import numpy as np
from PIL import Image

os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("OmniSVG-Interactive")

# ── Paths ─────────────────────────────────────────────────────────────────────
OMNISVG_CANDIDATES = [
    "/kaggle/input/datasets/rkamondal/omnisvg/OmniSVG",
    "/kaggle/input/omnisvg/OmniSVG",
    "/kaggle/input/omnisvg",
    "/kaggle/working/OmniSVG",
    "f:/SVG-20260310T151742Z-1-001/SVG/OmniSVG",
]
WORK = "/kaggle/working" if Path("/kaggle").exists() else "/tmp/omnisvg"
os.makedirs(WORK, exist_ok=True)
OUTPUT_DIR = os.path.join(WORK, "generated_svgs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MODEL_SIZE = "4B"
MAX_SVG_TOKENS = 1536

# ═══════════════════════════════════════════════════════════════════════════
# MODEL LOADING
# ═══════════════════════════════════════════════════════════════════════════
_model_state = {
    "decoder": None, "tokenizer": None, "processor": None,
    "svg_tokenizer": None, "config": None, "loaded": False,
}

SYSTEM_PROMPT = """You are an expert SVG code generator. 
Generate precise, valid SVG path commands that accurately represent the described scene or object.
Focus on capturing key shapes, spatial relationships, and visual composition."""


def _find_repo():
    for p in OMNISVG_CANDIDATES:
        if os.path.exists(p) and (os.path.exists(os.path.join(p, "decoder.py")) or
                                   os.path.exists(os.path.join(p, "tokenizer.py"))):
            return p
    d = os.path.join(WORK, "OmniSVG")
    if not os.path.exists(d):
        subprocess.check_call(["git", "clone", "https://github.com/OmniSVG/OmniSVG.git", d])
    return d


def load_model():
    """Load OmniSVG model (called once at startup)."""
    import yaml
    repo = _find_repo()
    log.info(f"Repo: {repo}")
    if repo not in sys.path:
        sys.path.insert(0, repo)

    from decoder import SketchDecoder
    from transformers import AutoTokenizer, AutoProcessor
    from tokenizer import SVGTokenizer

    cfg_path = os.path.join(repo, "config.yaml")
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)
    _model_state["config"] = cfg

    hf = cfg["models"][MODEL_SIZE]["huggingface"]
    qwen = hf["qwen_model"]
    omnisvg = hf["omnisvg_model"]

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    log.info("[1/4] Tokenizer + Processor...")
    _model_state["tokenizer"] = AutoTokenizer.from_pretrained(qwen, padding_side="left", trust_remote_code=True)
    _model_state["processor"] = AutoProcessor.from_pretrained(qwen, padding_side="left", trust_remote_code=True)
    _model_state["processor"].tokenizer.padding_side = "left"

    log.info("[2/4] SketchDecoder (4-bit)...")
    _model_state["decoder"] = SketchDecoder(
        config_path=cfg_path, model_path=qwen, model_size=MODEL_SIZE,
        pix_len=2048, text_len=cfg.get("text", {}).get("max_length", 200),
        torch_dtype=torch.float16, quantize_4bit=True,
    )

    log.info("[3/4] OmniSVG weights...")
    from huggingface_hub import hf_hub_download
    local = os.path.join(omnisvg, "pytorch_model.bin")
    if os.path.exists(local):
        bp = local
    else:
        bp = hf_hub_download(repo_id=omnisvg, filename="pytorch_model.bin", resume_download=True)
    sd = torch.load(bp, map_location="cpu")
    _model_state["decoder"].load_state_dict(sd, strict=False)
    _model_state["decoder"] = _model_state["decoder"].eval()

    log.info("[4/4] SVG tokenizer...")
    _model_state["svg_tokenizer"] = SVGTokenizer(cfg_path, model_size=MODEL_SIZE)
    _model_state["loaded"] = True

    if torch.cuda.is_available():
        log.info(f"GPU free: {torch.cuda.mem_get_info()[0]/1e9:.1f} GB")
    log.info("✓ Model ready!")


# ═══════════════════════════════════════════════════════════════════════════
# GENERATION
# ═══════════════════════════════════════════════════════════════════════════
def render_svg(svg_str, size=512):
    try:
        import cairosvg
        png = cairosvg.svg2png(bytestring=svg_str.encode(), output_width=size, output_height=size)
        rgba = Image.open(io.BytesIO(png)).convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[3])
        return bg
    except Exception:
        return None


def generate_svg(prompt: str, temperature: float = 0.5, num_candidates: int = 4) -> tuple:
    """Generate SVG from prompt. Returns (svg_string, pil_image, status_message)."""
    if not _model_state["loaded"]:
        return None, None, "❌ Model not loaded"

    cfg = _model_state["config"]["model"]
    BOS, EOS, PAD = cfg["bos_token_id"], cfg["eos_token_id"], cfg["pad_token_id"]
    colors_cfg = _model_state["config"]["colors"]
    BLACK = colors_cfg.get("black_color_token", colors_cfg["color_token_start"] + 2)

    proc = _model_state["processor"]
    decoder = _model_state["decoder"]
    svg_tok = _model_state["svg_tokenizer"]

    instruction = f"""Generate an SVG illustration for: {prompt}

Requirements:
- Create complete SVG path commands
- Include proper coordinates and colors
- Maintain visual clarity and composition"""

    msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [{"type": "text", "text": instruction}]},
    ]
    text_in = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = proc(text=[text_in], padding=True, truncation=True, return_tensors="pt")

    try:
        dev = next(decoder.transformer.model.embed_tokens.parameters()).device
    except Exception:
        dev = torch.device("cuda:0")

    ids = inputs["input_ids"].to(dev)
    mask = inputs["attention_mask"].to(dev)
    actual_n = num_candidates + 4

    start = time.time()
    try:
        with torch.no_grad():
            out = decoder.transformer.generate(
                input_ids=ids, attention_mask=mask,
                max_new_tokens=MAX_SVG_TOKENS, num_return_sequences=actual_n,
                do_sample=True, temperature=temperature,
                top_p=0.88, top_k=50, repetition_penalty=1.05,
                use_cache=True, eos_token_id=EOS, pad_token_id=PAD, bos_token_id=BOS,
            )
            gen = out[:, ids.shape[1]:]

        for i in range(min(actual_n, gen.shape[0])):
            try:
                cur = gen[i:i+1].cpu()
                wrapped = torch.cat([torch.full((1,1), BOS), cur, torch.full((1,1), EOS)], dim=1)
                xy = svg_tok.process_generated_tokens(wrapped)
                if len(xy) == 0:
                    continue
                tensors, colors = svg_tok.raster_svg(xy)
                if not tensors or not tensors[0]:
                    continue
                n = len(tensors[0])
                while len(colors) < n:
                    colors.append(BLACK)
                svg = svg_tok.apply_colors_to_svg(tensors[0], colors)
                svg_str = svg.to_str()
                if "width=" not in svg_str:
                    svg_str = svg_str.replace("<svg", '<svg width="448" height="448"', 1)
                img = render_svg(svg_str)
                if img is None or np.array(img).mean() > 252:
                    continue
                elapsed = time.time() - start
                # Save to disk
                ts = int(time.time())
                svg_path = os.path.join(OUTPUT_DIR, f"svg_{ts}.svg")
                png_path = os.path.join(OUTPUT_DIR, f"svg_{ts}.png")
                with open(svg_path, "w") as f:
                    f.write(svg_str)
                img.save(png_path)
                n_paths = svg_str.count("<path")
                return svg_str, img, f"✅ Generated in {elapsed:.1f}s | {n_paths} paths | Saved: {os.path.basename(svg_path)}"
            except Exception:
                continue
    except Exception as e:
        return None, None, f"❌ Error: {e}"

    gc.collect()
    torch.cuda.empty_cache()
    return None, None, "❌ No valid SVG generated. Try a different prompt or higher temperature."


# ═══════════════════════════════════════════════════════════════════════════
# GRADIO UI
# ═══════════════════════════════════════════════════════════════════════════
def build_app():
    import gradio as gr

    def on_generate(prompt, temperature, candidates):
        if not prompt.strip():
            return None, None, "⚠️ Please enter a prompt"
        svg_str, img, status = generate_svg(prompt.strip(), temperature, int(candidates))
        if svg_str:
            # Save SVG for download
            tmp = os.path.join(OUTPUT_DIR, "latest.svg")
            with open(tmp, "w") as f:
                f.write(svg_str)
            return img, tmp, status
        return None, None, status

    with gr.Blocks(
        title="OmniSVG — Text to SVG",
        theme=gr.themes.Soft(primary_hue="teal"),
        css="""
        .main-title { text-align: center; margin: 20px 0; }
        .main-title h1 { 
            background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            font-size: 2.5em; 
        }
        """
    ) as app:
        gr.HTML('<div class="main-title"><h1>🎨 OmniSVG — Text to SVG</h1>'
                '<p style="color:#888">Type any description → get a vector graphic</p></div>')

        with gr.Row():
            with gr.Column(scale=2):
                prompt_box = gr.Textbox(
                    label="Prompt",
                    placeholder="Describe what you want... e.g. 'A red heart with smooth edges'",
                    lines=3,
                )
                with gr.Row():
                    temp_slider = gr.Slider(0.1, 1.0, value=0.5, step=0.05, label="Temperature",
                                            info="Lower = more precise, Higher = more creative")
                    cand_slider = gr.Slider(1, 8, value=4, step=1, label="Candidates",
                                            info="More = slower but better quality")
                gen_btn = gr.Button("🚀 Generate SVG", variant="primary", size="lg")
                status_box = gr.Textbox(label="Status", interactive=False)

            with gr.Column(scale=2):
                preview = gr.Image(label="Preview", height=448)
                download = gr.File(label="Download SVG")

        # Examples
        gr.Examples(
            examples=[
                ["A red heart shape with smooth curved edges, centered."],
                ["A yellow star with five sharp points, flat color."],
                ["A cartoon cat wearing a top hat, simple illustration"],
                ["A coffee cup with steam rising, brown and white"],
                ["Desert landscape: orange sky, sand dunes, green cactus"],
                ["A rainbow arc with seven color bands"],
                ["A rocket launching with orange flame, space background"],
                ["A golden trophy cup with handles on both sides"],
                ["Profile silhouette: black side view of head with glasses"],
                ["A blue whale swimming, minimal design"],
            ],
            inputs=[prompt_box],
        )

        gen_btn.click(on_generate, [prompt_box, temp_slider, cand_slider],
                      [preview, download, status_box])

    return app


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    log.info("=" * 60)
    log.info("OmniSVG — Interactive Text-to-SVG Generator")
    log.info("=" * 60)

    # Load model once
    load_model()

    # Launch Gradio
    app = build_app()
    app.launch(share=True, server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
