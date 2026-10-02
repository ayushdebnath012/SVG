"""Stream every generated SVG-edit row through parsing, patching and engineering verification."""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import json
from pathlib import Path

import engsvg_svg_edit as EDIT
from svgpatchlab.core.xml import normalized_tree, parse_svg


def audit(data: Path, out: Path, limit: int | None = None):
    counts = Counter()
    by_family = {}
    exceptions = []
    mismatches = []
    violations = []
    for shard in sorted(data.glob("tasks-*.jsonl.gz")):
        with gzip.open(shard, "rt", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row["task"] != "svg_edit":
                    continue
                counts["rows"] += 1
                family = by_family.setdefault(row["family"], Counter())
                family["rows"] += 1
                head, source = row["prompt"].split("\nCurrent SVG:\n", 1)
                request = head.split("Request: ", 1)[1]
                try:
                    result = EDIT.edit_svg(source, request)
                    exact = (normalized_tree(parse_svg(result["output_svg"])) ==
                             normalized_tree(parse_svg(row["target"])))
                    if exact:
                        counts["stored_target_exact"] += 1
                        family["stored_target_exact"] += 1
                    else:
                        mismatches.append({"id": row["id"], "family": row["family"],
                                           "request": request})
                    if result["edit_fidelity_pass"]:
                        counts["edit_fidelity_pass"] += 1
                        family["edit_fidelity_pass"] += 1
                    if result["engineering_check_pass"]:
                        counts["engineering_check_pass"] += 1
                        family["engineering_check_pass"] += 1
                    else:
                        violations.append({"id": row["id"], "family": row["family"],
                                           "request": request, "check": result["after_verification"]})
                    counts[result["status"]] += 1
                    family[result["status"]] += 1
                except Exception as exc:
                    counts["exceptions"] += 1
                    family["exceptions"] += 1
                    exceptions.append({"id": row["id"], "family": row["family"],
                                       "request": request,
                                       "error": f"{type(exc).__name__}: {exc}"})
                if counts["rows"] % 1000 == 0:
                    print(counts["rows"], dict(counts), flush=True)
                if limit and counts["rows"] >= limit:
                    break
        if limit and counts["rows"] >= limit:
            break
    summary = {
        "benchmark": "engsvg-svg2svg-full-dataset-audit-v1",
        "dataset": str(data),
        "counts": dict(counts),
        "by_family": {name: dict(value) for name, value in sorted(by_family.items())},
        "exceptions": exceptions,
        "stored_target_mismatches": mismatches,
        "engineering_violations": violations,
        "interpretation": ("Edit fidelity and stored-target equality test the SVG pipeline. The "
                           "engineering check separately reports whether the requested revision "
                           "satisfies the stated FEM equilibrium or plate-clearance criteria."),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    result = audit(args.data, args.out, args.limit)
    print(json.dumps({"counts": result["counts"]}, indent=2))
