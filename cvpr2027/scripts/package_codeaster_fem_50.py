"""Package 50 acquired source cases and a drawing/reference review PDF.

This is a source release, never an automatic promotion to benchmark admission.
"""
from __future__ import annotations

import hashlib
import io
import json
import shutil
import zipfile
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

import ast
import fitz
import h5py
import resvg_py
from PIL import Image as PILImage, ImageDraw
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak

from crawl_codeaster_fem_50 import ROOT, CACHE, OUT, published_checks, sha


SELECTION = {
    "vibration and rotor dynamics": {
        "SDLL14": "Vibration modes of a thin pipe elbow",
        "SDLL149": "Seismic response of the NRC BM3 piping system",
        "SDLS102": "Natural frequencies of a compressor blade",
        "SDLS120": "Vibration modes of a cracked plate with X-FEM",
        "SDLV123": "Elastodynamic energy release rate of a finite crack",
        "SDLV129": "Vibration fatigue of a fan blade",
        "SDNL142": "Dynamic response of a submerged cable in a wave field",
        "SHLL103": "Gyroscopic harmonic response of a two-disc rotor",
        "SDNV110": "Gyroscopic modes of a rotating solid rotor",
    },
    "fluid-structure coupling": {
        "SDLS103": "Inertial coupling of coaxial shells in annular flow",
        "FDLL200": "Vibration of a fluid-filled cantilever pipe",
    },
    "buckling and stability": {
        "SDLS504": "Lateral torsional buckling of a beam",
        "SDLS505": "Cylindrical shell buckling under external pressure",
        "SSLL103": "Elastic buckling of an angle-section member",
        "SSLL105": "Elastic buckling of an L-shaped structure",
        "SSLL404": "Buckling of a curved arch",
        "SSLV139": "Buckling of a circular plate under edge compression",
        "SSNL126": "Elastoplastic buckling of a straight beam",
    },
    "shells and composites": {
        "SSLS20": "Pinched cylindrical shell with free edges",
        "SSLS104": "Pinched cylindrical shell with a diaphragm",
        "SSLS108": "Helicoidal shell under concentrated loads",
        "SSLS112": "Eccentric composite plates",
        "SSLS115": "Composite square plate under uniform pressure",
        "SSLS504": "Three-layer composite plate under sinusoidal loading",
        "SSLX102": "Bending of an elbow pipe with shell and beam models",
    },
    "fracture and crack propagation": {
        "SSLP103": "Mixed-mode stress intensity in a cracked circular plate",
        "SSLP311": "Oblique crack in a finite bimaterial plate",
        "SSLP314": "Deflected crack at an interface between elastic half-planes",
        "SSLP322": "Crack propagation in a three-hole bending specimen",
        "SSLV311": "Quarter-elliptical corner crack in a rotating thick disc",
        "SSLV312": "Semi-elliptical crack perpendicular to a bimaterial interface",
        "SSNP311": "Mode II fracture of an elastoplastic specimen",
        "SSNP312": "Interface-parallel crack in a bimetallic CT specimen",
        "SSNP110": "Edge crack in an elastoplastic finite plate",
    },
    "contact and friction": {
        "SSNA102": "Contact between multiple elastic bodies",
        "SSNA105": "Viscoelastic pressurised cylinder with contact",
        "SSNA122": "NAFEMS rounded punch contact benchmark",
        "SSNP153": "Shallow ironing with friction and large deformation",
        "SSNP154": "NAFEMS cylinder-roller contact benchmark",
        "SSNV104": "Hertzian contact between two spheres",
        "SSNV128": "Frictional contact of a plate with a rigid plane",
        "SSNV153": "Pulley-rope contact",
    },
    "plasticity and forming": {
        "SSNL106": "Elastoplastic beam in tension and pure bending",
        "SSNA303": "Large-strain notched elastoplastic specimen",
        "SSNL503": "Elastoplastic collapse of a thin elbow pipe",
        "SSNV501": "Sheet forming with a hemispherical punch",
        "SSNV506": "Elastoplastic block indented by an elastic sphere",
    },
    "thermomechanics": {
        "HPLA310": "Thermal shock of a radially cracked circular bar",
        "HPLP310": "Cracked thick cylinder under pressure and thermal loading",
        "HSNV132": "Thermoelastic cracked body with X-FEM",
    },
}


def physical_checks(record):
    # Geometry coordinates and adaptive error estimators alone are not FEM output targets.
    out = []
    for check in record["published_fem_checks"]:
        sel = check["selectors"]
        field = sel.get("NOM_CHAM", "")
        parameter = sel.get("NOM_PARA", sel.get("PARA", ""))
        if isinstance(parameter, str) and parameter.startswith("COOR_"):
            continue
        if isinstance(field, str) and field.startswith(("ERME", "ERRE")):
            continue
        out.append(check)
    return out


def make_records():
    dest = ROOT / "cvpr2027/tmp/published-fem-expansion-50"
    records = []
    checked_assets = {}
    mesh_reports = []
    for family, cases in SELECTION.items():
        for case, title in cases.items():
            original = json.loads((CACHE / "codeaster" / case / "record.json").read_text())
            r = json.loads(json.dumps(original))
            r.pop("published_document_tables", None)
            assert r["geometry_illustrations"] and not r["missing_export_dependencies"], case
            checks = physical_checks(r)
            assert checks, case
            cmd_path = ROOT / r["original_solver_input"]["path"]
            assert published_checks(cmd_path.read_text()) == r["published_fem_checks"]
            r.update(english_title=title, physics_family=family,
                     published_fem_checks=checks,
                     source_assertions_are_not_model_accuracy_scores=True,
                     source_precision_not_benchmark_acceptance_tolerance=True,
                     units_status="case-by-case review pending; values remain in original source units",
                     candidate_tracks={"cad_fem": "drawing completeness and answer separation pending",
                                       "analysis_fem": "portable geometry/CAD correspondence pending"})
            for key in ("original_solver_input", "original_export", "original_dependencies",
                        "original_geometry_definitions", "geometry_illustrations"):
                assets = r[key] if isinstance(r[key], list) else [r[key]]
                for asset in assets:
                    path = ROOT / asset["path"]
                    assert sha(path) == asset["sha256"], path
                    new = dest / case / path.parent.name / path.name
                    new.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, new)
                    asset["path"] = str(new.relative_to(ROOT))
                    checked_assets[asset["path"]] = asset
                    if asset.get("export_type") == "mmed":
                        assert h5py.is_hdf5(new), new
                        with h5py.File(new) as h:
                            assert "ENS_MAA" in h, new
                            mesh_reports.append({"case_id": r["case_id"],
                                                 "path": asset["path"],
                                                 "med_mesh_groups": list(h["ENS_MAA"]),
                                                 "valid_hdf5_med_container": True})
            # The original docs stay in the download cache; the ZIP links to them.
            for doc in r["documentation"]:
                doc["cached_path_not_in_archive"] = doc.pop("path")
            r["native_cad_files"] = [x for x in r["original_geometry_definitions"]
                                     if Path(x["path"]).suffix in {".step", ".stp"}]
            record_path = OUT / "records" / (case + ".json")
            record_path.parent.mkdir(parents=True, exist_ok=True)
            record_path.write_text(json.dumps(r, indent=2, ensure_ascii=False))
            records.append(r)
    assert len(records) == len({r["source_problem_id"] for r in records}) == 50
    validation = {"distinct_physical_problems": 50, "not_counting_track_or_mesh_variants": True,
                  "source_asset_hashes_verified": len(checked_assets),
                  "published_literal_fem_check_blocks": sum(len(r["published_fem_checks"]) for r in records),
                  "geometry_illustrations": sum(len(r["geometry_illustrations"]) for r in records),
                  "cases_with_original_geometry_scripts": sum(bool(r["original_geometry_definitions"]) for r in records),
                  "cases_with_native_step_cad": sum(bool(r["native_cad_files"]) for r in records),
                  "export_declared_dependencies_downloaded": True,
                  "source_code_executed": False, "fem_references_generated_locally": False,
                  "mesh_containers": mesh_reports, "assets": list(checked_assets.values()),
                  "new_cases_admitted_to_executable_pilot": 0,
                  "pilot_total_admitted_physical_cases": 3,
                  "certified_scored_cases": 0}
    (OUT / "validation.json").write_text(json.dumps(validation, indent=2, ensure_ascii=False))
    catalog = {"schema_version": 1, "release_kind": "published_source_expansion_for_benchmark_review",
               "case_count": 50, "minimum_requested_case_count": 50,
               "no_generated_engineering_problems": True, "solver": "Code_Aster",
               "requires_comsol": False,
               "status": "source_pairs_verified; benchmark admission pending",
               "families": dict(Counter(r["physics_family"] for r in records)),
               "cases": [{"case_id": r["case_id"], "title": r["english_title"],
                          "physics_family": r["physics_family"], "source_url": r["source_url"],
                          "record": str((OUT / "records" / (r["source_problem_id"] + ".json")).relative_to(ROOT)),
                          "fem_check_count": len(r["published_fem_checks"]),
                          "geometry_script_available": bool(r["original_geometry_definitions"]),
                          "native_step_available": bool(r["native_cad_files"]),
                          "admitted_to_executable_pilot": False} for r in records]}
    (OUT / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False))
    shutil.copyfile(CACHE / "LICENSE", OUT / "LICENSE-Code_Aster")
    return records, validation


def render_figure(asset, out):
    original = ROOT / asset["path"]
    if original.suffix == ".svg":
        data = resvg_py.svg_to_bytes(svg_path=str(original), dpi=96, width=1500, background="white")
        image = PILImage.open(io.BytesIO(data))
    else:
        image = PILImage.open(original)
    if image.mode == "RGBA":
        bg = PILImage.new("RGBA", image.size, "white")
        bg.alpha_composite(image)
        image = bg.convert("RGB")
    else:
        image = image.convert("RGB")
    image.save(out)
    return out, image.size


def pdf(records, validation):
    qa = CACHE / "pdf-qa"
    qa.mkdir(exist_ok=True)
    pdfmetrics.registerFont(TTFont("SourceArial", "/System/Library/Fonts/Supplemental/Arial.ttf"))
    pdfmetrics.registerFont(TTFont("SourceArialBold", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"))
    styles = getSampleStyleSheet()
    for name in styles.byName:
        styles[name].fontName = "SourceArial"
    styles["Title"].fontName = styles["Heading1"].fontName = "SourceArialBold"
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 14
    styles.add(ParagraphStyle("SmallSource", fontName="SourceArial", fontSize=8, leading=11))
    styles.add(ParagraphStyle("SmallHeader", fontName="SourceArialBold", fontSize=9, leading=12))
    def p(text, style="BodyText"):
        return Paragraph(text, styles[style])
    story = [p("50 published mechanical FEM problems", "Title"), Spacer(1, 16),
             p("Original source drawings, geometry illustrations and numerical FEM baselines", "Heading2"),
             p("This release contains 50 distinct physical problems from EDF's official Code_Aster validation library. "
               "Each has a publisher geometry illustration, an original solver command file, its declared input files, "
               "and numerical FEM baseline assertions. No engineering problem, CAD geometry or FEM reference was generated here."),
             Spacer(1, 12),
             p("Source release - benchmark admission pending", "Heading2"),
             p("The illustrations include technical geometry sketches and some model views. They are not all native CAD "
               "or manufacturing drawings. No STEP files were found in this release. Original GIBI geometry definitions "
               "are included where the publisher provides them; MED files are FE meshes. These distinctions are recorded per case."),
             Spacer(1, 10),
             p("The numerical values shown are published VALE_CALC FEM baselines, not model benchmark scores. "
               "They remain in original source units until unit and output-selector review. Source comparison tolerances "
               "are not adopted as model acceptance tolerances. The executable pilot still admits 3 cases; this release adds "
               "50 source pairs for review and does not claim 50 certified scored cases."),
             Spacer(1, 12)]
    family_rows = [["Physics family", "Problems"]] + [[k, str(v)] for k, v in Counter(r["physics_family"] for r in records).items()]
    tab = Table(family_rows, colWidths=[370, 105])
    tab.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#14344c")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONTNAME", (0, 0), (-1, -1), "SourceArial"),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 8)]))
    story += [tab, Spacer(1, 14), p("Evaluator material: the source decks and this PDF contain answers. "
             "Do not expose them to candidate models. The two benchmark tracks require separate answer-free input preparation.", "SmallSource"), PageBreak()]
    for i, r in enumerate(records, 1):
        story += [p(f"{i:02d} / 50 &nbsp; {r['case_id']}", "SmallHeader"),
                  p(escape(r["english_title"]), "Heading1"),
                  p(escape(r["physics_family"]), "SmallSource"), Spacer(1, 10)]
        image, size = render_figure(r["geometry_illustrations"][0], qa / (r["source_problem_id"] + ".png"))
        scale = min(475 / size[0], 330 / size[1])
        story += [Image(str(image), width=size[0] * scale, height=size[1] * scale), Spacer(1, 10),
                  p("Publisher geometry illustration; dimensions and physical setup are documented at the source link.", "SmallSource"),
                  Spacer(1, 8), p("Published FEM results", "Heading2")]
        rows = [[p("Source output selector", "SmallHeader"), p("FEM baseline", "SmallHeader"), p("Source line", "SmallHeader")]]
        shown = []
        for check in r["published_fem_checks"]:
            sel = check["selectors"]
            pieces = [f"{k}={v}" for k, v in sel.items() if k in
                      {"NOM_CHAM", "NOM_CMP", "GROUP_NO", "GROUP_MA", "NOM_PARA", "PARA", "INST", "NUME_ORDRE"}]
            text = "; ".join(pieces) or "Original TEST_RESU / TEST_TABLE selector"
            value = check["published_fem_value"]
            if isinstance(value, (list, tuple)):
                continue
            signature = (text, value)
            if signature in shown:
                continue
            shown.append(signature)
            rows.append([p(escape(text), "SmallSource"), p(f"{value:.10g}", "SmallSource"), p(str(check["line"]), "SmallSource")])
            if len(shown) == 3:
                break
        table = Table(rows, colWidths=[310, 110, 55])
        table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                  ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3edf4")),
                                  ("LINEBELOW", (0, 0), (-1, -1), .4, colors.HexColor("#d0dce5")),
                                  ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        story += [table, Spacer(1, 10), p("Values are in original source units. Full selectors and additional baselines are in the case JSON; "
                  "the original command file defines the physical inputs and result extraction.", "SmallSource"),
                  Spacer(1, 6), p(f"Original input: {Path(r['original_solver_input']['path']).name}. "
                  f"Geometry definition: {'original GIBI script supplied' if r['original_geometry_definitions'] else 'publisher diagram and original FE mesh; no separate CAD definition verified'}.", "SmallSource"),
                  Spacer(1, 6), p(f'<link href="{escape(r["source_url"])}" color="#215f86">Publisher documentation: {r["source_problem_id"]}</link>', "SmallSource"),
                  p("Source: EDF R&amp;D, Code_Aster. Original geometry illustration reproduced with attribution. "
                    "Solver assets retain their GPL notices. Admission and independent convergence review pending.", "SmallSource")]
        if i != len(records):
            story.append(PageBreak())
    out = ROOT / "cvpr2027/output/pdf/published-mechanical-fem-50-source-review.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    def footer(c, doc):
        c.setFont("SourceArial", 8)
        c.setFillColor(colors.HexColor("#567083"))
        c.drawString(48, 27, "Published source collection / evaluator review / admission pending")
        c.drawRightString(A4[0] - 48, 27, str(doc.page))
    SimpleDocTemplate(str(out), pagesize=A4, leftMargin=48, rightMargin=48, topMargin=40,
                      bottomMargin=48, title="50 published mechanical FEM problems").build(story, onFirstPage=footer, onLaterPages=footer)
    d = fitz.open(out)
    assert len(d) == 51, len(d)
    for n, page in enumerate(d):
        page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2)).save(qa / f"page-{n + 1:02d}.png")
        if n:
            assert f"{n:02d} / 50" in page.get_text(), n
    for start in range(0, len(d), 9):
        canvas = PILImage.new("RGB", (900, 1260), "#e5edf3")
        draw = ImageDraw.Draw(canvas)
        for offset, page in enumerate(d[start:start + 9]):
            image = PILImage.open(qa / f"page-{start + offset + 1:02d}.png")
            image.thumbnail((290, 400))
            x, y = (offset % 3) * 300, (offset // 3) * 420
            canvas.paste(image, (x + 5, y + 15))
            draw.text((x + 8, y), str(start + offset + 1), fill="black")
        canvas.save(qa / f"contact-{start // 9 + 1:02d}.jpg")
    return out


def package(records, report):
    out = ROOT / "cvpr2027/output/datasets/published-mechanical-fem-50-sources.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    files = set(OUT.rglob("*"))
    files.add(report)
    files.add(Path(__file__))
    files.add(Path(__file__).with_name("crawl_codeaster_fem_50.py"))
    for r in records:
        for key in ("original_solver_input", "original_export", "original_dependencies",
                    "original_geometry_definitions", "geometry_illustrations"):
            for asset in r[key] if isinstance(r[key], list) else [r[key]]:
                files.add(ROOT / asset["path"])
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(files):
            if path.is_file():
                z.write(path, str(path.relative_to(ROOT)))
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        names = z.namelist()
        assert len(names) == len(set(names))
        for r in records:
            for key in ("original_solver_input", "original_export", "original_dependencies",
                        "original_geometry_definitions", "geometry_illustrations"):
                for a in r[key] if isinstance(r[key], list) else [r[key]]:
                    assert hashlib.sha256(z.read(a["path"])).hexdigest() == a["sha256"]
    print(json.dumps({"zip": str(out), "bytes": out.stat().st_size,
                      "pdf": str(report), "cases": 50, "crc_and_all_asset_hashes_passed": True}))


if __name__ == "__main__":
    rs, validation = make_records()
    report = pdf(rs, validation)
    package(rs, report)
