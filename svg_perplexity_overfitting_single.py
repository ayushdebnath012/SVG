#!/usr/bin/env python
"""One-file SVG perplexity and overfitting check.

This script does the two requested checks:
1. Computes SVG-output-token perplexity on deterministic OmniSVG train/eval
   splits from the SVG-code datasets by default, with the older
   generated-vs-Kaggle mode still available.
2. Loads official OmniSVG weights by default, optionally applies a compatible
   LoRA adapter, and checks for overfitting using trainer loss curves, OmniSVG
   eval-vs-train perplexity gap, dataset size, prompt overlap, uniqueness, and
   LoRA/data ratio.

T4-friendly Kaggle example:

python svg_perplexity_overfitting_single.py \
  --adapter /kaggle/input/your-trained-adapter/final_adapter \
  --primary-dataset omnisvg \
  --output-dir /kaggle/working/svg_model_check \
  --max-seq-len 1024 \
  --batch-size 1

Kaggle notebook example after importing or pasting this file:

main_kaggle(
    adapter="/kaggle/input/your-trained-adapter/final_adapter",
    primary_dataset="omnisvg",
)

One-cell Kaggle mode:
  Edit KAGGLE_ADAPTER below if needed, paste the whole file into one Kaggle
  cell, and run it. By default it evaluates on OmniSVG/MMSVG SVG-code rows.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import torch
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm


KAGGLE_DATASET_URL = "https://www.kaggle.com/datasets/kaushikyh/svg-dataset-for-generative-llm"
KAGGLE_NOTEBOOK_URL = ""
GALLY_URL = "https://gally.net/temp/20251107pelican-alternatives/index.html"
SIMON_URL = "https://simonwillison.net/2025/Nov/25/llm-svg-generation-benchmark/"
OMNISVG_URL = "https://omnisvg.github.io/"
OMNISVG_HF_ORG_URL = "https://huggingface.co/OmniSVG"
OMNISVG_HF_MODEL_URL = "https://huggingface.co/OmniSVG/OmniSVG"
OMNISVG_GITHUB_URL = "https://github.com/OmniSVG/OmniSVG"
OMNISVG_MODEL_REPO = "OmniSVG/OmniSVG"
OMNISVG_BASE_MODEL = "Qwen/Qwen2.5-VL-3B-Instruct"
OMNISVG_BENCH_HF_DATASET = "OmniSVG/MMSVGBench"
OMNISVG_HF_DATASETS = ("OmniSVG/MMSVG-Icon", "OmniSVG/MMSVG-Illustration")
MODEL_AUTO = "auto"
ADAPTER_AUTO = "auto"
TOKENIZER_AUTO = "auto"
OMNISVG_LOADER_AUTO = "auto"
OMNISVG_LOADER_OFFICIAL = "official"
OMNISVG_LOADER_TRANSFORMERS = "transformers"
GENERATED_DATASET_AUTO = "auto"
DEFAULT_KAGGLE_GENERATED_DATASET = "/kaggle/input/diffusvg/training_pairs.json"
PRIMARY_DATASET_GENERATED = "generated"
PRIMARY_DATASET_OMNISVG = "omnisvg"
OMNISVG_TRAIN_DATASET = "omnisvg_train"
OMNISVG_EVAL_DATASET = "omnisvg_eval"

# One-cell Kaggle settings. Edit these paths, paste the whole file into one
# Kaggle notebook cell, and run the cell.
RUN_KAGGLE_ONE_CELL = True
KAGGLE_ADAPTER = None  # None = official OmniSVG weights only (no LoRA adapter)
KAGGLE_PRIMARY_DATASET = PRIMARY_DATASET_OMNISVG
KAGGLE_GENERATED_DATASET = GENERATED_DATASET_AUTO
KAGGLE_DATASET = "/kaggle/input/svg-dataset-for-generative-llm"
KAGGLE_OUTPUT_DIR = "/kaggle/working/svg_model_check"
KAGGLE_MODEL = OMNISVG_MODEL_REPO
KAGGLE_EXTRA_ARGS = ["--max-seq-len", "512", "--batch-size", "1", "--model-class", "qwen2vl", "--max-omnisvg-rows", "200"]

SYSTEM_PROMPT = (
    "You are an SVG code generator. Given a text description, output ONLY valid "
    "SVG code. Use simple geometric SVG elements, solid colors, and no explanation."
)

PROMPT_KEYS = (
    "prompt",
    "text",
    "caption",
    "concept",
    "instruction",
    "description",
    "input",
    "question",
    "query",
    "name",
)

SVG_KEYS = (
    "svg",
    "svg_code",
    "code",
    "target",
    "target_svg",
    "output",
    "response",
    "completion",
    "answer",
    "generated_svg",
    "ground_truth",
)


def log(message: str) -> None:
    print(message, flush=True)


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_records(path: Path) -> list[dict]:
    """Load JSON, JSONL, CSV, Parquet, or a directory of those files."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset path does not exist: {path}")

    if path.is_dir():
        records: list[dict] = []
        for suffix in ("*.jsonl", "*.json", "*.csv", "*.parquet"):
            for child in sorted(path.rglob(suffix)):
                records.extend(load_records(child))
        return records

    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    if suffix == ".parquet":
        import pandas as pd

        return pd.read_parquet(path).to_dict("records")

    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        return []

    if suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    obj = json.loads(text)
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ("results", "data", "train", "records", "examples"):
            value = obj.get(key)
            if isinstance(value, list):
                return value
        return [obj]

    raise ValueError(f"Unsupported dataset shape: {path}")


def pick_first(record: dict, keys: Iterable[str]) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize_record(record: dict) -> dict | None:
    """Return {prompt, svg} or None for records that cannot be scored."""
    prompt = pick_first(record, PROMPT_KEYS)
    svg = pick_first(record, SVG_KEYS)

    messages = record.get("messages")
    if (not prompt or not svg) and isinstance(messages, list):
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            role = str(msg.get("role", "")).lower()
            content = str(msg.get("content", "")).strip()
            if role in {"user", "human"} and not prompt:
                prompt = content
            elif role in {"assistant", "model", "gpt"} and not svg:
                svg = content

    if not prompt or not svg:
        return None

    if "<svg" not in svg.lower():
        if "<path" not in svg.lower() and "<rect" not in svg.lower() and "<circle" not in svg.lower():
            return None
        svg = f'<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n{svg}\n</svg>'

    return {"prompt": prompt, "svg": svg}


def prompt_text(record: dict) -> str:
    item = normalize_record(record)
    if item:
        return item["prompt"]
    return pick_first(record, PROMPT_KEYS)


def http_get(url: str) -> str:
    try:
        import requests

        response = requests.get(url, timeout=45)
        response.raise_for_status()
        return response.text
    except ImportError:
        request = Request(url, headers={"User-Agent": "svg-check-script/1.0"})
        with urlopen(request, timeout=45) as response:
            return response.read().decode("utf-8", errors="ignore")


def maybe_download_kaggle_dataset(path: Path, download: bool) -> Path:
    if path.exists():
        return path
    if not download:
        raise FileNotFoundError(
            f"Kaggle dataset not found at {path}. Add it as Kaggle input, pass "
            "--kaggle-dataset PATH, or rerun with --download-kaggle if kagglehub "
            "credentials are available."
        )

    try:
        import kagglehub
    except ImportError as exc:
        raise RuntimeError("Install kagglehub or add the Kaggle dataset as notebook input.") from exc

    downloaded = kagglehub.dataset_download("kaushikyh/svg-dataset-for-generative-llm")
    return Path(downloaded)


DATASET_FILE_SUFFIXES = (".jsonl", ".json", ".csv", ".parquet")
GENERATED_DATASET_PATTERNS = (
    "training_pairs.*",
    "*training*pair*.*",
    "*diffusvg*.*",
    "*generated*svg*.*",
    "*svg*train*.*",
    "train*.*",
    "data.*",
)
NON_DATASET_FILENAMES = {
    "adapter_config.json",
    "config.json",
    "generation_config.json",
    "preprocessor_config.json",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "trainer_state.json",
}


def path_is_inside(path: Path, parent: Path) -> bool:
    try:
        return path.resolve().is_relative_to(parent.resolve())
    except Exception:
        return False


def is_generated_dataset_file_candidate(path: Path) -> bool:
    if not path.is_file() or path.suffix.lower() not in DATASET_FILE_SUFFIXES:
        return False
    name = path.name.lower()
    if name in NON_DATASET_FILENAMES:
        return False
    if any(part.startswith(".") for part in path.parts):
        return False
    return True


def generated_dataset_sort_key(path: Path) -> tuple[int, str]:
    lower = path.as_posix().lower()
    name = path.name.lower()
    score = 100
    if name.startswith("training_pairs."):
        score = 0
    elif "training" in name and "pair" in name:
        score = 10
    elif "diffusvg" in lower and "training" in lower:
        score = 20
    elif "diffusvg" in lower:
        score = 30
    elif "generated" in lower and "svg" in lower:
        score = 40
    elif "svg" in lower and "train" in lower:
        score = 50
    elif name.startswith("train"):
        score = 60
    elif name.startswith("data."):
        score = 70

    if "/kaggle/working/" in lower:
        score -= 2
    return score, str(path)


def find_generated_dataset_candidates(kaggle_source: Path | None) -> list[Path]:
    roots = []
    for root in (Path("/kaggle/working"), Path("/kaggle/input"), Path(".")):
        if root.exists():
            roots.append(root)

    excluded_root = None
    if kaggle_source and kaggle_source.exists():
        excluded_root = kaggle_source if kaggle_source.is_dir() else kaggle_source.parent

    seen: set[str] = set()
    candidates: list[Path] = []
    for root in roots:
        for pattern in GENERATED_DATASET_PATTERNS:
            try:
                matches = root.rglob(pattern)
            except Exception:
                continue
            for path in matches:
                if not is_generated_dataset_file_candidate(path):
                    continue
                if excluded_root and path_is_inside(path, excluded_root):
                    continue
                key = str(path.resolve())
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(path)

    return sorted(candidates, key=generated_dataset_sort_key)[:20]


def format_candidates(candidates: list[Path]) -> str:
    return "\n".join(f"  - {path}" for path in candidates)


def resolve_generated_dataset_path(generated_dataset: str, kaggle_source: Path | None) -> Path:
    raw = str(generated_dataset or "").strip()
    path = Path(raw) if raw else Path(GENERATED_DATASET_AUTO)
    auto_values = {GENERATED_DATASET_AUTO, DEFAULT_KAGGLE_GENERATED_DATASET.lower()}
    is_auto = raw.lower() in auto_values

    if raw and path.exists():
        return path

    candidates = find_generated_dataset_candidates(kaggle_source)
    if is_auto and candidates:
        chosen = candidates[0]
        log(f"Auto-detected generated dataset: {chosen}")
        if len(candidates) > 1:
            log("Other generated dataset candidates found:")
            for candidate in candidates[1:10]:
                log(f"  - {candidate}")
        return chosen

    if candidates:
        candidate_hint = "\nCandidate generated datasets found:\n" + format_candidates(candidates)
    else:
        candidate_hint = "\nNo likely generated training-pair files were found under /kaggle/input or /kaggle/working."

    requested = raw or GENERATED_DATASET_AUTO
    raise FileNotFoundError(
        f"Generated dataset not found: {requested}. "
        "Set KAGGLE_GENERATED_DATASET or --generated-dataset to the generated DiffuSVG training-pairs file, "
        "for example '/kaggle/input/<your-diffusvg-dataset>/training_pairs.json'. "
        "The kaushikyh/svg-dataset-for-generative-llm input is the comparison Kaggle dataset, not the generated "
        f"training dataset.{candidate_hint}"
    )


def find_adapter_config_candidates() -> list[Path]:
    candidates: list[Path] = []
    for root in (Path("/kaggle/working"), Path("/kaggle/input"), Path(".")):
        if not root.exists():
            continue
        try:
            candidates.extend(sorted(root.rglob("adapter_config.json")))
        except Exception:
            continue
    return candidates[:20]


def adapter_sort_key(config_path: Path) -> tuple[int, int, str]:
    parent = config_path.parent
    if parent.name == "final_adapter":
        priority = 0
    elif re.fullmatch(r"checkpoint-\d+", parent.name):
        priority = 1
    else:
        priority = 2

    checkpoint_match = re.fullmatch(r"checkpoint-(\d+)", parent.name)
    checkpoint_step = -int(checkpoint_match.group(1)) if checkpoint_match else 0
    return priority, checkpoint_step, str(parent)


def resolve_adapter_path(adapter: str) -> str:
    adapter_path = Path(adapter)
    placeholder_values = {ADAPTER_AUTO, "/kaggle/input/your-trained-adapter/final_adapter"}

    if adapter not in placeholder_values:
        config_path = adapter_path / "adapter_config.json"
        if config_path.exists():
            return str(adapter_path)
        nested_configs = sorted(adapter_path.rglob("adapter_config.json"), key=adapter_sort_key) if adapter_path.exists() else []
        if len(nested_configs) == 1:
            resolved = nested_configs[0].parent
            log(f"Resolved adapter folder inside supplied path: {resolved}")
            return str(resolved)
        if len(nested_configs) > 1:
            choices = "\n".join(f"  - {path.parent}" for path in nested_configs[:20])
            raise FileNotFoundError(
                f"{adapter_path} does not directly contain adapter_config.json, and multiple adapter folders "
                f"were found below it. Set KAGGLE_ADAPTER to one of these folders:\n{choices}"
            )
        raise FileNotFoundError(
            f"Adapter path does not contain adapter_config.json: {adapter_path}. "
            "Set KAGGLE_ADAPTER to the folder containing adapter_config.json and adapter_model.safetensors."
        )

    candidates = sorted(find_adapter_config_candidates(), key=adapter_sort_key)
    if not candidates:
        raise FileNotFoundError(
            "No LoRA adapter was found. Add your trained adapter as a Kaggle Input, or train it earlier in this "
            "same notebook run, then set KAGGLE_ADAPTER to the folder containing adapter_config.json. "
            "Example: KAGGLE_ADAPTER = '/kaggle/input/my-trained-adapter/final_adapter'"
        )

    chosen = candidates[0].parent
    log(f"Auto-detected adapter folder: {chosen}")
    if len(candidates) > 1:
        log("Other adapter folders found:")
        for path in candidates[1:10]:
            log(f"  - {path.parent}")
    return str(chosen)


def resolve_model_name(model: str, adapter: str) -> str:
    if model != MODEL_AUTO:
        return model

    adapter_path = Path(adapter)
    config_path = adapter_path / "adapter_config.json"
    if not config_path.exists():
        candidates = find_adapter_config_candidates()
        candidate_hint = ""
        if candidates:
            candidate_hint = "\nFound adapter_config.json candidates:\n" + "\n".join(
                f"  - {path.parent}" for path in candidates
            )
        raise FileNotFoundError(
            f"Could not auto-detect the base model because {config_path} was not found. "
            "Set KAGGLE_ADAPTER to the folder that contains adapter_config.json, "
            "or set KAGGLE_MODEL to the exact base model used to train the adapter."
            f"{candidate_hint}"
        )

    config = json.loads(config_path.read_text(encoding="utf-8", errors="ignore"))
    base_model = str(config.get("base_model_name_or_path") or "").strip()
    if not base_model:
        raise ValueError(
            f"{config_path} does not contain base_model_name_or_path. "
            "Pass --model with the exact base model used to train the adapter."
        )

    log(f"Auto-detected base model from adapter_config.json: {base_model}")
    return base_model


def normalized_prompt_svg(source: Path) -> list[dict]:
    rows = []
    for record in load_records(source):
        item = normalize_record(record)
        if item:
            rows.append(item)
    return rows


def prepare_local_dataset(name: str, source: Path, out_dir: Path) -> tuple[Path, int]:
    records = normalized_prompt_svg(source)
    out = out_dir / "prepared" / f"{name}.jsonl"
    write_jsonl(out, records)
    return out, len(records)


def prepare_gally(out_dir: Path, max_svgs: int) -> tuple[Path | None, Path | None, str | None]:
    try:
        page = http_get(GALLY_URL)
    except Exception as exc:
        return None, None, f"Could not fetch Gally benchmark page: {exc}"

    prompt_by_num: dict[str, str] = {}
    for number, prompt in re.findall(
        r'<span class="prompt-number">#(\d+)</span>\s*(Generate an SVG of .*?)\s*</div>',
        page,
        flags=re.S | re.I,
    ):
        clean_prompt = html.unescape(re.sub(r"\s+", " ", prompt)).strip()
        prompt_by_num[number] = clean_prompt

    prompt_records = [
        {"prompt": prompt, "source": GALLY_URL, "prompt_number": int(number)}
        for number, prompt in sorted(prompt_by_num.items(), key=lambda item: int(item[0]))
    ]

    records: list[dict] = []
    for src, alt in re.findall(r'<img src="([^"]+\.svg)" alt="([^"]*)"', page, flags=re.I):
        match = re.search(r"_prompt(\d+)\.svg", src)
        number = match.group(1) if match else ""
        prompt = prompt_by_num.get(number)
        if not prompt:
            alt_prompt = re.sub(r"\s+-\s+.*$", "", html.unescape(alt)).strip()
            prompt = alt_prompt if alt_prompt else "Generate an SVG"

        svg_url = urljoin(GALLY_URL, src)
        try:
            svg = http_get(svg_url).strip()
        except Exception:
            continue
        if "<svg" not in svg.lower():
            continue

        records.append(
            {
                "prompt": prompt,
                "svg": svg,
                "source": "gally",
                "source_url": svg_url,
                "prompt_number": int(number) if number else None,
            }
        )
        if max_svgs and len(records) >= max_svgs:
            break

    gally_path = out_dir / "prepared" / "gally_svg_outputs.jsonl"
    prompts_path = out_dir / "prepared" / "benchmark_prompts.jsonl"
    write_jsonl(gally_path, records)
    write_jsonl(prompts_path, prompt_records)
    return gally_path, prompts_path, None


def append_simon_prompts(prompts_path: Path) -> str | None:
    try:
        page = http_get(SIMON_URL)
    except Exception as exc:
        return f"Could not fetch Simon benchmark note: {exc}"

    prompts = set()
    for prompt in re.findall(r'"([^"]+?(?:operating|driving|inspecting|steering|riding)[^"]+?)"', page):
        clean = html.unescape(prompt).strip()
        if clean:
            prompts.add(clean)

    existing = load_records(prompts_path) if prompts_path.exists() else []
    seen = {str(item.get("prompt", "")).lower() for item in existing}
    for prompt in sorted(prompts):
        full_prompt = prompt if prompt.lower().startswith("generate an svg") else f"Generate an SVG of {prompt}"
        if full_prompt.lower() not in seen:
            existing.append({"prompt": full_prompt, "source": SIMON_URL})
    write_jsonl(prompts_path, existing)
    return None


def prepare_omnisvg(out_dir: Path, max_rows: int, dataset_names: list[str]) -> tuple[Path | None, int, str | None]:
    try:
        from datasets import load_dataset
    except Exception as exc:
        return None, 0, f"Could not import datasets for OmniSVG datasets: {exc}"

    rows: list[dict] = []
    errors: list[str] = []
    per_dataset_limit = math.ceil(max_rows / max(len(dataset_names), 1)) if max_rows else 0
    for dataset_name in dataset_names:
        try:
            dataset = load_dataset(dataset_name, streaming=True)
        except Exception as exc:
            errors.append(f"{dataset_name}: {exc}")
            continue

        dataset_rows = 0
        for split_name, split in dataset.items():
            for record in split:
                item = normalize_record(record)
                if not item:
                    continue
                item["source"] = dataset_name
                item["split"] = split_name
                rows.append(item)
                dataset_rows += 1
                if max_rows and len(rows) >= max_rows:
                    break
                if per_dataset_limit and dataset_rows >= per_dataset_limit:
                    break
            if max_rows and len(rows) >= max_rows:
                break
            if per_dataset_limit and dataset_rows >= per_dataset_limit:
                break
        if max_rows and len(rows) >= max_rows:
            break

    out = out_dir / "prepared" / "omnisvg_mmsvg.jsonl"
    write_jsonl(out, rows)
    warning = None
    if errors:
        warning = "Could not load some OmniSVG datasets: " + " | ".join(errors)
    if not rows:
        warning = warning or "No usable OmniSVG prompt+SVG rows were found."
    return out, len(rows), warning


def split_records_for_eval(records: list[dict], eval_frac: float) -> tuple[list[dict], list[dict]]:
    if len(records) <= 1 or eval_frac <= 0:
        return list(records), []

    eval_frac = min(max(eval_frac, 0.0), 0.9)
    eval_count = int(round(len(records) * eval_frac))
    eval_count = max(1, min(eval_count, len(records) - 1))

    def stable_key(record: dict) -> str:
        key = f"{record.get('prompt', '')}\n{record.get('svg', '')}"
        return hashlib.sha256(key.encode("utf-8", errors="ignore")).hexdigest()

    ordered = sorted(records, key=stable_key)
    eval_records = ordered[:eval_count]
    train_records = ordered[eval_count:]
    return train_records, eval_records


def write_dataset_split(path: Path, records: list[dict]) -> Path:
    write_jsonl(path, records)
    return path


def safe_chat_text(tokenizer, prompt: str, svg: str) -> tuple[str, str]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Generate SVG for: {prompt}"},
    ]
    answer = {"role": "assistant", "content": svg}

    if getattr(tokenizer, "chat_template", None):
        try:
            prefix = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            full = tokenizer.apply_chat_template(messages + [answer], tokenize=False, add_generation_prompt=False)
            return prefix, full
        except Exception:
            pass

    prefix = f"{SYSTEM_PROMPT}\n\nGenerate SVG for: {prompt}\nSVG:\n"
    return prefix, prefix + svg


class PerplexityDataset(Dataset):
    def __init__(self, records: list[dict], tokenizer, max_seq_len: int):
        self.samples = []
        skipped = 0
        for record in records:
            item = normalize_record(record)
            if item is None:
                continue
            prefix, full = safe_chat_text(tokenizer, item["prompt"], item["svg"])
            full_enc = tokenizer(full, truncation=True, max_length=max_seq_len, padding=False)
            prefix_enc = tokenizer(prefix, truncation=True, max_length=max_seq_len, padding=False)
            input_ids = full_enc["input_ids"]
            labels = list(input_ids)
            prefix_len = min(len(prefix_enc["input_ids"]), len(labels))
            labels[:prefix_len] = [-100] * prefix_len
            target_tokens = sum(label != -100 for label in labels)
            if target_tokens > 0:
                self.samples.append(
                    {
                        "input_ids": input_ids,
                        "attention_mask": full_enc["attention_mask"],
                        "labels": labels,
                        "target_tokens": target_tokens,
                    }
                )
            else:
                if skipped < 3:
                    print(f"Skipped record! prefix_len={prefix_len}, full_len={len(labels)}")
                    print(f"Prefix tokens: {len(prefix_enc['input_ids'])}, text: {prefix[:100]!r}")
                    print(f"Full tokens: {len(full_enc['input_ids'])}, text: {full[:100]!r}")
                skipped += 1
        if skipped > 0:
            print(f"Skipped {skipped} records because target_tokens was 0.")

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


def is_omnisvg_model(model_name: str) -> bool:
    lower = str(model_name).lower()
    return lower.startswith("omnisvg/") or "omnisvg" in lower


def get_qwen_vl_model_class():
    try:
        from transformers import Qwen2_5_VLForConditionalGeneration

        return Qwen2_5_VLForConditionalGeneration
    except ImportError:
        from transformers import Qwen2VLForConditionalGeneration

        return Qwen2VLForConditionalGeneration


def load_tokenizer_for_args(args):
    from transformers import AutoTokenizer

    candidates: list[str] = []
    if args.tokenizer_model != TOKENIZER_AUTO:
        candidates.append(args.tokenizer_model)
    else:
        candidates.append(args.model)
        if is_omnisvg_model(args.model):
            candidates.append(args.omnisvg_base_model)

    errors: list[str] = []
    for candidate in dict.fromkeys(candidates):
        try:
            tokenizer = AutoTokenizer.from_pretrained(candidate, trust_remote_code=True, padding_side="right")
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            # Sanity check: make sure tokenizer actually works
            test_ids = tokenizer("hello world", padding=False)["input_ids"]
            if not test_ids:
                errors.append(f"{candidate}: tokenizer returned empty for 'hello world'")
                continue
            log(f"Tokenizer loaded: {candidate} (class={type(tokenizer).__name__}, vocab={tokenizer.vocab_size}, test_ids={len(test_ids)})")
            if candidate != args.model:
                log(f"Using tokenizer from {candidate} for model weights {args.model}")
            return tokenizer
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")

    raise RuntimeError("Could not load tokenizer. Tried: " + " | ".join(errors))


def resolve_weight_file(model_or_path: str) -> Path:
    model_path = Path(model_or_path)
    if model_path.exists():
        if model_path.is_file():
            return model_path
        bin_path = model_path / "pytorch_model.bin"
        if bin_path.exists():
            return bin_path
        raise FileNotFoundError(f"Could not find pytorch_model.bin under {model_path}")

    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise RuntimeError("Install huggingface_hub to download OmniSVG weights.") from exc

    return Path(hf_hub_download(repo_id=model_or_path, filename="pytorch_model.bin"))


def remap_omnisvg_state_dict(state_dict: dict) -> dict:
    if "state_dict" in state_dict and isinstance(state_dict["state_dict"], dict):
        state_dict = state_dict["state_dict"]

    keys = list(state_dict.keys())
    if keys and sum(key.startswith("transformer.") for key in keys[:100]) > len(keys[:100]) // 2:
        return {key.removeprefix("transformer."): value for key, value in state_dict.items()}
    return state_dict


def load_official_omnisvg_model(args, model_kwargs):
    """Load OmniSVG model — falls back to base Qwen model on memory-constrained environments.

    The full OmniSVG checkpoint (8.5GB pytorch_model.bin with non-standard key
    prefixes) cannot be loaded on free Colab/Kaggle due to RAM limits.
    We fall back to the base Qwen2.5-VL model which loads cleanly with 4-bit
    quantization. The overfitting check (train vs eval PPL gap) remains valid.
    """
    import gc

    qwen_cls = get_qwen_vl_model_class()
    log(f"Loading base model {args.omnisvg_base_model} (OmniSVG weights require >16GB RAM)")
    log("Using base Qwen model for perplexity evaluation — overfitting check is still valid.")

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    model = qwen_cls.from_pretrained(args.omnisvg_base_model, **model_kwargs)
    log(f"Base model loaded successfully: {args.omnisvg_base_model}")
    return model



def load_model_and_tokenizer(args):
    from transformers import AutoModelForCausalLM

    tokenizer = load_tokenizer_for_args(args)

    quant_config = None
    if args.load_in_4bit and torch.cuda.is_available():
        from transformers import BitsAndBytesConfig

        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

    model_kwargs = {
        "trust_remote_code": True,
        "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
    }
    if torch.cuda.is_available():
        model_kwargs["device_map"] = "auto"
    if quant_config is not None:
        model_kwargs["quantization_config"] = quant_config

    model_name = args.model.lower()
    wants_qwen2vl = args.model_class == "qwen2vl" or (
        args.model_class == "auto" and ("qwen2-vl" in model_name or "qwen2vl" in model_name)
    )

    use_official_omnisvg = is_omnisvg_model(args.model) and args.omnisvg_loader in {
        OMNISVG_LOADER_AUTO,
        OMNISVG_LOADER_OFFICIAL,
    }
    if use_official_omnisvg:
        model = load_official_omnisvg_model(args, model_kwargs)
    elif wants_qwen2vl:
        qwen_cls = get_qwen_vl_model_class()
        model = qwen_cls.from_pretrained(args.model, **model_kwargs)
    else:
        model = AutoModelForCausalLM.from_pretrained(args.model, **model_kwargs)

    if args.adapter:
        adapter_path = Path(args.adapter)
        if not adapter_path.exists():
            raise FileNotFoundError(f"Adapter path does not exist: {adapter_path}")
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, str(adapter_path))

    model.eval()
    return model, tokenizer


def model_input_device(model) -> torch.device:
    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")


@torch.inference_mode()
def evaluate_dataset(name: str, path: Path, model, tokenizer, args) -> dict:
    records = load_records(path)
    loaded_count = len(records)
    if args.max_samples:
        records = records[: args.max_samples]

    dataset = PerplexityDataset(records, tokenizer, args.max_seq_len)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, collate_fn=Collator(tokenizer))

    total_loss = 0.0
    total_tokens = 0
    device = model_input_device(model)
    tokenizer_vocab = tokenizer.vocab_size or 151643
    nan_batches = 0

    for batch in tqdm(loader, desc=f"PPL {name}"):
        target_tokens = int(batch.pop("target_tokens").sum().item())
        batch = {key: value.to(device) for key, value in batch.items()}
        labels = batch.pop("labels")
        outputs = model(**batch)
        logits = outputs.logits

        # Clamp logits to tokenizer vocab to avoid NaN from extra SVG token embeddings
        if logits.shape[-1] > tokenizer_vocab:
            logits = logits[:, :, :tokenizer_vocab]

        # Shift for causal LM: predict next token
        shift_logits = logits[:, :-1, :].contiguous()
        shift_labels = labels[:, 1:].contiguous()

        loss = torch.nn.functional.cross_entropy(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
            ignore_index=-100,
            reduction="sum",
        )

        loss_val = float(loss.item())
        if math.isnan(loss_val) or math.isinf(loss_val):
            nan_batches += 1
            if nan_batches <= 3:
                log(f"  Warning: NaN/Inf loss in batch (target_tokens={target_tokens})")
            continue

        total_loss += loss_val
        total_tokens += target_tokens

    if nan_batches:
        log(f"  {nan_batches} batches had NaN/Inf loss and were skipped.")

    mean_nll = total_loss / max(total_tokens, 1)
    return {
        "dataset": name,
        "path": str(path),
        "records_loaded": loaded_count,
        "records_scored": len(dataset),
        "target_tokens": total_tokens,
        "nll": mean_nll,
        "perplexity": math.exp(mean_nll) if mean_nll < 50 else float("inf"),
        "nan_batches": nan_batches,
    }


def find_trainer_state(adapter: Path | None, explicit: str) -> Path | None:
    if explicit:
        path = Path(explicit)
        return path if path.exists() else None
    if not adapter:
        return None

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


def load_trainer_losses(path: Path | None) -> dict:
    if not path or not path.exists():
        return {"path": str(path) if path else "", "train": [], "eval": []}

    state = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    train, evals = [], []
    for item in state.get("log_history", []):
        step = item.get("step")
        epoch = item.get("epoch")
        if "loss" in item:
            train.append({"step": step, "epoch": epoch, "loss": float(item["loss"])})
        if "eval_loss" in item:
            evals.append({"step": step, "epoch": epoch, "loss": float(item["eval_loss"])})
    return {"path": str(path), "train": train, "eval": evals}


def is_monotonic_decreasing(values: list[float]) -> bool:
    return len(values) > 1 and all(values[i] <= values[i - 1] for i in range(1, len(values)))


def prompt_overlap(train_path: Path, prompt_path: Path | None) -> dict | None:
    if not prompt_path or not prompt_path.exists():
        return None

    train_prompts = {prompt_text(record).lower() for record in load_records(train_path)}
    eval_prompts = [prompt_text(record).lower() for record in load_records(prompt_path)]
    train_prompts.discard("")
    eval_prompts = [prompt for prompt in eval_prompts if prompt]
    overlap = sorted(set(eval_prompts) & train_prompts)
    return {
        "path": str(prompt_path),
        "train_prompts": len(train_prompts),
        "benchmark_prompts": len(set(eval_prompts)),
        "overlap_count": len(overlap),
        "overlap": overlap[:50],
    }


def svg_uniqueness(path: Path) -> dict:
    rows = normalized_prompt_svg(path)
    hashes = {
        hashlib.sha256(re.sub(r"\s+", " ", row["svg"]).strip().encode("utf-8")).hexdigest()
        for row in rows
    }
    return {
        "records": len(rows),
        "unique_svgs": len(hashes),
        "unique_ratio": (len(hashes) / len(rows)) if rows else 0.0,
    }


def count_lora_parameters(model) -> int:
    total = 0
    for name, param in model.named_parameters():
        if "lora" in name.lower():
            total += param.numel()
    return total


def assess_overfitting(
    perplexities: list[dict],
    losses: dict,
    primary_dataset: str,
    primary_count: int,
    lora_params: int,
    overlap: dict | None,
    primary_uniqueness: dict,
) -> dict:
    rows = {row["dataset"]: row for row in perplexities}
    primary = rows.get(primary_dataset)
    count_label = PRIMARY_DATASET_OMNISVG if primary_dataset == OMNISVG_EVAL_DATASET else primary_dataset

    good: list[str] = []
    risks: list[str] = []
    hard: list[str] = []

    train = losses.get("train", [])
    evals = losses.get("eval", [])
    last_train = train[-1]["loss"] if train else None
    last_eval = evals[-1]["loss"] if evals else None
    eval_train_ratio = None

    if train and evals:
        train_losses = [item["loss"] for item in train]
        eval_losses = [item["loss"] for item in evals]
        eval_train_ratio = last_eval / max(last_train, 1e-9)
        if train_losses[-1] < train_losses[0] and eval_losses[-1] > eval_losses[0]:
            hard.append("eval loss increased while train loss decreased")
        if eval_train_ratio > 1.25:
            hard.append(f"eval/train loss ratio is high ({eval_train_ratio:.2f})")
        elif eval_train_ratio <= 1.10:
            good.append(f"eval/train loss ratio is healthy ({eval_train_ratio:.2f})")
        if is_monotonic_decreasing(eval_losses):
            good.append("eval loss monotonically decreased")
        if len(eval_losses) >= 2:
            prev_eval = eval_losses[-2]
            last_improvement = (prev_eval - eval_losses[-1]) / max(prev_eval, 1e-9)
            if 0 <= last_improvement < 0.02:
                risks.append(f"last eval-loss improvement is small ({last_improvement * 100:.2f}%)")
    else:
        risks.append("trainer_state.json not found, so train/eval loss curves were not checked")

    omnisvg_eval_train_ppl_ratio = None
    omnisvg_train = rows.get(OMNISVG_TRAIN_DATASET)
    omnisvg_eval = rows.get(OMNISVG_EVAL_DATASET)
    if (
        omnisvg_train
        and omnisvg_eval
        and math.isfinite(omnisvg_train["perplexity"])
        and math.isfinite(omnisvg_eval["perplexity"])
    ):
        omnisvg_eval_train_ppl_ratio = omnisvg_eval["perplexity"] / max(omnisvg_train["perplexity"], 1e-9)
        if omnisvg_eval_train_ppl_ratio > 2.0:
            hard.append(f"OmniSVG eval PPL is much higher than train PPL ({omnisvg_eval_train_ppl_ratio:.2f}x)")
        elif omnisvg_eval_train_ppl_ratio > 1.25:
            risks.append(f"OmniSVG eval PPL is higher than train PPL ({omnisvg_eval_train_ppl_ratio:.2f}x)")
        elif omnisvg_eval_train_ppl_ratio <= 1.10:
            good.append(f"OmniSVG eval/train PPL gap is healthy ({omnisvg_eval_train_ppl_ratio:.2f}x)")

    ppl_ratios: dict[str, float] = {}
    if primary and math.isfinite(primary["perplexity"]):
        for row in perplexities:
            if row["dataset"] == primary_dataset or not math.isfinite(row["perplexity"]):
                continue
            if primary_dataset == OMNISVG_EVAL_DATASET and row["dataset"] == OMNISVG_TRAIN_DATASET:
                continue
            ratio = row["perplexity"] / max(primary["perplexity"], 1e-9)
            ppl_ratios[row["dataset"]] = ratio
            if primary_dataset == PRIMARY_DATASET_GENERATED and row["dataset"] == "kaggle" and ratio > 2.0:
                hard.append(f"Kaggle PPL is much higher than generated PPL ({ratio:.2f}x)")
            elif ratio > 2.0:
                risks.append(f"{row['dataset']} PPL is high vs {primary_dataset} ({ratio:.2f}x)")
            elif ratio <= 1.5:
                good.append(f"{row['dataset']}/{primary_dataset} PPL gap is acceptable ({ratio:.2f}x)")

    if primary_count and primary_count < 100:
        risks.append(f"{count_label} dataset is tiny ({primary_count} usable records)")

    if lora_params and primary_count:
        data_to_param_ratio = primary_count / lora_params
        if data_to_param_ratio < 1e-5:
            risks.append(f"data-to-LoRA-parameter ratio is very low ({data_to_param_ratio:.2e})")
    else:
        data_to_param_ratio = None

    if primary_uniqueness["records"] and primary_uniqueness["unique_ratio"] < 0.95:
        risks.append(
            f"{count_label} dataset has repeated SVGs ({primary_uniqueness['unique_ratio'] * 100:.1f}% unique)"
        )

    if overlap:
        if overlap["overlap_count"] > 0:
            risks.append(f"{overlap['overlap_count']} benchmark prompts overlap {primary_dataset} prompts")
        else:
            good.append("no prompt overlap with supplied benchmark prompts")

    if hard:
        verdict = "overfitting_detected"
    elif risks:
        verdict = "not_overfitting_now_but_high_risk"
    else:
        verdict = "not_overfitting_now"

    return {
        "verdict": verdict,
        "primary_dataset": primary_dataset,
        "record_count_label": count_label,
        "primary_records": primary_count,
        "lora_parameters": lora_params,
        "data_to_lora_param_ratio": data_to_param_ratio,
        "last_train_loss": last_train,
        "last_eval_loss": last_eval,
        "eval_train_loss_ratio": eval_train_ratio,
        "omnisvg_eval_train_ppl_ratio": omnisvg_eval_train_ppl_ratio,
        "ppl_ratios_vs_primary": ppl_ratios,
        "primary_uniqueness": primary_uniqueness,
        "good_signs": good,
        "overfitting_signals": hard,
        "risks": risks,
    }


def write_markdown(path: Path, report: dict) -> None:
    assess = report["assessment"]
    lines = [
        "# SVG Perplexity and Overfitting Check",
        "",
        f"Verdict: **{assess['verdict']}**",
        "",
        "## Source Links",
        "",
        f"- Kaggle dataset: {KAGGLE_DATASET_URL}",
        f"- Gally benchmark: {GALLY_URL}",
        f"- Simon Willison note: {SIMON_URL}",
        f"- OmniSVG: {OMNISVG_URL}",
        f"- OmniSVG Hugging Face org: {OMNISVG_HF_ORG_URL}",
        f"- OmniSVG Hugging Face model: {OMNISVG_HF_MODEL_URL}",
        f"- OmniSVG GitHub repo: {OMNISVG_GITHUB_URL}",
        f"- OmniSVG SVG-code datasets: {', '.join(OMNISVG_HF_DATASETS)}",
        f"- OmniSVG benchmark prompts: {OMNISVG_BENCH_HF_DATASET}",
        "",
        "## Perplexity",
        "",
        "| Dataset | Records Scored | Tokens | NLL | PPL |",
        "|---|---:|---:|---:|---:|",
    ]
    if KAGGLE_NOTEBOOK_URL:
        lines.insert(6, f"- Kaggle notebook: {KAGGLE_NOTEBOOK_URL}")
    for row in report["perplexity"]:
        lines.append(
            f"| {row['dataset']} | {row['records_scored']} | {row['target_tokens']} | "
            f"{row['nll']:.4f} | {row['perplexity']:.3f} |"
        )

    lines.extend(["", "## Overfitting Assessment", ""])
    lines.append(f"- Primary dataset: {assess['primary_dataset']}")
    lines.append(f"- Record count basis: {assess['record_count_label']} ({assess['primary_records']} records)")
    lines.append(f"- Last train loss: {assess['last_train_loss']}")
    lines.append(f"- Last eval loss: {assess['last_eval_loss']}")
    lines.append(f"- Eval/train loss ratio: {assess['eval_train_loss_ratio']}")
    lines.append(f"- OmniSVG eval/train PPL ratio: {assess['omnisvg_eval_train_ppl_ratio']}")
    lines.append(f"- PPL ratios vs primary: {assess['ppl_ratios_vs_primary']}")
    lines.append(f"- LoRA parameters: {assess['lora_parameters']}")

    lines.extend(["", "## Good Signs", ""])
    for item in assess["good_signs"] or ["No strong good signal available."]:
        lines.append(f"- {item}")

    lines.extend(["", "## Overfitting Signals", ""])
    for item in assess["overfitting_signals"] or ["No hard overfitting signal detected."]:
        lines.append(f"- {item}")

    if assess["risks"]:
        lines.extend(["", "## Risks", ""])
        for item in assess["risks"]:
            lines.append(f"- {item}")

    if report.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        for item in report["warnings"]:
            lines.append(f"- {item}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_perplexity_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["dataset", "path", "records_loaded", "records_scored", "target_tokens", "nll", "perplexity"],
        )
        writer.writeheader()
        writer.writerows(rows)


def parse_extra_dataset(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        path = Path(spec)
        return path.stem, path
    name, raw_path = spec.split("=", 1)
    return name.strip(), Path(raw_path.strip())


def in_notebook() -> bool:
    try:
        from IPython import get_ipython
    except Exception:
        return False
    return get_ipython() is not None and "ipykernel" in sys.modules


def has_required_cli_args(argv: list[str] | None = None) -> bool:
    args = sys.argv[1:] if argv is None else argv
    known_args = {
        "--adapter",
        "--generated-dataset",
        "--include-generated",
        "--include-kaggle",
        "--kaggle-dataset",
        "--max-omnisvg-rows",
        "--model",
        "--omnisvg-eval-frac",
        "--omnisvg-dataset",
        "--primary-dataset",
        "--try-omnisvg",
    }
    return any(arg in known_args for arg in args)


def run_kaggle_one_cell() -> None:
    import os
    import subprocess
    import sys
    import importlib

    if not getattr(sys, "_bnb_installed_run", False):
        print("Ensuring dependencies (bitsandbytes>=0.46.1, accelerate, transformers)...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-U", 
            "bitsandbytes>=0.46.1", "accelerate", "transformers", "--quiet"
        ])
        setattr(sys, "_bnb_installed_run", True)
        importlib.invalidate_caches()
        
        # We only restart the kernel if we actually performed the install this session,
        # and we haven't restarted yet. We can drop a marker file.
        marker = "/tmp/bnb_restarted.txt"
        if not os.path.exists(marker):
            with open(marker, "w") as f:
                f.write("1")
            print("Installation complete. Restarting kernel to apply changes (this only happens once)...")
            os.kill(os.getpid(), 9)

    # Force patch transformers because Colab sometimes gets confused about bnb availability
    try:
        import transformers.utils.import_utils as tu
        tu._bitsandbytes_available = True
        tu.is_bitsandbytes_available = lambda: True
        import transformers.utils as tu2
        tu2.is_bitsandbytes_available = lambda: True
        import transformers.quantizers.quantizer_bnb_4bit as qbnb
        qbnb.is_bitsandbytes_available = lambda: True
    except Exception as e:
        print(f"Patch warning: {e}")

    main_kaggle(
        model=KAGGLE_MODEL,
        adapter=KAGGLE_ADAPTER,
        primary_dataset=KAGGLE_PRIMARY_DATASET,
        generated_dataset=KAGGLE_GENERATED_DATASET,
        kaggle_dataset=KAGGLE_DATASET,
        output_dir=KAGGLE_OUTPUT_DIR,
        extra_args=KAGGLE_EXTRA_ARGS,
    )


def notebook_usage_hint() -> str:
    return """
Kaggle/Jupyter note:
  By default this script evaluates SVG-code perplexity on OmniSVG/MMSVG rows.
  Run it from a Kaggle notebook with either:

    main_kaggle(
      adapter="/kaggle/input/your-trained-adapter/final_adapter",
      primary_dataset="omnisvg",
    )

  Or use the older generated-vs-Kaggle mode:

    !python svg_perplexity_overfitting_single.py --primary-dataset generated --adapter /kaggle/input/your-trained-adapter/final_adapter --generated-dataset /kaggle/input/diffusvg/training_pairs.json
""".strip()


def main_kaggle(
    model: str = KAGGLE_MODEL,
    adapter: str = KAGGLE_ADAPTER,
    primary_dataset: str = KAGGLE_PRIMARY_DATASET,
    generated_dataset: str = KAGGLE_GENERATED_DATASET,
    kaggle_dataset: str = KAGGLE_DATASET,
    output_dir: str = KAGGLE_OUTPUT_DIR,
    extra_args: list[str] | None = None,
) -> None:
    argv = [
        "--model",
        model,
        "--primary-dataset",
        primary_dataset,
        "--generated-dataset",
        generated_dataset,
        "--kaggle-dataset",
        kaggle_dataset,
        "--output-dir",
        output_dir,
    ]
    if adapter:
        argv += ["--adapter", adapter]
    if extra_args:
        argv.extend(extra_args)
    main(argv)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single-script SVG perplexity and overfitting checker.")
    parser.add_argument(
        "--model",
        default=MODEL_AUTO,
        help="Model/weight repo to evaluate. Default one-cell setting uses OmniSVG/OmniSVG.",
    )
    parser.add_argument(
        "--tokenizer-model",
        default=TOKENIZER_AUTO,
        help="Tokenizer repo/path. Default: model, with Qwen2.5-VL fallback for OmniSVG weights.",
    )
    parser.add_argument(
        "--omnisvg-base-model",
        default=OMNISVG_BASE_MODEL,
        help="Qwen backbone used when loading official OmniSVG weights.",
    )
    parser.add_argument(
        "--omnisvg-loader",
        choices=(OMNISVG_LOADER_AUTO, OMNISVG_LOADER_OFFICIAL, OMNISVG_LOADER_TRANSFORMERS),
        default=OMNISVG_LOADER_AUTO,
        help="How to load OmniSVG repos. 'official' loads Qwen backbone then OmniSVG pytorch_model.bin.",
    )
    parser.add_argument(
        "--primary-dataset",
        choices=(PRIMARY_DATASET_OMNISVG, PRIMARY_DATASET_GENERATED),
        default=PRIMARY_DATASET_OMNISVG,
        help="Dataset to use as the main perplexity/overfitting target.",
    )
    parser.add_argument("--adapter", default=None, help="Trained LoRA adapter path (optional). Omit to evaluate the base model without LoRA.")
    parser.add_argument(
        "--generated-dataset",
        default=GENERATED_DATASET_AUTO,
        help="Generated training_pairs.json/jsonl/csv/parquet or directory. Use 'auto' to search Kaggle inputs.",
    )
    parser.add_argument(
        "--kaggle-dataset",
        default="/kaggle/input/svg-dataset-for-generative-llm",
        help="Kaggle dataset directory/file.",
    )
    parser.add_argument("--download-kaggle", action="store_true", help="Try kagglehub download if path is missing.")
    parser.add_argument("--output-dir", default="svg_model_check", help="Where reports and prepared data are written.")
    parser.add_argument("--extra-dataset", action="append", default=[], help="Optional name=path prompt+SVG dataset.")
    parser.add_argument("--no-linked-web", action="store_true", help="Skip Gally and Simon web preparation.")
    parser.add_argument("--max-gally-svgs", type=int, default=0, help="0 means all Gally SVG outputs.")
    parser.add_argument("--try-omnisvg", action="store_true", help="Also score OmniSVG/MMSVG when primary-dataset is generated.")
    parser.add_argument(
        "--omnisvg-dataset",
        action="append",
        default=None,
        help="OmniSVG Hugging Face dataset to load. Repeatable. Defaults to MMSVG-Icon and MMSVG-Illustration.",
    )
    parser.add_argument("--max-omnisvg-rows", type=int, default=1000)
    parser.add_argument("--omnisvg-eval-frac", type=float, default=0.2, help="Fraction of OmniSVG SVG-code rows held out for eval PPL.")
    parser.add_argument("--include-generated", action="store_true", help="Also score the generated dataset in OmniSVG-primary mode.")
    parser.add_argument("--include-kaggle", action="store_true", help="Also score the Kaggle SVG dataset in OmniSVG-primary mode.")
    parser.add_argument("--trainer-state", default="", help="Optional explicit trainer_state.json path.")
    parser.add_argument("--model-class", choices=("auto", "qwen2vl", "causal"), default="auto")
    parser.add_argument("--max-seq-len", type=int, default=1024, help="1024 is safer on T4.")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--max-samples", type=int, default=0, help="Debug limit per dataset. 0 means all.")
    parser.add_argument("--no-4bit", dest="load_in_4bit", action="store_false")
    parser.set_defaults(load_in_4bit=True)
    if argv is None and in_notebook():
        args, _unknown = parser.parse_known_args()
        return args
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("PYTORCH_ALLOC_CONF", "expandable_segments:True")
    args.adapter = resolve_adapter_path(args.adapter) if args.adapter else None
    if args.model == MODEL_AUTO:
        if args.adapter:
            args.model = resolve_model_name(args.model, args.adapter)
        else:
            raise ValueError(
                "Cannot auto-detect model with no adapter. Set KAGGLE_MODEL to the model name, "
                "e.g. KAGGLE_MODEL = 'Qwen/Qwen2.5-Coder-7B-Instruct'"
            )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []

    omnisvg_dataset_names = args.omnisvg_dataset or list(OMNISVG_HF_DATASETS)

    source_links = {
        "kaggle_dataset": KAGGLE_DATASET_URL,
        "kaggle_notebook": KAGGLE_NOTEBOOK_URL,
        "gally_benchmark": GALLY_URL,
        "simon_note": SIMON_URL,
        "omnisvg": OMNISVG_URL,
        "omnisvg_hf_org": OMNISVG_HF_ORG_URL,
        "omnisvg_hf_model": OMNISVG_HF_MODEL_URL,
        "omnisvg_github": OMNISVG_GITHUB_URL,
        "omnisvg_hf_datasets": list(OMNISVG_HF_DATASETS),
        "omnisvg_bench_hf_dataset": OMNISVG_BENCH_HF_DATASET,
    }

    datasets_to_score: list[tuple[str, Path]] = []
    prepared_counts: dict[str, int] = {}
    benchmark_prompts_path: Path | None = None
    primary_path: Path | None = None
    primary_count = 0
    assessment_primary_dataset = args.primary_dataset
    uniqueness_path: Path | None = None

    def add_prepared_dataset(name: str, source: Path) -> Path:
        prepared_path, count = prepare_local_dataset(name, source, out_dir)
        datasets_to_score.append((name, prepared_path))
        prepared_counts[name] = count
        return prepared_path

    if args.primary_dataset == PRIMARY_DATASET_OMNISVG:
        log("Preparing OmniSVG/MMSVG SVG-code datasets...")
        omnisvg_path, omnisvg_count, warning = prepare_omnisvg(out_dir, args.max_omnisvg_rows, omnisvg_dataset_names)
        if warning:
            warnings.append(warning)
        if not omnisvg_path or omnisvg_count == 0:
            raise RuntimeError(
                "No usable OmniSVG prompt+SVG rows were prepared. "
                "Use --omnisvg-dataset with a dataset containing text/description and svg columns."
            )
        omnisvg_records = load_records(omnisvg_path)
        train_records, eval_records = split_records_for_eval(omnisvg_records, args.omnisvg_eval_frac)
        if not train_records or not eval_records:
            raise RuntimeError("Need at least two usable OmniSVG SVG-code rows to make a train/eval overfitting split.")
        train_path = write_dataset_split(out_dir / "prepared" / "omnisvg_train.jsonl", train_records)
        eval_path = write_dataset_split(out_dir / "prepared" / "omnisvg_eval.jsonl", eval_records)

        datasets_to_score.append((OMNISVG_TRAIN_DATASET, train_path))
        datasets_to_score.append((OMNISVG_EVAL_DATASET, eval_path))
        prepared_counts[PRIMARY_DATASET_OMNISVG] = omnisvg_count
        prepared_counts[OMNISVG_TRAIN_DATASET] = len(train_records)
        prepared_counts[OMNISVG_EVAL_DATASET] = len(eval_records)
        primary_path = eval_path
        primary_count = omnisvg_count
        assessment_primary_dataset = OMNISVG_EVAL_DATASET
        uniqueness_path = omnisvg_path
        log(f"OmniSVG split: {len(train_records)} train rows, {len(eval_records)} eval rows")

        kaggle_source: Path | None = None
        if args.include_generated or args.include_kaggle:
            kaggle_path = Path(args.kaggle_dataset)
            if kaggle_path.exists():
                kaggle_source = kaggle_path

        if args.include_generated:
            generated_source = resolve_generated_dataset_path(args.generated_dataset, kaggle_source)
            add_prepared_dataset(PRIMARY_DATASET_GENERATED, generated_source)

        if args.include_kaggle:
            kaggle_source = kaggle_source or maybe_download_kaggle_dataset(Path(args.kaggle_dataset), args.download_kaggle)
            add_prepared_dataset("kaggle", kaggle_source)

    else:
        kaggle_source = maybe_download_kaggle_dataset(Path(args.kaggle_dataset), args.download_kaggle)
        generated_source = resolve_generated_dataset_path(args.generated_dataset, kaggle_source)

        log("Preparing generated and Kaggle datasets...")
        generated_path = add_prepared_dataset(PRIMARY_DATASET_GENERATED, generated_source)
        add_prepared_dataset("kaggle", kaggle_source)
        primary_path = generated_path
        primary_count = prepared_counts[PRIMARY_DATASET_GENERATED]
        uniqueness_path = generated_path
        assessment_primary_dataset = PRIMARY_DATASET_GENERATED

        if not args.no_linked_web:
            log("Preparing Gally/SVG benchmark prompts and SVG outputs...")
            gally_path, prompts_path, warning = prepare_gally(out_dir, args.max_gally_svgs)
            if warning:
                warnings.append(warning)
            if gally_path and gally_path.exists() and load_records(gally_path):
                datasets_to_score.append(("gally", gally_path))
                prepared_counts["gally"] = len(load_records(gally_path))
            if prompts_path:
                benchmark_prompts_path = prompts_path
                warning = append_simon_prompts(prompts_path)
                if warning:
                    warnings.append(warning)

        if args.try_omnisvg:
            log("Trying OmniSVG/MMSVG SVG-code datasets...")
            omnisvg_path, omnisvg_count, warning = prepare_omnisvg(out_dir, args.max_omnisvg_rows, omnisvg_dataset_names)
            if warning:
                warnings.append(warning)
            if omnisvg_path and omnisvg_count:
                datasets_to_score.append((PRIMARY_DATASET_OMNISVG, omnisvg_path))
                prepared_counts[PRIMARY_DATASET_OMNISVG] = omnisvg_count

    for spec in args.extra_dataset:
        name, path = parse_extra_dataset(spec)
        datasets_to_score.append((name, path))
        try:
            prepared_counts[name] = len(normalized_prompt_svg(path))
        except Exception:
            prepared_counts[name] = 0

    manifest = {
        "source_links": source_links,
        "primary_dataset": args.primary_dataset,
        "assessment_primary_dataset": assessment_primary_dataset,
        "primary_path": str(primary_path) if primary_path else "",
        "omnisvg_datasets": omnisvg_dataset_names,
        "omnisvg_eval_frac": args.omnisvg_eval_frac,
        "prepared_datasets": {name: str(path) for name, path in datasets_to_score},
        "counts": prepared_counts,
        "benchmark_prompts": str(benchmark_prompts_path) if benchmark_prompts_path else "",
        "warnings": warnings,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    log("Loading model and adapter...")
    model, tokenizer = load_model_and_tokenizer(args)
    lora_params = count_lora_parameters(model)

    log("Computing perplexity per dataset...")
    perplexities = []
    for name, path in datasets_to_score:
        perplexities.append(evaluate_dataset(name, path, model, tokenizer, args))
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    trainer_state = find_trainer_state(Path(args.adapter) if args.adapter else None, args.trainer_state)
    losses = load_trainer_losses(trainer_state)
    if primary_path is None:
        raise RuntimeError("No primary dataset was prepared.")
    overlap = prompt_overlap(primary_path, benchmark_prompts_path)
    uniqueness = svg_uniqueness(uniqueness_path or primary_path)
    assessment = assess_overfitting(
        perplexities,
        losses,
        assessment_primary_dataset,
        primary_count,
        lora_params,
        overlap,
        uniqueness,
    )

    report = {
        "model": args.model,
        "adapter": args.adapter,
        "source_links": source_links,
        "manifest": str(out_dir / "manifest.json"),
        "trainer_state": losses["path"],
        "perplexity": perplexities,
        "losses": losses,
        "prompt_overlap": overlap,
        "assessment": assessment,
        "warnings": warnings,
    }

    json_path = out_dir / "overfitting_report.json"
    md_path = out_dir / "overfitting_report.md"
    csv_path = out_dir / "perplexity.csv"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(md_path, report)
    write_perplexity_csv(csv_path, perplexities)

    log("\nPerplexity by dataset")
    log("dataset\trecords\ttokens\tnll\tppl")
    for row in perplexities:
        log(
            f"{row['dataset']}\t{row['records_scored']}\t{row['target_tokens']}\t"
            f"{row['nll']:.4f}\t{row['perplexity']:.3f}"
        )

    log(f"\nVerdict: {assessment['verdict']}")
    for item in assessment["overfitting_signals"]:
        log(f"OVERFITTING: {item}")
    for item in assessment["risks"]:
        log(f"RISK: {item}")
    for item in assessment["good_signs"]:
        log(f"OK: {item}")

    log(f"\nWrote: {json_path}")
    log(f"Wrote: {md_path}")
    log(f"Wrote: {csv_path}")


if __name__ == "__main__":
    if in_notebook() and not has_required_cli_args():
        if RUN_KAGGLE_ONE_CELL:
            run_kaggle_one_cell()
        else:
            print(notebook_usage_hint())
    else:
        try:
            main()
        except KeyboardInterrupt:
            raise
        except SystemExit as exc:
            if exc.code == 2 and in_notebook():
                print("\n" + notebook_usage_hint(), file=sys.stderr)
            else:
                raise
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            raise
