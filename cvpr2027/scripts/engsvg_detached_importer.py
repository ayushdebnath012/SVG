"""Recover the bounded portal design from a detached engineering SVG.

Recovery uses the rendered member geometry and visible annotations.  Embedded
EngSVG metadata is preferred when present, but the detached path deliberately
works after that metadata is removed.  Unknown values are reported instead of
being invented.
"""
from __future__ import annotations

import json
import math
import re
import xml.etree.ElementTree as ET

import cad_astra_benchmark as B


FIELDS = (
    "width_mm", "height_mm", "section_b_mm", "section_h_mm", "E_mpa",
    "vertical_load_N", "horizontal_load_N",
)


def _number(text: str) -> float:
    return B.first_number(text)


def _canonical(value: float):
    rounded = round(value)
    return int(rounded) if abs(value - rounded) < 1e-9 else value


def _all_text(root):
    return ["".join(element.itertext()).strip() for element in root.iter()
            if element.tag.split("}")[-1] in {"text", "tspan"}]


def _embedded(root):
    node = next((element for element in root.iter()
                 if element.tag.split("}")[-1] == "metadata"
                 and element.get("id") == "engsvg-design"), None)
    if node is None or not node.text:
        return None
    value = json.loads(node.text)
    if value.get("schema_version") != "engsvg-design-v1":
        raise ValueError("unsupported engsvg metadata version")
    return value


def _check_portal_topology(members):
    required = {"left", "right", "top"}
    if set(members) != required:
        raise ValueError("expected exactly the left, right and top portal members")
    endpoints = {name: (points[0], points[-1]) for name, points in members.items()}
    left, right, top = endpoints["left"], endpoints["right"], endpoints["top"]
    tolerance = 1e-5
    if abs(left[0][0] - left[1][0]) > tolerance or abs(right[0][0] - right[1][0]) > tolerance:
        raise ValueError("portal legs are not vertical in the drawing")
    if abs(top[0][1] - top[1][1]) > tolerance:
        raise ValueError("portal top is not horizontal in the drawing")
    top_points = [top[0], top[1]]
    leg_tops = [min(left, key=lambda p: p[1]), min(right, key=lambda p: p[1])]
    for point in leg_tops:
        if min(math.dist(point, candidate) for candidate in top_points) > tolerance:
            raise ValueError("portal members are disconnected")
    return {"members": sorted(required), "connected": True, "layout": "two-leg portal"}


def import_svg(svg: str, supplied: dict | None = None) -> dict:
    """Return recovered fields, evidence, confidence, missing data and ambiguity."""
    if "<!DOCTYPE" in svg.upper() or "<!ENTITY" in svg.upper():
        raise ValueError("unsupported SVG declaration")
    root = ET.fromstring(svg)
    if root.tag.split("}")[-1] != "svg":
        raise ValueError("not an SVG root")

    embedded = _embedded(root)
    if embedded is not None:
        parameters = embedded.get("parameters", {})
        missing = [field for field in FIELDS if field not in parameters]
        return {
            "status": "recovered" if not missing else "needs_clarification",
            "mode": "embedded_metadata", "design": parameters if not missing else None,
            "partial_design": parameters, "missing": missing, "ambiguities": [],
            "confidence": {field: 1.0 for field in parameters},
            "evidence": {field: "engsvg-design-v1 metadata" for field in parameters},
            "topology": {"members": embedded.get("members", []),
                         "connected": True, "layout": "two-leg portal"},
        }

    members, dimensions, _ = B.svg_geometry(svg)
    topology = _check_portal_topology(members)
    values = {}
    evidence = {}
    confidence = {}
    ambiguities = []

    def assign(field, value, why, score):
        value = _canonical(float(value))
        if field in values and abs(values[field] - value) > 1e-6:
            ambiguities.append({"field": field, "values": [values[field], value],
                                "evidence": [evidence[field], why]})
            values.pop(field, None); confidence.pop(field, None); evidence.pop(field, None)
            return
        if not any(item["field"] == field for item in ambiguities):
            values[field] = value; evidence[field] = why; confidence[field] = score

    if "length_top" in dimensions:
        assign("width_mm", _number(dimensions["length_top"]),
               "visible data-dimension length_top", 0.98)
    leg_dimensions = [(key, dimensions[key]) for key in ("length_left", "length_right")
                      if key in dimensions]
    for key, text in leg_dimensions:
        assign("height_mm", _number(text), f"visible data-dimension {key}", 0.98)

    texts = _all_text(root)
    section_values = []
    for text in texts:
        match = re.search(r"\b(?:left|right|top)\s*:\s*"
                          r"(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\b", text, re.I)
        if match:
            section_values.append((_number(match.group(1)), _number(match.group(2)), text))
    for breadth, depth, text in section_values:
        assign("section_b_mm", breadth, f"visible section note: {text}", 0.95)
        assign("section_h_mm", depth, f"visible section note: {text}", 0.95)

    parameter_text = {}
    for element in root.iter():
        field = element.get("data-parameter")
        if field:
            if field in parameter_text:
                raise ValueError(f"duplicate visible parameter annotation: {field}")
            parameter_text[field] = "".join(element.itertext()).strip()
    for field in ("E_mpa", "vertical_load_N", "horizontal_load_N"):
        if field in parameter_text:
            assign(field, _number(parameter_text[field]),
                   f"visible data-parameter {field}", 0.98)

    supplied = supplied or {}
    unknown_supplied = set(supplied) - set(FIELDS)
    if unknown_supplied:
        raise ValueError("unknown supplied fields: " + ", ".join(sorted(unknown_supplied)))
    for field, value in supplied.items():
        if field in values and abs(values[field] - value) > 1e-6:
            ambiguities.append({"field": field, "values": [values[field], value],
                                "evidence": [evidence[field], "user supplied override"]})
            values.pop(field, None); confidence.pop(field, None); evidence.pop(field, None)
        elif not any(item["field"] == field for item in ambiguities):
            assign(field, value, "user supplied value", 1.0)

    missing = [field for field in FIELDS if field not in values]
    status = "recovered" if not missing and not ambiguities else "needs_clarification"
    return {
        "status": status, "mode": "detached_visible_evidence",
        "design": values if status == "recovered" else None,
        "partial_design": values, "missing": missing, "ambiguities": ambiguities,
        "confidence": confidence, "evidence": evidence, "topology": topology,
    }
