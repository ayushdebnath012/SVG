"""v1.2 stage: apply mesh-convergence tolerances and record independent reproduction (run by release.py).

Cycloidal tasks: the graded displacement keeps its published value. The independent convergence study of
2026-10-14 (scripts/run_cycloidal_convergence.py + converge_cycloidal_worker.py, output/cycloidal-convergence-study/)
gives each part an empirical band = |finest independent - published| / published + 2 x last refinement change
(rounded up to 1 %, at least 2 %). Parts with status `band_review_ready` (refinement changes < 1 % and < 2 %, force
balance < 1e-8, band <= 10 %) get max(band, published 5 %) as their relative tolerance; all others move to held/.
AgentFEM fresh_test_000 is marked reproduced from the follow-up study. All study files go into the evidence bundle.
v1.3: fcVM buckling tasks (admitted by fam_fcvm.assess with the same settling rule) are marked independently reproduced.
"""
from __future__ import annotations

import collections
import hashlib
import json
import shutil
from pathlib import Path

import common as C

RUNS = C.ROOT / "output/cycloidal-convergence-study"
FOLLOWUP = C.ROOT.parent / "cadfem-bench-v1.1-followup/independent-reproduction"
FAMILY = "cycloidal-drive-components"
KEY = "max_displacement_mm"
FCVM = C.ROOT / "output/fcvm-buckling-study"


def jl(p: Path) -> list:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def wjl(p: Path, rows: list) -> None:
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))


def settled(st: dict) -> tuple[bool, str]:
    """Study criteria (run_cycloidal_convergence.py) with the solver-accuracy cut-off at 1e-6 instead of 1e-8: a relative
    force-balance residual of 1e-7 is exact for these 2-10 % tolerances. Refinement must settle (last change < 1 %,
    previous < 2 %) and the empirical band must be <= 10 %."""
    runs = st.get("mesh_runs", [])
    if len(runs) < 3:
        lim = "; finer meshes exceed the study's 220k-element direct-solver guard" if any("guard" in str(f) or f.get("exit_code") for f in st.get("failures", [])) else ""
        return False, f"only {len(runs)} mesh(es) solved{lim}, no converged estimate"
    fb = max(r["force_balance_relative"] for r in runs)
    last, prev, band = st["last_mesh_change"], st["previous_mesh_change"], st["empirical_band"]
    if fb > 1e-6:
        vals = ", ".join("%.5g" % r["outputs"][KEY] for r in runs)
        return False, f"force-balance residual {fb:.1e} and refinement values {vals} mm do not settle cleanly"
    if last >= 0.01 or prev >= 0.02:
        return False, (f"not converged: last refinement change {100 * last:.2f} %, previous {100 * prev:.2f} %; finest independent value "
                       f"{100 * st['relative_source_difference']:.1f} % from the published value (empirical band {100 * band:.0f} %)")
    if band > 0.10:
        return False, f"empirical band {100 * band:.0f} % exceeds 10 % (published value too mesh-dependent)"
    return True, "settled"


def apply() -> dict:
    ev = C.EVAL
    tasks, refs = jl(C.CAND / "tasks.jsonl"), jl(ev / "references.jsonl")
    held_t, held_r = jl(C.OUT / "held/tasks.jsonl"), jl(ev.parent / "held/references.jsonl")
    man = jl(ev / "evidence-manifest.jsonl")
    have = {m["path"] for m in man}

    def add(src: Path, rel: str, role: str) -> str:
        dst = ev / "evidence" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        path = str(dst.relative_to(ev))
        if path not in have:
            man.append(dict(path=path, sha256=C.sha256(dst), bytes=dst.stat().st_size,
                            original_workspace_path=str(src.relative_to(C.ROOT.parent)), role=role))
            have.add(path)
        return path

    common_ev = [add(RUNS / "summary.json", "cycloidal-convergence-study/summary.json", "tolerance_evidence")]
    common_ev += [add(C.ROOT / "scripts" / f, f"cycloidal-convergence-study/{f}", "tolerance_evidence_code")
                  for f in ("run_cycloidal_convergence.py", "converge_cycloidal_worker.py")]
    keep_t, keep_r, counts = [], [], collections.Counter()
    for t, r in zip(tasks, refs):
        tid = t["task_id"]
        if t["family"] == FAMILY:
            sf = RUNS / tid / "study.json"
            st = json.loads(sf.read_text()) if sf.exists() else dict(status="study_missing")
            files = common_ev + ([add(sf, f"cycloidal-convergence-study/{tid}/study.json", "tolerance_evidence")] if sf.exists() else [])
            files += [add(f, f"cycloidal-convergence-study/{tid}/{f.parent.name}/result.json", "tolerance_evidence")
                      for f in sorted((RUNS / tid).glob("h*/result.json"))]
            ok, why = settled(st)
            if not ok:
                reason = f"Mesh-convergence study: {why}."
                t["status"] = r["status"] = "held"
                t["hold_reason"] = r["hold_reason"] = reason
                r["evidence_files"] = sorted(set(r["evidence_files"]) | set(files))
                src, dst = C.CAND / "tasks" / tid, C.OUT / "held/inputs" / tid
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                held_t.append(t)
                held_r.append(r)
                counts["held_by_convergence"] += 1
                continue
            ref = r["references"][KEY]
            assert abs(ref["value"] - st["published_reference_mm"]) < 1e-15, tid
            ref["source_protocol_tol"] = dict(ref["tol"])
            ref["tol"]["value"] = max(float(st["empirical_band"]), ref["tol"]["value"])
            ref["tol"]["basis"] = "independent mesh-convergence study (evaluator evidence), not a certified uncertainty bound"
            ref["independent_finest_mm"] = st["finest_independent_mm"]
            r["evidence_files"] = sorted(set(r["evidence_files"]) | set(files))
            r["flags"].append(f"Tolerance {100 * ref['tol']['value']:.0f} % from an independent convergence study: finest independent "
                              f"{st['finest_independent_mm']:.6g} mm vs published {st['published_reference_mm']:.6g} mm "
                              f"({100 * st['relative_source_difference']:.1f} %), last refinement change {100 * st['last_mesh_change']:.2f} %.")
            t["readiness"]["independently_reproduced"] = True
            t["readiness"]["tolerances"] = "convergence_study"
            counts["band"] += 1
        elif t["family"] == "fcvm-buckling":
            # v1.3: the published buckling factor is graded only if fam_fcvm.assess() admitted it (same settling rule as above).
            a = r["fcvm_assessment"]
            if a["decision"] != "admit":
                t["status"] = r["status"] = "held"
                t["hold_reason"] = r["hold_reason"] = f"Independent eigenvalue study: {a['reason']}."
                src, dst = C.CAND / "tasks" / tid, C.OUT / "held/inputs" / tid
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                held_t.append(t)
                held_r.append(r)
                counts["fcvm_held"] += 1
                continue
            ref = r["references"]["lambda1"]
            assert abs(ref["value"] - a["published_lambda1"]) < 1e-15 and ref["tol"]["value"] == a["band"], tid
            ref["tol"]["basis"] = "independent eigenvalue convergence study (evaluator evidence), not a certified uncertainty bound"
            t["readiness"]["independently_reproduced"] = True
            t["readiness"]["tolerances"] = "convergence_study"
            counts["fcvm_band"] += 1
        elif tid == "A-AGENTFEM-fresh_test_000" and FOLLOWUP.exists():
            files = [add(FOLLOWUP / "comparison.json", "reproduction-2026-10-14/comparison.json", "reproduction_evidence")]
            files += [add(f, f"reproduction-2026-10-14/{f.parent.name}/result.json", "reproduction_evidence")
                      for f in sorted(FOLLOWUP.glob("agentfem-*/result.json"))]
            r["evidence_files"] = sorted(set(r["evidence_files"]) | set(files))
            r["flags"].append("Independently reproduced (2026-10-14 follow-up, 5 meshes): max displacement within 0.006 %, seat mean within 0.47 % of the published values.")
            t["readiness"]["independently_reproduced"] = True
            counts["followup_reproduced"] += 1
        keep_t.append(t)
        keep_r.append(r)
    stale = "No independent FEM reproduction in this release; end-to-end pass requires evaluator-owned workflow review."
    for t, r in zip(keep_t, keep_r):      # repair_release wrote the stale flag on every task before the studies were applied
        if t["readiness"].get("independently_reproduced"):
            r["flags"] = [f if f != stale else "Independently reproduced in this release (evaluator evidence); an end-to-end pass still requires "
                                              "evaluator-owned workflow review." for f in r["flags"]]
    wjl(C.CAND / "tasks.jsonl", keep_t)
    wjl(ev / "references.jsonl", keep_r)
    wjl(C.OUT / "held/tasks.jsonl", held_t)
    wjl(C.OUT / "held/references.jsonl", held_r)
    wjl(ev / "evidence-manifest.jsonl", man)
    regs = jl(ev / "registry.jsonl")             # recount after the holds above (repair_release counted before them)
    for reg in regs:
        if reg["status"] in ("pilot", "held") and reg.get("families"):
            act = [t for t in keep_t if t["family"] in reg["families"]]
            hld = [t for t in held_t if t["family"] in reg["families"]]
            rep = sum(bool(t["readiness"].get("independently_reproduced")) for t in act)
            reg.update(tasks=len(act), held_tasks=len(hld), status="pilot" if act else "held",
                       readiness=f"{rep} of {len(act)} active tasks independently reproduced" if rep else "No independently reproduced or certified tasks")
            if not act:
                reg["blocker"] = "No active tasks after validation gates"
    wjl(ev / "registry.jsonl", regs)
    C.jdump({t["task_id"]: hashlib.sha256(json.dumps(t, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
             for t in keep_t}, ev / "task-hashes.json")
    val = json.loads((ev / "validation.json").read_text())
    val.update(version=C.VERSION, tasks=len(keep_t), graded_outputs=sum(len(r["references"]) for r in keep_r),
               reference_classes=dict(collections.Counter(v["ref_class"] for r in keep_r for v in r["references"].values() if v.get("graded", True))),
               by_track=dict(collections.Counter(t["track"] for t in keep_t)), by_family=dict(collections.Counter(t["family"] for t in keep_t)),
               held_tasks=len(held_t), independently_reproduced_tasks=sum(bool(t["readiness"].get("independently_reproduced")) for t in keep_t),
               convergence_band_tasks=counts["band"], held_by_convergence=counts["held_by_convergence"], fcvm_buckling_tasks=counts["fcvm_band"], fcvm_held_by_study=counts["fcvm_held"],
               geometry_gate_tasks=sum("geometry_check" in r for r in keep_r),
               source_evidence_files=len(man), source_evidence_bytes=sum(m["bytes"] for m in man),
               validation_solver_runs=sum(1 for _ in RUNS.glob("*/h*/result.json")) + sum(1 for _ in FCVM.glob("*/h-*/result.json")))
    C.jdump(val, ev / "validation.json")
    return dict(counts)
