"""Score the CADFEM-Bench v1.5 open-weight runs (local machine; references never leave it).

Pulls runs/<run>/<task>/result.json, transcripts and submissions/<run>/ from the GPU host, then scores them with
evaluator/score.py from the released package: the primary suite (candidate/tasks.jsonl) and the calibration suite
separately. No trusted workflow review exists for these runs, so `passed` and `workflow_verified` stay false by design.
The summary reports numerical accuracy, execution, artifact completeness, STEP validity and, for track B, the geometry gate.

  python score_openweight.py --runs gpt-oss-120b-high gpt-oss-20b-high qwen3.8-27b [--no-pull]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PKG = Path.home() / "SVG/cadfem-bench-v1.5"
OUT = Path(__file__).resolve().parents[3] / "runs/openweight-v1.5"
PYEVAL = Path(__file__).resolve().parents[3] / "tmp/cq-env/bin/python"      # the scorer's STEP/geometry checks need OpenCASCADE (OCP)
HOST = "trishita@10.71.9.40"
REMOTE = "cadfem-bench-run"
SSH = "ssh -o ControlPath=/tmp/claude-501/h100.sock"


def jl(p: Path) -> list:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def pull(run: str) -> None:
    for sub in (f"{REMOTE}/runs/{run}/", f"{REMOTE}/runs/submissions/{run}/"):
        dst = OUT / sub.split("runs/", 1)[1]
        dst.mkdir(parents=True, exist_ok=True)
        subprocess.run(["rsync", "-a", "--exclude", "work/", "--exclude", "replay/output/", "--exclude", "inputs/", "-e", SSH, f"{HOST}:{sub}", str(dst) + "/"], check=True)


def normalized(sub: Path) -> tuple[Path, list]:
    """Score <task_id>/ folders as submitted. The candidate README says "submit a directory named by task_id", so a
    main.py that writes into CADFEM_OUTPUT_DIR/<task_id>/ is accepted when that folder holds results.json and the task
    folder itself does not. Applied identically to every model; the affected tasks are reported."""
    import shutil, tempfile
    view, nested = Path(tempfile.mkdtemp()), []
    for d in sorted(p for p in sub.iterdir() if p.is_dir()):
        src = d
        if not (d / "results.json").is_file() and (d / d.name / "results.json").is_file():
            src = d / d.name
            nested.append(d.name)
        shutil.copytree(src, view / d.name, ignore=shutil.ignore_patterns(d.name) if src == d else None)
        if src != d and (d / "main.py").is_file() and not (view / d.name / "main.py").exists():
            shutil.copy2(d / "main.py", view / d.name / "main.py")
    return view, nested


def score(run: str, suite: str) -> dict:
    if suite == "primary":
        refs, tasks = PKG / "evaluator/references.jsonl", PKG / "candidate/tasks.jsonl"
    else:
        refs, tasks = PKG / f"evaluator/suites/{suite}/references.jsonl", PKG / f"evaluator/suites/{suite}/tasks.jsonl"
    out = OUT / "scores" / f"{run}-{suite}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    rid = run if suite == "primary" else f"{run}-{suite}"          # run_all.sh runs each suite under its own run id
    view, nested = normalized(OUT / "submissions" / rid)
    p = subprocess.run([str(PYEVAL), str(PKG / "evaluator/score.py"), "--refs", str(refs), "--tasks", str(tasks),
                        "--submissions", str(view), "--run-id", rid, "--out", str(out)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr[-2000:]
    res = json.loads(out.read_text())
    res["outputs_in_task_subfolder"] = nested
    out.write_text(json.dumps(res, indent=2) + "\n")
    return res


def summarize(run: str, suite: str, sc: dict) -> dict:
    ids = {r["task_id"] for r in sc["tasks"]}
    res = {}
    for f in (OUT / (run if suite == "primary" else f"{run}-{suite}")).glob("*/result.json"):
        r = json.loads(f.read_text())
        if r["task_id"] in ids:
            res[r["task_id"]] = r
    rows = sc["tasks"]
    n = len(rows)
    fam = collections.defaultdict(list)
    for r in rows:
        fam[r["engineering_family"]].append(r)
    complete = [r for r in rows if not any(e.startswith("missing/unsafe/empty artifact") for e in r["errors"])]
    b = [r for r in rows if r["track"] == "B"]
    validation = json.loads((PKG / 'evaluator/validation.json').read_text())
    task_file = PKG / ('candidate/tasks.jsonl' if suite == 'primary' else f'evaluator/suites/{suite}/tasks.jsonl')
    execution_ids = {k for k, x in res.items() if x.get('execution_verified') is True}
    return dict(run=run, suite=suite, dataset_version=validation['version'],
                scored_task_set_sha256=hashlib.sha256(task_file.read_bytes()).hexdigest(),
                generation_dataset_provenance='not independently verified by this scoring script',
                tasks=n, ran=len(res), unattempted=max(0,n-len(res)),
                submitted=sum(x["status"] == "submitted" for x in res.values()),
                replay_execution_verified=sum(bool(x.get("execution_verified")) for x in res.values()),
                all_artifacts=len(complete),
                valid_step=sum("submitted_solids" in r for r in rows),
                geometry_gate_passed=f"{sum(bool(r.get('geometry_check', {}).get('ok')) for r in b)}/{len(b)}",
                numerical_passed=sum(r["numerical_passed"] for r in rows),
                numerical_passed_after_verified_replay=sum(r['numerical_passed'] and r['task_id'] in execution_ids for r in rows),
                numerical_pass_rate=round(sum(r["numerical_passed"] for r in rows) / n, 3) if n else None,
                mean_output_score=round(sum(r["numerical_score"] for r in rows) / n, 3) if n else None,
                family_macro_numerical_pass_rate=round(sum(sum(x["numerical_passed"] for x in g) / len(g) for g in fam.values()) / len(fam), 3) if fam else None,
                by_family={k: f"{sum(x['numerical_passed'] for x in g)}/{len(g)}" for k, g in sorted(fam.items())},
                prompt_tokens=sum(x["usage"]["prompt_tokens"] for x in res.values()),
                completion_tokens=sum(x["usage"]["completion_tokens"] for x in res.values()),
                generation_hours=round(sum(x["generation_seconds"] for x in res.values()) / 3600, 2),
                workflow_verified=sum(r['workflow_verified'] for r in rows),
                passed=sum(r['passed'] for r in rows),
                hardware_timing_comparable=False,
                timing_note='Descriptive timing only: dedicated GPU allocation and identical resource conditions have not been verified.',
                note="Numerical pass and successful replay do not establish a verified workflow. Historical v1.5 runs are separate from corrected dataset comparisons.")


def main() -> None:
    global PKG, OUT, PYEVAL
    ap = argparse.ArgumentParser()
    ap.add_argument('--package', type=Path, default=PKG, help='Exact frozen dataset to score; historical default is v1.5')
    ap.add_argument('--out', type=Path, default=OUT, help='Existing local run/submission directory')
    ap.add_argument('--python-eval', type=Path, default=PYEVAL, help='Trusted Python with OpenCASCADE for STEP checks')
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--no-pull", action="store_true")
    a = ap.parse_args()
    PKG, OUT = a.package.resolve(), a.out.resolve()
    PYEVAL = a.python_eval.resolve()
    allsum = []
    for run in a.runs:
        if not a.no_pull:
            pull(run)
            pull(f"{run}-calibration")
        for suite in ("primary", "calibration"):
            s = summarize(run, suite, score(run, suite))
            allsum.append(s)
            print(json.dumps({k: v for k, v in s.items() if k != "by_family"}))
    (OUT / "summary.json").write_text(json.dumps(allsum, indent=1) + "\n")


if __name__ == "__main__":
    main()
