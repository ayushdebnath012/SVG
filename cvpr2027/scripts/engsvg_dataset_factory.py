"""Generate a sharded, lineage-safe multi-task engineering-SVG dataset."""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import shutil

import engsvg_ir as IR
import engsvg_multifamily_benchmark as BENCH
import engsvg_plate as plate
import engsvg_truss as truss


VERSION = "engsvg-dataset-factory-v2"
SEED = 260925
TASKS_PER_DESIGN = 14


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha(value):
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


def _dimension(model, name):
    return next(item for item in model["dimensions"] if item["id"] == name)


def _provenance():
    return {"mode": "procedural", "confidence": {}, "evidence": {}, "ambiguities": []}


def _truss_model(rng, topology):
    span = rng.randrange(3000, 6001, 100)
    height = rng.randrange(800, 2001, 50)
    model = truss.example_model()
    model["nodes"] = {"A": [0, 0], "B": [span / 4, 0], "C": [span / 2, height],
                      "D": [3 * span / 4, 0], "E": [span, 0]}
    if topology == "double_fan_6":
        model["nodes"]["F"] = [span / 2, 0]
        names = ("AB", "BF", "FD", "DE", "AC", "BC", "CF", "CD", "CE")
        model["members"] = [{"id": name, "a": name[0], "b": name[1],
                             "section": "bar", "material": "steel"} for name in names]
    model["materials"]["steel"]["E_mpa"] = rng.choice([69000, 70000, 190000, 200000, 205000, 210000])
    model["sections"]["bar"]["b_mm"] = rng.randrange(20, 66, 5)
    model["sections"]["bar"]["h_mm"] = rng.randrange(15, 56, 5)
    model["loads"]["C"][1] = -rng.randrange(5000, 40001, 250)
    _dimension(model, "span")["value_mm"] = span
    _dimension(model, "height")["value_mm"] = height
    model["provenance"] = _provenance()
    return IR.validate(model)


def _plate_model(rng, layout):
    width = rng.randrange(240, 401, 10)
    height = rng.randrange(160, 301, 10)
    diameter = rng.randrange(10, 31, 2)
    max_offset = min(width // 3, height // 3, 60)
    offset = rng.randrange(max(20, diameter // 2 + 15), max_offset + 1, 5)
    model = plate.example_model()
    item = model["plates"][0]
    item.update(width_mm=width, height_mm=height, thickness_mm=rng.randrange(4, 21))
    model["materials"]["steel"]["E_mpa"] = rng.choice([69000, 70000, 190000, 200000, 205000, 210000])
    if layout == "corner_4":
        centers = ((offset, offset), (width-offset, offset),
                   (offset, height-offset), (width-offset, height-offset))
    else:
        centers = ((offset, offset), (width/2, offset), (width-offset, offset),
                   (offset, height-offset), (width/2, height-offset), (width-offset, height-offset))
    model["holes"] = [{"id": f"H{i+1}", "plate": "P1", "center_mm": list(center),
                       "diameter_mm": diameter} for i, center in enumerate(centers)]
    _dimension(model, "width")["value_mm"] = width
    _dimension(model, "height")["value_mm"] = height
    _dimension(model, "hole_diameter")["value_mm"] = diameter
    _dimension(model, "edge_offset")["value_mm"] = offset
    count_name = {4: "four", 6: "six"}.get(len(centers), str(len(centers)))
    model["assumptions"] = ["flat rectangular plate", f"{count_name} circular through holes",
                            "geometry and manufacturing checks only"]
    model["provenance"] = _provenance()
    return IR.validate(model)


def _verify(model):
    if model["kind"] == "truss2d":
        result = truss.solve(model)
        return {"method": "linear_axial_truss_fem",
                "pass": max(abs(x) for x in result["equilibrium_residual_N_Nmm"]) < 1e-5,
                "peak_abs_stress_mpa": round(result["peak_abs_stress_mpa"], 8),
                "max_displacement_mm": round(max(abs(v) for xy in result["node_displacements_mm"].values()
                                                 for v in xy), 8),
                "equilibrium_residual_N_Nmm": [round(x, 8) for x in result["equilibrium_residual_N_Nmm"]],
                "assumptions": model["assumptions"]}
    result = plate.check_geometry(model)
    return {"method": "manufacturing_geometry_checks", "pass": result["pass"],
            "minimum_edge_distance_mm": result["minimum_edge_distance_mm"],
            "minimum_ligament_mm": result["minimum_ligament_mm"],
            "net_area_mm2": round(result["net_area_mm2"], 8),
            "violations": result["violations"], "criteria": result["criteria"],
            "assumptions": model["assumptions"]}


def _render(model):
    canonical = truss.render(model) if model["kind"] == "truss2d" else plate.render(model)
    if model["kind"] == "mechanical_part_2d" and len(model["holes"]) != 4:
        canonical = canonical.replace("four-hole mounting plate",
                                      f'{len(model["holes"])}-hole mounting plate')
    monochrome = canonical.replace("#1f3348", "#111111").replace("#eaf3f8", "#f4f4f4")
    blueprint = canonical.replace('fill="white"', 'fill="#102a43"').replace(
        "#1f3348", "#d9efff").replace("#eaf3f8", "#173f5f").replace("#6b7280", "#a8d8ff")
    return {name: {"sha256": _sha(svg), "svg": svg} for name, svg in
            (("canonical", canonical), ("monochrome", monochrome), ("blueprint", blueprint))}


def _engineering_equal(first, second, tolerance=1e-3):
    """Compare recovered engineering content while allowing SVG decimal rounding."""
    def normalize(model):
        value = IR.validate(model); value.pop("provenance")
        for member in value["members"]:
            member["a"], member["b"] = sorted((member["a"], member["b"]))
            if len(member["id"]) == 2:
                member["id"] = "".join(sorted(member["id"]))
        value["members"] = sorted(value["members"], key=lambda row: row["id"])
        value["dimensions"] = sorted(value["dimensions"], key=lambda row: row["id"])
        value["holes"] = sorted(value["holes"], key=lambda row: row["id"])
        return value
    def same(a, b):
        if isinstance(a, dict) and isinstance(b, dict):
            return set(a) == set(b) and all(same(a[key], b[key]) for key in a)
        if isinstance(a, list) and isinstance(b, list):
            return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
        if (isinstance(a, (int, float)) and not isinstance(a, bool) and
                isinstance(b, (int, float)) and not isinstance(b, bool)):
            return math.isclose(a, b, rel_tol=0, abs_tol=tolerance)
        return a == b
    return same(normalize(first), normalize(second))


def _description(model, family):
    if model["kind"] == "truss2d":
        sec = model["sections"]["bar"]
        return (f"Create a {family} pin-jointed truss with span {_dimension(model, 'span')['value_mm']:g} mm, "
                f"height {_dimension(model, 'height')['value_mm']:g} mm, rectangular bars "
                f"{sec['b_mm']:g} by {sec['h_mm']:g} mm, E={model['materials']['steel']['E_mpa']:g} MPa, "
                f"a downward load of {abs(model['loads']['C'][1]):g} N at C, a pin at A and roller at E.")
    p = model["plates"][0]
    return (f"Create a {p['width_mm']:g} by {p['height_mm']:g} by {p['thickness_mm']:g} mm rectangular "
            f"plate with {len(model['holes'])} through holes of diameter {model['holes'][0]['diameter_mm']:g} mm, "
            f"corner edge offset {_dimension(model, 'edge_offset')['value_mm']:g} mm and "
            f"E={model['materials']['steel']['E_mpa']:g} MPa.")


def _move_plate_holes(model, offset):
    width, height = model["plates"][0]["width_mm"], model["plates"][0]["height_mm"]
    six = len(model["holes"]) == 6
    centers = ((offset, offset), (width/2, offset), (width-offset, offset),
               (offset, height-offset), (width/2, height-offset), (width-offset, height-offset)) if six else (
               (offset, offset), (width-offset, offset), (offset, height-offset), (width-offset, height-offset))
    for hole, center in zip(model["holes"], centers):
        hole["center_mm"] = list(center)
    _dimension(model, "edge_offset")["value_mm"] = offset


def _edited(model, changes):
    target = copy.deepcopy(model)
    for path, value in changes.items():
        if path == "loads.C.fy_N": target["loads"]["C"][1] = value
        elif path == "sections.bar.b_mm": target["sections"]["bar"]["b_mm"] = value
        elif path == "sections.bar.h_mm": target["sections"]["bar"]["h_mm"] = value
        elif path == "materials.steel.E_mpa": target["materials"]["steel"]["E_mpa"] = value
        elif path == "plates.P1.thickness_mm": target["plates"][0]["thickness_mm"] = value
        elif path == "holes.*.diameter_mm":
            for hole in target["holes"]: hole["diameter_mm"] = value
            _dimension(target, "hole_diameter")["value_mm"] = value
        elif path == "dimensions.edge_offset.value_mm": _move_plate_holes(target, value)
        else: raise ValueError(f"unsupported change path: {path}")
    target["provenance"] = {**target["provenance"], "mode": "procedurally_edited"}
    return IR.validate(target)


def _task(task_id, lineage, family, split, task, prompt, target, target_format="json", **extra):
    return {"id": task_id, "lineage_id": lineage, "family": family, "split": split,
            "task": task, "prompt": prompt,
            "target": target if target_format == "svg" else _json(target),
            "target_format": target_format,
            "prompt_contains_svg": "<svg" in prompt,
            "target_contains_svg": target_format == "svg", **extra}


def _tasks(asset, model, rng):
    lineage, family, split = asset["lineage_id"], asset["family"], asset["split"]
    state = {"asset": lineage, "engineering_hash": asset["engineering_hash"]}
    source_svg = asset["svg_variants"]["canonical"]["svg"]
    rows = []
    rows.append(_task("text-to-svg", lineage, family, split, "text_to_svg",
                      "Return one complete standalone engineering SVG only. " + _description(model, family),
                      source_svg, target_format="svg", difficulty="drawing_generation", source=state))
    rows.append(_task("svg-to-ir", lineage, family, split, "svg_to_ir",
                      "Recover canonical EngSVG IR JSON from this drawing:\n" +
                      asset["svg_variants"][rng.choice(list(asset["svg_variants"]))]["svg"],
                      model, difficulty="visual_recovery", source=state))
    rows.append(_task("analyze", lineage, family, split, "engineering_analysis",
                      "Run the appropriate stated engineering check for this drawing and return JSON.\n" + source_svg,
                      asset["verification"], difficulty="physics", source=state))

    edit_specs = []
    if model["kind"] == "truss2d":
        load = abs(model["loads"]["C"][1]); percent = rng.choice([7, 12, 18, 25])
        edit_specs = [
            (f"Increase the downward load at C by {percent}%.", {"loads.C.fy_N": -round(load*(1+percent/100))}, "arithmetic"),
            (f"Reduce the downward load at C by {rng.choice([5,15,20,30])}%.", None, "arithmetic"),
            (f"Make every member {rng.choice([5,10,15])} mm wider.", None, "entity_binding"),
            (f"Set every member depth to {rng.randrange(20,61,5)} mm.", None, "basic"),
        ]
        decrease = int(edit_specs[1][0].split("by ")[1].split("%")[0])
        edit_specs[1] = (edit_specs[1][0], {"loads.C.fy_N": -round(load*(1-decrease/100))}, edit_specs[1][2])
        wider = int(edit_specs[2][0].split("member ")[1].split(" mm")[0])
        edit_specs[2] = (edit_specs[2][0], {"sections.bar.b_mm": model["sections"]["bar"]["b_mm"]+wider}, edit_specs[2][2])
        depth = int(edit_specs[3][0].split("to ")[1].split(" mm")[0])
        edit_specs[3] = (edit_specs[3][0], {"sections.bar.h_mm": depth}, edit_specs[3][2])
        multiplier = rng.choice([1.25, 1.5, 2, 3]); stress_limit = rng.choice([100, 150, 200, 250])
        constraint_request = (f"Multiply the downward load at C by {multiplier:g}, but only if the resulting "
                              f"peak member stress does not exceed {stress_limit} MPa.")
        constraint_changes = {"loads.C.fy_N": -round(load*multiplier)}
        clarify = {"action": "clarify", "missing": ["load_change_amount"]}
        clarify_prompt = "Increase the load at C, but no amount is specified."
    else:
        p = model["plates"][0]; diameter = model["holes"][0]["diameter_mm"]
        thickness_delta, diameter_delta, offset_delta = rng.choice([1,2,3,4]), rng.choice([2,4,6]), rng.choice([5,10])
        edit_specs = [
            (f"Make the plate {thickness_delta} mm thicker.", {"plates.P1.thickness_mm": p["thickness_mm"]+thickness_delta}, "arithmetic"),
            (f"Increase all hole diameters by {diameter_delta} mm.", {"holes.*.diameter_mm": diameter+diameter_delta}, "entity_binding"),
            (f"Move every corner hole {offset_delta} mm farther from its nearest edges.",
             {"dimensions.edge_offset.value_mm": _dimension(model,"edge_offset")["value_mm"]+offset_delta}, "entity_binding"),
            (f"Set the plate thickness to {rng.randrange(5,26)} mm.", None, "basic"),
        ]
        thickness = int(edit_specs[3][0].split("to ")[1].split(" mm")[0])
        edit_specs[3] = (edit_specs[3][0], {"plates.P1.thickness_mm": thickness}, edit_specs[3][2])
        constraint_delta = rng.choice([6, 10, 14, 20])
        constraint_request = (f"Increase every hole diameter by {constraint_delta} mm, but only if all holes "
                              "retain at least 15 mm edge distance and 20 mm ligament.")
        constraint_changes = {"holes.*.diameter_mm": diameter+constraint_delta}
        clarify = {"action": "clarify", "missing": ["hole_diameter_change"]}
        clarify_prompt = "Enlarge all holes, but no new diameter or change amount is specified."

    for index, (request, changes, difficulty) in enumerate(edit_specs, 1):
        target_model = _edited(model, changes); verification = _verify(target_model)
        action = {"action": "edit", "changes": changes}
        rows.append(_task(f"edit-{index}", lineage, family, split, "edit_action",
                          "Return one exact engineering edit JSON. Request: " + request + "\nCurrent SVG:\n" + source_svg,
                          action, difficulty=difficulty, source=state,
                          target_engineering_hash=IR.engineering_digest(target_model),
                          target_verification=verification))
        style = rng.choice(list(asset["svg_variants"])); target_svg = _render(target_model)[style]["svg"]
        rows.append(_task(f"svg-edit-{index}", lineage, family, split, "svg_edit",
                          "Return the complete edited standalone SVG only. Preserve unrequested content. Request: " +
                          request + "\nCurrent SVG:\n" + asset["svg_variants"][style]["svg"],
                          target_svg, target_format="svg", difficulty=difficulty, source=state,
                          source_style=style, target_engineering_hash=IR.engineering_digest(target_model),
                          target_verification=verification))
    candidate = _edited(model, constraint_changes); candidate_check = _verify(candidate)
    constraint_pass = (candidate_check["peak_abs_stress_mpa"] <= stress_limit
                       if model["kind"] == "truss2d" else candidate_check["pass"])
    constraint_target = ({"action": "edit", "changes": constraint_changes} if constraint_pass else
                         {"action": "reject", "reason": "constraint_violation"})
    rows.append(_task("constraint", lineage, family, split, "constraint_edit",
                      "Return one exact constrained engineering action JSON. Request: " + constraint_request +
                      "\nCurrent SVG:\n" + source_svg,
                      constraint_target, difficulty="constraint_reasoning", source=state,
                      candidate_engineering_hash=IR.engineering_digest(candidate),
                      constraint_pass=constraint_pass, candidate_verification=candidate_check))
    rows.append(_task("clarify", lineage, family, split, "clarify",
                      "Return clarification JSON. Request: " + clarify_prompt + "\nCurrent SVG:\n" + source_svg,
                      clarify, difficulty="ambiguity", source=state))
    rows.append(_task("reject", lineage, family, split, "reject",
                      "Return rejection JSON. Request: Delete the engineering object and replace it with a vacation "
                      "photograph.\nCurrent SVG:\n" + source_svg,
                      {"action": "reject", "reason": "unsupported_request"},
                      difficulty="scope", source=state))
    assert len(rows) == TASKS_PER_DESIGN
    for row in rows: row["id"] = lineage + ":" + row["id"]
    return rows


def _excluded_hashes(previous: Path | None):
    excluded = {row["source_hash"] for row in BENCH.edit_cases()}
    if previous and previous.exists():
        for path in previous.glob("*.jsonl"):
            for line in path.read_text().splitlines():
                row = json.loads(line)
                if "group" in row: excluded.add(row["group"])
    return excluded


def _write_shards(out, name, records, size):
    paths = []
    for start in range(0, len(records), size):
        path = out / f"{name}-{start//size:05d}.jsonl.gz"
        with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as handle:
            for row in records[start:start+size]: handle.write(json.dumps(row, separators=(",", ":")) + "\n")
        paths.append(path)
    return paths


def _write_review_gallery(out, assets, per_family=4):
    """Write ordinary SVG files so people can inspect the data without a loader."""
    sample_dir = out / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    sample_paths = []
    cards = []
    families = sorted({asset["family"] for asset in assets})
    for family in families:
        choices = sorted((asset for asset in assets if asset["family"] == family),
                         key=lambda asset: asset["lineage_id"])[:per_family]
        for index, asset in enumerate(choices, 1):
            name = f"{family}-{index:02d}-{asset['lineage_id'][-8:]}.svg"
            path = sample_dir / name
            path.write_text(asset["svg_variants"]["canonical"]["svg"], encoding="utf-8")
            sample_paths.append(path)
            cards.append(
                f'<figure><img src="samples/{name}" alt="{family} engineering drawing">'
                f'<figcaption>{family} · {asset["lineage_id"]}</figcaption></figure>')
    gallery = out / "sample-gallery.html"
    gallery.write_text(
        "<!doctype html><html><head><meta charset=\"utf-8\"><title>EngSVG dataset samples</title>"
        "<style>body{font:15px system-ui;margin:24px;background:#f5f7fa;color:#172b4d}"
        "h1{margin-bottom:6px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px}"
        "figure{margin:0;padding:14px;background:white;border:1px solid #ccd5df;border-radius:10px}"
        "img{display:block;width:100%;height:260px;object-fit:contain}figcaption{margin-top:8px;font-size:12px}</style>"
        "</head><body><h1>EngSVG dataset samples</h1><p>Direct SVG files generated by the dataset factory.</p>"
        f'<main class="grid">{"".join(cards)}</main></body></html>\n', encoding="utf-8")
    return sample_paths, gallery


def generate(out: Path, designs=10_000, seed=SEED, previous: Path | None = None):
    if out.exists() and any(out.iterdir()):
        raise ValueError("output directory is not empty; dataset versions are immutable")
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed); excluded = _excluded_hashes(previous)
    candidates, seen = [], set()
    families = ("truss_fan_5", "truss_double_fan_6", "plate_corner_4", "plate_grid_6")
    index = 0
    while len(candidates) < designs:
        family = families[index % len(families)]; index += 1
        model = (_truss_model(rng, "fan_5" if family == "truss_fan_5" else "double_fan_6")
                 if family.startswith("truss") else
                 _plate_model(rng, "corner_4" if family == "plate_corner_4" else "grid_6"))
        engineering_hash = IR.engineering_digest(model)
        if engineering_hash in seen or engineering_hash in excluded: continue
        seen.add(engineering_hash); candidates.append((family, model, engineering_hash))
    rng.shuffle(candidates)
    split_at = (int(designs*.8), int(designs*.9))
    assets, tasks = [], []
    for position, (family, model, engineering_hash) in enumerate(candidates):
        split = "train" if position < split_at[0] else "validation" if position < split_at[1] else "test"
        lineage = "engsvg-" + engineering_hash[:20]
        variants = _render(model); verification = _verify(model)
        canonical_roundtrip = False
        try:
            recovered = (truss.import_untagged(variants["canonical"]["svg"])
                         if model["kind"] == "truss2d" else plate.import_untagged(variants["canonical"]["svg"]))
            canonical_roundtrip = _engineering_equal(recovered, model)
        except Exception:
            pass
        asset = {"lineage_id": lineage, "family": family, "split": split,
                 "engineering_hash": engineering_hash, "model": model,
                 "verification": verification, "canonical_roundtrip_verified": canonical_roundtrip,
                 "svg_variants": variants,
                 "generator": {"version": VERSION, "seed": seed}}
        assets.append(asset); tasks.extend(_tasks(asset, model, rng))
    rng.shuffle(assets); rng.shuffle(tasks)
    asset_paths = _write_shards(out, "assets", assets, 500)
    task_paths = _write_shards(out, "tasks", tasks, 10_000)
    sample_paths, gallery_path = _write_review_gallery(out, assets)
    split_designs = {split: sum(a["split"] == split for a in assets) for split in ("train","validation","test")}
    split_tasks = {split: sum(r["split"] == split for r in tasks) for split in ("train","validation","test")}
    task_counts = {task: sum(r["task"] == task for r in tasks) for task in sorted({r["task"] for r in tasks})}
    family_counts = {family: sum(a["family"] == family for a in assets) for family in families}
    summary = {"version": VERSION, "seed": seed, "designs": len(assets), "tasks": len(tasks),
               "tasks_per_design": TASKS_PER_DESIGN, "split_designs": split_designs,
               "split_tasks": split_tasks, "task_counts": task_counts, "family_counts": family_counts,
               "svg_variants_per_design": 3,
               "rows_with_svg_in_prompt": sum(r["prompt_contains_svg"] for r in tasks),
               "rows_with_full_svg_target": sum(r["target_contains_svg"] for r in tasks),
               "review_sample_svgs": len(sample_paths),
               "canonical_roundtrip_verified": sum(a["canonical_roundtrip_verified"] for a in assets),
               "physics_or_geometry_verified": sum(a["verification"]["pass"] for a in assets),
               "excluded_hashes": len(excluded), "overlap_with_excluded": 0,
               "storage": "gzip JSONL shards; SVG training rows contain full XML and also retain content-addressed asset IDs",
               "claim_boundary": "procedural trusses and rectangular perforated plates; not real-CAD coverage"}
    (out / "dataset-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    readme_path = out / "README.md"
    readme_path.write_text(
        "# EngSVG scalable dataset v2\n\n"
        "Procedural, lineage-safe multi-task data. Asset shards store each model, three SVG styles and deterministic verification once. "
        "Task shards contain full inline SVG XML for drawing inputs and targets as well as exact JSON targets for structured tasks. "
        "Split by `lineage_id`; never split individual requests. Open `sample-gallery.html` to see ordinary SVG files.\n")
    files = asset_paths + task_paths + sample_paths + [out/"dataset-summary.json", readme_path, gallery_path]
    manifest = {path.relative_to(out).as_posix(): _sha(path.read_bytes()) for path in sorted(files)}
    (out / "sha256-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--designs", type=int, default=10_000); parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--previous", type=Path, default=Path("cvpr2027/data/engsvg-multifamily-train-v1"))
    args = parser.parse_args(); print(json.dumps(generate(args.out, args.designs, args.seed, args.previous), indent=2))
