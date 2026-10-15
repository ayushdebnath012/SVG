"""Dataset card for CADFEM-Bench v1, written from the built task, reference and registry files."""
from __future__ import annotations

from collections import Counter, defaultdict

import common as C

FAMILY_INFO = {
    "simjeb-analysis": ("GE jet-engine bracket, real competition designs", "4-case linear static"),
    "simjeb-design": ("GE bracket from specification (incl. material/load variants)", "design, 4-case static"),
    "simjeb-redesign": ("Failing GE bracket designs", "redesign to pass, mass cap"),
    "simjeb-lighten": ("Passing GE bracket designs", "remove >= 15 % mass, still pass"),
    "agentfem-bracket": ("Double-arm support bracket family", "linear static"),
    "geopinonet-holed-plate": ("Steel plate with a through hole", "two static load cases"),
    "morphing-wing-plates": ("Uniform/stepped PLA morphing-wing plates", "modal"),
    "cycloidal-drive-components": ("Cycloidal gearbox parts (PETG-CF, steel pins)", "linear static"),
    "cadworld-freecad-fem": ("Multi-feature aluminium part", "linear static, mesh protocol"),
    "nafems-calibration": ("NAFEMS LE1/LE10/LE11", "plane stress, 3-D static, thermoelastic"),
    "femcad-hard": ("Capacitor shell, L-bracket, pressure hull, holed plate, heated tube", "electrostatics, static, thermal"),
    "feenox-valve-transient": ("Power-plant valve, carbon + stainless", "nonlinear transient thermal"),
    "rigging-plate": ("7075-T6 rigging plate (5 load tests, drawing)", "linear static, figure-specified BCs"),
}


def write(tasks: list, refs: list, reg: list, val: dict) -> str:
    fam = defaultdict(list)
    for t, e in zip(tasks, refs):
        fam[t["family"]].append((t, e))
    L = [f"# CADFEM-Bench v{C.VERSION}", "",
         f"The final CAD + FEM benchmark for frontier AI models, assembled on {C.DATE} from every CAD/FEM source collected in this project. "
         f"**{len(tasks)} tasks, {val['graded_outputs']} graded numerical outputs, {len(fam)} task families, {val['sources_admitted']} admitted source collections.** "
         f"A further {val['sources_held']} held and {val['sources_excluded']} excluded collections are listed with their blockers in `registry.jsonl`. "
         "No FEM reference was produced for this release and no model has been run on it.", "",
         "## Tracks", ""]
    L += [f"- **{k}** - {v}" for k, v in C.TRACKS.items()]
    L += ["", "## Tiers", "",
          "- **gold**: open CAD (STEP/BREP) or a complete specification, fully stated set-up, reference from a saved solver result, a publisher table/CSV, a publisher evaluator, a closed form, or the validated SimJEB grader.",
          "- **silver**: reference read from a published result legend; part of the set-up is given by the source's own boundary-condition figure. Reported separately.",
          "- **control**: public NAFEMS benchmarks; they calibrate the harness and may be answerable from memory.", "",
          "## Error policy", "",
          "Tasks with a known error in their source data were fixed where the fix is verifiable and left out otherwise. Fixed: AgentFEM STEP files (metre values under a mm header) are shipped scaled to true mm and checked against the FEM nodes; GeoPINONet boundary conditions are stated from the verified fields (the archive's fixed/load STL names are swapped). "
          "Left out: DeepWheel (CAD/CSV mass mismatch, unknown density), CADWorld 002 (singular edge support) and 003 (811 mm displacement of a 30 mm specimen), rigging-plate tests 4 and 5 (conflicting load labels, revised results), cycloidal stress outputs (source error estimate 11-49 %), and 13 SimJEB redesign/lighten tasks without a passing human design proving feasibility. Every decision is in `registry.jsonl`.", "",
          "## Composition", "", "| family | track | tier | tasks | graded outputs | geometry | physics | reference classes | licence |",
          "|---|---|---|---:|---:|---|---|---|---|"]
    for f, rows in sorted(fam.items(), key=lambda kv: (kv[1][0][0]["track"], kv[0])):
        t0 = rows[0][0]
        n_out = sum(len([k for k, r in e["references"].items() if r.get("graded", True)]) for _, e in rows)
        rc = sorted({r["ref_class"] for _, e in rows for r in e["references"].values()}) or ["SimJEB grader"]
        geo, phys = FAMILY_INFO.get(f, ("", ""))
        tiers = "/".join(sorted({t["tier"] for t, _ in rows}))
        tracks = "/".join(sorted({t["track"] for t, _ in rows}))
        L.append(f"| {f} | {tracks} | {tiers} | {len(rows)} | {n_out} | {geo} | {phys} | {', '.join(rc)} | {t0['source']['license'][:40]} |")
    L += ["", "## Reference policy", "",
          "References are values published by the source: maxima of the source's own saved result files (CalculiX FRD, ANSYS/FEM CSV), cells of publisher spreadsheets or CSVs, values checked by the publisher's own evaluator, closed-form solutions, or NAFEMS targets. "
          "One exception is labelled `verifier`: for SimJEB analysis tasks the peak stress outside 2 mm of the bolt and pin walls and the pass verdict are not published, and come from the benchmark's FEM grader, which reproduces SimJEB's published OptiStruct fields exactly on SimJEB's mesh; SimJEB's published displacements are used directly.",
          "", "Every reference record carries its provenance (file, column, cell or legend). Classes in this release: "
          + ", ".join(f"{k} {v}" for k, v in sorted(val["ref_classes"].items(), key=lambda kv: -kv[1])) + ".", "",
          "## Tolerances", "",
          "Relative error |pred - ref| / |ref| unless stated. Defaults (gold): displacement, frequency, temperature, force 5 %; stress 10 %. Silver: 10 % / 20 %. A source's own tolerance overrides the default: CADWorld 5 %, SimJEB 10 % displacement / 15 % stress, FEMCAD-Hard 1 % (closed forms). "
          "Legend peak stresses at load edges (rigging plate) get 20 %; temperatures in transients are graded on the rise above the initial state; through-wall temperature differences get 10 %. The pass verdict is exact.", "",
          "## Scoring", "",
          "A task passes when all graded outputs are within tolerance (and, for the track B rigging task, the submitted part matches the source CAD volume and extents within 2 %). "
          "Report the pass rate per track and tier and the **family macro-average** so that large parametric families (SimJEB, AgentFEM, GeoPINONet) do not dominate. Track C uses the SimJEB harness verdicts (valid, passes, mass limit; design tasks also report the share of human designs beaten).", "",
          "```", "python evaluator/score.py --refs evaluator/references.jsonl --submissions runs/<model> --simjeb-results results.jsonl --out score.json", "```", "",
          f"Grader self-test at build time: the exact references pass {val['grader_selftest']['oracle']['passed']}/{val['grader_selftest']['oracle']['numeric_tasks']} numeric tasks; references scaled by 1.3 pass {val['grader_selftest']['perturbed']['passed']}.",
          f"Leak scan: no reference number appears in any prompt or text input ({len(val['leak_scan_hits'])} hits). Image inputs were reviewed by eye: problem and boundary-condition figures only.", "",
          "## Held and excluded sources", "",
          f"{val['sources_held']} collections are held: they contain real CAD and FEM data, but a specific blocker would make a graded answer ambiguous. The most common blockers:", ""]
    cats = Counter(r["blocker"] for r in reg if r["status"] == "held")
    L += [f"- {k}: {v}" for k, v in cats.most_common()]
    L += ["", "Largest held pools that could become tasks with further work: Code_Aster validation cases (50 cases, 761 checks; prompts must be transcribed from the V-documents and geometry built from their figures), SFEM (61, needs realised loads), Bath auxetics (18, Inventor CAD), GeoPINONet lugs (80, bore-load distribution).", "",
          "## Limitations", "",
          "- All sources are public; a model may have seen them. NAFEMS tasks are calibration only.",
          "- Several references come from unconverged source meshes (flagged per task); tolerances absorb typical discretisation differences, not modelling errors.",
          "- Licences differ: some sources are CC BY / Apache / GPL, others carry no licence and are for local research only (`source.redistributable` is false). Do not publish the candidate package as a whole.",
          "- No frontier-model results yet.", "",
          "## Files", "",
          "- `candidate/` (give to the model): `tasks.jsonl`, `tasks/<task_id>/` inputs, `README.md`, `submission.schema.json`.",
          "- `evaluator/` (keep hidden): `references.jsonl`, `registry.jsonl`, `score.py`, `validation.json`, this card.",
          "- Builder: `cvpr2027/scripts/cadfem_bench/` (`build.py` and one adapter per source family).", ""]
    return "\n".join(L)
