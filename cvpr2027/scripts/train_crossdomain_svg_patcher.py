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

sys.path.insert(0, str(ROOT / "scripts"))
try:  # network families are scored by re-solving the edited drawing
    import engsvg_networks as networks
except ImportError as error:  # other families never need it
    networks, NETWORK_IMPORT_ERROR = None, error


def load_rows(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


ADDRESS = "nodes"  # "ids": the model reads and writes '#<svg id>' instead of positional node ids


def _address_maps(svg: str):
    scene = build_scene(svg)
    to_xml, children = {}, {}
    for node in scene["nodes"]:
        if node["attributes"].get("id"):
            to_xml[node["id"]] = node["attributes"]["id"]
        if node["parent"] is not None:
            children[node["parent"]] = children.get(node["parent"], 0) + 1
    return to_xml, {xml: node for node, xml in to_xml.items()}, children


def to_id_addressed(patch: dict, svg: str) -> dict:
    """Name elements by their SVG id; an insertion at the end of its parent becomes index "end".

    Positional node ids (n77 = the 77th element) make the model count through the whole document,
    which it does badly; an id such as #R5-label is written on the element it refers to.
    """
    to_xml, _, children = _address_maps(svg)
    name = lambda node: "#" + to_xml[node] if node in to_xml else node  # noqa: E731
    operations = []
    for operation in patch["operations"]:
        operation = dict(operation)
        if "targets" in operation:
            operation["targets"] = [name(target) for target in operation["targets"]]
        if operation.get("op") == "insert_subtree":
            if operation.get("index") == children.get(operation["parent"], 0):
                operation["index"] = "end"
            operation["parent"] = name(operation["parent"])
        operations.append(operation)
    return {**patch, "operations": operations}


def from_id_addressed(text: str, svg: str) -> str:
    """Translate an id-addressed prediction back to the executor's positional form."""
    start = text.find("{")
    if start < 0:
        return text
    try:
        value, _ = json.JSONDecoder().raw_decode(text[start:])
    except ValueError:
        return text
    if not isinstance(value, dict) or not isinstance(value.get("operations"), list):
        return text
    _, from_xml, children = _address_maps(svg)
    resolve = lambda ref: from_xml.get(ref[1:], ref) if isinstance(ref, str) and ref.startswith("#") else ref  # noqa: E731
    for operation in value["operations"]:
        if not isinstance(operation, dict):
            continue
        if isinstance(operation.get("targets"), list):
            operation["targets"] = [resolve(target) for target in operation["targets"]]
        if "parent" in operation:
            operation["parent"] = resolve(operation["parent"])
            if operation.get("index") == "end":
                operation["index"] = children.get(operation["parent"], 0)
                children[operation["parent"]] = operation["index"] + 1
    return json.dumps(value)


def target_answer(row: dict) -> dict:
    return to_id_addressed(row["target_patch"], row["source_svg"]) if ADDRESS == "ids" else row["target_patch"]


def prompt_text(row: dict) -> str:
    if ADDRESS != "ids":
        return row["prompt"]
    return row["prompt"].replace("Return only an SVGPatchLab patch JSON.",
                                 "Return only an SVGPatchLab patch JSON. Refer to elements as '#' followed by their "
                                 "id attribute; use index \"end\" to append to a group.", 1)


def _strict_json(text: str):
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except (TypeError, ValueError):
        return None


def score(row: dict, prediction: str) -> dict:
    result = {"json_valid": False, "patch_valid": False, "exact_patch": False,
              "target_tree_equal": False, "reference_integrity": False, "error": None,
              "physics_equal": None}
    physics = "target_model" in row and row.get("physics_from_drawing")
    if physics:
        if networks is None:
            raise RuntimeError(f"network rows need engsvg_networks: {NETWORK_IMPORT_ERROR}")
        result["physics_equal"] = False
    direct = _strict_json(prediction)
    result["json_valid"] = direct is not None
    if direct is not None:
        result["exact_patch"] = direct == target_answer(row)
    if ADDRESS == "ids":
        prediction = from_id_addressed(prediction, row["source_svg"])
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
        if physics:
            # Same network, same solution: credit it even if the markup differs from the gold patch.
            match = networks.physics_match(output, row["family"], row["target_model"])
            result["physics_equal"] = bool(match.get("topology_equal") and match["physics_equal"])
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


def evaluate(model, tokenizer, rows: list[dict], label: str, out: Path, max_new_tokens: int,
             batch_size: int = 1) -> dict:
    import torch
    model.eval()
    if hasattr(model, "gradient_checkpointing_disable"):
        model.gradient_checkpointing_disable()
    model.config.use_cache = True
    records = []
    destination = out / f"{label}-predictions.jsonl"
    side = tokenizer.padding_side
    tokenizer.padding_side = "left"  # generation continues from the right edge of every prompt
    try:
        for start in range(0, len(rows), batch_size):
            batch = rows[start:start + batch_size]
            rendered = [tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt_text(row)}], tokenize=False,
                add_generation_prompt=True) for row in batch]
            inputs = tokenizer(rendered, return_tensors="pt", add_special_tokens=False,
                               padding=True).to("cuda")
            with torch.inference_mode():
                generated = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False,
                                           pad_token_id=tokenizer.pad_token_id)
            width = inputs["input_ids"].shape[1]
            for offset, row in enumerate(batch):
                raw = tokenizer.decode(generated[offset][width:], skip_special_tokens=True)
                record = {"id": row["id"], "family": row["family"], "edit_kind": row["edit_kind"],
                          "instruction": row["instruction"], "engineering_status": row["engineering_status"],
                          "prediction": raw, "metrics": score(row, raw)}
                records.append(record)
                with destination.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record, separators=(",", ":")) + "\n")
                physics = record["metrics"]["physics_equal"]
                print(label, len(records), "/", len(rows), row["family"],
                      "tree=", record["metrics"]["target_tree_equal"],
                      "" if physics is None else f"physics= {physics}", flush=True)
    finally:
        tokenizer.padding_side = side
    metrics = {}
    for name in ("json_valid", "patch_valid", "exact_patch", "target_tree_equal", "reference_integrity"):
        metrics[name] = sum(record["metrics"][name] for record in records)
    metrics["n"] = len(records)
    scored = [record for record in records if record["metrics"]["physics_equal"] is not None]
    if scored:
        metrics["physics_scored"] = len(scored)
        metrics["physics_equal"] = sum(record["metrics"]["physics_equal"] for record in scored)

    def breakdown(key):
        table = {}
        for value in sorted({record[key] for record in records}):
            subset = [record for record in records if record[key] == value]
            table[value] = {"n": len(subset), "target_tree_equal": sum(
                record["metrics"]["target_tree_equal"] for record in subset)}
            if any(record["metrics"]["physics_equal"] is not None for record in subset):
                table[value]["physics_equal"] = sum(bool(record["metrics"]["physics_equal"]) for record in subset)
        return table

    metrics["by_family"] = breakdown("family")
    metrics["by_edit_kind"] = breakdown("edit_kind")
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
    parser.add_argument("--batch-size", type=int, default=1,
                        help="per-device batch; effective batch is batch-size x grad-accum")
    parser.add_argument("--grad-accum", type=int, default=16)
    parser.add_argument("--eval-batch", type=int, default=1, help="prompts generated together")
    parser.add_argument("--no-gradient-checkpointing", action="store_true",
                        help="trade memory for speed on large GPUs")
    parser.add_argument("--address", choices=["nodes", "ids"], default="nodes",
                        help="how patches name elements: positional node ids or '#<svg id>'")
    args = parser.parse_args()
    global ADDRESS
    ADDRESS = args.address

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
        "batch_size": args.batch_size, "grad_accum": args.grad_accum,
        "gradient_checkpointing": not args.no_gradient_checkpointing, "address": args.address,
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
    import transformers
    # transformers renamed torch_dtype to dtype in 4.56; older builds silently load float32
    # when given the new name, so pick the keyword this build understands.
    major, minor = (int(part) for part in transformers.__version__.split(".")[:2])
    dtype_keyword = "dtype" if (major, minor) >= (4, 56) else "torch_dtype"
    base = AutoModelForCausalLM.from_pretrained(args.model, revision=revision, **{dtype_keyword: dtype},
                                               device_map={"": 0}, attn_implementation="sdpa")
    if hasattr(base, "enable_input_require_grads"):
        base.enable_input_require_grads()
    model = get_peft_model(base, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM"))
    model.print_trainable_parameters()

    def render_prompt(row):
        return tokenizer.apply_chat_template([{"role": "user", "content": prompt_text(row)}],
                                             tokenize=False, add_generation_prompt=True)

    def encode(items):
        encoded, omitted, lengths = [], 0, []
        for row in items:
            prefix = tokenizer(render_prompt(row), add_special_tokens=False)["input_ids"]
            answer_text = json.dumps(target_answer(row), separators=(",", ":"), ensure_ascii=False) + tokenizer.eos_token
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
        before = evaluate(model, tokenizer, evaluation, "base", args.out, args.max_new_tokens,
                          args.eval_batch)

    model.train(); model.config.use_cache = False
    training_args = _training_arguments(
        TrainingArguments,
        output_dir=str(args.out / "checkpoints"), num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size, gradient_accumulation_steps=args.grad_accum,
        per_device_eval_batch_size=1, learning_rate=2e-4,
        lr_scheduler_type="cosine", warmup_ratio=.05, weight_decay=.01,
        logging_steps=10, eval_strategy="epoch", save_strategy="steps", save_steps=250,
        save_total_limit=1, bf16=dtype == torch.bfloat16, fp16=dtype == torch.float16,
        report_to=[], seed=args.seed, data_seed=args.seed,
        gradient_checkpointing=not args.no_gradient_checkpointing,
        gradient_checkpointing_kwargs={"use_reentrant": False},
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
    # Merged weights decode several times faster than an unmerged LoRA wrapper; the saved
    # adapter above is unaffected.
    merged = model.merge_and_unload() if hasattr(model, "merge_and_unload") else model
    after = evaluate(merged, tokenizer, evaluation, "trained", args.out, args.max_new_tokens,
                     args.eval_batch)
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
