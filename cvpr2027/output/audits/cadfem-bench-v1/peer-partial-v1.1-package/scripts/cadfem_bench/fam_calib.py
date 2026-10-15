"""NAFEMS LE1/LE10/LE11 calibration tasks (tracks A and B) and FEMCAD-Hard v1 (track B).

NAFEMS: reuse the published-fem-pilot-v1 candidate inputs (original FeenoX geometry definitions, published problem
figure, original physics excerpt). References are the FeenoX published outputs, which equal the NAFEMS targets.
Tier `control`: these are public benchmarks whose answers a model may recall; they calibrate the harness.
FEMCAD-Hard: the five tasks with closed-form or page-stated references and their own tolerances (Wolfram FEM docs).
"""
from __future__ import annotations

import json

import common as C

PILOT = C.ROOT / "tmp/published-fem-pilot-v1"
FEMCAD = C.DATA / "femcad-hard-v1"
NAFEMS_SRC = dict(name="FeenoX NAFEMS mechanical examples (seamplex/feenox)", url="https://www.seamplex.com/feenox/examples/mechanical.html",
                  license="GPL-3.0-or-later (examples)", redistributable=True)
TITLES = {"NAFEMS-LE1": "NAFEMS LE1 elliptic membrane", "NAFEMS-LE10": "NAFEMS LE10 thick elliptic plate",
          "NAFEMS-LE11": "NAFEMS LE11 thermoelastic cylinder/taper/sphere"}
PHYS = {"NAFEMS-LE1": ["plane stress", "linear static"], "NAFEMS-LE10": ["linear static"], "NAFEMS-LE11": ["thermoelastic", "linear static"]}


def nafems() -> list:
    rows = []
    for track, sub in (("A", "analysis_fem"), ("B", "cad_fem")):
        for case in TITLES:
            d = PILOT / "candidate-inputs" / sub / case
            con = json.loads((PILOT / "evaluator-only" / case / "contract.json").read_text())
            q = con["qois"][0]
            tid = f"{track}-{case}"
            inputs = [C.put(tid, f, f.name, role={".step": "cad", ".geo": "cad", ".png": "drawing"}.get(f.suffix, "spec"))
                      for f in sorted(d.iterdir()) if f.name not in ("task.json", "task.md")]
            spec = json.loads((d / "input.json").read_text())
            prompt = (d / "task.md").read_text().split("results.json format")[0].strip()
            prompt = prompt.replace("# Published FEM problem\n\n", "")
            prompt += (f"\n\nRequested quantity: {spec.get('quantity', 'stress component')} '{q['key']}' at the point "
                       f"{spec.get('query')} ({spec.get('geometry_unit', '')}), reported in {q['unit']}. "
                       "input.json gives units, the sampling point and source precision notes.")
            outs = [C.out(q["key"], q["unit"], f"{spec.get('quantity', 'stress')} at the requested point (signed)")]
            refs = {q["key"]: C.refv(q["value"], "stress", "benchmark_target", q["locator"], tier="control", tol=0.05)}
            rows.append(C.task(tid, track, "control", "nafems-calibration", f"{TITLES[case]} ({'supplied geometry' if track == 'A' else 'build CAD from drawing'})",
                               PHYS[case], prompt, inputs, outs, NAFEMS_SRC, dict(solids=1, assembly=False, geometry_class="benchmark"),
                               refs, flags=["public NAFEMS benchmark: answer may be recalled; calibration only"]))
    return rows


def femcad_hard() -> list:
    rows = []
    for line in (FEMCAD / "tasks.jsonl").read_text().splitlines():
        r = json.loads(line)
        tid = f"B-{r['id']}"
        inputs = []
        for i, fg in enumerate(r.get("figures", [])):
            p = C.ROOT / fg["local"]
            if p.exists():
                inputs.append(C.put(tid, p, f"figure-{i + 1}{p.suffix}", role="figure"))
        outs = [C.out(q["key"], q["unit"], q["definition"]) for q in r["qois"]]
        refs = {q["key"]: C.refv(q["reference"], "scalar", "closed_form" if "closed" in q.get("reference_source", "") else "published_table",
                                 f"{q.get('reference_source', '')}; {r['source']['url']}", tol=q["rel_tol"]) for q in r["qois"]}
        prompt = r["prompt"].split("\n\nOutputs (results.json)")[0].replace(
            "The grader compares your geometry with the reference model and your results with the reference analysis.",
            "Your results are compared with the reference analysis.")
        src = dict(name=f"Wolfram FEM documentation: {r['source']['page']}", url=r["source"]["url"],
                   license="Wolfram documentation (copyright Wolfram Research); figures not redistributable", redistributable=False)
        rows.append(C.task(tid, "B", "gold", "femcad-hard", r["title"], [r["category"]], prompt, inputs, outs, src,
                           dict(model_kind=r["model_kind"], assembly=False), refs,
                           flags=[f"geometry check {r['geometry_check']['status']}"]))
    return rows


def build() -> list:
    return nafems() + femcad_hard()
