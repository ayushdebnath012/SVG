"""Grade a mechanism-design submission against its requirement sheet (scissor-jack family, v0.1).

Checks, each reported separately (a design passes only if all pass):
  dimensions   main.py regenerates the submitted assembly from params.json, and scaling arm_pin_spacing_mm by 1.05
               scales every arm's pin spacing by 1.05 while the mechanism stays valid (geometry is driven by dimensions)
  parts        every part is one valid solid with a catalogue material; the base sits on the ground plane z = 0
  mates        every part is in the joint graph, which is connected to the ground; every revolute is realised by
               coaxial cylindrical faces (pin or hole) on both parts
  motion       one degree of freedom; the drive moves the saddle top from <= h_min + 3 mm to >= h_max - 3 mm with the
               saddle level within 1 degree; no interference (> 2 mm^3 shared volume) at five poses
  strength     rated load W at the saddle-top centre, nine poses over the stroke: arm sections sliced from the
               submitted solids (axial + in-plane bending incl. eccentricity) >= FS_yield; Johnson/Euler buckling of
               compressed arms (pin-to-pin length) >= FS_buckling; pins in double shear (0.577 sigma_y) >= FS_yield;
               screw tension on its smallest section >= FS_yield
  economy      mass (part volumes x density) <= mass budget
  report       analysis.json screw tension, peak arm compression (5 %) and mass (3 %) agree with the grader, and no
               claimed pass where the grader finds a failure
Base, saddle and trunnion bodies are not stress-checked in v0.1; gear teeth are checked kinematically only.

  tmp/cq-env/bin/python scripts/mechbench/grade.py --task TASK.json --submission OUTPUTS [--code CODE] [--out grade.json] [--no-regen]
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geom as G  # noqa: E402
from planar import Mechanism, xz  # noqa: E402

MATERIALS = {   # yield MPa, E MPa, density kg/m3
    "S355": (355.0, 210000.0, 7850.0), "S700MC": (700.0, 210000.0, 7850.0),
    "8.8": (640.0, 210000.0, 7850.0), "10.9": (940.0, 210000.0, 7850.0), "12.9": (1080.0, 210000.0, 7850.0),
}


def johnson_euler(sy: float, E: float, A: float, I: float, L: float) -> float:
    r = math.sqrt(I / A)
    lam, lam_c = L / r, math.sqrt(2 * math.pi ** 2 * E / sy)
    s_cr = sy - (sy * lam / (2 * math.pi)) ** 2 / E if lam < lam_c else math.pi ** 2 * E / lam ** 2
    return s_cr * A


def regenerate(code: Path, params: dict, out: Path, python: str, timeout: int = 600) -> tuple[bool, str]:
    """Run the submitted code (main.py plus helper .py files) with the given parameters into a fresh folder."""
    out.mkdir(parents=True, exist_ok=True)
    for f in code.rglob("*.py"):
        dst = out / f.relative_to(code)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
    (out / "params.json").write_text(json.dumps(params))
    p = subprocess.run([python, "main.py", "--params", "params.json", "--out", "."], cwd=out, capture_output=True, text=True, timeout=timeout)
    return p.returncode == 0 and (out / "assembly.json").is_file(), (p.stderr or "")[-600:]


def grade(task: dict, sub: Path, python: str, do_regen: bool = True, code: Path | None = None) -> dict:
    code = code or sub
    R = {"task_id": task["task_id"], "checks": {}, "notes": []}
    C = R["checks"]
    spec = task["spec"]
    W, h0, h1 = spec["rated_load_N"], spec["h_min_mm"], spec["h_max_mm"]
    fs_y, fs_b, budget = spec["fs_yield"], spec["fs_buckling"], spec["mass_budget_kg"]
    try:
        asm = json.loads((sub / "assembly.json").read_text())
        params = json.loads((sub / "params.json").read_text())
        claim = json.loads((sub / "analysis.json").read_text())
    except Exception as e:                                       # noqa: BLE001
        C["files"] = dict(ok=False, error=f"{type(e).__name__}: {e}")
        R["passed"] = False
        return R
    names = [p["name"] for p in asm["parts"]]
    roles = {p["name"]: p.get("role") for p in asm["parts"]}
    arms = [n for n in names if roles[n] == "arm"]

    # ---- parts
    shapes, info, bad = {}, {}, []
    for p in asm["parts"]:
        try:
            sh = G.load(sub / p["step"])
        except Exception as e:                                   # noqa: BLE001
            bad.append(f"{p['name']}: unreadable ({type(e).__name__})")
            continue
        v = G.valid(sh)
        shapes[p["name"]], info[p["name"]] = sh, v
        if not v["valid"] or v["solids"] != 1 or v["volume_mm3"] <= 0:
            bad.append(f"{p['name']}: valid={v['valid']} solids={v['solids']}")
        if p.get("material") not in MATERIALS:
            bad.append(f"{p['name']}: material {p.get('material')!r} not in catalogue")
    base = asm.get("ground")
    if base in shapes and abs(shapes[base].BoundingBox().zmin) > 0.5:
        bad.append(f"ground part bottom at z = {shapes[base].BoundingBox().zmin:.2f} mm, not 0")
    for need in ("saddle", "screw"):
        if need not in roles.values():
            bad.append(f"no part with role {need!r}")
    if len(arms) < 2:
        bad.append("fewer than two arms")
    C["parts"] = dict(ok=not bad, problems=bad)
    if bad:
        R["passed"] = False
        return R
    saddle = next(n for n in names if roles[n] == "saddle")
    screw = next(n for n in names if roles[n] == "screw")

    # ---- mates
    probs, edges = [], {n: set() for n in names}
    for j in asm["joints"]:
        a, b = j["parts"]
        if a not in shapes or b not in shapes:
            probs.append(f"{j['name']}: unknown part")
            continue
        edges[a].add(b); edges[b].add(a)
        if j["type"] == "revolute":
            x, z = j["origin"][0], j["origin"][2]
            ca, cb = G.cylinders_on_axis(shapes[a], x, z), G.cylinders_on_axis(shapes[b], x, z)
            if not ca or not cb:
                probs.append(f"{j['name']}: no coaxial pin/hole on {'both parts' if not ca and not cb else (a if not ca else b)}")
            j["_pin_d"] = min(ca + cb) if ca and cb else None
    seen, todo = {base}, [base]
    while todo:
        for nb in edges[todo.pop()]:
            if nb not in seen:
                seen.add(nb); todo.append(nb)
    floating = sorted(set(names) - seen)
    if floating:
        probs.append(f"parts not connected to the ground: {floating}")
    C["mates"] = dict(ok=not probs, problems=probs, joints=len(asm["joints"]))

    # ---- motion
    mech = Mechanism(names, base, asm["joints"], asm["driver"])
    q0 = np.zeros(mech.n)
    mprob = []
    dof = mech.dof(q0)
    if dof != 1:
        mprob.append(f"{dof} degrees of freedom without the drive (need 1)")
    d0, d1 = asm["driver_range_mm"]
    if abs(mech.driver_value(q0) - d0) > 0.1:
        mprob.append(f"drive value in the submitted pose {mech.driver_value(q0):.2f} != declared collapsed {d0}")
    sweep = mech.sweep(d0, d1, 9) if dof == 1 else []
    sad_top = shapes[saddle].BoundingBox().zmax
    heights, tilts = [], []
    for v, q, err in sweep:
        if err > 1e-6:
            mprob.append(f"assembly does not close at drive {v:.1f} mm (residual {err:.1e})")
            break
        t, phi = mech.pose(q, saddle)
        heights.append(G.moved(shapes[saddle], t, phi).BoundingBox().zmax)
        tilts.append(abs(math.degrees(phi)))
    if heights:
        if min(heights) > h0 + 3 or max(heights) < h1 - 3:
            mprob.append(f"saddle top spans {min(heights):.1f}-{max(heights):.1f} mm; required {h0}-{h1} mm")
        if max(tilts) > 1.0:
            mprob.append(f"saddle tilts {max(tilts):.2f} deg")
    clash = []
    if sweep and not mprob:
        for k in (0, 2, 4, 6, 8):
            v, q, _ = sweep[k]
            posed = {n: G.moved(shapes[n], *mech.pose(q, n)) for n in names}
            for i, a in enumerate(names):
                for b in names[i + 1:]:
                    ov = G.overlap(posed[a], posed[b])
                    if not ov <= 2.0:
                        clash.append(f"{a}/{b} {ov:.1f} mm^3 at drive {v:.1f} mm")
    mprob += clash[:10]
    C["motion"] = dict(ok=not mprob, problems=mprob, dof=dof, saddle_height_range_mm=[min(heights), max(heights)] if heights else None)

    # ---- strength (only meaningful if the mechanism moves and closes)
    res, ends = {}, {}
    if sweep and dof == 1 and not any("close" in m for m in mprob):
        bb = shapes[saddle].BoundingBox()
        load_pt = np.array([(bb.xmin + bb.xmax) / 2, bb.zmax])
        props = {}
        for n in arms:
            pins = [xz(j["origin"]) for j in asm["joints"] if j["type"] == "revolute" and n in j["parts"]]
            if len(pins) < 2:
                continue
            A_, B_ = max(((p1, p2) for p1 in pins for p2 in pins), key=lambda pp: np.linalg.norm(pp[0] - pp[1]))
            L = float(np.linalg.norm(B_ - A_))
            u = (B_ - A_) / L
            ends[n] = (A_, u, L)
            props[n] = [(s, G.section(shapes[n], A_, u, s)) for s in np.linspace(0.0, L, 21)]
        jd = {j["name"]: j for j in asm["joints"]}
        worst = dict(sigma=0.0, comp=0.0, tension=0.0, pin_tau_fs=math.inf)
        fs_yield_min, fs_buck_min, where = math.inf, math.inf, ""
        for v, q, _ in sweep:
            st = mech.statics(q, [(saddle, load_pt, np.array([0.0, -W]))])
            if st["residual_N"] > 1e-3 * W:
                C["strength"] = dict(ok=False, problems=[f"mechanism cannot carry the load at drive {v:.1f} mm"])
                break
            lam = st["multipliers"]
            T = -lam[asm["driver"]][0]
            worst["tension"] = max(worst["tension"], T)
            for jn, jv in lam.items():
                j = jd[jn]
                if j["type"] == "revolute" and j.get("_pin_d"):
                    F = math.hypot(*jv[:2])
                    sy = min(MATERIALS[next(p["material"] for p in asm["parts"] if p["name"] == x)][0] for x in j["parts"])
                    tau = F / (2 * math.pi * j["_pin_d"] ** 2 / 4)
                    fs = 0.577 * sy / tau if tau > 0 else math.inf
                    if fs < fs_yield_min:
                        fs_yield_min, where = fs, f"pin {jn} at drive {v:.1f} mm"
            for n, (A_, u, L) in ends.items():
                sy, E, _ = MATERIALS[next(p["material"] for p in asm["parts"] if p["name"] == n)]
                nvec = np.array([-u[1], u[0]])
                loads = []
                for jn, pt, F in mech.body_loads(q, st, n):
                    t, phi = mech.pose(q, n)
                    c, s_ = math.cos(-phi), math.sin(-phi)       # back to the reference frame of the arm
                    Fr = np.array([c * F[0] - s_ * F[1], s_ * F[0] + c * F[1]])
                    pr = np.array([[c, -s_], [s_, c]]) @ (pt - t)
                    loads.append(((pr - A_) @ u, pr, Fr))
                loads.sort(key=lambda x: x[0])
                Nmin = 0.0
                for s, sec in props[n]:
                    if sec is None:
                        continue
                    Fs = sum((F for (si, _, F) in loads if si <= s + 1e-6), np.zeros(2))
                    Ms = sum(((pr - (A_ + s * u))[0] * F[1] - (pr - (A_ + s * u))[1] * F[0] for (si, pr, F) in loads if si <= s + 1e-6), 0.0)
                    N = -(Fs @ u)
                    M = abs(Ms) + abs(N * sec["centroid_offset"])
                    sig = abs(N) / sec["area"] + M * sec["c"] / sec["I_y"]
                    Nmin = min(Nmin, N)
                    fs = sy / sig if sig > 0 else math.inf
                    if fs < fs_yield_min:
                        fs_yield_min, where = fs, f"{n} at s = {s:.1f} mm, drive {v:.1f} mm"
                worst["comp"] = max(worst["comp"], -Nmin)
                mid = [sec for s, sec in props[n] if sec and 0.25 * L <= s <= 0.75 * L]
                if Nmin < 0 and mid:
                    sec = min(mid, key=lambda x: x["I_min"])
                    fsb = johnson_euler(sy, E, sec["area"], sec["I_min"], L) / -Nmin
                    if fsb < fs_buck_min:
                        fs_buck_min = fsb
        if "strength" not in C:
            jdrv = jd[asm["driver"]]
            pa, pb = xz(jdrv["point_a"]), xz(jdrv["point_b"])
            u = (pb - pa) / np.linalg.norm(pb - pa)
            secs = [G.section(shapes[screw], pa, u, s) for s in np.linspace(0.1, 0.9, 9) * np.linalg.norm(pb - pa)]
            secs = [s_ for s_ in secs if s_]
            sprob = []
            if not secs or any(abs(s_["centroid_offset"]) > 1.0 for s_ in secs):
                sprob.append("screw solid does not lie on the drive line between the trunnion points")
            else:
                A_min = min(s_["area"] for s_ in secs)
                sy = MATERIALS[next(p["material"] for p in asm["parts"] if p["name"] == screw)][0]
                fs = sy / (worst["tension"] / A_min)
                if fs < fs_yield_min:
                    fs_yield_min, where = fs, f"screw (A = {A_min:.1f} mm^2)"
            if fs_yield_min < fs_y:
                sprob.append(f"yield FS {fs_yield_min:.2f} < {fs_y} ({where})")
            if fs_buck_min < fs_b:
                sprob.append(f"buckling FS {fs_buck_min:.2f} < {fs_b}")
            C["strength"] = dict(ok=not sprob, problems=sprob, min_yield_fs=round(fs_yield_min, 3), governing=where,
                                 min_buckling_fs=round(fs_buck_min, 3), max_screw_tension_N=round(worst["tension"], 1),
                                 max_arm_compression_N=round(worst["comp"], 1))
            res = C["strength"]
    else:
        C["strength"] = dict(ok=False, problems=["not evaluated: mechanism does not move as one degree of freedom"])

    # ---- economy
    mass = sum(info[n]["volume_mm3"] * 1e-9 * MATERIALS[p["material"]][2] for p in asm["parts"] for n in [p["name"]])
    C["economy"] = dict(ok=mass <= budget, mass_kg=round(mass, 3), budget_kg=budget)

    # ---- report
    rp = []
    def close(k, ref, tol):
        v = claim.get(k)
        if not isinstance(v, (int, float)):
            rp.append(f"{k} missing")
        elif ref and abs(v - ref) > tol * abs(ref):
            rp.append(f"{k} {v:.4g} vs {ref:.4g}")
    if res:
        close("screw_tension_N", res.get("max_screw_tension_N"), 0.05)
        close("max_arm_compression_N", res.get("max_arm_compression_N"), 0.05)
    close("mass_kg", mass, 0.03)
    if str(claim.get("verdict", "")).lower() == "meets" and not all(C[k]["ok"] for k in ("strength", "economy", "motion")):
        rp.append("claims the design meets the requirements, but it does not")
    C["report"] = dict(ok=not rp, problems=rp)

    # ---- dimensions (parametric regeneration)
    if do_regen:
        dp = []
        with tempfile.TemporaryDirectory() as td:
            ok, err = regenerate(code, params, Path(td) / "a", python)
            if not ok:
                dp.append(f"main.py does not regenerate the submission: {err[-200:]}")
            else:
                a2 = json.loads((Path(td) / "a/assembly.json").read_text())
                if json.dumps(a2["joints"], sort_keys=True) != json.dumps(json.loads((sub / "assembly.json").read_text())["joints"], sort_keys=True):
                    dp.append("regenerated joints differ from the submitted assembly")
            key = "arm_pin_spacing_mm"
            if key not in params:
                dp.append(f"params.json has no {key}")
            else:
                L_sub = [ends[n][2] for n in ends]
                if L_sub and max(abs(x - params[key]) for x in L_sub) > 0.1:
                    dp.append(f"{key} = {params[key]} but arm pin spacings are {[round(x, 2) for x in L_sub]}")
                p2 = copy.deepcopy(params); p2[key] = params[key] * 1.05
                ok, err = regenerate(code, p2, Path(td) / "b", python)
                if not ok:
                    dp.append(f"main.py fails when {key} is scaled by 1.05: {err[-200:]}")
                else:
                    a3 = json.loads((Path(td) / "b/assembly.json").read_text())
                    for n in [p["name"] for p in a3["parts"] if p.get("role") == "arm"]:
                        pins = [xz(j["origin"]) for j in a3["joints"] if j["type"] == "revolute" and n in j["parts"]]
                        L2 = max(np.linalg.norm(p1 - p2_) for p1 in pins for p2_ in pins) if len(pins) >= 2 else 0
                        if abs(L2 - 1.05 * params[key]) > 0.005 * params[key]:
                            dp.append(f"{n}: pin spacing {L2:.2f} after scaling, expected {1.05 * params[key]:.2f}")
                    m3 = Mechanism([p["name"] for p in a3["parts"]], a3["ground"], a3["joints"], a3["driver"])
                    if m3.dof(np.zeros(m3.n)) != 1:
                        dp.append("scaled design no longer has one degree of freedom")
        C["dimensions"] = dict(ok=not dp, problems=dp)
    R["passed"] = all(c.get("ok") for c in C.values())
    return R


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", type=Path, required=True)
    ap.add_argument("--submission", type=Path, required=True, help="folder with the generated artifacts")
    ap.add_argument("--code", type=Path, help="folder with main.py and helpers (default: --submission)")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--python", default=sys.executable, help="interpreter used to run the submitted main.py")
    ap.add_argument("--no-regen", action="store_true")
    a = ap.parse_args()
    r = grade(json.loads(a.task.read_text()), a.submission.resolve(), a.python, not a.no_regen, a.code.resolve() if a.code else None)
    text = json.dumps(r, indent=1, default=float)
    if a.out:
        a.out.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
