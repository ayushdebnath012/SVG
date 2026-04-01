#!/usr/bin/env python3
"""
rebuild_outputs.py — Re-encodes dataset_pipeline.py + vectorize.py as base64
and regenerates DiffuSVG_Dataset_Finetune.py and DiffuSVG_Dataset_Finetune.ipynb.
"""

import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent

# ── 1. Read source files ──────────────────────────────────────────────────────
vec_src  = (ROOT / "vectorize.py").read_text(encoding="utf-8")
ds_src   = (ROOT / "dataset_pipeline.py").read_text(encoding="utf-8")
ft_src   = (ROOT / "finetune_qwen2vl.py").read_text(encoding="utf-8")

vec_b64  = base64.b64encode(vec_src.encode("utf-8")).decode("ascii")
ds_b64   = base64.b64encode(ds_src.encode("utf-8")).decode("ascii")

print(f"vectorize.py       : {len(vec_src):,} chars  ->  b64 {len(vec_b64):,} chars")
print(f"dataset_pipeline.py: {len(ds_src):,} chars  ->  b64 {len(ds_b64):,} chars")
print(f"finetune_qwen2vl.py: {len(ft_src):,} chars")

# ── 2. Build the mega-cell source ─────────────────────────────────────────────
# Read header (lines 1..62) and tail (lines 67..) of existing .py to preserve them
existing_py = (ROOT / "DiffuSVG_Dataset_Finetune.py").read_text(encoding="utf-8")
lines = existing_py.splitlines(keepends=True)

# Find the two b64 variable lines and replace them
new_lines = []
for line in lines:
    if re.match(r"^_VEC_B64\s*=", line):
        new_lines.append(f'_VEC_B64 = "{vec_b64}"\n')
    elif re.match(r"^_DS_B64\s*=", line):
        new_lines.append(f'_DS_B64  = "{ds_b64}"\n')
    else:
        new_lines.append(line)

new_py = "".join(new_lines)
(ROOT / "DiffuSVG_Dataset_Finetune.py").write_text(new_py, encoding="utf-8")
print(f"\nWrote DiffuSVG_Dataset_Finetune.py  ({len(new_py):,} bytes)")

# ── 3. Rebuild the notebook ───────────────────────────────────────────────────
# Strip the file-level docstring/shebang to get pure executable code for the cell
# Everything from "# ═══" onward is the mega-cell
mega_start = new_py.find("# ═══")
if mega_start == -1:
    mega_start = new_py.find("# ── CONFIG")
mega_cell_src = new_py[mega_start:]

notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"},
        "accelerator": "GPU",
        "colab": {"provenance": []}
    },
    "cells": [
        {
            "cell_type": "markdown",
            "id": "title-cell",
            "metadata": {},
            "source": [
                "# DiffuSVG — Dataset Build + Qwen2VL LoRA Fine-Tune\n",
                "\n",
                "> **Runtime**: GPU (T4 16 GB).  \n",
                "> Set `HF_TOKEN` in the code cell below, then **Runtime → Run all**.\n",
                ">\n",
                "> **Pipeline**: bad-prompts from `results.json`  \n",
                "> → SD 3.5 Medium → Potrace silhouette SVG  \n",
                "> → Qwen2VL lenient-silhouette gate → JSONL dataset  \n",
                "> → QLoRA SFT on Qwen2VL-7B-Instruct\n"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "id": "mega-cell",
            "metadata": {"id": "mega-cell"},
            "outputs": [],
            "source": mega_cell_src.splitlines(keepends=True)
        }
    ]
}

nb_path = ROOT / "DiffuSVG_Dataset_Finetune.ipynb"
with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)
print(f"Wrote DiffuSVG_Dataset_Finetune.ipynb  ({nb_path.stat().st_size:,} bytes)")
print("\nDone. Both files updated with lenient JUDGE_PROMPT.")
