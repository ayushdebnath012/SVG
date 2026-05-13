# %% [markdown]
# # OmniSVG Baseline Evaluation
#
# Runs the **pretrained** OmniSVG model (no RLRF fine-tuning) on the same eval
# captions used by the RLRF training run and scores each SVG with the full
# reward model (72B VLM judge + CLIP).
#
# Use this notebook to establish the baseline numbers that the RLRF run must beat.
# After RLRF training completes, run with LORA_ADAPTER pointing at the adapter
# directory to get the fine-tuned scores in the same format.
#
# Setup (run once in the Kaggle session):
#   !git clone https://github.com/ayush31010/SVG.git /kaggle/working/SVG_repo
#
# Expected outputs:
#   /kaggle/working/omnisvg_baseline/
#       eval_results.json          — per-caption scores and SVG text
#       summary.json               — aggregate metrics
#       svgs/                      — one .svg file per caption (best candidate)
#       pngs/                      — rendered PNG for each SVG

# %%
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import torch

IS_KAGGLE = Path("/kaggle").exists()

# ── Paths ──────────────────────────────────────────────────────────────────────
if IS_KAGGLE:
    SVG_REPO     = Path("/kaggle/working/SVG_repo")
    TEXT2SVG_DIR = SVG_REPO / "Text2SVG"
    OMNISVG_DIR  = SVG_REPO / "OmniSVG"
    WORK_ROOT    = Path("/kaggle/working")
else:
    # Local: assume we are inside SVG/Text2SVG
    TEXT2SVG_DIR = Path(__file__).resolve().parent
    OMNISVG_DIR  = TEXT2SVG_DIR.parent / "OmniSVG"
    WORK_ROOT    = TEXT2SVG_DIR

CONFIG_DIR   = TEXT2SVG_DIR / "configs"
OUTPUT_DIR   = WORK_ROOT / "omnisvg_baseline"
SVG_DIR      = OUTPUT_DIR / "svgs"
PNG_DIR      = OUTPUT_DIR / "pngs"

for d in [OUTPUT_DIR, SVG_DIR, PNG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Config knobs ───────────────────────────────────────────────────────────────
OMNISVG_MODEL_SIZE  = "4B"   # "4B" for T4/A100-40GB, "8B" for A100-80GB / H100 / H200
CANDIDATES_PER_CAPTION = 4   # number of SVG candidates to generate per caption
MAX_NEW_TOKENS      = 1024
# Set to a directory path to load a saved LoRA adapter (post-RLRF eval):
LORA_ADAPTER        = None   # e.g. "/kaggle/working/qwen3_text2svg_grpo_lora"

print("TEXT2SVG_DIR :", TEXT2SVG_DIR)
print("OMNISVG_DIR  :", OMNISVG_DIR)
print("OUTPUT_DIR   :", OUTPUT_DIR)
print("Model size   :", OMNISVG_MODEL_SIZE)
print("LoRA adapter :", LORA_ADAPTER or "(none — baseline)")

# %% [markdown]
# ## Install dependencies

# %%
if IS_KAGGLE:
    subprocess.run(["apt-get", "install", "-y", "-q", "libcairo2"], check=False)
    req = TEXT2SVG_DIR / "requirements.txt"
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)], check=True)

# %% [markdown]
# ## Load config

# %%
for p in [str(TEXT2SVG_DIR), str(OMNISVG_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from text2svg_rlrf.config import load_config

cfg = load_config(str(CONFIG_DIR))
print("judge model      :", cfg.reward.judge_model_name_or_path)
print("eval captions    :", cfg.eval.caption_files)
print("candidates/cap   :", cfg.eval.candidates_per_caption)
print("judge 4-bit      :", cfg.reward.judge_load_in_4bit)

# %% [markdown]
# ## Load OmniSVG (pretrained, no LoRA unless LORA_ADAPTER is set)

# %%
from text2svg_rlrf.omnisvg_policy import load_omnisvg_policy

print(f"Loading OmniSVG {OMNISVG_MODEL_SIZE}…")
bundle = load_omnisvg_policy(
    omnisvg_dir=str(OMNISVG_DIR),
    model_size=OMNISVG_MODEL_SIZE,
    lora_cfg=None,          # no LoRA — pure pretrained baseline
    cache_dir=cfg.runtime.cache_dir,
)

if LORA_ADAPTER:
    from peft import PeftModel
    from text2svg_rlrf.omnisvg_policy import OmniSVGBundle
    print(f"Attaching LoRA adapter from {LORA_ADAPTER}…")
    bundle = OmniSVGBundle(
        model=PeftModel.from_pretrained(bundle.model, LORA_ADAPTER),
        tokenizer=bundle.tokenizer,
        svg_tokenizer=bundle.svg_tokenizer,
        processor=bundle.processor,
        bos_token_id=bundle.bos_token_id,
        eos_token_id=bundle.eos_token_id,
        pad_token_id=bundle.pad_token_id,
    )

bundle.model.eval()
print("Model ready on device:", next(bundle.model.parameters()).device)

# %% [markdown]
# ## Load reward model

# %%
from text2svg_rlrf.reward import Text2SVGReward

reward_model = Text2SVGReward(cfg.runtime, cfg.svg, cfg.reward)
print("Reward model ready.")

# %% [markdown]
# ## Load eval captions

# %%
from text2svg_rlrf.config import DataConfig
from text2svg_rlrf.data import load_captions

eval_data_cfg = DataConfig(
    caption_files=cfg.eval.caption_files,
    unique_captions=cfg.eval.max_captions,
    caption_keys=cfg.data.caption_keys,
    shuffle=False,
)
captions = load_captions(eval_data_cfg, cfg.runtime.seed)
print(f"Eval captions loaded: {len(captions)}")
for c in captions[:5]:
    print(" •", c)

# %% [markdown]
# ## Generate + score

# %%
from text2svg_rlrf.omnisvg_policy import decode_omnisvg_tokens_to_svg, generate_omnisvg_rollouts

rows = []
for i, caption in enumerate(captions):
    print(f"\n[{i+1}/{len(captions)}] {caption[:80]}")

    rollout_group = generate_omnisvg_rollouts(
        bundle, [caption], CANDIDATES_PER_CAPTION, max_new_tokens=MAX_NEW_TOKENS
    )[0]

    prompt = bundle.format_prompt(caption)
    prompt_len = bundle.tokenizer(prompt, return_tensors="pt").input_ids.size(1)

    best_reward = -99.0
    best_svg    = ""
    candidates  = []

    for j, seq in enumerate(rollout_group):
        svg = decode_omnisvg_tokens_to_svg(bundle, seq, prompt_len)
        scored = reward_model.score(svg, caption)

        candidates.append({
            "candidate": j,
            "reward": scored.reward,
            "valid": scored.render.valid,
            "svg_chars": len(svg),
            "visible_elements": scored.render.visible_elements,
            "parts": scored.parts,
        })

        if scored.reward > best_reward and scored.render.valid:
            best_reward = scored.reward
            best_svg    = svg
            best_render = scored.render

        print(f"  cand {j}: reward={scored.reward:.3f}  valid={scored.render.valid}"
              f"  paths={scored.render.visible_elements}  chars={len(svg)}")

    # save best SVG
    safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in caption[:50]).strip()
    slug = f"{i+1:04d}_{safe}"

    if best_svg:
        (SVG_DIR / f"{slug}.svg").write_text(best_svg, encoding="utf-8")
        # render PNG
        try:
            import cairosvg
            from PIL import Image
            png = cairosvg.svg2png(bytestring=best_svg.encode(), output_width=512, output_height=512)
            Image.open(io.BytesIO(png)).convert("RGB").save(PNG_DIR / f"{slug}.png")
        except Exception as e:
            print(f"  PNG render failed: {e}")

    rows.append({
        "caption": caption,
        "best_reward": best_reward,
        "best_valid": best_svg != "",
        "best_svg_chars": len(best_svg),
        "slug": slug,
        "candidates": candidates,
    })

# %% [markdown]
# ## Summary

# %%
valid_rows   = [r for r in rows if r["best_valid"]]
mean_reward  = sum(r["best_reward"] for r in rows) / max(len(rows), 1)
valid_rate   = len(valid_rows) / max(len(rows), 1)
mean_chars   = sum(r["best_svg_chars"] for r in valid_rows) / max(len(valid_rows), 1)

summary = {
    "model": f"OmniSVG-{OMNISVG_MODEL_SIZE}",
    "lora_adapter": LORA_ADAPTER or "none (baseline)",
    "captions_evaluated": len(rows),
    "valid_rate": round(valid_rate, 4),
    "mean_best_reward": round(mean_reward, 4),
    "mean_svg_chars_valid": round(mean_chars, 1),
}

print("\n=== Summary ===")
for k, v in summary.items():
    print(f"  {k}: {v}")

(OUTPUT_DIR / "eval_results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
(OUTPUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(f"\nResults saved to {OUTPUT_DIR}")

# %% [markdown]
# ## Per-caption reward table

# %%
print(f"\n{'#':<4} {'reward':>7}  {'valid':>5}  {'chars':>6}  caption")
print("-" * 72)
for r in sorted(rows, key=lambda x: -x["best_reward"]):
    print(f"{rows.index(r)+1:<4} {r['best_reward']:>7.3f}  {str(r['best_valid']):>5}  "
          f"{r['best_svg_chars']:>6}  {r['caption'][:55]}")
