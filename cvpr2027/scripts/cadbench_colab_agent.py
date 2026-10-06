"""Open models on Parametric CAD Bench v2 with an execution-feedback repair loop (runs on a Colab GPU).

Round 0 sends each task's verbatim Harbor instruction.md plus one line asking for the complete answer.py.
Every script is executed by conda-forge FreeCAD 1.1.0 (the official verifier runtime). A failed attempt --
a Python error, no answer.FCStd next to the script, or a document that violates the instruction's single
PartDesign Body / editable feature-tree requirement (the public validator's integrity gates, which read only
the candidate) -- is returned to the model with the error text for up to --repairs further rounds. Neither
the reference part nor the grader's spec/param_check files are used before final scoring. Greedy decoding.
The literal Harbor path /app/answer.FCStd is mapped to the task folder, where /app does not exist.

  run   : generate + execute + repair for one model, all tasks batched per round through vLLM
  score : score the final answers with each task's tests/run_scorer.py (gnucleus-freecad-validator 0.4.0)
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

ASK = "\n\nReply with the complete contents of answer.py in a single ```python code block and nothing else."
FIX = "Fix the script. Reply with the complete corrected answer.py in a single ```python code block and nothing else."
GATE = '''import json, sys
import FreeCAD
from freecad_validator.comparators.integrity_gates import partdesign_body_gate, partdesign_feature_tree_gate
doc = FreeCAD.openDocument(sys.argv[1])
try:
    print(json.dumps({"reason": partdesign_body_gate(doc) or partdesign_feature_tree_gate(doc)}))
finally:
    FreeCAD.closeDocument(doc.Name)
'''


def extract_code(text: str) -> str | None:
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.S)
    if blocks:
        return max(blocks, key=len)
    opened = re.search(r"```(?:python|py)?\s*\n(.*)", text, re.S)  # unclosed fence, e.g. a reply cut at the cap
    if opened:
        return opened.group(1)
    return text if "import FreeCAD" in text else None


def execute(folder: Path, code: str, fc_python: str, env: dict) -> dict:
    """Run one answer.py with FreeCAD; return {ok, feedback, status}."""
    script, fcstd = folder / "answer.py", folder / "answer.FCStd"
    for stale in (fcstd, folder / "_run.FCStd"):
        stale.unlink(missing_ok=True)
    script.write_text(code)
    runnable = folder / "_run.py"
    runnable.write_text(code.replace("/app/answer.FCStd", str(fcstd)).replace("/app/answer.py", str(script)))
    try:
        proc = subprocess.run([fc_python, runnable.name], cwd=folder, capture_output=True, text=True, timeout=120, env=env)
    except subprocess.TimeoutExpired:
        return dict(ok=False, status="timeout", feedback="Running answer.py with FreeCAD 1.1.0 did not finish within "
                    "120 seconds.")
    if (folder / "_run.FCStd").exists() and not fcstd.exists():
        (folder / "_run.FCStd").rename(fcstd)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout)[-2500:]
        return dict(ok=False, status="script_error",
                    feedback=f"I ran answer.py with FreeCAD 1.1.0 and it failed:\n```\n{tail}\n```")
    if not fcstd.exists():
        return dict(ok=False, status="no_fcstd", feedback="answer.py ran, but no answer.FCStd was written next to the "
                    "script. Derive the output path from __file__ and save the document there.")
    gate = folder / "_gate.py"
    gate.write_text(GATE)
    proc = subprocess.run([fc_python, gate.name, str(fcstd)], cwd=folder, capture_output=True, text=True, timeout=120,
                          env=env)
    try:
        reason = json.loads(proc.stdout.strip().splitlines()[-1])["reason"]
    except Exception:  # noqa: BLE001 - an unreadable document is a failure
        reason = "the saved answer.FCStd could not be opened: " + proc.stderr[-800:]
    if reason:
        return dict(ok=False, status="gate_failed", feedback=f"answer.py ran, but the saved model violates the task "
                    f"requirements: {reason}")
    return dict(ok=True, status="ok", feedback=None)


def run(tasks: Path, out: Path, model: str, tag: str, repairs: int, fc_python: str, workers: int,
        max_model_len: int, max_tokens: int, gpu_util: float) -> None:
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    env = dict(os.environ)
    ids = sorted(p.name.removeprefix("freecad-") for p in tasks.glob("freecad-*"))
    root = out / tag
    root.mkdir(parents=True, exist_ok=True)
    (root / "protocol.json").write_text(json.dumps(dict(model=model, repairs=repairs, decoding="greedy",
                                                        max_tokens=max_tokens, max_model_len=max_model_len,
                                                        ask=ASK, fix=FIX, tasks=len(ids)), indent=2) + "\n")
    tokenizer = AutoTokenizer.from_pretrained(model)
    llm = LLM(model=model, max_model_len=max_model_len, gpu_memory_utilization=gpu_util, seed=0)
    params = SamplingParams(temperature=0.0, max_tokens=max_tokens)
    state = {tid: dict(instruction=(tasks / f"freecad-{tid}" / "instruction.md").read_text(), history=[],
                       done=False) for tid in ids}
    rounds = []
    for r in range(repairs + 1):
        active = [tid for tid in ids if not state[tid]["done"]]
        if not active:
            break
        prompts = []
        for tid in active:
            s = state[tid]
            messages = [dict(role="user", content=s["instruction"] + ASK)]
            if s["history"]:  # compact repair context: original task, last script, last feedback
                last = s["history"][-1]
                messages += [dict(role="assistant", content=last["reply"]),
                             dict(role="user", content=last["feedback"] + "\n\n" + FIX)]
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            if len(tokenizer(prompt).input_ids) + max_tokens > max_model_len:
                messages = messages[:1]
                prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            prompts.append(prompt)
        started = time.perf_counter()
        outputs = [o.outputs[0] for o in llm.generate(prompts, params)]
        replies = [o.text for o in outputs]
        truncated = [o.finish_reason == "length" for o in outputs]
        gen_seconds = time.perf_counter() - started

        def attempt(item):
            tid, reply, cut = item
            folder = root / tid
            folder.mkdir(exist_ok=True)
            code = extract_code(reply)
            result = execute(folder, code, fc_python, env) if code else dict(
                ok=False, status="no_code", feedback="Your reply contained no python code block.")
            if cut and not result["ok"]:
                result["feedback"] = (f"Your reply was cut off at the {max_tokens}-token limit, so answer.py is "
                                      "incomplete; write a shorter script without repeated lines.\n" + result["feedback"])
            return tid, reply, cut, result
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for tid, reply, cut, result in pool.map(attempt, zip(active, replies, truncated)):
                s = state[tid]
                s["history"].append(dict(round=r, reply=reply, truncated=cut, status=result["status"],
                                         feedback=result["feedback"]))
                s["done"] = result["ok"]
        ok = sum(state[t]["done"] for t in ids)
        rounds.append(dict(round=r, attempted=len(active), passing_total=ok, gen_seconds=round(gen_seconds, 1)))
        print(f"{tag} round {r}: attempted {len(active)}, passing execution+gates {ok}/{len(ids)}, "
              f"generation {gen_seconds:.0f}s", flush=True)
    for tid, s in state.items():
        folder = root / tid
        folder.mkdir(exist_ok=True)
        (folder / "transcript.json").write_text(json.dumps(dict(passed=s["done"], attempts=s["history"]), indent=2))
    (root / "rounds.json").write_text(json.dumps(rounds, indent=2) + "\n")


def score(tasks: Path, out: Path, tag: str, fc_python: str, workers: int) -> dict:
    root = out / tag
    ids = sorted(p.name.removeprefix("freecad-") for p in tasks.glob("freecad-*"))
    env = dict(os.environ)

    def one(tid):
        task, folder = tasks / f"freecad-{tid}", root / tid
        row = dict(task=tid, combined=0.0, geometry=0.0, spec=0.0, status="missing_candidate")
        if (folder / "answer.FCStd").exists():
            proc = subprocess.run([fc_python, str(task / "tests/run_scorer.py"), "--reference",
                                   str(task / "tests/grader/reference.FCStd"), "--candidate", str(folder / "answer.FCStd"),
                                   "--spec", str(task / "tests/grader/spec.json"), "--reward-txt",
                                   str(folder / "reward.txt"), "--reward-json", str(folder / "reward.json")],
                                  capture_output=True, text=True, timeout=600, env=env)
            details = folder / "reward_details.json"
            if proc.returncode == 0 and details.exists():
                d = json.loads(details.read_text())
                row.update(combined=d["combined"], geometry=d["geometry_similarity"],
                           spec=d["cad_spec_consistency"], status="scored")
            else:
                row.update(status="scorer_error", error=proc.stderr[-400:])
        return row
    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(one, ids))
    n = len(rows)
    summary = dict(tag=tag, tasks=n, scored=sum(r["status"] == "scored" for r in rows),
                   mean_combined=sum(r["combined"] for r in rows) / n, mean_geometry=sum(r["geometry"] for r in rows) / n,
                   mean_spec=sum(r["spec"] for r in rows) / n, per_task={r["task"]: r for r in rows},
                   rounds=json.loads((root / "rounds.json").read_text()))
    (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_task"}, indent=1))
    return summary


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    s = sub.add_parser("score")
    for q in (r, s):
        q.add_argument("--tasks", type=Path, required=True)
        q.add_argument("--out", type=Path, required=True)
        q.add_argument("--tag", required=True)
        q.add_argument("--fc-python", required=True)
        q.add_argument("--workers", type=int, default=8)
    r.add_argument("--model", required=True)
    r.add_argument("--repairs", type=int, default=3)
    r.add_argument("--max-model-len", type=int, default=16384)
    r.add_argument("--max-tokens", type=int, default=4096)
    r.add_argument("--gpu-util", type=float, default=0.88)
    a = p.parse_args()
    if a.cmd == "run":
        run(a.tasks, a.out, a.model, a.tag, a.repairs, a.fc_python, a.workers, a.max_model_len, a.max_tokens,
            a.gpu_util)
    else:
        score(a.tasks, a.out, a.tag, a.fc_python, a.workers)


if __name__ == "__main__":
    main()
