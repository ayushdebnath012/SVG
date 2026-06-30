"""
Plan C — SFT training for the decomposer model.

The decomposer converts a complex edit instruction into an ordered list of
Basic Task steps (change_color, set_contour, upside_down, transparency,
crop_to_half, rotate, flip, delete).

Data generation
---------------
Training examples are built programmatically by chaining 2-4 Basic Task
cases from SVGEditBench (using non-benchmark emoji IDs):

    1. Sample k Basic Task cases sharing the same base emoji.
    2. Chain them: apply gold patch for step i to SVG_{i-1} to get SVG_i.
    3. Write a natural-language composite instruction.
    4. Supervision target: ordered JSON list of {"task", "instruction"} pairs.

Usage
-----
    python -m train.sft_decomposer --config configs/train/sft_decomposer.json

Config
------
    {
      "base_model": "Qwen/Qwen3.5-4B",
      "output_dir": "checkpoints/decomposer-sft",
      "train_data": "data/decomposer_train.jsonl",
      "val_data":   "data/decomposer_val.jsonl",
      "max_steps": 4,
      "max_seq_len": 2048,
      "batch_size": 8,
      "grad_accum": 4,
      "learning_rate": 2e-5,
      "num_epochs": 3,
      "lora_r": 16,
      "lora_alpha": 32
    }
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

def generate_chain_example(
    cases: list[dict[str, Any]],
    max_steps: int = 4,
    rng: random.Random | None = None,
) -> dict[str, Any] | None:
    """Build one synthetic chain example from k randomly sampled Basic Task cases.

    Returns a dict with keys:
        svg         — the starting SVG string
        instruction — composite natural-language instruction
        steps       — list of {"task", "instruction"} dicts (supervision target)
        final_svg   — the SVG after all gold patches are applied
    Returns None if the chain cannot be constructed (e.g., derive_patch fails).
    """
    from svgpatchlab.core import apply_patch, derive_patch

    if rng is None:
        rng = random.Random()

    k = rng.randint(2, max_steps)
    sampled = rng.sample(cases, min(k, len(cases)))
    if not sampled:
        return None

    current_svg = sampled[0]["source_svg"]
    steps: list[dict[str, str]] = []
    for case in sampled:
        try:
            patch = derive_patch(case["source_svg"], case["answer_svg"])
            current_svg = apply_patch(current_svg, patch)
            steps.append({"task": case["task"], "instruction": case["instruction"]})
        except Exception:
            continue

    if len(steps) < 2:
        return None

    composite_instruction = "; then ".join(s["instruction"] for s in steps)
    return {
        "svg": sampled[0]["source_svg"],
        "instruction": composite_instruction,
        "steps": steps,
        "final_svg": current_svg,
    }


def build_training_dataset(
    bench_root: str,
    output_path: str,
    n_examples: int = 5000,
    max_steps: int = 4,
    seed: int = 42,
) -> None:
    """Generate and write SFT training data to a JSONL file."""
    from svgpatchlab.data import SVGEditBench

    rng = random.Random(seed)
    bench = SVGEditBench(bench_root)
    cases = [
        {
            "task": case.task,
            "emoji_id": case.emoji_id,
            "instruction": case.instruction,
            "source_svg": case.source_svg,
            "answer_svg": case.answer_svg,
        }
        for case in bench.iter_cases()
    ]

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with out.open("w") as f:
        while written < n_examples:
            example = generate_chain_example(cases, max_steps=max_steps, rng=rng)
            if example:
                f.write(json.dumps(example) + "\n")
                written += 1
    print(f"Wrote {written} examples to {out}")


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def format_sft_example(example: dict[str, Any], tokenizer: Any) -> dict[str, Any]:
    """Format one example into model input/output for cross-entropy SFT."""
    from svgpatchlab.core import build_scene
    from svgpatchlab.decompose.model import DECOMPOSE_PROMPT

    scene = build_scene(example["svg"])
    prompt = DECOMPOSE_PROMPT.substitute(
        instruction=example["instruction"],
        skeleton=json.dumps(scene, indent=2, sort_keys=True),
    )
    target = json.dumps({"steps": example["steps"]})
    full_text = prompt + "\n" + target
    return tokenizer(full_text, truncation=True, max_length=2048, return_tensors="pt")


def train(config: dict[str, Any]) -> None:
    """Run SFT training. Requires: pip install transformers peft datasets torch."""
    try:
        import torch
        from peft import LoraConfig, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
        from datasets import Dataset
    except ImportError as exc:
        raise SystemExit(f"SFT training requires additional dependencies: {exc}")

    tokenizer = AutoTokenizer.from_pretrained(config["base_model"])
    model = AutoModelForCausalLM.from_pretrained(config["base_model"], torch_dtype=torch.bfloat16)

    lora_config = LoraConfig(
        r=config.get("lora_r", 16),
        lora_alpha=config.get("lora_alpha", 32),
        target_modules=["q_proj", "v_proj"],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    def load_jsonl(path: str) -> list[dict]:
        return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

    train_data = load_jsonl(config["train_data"])
    val_data = load_jsonl(config["val_data"])

    train_dataset = Dataset.from_list([format_sft_example(ex, tokenizer) for ex in train_data])
    val_dataset = Dataset.from_list([format_sft_example(ex, tokenizer) for ex in val_data])

    args = TrainingArguments(
        output_dir=config["output_dir"],
        num_train_epochs=config.get("num_epochs", 3),
        per_device_train_batch_size=config.get("batch_size", 8),
        gradient_accumulation_steps=config.get("grad_accum", 4),
        learning_rate=config.get("learning_rate", 2e-5),
        evaluation_strategy="epoch",
        save_strategy="epoch",
        bf16=torch.cuda.is_available(),
        logging_steps=50,
    )
    trainer = Trainer(model=model, args=args, train_dataset=train_dataset, eval_dataset=val_dataset)
    trainer.train()
    model.save_pretrained(config["output_dir"])
    tokenizer.save_pretrained(config["output_dir"])
    print(f"SFT checkpoint saved to {config['output_dir']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="SFT training for the Plan C decomposer")
    parser.add_argument("--config", required=True)
    parser.add_argument("--generate-data-only", action="store_true")
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text())
    if args.generate_data_only:
        build_training_dataset(
            config.get("bench_root", "SVGEditBench"),
            config.get("train_data", "data/decomposer_train.jsonl"),
            n_examples=config.get("n_train_examples", 5000),
        )
    else:
        train(config)


if __name__ == "__main__":
    main()
