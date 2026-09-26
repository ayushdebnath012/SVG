"""Domain-independent SVG scene graphs, node correspondence and structural patches."""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import hashlib
import math
import re
import xml.etree.ElementTree as ET
from typing import Any

from .patch import Patch, PatchOperation
from .xml import index_tree, local_name, parse_svg


NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
REFERENCE = re.compile(r"url\(\s*['\"]?#([^)'\"]+)", re.I)
FORBIDDEN_ELEMENTS = {"script", "foreignObject", "iframe", "object", "embed"}


@dataclass(frozen=True)
class TreeCorrespondence:
    source_to_target: dict[str, str]
    target_to_source: dict[str, str]
    source_unmatched: tuple[str, ...]
    target_unmatched: tuple[str, ...]


def _float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bbox_hint(element):
    tag = local_name(element.tag)
    a = element.attrib
    if tag == "line":
        values = [_float(a.get(key)) for key in ("x1", "y1", "x2", "y2")]
        if None not in values:
            x1, y1, x2, y2 = values
            return [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
    if tag == "rect":
        values = [_float(a.get(key, 0)) for key in ("x", "y", "width", "height")]
        if None not in values:
            x, y, width, height = values
            return [x, y, x + width, y + height]
    if tag in {"circle", "ellipse"}:
        cx, cy = _float(a.get("cx", 0)), _float(a.get("cy", 0))
        rx = _float(a.get("r" if tag == "circle" else "rx"))
        ry = rx if tag == "circle" else _float(a.get("ry"))
        if None not in (cx, cy, rx, ry):
            return [cx - rx, cy - ry, cx + rx, cy + ry]
    if tag == "text":
        x, y = _float(a.get("x", 0)), _float(a.get("y", 0))
        if None not in (x, y):
            return [x, y, x, y]
    return None


def _references(element):
    result = []
    for name, value in element.attrib.items():
        if local_name(name) == "href" and value.startswith("#"):
            result.append({"attribute": local_name(name), "target_xml_id": value[1:]})
        for target in REFERENCE.findall(value):
            result.append({"attribute": local_name(name), "target_xml_id": target})
    return result


def build_scene_graph(svg: str) -> dict[str, Any]:
    """Represent any safe SVG as DOM nodes plus hierarchy and local reference edges."""
    root = parse_svg(svg)
    for element in root.iter():
        tag = local_name(element.tag)
        if tag in FORBIDDEN_ELEMENTS:
            raise ValueError(f"unsafe SVG element: {tag}")
        for name, value in element.attrib.items():
            lname = local_name(name).lower()
            lowered = value.lower().replace(" ", "")
            if lname.startswith("on") or "javascript:" in lowered:
                raise ValueError(f"unsafe SVG attribute: {lname}")
            if lname == "href" and value and not value.startswith("#"):
                raise ValueError("external SVG references are not allowed")
            for reference in re.findall(r"url\((.*?)\)", value, re.I):
                if not reference.strip(" \"'").startswith("#"):
                    raise ValueError("external SVG URL references are not allowed")
    indexed = index_tree(root)
    nodes = []
    xml_ids = {}
    for node in indexed:
        xml_id = node.element.attrib.get("id")
        if xml_id:
            xml_ids.setdefault(xml_id, []).append(node.node_id)
        geometry = {name: node.element.attrib[name] for name in ("d", "points")
                    if name in node.element.attrib}
        nodes.append({
            "id": node.node_id,
            "xml_id": xml_id,
            "tag": local_name(node.element.tag),
            "parent": node.parent_id,
            "child_index": node.child_index,
            "children": [],
            "attributes": dict(node.element.attrib),
            "text": (node.element.text or "").strip(),
            "bbox_hint": _bbox_hint(node.element),
            "geometry_sha256": (hashlib.sha256(repr(sorted(geometry.items())).encode()).hexdigest()
                                if geometry else None),
            "references": _references(node.element),
        })
    by_id = {node["id"]: node for node in nodes}
    hierarchy = []
    references = []
    for node in nodes:
        if node["parent"] is not None:
            by_id[node["parent"]]["children"].append(node["id"])
            hierarchy.append({"from": node["parent"], "to": node["id"], "kind": "parent_child"})
        for reference in node["references"]:
            targets = xml_ids.get(reference["target_xml_id"], [])
            references.append({"from": node["id"], "to": targets[0] if len(targets) == 1 else None,
                               "kind": "svg_reference", **reference})
    duplicates = sorted(xml_id for xml_id, values in xml_ids.items() if len(values) > 1)
    return {"format": "svgpatchlab.scene-graph.v1", "root_id": "n0", "nodes": nodes,
            "duplicate_xml_ids": duplicates,
            "hierarchy_edges": hierarchy, "reference_edges": references}


def _records(svg):
    root = parse_svg(svg)
    indexed = index_tree(root)
    by_id = {node.node_id: node for node in indexed}
    children = {node.node_id: [] for node in indexed}
    for node in indexed:
        if node.parent_id is not None:
            children[node.parent_id].append(node.node_id)
    return root, by_id, children


def _numeric_distance(first, second):
    a = [float(value) for value in NUMBER.findall(first)]
    b = [float(value) for value in NUMBER.findall(second)]
    if len(a) != len(b) or NUMBER.sub("#", first) != NUMBER.sub("#", second):
        return 1.0
    if not a:
        return 0.0 if first == second else 1.0
    return min(1.0, sum(abs(x - y) / max(abs(x), abs(y), 1.0) for x, y in zip(a, b)) / len(a))


def _match_cost(source, target):
    a, b = source.element, target.element
    if local_name(a.tag) != local_name(b.tag):
        return math.inf
    aid, bid = a.attrib.get("id"), b.attrib.get("id")
    if aid and bid:
        if aid == bid:
            id_cost = -3.0
        else:
            return math.inf
    else:
        id_cost = 0.0
    keys = (set(a.attrib) | set(b.attrib)) - {"id"}
    attribute_cost = 0.0
    for key in keys:
        if key not in a.attrib or key not in b.attrib:
            attribute_cost += 0.8
        elif a.attrib[key] != b.attrib[key]:
            attribute_cost += 0.2 + 0.8 * _numeric_distance(a.attrib[key], b.attrib[key])
    first_text, second_text = (a.text or "").strip(), (b.text or "").strip()
    text_cost = 0.0 if first_text == second_text else 1.2 * (1 - SequenceMatcher(
        None, first_text, second_text).ratio())
    child_a = [local_name(item.tag) for item in list(a)]
    child_b = [local_name(item.tag) for item in list(b)]
    child_cost = 0.8 * (1 - SequenceMatcher(None, child_a, child_b).ratio())
    return max(0.0, id_cost + attribute_cost + text_cost + child_cost)


def _align(source_ids, target_ids, source_by_id, target_by_id, gap=2.5):
    rows, cols = len(source_ids), len(target_ids)
    dp = [[0.0] * (cols + 1) for _ in range(rows + 1)]
    step = [[None] * (cols + 1) for _ in range(rows + 1)]
    for i in range(1, rows + 1):
        dp[i][0] = i * gap; step[i][0] = "delete"
    for j in range(1, cols + 1):
        dp[0][j] = j * gap; step[0][j] = "insert"
    for i in range(1, rows + 1):
        for j in range(1, cols + 1):
            cost = _match_cost(source_by_id[source_ids[i - 1]], target_by_id[target_ids[j - 1]])
            choices = ((dp[i - 1][j] + gap, "delete"),
                       (dp[i][j - 1] + gap, "insert"),
                       (dp[i - 1][j - 1] + cost, "match"))
            dp[i][j], step[i][j] = min(choices, key=lambda item: item[0])
    matches = []
    i, j = rows, cols
    while i or j:
        action = step[i][j]
        if action == "match":
            source_id, target_id = source_ids[i - 1], target_ids[j - 1]
            if _match_cost(source_by_id[source_id], target_by_id[target_id]) < 2 * gap:
                matches.append((source_id, target_id))
            i -= 1; j -= 1
        elif action == "delete":
            i -= 1
        else:
            j -= 1
    return list(reversed(matches))


def correspond_svg_trees(source_svg: str, target_svg: str) -> TreeCorrespondence:
    """Establish source-to-target DOM correspondence without engineering-family assumptions."""
    _, source, source_children = _records(source_svg)
    _, target, target_children = _records(target_svg)
    if local_name(source["n0"].element.tag) != local_name(target["n0"].element.tag):
        raise ValueError("source and target roots have different element types")
    mapping = {"n0": "n0"}
    inverse = {"n0": "n0"}
    queue = [("n0", "n0")]
    while queue:
        source_parent, target_parent = queue.pop(0)
        pairs = _align(source_children[source_parent], target_children[target_parent], source, target)
        for source_id, target_id in pairs:
            if source_id in mapping or target_id in inverse:
                continue
            mapping[source_id] = target_id
            inverse[target_id] = source_id
            queue.append((source_id, target_id))
    return TreeCorrespondence(
        source_to_target=mapping,
        target_to_source=inverse,
        source_unmatched=tuple(node_id for node_id in source if node_id not in mapping),
        target_unmatched=tuple(node_id for node_id in target if node_id not in inverse),
    )


def derive_structural_patch(source_svg: str, target_svg: str) -> Patch:
    """Derive a generic tree patch, including insertions and explicit geometry replacement."""
    _, source, _ = _records(source_svg)
    _, target, _ = _records(target_svg)
    contact = correspond_svg_trees(source_svg, target_svg)
    mapping, inverse = contact.source_to_target, contact.target_to_source
    operations = []
    needs_v3 = False
    needs_v2 = False

    for source_id, target_id in mapping.items():
        first, second = source[source_id].element, target[target_id].element
        changed = {name: value for name, value in second.attrib.items()
                   if name not in {"d", "points"} and first.attrib.get(name) != value}
        removed = tuple(name for name in first.attrib
                        if name not in {"d", "points"} and name not in second.attrib)
        geometry = {name: value for name, value in second.attrib.items()
                    if name in {"d", "points"} and first.attrib.get(name) != value}
        removed_geometry = tuple(name for name in ("d", "points")
                                 if name in first.attrib and name not in second.attrib)
        if changed:
            operations.append(PatchOperation("set_attributes", (source_id,),
                                             tuple(sorted(changed.items()))))
        if removed:
            operations.append(PatchOperation("remove_attributes", (source_id,), names=removed))
        if geometry or removed_geometry:
            operations.append(PatchOperation("replace_geometry", (source_id,),
                                             tuple(sorted(geometry.items())), names=removed_geometry))
            needs_v3 = True
        if (first.text or "") != (second.text or ""):
            operations.append(PatchOperation("set_text", (source_id,), text=second.text or ""))
            needs_v2 = True

    # Removing only unmatched roots removes each unmatched descendant exactly once.
    removals = [node_id for node_id in contact.source_unmatched
                if source[node_id].parent_id in mapping]
    for node_id in sorted(removals, key=lambda item: source[item].depth, reverse=True):
        operations.append(PatchOperation("remove_element", (node_id,)))
        needs_v2 = True

    # Insert unmatched target roots at their final child index after removals.
    insertions = [node_id for node_id in contact.target_unmatched
                  if target[node_id].parent_id in inverse]
    insertions.sort(key=lambda item: (target[item].parent_id or "", target[item].child_index))
    for target_id in insertions:
        node = target[target_id]
        operations.append(PatchOperation(
            "insert_subtree", parent=inverse[node.parent_id], index=node.child_index,
            subtree=ET.tostring(node.element, encoding="unicode", short_empty_elements=True)))
        needs_v3 = True

    version = 3 if needs_v3 else 2 if needs_v2 else 1
    return Patch(tuple(operations), version=version)
