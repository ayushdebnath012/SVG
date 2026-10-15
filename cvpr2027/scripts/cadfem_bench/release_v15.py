"""Assemble CADFEM-Bench v1.5: the v1.4 suite release plus two new physics families, each admitted only after an
independent check. Every v1.4 task, target, tolerance and suite assignment is carried over unchanged.

New families (primary suite unless stated; at most five tasks per family):
- fcvm-plastic-limit (plasticity): fcVM's published elastic-perfectly plastic collapse load factors, for the models whose
  published load-displacement curve ends on a flat plateau. Each load set is rebuilt from the FreeCAD constraints and
  matches the published load sum (fcvm_extract.py). Independent check: FEniCSx limit analysis on refined meshes
  (scripts/fcvm_plastic_check.py, output/fcvm-plastic-study/), with the same settling rule and band as the buckling
  family. The tensile bar has a closed-form limit and goes to the calibration suite.
- interface-crack-fracture (linear-elastic fracture): Code_Aster validation test SSLP311. A central crack lies on an
  inclined bimaterial interface in a finite plate under tension, and G is the energy release rate at both tips. The
  reference is the published boundary-element solution (Miyazaki et al. 1993) as tabulated by the source. G for
  theta = 15 deg is stated directly in the source test; for 30/45/60 deg it follows from the source's tabulated F_I,
  F_II with the source's own G formula, which reproduces the two directly stated values to 1e-6. Independent check:
  FEniCSx J-integral study on five mesh levels (scripts/interface_crack_g.py, output/interface-crack-study/).

  tmp/cq-env/bin/python scripts/cadfem_bench/release_v15.py            # assemble output/datasets/cadfem-bench-v1.5
  CADFEM_BENCH_OUT=... CADFEM_BENCH_VERSION=1.5 tmp/cq-env/bin/python scripts/cadfem_bench/finish_suites.py --copy-to ~/SVG
"""
from __future__ import annotations

import collections
import hashlib
import json
import math
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "output/datasets/cadfem-bench-v1.4"
OUT = ROOT / "output/datasets/cadfem-bench-v1.5"
os.environ.update(CADFEM_BENCH_OUT=str(OUT), CADFEM_BENCH_VERSION="1.5")

import common as C          # noqa: E402
import fam_fcvm as F        # noqa: E402
import fcvm_extract as X    # noqa: E402

FOLLOW = ROOT.parent / "cadfem-bench-v1.1-followup/published-source-expansion"
CRACK = ROOT / "output/interface-crack-study"
ASTER_DOC = ROOT / "tmp/fem-expansion-50/codeaster/SSLP311/docs"
ASTER_SRC = ROOT / "tmp/published-fem-expansion-50/SSLP311"
ASTER_REC = ROOT / "data/published-fem-expansion-50/records/SSLP311.json"
ASTER_LIC = ROOT / "data/published-fem-expansion-50/LICENSE-Code_Aster"
SUFFIX = ("\n\nSubmit results.json containing exactly an outputs object with these numeric keys. Also submit main.py, part.step, mesh.msh, "
          "fields.npz, solver.log, refinement.json and environment.json. See candidate README for the artifact contract. Correct numerical "
          "answers alone do not establish workflow completion.")
ARTIFACTS = ["results.json", "main.py", "part.step", "mesh.msh", "fields.npz", "solver.log", "refinement.json", "environment.json"]
FCVM_SOURCE = F.SOURCE
ASTER_SOURCE = dict(name="Code_Aster validation test SSLP311 (EDF R&D), reference solution Miyazaki, Ikeda, Soda & Munakata, Eng. Fract. Mech. 45 (1993) 599-610",
                    url="https://codeaster.gitlab.io/doc/docaster/manuals/man_v/v3/v3.02.311/index.html",
                    license="Code_Aster sources GPL-3.0 (see LICENSE-Code_Aster); documentation (c) EDF R&D. Local research use.", redistributable=False)
# Published boundary-element factors (V-doc v3.02.311 section 2.2, contour-integral method): theta -> ((F_I, F_II) left tip, (F_I, F_II) right tip)
SSLP311_F = {15: ((1.0115, 0.4434), (1.1266, 0.0862)), 30: ((0.7868, 0.6244), (0.9910, 0.2961)),
             45: ((0.5211, 0.6723), (0.7646, 0.4056)), 60: ((0.2770, 0.5804), (0.4919, 0.4057))}
SSLP311_STATED = {"right": 101.2506, "left": 96.7362}       # sslp311a.comm VALE_REFE (theta = 15 deg; FOND1 = right tip)


def jl(p: Path) -> list:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def wjl(p: Path, rows: list) -> None:
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))


def finish_prompt(body: str, outputs: list) -> str:
    return body.strip() + "\n\nOutputs:\n" + "\n".join(f"- {o['key']} [{o['unit']}]: {o['definition']}" for o in outputs) + SUFFIX


def record(tid, track, tier, family, title, physics, body, inputs, outputs, complexity, source, refs, flags, reproduced, extra=None):
    t = dict(task_id=tid, track=track, tier=tier, family=family, title=title, physics=physics, prompt=finish_prompt(body, outputs),
             inputs=inputs, outputs=outputs, complexity=complexity,
             source=dict(name=source["name"], url=source["url"], license=source["license"], redistributable=source["redistributable"]),
             status="active", engineering_family=family,
             readiness=dict(independently_reproduced=reproduced, workflow_scoring="trusted_review_required",
                            tolerances="convergence_study" if reproduced else "provisional_source_protocol"),
             required_artifacts=ARTIFACTS)
    r = dict(task_id=tid, grader="numeric", tier=tier, family=family, track=track, references=refs, flags=flags, source=t["source"],
             status="active", engineering_family=family)
    r.update(extra or {})
    return t, r


# ---------------------------------------------------------------- evidence bundle
class Evidence:
    def __init__(self):
        self.man = jl(C.EVAL / "evidence-manifest.jsonl")
        self.have = {m["path"]: m for m in self.man}

    def add(self, src: Path, rel: str, role: str) -> str:
        src = Path(src)
        assert src.is_file(), src
        dst = C.EVAL / "evidence" / rel
        path = str(dst.relative_to(C.EVAL))
        if path in self.have:
            assert self.have[path]["sha256"] == C.sha256(src), path
            return path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        m = dict(path=path, sha256=C.sha256(dst), bytes=dst.stat().st_size, original_workspace_path=str(src.resolve().relative_to(ROOT.parent)), role=role)
        self.man.append(m)
        self.have[path] = m
        return path

    def save(self):
        wjl(C.EVAL / "evidence-manifest.jsonl", self.man)


# ---------------------------------------------------------------- fcVM plastic limit loads
def setup_text(s: dict) -> tuple[str, str]:
    """Support and load wording of fam_fcvm.build() (same descriptors, same conventions)."""
    import numpy as np
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
    return " ".join(f"({k + 1}) {x}." for k, x in enumerate(sup)), " ".join(f"({k + 1}) {x}." for k, x in enumerate(lds))


def plastic_family(ev: Evidence) -> tuple[list, list, list]:
    """Returns (primary rows, calibration rows, held rows) as (task, ref) pairs."""
    prim, cal, held = [], [], []
    for name in F.PLASTIC:
        a = F.plastic_assess(name)
        d = F.PLASTIC_STUDY / name
        C.jdump(a, d / "assessment.json")
        s = json.loads((d / "setup.json").read_text())
        assert not any(s["gravity_m_s2"]), name
        tid = "A-FCVM-PL-" + name
        inputs = [C.put(tid, d / "analysis.step", "analysis.step"), C.put(tid, d / "faces.json", "faces.json", role="spec")]
        sup, lds = setup_text(s)
        body = f"""Plastic collapse (limit load) analysis of a steel part from the fcVM workbench examples ({name}). analysis.step holds the analysis geometry in millimetres ({s['solids']} solid region(s) that share their interfaces and act as one continuous body, volume {s['volume_mm3']:.0f} mm^3). faces.json describes every face (index, type, area, centroid, normal/axis).
Material: elastic-perfectly plastic von Mises (associated flow, no hardening), E = {s['E_MPa']:g} MPa, Poisson ratio {s['nu']:g}, yield stress {a['sigma_y_MPa']:g} MPa. Small strains and small displacements (geometrically linear).
Supports: {sup}
Reference load set (load factor 1): {lds} No self-weight.
Analysis: scale the whole reference load set proportionally by a load factor lambda and find the plastic collapse (limit) load factor, the largest lambda for which equilibrium exists (the load-displacement curve becomes flat)."""
        outs = [C.out("limit_load_factor", "-", "plastic collapse (limit) load factor of the reference load set")]
        pl = a["published_plateau"]
        ref = C.refv(a["published_limit_factor"], "scalar", "published_table",
                     f"fcVM output files/{X.SRC.joinpath('output files', name + '.out').name} 'load' column: maximum, on a flat plateau "
                     f"({pl['rows_within_1pct']} printed rows within 1 % of it while the displacement grows {pl['displacement_growth_on_plateau']:.1f}x)",
                     tol=a.get("band", 0.05), note="tolerance from an independent limit-analysis convergence study")
        ref["tol"]["basis"] = "independent limit-analysis convergence study (evaluator evidence), not a certified uncertainty bound"
        if "finest" in a:
            ref["independent_finest"] = a["finest"]
        files = [ev.add(FOLLOW / "freeCAD files" / f"{name}.FCStd", f"fcvm/freeCAD files/{name}.FCStd", "original_source"),
                 ev.add(FOLLOW / "control files" / f"{name}.inp", f"fcvm/control files/{name}.inp", "original_source"),
                 ev.add(FOLLOW / "output files" / f"{name}.out", f"fcvm/output files/{name}.out", "original_source")]
        files += [ev.add(FOLLOW / f, f"fcvm/{f}", "source_metadata_or_notice") for f in ("README.md", "catalog.json", "download-manifest.json")]
        files += [ev.add(f, f"fcvm-plastic-study/{name}/{f.relative_to(d)}", "tolerance_evidence")
                  for f in [d / "setup.json", d / "assessment.json", *sorted(d.glob("h-*/result.json")), *sorted(d.glob("coarse-*/result.json"))]]
        files += [ev.add(ROOT / p, f"fcvm-plastic-study/code/{Path(p).name}", "tolerance_evidence_code")
                  for p in ("scripts/fcvm_plastic_check.py", "scripts/cadfem_bench/fam_fcvm.py", "scripts/cadfem_bench/fcvm_extract.py")]
        calib = name == "tensile"
        flags = [f"load set matches the published fcVM load sums (max relative difference {s['load_check']['max_relative_difference']:.1e})"]
        if "finest" in a:
            flags.append(f"independent finest-mesh limit factor {a['finest']:.4g} vs published {a['published_limit_factor']:g} "
                         f"({100 * a['relative_difference']:+.1f} %), last refinement change {100 * a['last_change']:.2f} %")
        if calib:
            flags.append("closed form: uniform bar, limit factor = yield stress x cross-section / applied force = 0.5; calibration only")
        admitted = a["decision"] == "admit"
        if admitted:
            flags.append("Independently reproduced in this release (evaluator evidence); an end-to-end pass still requires evaluator-owned workflow review.")
        t, r = record(tid, "A", "control" if calib else "source_backed_pilot", "fcvm-plastic-limit", f"fcVM {name}: plastic collapse load factor",
                      ["elastoplastic", "limit analysis", "von Mises perfect plasticity"], body, inputs, outs,
                      dict(solids=s["solids"], assembly=s["solids"] > 1), FCVM_SOURCE, dict(limit_load_factor=ref), flags, admitted,
                      dict(plastic_assessment=a, evidence_files=sorted(set(files))))
        if not admitted:
            t["status"] = r["status"] = "held"
            t["hold_reason"] = r["hold_reason"] = f"Independent limit-analysis study: {a['reason']}."
            held.append((t, r))
        else:
            (cal if calib else prim).append((t, r))
    return prim, cal, held


# ---------------------------------------------------------------- Code_Aster SSLP311 interface crack
def sslp311_beta() -> float:
    nu, E1, E2 = 0.3, 2e12, 2e11
    k = (3 - nu) / (1 + nu)
    m1, m2 = E1 / (2 * (1 + nu)), E2 / (2 * (1 + nu))
    al = 1 / (2 * math.pi) * math.log((k / m1 + 1 / m2) / (k / m2 + 1 / m1))
    return 1 / (16 * math.cosh(al * math.pi) ** 2) * ((1 + k) / m1 + (1 + k) / m2)


def sslp311_G() -> dict:
    """G (J/m^2) from the published factors with the source formula G = beta (K_I^2 + K_II^2), K = F sigma_0 sqrt(pi a)."""
    beta, s0, a = sslp311_beta(), 1e8, 1e-3
    G = {th: {tip: beta * s0 ** 2 * math.pi * a * (f[0] ** 2 + f[1] ** 2) for tip, f in zip(("left", "right"), v)} for th, v in SSLP311_F.items()}
    for tip, v in SSLP311_STATED.items():
        assert abs(G[15][tip] - v) / v < 2e-6, (tip, G[15][tip], v)
    return G


def crack_cad(theta: float, path: Path, t: float = 0.1) -> dict:
    import cadquery as cq
    th = math.radians(theta)
    W, H, a = 2.0, 4.0, 1.0
    yE = W * math.tan(th)
    c, s = math.cos(th), math.sin(th)
    EL, ER, TL, TR, BL, BR, L, R = (-W, -yE), (W, yE), (-W, H), (W, H), (-W, -H), (W, -H), (-a * c, -a * s), (a * c, a * s)
    s1 = cq.Workplane("XY").polyline([EL, L, R, ER, TR, TL]).close().extrude(t, clean=False).val()   # keep the crack face separate
    s2 = cq.Workplane("XY").polyline([BL, BR, ER, R, L, EL]).close().extrude(t, clean=False).val()
    comp = cq.Compound.makeCompound([s1, s2]).wrapped
    C.write_step(comp, path)
    back = C.read_shape(path)
    summ = C.shape_summary(back)
    assert summ["valid"] and summ["solids"] == 2 and abs(summ["volume_mm3"] - 2 * W * 2 * H * t) < 1e-9, summ
    desc = [C.face_descriptor(f, i + 1) for i, f in enumerate(C.faces(back))]
    n_up = (-s, c, 0.0)                 # normal of the interface line pointing into material 1

    def find(pred):
        hits = [d for d in desc if d["type"] == "plane" and pred(d)]
        assert len(hits) == 1, [h["face_index"] for h in hits]
        return hits[0]
    on_crack = lambda d: abs(d["centroid_mm"][0]) < 1e-6 and abs(d["centroid_mm"][1]) < 1e-6 and abs(d["area_mm2"] - 2 * a * t) < 1e-6
    crack1 = find(lambda d: on_crack(d) and sum(x * y for x, y in zip(d["outward_normal"], n_up)) < -0.99)   # material-1 crack face
    crack2 = find(lambda d: on_crack(d) and sum(x * y for x, y in zip(d["outward_normal"], n_up)) > 0.99)
    top = find(lambda d: abs(d["centroid_mm"][1] - H) < 1e-6 and d["outward_normal"][1] > 0.99)
    bot = find(lambda d: abs(d["centroid_mm"][1] + H) < 1e-6 and d["outward_normal"][1] < -0.99)
    C.jdump(dict(face_descriptors=desc, solids={"1": "material 1 (above the interface line)", "2": "material 2 (below it)"},
                 note="Faces of solid 1 are listed before those of solid 2 (OpenCASCADE order of the STEP compound)."), path.parent / "faces.json")
    return dict(crack1=crack1, crack2=crack2, top=top, bottom=bot, tipR=(a * c, a * s), tipL=(-a * c, -a * s), summary=summ)


def crack_assess(theta: int, G: dict) -> dict:
    tips = {}
    for tip in ("right", "left"):
        runs = [json.loads((CRACK / f"theta-{theta}/level-{l}/result.json").read_text()) for l in range(5)]
        v = [r["G"][tip]["G_J_per_m2"] for r in runs]
        last, prev = abs(v[-1] - v[-2]) / v[-1], abs(v[-2] - v[-3]) / v[-2]
        pub = G[theta][tip]
        diff = (v[-1] - pub) / pub
        band = max(0.05, math.ceil((abs(diff) + 2 * last * abs(v[-1] / pub)) * 100) / 100)
        tips[tip] = dict(published_G=pub, levels=[dict(level=r["level"], cells=r["cells"], G=x, ring_spread=r["G"][tip]["ring_spread"]) for r, x in zip(runs, v)],
                         finest=v[-1], relative_difference=diff, last_change=last, previous_change=prev, band=band,
                         settled=last < 0.01 and prev < 0.02)
    ok = all(x["settled"] and x["band"] <= 0.10 for x in tips.values())
    return dict(theta_deg=theta, tips=tips, decision="admit" if ok else "hold",
                reason="settled independent G within the band at both tips" if ok else "independent G not settled or outside the 10 % band")


def crack_family(ev: Evidence) -> tuple[list, list]:
    G = sslp311_G()
    deriv = dict(formula="G = beta (K_I^2 + K_II^2), K_j = F_j sigma_0 sqrt(pi a); beta = (1/(16 cosh^2(alpha pi))) ((1+kappa_1)/mu_1 + (1+kappa_2)/mu_2), "
                         "kappa_i = (3 - nu_i)/(1 + nu_i) (plane stress), alpha = (1/2pi) ln[(kappa_1/mu_1 + 1/mu_2)/(kappa_2/mu_2 + 1/mu_1)] (V-doc 2.2)",
                 beta_per_Pa=sslp311_beta(), published_F=SSLP311_F, G_J_per_m2=G, stated_theta15=SSLP311_STATED,
                 check="the formula reproduces both G values stated in sslp311a.comm (theta = 15 deg) to better than 2e-6")
    study_ev = CRACK / "reference-derivation.json"
    C.jdump(deriv, study_ev)
    common = [ev.add(study_ev, "interface-crack/reference-derivation.json", "reference_derivation")]
    common += [ev.add(ASTER_DOC / f, f"interface-crack/v-doc/{f}", "original_source")
               for f in ("index.html", "Probl_me_de_r_f_rence.html", "Solution_de_r_f_rence.html", "Mod_lisation_A.html", "Synth_se_des_r_sultats.html")]
    common += [ev.add(ASTER_SRC / "figures/geometry-01.png", "interface-crack/v-doc/geometry-01.png", "original_source")]
    common += [ev.add(ASTER_SRC / "original" / f, f"interface-crack/original/{f}", "original_source")
               for f in ("sslp311a.comm", "sslp311a.datg", "sslp311a.export", "sslp311a.mmed")]
    common += [ev.add(ASTER_REC, "interface-crack/SSLP311-record.json", "source_metadata_or_notice"),
               ev.add(ASTER_LIC, "interface-crack/LICENSE-Code_Aster", "source_metadata_or_notice"),
               ev.add(ROOT / "scripts/interface_crack_g.py", "interface-crack/code/interface_crack_g.py", "tolerance_evidence_code"),
               ev.add(HERE / "release_v15.py", "interface-crack/code/release_v15.py", "tolerance_evidence_code")]
    prim, held = [], []
    for th in (15, 30, 45, 60):
        a = crack_assess(th, G)
        C.jdump(a, CRACK / f"theta-{th}/assessment.json")
        tid = f"A-ASTER-SSLP311-theta{th}"
        tdir = C.CAND / "tasks" / tid
        tdir.mkdir(parents=True, exist_ok=True)
        geo = crack_cad(th, tdir / "plate.step")
        inputs = [dict(path=str(p.relative_to(C.CAND)), role=role, bytes=p.stat().st_size, sha256=C.sha256(p))
                  for p, role in ((tdir / "plate.step", "cad"), (tdir / "faces.json", "spec"))]
        files = common + [ev.add(f, f"interface-crack/study/theta-{th}/{f.relative_to(CRACK / f'theta-{th}')}", "tolerance_evidence")
                          for f in [CRACK / f"theta-{th}/assessment.json", *sorted((CRACK / f"theta-{th}").glob("level-*/result.json"))]]
        f1, f2 = geo["crack1"]["face_index"], geo["crack2"]["face_index"]
        tR, tL = (round(x, 6) for x in geo["tipR"]), (round(x, 6) for x in geo["tipL"])
        tR, tL = tuple(tR), tuple(tL)
        body = f"""Linear-elastic fracture analysis of a central crack lying on an inclined bimaterial interface in a finite plate under uniform tension (Code_Aster validation test SSLP311). plate.step holds the plate in millimetres as two solids: solid 1 (material 1) above the interface line and solid 2 (material 2) below it. The 2-D domain is extruded 0.1 mm along +z from z = 0 only as an exchange convention; analyse the z = 0 cross-section as a 2-D plane-stress problem. faces.json describes every face (index, type, area, centroid, normal).
Geometry: the plate occupies x from -2 to 2 mm and y from -4 to 4 mm. The interface is the straight line through the origin at {th} degrees to the +x axis. The crack is the 2 mm long segment of that line centred on the origin, with tips at {tR} mm (right tip) and {tL} mm (left tip). Its faces (face {f1} of solid 1 and face {f2} of solid 2) are traction-free and not connected; the rest of the interface is perfectly bonded.
Materials: solid 1 E = 2.0e6 MPa, Poisson ratio 0.3; solid 2 E = 2.0e5 MPa, Poisson ratio 0.3. Linear elastic, small strain.
Loads and supports: uniform traction sigma_yy = 100 MPa on the top edge y = 4 mm (face {geo['top']['face_index']}); u_y = 0 on the bottom edge y = -4 mm (face {geo['bottom']['face_index']}); u_x = 0 at the bottom-left corner (x, y) = (-2, -4) mm.
Analysis: compute the energy release rate G (J-integral) at each crack tip, per unit thickness."""
        outs = [C.out("G_right_tip", "J/m^2", f"energy release rate at the crack tip {tR} mm"),
                C.out("G_left_tip", "J/m^2", f"energy release rate at the crack tip {tL} mm")]
        refs = {}
        for key, tip in (("G_right_tip", "right"), ("G_left_tip", "left")):
            x = a["tips"][tip]
            prov = (f"sslp311a.comm VALE_REFE ({'FOND1, right' if tip == 'right' else 'left'} tip, theta = 15 deg)" if th == 15 else
                    f"V-doc v3.02.311 section 2.2: published F_I = {SSLP311_F[th][1 if tip == 'right' else 0][0]}, F_II = {SSLP311_F[th][1 if tip == 'right' else 0][1]} "
                    f"({tip} tip, theta = {th} deg) with the source's G formula (evidence: interface-crack/reference-derivation.json)")
            refs[key] = C.refv(round(G[th][tip], 4), "scalar", "published_table", prov, tol=x["band"],
                               note="boundary-element reference (Miyazaki et al. 1993) as published by the source; tolerance from an independent J-integral study")
            refs[key]["tol"]["basis"] = "independent J-integral convergence study (evaluator evidence), not a certified uncertainty bound"
            refs[key]["independent_finest"] = x["finest"]
        admitted = a["decision"] == "admit"
        flags = [f"independent finest-mesh G: right {a['tips']['right']['finest']:.4g} ({100 * a['tips']['right']['relative_difference']:+.2f} %), "
                 f"left {a['tips']['left']['finest']:.4g} ({100 * a['tips']['left']['relative_difference']:+.2f} %) J/m^2; last level change "
                 f"{100 * max(x['last_change'] for x in a['tips'].values()):.2f} %",
                 "the source's own finite-element run (theta = 15 deg) is within 0.3 % of the same reference"]
        if admitted:
            flags.append("Independently reproduced in this release (evaluator evidence); an end-to-end pass still requires evaluator-owned workflow review.")
        t, r = record(tid, "A", "source_backed_pilot", "interface-crack-fracture", f"Code_Aster SSLP311: interface crack at {th} deg, energy release rates",
                      ["linear elastic fracture mechanics", "bimaterial interface crack", "plane stress"], body, inputs, outs,
                      dict(solids=2, assembly=True, geometry_class="2-D plane stress (exchange extrusion)"), ASTER_SOURCE, refs, flags, admitted,
                      dict(crack_assessment=a, evidence_files=sorted(set(files))))
        if admitted:
            prim.append((t, r))
        else:
            t["status"] = r["status"] = "held"
            t["hold_reason"] = r["hold_reason"] = f"Independent J-integral study: {a['reason']}."
            held.append((t, r))
    return prim, held


# ---------------------------------------------------------------- documentation
def write_docs(prim: list, refs: dict, cal: list, held: list, pool: list, val: dict, new_prim, new_cal, new_held) -> None:
    import re
    fam = collections.Counter(t["engineering_family"] for t in prim)
    nb = sum(t["track"] == "B" for t in prim)
    big = sum(fam[f] for f in ("simjeb-bracket", "agentfem-bracket", "geopinonet-holed-plate"))
    L = ["# CADFEM-Bench v1.5: balanced pilot with plasticity and fracture families", "",
         f"Released {C.DATE}. The primary comparison suite has **{len(prim)} tasks, {val['graded_outputs']} published numerical targets and "
         f"{len(fam)} engineering-family labels**, capped at five tasks per family: {len(prim) - nb} supplied-CAD tasks and {nb} drawing/specification-to-CAD "
         f"tasks. {val['independently_reproduced_tasks']} primary tasks have independent reproduction evidence. Calibration ({len(cal)} tasks), reserved "
         f"public-source ({val['suite_counts']['reserved_public']}) and related ({val['suite_counts']['related_public']}) suites are evaluator-only and scored "
         f"separately; {len(held)} tasks are held with reasons. Bracket and holed-plate families contribute {big} of {len(prim)} primary tasks. "
         "This is a source-backed pilot, not a certified engineering leaderboard; every graded value is published by its source.", "",
         "## Changes in v1.5", "",
         "v1.5 adds two physics classes the v1.3 audit found missing, plasticity and fracture. Every v1.4 task, target, tolerance and suite "
         "assignment is unchanged. A new case is graded only when an independent solver run settles within a 10 % band around the published "
         "value: last mesh change < 1 %, previous < 2 %, band = |finest - published| / published + 2 x last change, tolerance = band, at least 5 %. "
         "This is the rule the cycloidal and buckling families already use.", ""]
    pl = [r for t, r in new_prim + new_cal + new_held if r["family"] == "fcvm-plastic-limit"]
    L += ["### Plasticity: fcVM plastic collapse (limit) load factors", "",
          "fcVM's published elastic-perfectly plastic collapse factors (von Mises, no hardening, geometrically linear). Only models whose published "
          "load-displacement curve ends on a flat plateau are used: the lug, barrier and train-bridge runs stop while the load is still rising, so "
          "their peak is a lower bound and stays held. Each load set is rebuilt from the original FreeCAD constraints and matches the published "
          "load sum. The independent check (`scripts/fcvm_plastic_check.py`) is a FEniCSx limit analysis: quadratic tetrahedra, radial return with "
          "the consistent tangent, and proportional loading with bisection. The limit factor is bracketed to 0.2 %. Its solver check is the tensile "
          "bar, whose closed-form limit 0.5 it reproduces; that bar goes to the calibration suite.", "",
          "| model | published | finest independent | difference | last change | decision |", "|---|---:|---:|---:|---:|---|"]
    for r in sorted(pl, key=lambda r: r["task_id"]):
        a = r["plastic_assessment"]
        dec = (f"held: {a['reason']}" if r.get("status") == "held" else
               ("calibration" if r["tier"] == "control" else "primary") + f", tolerance {100 * r['references']['limit_load_factor']['tol']['value']:.0f} %")
        L.append(f"| {a['case']} | {a['published_limit_factor']:g} | " + (f"{a['finest']:.4g} | {100 * a['relative_difference']:+.1f} % | {100 * a['last_change']:.2f} % | "
                                                                          if "finest" in a else "- | - | - | ") + dec + " |")
    cr = [r for t, r in new_prim + new_held if r["family"] == "interface-crack-fracture"]
    L += ["", "### Fracture: Code_Aster SSLP311, crack on an inclined bimaterial interface", "",
          "A 4 x 8 mm plate made of two elastic materials (E = 2.0e6 and 2.0e5 MPa) is joined along an inclined line through its centre. A 2 mm "
          "crack lies on that line, and the plate is in plane-stress tension. Outputs: the energy release rate G at both tips, for 15, 30, 45 and 60 "
          "degrees. The reference is the published boundary-element solution of Miyazaki et al. (1993) as tabulated by the source, with a stated "
          "uncertainty below 0.1 %. The source test states G directly for 15 degrees. For the other angles, G follows from the tabulated F_I and "
          "F_II through the source's G formula, which reproduces the two stated values to 2e-6 (`evidence/interface-crack/reference-derivation.json`). "
          "The CAD (`plate.step`, two solids with the crack faces split out) is built from the documented geometry. The independent check "
          "(`scripts/interface_crack_g.py`) is a FEniCSx plane-stress model on quadratic triangles with an equivalent-domain J-integral over three "
          "rings, run on five mesh levels. It is itself checked against a Griffith crack (within 0.1 %).", "",
          "| angle | tip | published G (J/m^2) | finest independent | difference | last change | decision |", "|---:|---|---:|---:|---:|---:|---|"]
    for r in sorted(cr, key=lambda r: r["crack_assessment"]["theta_deg"]):
        a = r["crack_assessment"]
        for tip in ("right", "left"):
            x = a["tips"][tip]
            dec = "held" if r.get("status") == "held" else f"primary, tolerance {100 * r['references']['G_' + tip + '_tip']['tol']['value']:.0f} %"
            L.append(f"| {a['theta_deg']} | {tip} | {x['published_G']:.4f} | {x['finest']:.4f} | {100 * x['relative_difference']:+.2f} % | {100 * x['last_change']:.2f} % | {dec} |")
    L += ["", "### Reviewed and held in v1.5", "",
          "- Code_Aster SSNV104 (Hertz contact of two hemispheres): the analytical reference assumes a contact radius much smaller than the sphere "
          "radius, but here a/R = 0.2, and the source's own result differs from it by 13.5 % (source tolerance 14 %). Not a usable target.",
          "- Code_Aster SSNV506 (elastoplastic indentation): the reference is an approximate textbook plasticity estimate for a 100 mm indentation.",
          "- fcVM plastic peaks that are not limit loads (lug, barrier, train bridge) and the geometric-nonlinear post-buckling peaks (plate girder, U100).",
          "- Frictional contact remains absent: the FreeCAD shell-contact pair (under review in `evaluator/source-review/`) and the Code_Aster contact "
          "cases are not admitted.",
          f"- Scorer: `evaluator/score.py` is the v1.4 scorer (solid-count and analytic-radius gates, reproduced-task summaries); it reports version 1.5.", "",
          "Registry: new rows `fcvm-plastic` and `codeaster-sslp311`; `fcvm-collapse` and `codeaster-50` are narrowed to what remains held.", ""]
    v14 = (SRC / "evaluator/DATASET_CARD.md").read_text()
    v14 = v14.split("\n", 1)[1]                               # drop the v1.4 title
    v14 = re.sub(r"^## Retained release verification.*?(?=^## |\Z)", "", v14, flags=re.S | re.M)   # superseded by this release's verification
    v14 = re.sub(r"^## Release verification \(finish_v14\.py\).*?(?=^## |\Z)", "", v14, flags=re.S | re.M)
    v14 = re.sub(r"^## Folder layout.*?(?=^## |\Z)", "", v14, flags=re.S | re.M)
    v14 = re.sub(r"^(#+) ", lambda m: "#" + m.group(1) + " ", v14, flags=re.M)
    v14 = v14.replace("/path/cadfem-bench-v1.4", "/path/cadfem-bench-v1.5")      # run instructions apply to this release
    L += ["## v1.4 release notes (carried over unchanged)", "", v14.strip(), ""]
    (C.EVAL / "DATASET_CARD.md").write_text("\n".join(L))
    cr_md = C.CAND / "README.md"
    txt = cr_md.read_text()
    first, rest = txt.split("\n", 1)
    rest = re.sub(r"^\d+ primary tasks: \d+ supplied-geometry tasks \(A\), \d+ drawing/specification-to-CAD tasks \(B\)\.",
                  f"{len(prim)} primary tasks: {len(prim) - nb} supplied-geometry tasks (A), {nb} drawing/specification-to-CAD tasks (B).", rest.lstrip("\n"), flags=re.M)
    assert f"{len(prim)} primary tasks" in rest, rest[:300]
    rest += ("\nFor the SSLP311 fracture tasks, plate.step is a 2-D plane-stress domain extruded 0.1 mm along +z as an exchange convention. Analyse "
             "the z = 0 section in plane stress, report G per unit thickness, and submit the analysed domain as part.step (the extruded solids are accepted). "
             "For the plastic limit-load tasks, the curve of load factor against displacement must be part of fields.npz or refinement.json.\n")
    cr_md.write_text("# CADFEM-Bench v1.5 - published-source pilot\n\n" + rest)


# ---------------------------------------------------------------- assembly
def main() -> None:
    assert SRC.is_dir() and not OUT.exists(), (SRC, OUT)
    subprocess.run(["cp", "-cRp", str(SRC), str(OUT)], check=True)
    for f in ("report",):
        if (OUT / f).exists():
            shutil.rmtree(OUT / f)
    for f in (OUT / "SHA256SUMS.txt",):
        f.unlink(missing_ok=True)
    ev = Evidence()
    p_prim, p_cal, p_held = plastic_family(ev)
    c_prim, c_held = crack_family(ev)
    new_prim, new_cal, new_held = p_prim + c_prim, p_cal, p_held + c_held
    for fam in collections.Counter(t["family"] for t, _ in new_prim).values():
        assert fam <= 5
    # held inputs leave candidate/
    for t, _ in new_held + new_cal:
        src = C.CAND / "tasks" / t["task_id"]
        dst = (OUT / "held/inputs" if t["status"] == "held" else C.EVAL / "suites/calibration/inputs") / t["task_id"]
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
    ev.save()

    def extend(folder: Path, rows: list):
        wjl(folder / "tasks.jsonl", jl(folder / "tasks.jsonl") + [t for t, _ in rows])
        wjl(folder / "references.jsonl", jl(folder / "references.jsonl") + [r for _, r in rows])
    wjl(C.CAND / "tasks.jsonl", jl(C.CAND / "tasks.jsonl") + [t for t, _ in new_prim])
    wjl(C.EVAL / "references.jsonl", jl(C.EVAL / "references.jsonl") + [r for _, r in new_prim])
    extend(C.EVAL / "suites/primary", new_prim)
    extend(C.EVAL / "suites/calibration", new_cal)
    extend(C.EVAL / "task-pool", new_prim + new_cal)
    extend(OUT / "held", new_held)

    prim = jl(C.CAND / "tasks.jsonl")
    refs = {r["task_id"]: r for r in jl(C.EVAL / "references.jsonl")}
    pool = jl(C.EVAL / "task-pool/tasks.jsonl")
    held = jl(OUT / "held/tasks.jsonl")
    cal = jl(C.EVAL / "suites/calibration/tasks.jsonl")
    # registry
    reg = jl(C.EVAL / "registry.jsonl")
    nfp = sum(t["family"] == "fcvm-plastic-limit" for t in prim + cal)
    for row in reg:
        if row["registry_id"] == "fcvm-collapse":
            row.update(title="fcVM workbench examples: plastic peaks that are not limit loads, and post-buckling peaks (5 results)", candidates=5,
                       reason="The lug, barrier and train-bridge outputs end before the load-displacement curve flattens, so their peak is a lower bound, not a "
                              "limit load; the plate-girder and U100 geometric-nonlinear peaks depend on fcVM's imperfection settings. The three plateau cases "
                              "are studied under registry fcvm-plastic.")
        if row["registry_id"] == "codeaster-50":
            row.update(candidates=49, reason=row["reason"] + " SSLP311 is admitted under codeaster-sslp311 (CAD built from the documented geometry). "
                       "Reviewed and held in v1.5: SSNV104 Hertz spheres (the analytical reference assumes a << R, but a/R = 0.2 here and the source's own "
                       "result differs by 13.5 %); SSNV506 indentation (approximate textbook plasticity estimate for a 100 mm indentation).")
    reg += [dict(registry_id="fcvm-plastic", collection="../cadfem-bench-v1.1-followup/published-source-expansion",
                 title="fcVM workbench examples: plastic limit loads (3 models whose published curve ends on a flat plateau)", status="pilot",
                 reason="Published fcVM collapse factor, elastic-perfectly plastic von Mises, geometrically linear. Load sets match the published load sums. "
                        "Graded only if an independent FEniCSx limit analysis settles within the 10 % band; the tensile bar (closed form) is calibration.",
                 families=["fcvm-plastic-limit"], tasks=sum(t["family"] == "fcvm-plastic-limit" for t in prim),
                 held_tasks=sum(t["family"] == "fcvm-plastic-limit" for t in held), calibration_tasks=sum(t["family"] == "fcvm-plastic-limit" for t in cal),
                 readiness=f"{sum(t['family'] == 'fcvm-plastic-limit' for t in prim)} primary tasks independently reproduced"),
            dict(registry_id="codeaster-sslp311", collection="data/published-fem-expansion-50/records/SSLP311.json",
                 title="Code_Aster SSLP311: central crack on an inclined bimaterial interface (4 angles)", status="pilot",
                 reason="Published boundary-element energy release rates at both tips (Miyazaki et al. 1993, tabulated by the source); geometry built from the "
                        "V-document; graded only if an independent J-integral study settles within the 10 % band.",
                 families=["interface-crack-fracture"], tasks=sum(t["family"] == "interface-crack-fracture" for t in prim),
                 held_tasks=sum(t["family"] == "interface-crack-fracture" for t in held),
                 readiness=f"{sum(t['family'] == 'interface-crack-fracture' for t in prim)} primary tasks independently reproduced")]
    wjl(C.EVAL / "registry.jsonl", reg)
    # validation, suite manifest, task hashes
    val = json.loads((C.EVAL / "validation.json").read_text())
    rr = [refs[t["task_id"]] for t in prim]
    val.update(version="1.5", tasks=len(prim), graded_outputs=sum(len(r["references"]) for r in rr),
               by_track=dict(collections.Counter(t["track"] for t in prim)), by_family=dict(collections.Counter(t["family"] for t in prim)),
               engineering_families=len({t["engineering_family"] for t in prim}), held_tasks=len(held),
               reference_classes=dict(collections.Counter(v["ref_class"] for r in rr for v in r["references"].values())),
               independently_reproduced_tasks=sum(bool(t["readiness"].get("independently_reproduced")) for t in prim),
               source_evidence_files=len(ev.man), source_evidence_bytes=sum(m["bytes"] for m in ev.man),
               fcvm_plastic_tasks=sum(t["family"] == "fcvm-plastic-limit" for t in prim),
               interface_crack_tasks=sum(t["family"] == "interface-crack-fracture" for t in prim),
               v15_held=[t["task_id"] for t, _ in new_held], v15_calibration=[t["task_id"] for t, _ in new_cal],
               validation_solver_runs=val.get("validation_solver_runs", 0) + sum(1 for _ in F.PLASTIC_STUDY.glob("*/*-*/result.json"))
               + sum(1 for _ in CRACK.glob("theta-*/level-*/result.json")))
    val["suite_counts"].update(primary=len(prim), calibration=len(cal), full_source_backed_pool=len(pool))
    C.jdump(val, C.EVAL / "validation.json")
    man = json.loads((C.EVAL / "suite-manifest.json").read_text())
    man.update(version="1.5", primary=len(prim), calibration=len(cal), full_source_backed_pool=len(pool))
    C.jdump(man, C.EVAL / "suite-manifest.json")
    C.jdump({t["task_id"]: hashlib.sha256(json.dumps(t, sort_keys=True, separators=(",", ":")).encode()).hexdigest() for t in prim}, C.EVAL / "task-hashes.json")
    (C.EVAL / "reproduced-task-ids.txt").write_text("\n".join(t["task_id"] for t in prim if t["readiness"].get("independently_reproduced")) + "\n")
    lim = json.loads((C.EVAL / "limitations-status.json").read_text())
    nrep = val["independently_reproduced_tasks"]
    lim.update(reproduction=f"partial: {nrep} of {len(prim)} primary tasks independently reproduced; no new tasks counted from repeat solves",
               complex_physics=f"partial: v1.5 adds plasticity ({val['fcvm_plastic_tasks']} limit-load tasks) and linear-elastic fracture "
                               f"({val['interface_crack_tasks']} interface-crack tasks), each independently checked; frictional contact, forming, crash and "
                               "fatigue remain absent (the FreeCAD shell-contact pair and the Code_Aster contact cases stay held)")
    C.jdump(lim, C.EVAL / "limitations-status.json")
    rp = C.EVAL / "REVIEW_PROTOCOL.md"
    txt = rp.read_text()
    old = "The primary suite has 10 independently reproduced tasks; the full pool has 16."
    assert old in txt
    rp.write_text(txt.replace(old, f"The primary suite has {nrep} independently reproduced tasks; the full pool has "
                                   f"{sum(bool(t.get('readiness', {}).get('independently_reproduced')) for t in pool)}."))
    write_docs(prim, refs, cal, held, pool, val, new_prim, new_cal, new_held)
    print(json.dumps(dict(primary=len(prim), graded_outputs=val["graded_outputs"], reproduced=nrep, calibration=len(cal), held=len(held), pool=len(pool),
                          new_primary=[t["task_id"] for t, _ in new_prim], new_calibration=val["v15_calibration"], new_held=val["v15_held"]), indent=1))


if __name__ == "__main__":
    main()
