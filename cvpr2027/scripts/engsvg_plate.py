"""Untagged mechanical plate SVG recovery and manufacturing geometry checks."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import engsvg_ir as IR
import engsvg_svg_geometry as SVG


def example_model() -> dict:
    model = {
        "version": IR.VERSION, "kind": "mechanical_part_2d",
        "units": {"length": "mm", "force": "N", "stress": "MPa"},
        "nodes": {}, "materials": {"steel": {"E_mpa": 200000}}, "sections": {},
        "members": [],
        "plates": [{"id": "P1", "width_mm": 300, "height_mm": 200,
                    "thickness_mm": 10, "material": "steel"}],
        "holes": [{"id": f"H{i+1}", "plate": "P1", "center_mm": list(center),
                   "diameter_mm": 20} for i, center in enumerate(((30, 30), (270, 30), (30, 170), (270, 170)))],
        "dimensions": [
            {"id": "width", "value_mm": 300}, {"id": "height", "value_mm": 200},
            {"id": "hole_diameter", "value_mm": 20}, {"id": "edge_offset", "value_mm": 30},
        ],
        "supports": {}, "loads": {},
        "assumptions": ["flat rectangular plate", "four circular through holes",
                        "geometry and manufacturing checks only"],
        "provenance": {"mode": "authored", "confidence": {}, "evidence": {}, "ambiguities": []},
    }
    return IR.validate(model)


def render(model: dict) -> str:
    model = IR.validate(model)
    plate = model["plates"][0]
    dimension_values = {item["id"]: item["value_mm"] for item in model["dimensions"]}
    diameters = {hole["diameter_mm"] for hole in model["holes"]}
    if len(diameters) != 1:
        raise ValueError("fixture renderer requires one common hole diameter")
    hole_diameter = next(iter(diameters))
    scale = 2.0; x0, y0 = 200.0, 180.0
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 760" width="1000" height="760">',
        '<rect width="1000" height="760" fill="white"/>',
        '<text x="35" y="40" font-size="23">Untagged four-hole mounting plate</text>',
        '<text x="35" y="67" font-size="13">Visible geometry and conventional dimensions; units mm</text>',
        '<g transform="translate(12 8)">',
        f'<rect x="{x0}" y="{y0}" width="{plate["width_mm"]*scale}" height="{plate["height_mm"]*scale}" fill="#eaf3f8" stroke="#1f3348" stroke-width="4"/>',
    ]
    for hole in model["holes"]:
        x, y = hole["center_mm"]
        parts.append(f'<circle cx="{x0+x*scale}" cy="{y0+(plate["height_mm"]-y)*scale}" r="{hole["diameter_mm"]*scale/2}" fill="white" stroke="#1f3348" stroke-width="3"/>')
    parts += [
        '</g>',
        '<line x1="212" y1="620" x2="812" y2="620" stroke="#6b7280" stroke-width="1"/>',
        '<line x1="212" y1="608" x2="212" y2="632" stroke="#6b7280" stroke-width="1"/>',
        '<line x1="812" y1="608" x2="812" y2="632" stroke="#6b7280" stroke-width="1"/>',
        f'<text x="480" y="610" font-size="14">{plate["width_mm"]:g} mm</text>',
        '<line x1="165" y1="188" x2="165" y2="588" stroke="#6b7280" stroke-width="1"/>',
        '<line x1="153" y1="188" x2="177" y2="188" stroke="#6b7280" stroke-width="1"/>',
        '<line x1="153" y1="588" x2="177" y2="588" stroke="#6b7280" stroke-width="1"/>',
        f'<text x="105" y="395" font-size="14">{plate["height_mm"]:g} mm</text>',
        f'<text x="35" y="675" font-size="14">{len(model["holes"])}x Ø{hole_diameter:g} mm THRU</text>',
        f'<text x="235" y="675" font-size="14">Edge offsets: {dimension_values["edge_offset"]:g} mm X and Y</text>',
        f'<text x="535" y="675" font-size="14">Thickness: {plate["thickness_mm"]} mm</text>',
        f'<text x="735" y="675" font-size="14">E: {model["materials"]["steel"]["E_mpa"]} MPa</text>',
        '</svg>',
    ]
    svg = "\n".join(parts); ET.fromstring(svg)
    if "data-" in svg:
        raise AssertionError("untagged plate contains semantic data attributes")
    return svg


def import_untagged(svg: str) -> dict:
    geometry = SVG.extract(svg)
    plates = [rect for rect in geometry["rectangles"] if str(rect["fill"]).lower() == "#eaf3f8"]
    holes = [circle for circle in geometry["circles"] if str(circle["fill"]).lower() == "white"
             and str(circle["stroke"]).lower() == "#1f3348"]
    if len(plates) != 1 or not holes:
        raise ValueError("expected one visible plate and at least one circular hole")
    corners = plates[0]["corners"]
    xs = [point[0] for point in corners]; ys = [point[1] for point in corners]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    # Current IR stores axis-aligned plate geometry; a rotated plate remains valid
    # only when its transformed corners form an axis-aligned rectangle.
    expected_corners = {(round(x0, 6), round(y0, 6)), (round(x1, 6), round(y0, 6)),
                        (round(x1, 6), round(y1, 6)), (round(x0, 6), round(y1, 6))}
    if {(round(x, 6), round(y, 6)) for x, y in corners} != expected_corners:
        raise ValueError("rotated plate recovery is outside importer v1")
    dimensions = SVG.associate_linear_dimensions(geometry)
    horizontal = [item for item in dimensions if item["orientation"] == "horizontal"]
    vertical = [item for item in dimensions if item["orientation"] == "vertical"]
    if not horizontal or not vertical:
        raise ValueError("missing associated width or height dimension")
    width = max(horizontal, key=lambda item: math.dist(item["line"]["a"], item["line"]["b"]))["value_mm"]
    height = max(vertical, key=lambda item: math.dist(item["line"]["a"], item["line"]["b"]))["value_mm"]
    sx, sy = width / (x1 - x0), height / (y1 - y0)
    if abs(sx - sy) / max(sx, sy) > 0.02:
        raise ValueError("plate dimensions imply inconsistent drawing scales")
    text = " | ".join(item["text"] for item in geometry["texts"])
    hole_match = re.search(r"(\d+)\s*x\s*[Ø⌀]\s*(\d+(?:\.\d+)?)\s*mm", text, re.I)
    thickness_match = re.search(r"Thickness\s*:\s*(\d+(?:\.\d+)?)\s*mm", text, re.I)
    modulus_match = re.search(r"\bE\s*:\s*(\d+(?:\.\d+)?)\s*MPa", text, re.I)
    edge_match = re.search(r"Edge\s+offsets\s*:\s*(\d+(?:\.\d+)?)\s*mm", text, re.I)
    if not hole_match or not thickness_match or not modulus_match or not edge_match:
        raise ValueError("missing visible hole, thickness or material annotation")
    expected_count, diameter = int(hole_match.group(1)), float(hole_match.group(2))
    if expected_count != len(holes):
        raise ValueError("visible hole count disagrees with hole note")
    recovered_geometry = []
    for circle in holes:
        cx, cy = circle["center"]
        measured_diameter = 2 * circle["radius"] * (sx + sy) / 2
        if abs(measured_diameter - diameter) > 0.5:
            raise ValueError("visible hole geometry disagrees with diameter note")
        recovered_geometry.append([round((cx - x0) * sx, 6), round((y1 - cy) * sy, 6)])
    recovered_holes = [{"id": f"H{index}", "plate": "P1", "center_mm": center,
                        "diameter_mm": diameter}
                       for index, center in enumerate(sorted(recovered_geometry, key=lambda item: (item[1], item[0])), 1)]
    model = {
        "version": IR.VERSION, "kind": "mechanical_part_2d",
        "units": {"length": "mm", "force": "N", "stress": "MPa"},
        "nodes": {}, "materials": {"steel": {"E_mpa": float(modulus_match.group(1))}},
        "sections": {}, "members": [],
        "plates": [{"id": "P1", "width_mm": width, "height_mm": height,
                    "thickness_mm": float(thickness_match.group(1)), "material": "steel"}],
        "holes": recovered_holes,
        "dimensions": [{"id": "width", "value_mm": width}, {"id": "height", "value_mm": height},
                       {"id": "hole_diameter", "value_mm": diameter},
                       {"id": "edge_offset", "value_mm": float(edge_match.group(1))}],
        "supports": {}, "loads": {},
        "assumptions": ["flat rectangular plate",
                        f'{ {4: "four", 6: "six"}.get(expected_count, str(expected_count))} circular through holes',
                        "geometry and manufacturing checks only"],
        "provenance": {"mode": "detached_untagged_svg",
                       "confidence": {"outline": 0.95, "dimensions": 0.95, "holes": 0.95,
                                      "thickness": 0.95, "material": 0.95},
                       "evidence": {"outline": "visible transformed rectangle",
                                    "dimensions": "associated dimension lines and nearby text",
                                    "holes": "visible transformed circles plus hole note",
                                    "thickness": "visible Thickness note", "material": "visible E note"},
                       "ambiguities": []},
    }
    return IR.validate(model)


def check_geometry(model: dict, min_edge_distance_mm: float = 15,
                   min_ligament_mm: float = 20) -> dict:
    model = IR.validate(model)
    if len(model["plates"]) != 1:
        raise ValueError("geometry checker requires one plate")
    plate = model["plates"][0]; holes = model["holes"]
    edge_distances = {}
    violations = []
    for hole in holes:
        x, y = hole["center_mm"]; radius = hole["diameter_mm"] / 2
        edge = min(x - radius, y - radius, plate["width_mm"] - x - radius,
                   plate["height_mm"] - y - radius)
        edge_distances[hole["id"]] = edge
        if edge < 0:
            violations.append(f'{hole["id"]} crosses the plate boundary')
        elif edge < min_edge_distance_mm:
            violations.append(f'{hole["id"]} edge distance {edge:g} mm is below {min_edge_distance_mm:g} mm')
    ligaments = {}
    for i, first in enumerate(holes):
        for second in holes[i + 1:]:
            distance = math.dist(first["center_mm"], second["center_mm"])
            ligament = distance - (first["diameter_mm"] + second["diameter_mm"]) / 2
            key = first["id"] + "-" + second["id"]; ligaments[key] = ligament
            if ligament < 0:
                violations.append(f"{key} holes overlap")
            elif ligament < min_ligament_mm:
                violations.append(f"{key} ligament {ligament:g} mm is below {min_ligament_mm:g} mm")
    gross_area = plate["width_mm"] * plate["height_mm"]
    removed_area = sum(math.pi * (hole["diameter_mm"] / 2) ** 2 for hole in holes)
    return {"pass": not violations, "violations": violations,
            "minimum_edge_distance_mm": min(edge_distances.values()) if edge_distances else None,
            "minimum_ligament_mm": min(ligaments.values()) if ligaments else None,
            "gross_area_mm2": gross_area, "net_area_mm2": gross_area - removed_area,
            "volume_mm3": (gross_area - removed_area) * plate["thickness_mm"],
            "criteria": {"min_edge_distance_mm": min_edge_distance_mm,
                         "min_ligament_mm": min_ligament_mm}}


def build(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    reference = example_model(); svg = render(reference); recovered = import_untagged(svg)
    checks = check_geometry(recovered)
    (out / "untagged-plate.svg").write_text(svg)
    (out / "reference-ir.json").write_text(json.dumps(reference, indent=2) + "\n")
    (out / "recovered-ir.json").write_text(json.dumps(recovered, indent=2) + "\n")
    (out / "geometry-checks.json").write_text(json.dumps(checks, indent=2) + "\n")
    summary = {"benchmark": "engsvg-untagged-plate-v1",
               "reference_engineering_hash": IR.engineering_digest(reference),
               "recovered_engineering_hash": IR.engineering_digest(recovered),
               "engineering_equal": IR.engineering_digest(reference) == IR.engineering_digest(recovered),
               "manufacturing_geometry_pass": checks["pass"],
               "scope": "One untagged rectangular four-hole plate; geometry/manufacturing checks, no plate FEM"}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(build(args.out), indent=2))
