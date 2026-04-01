#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DiffuSVG_Generate_CPU.py
========================
Dataset generation for DiffuSVG on a HIGH-RAM CPU machine (no GPU needed).

Pipeline (same whiteboard design, CPU edition):
  results.json → mine bad prompts
  → SD3.5-M (no T5, CPU, bf16/fp32) → raster image
  → Potrace + ImageMagick → SVG
  → structural quality check
  → dataset_train.jsonl  (ready for fine-tuning in DiffuSVG_Dataset_Finetune.py)

Requirements
------------
  RAM   : ≥16 GB (SD3.5-M without T5 ≈ 11-12 GB in fp32)
  Disk  : ≥8 GB  (model cache)
  System: potrace, imagemagick  (apt / brew / winget)
  Python: pip install diffusers transformers accelerate pillow tqdm

Usage
-----
  python DiffuSVG_Generate_CPU.py \\
      --results results.json \\
      --hf_token hf_xxx... \\
      --output_dir ./dataset

  # Then upload dataset_train.jsonl to Colab and run DiffuSVG_Dataset_Finetune.py
  # with FORCE_REGEN=False to skip generation and jump straight to fine-tuning.
"""

import argparse
import gc
import json
import logging
import os
import random
import shutil
import subprocess
import sys
import tempfile
import re
from pathlib import Path

log = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────

def _require_tool(name: str, hint: str):
    if not shutil.which(name):
        raise EnvironmentError(f"'{name}' not found in PATH.  Install: {hint}")


def _mine_bad_prompts(results_path: str, clip_thr: float, dino_thr: float):
    """Return list of prompts that failed CLIP / DINO / success checks."""
    import csv
    path = Path(results_path)
    if path.suffix == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        records = data["results"] if isinstance(data, dict) else data
    elif path.suffix == ".csv":
        with open(path, encoding="utf-8", newline="") as f:
            records = list(csv.DictReader(f))
        for r in records:
            r["success"] = r.get("success", "True").lower() in ("true", "1", "yes")
            r["clip"]    = float(r.get("clip", 0) or 0)
            r["dino"]    = float(r.get("dino", 0) or 0)
    else:
        raise ValueError(f"Unsupported format: {path.suffix} (use .json or .csv)")

    bad = []
    for r in records:
        if (not r.get("success", True)
                or float(r.get("clip", 0)) < clip_thr
                or float(r.get("dino", 0)) < dino_thr):
            bad.append(r["prompt"])
    return bad


# ── Vectorizer (inline — no import from dataset_pipeline needed) ──────────

def _to_bmp(image, path: str, resolution: int, threshold: float):
    """PIL Image → 1-bit BMP via ImageMagick (or PIL fallback)."""
    import numpy as np
    from PIL import Image

    if shutil.which("convert"):
        import tempfile as _tf
        with _tf.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            png = tmp.name
        image.convert("RGB").save(png)
        cmd = [
            "convert", png,
            "-resize", f"{resolution}x{resolution}!",
            "-colorspace", "Gray",
            "-level", "2%x98%",
            "-threshold", f"{int(threshold * 100)}%",
            "-type", "Bilevel",
            f"BMP3:{path}",
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
        finally:
            os.unlink(png)
    else:
        img = image.convert("RGB").resize((resolution, resolution))
        grey = np.array(img.convert("L")).astype("float32") / 255.0
        binary = (grey < threshold).astype("uint8")
        from PIL import Image as _PIL
        _PIL.fromarray((binary * 255).astype("uint8"), "L").convert("1").save(path, format="BMP")


def _potrace(bmp: str, svg: str) -> bool:
    try:
        r = subprocess.run(
            ["potrace", bmp, "--svg", "--turdsize=2", "--alphamax=1.0",
             "--opttolerance=0.2", "--output", svg],
            capture_output=True, timeout=30,
        )
        return r.returncode == 0
    except Exception:
        return False


def _vectorize(image, resolution: int = 512, threshold: float = 0.45):
    """PIL Image → SVG string, or None on failure."""
    with tempfile.TemporaryDirectory() as tmp:
        bmp = os.path.join(tmp, "in.bmp")
        svg = os.path.join(tmp, "out.svg")
        _to_bmp(image, bmp, resolution, threshold)
        if not _potrace(bmp, svg):
            return None
        raw = Path(svg).read_text(encoding="utf-8")

    # Normalize viewBox to 200×200
    raw = re.sub(r'<\?xml[^>]*\?>', '', raw)
    raw = re.sub(r'<!DOCTYPE[^>]*>', '', raw)
    raw = re.sub(r'<!--.*?-->', '', raw, flags=re.DOTALL)
    raw = re.sub(r'<metadata\b[^>]*>.*?</metadata>', '', raw, flags=re.DOTALL)
    vb = re.search(r'viewBox="([^"]+)"', raw)
    if vb:
        parts = vb.group(1).split()
        ow = float(parts[2]) if len(parts) == 4 else resolution
        oh = float(parts[3]) if len(parts) == 4 else resolution
    else:
        ow = oh = float(resolution)
    sx, sy = 200.0 / max(ow, 1), 200.0 / max(oh, 1)
    raw = re.sub(r'<svg[^>]*>',
                 '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">',
                 raw, count=1)
    if abs(sx - 1) > 0.01 or abs(sy - 1) > 0.01:
        raw = raw.replace(
            '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">',
            f'<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
            f'<g transform="scale({sx:.4f},{sy:.4f})">',
        )
        raw = raw.replace('</svg>', '</g></svg>')
    raw = "\n".join(l for l in raw.splitlines() if l.strip())
    return raw.strip()


def _is_good_svg(svg: str, min_paths: int = 1, max_paths: int = 500) -> bool:
    if not svg or "<svg" not in svg:
        return False
    paths = len(re.findall(r'<path', svg))
    if not (min_paths <= paths <= max_paths):
        return False
    ds = re.findall(r'd="([^"]+)"', svg)
    return bool(ds) and max(len(d) for d in ds) >= 10


# ── Diffusion (CPU) ───────────────────────────────────────────────────────

def load_sd35_cpu(hf_token: str):
    """
    Load SD3.5-M without T5-XXL on CPU.
    fp32 ≈ 11-12 GB RAM.  bf16 ≈ 5-6 GB RAM (supported on modern CPUs).
    """
    import torch
    from diffusers import StableDiffusion3Pipeline

    dtype = torch.bfloat16 if torch.backends.cpu.is_bf16_supported() else torch.float32
    log.info(f"Loading SD3.5-M on CPU ({dtype}) — no T5-XXL ...")
    pipe = StableDiffusion3Pipeline.from_pretrained(
        "stabilityai/stable-diffusion-3.5-medium",
        text_encoder_3=None,
        tokenizer_3=None,
        torch_dtype=dtype,
        token=hf_token,
    )
    pipe = pipe.to("cpu")
    log.info("SD3.5-M loaded on CPU.")

    _STYLE = (
        "ultra-simple flat vector icon, geometric shapes only, solid colors, "
        "no gradients, no shadows, no texture, minimalist, SVG-ready, "
    )
    _NEG = "gradient, shadow, texture, 3d, realistic, photograph, complex details, blurry"

    def generate(prompt: str, seed: int | None = None,
                 steps: int = 20, guidance: float = 5.0):
        import torch
        gen = torch.Generator("cpu").manual_seed(seed) if seed is not None else None
        return pipe(
            _STYLE + prompt,
            negative_prompt=_NEG,
            num_inference_steps=steps,
            guidance_scale=guidance,
            generator=gen,
        ).images[0]

    return generate


# ── Dataset split ─────────────────────────────────────────────────────────

def _split(records, out_dir: Path, train_ratio: float = 0.9, seed: int = 42):
    random.seed(seed)
    random.shuffle(records)
    n = max(1, int(len(records) * train_ratio))
    train, val = records[:n], records[n:]
    train_p = out_dir / "dataset_train.jsonl"
    val_p   = out_dir / "dataset_val.jsonl" if val else None
    with open(train_p, "w", encoding="utf-8") as f:
        for r in train:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    if val_p:
        with open(val_p, "w", encoding="utf-8") as f:
            for r in val:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    log.info(f"Train: {len(train)} → {train_p}")
    log.info(f"Val  : {len(val)}  → {val_p}")
    return train_p, val_p


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Generate DiffuSVG dataset on a high-RAM CPU (no GPU needed)."
    )
    ap.add_argument("--results",       required=True, help="results.json or results.csv")
    ap.add_argument("--hf_token",      default=os.environ.get("HF_TOKEN", ""),
                    help="HuggingFace token (or set HF_TOKEN env var)")
    ap.add_argument("--output_dir",    default="./dataset")
    ap.add_argument("--clip_threshold", type=float, default=24.0)
    ap.add_argument("--dino_threshold", type=float, default=0.35)
    ap.add_argument("--steps",         type=int,   default=20,
                    help="Diffusion steps (20 is enough for CPU; fewer = faster)")
    ap.add_argument("--guidance",      type=float, default=5.0)
    ap.add_argument("--seed",          type=int,   default=42)
    ap.add_argument("--resolution",    type=int,   default=512)
    ap.add_argument("--threshold",     type=float, default=0.45,
                    help="Greyscale binarisation threshold for Potrace")
    ap.add_argument("--train_ratio",   type=float, default=0.9)
    ap.add_argument("--save_images",   action="store_true")
    ap.add_argument("--max_prompts",   type=int,   default=0,
                    help="Limit number of prompts processed (0 = all)")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    _require_tool("potrace",
                  "apt install potrace  /  brew install potrace  /  winget install potrace")

    assert args.hf_token, (
        "HuggingFace token required.  Pass --hf_token or set HF_TOKEN env var.\n"
        "Get one at https://huggingface.co/settings/tokens"
    )

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if args.save_images:
        (out / "images").mkdir(exist_ok=True)

    # ── Mine bad prompts ──────────────────────────────────────────────────
    log.info(f"Mining bad prompts from {args.results} ...")
    bad_prompts = _mine_bad_prompts(args.results, args.clip_threshold, args.dino_threshold)
    if args.max_prompts:
        bad_prompts = bad_prompts[:args.max_prompts]
    log.info(f"Bad prompts found: {len(bad_prompts)}")
    if not bad_prompts:
        log.info("Nothing to do — thresholds may be too lenient.")
        return

    # ── Load SD3.5-M on CPU ───────────────────────────────────────────────
    generate = load_sd35_cpu(args.hf_token)

    # ── Generate + vectorize ──────────────────────────────────────────────
    records = []
    log.info(f"Generating {len(bad_prompts)} SVGs (CPU — expect ~30–120 s/image) ...")
    for i, prompt in enumerate(bad_prompts):
        seed = args.seed + i if args.seed is not None else None
        log.info(f"[{i+1}/{len(bad_prompts)}] {prompt[:70]}")
        try:
            img = generate(prompt, seed=seed, steps=args.steps, guidance=args.guidance)
        except Exception as e:
            log.warning(f"  diffusion failed: {e}")
            continue

        if args.save_images:
            img.save(out / "images" / f"{i:05d}.png")

        svg = _vectorize(img, resolution=args.resolution, threshold=args.threshold)
        if not svg:
            log.info("  SKIP — vectorization failed")
            continue
        if not _is_good_svg(svg):
            log.info("  SKIP — SVG failed structural check")
            continue

        records.append({"text": prompt, "svg": svg})
        log.info(f"  OK   ({len(re.findall(r'<path', svg))} paths)")

        gc.collect()  # keep RSS stable across iterations

    log.info(f"\nTotal accepted: {len(records)}/{len(bad_prompts)}")
    if not records:
        log.error("No SVGs generated — check model download and RAM availability.")
        sys.exit(1)

    # ── Write JSONL ───────────────────────────────────────────────────────
    jsonl = out / "dataset.jsonl"
    with open(jsonl, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    log.info(f"Dataset: {jsonl}")

    train_p, val_p = _split(records, out, train_ratio=args.train_ratio, seed=args.seed)

    print()
    print("=" * 60)
    print("Done!")
    print(f"  Train : {train_p}")
    print(f"  Val   : {val_p}")
    print()
    print("Next step: upload dataset_train.jsonl (and dataset_val.jsonl)")
    print("to Colab, set FORCE_REGEN=False in DiffuSVG_Dataset_Finetune.py,")
    print("and run it to skip generation and go straight to LoRA fine-tuning.")
    print("=" * 60)


if __name__ == "__main__":
    main()
