"""Score answers on Parametric CAD Bench v3 (gnucleus-ai/cad-bench@v3) with the task's own verifier.

v3 pins gnucleus-freecad-validator==0.6.0 (v2 geometry scorer) on FreeCAD 1.1.0 with OCP 7.9.3.1 and numpy 2.4.6,
plus pyvista 0.48.4 for the drawing tasks. Locally this is tmp/cadbench/fc-venv-060 built from the FreeCAD 1.1.0
macOS app's Python (OCCT 7.8.1 inside FreeCAD; the official image is conda-forge). Each task's tests/run_scorer.py
is called with the arguments of its tests/test.sh:

  create (30)        --reference REF.FCStd --candidate answer.FCStd
  drawing (40)       --reference REF.FCStd --candidate answer.FCStd
  create+edit (30)   --reference-base/--reference-target REF --candidate-base/--candidate-target answer_{base,edit}
                     (the scorer combines both by harmonic mean)

A missing candidate or a scorer crash scores 0, as in test.sh.

  python cadbench_v3_eval.py oracle [--workers 6]        references as answers: verifies the local verifier (~1.0)
  python cadbench_v3_eval.py score --answers DIR --name NAME    DIR/<task>/answer.FCStd or answer_{base,edit}.FCStd
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "tmp/cadbench"
TASKS = BENCH / "harbor-tasks-v3/cad-bench"
PYTHON = BENCH / "fc-venv-060/bin/python"
FREECAD_LIB = BENCH / "FreeCAD.app/Contents/Resources/lib"
OUT = ROOT / "runs/cadbench-v3"


def kind(task: Path) -> str:
    text = (task / "tests/test.sh").read_text()
    if "--reference-base" in text:
        return "create+edit"
    return "drawing" if "render" in (task / "tests/Dockerfile").read_text() else "create"


def score_task(task: Path, answers: Path | None) -> dict:
    k = kind(task)
    grader = task / "tests/grader"
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        if k == "create+edit":
            files = {"answer_base.FCStd": grader / "reference_base.FCStd", "answer_edit.FCStd": grader / "reference_target.FCStd"}
        else:
            files = {"answer.FCStd": grader / "reference.FCStd"}
        for name, ref in files.items():
            src = ref if answers is None else answers / task.name / name
            if not src.exists() or src.is_symlink():
                return dict(task=task.name, kind=k, reward=0.0, reason=f"missing or symlinked {name}")
            shutil.copy(src, d / name)
        if (grader / "param_check.py").exists():
            os.symlink(grader / "param_check.py", d / "param_check.py")
        args = (["--reference-base", str(grader / "reference_base.FCStd"), "--reference-target", str(grader / "reference_target.FCStd"),
                 "--candidate-base", str(d / "answer_base.FCStd"), "--candidate-target", str(d / "answer_edit.FCStd")]
                if k == "create+edit" else ["--reference", str(grader / "reference.FCStd"), "--candidate", str(d / "answer.FCStd")])
        args += ["--spec", str(grader / "spec.json"), "--reward-txt", str(d / "reward.txt"), "--reward-json", str(d / "reward.json")]
        env = dict(os.environ, FREECAD_LIB=str(FREECAD_LIB), PYTHONPATH=str(FREECAD_LIB))
        try:
            r = subprocess.run([str(PYTHON), str(task / "tests/run_scorer.py"), *args], capture_output=True, text=True, timeout=900,
                               cwd=d, env=env)
            reward = json.loads((d / "reward.json").read_text()) if (d / "reward.json").exists() else {}
            if r.returncode != 0 or "reward" not in reward:
                return dict(task=task.name, kind=k, reward=0.0, reason="scorer crashed: " + r.stderr[-300:])
            return dict(task=task.name, kind=k, **reward)
        except subprocess.TimeoutExpired:
            return dict(task=task.name, kind=k, reward=0.0, reason="scorer timeout")


def run(answers: Path | None, name: str, workers: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = sorted(p for p in TASKS.iterdir() if (p / "task.toml").exists())
    rows = []
    with ThreadPoolExecutor(workers) as pool:
        for n, fut in enumerate(as_completed([pool.submit(score_task, t, answers) for t in tasks]), 1):
            rows.append(fut.result())
            if n % 10 == 0:
                print("SCORED", n, "/", len(tasks), flush=True)
    (OUT / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in sorted(rows, key=lambda r: r["task"])))
    by = {}
    for r in rows:
        by.setdefault(r["kind"], []).append(r["reward"])
    summary = dict(name=name, overall=round(100 * sum(r["reward"] for r in rows) / len(tasks), 2),
                   **{k: dict(n=len(v), mean=round(100 * sum(v) / len(v), 2)) for k, v in sorted(by.items())},
                   failures=[r for r in rows if r["reward"] == 0][:5])
    (OUT / f"{name}-summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k != "failures"}))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("oracle", "score"))
    p.add_argument("--answers", type=Path)
    p.add_argument("--name", default="oracle")
    p.add_argument("--workers", type=int, default=6)
    a = p.parse_args()
    run(None if a.cmd == "oracle" else a.answers, "oracle" if a.cmd == "oracle" else a.name, a.workers)


if __name__ == "__main__":
    main()
