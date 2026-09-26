from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import engsvg_crossdomain_dataset as dataset  # noqa: E402


def test_small_dataset_has_real_svg_patches_verifiers_and_disjoint_lineages():
    splits = dataset.dataset(designs_per_family=10, seed=7)
    assert {name: len(rows) for name, rows in splits.items()} == {
        "train": 160, "validation": 20, "test": 20,
    }
    all_rows = sum(splits.values(), [])
    assert len(all_rows) == 200
    assert {row["family"] for row in all_rows} == set(dataset.FAMILIES)
    assert all(row["source_svg"].startswith("<svg") for row in all_rows)
    assert all(row["target_svg"].startswith("<svg") for row in all_rows)
    assert all(row["target_patch"]["operations"] for row in all_rows)
    assert all(row["patch_verified"] and row["target_tree_equal"] for row in all_rows)
    groups = {name: {row["lineage_id"] for row in rows} for name, rows in splits.items()}
    assert groups["train"].isdisjoint(groups["validation"])
    assert groups["train"].isdisjoint(groups["test"])
    assert groups["validation"].isdisjoint(groups["test"])


def test_dataset_covers_topology_geometry_text_and_family_specific_checks():
    rows = sum(dataset.dataset(designs_per_family=2, seed=11).values(), [])
    operations = {operation for row in rows for operation in row["patch_operation_types"]}
    assert {"set_attributes", "set_text", "replace_geometry", "insert_subtree"} <= operations
    methods = {row["after_verification"]["method"] for row in rows}
    assert methods == {
        "building_plan_geometry_and_clearance_rules",
        "beam_bending_and_euler_buckling",
        "manufacturing_feature_geometry",
        "dc_series_kcl_kvl_and_power",
        "darcy_weisbach_continuity_and_minor_losses",
    }


def test_build_writes_reproducible_gzip_splits_and_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(dataset, "CHROME", tmp_path / "missing-chrome")
    summary = dataset.build(tmp_path / "data", designs_per_family=2, seed=19)
    assert summary["edit_examples"] == 40
    assert summary["rows_with_source_svg"] == 40
    assert summary["rows_with_target_svg"] == 40
    assert summary["exact_patch_roundtrips"] == 40
    with gzip.open(tmp_path / "data" / "train.jsonl.gz", "rt") as handle:
        row = json.loads(next(handle))
    assert row["source_svg"].startswith("<svg")
    assert row["target_patch"]["version"] in (1, 2, 3)
    manifest = json.loads((tmp_path / "data" / "sha256-manifest.json").read_text())
    for name, expected in manifest.items():
        assert hashlib.sha256((tmp_path / "data" / name).read_bytes()).hexdigest() == expected
