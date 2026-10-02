"""Make an SVG-ID-blinded network evaluation set without changing the drawing.

The same per-row substitution is applied to source and target. Gold patches are
re-derived and checked after substitution; visible text and geometry stay intact.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from svgpatchlab.core import apply_patch, build_scene, derive_structural_patch, generic_svg_policy, validate_patch
from svgpatchlab.core.xml import normalized_tree, parse_svg
import engsvg_networks as networks

ID = re.compile(r'(?<![\w:-])id="([^"]+)"')


def blind(row: dict, seed: int) -> dict:
    ids = sorted(set(ID.findall(row["source_svg"])) | set(ID.findall(row["target_svg"])))
    rng = random.Random(f"{seed}:{row['id']}")
    shuffled = list(range(len(ids)))
    rng.shuffle(shuffled)
    mapping = {old: f"e{shuffled[i]:04d}" for i, old in enumerate(ids)}

    def replace(svg: str) -> str:
        return ID.sub(lambda match: f'id="{mapping[match.group(1)]}"', svg)

    result = dict(row)
    result["source_svg"] = replace(row["source_svg"])
    result["target_svg"] = replace(row["target_svg"])
    result["prompt"] = row["prompt"].replace(row["source_svg"], result["source_svg"])
    assert result["prompt"] != row["prompt"]
    assert ID.sub('id=""', result["source_svg"]) == ID.sub('id=""', row["source_svg"])
    assert ID.sub('id=""', result["target_svg"]) == ID.sub('id=""', row["target_svg"])
    patch = derive_structural_patch(result["source_svg"], result["target_svg"])
    validate_patch(patch, build_scene(result["source_svg"]), generic_svg_policy(max_operations=500))
    edited = apply_patch(result["source_svg"], patch)
    assert normalized_tree(parse_svg(edited)) == normalized_tree(parse_svg(result["target_svg"]))
    match = networks.physics_match(edited, result["family"], result["target_model"])
    assert match.get("topology_equal") and match["physics_equal"]
    result["target_patch"] = patch.to_dict()
    result["source_sha256"] = hashlib.sha256(result["source_svg"].encode()).hexdigest()
    result["target_sha256"] = hashlib.sha256(result["target_svg"].encode()).hexdigest()
    result["id_blinding"] = {"seed": seed, "method": "per-row random opaque IDs"}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20270930)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    output = args.out / "test.jsonl.gz"
    count = 0
    with gzip.open(args.source, "rt", encoding="utf-8") as source, output.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8") as dest:
                for line in source:
                    if args.limit and count >= args.limit:
                        break
                    dest.write(json.dumps(blind(json.loads(line), args.seed), separators=(",", ":")) + "\n")
                    count += 1
    summary = {"source": str(args.source), "output": str(output), "seed": args.seed,
               "rows": count, "gold_patch_roundtrips": count, "gold_physics_matches": count,
               "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
               "content_sha256": hashlib.sha256(gzip.decompress(output.read_bytes())).hexdigest()}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
