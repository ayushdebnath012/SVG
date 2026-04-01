# -*- coding: utf-8 -*-
"""
test_finetuned_vlm.py
Run on Colab T4 GPU. Upload finetuned_vlm_adapter/ folder before running.

Tests the fine-tuned Qwen2-VL LoRA adapter on a set of prompts,
renders SVG outputs to PNGs, and reports CLIP scores.
"""

import subprocess, sys, os, re, io, json
from pathlib import Path

# ── Install deps ──
subprocess.run([sys.executable, "-m", "pip", "install", "-q",
    "transformers>=4.40", "accelerate>=0.27", "peft>=0.10",
    "bitsandbytes>=0.43", "cairosvg", "open_clip_torch", "pillow"], check=True)
subprocess.run(["apt-get", "install", "-y", "-qq", "libcairo2"], capture_output=True)

import torch
import numpy as np
from PIL import Image

print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE'}")

# ════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════
ADAPTER_PATH  = "./finetuned_vlm_adapter"   # unzipped from local C:\Users\USER_HP\Desktop\CMU Project\SVG\finetuned_vlm_adapter
BASE_MODEL    = "Qwen/Qwen2-VL-2B-Instruct"
OUTPUT_DIR    = "./vlm_test_outputs"
Path(OUTPUT_DIR).mkdir(exist_ok=True)

TEST_PROMPTS = [
    # Seen during training (should perform well)
    "a red apple",
    "a yellow sun",
    "a gear icon",
    "a home icon",
    "a music note",
    # Unseen / generalization test
    "a cloud",
    "a diamond",
    "a flag",
    "a clock",
    "a star with five points",
]

# ════════════════════════════════════════════════════════════════════════
# LOAD MODEL
# ════════════════════════════════════════════════════════════════════════
from transformers import AutoTokenizer, Qwen2VLForConditionalGeneration, BitsAndBytesConfig
from peft import PeftModel

print("\nLoading base model with 4-bit quantization …")
quant_cfg = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
)
base = Qwen2VLForConditionalGeneration.from_pretrained(
    BASE_MODEL,
    quantization_config=quant_cfg,
    device_map={"": 0},
    trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained(ADAPTER_PATH, trust_remote_code=True)

print("Loading LoRA adapter …")
model = PeftModel.from_pretrained(base, ADAPTER_PATH)
model.eval()
print("Model ready.\n")


# ════════════════════════════════════════════════════════════════════════
# INFERENCE
# ════════════════════════════════════════════════════════════════════════
@torch.inference_mode()
def generate_svg(prompt: str, max_new_tokens: int = 1500) -> str:
    messages = [
        {"role": "system", "content": (
            "You are an SVG generation assistant. "
            "Given a text description of an icon, output clean minimal SVG code. "
            "Output ONLY the SVG, no explanation."
        )},
        {"role": "user", "content": f"Generate an SVG icon for: {prompt}"},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    out = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.1,
    )
    response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    m = re.search(r"(<svg[\s\S]*?</svg>)", response)
    return m.group(1) if m else response


def render_svg(svg_str: str, size: int = 256) -> Image.Image | None:
    try:
        import cairosvg
        png = cairosvg.svg2png(bytestring=svg_str.encode(), output_width=size, output_height=size)
        return Image.open(io.BytesIO(png)).convert("RGB")
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════
# CLIP SCORER
# ════════════════════════════════════════════════════════════════════════
import open_clip
clip_model, _, clip_prep = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
clip_tok = open_clip.get_tokenizer("ViT-B-32")
clip_model = clip_model.float().eval().cuda()

def clip_score(image: Image.Image, prompt: str) -> float:
    img_t = clip_prep(image).unsqueeze(0).cuda()
    txt_t = clip_tok([prompt]).cuda()
    with torch.no_grad():
        iv = clip_model.encode_image(img_t); iv /= iv.norm(dim=-1, keepdim=True)
        tv = clip_model.encode_text(txt_t);  tv /= tv.norm(dim=-1, keepdim=True)
    return (iv @ tv.T).item() * 100


# ════════════════════════════════════════════════════════════════════════
# RUN TESTS
# ════════════════════════════════════════════════════════════════════════
results = []
slug = lambda s: re.sub(r"[^\w]+", "_", s).strip("_")[:40]

print(f"{'Prompt':<35} {'SVG len':>8} {'Rendered':>9} {'CLIP':>7}")
print("-" * 65)

for i, prompt in enumerate(TEST_PROMPTS):
    svg = generate_svg(prompt)
    stem = f"{i:02d}_{slug(prompt)}"

    # Save raw SVG always
    svg_path = f"{OUTPUT_DIR}/{stem}.svg"
    Path(svg_path).write_text(svg, encoding="utf-8")

    rendered = render_svg(svg)
    ok = rendered is not None

    score = 0.0
    if ok:
        rendered.save(f"{OUTPUT_DIR}/{stem}.png")
        score = clip_score(rendered, prompt)

    results.append({"prompt": prompt, "svg_len": len(svg), "rendered": ok, "clip": score})
    print(f"{prompt:<35} {len(svg):>8}  {'✓' if ok else '✗':>8}  {score:>6.2f}")

# ════════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════════
n_ok    = sum(r["rendered"] for r in results)
scores  = [r["clip"] for r in results if r["rendered"]]
print("\n" + "=" * 65)
print(f"Rendered:   {n_ok}/{len(results)}")
if scores:
    print(f"CLIP mean:  {np.mean(scores):.2f}")
    print(f"CLIP median:{np.median(scores):.2f}")
    print(f"CLIP range: {min(scores):.2f} – {max(scores):.2f}")

with open(f"{OUTPUT_DIR}/test_summary.json", "w") as f:
    json.dump({"n_total": len(results), "n_rendered": n_ok,
               "clip_mean": np.mean(scores) if scores else 0,
               "results": results}, f, indent=2)
print(f"\nOutputs → {OUTPUT_DIR}/")

# Display in Colab
try:
    from IPython.display import display, Image as IPImage
    pngs = sorted(Path(OUTPUT_DIR).glob("*.png"))
    print(f"\nRendered images ({len(pngs)}):")
    for p in pngs:
        print(p.name)
        display(IPImage(str(p), width=200))
except Exception:
    pass
