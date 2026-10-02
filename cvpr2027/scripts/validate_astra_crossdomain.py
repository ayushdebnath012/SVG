"""Re-audit saved structural and mechanical Astra drawings without API calls.

The selected structural result is an honest analysis refusal on a correctly
edited frame. It is separate from ReSolve's circuit/pipe benchmark.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src")]
import cad_astra_benchmark as bench  # noqa: E402
import cad_functional_sizing as sizing  # noqa: E402
import pymupdf as fitz  # noqa: E402

STAMP = "20261001"
FRAME_ID = "threebay_three_edit"
FRAME_RUNS = (
    ("eng-frame-xl-20260922", "sample-0"),
    ("eng-frame-xl-confirm-20260922", "sample-0"),
    ("eng-frame-xl-confirm-20260922", "sample-1"),
    ("eng-frame-xl-confirm-20260922", "sample-2"),
)
CAD_RUNS = (
    ("screen", "cad-hard-geometry"),
    ("torus-screen", "cad-torus-sections"),
    ("precision-screen", "cad-precision-sections"),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame_audit() -> dict:
    manifest = ROOT / "data/eng-frame-bench-xl/tasks.json"
    task = next(t for t in json.loads(manifest.read_text())["tasks"] if t["id"] == FRAME_ID)
    assert len(task["model"]["members"]) == 21
    assert task["indeterminacy"] == 27
    assert task["source_model"]["nodes"]["N1_0"][0] == 3300
    assert task["model"]["nodes"]["N1_0"][0] == 4000
    assert task["source_model"]["loads"]["N3_3"][1] == -53000
    assert task["model"]["loads"]["N3_3"][1] == -68000
    coarse = bench.solve(task["model"])
    fine = bench.solve(task["model"], subdivisions=4)
    keys = ("ux_mm", "uy_mm", "peak_stress_mpa")
    for key in keys:
        assert abs(coarse[key] - task["reference"][key]) < 1e-7
        assert abs(coarse[key] - fine[key]) / max(abs(coarse[key]), 1e-8) < 1e-7

    rows = []
    for run, sample in FRAME_RUNS:
        folder = ROOT / "runs" / run / FRAME_ID / sample
        result = json.loads((folder / "result.json").read_text())
        assert result["status"] == "completed" and result["finish_reason"] == "stop"
        response = (folder / "response.txt").read_text()
        parsed = bench.read_response(response)
        score = bench.score(task, response)
        assert parsed["svg"] == (folder / "output.svg").read_text()
        assert not score["geometry_errors"] and not score["dimension_errors"]
        assert not score["analysis_errors"] and not score["visible_result_errors"]
        drawn = score["drawn_geometry_fem"]
        for key in keys:
            assert abs(drawn[key] - coarse[key]) < 1e-6
        assert "4000 mm" in parsed["svg"] and "68000 N" in parsed["svg"]
        analysis = parsed["analysis"]
        declined = analysis.get("status") == "unavailable"
        if declined:
            assert all(analysis.get(key) is None for key in keys)
            assert all("unavailable numeric analysis" in e for e in score["format_errors"])
        else:
            assert score["outcome"] == "pass"
        rows.append({
            "run": run,
            "sample": sample,
            "status": analysis.get("status"),
            "declined": declined,
            "geometry_and_dimensions_pass": True,
            "astra_analysis": {key: analysis.get(key) for key in keys},
            "solved_returned_svg": {key: drawn[key] for key in keys},
            "response_sha256": sha(folder / "response.txt"),
            "svg_sha256": sha(folder / "output.svg"),
        })
    assert sum(row["declined"] for row in rows) == 3
    assert len(rows) == 4
    return {
        "task": FRAME_ID,
        "manifest_sha256": sha(manifest),
        "edit": "Move second column grid from x=3300 to 4000 mm; increase N3_3 downward load from 53000 to 68000 N.",
        "members": 21,
        "joints": len(task["model"]["nodes"]),
        "degree_of_static_indeterminacy": 27,
        "reference": {key: coarse[key] for key in keys},
        "subdivision_relative_error": {
            key: abs(coarse[key] - fine[key]) / max(abs(coarse[key]), 1e-8) for key in keys
        },
        "completed_attempts": 4,
        "declined": 3,
        "calculated_correctly": 1,
        "rows": rows,
    }


def mechanical_audit() -> dict:
    rows = []
    for run, data in CAD_RUNS:
        manifest = json.loads((ROOT / "data" / data / "tasks.json").read_text())
        tasks = {task["id"]: task for task in manifest["tasks"]}
        base = ROOT / "runs/astra-cad-hard-20260920" / run
        protocol = json.loads((base / "protocol.json").read_text())
        assert bench.digest(manifest) == protocol["manifest_sha256"]
        for task_id in protocol["task_ids"]:
            folder = base / task_id / "sample-0"
            result = json.loads((folder / "result.json").read_text())
            assert result["status"] == "completed" and result["finish_reason"] == "stop"
            score = bench.score(tasks[task_id], (folder / "response.txt").read_text())
            assert score["outcome"] == "pass", (task_id, score)
            rows.append({
                "run": run,
                "task": task_id,
                "outcome": score["outcome"],
                "response_sha256": sha(folder / "response.txt"),
            })
    assert len(rows) == 10
    return {"completed": len(rows), "passes": len(rows), "confirmed_shape_failures": 0, "rows": rows}


def functional_audit() -> dict:
    tasks = {}
    for name in ("cad-functional-sizing", "cad-functional-braced", "cad-functional-three-bay"):
        manifest = json.loads((ROOT / "data" / name / "tasks.json").read_text())
        tasks.update({task["id"]: task for task in manifest["tasks"]})
    rows = []
    base = ROOT / "runs/astra-functional-sizing-20260921"
    for path in sorted(base.glob("*/*/result.json")):
        saved = json.loads(path.read_text())
        assert saved["status"] == "completed"
        task = tasks[saved["id"]]
        design = sizing.read_drawing(task, (path.parent / "output.svg").read_text())
        grade = sizing.rows(task, [design])[0]
        assert grade["all_constraints_pass"]
        assert design == saved["grade"]["design"]
        model = copy.deepcopy(task["model"])
        for member, index in zip(model["members"], design):
            member["h_mm"] = task["catalog_h_mm"][index]
        checks = []
        for loads in task["load_cases"]:
            model["loads"] = loads
            for node in model["nodes"]:
                model["probe"] = node
                checks.append(sizing.fem.solve(model, subdivisions=2))
        for quantity, source in (
            ("ux_mm", "ux_mm"),
            ("uy_mm", "uy_mm"),
            ("stress_mpa", "peak_stress_mpa"),
        ):
            assert abs(grade[quantity] - max(abs(row[source]) for row in checks)) < 1e-6
        rows.append({
            "task": saved["id"],
            "pass": True,
            "svg_sha256": sha(path.parent / "output.svg"),
        })
    assert len(rows) == 6
    return {
        "completed": len(rows),
        "passes": len(rows),
        "scope": "Catalog section choice with deterministic SVG export and FEM; not free-form drawing.",
        "rows": rows,
    }


def make_figure(frame: dict) -> dict:
    source = ROOT / "runs/eng-frame-xl-confirm-20260922" / FRAME_ID / "sample-0/output.svg"
    figures = ROOT / "paper/network/figures"
    figures.mkdir(parents=True, exist_ok=True)
    raw = figures / "astra-frame-decline-raw.svg"
    raw.write_bytes(source.read_bytes())
    assert sha(raw) == sha(source)
    annotated = figures / "astra-frame-decline-annotated.svg"
    overlay = """
<g xmlns="http://www.w3.org/2000/svg" pointer-events="none">
  <rect x="300" y="145" width="29" height="473" rx="5" fill="none" stroke="#df7c20" stroke-width="4"/>
  <rect x="632" y="77" width="96" height="28" rx="4" fill="none" stroke="#df7c20" stroke-width="3"/>
  <rect x="747" y="356" width="328" height="255" rx="10" fill="none" stroke="#c52d37" stroke-width="3"/>
</g>
"""
    svg = raw.read_text().replace("</svg>", overlay + "</svg>")
    assert svg != raw.read_text()
    annotated.write_text(svg)
    pdf = figures / "astra-frame-decline-annotated.pdf"
    doc = fitz.open(stream=svg.encode(), filetype="svg")
    pdf.write_bytes(doc.convert_to_pdf())
    check = fitz.open(pdf)
    assert len(check) == 1
    preview = ROOT / "tmp/astra-frame-decline-annotated.png"
    preview.parent.mkdir(parents=True, exist_ok=True)
    check[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False).save(preview)
    return {
        "original_svg": str(source.relative_to(ROOT)),
        "paper_raw_svg": str(raw.relative_to(ROOT)),
        "paper_annotated_svg": str(annotated.relative_to(ROOT)),
        "paper_annotated_pdf": str(pdf.relative_to(ROOT)),
        "raw_svg_sha256": sha(raw),
        "presentation_overlay_only": True,
    }


def main() -> None:
    frame = frame_audit()
    mechanical = mechanical_audit()
    functional = functional_audit()
    figure = make_figure(frame)
    result = {
        "audit_date": "2026-10-01",
        "method": "Offline re-scoring of saved model responses; no new Astra call.",
        "structural_frame": frame,
        "mechanical_cad": mechanical,
        "functional_structural_sizing": functional,
        "figure": figure,
        "scope_note": (
            "The frame verifier is a separate idealised planar-frame FEM harness. "
            "ReSolve in the network paper has not been validated on frames or mechanical CAD. "
            "A refusal to calculate is distinct from a wrong numerical claim."
        ),
    }
    out = ROOT / f"reports/ASTRA_CROSSDOMAIN_VALIDATION_{STAMP}.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "audit": str(out.relative_to(ROOT)),
        "frame": f"{frame['declined']}/{frame['completed_attempts']} declined",
        "mechanical": f"{mechanical['passes']}/{mechanical['completed']} pass",
        "functional": f"{functional['passes']}/{functional['completed']} pass",
        "figure": figure["paper_annotated_svg"],
    }, indent=2))


if __name__ == "__main__":
    main()
