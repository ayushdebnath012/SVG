"""Untagged triangular-truss SVG generation, recovery and FEM verification."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import numpy as np

import engsvg_ir as IR
import engsvg_svg_geometry as SVG


STRUCTURE_STROKE = "#1f3348"


def example_model() -> dict:
    model = {
        "version": IR.VERSION,
        "kind": "truss2d",
        "units": {"length": "mm", "force": "N", "stress": "MPa"},
        "nodes": {"A": [0, 0], "B": [1000, 0], "C": [2000, 1200],
                  "D": [3000, 0], "E": [4000, 0]},
        "materials": {"steel": {"E_mpa": 200000}},
        "sections": {"bar": {"shape": "rect", "b_mm": 40, "h_mm": 20}},
        "members": [
            {"id": name, "a": name[0], "b": name[1], "section": "bar", "material": "steel"}
            for name in ("AB", "BD", "DE", "AC", "BC", "CD", "CE")
        ],
        "plates": [], "holes": [],
        "dimensions": [
            {"id": "span", "value_mm": 4000, "between": ["A", "E"]},
            {"id": "height", "value_mm": 1200, "between": ["baseline", "C"]},
        ],
        "supports": {"A": [0, 1], "E": [1]},
        "loads": {"C": [0, -20000]},
        "assumptions": ["planar pin-jointed truss", "linear elastic axial members",
                        "nodal loads only", "small displacement"],
        "provenance": {"mode": "authored", "confidence": {}, "evidence": {},
                       "ambiguities": []},
    }
    return IR.validate(model)


def solve(model: dict) -> dict:
    model = IR.validate(model)
    if model["kind"] != "truss2d":
        raise ValueError("truss solver requires kind=truss2d")
    names = list(model["nodes"])
    index = {name: i for i, name in enumerate(names)}
    stiffness = np.zeros((2 * len(names), 2 * len(names)))
    member_data = {}
    for member in model["members"]:
        a = np.asarray(model["nodes"][member["a"]], dtype=float)
        b = np.asarray(model["nodes"][member["b"]], dtype=float)
        delta = b - a; length = float(np.linalg.norm(delta))
        if length <= 0:
            raise ValueError("zero-length truss member")
        c, s = delta / length
        area = IR.section_area(model["sections"][member["section"]])
        modulus = model["materials"][member["material"]]["E_mpa"]
        q = np.array([-c, -s, c, s])
        local = modulus * area / length * np.outer(q, q)
        dofs = [2 * index[member["a"]], 2 * index[member["a"]] + 1,
                2 * index[member["b"]], 2 * index[member["b"]] + 1]
        stiffness[np.ix_(dofs, dofs)] += local
        member_data[member["id"]] = (q, dofs, modulus, length)
    force = np.zeros(2 * len(names))
    for node, load in model["loads"].items():
        force[2 * index[node]:2 * index[node] + 2] += load[:2]
    fixed = sorted({2 * index[node] + dof for node, dofs in model["supports"].items()
                    for dof in dofs if dof in (0, 1)})
    free = [dof for dof in range(len(force)) if dof not in fixed]
    displacement = np.zeros_like(force)
    displacement[free] = np.linalg.solve(stiffness[np.ix_(free, free)], force[free])
    residual = stiffness @ displacement - force
    reactions = {node: [float(residual[2 * index[node]]), float(residual[2 * index[node] + 1])]
                 for node in model["supports"]}
    stresses = {}
    for member in model["members"]:
        q, dofs, modulus, length = member_data[member["id"]]
        strain = float(q @ displacement[dofs] / length)
        stresses[member["id"]] = modulus * strain
    total_fx = sum(load[0] for load in model["loads"].values()) + sum(r[0] for r in reactions.values())
    total_fy = sum(load[1] for load in model["loads"].values()) + sum(r[1] for r in reactions.values())
    moment = 0.0
    for node, load in list(model["loads"].items()) + list(reactions.items()):
        x, y = model["nodes"][node]
        moment += x * load[1] - y * load[0]
    return {
        "node_displacements_mm": {name: displacement[2 * i:2 * i + 2].tolist()
                                  for i, name in enumerate(names)},
        "member_stress_mpa": stresses,
        "peak_abs_stress_mpa": max(abs(value) for value in stresses.values()),
        "reactions_N": reactions,
        "equilibrium_residual_N_Nmm": [float(total_fx), float(total_fy), float(moment)],
        "free_residual_max_N": float(np.max(np.abs(residual[free]))),
    }


def render(model: dict) -> str:
    model = IR.validate(model)
    if model["kind"] != "truss2d":
        raise ValueError("truss renderer requires kind=truss2d")
    left, right, bottom, top = 100.0, 1000.0, 560.0, 250.0
    xs = [point[0] for point in model["nodes"].values()]
    ys = [point[1] for point in model["nodes"].values()]
    scale = min((right - left) / (max(xs) - min(xs)), (bottom - top) / (max(ys) - min(ys)))
    def point(name):
        x, y = model["nodes"][name]
        return left + (x - min(xs)) * scale, bottom - (y - min(ys)) * scale
    section = model["sections"]["bar"]
    modulus = model["materials"]["steel"]["E_mpa"]
    load = abs(model["loads"]["C"][1])
    dimension_values = {item["id"]: item["value_mm"] for item in model["dimensions"]}
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 800" width="1100" height="800">',
             '<rect width="1100" height="800" fill="white"/>',
             '<text x="35" y="40" font-size="23">Five-node triangular engineering truss</text>',
             '<text x="35" y="67" font-size="13">Untagged SVG geometry; canonical drawing units are mm, N and MPa</text>',
             '<g transform="translate(15 10)">']
    for member in model["members"]:
        x1, y1 = point(member["a"]); x2, y2 = point(member["b"])
        parts.append(f'<line x1="{x1:.6f}" y1="{y1:.6f}" x2="{x2:.6f}" y2="{y2:.6f}" stroke="{STRUCTURE_STROKE}" stroke-width="4"/>')
    for name in model["nodes"]:
        x, y = point(name)
        parts.append(f'<circle cx="{x:.6f}" cy="{y:.6f}" r="5" fill="{STRUCTURE_STROKE}"/>')
        parts.append(f'<text x="{x + 8:.6f}" y="{y - 9:.6f}" font-size="14">{name}</text>')
    parts.append('</g>')
    ax, ay = point("A"); ex, ey = point("E"); cx, cy = point("C")
    parts += [
        f'<path d="M{ax-14},{ay+10} H{ax+14} L{ax},{ay} Z" fill="none" stroke="black"/>',
        f'<path d="M{ex-14},{ey+10} H{ex+14} L{ex},{ey} Z M{ex-8},{ey+15} a4,4 0 1,0 8,0 M{ex+4},{ey+15} a4,4 0 1,0 8,0" fill="none" stroke="black"/>',
        f'<line x1="{cx}" y1="{cy-85}" x2="{cx}" y2="{cy-10}" stroke="#b3261e" stroke-width="3"/>',
        f'<path d="M{cx-8},{cy-22} L{cx},{cy-8} L{cx+8},{cy-22}" fill="#b3261e"/>',
        '<line x1="115" y1="600" x2="1015" y2="600" stroke="#6b7280" stroke-width="1"/>',
        '<line x1="115" y1="585" x2="115" y2="610" stroke="#6b7280" stroke-width="1"/>',
        '<line x1="1015" y1="585" x2="1015" y2="610" stroke="#6b7280" stroke-width="1"/>',
        f'<text x="535" y="590" font-size="14">{dimension_values["span"]:g} mm</text>',
        '<line x1="75" y1="260" x2="75" y2="570" stroke="#6b7280" stroke-width="1"/>',
        '<line x1="65" y1="260" x2="90" y2="260" stroke="#6b7280" stroke-width="1"/>',
        '<line x1="65" y1="570" x2="90" y2="570" stroke="#6b7280" stroke-width="1"/>',
        f'<text x="20" y="420" font-size="14">{dimension_values["height"]:g} mm</text>',
        f'<text x="35" y="635" font-size="14">Section: {section["b_mm"]} x {section["h_mm"]} mm</text>',
        f'<text x="330" y="635" font-size="14">E: {modulus} MPa</text>',
        f'<text x="35" y="670" font-size="14">Load at C: {load:g} N downward</text>',
        '<text x="350" y="670" font-size="14">Supports: A pin; E roller</text>',
        '<text x="35" y="755" font-size="12">Planar linear pin-jointed truss; nodal loads; small displacement.</text>',
        '</svg>',
    ]
    svg = "\n".join(parts)
    ET.fromstring(svg)
    if "data-member" in svg or "data-dimension" in svg:
        raise AssertionError("untagged fixture contains semantic geometry tags")
    return svg


def import_untagged(svg: str) -> dict:
    geometry = SVG.extract(svg)
    structural = [segment for segment in geometry["segments"]
                  if str(segment["stroke"]).lower() == STRUCTURE_STROKE and segment["stroke_width"] >= 3]
    if len(structural) < 3:
        raise ValueError("at least three visible structural segments are required")
    points, edges = SVG.cluster_points(structural, tolerance=1e-3)
    if len(points) < 3:
        raise ValueError("at least three connected truss nodes are required")
    # Recover node names from nearby single-letter visible labels.
    labels = {}
    label_items = [item for item in geometry["texts"] if re.fullmatch(r"[A-Z]", item["text"])]
    for index, point in enumerate(points):
        candidates = [(math.dist(point, item["position"]), item["text"]) for item in label_items]
        if candidates and min(candidates)[0] <= 32:
            labels[index] = min(candidates)[1]
    if len(labels) != len(points) or len(set(labels.values())) != len(points):
        raise ValueError("could not uniquely associate visible node labels with every endpoint")
    edge_names = {"".join(sorted((labels[a], labels[b]))) for a, b in edges}
    if len(edge_names) != len(edges):
        raise ValueError("duplicate visible truss members")
    adjacency = {index: set() for index in range(len(points))}
    for a, b in edges:
        adjacency[a].add(b); adjacency[b].add(a)
    reached = {next(iter(adjacency))}
    frontier = list(reached)
    while frontier:
        current = frontier.pop()
        for neighbour in adjacency[current] - reached:
            reached.add(neighbour); frontier.append(neighbour)
    if len(reached) != len(points):
        raise ValueError("visible truss graph is disconnected")

    text = " | ".join(item["text"] for item in geometry["texts"])
    def require(pattern, label):
        match = re.search(pattern, text, re.I)
        if not match:
            raise ValueError(f"missing visible {label}")
        return match
    span_match = re.search(r"Span\s*:\s*(\d+(?:\.\d+)?)\s*mm", text, re.I)
    height_match = re.search(r"Height\s*:\s*(\d+(?:\.\d+)?)\s*mm", text, re.I)
    associated = SVG.associate_linear_dimensions(geometry)
    horizontal = [item for item in associated if item["orientation"] == "horizontal"]
    vertical = [item for item in associated if item["orientation"] == "vertical"]
    if span_match:
        span = float(span_match.group(1))
    elif horizontal:
        span = max(horizontal, key=lambda item: math.dist(item["line"]["a"], item["line"]["b"]))["value_mm"]
    else:
        raise ValueError("missing visible span dimension")
    if height_match:
        height = float(height_match.group(1))
    elif vertical:
        height = max(vertical, key=lambda item: math.dist(item["line"]["a"], item["line"]["b"]))["value_mm"]
    else:
        raise ValueError("missing visible height dimension")
    section_match = require(r"Section\s*:\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*mm", "section")
    modulus = float(require(r"\bE\s*:\s*(\d+(?:\.\d+)?)\s*MPa", "modulus").group(1))
    load_match = require(r"Load\s+at\s+([A-Z])\s*:\s*(\d+(?:\.\d+)?)\s*N\s+downward", "load")
    load_node, load = load_match.group(1), float(load_match.group(2))
    supports_match = require(r"Supports\s*:\s*([A-Z])\s+pin\s*;\s*([A-Z])\s+roller", "support definition")
    pin_node, roller_node = supports_match.group(1), supports_match.group(2)
    if load_node not in labels.values() or pin_node not in labels.values() or roller_node not in labels.values():
        raise ValueError("visible load or support references an unknown node")

    min_x, max_x = min(p[0] for p in points), max(p[0] for p in points)
    bottom_y, top_y = max(p[1] for p in points), min(p[1] for p in points)
    if max_x <= min_x or bottom_y <= top_y or height <= 0 or span <= 0:
        raise ValueError("invalid visible scale dimensions")
    scale_x = span / (max_x - min_x)
    scale_y = height / (bottom_y - top_y)
    if abs(scale_x - scale_y) / max(scale_x, scale_y) > 0.02:
        raise ValueError("visible span and height imply inconsistent drawing scales")
    nodes = {label: [round((points[index][0] - min_x) * scale_x, 6),
                     round((bottom_y - points[index][1]) * scale_y, 6)]
             for index, label in labels.items()}
    b_mm, h_mm = map(float, section_match.groups())
    model = {
        "version": IR.VERSION, "kind": "truss2d",
        "units": {"length": "mm", "force": "N", "stress": "MPa"},
        "nodes": nodes, "materials": {"steel": {"E_mpa": modulus}},
        "sections": {"bar": {"shape": "rect", "b_mm": b_mm, "h_mm": h_mm}},
        "members": [{"id": name, "a": name[0], "b": name[1],
                     "section": "bar", "material": "steel"} for name in sorted(edge_names)],
        "plates": [], "holes": [],
        "dimensions": [{"id": "span", "value_mm": span, "between": [pin_node, roller_node]},
                       {"id": "height", "value_mm": height, "between": ["baseline", load_node]}],
        "supports": {pin_node: [0, 1], roller_node: [1]}, "loads": {load_node: [0, -load]},
        "assumptions": ["planar pin-jointed truss", "linear elastic axial members",
                        "nodal loads only", "small displacement"],
        "provenance": {
            "mode": "detached_untagged_svg", "confidence": {
                "geometry": 0.90, "connectivity": 0.95, "dimensions": 0.95,
                "section": 0.95, "material": 0.95, "loads": 0.95, "supports": 0.95,
            },
            "evidence": {
                "geometry": f"{len(edges)} ordinary visible SVG segments clustered into {len(points)} endpoints",
                "dimensions": "visible Span and Height text", "section": "visible Section text",
                "material": "visible E text", "loads": "visible Load at C text",
                "supports": "visible support symbols and Supports text",
            },
            "ambiguities": [],
        },
    }
    return IR.validate(model)


def build(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    reference = example_model(); svg = render(reference); recovered = import_untagged(svg)
    analysis = solve(recovered)
    (out / "untagged-truss.svg").write_text(svg)
    (out / "reference-ir.json").write_text(json.dumps(reference, indent=2) + "\n")
    (out / "recovered-ir.json").write_text(json.dumps(recovered, indent=2) + "\n")
    (out / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")
    summary = {
        "benchmark": "engsvg-untagged-truss-v1", "reference_record_hash": IR.digest(reference),
        "recovered_record_hash": IR.digest(recovered),
        "reference_engineering_hash": IR.engineering_digest(reference),
        "recovered_engineering_hash": IR.engineering_digest(recovered),
        "engineering_equal": IR.engineering_digest(reference) == IR.engineering_digest(recovered),
        "geometry_equal": reference["nodes"] == recovered["nodes"],
        "topology_equal": {m["id"] for m in reference["members"]} == {m["id"] for m in recovered["members"]},
        "max_equilibrium_residual": max(abs(x) for x in analysis["equilibrium_residual_N_Nmm"]),
        "scope": "One untagged five-node triangular truss; not general SVG recognition",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.out), indent=2))
