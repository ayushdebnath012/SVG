"""Recover engineering parameters from edited SVGs and rerun family verifiers.

This is an additional semantic check for the procedural cross-domain dataset.
It does not certify real-world engineering safety. The recovery is validated
against every generated gold drawing before model predictions are scored.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engsvg_crossdomain_dataset as data  # noqa: E402
import train_crossdomain_svg_patcher as train  # noqa: E402


NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def _svg_elements(svg: str) -> dict[str, ET.Element]:
    root = ET.fromstring(svg)
    result = {node.attrib["id"]: node for node in root.iter() if "id" in node.attrib}
    if len(result) != sum("id" in node.attrib for node in root.iter()):
        raise ValueError("duplicate SVG ids")
    return result


def _text(nodes: dict, name: str) -> str:
    return "".join(nodes[name].itertext()).strip()


def _numbers(text: str) -> list[float]:
    return [float(value) for value in re.findall(NUMBER, text)]


def _one_number(nodes: dict, name: str) -> float:
    values = _numbers(_text(nodes, name))
    if len(values) != 1:
        raise ValueError(f"expected one number in {name}: {values}")
    return values[0]


def recover(svg: str, source_model: dict) -> dict:
    """Read visible dimensions/values and key geometry from a generated drawing."""
    nodes = _svg_elements(svg)
    model = json.loads(json.dumps(source_model))
    family = model["family"]
    if family == "building_plan":
        model["width_mm"] = _one_number(nodes, "width-note")
        model["height_mm"] = _one_number(nodes, "depth-note")
        model["door_width_mm"] = _one_number(nodes, "door-note")
        scale = min(760 / model["width_mm"], 460 / model["height_mm"])
        model["partition_x_mm"] = (float(nodes["partition"].attrib["x1"]) - 120) / scale
        model["door_x_mm"] = (float(nodes["door-leaf"].attrib["x1"]) - 120) / scale
        model["left_room"] = _text(nodes, "left-room")
        model["right_room"] = _text(nodes, "right-room")
    elif family == "furniture_table":
        model["width_mm"] = _one_number(nodes, "width-note")
        model["height_mm"] = _one_number(nodes, "height-note")
        section = _numbers(_text(nodes, "section-note"))
        if len(section) != 3:
            raise ValueError("table section note has unexpected dimensions")
        model["top_depth_mm"], model["top_thickness_mm"], model["load_N"] = section
        scale = min(760 / model["width_mm"], 480 / model["height_mm"])
        model["leg_width_mm"] = float(nodes["left-leg"].attrib["width"]) / scale
        model["leg_inset_mm"] = (float(nodes["left-leg"].attrib["x"]) - 120) / scale
    elif family == "mechanical_part":
        size = _numbers(_text(nodes, "size-note"))
        hole = _numbers(_text(nodes, "hole-note"))
        slot = _numbers(_text(nodes, "slot-note"))
        if len(size) != 3 or len(hole) != 3 or len(slot) != 2 or hole[0] != 4:
            raise ValueError("mechanical dimension notes are incomplete")
        model["width_mm"], model["height_mm"], model["thickness_mm"] = size
        model["hole_diameter_mm"], model["hole_offset_mm"] = hole[1:]
        model["slot_length_mm"], model["slot_width_mm"] = slot
    elif family == "dc_circuit":
        model["voltage_V"] = _one_number(nodes, "voltage-note")
        model["resistor_power_rating_W"] = _one_number(nodes, "rating-note")
        labels = sorted((int(match.group(1)), name) for name in nodes
                        if (match := re.fullmatch(r"resistor-(\d+)-label", name)))
        if [index for index, _ in labels] != list(range(1, len(labels) + 1)) or not labels:
            raise ValueError("missing or nonsequential resistor labels")
        model["resistors_ohm"] = [_numbers(_text(nodes, name))[-1] for _, name in labels]
    elif family == "water_piping":
        model["length_m"] = _one_number(nodes, "length-note")
        model["diameter_mm"] = _one_number(nodes, "diameter-note")
        model["flow_m3_s"] = _one_number(nodes, "flow-note")
        labels = sorted((int(match.group(1)), name) for name in nodes
                        if (match := re.fullmatch(r"valve-(\d+)-label", name)))
        if [index for index, _ in labels] != list(range(1, len(labels) + 1)) or not labels:
            raise ValueError("missing or nonsequential valve labels")
        model["valve_K"] = [_one_number(nodes, name) for _, name in labels]
    else:
        raise ValueError(f"unsupported family {family}")
    for key, original in source_model.items():
        if isinstance(original, int) and isinstance(model[key], float) and abs(model[key] - round(model[key])) < 1e-5:
            model[key] = round(model[key])
        elif isinstance(original, list) and original and isinstance(original[0], int):
            model[key] = [round(value) if abs(value - round(value)) < 1e-5 else value
                          for value in model[key]]
    return model


def _equal(left, right) -> bool:
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_equal(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_equal(a, b) for a, b in zip(left, right))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(left - right) <= 1e-5 * max(1, abs(right))
    return left == right


def _changed_fields(found: dict, target: dict) -> list[str]:
    return [key for key in target if not _equal(found.get(key), target[key])]


def _attribute_close(left: str, right: str) -> bool:
    if left == right:
        return True
    left_parts = re.split(f"({NUMBER})", left)
    right_parts = re.split(f"({NUMBER})", right)
    return (len(left_parts) == len(right_parts) and all(
        _equal(float(a), float(b)) if index % 2 else a == b
        for index, (a, b) in enumerate(zip(left_parts, right_parts))))


def _drawing_close(left: str, right: str) -> bool:
    """Compare all geometry and markup, allowing only tiny numeric rounding."""
    a, b = ET.fromstring(left), ET.fromstring(right)
    def visit(x: ET.Element, y: ET.Element) -> bool:
        if x.tag != y.tag or x.attrib.keys() != y.attrib.keys():
            return False
        if (x.text or "").strip() != (y.text or "").strip():
            return False
        if not all(_attribute_close(x.attrib[key], y.attrib[key]) for key in x.attrib):
            return False
        return len(x) == len(y) and all(visit(xx, yy) for xx, yy in zip(x, y))
    return visit(a, b)


def score(predictions: Path, test: Path, output: Path) -> dict:
    rows = train.load_rows(test)
    by_id = {row["id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("duplicate test row ids")
    # Establish that recovery is accurate on the complete test set, including
    # the geometry fields that are not printed as note text.
    for row in rows:
        recovered = recover(row["target_svg"], row["source_model"])
        if not _equal(recovered, row["target_model"]):
            raise AssertionError(f"gold recovery failed for {row['id']}: {_changed_fields(recovered, row['target_model'])}")
        if not _drawing_close(row["target_svg"], data.BUILDERS[row["family"]][2](recovered)):
            raise AssertionError(f"gold geometry recovery failed for {row['id']}")

    records = []
    seen = set()
    with predictions.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            prediction = json.loads(line)
            row = by_id[prediction["id"]]
            if row["id"] in seen:
                raise ValueError(f"duplicate prediction {row['id']}")
            seen.add(row["id"])
            outcome = {"id": row["id"], "family": row["family"], "edit_kind": row["edit_kind"],
                       "target_tree_equal": prediction["metrics"]["target_tree_equal"],
                       "recovered": False, "model_equal": False, "drawing_consistent": False,
                       "engineering_equal": False, "verification_pass_equal": False,
                       "verification_report_equal": False,
                       "changed_fields": [], "error": None}
            if prediction["metrics"]["patch_valid"]:
                try:
                    patch = train.parse_patch(prediction["prediction"])
                    drawing = train.apply_patch(row["source_svg"], patch)
                    found = recover(drawing, row["source_model"])
                    checked = data.BUILDERS[row["family"]][3](found)
                    model_equal = _equal(found, row["target_model"])
                    drawing_consistent = _drawing_close(drawing, data.BUILDERS[row["family"]][2](found))
                    outcome.update(recovered=True, model_equal=model_equal,
                                   drawing_consistent=drawing_consistent,
                                   engineering_equal=model_equal and drawing_consistent,
                                   verification_pass_equal=checked["pass"] == row["after_verification"]["pass"],
                                   verification_report_equal=_equal(checked, row["after_verification"]),
                                   changed_fields=_changed_fields(found, row["target_model"]),
                                   predicted_verification=checked)
                except Exception as exc:
                    outcome["error"] = f"{type(exc).__name__}: {exc}"[:300]
            records.append(outcome)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "drawing-checks.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")

    def group(items):
        return {"n": len(items), "tree_equal": sum(r["target_tree_equal"] for r in items),
                "recovered": sum(r["recovered"] for r in items),
                "model_equal": sum(r["model_equal"] for r in items),
                "drawing_consistent": sum(r["drawing_consistent"] for r in items),
                "engineering_equal": sum(r["engineering_equal"] for r in items),
                "verification_pass_equal": sum(r["verification_pass_equal"] for r in items),
                "verification_report_equal": sum(r["verification_report_equal"] for r in items)}

    families = sorted({r["family"] for r in records})
    kinds = sorted({r["edit_kind"] for r in records})
    summary = {"gold_recovery_validated": len(rows), "scored": len(records),
               "overall": group(records),
               "by_family": {family: group([r for r in records if r["family"] == family]) for family in families},
               "by_edit_kind": {kind: group([r for r in records if r["edit_kind"] == kind]) for kind in kinds},
               "failed_fields": dict(sorted((key, count) for key, count in
                                             _field_counts(records).items()))}
    (output / "drawing-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def _field_counts(records):
    counts = defaultdict(int)
    for record in records:
        for field in record["changed_fields"]:
            counts[field] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--test", type=Path, default=Path("cvpr2027/data/engsvg-crossdomain-edit-v1/test.jsonl.gz"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(score(args.predictions, args.test, args.out), indent=2))


if __name__ == "__main__":
    main()
