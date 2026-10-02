"""Apply a domain-independent, parsed SVG tree edit from a source and proposed target SVG."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from svgpatchlab.core import (  # noqa: E402
    apply_patch,
    build_scene,
    build_scene_graph,
    correspond_svg_trees,
    derive_structural_patch,
    generic_svg_policy,
    parse_patch,
    validate_patch,
)
from svgpatchlab.core.xml import normalized_tree, parse_svg  # noqa: E402


def edit_to_target(source_svg: str, target_svg: str):
    source_scene = build_scene_graph(source_svg)
    target_scene = build_scene_graph(target_svg)
    contact = correspond_svg_trees(source_svg, target_svg)
    derived = derive_structural_patch(source_svg, target_svg)
    patch = parse_patch(derived.to_json())
    validate_patch(patch, build_scene(source_svg), generic_svg_policy())
    output = apply_patch(source_svg, patch)
    output_scene = build_scene_graph(output)
    exact = normalized_tree(parse_svg(output)) == normalized_tree(parse_svg(target_svg))
    dangling = [edge for edge in output_scene["reference_edges"] if edge["to"] is None]
    duplicate_ids = output_scene["duplicate_xml_ids"]
    return {
        "status": "verified" if exact and not dangling and not duplicate_ids else "failed",
        "target_tree_equal": exact,
        "dangling_reference_count": len(dangling),
        "duplicate_xml_ids": duplicate_ids,
        "source_nodes": len(source_scene["nodes"]),
        "target_nodes": len(target_scene["nodes"]),
        "matched_nodes": len(contact.source_to_target),
        "removed_source_nodes": len(contact.source_unmatched),
        "inserted_target_nodes": len(contact.target_unmatched),
        "patch_version": patch.version,
        "patch_operation_count": len(patch.operations),
        "patch_operation_types": [operation.op for operation in patch.operations],
        "patch": patch.to_dict(),
        "correspondence": {
            "source_to_target": contact.source_to_target,
            "source_unmatched": contact.source_unmatched,
            "target_unmatched": contact.target_unmatched,
        },
        "source_scene": source_scene,
        "target_scene": target_scene,
        "output_scene": output_scene,
        "output_svg": output,
    }


def save(source: Path, target: Path, out: Path):
    result = edit_to_target(source.read_text(), target.read_text())
    out.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "source.svg": source.read_text(),
        "proposed-target.svg": target.read_text(),
        "edited.svg": result.pop("output_svg"),
        "patch.json": json.dumps(result.pop("patch"), indent=2) + "\n",
        "correspondence.json": json.dumps(result.pop("correspondence"), indent=2) + "\n",
        "source-scene.json": json.dumps(result.pop("source_scene"), indent=2) + "\n",
        "target-scene.json": json.dumps(result.pop("target_scene"), indent=2) + "\n",
        "output-scene.json": json.dumps(result.pop("output_scene"), indent=2) + "\n",
    }
    for name, content in artifacts.items():
        (out / name).write_text(content)
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    manifest = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(out.iterdir()) if path.is_file() and path.name != "sha256-manifest.json"}
    (out / "sha256-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(save(args.source, args.target, args.out), indent=2))
