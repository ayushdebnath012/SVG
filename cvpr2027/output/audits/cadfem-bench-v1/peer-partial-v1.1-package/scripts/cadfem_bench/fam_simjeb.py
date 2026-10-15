"""SimJEB-Bench (GE jet engine bracket; SimJEB doi:10.7910/DVN/XFUWJG): track A analysis and track C design tasks.

Analysis: maximum displacement magnitudes are graded against SimJEB's published OptiStruct values (metadata CSV,
max_<case>_magdisp). The peak von Mises stress outside 2 mm of the bolt/pin walls and the pass verdict are not
published by SimJEB; they come from the benchmark's FEM grader (labelled `verifier`), which reproduces SimJEB's
published fields exactly on SimJEB's own mesh. Tolerances are SimJEB-Bench's own (10 % displacement, 15 % stress).
Design / redesign / lighten: graded by scripts/simjeb_bench.py evaluate (geometry rules + FEM + mass).
"""
from __future__ import annotations

import csv
import json

import common as C

BENCH = C.ROOT / "tmp/simjeb/bench"
CAD = C.ROOT / "tmp/simjeb/cad"
META_CSV = C.ROOT / "tmp/simjeb/dl/f4639239"
SOURCE = dict(name="SimJEB: simulated jet engine bracket dataset (Whalen, Beyene, Mueller, CGF 2021) / GE bracket challenge",
              url="https://doi.org/10.7910/DVN/XFUWJG",
              license="Dataverse CC0 / README ODC-By; GE bracket CAD from GrabCAD (non-commercial). Local research use.",
              redistributable=False)
CASES = {"vertical": "ver", "horizontal": "hor", "diagonal": "dia", "torsion": "tor"}


def _rows(f: str) -> list[dict]:
    return [json.loads(x) for x in (BENCH / f"{f}.jsonl").read_text().splitlines()]


def build() -> list:
    pub = {r["id"]: r for r in csv.DictReader(open(META_CSV))}
    env = BENCH / "envelope.json"
    rows = []
    for r in _rows("analysis"):
        tid = f"A-SIMJEB-analysis-{r['design']}"
        p = pub[str(r["design"])]
        inputs = [C.put(tid, CAD / f"{r['design']}.stp", "bracket.step")]
        prompt = r["prompt"].split("Answer as JSON")[0].strip()
        outs, refs = [], {}
        for case, short in CASES.items():
            k1, k2 = f"{case}_max_displacement_mm", f"{case}_peak_von_mises_MPa"
            outs += [C.out(k1, "mm", f"maximum displacement magnitude, {case} case"),
                     C.out(k2, "MPa", f"peak von Mises stress outside 2 mm of the bolt-hole and lug-bore walls, {case} case")]
            refs[k1] = C.refv(float(p[f"max_{short}_magdisp"]), "displacement", "published_table",
                              f"SimJEB metadata CSV id {r['design']} column max_{short}_magdisp (OptiStruct)", tol=r["tolerance"]["max_displacement_mm"])
            refs[k2] = C.refv(r["reference"]["cases"][case]["peak_von_mises_MPa"], "stress", "verifier",
                              "SimJEB-Bench FEM grader (scripts/simjeb_tasks.py)", tol=r["tolerance"]["peak_von_mises_MPa"])
        outs.append(C.out("passes", "bool", "true if the bracket passes all four cases (peak stress <= 903 MPa)"))
        refs["passes"] = C.refv(bool(r["reference"]["passes"]), "scalar", "verifier", "SimJEB-Bench FEM grader verdict", tol=0, tol_kind="bool")
        rows.append(C.task(tid, "A", "gold", "simjeb-analysis", f"GE bracket design {r['design']}: four-case static analysis",
                           ["linear static", "multi-load-case"], prompt, inputs, outs, SOURCE,
                           dict(solids=1, assembly=False, mass_kg=round(r["mass_kg"], 4)), refs,
                           flags=["peak stress and verdict use the validated benchmark grader (no published equivalent)"]))
    for fam in ("design", "redesign", "lighten"):
        for r in _rows(fam):
            if not r.get("feasible", True):
                continue                            # no passing human design proves the task can be solved
            tid = f"C-{r['id'].replace('simjeb-', 'SIMJEB-')}"
            inputs = [C.put(tid, env, "envelope.json", role="spec")]
            if "design" in r and fam != "design":
                inputs.append(C.put(tid, CAD / f"{r['design']}.stp", "bracket.step"))
            outs = [C.out("mass_kg", "kg", "mass of the submitted part (Ti-6Al-4V unless the task names another material)"),
                    C.out("worst_peak_von_mises_MPa", "MPa", "your computed largest peak stress over the four cases")]
            extra = dict(grader_command=f"python scripts/simjeb_bench.py evaluate --family {fam} --id {r['id']} (--step part.step | --cadquery part.py)",
                         success=dict(design="valid and passes all four cases; score = share of valid passing human designs heavier than the submission",
                                      redesign=f"valid, passes, interfaces kept, mass <= {r.get('mass_limit_kg', 0):.4f} kg",
                                      lighten=f"valid, passes, interfaces kept, mass <= {r.get('mass_limit_kg', 0):.4f} kg")[fam],
                         feasible=r.get("feasible", True), witness=r.get("witness"), simjeb_task_id=r["id"],
                         mass_limit_kg=r.get("mass_limit_kg"), human_reference=r.get("human_reference"))
            rows.append(C.task(tid, "C", "gold", f"simjeb-{fam}", f"GE bracket {fam}: {r['id'].replace('simjeb-', '')}",
                               ["linear static", "design optimisation"], r["prompt"], inputs, outs, SOURCE,
                               dict(solids=1, assembly=False), {}, grader="simjeb", extra_eval=extra,
                               flags=[] if r.get("feasible", True) else ["no human witness design proves feasibility"]))
    return rows
