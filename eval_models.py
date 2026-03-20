#!/usr/bin/env python3
"""
eval_models.py — Run SVG generation models on the held-out eval set and compare.

WORKFLOW
────────
Step 1 — Generate SVGs (one model at a time, saves to eval_results_{model}.json):
    python eval_models.py --run qwen_lora         # fine-tuned Qwen2-VL-2B + LoRA
    python eval_models.py --run qwen_base         # Qwen2-VL-2B base (no LoRA)
    python eval_models.py --run gpt4o_mini        # needs OPENAI_API_KEY
    python eval_models.py --run claude_haiku      # needs ANTHROPIC_API_KEY

Step 2 — Score with CLIP (run on GPU Colab for speed):
    python eval_models.py --score qwen_lora
    python eval_models.py --score qwen_base
    python eval_models.py --score gpt4o_mini
    python eval_models.py --score claude_haiku

Step 3 — Compare all scored models:
    python eval_models.py --compare

Options:
    --prompts   path to eval_prompts.json   (default: ./eval_prompts.json)
    --out_dir   directory for result files  (default: .)
    --adapter   LoRA adapter path           (default: ./qwen2vl_svg_lora/final_adapter)
    --base      Qwen2VL base model id       (default: Qwen/Qwen2-VL-2B-Instruct)
"""

import argparse
import gc
import io
import json
import os
import re
import sys
import time
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_ADAPTER  = "./qwen2vl_svg_lora/final_adapter"
DEFAULT_BASE     = "Qwen/Qwen2-VL-2B-Instruct"
DEFAULT_PROMPTS  = "eval_prompts.json"
DEFAULT_OUT_DIR  = "."

SYSTEM_PROMPT = (
    "You are an expert SVG code generator. "
    "Given a text description, output ONLY valid SVG code. "
    "Rules:\n"
    '- Start with: <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n'
    "- Use simple shapes: <rect>, <circle>, <ellipse>, <polygon>, <path>\n"
    '- Use solid hex fill colors (e.g., fill="#FF0000")\n'
    "- Keep it minimal: 5-20 elements\n"
    "- End with: </svg>\n"
    "Output the SVG code directly, no explanation."
)

# ── SVG utilities ─────────────────────────────────────────────────────────────

def extract_svg(text: str) -> str | None:
    if not text:
        return None
    if "```" in text:
        for part in text.split("```"):
            p = part.strip().lstrip("svg").lstrip("xml").strip()
            if p.startswith("<svg"):
                text = p
                break
    m = re.search(r"<svg[\s>]", text)
    if m:
        text = text[m.start():]
    end = text.rfind("</svg>")
    if end != -1:
        text = text[: end + len("</svg>")]
    return text.strip() if "<svg" in text else None


def repair_svg(svg: str) -> str:
    svg = svg.strip()
    m = re.search(r"<svg[\s>]", svg)
    if m:
        svg = svg[m.start():]
    open_g  = len(re.findall(r"<g\b[^>]*>", svg))
    close_g = len(re.findall(r"</g>",        svg))
    svg += "</g>" * max(0, open_g - close_g)
    if not svg.rstrip().endswith("</svg>"):
        svg = svg.rstrip()
        svg += "\n</svg>" if svg.endswith(">") else '" fill="#000000"/>\n</svg>'
    return svg


def count_elements(svg: str) -> int:
    return len(re.findall(r"<(path|rect|circle|ellipse|polygon|polyline|line)\b", svg, re.I))


def validate_svg(svg: str) -> bool:
    if not svg or "<svg" not in svg:
        return False
    try:
        import cairosvg
        cairosvg.svg2png(bytestring=svg.encode(), output_width=64, output_height=64)
        return True
    except Exception:
        return False


def render_svg(svg: str, size: int = 224):
    """Render SVG → PIL Image, or None on failure."""
    try:
        import cairosvg
        from PIL import Image
        png = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
        return Image.open(io.BytesIO(png)).convert("RGB")
    except Exception:
        return None


# ── Load prompts ──────────────────────────────────────────────────────────────

def load_prompts(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["prompts"] if isinstance(data, dict) else data


# ── Result I/O ────────────────────────────────────────────────────────────────

def results_path(out_dir: str, model: str) -> Path:
    return Path(out_dir) / f"eval_results_{model}.json"


def load_results(out_dir: str, model: str) -> list[dict]:
    p = results_path(out_dir, model)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("results", data) if isinstance(data, dict) else data


def save_results(out_dir: str, model: str, results: list[dict]):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    p = results_path(out_dir, model)
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"model": model, "results": results}, f, indent=2)


# ── Qwen2-VL runner ───────────────────────────────────────────────────────────

def load_qwen(adapter_path: str | None, base_model: str):
    """Load Qwen2-VL-2B with optional LoRA adapter."""
    import torch
    from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer, BitsAndBytesConfig

    print(f"Loading base model: {base_model}")
    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
    )
    base = Qwen2VLForConditionalGeneration.from_pretrained(
        base_model,
        quantization_config=quant,
        device_map="auto",
        trust_remote_code=True,
    )
    if adapter_path:
        from peft import PeftModel
        print(f"Loading LoRA adapter: {adapter_path}")
        model = PeftModel.from_pretrained(base, adapter_path)
        tok = AutoTokenizer.from_pretrained(adapter_path, trust_remote_code=True)
    else:
        print("No adapter — running base model only.")
        model = base
        tok = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)

    model.eval()
    print("Model ready.\n")
    return model, tok


def gen_qwen_svg(prompt: str, model, tok, max_new_tokens: int = 1500) -> str | None:
    import torch

    chat = tok.apply_chat_template(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Generate SVG for: {prompt}"},
        ],
        tokenize=False,
        add_generation_prompt=True,
    )
    ids = tok(chat, return_tensors="pt").to(model.device)
    stop_ids = tok.encode("</svg>", add_special_tokens=False)
    stop_id  = stop_ids[-1] if stop_ids else tok.eos_token_id

    with torch.inference_mode():
        out = model.generate(
            **ids,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            repetition_penalty=1.05,  # gentle penalty; 1.5 kills Potrace's naturally repetitive coord data
            eos_token_id=stop_id,
        )
    raw = tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    svg = extract_svg(raw)
    return repair_svg(svg) if svg else None


def run_qwen(model_key: str, adapter_path: str | None, base_model: str,
             prompts_path: str, out_dir: str):
    prompts = load_prompts(prompts_path)

    # Resume support
    existing = {r["prompt"]: r for r in load_results(out_dir, model_key)}
    if existing:
        print(f"Resuming — {len(existing)} prompts already done.")

    model, tok = load_qwen(adapter_path, base_model)
    results = []

    for item in prompts:
        prompt    = item["prompt"]
        category  = item.get("category", "")
        prompt_id = item.get("id", -1)

        if prompt in existing:
            results.append(existing[prompt])
            continue

        print(f"[{prompt_id:02d}] {prompt} ...", end=" ", flush=True)
        t0  = time.time()
        svg = gen_qwen_svg(prompt, model, tok)
        elapsed = time.time() - t0

        success = bool(svg and validate_svg(svg))
        r = {
            "id":       prompt_id,
            "prompt":   prompt,
            "category": category,
            "model":    model_key,
            "success":  success,
            "clip":     0.0,
            "dino":     None,
            "elements": count_elements(svg) if svg else 0,
            "time":     round(elapsed, 2),
            "svg":      svg or "",
            "error":    None if success else "SVG invalid or extraction failed",
        }
        results.append(r)
        print(f"{'OK' if success else 'FAIL'}  ({elapsed:.1f}s, {r['elements']} elems)")
        save_results(out_dir, model_key, results)

    gc.collect()
    try:
        import torch; torch.cuda.empty_cache()
    except Exception:
        pass

    valid = sum(1 for r in results if r["success"])
    print(f"\nDone. {valid}/{len(results)} valid SVGs → {results_path(out_dir, model_key)}")
    print(f"Next: python eval_models.py --score {model_key}")


# ── API baseline runner (delegates to baselines.py logic) ────────────────────

def run_api_model(model_key: str, prompts_path: str, out_dir: str):
    """Thin wrapper: just calls baselines.py's run() directly."""
    try:
        from baselines import run as baselines_run
    except ImportError:
        print("ERROR: baselines.py not found. Place it next to eval_models.py.")
        sys.exit(1)
    baselines_run(model_key, prompts_path, out_dir)


# ── CLIP scoring ──────────────────────────────────────────────────────────────

def score_model(model_key: str, out_dir: str):
    """Compute CLIP scores for all valid SVGs in eval_results_{model}.json."""
    import torch
    import torch.nn.functional as F
    import open_clip
    import numpy as np

    results = load_results(out_dir, model_key)
    if not results:
        print(f"No results found for {model_key}. Run --run first.")
        return

    already_scored = sum(1 for r in results if r.get("clip", 0.0) > 0)
    if already_scored == len(results):
        print(f"All {len(results)} results already scored.")
        return

    print(f"Loading CLIP (ViT-B-32)...")
    clip_model, _, clip_prep = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
    clip_model = clip_model.cuda().eval()
    tokenizer  = open_clip.get_tokenizer("ViT-B-32")

    scored = 0
    for r in results:
        if r.get("clip", 0.0) > 0:
            continue
        if not r.get("success") or not r.get("svg"):
            continue

        img = render_svg(r["svg"])
        if img is None:
            r["error"] = (r.get("error") or "") + " | render failed"
            continue

        with torch.no_grad():
            img_t = clip_prep(img).unsqueeze(0).cuda()
            txt_t = tokenizer([r["prompt"]]).cuda()
            img_f = F.normalize(clip_model.encode_image(img_t), dim=-1)
            txt_f = F.normalize(clip_model.encode_text(txt_t),  dim=-1)
            r["clip"] = round((img_f @ txt_f.T).item() * 100, 4)

        scored += 1
        print(f"  [{r['id']:02d}] {r['prompt'][:40]:<40}  CLIP={r['clip']:.2f}")
        save_results(out_dir, model_key, results)

    # Summary
    valid = [r for r in results if r.get("clip", 0) > 0]
    if valid:
        clips = [r["clip"] for r in valid]
        print(f"\nScored {scored} new / {len(valid)} total")
        print(f"  CLIP mean ± std: {np.mean(clips):.2f} ± {np.std(clips):.2f}")
        print(f"  CLIP range:      {min(clips):.2f} – {max(clips):.2f}")

    del clip_model
    gc.collect()
    try:
        torch.cuda.empty_cache()
    except Exception:
        pass


# ── Compare table ─────────────────────────────────────────────────────────────

def compare(out_dir: str):
    """Print a comparison table for every eval_results_*.json in out_dir."""
    import numpy as np

    files = sorted(Path(out_dir).glob("eval_results_*.json"))
    if not files:
        print(f"No eval_results_*.json found in {out_dir}. Run --run first.")
        return

    rows = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        model   = data.get("model", f.stem.replace("eval_results_", ""))
        results = data.get("results", [])

        total   = len(results)
        valid   = [r for r in results if r.get("success")]
        scored  = [r for r in valid   if r.get("clip", 0) > 0]
        clips   = [r["clip"]     for r in scored]
        elems   = [r["elements"] for r in valid]
        times   = [r["time"]     for r in results if r.get("time")]

        rows.append({
            "Model":       model,
            "N":           total,
            "Valid":       len(valid),
            "Valid %":     100 * len(valid) / total if total else 0,
            "CLIP mean":   np.mean(clips)   if clips else float("nan"),
            "CLIP std":    np.std(clips)    if clips else float("nan"),
            "Avg elements":np.mean(elems)   if elems else float("nan"),
            "Avg time(s)": np.mean(times)   if times else float("nan"),
        })

    # Per-category breakdown
    cat_data: dict[str, dict[str, list]] = {}
    for f in files:
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        model   = data.get("model", f.stem.replace("eval_results_", ""))
        results = data.get("results", [])
        for r in results:
            cat = r.get("category", "?")
            if cat not in cat_data:
                cat_data[cat] = {}
            if model not in cat_data[cat]:
                cat_data[cat][model] = []
            cat_data[cat][model].append(r.get("clip", 0.0) if r.get("success") else 0.0)

    # ── Print ──────────────────────────────────────────────────────────────────
    col_w   = 16
    metrics = ["Valid %", "CLIP mean", "CLIP std", "Avg elements", "Avg time(s)"]
    models  = [row["Model"] for row in rows]

    hdr = f"{'Metric':<20}" + "".join(f"{m:>{col_w}}" for m in models)
    sep = "─" * len(hdr)

    print()
    print("=" * len(hdr))
    print("  SVG GENERATION MODEL COMPARISON")
    print("=" * len(hdr))
    print(hdr)
    print(sep)

    for metric in metrics:
        line = f"{metric:<20}"
        for row in rows:
            val = row[metric]
            if metric.endswith("%"):
                line += f"{val:>{col_w}.1f}%"[:-1].rjust(col_w) + " "
                line = line[:-1]
                line += f"{val:>{col_w-1}.1f}%"
            else:
                line += f"{val:>{col_w}.2f}"
        print(line)

    print(sep)

    # Per-category CLIP
    print(f"\n{'Category CLIP mean':<20}" + "".join(f"{m:>{col_w}}" for m in models))
    print(sep)
    for cat in sorted(cat_data):
        line = f"{cat:<20}"
        for model in models:
            vals = [v for v in cat_data[cat].get(model, []) if v > 0]
            line += f"{float(np.mean(vals)) if vals else float('nan'):>{col_w}.2f}"
        print(line)

    print(sep)
    print()
    print("CLIP = CLIP ViT-B-32 score (higher is better, ~25–35 typical range)")
    print("Run --score {model} first if CLIP shows 0 / nan.")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

QWEN_MODELS  = {"qwen_lora", "qwen_base"}
API_MODELS   = {"gpt4o_mini", "claude_haiku"}
ALL_MODELS   = QWEN_MODELS | API_MODELS


def main():
    parser = argparse.ArgumentParser(
        description="Eval SVG generation models on held-out prompt set",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run",     metavar="MODEL",
                       help=f"Generate SVGs: {ALL_MODELS | {'all'}}")
    group.add_argument("--score",   metavar="MODEL",
                       help="Compute CLIP scores for a model's saved results")
    group.add_argument("--compare", action="store_true",
                       help="Print comparison table of all scored models")

    parser.add_argument("--prompts",  default=DEFAULT_PROMPTS)
    parser.add_argument("--out_dir",  default=DEFAULT_OUT_DIR)
    parser.add_argument("--adapter",  default=DEFAULT_ADAPTER,
                        help="LoRA adapter dir (used with --run qwen_lora)")
    parser.add_argument("--base",     default=DEFAULT_BASE,
                        help="Qwen2-VL base model id")

    args = parser.parse_args()

    if args.compare:
        compare(args.out_dir)
        return

    if args.score:
        score_model(args.score, args.out_dir)
        return

    # --run
    model = args.run

    if model == "all":
        # Run Qwen models first (need GPU), then API models
        print("=== qwen_lora ===")
        run_qwen("qwen_lora", args.adapter, args.base, args.prompts, args.out_dir)
        print("\n=== qwen_base ===")
        run_qwen("qwen_base", None, args.base, args.prompts, args.out_dir)
        for api_m in ["gpt4o_mini", "claude_haiku"]:
            print(f"\n=== {api_m} ===")
            run_api_model(api_m, args.prompts, args.out_dir)
        return

    if model == "qwen_lora":
        run_qwen("qwen_lora", args.adapter, args.base, args.prompts, args.out_dir)
    elif model == "qwen_base":
        run_qwen("qwen_base", None, args.base, args.prompts, args.out_dir)
    elif model in API_MODELS:
        run_api_model(model, args.prompts, args.out_dir)
    else:
        print(f"Unknown model '{model}'. Choose from: {ALL_MODELS | {'all'}}")
        sys.exit(1)


if __name__ == "__main__":
    main()
