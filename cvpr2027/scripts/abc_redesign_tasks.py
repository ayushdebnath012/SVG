"""CAD + FEM redesign tasks from ABC parts: the part fails under its load; edit the CAD so it passes.

Built on the analysis tasks of abc_engineering_fem.py (real units, bolted holes or a clamped face, a pin or face load,
converged P2 FEM). For each analysis task:
  1. interface spec: the support holes / clamped plane and the load hole / loaded plane, by geometry (axis, radius,
     plane normal and offset), so they can be found again on any edited part;
  2. reference fix, proving the task can be solved: thicken the part by an outward offset and restore the
     interfaces (scripts/cad_thicken_keep_interfaces.py, OpenCASCADE), for growing offsets until the peak stress has
     dropped enough within the mass limit;
  3. the force is set so the original part fails (safety factor <= 0.95) while the reference fix passes
     (safety factor >= 1.5 with 5 % margin before rounding the force down).
The grader re-runs the same FEM on a submitted STEP: interfaces present, one solid, volume within the limit, safety
factor >= 1.5 (yield / peak von Mises outside the stated zone, quadratic tets on the fine mesh of the analysis task).

  python abc_redesign_tasks.py build --analysis tmp/abc-eng/pilot --out tmp/abc-eng/redesign [--workers 3]
  python abc_redesign_tasks.py grade --tasks tmp/abc-eng/redesign/tasks.jsonl --id <task id> --step part.step
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("abc_engineering_fem", HERE / "abc_engineering_fem.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

OCP_PYTHON = HERE.parent / "tmp/benchcad-official/repo/.venv/bin/python"  # any Python with OCP
SF_REQUIRED, MASS_LIMIT, SF_FAIL_MAX, MARGIN = 1.5, 0.25, 0.95, 1.05
OFFSETS = (0.005, 0.01, 0.02, 0.03, 0.045, 0.06)  # x longest side
EVAL_TIMEOUT = 900


# ---------------------------------------------------------------- interfaces
def interface_spec(bcs: dict) -> dict:
    def item(kind, d):
        if kind == "hole":
            return dict(kind="hole", centre=d["centre"], axis=d["axis"], radius=d["radius"], length=d["length"])
        return dict(kind="plane", normal=d["normal"], offset=d["offset"], area=d["area"], centre=d["centre"])
    s, ld = bcs["support"], bcs["load"]
    sup = [item("hole", h) for h in s["holes"]] if s["kind"] == "bolted holes" else [item("plane", s["plane"])]
    lod = [item("hole", ld["hole"])] if ld["kind"] == "pin load in hole" else [item("plane", ld["plane"])]
    return dict(support_kind=s["kind"], support=sup, load_kind=ld["kind"], load=lod, direction=ld["direction"])


def locate(items: list[dict], feats: list[dict], L: float) -> list[int] | None:
    faces: list[int] = []
    for it in items:
        if it["kind"] == "hole":
            e0, c0 = np.array(it["axis"]), np.array(it["centre"])
            hit = None
            for f in feats:
                if f["kind"] != "hole" or abs(f["radius"] - it["radius"]) > 0.02 * it["radius"] or abs(np.dot(f["axis"], e0)) < 0.999:
                    continue
                dc = np.array(f["centre"]) - c0
                if np.linalg.norm(dc - (dc @ e0) * e0) < 0.02 * it["radius"] + 1e-3 * L:
                    hit = f
                    break
            if hit is None:
                return None
            faces += hit["faces"]
        else:
            n0 = np.array(it["normal"])
            fs = [f for f in feats if f["kind"] == "plane" and np.dot(f["normal"], n0) > 0.9995 and abs(f["offset"] - it["offset"]) < 1e-3 * L]
            if sum(f["area"] for f in fs) < 0.95 * it["area"]:
                return None
            faces += sum((f["faces"] for f in fs), [])
    return faces


def restorable(spec: dict, bnd: dict, L: float) -> str | None:
    """Can the thicken-and-restore fix keep these interfaces? Holes must be through, planes must be extreme."""
    for it in spec["support"] + spec["load"]:
        if it["kind"] == "hole":
            e, c, R = np.array(it["axis"]), np.array(it["centre"]), it["radius"]
            q = bnd["c"] - c
            t = q @ e
            rad = np.linalg.norm(q - np.outer(t, e), axis=1)
            inside = rad < 0.9 * R
            if (inside & (np.abs(bnd["n"] @ e) > 0.9)).any() or (inside & (np.abs(t) > it["length"] / 2 + 1e-3 * L)).any():
                return "blind or obstructed hole"
        else:
            n = np.array(it["normal"])
            if (bnd["P"].reshape(-1, 3) @ n).max() > it["offset"] + 1e-4 * L:
                return "interface plane is not an outer face"
    return None


# ---------------------------------------------------------------- evaluation (own process)
def evaluate(step: str, task: dict) -> dict:
    """Mesh (fine mesh of the analysis task), locate interfaces, solve at the unit force F0."""
    import gmsh
    from mpi4py import MPI
    from dolfinx.io import gmshio

    spec, L = task["interfaces"], task["L_mm"]
    mat = next(m for m in eng.MATERIALS if m[0] == task["material"]["name"])
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setString("Geometry.OCCTargetUnit", "MM")
    try:
        gmsh.model.occ.importShapes(step)
        gmsh.model.occ.synchronize()
        vols = gmsh.model.getEntities(3)
        if len(vols) != 1:
            return dict(ok=False, reason=f"{len(vols)} solids")
        volume = gmsh.model.occ.getMass(3, vols[0][1])
        info = eng.faces_info(gmsh)
        gmsh.model.addPhysicalGroup(3, [vols[0][1]], tag=1)
        for _, s in gmsh.model.getEntities(2):
            gmsh.model.addPhysicalGroup(2, [s], tag=s)
        nodes = eng.mesh_model(gmsh, L, eng.FINE_FACTOR)
        if nodes > eng.MAX_NODES * 1.5:
            return dict(ok=False, reason=f"mesh too large ({nodes} nodes)", volume_mm3=volume)
        domain, _, ft = gmshio.model_to_mesh(gmsh.model, MPI.COMM_SELF, 0, gdim=3)
    finally:
        gmsh.finalize()
    bnd = eng.boundary(domain, ft)
    feats = eng.features(info, bnd, L)
    sup, lod = locate(spec["support"], feats, L), locate(spec["load"], feats, L)
    if sup is None or lod is None:
        return dict(ok=False, reason="interface missing or changed", volume_mm3=volume, restorable=restorable(spec, bnd, L))
    bcs = dict(support=dict(kind=spec["support_kind"], faces=sup), load=dict(kind=spec["load_kind"], faces=lod, direction=spec["direction"]))
    r = eng.solve(domain, ft, bcs, mat, L)
    return dict(ok=True, volume_mm3=volume, peak_vm_F0=r["peak_vm"], max_u_F0=r["max_u"], peak_at=r["peak_at"],
                dofs=r["dofs"], nodes=nodes, restorable=restorable(spec, bnd, L))


def run_eval(step: str, task: dict, work: Path) -> dict:
    tj = work / f"eval-{abs(hash((step, time.time()))) % 10**9}.json"
    tj.write_text(json.dumps(task))
    try:
        r = subprocess.run([sys.executable, "-I", __file__, "evaluate", step, str(tj)], capture_output=True, text=True, timeout=EVAL_TIMEOUT)
        lines = [ln for ln in r.stdout.splitlines() if ln.startswith("{")]
        return json.loads(lines[-1]) if r.returncode == 0 and lines else dict(ok=False, reason="evaluation crashed", error=r.stderr[-300:])
    except subprocess.TimeoutExpired:
        return dict(ok=False, reason="evaluation timed out")
    finally:
        tj.unlink(missing_ok=True)


def thicken(src: str, dst: Path, spec: dict, L: float, centre: list, delta: float, work: Path) -> dict:
    sj = work / f"{dst.stem}.spec.json"
    sj.write_text(json.dumps(dict(L=L, centre=centre,
                                  holes=[i for i in spec["support"] + spec["load"] if i["kind"] == "hole"],
                                  planes=[i for i in spec["support"] + spec["load"] if i["kind"] == "plane"])))
    r = subprocess.run([str(OCP_PYTHON), "-I", str(HERE / "cad_thicken_keep_interfaces.py"), src, str(dst), str(sj), str(delta)],
                       capture_output=True, text=True, timeout=600)
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith("{")]
    return json.loads(lines[-1]) if lines else dict(ok=False, error=r.stderr[-300:])


# ---------------------------------------------------------------- tasks
def round_down(x: float) -> float:
    e = 10 ** (math.floor(math.log10(x)) - 1)
    return math.floor(x / e) * e


def build_one(a_row: dict, out: Path) -> dict:
    tid = a_row["id"]
    work = out / "work" / tid
    work.mkdir(parents=True, exist_ok=True)
    spec = interface_spec(a_row["bcs"])
    L = a_row["L_mm"]
    base = dict(id=tid, step=a_row["step"], sha256=a_row["sha256"], material=a_row["material"], L_mm=L,
                size_mm=a_row["size_mm"], zone_mm=a_row["zone_mm"], interfaces=spec, bcs=a_row["bcs"])
    orig = run_eval(a_row["step"], base, work)
    if not orig.get("ok"):
        return dict(base, status="skipped:original", detail=orig)
    if orig.get("restorable"):
        return dict(base, status="skipped:not_restorable", detail=orig["restorable"])
    centre = np.mean([np.array(a_row["bcs"]["support_centre"])], axis=0).tolist()
    tries, best = [], None
    for f in OFFSETS:
        cand = work / f"thicken_{f:g}.step"
        t = thicken(a_row["step"], cand, spec, L, centre, f * L, work)
        if not t.get("ok"):
            tries.append(dict(offset=f, error=t.get("error")))
            continue
        ratio = t["volume_out"] / orig["volume_mm3"]
        if ratio > 1 + MASS_LIMIT:
            tries.append(dict(offset=f, volume_ratio=ratio))
            break
        ev = run_eval(str(cand), base, work)
        if not ev.get("ok"):
            tries.append(dict(offset=f, volume_ratio=ratio, error=ev.get("reason")))
            continue
        rho = orig["peak_vm_F0"] / ev["peak_vm_F0"]
        tries.append(dict(offset=f, volume_ratio=ratio, stress_reduction=rho))
        if best is None or rho > best["rho"]:
            best = dict(rho=rho, offset=f, step=str(cand), volume_ratio=ratio, eval=ev)
        if rho * SF_FAIL_MAX >= SF_REQUIRED * MARGIN:
            break
    base["reference_search"] = tries
    if best is None:
        return dict(base, status="skipped:no_reference_fix")
    Sy = a_row["material"]["yield_MPa"]
    F = round_down(eng.F0 * Sy / (SF_REQUIRED * MARGIN * best["eval"]["peak_vm_F0"]))
    k = F / eng.F0
    sf_orig, sf_ref = Sy / (k * orig["peak_vm_F0"]), Sy / (k * best["eval"]["peak_vm_F0"])
    if sf_orig > SF_FAIL_MAX or sf_ref < SF_REQUIRED:
        return dict(base, status="skipped:fix_too_weak", stress_reduction=best["rho"])
    row = dict(base, status="ok", force_N=F, volume_mm3=orig["volume_mm3"], volume_limit_mm3=orig["volume_mm3"] * (1 + MASS_LIMIT),
               original=dict(safety_factor=sf_orig, peak_von_mises_MPa=k * orig["peak_vm_F0"], peak_at=orig["peak_at"],
                             max_displacement_mm=k * orig["max_u_F0"]),
               reference_fix=dict(method="outward offset, interfaces re-drilled / re-faced", offset_mm=best["offset"] * L,
                                  step=best["step"], volume_ratio=best["volume_ratio"], safety_factor=sf_ref,
                                  peak_von_mises_MPa=k * best["eval"]["peak_vm_F0"]),
               requirement=dict(safety_factor_min=SF_REQUIRED, volume_max_ratio=1 + MASS_LIMIT))
    row["prompt"] = prompt(row)
    return row


def prompt(r: dict) -> str:
    a = dict(r, force_N=r["force_N"], zone_mm=r["zone_mm"])
    m, s, ld = r["material"], r["bcs"]["support"], r["bcs"]["load"]
    analysis = eng.prompt(dict(a, reference={}, size_mm=r["size_mm"]))
    setup = analysis.split(" Assume small deformations")[0]
    return (f"{setup} Under this load the part fails: its safety factor against yield is {r['original']['safety_factor']:.2f}. "
            f"Redesign the part so that the safety factor is at least {SF_REQUIRED}. The safety factor is the yield "
            f"strength divided by the peak von Mises stress outside {r['zone_mm']:.3g} mm of the supports and the loaded "
            "surface, from linear static FEM with quadratic tetrahedra. Constraints: keep every support and load feature "
            "exactly as it is (hole diameters, axes and positions; flat faces in the same plane with at least the same area); "
            f"the part must stay one solid; its volume may be at most {r['volume_limit_mm3']:.4g} mm^3 "
            f"({100 * MASS_LIMIT:.0f} % above the current {r['volume_mm3']:.4g} mm^3). Return the redesigned part as a STEP "
            "file in millimetres, and report the safety factor and volume you computed for it.")


def build(a) -> None:
    out = Path(a.out)
    (out / "work").mkdir(parents=True, exist_ok=True)
    rows = [json.loads(line) for line in (Path(a.analysis) / "tasks.jsonl").open()]
    man = out / "manifest.jsonl"
    done = {json.loads(line)["id"] for line in man.open()} if man.exists() else set()
    todo = [r for r in rows if r["id"] not in done]
    print(f"{len(rows)} analysis tasks, {len(todo)} to build", flush=True)
    with ThreadPoolExecutor(a.workers) as ex, man.open("a") as h:
        for i, row in enumerate(ex.map(lambda r: build_one(r, out), todo), 1):
            h.write(json.dumps(row) + "\n")
            h.flush()
            print(f"{i}/{len(todo)} {row['id'][:8]} {row['status']}", flush=True)
    rows = [json.loads(line) for line in man.open()]
    (out / "tasks.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows if r["status"] == "ok"))
    stat: dict[str, int] = {}
    for r in rows:
        stat[r["status"]] = stat.get(r["status"], 0) + 1
    (out / "summary.json").write_text(json.dumps(stat, indent=1))
    print(json.dumps(stat), flush=True)


def grade(a) -> None:
    task = next(json.loads(line) for line in Path(a.tasks).open() if json.loads(line)["id"] == a.id)
    ev = run_eval(a.step, task, Path(a.tasks).parent)
    v = dict(id=task["id"], step=a.step, passed=False)
    if not ev.get("ok"):
        v["reason"] = ev.get("reason")
    else:
        k = task["force_N"] / eng.F0
        sf = task["material"]["yield_MPa"] / (k * ev["peak_vm_F0"])
        v.update(safety_factor=sf, volume_mm3=ev["volume_mm3"], volume_ratio=ev["volume_mm3"] / task["volume_mm3"],
                 peak_von_mises_MPa=k * ev["peak_vm_F0"], peak_at=ev["peak_at"])
        v["passed"] = sf >= SF_REQUIRED and ev["volume_mm3"] <= task["volume_limit_mm3"]
        if not v["passed"]:
            v["reason"] = "safety factor too low" if sf < SF_REQUIRED else "too heavy"
    print(json.dumps(v))


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "evaluate":  # child process
        print(json.dumps(evaluate(sys.argv[2], json.loads(Path(sys.argv[3]).read_text()))))
        return
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--analysis", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--workers", type=int, default=3)
    g = sub.add_parser("grade")
    g.add_argument("--tasks", required=True)
    g.add_argument("--id", required=True)
    g.add_argument("--step", required=True)
    a = p.parse_args()
    dict(build=build, grade=grade)[a.cmd](a)


if __name__ == "__main__":
    main()
