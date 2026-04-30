#!/usr/bin/env python
"""Run the two required model checks:

1. SVG-token perplexity on generated and Kaggle datasets separately.
2. Overfitting assessment for the trained adapter.

Designed for Kaggle/Colab T4. Example:

python check_svg_model_overfitting.py \
  --adapter /kaggle/working/qwen2vl_svg_lora/final_adapter \
  --generated-dataset /kaggle/input/diffusvg/training_pairs.json \
  --kaggle-dataset /kaggle/input/svg-dataset-for-generative-llm \
  --output-json /kaggle/working/overfitting_report.json \
  --output-md /kaggle/working/overfitting_report.md
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from types import SimpleNamespace

from evaluate_perplexity import evaluate_dataset, load_model_and_tokenizer, load_records, normalize_record


def _find_trainer_state(adapter: Path) -> Path | None:
    candidates = [
        adapter / "trainer_state.json",
        adapter.parent / "trainer_state.json",
        adapter.parent.parent / "trainer_state.json",
    ]
    candidates.extend(sorted(adapter.parent.glob("checkpoint-*/trainer_state.json")))
    candidates.extend(sorted(adapter.parent.parent.glob("checkpoint-*/trainer_state.json")))
    for path in candidates:
        if path.exists():
            return path
    return None


def _load_trainer_losses(path: Path | None) -> dict:
    if not path or not path.exists():
        return {"path": str(path) if path else "", "train": [], "eval": []}

    state = json.loads(path.read_text(encoding="utf-8"))
    train, evals = [], []
    for item in state.get("log_history", []):
        step = item.get("step")
        epoch = item.get("epoch")
        if "loss" in item:
            train.append({"step": step, "epoch": epoch, "loss": float(item["loss"])})
        if "eval_loss" in item:
            evals.append({"step": step, "epoch": epoch, "loss": float(item["eval_loss"])})
    return {"path": str(path), "train": train, "eval": evals}


def _count_scored_records(path: Path) -> int:
    return sum(1 for r in load_records(path) if normalize_record(r) is not None)


def _prompt_text(record: dict) -> str:
    item = normalize_record(record)
    if item:
        return item["prompt"]
    for key in ("prompt", "text", "caption", "instruction", "description"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _prompt_overlap(train_path: Path, prompt_path: Path | None) -> dict | None:
    if not prompt_path or not prompt_path.exists():
        return None

    train_prompts = {_prompt_text(r).lower() for r in load_records(train_path)}
    eval_prompts = [_prompt_text(r).lower() for r in load_records(prompt_path)]
    train_prompts.discard("")
    eval_prompts = [p for p in eval_prompts if p]
    overlap = sorted(set(eval_prompts) & train_prompts)
    return {
        "path": str(prompt_path),
        "train_prompts": len(train_prompts),
        "benchmark_prompts": len(set(eval_prompts)),
        "overlap_count": len(overlap),
        "overlap": overlap[:50],
    }


def _assess(perplexities: list[dict], losses: dict, generated_count: int, prompt_overlap: dict | None) -> dict:
    rows = {row["dataset"]: row for row in perplexities}
    generated = rows.get("generated")
    kaggle = rows.get("kaggle")

    signals: list[str] = []
    risks: list[str] = []

    train = losses.get("train", [])
    evals = losses.get("eval", [])
    last_train = train[-1]["loss"] if train else None
    last_eval = evals[-1]["loss"] if evals else None
    eval_train_ratio = None

    if train and evals:
        eval_train_ratio = last_eval / max(last_train, 1e-9)
        if train[-1]["loss"] < train[0]["loss"] and evals[-1]["loss"] > evals[0]["loss"]:
            signals.append("eval loss increased while train loss decreased")
        if eval_train_ratio > 1.25:
            signals.append(f"eval/train loss ratio is high ({eval_train_ratio:.2f})")
        elif eval_train_ratio <= 1.10:
            signals.append(f"eval/train loss ratio is healthy ({eval_train_ratio:.2f})")
    else:
        risks.append("trainer_state.json not found, so loss-curve overfitting could not be checked")

    ppl_ratio = None
    if generated and kaggle:
        ppl_ratio = kaggle["perplexity"] / max(generated["perplexity"], 1e-9)
        if ppl_ratio > 2.0:
            signals.append(f"Kaggle PPL is much higher than generated PPL ({ppl_ratio:.2f}x)")
        elif ppl_ratio > 1.5:
            risks.append(f"Kaggle PPL is moderately higher than generated PPL ({ppl_ratio:.2f}x)")
        else:
            signals.append(f"generated/Kaggle PPL gap is acceptable ({ppl_ratio:.2f}x)")

    if generated_count and generated_count < 100:
        risks.append(f"generated dataset is tiny ({generated_count} usable records)")

    for row in perplexities:
        if row["dataset"] in {"generated", "kaggle"} or not generated:
            continue
        ratio = row["perplexity"] / max(generated["perplexity"], 1e-9)
        if ratio > 2.0:
            risks.append(f"{row['dataset']} PPL is high vs generated ({ratio:.2f}x)")

    if prompt_overlap:
        if prompt_overlap["overlap_count"] > 0:
            risks.append(
                f"benchmark prompt overlap found: {prompt_overlap['overlap_count']} prompts overlap training prompts"
            )
        else:
            signals.append("no prompt overlap with supplied benchmark prompts")

    hard_overfit = any(
        s.startswith("eval loss increased")
        or s.startswith("eval/train loss ratio is high")
        or s.startswith("Kaggle PPL is much higher")
        for s in signals
    )
    verdict = "overfitting" if hard_overfit else "not_overfitting_now"
    if not hard_overfit and risks:
        verdict = "not_overfitting_now_but_high_risk"

    return {
        "verdict": verdict,
        "generated_records": generated_count,
        "last_train_loss": last_train,
        "last_eval_loss": last_eval,
        "eval_train_loss_ratio": eval_train_ratio,
        "kaggle_to_generated_ppl_ratio": ppl_ratio,
        "signals": signals,
        "risks": risks,
    }


def _write_md(path: Path, report: dict) -> None:
    rows = report["perplexity"]
    assess = report["assessment"]
    lines = [
        "# Perplexity and Overfitting Check",
        "",
        f"Verdict: **{assess['verdict']}**",
        "",
        "## Perplexity",
        "",
        "| Dataset | Records | Tokens | NLL | PPL |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['dataset']} | {row['records_scored']} | {row['target_tokens']} | "
            f"{row['nll']:.4f} | {row['perplexity']:.3f} |"
        )
    lines.extend(["", "## Overfitting Signals", ""])
    for item in assess["signals"] or ["No hard overfitting signal detected."]:
        lines.append(f"- {item}")
    if assess["risks"]:
        lines.extend(["", "## Risks", ""])
        for item in assess["risks"]:
            lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen2-VL-7B-Instruct")
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--generated-dataset", required=True)
    parser.add_argument("--kaggle-dataset", required=True)
    parser.add_argument("--extra-dataset", action="append", default=[], help="Optional name=path prompt+SVG dataset")
    parser.add_argument("--benchmark-prompts", default="", help="Optional prompt-only JSON/JSONL for leakage check")
    parser.add_argument("--trainer-state", default="")
    parser.add_argument("--max-seq-len", type=int, default=2048)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--output-json", default="overfitting_report.json")
    parser.add_argument("--output-md", default="overfitting_report.md")
    args = parser.parse_args()

    adapter = Path(args.adapter)
    generated_path = Path(args.generated_dataset)
    kaggle_path = Path(args.kaggle_dataset)
    trainer_state = Path(args.trainer_state) if args.trainer_state else _find_trainer_state(adapter)

    ppl_args = SimpleNamespace(
        model=args.model,
        adapter=args.adapter,
        model_class="auto",
        max_seq_len=args.max_seq_len,
        batch_size=args.batch_size,
        max_samples=args.max_samples,
        load_in_4bit=True,
    )
    model, tokenizer = load_model_and_tokenizer(ppl_args)
    perplexities = [
        evaluate_dataset("generated", generated_path, model, tokenizer, ppl_args),
        evaluate_dataset("kaggle", kaggle_path, model, tokenizer, ppl_args),
    ]
    for spec in args.extra_dataset:
        if "=" not in spec:
            raise ValueError("--extra-dataset must be name=path")
        name, raw_path = spec.split("=", 1)
        perplexities.append(evaluate_dataset(name, Path(raw_path), model, tokenizer, ppl_args))

    losses = _load_trainer_losses(trainer_state)
    generated_count = _count_scored_records(generated_path)
    overlap = _prompt_overlap(generated_path, Path(args.benchmark_prompts)) if args.benchmark_prompts else None
    assessment = _assess(perplexities, losses, generated_count, overlap)

    report = {
        "adapter": str(adapter),
        "model": args.model,
        "trainer_state": losses["path"],
        "perplexity": perplexities,
        "losses": losses,
        "prompt_overlap": overlap,
        "assessment": assessment,
    }

    Path(args.output_json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    _write_md(Path(args.output_md), report)

    print(json.dumps({"perplexity": perplexities, "assessment": assessment}, indent=2))


if __name__ == "__main__":
    main()
