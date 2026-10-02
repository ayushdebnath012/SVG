from __future__ import annotations

import sys
import pytest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import engsvg_plate as PLATE  # noqa: E402
import engsvg_svg_edit as EDIT  # noqa: E402
import engsvg_truss as TRUSS  # noqa: E402
import engsvg_truss_families as BRIDGE  # noqa: E402


def test_truss_text_edit_is_patched_and_fem_checked():
    model = TRUSS.example_model()
    before = TRUSS.solve(model)["peak_abs_stress_mpa"]
    result = EDIT.edit_svg(TRUSS.render(model), "Set every member depth to 40 mm.")
    assert result["status"] == "verified_safe"
    assert result["mode"] == "tree_patch"
    assert result["patch_operation_types"] == ["set_text"]
    assert abs(result["after_verification"]["peak_abs_stress_mpa"] - before / 2) < 1e-8


def test_blueprint_plate_geometry_edit_is_recovered_and_checked():
    source = EDIT._apply_style(PLATE.render(PLATE.example_model()), "blueprint")
    result = EDIT.edit_svg(source, "Increase all hole diameters by 4 mm.")
    assert result["status"] == "verified_safe"
    assert result["style"] == "blueprint"
    assert result["after_verification"]["method"] == "manufacturing_geometry_checks"
    assert result["after_verification"]["pass"]


def test_faithful_plate_edit_reports_engineering_violation_separately():
    model = PLATE.example_model()
    for hole, center in zip(model["holes"], ((20, 20), (280, 20), (20, 180), (280, 180))):
        hole["center_mm"] = list(center)
        hole["diameter_mm"] = 10
    next(item for item in model["dimensions"] if item["id"] == "edge_offset")["value_mm"] = 20
    next(item for item in model["dimensions"] if item["id"] == "hole_diameter")["value_mm"] = 10
    result = EDIT.edit_svg(PLATE.render(model), "Increase all hole diameters by 4 mm.")
    assert result["status"] == "verified_with_violations"
    assert result["edit_fidelity_pass"]
    assert not result["engineering_check_pass"]
    assert result["after_verification"]["violations"]


def test_bridge_load_edit_patches_and_resolves_actual_output():
    model, _ = BRIDGE.build("pratt", panels=6)
    before = TRUSS.solve(model)["peak_abs_stress_mpa"]
    result = EDIT.edit_svg(BRIDGE.render(model), "Double the downward load.")
    assert result["status"] == "verified_safe"
    assert result["mode"] == "tree_patch"
    assert abs(result["after_verification"]["peak_abs_stress_mpa"] - before * 2) < 1e-7


@pytest.mark.parametrize("panels", [4, 8])
def test_bridge_panel_edit_applies_parsed_structural_patch_and_fem(panels):
    model, _ = BRIDGE.build("pratt", panels=6)
    result = EDIT.edit_svg(BRIDGE.render(model), f"Change the bridge to {panels} panels.")
    assert result["status"] == "verified_safe"
    assert result["mode"] == "structural_tree_patch"
    assert result["patch"]["version"] == 3
    assert ("insert_subtree" if panels > 6 else "remove_element") in result["patch_operation_types"]
    from svgpatchlab.core import apply_patch, parse_patch, validate_patch, build_scene, generic_svg_policy
    from svgpatchlab.core.xml import normalized_tree, parse_svg
    import json
    patch = parse_patch(json.dumps(result["patch"]))
    source = BRIDGE.render(model)
    validate_patch(patch, build_scene(source), generic_svg_policy())
    replayed = apply_patch(source, patch)
    assert normalized_tree(parse_svg(replayed)) == normalized_tree(parse_svg(result["output_svg"]))
    assert result["after_verification"]["method"] == "linear_axial_truss_fem"
    assert result["after_verification"]["pass"]
