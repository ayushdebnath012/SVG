"""Safe transform-aware extraction of visible SVG geometry and annotations."""
from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET

import numpy as np

from svgpatchlab.eval.field_fidelity import element_path, transform_matrix
from svgpathtools import Line


UNSAFE_TAGS = {"script", "image", "foreignObject", "use", "style", "clipPath", "mask", "filter"}


def _tag(element):
    return element.tag.split("}")[-1]


def _float(value, default=None):
    if value is None:
        if default is None:
            raise ValueError("missing numeric SVG attribute")
        return default
    match = re.match(r"\s*([-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?)", value)
    if not match:
        raise ValueError("invalid numeric SVG attribute")
    result = float(match.group(1))
    if not math.isfinite(result):
        raise ValueError("nonfinite SVG coordinate")
    return result


def _point(matrix, x, y):
    result = matrix @ np.array([x, y, 1.0])
    return [float(result[0]), float(result[1])]


def extract(svg: str) -> dict:
    """Extract visible straight geometry, rectangles, circles and positioned text."""
    if "<!DOCTYPE" in svg.upper() or "<!ENTITY" in svg.upper():
        raise ValueError("unsupported SVG declaration")
    root = ET.fromstring(svg)
    if _tag(root) != "svg":
        raise ValueError("not an SVG root")
    result = {"segments": [], "rectangles": [], "circles": [], "texts": []}

    def walk(element, parent_matrix, inherited, hidden_parent=False):
        tag = _tag(element)
        if tag in UNSAFE_TAGS:
            raise ValueError("unsupported SVG element: " + tag)
        if tag == "svg" and element is not root:
            raise ValueError("nested SVG is unsupported")
        if any(key in element.attrib for key in ("clip-path", "mask", "filter")):
            raise ValueError("unsupported SVG compositing")
        style = dict(inherited)
        for key in ("stroke", "stroke-width", "stroke-opacity", "fill", "fill-opacity",
                    "opacity", "display", "visibility"):
            if key in element.attrib:
                style[key] = element.get(key)
        for entry in element.get("style", "").split(";"):
            if ":" in entry:
                key, value = entry.split(":", 1); style[key.strip()] = value.strip()
        matrix = parent_matrix @ transform_matrix(element.get("transform", ""))
        hidden = hidden_parent or tag == "defs" or style.get("display") == "none" or style.get("visibility") in {"hidden", "collapse"}
        for key in ("opacity", "stroke-opacity", "fill-opacity"):
            if key in style and _float(style[key], 1) == 0:
                hidden = True
        if not hidden and tag in {"line", "path", "polyline"} and style.get("stroke", "none") not in {"none", "transparent"}:
            path = element_path(element)
            if path and all(isinstance(segment, Line) for segment in path):
                width = _float(style.get("stroke-width"), 1)
                for segment in path:
                    a = _point(matrix, segment.start.real, segment.start.imag)
                    b = _point(matrix, segment.end.real, segment.end.imag)
                    result["segments"].append({"a": a, "b": b, "stroke": style.get("stroke"),
                                               "stroke_width": width, "source_tag": tag})
        if not hidden and tag == "rect" and style.get("fill", "none") not in {"none", "transparent"}:
            x = _float(element.get("x"), 0); y = _float(element.get("y"), 0)
            width = _float(element.get("width")); height = _float(element.get("height"))
            corners = [_point(matrix, x, y), _point(matrix, x + width, y),
                       _point(matrix, x + width, y + height), _point(matrix, x, y + height)]
            result["rectangles"].append({"corners": corners, "fill": style.get("fill"),
                                         "stroke": style.get("stroke", "none")})
        if not hidden and tag == "circle" and style.get("fill", "none") not in {"none", "transparent"}:
            center = _point(matrix, _float(element.get("cx"), 0), _float(element.get("cy"), 0))
            radius = _float(element.get("r"))
            px = _point(matrix, _float(element.get("cx"), 0) + radius, _float(element.get("cy"), 0))
            py = _point(matrix, _float(element.get("cx"), 0), _float(element.get("cy"), 0) + radius)
            rx, ry = math.dist(center, px), math.dist(center, py)
            if abs(rx - ry) > 1e-5 * max(rx, ry, 1):
                raise ValueError("nonuniformly transformed circle is unsupported")
            result["circles"].append({"center": center, "radius": (rx + ry) / 2,
                                      "fill": style.get("fill"), "stroke": style.get("stroke", "none")})
        if not hidden and tag == "text":
            text = "".join(element.itertext()).strip()
            if text:
                result["texts"].append({"text": text, "position": _point(
                    matrix, _float(element.get("x"), 0), _float(element.get("y"), 0))})
        for child in element:
            walk(child, matrix, style, hidden)

    walk(root, np.eye(3), {})
    return result


def cluster_points(segments: list[dict], tolerance: float = 1e-4):
    points = []
    def index(point):
        for i, existing in enumerate(points):
            if math.dist(point, existing) <= tolerance:
                return i
        points.append(point); return len(points) - 1
    edges = [(index(segment["a"]), index(segment["b"])) for segment in segments]
    return points, edges


def associate_linear_dimensions(geometry: dict, stroke: str = "#6b7280") -> list[dict]:
    """Associate visible `number mm` text with nearby horizontal/vertical dimension lines."""
    lines = [segment for segment in geometry["segments"]
             if str(segment["stroke"]).lower() == stroke and segment["stroke_width"] <= 2]
    labels = []
    for item in geometry["texts"]:
        match = re.search(r"(?<![\w.])(\d+(?:\.\d+)?)\s*mm\b", item["text"], re.I)
        if match:
            labels.append((float(match.group(1)), item))
    associations = []
    for segment in lines:
        ax, ay = segment["a"]; bx, by = segment["b"]
        horizontal = abs(by - ay) <= 1e-5
        vertical = abs(bx - ax) <= 1e-5
        if not (horizontal or vertical):
            continue
        midpoint = [(ax + bx) / 2, (ay + by) / 2]
        candidates = [(math.dist(midpoint, item["position"]), value, item) for value, item in labels]
        if not candidates:
            continue
        distance, value, item = min(candidates, key=lambda row: row[0])
        if distance <= max(60, 0.25 * math.dist(segment["a"], segment["b"])):
            associations.append({"orientation": "horizontal" if horizontal else "vertical",
                                 "value_mm": value, "line": segment,
                                 "label": item["text"], "label_distance_px": distance})
    return associations
