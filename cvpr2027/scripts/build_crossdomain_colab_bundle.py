"""Package the cross-domain SVG patch dataset and create its one-click Colab notebook."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
DATA = ROOT / "data" / "engsvg-crossdomain-edit-v1"
BUNDLE = PROJECT / "engsvg-crossdomain-colab-bundle.zip"
NOTEBOOK = ROOT / "notebooks" / "EngSVG_Crossdomain_Patch_Train.ipynb"


def notebook() -> dict:
    code = '''import json, os, pathlib, shutil, subprocess, sys, zipfile, torch

def run(args, env=None):
    print('RUN:', ' '.join(map(str, args)), flush=True)
    process = subprocess.Popen(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, bufsize=1)
    for line in process.stdout:
        print(line, end='', flush=True)
    if process.wait():
        raise RuntimeError(f'command failed with status {process.returncode}')

assert torch.cuda.is_available(), 'Select Kernel > Colab > Auto Connect with a GPU runtime first.'
print('GPU:', torch.cuda.get_device_name(0), flush=True)
bundle = pathlib.Path('/content/engsvg-crossdomain-colab-bundle.zip')
if not bundle.exists():
    from google.colab import files
    print('Upload engsvg-crossdomain-colab-bundle.zip', flush=True)
    uploaded = files.upload()
    if bundle.name not in uploaded:
        raise RuntimeError('Expected ' + bundle.name)

work = pathlib.Path('/content/engsvg-crossdomain')
if work.exists():
    shutil.rmtree(work)
with zipfile.ZipFile(bundle) as archive:
    archive.extractall(work)

run([sys.executable, '-m', 'pip', 'install', '-q',
     'transformers>=4.48,<5', 'peft>=0.14', 'accelerate>=1.2', 'huggingface_hub>=0.27'])
subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', '-q', 'torchao'], check=False)

project = work / 'payload'
env = os.environ.copy()
env['PYTHONPATH'] = str(project / 'cvpr2027/src')
output = pathlib.Path('/content/engsvg-crossdomain-run')
command = [sys.executable, str(project / 'cvpr2027/scripts/train_crossdomain_svg_patcher.py'),
           '--data', str(project / 'cvpr2027/data/engsvg-crossdomain-edit-v1'),
           '--out', str(output), '--epochs', '1', '--eval-count', '100',
           '--max-length', '4096', '--max-new-tokens', '1400']
run(command, env=env)

summary = json.loads((output / 'summary.json').read_text())
print()
print('FINAL RESULTS', flush=True)
print(json.dumps(summary, indent=2), flush=True)
print()
print('Download before the runtime expires:', str(output) + '-artifacts.zip', flush=True)
'''
    return {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": [
                "# Cross-domain engineering SVG patch training\n",
                "Connect a Colab GPU in VS Code and run this cell. It trains a LoRA on 8,000 "
                "source-lineage-disjoint SVG edit examples and evaluates 100 held-out examples before and after training.\n\n",
                "The target is constrained patch JSON. Every training target was applied to its source SVG and "
                "proved to reproduce the intended target tree before this bundle was created.\n",
            ]},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
             "source": [line + "\n" for line in code.splitlines()]},
        ],
        "metadata": {
            "accelerator": "GPU",
            "colab": {"gpuType": "L4", "provenance": []},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4, "nbformat_minor": 0,
    }


def build() -> dict:
    required = [DATA / name for name in ("train.jsonl.gz", "validation.jsonl.gz", "test.jsonl.gz",
                                           "dataset-summary.json", "sha256-manifest.json", "README.md")]
    if not all(path.exists() for path in required):
        raise FileNotFoundError("build engsvg-crossdomain-edit-v1 before creating the Colab bundle")
    NOTEBOOK.write_text(json.dumps(notebook(), indent=1) + "\n")
    with tempfile.TemporaryDirectory() as temporary:
        payload = Path(temporary) / "payload"
        destination = payload / "cvpr2027" / "data" / DATA.name
        destination.mkdir(parents=True)
        for path in required:
            shutil.copy2(path, destination / path.name)
        script_dir = payload / "cvpr2027" / "scripts"; script_dir.mkdir(parents=True)
        shutil.copy2(ROOT / "scripts" / "train_crossdomain_svg_patcher.py", script_dir)
        shutil.copytree(ROOT / "src" / "svgpatchlab", payload / "cvpr2027" / "src" / "svgpatchlab")
        with zipfile.ZipFile(BUNDLE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(payload.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(Path(temporary)))
    result = {"bundle": str(BUNDLE), "bundle_bytes": BUNDLE.stat().st_size,
              "bundle_sha256": hashlib.sha256(BUNDLE.read_bytes()).hexdigest(),
              "notebook": str(NOTEBOOK),
              "notebook_sha256": hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest()}
    (ROOT / "notebooks" / "EngSVG_Crossdomain_Patch_Train.bundle.json").write_text(
        json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
