#!/usr/bin/env python3
"""Run text-to-SVG generation prompts through a model config and report failures.

Example:
    set -a; . ./.env; set +a
    python3 scripts/eval_generation.py \
        --model-config configs/models/openai-gpt-6-astra.json \
        --limit 3 --output-dir runs/gen-astra-smoke
Then open runs/gen-astra-smoke/index.html (failures are listed first).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from svgpatchlab.config import load_model_config  # noqa: E402
from svgpatchlab.eval.generation import load_cases, rescore, run_generation_eval  # noqa: E402
from svgpatchlab.eval.render import RendererUnavailable, ensure_renderer  # noqa: E402
from svgpatchlab.models.factory import create_model  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model-config", help="required unless --rescore")
    parser.add_argument("--prompts", default="configs/prompts/engineering_v1.json")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--limit", type=int, help="only the first N prompts")
    parser.add_argument("--ids", nargs="*", help="only these prompt ids")
    parser.add_argument("--samples", type=int, default=1, help="generations per prompt")
    parser.add_argument("--template", default="generation_v1")
    parser.add_argument("--render", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--price-in", type=float, default=0.0, help="USD per 1M input tokens, for the estimate")
    parser.add_argument("--price-out", type=float, default=0.0, help="USD per 1M output tokens, for the estimate")
    parser.add_argument("--rescore", action="store_true", help="re-run checks on an existing output dir; no model calls")
    args = parser.parse_args()

    if args.render:
        try:
            ensure_renderer()
        except RendererUnavailable as exc:
            sys.exit(f"{exc}\n(or pass --no-render)")

    cases = load_cases(args.prompts)
    if args.ids:
        cases = [c for c in cases if c.id in set(args.ids)]
    if args.limit:
        cases = cases[: args.limit]
    if not cases:
        sys.exit("no prompts selected")
    if not args.rescore and not args.model_config:
        sys.exit("--model-config is required unless --rescore")

    if args.rescore:
        summary = rescore(args.output_dir, cases, render=args.render, price_in_per_m=args.price_in, price_out_per_m=args.price_out)
        print(f"rescored {summary['cases']} records: ok {summary['ok']}/{summary['cases']} | failures: "
              + (", ".join(f"{k}={v}" for k, v in summary["failures"].items() if v) or "none"))
        return

    model_config = load_model_config(args.model_config)
    model = create_model(model_config)
    print(f"model={model_config.get('model')} base_url={model_config.get('base_url')} prompts={len(cases)} samples={args.samples}")
    summary = run_generation_eval(
        model,
        cases,
        args.output_dir,
        render=args.render,
        samples=args.samples,
        template_name=args.template,
        price_in_per_m=args.price_in,
        price_out_per_m=args.price_out,
    )
    print()
    print(f"ok {summary['ok']}/{summary['cases']} | failures: " + ", ".join(f"{k}={v}" for k, v in summary["failures"].items() if v))
    print(f"tokens {summary['prompt_tokens']} in / {summary['completion_tokens']} out | est ${summary['estimated_cost_usd']}"
          + (f" | gateway-reported ${summary['gateway_reported_cost_usd']}" if summary["gateway_reported_cost_usd"] else ""))
    print(f"report: {Path(args.output_dir) / 'index.html'}")


if __name__ == "__main__":
    main()
