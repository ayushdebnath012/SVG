"""Single-shot open-model answers for Parametric CAD Bench v2: Harbor instruction -> answer.py -> answer.FCStd.

The model receives each task's verbatim instruction.md plus one line asking for the complete answer.py in a
single python code block (it has no shell, unlike the leaderboard agents). Each script is then executed by
FreeCAD 1.1.0 next to where it is saved; the literal Harbor path /app/answer.FCStd is mapped to the local
answer.FCStd because /app exists only in the Harbor container. Score with cadbench_eval.py.

  generate : write <out>/<task_id>/{answer.py,raw.txt}; --k > 1 writes sample-<j>/ subfolders
  execute  : run every answer.py with FreeCAD (120 s limit) and record exec.json
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tmp/cadbench/harbor-tasks/cad-bench"
FREECAD_PYTHON = ROOT / "tmp/cadbench/fc-venv/bin/python"
FREECAD_LIB = ROOT / "tmp/cadbench/FreeCAD.app/Contents/Resources/lib"
ASK = "\n\nReply with the complete contents of answer.py in a single ```python code block and nothing else."


def task_ids(limit: int | None = None, ids: str | None = None) -> list[str]:
    all_ids = sorted(p.name.removeprefix("freecad-") for p in TASKS.glob("freecad-*"))
    if ids:
        return [i for i in ids.split(",") if i in all_ids]
    return all_ids[:limit] if limit else all_ids


def extract_code(text: str) -> str | None:
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.S)
    if blocks:
        return max(blocks, key=len)
    opened = re.search(r"```(?:python|py)?\s*\n(.*)", text, re.S)  # unclosed fence, e.g. a reply cut at the cap
    if opened:
        return opened.group(1)
    return text if "import FreeCAD" in text else None


def generate(out: Path, model_id: str, adapter: str | None, limit: int | None, ids: str | None, k: int,
             temperature: float, max_new_tokens: int, device: str) -> None:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    dtype = torch.bfloat16 if device != "cpu" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype).to(device)
    if adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter)
    model.eval()
    out.mkdir(parents=True, exist_ok=True)
    (out / "protocol.json").write_text(json.dumps(dict(model=model_id, adapter=adapter, k=k, temperature=temperature,
                                                       max_new_tokens=max_new_tokens, device=device, prompt_suffix=ASK,
                                                       interaction="single-shot, no tool use"), indent=2) + "\n")
    for n, tid in enumerate(task_ids(limit, ids)):
        folder = out / tid
        if (folder / "raw.json").exists():
            continue
        instruction = (TASKS / f"freecad-{tid}" / "instruction.md").read_text()
        prompt = tokenizer.apply_chat_template([dict(role="user", content=instruction + ASK)], tokenize=False,
                                               add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to(device)
        started = time.perf_counter()
        with torch.inference_mode():
            kwargs = dict(do_sample=True, temperature=temperature, top_p=0.95) if k > 1 else dict(do_sample=False)
            outputs = model.generate(**inputs, max_new_tokens=max_new_tokens, num_return_sequences=k,
                                     pad_token_id=tokenizer.eos_token_id, **kwargs)
        texts = tokenizer.batch_decode(outputs[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)
        for j, text in enumerate(texts):
            target = folder if k == 1 else folder / f"sample-{j}"
            target.mkdir(parents=True, exist_ok=True)
            (target / "raw.txt").write_text(text)
            code = extract_code(text)
            if code:
                (target / "answer.py").write_text(code)
        (folder / "raw.json").write_text(json.dumps(dict(seconds=time.perf_counter() - started, samples=len(texts))))
        print(n + 1, tid, f"{time.perf_counter() - started:.0f}s", flush=True)


def execute(out: Path, workers: int) -> None:
    scripts = sorted(out.glob("*/answer.py")) + sorted(out.glob("*/sample-*/answer.py"))

    def run(script: Path):
        local = script.with_suffix(".FCStd")
        if local.exists():
            local.unlink()
        code = script.read_text().replace("/app/answer.FCStd", str(local)).replace("/app/answer.py", str(script))
        runnable = script.with_name("_run_answer.py")
        runnable.write_text(code)
        status = "ok"
        try:
            proc = subprocess.run([str(FREECAD_PYTHON), runnable.name], cwd=script.parent, capture_output=True, text=True,
                                  timeout=120, env=dict(os.environ, PYTHONPATH=str(FREECAD_LIB)))
            produced = runnable.with_suffix(".FCStd")
            if produced.exists() and not local.exists():
                produced.rename(local)
            if proc.returncode != 0:
                status = "script_error"
            if not local.exists():
                status = status if status != "ok" else "no_fcstd"
            tail = proc.stderr[-600:]
        except subprocess.TimeoutExpired:
            status, tail = "timeout", ""
        (script.parent / "exec.json").write_text(json.dumps(dict(status=status, fcstd=local.exists(), stderr=tail), indent=2))
        return status

    with ThreadPoolExecutor(max_workers=workers) as pool:
        statuses = list(pool.map(run, scripts))
    print({s: statuses.count(s) for s in set(statuses)}, "of", len(scripts))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--out", type=Path, required=True)
    g.add_argument("--model", default="Qwen/Qwen2.5-Coder-3B-Instruct")
    g.add_argument("--adapter")
    g.add_argument("--limit", type=int)
    g.add_argument("--ids")
    g.add_argument("--k", type=int, default=1)
    g.add_argument("--temperature", type=float, default=0.8)
    g.add_argument("--max-new-tokens", type=int, default=4096)
    g.add_argument("--device", default="mps")
    e = sub.add_parser("execute")
    e.add_argument("--out", type=Path, required=True)
    e.add_argument("--workers", type=int, default=4)
    a = p.parse_args()
    if a.cmd == "generate":
        generate(a.out, a.model, a.adapter, a.limit, a.ids, a.k, a.temperature, a.max_new_tokens, a.device)
    else:
        execute(a.out, a.workers)


if __name__ == "__main__":
    main()
