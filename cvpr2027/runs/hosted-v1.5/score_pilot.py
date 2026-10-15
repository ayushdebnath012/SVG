"""Provisional score of finished hosted-run tasks (local; uses the v1.5 evaluator). Usage: score_pilot.py RUN_ID"""
import json, subprocess, sys, tempfile
from pathlib import Path
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


run = sys.argv[1]
pkg = Path.home() / "SVG/cadfem-bench-v1.5"
base = Path(__file__).resolve().parent / "runs"
sub = base / "submissions" / run
refs = {json.loads(l)["task_id"]: l for l in (pkg / "evaluator/references.jsonl").read_text().splitlines()}
tasks = {json.loads(l)["task_id"]: l for l in (pkg / "candidate/tasks.jsonl").read_text().splitlines()}
view, nested = normalized(sub) if sub.exists() else (sub, [])
done = sorted(p.name for p in view.iterdir() if p.is_dir()) if sub.exists() else []
results = {p.parent.name: json.loads(p.read_text()) for p in (base / run).glob("*/result.json")}
if done:
    d = Path(tempfile.mkdtemp())
    import shutil
    shutil.copytree(pkg / "evaluator/evidence/geometry", d / "evidence/geometry")    # the scorer resolves geometry references next to the refs file
    (d / "r.jsonl").write_text("\n".join(refs[t] for t in done) + "\n"); (d / "t.jsonl").write_text("\n".join(tasks[t] for t in done) + "\n")
    subprocess.run([str(Path(__file__).resolve().parents[2] / "tmp/cq-env/bin/python"), str(pkg / "evaluator/score.py"), "--refs", str(d / "r.jsonl"), "--tasks", str(d / "t.jsonl"),
                    "--submissions", str(view), "--run-id", run, "--out", str(d / "s.json")], capture_output=True, text=True, check=True)
    rows = {r["task_id"]: r for r in json.loads((d / "s.json").read_text())["tasks"]}
else:
    rows = {}
tot = 0.0
for tid in sorted(results):
    res, r = results[tid], rows.get(tid)
    tot += res.get("cost_usd", 0)
    ref = json.loads(refs[tid])["references"]
    try:
        outs = json.loads((view / tid / "results.json").read_text())["outputs"]
        det = ", ".join(f"{k} {100 * (outs[k] / v['value'] - 1):+.1f}% (tol {100 * v['tol']['value']:.0f}%)" for k, v in ref.items() if k in outs and v["value"])
    except Exception:
        det = "no valid results.json"
    verdict = "PASS" if r and r["numerical_passed"] else "fail"
    geo = r.get("geometry_check", {}) if r else {}
    g = "" if not geo else (" geometry OK" if geo.get("ok") else f" geometry FAIL ({geo.get('error', geo.get('relative_symmetric_difference'))})")
    print(f"{tid:28s} {verdict} {det}{g}{' [outputs in <task_id>/ subfolder]' if tid in nested else ''} | calls={res['tool_calls']} {res['generation_seconds'] / 60:.1f}min ${res.get('cost_usd', 0):.2f}")
print(f"total spent on this run: ${tot:.2f}")
