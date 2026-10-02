import json

import engsvg_multifamily_train as train


def test_dataset_is_group_disjoint_and_excludes_frozen_benchmark():
    splits, heldout = train.dataset()
    groups = {name: {row["group"] for row in rows} for name, rows in splits.items()}
    assert {name: len(rows) for name, rows in splits.items()} == {
        "train": 8000, "validation": 1000, "test": 1000,
    }
    assert groups["train"].isdisjoint(groups["validation"])
    assert groups["train"].isdisjoint(groups["test"])
    assert groups["validation"].isdisjoint(groups["test"])
    assert not set.union(*groups.values()) & heldout

    rows = sum(splits.values(), [])
    assert len({row["group"] for row in rows}) == 2000
    assert {kind: sum(row["kind"] == kind for row in rows)
            for kind in ("edit", "clarify", "reject")} == {
                "edit": 8000, "clarify": 1000, "reject": 1000,
            }
    assert all(json.loads(row["target"])["action"] == row["kind"] for row in rows)


def test_hidden_benchmark_prompts_use_source_state():
    rows = {row["id"]: row for row in train._benchmark_rows()}
    assert len(rows) == 100
    # truss-01 starts at 10,000 N; its target is 11,000 N. The prompt state must
    # contain the former, otherwise the benchmark gives the model its answer.
    row = rows["truss-edit-001"]
    assert '"downward_load_N":10000' in row["prompt"]
    assert json.loads(row["target"])["changes"]["loads.C.fy_N"] == -11000


def test_prepare_writes_reproducible_manifest(tmp_path):
    summary = train.prepare(tmp_path)
    assert summary["heldout_source_overlap"] == 0
    assert summary["counts"]["train"]["total"] == 8000
    manifest = json.loads((tmp_path / "sha256-manifest.json").read_text())
    assert set(manifest) == {
        "dataset-summary.json", "train.jsonl", "validation.jsonl", "test.jsonl",
    }
