from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from svgpatchlab.architectures.factory import ARCHITECTURES
from svgpatchlab.config import load_config, load_model_config
from svgpatchlab.data import SVGEditBench
from svgpatchlab.eval.runner import run_evaluation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="svgpatchlab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="inspect SVGEditBench")
    inspect_parser.add_argument("dataset", nargs="?", default="SVGEditBench")

    evaluate_parser = subparsers.add_parser("evaluate", help="run one experiment configuration")
    evaluate_parser.add_argument("--config", required=True)
    evaluate_parser.add_argument("--model-config")
    evaluate_parser.add_argument("--architecture", choices=sorted(ARCHITECTURES))
    evaluate_parser.add_argument("--limit", type=int)
    evaluate_parser.add_argument("--limit-per-task", type=int)
    evaluate_parser.add_argument("--output-dir")
    evaluate_parser.add_argument(
        "--render",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="enable or disable CairoSVG raster metrics",
    )

    subparsers.add_parser("architectures", help="list available architectures")

    matrix_parser = subparsers.add_parser("matrix", help="run several architectures with one model")
    matrix_parser.add_argument("--config", default="configs/experiments/skeleton_patch.json")
    matrix_parser.add_argument("--model-config", required=True)
    matrix_parser.add_argument(
        "--architectures",
        nargs="+",
        default=[
            "full_rewrite",
            "full_context_patch",
            "skeleton_patch",
            "two_stage_patch",
            "visual_skeleton_patch",
            "oracle_target_patch",
        ],
        choices=sorted(ARCHITECTURES),
    )
    matrix_parser.add_argument("--limit", type=int)
    matrix_parser.add_argument("--limit-per-task", type=int)
    matrix_parser.add_argument("--output-root", default="runs/matrix")
    matrix_parser.add_argument(
        "--render", action=argparse.BooleanOptionalAction, default=None
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "inspect":
        print(json.dumps(SVGEditBench(args.dataset).summary(), indent=2, sort_keys=True))
    elif args.command == "evaluate":
        config = load_config(args.config)
        if args.model_config:
            config["model"] = load_model_config(args.model_config)
        if args.architecture:
            config["architecture"]["name"] = args.architecture
        if args.limit is not None:
            config["dataset"]["limit"] = args.limit
        if args.limit_per_task is not None:
            config["dataset"]["limit_per_task"] = args.limit_per_task
        if args.output_dir:
            config.setdefault("evaluation", {})["output_dir"] = args.output_dir
        if args.render is not None:
            config.setdefault("evaluation", {})["render"] = args.render
        print(json.dumps(run_evaluation(config), indent=2, sort_keys=True))
    elif args.command == "architectures":
        print("\n".join(sorted(ARCHITECTURES)))
    elif args.command == "matrix":
        base_config = load_config(args.config)
        model_config = load_model_config(args.model_config)
        output_root = Path(args.output_root)
        summaries = {}
        for architecture_name in args.architectures:
            config = copy.deepcopy(base_config)
            config["model"] = model_config
            config["architecture"]["name"] = architecture_name
            config.setdefault("evaluation", {})["output_dir"] = str(
                output_root / architecture_name
            )
            if args.limit is not None:
                config["dataset"]["limit"] = args.limit
            if args.limit_per_task is not None:
                config["dataset"]["limit_per_task"] = args.limit_per_task
            if args.render is not None:
                config["evaluation"]["render"] = args.render
            summaries[architecture_name] = run_evaluation(config)
        output_root.mkdir(parents=True, exist_ok=True)
        matrix_path = output_root / "matrix-summary.json"
        matrix_path.write_text(json.dumps(summaries, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"matrix_summary": str(matrix_path), "architectures": list(summaries)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
