"""Score FreeCAD answers on Parametric CAD Bench v2 (gnucleus-ai/cad-bench@v2) exactly as its Harbor verifier does.

Each task's own tests/run_scorer.py is run with gnucleus-freecad-validator==0.4.0 (the version pinned in the
task's verifier Dockerfile, default settings: harmonic combine) against the task's held-back
tests/grader/{reference.FCStd, spec.json, param_check.py}. The candidate is <answers>/<task_id>/answer.FCStd.
A missing candidate or a scorer failure scores 0, as on the leaderboard. Local differences from the official
Linux verifier: FreeCAD 1.1.0 official macOS build (OCCT 7.8.1) instead of conda-forge (OCCT 7.9.3).

  score   : score every task, write <work>/summary.json (mean over all 100 tasks)
  compare : per-task agreement of a local score with the published reward of the same answers

Task suite: `uvx --from harbor harbor download gnucleus-ai/cad-bench@v2 -o tmp/cadbench/harbor-tasks`.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "tmp/cadbench"
TASKS = BENCH / "harbor-tasks/cad-bench"
PYTHON = BENCH / "fc-venv-040/bin/python"
FREECAD_LIB = BENCH / "FreeCAD.app/Contents/Resources/lib"


def task_ids() -> list[str]:
    return sorted(p.name.removeprefix("freecad-") for p in TASKS.glob("freecad-*") if (p / "tests/grader").is_dir())


def score_one(tid: str, answers: Path, work: Path) -> dict:
    task, out = TASKS / f"freecad-{tid}", work / tid
    out.mkdir(parents=True, exist_ok=True)
    candidate = answers / tid / "answer.FCStd"
    row = dict(task=tid, combined=0.0, geometry=0.0, spec=0.0, status="missing_candidate")
    if candidate.exists():
        proc = subprocess.run(
            [str(PYTHON), str(task / "tests/run_scorer.py"), "--reference", str(task / "tests/grader/reference.FCStd"),
             "--candidate", str(candidate), "--spec", str(task / "tests/grader/spec.json"),
             "--reward-txt", str(out / "reward.txt"), "--reward-json", str(out / "reward.json")],
            capture_output=True, text=True, timeout=600, env=dict(os.environ, FREECAD_LIB=str(FREECAD_LIB)))
        details = out / "reward_details.json"
        if proc.returncode == 0 and details.exists():
            d = json.loads(details.read_text())
            row.update(combined=d["combined"], geometry=d["geometry_similarity"], spec=d["cad_spec_consistency"],
                       status="scored")
        else:
            row.update(status="scorer_error", error=proc.stderr[-500:])
    (out / "row.json").write_text(json.dumps(row, indent=2) + "\n")
    return row


def score(answers: Path, work: Path, workers: int) -> dict:
    ids = task_ids()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(lambda t: score_one(t, answers, work), ids))
    n = len(rows)
    summary = dict(tasks=n, scored=sum(r["status"] == "scored" for r in rows),
                   statuses={s: sum(r["status"] == s for r in rows) for s in {r["status"] for r in rows}},
                   mean_combined=sum(r["combined"] for r in rows) / n, mean_geometry=sum(r["geometry"] for r in rows) / n,
                   mean_spec=sum(r["spec"] for r in rows) / n, validator="gnucleus-freecad-validator==0.4.0",
                   per_task={r["task"]: r for r in rows})
    (work / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_task"}, indent=1))
    return summary


def compare(work: Path, published: Path) -> None:
    local = json.loads((work / "summary.json").read_text())["per_task"]
    diffs, pub_mean = [], []
    for tid, row in local.items():
        path = published / f"freecad-{tid}" / "reward_details.json"
        if path.exists():
            p = json.loads(path.read_text())["combined"]
            pub_mean.append(p)
            diffs.append((round(abs(row["combined"] - p), 4), tid))
    diffs.sort(reverse=True)
    print(f"published mean {sum(pub_mean) / len(pub_mean):.6f}; tasks compared {len(diffs)}; "
          f"exact (<1e-4) {sum(d < 1e-4 for d, _ in diffs)}; within 0.01 {sum(d < 0.01 for d, _ in diffs)}; "
          f"largest {diffs[:5]}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score")
    s.add_argument("--answers", type=Path, required=True)
    s.add_argument("--work", type=Path, required=True)
    s.add_argument("--workers", type=int, default=4)
    c = sub.add_parser("compare")
    c.add_argument("--work", type=Path, required=True)
    c.add_argument("--published", type=Path, required=True)
    a = p.parse_args()
    if a.cmd == "score":
        score(a.answers, a.work, a.workers)
    else:
        compare(a.work, a.published)


if __name__ == "__main__":
    main()
