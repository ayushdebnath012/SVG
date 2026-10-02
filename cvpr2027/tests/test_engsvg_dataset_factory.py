import gzip
import hashlib
import json
import xml.etree.ElementTree as ET

import engsvg_dataset_factory as factory


def test_small_factory_dataset_is_complete_and_lineage_safe(tmp_path):
    summary = factory.generate(tmp_path, designs=40, seed=31, previous=None)
    assert summary["designs"] == 40
    assert summary["tasks"] == 560
    assert summary["split_designs"] == {"train": 32, "validation": 4, "test": 4}
    assert summary["split_tasks"] == {"train": 448, "validation": 56, "test": 56}
    assert summary["task_counts"] == {
        "clarify": 40, "constraint_edit": 40, "edit_action": 160, "engineering_analysis": 40,
        "reject": 40, "svg_edit": 160, "svg_to_ir": 40, "text_to_svg": 40,
    }
    assert summary["rows_with_svg_in_prompt"] == 520
    assert summary["rows_with_full_svg_target"] == 200
    rows = []
    for path in tmp_path.glob("tasks-*.jsonl.gz"):
        with gzip.open(path, "rt") as handle: rows.extend(json.loads(line) for line in handle)
    lineage_splits = {}
    for row in rows:
        lineage_splits.setdefault(row["lineage_id"], set()).add(row["split"])
        assert row["prompt_contains_svg"] == ("<svg" in row["prompt"])
        assert row["target_contains_svg"] == (row["target_format"] == "svg")
        if row["target_format"] == "svg":
            assert ET.fromstring(row["target"]).tag.endswith("svg")
        else:
            assert json.loads(row["target"])
    assert all(len(splits) == 1 for splits in lineage_splits.values())


def test_manifest_and_assets_are_valid(tmp_path):
    summary = factory.generate(tmp_path, designs=8, seed=9, previous=None)
    manifest = json.loads((tmp_path / "sha256-manifest.json").read_text())
    assert all(hashlib.sha256((tmp_path/name).read_bytes()).hexdigest() == digest
               for name, digest in manifest.items())
    assets = []
    for path in tmp_path.glob("assets-*.jsonl.gz"):
        with gzip.open(path, "rt") as handle: assets.extend(json.loads(line) for line in handle)
    assert len(assets) == 8
    assert all(len(asset["svg_variants"]) == 3 for asset in assets)
    assert all(asset["verification"]["method"] in
               {"linear_axial_truss_fem", "manufacturing_geometry_checks"} for asset in assets)
    assert all(asset["canonical_roundtrip_verified"] for asset in assets)
    assert summary["review_sample_svgs"] == 8
    assert len(list((tmp_path / "samples").glob("*.svg"))) == 8
    assert (tmp_path / "sample-gallery.html").exists()
    assert summary["overlap_with_excluded"] == 0
