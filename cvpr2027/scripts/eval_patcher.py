"""Evaluate a saved LoRA patch adapter on a dataset split without training (e.g. the hard network tier)."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from train_crossdomain_svg_patcher import _balanced_eval, evaluate, load_rows  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--split", default="test")
    parser.add_argument("--adapter", type=Path, required=True, help="directory written by the trainer")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--eval-count", type=int, default=100000)
    parser.add_argument("--eval-batch", type=int, default=8)
    parser.add_argument("--max-new-tokens", type=int, default=1400)
    args = parser.parse_args()

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import transformers

    manifest = json.loads((args.adapter.parent / "run-manifest.json").read_text())
    import train_crossdomain_svg_patcher as trainer
    trainer.ADDRESS = manifest.get("address", "nodes")  # score in the addressing the adapter was trained on
    rows = _balanced_eval(load_rows(args.data / f"{args.split}.jsonl.gz"), args.eval_count)
    args.out.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(args.adapter)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    major, minor = (int(part) for part in transformers.__version__.split(".")[:2])
    keyword = "dtype" if (major, minor) >= (4, 56) else "torch_dtype"
    base = AutoModelForCausalLM.from_pretrained(manifest["model"], revision=manifest["model_revision"],
                                                **{keyword: dtype}, device_map={"": 0}, attn_implementation="sdpa")
    model = PeftModel.from_pretrained(base, args.adapter).merge_and_unload()
    metrics = evaluate(model, tokenizer, rows, "adapter", args.out, args.max_new_tokens, args.eval_batch)
    record = {"completed_utc": datetime.now(timezone.utc).isoformat(), "adapter": str(args.adapter),
              "model": manifest["model"], "model_revision": manifest["model_revision"],
              "data": str(args.data), "split": args.split, "metrics": metrics}
    (args.out / "summary.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2), flush=True)


if __name__ == "__main__":
    main()
