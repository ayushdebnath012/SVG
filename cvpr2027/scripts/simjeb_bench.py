"""CAD generation judged by FEM: a benchmark on the GE jet engine bracket (SimJEB, doi:10.7910/DVN/XFUWJG).

Task families (all share the GE interfaces, the four GE load cases, Ti-6Al-4V and the rules below):
  design    design a bracket from the GE specification alone; objective: lowest mass that passes.
  redesign  a real SimJEB design that fails must be changed so it passes; interfaces kept, mass <= 1.25 x.
  lighten   a real SimJEB design that passes must lose >= 15 % of its mass and still pass.
  analysis  report the per-case maximum displacement and peak stress of a real design, and whether it passes.

Rules for every submitted part (STEP file, or CadQuery code that assigns the part to `result`):
  one solid; GE interfaces present (four bolt-hole walls of the bolt diameter starting within 1 mm of the mounting
  plane z = 0 and at least 5.5 mm long, both clevis lug bores, nothing inside the clevis gap); nothing below z = 0;
  inside the design envelope; surface thinner than 1.27 mm (the GE minimum feature) on at most WALL_TOL of the area;
  and, for passing, peak von Mises stress <= 903 MPa in all four load cases (scripts/simjeb_tasks.py grade).
Design scores are placed against the 381 human SimJEB designs: the share of valid passing human designs that are
heavier than the submission.

  python simjeb_bench.py fetch      # SimJEB CAD (207 MB) into tmp/simjeb/cad
  python simjeb_tasks.py grade-all --cad tmp/simjeb/cad --out tmp/simjeb/graded   # FEM-grade the 381 human designs
  python cad_checks.py tmp/simjeb/cad/*.stp --jsonl tmp/simjeb/checks-0.jsonl     # their geometry checks
  python simjeb_bench.py baseline   # merge FEM grades and geometry checks of the human designs, fix the envelope
  python simjeb_bench.py tasks      # write the task files
  python simjeb_bench.py evaluate --family design --id simjeb-design-ge --cadquery bracket.py
  python simjeb_bench.py score --results tmp/simjeb/bench/results.jsonl
  python simjeb_bench.py package    # task files, envelope and human baseline into data/simjeb-bench
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FEM_PY = ROOT / "tmp/fenicsx/env/bin/python"
CAD_PY = ROOT / "tmp/cq-env/bin/python"
BENCH = ROOT / "tmp/simjeb/bench"
YIELD, BOLT_START, BOLT_MIN_LEN, WALL_LIMIT, WALL_TOL = 903.0, 1.0, 5.5, 1.27, 0.02
PLANE_TOL = 0.5  # mm below z = 0 tolerated (CAD modelling slack seen in the human designs)
LUG_MIN_LEN = 5.0
REDESIGN_MASS, LIGHTEN_MASS = 1.25, 0.85


# ---------------------------------------------------------------- rules
def interface_rules(itf: dict) -> list[str]:
    bad = []
    for k in (1, 2, 3, 4):
        b = itf.get(f"bolt{k}") or {}
        z = b.get("z_range")
        if not b.get("radius") or b.get("coverage", 0) < 300 / 360 or z is None:
            bad.append(f"bolt hole {k} missing")
        elif z[0] > BOLT_START or z[1] - z[0] < BOLT_MIN_LEN:
            bad.append(f"bolt hole {k} wall {z[0]:.2f}-{z[1]:.2f} mm (must start within {BOLT_START} mm of z = 0 and be >= {BOLT_MIN_LEN} mm long)")
    for k in (1, 2):
        lug = (itf.get(f"lug{k}") or {}).get("axial")
        if lug is None or lug[1] - lug[0] < LUG_MIN_LEN:
            bad.append(f"clevis lug {k} bore missing or shorter than {LUG_MIN_LEN} mm")
    if itf.get("pin_wall_in_clevis_gap", 0) > 0:
        bad.append("material inside the clevis gap")
    return bad


def geometry_rules(chk: dict, env: dict) -> list[str]:
    bad = []
    if chk.get("error"):
        return [f"geometry check failed: {chk['error']}"]
    if chk["solids"] != 1:
        bad.append(f"{chk['solids']} solids")
    lo, hi = np.array(chk["bbox_min"]), np.array(chk["bbox_max"])
    if lo[2] < -PLANE_TOL:
        bad.append(f"material below the mounting plane (z = {lo[2]:.2f} mm)")
    if (lo[:2] < np.array(env["min"][:2]) - 0.01).any() or (hi > np.array(env["max"]) + 0.01).any():
        bad.append("outside the design envelope")
    if chk["thin_area_fraction"] is not None and chk["thin_area_fraction"] > WALL_TOL:
        bad.append(f"{100 * chk['thin_area_fraction']:.1f} % of the surface is thinner than {WALL_LIMIT} mm")
    return bad


# ---------------------------------------------------------------- running checks
def run_cadquery(code: Path, out_step: Path, timeout: int = 300) -> str | None:
    out_step = out_step.resolve()
    wrapper = code.read_text() + (
        "\n\nimport cadquery as _cq\n_r = result\n"
        "_cq.exporters.export(_r if isinstance(_r, _cq.Workplane) else _cq.Workplane().add(_r), "
        f"{str(out_step)!r})\n")
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "part.py"
        f.write_text(wrapper)
        try:
            r = subprocess.run([str(CAD_PY), "-I", str(f)], cwd=d, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return "CadQuery code timed out"
    return None if r.returncode == 0 and out_step.exists() else f"CadQuery code failed: {r.stderr[-400:]}"


def geometry_check(step: Path) -> dict:
    r = subprocess.run([str(CAD_PY), "-I", str(HERE / "cad_checks.py"), str(step)], capture_output=True, text=True, timeout=1800)
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith("{")]
    return json.loads(lines[-1]) if lines else dict(error=r.stderr[-300:])


def fem_grade(step: Path, material: dict | None = None, scale: float = 1.0, mesh_size: float | None = None) -> dict:
    cmd = [str(FEM_PY), "-I", str(HERE / "simjeb_tasks.py"), "grade", str(step), "--load-scale", str(scale)]
    if material:
        cmd += ["--material", json.dumps(material)]
    if mesh_size:
        cmd += ["--mesh-size", str(mesh_size)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith("{")]
    return json.loads(lines[-1]) if lines else dict(passed=None, reason="FEM grader crashed", error=r.stderr[-300:])


def judge(chk: dict, fem: dict, env: dict) -> dict:
    geo = geometry_rules(chk, env)
    itf = interface_rules(fem.get("interfaces") or {}) if fem.get("interfaces") else ["GE interfaces not found"]
    valid = not geo and not itf and fem.get("passed") is not None
    return dict(valid=valid, violations=geo + itf, passed=bool(valid and fem.get("passed")),
                mass_kg=fem.get("mass_kg"), safety_factor=fem.get("safety_factor"), worst_case=fem.get("worst_case"),
                cases=fem.get("cases"), interfaces=fem.get("interfaces"))


# ---------------------------------------------------------------- human baseline
def baseline(a) -> None:
    graded = {r["id"]: r for r in (json.loads(x) for x in open(a.graded))}
    checks = {}
    for f in Path(a.checks).parent.glob(Path(a.checks).name):
        for x in open(f):
            r = json.loads(x)
            if r["id"] not in checks or checks[r["id"]].get("error"):  # a successful check (e.g. a retry) wins over a failed one
                checks[r["id"]] = r
    ok = [c for k, c in checks.items() if not c.get("error") and not interface_rules((graded.get(k) or {}).get("interfaces") or {})]
    lo = np.array([c["bbox_min"] for c in ok])
    hi = np.array([c["bbox_max"] for c in ok])
    env = dict(min=np.floor(lo.min(0)).tolist(), max=np.ceil(hi.max(0)).tolist(),
               note="union of the bounding boxes of the human designs whose GE interfaces are intact, rounded outward to 1 mm "
                    "(SimJEB does not publish the GE design-space model); z from the mounting plane z = 0")
    env["min"][2] = 0.0
    rows = []
    for k in sorted(set(graded) | set(checks), key=int):
        g, c = graded.get(k, dict(passed=None, reason="not graded")), checks.get(k, dict(error="not checked"))
        j = judge(c, g, env) if g.get("interfaces") else dict(valid=False, violations=[g.get("reason") or "not graded"], passed=False,
                                                                mass_kg=g.get("mass_kg"))
        rows.append(dict(id=k, **j, fem_passed=g.get("passed"), thin_area_fraction=c.get("thin_area_fraction"),
                         bbox_min=c.get("bbox_min"), bbox_max=c.get("bbox_max")))
    BENCH.mkdir(parents=True, exist_ok=True)
    (BENCH / "envelope.json").write_text(json.dumps(env, indent=1))
    (BENCH / "human_baseline.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    v = [r for r in rows if r["valid"]]
    print(json.dumps(dict(designs=len(rows), valid=len(v), valid_passing=sum(r["passed"] for r in v),
                          fem_passing_any=sum(bool(r["fem_passed"]) for r in rows), envelope=env)), flush=True)
    from collections import Counter
    print(Counter(x.split(" (")[0].split(":")[0] for r in rows for x in r["violations"]).most_common(12), flush=True)


def load_baseline() -> tuple[list[dict], dict]:
    rows = [json.loads(x) for x in open(BENCH / "human_baseline.jsonl")]
    return rows, json.loads((BENCH / "envelope.json").read_text())


def human_percentile(mass: float, rows: list[dict]) -> dict:
    ref = np.array([r["mass_kg"] for r in rows if r["valid"] and r["passed"]])
    return dict(beats_share=float((ref > mass).mean()), rank=int((ref < mass).sum()) + 1, of=int(len(ref)),
                human_best_kg=float(ref.min()), human_median_kg=float(np.median(ref)))


# ---------------------------------------------------------------- design variants
MATERIALS = {  # E [MPa], nu, density [t/mm^3], yield [MPa]; handbook values (MMPDS / supplier datasheets, room temperature)
    "Ti-6Al-4V": dict(E=113800.0, nu=0.342, rho=4.43e-9, yield_MPa=903.0),
    "Al 7075-T6": dict(E=71700.0, nu=0.33, rho=2.81e-9, yield_MPa=503.0),
    "Al 2024-T3": dict(E=73100.0, nu=0.33, rho=2.78e-9, yield_MPa=345.0),
    "Al 6061-T6": dict(E=68900.0, nu=0.33, rho=2.70e-9, yield_MPa=276.0),
    "Mg AZ80A-T5": dict(E=45000.0, nu=0.35, rho=1.80e-9, yield_MPa=275.0),
}
LOAD_SCALES = (1.0, 0.8, 0.6, 0.4)
VARIANT_MARGIN = 0.97  # a human design counts for a variant only with 3 % stress margin (nu differs slightly)


def variants(rows: list[dict]) -> list[dict]:
    """GE interfaces and load directions, other materials / load levels. A human design passes a variant when its
    Ti-6Al-4V peak stresses, scaled by the load factor, stay below the variant's yield (stress does not depend on E)."""
    ti = MATERIALS["Ti-6Al-4V"]
    valid = [r for r in rows if r["valid"] and r.get("cases")]
    out = []
    for name, m in MATERIALS.items():
        for sc in LOAD_SCALES:
            ok = [r for r in valid if sc * max(c["peak_von_mises_MPa"] for c in r["cases"].values()) <= VARIANT_MARGIN * m["yield_MPa"]]
            if not ok:
                continue
            masses = sorted(r["mass_kg"] * m["rho"] / ti["rho"] for r in ok)
            best = min(ok, key=lambda r: r["mass_kg"])
            out.append(dict(material=name, props=m, load_scale=sc, human_passing=len(ok), human_lightest_kg=masses[0],
                            human_median_kg=float(np.median(masses)), witness=dict(design=int(best["id"]), mass_kg=masses[0], confirmed=None),
                            human_masses_kg=masses))
    return out


def task_percentile(mass: float, task: dict) -> dict:
    ref = np.array(task["human_reference"]["masses_kg"])
    return dict(beats_share=float((ref > mass).mean()), rank=int((ref < mass).sum()) + 1, of=int(len(ref)),
                mass_vs_lightest_human=mass / float(ref.min()))


def human_summary(rows: list[dict]) -> dict:
    ref = np.array([r["mass_kg"] for r in rows if r["valid"] and r["passed"]])
    return dict(valid_passing_designs=int(len(ref)), lightest_kg=float(ref.min()), p10_kg=float(np.percentile(ref, 10)),
                median_kg=float(np.median(ref)))


# ---------------------------------------------------------------- tasks
def spec(env: dict, material: str = "Ti-6Al-4V", scale: float = 1.0) -> str:
    st = _simjeb_tasks()
    m = MATERIALS[material]
    bolts = "; ".join(f"({c[0]:.4f}, {c[1]:.4f})" for c in st.BOLTS)
    f = lambda v: f"{scale * v:,.2f}"  # noqa: E731
    return (
        "Design task: the GE jet engine bracket" + ("" if (material, scale) == ("Ti-6Al-4V", 1.0) else
        f" (GE interfaces and load directions; {material}, loads at {100 * scale:g} % of the GE values)") +
        f". Units: millimetres, newtons, MPa. Material: {material} (E = {m['E'] / 1000:g} GPa, nu = {m['nu']}, density "
        f"{m['rho'] * 1e9:g} g/cm^3, yield strength {m['yield_MPa']:g} MPa). The bracket is bolted to a flat mounting surface, the "
        "plane z = 0, with nothing below it, and carries a clevis for a pin.\n"
        f"Interfaces: (a) four vertical (+z) bolt holes of diameter 10.3124 mm (0.406 in) at (x, y) = {bolts}; each hole "
        f"wall must start within {BOLT_START} mm of z = 0 and be at least {BOLT_MIN_LEN} mm long; the bolts are rigid and "
        "fully fixed. (b) a clevis of two lugs, each with a bore of diameter 19.1008 mm on the pin axis through "
        f"({st.PIN_POINT[0]:.4f}, {st.PIN_POINT[1]:.4f}, {st.PIN_POINT[2]:.4f}) with direction ({st.PIN_AXIS[0]:.6f}, "
        f"{st.PIN_AXIS[1]:.6f}, 0); measured along the axis from that point, the lug bores span 11.112 to 17.463 mm and "
        "-17.463 to -11.113 mm; the gap between the lugs must stay empty.\n"
        f"Design envelope: x {env['min'][0]:g} to {env['max'][0]:g}, y {env['min'][1]:g} to {env['max'][1]:g}, "
        f"z {env['min'][2]:g} to {env['max'][2]:g} mm. Minimum wall / feature thickness 1.27 mm (at most "
        f"{100 * WALL_TOL:g} % of the surface may be thinner). One solid.\n"
        "Loads, four separate linear static cases, each acting at the point "
        f"({st.LOAD_POINT[0]:.4f}, {st.LOAD_POINT[1]:.4f}, {st.LOAD_POINT[2]:.4f}) and spread over the two lug bores (RBE3): "
        f"(1) vertical: {f(35585.77)} N along +z; (2) horizontal: {f(37809.9)} N along -x; (3) diagonal, 42 degrees from "
        f"vertical: ({f(-28276.2)}, 0, {f(31403.9)}) N; (4) torsion: {f(564924.2)} N mm about +z.\n"
        "Pass criterion: in every case the peak von Mises stress (nodal-averaged, first-order tetrahedra of about 1.2 mm) "
        f"outside 2 mm of the bolt-hole and lug-bore walls is at most {m['yield_MPa']:g} MPa.")


def _simjeb_tasks():
    import importlib.util
    s = importlib.util.spec_from_file_location("simjeb_tasks", HERE / "simjeb_tasks.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def tasks(a) -> None:
    rows, env = load_baseline()
    graded = {r["id"]: r for r in (json.loads(x) for x in open(a.graded))}
    text = spec(env)
    out = []
    ask = ("\nProduce the bracket as CadQuery code that assigns the finished solid to `result` (or as a STEP file). Goal: "
           "pass all four load cases with the lowest mass you can. Report the mass and the per-case peak stress you computed.")
    for v in variants(rows):
        canon = (v["material"], v["load_scale"]) == ("Ti-6Al-4V", 1.0)
        tid = "simjeb-design-ge" if canon else f"simjeb-design-{v['material'].lower().replace(' ', '').replace('-', '')}-{int(100 * v['load_scale'])}"
        vt = spec(env, v["material"], v["load_scale"])
        out.append(dict(id=tid, family="design", variant=not canon, material=v["material"], props=v["props"],
                        load_scale=v["load_scale"], spec=vt, prompt=vt + ask,
                        human_reference=dict(passing_designs=v["human_passing"], lightest_kg=v["human_lightest_kg"],
                                             median_kg=v["human_median_kg"], masses_kg=v["human_masses_kg"]),
                        feasible=True, witness=v["witness"]))
    valid_pass = [r for r in rows if r["valid"] and r["passed"]]
    for r in rows:
        if not r["valid"] or r["fem_passed"] is None:
            continue
        g = graded[r["id"]]
        step = str(ROOT / f"tmp/simjeb/cad/{r['id']}.stp")
        radii = _radii(g["interfaces"])
        base = dict(design=int(r["id"]), step=step, mass_kg=r["mass_kg"], interface_radii=radii)
        if not r["passed"]:
            limit = REDESIGN_MASS * r["mass_kg"]
            wit = sorted((w for w in valid_pass if w["mass_kg"] <= limit and _radii(graded[w["id"]]["interfaces"]) == radii),
                         key=lambda w: w["mass_kg"])
            worst = r["worst_case"]
            out.append(dict(base, id=f"simjeb-redesign-{r['id']}", family="redesign", spec=text,
                            prompt=text + f"\nThe attached STEP file is a real competition design ({r['mass_kg']:.3f} kg) that "
                            f"fails: in the {worst} case its peak stress is {r['cases'][worst]['peak_von_mises_MPa']:.0f} MPa "
                            f"(safety factor {r['safety_factor']:.2f}). Change it so it passes all four cases, keeping its bolt "
                            f"holes and lug bores exactly (same diameters and positions), with a mass of at most {limit:.3f} kg. "
                            "Return CadQuery code assigning the solid to `result`, or a STEP file, and report your mass and per-case peak stress.",
                            mass_limit_kg=limit, current=dict(safety_factor=r["safety_factor"], worst_case=worst, cases=r["cases"]),
                            feasible=bool(wit), witness=dict(design=int(wit[0]["id"]), mass_kg=wit[0]["mass_kg"]) if wit else None))
        else:
            limit = LIGHTEN_MASS * r["mass_kg"]
            wit = sorted((w for w in valid_pass if w["mass_kg"] <= limit and _radii(graded[w["id"]]["interfaces"]) == radii),
                         key=lambda w: w["mass_kg"])
            out.append(dict(base, id=f"simjeb-lighten-{r['id']}", family="lighten", spec=text,
                            prompt=text + f"\nThe attached STEP file is a real competition design that passes ({r['mass_kg']:.3f} kg, "
                            f"safety factor {r['safety_factor']:.2f}). Make it at least {100 * (1 - LIGHTEN_MASS):.0f} % lighter "
                            f"(at most {limit:.3f} kg) while it still passes all four cases, keeping its bolt holes and lug bores "
                            "exactly. Return CadQuery code assigning the solid to `result`, or a STEP file.",
                            mass_limit_kg=limit, current=dict(safety_factor=r["safety_factor"]),
                            feasible=bool(wit), witness=dict(design=int(wit[0]["id"]), mass_kg=wit[0]["mass_kg"]) if wit else None))
        out.append(dict(base, id=f"simjeb-analysis-{r['id']}", family="analysis", spec=text,
                        prompt=text + "\nThe attached STEP file is a real competition design. Run the four load cases and "
                        "report, per case, the maximum displacement magnitude (mm) and the peak von Mises stress (MPa) by the "
                        "criterion above, and whether the bracket passes. Answer as JSON: {\"cases\": {\"vertical\": "
                        "{\"max_displacement_mm\": ..., \"peak_von_mises_MPa\": ...}, ...}, \"passes\": true/false}.",
                        reference=dict(cases={c: {k: v[k] for k in ("max_displacement_mm", "peak_von_mises_MPa")} for c, v in g["cases"].items()},
                                       passes=r["passed"]),
                        tolerance=dict(max_displacement_mm=0.10, peak_von_mises_MPa=0.15)))
    BENCH.mkdir(parents=True, exist_ok=True)
    fam: dict[str, list] = {}
    for t in out:
        fam.setdefault(t["family"], []).append(t)
    for f, ts in fam.items():
        (BENCH / f"{f}.jsonl").write_text("".join(json.dumps(t) + "\n" for t in ts))
    print(json.dumps({f: dict(tasks=len(ts), feasible=sum(t.get("feasible", True) for t in ts)) for f, ts in fam.items()}), flush=True)


def _radii(itf: dict) -> tuple:
    return tuple(round(itf[f"bolt{k}"]["radius"], 2) for k in (1, 2, 3, 4)) + (round(itf["pin_radius"], 2),)


# ---------------------------------------------------------------- evaluation
def evaluate(a) -> None:
    rows, env = load_baseline()
    task = next(json.loads(x) for x in open(BENCH / f"{a.family}.jsonl") if json.loads(x)["id"] == a.id)
    work = Path(a.out or BENCH / "runs" / f"{a.id}-{int(time.time())}").resolve()
    work.mkdir(parents=True, exist_ok=True)
    v = dict(id=a.id, family=task["family"], submission=a.cadquery or a.step or a.answer)
    t0 = time.time()
    if task["family"] == "analysis":
        ans, ref, tol = json.loads(Path(a.answer).read_text()), task["reference"], task["tolerance"]
        hits = {}
        for c, rc in ref["cases"].items():
            for q, rv in rc.items():
                got = ((ans.get("cases") or {}).get(c) or {}).get(q)
                hits[f"{c}.{q}"] = got is not None and abs(got - rv) <= tol[q] * abs(rv)
        hits["passes"] = ans.get("passes") == ref["passes"]
        v.update(correct=hits, score=sum(hits.values()) / len(hits), success=all(hits.values()))
    else:
        step = work / "part.step"
        if a.cadquery:
            err = run_cadquery(Path(a.cadquery), step)
            if err:
                v.update(success=False, valid=False, violations=[err], score=0.0)
                _emit(v, work, a)
                return
        else:
            step.write_bytes(Path(a.step).read_bytes())
        chk, fem = geometry_check(step), fem_grade(step, task.get("props"), task.get("load_scale", 1.0))
        j = judge(chk, fem, env)
        v.update(j, geometry=chk)
        if task["family"] in ("redesign", "lighten") and j["interfaces"]:
            same = _radii(j["interfaces"]) == tuple(task["interface_radii"]) if j["interfaces"].get("pin_radius") else False
            if not same:
                v["violations"] = v["violations"] + ["interface diameters changed"]
                v["valid"] = v["passed"] = False
        if task["family"] == "design":
            v["success"] = v["passed"]
            v["human"] = task_percentile(j["mass_kg"], task) if v["passed"] else None
            v["score"] = v["human"]["beats_share"] if v["passed"] else 0.0
        else:
            limit = task["mass_limit_kg"]
            v["success"] = bool(v["passed"] and j["mass_kg"] <= limit)
            if v["passed"] and j["mass_kg"] > limit:
                v["violations"] = v["violations"] + [f"mass {j['mass_kg']:.3f} kg > limit {limit:.3f} kg"]
            v["mass_ratio"] = j["mass_kg"] / task["mass_kg"] if j["mass_kg"] else None
            v["score"] = float(v["success"])
    v["seconds"] = round(time.time() - t0, 1)
    _emit(v, work, a)


def _emit(v: dict, work: Path, a) -> None:
    (work / "verdict.json").write_text(json.dumps(v, indent=1))
    print(json.dumps({k: v[k] for k in v if k not in ("cases", "interfaces", "geometry")}), flush=True)
    if a.results:
        with open(a.results, "a") as h:
            h.write(json.dumps(dict(v, model=a.model)) + "\n")


def score(a) -> None:
    rs = [json.loads(x) for x in open(a.results)]
    by: dict[tuple, list] = {}
    for r in rs:
        by.setdefault((r.get("model"), r["family"]), []).append(r)
    for (m, f), xs in sorted(by.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        line = dict(model=m, family=f, n=len(xs), success_rate=float(np.mean([bool(x.get("success")) for x in xs])),
                    valid_rate=float(np.mean([bool(x.get("valid", True)) for x in xs])), mean_score=float(np.mean([x.get("score", 0) for x in xs])))
        if f == "design":
            ok = [x for x in xs if x.get("success")]
            line["best_beats_share"] = max((x["human"]["beats_share"] for x in ok), default=0.0)
            line["best_mass_kg"] = min((x["mass_kg"] for x in ok), default=None)
        print(json.dumps(line), flush=True)


DATA = ROOT / "data/simjeb-bench"
CAD_ZIP_FILE_ID = 4639266  # SimJEB_cad_(stp).zip on Harvard Dataverse


def confirm(a) -> None:
    """Re-grade each design variant's witness (the lightest human design predicted to pass) with the variant's material
    and loads; on failure try the next lightest candidates."""
    rows, _ = load_baseline()
    tasks_ = [json.loads(x) for x in open(BENCH / "design.jsonl")]
    by_mass = sorted((r for r in rows if r["valid"] and r.get("cases")), key=lambda r: r["mass_kg"])
    for t in tasks_:
        if t["witness"].get("confirmed"):
            continue
        cands = [r for r in by_mass if t["load_scale"] * max(c["peak_von_mises_MPa"] for c in r["cases"].values())
                 <= VARIANT_MARGIN * t["props"]["yield_MPa"]][:3]
        for r in cands:
            g = fem_grade(ROOT / f"tmp/simjeb/cad/{r['id']}.stp", t["props"], t["load_scale"])
            if g.get("passed"):
                t["witness"] = dict(design=int(r["id"]), mass_kg=g["mass_kg"], safety_factor=g["safety_factor"], confirmed=True)
                break
        else:
            t["witness"]["confirmed"] = False
            t["feasible"] = False
        print(t["id"], t["witness"], flush=True)
    (BENCH / "design.jsonl").write_text("".join(json.dumps(t) + "\n" for t in tasks_))


def frontier(a) -> None:
    """Fixed evaluation set for frontier models: every design variant, redesign tasks stratified by how badly the
    original fails, lighten tasks; only feasible tasks (a real passing design inside the limits exists)."""
    import random
    rng = random.Random(a.seed)
    pick = []
    pick += [json.loads(x) for x in open(BENCH / "design.jsonl") if json.loads(x).get("feasible")]
    red = [json.loads(x) for x in open(BENCH / "redesign.jsonl") if json.loads(x).get("feasible")]
    for lo, hi in ((0.8, 1.0), (0.5, 0.8), (0.0, 0.5)):
        band = [t for t in red if lo <= t["current"]["safety_factor"] < hi]
        pick += rng.sample(band, min(a.per_band, len(band)))
    lig = [json.loads(x) for x in open(BENCH / "lighten.jsonl") if json.loads(x).get("feasible")]
    pick += rng.sample(lig, min(a.lighten, len(lig)))
    (BENCH / "frontier.jsonl").write_text("".join(json.dumps(t) + "\n" for t in pick))
    from collections import Counter
    print(json.dumps(dict(tasks=len(pick), by_family=Counter(t["family"] for t in pick))), flush=True)


def fetch(a) -> None:
    """Download SimJEB's cleaned CAD (207 MB) into tmp/simjeb/cad (kept out of git: GrabCAD non-commercial licence)."""
    import urllib.request
    import zipfile
    dest = ROOT / "tmp/simjeb/cad"
    dest.mkdir(parents=True, exist_ok=True)
    z = ROOT / "tmp/simjeb/SimJEB_cad_stp.zip"
    if not z.exists():
        urllib.request.urlretrieve(f"https://dataverse.harvard.edu/api/access/datafile/{CAD_ZIP_FILE_ID}?format=original", z)
    with zipfile.ZipFile(z) as f:
        f.extractall(dest)
    print(f"{len(list(dest.glob('*.stp')))} STEP files in {dest}", flush=True)


def package(a) -> None:
    """Copy the task files, envelope and human baseline into data/simjeb-bench with CAD paths relative to the repo."""
    DATA.mkdir(parents=True, exist_ok=True)
    for f in ("design", "redesign", "lighten", "analysis", "frontier"):
        if not (BENCH / f"{f}.jsonl").exists():
            continue
        rows = [json.loads(x) for x in open(BENCH / f"{f}.jsonl")]
        for r in rows:
            if "step" in r:
                r["step"] = f"tmp/simjeb/cad/{Path(r['step']).name}"
        (DATA / f"{f}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    for f in ("envelope.json", "human_baseline.jsonl"):
        (DATA / f).write_text((BENCH / f).read_text())
    print("packaged into", DATA, flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("baseline")
    b.add_argument("--graded", default=str(ROOT / "tmp/simjeb/graded/graded.jsonl"))
    b.add_argument("--checks", default=str(ROOT / "tmp/simjeb/checks-*.jsonl"))
    t = sub.add_parser("tasks")
    t.add_argument("--graded", default=str(ROOT / "tmp/simjeb/graded/graded.jsonl"))
    e = sub.add_parser("evaluate")
    e.add_argument("--family", required=True, choices=["design", "redesign", "lighten", "analysis"])
    e.add_argument("--id", required=True)
    g = e.add_mutually_exclusive_group(required=True)
    g.add_argument("--cadquery")
    g.add_argument("--step")
    g.add_argument("--answer")
    e.add_argument("--out")
    e.add_argument("--results")
    e.add_argument("--model")
    s = sub.add_parser("score")
    s.add_argument("--results", required=True)
    sub.add_parser("fetch")
    sub.add_parser("package")
    sub.add_parser("confirm")
    fr = sub.add_parser("frontier")
    fr.add_argument("--per-band", type=int, default=10)
    fr.add_argument("--lighten", type=int, default=10)
    fr.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    dict(baseline=baseline, tasks=tasks, evaluate=evaluate, score=score, fetch=fetch, package=package, confirm=confirm,
         frontier=frontier)[a.cmd](a)


if __name__ == "__main__":
    main()
