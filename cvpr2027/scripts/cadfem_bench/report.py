"""PDF report for CADFEM-Bench: composition, audit corrections (v1.1), convergence tolerances (v1.2), geometry gates and fcVM
buckling (v1.3), verification, one page per engineering family with CAD renders, held tasks and the source registry.  tmp/cq-env/bin/python scripts/cadfem_bench/report.py
"""
from __future__ import annotations

import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import common as C
import render

PDF = C.ROOT / f"output/pdf/{C.OUT.name}.pdf"
IMG = C.ROOT / f"tmp/{C.OUT.name}-report"
BLUE, RED = (0.25, 0.5, 1.0), (1.0, 0.3, 0.22)
st = getSampleStyleSheet()
st["BodyText"].fontSize, st["BodyText"].leading = 9, 12
st["Heading1"].fontSize, st["Heading1"].leading = 16, 20
st["Heading2"].fontSize, st["Heading2"].leading = 12, 15
small = st["BodyText"].clone("small", fontSize=7.4, leading=9.2)
mono = st["Code"].clone("mono", fontSize=6.9, leading=8.4)
story: list = []


def p(s, style=None):
    story.extend([Paragraph(s, style or st["BodyText"]), Spacer(1, 5)])


def h(s, lvl=1):
    story.extend([Paragraph(s, st[f"Heading{lvl}"]), Spacer(1, 6)])


def table(rows, widths, style=small, head=True):
    t = Table([[Paragraph(html.escape(str(x)), style) for x in r] for r in rows], colWidths=widths, repeatRows=1 if head else 0)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e4edf4") if head else colors.white),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5), ("LINEBELOW", (0, 0), (-1, -1), .3, colors.lightgrey)]))
    story.extend([t, Spacer(1, 7)])


def pics(files, w=500, mh=170):
    cells = []
    for f in files:
        im = PILImage.open(f)
        cw = w / len(files)
        hh = cw * im.height / im.width
        sc = min(1.0, mh / hh)
        cells.append(Image(str(f), width=cw * sc, height=hh * sc))
    t = Table([cells], colWidths=[w / len(files)] * len(files))
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.extend([t, Spacer(1, 6)])


def faces_in(line: str) -> list[int]:
    return [int(x) for x in re.findall(r"face (\d+):", line)]


def cad_png(task: dict, name: str, view=(24, -58)) -> Path:
    cad = next(i for i in task["inputs"] if i["role"] == "cad")
    hl = {}
    for line in task["prompt"].splitlines():
        if line.startswith("Supports:"):
            hl.update({f: BLUE for f in faces_in(line)})
        if line.startswith(("Load:", "Reference load set")):
            hl.update({f: RED for f in faces_in(line)})
    return render.render(C.CAND / cad["path"], IMG / f"{name}.png", hl or None, view=view)


def convergence_plot(tasks: list, refs: dict) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ts = [t for t in tasks if t["family"] == "cycloidal-drive-components"]
    held = [json.loads(x) for x in (C.OUT / "held/tasks.jsonl").read_text().splitlines() if x.strip()]
    ts += [t for t in held if t["family"] == "cycloidal-drive-components" and "convergence" in t.get("hold_reason", "")
           and (C.EVAL / "evidence/cycloidal-convergence-study" / t["task_id"] / "study.json").exists()]
    n, cols = len(ts), 5
    fig, axs = plt.subplots((n + cols - 1) // cols, cols, figsize=(15, 2.9 * ((n + cols - 1) // cols)), dpi=110)
    for ax, t in zip(axs.flat, ts):
        st = json.loads((C.EVAL / "evidence/cycloidal-convergence-study" / t["task_id"] / "study.json").read_text())
        h = [r["mesh_size_mm"] for r in st["mesh_runs"]]
        u = [r["outputs"]["max_displacement_mm"] for r in st["mesh_runs"]]
        pub = st["published_reference_mm"]
        ax.plot(h, u, "o-", color="#2a6fb0", ms=4, label="independent solve")
        ax.axhline(pub, color="#c0392b", lw=1.2, label="published")
        r = refs.get(t["task_id"])
        if r:
            tol = r["references"]["max_displacement_mm"]["tol"]["value"]
            ax.axhspan(pub * (1 - tol), pub * (1 + tol), color="#27ae60", alpha=0.15, label="tolerance")
        ax.set_xscale("log")
        ax.minorticks_off()
        ax.set_xticks(h)
        ax.set_xticklabels([f"{x:g}" for x in h], fontsize=6)
        ax.invert_xaxis()
        ax.set_title(t["task_id"].replace("A-CYC-", "") + ("" if r else " [held]"), fontsize=8)
        ax.tick_params(labelsize=6.5)
        ax.set_xlabel("element size h (mm)", fontsize=7)
    for ax in list(axs.flat)[n:]:
        ax.axis("off")
    axs.flat[0].legend(fontsize=6)
    fig.tight_layout()
    p = IMG / "cycloidal-convergence.png"
    fig.savefig(p)
    plt.close(fig)
    return p


def fcvm_cases(tasks: list, refs: dict) -> list:
    held = {r["task_id"]: r for r in (json.loads(x) for x in (C.OUT / "held/references.jsonl").read_text().splitlines() if x.strip())}
    return sorted([refs[t["task_id"]] for t in tasks if t["family"] == "fcvm-buckling"]
                  + [r for r in held.values() if r["family"] == "fcvm-buckling"], key=lambda r: r["task_id"])


def fcvm_plot(cases: list) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n, cols = len(cases), 4
    rows_ = (n + cols - 1) // cols
    fig, axs = plt.subplots(rows_, cols, figsize=(15, 3.0 * rows_), dpi=110)
    for ax, r in zip(axs.flat, cases):
        a = r["fcvm_assessment"]
        h = [x["h_mm"] for x in a["runs"]]
        lam = [x["lambda1"] for x in a["runs"]]
        pub = a["published_lambda1"]
        ax.plot(h, lam, "o-", color="#2a6fb0", ms=4, label="independent eigen solve")
        ax.axhline(pub, color="#c0392b", lw=1.2, label="published (fcVM)")
        if r.get("status") != "held":
            tol = r["references"]["lambda1"]["tol"]["value"]
            ax.axhspan(pub * (1 - tol), pub * (1 + tol), color="#27ae60", alpha=0.15, label="tolerance")
        for d in a.get("coarse_diagnostic", []):
            ax.plot([d["h_mm"]], [d["lambda1"]], "s", color="#8e44ad", ms=5, label="fcVM-size mesh (diagnostic)")
        if h:
            ax.set_xscale("log")
            ax.minorticks_off()
            hs = sorted(set(h + [d["h_mm"] for d in a.get("coarse_diagnostic", [])]))
            ax.set_xticks(hs)
            ax.set_xticklabels([f"{x:.3g}" for x in hs], fontsize=6)
            ax.invert_xaxis()
        ax.set_title(r["task_id"].replace("A-FCVM-", "") + ("" if r.get("status") != "held" else " [held]"), fontsize=8)
        ax.tick_params(labelsize=6.5)
        ax.set_xlabel("element size h (mm)", fontsize=7)
    for ax in list(axs.flat)[n:]:
        ax.axis("off")
    hdl = {}
    for ax in axs.flat:
        for hh, ll in zip(*ax.get_legend_handles_labels()):
            hdl.setdefault(ll, hh)
    axs.flat[0].legend(hdl.values(), hdl.keys(), fontsize=6)
    fig.tight_layout()
    p = IMG / "fcvm-convergence.png"
    fig.savefig(p)
    plt.close(fig)
    return p


def v15_plot(prim_refs: list, other_refs: list) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pl = sorted([r for r in prim_refs + other_refs if r["family"] == "fcvm-plastic-limit"], key=lambda r: r["task_id"])
    cr = sorted([r for r in prim_refs + other_refs if r["family"] == "interface-crack-fracture"], key=lambda r: r["crack_assessment"]["theta_deg"])
    n = len(pl) + len(cr)
    cols = 4
    rows_ = (n + cols - 1) // cols
    fig, axs = plt.subplots(rows_, cols, figsize=(15, 2.9 * rows_), dpi=110)
    axs = list(getattr(axs, "flat", [axs]))
    k = 0
    for r in pl:
        ax, a = axs[k], r["plastic_assessment"]
        k += 1
        h = [x["h_mm"] for x in a["runs"]]
        lam = [x["lambda_limit"] for x in a["runs"]]
        pub = a["published_limit_factor"]
        ax.plot(h, lam, "o-", color="#2a6fb0", ms=4, label="independent limit analysis")
        ax.axhline(pub, color="#c0392b", lw=1.2, label="published (fcVM)")
        if r.get("status") != "held":
            tol = r["references"]["limit_load_factor"]["tol"]["value"]
            ax.axhspan(pub * (1 - tol), pub * (1 + tol), color="#27ae60", alpha=0.15, label="tolerance")
        for c in a.get("coarse_diagnostic", []):
            ax.plot([c["h_mm"]], [c["lambda1"]], "s", color="#8e44ad", ms=5, label="fcVM-size mesh (diagnostic)")
        if h:
            ax.set_xscale("log")
            ax.minorticks_off()
            hs = sorted(set(h + [c["h_mm"] for c in a.get("coarse_diagnostic", [])]))
            ax.set_xticks(hs)
            ax.set_xticklabels([f"{x:.3g}" for x in hs], fontsize=6)
            ax.invert_xaxis()
        ax.set_title(a["case"] + (" [held]" if r.get("status") == "held" else " [calibration]" if r["tier"] == "control" else ""), fontsize=8)
        ax.set_xlabel("element size h (mm)", fontsize=7)
        ax.tick_params(labelsize=6.5)
    for r in cr:
        ax, a = axs[k], r["crack_assessment"]
        k += 1
        for tip, col in (("right", "#2a6fb0"), ("left", "#e67e22")):
            x = a["tips"][tip]
            ax.plot([l["level"] for l in x["levels"]], [l["G"] for l in x["levels"]], "o-", color=col, ms=4, label=f"independent J, {tip} tip")
            ax.axhline(x["published_G"], color=col, lw=1, ls="--", label=f"published, {tip} tip")
        ax.set_title(f"SSLP311 theta = {a['theta_deg']} deg", fontsize=8)
        ax.set_xlabel("mesh level (element size halves per level)", fontsize=7)
        ax.set_ylabel("G (J/m^2)", fontsize=7)
        ax.tick_params(labelsize=6.5)
    for ax in axs[k:]:
        ax.axis("off")
    for ax in axs[:k]:
        ax.legend(fontsize=5.5)
    fig.tight_layout()
    out = IMG / "v15-studies.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def main() -> None:
    jl = lambda p: [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    tasks, reg, held = jl(C.CAND / "tasks.jsonl"), jl(C.EVAL / "registry.jsonl"), jl(C.OUT / "held/tasks.jsonl")
    refs = {r["task_id"]: r for r in jl(C.EVAL / "references.jsonl")}
    val = json.loads((C.EVAL / "validation.json").read_text())
    ver = json.loads((C.EVAL / "verification.json").read_text())
    T = {t["task_id"]: t for t in tasks}
    fam = defaultdict(list)
    for t in tasks:
        fam[t["engineering_family"]].append(t)

    h(f"CADFEM-Bench v{C.VERSION}: published-source CAD + FEM pilot")
    big = sum(len(fam[f]) for f in ("simjeb-bracket", "agentfem-bracket", "geopinonet-holed-plate"))
    p(f"{C.DATE}. <b>{len(tasks)} active tasks</b> with <b>{val['graded_outputs']} graded outputs</b> in {len(fam)} engineering families; "
      f"{len(held)} tasks held with reasons; {val['excluded_local_targets']} locally computed v1.0 targets excluded. Every graded target is a value published by its "
      "source (saved solver results, publisher tables and evaluators, result legends, NAFEMS targets); none was computed for this release. "
      f"This is a <b>source-backed pilot</b>, not a certified benchmark: {val.get('independently_reproduced_tasks', 0)} tasks are independently reproduced, most tolerances are provisional, and "
      f"{big} of {len(tasks)} tasks come from three parametric families (SimJEB, AgentFEM, GeoPINONet). Frictional contact, plasticity, forming, crash, fatigue and "
      "coupled assembly mechanics are not covered by the active tasks.")
    if "fcvm_plastic_tasks" in val:   # v1.5: new physics families
        p(f"<b>Changes in v1.5.</b> Two physics classes that were missing from the active tasks are added, each graded only after an independent "
          f"solver run settles within a 10 % band around the published value. (1) <b>Plasticity</b>: {val['fcvm_plastic_tasks']} fcVM elastic-perfectly "
          "plastic collapse (limit) load factors, checked by an independent FEniCSx limit analysis; the tensile bar (closed form) is calibration. "
          f"(2) <b>Fracture</b>: {val['interface_crack_tasks']} Code_Aster SSLP311 tasks, energy release rates at both tips of a crack on an inclined "
          "bimaterial interface (published boundary-element reference), checked by an independent J-integral study. All v1.4 tasks and targets are "
          "unchanged. Held after review: " + ", ".join(val.get("v15_held", [])) + "; the Hertz-contact and indentation cases, whose analytical "
          "references do not fit the posed geometry; frictional contact remains absent.")
    if "suite_counts" in val:      # v1.4+: balanced suites derived from the v1.3 pool
        rv = C.EVAL / "runtime-validation"
        fc_ok = json.loads((rv / "solver-job-002/field-check.json").read_text())
        fc_bad = json.loads((rv / "tampered-field-check.json").read_text())
        sbx = ver["sandbox_probe"]
        cpl = refs["A-CYC-Coupler-PETGCF"]["references"]["max_displacement_mm"]
        p(f"<b>Release v1.4: balanced primary suite.</b> Models receive only the primary suite: at most five tasks per engineering family, so the "
          f"bracket and holed-plate families contribute {sum(len(fam[f]) for f in ('simjeb-bracket', 'agentfem-bracket', 'geopinonet-holed-plate'))} of "
          f"{len(tasks)} tasks instead of 84 of 126. The rest of the v1.3 pool is kept in evaluator-only suites that are scored separately, never added "
          "to the primary score. All targets, tolerances and task texts are the v1.3 ones.")
        rows = [["suite", "tasks", "graded outputs", "role", "release check (this build)"]]
        su = ver["suites"]
        rows.append(["primary (candidate/)", len(tasks), val["graded_outputs"], "the scored comparison suite",
                     f"exact answers {ver['scorer_probes']['answers_only']['numerical_passed']}/{len(tasks)} numerical, 0 passes; x1.3 answers "
                     f"{ver['scorer_probes']['perturbed_numerical_passed']}; {len(ver['geometry_gate_probes'])} geometry gates probed"])
        role = {"calibration": "NAFEMS controls; report separately", "reserved-public": "public-source tasks kept out of model inputs (not a private hold-out)",
                "related-public": "shares CAD with a primary task"}
        for k, x in su.items():
            rows.append([k, x["tasks"], x["graded_outputs"], role.get(k, ""),
                         f"exact answers {x['answers_only_numerical_passed']}/{x['tasks']} numerical, 0 passes; x1.3 answers {x['perturbed_numerical_passed']}"
                         + (f"; {len(x['geometry_gate_probes'])} geometry gates probed" if x["geometry_gate_probes"] else "")])
        rows.append(["full pool (task-pool/)", val["suite_counts"]["full_source_backed_pool"], "", "v1.3 tasks and references, unchanged", ""])
        table(rows, [92, 34, 46, 140, 200])
        p(f"<b>Execution and field checks.</b> <i>evaluator/sandbox_runner.py</i> freezes a submission and its inputs and replays main.py offline. "
          f"A denial probe re-run against this folder ({sbx['backend']}) was blocked from reading this package, the released v1.3 references and workspace "
          "source data, writing outside its job, modifying inputs and opening network connections; the pinned CadQuery/Gmsh/NumPy/SciPy runtime still "
          f"imported. A trusted software solver replayed the cycloidal coupler in the sandbox: maximum displacement {fc_ok['extracted_max_displacement_mm']:.6g} mm "
          f"on {fc_ok['elements']} elements (published {cpl['value']:.6g} mm, tolerance {100 * cpl['tol']['value']:.0f} %). <i>verify_static_fields.py</i> re-assembles the source-defined operator: "
          f"relative residual {fc_ok['source_operator_residual_relative']:.1e} for that field, and {fc_bad['source_operator_residual_relative']:.1e} "
          "(rejected) for the same field scaled by 1.001. These are infrastructure checks and one solver baseline, not model or expert runs; "
          "boundary-face scope, geometry and convergence still need the trusted review. The common run protocol (budgets, attempts, provenance, "
          "separate numerical/execution/geometry/workflow metrics) is in <i>evaluator/evaluation-protocol.json</i>.")
    nb = sum(t["track"] == "B" for t in tasks)
    p(f"<b>Tracks.</b> A: the model receives the CAD and the source set-up and must compute the requested results ({len(tasks) - nb} tasks). "
      f"B: the model receives a dimensioned drawing or written specification, builds the CAD and analyses it ({nb} tasks; the built part is gated against an evaluator-only reference solid). "
      "<b>Tiers.</b> source_backed_pilot (numerical published reference), figure_reference (legend value, set-up partly from the source's BC figure), control (NAFEMS).")
    rows = [["engineering family", "tracks", "tiers", "tasks", "graded outputs", "distinct CAD", "physics", "reference class"]]
    for f, ts in sorted(fam.items(), key=lambda kv: -len(kv[1])):
        rc = sorted({r["ref_class"] for t in ts for r in refs[t["task_id"]]["references"].values()})
        n = sum(len(refs[t["task_id"]]["references"]) for t in ts)
        ncad = len({i["sha256"] for t in ts for i in t["inputs"] if i["role"] == "cad"})
        rows.append([f, "/".join(sorted({t["track"] for t in ts})), "/".join(sorted({t["tier"] for t in ts})), len(ts), n, ncad,
                     ", ".join(sorted({x for t in ts for x in t["physics"]})), ", ".join(rc)])
    rows.append(["total", "", "", len(tasks), val["graded_outputs"], len({i["sha256"] for t in tasks for i in t["inputs"] if i["role"] == "cad"}), "", ""])
    table(rows, [92, 32, 70, 30, 40, 38, 100, 98])
    fc = fcvm_cases(tasks, refs)
    geo_refs = json.loads((C.ROOT / "output/geometry-references-v1.3/references.json").read_text())
    nfa = sum(r.get("status") != "held" for r in fc)
    p(f"<b>Changes in v1.3 (2026-10-14).</b> (1) The {len(geo_refs)} drawing/specification-to-CAD tasks held in v1.1 for lack of a geometry check are restored. Each has an "
      "evaluator-only reference solid built from the task's own specification (NAFEMS LE10: the source CAD) and accepted only if its volume matches a closed form or Pappus's theorem "
      f"(worst disagreement {max(r['relative_volume_error'] for r in geo_refs.values()):.0e}). The submitted part must match it within 2 % symmetric volume difference after alignment. "
      f"(2) New family: fcVM elastic buckling. These are 8 FreeCAD steel models with the source's published outputs. The load set rebuilt from each model matches the published load sum, and an independent "
      f"FEniCSx/SLEPc eigenvalue study admits the published first factor only if it settles within the cycloidal rule: {nfa} admitted, {len(fc) - nfa} held. "
      "Plastic-collapse and post-buckling factors from the same source are held. (3) Registry counts are recomputed after every hold.")
    p(f"<b>Changes in v1.2 (2026-10-14).</b> The published cycloidal displacements are coarse-mesh values (the coupler converges about 5 % above its "
      "reference, outside the old 5 % tolerance). An independent FEniCSx convergence study now sets each part's tolerance to the observed published-vs-converged "
      f"difference plus twice the last refinement change (at least 5 %); {val.get('convergence_band_tasks', 0)} parts are admitted this way and "
      f"{val.get('held_by_convergence', 0)} held. Published values are unchanged. AgentFEM fresh_test_000 is recorded as reproduced (follow-up study).")
    p("<b>Changes from v1.0 (audit of 2026-10-13).</b> (1) Scoring separates <i>numerical_passed</i> from <i>workflow_verified</i>; a pass needs both, and workflow "
      "verification needs eight artifacts (results, script, STEP, mesh, fields, solver log, refinement study, environment) plus a trusted review bound to task, run "
      "and artifact hashes. (2) The 190 targets computed by the local SimJEB grader are removed; SimJEB analysis keeps SimJEB's published displacement maxima and the "
      "40 design tasks are held. (3) The two SimJEB STEP files that fail OpenCASCADE validity are held. (4) The rigging drawing task has a volume-overlap gate against "
      "the original CAD after alignment over the 24 axis rotations; the other 8 reconstruction tasks are held. (5) CADWorld's 'Tresca' column is (s1 - s3)/2 and is "
      "now requested as maximum shear stress. (6) Malformed submissions are rejected per task without stopping the run. (7) Tiers are renamed to what they show, and "
      "the original source files for every reference ship in an evaluator-only evidence bundle with hashes.")
    sp = ver["scorer_probes"]
    p(f"<b>Verification at build time.</b> {ver['inputs_hash_checked']} input files and {ver['evidence_files']} evidence files hash-checked; all "
      f"{ver['distinct_cad_files']} distinct CAD files valid in OpenCASCADE; no reference number in any prompt or text input; no verifier target. Scorer probes: exact "
      f"answers alone give {sp['answers_only']['numerical_passed']} numerical passes and {sp['answers_only']['passed']} passes; answers scaled by 1.3 give "
      f"{sp['perturbed_numerical_passed']} numerical passes; four malformed submissions are rejected without stopping the run; a reviewed probe passes and is "
      f"rejected once an artifact changes; the {len(ver['geometry_gate_probes'])} geometry gates accept their reference solid rotated and moved (symmetric difference at most "
      f"{max(g['rotated_moved'] for g in ver['geometry_gate_probes'].values()):.2g}) and reject it scaled by 3 % (at least "
      f"{min(g['scaled_103'] for g in ver['geometry_gate_probes'].values() if g['scaled_103'] is not None):.3g}; limit 0.02; "
      f"{sum(g['scaled_103'] is None for g in ver['geometry_gate_probes'].values())} are rejected earlier by the solid-count or analytic-radius check); "
      "submitting the independent finest-mesh values passes all "
      f"{ver['converged_value_probe']['tasks']} convergence-study tasks. "
      "Earlier set-up checks still hold: cycloidal fixed node sets lie on the stated faces and per-face loads sum to the deck resultants; GeoPINONet section "
      "forces are -1000 N; AgentFEM CAD scaled to mm matches the FEM nodes; the valve's Gmsh surface tags equal the OpenCASCADE face indices.")
    story.append(PageBreak())

    pages = [
        ("simjeb-bracket", "GE jet-engine bracket: four-case analysis of real competition designs", ["A-SIMJEB-analysis-0", "A-SIMJEB-analysis-16", "A-SIMJEB-analysis-22"],
         "Ti-6Al-4V bracket, four GE load cases at the clevis pin (RBE3), rigid fully fixed bolts. Output per case: maximum displacement magnitude, graded against "
         "SimJEB's published OptiStruct maxima (10 %). Peak stress and the pass verdict are no longer graded (SimJEB does not publish them). Held: analyses 15 and 120 "
         "(invalid STEP) and all 40 design/redesign/lighten tasks (graded by the local FEM grader)."),
        ("agentfem-bracket", "AgentFEM double-arm support brackets (publisher test split)", [x["task_id"] for x in fam["agentfem-bracket"][:2]],
         "Aluminium bracket (E 70 GPa), foot undersides fixed, uniform downward seat traction of 1000 or 10000 N. Outputs: mean seat deflection and maximum displacement "
         "(publisher summary, 10 %; publisher mesh not converged). The source STEP declared mm but held metre values; the shipped copy is scaled to true mm and checked against the FEM nodes."),
        ("geopinonet-holed-plate", "GeoPINONet holed steel plates (validation split)", [x["task_id"] for x in fam["geopinonet-holed-plate"][:2]],
         "Structural steel, one end fixed, 1000 N on the opposite end face: compression (-y) and lateral (+x). Outputs: maximum displacement per case from the published ANSYS "
         "nodal CSVs (5 %). The archive's fixed/load STL names are swapped relative to the fields; supports and loads are stated from the verified fields."),
        ("morphing-wing-plates", "Active-camber morphing-wing cantilever plates (modal)", ["A-MORPHWING-Test1", "A-MORPHWING-Test5"],
         "FDM-printed PLA plates, uniform and with a 1 mm flexible strip, clamped at the end of a 19 mm grip. Outputs: first bending, first torsion and second bending "
         "frequencies from the publisher workbook (Abaqus thick shell / Nastran plate models, 5 %). The references are shell idealisations of solid CAD."),
        ("cycloidal-drive-components", "3D-printable cycloidal gearbox: component static analyses", ["A-CYC-Coupler-PETGCF", "A-CYC-Disk-PETGCF", "A-CYC-ShaftP2-radial-PETGCF"],
         "FreeCAD/CalculiX studies of 13 printed PETG-CF parts and 2 steel pins, each analysed alone (no gearbox contact). Blue: fixed faces; red: loaded faces "
         "(uniform traction, resultant from the source-corrected deck). Output: maximum displacement from the saved FRD files, with a tolerance set by an independent convergence study (see the study page); stress not graded (source error estimate 11-49 %)."),
        ("cadworld-freecad-fem", "CADWorld FreeCAD FEM task (publisher mesh protocol)", ["A-CADWORLD-001"],
         "Publisher geometry, material, constraints and mesh protocol (Gmsh, first-order tetrahedra); references are the values the publisher's evaluator checks (5 %). "
         "The publisher's 'Tresca' column is maximum shear stress (s1 - s3)/2 and is now requested under that name. The task reproduces the source's linear model "
         "(31 mm deflection of a 260 mm part, stresses above yield); it is not a strength assessment."),
        ("feenox-valve-transient", "Power-plant valve: nonlinear transient heat conduction", ["A-VALVE-transient"],
         "Carbon-steel nozzle and stainless bodies (4 solids), ASME temperature-dependent properties, internal temperature ramp 40-250-40 C over 1000 s, weak external "
         "convection. Outputs: through-wall temperature differences at two stress classification lines (10 %) and outer-wall temperatures at 100 s, from the published FeenoX history."),
        ("rigging-plate", "7075-T6 rigging plate: five ANSYS load tests and the drawing-to-CAD task (figure_reference)", ["A-RIGGING-test1"],
         "Supplied STEP (track A) or the dimensioned manufacturing drawing (track B) plus the source's boundary-condition figure per test. Output: maximum von Mises stress "
         "from the original legend (20 %). Track B: the built part must overlap the original CAD within 2 % symmetric difference after alignment. Material card and "
         "remote-coupling details are not published; tests 4 and 5 are left out (conflicting load labels; revised TEST-5R results)."),
        ("nafems-calibration", "NAFEMS calibration (control)", ["A-NAFEMS-LE10"],
         "NAFEMS LE1 (elliptic membrane), LE10 (thick elliptic plate) and LE11 (thermoelastic cylinder/taper/sphere) with supplied geometry. References are the FeenoX "
         "outputs, equal to the NAFEMS targets (5 %). Answers may be recalled; calibration only. Track B variants (LE1, LE10, LE11) supply the published geometry "
         "definition instead of the CAD; their geometry gates are on the geometry-gate page."),
        ("femcad-hard", "FEMCAD-Hard: specification-to-CAD-to-FEM tasks (track B)", ["B-FEMCAD-057"],
         "Five tasks from the Wolfram FEM documentation: spherical capacitor shell (electrostatics), L-bracket with a filleted inner corner, octant of a spherical "
         "pressure hull, plate with a hole in tension and a thick tube heated on an inner band. The model reads the written specification, builds the solid, meshes and "
         "solves it. References are closed-form or page-stated values with the page's tolerance; the built part is gated against the reference solid."),
        ("fcvm-plastic-limit", "fcVM plastic collapse (limit) load factors (v1.5)", [],
         "Steel parts from the fcVM workbench analysed as elastic-perfectly plastic von Mises bodies under proportional loading (small strain). Blue: "
         "supported faces; red: loaded faces. Output: the collapse load factor of the reference load set, graded against fcVM's published plateau "
         "value with a tolerance set by an independent limit-analysis convergence study (see the v1.5 study page)."),
        ("interface-crack-fracture", "Code_Aster SSLP311: crack on an inclined bimaterial interface (v1.5)", [],
         "A 4 x 8 mm plate of two elastic materials (E = 2.0e6 / 2.0e5 MPa) bonded along an inclined line through the centre, with a 2 mm crack on "
         "that line, in plane-stress tension. Supplied CAD: the domain extruded 0.1 mm, two solids, crack faces split out. Outputs: the energy "
         "release rate at both tips, graded against the published boundary-element solution with a tolerance from an independent J-integral study."),
        ("fcvm-buckling", "fcVM elastic buckling of steel members and welded assemblies (v1.3)", ["A-FCVM-buckling_U100_3D", "A-FCVM-Plate_girder_EC3"],
         "FreeCAD models from the fcVM workbench (Harry van Langen), with face supports, edge supports, distributed forces, pressures and self-weight as in the original "
         "constraints. Blue: supported faces; red: loaded faces. Output: first elastic buckling factor of the reference load set, graded against the factor in the "
         "published fcVM output, with a tolerance set by an independent eigenvalue convergence study (see the study page)."),
    ]
    for f, title, ids, text in pages:
        if not fam[f]:
            continue
        ids = [i for i in ids if i in T] or [x["task_id"] for x in fam[f][:2]]
        h(title, 2)
        imgs = []
        for tid in ids:
            if any(x["role"] == "cad" and x["path"].endswith((".step", ".stp", ".brep")) for x in T[tid]["inputs"]):
                imgs.append(cad_png(T[tid], tid))
        if f == "rigging-plate":
            imgs.append(C.CAND / "tasks/A-RIGGING-test1/boundary-conditions.png")
            doc = pymupdf.open(C.CAND / "tasks/B-RIGGING-test1/rigging-plate-drawing.pdf")
            png = IMG / "rigging-drawing.png"
            doc[0].get_pixmap(dpi=90).save(png)
            imgs.append(png)
        if f == "feenox-valve-transient":
            imgs.append(C.CAND / "tasks/A-VALVE-transient/valve-surfaces.png")
        if f == "femcad-hard":
            imgs += [render.render(C.ROOT / "output/geometry-references-v1.3" / f"{k}-reference.step", IMG / f"{k}-ref.png")
                     for k in [x["task_id"] for x in fam[f]][:3]]
        if f == "nafems-calibration":
            imgs += [C.CAND / next(i["path"] for i in T[k]["inputs"] if i["path"].endswith(".png")) for k in ("A-NAFEMS-LE1", "A-NAFEMS-LE11")]
        pics(imgs, mh=150)
        p(text)
        ts = fam[f]
        p(f"<b>Tasks:</b> {len(ts)}. <b>Licence:</b> {html.escape(ts[0]['source']['license'].rstrip('.'))}. <b>Source:</b> "
          f"<link href='{ts[0]['source']['url']}' color='blue'>{html.escape(ts[0]['source']['name'])}</link>.", small)
        ex, r = T[ids[0]], refs[ids[0]]
        rows = [["output", "unit", "reference", "tolerance", "class", "evidence / provenance"]]
        for o in ex["outputs"]:
            rr = r["references"][o["key"]]
            rows.append([o["key"], o["unit"], f"{rr['value']:.6g}", f"{rr['tol']['kind']} {rr['tol']['value']:g}", rr["ref_class"], rr["provenance"][:110]])
        p(f"Example {ids[0]} (hidden references; {len(r['evidence_files'])} evidence files):", small)
        table(rows[:10], [92, 30, 52, 50, 70, 206])
        p("<b>Example prompt (" + ids[0] + "), first lines:</b>", small)
        p(html.escape(ex["prompt"][:1150]).replace("\n", "<br/>") + " ...", mono)
        if r["flags"]:
            p("<b>Flags:</b> " + html.escape("; ".join(r["flags"])), small)
        story.append(PageBreak())

    h("Geometry gates for drawing/specification-to-CAD tasks (v1.3)", 2)
    gt = [k for k in geo_refs if k in T]
    pics([render.render(C.ROOT / "output/geometry-references-v1.3" / f"{k}-reference.step", IMG / f"{k}-ref.png") for k in gt[:4]], mh=120)
    pics([render.render(C.ROOT / "output/geometry-references-v1.3" / f"{k}-reference.step", IMG / f"{k}-ref.png") for k in gt[4:]], mh=120)
    gp = ver["geometry_gate_probes"]
    rows = [["task", "reference solid", "volume (mm^3)", "volume check", "rotated + moved", "scaled x1.03"]]
    for k in gt:
        g = geo_refs[k]
        rows.append([k, g["description"], f"{g['volume_mm3']:.6g}", f"{g['relative_volume_error']:.0e}", f"{gp[k]['rotated_moved']:.2g}",
                     f"{gp[k]['scaled_103']:.3f}" if gp[k]["scaled_103"] is not None else "rejected: " + gp[k].get("scaled_103_rejected_by", "")[:40]])
    rb = [k for k in gp if k not in geo_refs]
    for k in rb:
        rows.append([k, "original source CAD (rigging plate)", "", "", f"{gp[k]['rotated_moved']:.2g}",
                     f"{gp[k]['scaled_103']:.3f}" if gp[k]["scaled_103"] is not None else "rejected"])
    table(rows, [78, 190, 62, 60, 55, 55])
    p("Order of the renders: the table rows. Reference solids are built from the task text (FEMCAD-Hard pages, NAFEMS LE1/LE11 geometry definitions) or taken from the "
      "source CAD (LE10). Each is accepted only if its OpenCASCADE volume agrees with a closed form, or with Pappus's theorem for the revolved LE11 profile, to 1e-4. "
      "The scorer aligns the submitted part.step to the reference using bounding-box centres and the 24 proper axis rotations (mirror images are rejected), and "
      "passes it if the symmetric volume difference is at most 2 % of the reference volume. Probe columns: symmetric difference for the reference rotated 90 degrees and "
      "moved (must pass) and for it scaled by 3 % (must fail). The gate is a necessary check; features, regions and boundary-condition faces are covered by the trusted review.", small)
    story.append(PageBreak())

    h("fcVM elastic buckling: correspondence and independent eigenvalue study (v1.3)", 2)
    pics([fcvm_plot(fc)], mh=300)
    rows = [["model", "published lambda1", "meshes", "finest h (mm)", "finest independent", "difference", "last change", "decision"]]
    for r in fc:
        a = r["fcvm_assessment"]
        rows.append([r["task_id"].replace("A-FCVM-", ""), f"{a['published_lambda1']:g}", len(a["runs"]), f"{a['runs'][-1]['h_mm']:.3g}" if a["runs"] else "-",
                     f"{a['finest']:.5g}" if "finest" in a else "-", f"{100 * a['relative_difference']:+.1f} %" if "finest" in a else "-",
                     f"{100 * a['last_change']:.2f} %" if "finest" in a else "-",
                     f"admitted, tol {100 * r['references']['lambda1']['tol']['value']:.0f} %" if r.get("status") != "held" else "held"])
    table(rows, [92, 62, 38, 50, 66, 52, 50, 90])
    p("Correspondence: scripts/cadfem_bench/fcvm_extract.py reads each original FreeCAD document as data, without executing it. It maps every constraint's references onto the "
      "analysis solid and rebuilds the reference load the way fcVM's own code does: the force direction vector over the total face area, signed pressure along the outward normal, and self-weight from "
      "density times the control-file gravity. All 14 fcVM models reproduce the 'Sum of loads' printed in their published output; the largest difference is "
      "5.8e-4, from a value printed to 3 significant figures. Independent study: the analysis solid is remeshed with gmsh (solids fragmented into one conforming body) on "
      "quadratic tetrahedra, with element size reduced by 0.8 per step. Where finer meshes exceed the study machine's memory, the sequence is completed on the coarse side "
      "with the same ratio. A FEniCSx prebuckling solve is followed by the geometric stiffness K_G, and SLEPc solves (-K_G) x = mu K x for the largest mu "
      "(lambda = 1/mu, so load-reversal modes do not interfere). The bar case agrees with Euler's cantilever value to 0.05 %. Admission uses the cycloidal rule: last change "
      "< 1 %, previous < 2 %, band = |finest - published| / published + 2 x last change <= 10 %, tolerance = band (at least 5 %). Purple squares: a diagnostic solve "
      "on a coarser mesh near fcVM's element count, shown where the gap is large; it never changes a decision. Held: " + "; ".join(f"{r['task_id'].replace('A-FCVM-', '')}: {r['fcvm_assessment']['reason']}"
                                                         for r in fc if r.get("status") == "held") + ".", small)
    story.append(PageBreak())

    if "fcvm_plastic_tasks" in val:
        others = [json.loads(x) for x in (C.OUT / "held/references.jsonl").read_text().splitlines() if x.strip()]
        others += [json.loads(x) for x in (C.EVAL / "suites/calibration/references.jsonl").read_text().splitlines() if x.strip()]
        new_refs = [r for r in refs.values() if r["family"] in ("fcvm-plastic-limit", "interface-crack-fracture")]
        others = [r for r in others if r["family"] in ("fcvm-plastic-limit", "interface-crack-fracture")]
        h("v1.5 studies: plastic limit loads and interface-crack energy release rates", 2)
        pics([v15_plot(new_refs, others)], mh=300)
        rows = [["task", "output", "published", "finest independent", "difference", "last change", "decision"]]
        for r in sorted(new_refs + others, key=lambda r: r["task_id"]):
            if "plastic_assessment" in r:
                a = r["plastic_assessment"]
                rows.append([r["task_id"], "limit_load_factor", f"{a['published_limit_factor']:g}", f"{a['finest']:.4g}" if "finest" in a else "-",
                             f"{100 * a['relative_difference']:+.1f} %" if "finest" in a else "-", f"{100 * a['last_change']:.2f} %" if "finest" in a else "-",
                             "held" if r.get("status") == "held" else ("calibration" if r["tier"] == "control" else "primary") +
                             f", tol {100 * r['references']['limit_load_factor']['tol']['value']:.0f} %"])
            else:
                for tip in ("right", "left"):
                    x = r["crack_assessment"]["tips"][tip]
                    rows.append([r["task_id"], f"G_{tip}_tip", f"{x['published_G']:.4f}", f"{x['finest']:.4f}", f"{100 * x['relative_difference']:+.2f} %",
                                 f"{100 * x['last_change']:.2f} %", "held" if r.get("status") == "held" else f"primary, tol {100 * r['references']['G_' + tip + '_tip']['tol']['value']:.0f} %"])
        table(rows, [128, 74, 50, 64, 50, 48, 86])
        p("Plastic limit loads: published value = fcVM's maximum load factor, on a flat plateau of the published load-displacement curve. The load "
          "set is rebuilt from the FreeCAD constraints and matches the published load sum. Independent check: FEniCSx, quadratic tetrahedra, "
          "elastic-perfectly plastic von Mises with radial return and the consistent tangent, proportional loading with bisection; the limit is "
          "bracketed to 0.2 %. The solver reproduces the tensile bar's closed-form 0.5. Interface crack: published G from the source "
          "(boundary-element solution, stated uncertainty below 0.1 %). Independent check: FEniCSx plane stress, quadratic triangles graded to the "
          "tips, equivalent-domain J-integral on three rings, five mesh levels; it reproduces a Griffith crack within 0.1 %. Admission rule as for "
          "the other studied families: last change < 1 %, previous < 2 %, band <= 10 %, tolerance = band (at least 5 %).", small)
        story.append(PageBreak())

    h("Cycloidal convergence study (v1.2)", 2)
    pics([convergence_plot(tasks, refs)], mh=330)
    rows = [["part", "published (mm)", "finest independent (mm)", "difference", "meshes", "tolerance"]]
    for t in tasks:
        if t["family"] == "cycloidal-drive-components":
            rr = refs[t["task_id"]]["references"]["max_displacement_mm"]
            st = json.loads((C.EVAL / "evidence/cycloidal-convergence-study" / t["task_id"] / "study.json").read_text())
            rows.append([t["task_id"].replace("A-CYC-", ""), f"{rr['value']:.6g}", f"{rr['independent_finest_mm']:.6g}",
                         f"{100 * (rr['independent_finest_mm'] / rr['value'] - 1):+.1f} %", len(st["mesh_runs"]), f"{100 * rr['tol']['value']:.0f} %"])
    table(rows, [120, 80, 100, 70, 50, 70])
    p("Independent solves: supplied STEP remeshed with gmsh, second-order geometry, quadratic displacement, FEniCSx/PETSc MUMPS, loads as constant traction "
      "normalised to the meshed area. Admitted parts: refinement settled (last change < 1 %, previous < 2 %), force-balance residual < 1e-6 "
      "(the study script's 1e-8 cut-off is relaxed because 1e-8 to 1e-7 residuals are exact at these tolerances), band <= 10 %. "
      "Tolerance = |finest - published| / published + 2 x last change, rounded up to 1 %, at least 5 %. "
      "Held: Housing and Lid (finer meshes exceed the study's 220k-element solver guard), Ring1x15 (residual 4.7e-4, values do not settle), "
      "ShaftP2-radial (still changing 1.8 % per refinement, 7.9 % from the published value). "
      "The study files are in the evaluator evidence bundle; they never replace the published targets.", small)
    story.append(PageBreak())

    h("Held tasks and source registry", 2)
    hc = Counter(t["hold_reason"] for t in held)
    table([["held tasks", "reason"]] + [[n, k] for k, n in hc.most_common()], [60, 440])
    st_ = Counter(r["status"] for r in reg)
    p(f"Source registry: {len(reg)} collected collections (" + ", ".join(f"{v} {k}" for k, v in st_.most_common()) + "). Largest held pools that could "
      "become tasks with further work: Code_Aster validation cases (50 cases, 761 published checks), SFEM (61), GeoPINONet lugs (80), Bath auxetics (18).")
    rows = [["collection", "status", "tasks / candidates", "blocker / decision"]]
    for r in sorted(reg, key=lambda r: (r["status"] != "pilot", r["status"])):
        rows.append([r["title"], r["status"], r.get("tasks", r.get("candidates", "")), r.get("blocker", "") + (" - " if r.get("blocker") else "") + r["reason"]])
    table(rows, [150, 50, 50, 250])
    p("Files: candidate/ (give to the model), evaluator/ (keep hidden: references, registry, scorer, review protocol, evidence bundle), held/ (held tasks with "
      "their inputs and the excluded local targets), report/, scripts/. Licences differ per source and several sources are local-research-only: do not publish the "
      "package as a whole. No model results yet.", small)

    def footer(c, d):
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.grey)
        c.drawString(40, 22, f"CADFEM-Bench v{C.VERSION} | {C.DATE}")
        c.drawRightString(A4[0] - 40, 22, str(d.page))

    PDF.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(PDF), pagesize=A4, leftMargin=40, rightMargin=40, topMargin=34, bottomMargin=36).build(story, onFirstPage=footer, onLaterPages=footer)
    doc = pymupdf.open(PDF)
    for i, page in enumerate(doc):
        page.get_pixmap(dpi=70).save(IMG / f"page-{i + 1}.png")
    print(PDF, len(doc), "pages", PDF.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
