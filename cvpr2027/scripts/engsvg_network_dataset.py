"""Build the circuit and pipe-network SVG edit dataset whose physics is re-solved from the drawings.

Rows use the cross-domain v1 schema, so the same trainer reads them. The difference is where the
verification comes from: every before/after report is produced by recovering the network from
the rendered SVG (geometry and text only) and solving that, and a row is written only when the
recovered network equals the parametric model it was drawn from.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from svgpatchlab.core import (  # noqa: E402
    apply_patch,
    build_scene,
    build_scene_graph,
    derive_structural_patch,
    generic_svg_policy,
    parse_patch,
    validate_patch,
)
from svgpatchlab.core.xml import normalized_tree, parse_svg  # noqa: E402

import engsvg_networks as networks  # noqa: E402
from engsvg_crossdomain_dataset import _canonical, _render_png, _sha, _write_jsonl_gz  # noqa: E402


VERSION = "engsvg-network-edit-v1"
SEED = 260927
DESIGNS_PER_FAMILY = 1250
EDITS_PER_DESIGN = 4
FAMILIES = tuple(networks.FAMILIES)
HARDY_CROSS_LIMIT_M3_S = 1e-9


def _report(family: str, svg: str, model: dict) -> dict:
    report = networks.FAMILIES[family][3](svg, model)
    if not report["recovered_matches_model"]:
        raise AssertionError(f"{family}: drawing does not recover to its model")
    if family == "pipe_network" and report["hardy_cross_max_flow_gap_m3_s"] > HARDY_CROSS_LIMIT_M3_S:
        raise AssertionError("Newton and Hardy Cross disagree")
    return report


def _make_row(family: str, split: str, design_index: int, edit_index: int, source: dict,
              target: dict, instruction: str, edit_kind: str) -> dict:
    render = networks.FAMILIES[family][2]
    source_svg, target_svg = render(source), render(target)
    build_scene_graph(source_svg)
    build_scene_graph(target_svg)
    patch = parse_patch(derive_structural_patch(source_svg, target_svg).to_json())
    validate_patch(patch, build_scene(source_svg), generic_svg_policy(max_operations=500))
    edited = apply_patch(source_svg, patch)
    exact = normalized_tree(parse_svg(edited)) == normalized_tree(parse_svg(target_svg))
    scene = build_scene_graph(edited)
    dangling = [edge for edge in scene["reference_edges"] if edge["to"] is None]
    if not exact or dangling or scene["duplicate_xml_ids"]:
        raise AssertionError(f"unverified patch for {family}-{design_index}-{edit_index}")
    before, after = _report(family, source_svg, source), _report(family, edited, target)
    digest = _sha(_canonical(source))
    lineage = f"net-{family}-{digest[:16]}"
    prompt = ("Edit the engineering SVG according to the instruction. Return only an SVGPatchLab patch JSON.\n"
              f"Instruction: {instruction}\nSource SVG:\n{source_svg}")
    return {
        "version": VERSION,
        "id": f"{lineage}:edit-{edit_index}",
        "lineage_id": lineage,
        "family": family,
        "split": split,
        "edit_kind": edit_kind,
        "instruction": instruction,
        "prompt": prompt,
        "source_svg": source_svg,
        "target_svg": target_svg,
        "target_patch": patch.to_dict(),
        "source_model": source,
        "target_model": target,
        "before_verification": before,
        "after_verification": after,
        "engineering_status": "verified_safe" if after["pass"] else "verified_with_violations",
        "verdict_changed": before["pass"] != after["pass"],
        "physics_from_drawing": True,
        "patch_verified": True,
        "target_tree_equal": True,
        "source_sha256": _sha(source_svg),
        "target_sha256": _sha(target_svg),
        "patch_operation_types": [operation.op for operation in patch.operations],
    }


def dataset(designs_per_family: int = DESIGNS_PER_FAMILY, seed: int = SEED):
    rng = random.Random(seed)
    rows = {"train": [], "validation": [], "test": []}
    seen = set()
    for family in FAMILIES:
        make_model, make_edits = networks.FAMILIES[family][:2]
        train_end, validation_end = int(designs_per_family * .8), int(designs_per_family * .9)
        for design_index in range(designs_per_family):
            split = ("train" if design_index < train_end else
                     "validation" if design_index < validation_end else "test")
            while True:
                source = make_model(rng, design_index)
                digest = _sha(_canonical(source))
                if digest not in seen:
                    seen.add(digest)
                    break
            edits = make_edits(source, rng)
            if len(edits) != EDITS_PER_DESIGN:
                raise AssertionError("each design must supply four edit tasks")
            for edit_index, (instruction, target, kind) in enumerate(edits, 1):
                rows[split].append(_make_row(family, split, design_index, edit_index, source, target,
                                             instruction, kind))
        print(family, "done", flush=True)
    for split in rows:
        rng.shuffle(rows[split])
    return rows


def _write_samples(out: Path, rows: dict, per_family: int = 4) -> tuple[int, int]:
    sample_dir = out / "samples"
    sample_dir.mkdir()
    candidates = rows["test"] + rows["validation"]
    chosen = []
    for family in FAMILIES:
        kinds_seen, picked = set(), []
        for row in candidates:
            if row["family"] == family and row["edit_kind"] not in kinds_seen:
                kinds_seen.add(row["edit_kind"])
                picked.append(row)
            if len(picked) == per_family:
                break
        chosen.extend(picked)
    pngs = 0
    for row in chosen:
        stem = row["id"].replace(":", "-")
        for side in ("source", "target"):
            svg_path = sample_dir / f"{stem}-{side}.svg"
            png_path = sample_dir / f"{stem}-{side}.png"
            svg_path.write_text(row[f"{side}_svg"])
            if _render_png(svg_path, png_path):
                pngs += 1
        (sample_dir / f"{stem}-record.json").write_text(json.dumps(
            {key: row[key] for key in ("id", "family", "edit_kind", "instruction", "engineering_status",
                                       "target_patch", "before_verification", "after_verification")},
            indent=2, ensure_ascii=False) + "\n")
    return len(chosen) * 2, pngs


def build(out: Path, designs_per_family: int = DESIGNS_PER_FAMILY, seed: int = SEED) -> dict:
    if out.exists() and any(out.iterdir()):
        raise ValueError("output directory is not empty; dataset versions are immutable")
    out.mkdir(parents=True, exist_ok=True)
    controls = networks.controls()
    if not all(row["pass"] for row in controls):
        raise AssertionError("analytical controls failed; refusing to build")
    rows = dataset(designs_per_family, seed)
    for split, items in rows.items():
        _write_jsonl_gz(out / f"{split}.jsonl.gz", items)
    svg_samples, png_samples = _write_samples(out, rows)
    all_rows = sum(rows.values(), [])
    groups = {split: {row["lineage_id"] for row in items} for split, items in rows.items()}
    if any(groups[a] & groups[b] for a in groups for b in groups if a < b):
        raise AssertionError("source lineage leaked across dataset splits")

    def count(key):
        result = {}
        for row in all_rows:
            for value in (row[key] if isinstance(row[key], list) else [row[key]]):
                result[value] = result.get(value, 0) + 1
        return dict(sorted(result.items()))

    loops = {family: sorted(row["before_verification"]["independent_loops"] for row in all_rows
                            if row["family"] == family and row["id"].endswith("edit-1")) for family in FAMILIES}
    summary = {
        "version": VERSION, "seed": seed,
        "source_designs": len({row["lineage_id"] for row in all_rows}),
        "edit_examples": len(all_rows), "families": list(FAMILIES),
        "family_counts": count("family"), "edit_kind_counts": count("edit_kind"),
        "split_examples": {split: len(items) for split, items in rows.items()},
        "split_source_designs": {split: len(groups[split]) for split in groups},
        "lineage_overlap_between_splits": 0,
        "exact_patch_roundtrips": sum(row["target_tree_equal"] for row in all_rows),
        "drawings_recovered_to_model": 2 * len(all_rows),
        "verified_safe": sum(row["engineering_status"] == "verified_safe" for row in all_rows),
        "verified_with_violations": sum(row["engineering_status"] == "verified_with_violations" for row in all_rows),
        "edits_that_change_the_verdict": sum(row["verdict_changed"] for row in all_rows),
        "patch_operation_coverage": {name: sum(name in row["patch_operation_types"] for row in all_rows)
                                     for name in sorted({op for row in all_rows for op in row["patch_operation_types"]})},
        "independent_loops_per_design": {family: {"min": values[0], "median": values[len(values) // 2],
                                                  "max": values[-1]} for family, values in loops.items()},
        "max_hardy_cross_gap_m3_s": max(row[side]["hardy_cross_max_flow_gap_m3_s"] for row in all_rows
                                        if row["family"] == "pipe_network"
                                        for side in ("before_verification", "after_verification")),
        "max_kcl_residual_A": max(row[side]["kcl_residual_A"] for row in all_rows if row["family"] == "dc_network"
                                  for side in ("before_verification", "after_verification")),
        "analytical_controls": controls,
        "sample_svgs": svg_samples, "sample_pngs": png_samples,
        "training_objective": "source SVG + natural-language instruction -> constrained patch JSON",
        "scoring": ("apply the predicted patch, recover the network from the edited drawing with "
                    "engsvg_networks.physics_match, and compare its solution with the target design"),
        "claim_boundary": ("procedural 2D schematics with idealised steady-state DC and pipe-flow checks; "
                           "not electrical or water-supply approval"),
    }
    (out / "dataset-summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    (out / "README.md").write_text(
        "# Circuit and pipe-network SVG edit dataset v1\n\n"
        "Resistor networks (bridges, ladders, one or two sources) and looped water-distribution networks "
        "(one or two reservoirs, tees, elbows, dead ends), each with four text-guided edits. Every row has "
        "the source SVG, instruction, target SVG, a gold patch that reproduces the target exactly, and "
        "before/after engineering reports.\n\n"
        "The reports are computed from the drawings, not from parameters: `scripts/engsvg_networks.py` "
        "reads wire and pipe endpoints, T-junctions and junction dots into nodes, reads component values "
        "from the labels, and solves the result (nodal analysis for circuits; Newton on flows and heads "
        "with Darcy-Weisbach/Churchill losses for pipes, cross-checked by Hardy Cross). A row is kept only "
        "if both drawings recover to the model they were drawn from.\n\n"
        "Score a model's patch with `engsvg_networks.physics_match(edited_svg, family, target_model)`: "
        "a drawing that differs in markup but describes the same network still scores as correct.\n")
    files = sorted(path for path in out.rglob("*") if path.is_file())
    manifest = {path.relative_to(out).as_posix(): _sha(path.read_bytes()) for path in files}
    (out / "sha256-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--designs-per-family", type=int, default=DESIGNS_PER_FAMILY)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    summary = build(args.out, args.designs_per_family, args.seed)
    print(json.dumps({k: v for k, v in summary.items() if k != "analytical_controls"}, indent=2, ensure_ascii=False))
