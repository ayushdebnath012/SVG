"""CADFEM-Bench v1 grader.

  python score.py --refs evaluator/references.jsonl --submissions runs/<model> [--simjeb-results results.jsonl] [--out score.json]

Submissions: <dir>/<task_id>/results.json = {"outputs": {key: value, ...}}; track B/C also <dir>/<task_id>/part.step.
A task passes when every graded output is within its tolerance and, where a reference geometry exists, the
submitted part.step matches it (volume and sorted bounding-box extents within rel_tol; needs OCP).
Track C (SimJEB design/redesign/lighten) is judged by scripts/simjeb_bench.py evaluate; pass its results.jsonl here.
Aggregates: pass rate per task, per family, and the family macro-average per track and tier (large parametric
families do not dominate). Missing answers count as failures.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path


def within(pred, ref: dict) -> tuple[bool, float | None]:
    t = ref["tol"]
    if t["kind"] == "bool":
        return (isinstance(pred, bool) and pred == ref["value"]), None
    try:
        p = float(pred)
    except (TypeError, ValueError):
        return False, None
    if not math.isfinite(p):
        return False, None
    v = float(ref["value"])
    if t["kind"] == "abs":
        err = abs(p - v)
        return err <= t["value"], err
    off = t.get("offset", 0.0) if t["kind"] == "rel_offset" else 0.0
    err = abs(p - v) / max(abs(v - off), 1e-300)
    return err <= t["value"], err


def geometry(step: Path, chk: dict) -> tuple[bool, dict]:
    try:
        from OCP.BRepGProp import BRepGProp
        from OCP.GProp import GProp_GProps
        from OCP.STEPControl import STEPControl_Reader
        from OCP.Bnd import Bnd_Box
        from OCP.BRepBndLib import BRepBndLib
    except ImportError:
        return False, dict(error="OCP not available for the geometry check")
    if not step.exists():
        return False, dict(error="part.step missing")
    r = STEPControl_Reader()
    if r.ReadFile(str(step)) != 1:
        return False, dict(error="unreadable STEP")
    r.TransferRoots()
    s = r.OneShape()
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(s, g)
    b = Bnd_Box()
    BRepBndLib.AddOptimal_s(s, b, False, False)
    x0, y0, z0, x1, y1, z1 = b.Get()
    ext = sorted([x1 - x0, y1 - y0, z1 - z0])
    ref_ext = sorted(chk["bbox_extent_mm"])
    dv = abs(g.Mass() - chk["volume_mm3"]) / chk["volume_mm3"]
    de = max(abs(a - b_) / b_ for a, b_ in zip(ext, ref_ext))
    return dv <= chk["rel_tol"] and de <= chk["rel_tol"], dict(volume_rel_err=dv, extent_rel_err=de)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs", required=True)
    ap.add_argument("--submissions", required=True)
    ap.add_argument("--simjeb-results")
    ap.add_argument("--out")
    ap.add_argument("--tasks", help="optional file with one task_id per line to restrict scoring")
    a = ap.parse_args()
    refs = [json.loads(x) for x in open(a.refs)]
    if a.tasks:
        keep = set(Path(a.tasks).read_text().split())
        refs = [r for r in refs if r["task_id"] in keep]
    sim = {}
    if a.simjeb_results:
        for x in open(a.simjeb_results):
            v = json.loads(x)
            sim[v["id"]] = v
    sub = Path(a.submissions)
    per_task = []
    for r in refs:
        tid = r["task_id"]
        rec = dict(task_id=tid, track=r["track"], tier=r["tier"], family=r["family"])
        if r["grader"] == "simjeb":
            v = sim.get(r["simjeb_task_id"])
            rec.update(passed=bool(v and v.get("success")), score=float(v.get("score", 0.0)) if v else 0.0,
                       detail="not evaluated" if v is None else {k: v.get(k) for k in ("valid", "passed", "mass_kg", "safety_factor", "violations")})
            per_task.append(rec)
            continue
        f = sub / tid / "results.json"
        outs = {}
        if f.exists():
            try:
                outs = json.loads(f.read_text()).get("outputs", {})
            except json.JSONDecodeError:
                outs = {}
        checks = {}
        for k, ref in r["references"].items():
            if not ref.get("graded", True):
                continue
            ok, err = within(outs.get(k), ref)
            checks[k] = dict(ok=ok, rel_err=err, pred=outs.get(k), ref=ref["value"], tol=ref["tol"])
        geo_ok = True
        if r.get("geometry_check"):
            geo_ok, gd = geometry(sub / tid / "part.step", r["geometry_check"])
            checks["_geometry"] = dict(ok=geo_ok, **gd)
        n_ok = sum(c["ok"] for k, c in checks.items() if not k.startswith("_"))
        n = sum(1 for k in checks if not k.startswith("_"))
        rec.update(passed=bool(checks) and all(c["ok"] for c in checks.values()), score=(n_ok / n if n else 0.0) * (1.0 if geo_ok else 0.5),
                   answered=f.exists(), checks=checks)
        per_task.append(rec)

    def agg(rows):
        fam = defaultdict(list)
        for x in rows:
            fam[x["family"]].append(x)
        fam_rates = {k: sum(y["passed"] for y in v) / len(v) for k, v in fam.items()}
        return dict(tasks=len(rows), passed=sum(x["passed"] for x in rows),
                    pass_rate=sum(x["passed"] for x in rows) / len(rows) if rows else None,
                    mean_output_score=sum(x["score"] for x in rows) / len(rows) if rows else None,
                    family_macro_pass_rate=sum(fam_rates.values()) / len(fam_rates) if fam_rates else None)

    groups = defaultdict(list)
    for x in per_task:
        groups[("all", "all")].append(x)
        groups[(f"track {x['track']}", "all")].append(x)
        groups[(f"track {x['track']}", x["tier"])].append(x)
        groups[("family", x["family"])].append(x)
    summary = {f"{k[0]} / {k[1]}": agg(v) for k, v in sorted(groups.items())}
    res = dict(summary=summary, tasks=per_task)
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1, default=str))
    for k, v in summary.items():
        if not k.startswith("family"):
            print(f"{k:28s} tasks {v['tasks']:4d}  pass {v['passed']:4d}  rate {v['pass_rate']:.3f}  family-macro {v['family_macro_pass_rate']:.3f}")


if __name__ == "__main__":
    main()
