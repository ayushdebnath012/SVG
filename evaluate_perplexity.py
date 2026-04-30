#!/usr/bin/env python
"""Evaluate SVG-token perplexity for one or more text-to-SVG datasets.

Example:
    python evaluate_perplexity.py \
      --model Qwen/Qwen2-VL-7B-Instruct \
      --adapter /kaggle/working/qwen2vl_svg_lora/final_adapter \
      --dataset generated=/kaggle/input/diffusvg/training_pairs.json \
      --dataset kaggle=/kaggle/input/svg-dataset-for-generative-llm/data.jsonl \
      --output-json perplexity_report.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Iterable

import torch
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm


SYSTEM_PROMPT = (
    "You are an SVG code generator. Given a text description, output ONLY valid "
    "SVG code. Use simple geometric SVG elements, solid colors, and no explanation."
)


def load_records(path: Path) -> list[dict]:
    """Load JSON, JSONL, CSV, Parquet, or a directory of those files."""
    if path.is_dir():
        records = []
        for suffix in ("*.jsonl", "*.json", "*.csv", "*.parquet"):
            for child in sorted(path.rglob(suffix)):
                records.extend(load_records(child))
        return records

    if path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    if path.suffix.lower() == ".parquet":
        import pandas as pd

        return pd.read_parquet(path).to_dict("records")

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    obj = json.loads(text)
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        if isinstance(obj.get("results"), list):
            return obj["results"]
        if isinstance(obj.get("data"), list):
            return obj["data"]
        if isinstance(obj.get("train"), list):
            return obj["train"]
    raise ValueError(f"Unsupported dataset shape: {path}")


def pick_first(record: dict, keys: Iterable[str]) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize_record(record: dict) -> dict | None:
    prompt = pick_first(record, ("prompt", "text", "caption", "concept", "instruction", "description", "input", "question"))
    svg = pick_first(record, ("svg", "svg_code", "code", "target", "output", "response", "completion", "answer"))
    if (not prompt or not svg) and isinstance(record.get("messages"), list):
        for msg in record["messages"]:
            if not isinstance(msg, dict):
                continue
            role = str(msg.get("role", "")).lower()
            content = str(msg.get("content", "")).strip()
            if role == "user" and not prompt:
                prompt = content
            elif role == "assistant" and not svg:
                svg = content
    if not prompt or not svg:
        return None
    if "<svg" not in svg:
        svg = f'<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n{svg}\n</svg>'
    return {"prompt": prompt, "svg": svg}


def build_text(tokenizer, prompt: str, svg: str) -> tuple[str, str]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Generate SVG for: {prompt}"},
    ]
    answer = {"role": "assistant", "content": svg}

    if getattr(tokenizer, "chat_template", None):
        prefix = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        full = tokenizer.apply_chat_template(messages + [answer], tokenize=False, add_generation_prompt=False)
        return prefix, full

    prefix = f"{SYSTEM_PROMPT}\n\nGenerate SVG for: {prompt}\nSVG:\n"
    return prefix, prefix + svg


class PerplexityDataset(Dataset):
    def __init__(self, records: list[dict], tokenizer, max_seq_len: int):
        self.samples = []
        for record in records:
            item = normalize_record(record)
            if item is None:
                continue
            prefix, full = build_text(tokenizer, item["prompt"], item["svg"])
            full_enc = tokenizer(full, truncation=True, max_length=max_seq_len, padding=False)
            prefix_enc = tokenizer(prefix, truncation=True, max_length=max_seq_len, padding=False)
            input_ids = full_enc["input_ids"]
            labels = list(input_ids)
            prefix_len = min(len(prefix_enc["input_ids"]), len(labels))
            labels[:prefix_len] = [-100] * prefix_len
            target_tokens = sum(label != -100 for label in labels)
            if target_tokens:
                self.samples.append(
                    {
                        "input_ids": input_ids,
                        "attention_mask": full_enc["attention_mask"],
                        "labels": labels,
                        "target_tokens": target_tokens,
                    }
                )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> dict:
        return self.samples[index]


class Collator:
    def __init__(self, tokenizer):
        self.pad_id = tokenizer.pad_token_id or tokenizer.eos_token_id or 0

    def __call__(self, samples: list[dict]) -> dict:
        max_len = max(len(sample["input_ids"]) for sample in samples)

        def pad(values: list[int], pad_value: int) -> list[int]:
            return values + [pad_value] * (max_len - len(values))

        return {
            "input_ids": torch.tensor([pad(s["input_ids"], self.pad_id) for s in samples], dtype=torch.long),
            "attention_mask": torch.tensor([pad(s["attention_mask"], 0) for s in samples], dtype=torch.long),
            "labels": torch.tensor([pad(s["labels"], -100) for s in samples], dtype=torch.long),
            "target_tokens": torch.tensor([s["target_tokens"] for s in samples], dtype=torch.long),
        }


def parse_dataset_arg(value: str) -> tuple[str, Path]:
    if "=" not in value:
        path = Path(value)
        return path.stem, path
    name, raw_path = value.split("=", 1)
    return name.strip(), Path(raw_path.strip())


def load_model_and_tokenizer(args):
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True, padding_side="right")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quant_config = None
    if args.load_in_4bit and torch.cuda.is_available():
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

    model_kwargs = {
        "trust_remote_code": True,
        "device_map": "auto" if torch.cuda.is_available() else None,
        "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
    }
    if quant_config is not None:
        model_kwargs["quantization_config"] = quant_config

    if args.model_class == "qwen2vl" or (args.model_class == "auto" and "vl" in args.model.lower()):
        from transformers import Qwen2VLForConditionalGeneration

        model = Qwen2VLForConditionalGeneration.from_pretrained(args.model, **model_kwargs)
    else:
        model = AutoModelForCausalLM.from_pretrained(args.model, **model_kwargs)

    if args.adapter:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, args.adapter)

    model.eval()
    return model, tokenizer


@torch.inference_mode()
def evaluate_dataset(name: str, path: Path, model, tokenizer, args) -> dict:
    records = load_records(path)
    if args.max_samples:
        records = records[: args.max_samples]

    dataset = PerplexityDataset(records, tokenizer, args.max_seq_len)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, collate_fn=Collator(tokenizer))

    total_loss = 0.0
    total_tokens = 0
    device = next(model.parameters()).device

    for batch in tqdm(loader, desc=name):
        target_tokens = int(batch.pop("target_tokens").sum().item())
        batch = {key: value.to(device) for key, value in batch.items()}
        outputs = model(**batch)
        total_loss += float(outputs.loss.item()) * target_tokens
        total_tokens += target_tokens

    mean_nll = total_loss / max(total_tokens, 1)
    return {
        "dataset": name,
        "path": str(path),
        "records_loaded": len(records),
        "records_scored": len(dataset),
        "target_tokens": total_tokens,
        "nll": mean_nll,
        "perplexity": math.exp(mean_nll) if mean_nll < 50 else float("inf"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen2-VL-7B-Instruct")
    parser.add_argument("--adapter", default="", help="Optional LoRA adapter path")
    parser.add_argument("--dataset", action="append", required=True, help="name=path or path")
    parser.add_argument("--model-class", choices=("auto", "qwen2vl", "causal"), default="auto")
    parser.add_argument("--max-seq-len", type=int, default=2048)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--no-4bit", dest="load_in_4bit", action="store_false")
    parser.add_argument("--output-json", default="")
    parser.set_defaults(load_in_4bit=True)
    args = parser.parse_args()

    model, tokenizer = load_model_and_tokenizer(args)
    results = []
    for dataset_arg in args.dataset:
        name, path = parse_dataset_arg(dataset_arg)
        results.append(evaluate_dataset(name, path, model, tokenizer, args))

    print("\nPerplexity by dataset")
    print("dataset\trecords\ttokens\tnll\tppl")
    for row in results:
        print(
            f"{row['dataset']}\t{row['records_scored']}\t{row['target_tokens']}\t"
            f"{row['nll']:.4f}\t{row['perplexity']:.3f}"
        )

    if args.output_json:
        Path(args.output_json).write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
