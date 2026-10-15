"""Build MechDesign-Bench v0.1: scissor-jack design-to-requirements tasks grounded in published product ratings.

  tmp/cq-env/bin/python scripts/mechbench/build_mechbench.py

Writes output/datasets/mechdesign-bench-v0.1/ (+ .zip):
  candidate/README.md      contract shown to the model (also the agent harness's system prompt)
  candidate/tasks.jsonl    task prompts (no input files)
  evaluator/specs.jsonl    requirement sheets used by the grader
  evaluator/sources.json   product ratings and where they come from
  evaluator/grader/        planar.py, geom.py, grade.py
  evaluator/validation/    validation.json: hand-sized fixture passes every task; eight broken designs are caught
  evaluator/fixture/       the validation fixture (evaluator-only; not an answer key)
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "output/datasets/mechdesign-bench-v0.1"
G = 9.80665
FS_YIELD, FS_BUCKLING, ALLOWANCE = 1.5, 2.0, 1.3

PRODUCTS = [
    dict(key="SWSTAHL", name="SW-Stahl scissor jack 1500 kg", rated_kg=1500, h_min=100, h_max=360, mass_kg=2.65,
         url="https://www.galaxus.de/en/s4/product/sw-stahl-scissor-jack-1500-kg-10-36-cm-jacks-9476919",
         note="Listing gives 2.65 kg in the specification and 2.26 kg in the marketing text; the larger value is used."),
    dict(key="HP", name="HP Autozubehoer scissor jack 1500 kg", rated_kg=1500, h_min=104, h_max=385, mass_kg=2.62,
         url="https://www.galaxus.de/en/s4/product/hp-autozubehoer-scissor-jack-1500-kg-1040-3850-cm-jacks-10053639",
         note="Listing gives 2.62 kg; marketing text says 'only 2 kg'. The specification value is used."),
    dict(key="CT", name="Certified scissor jack 3300 lb (1.5 ton)", rated_kg=round(3300 * 0.45359237, 1), h_min=102, h_max=382, mass_kg=3.20,
         url="https://www.canadiantire.ca/en/pdp/certified-scissor-jack-3300-lbs-0091057p.0091057.html",
         note="Rated 3300 lb; assembled weight 3.20 kg."),
    dict(key="HALFORDS", name="Halfords 1.5 tonne scissor jack", rated_kg=1500, h_min=95, h_max=390, mass_kg=3.2,
         url="https://www.halfords.com/tools/garage-workshop/axle-stands-trolley-jacks/halfords-1.5-tonne-scissor-jack-657065.html", note=""),
    dict(key="DRAPER", name="Draper 1 tonne scissor jack", rated_kg=1000, h_min=200, h_max=370, mass_kg=2.3,
         url="https://www.everydayweldingsupplies.com/draper-tools/mechanics-automotive-and-workshop/vehicle-lifting/scissor-jacks",
         note="Saddle 50 x 36 mm, handle 410 mm, net weight 2.3 kg."),
    dict(key="TOWSURE", name="Towsure scissor jack 1000 kg", rated_kg=1000, h_min=90, h_max=330, mass_kg=2.1,
         url="https://towsure.com/products/scissor-jack-1000kg-capacity", note="Weight given as 2.1 kg (approx.)."),
]
HELD = [
    dict(name="Rockforce mechanical scissor jack 2 t", rated_kg=2000, h_min=115, h_max=380, reason="no published mass"),
    dict(name="Micks Garage scissor jack with ratchet 1000 kg", rated_kg=1000, h_min=100, h_max=350, reason="no published mass"),
    dict(name="Eisco laboratory scissor jack 25 kg", rated_kg=25, h_min=64, h_max=244, reason="no published mass; conflicting heights on the page"),
    dict(name="Valken ESC12V electric scissor jack 2000 kg", rated_kg=2000, h_min=130, h_max=350, reason="electric (motor included in the 5.5 kg mass)"),
]

CONTRACT = """# MechDesign-Bench task contract (scissor jacks, v0.1)

You design a manual scissor jack that lifts a rated load between two saddle heights. The design is graded by
re-running your code and checking the generated parts, mates, motion, strength, mass and report. Looking finished is
not enough: every requirement below is checked from the geometry you produce.

## Coordinates and units

Millimetres, newtons, MPa. z is up, the ground plane is z = 0, the jack works in the x-z plane and every pivot axis is
parallel to y. Model every part in the collapsed position (saddle at its lowest height).

## What to deliver

`main.py` (helper .py files allowed). `python main.py` with no arguments must write, into the working directory:

- `params.json`: the design's named dimensions. It must contain `arm_pin_spacing_mm`, the pin-to-pin length shared by
  the scissor arms. Every dimension of the parts must be derived from these parameters.
- `parts/<name>.step`: one valid solid per part, modelled in its assembled collapsed position.
- `assembly.json` (schema below).
- `analysis.json`: `screw_tension_N` (largest over the stroke), `max_arm_compression_N` (largest over the stroke),
  `mass_kg`, `min_yield_fs`, `min_buckling_fs`, and `verdict` ("meets" or "fails").

`python main.py --params FILE --out DIR` must regenerate the whole design from the parameters in FILE into DIR. The
grader runs it once unchanged and once with `arm_pin_spacing_mm` scaled by 1.05; the regenerated arms must then have
that pin spacing and the mechanism must still work.

## assembly.json

```
{"units": "mm", "ground": "<base part>",
 "parts": [{"name": "...", "step": "parts/<name>.step", "material": "S355|S700MC|8.8|10.9|12.9",
            "role": "base|arm|saddle|trunnion|screw|other"}, ...],
 "joints": [ {"name": "...", "type": "revolute", "parts": [A, B], "origin": [x, y, z]},
             {"name": "...", "type": "prismatic", "parts": [A, B], "origin": [x, y, z], "axis": [ux, 0, uz]},
             {"name": "...", "type": "fixed", "parts": [A, B]},
             {"name": "...", "type": "gear", "parts": [A, B], "ratio": r},          # rotation of A = r x rotation of B
             {"name": "...", "type": "distance", "parts": [A, B], "point_a": [...], "point_b": [...]} ],
 "driver": "<name of the distance joint set by the lead screw>",
 "driver_range_mm": [<value when collapsed>, <value when fully raised>]}
```

Joint points are global coordinates in the collapsed position. A revolute is only accepted if both parts carry a
cylindrical pin or hole on that axis (parallel to y, within 0.3 mm). Arms are parts with role "arm"; each arm's two
end pivots define its pin-to-pin line.

## Requirements and how they are checked

- Mates: every part takes part in a joint, the joint graph reaches the ground part, and each revolute is realised by
  real coaxial pin/hole geometry.
- Motion: exactly one degree of freedom (the lead screw). Driving through driver_range_mm moves the saddle top from at
  most h_min + 3 mm to at least h_max - 3 mm, with the saddle level within 1 degree. No two parts may share more than
  2 mm^3 of volume at five positions along the stroke. Allow clearance between pins and holes.
- Strength: the rated load acts vertically downward at the centre of the saddle top, at nine positions over the full
  stroke, including the lowest. Arm sections are cut from your solids along the pin-to-pin line (holes included):
  axial plus in-plane bending stress, including the eccentricity of the section centroid, must keep yield FS >= the
  required value. Compressed arms are checked for Johnson/Euler buckling over their pin-to-pin length with the
  minimum principal second moment of area. Pins are checked in double shear at 0.577 x yield of the weaker of the two
  parts. The screw's smallest cross-section between its two points must carry the tension (model the threaded length
  at the thread minor diameter). Base, saddle and trunnions are not stress-checked in this version.
- Mass: the sum of part volumes x density (7850 kg/m^3 for every catalogue material) must not exceed the budget.
- Report: analysis.json screw tension and peak arm compression within 5 % of the grader's values, mass within 3 %,
  and no "meets" verdict for a design that fails a check.

Materials (yield MPa, E = 210000 MPa): S355 355, S700MC 700, 8.8 640, 10.9 940, 12.9 1080.
"""

_head, _rest = CONTRACT.split("## Coordinates and units", 1)
_fmt, _rules = _rest.split("## Requirements and how they are checked", 1)
CONTRACT_BLIND = ("# MechDesign-Bench deliverable format (scissor jacks, v0.1, blind brief)\n\n"
                  "You receive an engineering brief. Deliver a design in the format below.\n\n## Coordinates and units" +
                  _fmt.replace(" The\ngrader runs it once unchanged and once with `arm_pin_spacing_mm` scaled by 1.05; the regenerated arms must then have\n"
                               "that pin spacing and the mechanism must still work.", "")
                      .replace(" (largest over the stroke)", "")
                      .replace(" A revolute is only accepted if both parts carry a\ncylindrical pin or hole on that axis (parallel to y, within 0.3 mm).", "") +
                  "Materials (yield MPa, E = 210000 MPa, density 7850 kg/m^3): S355 355, S700MC 700, 8.8 640, 10.9 940, 12.9 1080.\n")


def blind_prompt(p: dict, budget: float) -> str:
    return (f"Brief: we need a manual scissor car jack to replace the {p['name']}. It must lift {p['rated_kg']} kg from a "
            f"collapsed saddle height of {p['h_min']} mm to {p['h_max']} mm, be safe at its rating (factor of safety "
            f"{FS_YIELD} against yield and {FS_BUCKLING} against buckling) and weigh no more than the current product, "
            f"{budget:.3f} kg. Raise it with a lead screw. Deliver a production-ready design: parametric CAD driven by its "
            f"dimensions, an assembly with its mates, and your engineering analysis, in the deliverable format.")


def prompt(p: dict, track: str, budget: float) -> str:
    W = round(p["rated_kg"] * G, 1)
    tight = (f"Mass budget: {budget:.3f} kg, the published mass of the real product ({p['name']}). Your design must be no "
             f"heavier than the jack it replaces.") if track == "tight" else (
            f"Mass budget: {budget:.3f} kg ({ALLOWANCE} x the {p['mass_kg']} kg published mass of {p['name']}).")
    return (f"Design a manual scissor car jack to the rating of the {p['name']}.\n\n"
            f"Rated load: {p['rated_kg']} kg = {W} N, carried at every saddle height from {p['h_min']} mm (collapsed) to "
            f"{p['h_max']} mm (fully raised), saddle-top height measured from the ground plane.\n"
            f"Safety factors at the rated load: yield {FS_YIELD}, buckling {FS_BUCKLING}.\n{tight}\n"
            f"The jack is raised by a lead screw. Use the materials catalogue in the contract. Deliver main.py and the "
            f"artifacts exactly as the contract specifies; the design is graded by regenerating it from your code.")


def build_tasks() -> tuple[list, list]:
    tasks, specs = [], []
    for p in PRODUCTS:
        for track in ("standard", "tight", "blind"):
            budget = round(p["mass_kg"] * (ALLOWANCE if track == "standard" else 1.0), 3)
            tid = f"SJ-{int(round(p['rated_kg'], -1))}-{p['key']}" + {"standard": "", "tight": "-TIGHT", "blind": "-BLIND"}[track]
            tasks.append(dict(task_id=tid, title=f"Scissor jack to the {p['name']} rating ({track})", family="scissor-jack", track=track,
                              prompt=blind_prompt(p, budget) if track == "blind" else prompt(p, track, budget), inputs=[]))
            specs.append(dict(task_id=tid, track=track, product=p["name"], spec=dict(
                rated_load_N=round(p["rated_kg"] * G, 3), h_min_mm=p["h_min"], h_max_mm=p["h_max"], fs_yield=FS_YIELD,
                fs_buckling=FS_BUCKLING, mass_budget_kg=budget, published_mass_kg=p["mass_kg"])))
    return tasks, specs


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "candidate").mkdir(parents=True)
    ev = OUT / "evaluator"
    for d in ("grader", "validation", "fixture"):
        (ev / d).mkdir(parents=True)
    tasks, specs = build_tasks()
    (OUT / "candidate/README.md").write_text(CONTRACT)
    (OUT / "candidate/tasks.jsonl").write_text("".join(json.dumps(t) + "\n" for t in tasks if t["track"] != "blind"))
    (OUT / "candidate-blind").mkdir()
    (OUT / "candidate-blind/README.md").write_text(CONTRACT_BLIND)
    (OUT / "candidate-blind/tasks.jsonl").write_text("".join(json.dumps(t) + "\n" for t in tasks if t["track"] == "blind"))
    (ev / "specs.jsonl").write_text("".join(json.dumps(s) + "\n" for s in specs))
    (ev / "sources.json").write_text(json.dumps(dict(
        rule=f"Mass budget = published product mass x {ALLOWANCE} (standard) or x 1.0 (tight). Rated load at every height "
             f"including the lowest, FS yield {FS_YIELD}, FS buckling {FS_BUCKLING}: fixed before any model was evaluated. "
             "A task is admitted only if the hand-sized validation fixture meets it.",
        load_path_basis="two-force arms: screw tension W/tan(theta), arm thrust W/(2 sin(theta)); worst at the lowest position",
        admitted=PRODUCTS, held=HELD), indent=1) + "\n")
    for f in ("planar.py", "geom.py", "grade.py"):
        shutil.copy2(HERE / f, ev / "grader" / f)
    for f in ("fixture_scissor.py", "validate_grader.py"):
        shutil.copy2(HERE / f, ev / "fixture" / f)
    shutil.copy2(Path(__file__), OUT / Path(__file__).name)
    subprocess.run([sys.executable, str(HERE / "validate_grader.py"), "--tasks", str(ev / "specs.jsonl"), "--out", str(ev / "validation")],
                   check=True, stdout=subprocess.DEVNULL)
    shutil.rmtree(ev / "validation/work")
    val = json.loads((ev / "validation/validation.json").read_text())
    feas = {f["task_id"]: f for f in val["feasibility"]}
    rows = "\n".join(f"| `{s['task_id']}` | {s['product']} | {s['spec']['rated_load_N'] / G:.0f} kg | {s['spec']['h_min_mm']}-{s['spec']['h_max_mm']} mm "
                     f"| {s['spec']['mass_budget_kg']} kg | {feas[s['task_id']]['mass_kg']} kg | {'yes' if feas[s['task_id']]['passed'] else 'NO'} |" for s in specs)
    caught = "\n".join(f"| {v['variant']} | {v['targets']} | {', '.join(v['failing'])} | {'yes' if v['caught'] else 'NO'} |" for v in val["broken_variants"])
    (OUT / "README.md").write_text(f"""# MechDesign-Bench v0.1: scissor jacks

Design-to-requirements tasks modelled on a reported failure: a frontier model's scissor jack that "looked finished"
had sketches without real dimensions, no assembly mates, an ignored load path and an FEA that "passed" by overbuilding
every part. Each task gives the rating of a real product (rated load, lift range, published mass). The model must
deliver parametric CAD, an assembly with real mates and an analysis. The grader re-runs the code and checks each of
those failure modes from the generated geometry:

| Check | Failure it targets |
|---|---|
| dimensions | geometry not driven by named dimensions (arm length scaled by 1.05 must regenerate) |
| mates | parts not connected; pivots declared without pin/hole geometry; floating parts |
| motion | mechanism that does not move with one degree of freedom over the full lift range; interpenetrating parts |
| strength | load path ignored: stress, buckling, pin shear and screw tension at nine positions, worst at the bottom |
| economy | overbuilt: mass above the budget (published product mass x {ALLOWANCE}, or x 1.0 on the tight track) |
| report | numbers that do not match the design; a "meets" verdict for a design that fails |

## Tasks (18)

| Task | Product rating | Load | Lift range | Budget | Validation fixture mass | Feasible |
|---|---|---|---|---|---|---|
{rows}

Tracks: standard (budget = {ALLOWANCE} x published mass; contract lists every check), tight (budget = published mass;
same contract), blind (budget = published mass; candidate-blind/README.md gives the deliverable format only, not how
designs are checked, and the prompt reads as a customer brief). All tracks use the same grader.

Feasibility: a hand-sized fixture (evaluator/fixture, not an answer key) meets every requirement of every task.
Held, not tasks: {', '.join(h['name'] + ' (' + h['reason'] + ')' for h in HELD)}.

## Grader validation

| Broken design | Intended check | Checks failed | Caught |
|---|---|---|---|
{caught}

## Running

The candidate folder is a suite for the CADFEM agent harness (tasks.jsonl + README.md contract). Grade a run with
`tmp/cq-env/bin/python evaluator/grader/grade.py --task <spec row as JSON> --submission <outputs> --code <main.py folder>`.
Submitted code must be run sandboxed. Limitations: base, saddle and trunnion stresses and gear teeth are not checked;
statics assume rigid parts and frictionless pins; product masses come from retailer listings (some inconsistent, noted
in evaluator/sources.json); the rule set (load at the lowest height, FS {FS_YIELD}/{FS_BUCKLING}) is this benchmark's,
not a jack standard. Local research package.
""")
    files = sorted(p for p in OUT.rglob("*") if p.is_file())
    (OUT / "SHA256SUMS").write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT)}\n" for p in files))
    with zipfile.ZipFile(OUT.parent / f"{OUT.name}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, Path(OUT.name) / p.relative_to(OUT))
    print(json.dumps(dict(tasks=len(tasks), all_feasible=val["all_feasible"], all_variants_caught=val["all_variants_caught"], out=str(OUT))))


if __name__ == "__main__":
    main()
