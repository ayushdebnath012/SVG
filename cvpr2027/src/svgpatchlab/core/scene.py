from __future__ import annotations

import hashlib
from typing import Any

from .xml import index_tree, local_name, parse_svg


INHERITED_STYLE_ATTRIBUTES = {
    "color",
    "fill",
    "fill-opacity",
    "fill-rule",
    "font-family",
    "font-size",
    "opacity",
    "stroke",
    "stroke-dasharray",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-opacity",
    "stroke-width",
    "visibility",
}

HEAVY_ATTRIBUTES = {"d", "points"}


def _parse_style(value: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for declaration in value.split(";"):
        if ":" not in declaration:
            continue
        name, item = declaration.split(":", 1)
        if name.strip():
            result[name.strip()] = item.strip()
    return result


def build_scene(
    svg: str,
    visual_embeddings: dict[str, list[float]] | None = None,
    visual_stats: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a compact DOM skeleton without exposing path coordinate data.

    Pass visual_embeddings (node_id → vector) from the Plan A vision module
    to include per-node visual context in the returned scene. Pass
    visual_stats (node_id → stats dict from eval.render.node_visual_stats)
    to include a human-readable "visual" field per node instead.
    """
    root = parse_svg(svg)
    indexed = index_tree(root)
    resolved_by_id: dict[str, dict[str, str]] = {}
    nodes: list[dict[str, Any]] = []

    for node in indexed:
        element = node.element
        inherited = dict(resolved_by_id.get(node.parent_id or "", {}))
        direct_style = _parse_style(element.attrib.get("style", ""))
        for name in INHERITED_STYLE_ATTRIBUTES:
            if name in element.attrib:
                inherited[name] = element.attrib[name]
            if name in direct_style:
                inherited[name] = direct_style[name]
        resolved_by_id[node.node_id] = inherited

        attributes: dict[str, str] = {}
        geometry: dict[str, Any] = {}
        for name, value in element.attrib.items():
            if name in HEAVY_ATTRIBUTES:
                geometry[name] = {
                    "sha256": hashlib.sha256(value.encode()).hexdigest(),
                    "characters": len(value),
                }
            else:
                attributes[name] = value

        item: dict[str, Any] = {
            "id": node.node_id,
            "parent": node.parent_id,
            "depth": node.depth,
            "child_index": node.child_index,
            "tag": local_name(element.tag),
            "attributes": attributes,
        }
        if inherited:
            item["resolved_style"] = inherited
        if geometry:
            item["protected_geometry"] = geometry
        text = (element.text or "").strip()
        if text:
            item["text"] = text[:160]
        if visual_embeddings and node.node_id in visual_embeddings:
            item["visual_embedding"] = visual_embeddings[node.node_id]
        if visual_stats and node.node_id in visual_stats:
            item["visual"] = visual_stats[node.node_id]
        nodes.append(item)

    return {
        "format": "svgpatchlab.scene.v1",
        "root_id": "n0",
        "node_count": len(nodes),
        "nodes": nodes,
    }
