"""Package the DPO checker for a Kaggle T4 run: a private dataset (pairs, comparisons, trainer) and a small notebook.

Kaggle T4s lack bfloat16, so the checker is Qwen3.5-4B in fp16 on one GPU, trained with the single-token DPO loop
(dpo_checker_train.py train-letter: TRL's full-vocabulary logits do not fit 16 GB); if fp16 produces non-finite values
the notebook falls back to Qwen3.5-2B in fp32. An 8-example smoke run precedes each full run. Outputs (adapter, scored comparisons, logs) are written to /kaggle/working.

  python make_kaggle_dpo_checker.py --tag fem-syn --user ayushdebnath0123
  kaggle datasets create -p tmp/kaggle-dpo-checker/data      (or `datasets version` after the first upload)
  kaggle kernels push -p tmp/kaggle-dpo-checker/kernel --accelerator NvidiaTeslaT4
"""
import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/dpo-checker-benchcad-20261008"

SETUP = r'''import os, subprocess, sys, pathlib
os.environ["CUDA_VISIBLE_DEVICES"] = "0"   # one T4: avoids DataParallel
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "transformers==5.18.0", "trl==1.14.2", "peft==0.21.2",
                "accelerate", "datasets"], check=True)
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"])  # Kaggle's torchao 0.10 blocks peft LoRA
src = next(pathlib.Path("/kaggle/input").rglob("dpo_checker_train.py")).parent
work = pathlib.Path("/kaggle/working"); os.chdir(work)
for f in src.iterdir():
    if f.is_file():
        (work / f.name).write_bytes(f.read_bytes())
print(sorted(p.name for p in work.iterdir()))
'''

RUN_CELL = r'''import subprocess, sys, json, pathlib
TAG = "{tag}"
def sh(args, log):
    with open(log, "a") as h:
        r = subprocess.run([sys.executable, "dpo_checker_train.py", *args], stdout=h, stderr=subprocess.STDOUT)
    print(" ".join(args[:1]), "exit", r.returncode, flush=True); return r.returncode
used = None
for model, dtype in (("Qwen/Qwen3.5-4B", "fp16"), ("Qwen/Qwen3.5-2B", "fp32")):
    common = ["--model", model, "--dtype", dtype, "--train", f"dpo-train-{{TAG}}.jsonl", "--dev", f"dpo-dev-pairs-{{TAG}}.jsonl",
              "--epochs", "1", "--max-length", "2048"]
    if sh(["train-letter", *common, "--out", "out-smoke", "--limit", "8"], "train.log") != 0:  # minutes, not hours
        print(open("train.log").read()[-3000:]); continue
    if sh(["train-letter", *common, "--out", f"out-{{TAG}}"], "train.log") == 0:
        used = (model, dtype); break
    print(open("train.log").read()[-3000:])
assert used, "training failed for both settings"
for split in ("dev", "test"):
    sh(["score", "--model", used[0], "--dtype", used[1], "--adapter", f"out-{{TAG}}/adapter", "--batch", "4",
        "--input", f"{{split}}-comparisons-{{TAG}}.jsonl", "--output", f"{{split}}-scored-{{TAG}}.jsonl"], "score.log")
    sh(["score", "--model", used[0], "--dtype", used[1], "--adapter", "none", "--batch", "4",
        "--input", f"{{split}}-comparisons-{{TAG}}.jsonl", "--output", f"{{split}}-scored-zeroshot-{{TAG}}.jsonl"], "score.log")
json.dump(dict(model=used[0], dtype=used[1], tag=TAG), open("run-config.json", "w"))
print("ALL-DONE", used, flush=True)
'''


def notebook(cells):
    return {"cells": [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": c} for c in cells],
            "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                         "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tag", default="fem-syn")
    p.add_argument("--user", default="ayushdebnath0123")
    a = p.parse_args()
    out = ROOT / "tmp/kaggle-dpo-checker"
    data, kernel = out / "data", out / "kernel"
    for d in (data, kernel):
        d.mkdir(parents=True, exist_ok=True)
    for name in (f"dpo-train-{a.tag}.jsonl", f"dpo-dev-pairs-{a.tag}.jsonl", f"dev-comparisons-{a.tag}.jsonl",
                 f"test-comparisons-{a.tag}.jsonl"):
        shutil.copy(RUN / name, data / name)
    import random
    dev = (data / f"dpo-dev-pairs-{a.tag}.jsonl").read_text().splitlines()
    random.Random(17).shuffle(dev)  # 200 development pairs suffice for the epoch-end DPO loss; tau uses the comparisons
    (data / f"dpo-dev-pairs-{a.tag}.jsonl").write_text("\n".join(dev[:200]) + "\n")
    shutil.copy(ROOT / "scripts/dpo_checker_train.py", data / "dpo_checker_train.py")
    slug = "cad-dpo-checker-data"
    (data / "dataset-metadata.json").write_text(json.dumps(dict(title="CAD DPO checker data", id=f"{a.user}/{slug}",
                                                                 licenses=[{"name": "CC0-1.0"}]), indent=1))
    (kernel / "cad-dpo-checker.ipynb").write_text(json.dumps(notebook([SETUP, RUN_CELL.format(tag=a.tag)]), indent=1))
    (kernel / "kernel-metadata.json").write_text(json.dumps(dict(
        id=f"{a.user}/cad-dpo-checker-benchcad", title="CAD DPO checker BenchCAD", code_file="cad-dpo-checker.ipynb",
        language="python", kernel_type="notebook", is_private=True, enable_gpu=True, enable_internet=True,
        dataset_sources=[f"{a.user}/{slug}"], competition_sources=[], kernel_sources=[], machine_shape="NvidiaTeslaT4"), indent=1))
    print(json.dumps({f.name: f.stat().st_size for f in sorted(data.iterdir())}))


if __name__ == "__main__":
    main()
