from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from svgpatchlab.core import apply_patch, build_scene, derive_patch, validate_patch  # noqa: E402
from svgpatchlab.core.patch import PatchError, parse_patch  # noqa: E402
from svgpatchlab.core.xml import normalized_tree, parse_svg  # noqa: E402


SOURCE = '<svg xmlns="http://www.w3.org/2000/svg"><text x="0" y="10">Depth: 20 mm</text></svg>'
TARGET = '<svg xmlns="http://www.w3.org/2000/svg"><text x="0" y="10">Depth: 40 mm</text></svg>'


def test_text_patch_survives_json_parse_validate_and_apply():
    derived = derive_patch(SOURCE, TARGET)
    assert derived.version == 2
    assert [operation.op for operation in derived.operations] == ["set_text"]
    parsed = parse_patch(derived.to_json())
    validate_patch(parsed, build_scene(SOURCE))
    output = apply_patch(SOURCE, parsed)
    assert normalized_tree(parse_svg(output)) == normalized_tree(parse_svg(TARGET))


def test_text_patch_rejects_non_text_target():
    raw = '{"version":2,"operations":[{"op":"set_text","targets":["n0"],"text":"bad"}]}'
    patch = parse_patch(raw)
    try:
        validate_patch(patch, build_scene(SOURCE))
    except PatchError:
        return
    raise AssertionError("set_text accepted a non-text SVG node")
