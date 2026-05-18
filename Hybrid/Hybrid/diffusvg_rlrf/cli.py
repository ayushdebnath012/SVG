from __future__ import annotations

import argparse
import json

from .config import apply_a100_profile, apply_legacy_t4_profile, load_config
from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="DiffuSVG Text2SVG RLRF experiment runner")
    parser.add_argument("--config", default="", help="Path to JSON config override")
    parser.add_argument(
        "--profile",
        choices=["config", "legacy-t4", "a100"],
        default="config",
        help="Hardware profile: legacy-t4 (NF4/16GB), a100 (bf16/SFT+RLRF/VLM judge)",
    )
    parser.add_argument("--policy-model", default="", help="Qwen base model path used by OmniSVG")
    parser.add_argument("--adapter", default="", help="Existing RLRF/PEFT adapter to train/evaluate")
    parser.add_argument("--omnisvg-dir", default="", help="Path to OmniSVG repo containing inference.py")
    parser.add_argument("--omnisvg-model-size", default="", help="OmniSVG model size, usually 4B on T4")
    parser.add_argument("--omnisvg-model", default="", help="Override OmniSVG Qwen model path")
    parser.add_argument("--omnisvg-weights", default="", help="Override OmniSVG fine-tuned weights path or HF repo")
    parser.add_argument("--bootstrap-sft", action="store_true", help="Run optional custom SFT bootstrap before RLRF")
    parser.add_argument("--sft-pairs", default="", help="Prompt/SVG JSON for optional bootstrap SFT")
    parser.add_argument("--diffusvg-base-pairs", default="", help="Alias for --sft-pairs")
    parser.add_argument("--prompts", default="", help="Prompt JSON/TXT for Text2SVG RLRF")
    parser.add_argument("--eval-prompts", default="", help="Prompt JSON/TXT/directory for evaluation")
    parser.add_argument("--output", default="", help="Output directory")
    parser.add_argument("--steps", type=int, default=0, help="Override RLRF train steps")
    parser.add_argument("--no-diffusvg-base", action="store_true", help="Disable optional bootstrap SFT")
    parser.add_argument("--no-rl", action="store_true", help="Skip RLRF and only evaluate")
    parser.add_argument("--no-eval", action="store_true", help="Skip evaluation")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.profile == "legacy-t4":
        apply_legacy_t4_profile(cfg)
    elif args.profile == "a100":
        apply_a100_profile(cfg)
    if args.policy_model:
        cfg.diffusvg.model_name_or_path = args.policy_model
    if args.adapter:
        cfg.diffusvg.adapter_name_or_path = args.adapter
    if args.omnisvg_dir:
        cfg.omnisvg.repo_dir = args.omnisvg_dir
    if args.omnisvg_model_size:
        cfg.omnisvg.model_size = args.omnisvg_model_size
    if args.omnisvg_model:
        cfg.omnisvg.model_path = args.omnisvg_model
    if args.omnisvg_weights:
        cfg.omnisvg.weight_path = args.omnisvg_weights
    if args.sft_pairs or args.diffusvg_base_pairs:
        cfg.sft.pairs_path = args.sft_pairs or args.diffusvg_base_pairs
    if args.bootstrap_sft:
        cfg.sft.enabled = True
    if args.prompts:
        cfg.rlrf.prompt_path = args.prompts
    if args.eval_prompts:
        cfg.eval.prompt_path = args.eval_prompts
    if args.output:
        cfg.runtime.output_dir = args.output
    if args.steps:
        cfg.rlrf.train_steps = args.steps
    if args.no_diffusvg_base:
        cfg.sft.enabled = False
    if args.no_rl:
        cfg.rlrf.enabled = False
    if args.no_eval:
        cfg.eval.enabled = False

    result = run_pipeline(cfg)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
