#!/usr/bin/env python
"""Prepare the linked SVG datasets for perplexity and overfitting checks.

Sources covered:
- local/generated DiffuSVG training pairs
- Kaggle SVG dataset folder: kaushikyh/svg-dataset-for-generative-llm
- Gally SVG benchmark page outputs
- Simon Willison benchmark article prompts
- optional OmniSVG/MMSVGBench via Hugging Face datasets, if it has prompt+SVG rows
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import urljoin

from evaluate_perplexity import load_records, normalize_record


KAGGLE_DATASET_URL = "https://www.kaggle.com/datasets/kaushikyh/svg-dataset-for-generative-llm"
KAGGLE_NOTEBOOK_URL = "https://www.kaggle.com/code/gumballnguyen/fine-turning-model-qwen2-5-coder-text2svg"
GALLY_URL = "https://gally.net/temp/20251107pelican-alternatives/index.html"
SIMON_URL = "https://simonwillison.net/2025/Nov/25/llm-svg-generation-benchmark/"
OMNISVG_URL = "https://omnisvg.github.io/"
OMNISVG_HF_DATASET = "OmniSVG/MMSVGBench"


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _normalized_prompt_svg(path: Path) -> list[dict]:
    out = []
    for record in load_records(path):
        item = normalize_record(record)
        if item:
            out.append(item)
    return out


def _http_get(url: str) -> str:
    import requests

    try:
        return requests.get(url, timeout=45).text
    except requests.exceptions.SSLError:
        return requests.get(url, timeout=45, verify=False).text


def _prepare_generated(source: Path, out_dir: Path) -> Path:
    records = _normalized_prompt_svg(source)
    out = out_dir / "generated.jsonl"
    _write_jsonl(out, records)
    return out


def _prepare_kaggle(source: Path, out_dir: Path) -> Path:
    records = _normalized_prompt_svg(source)
    out = out_dir / "kaggle_svg_dataset.jsonl"
    _write_jsonl(out, records)
    return out


def _prepare_gally(out_dir: Path, max_svgs: int = 0) -> tuple[Path, Path]:
    page = _http_get(GALLY_URL)

    prompt_by_num = {}
    for number, prompt in re.findall(
        r'<span class="prompt-number">#(\d+)</span>\s*(Generate an SVG of .*?)\s*</div>',
        page,
        flags=re.S,
    ):
        prompt_by_num[number] = html.unescape(re.sub(r"\s+", " ", prompt)).strip()

    records = []
    prompt_records = []
    for number, prompt in sorted(prompt_by_num.items(), key=lambda x: int(x[0])):
        prompt_records.append({"prompt": prompt, "source": GALLY_URL, "prompt_number": int(number)})

    for src, alt in re.findall(r'<img src="([^"]+\.svg)" alt="([^"]+)"', page):
        match = re.search(r"_prompt(\d+)\.svg", src)
        number = match.group(1) if match else ""
        prompt = prompt_by_num.get(number)
        if not prompt:
            alt_prompt = re.sub(r"\s+-\s+.*$", "", html.unescape(alt)).strip()
            prompt = alt_prompt
        svg_url = urljoin(GALLY_URL, src)
        try:
            svg = _http_get(svg_url).strip()
        except Exception:
            continue
        if "<svg" not in svg:
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

    gally_path = out_dir / "gally_svg_outputs.jsonl"
    prompts_path = out_dir / "benchmark_prompts.jsonl"
    _write_jsonl(gally_path, records)
    _write_jsonl(prompts_path, prompt_records)
    return gally_path, prompts_path


def _append_simon_prompts(prompts_path: Path) -> None:
    page = _http_get(SIMON_URL)
    prompts = set()
    for prompt in re.findall(r'"([^"]+?(?:operating|driving|inspecting|steering|riding)[^"]+?)"', page):
        prompts.add(html.unescape(prompt).strip())
    existing = load_records(prompts_path) if prompts_path.exists() else []
    for prompt in sorted(prompts):
        existing.append({"prompt": f"Generate an SVG of {prompt}", "source": SIMON_URL})
    _write_jsonl(prompts_path, existing)


def _prepare_omnisvg(out_dir: Path, max_rows: int = 0) -> Path | None:
    try:
        from datasets import load_dataset
    except Exception:
        return None

    rows = []
    try:
        ds = load_dataset(OMNISVG_HF_DATASET)
    except Exception:
        return None

    for split_name, split in ds.items():
        for record in split:
            item = normalize_record(record)
            if not item:
                continue
            item["source"] = OMNISVG_HF_DATASET
            item["split"] = split_name
            rows.append(item)
            if max_rows and len(rows) >= max_rows:
                break
        if max_rows and len(rows) >= max_rows:
            break

    out = out_dir / "omnisvg_mmsvgbench.jsonl"
    _write_jsonl(out, rows)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated", required=True, help="Generated training_pairs.json/jsonl")
    parser.add_argument("--kaggle", required=True, help="Kaggle dataset directory/file")
    parser.add_argument("--out-dir", default="svg_check_data")
    parser.add_argument("--max-gally-svgs", type=int, default=0)
    parser.add_argument("--try-omnisvg", action="store_true")
    parser.add_argument("--max-omnisvg-rows", type=int, default=1000)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    manifest = {
        "source_links": {
            "kaggle_dataset": KAGGLE_DATASET_URL,
            "kaggle_notebook": KAGGLE_NOTEBOOK_URL,
            "gally_benchmark": GALLY_URL,
            "simon_note": SIMON_URL,
            "omnisvg": OMNISVG_URL,
            "omnisvg_hf_dataset": OMNISVG_HF_DATASET,
        },
        "datasets": {},
    }

    generated = _prepare_generated(Path(args.generated), out_dir)
    kaggle = _prepare_kaggle(Path(args.kaggle), out_dir)
    gally, prompts = _prepare_gally(out_dir, args.max_gally_svgs)
    _append_simon_prompts(prompts)

    manifest["datasets"]["generated"] = str(generated)
    manifest["datasets"]["kaggle"] = str(kaggle)
    manifest["datasets"]["gally"] = str(gally)
    manifest["benchmark_prompts"] = str(prompts)

    if args.try_omnisvg:
        omnisvg = _prepare_omnisvg(out_dir, args.max_omnisvg_rows)
        if omnisvg:
            manifest["datasets"]["omnisvg"] = str(omnisvg)

    for name, path in manifest["datasets"].items():
        records = load_records(Path(path))
        manifest.setdefault("counts", {})[name] = len(records)

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
