"""
IntroSVG — Step 1: Data Collection and Standardisation  → D_G^direct
=======================================================================
Paper §3.1 – §3.2:
  • Pull SVGs from LLM4SVG, OmniSVG (MMSVG-2M), and SVGen (SVG-1M-Json)
  • Apply D_final standardisation pipeline
  • Filter: colorful, renderable, ≤ 8 000 tokens
  • Output: data/d_g_direct.jsonl  (~200 K rows)
            Each row: {"prompt": "...", "svg": "<svg ...>...</svg>"}

Run (single GPU / CPU):
    python 01_standardize_data.py

Run (multi-GPU parallel workers via torchrun):
    torchrun --nproc_per_node=8 01_standardize_data.py
"""

import argparse
import json
import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from svg_utils import standardize_svg, is_colorful, is_renderable

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("step1")

# ── Config ────────────────────────────────────────────────────────────────────
OUT_DIR    = Path("data")
OUT_FILE   = OUT_DIR / "d_g_direct.jsonl"
MAX_TOKENS = 8_000          # paper: remove SVGs with sequence length > 8 000 tokens
NUM_WORKERS = 16            # parallel standardisation workers
TOKENIZER_NAME = "Qwen/Qwen2.5-VL-7B-Instruct"

# HuggingFace dataset identifiers (verify these match current HF hub names)
DATASETS = [
    # (hf_dataset_id,  split,   text_col,   svg_col)
    ("jdl777/LLM4SVG",             "train", "caption",     "svg"),
    ("OmniSVG/MMSVG-2M",           "train", "description", "svg_code"),
    ("feiyu26/SVG-1M-Json",        "train", "caption",     "svg"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Workers
# ─────────────────────────────────────────────────────────────────────────────

def _process_one(prompt: str, svg_raw: str, max_tok: int) -> Optional[dict]:
    """Standardise one (prompt, svg) pair. Returns None if filtered out."""
    svg = standardize_svg(svg_raw)
    if svg is None:
        return None
    if not is_colorful(svg):
        return None
    if not is_renderable(svg):
        return None
    # Token-length check (lazy import to avoid loading tokenizer in every worker)
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
        if len(tok.encode(svg, add_special_tokens=False)) > max_tok:
            return None
    except Exception:
        # If tokenizer unavailable, skip the token check (warn only once)
        pass
    return {"prompt": prompt.strip(), "svg": svg}


def _process_batch(rows: list) -> list:
    """Process a batch; called inside a worker process."""
    results = []
    for prompt, svg_raw in rows:
        r = _process_one(prompt, svg_raw, MAX_TOKENS)
        if r:
            results.append(r)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Dataset loaders
# ─────────────────────────────────────────────────────────────────────────────

def _stream_dataset(ds_id: str, split: str, text_col: str, svg_col: str):
    """Yield (prompt, svg_raw) pairs from a HuggingFace dataset."""
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("pip install datasets")

    log.info(f"Loading {ds_id} / {split} ...")
    try:
        ds = load_dataset(ds_id, split=split, streaming=True, trust_remote_code=True)
    except Exception as e:
        log.warning(f"Could not load {ds_id}: {e}")
        return

    for row in ds:
        prompt  = row.get(text_col, "")
        svg_raw = row.get(svg_col,  "")
        if prompt and svg_raw:
            yield prompt, svg_raw


def _load_local_dir(directory: str):
    """Yield (prompt, svg_raw) pairs from a local directory of .svg files
    paired with same-stem .txt caption files."""
    d = Path(directory)
    for svg_path in d.rglob("*.svg"):
        txt_path = svg_path.with_suffix(".txt")
        if not txt_path.exists():
            continue
        try:
            svg_raw = svg_path.read_text(encoding="utf-8", errors="ignore")
            prompt  = txt_path.read_text(encoding="utf-8", errors="ignore").strip()
            if prompt and svg_raw:
                yield prompt, svg_raw
        except Exception:
            continue


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main(args):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    seen_prompts: set = set()
    total_in = total_out = 0
    BATCH = 256   # rows per worker task

    with open(OUT_FILE, "w", encoding="utf-8") as fout, \
         ProcessPoolExecutor(max_workers=args.workers) as pool:

        futures = {}
        batch   = []

        def _flush_batch(b):
            nonlocal total_in
            total_in += len(b)
            f = pool.submit(_process_batch, b)
            futures[f] = True

        def _collect():
            nonlocal total_out
            done = [f for f in futures if f.done()]
            for f in done:
                del futures[f]
                for item in f.result():
                    key = item["prompt"][:120]
                    if key not in seen_prompts:
                        seen_prompts.add(key)
                        fout.write(json.dumps(item, ensure_ascii=False) + "\n")
                        total_out += 1
                        if total_out % 1000 == 0:
                            log.info(f"  saved {total_out:,} / scanned {total_in:,}")

        # Stream from HuggingFace datasets
        for ds_id, split, text_col, svg_col in DATASETS:
            for prompt, svg_raw in _stream_dataset(ds_id, split, text_col, svg_col):
                batch.append((prompt, svg_raw))
                if len(batch) >= BATCH:
                    _flush_batch(batch); batch = []
                _collect()
                if args.max_samples and total_out >= args.max_samples:
                    log.info(f"  --max-samples {args.max_samples} reached, stopping.")
                    break
            if args.max_samples and total_out >= args.max_samples:
                break

        # Optionally load local directories
        for local_dir in args.local_dirs:
            if args.max_samples and total_out >= args.max_samples:
                break
            for prompt, svg_raw in _load_local_dir(local_dir):
                batch.append((prompt, svg_raw))
                if len(batch) >= BATCH:
                    _flush_batch(batch); batch = []
                _collect()
                if args.max_samples and total_out >= args.max_samples:
                    break

        if batch:
            _flush_batch(batch)

        # Drain remaining futures
        for f in as_completed(futures):
            for item in f.result():
                key = item["prompt"][:120]
                if key not in seen_prompts:
                    seen_prompts.add(key)
                    fout.write(json.dumps(item, ensure_ascii=False) + "\n")
                    total_out += 1

    log.info(f"Done. D_G^direct: {total_out:,} samples saved to {OUT_FILE}")
    log.info(f"Acceptance rate: {total_out/max(total_in,1):.1%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers",     type=int, default=NUM_WORKERS)
    parser.add_argument("--max-samples", type=int, default=0,
                        help="Stop after N accepted samples (0 = no limit; use 5000 for smoke run)")
    parser.add_argument("--local-dirs",  nargs="*", default=[],
                        help="Optional local directories of .svg + .txt pairs")
    args = parser.parse_args()
    main(args)
