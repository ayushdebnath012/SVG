"""Build a frozen multi-family detached-SVG recovery and edit benchmark."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import engsvg_ir as IR
import engsvg_plate as plate
import engsvg_truss as truss


VERSION = "engsvg-multifamily-v1"


def _truss_variants():
    rows = []
    for index in range(15):
        model = truss.example_model()
        model["materials"]["steel"]["E_mpa"] = [70000, 200000, 210000][index % 3]
        model["sections"]["bar"]["b_mm"] = 25 + 5 * (index % 5)
        model["sections"]["bar"]["h_mm"] = 15 + 5 * (index // 5)
        model["loads"]["C"][1] = -(10000 + 1000 * index)
        rows.append((f"truss-{index+1:02d}", IR.validate(model)))
    return rows


def _plate_variants():
    rows = []
    for index in range(15):
        model = plate.example_model()
        model["materials"]["steel"]["E_mpa"] = [70000, 200000, 210000][index % 3]
        model["plates"][0]["thickness_mm"] = 6 + 2 * (index % 5)
        diameter = 12 + 2 * (index % 5)
        offset = 25 + 5 * (index // 5)
        model["dimensions"][2]["value_mm"] = diameter
        model["dimensions"][3]["value_mm"] = offset
        centers = ((offset, offset), (300 - offset, offset),
                   (offset, 200 - offset), (300 - offset, 200 - offset))
        for hole, center in zip(model["holes"], centers):
            hole["center_mm"] = list(center); hole["diameter_mm"] = diameter
        rows.append((f"plate-{index+1:02d}", IR.validate(model)))
    return rows


def recovery_cases():
    cases = []
    for case_id, reference in _truss_variants():
        svg = truss.render(reference); recovered = truss.import_untagged(svg)
        cases.append({"id": case_id, "family": "truss2d", "svg": svg,
                      "reference": reference, "recovered": recovered,
                      "reference_hash": IR.engineering_digest(reference),
                      "recovered_hash": IR.engineering_digest(recovered),
                      "success": IR.engineering_digest(reference) == IR.engineering_digest(recovered),
                      "verification": truss.solve(recovered)})
    for case_id, reference in _plate_variants():
        svg = plate.render(reference); recovered = plate.import_untagged(svg)
        cases.append({"id": case_id, "family": "mechanical_part_2d", "svg": svg,
                      "reference": reference, "recovered": recovered,
                      "reference_hash": IR.engineering_digest(reference),
                      "recovered_hash": IR.engineering_digest(recovered),
                      "success": IR.engineering_digest(reference) == IR.engineering_digest(recovered),
                      "verification": plate.check_geometry(recovered)})
    return cases


def _edit_case(case_id, family, source_id, source, prompt, changes, target):
    return {"id": case_id, "family": family, "source_id": source_id,
            "source_hash": IR.engineering_digest(source), "request": prompt,
            "expected_action": {"action": "edit", "changes": changes},
            "target": IR.validate(target), "target_hash": IR.engineering_digest(target)}


def edit_cases():
    cases = []
    trusses = _truss_variants()
    for index in range(50):
        source_id, source = trusses[index % len(trusses)]; target = copy.deepcopy(source)
        kind = index % 5
        if kind == 0:
            old = abs(source["loads"]["C"][1]); new = round(old * 1.1)
            prompt = "Increase the downward load at C by 10 percent."
            changes = {"loads.C.fy_N": -new}; target["loads"]["C"][1] = -new
        elif kind == 1:
            new = [70000, 200000, 210000][(index // 5) % 3]
            prompt = f"Set the member material modulus to {new} MPa."
            changes = {"materials.steel.E_mpa": new}; target["materials"]["steel"]["E_mpa"] = new
        elif kind == 2:
            new = source["sections"]["bar"]["b_mm"] + 5
            prompt = "Increase every bar breadth by 5 mm."
            changes = {"sections.bar.b_mm": new}; target["sections"]["bar"]["b_mm"] = new
        elif kind == 3:
            new = source["sections"]["bar"]["h_mm"] + 5
            prompt = "Make the common bar depth 5 mm larger."
            changes = {"sections.bar.h_mm": new}; target["sections"]["bar"]["h_mm"] = new
        else:
            old = abs(source["loads"]["C"][1]); new = round(old * 0.75)
            prompt = "Reduce the downward load at C by one quarter."
            changes = {"loads.C.fy_N": -new}; target["loads"]["C"][1] = -new
        cases.append(_edit_case(f"truss-edit-{index+1:03d}", "truss2d", source_id,
                                source, prompt, changes, target))
    plates = _plate_variants()
    for index in range(50):
        source_id, source = plates[index % len(plates)]; target = copy.deepcopy(source)
        kind = index % 5
        if kind == 0:
            new = source["plates"][0]["thickness_mm"] + 2
            prompt = "Increase the plate thickness by 2 mm."
            changes = {"plates.P1.thickness_mm": new}; target["plates"][0]["thickness_mm"] = new
        elif kind == 1:
            new = source["holes"][0]["diameter_mm"] + 2
            prompt = "Increase all four through-hole diameters by 2 mm."
            changes = {"holes.*.diameter_mm": new}
            for hole in target["holes"]: hole["diameter_mm"] = new
            next(item for item in target["dimensions"] if item["id"] == "hole_diameter")["value_mm"] = new
        elif kind == 2:
            old = next(item for item in source["dimensions"] if item["id"] == "edge_offset")["value_mm"]
            new = old + 5; prompt = "Move every hole 5 mm farther from its two nearest edges."
            changes = {"dimensions.edge_offset.value_mm": new}
            next(item for item in target["dimensions"] if item["id"] == "edge_offset")["value_mm"] = new
            target["holes"][0]["center_mm"] = [new, new]
            target["holes"][1]["center_mm"] = [300-new, new]
            target["holes"][2]["center_mm"] = [new, 200-new]
            target["holes"][3]["center_mm"] = [300-new, 200-new]
        elif kind == 3:
            new = [70000, 200000, 210000][(index // 5) % 3]
            prompt = f"Change the stated material modulus to {new} MPa."
            changes = {"materials.steel.E_mpa": new}; target["materials"]["steel"]["E_mpa"] = new
        else:
            new = source["plates"][0]["thickness_mm"] * 2
            prompt = "Double the plate thickness while preserving the outline and holes."
            changes = {"plates.P1.thickness_mm": new}; target["plates"][0]["thickness_mm"] = new
        cases.append(_edit_case(f"plate-edit-{index+1:03d}", "mechanical_part_2d", source_id,
                                source, prompt, changes, target))
    return cases


def build(out: Path):
    if (out / "manifest.json").exists():
        raise ValueError("frozen benchmark already exists; choose a new output directory")
    out.mkdir(parents=True, exist_ok=True)
    recovery = recovery_cases(); edits = edit_cases()
    drawings = out / "drawings"; drawings.mkdir()
    recovery_rows = []
    for row in recovery:
        (drawings / f'{row["id"]}.svg').write_text(row.pop("svg"))
        (drawings / f'{row["id"]}.reference.json').write_text(json.dumps(row.pop("reference"), indent=2) + "\n")
        (drawings / f'{row["id"]}.recovered.json').write_text(json.dumps(row.pop("recovered"), indent=2) + "\n")
        recovery_rows.append(row)
    manifest = {"version": VERSION, "frozen": True, "training_overlap": "none",
                "scope": "30 generated detached SVG recovery cases across trusses and plates; 100 held-out edit requests",
                "recovery_cases": recovery_rows, "edit_cases": edits}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    summary = {"version": VERSION, "recovery_cases": len(recovery),
               "recovery_success": sum(row["success"] for row in recovery),
               "edit_cases": len(edits),
               "families": sorted({row["family"] for row in recovery}),
               "all_recovery_hashes_match": all(row["success"] for row in recovery)}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    files = [path for path in out.rglob("*") if path.is_file()]
    checksums = {str(path.relative_to(out)): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in sorted(files) if path.name != "sha256-manifest.json"}
    (out / "sha256-manifest.json").write_text(json.dumps(checksums, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(build(args.out), indent=2))
