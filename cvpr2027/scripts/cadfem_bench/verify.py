"""Release verification for CADFEM-Bench v1.1 (run by release.py; read-only except a temporary probe directory).

Checks the audit findings on the built release: task/reference alignment, input and evidence hashes, validity of every
active CAD input, absence of locally computed (verifier) targets, leak scan, and scorer probes: answers-only and
perturbed submissions, malformed submissions, a fully reviewed submission, a tampered submission, and the rigging
geometry gate under rotation/translation (accept) and scaling (reject).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import common as C
from build import leak_scan

PY = sys.executable


def jl(p: Path) -> list:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def score(sub: Path, out: Path, reviews: Path | None = None) -> dict:
    cmd = [PY, str(C.EVAL / "score.py"), "--refs", str(C.EVAL / "references.jsonl"), "--tasks", str(C.CAND / "tasks.jsonl"),
           "--submissions", str(sub), "--run-id", "verify-run", "--out", str(out)]
    if reviews:
        cmd += ["--reviews", str(reviews)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr[-2000:]
    return json.loads(out.read_text())


def answers(refs: list, root: Path, scale: float = 1.0) -> None:
    for r in refs:
        outs = {}
        for k, v in r["references"].items():
            off = v["tol"].get("offset", 0.0)
            outs[k] = (off + (v["value"] - off) * scale) if not isinstance(v["value"], bool) else v["value"]
        (root / r["task_id"]).mkdir(parents=True, exist_ok=True)
        (root / r["task_id"] / "results.json").write_text(json.dumps(dict(outputs=outs)))


def transformed_step(src: Path, dst: Path, rot_z_deg: float = 0.0, shift=(0, 0, 0), scale: float = 1.0) -> None:
    import math
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt, gp_Trsf, gp_Vec
    s = C.read_shape(src)
    t = gp_Trsf()
    if scale != 1.0:
        t.SetScale(gp_Pnt(0, 0, 0), scale)
    r = gp_Trsf()
    r.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), math.radians(rot_z_deg))
    m = gp_Trsf()
    m.SetTranslation(gp_Vec(*shift))
    s = BRepBuilderAPI_Transform(s, m.Multiplied(r).Multiplied(t), True).Shape()
    C.write_step(s, dst)


def main() -> dict:
    tasks, refs = jl(C.CAND / "tasks.jsonl"), jl(C.EVAL / "references.jsonl")
    held_t = jl(C.OUT / "held/tasks.jsonl")
    v = {}
    assert [t["task_id"] for t in tasks] == [r["task_id"] for r in refs]
    assert len({t["task_id"] for t in tasks}) == len(tasks)
    assert all(t["status"] == r["status"] == "active" for t, r in zip(tasks, refs))
    assert not {t["task_id"] for t in tasks} & {t["task_id"] for t in held_t}
    v["tasks_active"], v["tasks_held"] = len(tasks), len(held_t)
    # inputs and CAD validity
    n_in, cad = 0, {}
    for t in tasks:
        for i in t["inputs"]:
            p = C.CAND / i["path"]
            assert p.exists() and C.sha256(p) == i["sha256"], i["path"]
            n_in += 1
            if p.suffix.lower() in (".step", ".stp", ".brep", ".brp"):
                cad.setdefault(i["sha256"], (p, []))[1].append(t["task_id"])
    invalid = [ids for h, (p, ids) in cad.items() if not C.shape_summary(C.read_shape(p))["valid"]]
    assert not invalid, invalid
    v.update(inputs_hash_checked=n_in, distinct_cad_files=len(cad), invalid_cad_files=0)
    for t in held_t:
        assert (C.OUT / "held/inputs" / t["task_id"]).exists() or not t["inputs"], t["task_id"]
    # evidence bundle
    man = jl(C.EVAL / "evidence-manifest.jsonl")
    for m in man:
        p = C.EVAL / m["path"]
        assert p.exists() and p.stat().st_size == m["bytes"] and C.sha256(p) == m["sha256"], m["path"]
    paths = {m["path"] for m in man}
    assert all(r["evidence_files"] and set(r["evidence_files"]) <= paths for r in refs)
    v.update(evidence_files=len(man), evidence_bytes=sum(m["bytes"] for m in man))
    # reference classes and the Tresca fix
    rc = Counter(x["ref_class"] for r in refs for x in r["references"].values())
    assert "verifier" not in rc, rc
    cw = next(r for r in refs if r["family"] == "cadworld-freecad-fem")
    assert "max_tresca_MPa" not in cw["references"] and "max_shear_stress_MPa" in cw["references"]
    v["reference_classes"] = dict(rc)
    validation = json.loads((C.EVAL / "validation.json").read_text())
    assert validation["reference_classes"] == dict(rc), "validation reference classes must describe active references"
    v["graded_outputs"] = sum(len(r["references"]) for r in refs)
    leaks = leak_scan(tasks, refs)
    assert not leaks, leaks[:5]
    v["leak_scan_hits"] = 0

    tmp = C.ROOT / "tmp/cadfem-bench-v1.1-verify"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    # 1. answers only: numerically right, never a pass
    answers(refs, tmp / "answers")
    s = score(tmp / "answers", tmp / "answers.json")["summary"]["all"]
    assert s["numerical_passed"] == len(refs) and s["passed"] == 0 and s["workflow_verified"] == 0, s
    # 2. perturbed answers
    answers(refs, tmp / "perturbed", 1.3)
    s2 = score(tmp / "perturbed", tmp / "perturbed.json")["summary"]["all"]
    assert s2["numerical_passed"] == 0, s2
    # 2b. independent converged answers pass where a convergence study set the tolerance
    fin = lambda x: x.get("independent_finest_mm", x.get("independent_finest"))
    conv = [r for r in refs if any(fin(v) is not None for v in r["references"].values())]
    if conv:
        for r in conv:
            for x in r["references"].values():
                assert x["tol"]["value"] >= x["source_protocol_tol"]["value"] if "source_protocol_tol" in x else True
        cdir = tmp / "converged"
        answers(conv, cdir)
        for r in conv:
            outs = {k: fin(x) if fin(x) is not None else x["value"] for k, x in r["references"].items()}
            (cdir / r["task_id"] / "results.json").write_text(json.dumps(dict(outputs=outs)))
        rows_c = {x["task_id"]: x for x in score(cdir, tmp / "converged.json")["tasks"]}
        bad_c = [r["task_id"] for r in conv if not rows_c[r["task_id"]]["numerical_passed"]]
        assert not bad_c, bad_c
    v["converged_value_probe"] = dict(tasks=len(conv), numerical_passed=len(conv),
                                     by_family=dict(Counter(r["family"] for r in conv)))
    # 3. malformed submissions are rejected per task, the run completes
    bad = tmp / "malformed"
    answers(refs, bad)
    ids = [r["task_id"] for r in refs[:4]]
    (bad / ids[0] / "results.json").write_text('{"outputs": null}')
    (bad / ids[1] / "results.json").write_text('{"outputs": {"x": "1.0"}}')
    (bad / ids[2] / "results.json").write_text('{"outputs": {"a": 1, "a": 2}}')
    (bad / ids[3] / "results.json").write_text('not json')
    res = score(bad, tmp / "malformed.json")
    rows = {x["task_id"]: x for x in res["tasks"]}
    assert all(not rows[i]["numerical_passed"] and any("invalid numerical submission" in e for e in rows[i]["errors"]) for i in ids)
    assert res["summary"]["all"]["numerical_passed"] == len(refs) - 4
    # 4. a fully reviewed submission passes; a tampered one does not
    tid = "A-CYC-Coupler-PETGCF"
    task = next(t for t in tasks if t["task_id"] == tid)
    good = tmp / "reviewed"
    answers([r for r in refs if r["task_id"] == tid], good)
    d = good / tid
    shutil.copy2(C.CAND / f"tasks/{tid}/part.step", d / "part.step")
    for name in ("main.py", "mesh.msh", "fields.npz", "solver.log", "refinement.json", "environment.json"):
        (d / name).write_text(f"probe artifact {name}\n")
    rev = tmp / "reviews.jsonl"
    subprocess.run([PY, str(C.EVAL / "prepare_review.py"), "--tasks", str(C.CAND / "tasks.jsonl"), "--task-id", tid,
                    "--submissions", str(good), "--run-id", "verify-run", "--out", str(rev)], check=True, capture_output=True,
                   cwd=C.EVAL)
    rec = json.loads(rev.read_text())
    rec["reviewer"] = "verify.py probe"
    for k in rec["evidence"]:
        rec[k] = True
        rec["evidence"][k] = "probe: positive-path test of the scorer, not a real review"
    rev.write_text(json.dumps(rec) + "\n")
    ok = {x["task_id"]: x for x in score(good, tmp / "reviewed.json", rev)["tasks"]}[tid]
    assert ok["passed"] and ok["workflow_verified"], ok
    (d / "solver.log").write_text("tampered after review\n")
    bad2 = {x["task_id"]: x for x in score(good, tmp / "tampered.json", rev)["tasks"]}[tid]
    assert not bad2["passed"] and any("hash" in e for e in bad2["errors"]), bad2
    # 5. rigging geometry gate: rotated + moved source CAD passes, a 3 % larger part fails
    sys.path.insert(0, str(C.EVAL))
    import importlib
    sc = importlib.import_module("score")
    geo = {}
    for rb in [r for r in refs if r.get("geometry_check")]:
        src = C.EVAL / rb["geometry_check"]["reference_step"]
        rot, big = tmp / f"{rb['task_id']}-rot.step", tmp / f"{rb['task_id']}-big.step"
        transformed_step(src, rot, 90.0, (40.0, -15.0, 7.0))
        transformed_step(src, big, 0.0, (0, 0, 0), 1.03)
        g_ok, g1 = sc.geometry(rot, rb["geometry_check"], C.EVAL)
        g_bad, g2 = sc.geometry(big, rb["geometry_check"], C.EVAL)
        assert g_ok and not g_bad, (rb["task_id"], g1, g2)
        geo[rb["task_id"]] = dict(rotated_moved=g1["relative_symmetric_difference"], scaled_103=g2.get("relative_symmetric_difference"),
                                  scaled_103_rejected_by=g2.get("error", "volume difference above the limit"))
    g1, g2 = ({"relative_symmetric_difference": geo["B-RIGGING-test1"]["rotated_moved"]},
              {"relative_symmetric_difference": geo["B-RIGGING-test1"]["scaled_103"]})
    v["geometry_gate_probes"] = geo
    v["scorer_probes"] = dict(answers_only=dict(numerical_passed=s["numerical_passed"], passed=s["passed"]),
                              perturbed_numerical_passed=s2["numerical_passed"], malformed_rejected_without_crash=4,
                              reviewed_probe_passed=True, tampered_probe_rejected=True,
                              rigging_rotated_moved=g1, rigging_scaled_103=g2)
    shutil.rmtree(tmp)
    return v


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
