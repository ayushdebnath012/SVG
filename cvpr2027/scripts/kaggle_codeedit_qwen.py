"""Kaggle launcher for the BenchCAD CodeEdit pipeline with Qwen (T4 x2).

Installs the official BenchCAD-main environment (pinned commit, uv.lock), downloads edit-bench with the official tool,
serves Qwen with vLLM (fp16, tensor-parallel over both T4s, thinking off) and runs scripts/benchcad_codeedit_pipeline.py:
  1. GEPA on training tasks          -> frozen repair prompt
  2. held-out test with the frozen prompt (edit -> execute -> diagnose -> repair, evaluator-ranked MCTS)
The test stage resumes from its results.jsonl. Results (summary, results.jsonl, search trees, best programs and STEP
files) are packed into /kaggle/working/codeedit-results.bin.

  python kaggle_codeedit_qwen.py [--model Qwen/Qwen3.5-9B] [--hours 11]
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request

BENCH_REPO, BENCH_COMMIT = "https://github.com/BenchCAD/BenchCAD-main.git", "77fd16a80a4e5fc39964ee23b6cc3225beefac8f"
VLLM_WHEEL = "https://github.com/vllm-project/vllm/releases/download/v0.31.0/vllm-0.31.0+cu129-cp38-abi3-manylinux_2_28_x86_64.whl"
HERE = Path(__file__).resolve().parent
WORK, OUT = Path("/tmp/codeedit"), Path("/kaggle/working/out")  # WORK is not saved with the kernel output


def sh(cmd: str, log: Path | None = None, timeout: int = 3600) -> None:
    print("$", cmd[:200], flush=True)
    with (log.open("a") if log else open(os.devnull, "w")) as h:
        subprocess.run(cmd, shell=True, check=True, timeout=timeout, stdout=h if log else None, stderr=subprocess.STDOUT if log else None)


def setup_bench() -> Path:
    repo = WORK / "BenchCAD-main"
    if not (repo / ".venv/bin/python").exists():
        sh(f"{sys.executable} -m pip install -q uv")
        sh(f"git clone -q {BENCH_REPO} {repo} && cd {repo} && git checkout -q {BENCH_COMMIT}")
        sh(f"cd {repo} && uv sync", WORK / "bench-install.log", 3600)
        sh(f"uv pip install --python {repo}/.venv/bin/python -q gepa", WORK / "bench-install.log")
    if not (repo / "CodeEdit/data/records.jsonl").exists():
        sh(f"cd {repo}/CodeEdit && {repo}/.venv/bin/python tools/download_edit_bench.py", WORK / "download.log", 3600)
    return repo


def start_vllm(model: str, max_len: int) -> str:
    venv = WORK / "vllm-env"
    py = venv / "bin/python"
    if not (venv / "bin/vllm").exists():
        sh(f"uv venv -p {sys.executable} {venv} && uv pip install --python {py} '{VLLM_WHEEL}' "
           "--extra-index-url https://download.pytorch.org/whl/cu129 --index-strategy unsafe-best-match", WORK / "vllm-install.log", 2400)
        subprocess.run(f"uv pip uninstall --python {py} torchcodec", shell=True, capture_output=True)  # cannot load on Kaggle
    gpus = len(subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True).stdout.strip().splitlines())
    env = dict(os.environ, VLLM_USE_FLASHINFER_SAMPLER="0", PATH=f"{venv}/bin:" + os.environ["PATH"])
    for extra in ([], ["--enforce-eager"]):
        cmd = [str(venv / "bin/vllm"), "serve", model, "--host", "127.0.0.1", "--port", "8000", "--dtype", "float16",
               "--tensor-parallel-size", str(gpus), "--max-model-len", str(max_len), "--gpu-memory-utilization", "0.9",
               "--max-num-seqs", "16", "--seed", "17", *extra]
        print("VLLM START", " ".join(cmd[2:]), flush=True)
        proc = subprocess.Popen(cmd, stdout=(WORK / "vllm.log").open("a"), stderr=subprocess.STDOUT, env=env)
        t0 = time.time()
        while proc.poll() is None and time.time() - t0 < 2400:
            try:
                urllib.request.urlopen("http://127.0.0.1:8000/v1/models", timeout=5)
            except Exception:  # noqa: BLE001 - not up yet
                time.sleep(15)
                continue
            body = json.dumps(dict(model=model, max_tokens=48, temperature=0, chat_template_kwargs=dict(enable_thinking=False),
                                   messages=[{"role": "user", "content": "Write one line of CadQuery that makes a box."}])).encode()
            req = urllib.request.Request("http://127.0.0.1:8000/v1/chat/completions", body, {"Content-Type": "application/json"})
            text = json.loads(urllib.request.urlopen(req, timeout=600).read())["choices"][0]["message"]["content"] or ""
            print(f"VLLM READY after {time.time() - t0:.0f}s; probe {text[:100]!r}", flush=True)
            if sum(ch.isalpha() for ch in text) >= 10:  # fp16 overflow shows up as empty / punctuation-only output
                return "http://127.0.0.1:8000/v1"
            break
        proc.kill()
        proc.wait()
        print("VLLM FAILED; log tail:\n" + "\n".join((WORK / "vllm.log").read_text().splitlines()[-25:]), flush=True)
    raise SystemExit("vLLM could not serve " + model)


def pack() -> None:
    """Small archive: everything except candidate STEP files other than best.step (named .bin: Kaggle unpacks tars)."""
    arc = Path("/kaggle/working/codeedit-results.bin")
    with tarfile.open(arc, "w:gz") as t:
        for p in OUT.rglob("*"):
            if p.is_dir():
                continue
            if p.suffix == ".step" and p.name != "best.step":
                continue
            if "rollouts" in p.parts and p.suffix in (".step", ".py"):
                continue
            t.add(p, arcname=str(p.relative_to(OUT.parent)))
    print("packed", arc, arc.stat().st_size // 1024, "KB", flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="Qwen/Qwen3.5-9B")
    p.add_argument("--hours", type=float, default=11.0)
    p.add_argument("--max-len", type=int, default=16384)
    a = p.parse_args()
    deadline = time.time() + a.hours * 3600
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    repo = setup_bench()
    endpoint = start_vllm(a.model, a.max_len)
    py, pipe = repo / ".venv/bin/python", HERE / "benchcad_codeedit_pipeline.py"
    common = (f"{py} {pipe} {{stage}} --bench {repo} --data {repo}/CodeEdit/data --split {HERE}/benchcad-codeedit-split.json "
              f"--endpoint {endpoint} --model {a.model} --workers 6 --max-tokens 4096 --exec-timeout 120")
    stages = [
        ("gepa", common.format(stage="gepa") + f" --part train --val-part validation --train-n 40 --val-n 20 --gepa-budget 160 "
                                                 f"--minibatch 4 --k 2 --budget 3 --out {OUT}/gepa", 4.0),
        ("test", common.format(stage="eval") + f" --part test --k 3 --budget 6 "
                                                 f"--repair-prompt {OUT}/gepa/repair_prompt.txt --out {OUT}/test", 4.0),
    ]
    for name, cmd, need_h in stages:
        left = (deadline - time.time()) / 3600
        if left < 0.3 or ("gepa/repair_prompt.txt" in cmd and not (OUT / "gepa/repair_prompt.txt").exists()):
            print(f"SKIP {name}: {left:.1f} h left", flush=True)
            continue
        print(f"STAGE {name} ({left:.1f} h left)", flush=True)
        try:
            subprocess.run(cmd, shell=True, check=True, timeout=max(600, int(min(left - 0.25, need_h * 1.6) * 3600)))
        except subprocess.TimeoutExpired:
            print(f"STAGE {name} timed out; partial results kept", flush=True)
        except subprocess.CalledProcessError as e:
            print(f"STAGE {name} failed: {e}", flush=True)
        pack()
    summaries = {d.name: json.loads((d / "summary.json").read_text()) for d in OUT.iterdir() if (d / "summary.json").exists()}
    for name, s in summaries.items():
        print(name, {k: v for k, v in s.items() if k != "repair_prompt"}, flush=True)
    shutil.rmtree(WORK / "vllm-env", ignore_errors=True)


if __name__ == "__main__":
    main()
