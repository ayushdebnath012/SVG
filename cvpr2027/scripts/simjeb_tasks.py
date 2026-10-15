"""Real engineering CAD + FEM tasks from SimJEB (GE jet engine bracket challenge; doi:10.7910/DVN/XFUWJG).

Every bracket shares the GE interfaces (SimJEB frame, mm): four bolt holes (diameter 10.3124, axis +Z, flange from the
mounting plane z = 0) and a clevis with two lugs on a 19.1008 mm pin. The four GE load cases act at the pin point
(from SimJEB's OptiStruct decks): vertical 35,585.77 N up, horizontal 37,809.9 N along -X, diagonal (42 deg)
(-28,276.2, 0, 31,403.9) N, torsion 564,924.2 N mm about Z. Material Ti-6Al-4V: E = 113.8 GPa, nu = 0.342,
density 4.43 g/cm^3, yield 903 MPa (131 ksi).

The grader meshes any STEP with first-order tets of about SimJEB's density (gmsh size 1.2 mm), fixes the bolt-hole walls (SimJEB: rigid RBE2 to a
fixed point), loads the pin-hole walls through an RBE3 distribution, solves the four cases and reports, per case, the
maximum displacement and the peak von Mises stress of the nodal-averaged stress tensor (SimJEB's measure) outside
2 mm of the bolt and pin walls (inside, the idealised rigid connections make it mesh-dependent; see
scripts/simjeb_fem.py, which reproduces SimJEB's published values exactly on SimJEB's own mesh).

  python simjeb_tasks.py grade part.step [--json out.json]
  python simjeb_tasks.py grade-all --cad tmp/simjeb/cad --out tmp/simjeb/graded
  python simjeb_tasks.py build --meta tmp/simjeb/dl/f4639239 --cad tmp/simjeb/cad --graded tmp/simjeb/graded --out tmp/simjeb/tasks
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
import time

import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("simjeb_fem", HERE / "simjeb_fem.py")
sfem = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sfem)

E, NU, RHO, YIELD = 113800.0, 0.342, 4.43e-9, 903.0  # MPa, -, t/mm^3, MPa
BOLT_R, BOLT_FLANGE = 5.1562, 6.985
BOLTS = np.array([[0.0, 0.0], [52.0472, 1.5805], [0.0, -148.1248], [38.0833, -146.9684]])
PIN_R = 9.5504
PIN_AXIS = np.array([-0.030352, 0.999539, 0.0]) / np.linalg.norm([-0.030352, 0.999539, 0.0])
PIN_POINT = np.array([-20.9236, -74.6978, 44.7246])
LUGS = ((11.112, 17.463), (-17.463, -11.113))  # axial ranges of the two lug bores from PIN_POINT
LOAD_POINT = np.array([-21.0359, -75.0647, 44.80101])  # RBE3 reference node in SimJEB's decks
CASES = {
    "vertical": (np.array([0.0, 0.0, 35585.77]), np.zeros(3)),
    "horizontal": (np.array([-37809.9, 0.0, 0.0]), np.zeros(3)),
    "diagonal": (np.array([-28276.2, 0.0, 31403.9]), np.zeros(3)),
    "torsion": (np.zeros(3), np.array([0.0, 0.0, 564924.2])),
}
ZONE = 2.0  # mm around the bolt / pin walls, where the idealised rigid connections make stress singular
MESH_SIZE = 1.2  # gmsh size giving about SimJEB's node count (HyperMesh '2 mm average' meshes are finer)


def mesh_step(step: str, size: float = MESH_SIZE):
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setNumber("General.NumThreads", 2)  # several graders run side by side
    gmsh.option.setString("Geometry.OCCTargetUnit", "MM")
    try:
        gmsh.model.occ.importShapes(step)
        gmsh.model.occ.synchronize()
        vols = gmsh.model.getEntities(3)
        if not vols:  # some SimJEB files hold a closed shell rather than a solid: close it into a volume
            surfs = [s for _, s in gmsh.model.occ.getEntities(2)]
            if surfs:
                gmsh.model.occ.addVolume([gmsh.model.occ.addSurfaceLoop(surfs, sewing=True)])
                gmsh.model.occ.synchronize()
                vols = gmsh.model.getEntities(3)
        if len(vols) != 1:
            raise ValueError(f"{len(vols)} solids (one is required)")
        volume = gmsh.model.occ.getMass(3, vols[0][1])
        gmsh.option.setNumber("Mesh.MeshSizeMax", size)
        gmsh.option.setNumber("Mesh.MeshSizeMin", size / 4)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.Algorithm", 6)
        gmsh.option.setNumber("Mesh.Algorithm3D", 10)
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
        try:
            gmsh.model.mesh.generate(3)
        except Exception:  # noqa: BLE001 - HXT failed; Delaunay
            gmsh.model.mesh.clear()
            gmsh.option.setNumber("Mesh.Algorithm3D", 1)
            gmsh.model.mesh.generate(3)
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        _, ntags = gmsh.model.mesh.getElementsByType(4)  # 4-node tets
        _, btags = gmsh.model.mesh.getElementsByType(2)  # boundary triangles
    finally:
        gmsh.finalize()
    if len(ntags) == 0:
        raise ValueError("meshing failed (defective geometry)")
    idx = np.full(int(tags.max()) + 1, -1, np.int64)
    idx[tags.astype(np.int64)] = np.arange(len(tags))
    x = xyz.reshape(-1, 3)
    tets = idx[ntags.astype(np.int64)].reshape(-1, 4)
    used = np.unique(tets)
    remap = np.full(len(x), -1, np.int64)
    remap[used] = np.arange(len(used))
    bnodes = remap[np.unique(idx[btags.astype(np.int64)])]
    return x[used], remap[tets], bnodes[bnodes >= 0], volume


def circle_fit(p: np.ndarray) -> tuple[np.ndarray, float]:
    """Least-squares circle through 2-D points (Kasa)."""
    A = np.c_[2 * p, np.ones(len(p))]
    sol = np.linalg.lstsq(A, (p ** 2).sum(1), rcond=None)[0]
    c = sol[:2]
    return c, float(np.sqrt(sol[2] + c @ c))


def find_wall(q2: np.ndarray, extra: np.ndarray, lo: float, hi: float, tol: float = 0.02):
    """Nodes (2-D coordinates q2 in the plane across the axis) on a cylindrical wall of radius in [lo, hi] near the
    nominal axis (the origin). Candidate radii (the most common node radius, a smoothed version that tolerates small
    hole offsets, and the next most common radii) are each refined by a circle fit; the candidate whose circle has the
    widest angular coverage, then the most nodes, is the wall. Returns (mask, centre offset, radius)."""
    d = np.linalg.norm(q2, axis=1)
    band = (d > lo) & (d < hi) & extra
    if band.sum() < 8:
        return np.zeros(len(q2), bool), None, None
    vals, counts = np.unique(np.round(d[band], 2), return_counts=True)
    smooth = np.convolve(counts, np.ones(15), "same")
    starts = {float(vals[np.argmax(smooth)])} | {float(v) for v in vals[np.argsort(counts)[::-1][:4]]}
    best, best_key = (np.zeros(len(q2), bool), None, None), (-1.0, -1)
    for R0 in starts:
        cand = band & (np.abs(d - R0) < 0.15)
        if cand.sum() < 8:
            continue
        c, R = circle_fit(q2[cand])
        for _ in range(2):
            sel = (np.abs(np.linalg.norm(q2 - c, axis=1) - R) < 0.05) & extra
            if sel.sum() < 8:
                break
            c, R = circle_fit(q2[sel])
        m = (np.abs(np.linalg.norm(q2 - c, axis=1) - R) < tol) & extra
        if not lo <= R <= hi or np.linalg.norm(c) > 0.5 or m.sum() < 8:
            continue
        key = (coverage(q2[m] - c), int(m.sum()))
        if key > best_key:
            best, best_key = (m, c, R), key
    return best


def coverage(q2: np.ndarray) -> float:
    ang = np.arctan2(q2[:, 1], q2[:, 0])
    return len(np.unique(np.floor((ang + np.pi) / (2 * np.pi) * 24).astype(int) % 24)) / 24


def interfaces(x: np.ndarray, bnodes: np.ndarray) -> dict:
    """Boundary nodes on the bolt-hole walls and on the pin-bore walls. Each hole's centre and radius are fitted
    (the GE holes are 10.31-10.67 mm and 19.05-19.18 mm across SimJEB and may sit a few hundredths off nominal)."""
    xb = x[bnodes]
    bolt_sets, report = [], {}
    for k, c in enumerate(BOLTS):
        q2 = xb[:, :2] - c
        m, off, R = find_wall(q2, xb[:, 2] > -0.02, 5.0, 5.5)
        z = xb[m, 2]
        report[f"bolt{k + 1}"] = dict(radius=R, offset=None if off is None else off.round(3).tolist(), nodes=int(m.sum()),
                                      coverage=coverage(q2[m] - off) if m.any() else 0.0,
                                      z_range=[float(z.min()), float(z.max())] if m.any() else None)
        bolt_sets.append(bnodes[m])
    q = xb - PIN_POINT
    t = q @ PIN_AXIS
    e1 = np.cross(PIN_AXIS, [0, 0, 1.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(PIN_AXIS, e1)
    q2 = np.c_[q @ e1, q @ e2]
    m, off, R = find_wall(q2, np.abs(t) < 25, 9.3, 9.8)
    report["pin_radius"], report["pin_offset"] = R, None if off is None else off.round(3).tolist()
    for k, (lo, hi) in enumerate(LUGS):
        mm = m & (t > lo - 0.5) & (t < hi + 0.5)
        report[f"lug{k + 1}"] = dict(nodes=int(mm.sum()), axial=[float(t[mm].min()), float(t[mm].max())] if mm.any() else None)
    report["pin_wall_in_clevis_gap"] = int((m & (t > LUGS[1][1] + 0.5) & (t < LUGS[0][0] - 0.5)).sum())
    ok = (all(report[f"bolt{k + 1}"]["coverage"] >= 300 / 360 and report[f"bolt{k + 1}"]["nodes"] >= 8 for k in range(4))
          and all(report[f"lug{k + 1}"]["nodes"] >= 8 for k in range(2)))
    return dict(ok=bool(ok), fixed=np.concatenate(bolt_sets), pin=bnodes[m], report=report)


def grade(step: str, mesh_size: float = MESH_SIZE, material: dict | None = None, load_scale: float = 1.0) -> dict:
    """material: dict(E=MPa, nu, rho=t/mm^3, yield_MPa); default Ti-6Al-4V. load_scale multiplies all four GE loads."""
    m = dict(E=E, nu=NU, rho=RHO, yield_MPa=YIELD) | (material or {})
    t0 = time.time()
    x, tets, bnodes, volume = mesh_step(step, mesh_size)
    itf = interfaces(x, bnodes)
    out = dict(step=step, nodes=len(x), tets=len(tets), volume_mm3=volume, mass_kg=volume * m["rho"] * 1e3, mesh_size=mesh_size, material=m, load_scale=load_scale,
               z_min=float(x[:, 2].min()), interfaces_ok=itf["ok"], interfaces=itf["report"])
    if not itf["ok"]:
        return dict(out, passed=False, reason="GE interfaces missing or changed", seconds=round(time.time() - t0, 1))
    loads = []
    for F, M in CASES.values():
        f = np.zeros_like(x)
        f[itf["pin"]] = sfem.rbe3_forces(x[itf["pin"]], LOAD_POINT, load_scale * F, load_scale * M)
        loads.append(f)
    U = sfem.solve(x, tets, itf["fixed"], loads, m["E"], m["nu"])
    from scipy.spatial import cKDTree
    far = cKDTree(x[np.concatenate([itf["fixed"], itf["pin"]])]).query(x)[0] > ZONE
    cnt = np.maximum(np.bincount(tets.ravel(), minlength=len(x)), 1)
    res = {}
    for name, u in zip(CASES, U):
        s = sfem.element_stress(x, tets, u, m["E"], m["nu"])
        s_avg = np.stack([np.bincount(tets.ravel(), np.repeat(s[:, i, j], 4), minlength=len(x))
                          for i in range(3) for j in range(3)], 1).reshape(-1, 3, 3) / cnt[:, None, None]
        vm = sfem.von_mises(s_avg)
        k, kz = int(np.argmax(vm)), int(np.argmax(np.where(far, vm, -1)))
        res[name] = dict(max_displacement_mm=float(np.linalg.norm(u, axis=1).max()), peak_von_mises_MPa=float(vm[kz]),
                         peak_at=x[kz].round(2).tolist(), raw_peak_von_mises_MPa=float(vm[k]), raw_peak_at=x[k].round(2).tolist())
    worst = max(r["peak_von_mises_MPa"] for r in res.values())
    return dict(out, cases=res, peak_von_mises_MPa=worst, safety_factor=m["yield_MPa"] / worst, passed=bool(worst <= m["yield_MPa"]),
                worst_case=max(res, key=lambda c: res[c]["peak_von_mises_MPa"]), seconds=round(time.time() - t0, 1))


MASS_LIMIT = 1.25  # a redesign may weigh at most 25 % more than the current design
CASE_KEYS = dict(vertical="ver", horizontal="hor", diagonal="dia", torsion="tor")


def spec_text(g: dict) -> str:
    r = g["interfaces"]
    bolts = "; ".join(f"({c[0]:.4g}, {c[1]:.4g})" for c in BOLTS)
    return ("GE jet engine bracket, Ti-6Al-4V titanium (E = 113.8 GPa, nu = 0.342, density 4.43 g/cm^3, yield strength "
            "903 MPa). Geometry: the attached STEP file, millimetres, mounting plane z = 0. Supports: four bolts through "
            f"the holes of diameter {2 * r['bolt1']['radius']:.4g} mm with vertical (+z) axes at (x, y) = {bolts}; the bolts are "
            "rigid and fully fixed, so the bolt-hole walls do not move. Loads: a pin of diameter "
            f"{2 * r['pin_radius']:.4g} mm through the two clevis lugs, axis ({PIN_AXIS[0]:.4f}, {PIN_AXIS[1]:.4f}, 0) through "
            f"({PIN_POINT[0]:.4g}, {PIN_POINT[1]:.4g}, {PIN_POINT[2]:.4g}); each load acts at the point "
            f"({LOAD_POINT[0]:.4g}, {LOAD_POINT[1]:.4g}, {LOAD_POINT[2]:.4g}) and is spread over the pin-bore walls as by an "
            "RBE3 element. Four separate linear static load cases: (1) vertical: 35,585.77 N along +z; (2) horizontal: "
            "37,809.9 N along -x; (3) diagonal, 42 degrees from vertical: (-28,276.2, 0, 31,403.9) N; (4) torsion: "
            "564,924.2 N mm about +z. Stress measure: von Mises stress of the nodal-averaged stress tensor of first-order "
            "tetrahedra of about 1.2 mm, ignoring material within 2 mm of the bolt-hole and pin-bore walls (the idealised "
            "rigid connections make stress there mesh-dependent).")


def build(a) -> None:
    meta = {r["id"]: r for r in csv.DictReader(open(a.meta))}
    graded = {r["id"]: r for r in (json.loads(line) for line in open(Path(a.graded) / "graded.jsonl")) if r.get("passed") is not None}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ok = {k: g for k, g in graded.items() if g.get("interfaces_ok")}
    def radii(g):
        r = g["interfaces"]
        return tuple(round(r[f"bolt{k}"]["radius"] or 0, 2) for k in (1, 2, 3, 4)) + (round(r["pin_radius"] or 0, 2),)
    analysis, redesign = [], []
    for k, g in sorted(ok.items(), key=lambda kv: int(kv[0])):
        m = meta[k]
        src = dict(dataset="SimJEB (doi:10.7910/DVN/XFUWJG)", design=int(k), designer=m["author"],
                   grabcad=f"https://grabcad.com/library/{m['link_name']}", category=m["category"])
        published = {c: dict(max_displacement_mm=float(m[f"max_{v}_magdisp"]), raw_peak_von_mises_MPa=float(m[f"max_{v}_stress"]))
                     for c, v in CASE_KEYS.items()}
        step = str(Path(a.cad) / f"{k}.stp")
        base = dict(source=src, step=step, mass_kg=g["mass_kg"], spec=spec_text(g), interfaces=g["interfaces"])
        analysis.append(dict(base, id=f"simjeb-analysis-{k}", family="analysis",
                             prompt=spec_text(g) + " For each load case report the maximum displacement magnitude in mm "
                             "and the peak von Mises stress in MPa, and say whether the bracket stays below yield in all four.",
                             reference=dict(cases={c: dict(max_displacement_mm=g["cases"][c]["max_displacement_mm"],
                                                           peak_von_mises_MPa=g["cases"][c]["peak_von_mises_MPa"]) for c in CASE_KEYS},
                                            passes=g["passed"], simjeb_published=published),
                             tolerance=dict(max_displacement_mm=0.10, peak_von_mises_MPa=0.15)))
        if g["passed"]:
            continue
        limit = MASS_LIMIT * g["mass_kg"]
        witness = sorted((w for w in ok.values() if w["passed"] and w["mass_kg"] <= limit and radii(w) == radii(g)),
                         key=lambda w: w["mass_kg"])
        worst = g["worst_case"]
        prompt = (spec_text(g) + f" The current design ({g['mass_kg']:.3f} kg) fails: in the {worst} case its peak von Mises "
                  f"stress is {g['cases'][worst]['peak_von_mises_MPa']:.0f} MPa (safety factor {g['safety_factor']:.2f}). "
                  "Redesign the bracket so that the peak von Mises stress stays at or below 903 MPa in all four load cases. "
                  "Keep the interfaces exactly: the four bolt holes (same diameter, position and axis, open from z = 0 through "
                  "the flange), the two clevis lugs with the same pin bore, and the gap between the lugs clear. Nothing may lie "
                  f"below z = {min(0.0, g['z_min']):.3g} mm, the part must be one solid, and its mass may be at most "
                  f"{limit:.3f} kg. Return the redesigned bracket as a STEP file in millimetres and report the per-case "
                  "maximum displacement, peak stress and the mass you computed.")
        redesign.append(dict(base, id=f"simjeb-redesign-{k}", family="redesign-to-pass", prompt=prompt,
                             current=dict(cases=g["cases"], worst_case=worst, safety_factor=g["safety_factor"],
                                          simjeb_published=published),
                             requirement=dict(peak_von_mises_max_MPa=YIELD, mass_max_kg=limit, z_min_mm=min(0.0, g["z_min"]),
                                              interface_radii=radii(g)),
                             feasible=bool(witness),
                             feasibility_witness=dict(design=int(witness[0]["id"]), mass_kg=witness[0]["mass_kg"],
                                                      safety_factor=witness[0]["safety_factor"]) if witness else None,
                             grader="python scripts/simjeb_tasks.py grade <redesign.step>"))
    for name, rows in (("analysis", analysis), ("redesign", redesign)):
        (out / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    summary = dict(graded=len(graded), interfaces_found=len(ok), analysis_tasks=len(analysis), redesign_tasks=len(redesign),
                   redesign_with_witness=sum(r["feasible"] for r in redesign),
                   passing_designs=sum(g["passed"] for g in ok.values()))
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary), flush=True)


def grade_all(a) -> None:
    """Grade every SimJEB design (subprocess per design, resumable)."""
    import subprocess
    import sys
    from concurrent.futures import ThreadPoolExecutor
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    man = out / "graded.jsonl"
    done = {json.loads(line)["id"] for line in man.open()} if man.exists() else set()
    steps = sorted(Path(a.cad).glob("*.stp"), key=lambda q: int(q.stem))
    todo = [p for p in steps if p.stem not in done]
    print(f"{len(steps)} designs, {len(todo)} to grade", flush=True)

    def one(p: Path) -> dict:
        try:
            r = subprocess.run([sys.executable, "-I", __file__, "grade", str(p)], capture_output=True, text=True, timeout=3600)
            lines = [ln for ln in r.stdout.splitlines() if ln.startswith("{")]
            row = json.loads(lines[-1]) if lines else dict(passed=None, reason="grader crashed", error=r.stderr[-300:])
        except subprocess.TimeoutExpired:
            row = dict(passed=None, reason="timeout")
        return dict(row, id=p.stem)

    with ThreadPoolExecutor(a.workers) as ex, man.open("a") as h:
        for i, row in enumerate(ex.map(one, todo), 1):
            h.write(json.dumps(row) + "\n")
            h.flush()
            print(f"{i}/{len(todo)} design {row['id']}: passed={row.get('passed')} SF={row.get('safety_factor', 0):.2f} {row.get('reason') or ''}", flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grade")
    g.add_argument("step")
    g.add_argument("--json")
    g.add_argument("--mesh-size", type=float, default=MESH_SIZE)
    g.add_argument("--material", help='JSON, e.g. {"E": 71700, "nu": 0.33, "rho": 2.81e-9, "yield_MPa": 503}')
    g.add_argument("--load-scale", type=float, default=1.0)
    b = sub.add_parser("grade-all")
    b.add_argument("--cad", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--workers", type=int, default=3)
    k = sub.add_parser("build")
    k.add_argument("--meta", required=True)
    k.add_argument("--cad", required=True)
    k.add_argument("--graded", required=True)
    k.add_argument("--out", required=True)
    a = p.parse_args()
    if a.cmd == "build":
        build(a)
    elif a.cmd == "grade-all":
        grade_all(a)
    elif a.cmd == "grade":
        r = grade(a.step, a.mesh_size, json.loads(a.material) if a.material else None, a.load_scale)
        print(json.dumps(r))
        if a.json:
            Path(a.json).write_text(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
