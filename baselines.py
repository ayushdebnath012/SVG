#!/usr/bin/env python3
"""
baselines.py — Generate SVGs using API-based baseline models.

Supports:
  - gpt4o_mini  : OpenAI GPT-4o-mini (needs OPENAI_API_KEY env var)
  - claude_haiku: Anthropic Claude Haiku (needs ANTHROPIC_API_KEY env var)

Output is saved to eval_results_{model}.json in the same format as eval_models.py
so --compare in eval_models.py can read all results uniformly.

Usage:
    export OPENAI_API_KEY=sk-...
    python baselines.py --model gpt4o_mini

    export ANTHROPIC_API_KEY=sk-ant-...
    python baselines.py --model claude_haiku

    # Custom prompt file or output dir
    python baselines.py --model gpt4o_mini --prompts eval_prompts.json --out_dir ./eval_out
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

# ── Prompt sent to every model ────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are an expert SVG code generator. "
    "Given a text description, output ONLY valid SVG code with NO explanation.\n"
    "Rules:\n"
    '- Start with: <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n'
    "- Use simple shapes: <rect>, <circle>, <ellipse>, <polygon>, <path>\n"
    '- Use solid hex fill colors (e.g., fill="#FF0000")\n'
    "- Keep it minimal: 5-20 elements\n"
    "- End with: </svg>\n"
    "Output the SVG code directly, nothing else."
)

USER_TEMPLATE = "Generate an SVG illustration for: {prompt}"

# ── SVG helpers (mirror of infer_svg.py) ─────────────────────────────────────

def extract_svg(text: str) -> str | None:
    """Pull the first <svg...>...</svg> block out of a string."""
    if not text:
        return None
    # Strip markdown fences
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
    close_g = len(re.findall(r"</g>", svg))
    svg += "</g>" * max(0, open_g - close_g)
    if not svg.rstrip().endswith("</svg>"):
        svg = svg.rstrip()
        svg += "\n</svg>" if svg.endswith(">") else '" fill="#000000"/>\n</svg>'
    return svg


def count_elements(svg: str) -> int:
    return len(re.findall(r"<(path|rect|circle|ellipse|polygon|polyline|line)\b", svg, re.I))


# ── Model-specific generators ─────────────────────────────────────────────────

def gen_gpt4o_mini(prompt: str, client) -> tuple[str | None, str | None]:
    """Returns (svg_string, error_string)."""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": USER_TEMPLATE.format(prompt=prompt)},
            ],
            max_tokens=1500,
            temperature=0.0,
        )
        raw = resp.choices[0].message.content or ""
        svg = extract_svg(raw)
        if svg:
            svg = repair_svg(svg)
        return svg, None
    except Exception as e:
        return None, str(e)


def gen_claude_haiku(prompt: str, client) -> tuple[str | None, str | None]:
    """Returns (svg_string, error_string)."""
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": USER_TEMPLATE.format(prompt=prompt)}],
        )
        raw = msg.content[0].text if msg.content else ""
        svg = extract_svg(raw)
        if svg:
            svg = repair_svg(svg)
        return svg, None
    except Exception as e:
        return None, str(e)


# ── Validation (cairosvg if available, else regex fallback) ──────────────────

def validate_svg(svg: str) -> bool:
    if not svg or "<svg" not in svg:
        return False
    try:
        import cairosvg
        cairosvg.svg2png(bytestring=svg.encode(), output_width=64, output_height=64)
        return True
    except Exception:
        return False
    except ImportError:
        # fallback: basic structure check
        return bool(re.search(r"<svg[^>]*>", svg) and svg.rstrip().endswith("</svg>"))


# ── Main ──────────────────────────────────────────────────────────────────────

SUPPORTED_MODELS = {
    "gpt4o_mini":   ("OPENAI_API_KEY",     "openai",     gen_gpt4o_mini),
    "claude_haiku": ("ANTHROPIC_API_KEY",  "anthropic",  gen_claude_haiku),
}


def load_prompts(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["prompts"] if isinstance(data, dict) else data


def build_client(model_key: str):
    env_var, lib, _ = SUPPORTED_MODELS[model_key]
    api_key = os.environ.get(env_var)
    if not api_key:
        print(f"ERROR: {env_var} is not set.", file=sys.stderr)
        sys.exit(1)
    if lib == "openai":
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    else:
        from anthropic import Anthropic
        return Anthropic(api_key=api_key)


def run(model_key: str, prompts_path: str, out_dir: str, delay: float = 0.5):
    if model_key not in SUPPORTED_MODELS:
        print(f"Unknown model '{model_key}'. Choose from: {list(SUPPORTED_MODELS)}")
        sys.exit(1)

    _, _, gen_fn = SUPPORTED_MODELS[model_key]
    client = build_client(model_key)
    prompts = load_prompts(prompts_path)

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_path = Path(out_dir) / f"eval_results_{model_key}.json"

    # Resume support: load existing results
    existing: dict[str, dict] = {}
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            saved = json.load(f)
        existing = {r["prompt"]: r for r in saved.get("results", [])}
        print(f"Resuming — {len(existing)} prompts already done.")

    results = []
    for item in prompts:
        prompt    = item["prompt"]
        category  = item.get("category", "")
        prompt_id = item.get("id", -1)

        if prompt in existing:
            results.append(existing[prompt])
            continue

        print(f"[{prompt_id:02d}] {prompt} ...", end=" ", flush=True)
        t0 = time.time()
        svg, err = gen_fn(prompt, client)
        elapsed = time.time() - t0

        success = bool(svg and validate_svg(svg))
        r = {
            "id":       prompt_id,
            "prompt":   prompt,
            "category": category,
            "model":    model_key,
            "success":  success,
            "clip":     0.0,   # scored later by eval_models.py --score
            "dino":     None,  # N/A for text-only models
            "elements": count_elements(svg) if svg else 0,
            "time":     round(elapsed, 2),
            "svg":      svg or "",
            "error":    err,
        }
        results.append(r)

        ok = "OK" if success else f"FAIL ({err or 'no svg'})"
        print(f"{ok}  ({elapsed:.1f}s, {r['elements']} elements)")

        # Save after every prompt so a crash doesn't lose work
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"model": model_key, "results": results}, f, indent=2)

        time.sleep(delay)   # rate-limit

    # Final summary
    valid = [r for r in results if r["success"]]
    print(f"\nDone. {len(valid)}/{len(results)} valid SVGs → {out_path}")
    print("Next step: run  python eval_models.py --score {model}  to compute CLIP scores.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baseline SVG generation via API models")
    parser.add_argument("--model",   required=True,
                        choices=list(SUPPORTED_MODELS),
                        help="Which model to run")
    parser.add_argument("--prompts", default="eval_prompts.json",
                        help="Path to eval_prompts.json")
    parser.add_argument("--out_dir", default=".",
                        help="Directory to save eval_results_{model}.json")
    parser.add_argument("--delay",   type=float, default=0.5,
                        help="Seconds between API calls (default 0.5)")
    args = parser.parse_args()
    run(args.model, args.prompts, args.out_dir, args.delay)
