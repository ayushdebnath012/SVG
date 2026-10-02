"""Edit generated engineering SVGs and verify the drawing that was actually produced.

Bounded pipeline:

    SVG -> untagged importer -> EngSVG IR -> deterministic edit -> target SVG
        -> tree patch -> JSON parse/policy validation -> apply -> re-import -> engineering check

All delivered edits are applied to the original SVG through parsed, validated patches.
Topology edits use version-3 structural operations and are re-imported to check connectivity.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import re
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import engsvg_ir as IR  # noqa: E402
import engsvg_plate as PLATE  # noqa: E402
import engsvg_svg_geometry as SVG_GEOMETRY  # noqa: E402
import engsvg_truss as TRUSS  # noqa: E402
import engsvg_truss_families as BRIDGE  # noqa: E402
import svg_scene_edit as STRUCTURAL  # noqa: E402
from svgpatchlab.core import apply_patch, build_scene, derive_patch, validate_patch  # noqa: E402
from svgpatchlab.core.patch import parse_patch  # noqa: E402
from svgpatchlab.core.xml import normalized_tree, parse_svg, serialize_svg  # noqa: E402


NUMBER = r"(?:\d+(?:\.\d+)?|\.\d+)"
SVG_NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def _dimension(model, name):
    return next(item for item in model["dimensions"] if item["id"] == name)


def _style(svg):
    if "#102a43" in svg or "#d9efff" in svg:
        return "blueprint"
    if "#111111" in svg:
        return "monochrome"
    return "canonical"


def _canonical_style(svg, style):
    if style == "blueprint":
        return (svg.replace('fill="#102a43"', 'fill="white"')
                .replace("#d9efff", "#1f3348").replace("#173f5f", "#eaf3f8")
                .replace("#a8d8ff", "#6b7280"))
    if style == "monochrome":
        return svg.replace("#111111", "#1f3348").replace("#f4f4f4", "#eaf3f8")
    return svg


def _apply_style(svg, style):
    if style == "blueprint":
        return (svg.replace('fill="white"', 'fill="#102a43"')
                .replace("#1f3348", "#d9efff").replace("#eaf3f8", "#173f5f")
                .replace("#6b7280", "#a8d8ff"))
    if style == "monochrome":
        return svg.replace("#1f3348", "#111111").replace("#eaf3f8", "#f4f4f4")
    return svg


def _integral_numbers(value):
    """Restore compact integer annotations after importers parse visible numbers as floats."""
    if isinstance(value, dict):
        return {key: _integral_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_integral_numbers(item) for item in value]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _preserve_labeled_truss_order(model, canonical_svg):
    """Keep DOM node/member order so unchanged geometry does not become a patch operation."""
    geometry = SVG_GEOMETRY.extract(canonical_svg)
    labels = [item for item in geometry["texts"] if re.fullmatch(r"[A-Z]", item["text"])]
    circles = [item for item in geometry["circles"]
               if str(item["fill"]).lower() == TRUSS.STRUCTURE_STROKE]
    ordered_nodes = []
    screen_names = []
    for circle in circles:
        distance, label = min((math.dist(circle["center"], item["position"]), item["text"])
                              for item in labels)
        if distance > 32 or label in ordered_nodes:
            return model
        ordered_nodes.append(label)
        screen_names.append((circle["center"], label))
    if set(ordered_nodes) != set(model["nodes"]):
        return model
    member_by_nodes = {frozenset((member["a"], member["b"])): member for member in model["members"]}
    ordered_members = []
    structural = [segment for segment in geometry["segments"]
                  if str(segment["stroke"]).lower() == TRUSS.STRUCTURE_STROKE
                  and segment["stroke_width"] >= 3]
    for segment in structural:
        names = []
        for endpoint in (segment["a"], segment["b"]):
            distance, name = min((math.dist(endpoint, center), label)
                                 for center, label in screen_names)
            if distance > 1e-3:
                return model
            names.append(name)
        member = member_by_nodes.get(frozenset(names))
        if member is None or member in ordered_members:
            return model
        member["a"], member["b"] = names
        ordered_members.append(member)
    if len(ordered_members) != len(model["members"]):
        return model
    model["nodes"] = {name: model["nodes"][name] for name in ordered_nodes}
    model["members"] = ordered_members
    return model


def _numeric_equivalent(first, second, tolerance=1e-3):
    """Treat exporter/importer decimal round-off as unchanged SVG content."""
    first_numbers = [float(value) for value in SVG_NUMBER.findall(first)]
    second_numbers = [float(value) for value in SVG_NUMBER.findall(second)]
    if len(first_numbers) != len(second_numbers):
        return False
    first_shape = SVG_NUMBER.sub("#", first)
    second_shape = SVG_NUMBER.sub("#", second)
    return (first_shape == second_shape and
            all(math.isclose(a, b, rel_tol=0, abs_tol=tolerance)
                for a, b in zip(first_numbers, second_numbers)))


def _stabilize_target(source_svg, target_svg):
    """Keep byte-level source values when recovered values differ only by harmless round-off."""
    source = parse_svg(source_svg)
    target = parse_svg(target_svg)
    source_nodes, target_nodes = list(source.iter()), list(target.iter())
    if len(source_nodes) != len(target_nodes):
        return target_svg
    for first, second in zip(source_nodes, target_nodes):
        if first.tag != second.tag:
            return target_svg
        for name, value in first.attrib.items():
            if name in second.attrib and value != second.attrib[name] and _numeric_equivalent(value, second.attrib[name]):
                second.attrib[name] = value
        first_text, second_text = first.text or "", second.text or ""
        if first_text != second_text and _numeric_equivalent(first_text, second_text):
            second.text = first.text
    return serialize_svg(target)


def recover(svg):
    """Recover a supported model from visible geometry and annotations, without metadata."""
    style = _style(svg)
    canonical = _canonical_style(svg, style)
    if "Parallel-chord bridge truss" in canonical:
        model, family = BRIDGE.import_untagged(canonical), "bridge_truss"
    elif "mounting plate" in canonical:
        model, family = PLATE.import_untagged(canonical), "plate"
    else:
        model, family = TRUSS.import_untagged(canonical), "truss"
        model = _preserve_labeled_truss_order(model, canonical)
    return IR.validate(_integral_numbers(model)), family, style


def render(model, family, style="canonical"):
    if family == "bridge_truss":
        svg = BRIDGE.render(model)
    elif family == "plate":
        svg = PLATE.render(model)
        if len(model["holes"]) != 4:
            svg = svg.replace("four-hole mounting plate", f'{len(model["holes"])}-hole mounting plate')
    else:
        svg = TRUSS.render(model)
    return _apply_style(svg, style)


def _verification(model):
    if model["kind"] == "truss2d":
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            result = TRUSS.solve(model)
        fx, fy, moment = result["equilibrium_residual_N_Nmm"]
        force_scale = max((abs(v) for load in model["loads"].values() for v in load[:2]), default=1) or 1
        length_scale = max((max(abs(x), abs(y)) for x, y in model["nodes"].values()), default=1) or 1
        relative_residual = max(abs(fx) / force_scale, abs(fy) / force_scale,
                                abs(moment) / (force_scale * length_scale))
        return {
            "method": "linear_axial_truss_fem",
            "pass": relative_residual < 1e-9,
            "peak_abs_stress_mpa": result["peak_abs_stress_mpa"],
            "max_displacement_mm": max(abs(value) for xy in result["node_displacements_mm"].values()
                                           for value in xy),
            "equilibrium_residual_N_Nmm": result["equilibrium_residual_N_Nmm"],
            "relative_equilibrium_residual": relative_residual,
            "assumptions": model["assumptions"],
        }
    result = PLATE.check_geometry(model)
    return {
        "method": "manufacturing_geometry_checks",
        "pass": result["pass"],
        "minimum_edge_distance_mm": result["minimum_edge_distance_mm"],
        "minimum_ligament_mm": result["minimum_ligament_mm"],
        "net_area_mm2": result["net_area_mm2"],
        "volume_mm3": result["volume_mm3"],
        "violations": result["violations"],
        "criteria": result["criteria"],
        "assumptions": model["assumptions"],
    }


def _same_load_value(model):
    values = {round(load[1], 9) for load in model["loads"].values()}
    if len(values) != 1:
        raise ValueError("the bounded editor requires one common vertical load value")
    return next(iter(values))


def interpret(request, model, family):
    """Parse the edit types used by the generated dataset, with explicit arithmetic."""
    text = " ".join(request.lower().replace(",", " ").split())
    panel = re.search(rf"(?:change|set|make|use).*?(?P<n>\d+)\s+panels?", text)
    if not panel:
        panel = re.search(rf"(?P<n>\d+)\s+panels?", text)
    if panel:
        if family != "bridge_truss":
            raise ValueError("panel-count edits are supported only for generated bridge trusses")
        return {"action": "edit_topology", "panels": int(panel.group("n"))}

    changes = {}
    if model["kind"] == "truss2d":
        load = abs(_same_load_value(model))
        match = re.search(rf"increase .*?(?:load|force).*? by (?P<p>{NUMBER})\s*%", text)
        if match:
            changes["loads.*.fy_N"] = -round(load * (1 + float(match.group("p")) / 100))
        match = re.search(rf"(?:reduce|decrease) .*?(?:load|force).*? by (?P<p>{NUMBER})\s*%", text)
        if match:
            changes["loads.*.fy_N"] = -round(load * (1 - float(match.group("p")) / 100))
        doubled = (re.search(r"\bdouble\b.*?\b(?:load|force)\b", text) or
                   re.search(r"\b(?:load|force)\b.*?\bdouble\b", text) or
                   re.search(r"\bmultiply\b.*?\b(?:load|force)\b.*?\bby\s+2(?:\.0+)?\b", text))
        if doubled:
            changes["loads.*.fy_N"] = -2 * load
        match = re.search(rf"make every member (?P<v>{NUMBER})\s*mm wider", text)
        if match:
            changes["sections.bar.b_mm"] = model["sections"]["bar"]["b_mm"] + float(match.group("v"))
        match = re.search(rf"set (?:every|all|the)?\s*member (?:depth|height) to (?P<v>{NUMBER})\s*mm", text)
        if match:
            changes["sections.bar.h_mm"] = float(match.group("v"))
        match = re.search(rf"(?:set|change).*?(?:modulus|\be\b).*?to (?P<v>{NUMBER})\s*(?P<u>gpa|mpa)", text)
        if match:
            changes["materials.steel.E_mpa"] = float(match.group("v")) * (1000 if match.group("u") == "gpa" else 1)
        match = re.search(rf"(?:set|change).*?(?:height|rise).*?to (?P<v>{NUMBER})\s*mm", text)
        if match:
            changes["dimensions.height.value_mm"] = float(match.group("v"))
        match = re.search(rf"(?:set|change).*?(?:span|width).*?to (?P<v>{NUMBER})\s*mm", text)
        if match:
            changes["dimensions.span.value_mm"] = float(match.group("v"))
    else:
        plate = model["plates"][0]
        diameter = model["holes"][0]["diameter_mm"]
        offset = _dimension(model, "edge_offset")["value_mm"]
        match = re.search(rf"(?:make the plate|increase (?:the )?plate thickness by) (?P<v>{NUMBER})\s*mm thicker", text)
        if not match:
            match = re.search(rf"make the plate (?P<v>{NUMBER})\s*mm thicker", text)
        if match:
            changes["plates.P1.thickness_mm"] = plate["thickness_mm"] + float(match.group("v"))
        match = re.search(rf"set (?:the )?plate thickness to (?P<v>{NUMBER})\s*mm", text)
        if match:
            changes["plates.P1.thickness_mm"] = float(match.group("v"))
        match = re.search(rf"increase (?:all|every) hole diameters? by (?P<v>{NUMBER})\s*mm", text)
        if match:
            changes["holes.*.diameter_mm"] = diameter + float(match.group("v"))
        match = re.search(rf"set (?:all|every) hole diameters? to (?P<v>{NUMBER})\s*mm", text)
        if match:
            changes["holes.*.diameter_mm"] = float(match.group("v"))
        match = re.search(rf"move every (?:corner )?hole (?P<v>{NUMBER})\s*mm farther from", text)
        if match:
            changes["dimensions.edge_offset.value_mm"] = offset + float(match.group("v"))
        match = re.search(rf"(?:set|change).*?(?:modulus|\be\b).*?to (?P<v>{NUMBER})\s*(?P<u>gpa|mpa)", text)
        if match:
            changes["materials.steel.E_mpa"] = float(match.group("v")) * (1000 if match.group("u") == "gpa" else 1)
    if not changes:
        raise ValueError("no supported unambiguous engineering edit found")
    return {"action": "edit", "changes": changes}


def _move_holes(model, offset):
    plate = model["plates"][0]
    width, height = plate["width_mm"], plate["height_mm"]
    if len(model["holes"]) == 6:
        centers = ((offset, offset), (width / 2, offset), (width - offset, offset),
                   (offset, height - offset), (width / 2, height - offset),
                   (width - offset, height - offset))
    elif len(model["holes"]) == 4:
        centers = ((offset, offset), (width - offset, offset),
                   (offset, height - offset), (width - offset, height - offset))
    else:
        raise ValueError("hole-offset edit requires the generated four- or six-hole layout")
    for hole, center in zip(model["holes"], centers):
        hole["center_mm"] = list(center)
    _dimension(model, "edge_offset")["value_mm"] = offset


def apply_changes(model, changes):
    target = copy.deepcopy(model)
    for path, value in changes.items():
        if path == "loads.*.fy_N":
            for load in target["loads"].values():
                load[1] = value
        elif path == "sections.bar.b_mm":
            target["sections"]["bar"]["b_mm"] = value
        elif path == "sections.bar.h_mm":
            target["sections"]["bar"]["h_mm"] = value
        elif path == "materials.steel.E_mpa":
            target["materials"]["steel"]["E_mpa"] = value
        elif path == "plates.P1.thickness_mm":
            target["plates"][0]["thickness_mm"] = value
        elif path == "holes.*.diameter_mm":
            for hole in target["holes"]:
                hole["diameter_mm"] = value
            _dimension(target, "hole_diameter")["value_mm"] = value
        elif path == "dimensions.edge_offset.value_mm":
            _move_holes(target, value)
        elif path in {"dimensions.height.value_mm", "dimensions.span.value_mm"}:
            dimension = "height" if ".height." in path else "span"
            old = _dimension(target, dimension)["value_mm"]
            axis = 1 if dimension == "height" else 0
            for point in target["nodes"].values():
                point[axis] *= value / old
            _dimension(target, dimension)["value_mm"] = value
        else:
            raise ValueError(f"unsupported change path: {path}")
    target["provenance"] = {"mode": "svg_edit", "confidence": {}, "evidence": {}, "ambiguities": []}
    return IR.validate(_integral_numbers(target))


def _signature(model):
    def point(value):
        return tuple(round(x, 2) for x in value)
    coordinates = {name: point(value) for name, value in model["nodes"].items()}
    edges = {tuple(sorted((coordinates[m["a"]], coordinates[m["b"]]))) for m in model["members"]}
    return set(coordinates.values()), edges


def _identify_bridge_family(model):
    ys = [point[1] for point in model["nodes"].values()]
    bottom = min(ys)
    panels = sum(abs(point[1] - bottom) < 1e-3 for point in model["nodes"].values()) - 1
    span = _dimension(model, "span")["value_mm"]
    height = _dimension(model, "height")["value_mm"]
    load = _same_load_value(model)
    section = model["sections"]["bar"]
    want = _signature(model)
    for name, generator in BRIDGE.FAMILIES.items():
        try:
            candidate = generator(panels=panels, span=span, height=height, load_N=load,
                                  b_mm=section["b_mm"], h_mm=section["h_mm"],
                                  E=model["materials"]["steel"]["E_mpa"])
        except Exception:
            continue
        if _signature(candidate) == want:
            return name
    raise ValueError("could not identify the generated bridge topology")


def _plan_topology(model, panels):
    if panels < 2 or panels > 30:
        raise ValueError("panel count must be between 2 and 30")
    family = _identify_bridge_family(model)
    section = model["sections"]["bar"]
    target = BRIDGE.FAMILIES[family](
        panels=panels, span=_dimension(model, "span")["value_mm"],
        height=_dimension(model, "height")["value_mm"], load_N=_same_load_value(model),
        b_mm=section["b_mm"], h_mm=section["h_mm"],
        E=model["materials"]["steel"]["E_mpa"])
    target["provenance"] = {"mode": "topology_patch_plan", "confidence": {},
                            "evidence": {}, "ambiguities": []}
    return IR.validate(target), family


def edit_svg(svg, request):
    source_model, family, style = recover(svg)
    before = _verification(source_model)
    action = interpret(request, source_model, family)
    if action["action"] == "edit_topology":
        target_model, topology = _plan_topology(source_model, action["panels"])
        target_svg = render(target_model, family, style)
        # The rendered design is an internal patch-planning reference, never the delivered output.
        edited = STRUCTURAL.edit_to_target(svg, target_svg)
        if edited["status"] != "verified":
            raise ValueError("structural patch failed SVG tree/reference validation")
        output = edited["output_svg"]
        patch_json = edited["patch"]
        mode = "structural_tree_patch"
        operations = edited["patch_operation_types"]
        action["topology"] = topology
    else:
        target_model = apply_changes(source_model, action["changes"])
        target_svg = _stabilize_target(svg, render(target_model, family, style))
        derived = derive_patch(svg, target_svg)
        # Exercise the same serialization boundary used for stored/model-produced patches.
        parsed = parse_patch(derived.to_json())
        validate_patch(parsed, build_scene(svg))
        output = apply_patch(svg, parsed)
        patch_json = parsed.to_dict()
        mode = "tree_patch"
        operations = [item.op for item in parsed.operations]
        if normalized_tree(parse_svg(output)) != normalized_tree(parse_svg(target_svg)):
            raise ValueError("applied patch did not reproduce the intended SVG tree")
    actual_model, actual_family, actual_style = recover(output)
    after = _verification(actual_model)
    exact_tree = normalized_tree(parse_svg(output)) == normalized_tree(parse_svg(target_svg))
    status = ("failed" if not exact_tree else
              "verified_safe" if after["pass"] else "verified_with_violations")
    return {
        "status": status,
        "mode": mode,
        "request": request,
        "family": family,
        "style": style,
        "action": action,
        "patch": patch_json,
        "patch_operation_count": len(operations),
        "patch_operation_types": operations,
        "target_tree_equal": exact_tree,
        "edit_fidelity_pass": exact_tree,
        "engineering_check_pass": after["pass"],
        "recovered_output_family": actual_family,
        "recovered_output_style": actual_style,
        "before_verification": before,
        "after_verification": after,
        "output_svg": output,
    }


def save_edit(input_path, request, out):
    svg = input_path.read_text()
    result = edit_svg(svg, request)
    out.mkdir(parents=True, exist_ok=True)
    (out / "source.svg").write_text(svg)
    (out / "edited.svg").write_text(result.pop("output_svg"))
    if result["patch"] is not None:
        (out / "patch.json").write_text(json.dumps(result["patch"], indent=2) + "\n")
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(save_edit(args.input, args.request, args.out), indent=2))
