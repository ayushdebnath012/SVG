#!/usr/bin/env python3
"""
infer_svg.py  —  Test the fine-tuned Qwen2VL LoRA adapter for SVG generation.

Usage (Colab cell):
    !python infer_svg.py
    !python infer_svg.py --prompts "a cat" "a sun" "a tree"
    !python infer_svg.py --adapter ./qwen2vl_svg_lora/final_adapter --out_dir ./svg_out

Fixes applied vs raw training output:
  - repetition_penalty=1.3  : kills zero-padding degeneration (00000... in path d=)
  - max_new_tokens=3000     : enough for full Potrace-style SVGs (~9k chars)
  - eos on </svg>           : generation stops cleanly at end of SVG
  - repair_svg()            : closes unclosed <g> tags, appends </svg> if truncated
  - HTML fallback display   : works even when strict XML parser rejects output
  - saves .svg files        : open in browser for ground-truth visual check
"""

import argparse
import gc
import re
import sys
import os
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────
DEFAULT_ADAPTER  = "./qwen2vl_svg_lora/final_adapter"
DEFAULT_BASE     = "Qwen/Qwen2-VL-2B-Instruct"
DEFAULT_OUT_DIR  = "./svg_out"
DEFAULT_PROMPTS  = [
    # training-set prompts (should work best)
    "a house with red roof",
    "a coffee cup",
    "a car",
    "a lighthouse",
    "a bicycle",
    "a rocket",
    # unseen prompts (generalisation test)
    "a star",
    "a tree",
    "a flower",
    "a dog",
]

SYSTEM_PROMPT = (
    "You are an expert SVG code generator. "
    "Given a text description, output ONLY valid SVG code. "
    "Rules:\n"
    '- Start with: <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n'
    '- Use simple shapes: <rect>, <circle>, <ellipse>, <polygon>, <path>\n'
    '- Use solid hex fill colours (e.g., fill="#FF0000")\n'
    "- Keep it minimal: 5-20 elements\n- End with: </svg>\n"
    "Output the SVG code directly, no explanation."
)

# ── Helpers ───────────────────────────────────────────────────────────────

def repair_svg(svg: str) -> str:
    """Close unclosed <g> tags and ensure </svg> at end."""
    svg = svg.strip()
    # Strip anything before <svg
    m = re.search(r'<svg[\s>]', svg)
    if m:
        svg = svg[m.start():]
    # Close unclosed <g> tags
    open_g  = len(re.findall(r'<g\b[^>]*>', svg))
    close_g = len(re.findall(r'</g>', svg))
    svg += '</g>' * max(0, open_g - close_g)
    # Ensure </svg> at end
    if not svg.rstrip().endswith('</svg>'):
        svg = svg.rstrip()
        if svg.endswith('/>') or svg.endswith('>'):
            svg += '\n</svg>'
        else:
            # truncated mid-attribute — close path and svg
            svg += '" fill="#000000"/>\n</svg>'
    return svg


def svg_quality(svg: str) -> dict:
    """Quick structural metrics for a generated SVG."""
    paths      = len(re.findall(r'<path\b',      svg))
    rects      = len(re.findall(r'<rect\b',      svg))
    circles    = len(re.findall(r'<circle\b',    svg))
    ellipses   = len(re.findall(r'<ellipse\b',   svg))
    polygons   = len(re.findall(r'<polygon\b',   svg))
    polylines  = len(re.findall(r'<polyline\b',  svg))
    lines      = len(re.findall(r'<line\b',      svg))
    texts      = len(re.findall(r'<text\b',      svg))
    elements   = paths + rects + circles + ellipses + polygons + polylines + lines + texts
    has_zeros  = bool(re.search(r'0{20,}', svg))          # numeric zero-padding
    has_repeat = bool(re.search(r'(\b\w+\b)(\s+\1){9,}', svg))  # word repetition (oii oii...)
    d_attrs    = re.findall(r'd="([^"]*)"', svg)
    max_d_len  = max((len(d) for d in d_attrs), default=0)
    is_potrace = max_d_len > 500   # Potrace paths have very long d= strings
    return {
        "elements": elements, "paths": paths, "rects": rects,
        "circles": circles, "polylines": polylines, "lines": lines,
        "length": len(svg),
        "has_zeros": has_zeros, "has_repeat": has_repeat,
        "is_potrace_style": is_potrace,
    }


def display_svg(svg: str, label: str = ""):
    """Render in Colab (IPython) if available, else save file only."""
    try:
        from IPython.display import display as ipy_display, SVG, HTML
        svg_repaired = repair_svg(svg)
        try:
            ipy_display(SVG(svg_repaired))
        except Exception:
            ipy_display(HTML(svg_repaired))
    except ImportError:
        pass   # not in notebook — file output only


# ── Core inference ────────────────────────────────────────────────────────

def load_model(adapter_path: str, base_model: str):
    import torch
    from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer, BitsAndBytesConfig
    from peft import PeftModel

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
    print(f"Loading LoRA adapter: {adapter_path}")
    model = PeftModel.from_pretrained(base, adapter_path)
    model.eval()

    tok = AutoTokenizer.from_pretrained(adapter_path, trust_remote_code=True)
    print("Model ready.\n")
    return model, tok


def gen_svg(prompt: str, model, tok, max_new_tokens: int = 3000) -> str:
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

    # Stop cleanly at </svg> token sequence
    svg_end_ids = tok.encode("</svg>", add_special_tokens=False)
    stop_id = svg_end_ids[-1] if svg_end_ids else tok.eos_token_id

    with torch.inference_mode():
        out = model.generate(
            **ids,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            repetition_penalty=1.05,  # gentle penalty; 1.5 kills Potrace's naturally repetitive coord data
            eos_token_id=stop_id,
        )

    raw = tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    # Strip markdown code fences if present
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            p = part.strip()
            if p.startswith("svg"):
                p = p[3:].strip()
            if p.startswith("<svg"):
                raw = p
                break

    # Ensure it starts at <svg
    m = re.search(r'<svg[\s>]', raw)
    if m:
        raw = raw[m.start():]

    return raw


# ── Main ──────────────────────────────────────────────────────────────────

def run(adapter_path: str, base_model: str, prompts: list, out_dir: str):
    import torch

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    model, tok = load_model(adapter_path, base_model)

    results = []
    for prompt in prompts:
        print(f"{'─' * 55}")
        print(f"Prompt : {prompt}")

        svg_raw = gen_svg(prompt, model, tok)
        svg     = repair_svg(svg_raw)
        q       = svg_quality(svg)

        status = []
        if q["has_zeros"]:        status.append("ZERO-LOOP")
        if q["has_repeat"]:       status.append("WORD-REPEAT")
        if q["elements"] == 0:    status.append("NO-ELEMENTS")
        if q["is_potrace_style"]: status.append("potrace-style")
        status_str = "  ⚠ " + " | ".join(status) if status else "  ✓"

        print(f"  Length  : {q['length']:,} chars")
        print(f"  Elements: {q['elements']}  "
              f"(paths={q['paths']} rects={q['rects']} "
              f"circles={q['circles']} polylines={q['polylines']} "
              f"lines={q['lines']}){status_str}")
        print(f"  Tail    : {svg_raw[-60:]!r}")

        # Save SVG file
        slug = re.sub(r'\W+', '_', prompt)[:40]
        svg_path = out / f"{slug}.svg"
        svg_path.write_text(svg, encoding="utf-8")
        print(f"  Saved   : {svg_path}")

        # Display in notebook
        display_svg(svg, prompt)

        results.append({"prompt": prompt, "svg": svg, "quality": q})

    # Summary
    print(f"\n{'═' * 55}")
    print(f"Results summary  ({len(prompts)} prompts → {out_dir})")
    print(f"{'═' * 55}")
    ok        = sum(1 for r in results if not r["quality"]["has_zeros"]
                    and not r["quality"]["has_repeat"]
                    and r["quality"]["elements"] > 0)
    zero_deg  = sum(1 for r in results if r["quality"]["has_zeros"])
    word_rep  = sum(1 for r in results if r["quality"]["has_repeat"])
    empty     = sum(1 for r in results if r["quality"]["elements"] == 0)
    print(f"  Valid              : {ok}/{len(prompts)}")
    print(f"  Zero-loop degen    : {zero_deg}")
    print(f"  Word-repeat degen  : {word_rep}")
    print(f"  No elements        : {empty}")

    gc.collect()
    try:
        torch.cuda.empty_cache()
    except Exception:
        pass

    return results


# ── Entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inference test for fine-tuned Qwen2VL SVG adapter")
    parser.add_argument("--adapter",  default=DEFAULT_ADAPTER,  help="Path to LoRA adapter directory")
    parser.add_argument("--base",     default=DEFAULT_BASE,     help="Base model name/path")
    parser.add_argument("--out_dir",  default=DEFAULT_OUT_DIR,  help="Directory to save .svg files")
    parser.add_argument("--prompts",  nargs="+",                help="Prompts to test (overrides defaults)")
    parser.add_argument("--max_tok",  type=int, default=3000,   help="max_new_tokens for generation")
    args, _ = parser.parse_known_args()   # ignore Jupyter's -f kernel.json arg

    prompts = args.prompts if args.prompts else DEFAULT_PROMPTS
    run(args.adapter, args.base, prompts, args.out_dir)
