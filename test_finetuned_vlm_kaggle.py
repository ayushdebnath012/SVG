# -*- coding: utf-8 -*-
"""
test_finetuned_vlm_kaggle.py
Run on Kaggle T4 GPU AFTER DiffuSVG_Pipeline_v2.py completes.
Reads the adapter from /kaggle/working/qwen2vl_svg_lora/final_adapter
and appends test results into the full output zip.
"""

import subprocess, sys, os, re, io, json, shutil
from pathlib import Path

import torch
import numpy as np
from PIL import Image

ADAPTER_PATH = "/kaggle/working/qwen2vl_svg_lora/final_adapter"
BASE_MODEL   = "Qwen/Qwen2-VL-2B-Instruct"
OUTPUT_DIR   = "/kaggle/working/vlm_test_outputs"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE'}")
print(f"Adapter: {ADAPTER_PATH}")
assert Path(ADAPTER_PATH).exists(), \
    "Adapter not found — run DiffuSVG_Pipeline_v2.py first!"

TEST_PROMPTS = [
    # ── Seen during training ──
    "a red apple",
    "a yellow sun",
    "a gear icon",
    "a home icon",
    "a music note",
    "a blue circle",
    "a green tree",
    "a rocket",
    "a cat face",
    "a phone icon",
    # ── Unseen / generalisation ──
    "a cloud",
    "a diamond",
    "a flag",
    "a clock",
    "a star with five points",
    "a bicycle",
    "a lightning bolt",
    "a pizza slice",
    "a coffee cup",
    "a camera",
]

# ════════════════════════════════════════════════════════════════════════
# LOAD MODEL + ADAPTER
# ════════════════════════════════════════════════════════════════════════
from transformers import AutoTokenizer, Qwen2VLForConditionalGeneration, BitsAndBytesConfig
from peft import PeftModel

print("\nLoading base model (4-bit) …")
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

print("Merging LoRA adapter …")
model = PeftModel.from_pretrained(base, ADAPTER_PATH)
model.eval()
print("Model ready.\n")


# ════════════════════════════════════════════════════════════════════════
# HELPERS
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


def render_svg(svg_str: str, size: int = 256):
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
print("Loading CLIP …")
clip_model, _, clip_prep = open_clip.create_model_and_transforms(
    "ViT-B-32", pretrained="laion2b_s34b_b79k"
)
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
slug = lambda s: re.sub(r"[^\w]+", "_", s).strip("_")[:40]

results = []
print(f"\n{'#':<4} {'Prompt':<32} {'SVG len':>8} {'OK':>4} {'CLIP':>7}")
print("-" * 60)

for i, prompt in enumerate(TEST_PROMPTS):
    svg  = generate_svg(prompt)
    stem = f"{i:02d}_{slug(prompt)}"

    (Path(OUTPUT_DIR) / f"{stem}.svg").write_text(svg, encoding="utf-8")

    rendered = render_svg(svg)
    score = 0.0
    if rendered is not None:
        rendered.save(str(Path(OUTPUT_DIR) / f"{stem}.png"))
        score = clip_score(rendered, prompt)

    results.append({
        "prompt":   prompt,
        "svg_len":  len(svg),
        "rendered": rendered is not None,
        "clip":     round(score, 3),
        "seen":     i < 10,   # first 10 are training prompts
    })
    print(f"{i:<4} {prompt:<32} {len(svg):>8}  {'✓' if rendered else '✗':>3}  {score:>6.2f}")

# ════════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════════
n_ok   = sum(r["rendered"] for r in results)
scores = [r["clip"] for r in results if r["rendered"]]
seen_scores   = [r["clip"] for r in results if r["rendered"] and r["seen"]]
unseen_scores = [r["clip"] for r in results if r["rendered"] and not r["seen"]]

print("\n" + "=" * 60)
print(f"Rendered:        {n_ok}/{len(results)}")
if scores:
    print(f"CLIP mean:       {np.mean(scores):.2f}")
    print(f"CLIP (seen):     {np.mean(seen_scores):.2f}" if seen_scores else "")
    print(f"CLIP (unseen):   {np.mean(unseen_scores):.2f}" if unseen_scores else "")

summary = {
    "n_total":        len(results),
    "n_rendered":     n_ok,
    "clip_mean":      float(np.mean(scores)) if scores else 0,
    "clip_seen_mean": float(np.mean(seen_scores)) if seen_scores else 0,
    "clip_unseen_mean": float(np.mean(unseen_scores)) if unseen_scores else 0,
    "results":        results,
}
with open(f"{OUTPUT_DIR}/test_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

# ════════════════════════════════════════════════════════════════════════
# REPACK INTO FULL ZIP
# ════════════════════════════════════════════════════════════════════════
import zipfile
archive = "/kaggle/working/diffusvg_full_output.zip"
print(f"\nAppending test results to {archive} …")
with zipfile.ZipFile(archive, "a", zipfile.ZIP_DEFLATED) as zf:
    for fpath in Path(OUTPUT_DIR).rglob("*"):
        if fpath.is_file():
            zf.write(fpath, "vlm_test_outputs/" + fpath.relative_to(OUTPUT_DIR).as_posix())
print("Done. Download diffusvg_full_output.zip from Kaggle output panel.")
