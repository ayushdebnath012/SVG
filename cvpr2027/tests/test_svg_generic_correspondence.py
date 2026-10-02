from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from svgpatchlab.core import (  # noqa: E402
    Patch,
    PatchOperation,
    apply_patch,
    build_scene,
    build_scene_graph,
    correspond_svg_trees,
    derive_structural_patch,
    generic_svg_policy,
    parse_patch,
    validate_patch,
)
from svgpatchlab.core.patch import PatchError  # noqa: E402
from svgpatchlab.core.xml import normalized_tree, parse_svg  # noqa: E402


def _same(first, second):
    return normalized_tree(parse_svg(first)) == normalized_tree(parse_svg(second))


def _roundtrip(source, target):
    derived = derive_structural_patch(source, target)
    parsed = parse_patch(derived.to_json())
    validate_patch(parsed, build_scene(source), generic_svg_policy())
    output = apply_patch(source, parsed)
    assert _same(output, target)
    return parsed


def test_scene_graph_records_hierarchy_and_local_references():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg">
      <defs><marker id="arrow"><path d="M0 0 L5 2 L0 4 Z"/></marker></defs>
      <g id="loads"><line x1="0" y1="0" x2="20" y2="0" marker-end="url(#arrow)"/></g>
    </svg>'''
    scene = build_scene_graph(svg)
    assert scene["format"] == "svgpatchlab.scene-graph.v1"
    assert len(scene["hierarchy_edges"]) == len(scene["nodes"]) - 1
    reference = next(edge for edge in scene["reference_edges"] if edge["target_xml_id"] == "arrow")
    assert reference["to"] is not None


def test_building_edit_matches_text_replaces_path_and_inserts_door_subtree():
    source = '''<svg xmlns="http://www.w3.org/2000/svg"><g id="plan">
      <path id="wall" d="M0 0 H100 V80 H0 Z" fill="none" stroke="black"/>
      <text id="room" x="30" y="40">Office</text></g></svg>'''
    target = '''<svg xmlns="http://www.w3.org/2000/svg"><g id="plan">
      <path id="wall" d="M0 0 H120 V80 H0 Z" fill="none" stroke="black"/>
      <g id="door"><line x1="55" y1="80" x2="75" y2="80" stroke="white"/>
        <path d="M55 80 A20 20 0 0 1 75 60" fill="none" stroke="black"/></g>
      <text id="room" x="35" y="40">Laboratory</text></g></svg>'''
    patch = _roundtrip(source, target)
    assert patch.version == 3
    assert {operation.op for operation in patch.operations} >= {
        "replace_geometry", "insert_subtree", "set_text"
    }


def test_generic_roundtrip_across_engineering_drawing_types():
    cases = [
        (
            '<svg xmlns="http://www.w3.org/2000/svg"><g id="table"><rect id="top" x="0" y="0" width="100" height="10"/><rect id="leg-a" x="5" y="10" width="8" height="70"/></g></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><g id="table"><rect id="top" x="0" y="0" width="100" height="10"/><rect id="leg-a" x="5" y="10" width="8" height="70"/><rect id="leg-b" x="87" y="10" width="8" height="70"/></g></svg>',
        ),
        (
            '<svg xmlns="http://www.w3.org/2000/svg"><g id="circuit"><polyline id="wire" points="0,10 40,10 40,30" fill="none" stroke="black"/><text x="5" y="8">12 V</text></g></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><g id="circuit"><polyline id="wire" points="0,10 60,10 60,30" fill="none" stroke="black"/><text x="5" y="8">24 V</text></g></svg>',
        ),
        (
            '<svg xmlns="http://www.w3.org/2000/svg"><g id="pipe"><path id="run" d="M0 20 H80" fill="none" stroke="blue"/></g></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><g id="pipe"><path id="run" d="M0 20 H120" fill="none" stroke="blue"/><circle id="valve" cx="60" cy="20" r="5"/></g></svg>',
        ),
    ]
    for source, target in cases:
        _roundtrip(source, target)


def test_correspondence_survives_insertion_between_repeated_lines():
    source = '<svg xmlns="http://www.w3.org/2000/svg"><g><line id="a" x2="10"/><line id="b" x2="20"/></g></svg>'
    target = '<svg xmlns="http://www.w3.org/2000/svg"><g><line id="a" x2="10"/><line id="new" x2="15"/><line id="b" x2="20"/></g></svg>'
    contact = correspond_svg_trees(source, target)
    patch = _roundtrip(source, target)
    assert len(contact.target_unmatched) == 1
    assert [operation.op for operation in patch.operations] == ["insert_subtree"]


def test_multiple_insertions_and_deletion_preserve_final_order():
    source = '<svg xmlns="http://www.w3.org/2000/svg"><g><line id="old"/><circle id="keep"/></g></svg>'
    target = '<svg xmlns="http://www.w3.org/2000/svg"><g><rect id="first"/><text id="second">new</text><circle id="keep"/></g></svg>'
    patch = _roundtrip(source, target)
    assert [operation.op for operation in patch.operations].count("insert_subtree") == 2
    assert [operation.op for operation in patch.operations].count("remove_element") == 1


def test_inserted_script_subtree_is_rejected():
    source = '<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>'
    patch = Patch((PatchOperation("insert_subtree", parent="n0", index=0,
                                  subtree='<script xmlns="http://www.w3.org/2000/svg">bad()</script>'),),
                  version=3)
    try:
        validate_patch(patch, build_scene(source))
    except PatchError:
        return
    raise AssertionError("unsafe inserted subtree was accepted")


def test_scene_graph_rejects_active_or_external_content():
    unsafe = [
        '<svg xmlns="http://www.w3.org/2000/svg"><script>bad()</script></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.com/a.png"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><rect onclick="bad()"/></svg>',
    ]
    for svg in unsafe:
        try:
            build_scene_graph(svg)
        except ValueError:
            continue
        raise AssertionError("unsafe SVG content was accepted")


def test_generic_policy_allows_drafting_text_and_local_marker_changes():
    source = '''<svg xmlns="http://www.w3.org/2000/svg"><defs>
      <marker id="arrow"><path d="M0 0 L5 2 L0 4 Z"/></marker></defs>
      <line x1="0" y1="0" x2="20" y2="0"/>
      <text x="0" y="10" font-size="8">10 mm</text></svg>'''
    target = '''<svg xmlns="http://www.w3.org/2000/svg"><defs>
      <marker id="arrow"><path d="M0 0 L5 2 L0 4 Z"/></marker></defs>
      <line x1="0" y1="0" x2="20" y2="0" marker-end="url(#arrow)" stroke-dasharray="2 1"/>
      <text x="0" y="10" font-size="10" text-anchor="middle">10 mm</text></svg>'''
    _roundtrip(source, target)


def test_generic_policy_rejects_external_marker_reference():
    source = '<svg xmlns="http://www.w3.org/2000/svg"><line/></svg>'
    target = '<svg xmlns="http://www.w3.org/2000/svg"><line marker-end="url(https://example.com/a.svg#x)"/></svg>'
    patch = derive_structural_patch(source, target)
    try:
        validate_patch(patch, build_scene(source), generic_svg_policy())
    except PatchError:
        return
    raise AssertionError("external marker reference was accepted")
