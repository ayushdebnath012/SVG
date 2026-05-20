"""
IntroSVG — Step 2: Synthetic SFT Data Construction via GPT-4o
==============================================================
Paper §3.2:
  Uses an early-checkpoint model to generate 50 K draft SVGs, then calls
  GPT-4o on (prompt, rendered PNG) to produce structured critiques.

  Outputs (LLaMA-Factory compatible format):
    D_G^direct     → data/d_g_direct.jsonl      (from step 1, already exists)
    D_G^correction → data/d_g_correction.jsonl  (~50 K correction samples)
    D_C            → data/d_c.jsonl             (~50 K critic samples, images in data/images/)
    D_SFT          → data/d_sft.jsonl           (all three merged)
    data/dataset_info.json                      (LLaMA-Factory dataset registry)

  Critic rows use the <image> placeholder format matching gitcat404/IntroSVG-train:
    {"messages": [{"role":"user","content":"<image>\\n<critic_text>"},
                  {"role":"assistant","content":"{json}"}],
     "images": ["images/00001.png"]}

Prerequisites:
    export OPENAI_API_KEY="sk-..."
    export EARLY_CKPT="Qwen/Qwen2.5-VL-7B-Instruct"

Run:
    python 02_build_sft_data.py --n-prompts 50000 --model-name $EARLY_CKPT
"""

import argparse
import base64
import io
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("step2")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DATA_DIR  = Path("data")
IMG_DIR   = DATA_DIR / "images"        # PNGs referenced by critic rows
D_DIRECT     = DATA_DIR / "d_g_direct.jsonl"
D_CORRECTION = DATA_DIR / "d_g_correction.jsonl"
D_CRITIC     = DATA_DIR / "d_c.jsonl"
D_SFT        = DATA_DIR / "d_sft.jsonl"
DATASET_INFO = DATA_DIR / "dataset_info.json"

GPT_MODEL    = "gpt-4o"
MAX_RETRIES  = 5
RETRY_DELAY  = 2.0

GPT4O_SYSTEM = (
    "You are an expert SVG quality evaluator. "
    "Given the original text prompt and the rendered SVG image, "
    "output ONLY valid JSON with keys: score (0-10 integer), "
    "critique (one sentence of main issues), suggestions (one sentence of fixes). "
    'Example: {"score": 6, "critique": "Missing leaf detail.", "suggestions": "Add a curved path for the leaf."}'
)


# ─────────────────────────────────────────────────────────────────────────────
# GPT-4o helpers
# ─────────────────────────────────────────────────────────────────────────────

def _png_to_b64(png_bytes: bytes) -> str:
    return base64.b64encode(png_bytes).decode()


def _call_gpt4o(prompt: str, png_bytes: bytes, client) -> Optional[Dict[str, Any]]:
    """Call GPT-4o with (text prompt, rendered PNG) → JSON critique."""
    b64 = _png_to_b64(png_bytes)
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": GPT4O_SYSTEM},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type":      "image_url",
                                "image_url": {"url": f"data:image/png;base64,{b64}",
                                              "detail": "low"},
                            },
                            {"type": "text",
                             "text": f'Original design prompt: "{prompt}"\n\nEvaluate this rendered SVG.'},
                        ],
                    },
                ],
                max_tokens=256,
                temperature=0.0,
            )
            raw = resp.choices[0].message.content.strip()
            # Strip markdown fences if present
            import re
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                parsed = json.loads(m.group(0))
                return {
                    "score":       int(float(parsed.get("score", 5))),
                    "critique":    str(parsed.get("critique", "")),
                    "suggestions": str(parsed.get("suggestions", "")),
                }
        except Exception as e:
            log.warning(f"GPT-4o attempt {attempt+1} failed: {e}")
            time.sleep(RETRY_DELAY * (attempt + 1))
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Draft generation with early-checkpoint model
# ─────────────────────────────────────────────────────────────────────────────

def _load_gen_model(model_name: str):
    from transformers import (
        Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
    )
    import torch
    quant = BitsAndBytesConfig(load_in_8bit=True, llm_int8_skip_modules=["visual"])
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_name, quantization_config=quant, device_map="auto"
    )
    model.eval()
    processor = AutoProcessor.from_pretrained(model_name)
    return model, processor


def _generate_draft(prompt: str, model, processor) -> Optional[str]:
    """Generate one SVG draft from the early-checkpoint model."""
    import torch, re
    from svg_utils import gen_prompt
    messages = [{"role": "user", "content": gen_prompt(prompt)}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    device = next(model.parameters()).device
    inputs = processor(text=[text], return_tensors="pt").to(device)
    with torch.inference_mode():
        ids = model.generate(
            **inputs,
            max_new_tokens=2048,
            do_sample=True,
            temperature=0.8,
            top_p=0.9,
            repetition_penalty=1.3,
            pad_token_id=processor.tokenizer.eos_token_id,
        )
    n = inputs["input_ids"].shape[1]
    raw = processor.tokenizer.decode(ids[0][n:], skip_special_tokens=True).strip()
    m = re.search(r'(<svg[\s>].*?</svg>)', raw, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else None


# ─────────────────────────────────────────────────────────────────────────────
# Build D_C and D_G^correction
# ─────────────────────────────────────────────────────────────────────────────

_img_counter = 0

def _format_critic_row(prompt: str, png_bytes: bytes, critique: dict) -> dict:
    """
    D_C row in LLaMA-Factory vision format (matches gitcat404/IntroSVG-train).
    PNG is saved to data/images/; 'images' field holds the relative path.
    The <image> placeholder in content is resolved by LLaMA-Factory at train time.
    """
    global _img_counter
    _img_counter += 1
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    img_filename = f"{_img_counter:06d}.png"
    img_rel_path = f"images/{img_filename}"
    (IMG_DIR / img_filename).write_bytes(png_bytes)

    critic_text = (
        f'You are a professional SVG design critic. Please analyze the input '
        f'AI-generated SVG draft according to the "Original Design Prompt".\n\n'
        f'**Original Design Prompt**: "{prompt}"\n\n'
        f'Your task is to output a structured critique report, strictly following '
        f'the JSON format: {{"score": <0-10>, "critique": "<issues>", "suggestions": "<fixes>"}}'
    )

    return {
        "messages": [
            {"role": "user",      "content": f"<image>\n{critic_text}"},
            {"role": "assistant", "content": json.dumps(critique, ensure_ascii=False)},
        ],
        "images":   [img_rel_path],
        "_type":    "critic",     # internal tag; stripped before LLaMA-Factory sees it
    }


def _format_correction_row(
    prompt: str,
    failed_svg: str,
    critique: dict,
    gold_svg: str,
) -> dict:
    """D_G^correction row — text-only, LLaMA-Factory format."""
    from svg_utils import correction_prompt
    return {
        "messages": [
            {"role": "user",      "content": correction_prompt(prompt, failed_svg, critique)},
            {"role": "assistant", "content": gold_svg},
        ],
    }


def _format_generator_row(prompt: str, svg: str) -> dict:
    """D_G^direct row — text-only, LLaMA-Factory format."""
    from svg_utils import gen_prompt
    return {
        "messages": [
            {"role": "user",      "content": gen_prompt(prompt)},
            {"role": "assistant", "content": svg},
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def _strip_internal(row: dict) -> dict:
    """Remove internal-only keys before writing to LLaMA-Factory JSONL."""
    return {k: v for k, v in row.items() if not k.startswith("_")}


def main(args):
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("pip install openai")

    from svg_utils import render_to_png, is_renderable, standardize_svg

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    # Load D_G^direct
    log.info(f"Loading D_G^direct from {D_DIRECT} ...")
    direct_rows: List[dict] = []
    with open(D_DIRECT, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                direct_rows.append(json.loads(line))
    log.info(f"  {len(direct_rows):,} direct samples loaded")

    random.shuffle(direct_rows)
    sample_rows = direct_rows[:args.n_prompts]

    # Load early-checkpoint model for draft generation
    log.info(f"Loading early-checkpoint model: {args.model_name}")
    model, processor = _load_gen_model(args.model_name)

    n_ok = 0
    with open(D_CORRECTION, "w", encoding="utf-8") as f_corr, \
         open(D_CRITIC,     "w", encoding="utf-8") as f_crit:

        for i, row in enumerate(sample_rows):
            prompt   = row["prompt"]
            gold_svg = row["svg"]

            # ── Generate draft ───────────────────────────────────────────────
            draft = _generate_draft(prompt, model, processor)
            if draft is None:
                continue

            draft = standardize_svg(draft) or draft

            # ── Render draft ─────────────────────────────────────────────────
            png = render_to_png(draft, size=224)
            if png is None:
                # Non-renderable draft: still useful as correction training
                png = render_to_png(
                    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">'
                    '<rect fill="#ffffff" width="200" height="200"/></svg>',
                    size=224,
                )

            # ── Call GPT-4o ──────────────────────────────────────────────────
            critique = _call_gpt4o(prompt, png, client)
            if critique is None:
                continue

            # ── Write D_C row (saves PNG to disk) ───────────────────────────
            critic_row = _format_critic_row(prompt, png, critique)
            f_crit.write(json.dumps(_strip_internal(critic_row), ensure_ascii=False) + "\n")

            # ── Write D_G^correction row ─────────────────────────────────────
            corr_row = _format_correction_row(prompt, draft, critique, gold_svg)
            f_corr.write(json.dumps(corr_row, ensure_ascii=False) + "\n")

            n_ok += 1
            if n_ok % 100 == 0:
                log.info(f"  [{i+1}/{len(sample_rows)}] generated {n_ok} pairs")

    log.info(f"D_C + D_G^correction: {n_ok:,} pairs")

    # ── Merge into D_SFT ──────────────────────────────────────────────────────
    log.info("Merging into D_SFT ...")
    with open(D_SFT, "w", encoding="utf-8") as fout:
        # D_G^direct (convert raw {"prompt","svg"} to messages format)
        with open(D_DIRECT, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                fout.write(json.dumps(
                    _format_generator_row(row["prompt"], row["svg"]),
                    ensure_ascii=False,
                ) + "\n")
        # D_G^correction
        with open(D_CORRECTION, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    fout.write(line)
        # D_C
        with open(D_CRITIC, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    fout.write(line)

    total = sum(1 for ln in open(D_SFT, encoding="utf-8") if ln.strip())
    log.info(f"D_SFT written: {total:,} rows → {D_SFT}")

    # ── Write dataset_info.json for LLaMA-Factory ─────────────────────────────
    dataset_info = {
        "d_sft": {
            "file_name": "d_sft.jsonl",
            "formatting": "sharegpt",
            "columns": {"messages": "messages", "images": "images"},
        },
        "d_c": {
            "file_name": "d_c.jsonl",
            "formatting": "sharegpt",
            "columns": {"messages": "messages", "images": "images"},
        },
        "d_pref_g": {
            "file_name": "d_pref_g.jsonl",
            "formatting": "sharegpt",
            "ranking": True,
            "columns": {"messages": "messages", "chosen": "chosen", "rejected": "rejected"},
        },
    }
    DATASET_INFO.write_text(json.dumps(dataset_info, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"dataset_info.json written → {DATASET_INFO}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-prompts",  type=int, default=50_000,
                        help="Number of prompts to generate drafts for")
    parser.add_argument("--model-name", default=os.environ.get(
                            "EARLY_CKPT", "Qwen/Qwen2.5-VL-7B-Instruct"),
                        help="Early checkpoint (or base model) for draft generation")
    args = parser.parse_args()
    main(args)
