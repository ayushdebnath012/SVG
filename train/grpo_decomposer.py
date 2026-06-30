"""
Plan C — GRPO (Group Relative Policy Optimization) training for the decomposer.

After SFT (train/sft_decomposer.py), GRPO fine-tunes the decomposer using
final SVG quality as a reward signal instead of cross-entropy loss. This
allows the model to discover decompositions that weren't in the training set
and to self-correct systematic SFT errors.

Why GRPO
--------
The reward (final SVG quality) is not differentiable — it requires executing
the full chain and measuring pixel MSE. GRPO avoids a separate value model by
normalizing rewards within a group of sampled decompositions for the same input,
making it efficient for small models.

Reward function
---------------
For a decomposed plan [step_1, ..., step_k] applied to produce final_svg:

    R = alpha * (1 - failure_aware_mse)
      + beta  * step_recall          (did we get the right task types?)
      + gamma * mean(geometry_ok_i)  (geometry preserved at each step)
      - delta * max(0, k - k_gold)   (penalise over-decomposition)

Default weights: alpha=0.6, beta=0.2, gamma=0.1, delta=0.1

Usage
-----
    python -m train.grpo_decomposer --config configs/train/grpo_decomposer.json

Config
------
    {
      "sft_checkpoint": "checkpoints/decomposer-sft",
      "output_dir":     "checkpoints/decomposer-grpo",
      "train_data":     "data/decomposer_train.jsonl",
      "group_size":     8,
      "kl_coef":        0.05,
      "learning_rate":  1e-5,
      "num_iterations": 1000,
      "reward_alpha":   0.6,
      "reward_beta":    0.2,
      "reward_gamma":   0.1,
      "reward_delta":   0.1,
      "patch_architecture": "skeleton_patch",
      "patch_model_config": "configs/models/qwen3.5-4b-openai.json"
    }
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Reward computation
# ---------------------------------------------------------------------------

def compute_reward(
    source_svg: str,
    answer_svg: str,
    steps: list[dict[str, str]],
    gold_steps: list[str],
    patch_architecture: str,
    patch_model: Any,
    weights: dict[str, float],
) -> float:
    """Execute the predicted step list and return a scalar reward in [0, 1]."""
    from svgpatchlab.decompose import ChainExecutor
    from svgpatchlab.eval.metrics import chain_metrics, evaluate_output

    executor = ChainExecutor(patch_model, architecture_name=patch_architecture)
    chain_result = executor.execute(source_svg, steps)

    output_svg = chain_result.output_svg
    eval_metrics = evaluate_output(
        source_svg,
        answer_svg,
        output_svg,
        candidate_patch=None,
        render=True,
    )
    predicted_types = [s["task"] for s in steps]
    step_m = chain_metrics(predicted_types, gold_steps)
    k = len(steps)
    k_gold = len(gold_steps)

    mse_reward = 1.0 - float(eval_metrics.get("failure_aware_mse") or 1.0)
    step_recall = float(step_m.get("step_recall", 0.0))
    geom_ok = float(eval_metrics.get("protected_geometry_preserved", False))
    over_decomp_penalty = max(0, k - k_gold)

    a = weights.get("alpha", 0.6)
    b = weights.get("beta", 0.2)
    g = weights.get("gamma", 0.1)
    d = weights.get("delta", 0.1)

    return a * mse_reward + b * step_recall + g * geom_ok - d * over_decomp_penalty


# ---------------------------------------------------------------------------
# GRPO training loop
# ---------------------------------------------------------------------------

def train(config: dict[str, Any]) -> None:
    """Run GRPO training. Requires: pip install torch transformers trl."""
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from trl import GRPOConfig, GRPOTrainer
    except ImportError as exc:
        raise SystemExit(f"GRPO training requires additional dependencies: {exc}")

    from svgpatchlab.config import load_model_config
    from svgpatchlab.models import RecordingModelAdapter, create_model

    tokenizer = AutoTokenizer.from_pretrained(config["sft_checkpoint"])
    model = AutoModelForCausalLM.from_pretrained(
        config["sft_checkpoint"], dtype=torch.bfloat16
    )

    patch_model = RecordingModelAdapter(
        create_model(load_model_config(config["patch_model_config"]))
    )
    patch_arch = config.get("patch_architecture", "skeleton_patch")
    weights = {
        "alpha": config.get("reward_alpha", 0.6),
        "beta": config.get("reward_beta", 0.2),
        "gamma": config.get("reward_gamma", 0.1),
        "delta": config.get("reward_delta", 0.1),
    }

    train_data = [
        json.loads(line)
        for line in Path(config["train_data"]).read_text().splitlines()
        if line.strip()
    ]

    def reward_fn(completions: list[str], batch: dict) -> list[float]:
        rewards = []
        for i, completion in enumerate(completions):
            try:
                from svgpatchlab.core.patch import extract_json_object
                payload = extract_json_object(completion)
                steps = payload.get("steps", [])
                r = compute_reward(
                    source_svg=batch["source_svg"][i],
                    answer_svg=batch["answer_svg"][i],
                    steps=steps,
                    gold_steps=batch["gold_steps"][i],
                    patch_architecture=patch_arch,
                    patch_model=patch_model,
                    weights=weights,
                )
            except Exception:
                r = 0.0
            rewards.append(r)
        return rewards

    grpo_config = GRPOConfig(
        output_dir=config["output_dir"],
        num_train_epochs=1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=config.get("group_size", 8),
        learning_rate=config.get("learning_rate", 1e-5),
        kl_coef=config.get("kl_coef", 0.05),
        logging_steps=10,
    )
    trainer = GRPOTrainer(
        model=model,
        tokenizer=tokenizer,
        reward_funcs=reward_fn,
        args=grpo_config,
        train_dataset=train_data,
    )
    trainer.train()
    model.save_pretrained(config["output_dir"])
    tokenizer.save_pretrained(config["output_dir"])
    print(f"GRPO checkpoint saved to {config['output_dir']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="GRPO training for the Plan C decomposer")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    train(config)


if __name__ == "__main__":
    main()
