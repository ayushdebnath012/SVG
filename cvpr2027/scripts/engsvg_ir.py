"""Common intermediate representation for engineering SVG drawings."""
from __future__ import annotations

import copy
import hashlib
import json
import math


VERSION = "engsvg-ir-v1"
KINDS = {"frame2d", "truss2d", "plate2d", "mechanical_part_2d"}


def _positive_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be a positive finite number")


def validate(model: dict) -> dict:
    """Validate and return a defensive copy of a canonical engineering model."""
    value = copy.deepcopy(model)
    required = {"version", "kind", "units", "nodes", "materials", "sections",
                "members", "plates", "holes", "dimensions", "supports", "loads",
                "assumptions", "provenance"}
    if set(value) != required:
        raise ValueError("IR keys must be exactly: " + ", ".join(sorted(required)))
    if value["version"] != VERSION or value["kind"] not in KINDS:
        raise ValueError("unsupported IR version or drawing kind")
    if value["units"] != {"length": "mm", "force": "N", "stress": "MPa"}:
        raise ValueError("IR must use canonical mm, N and MPa units")
    if not isinstance(value["nodes"], dict):
        raise ValueError("nodes must be an object")
    if value["kind"] in {"frame2d", "truss2d"} and not value["nodes"]:
        raise ValueError("frame and truss models require at least one node")
    for node, point in value["nodes"].items():
        if not isinstance(node, str) or not node or not isinstance(point, list) or len(point) != 2:
            raise ValueError("invalid node")
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in point):
            raise ValueError("node coordinates must be finite numbers")

    for name, material in value["materials"].items():
        if not isinstance(name, str) or set(material) != {"E_mpa"}:
            raise ValueError("invalid material")
        _positive_number(material["E_mpa"], "E_mpa")
    for name, section in value["sections"].items():
        if not isinstance(name, str) or section.get("shape") not in {"rect", "area"}:
            raise ValueError("invalid section")
        if section["shape"] == "rect":
            if set(section) != {"shape", "b_mm", "h_mm"}:
                raise ValueError("rectangular section requires b_mm and h_mm")
            _positive_number(section["b_mm"], "b_mm")
            _positive_number(section["h_mm"], "h_mm")
        else:
            if set(section) != {"shape", "area_mm2"}:
                raise ValueError("area section requires area_mm2")
            _positive_number(section["area_mm2"], "area_mm2")

    member_ids = set()
    for member in value["members"]:
        if set(member) != {"id", "a", "b", "section", "material"}:
            raise ValueError("invalid member schema")
        if member["id"] in member_ids:
            raise ValueError("duplicate member ID")
        member_ids.add(member["id"])
        if member["a"] not in value["nodes"] or member["b"] not in value["nodes"] or member["a"] == member["b"]:
            raise ValueError("member references invalid nodes")
        if member["section"] not in value["sections"] or member["material"] not in value["materials"]:
            raise ValueError("member references unknown section or material")
    for node, dofs in value["supports"].items():
        if node not in value["nodes"] or not isinstance(dofs, list) or not set(dofs) <= {0, 1, 2}:
            raise ValueError("invalid support")
    for node, load in value["loads"].items():
        if node not in value["nodes"] or not isinstance(load, list) or len(load) not in {2, 3}:
            raise ValueError("invalid nodal load")
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in load):
            raise ValueError("load values must be finite numbers")
    if not isinstance(value["dimensions"], list) or not isinstance(value["plates"], list) or not isinstance(value["holes"], list):
        raise ValueError("dimensions, plates and holes must be lists")
    plate_ids = set()
    for plate in value["plates"]:
        if set(plate) != {"id", "width_mm", "height_mm", "thickness_mm", "material"}:
            raise ValueError("invalid plate schema")
        if plate["id"] in plate_ids or plate["material"] not in value["materials"]:
            raise ValueError("duplicate plate or unknown plate material")
        plate_ids.add(plate["id"])
        for field in ("width_mm", "height_mm", "thickness_mm"):
            _positive_number(plate[field], field)
    hole_ids = set()
    for hole in value["holes"]:
        if set(hole) != {"id", "plate", "center_mm", "diameter_mm"}:
            raise ValueError("invalid hole schema")
        if hole["id"] in hole_ids or hole["plate"] not in plate_ids:
            raise ValueError("duplicate hole or unknown parent plate")
        hole_ids.add(hole["id"])
        if not isinstance(hole["center_mm"], list) or len(hole["center_mm"]) != 2:
            raise ValueError("invalid hole center")
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in hole["center_mm"]):
            raise ValueError("hole center must contain finite coordinates")
        _positive_number(hole["diameter_mm"], "diameter_mm")
    if not isinstance(value["assumptions"], list) or not isinstance(value["provenance"], dict):
        raise ValueError("invalid assumptions or provenance")
    return value


def section_area(section: dict) -> float:
    return section["b_mm"] * section["h_mm"] if section["shape"] == "rect" else section["area_mm2"]


def digest(model: dict) -> str:
    value = validate(model)
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def engineering_digest(model: dict) -> str:
    """Hash engineering content while excluding origin-specific provenance."""
    value = validate(model)
    value.pop("provenance")
    for member in value["members"]:
        member["a"], member["b"] = sorted((member["a"], member["b"]))
        member["id"] = "".join(sorted(member["id"])) if len(member["id"]) == 2 else member["id"]
    value["members"] = sorted(value["members"], key=lambda item: item["id"])
    value["dimensions"] = sorted(value["dimensions"], key=lambda item: item["id"])
    def normalize(item):
        if isinstance(item, dict):
            return {key: normalize(child) for key, child in item.items()}
        if isinstance(item, list):
            return [normalize(child) for child in item]
        if isinstance(item, float) and item.is_integer():
            return int(item)
        return item
    value = normalize(value)
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
