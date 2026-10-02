"""Resume full held-out evaluation of a saved cross-domain LoRA adapter.

Run on a CUDA machine with the training dependencies installed. Completed
25-example chunks are reused only when their IDs match the test split.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_crossdomain_svg_patcher as train  # noqa: E402


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def metrics(records: list[dict]) -> dict:
    result = {name: sum(bool(row["metrics"][name]) for row in records)
              for name in ("json_valid", "patch_valid", "exact_patch",
                           "target_tree_equal", "reference_integrity")}
    result["n"] = len(records)
    for key in ("family", "edit_kind"):
        result[f"by_{key}"] = {
            value: {"n": sum(row[key] == value for row in records),
                    "target_tree_equal": sum(row[key] == value and
                                             row["metrics"]["target_tree_equal"] for row in records)}
            for value in sorted({row[key] for row in records})}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True,
                        help="Test .jsonl.gz from engsvg-crossdomain-edit-v1")
    parser.add_argument("--run", type=Path, required=True,
                        help="Completed training run containing adapter and manifest")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reuse", type=Path,
                        help="Earlier predictions on the first balanced test examples")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--chunk-size", type=int, default=25)
    parser.add_argument("--max-new-tokens", type=int, default=1400)
    args = parser.parse_args()
    if args.batch_size < 1 or args.chunk_size < 1:
        parser.error("batch and chunk sizes must be positive")

    import torch
    import transformers
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required")
    run_manifest = json.loads((args.run / "run-manifest.json").read_text())
    if run_manifest["status"] != "complete":
        raise ValueError("training run is incomplete")
    train.ADDRESS = run_manifest["address"]
    rows = train._balanced_eval(train.load_rows(args.data), 1000)
    if len(rows) != 1000:
        raise ValueError(f"expected 1,000 test rows, got {len(rows)}")
    args.out.mkdir(parents=True, exist_ok=True)

    prior = read_jsonl(args.reuse) if args.reuse else []
    if [row["id"] for row in prior] != [row["id"] for row in rows[:len(prior)]]:
        raise ValueError("reused predictions do not match test ordering")
    if len(prior) > len(rows):
        raise ValueError("too many reused predictions")
    tokenizer = AutoTokenizer.from_pretrained(args.run / "adapter")
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    version = tuple(int(part) for part in transformers.__version__.split(".")[:2])
    dtype_key = "dtype" if version >= (4, 56) else "torch_dtype"
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    base = AutoModelForCausalLM.from_pretrained(
        run_manifest["model"], revision=run_manifest["model_revision"],
        **{dtype_key: dtype}, device_map={"": 0}, attn_implementation="sdpa")
    model = PeftModel.from_pretrained(base, args.run / "adapter").merge_and_unload()
    del base

    started = time.perf_counter()
    records = list(prior)
    for start in range(len(prior), len(rows), args.chunk_size):
        batch = rows[start:start + args.chunk_size]
        label = f"heldout-{start:04d}"
        destination = args.out / f"{label}-predictions.jsonl"
        if destination.exists():
            saved = read_jsonl(destination)
            if [row["id"] for row in saved] == [row["id"] for row in batch]:
                records.extend(saved)
                print(f"reused {label}; {len(records)}/1000", flush=True)
                continue
            destination.unlink()
        train.evaluate(model, tokenizer, batch, label, args.out,
                       args.max_new_tokens, args.batch_size)
        saved = read_jsonl(destination)
        if [row["id"] for row in saved] != [row["id"] for row in batch]:
            raise AssertionError(f"incomplete chunk {label}")
        records.extend(saved)
        print(f"completed {len(records)}/1000", flush=True)

    if len(records) != 1000 or len({row["id"] for row in records}) != 1000:
        raise AssertionError("evaluation coverage is incomplete")
    with (args.out / "trained-full-predictions.jsonl").open("w", encoding="utf-8") as handle:
        for row in records:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")
    result = metrics(records)
    (args.out / "trained-full-metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    manifest = {"status": "complete", "completed_utc": datetime.now(timezone.utc).isoformat(),
                "model": run_manifest["model"], "model_revision": run_manifest["model_revision"],
                "gpu": torch.cuda.get_device_name(0), "address": run_manifest["address"],
                "test_examples": 1000, "prior_examples_reused": len(prior),
                "batch_size": args.batch_size, "max_new_tokens": args.max_new_tokens,
                "seconds": round(time.perf_counter() - started, 2)}
    (args.out / "full-eval-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
