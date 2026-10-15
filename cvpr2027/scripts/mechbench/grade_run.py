"""Grade every task of an agent-harness run on MechDesign-Bench (replayed outputs + the submitted code).

  tmp/cq-env/bin/python scripts/mechbench/grade_run.py --run runs/mechbench-astra/runs/<run-id> \
      [--package output/datasets/mechdesign-bench-v0.1]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import grade as G  # noqa: E402

ROOT = HERE.parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--package", type=Path, default=ROOT / "output/datasets/mechdesign-bench-v0.1")
    a = ap.parse_args()
    specs = {s["task_id"]: s for s in map(json.loads, (a.package / "evaluator/specs.jsonl").read_text().splitlines())}
    rows = []
    for d in sorted(p for p in a.run.iterdir() if p.is_dir() and p.name in specs):
        res = json.loads((d / "result.json").read_text()) if (d / "result.json").is_file() else {}
        out, code = d / "replay/output", d / "replay/submission"
        if not (out / "assembly.json").is_file():
            r = dict(task_id=d.name, passed=False, checks={"files": dict(ok=False, problems=["no replayed assembly.json"])})
        else:
            r = G.grade(specs[d.name], out, sys.executable, True, code)
        r["agent_status"] = res.get("status")
        r["tool_calls"] = res.get("tool_calls")
        r["cost_usd"] = res.get("cost_usd")
        (d / "grade.json").write_text(json.dumps(r, indent=1, default=float) + "\n")
        rows.append(r)
        print(d.name, "PASSED" if r["passed"] else "failed", {k: v.get("ok") for k, v in r["checks"].items()}, flush=True)
    (a.run / "grades.json").write_text(json.dumps(rows, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
