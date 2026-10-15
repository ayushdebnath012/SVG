"""Track A: fcVM elastic buckling tasks (HarryvL/fcVM-workbench, LGPL; original FreeCAD models, control files and
published .out results collected by the 2026-10-14 follow-up).

Correspondence: fcvm_extract.check() rebuilds each model's applied load from the FreeCAD constraints exactly as fcVM
does and matches the "Sum of loads" printed in the published output (all 14 models agree to print precision).
Admission: the published first elastic buckling factor is graded only if an independent eigenvalue study
(scripts/fcvm_buckling_check.py, FEniCSx/SLEPc on refined meshes) settles (last change < 1 %, previous < 2 %) and the
band |finest - published| / published + 2 x last change is <= 10 %; the tolerance is that band (at least 5 %).
Plastic-collapse and post-buckling load factors are not admitted (no independent elastoplastic replay).

  tmp/cq-env/bin/python scripts/cadfem_bench/fam_fcvm.py prepare      # analysis.step + setup.json per buckling case
  tmp/cq-env/bin/python scripts/cadfem_bench/fam_fcvm.py study [--workers 2]
  tmp/cq-env/bin/python scripts/cadfem_bench/fam_fcvm.py diagnose     # one fcVM-size mesh where the gap exceeds 5 % (diagnostic)
  tmp/cq-env/bin/python scripts/cadfem_bench/fam_fcvm.py assess
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

import common as C
import fcvm_extract as X

STUDY = C.ROOT / "output/fcvm-buckling-study"
FEM_PY = C.ROOT / "tmp/fenicsx/env/bin/python"
SOLVER = C.ROOT / "scripts/fcvm_buckling_check.py"
SOURCE = dict(name="fcVM workbench examples (Harry van Langen, HarryvL/fcVM-workbench)", url="https://github.com/HarryvL/fcVM-workbench",
              license="LGPL-2.1-or-later (repository); example data licence not stated separately. Local research use.", redistributable=False)
TMAX = 260_000
COMP = {"x": 0, "y": 1, "z": 2}


def buckling_cases() -> list[str]:
    return sorted(f.stem for f in (X.SRC / "freeCAD files").glob("*.FCStd") if X.published(f.stem)["buckling"])


def _edge_polyline(edge, n: int = 40) -> list:
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.TopoDS import TopoDS
    c = BRepAdaptor_Curve((getattr(TopoDS, "Edge_s", None) or TopoDS.Edge)(edge))
    t = np.linspace(c.FirstParameter(), c.LastParameter(), n)
    return [[c.Value(x).X(), c.Value(x).Y(), c.Value(x).Z()] for x in t]


def prepare(name: str, root: Path = STUDY) -> dict:
    x = X.extract(name)
    chk = X.check(x)
    assert chk["max_relative_difference"] < 2e-3, (name, chk)
    d = root / name.replace(" ", "_")
    d.mkdir(parents=True, exist_ok=True)
    C.write_step(x["shape"], d / "analysis.step")
    desc = lambda i: C.face_descriptor(x["faces"][i - 1], i)
    face_bcs, edge_bcs, loads = [], [], []
    for c in x["constraints"]:
        if c["type"] in ("ConstraintFixed", "ConstraintDisplacement"):
            comps = [0, 1, 2] if c["type"] == "ConstraintFixed" else [COMP[a] for a in c["fixed_components"]]
            assert all(v == 0.0 for v in c.get("prescribed", {}).values()), (name, c["name"], "non-zero prescribed displacement")
            faces = [desc(i) for k, i in c["targets"] if k == "Face"]
            if faces:
                face_bcs.append(dict(constraint=c["name"], components=comps, faces=faces))
            for k, i in c["targets"]:
                if k == "Edge":
                    edge_bcs.append(dict(constraint=c["name"], components=comps, edge_index=i, polyline_mm=_edge_polyline(x["edges"][i - 1])))
        elif c["type"] == "ConstraintForce":
            area = sum(desc(int(i))["area_mm2"] for i in c["face_vectors_N"])
            for i, vec in c["face_vectors_N"].items():
                loads.append(dict(constraint=c["name"], kind="traction", face=desc(int(i)),
                                  traction_MPa=(np.array(c["direction"]) * c["force_N"] / area).tolist(), resultant_N=vec))
        elif c["type"] == "ConstraintPressure":
            sign = 1.0 if c["reversed"] else -1.0
            for k, i in c["targets"]:
                loads.append(dict(constraint=c["name"], kind="pressure", face=desc(i), signed_pressure_MPa=sign * c["pressure_MPa"],
                                  resultant_N=c["face_vectors_N"][str(i)]))
    ctl = x["control"]
    body = (x["density_kg_mm3"] * np.array([ctl["grav_x"], ctl["grav_y"], ctl["grav_z"]])).tolist()
    setup = dict(name=name, E_MPa=x["E_MPa"], nu=x["nu"], density_kg_mm3=x["density_kg_mm3"], body_force_N_mm3=body,
                 gravity_m_s2=[ctl["grav_x"], ctl["grav_y"], ctl["grav_z"]], face_bcs=face_bcs, edge_bcs=edge_bcs, face_loads=loads,
                 volume_mm3=x["volume_mm3"], solids=C.shape_summary(x["shape"])["solids"], load_check=chk,
                 published_elements=x["published"]["elements"], analysis_object=x["analysis_object"])
    C.jdump(setup, d / "setup.json")
    C.jdump(dict(face_descriptors=[desc(i + 1) for i in range(len(x["faces"]))]), d / "faces.json")
    return setup


def sizes(d: Path) -> list[float]:
    s = json.loads((d / "setup.json").read_text())
    h0 = round((4.87 * s["volume_mm3"] / max(s["published_elements"], 2000)) ** (1 / 3), 4)
    cal = d / f"h-{h0:g}" / "result.json"
    if not cal.exists():
        return [h0]
    n0 = json.loads(cal.read_text())["elements"]
    out = [h0]
    for f in (0.8, 0.64, 0.51, 0.41):
        h = round(h0 * f, 4)
        if n0 * (h0 / h) ** 3 <= TMAX:
            out.append(h)
    if len(out) < 3:      # refinement capped by memory: complete the sequence with the same 0.8 ratio on the coarse side
        out += [round(h0 / f, 4) for f in (0.8, 0.64)][:3 - len(out)]
    return out


def solve(d: Path, h: float) -> None:
    out = d / f"h-{h:g}"
    if (out / "result.json").exists():
        return
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "solver.log", "w") as log:
        subprocess.run([str(FEM_PY), str(SOLVER), "--case", str(d), "--size", str(h), "--out", str(out)], stdout=log, stderr=subprocess.STDOUT,
                       timeout=3600)
    if (out / "result.json").exists():
        r = json.loads((out / "result.json").read_text())
        print(f"{d.name:22s} h={h:<8g} elements={r['elements']:>7d} lambda1={r['lambda1']} t={r['runtime_seconds']:.0f}s", flush=True)
    else:
        print(f"{d.name:22s} h={h:<8g} FAILED (see {out / 'solver.log'})", flush=True)


def diagnose(name: str) -> dict | None:
    """Diagnostic only (never used for admission): one solve at roughly fcVM's own element count, for cases whose settled
    independent value is more than 5 % from the published factor. Shows whether the gap is a coarse-mesh effect."""
    d = STUDY / name.replace(" ", "_")
    a = assess(name)
    if not a["runs"] or abs(a["runs"][-1]["lambda1"] / a["published_lambda1"] - 1) <= 0.05:
        return None
    s = json.loads((d / "setup.json").read_text())
    r0 = a["runs"][0]
    h = round(r0["h_mm"] * (r0["elements"] / max(s["published_elements"], 1)) ** (1 / 3), 4)
    out = d / f"coarse-h-{h:g}"
    if not (out / "result.json").exists():
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "solver.log", "w") as log:
            subprocess.run([str(FEM_PY), str(SOLVER), "--case", str(d), "--size", str(h), "--out", str(out)], stdout=log, stderr=subprocess.STDOUT, timeout=3600)
    if not (out / "result.json").exists():
        return None
    r = json.loads((out / "result.json").read_text())
    return dict(h_mm=h, elements=r["elements"], lambda1=r["lambda1"], published_elements=s["published_elements"])


def study(workers: int) -> None:
    dirs = [STUDY / n.replace(" ", "_") for n in buckling_cases()]
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda d: solve(d, sizes(d)[0]), dirs))
    jobs = [(d, h) for d in dirs for h in sizes(d)[1:]]
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda j: solve(*j), jobs))


def _coarse_note(rec: dict, pub: float) -> str:
    """Describe the fcVM-size diagnostic by how much of the finest-mesh gap it closes (it never changes the decision)."""
    cd = rec.get("coarse_diagnostic")
    if not cd or not rec["runs"]:
        return ""
    c, fine = cd[0], rec["runs"][-1]["lambda1"]
    closure = (c["lambda1"] - fine) / (pub - fine) if pub != fine else 1.0
    seq = [c["lambda1"]] + [r["lambda1"] for r in rec["runs"]]          # coarse -> fine
    steps = np.sign(np.diff(seq))
    if len(set(steps[steps != 0])) > 1:
        return (f"; a diagnostic solve on a coarser mesh ({c['elements']} elements; fcVM used {c['published_elements']}) gives {c['lambda1']:.4g}, but the "
                "independent factor is non-monotonic under refinement (strongly mesh-dependent), so no cause is assigned")
    verdict = ("most of the gap closes on coarsening, consistent with a coarse-mesh published value" if closure >= 0.5 else
               "part of the gap closes on coarsening, so the published value is at least partly a coarse-mesh value" if closure >= 0.2 else
               "coarsening barely moves it, so mesh size does not explain the gap and the set-up correspondence beyond the load sum is unresolved")
    return (f"; a diagnostic solve on a coarser mesh ({c['elements']} elements; fcVM used {c['published_elements']}) gives {c['lambda1']:.4g}: {verdict}")


def assess(name: str) -> dict:
    d = STUDY / name.replace(" ", "_")
    pub = X.published(name)["buckling"][0]
    runs = sorted((json.loads(f.read_text()) for f in d.glob("h-*/result.json")), key=lambda r: -r["mesh_size_mm"])
    runs = [r for r in runs if r.get("lambda1")]
    rec = dict(case=name, published_lambda1=pub, runs=[dict(h_mm=r["mesh_size_mm"], elements=r["elements"], lambda1=r["lambda1"]) for r in runs])
    coarse = [json.loads(f.read_text()) for f in d.glob("coarse-h-*/result.json")]
    if coarse:
        pe = json.loads((d / "setup.json").read_text())["published_elements"]
        rec["coarse_diagnostic"] = [dict(h_mm=c["mesh_size_mm"], elements=c["elements"], lambda1=c["lambda1"], published_elements=pe,
                                         note="diagnostic at about fcVM's element count; not used for admission") for c in coarse]
    if len(runs) < 3:
        cap = ""
        why = f"only {len(runs)} mesh(es) solved{cap}; no settled independent value"
        if runs:
            why += f" (finest {runs[-1]['lambda1']:.5g}, {100 * (runs[-1]['lambda1'] / pub - 1):+.1f} % from the published factor {pub:g})"
        return rec | dict(decision="hold", reason=why + _coarse_note(rec, pub))
    lam = [r["lambda1"] for r in runs]
    last, prev = abs(lam[-1] - lam[-2]) / abs(lam[-1]), abs(lam[-2] - lam[-3]) / abs(lam[-2])
    diff = (lam[-1] - pub) / pub
    band = max(0.05, math.ceil((abs(diff) + 2 * last * abs(lam[-1] / pub)) * 100) / 100)
    rec.update(finest=lam[-1], relative_difference=diff, last_change=last, previous_change=prev, band=band)
    if last >= 0.01 or prev >= 0.02:
        return rec | dict(decision="hold", reason=f"independent buckling factor not settled (last change {100 * last:.2f} %, previous {100 * prev:.2f} %; "
                                                  f"finest {lam[-1]:.5g}, {100 * diff:+.1f} % from the published factor {pub:g})" + _coarse_note(rec, pub))
    if band > 0.10:
        why = f"settled independent value {lam[-1]:.5g} is {100 * diff:+.1f} % from the published factor {pub:g} (band {100 * band:.0f} % > 10 %)"
        return rec | dict(decision="hold", reason=why + _coarse_note(rec, pub))
    return rec | dict(decision="admit", reason="settled independent value within the band")


# ---------------------------------------------------------------- v1.5: plastic limit loads (perfect plasticity, geometric linear)
PLASTIC_STUDY = C.ROOT / "output/fcvm-plastic-study"
PLASTIC_SOLVER = C.ROOT / "scripts/fcvm_plastic_check.py"
# Mesh sequences (element size x0.8 per step) and, where fcVM's mesh is much coarser, one diagnostic near its element count.
PLASTIC = {"tensile": dict(sizes=[2.5, 2.0, 1.6]),
           "transition": dict(sizes=[14.3, 11.44, 9.15], diagnostic=25.0),
           "Wyk_Rohrstoss_ring": dict(sizes=[12.0, 9.6, 7.68])}
# The other plastic fcVM outputs end before the load-displacement curve flattens: their peak is not a limit load.
PLASTIC_NOT_LIMIT = ["Lug_Pressure_Example", "barrier", "train_bridge"]


def plastic_solve(name: str, h: float, kind: str = "h") -> None:
    d = PLASTIC_STUDY / name
    out = d / f"{kind}-{h:g}"
    if (out / "result.json").exists():
        return
    out.mkdir(parents=True, exist_ok=True)
    sy = X.control(name)["sig_yield"]
    with open(out / "solver.log", "w") as log:
        subprocess.run([str(FEM_PY), str(PLASTIC_SOLVER), "--case", str(d), "--size", str(h), "--sigma-y", str(sy), "--out", str(out)],
                       stdout=log, stderr=subprocess.STDOUT, timeout=4 * 3600)
    if (out / "result.json").exists():
        r = json.loads((out / "result.json").read_text())
        print(f"{name:22s} {kind}={h:<6g} elements={r['elements']:>7d} limit={r['lambda_limit']} bracket=[{r['lambda_last_converged']:.5g}, "
              f"{r['lambda_first_failed']}] t={r['runtime_seconds']:.0f}s", flush=True)
    else:
        print(f"{name:22s} {kind}={h:<6g} FAILED (see {out / 'solver.log'})", flush=True)


def plastic_study(workers: int) -> None:
    for n in PLASTIC:
        if not (PLASTIC_STUDY / n / "setup.json").exists():
            prepare(n, PLASTIC_STUDY)

    def chain(n):
        for h in PLASTIC[n]["sizes"]:
            plastic_solve(n, h)
        if "diagnostic" in PLASTIC[n]:
            plastic_solve(n, PLASTIC[n]["diagnostic"], "coarse")
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(chain, ["Wyk_Rohrstoss_ring", "transition", "tensile"]))


def published_limit(name: str) -> dict:
    rows = X.published(name)["rows"]
    lf = [r[4] for r in rows]
    m = max(lf)
    near = [k for k in range(len(lf)) if lf[k] >= 0.99 * m]
    return dict(value=m, rows_within_1pct=len(near), displacement_growth_on_plateau=rows[near[-1]][5] / max(rows[near[0]][5], 1e-12))


def plastic_assess(name: str) -> dict:
    d = PLASTIC_STUDY / name
    pl = published_limit(name)
    pub = pl["value"]
    runs = sorted((json.loads(f.read_text()) for f in d.glob("h-*/result.json")), key=lambda r: -r["mesh_size_mm"])
    runs = [r for r in runs if r.get("lambda_limit")]
    rec = dict(case=name, published_limit_factor=pub, published_plateau=pl, sigma_y_MPa=X.control(name)["sig_yield"],
               runs=[dict(h_mm=r["mesh_size_mm"], elements=r["elements"], lambda_limit=r["lambda_limit"], bracket=[r["lambda_last_converged"], r["lambda_first_failed"]])
                     for r in runs])
    coarse = [json.loads(f.read_text()) for f in d.glob("coarse-*/result.json")]
    if coarse:
        rec["coarse_diagnostic"] = [dict(h_mm=c["mesh_size_mm"], elements=c["elements"], lambda1=c["lambda_limit"],
                                         published_elements=X.published(name)["elements"], note="diagnostic near fcVM's element count; not used for admission")
                                    for c in coarse if c.get("lambda_limit")]
    if len(runs) < 3:
        return rec | dict(decision="hold", reason=f"only {len(runs)} mesh(es) bracketed the limit load; no settled independent value")
    lam = [r["lambda_limit"] for r in runs]
    last, prev = abs(lam[-1] - lam[-2]) / abs(lam[-1]), abs(lam[-2] - lam[-3]) / abs(lam[-2])
    diff = (lam[-1] - pub) / pub
    band = max(0.05, math.ceil((abs(diff) + 2 * last * abs(lam[-1] / pub)) * 100) / 100)
    rec.update(finest=lam[-1], relative_difference=diff, last_change=last, previous_change=prev, band=band)
    note = _coarse_note({"coarse_diagnostic": [dict(c, lambda1=c["lambda1"]) for c in rec.get("coarse_diagnostic", [])],
                         "runs": [dict(lambda1=x["lambda_limit"]) for x in rec["runs"]]}, pub) if rec.get("coarse_diagnostic") else ""
    if last >= 0.01 or prev >= 0.02:
        return rec | dict(decision="hold", reason=f"independent limit load not settled (last change {100 * last:.2f} %, previous {100 * prev:.2f} %; "
                                                  f"finest {lam[-1]:.4g}, {100 * diff:+.1f} % from the published factor {pub:g})" + note)
    if band > 0.10:
        return rec | dict(decision="hold", reason=f"settled independent limit load {lam[-1]:.4g} is {100 * diff:+.1f} % from the published factor {pub:g} "
                                                  f"(band {100 * band:.0f} % > 10 %)" + note)
    return rec | dict(decision="admit", reason="settled independent limit load within the band")


def build() -> list:
    rows = []
    for name in buckling_cases():
        a = assess(name)
        d = STUDY / name.replace(" ", "_")
        C.jdump(a, d / "assessment.json")     # apply_bands.py holds the task unless a["decision"] == "admit"
        s = json.loads((d / "setup.json").read_text())
        tid = "A-FCVM-" + name.replace(" ", "_")
        inputs = [C.put(tid, d / "analysis.step", "analysis.step"), C.put(tid, d / "faces.json", "faces.json", role="spec")]
        ax = "xyz"
        sup = []
        for b in s["face_bcs"]:
            comps = "all displacement components" if len(b["components"]) == 3 else "displacement " + ", ".join("u_" + ax[c] for c in b["components"])
            sup.append(f"{comps} = 0 on {C.describe_faces(b['faces'])}")
        for e in s["edge_bcs"]:
            comps = "all displacement components" if len(e["components"]) == 3 else "displacement " + ", ".join("u_" + ax[c] for c in e["components"])
            p0, p1 = np.round(e["polyline_mm"][0], 3).tolist(), np.round(e["polyline_mm"][-1], 3).tolist()
            sup.append(f"{comps} = 0 along the edge from {tuple(p0)} to {tuple(p1)} mm (edge {e['edge_index']} of analysis.step)")
        lds = []
        for l in s["face_loads"]:
            if l["kind"] == "traction":
                lds.append(f"uniform traction {tuple(np.round(l['traction_MPa'], 6).tolist())} MPa on {C.describe_faces([l['face']])}")
            else:
                lds.append(f"pressure {abs(l['signed_pressure_MPa']):g} MPa {'pushing into' if l['signed_pressure_MPa'] < 0 else 'pulling out of'} "
                           f"the material on {C.describe_faces([l['face']])}")
        g = s["gravity_m_s2"]
        grav = (f"Self-weight is part of the reference load: density {s['density_kg_mm3'] * 1e9:g} kg/m^3, gravity {tuple(g)} m/s^2 "
                f"(body force {tuple(np.round(s['body_force_N_mm3'], 9).tolist())} N/mm^3)." if any(g) else "No self-weight.")
        prompt = f"""Linear (eigenvalue) buckling analysis of a steel structure from the fcVM workbench examples ({name}). analysis.step holds the analysis geometry in millimetres ({s['solids']} solid region(s) that share their interfaces and act as one continuous body, volume {s['volume_mm3']:.0f} mm^3). faces.json describes every face (index, type, area, centroid, normal/axis).
Material: linear isotropic elastic, E = {s['E_MPa']:g} MPa, Poisson ratio {s['nu']:g}.
Supports: {' '.join(f'({k + 1}) {x}.' for k, x in enumerate(sup))}
Reference load set (load factor 1): {' '.join(f'({k + 1}) {x}.' for k, x in enumerate(lds))} {grav}
Analysis: compute the linear prebuckling stress state under the reference load set, then the elastic buckling load factors lambda (eigenvalues of K + lambda K_G = 0, the whole reference load set scaled by lambda). Report the smallest positive one."""
        outs = [C.out("lambda1", "-", "first (smallest positive) elastic buckling load factor of the reference load set")]
        refs = dict(lambda1=C.refv(a["published_lambda1"], "scalar", "published_table", f"fcVM output files/{name}.out header 'elastic buckling factors'",
                                   tol=a.get("band", 0.05), note="tolerance from an independent eigenvalue convergence study"))
        if "finest" in a:
            refs["lambda1"]["independent_finest"] = a["finest"]
        rows.append(C.task(tid, "A", "gold", "fcvm-buckling", f"fcVM {name}: elastic buckling factor", ["linear buckling", "eigenvalue"],
                           prompt, inputs, outs, SOURCE, dict(solids=s["solids"], assembly=s["solids"] > 1), refs,
                           flags=[f"load set matches the published fcVM load sums (max relative difference {s['load_check']['max_relative_difference']:.1e})",
                                  f"independent finest-mesh factor {a['finest']:.5g} vs published {a['published_lambda1']:g} ({100 * a['relative_difference']:+.1f} %), "
                                  f"last refinement change {100 * a['last_change']:.2f} %" if "finest" in a else "no settled independent value"],
                           extra_eval=dict(fcvm_assessment=a)))
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prepare", "study", "assess", "diagnose", "plastic-study", "plastic-assess"])
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    if a.cmd == "prepare":
        for n in buckling_cases():
            s = prepare(n)
            print(f"{n:22s} solids={s['solids']:3d} face_bcs={len(s['face_bcs'])} edge_bcs={len(s['edge_bcs'])} loads={len(s['face_loads'])} "
                  f"load_check={s['load_check']['max_relative_difference']:.1e} body={np.round(s['body_force_N_mm3'], 9).tolist()}", flush=True)
    elif a.cmd == "study":
        study(a.workers)
    elif a.cmd == "plastic-study":
        plastic_study(a.workers)
    elif a.cmd == "plastic-assess":
        for n in PLASTIC:
            r = plastic_assess(n)
            print(f"{n:22s} {r['decision']:5s} pub={r['published_limit_factor']:<8g} finest={r.get('finest')} band={r.get('band')} | {r['reason']}")
    elif a.cmd == "diagnose":
        for n in buckling_cases():
            print(f"{n:22s} {diagnose(n)}", flush=True)
    else:
        for n in buckling_cases():
            r = assess(n)
            print(f"{n:22s} {r['decision']:5s} pub={r['published_lambda1']:<10g} finest={r.get('finest')} band={r.get('band')} | {r['reason']}")
