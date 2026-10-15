"""PDF report for CADFEM-Bench v1: composition, policies, one page per task family with CAD renders, and the full
source registry with blockers.  tmp/cq-env/bin/python scripts/cadfem_bench/report.py
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

PDF = C.ROOT / "output/pdf/cadfem-bench-v1.pdf"
IMG = C.ROOT / "tmp/cadfem-bench-v1-report"
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
        if line.startswith("Load:"):
            hl.update({f: RED for f in faces_in(line)})
    return render.render(C.CAND / cad["path"], IMG / f"{name}.png", hl or None, view=view)


def main() -> None:
    tasks = [json.loads(x) for x in (C.CAND / "tasks.jsonl").read_text().splitlines()]
    refs = {json.loads(x)["task_id"]: json.loads(x) for x in (C.EVAL / "references.jsonl").read_text().splitlines()}
    reg = [json.loads(x) for x in (C.EVAL / "registry.jsonl").read_text().splitlines()]
    val = json.loads((C.EVAL / "validation.json").read_text())
    T = {t["task_id"]: t for t in tasks}
    fam = defaultdict(list)
    for t in tasks:
        fam[t["family"]].append(t)

    h(f"CADFEM-Bench v{C.VERSION}: the final CAD + FEM engineering benchmark")
    p(f"{C.DATE}. This release assembles every CAD/FEM source collected in the project into one benchmark for frontier models. "
      f"<b>{val['tasks']} tasks</b> with <b>{val['graded_outputs']} graded numerical outputs</b> in {val['families']} task families come from "
      f"{val['sources_admitted']} admitted source collections; {val['sources_held']} more collections are held and {val['sources_excluded']} excluded, each with its blocker. "
      "Every reference is source-published (saved solver results, publisher tables, publisher evaluators, closed forms, NAFEMS targets) except the "
      "SimJEB peak-stress/verdict outputs, which use the validated SimJEB grader and are labelled <i>verifier</i>. No solver run or model call was made for this release.")
    p("<b>Tracks.</b> " + " ".join(f"<b>{k}</b>: {v}" for k, v in C.TRACKS.items()))
    p("<b>Tiers.</b> <b>gold</b>: open CAD or complete specification, fully stated set-up, numerical published or validated reference. "
      "<b>silver</b>: reference read from a result legend, part of the set-up from the source's boundary-condition figure. "
      "<b>control</b>: public NAFEMS benchmarks, used to calibrate the harness.")
    rows = [["family", "track", "tier", "tasks", "graded outputs", "physics", "reference class"]]
    for f, ts in sorted(fam.items(), key=lambda kv: (sorted({t["track"] for t in kv[1]})[0], kv[0])):
        rc = sorted({r["ref_class"] for t in ts for r in refs[t["task_id"]]["references"].values()}) or ["SimJEB grader"]
        n = sum(len([1 for r in refs[t["task_id"]]["references"].values() if r.get("graded", True)]) for t in ts)
        rows.append([f, "/".join(sorted({t["track"] for t in ts})), "/".join(sorted({t["tier"] for t in ts})), len(ts), n,
                     ", ".join(sorted({x for t in ts for x in t["physics"]})), ", ".join(rc)])
    rows.append(["total", "", "", val["tasks"], val["graded_outputs"], "", ""])
    table(rows, [118, 32, 52, 32, 44, 120, 112])
    bt = val["by_track"]
    p("Tasks by track and tier: " + "; ".join(f"track {k}: " + ", ".join(f"{n} {tier}" for tier, n in v.items()) for k, v in bt.items()) + ".")
    p("<b>Tolerances.</b> Relative error. Gold defaults 5 % (displacement, frequency, temperature) and 10 % (stress); silver 10 %/20 %. "
      "Source tolerances override: CADWorld 5 %, SimJEB 10 % displacement / 15 % stress, FEMCAD-Hard 1 %. Legend peak stresses at load "
      "edges (rigging plate) get 20 %; transient temperatures are graded on the rise above the initial state. A task passes only if all its graded outputs pass; "
      "results are reported per track and tier and as a family macro-average.")
    p("<b>Error policy.</b> Tasks with a known error in their source data were fixed where the fix can be verified and left out otherwise. "
      "Fixed: AgentFEM STEP files (metre values under a millimetre header) ship scaled to true millimetres and checked against the FEM nodes; GeoPINONet "
      "boundary conditions are stated from the verified fields (the archive's fixed/load STL names are swapped). Left out: DeepWheel (CAD/CSV mass mismatch, "
      "unknown density), CADWorld 002 and 003, rigging-plate tests 4 and 5, cycloidal stress outputs (source error estimate 11-49 %) and 13 SimJEB "
      "redesign/lighten tasks without a passing human design that proves they can be solved.")
    p(f"<b>Checks at build time.</b> All {val['inputs_hash_checked']} input files hash-verified; no reference number appears in any prompt or text input "
      f"({len(val['leak_scan_hits'])} leak hits); image inputs were reviewed by eye (problem and boundary-condition figures only). Grader self-test: exact references pass "
      f"{val['grader_selftest']['oracle']['passed']}/{val['grader_selftest']['oracle']['numeric_tasks']} numeric tasks, references scaled by 1.3 pass "
      f"{val['grader_selftest']['perturbed']['passed']}. Set-up checks against the source data: cycloidal fixed node sets lie on the stated faces and the per-face loads "
      "sum to the deck resultants; GeoPINONet section forces equal -1000 N; the FeenoX valve's Gmsh surface tags equal the OpenCASCADE face indices.")
    story.append(PageBreak())

    pages = [
        ("simjeb-analysis", "GE jet-engine bracket: analysis of real competition designs (track A) and design, redesign, lighten (track C)",
         ["A-SIMJEB-analysis-0", "C-SIMJEB-redesign-16", "C-SIMJEB-lighten-0"],
         "Ti-6Al-4V bracket, four GE load cases at the clevis pin (RBE3), rigid fully fixed bolts. Analysis tasks ask for the per-case maximum displacement "
         "(graded against SimJEB's published OptiStruct magnitudes, 10 %), the peak von Mises stress outside 2 mm of the bolt/pin walls (verifier, 15 %) and the pass verdict. "
         "Track C: 15 design tasks (GE specification and material/load variants), 6 redesigns of failing designs (mass cap 1.25x) and 19 lightening tasks (-15 % mass), "
         "each with a passing human design that proves it can be solved; "
         "graded by scripts/simjeb_bench.py (geometry rules, FEM, mass) and placed against the 381 human designs."),
        ("agentfem-bracket", "AgentFEM double-arm support brackets (publisher test split)", [x["task_id"] for x in fam["agentfem-bracket"][:2]],
         "Aluminium bracket (E 70 GPa), foot undersides fixed, uniform downward seat traction of 1000 or 10000 N. Outputs: mean seat deflection and maximum displacement "
         "(publisher summary, 10 %; publisher mesh not converged). The source STEP declared mm but held metre values; the shipped copy is scaled to true mm and checked against the FEM nodes."),
        ("geopinonet-holed-plate", "GeoPINONet holed steel plates (validation split)", [x["task_id"] for x in fam["geopinonet-holed-plate"][:2]],
         "Structural steel, one end fixed, 1000 N on the opposite end face: compression (-y) and lateral (+x). Outputs: maximum displacement per case from the published ANSYS "
         "nodal CSVs (5 %). The archive's fixed/load STL names are swapped relative to the fields; supports and loads are therefore stated by geometry."),
        ("morphing-wing-plates", "Active-camber morphing-wing cantilever plates (modal)", ["A-MORPHWING-Test1", "A-MORPHWING-Test5"],
         "FDM-printed PLA plates, uniform and with a 1 mm flexible strip, clamped at the end of a 19 mm grip. Outputs: first bending, first torsion and second bending "
         "frequencies from the publisher workbook (Abaqus thick shell / Nastran plate models, 5 %)."),
        ("cycloidal-drive-components", "3D-printable cycloidal gearbox: component static analyses", ["A-CYC-Coupler-PETGCF", "A-CYC-Disk-PETGCF", "A-CYC-ShaftP2-radial-PETGCF"],
         "FreeCAD/CalculiX studies of 13 printed PETG-CF parts and 2 steel pins. Blue: fixed faces; red: loaded faces (uniform traction, resultant from the source-corrected deck). "
         "Output: maximum displacement (5 %) read from the saved FRD files. Stress is not graded: the source's own CalculiX error estimate at the stress peaks is 11-49 %."),
        ("cadworld-freecad-fem", "CADWorld FreeCAD FEM task", ["A-CADWORLD-001"],
         "Publisher geometry, material, constraints and mesh protocol (Gmsh, first-order tetrahedra); references are the values the publisher's evaluator checks (5 %). "
         "002 (edge support, auxiliary load object) and 003 (20 MN on a 30 mm specimen, 811 mm displacement) are left out."),
        ("feenox-valve-transient", "Power-plant valve: nonlinear transient heat conduction", ["A-VALVE-transient"],
         "Carbon-steel nozzle and stainless bodies, ASME temperature-dependent properties, internal temperature ramp 40-250-40 C over 1000 s, weak external convection. "
         "Outputs: through-wall temperature differences at two stress classification lines (heat-up and cool-down extrema, 10 %) and outer-wall temperatures at 100 s, "
         "from the published FeenoX history."),
        ("rigging-plate", "7075-T6 rigging plate: five ANSYS load tests and the drawing-to-CAD variant (silver)", ["A-RIGGING-test1"],
         "Supplied STEP (track A) or the dimensioned manufacturing drawing (track B) plus the source's boundary-condition figure per test. Output: maximum von Mises stress "
         "from the original legend (20 %). Track B also checks the built part's volume and extents against the source CAD (2 %). Tests 4 and 5 are left out (conflicting load labels; revised TEST-5R results)."),
    ]
    for f, title, ids, text in pages:
        h(title, 2)
        imgs = []
        for i, tid in enumerate(ids):
            if any(x["role"] == "cad" for x in T[tid]["inputs"]):
                imgs.append(cad_png(T[tid], tid, view=(55, -60) if "DEEPWHEEL" in tid else (24, -58)))
        if f == "rigging-plate":
            imgs.append(C.CAND / "tasks/A-RIGGING-test1/boundary-conditions.png")
            doc = pymupdf.open(C.CAND / "tasks/B-RIGGING-test1/rigging-plate-drawing.pdf")
            png = IMG / "rigging-drawing.png"
            doc[0].get_pixmap(dpi=90).save(png)
            imgs.append(png)
        if f == "feenox-valve-transient":
            imgs.append(C.CAND / "tasks/A-VALVE-transient/valve-surfaces.png")
        pics(imgs, mh=150)
        p(text)
        ts = [t for t in tasks if t["family"] == f or (f == "simjeb-analysis" and t["family"].startswith("simjeb"))]
        p(f"<b>Tasks:</b> {len(ts)}. <b>Licence:</b> {html.escape(ts[0]['source']['license'].rstrip('.'))}. <b>Source:</b> "
          f"<link href='{ts[0]['source']['url']}' color='blue'>{html.escape(ts[0]['source']['name'])}</link>.", small)
        ex = T[ids[0]]
        r = refs[ids[0]]
        rows = [["output", "unit", "reference", "tolerance", "class", "provenance"]]
        for o in ex["outputs"]:
            if o["key"] in r["references"]:
                rr = r["references"][o["key"]]
                v = rr["value"]
                rows.append([o["key"], o["unit"], v if isinstance(v, bool) else f"{v:.6g}", f"{rr['tol']['kind']} {rr['tol']['value']:g}", rr["ref_class"], rr["provenance"][:110]])
        if len(rows) > 1:
            p(f"Example {ids[0]} (hidden references):", small)
            table(rows[:10], [92, 30, 52, 50, 70, 206])
        p("<b>Example prompt (" + ids[0] + "), first lines:</b>", small)
        p(html.escape(ex["prompt"][:1150]).replace("\n", "<br/>") + " ...", mono)
        if r["flags"]:
            p("<b>Flags:</b> " + html.escape("; ".join(r["flags"])), small)
        story.append(PageBreak())

    h("Calibration and closed-form tasks", 2)
    nf = [T["A-NAFEMS-LE1"]["inputs"], T["A-NAFEMS-LE10"]["inputs"]]
    pics([C.CAND / next(i["path"] for i in x if i["path"].endswith(".png")) for x in nf], mh=150)
    p("NAFEMS LE1 (elliptic membrane), LE10 (thick elliptic plate) and LE11 (thermoelastic cylinder/taper/sphere), each as track A (supplied geometry) and track B "
      "(build CAD from the published figure). References are the FeenoX outputs, which equal the NAFEMS targets (5 %). Control tier: answers may be recalled.")
    rows = [["task", "title", "outputs (hidden reference, tolerance)"]]
    for t in fam["femcad-hard"]:
        rr = refs[t["task_id"]]["references"]
        rows.append([t["task_id"], t["title"], "; ".join(f"{k} = {v['value']:.6g} ({v['tol']['value']:g}, {v['ref_class']})" for k, v in rr.items())])
    p("FEMCAD-Hard (track B, gold): build the part from the written specification with CadQuery, analyse it with an open-source FEM code, report converged values. "
      "References are closed forms or values stated on the Wolfram FEM documentation pages, with the task's own 1 % tolerance.")
    table(rows, [70, 150, 280])
    story.append(PageBreak())

    h("Source registry: held and excluded collections", 2)
    cats = Counter(r["blocker"] for r in reg if r["status"] == "held")
    p(f"{val['sources_held']} held collections contain real CAD/FEM data with a specific blocker; {val['sources_excluded']} are excluded. Held blockers: "
      + "; ".join(f"{k} ({v})" for k, v in cats.most_common()) + ". Largest pools that could be admitted with further work: Code_Aster validation cases (50 cases, "
      "761 published checks), SFEM (61), GeoPINONet lugs (80), Bath auxetics (18). Tasks left out of admitted sources because of source errors are listed under each source's decision.")
    rows = [["collection", "status", "candidates", "blocker / decision"]]
    for r in reg:
        if r["status"] == "admitted":
            rows.append([r["title"], f"admitted ({r['tasks']} tasks)", "", r["reason"]])
    for r in reg:
        if r["status"] != "admitted":
            rows.append([r["title"], r["status"], r.get("candidates", ""), r["reason"]])
    table(rows, [150, 62, 42, 246])
    p("Files: candidate package (give to the model) cadfem-bench-v1-candidate.zip; evaluator package (keep hidden) cadfem-bench-v1-evaluator.zip with "
      "references.jsonl, registry.jsonl, score.py, validation.json and the dataset card; builder scripts in cvpr2027/scripts/cadfem_bench/. "
      "Licences differ per source and several sources are local-research-only: do not publish the candidate package as a whole. No model results yet.", small)

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
