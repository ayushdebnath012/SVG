"""Dataset card for CADFEM-Bench (v1.1 audit corrections, v1.2 convergence tolerances, v1.3 geometry gates + fcVM buckling),
written from the released files."""
from __future__ import annotations

import json
from collections import Counter, defaultdict

import common as C

INFO = {
    "simjeb-bracket": ("GE jet-engine bracket competition designs", "4-case linear static", "SimJEB published OptiStruct displacement maxima"),
    "agentfem-bracket": ("Double-arm support bracket family", "linear static", "publisher summary table"),
    "geopinonet-holed-plate": ("Steel plate with a through hole", "2 static load cases", "maxima of the published ANSYS nodal CSVs"),
    "morphing-wing-plates": ("Uniform/stepped PLA morphing-wing plates", "modal", "publisher workbook cells (shell models)"),
    "cycloidal-drive-components": ("Cycloidal gearbox parts (PETG-CF, steel pins)", "linear static", "maxima of the saved CalculiX FRD files"),
    "cadworld-freecad-fem": ("Multi-feature aluminium part", "linear static, publisher mesh protocol", "publisher evaluator values"),
    "nafems-calibration": ("NAFEMS LE1, LE10, LE11", "plane stress, 3-D static, thermoelastic", "NAFEMS targets (FeenoX output)"),
    "feenox-valve-transient": ("Power-plant valve, carbon + stainless steel", "nonlinear transient thermal", "published FeenoX history"),
    "rigging-plate": ("7075-T6 rigging plate (5 load tests + drawing)", "linear static, figure-specified BCs", "result-legend maxima"),
    "femcad-hard": ("Specification-defined solids (shell, L-bracket, hull octant, holed plate, tube)", "electrostatics, linear static, steady heat", "closed form or page-stated values (Wolfram FEM docs)"),
    "fcvm-buckling": ("Steel members and welded assemblies (bar, beams, girders, handle)", "linear eigenvalue buckling", "fcVM published output (elastic buckling factors)"),
}


def jl(p):
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def write(val: dict, ver: dict) -> str:
    tasks, refs = jl(C.CAND / "tasks.jsonl"), {r["task_id"]: r for r in jl(C.EVAL / "references.jsonl")}
    held, reg = jl(C.OUT / "held/tasks.jsonl"), jl(C.EVAL / "registry.jsonl")
    held_refs = {r["task_id"]: r for r in jl(C.OUT / "held/references.jsonl")}
    georefs = json.loads((C.ROOT / "output/geometry-references-v1.3/references.json").read_text())
    gtasks = [t for t in tasks if refs[t["task_id"]].get("geometry_check")]
    fc = sorted([refs[t["task_id"]] for t in tasks if t["family"] == "fcvm-buckling"]
                + [r for r in held_refs.values() if r["family"] == "fcvm-buckling"], key=lambda r: r["task_id"])
    fam = defaultdict(list)
    for t in tasks:
        fam[t["engineering_family"]].append(t)
    cad = defaultdict(set)
    for t in tasks:
        for i in t["inputs"]:
            if i["role"] == "cad":
                cad[t["engineering_family"]].add(i["sha256"])
    big = sum(len(fam[f]) for f in ("simjeb-bracket", "agentfem-bracket", "geopinonet-holed-plate"))
    tr = Counter((t["track"], t["tier"]) for t in tasks)
    rc = Counter(x["ref_class"] for r in refs.values() for x in r["references"].values())
    hold = Counter(t["hold_reason"] for t in held)
    L = [f"# CADFEM-Bench v{C.VERSION}: published-source CAD + FEM pilot", "",
         f"Released {C.DATE}. **{len(tasks)} active tasks, {val['graded_outputs']} graded outputs, {len(fam)} engineering families, "
         f"{sum(len(v) for v in cad.values())} distinct CAD inputs** ({ver['distinct_cad_files']} STEP/BREP files, all valid in OpenCASCADE, and "
         f"{sum(len(v) for v in cad.values()) - ver['distinct_cad_files']} Gmsh geometry scripts for NAFEMS). Every graded target is a value published by its source; none was computed for this release. "
         f"{len(held)} further tasks are held with their reasons, and {val['excluded_local_targets']} locally computed targets from v1.0 are excluded.", "",
         "**What this release is:** a source-backed pilot for evaluating whether a model can set up and run a CAD/FEM analysis that reproduces published results. "
         f"**What it is not:** a certified benchmark. {val.get('independently_reproduced_tasks', 0)} tasks are independently reproduced, most tolerances are provisional, and "
         f"{big} of {len(tasks)} tasks ({100 * big / len(tasks):.0f} %) come from three parametric families (SimJEB, AgentFEM, GeoPINONet). "
         "It does not establish breadth across mechanical engineering: there is no frictional contact, plasticity, forming, crash, fatigue or coupled assembly mechanics among the active tasks.", "",
         "## Changes in v1.3 (2026-10-14)", "",
         f"- **Drawing/specification -> CAD tasks restored with a geometry gate ({len(georefs)} tasks; all {len(gtasks)} track-B tasks are now gated).** v1.1 held these {len(georefs)} because no geometry check existed. Each now has an evaluator-only "
         "reference solid built from the task's own specification (the NAFEMS LE10 one is the source CAD). It is accepted only if its OpenCASCADE volume matches an independent value: "
         f"a closed form, or Pappus's theorem for the revolved LE11 profile; the largest disagreement is {max(r['relative_volume_error'] for r in georefs.values()):.0e}. "
         "The gate is the rigging one: align the submitted part.step to the reference (bounding-box centres, 24 proper axis rotations) and require a relative symmetric volume difference of at most 2 %. "
         "The LE1 membrane is 2-D, so its prompt fixes a 100 mm +z extrusion as an exchange convention; the LE10/LE11 prompts require millimetres.",
         f"- **fcVM elastic buckling (new family).** These are 8 FreeCAD buckling models from the fcVM workbench, with the source's own published outputs. The load set rebuilt from each model's constraints, using fcVM's rules, "
         "matches the 'Sum of loads' printed in its output. All 14 fcVM models agree to print precision. An independent FEniCSx/SLEPc study then repeats the linear buckling eigenproblem "
         "(quadratic tetrahedra, element size reduced by 0.8 per step; where finer meshes exceed the study machine's memory the sequence is completed on the coarse side with the same ratio). "
         "The published first factor is graded only under the cycloidal rule: last refinement change < 1 %, previous < 2 %, and band "
         "|finest - published| / published + 2 x last change <= 10 %. The tolerance is that band, at least 5 %. "
         f"Result: {val.get('fcvm_buckling_tasks', 0)} admitted (now {val.get('independently_reproduced_tasks', 0)} independently reproduced tasks in total), {val.get('fcvm_held_by_study', 0)} held. Plastic-collapse and post-buckling factors from the same source are held (registry `fcvm-collapse`): "
         "there is no independent elastoplastic or geometric-nonlinear replay. Where a gap is large, one extra solve on a coarser mesh near fcVM's element count is reported "
         "as a diagnostic. It shows whether the gap is a coarse-mesh effect and never changes a decision.",
         "- **Registry recounted after every hold.** v1.2 listed the cycloidal source as 15 tasks with none reproduced; the registry now counts active and held tasks and reproduced tasks after the convergence holds.",
         "- **FEMCAD-Hard prompts** no longer ask for separate part.py and fem.py files, which conflicted with the single main.py in the artifact contract.", "",
         "| fcVM model | published lambda1 | finest independent | difference | last refinement change | decision |", "|---|---:|---:|---:|---:|---|"] + [
         f"| {r['task_id'].replace('A-FCVM-', '')} | {r['fcvm_assessment']['published_lambda1']:g} | "
         + (f"{r['fcvm_assessment']['finest']:.5g} | {100 * r['fcvm_assessment']['relative_difference']:+.1f} % | {100 * r['fcvm_assessment']['last_change']:.2f} % | "
            if "finest" in r["fcvm_assessment"] else "- | - | - | ")
         + (f"admitted, tolerance {100 * r['references']['lambda1']['tol']['value']:.0f} % |" if r.get("status") != "held" else f"held: {r['fcvm_assessment']['reason']} |")
         for r in fc] + ["",
         "## Changes in v1.2 (2026-10-14)", "",
         f"- **Cycloidal tolerances from an independent mesh-convergence study.** The published displacements of these parts are coarse-mesh values: the coupler's converges about 5 % above it, outside the old 5 % tolerance. "
         "An independent FEniCSx study (second-order geometry, quadratic displacement, up to six meshes per part, force balance < 1e-8) sets each part's tolerance to "
         "|finest independent - published| / published + 2 x last refinement change, rounded up to 1 % (at least the old 5 %). A part is admitted only if its refinement settled (last change < 1 %, previous < 2 %), "
         "the relative force-balance residual is below 1e-6 (the study script used 1e-8; residuals of 1e-8 to 1e-7 are exact at these tolerances) and the band is at most 10 %; otherwise it is held with the reason. "
         f"Result: {val.get('convergence_band_tasks', 0)} parts admitted with study-based tolerances, {val.get('held_by_convergence', 0)} held. The published values are unchanged; the study is evaluator evidence, never a target.",
         f"- **Independently reproduced tasks in v1.2: {val.get('convergence_band_tasks', 0) + 1}** (the cycloidal parts above and AgentFEM fresh_test_000 from the 2026-10-14 follow-up).", "",
         "| cycloidal part | published (mm) | finest independent (mm) | difference | last refinement change | tolerance |", "|---|---:|---:|---:|---:|---:|"] + [
         f"| {t['task_id'].replace('A-CYC-', '')} | {refs[t['task_id']]['references']['max_displacement_mm']['value']:.6g} | "
         f"{refs[t['task_id']]['references']['max_displacement_mm']['independent_finest_mm']:.6g} | "
         f"{100 * (refs[t['task_id']]['references']['max_displacement_mm']['independent_finest_mm'] / refs[t['task_id']]['references']['max_displacement_mm']['value'] - 1):+.1f} % | "
         f"{next((f.split('last refinement change ')[1].rstrip('.') for f in refs[t['task_id']]['flags'] if 'last refinement change' in f), '')} | "
         f"{100 * refs[t['task_id']]['references']['max_displacement_mm']['tol']['value']:.0f} % |"
         for t in tasks if t["family"] == "cycloidal-drive-components"] + ["",
         "## Changes from v1.0 (audit of 2026-10-13)", "",
         "| audit finding | action in v1.1 |", "|---|---|",
         "| Numerical answers passed without any CAD/FEM workflow | Scoring now reports `numerical_passed` and `workflow_verified` separately; a pass needs both. Workflow verification requires eight artifacts (results, script, STEP, mesh, fields, solver log, refinement study, environment) and a trusted evaluator review bound to the task, run and artifact hashes (`evaluator/REVIEW_PROTOCOL.md`). |",
         "| 190 targets were computed by the local SimJEB grader | Removed: SimJEB analysis tasks keep only SimJEB's published OptiStruct displacement maxima; the 40 design/redesign/lighten tasks (graded by the local FEM grader) are held. |",
         "| Two SimJEB STEP files fail OpenCASCADE validity | Held (analysis 15 and 120; lighten 15/120 are held with track C). Every active CAD input is checked valid at build time. |",
         "| Reconstruction tasks had no geometry check | Rigging drawing task: volume-overlap gate against the original CAD after alignment over the 24 axis rotations (2 % symmetric difference). The other 8 reconstruction tasks are held until a geometry validator exists for them. |",
         "| CADWorld 'Tresca' target was really (s1 - s3)/2 | Output renamed `max_shear_stress_MPa` and defined explicitly; value unchanged (397.017 MPa). |",
         "| Track C could not run from the folder | Held (needs the external SimJEB evaluator and FEniCSx environment). |",
         "| One malformed answer crashed the scorer | Strict per-task validation (types, exact keys, duplicate keys, finite numbers); errors are reported per task and scoring continues. |",
         "| 'Gold' overstated validation | Tiers renamed: `source_backed_pilot`, `figure_reference`, `control`. Original source files for every reference are in an evaluator-only evidence bundle with hashes. |",
         "| Composition overstated breadth | Counts by engineering family, distinct CAD and track below; summaries use an engineering-family macro-average (SimJEB counts once). |", "",
         "## Composition", "",
         "| engineering family | tasks | graded outputs | distinct CAD files | geometry | physics | reference source |", "|---|---:|---:|---:|---|---|---|"]
    for f, ts in sorted(fam.items(), key=lambda kv: -len(kv[1])):
        g, ph, src = INFO.get(f, ("", "", ""))
        n = sum(len(refs[t["task_id"]]["references"]) for t in ts)
        L.append(f"| {f} | {len(ts)} | {n} | {len(cad[f])} | {g} | {ph} | {src} |")
    L += ["", "By track and tier: " + "; ".join(f"track {k[0]} {k[1]}: {v}" for k, v in sorted(tr.items())) + ". "
          f"Track A supplies the CAD; track B ({sum(t['track'] == 'B' for t in tasks)} tasks) supplies a drawing or written specification, and the model must build and submit the CAD.", "",
          "Reference classes: " + ", ".join(f"{k} {v}" for k, v in rc.most_common()) + ".", "",
          "## Scoring", "",
          "`evaluator/score.py` never executes candidate code. Per task it reports `numerical_passed` (every requested quantity within its tolerance), "
          "`workflow_verified` (all eight artifacts present, a valid STEP solid, the track-B geometry gate, and a matching trusted review "
          "approving execution, geometry, set-up, field extraction and convergence) and `passed` (both). Summaries give pass rates per track, tier and "
          "engineering family, plus the engineering-family macro-average.", "",
          "```", "python evaluator/score.py --refs evaluator/references.jsonl --tasks candidate/tasks.jsonl \\",
          "    --submissions runs/<model> --run-id <run> --reviews reviews.jsonl --out score.json", "```", "",
          "Tolerances (per output in `references.jsonl`): cycloidal parts and fcVM buckling factors use their convergence-study tolerance (see above); otherwise provisional: 5 % for displacement, frequency and temperature; 10 % for SimJEB and AgentFEM displacements "
          "(the AgentFEM publisher states its mesh is not converged) and for through-wall temperature differences; 20 % for rigging legend stresses; 5 % for CADWorld (publisher protocol).", "",
          "## Held tasks", ""]
    L += [f"- {n} tasks: {r}" for r, n in hold.most_common()]
    L += ["", f"The source registry (`evaluator/registry.jsonl`) lists all {len(reg)} collected collections: "
          + ", ".join(f"{v} {k}" for k, v in Counter(r['status'] for r in reg).most_common()) + ", each with its blocker.", "",
          "## Verification at build time", "",
          f"- {ver['inputs_hash_checked']} candidate input files hash-checked; {ver['distinct_cad_files']} distinct CAD files, all valid in OpenCASCADE.",
          f"- {ver['evidence_files']} evidence files ({ver['evidence_bytes'] / 1e6:.0f} MB) hash-checked; every reference names its evidence.",
          "- No locally computed (verifier) target remains; no reference number appears in any prompt or text input.",
          f"- Scorer probes: exact answers alone give {ver['scorer_probes']['answers_only']['numerical_passed']} numerical passes and "
          f"{ver['scorer_probes']['answers_only']['passed']} passes; answers scaled by 1.3 give {ver['scorer_probes']['perturbed_numerical_passed']} numerical passes; "
          "four malformed submissions are rejected without stopping the run; a fully reviewed probe submission passes and is rejected after one artifact is changed; "
          f"each of the {len(ver['geometry_gate_probes'])} geometry gates accepts its reference solid rotated and moved and rejects it scaled by 3 %; "
          f"submitting the independent finest-mesh values passes all {ver['converged_value_probe']['tasks']} convergence-study tasks.", "",
          "## Limitations", "",
          f"- Pilot: {val.get('independently_reproduced_tasks', 0)} of {len(tasks)} tasks independently reproduced; the remaining tolerances are provisional source protocols, and the study-based ones are empirical, not certified uncertainty bounds.",
          "- Several references come from unconverged or idealised source models (AgentFEM 9 mm mesh, shell models for the wing plates, figure-defined supports for the rigging plate).",
          "- Workflow verification depends on a trusted human or isolated-runner review; the scorer checks hashes and attestations, not execution.",
          "- All sources are public; prior exposure is possible. NAFEMS tasks are calibration only.",
          "- Licences differ; several sources are local-research-only (`source.redistributable` false). Do not publish the package as a whole.", ""]
    return "\n".join(L)
