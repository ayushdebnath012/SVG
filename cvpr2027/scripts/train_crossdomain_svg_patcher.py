"""LoRA training for source-SVG plus instruction to validated patch JSON."""
from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import nullcontext
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from svgpatchlab.core import (  # noqa: E402
    apply_patch,
    build_scene,
    build_scene_graph,
    generic_svg_policy,
    parse_patch,
    validate_patch,
)
from svgpatchlab.core.xml import normalized_tree, parse_svg  # noqa: E402


DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"


def load_rows(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _strict_json(text: str):
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except (TypeError, ValueError):
        return None


def score(row: dict, prediction: str) -> dict:
    result = {"json_valid": False, "patch_valid": False, "exact_patch": False,
              "target_tree_equal": False, "reference_integrity": False, "error": None}
    direct = _strict_json(prediction)
    result["json_valid"] = direct is not None
    if direct is not None:
        result["exact_patch"] = direct == row["target_patch"]
    try:
        patch = parse_patch(prediction)
        validate_patch(patch, build_scene(row["source_svg"]), generic_svg_policy(max_operations=500))
        result["patch_valid"] = True
        output = apply_patch(row["source_svg"], patch)
        scene = build_scene_graph(output)
        result["target_tree_equal"] = (
            normalized_tree(parse_svg(output)) == normalized_tree(parse_svg(row["target_svg"]))
        )
        result["reference_integrity"] = (
            not scene["duplicate_xml_ids"] and
            not any(edge["to"] is None for edge in scene["reference_edges"])
        )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"[:300]
    return result


def _balanced_eval(rows: list[dict], count: int) -> list[dict]:
    by_family = defaultdict(list)
    for row in rows:
        by_family[row["family"]].append(row)
    families = sorted(by_family)
    chosen = []
    while len(chosen) < min(count, len(rows)):
        progressed = False
        for family in families:
            if by_family[family]:
                chosen.append(by_family[family].pop(0)); progressed = True
                if len(chosen) == min(count, len(rows)): break
        if not progressed: break
    return chosen


def evaluate(model, tokenizer, rows: list[dict], label: str, out: Path, max_new_tokens: int) -> dict:
    import torch
    model.eval()
    if hasattr(model, "gradient_checkpointing_disable"):
        model.gradient_checkpointing_disable()
    model.config.use_cache = True
    records = []
    destination = out / f"{label}-predictions.jsonl"
    for index, row in enumerate(rows, 1):
        rendered = tokenizer.apply_chat_template(
            [{"role": "user", "content": row["prompt"]}], tokenize=False,
            add_generation_prompt=True)
        inputs = tokenizer(rendered, return_tensors="pt", add_special_tokens=False).to("cuda")
        with torch.inference_mode():
            generated = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False,
                                       pad_token_id=tokenizer.pad_token_id)
        raw = tokenizer.decode(generated[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        record = {"id": row["id"], "family": row["family"], "edit_kind": row["edit_kind"],
                  "instruction": row["instruction"], "engineering_status": row["engineering_status"],
                  "prediction": raw, "metrics": score(row, raw)}
        records.append(record)
        with destination.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
        print(label, index, "/", len(rows), row["family"],
              "tree=", record["metrics"]["target_tree_equal"], flush=True)
    metrics = {}
    for name in ("json_valid", "patch_valid", "exact_patch", "target_tree_equal", "reference_integrity"):
        metrics[name] = sum(record["metrics"][name] for record in records)
    metrics["n"] = len(records)
    metrics["by_family"] = {}
    for family in sorted({record["family"] for record in records}):
        subset = [record for record in records if record["family"] == family]
        metrics["by_family"][family] = {"n": len(subset), "target_tree_equal": sum(
            record["metrics"]["target_tree_equal"] for record in subset)}
    (out / f"{label}-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    return metrics


def _training_arguments(cls, **kwargs):
    """Build TrainingArguments with only the keywords this transformers build accepts.

    The Colab image is not pinned and its signature has churned: evaluation_strategy was renamed to
    eval_strategy, and warmup_ratio is absent from some builds. An unknown keyword is a hard
    TypeError, so a cosmetic scheduling option aborted a run after the baseline had already been
    measured. Drop what the signature will not take and say so, rather than losing the run.
    """
    import inspect
    parameters = inspect.signature(cls.__init__).parameters
    if "eval_strategy" not in parameters and "eval_strategy" in kwargs:
        kwargs["evaluation_strategy"] = kwargs.pop("eval_strategy")
    if "report_to" in kwargs and kwargs["report_to"] == []:
        kwargs["report_to"] = "none"
    dropped = sorted(k for k in kwargs if k not in parameters)
    for key in dropped:
        kwargs.pop(key)
    if dropped:
        print(f"note: this transformers build does not accept {dropped}; proceeding without them",
              flush=True)
    return cls(**kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--max-length", type=int, default=4096)
    parser.add_argument("--max-new-tokens", type=int, default=1400)
    parser.add_argument("--eval-count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=260925)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    import torch
    from huggingface_hub import model_info
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, set_seed

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required")
    args.out.mkdir(parents=True, exist_ok=True)
    set_seed(args.seed)
    rows = {split: load_rows(args.data / f"{split}.jsonl.gz")
            for split in ("train", "validation", "test")}
    groups = {split: {row["lineage_id"] for row in items} for split, items in rows.items()}
    if any(groups[a] & groups[b] for a in groups for b in groups if a < b):
        raise ValueError("source lineage leakage between splits")
    evaluation = _balanced_eval(rows["test"], args.eval_count)

    revision = model_info(args.model).sha
    run_manifest = {
        "status": "started", "created_utc": datetime.now(timezone.utc).isoformat(),
        "model": args.model, "model_revision": revision, "seed": args.seed,
        "epochs": args.epochs, "max_length": args.max_length,
        "train_examples": len(rows["train"]), "validation_examples": len(rows["validation"]),
        "test_examples": len(rows["test"]), "test_evaluated": len(evaluation),
        "dataset_summary": json.loads((args.data / "dataset-summary.json").read_text()),
        "dataset_manifest_sha256": hashlib.sha256((args.data / "sha256-manifest.json").read_bytes()).hexdigest(),
        "training_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "gpu": torch.cuda.get_device_name(0),
        "selection": "fixed final epoch; no test-based checkpoint selection",
    }
    (args.out / "run-manifest.json").write_text(json.dumps(run_manifest, indent=2) + "\n")
    (args.out / "packages.txt").write_text(
        subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True))

    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=revision)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    tokenizer.padding_side = "right"
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    base = AutoModelForCausalLM.from_pretrained(args.model, revision=revision, dtype=dtype,
                                               device_map={"": 0}, attn_implementation="sdpa")
    if hasattr(base, "enable_input_require_grads"):
        base.enable_input_require_grads()
    model = get_peft_model(base, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM"))
    model.print_trainable_parameters()

    def render_prompt(row):
        return tokenizer.apply_chat_template([{"role": "user", "content": row["prompt"]}],
                                             tokenize=False, add_generation_prompt=True)

    def encode(items):
        encoded, omitted, lengths = [], 0, []
        for row in items:
            prefix = tokenizer(render_prompt(row), add_special_tokens=False)["input_ids"]
            answer_text = json.dumps(row["target_patch"], separators=(",", ":")) + tokenizer.eos_token
            answer = tokenizer(answer_text, add_special_tokens=False)["input_ids"]
            lengths.append(len(prefix) + len(answer))
            if len(prefix) + len(answer) > args.max_length:
                omitted += 1; continue
            encoded.append({"input_ids": prefix + answer, "labels": [-100] * len(prefix) + answer})
        return encoded, omitted, lengths

    encoded_train, omitted_train, train_lengths = encode(rows["train"])
    encoded_validation, omitted_validation, validation_lengths = encode(rows["validation"])
    token_summary = {
        "train_encoded": len(encoded_train), "train_omitted": omitted_train,
        "validation_encoded": len(encoded_validation), "validation_omitted": omitted_validation,
        "maximum_train_tokens": max(train_lengths), "maximum_validation_tokens": max(validation_lengths),
    }
    (args.out / "token-summary.json").write_text(json.dumps(token_summary, indent=2) + "\n")
    print(json.dumps(token_summary, indent=2), flush=True)
    if omitted_train or omitted_validation:
        raise ValueError("examples exceed max length; increase --max-length instead of silently truncating")

    def collate(batch):
        length = max(len(item["input_ids"]) for item in batch)
        return {
            "input_ids": torch.tensor([item["input_ids"] + [tokenizer.pad_token_id] *
                                       (length-len(item["input_ids"])) for item in batch]),
            "labels": torch.tensor([item["labels"] + [-100] *
                                    (length-len(item["labels"])) for item in batch]),
            "attention_mask": torch.tensor([[1] * len(item["input_ids"]) + [0] *
                                            (length-len(item["input_ids"])) for item in batch]),
        }

    print("--- base evaluation ---", flush=True)
    context = model.disable_adapter() if hasattr(model, "disable_adapter") else nullcontext()
    with context:
        before = evaluate(model, tokenizer, evaluation, "base", args.out, args.max_new_tokens)

    model.train(); model.config.use_cache = False
    training_args = _training_arguments(
        TrainingArguments,
        output_dir=str(args.out / "checkpoints"), num_train_epochs=args.epochs,
        per_device_train_batch_size=1, gradient_accumulation_steps=16,
        per_device_eval_batch_size=1, learning_rate=2e-4,
        lr_scheduler_type="cosine", warmup_ratio=.05, weight_decay=.01,
        logging_steps=10, eval_strategy="epoch", save_strategy="steps", save_steps=250,
        save_total_limit=1, bf16=dtype == torch.bfloat16, fp16=dtype == torch.float16,
        report_to=[], seed=args.seed, data_seed=args.seed,
        gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
        remove_unused_columns=False, label_names=["labels"], optim="adamw_torch",
        dataloader_num_workers=0,
    )
    trainer = Trainer(model=model, args=training_args, train_dataset=encoded_train,
                      eval_dataset=encoded_validation, data_collator=collate)
    checkpoints = sorted((args.out / "checkpoints").glob("checkpoint-*"),
                         key=lambda path: int(path.name.split("-")[-1]))
    started = time.perf_counter()
    history = trainer.train(resume_from_checkpoint=str(checkpoints[-1])
                            if args.resume and checkpoints else None)
    training_seconds = time.perf_counter() - started
    model.save_pretrained(args.out / "adapter")
    tokenizer.save_pretrained(args.out / "adapter")
    trainer.state.save_to_json(str(args.out / "trainer-state.json"))
    (args.out / "training-metrics.json").write_text(json.dumps(history.metrics, indent=2) + "\n")

    print("--- trained evaluation ---", flush=True)
    after = evaluate(model, tokenizer, evaluation, "trained", args.out, args.max_new_tokens)
    summary = {
        "status": "complete", "completed_utc": datetime.now(timezone.utc).isoformat(),
        "model": args.model, "model_revision": revision, "gpu": torch.cuda.get_device_name(0),
        "epochs": args.epochs, "training_seconds": training_seconds,
        "train_examples": len(encoded_train), "validation_examples": len(encoded_validation),
        "evaluation_protocol": "balanced held-out lineages; greedy generation; exact applied target tree",
        "before": before, "after": after, "training_metrics": history.metrics,
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    run_manifest.update(status="complete", completed_utc=summary["completed_utc"],
                        training_seconds=training_seconds, global_steps=trainer.state.global_step)
    (args.out / "run-manifest.json").write_text(json.dumps(run_manifest, indent=2) + "\n")
    shutil.make_archive(str(args.out) + "-artifacts", "zip", args.out)
    print(json.dumps(summary, indent=2), flush=True)
    print("ARTIFACT", str(args.out) + "-artifacts.zip", flush=True)


if __name__ == "__main__":
    main()
