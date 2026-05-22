"""
Download the official gitcat404/IntroSVG-train dataset and write it as
data/d_sft.jsonl + data/dataset_info.json, bypassing the need for
Steps 1 (standardize) and 2 (GPT-4o critiques).

This is the exact same data the paper used — higher quality than anything
we could generate locally.

Run:
    python 00_download_official_data.py [--max-samples N]
"""

import argparse
import io
import json
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("step0")

DATA_DIR    = Path("data")
IMG_DIR     = DATA_DIR / "images"
D_SFT       = DATA_DIR / "d_sft.jsonl"
D_DIRECT    = DATA_DIR / "d_g_direct.jsonl"
DATASET_INFO = DATA_DIR / "dataset_info.json"

HF_DATASET  = "gitcat404/IntroSVG-train"


def main(args):
    from datasets import load_dataset

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    log.info(f"Downloading {HF_DATASET} ...")
    ds = load_dataset(HF_DATASET, split="train", streaming=True)

    img_counter = 0
    n_written = 0

    with open(D_SFT, "w", encoding="utf-8") as f_sft, \
         open(D_DIRECT, "w", encoding="utf-8") as f_direct:

        for row in ds:
            if args.max_samples and n_written >= args.max_samples:
                break

            messages = row.get("messages", [])
            images   = row.get("images", [])

            if not messages:
                continue

            # Rows with images: save PIL image to disk, update path
            if images and len(images) > 0:
                new_image_paths = []
                for img_obj in images:
                    img_counter += 1
                    fname = f"{img_counter:06d}.png"
                    fpath = IMG_DIR / fname
                    try:
                        if hasattr(img_obj, "save"):
                            # PIL Image
                            img_obj.save(fpath, format="PNG")
                        elif isinstance(img_obj, bytes):
                            fpath.write_bytes(img_obj)
                        else:
                            continue
                        new_image_paths.append(f"images/{fname}")
                    except Exception as e:
                        log.warning(f"Could not save image: {e}")
                        continue

                out = {"messages": messages, "images": new_image_paths}
            else:
                out = {"messages": messages}

            f_sft.write(json.dumps(out, ensure_ascii=False) + "\n")

            # If it's a generator row (no images), also write to d_g_direct
            # so step 2 skip check works
            if not images:
                # Extract prompt+svg for d_g_direct format
                if len(messages) == 2:
                    f_direct.write(json.dumps({
                        "prompt": messages[0].get("content", ""),
                        "svg":    messages[1].get("content", ""),
                    }, ensure_ascii=False) + "\n")

            n_written += 1
            if n_written % 1000 == 0:
                log.info(f"  {n_written:,} rows written")

    log.info(f"Done. {n_written:,} rows → {D_SFT}")

    # Write dataset_info.json for LLaMA-Factory
    dataset_info = {
        "d_sft": {
            "file_name": "d_sft.jsonl",
            "formatting": "sharegpt",
            "columns": {"messages": "messages", "images": "images"},
        },
        "d_pref_g": {
            "file_name": "d_pref_g.jsonl",
            "formatting": "sharegpt",
            "ranking": True,
            "columns": {"messages": "messages", "chosen": "chosen", "rejected": "rejected"},
        },
    }
    DATASET_INFO.write_text(json.dumps(dataset_info, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"dataset_info.json → {DATASET_INFO}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-samples", type=int, default=0,
                        help="Cap rows to download (0 = all)")
    args = parser.parse_args()
    main(args)
