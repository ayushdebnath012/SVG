"""
IntroSVG — Step 4: DPO Preference Dataset Construction  → D_pref-G
====================================================================
Paper §3.2 / §4.2:
  • Sample 10 000 prompts from D_G^direct
  • Use M_SFT to generate N=5 candidate SVGs per prompt  (50 000 total)
  • Render all candidates to PNG
  • Score all 50 000 with GPT-4o
  • Build preference pairs (prompt, S_w, S_l) using two rules:
      1. Render-Success Priority  — renderable always beats non-renderable
      2. High-Score Priority      — higher expert score wins (diff > δ)
  • Output: data/d_pref_g.jsonl

Run:
    python 04_build_dpo_data.py \
        --sft-ckpt checkpoints/m_sft/epoch_3 \
        --n-prompts 10000 \
        --n-candidates 5
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
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("step4")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DATA_DIR  = Path("data")
D_DIRECT  = DATA_DIR / "d_g_direct.jsonl"
D_PREF    = DATA_DIR / "d_pref_g.jsonl"

N_CANDIDATES = 5
SCORE_DELTA  = 1      # minimum score difference to form a preference pair (δ)
GPT_MODEL    = "gpt-4o"
MAX_RETRIES  = 5
RETRY_DELAY  = 2.0

GPT4O_SYSTEM = (
    "You are an expert SVG quality evaluator. "
    "Given the original text prompt and a rendered SVG image, "
    "output ONLY a single integer score from 0 to 10. No other text."
)


# ─────────────────────────────────────────────────────────────────────────────
# GPT-4o scoring
# ─────────────────────────────────────────────────────────────────────────────

def _score_one(prompt: str, png_bytes: bytes, client) -> int:
    """Return GPT-4o score 0-10 for (prompt, rendered SVG)."""
    b64 = base64.b64encode(png_bytes).decode()
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": GPT4O_SYSTEM},
                    {"role": "user", "content": [
                        {"type": "image_url",
                         "image_url": {"url": f"data:image/png;base64,{b64}",
                                       "detail": "low"}},
                        {"type": "text",
                         "text": f'Prompt: "{prompt}"\n\nScore this SVG (0-10):'},
                    ]},
                ],
                max_tokens=4,
                temperature=0.0,
            )
            raw = resp.choices[0].message.content.strip()
            import re
            m = re.search(r'\d+', raw)
            return min(10, max(0, int(m.group()))) if m else 5
        except Exception as e:
            log.warning(f"GPT-4o attempt {attempt+1} failed: {e}")
            time.sleep(RETRY_DELAY * (attempt + 1))
    return 5


# ─────────────────────────────────────────────────────────────────────────────
# Candidate generation using M_SFT
# ─────────────────────────────────────────────────────────────────────────────

def _load_model(ckpt: str):
    from transformers import (
        Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
    )
    import torch
    quant = BitsAndBytesConfig(load_in_8bit=True, llm_int8_skip_modules=["visual"])
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        ckpt, quantization_config=quant, device_map="auto"
    )
    model.eval()
    processor = AutoProcessor.from_pretrained(ckpt)
    return model, processor


def _gen_candidates(prompt: str, model, processor, n: int) -> List[Optional[str]]:
    """Generate n SVG candidates with temperature sampling."""
    import torch, re
    from svg_utils import gen_prompt, standardize_svg

    messages = [{"role": "user", "content": gen_prompt(prompt)}]
    text     = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    device   = next(model.parameters()).device
    inputs   = processor(text=[text], return_tensors="pt").to(device)

    candidates = []
    # Generate n times (single-sample per call keeps memory predictable)
    for _ in range(n):
        with torch.inference_mode():
            ids = model.generate(
                **inputs,
                max_new_tokens=2048,
                do_sample=True,
                temperature=0.8,
                top_p=0.95,
                repetition_penalty=1.3,
                pad_token_id=processor.tokenizer.eos_token_id,
            )
        nt  = inputs["input_ids"].shape[1]
        raw = processor.tokenizer.decode(ids[0][nt:], skip_special_tokens=True)
        m   = re.search(r'(<svg[\s>].*?</svg>)', raw, re.DOTALL | re.IGNORECASE)
        svg = standardize_svg(m.group(1)) if m else None
        candidates.append(svg)

    return candidates


# ─────────────────────────────────────────────────────────────────────────────
# Preference pair construction (paper §3.2 rules)
# ─────────────────────────────────────────────────────────────────────────────

def _build_pairs(
    prompt: str,
    candidates: List[Optional[str]],
    scores: List[Tuple[int, bool]],  # (score, is_renderable)
    delta: int = SCORE_DELTA,
) -> List[Dict[str, str]]:
    """
    Apply the two preference rules from the paper and return a list of
    (prompt, chosen, rejected) dicts.
    """
    pairs = []
    n = len(candidates)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            si, ri = scores[i]
            sj, rj = scores[j]
            ci, cj = candidates[i], candidates[j]
            if ci is None or cj is None:
                continue

            # Rule 1: renderable beats non-renderable
            if ri and not rj:
                pairs.append({"prompt": prompt, "chosen": ci, "rejected": cj})
            # Rule 2: higher score wins (with gap > delta)
            elif ri and rj and (si - sj) >= delta:
                pairs.append({"prompt": prompt, "chosen": ci, "rejected": cj})

    return pairs


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main(args):
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("pip install openai")
    from svg_utils import render_to_png, is_renderable

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Load prompts from D_G^direct
    log.info(f"Loading prompts from {D_DIRECT} ...")
    prompts: List[str] = []
    with open(D_DIRECT, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                prompts.append(json.loads(line)["prompt"])
    random.shuffle(prompts)
    prompts = prompts[:args.n_prompts]
    log.info(f"  {len(prompts):,} prompts selected")

    # Load M_SFT
    log.info(f"Loading M_SFT from {args.sft_ckpt} ...")
    model, processor = _load_model(args.sft_ckpt)

    n_pairs = 0
    with open(D_PREF, "w", encoding="utf-8") as fout:
        for i, prompt in enumerate(prompts):
            # ── Generate candidates ──────────────────────────────────────────
            candidates = _gen_candidates(prompt, model, processor, args.n_candidates)

            # ── Render + score each candidate ────────────────────────────────
            scored: List[Tuple[int, bool]] = []
            for svg in candidates:
                if svg is None:
                    scored.append((0, False))
                    continue
                png = render_to_png(svg, size=224)
                if png is None:
                    scored.append((0, False))
                else:
                    score = _score_one(prompt, png, client)
                    scored.append((score, True))

            # ── Build preference pairs ────────────────────────────────────────
            pairs = _build_pairs(prompt, candidates, scored, delta=args.delta)
            for p in pairs:
                fout.write(json.dumps(p, ensure_ascii=False) + "\n")
                n_pairs += 1

            if (i + 1) % 100 == 0:
                log.info(f"  [{i+1}/{len(prompts)}] total pairs so far: {n_pairs:,}")

    log.info(f"D_pref-G: {n_pairs:,} preference pairs → {D_PREF}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sft-ckpt",      default="checkpoints/m_sft/epoch_3")
    parser.add_argument("--n-prompts",     type=int, default=10_000)
    parser.add_argument("--n-candidates",  type=int, default=N_CANDIDATES)
    parser.add_argument("--delta",         type=int, default=SCORE_DELTA,
                        help="Minimum score gap to form a preference pair")
    args = parser.parse_args()
    main(args)
