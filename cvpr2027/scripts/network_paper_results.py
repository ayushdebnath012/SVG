"""Compute every number in the network paper from saved artefacts and write paper/network/results.tex.

Nothing in the paper's tables is typed by hand: controls and round trips are re-run on the current code,
dataset statistics come from the dataset summaries, Astra scores from its saved responses, and our editor's
scores from the prediction files the trainer and eval_patcher wrote, re-scored here end to end.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import engsvg_networks as N  # noqa: E402
import network_astra_benchmark as B  # noqa: E402
from svgpatchlab.core import apply_patch, build_scene, generic_svg_policy, parse_patch, validate_patch  # noqa: E402

PAPER = ROOT / "paper/network"
MAIN, HARD = ROOT / "data/engsvg-network-edit-v1", ROOT / "data/engsvg-network-edit-hard-v1"
FAMILY_NAME = {"dc_network": "Circuits", "pipe_network": "Pipes"}


def _load(data: Path, split: str = "test") -> dict:
    with gzip.open(data / f"{split}.jsonl.gz", "rt", encoding="utf-8") as handle:
        return {row["id"]: row for row in map(json.loads, handle)}


def _n(value: int) -> str:
    return f"{value:,}".replace(",", "{,}")


def round_trips(seeds=((21, 400), (33, 600))) -> int:
    total = 0
    for seed, designs in seeds:
        rng = random.Random(seed)
        for index in range(designs):
            for family, (make, edits, render, _, recover, netlist, compare) in N.FAMILIES.items():
                model = make(rng, index)
                for target in [model] + [t for _, t, _ in edits(model, rng)]:
                    result = compare(netlist(target), recover(render(target)))
                    if not (result["topology_equal"] and result["physics_equal"]):
                        raise AssertionError(f"round trip failed: {family} seed {seed} design {index}")
                    total += 1
    return total


FAILED = {"edit_correct": False, "verdict_correct": False, "violations_correct": False, "end_to_end": False,
          "readable": False}


def verify_svg(row: dict, edited: str | None) -> dict:
    """Our verdict on any edited drawing: recover it, solve it, check it, compare with the target."""
    if edited is None:
        return dict(FAILED)
    try:
        recovered = N.FAMILIES[row["family"]][4](edited)
        solution = (N.solve_circuit if row["family"] == "dc_network" else N.solve_pipes)(recovered)
        check = (N.check_circuit if row["family"] == "dc_network" else N.check_pipes)(recovered, solution)
    except (N.RecoveryError, N.IllPosed, ValueError):
        return dict(FAILED)
    match = N.physics_match(edited, row["family"], row["target_model"])
    truth = row["after_verification"]
    result = {"readable": True, "edit_correct": bool(match.get("topology_equal") and match["physics_equal"]),
              "verdict_correct": check["pass"] == truth["pass"],
              "violations_correct": B._names(check["violations"]) == B._names(truth["violations"])}
    result["end_to_end"] = result["edit_correct"] and result["verdict_correct"] and result["violations_correct"]
    return result


def our_answer(row: dict, prediction: str) -> dict:
    """Apply a predicted patch and score the edited drawing exactly as Astra's drawings are scored."""
    try:
        patch = parse_patch(prediction)
        validate_patch(patch, build_scene(row["source_svg"]), generic_svg_policy(max_operations=500))
        edited = apply_patch(row["source_svg"], patch)
    except Exception:  # noqa: BLE001 - an unusable patch is simply a failed edit
        return dict(FAILED)
    return verify_svg(row, edited)


def ours(run: Path, rows: dict, prediction_file: str, ids=None) -> list[dict] | None:
    path = run / prediction_file
    if not path.exists():
        return None
    records = []
    for line in path.read_text().splitlines():
        record = json.loads(line)
        if ids is not None and record["id"] not in ids:
            continue
        row = rows[record["id"]]
        records.append({"id": record["id"], "family": row["family"], "edit_kind": row["edit_kind"],
                        "loops": row["before_verification"]["independent_loops"],
                        **our_answer(row, record["prediction"])})
    return records


def astra(out: Path, tasks: Path) -> tuple[list[dict], dict] | None:
    if not (out / "protocol.json").exists():
        return None
    manifest = json.loads((tasks / "tasks.json").read_text())
    rows = _load(ROOT / manifest["data"])
    records, usage, seconds = [], [], []
    for task in manifest["tasks"]:
        folder = out / task["id"].replace(":", "_")
        if not (folder / "result.json").exists():
            continue
        result = json.loads((folder / "result.json").read_text())
        if result["status"] != "completed":
            continue
        usage.append(result.get("usage") or {})
        seconds.append(result.get("wall_seconds", 0))
        svg, data = B._blocks((folder / "response.txt").read_text())
        row = rows[task["id"]]
        records.append({"id": task["id"], "family": task["family"], "edit_kind": task["edit_kind"],
                        "loops": row["before_verification"]["independent_loops"],
                        "finish_reason": result.get("finish_reason"), **B.score_answer(row, svg, data),
                        "hybrid": verify_svg(row, svg)})
    cost = [B._cost(u) for u in usage]
    meta = {"n": len(records), "cost_mean": statistics.mean(cost) if cost else 0, "cost_total": sum(cost),
            "seconds_median": statistics.median(seconds) if seconds else 0,
            "truncated": sum(r["finish_reason"] == "length" for r in records),
            "reasoning_tokens_median": statistics.median(
                [(u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) for u in usage]) if usage else 0}
    return records, meta


def _cell(records, key, family=None):
    subset = [r for r in records if family is None or r["family"] == family]
    if not subset:
        return "--"
    hits = sum(bool(r.get(key)) for r in subset)
    return f"{100 * hits / len(subset):.0f} ({hits}/{len(subset)})"


def comparison_rows(systems: list[tuple[str, list[dict] | None]]) -> str:
    lines = []
    for family in ("dc_network", "pipe_network"):
        lines.append(rf"\multicolumn{{5}}{{l}}{{\itshape {FAMILY_NAME[family]}}} \\")
        for name, records in systems:
            if records is None:
                lines.append(rf"{name} & \multicolumn{{4}}{{c}}{{pending}} \\")
                continue
            cells = [_cell(records, key, family) for key in ("edit_correct", "verdict_correct",
                                                               "violations_correct", "end_to_end")]
            lines.append(f"{name} & " + " & ".join(cells) + r" \\")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", type=Path, default=ROOT / "runs/remote-network-20260927",
                        help="fetched copy of the host's network runs directory")
    args = parser.parse_args()
    macros, facts = {}, {}

    controls = N.controls()
    macros["numControls"] = str(len(controls))
    macros["controlRows"] = "\n".join(
        f"{row['control'].replace('&', 'and')} & {row['value']:.6g} & {row['expected']:.6g} \\\\"
        .replace("Ω", r"$\Omega$") for row in controls)
    if not all(row["pass"] for row in controls):
        raise AssertionError("a control failed")
    total = round_trips()
    macros["roundTripTotal"] = _n(total)

    main_summary = json.loads((MAIN / "dataset-summary.json").read_text())
    hard_summary = json.loads((HARD / "dataset-summary.json").read_text())
    macros["netEdits"] = _n(main_summary["edit_examples"])
    macros["netDesigns"] = _n(main_summary["source_designs"])
    macros["hardEdits"] = _n(hard_summary["edit_examples"])
    macros["hardMaxLoopsDC"] = str(hard_summary["independent_loops_per_design"]["dc_network"]["max"])
    macros["datasetDrawings"] = _n(main_summary["drawings_recovered_to_model"] + hard_summary["drawings_recovered_to_model"])

    def loops(summary, family):
        item = summary["independent_loops_per_design"][family]
        return f"{item['median']} ({item['min']}--{item['max']})"

    def split(summary):
        s = summary["split_examples"]
        return "/".join(_n(s.get(k, 0)) for k in ("train", "validation", "test"))

    rows = [("Source designs", _n(main_summary["source_designs"]), _n(hard_summary["source_designs"])),
            ("Edits (train/val/test)", split(main_summary), split(hard_summary)),
            ("Circuit loops", loops(main_summary, "dc_network"), loops(hard_summary, "dc_network")),
            ("Pipe-network loops", loops(main_summary, "pipe_network"), loops(hard_summary, "pipe_network")),
            ("Edited designs safe", _n(main_summary["verified_safe"]), _n(hard_summary["verified_safe"])),
            ("Verdict flips", _n(main_summary["edits_that_change_the_verdict"]),
             _n(hard_summary["edits_that_change_the_verdict"]))]
    for op in ("set_text", "set_attributes", "remove_element", "insert_subtree"):
        rows.append((rf"Edits using \code{{{op.replace('_', chr(92) + '_')}}}",
                     _n(main_summary["patch_operation_coverage"].get(op, 0)),
                     _n(hard_summary["patch_operation_coverage"].get(op, 0))))
    macros["dataRows"] = "\n".join(" & ".join(r) + r" \\" for r in rows)

    main_rows, hard_rows = _load(MAIN), _load(HARD)
    astra_main = astra(ROOT / "runs/network-astra-20260927", ROOT / "data/network-astra-bench-v1")
    astra_hard = astra(ROOT / "runs/network-astra-hard-20260927", ROOT / "data/network-astra-bench-hard-v1")
    main_ids = {r["id"] for r in astra_main[0]} if astra_main else None
    hard_ids = {r["id"] for r in astra_hard[0]} if astra_hard else None

    ours_runs = {}
    for size in ("1.5b", "7b"):
        run = args.remote / f"net-qwen-coder-{size}"
        ours_runs[size] = {
            "main_subset": ours(run, main_rows, "trained-predictions.jsonl", main_ids),
            "main_all": ours(run, main_rows, "trained-predictions.jsonl"),
            "hard_subset": ours(args.remote / f"net-qwen-coder-{size}-hard", hard_rows, "adapter-predictions.jsonl", hard_ids),
            "hard_all": ours(args.remote / f"net-qwen-coder-{size}-hard", hard_rows, "adapter-predictions.jsonl"),
        }
    base = ours(args.remote / "net-qwen-coder-1.5b", main_rows, "base-predictions.jsonl", main_ids)

    def hybrid(records):
        # Astra's own drawing, but the verdict computed by our verifier from that drawing.
        if records is None:
            return None
        return [{**r, **r["hybrid"]} for r in records]

    for tier, a, key in (("Main", astra_main, "main_subset"), ("Hard", astra_hard, "hard_subset")):
        systems = [(r"\astra (own analysis)", a[0] if a else None),
                   (r"\astra drawing $+$ \ours verdict", hybrid(a[0]) if a else None),
                   (r"\ours editor 1.5B", ours_runs["1.5b"][key]),
                   (r"\ours editor 7B", ours_runs["7b"][key])]
        if tier == "Main":
            systems.insert(2, (r"Qwen2.5-Coder 1.5B, untrained", base))
        macros[f"compare{tier}Rows"] = comparison_rows(systems)
        if a:
            meta = a[1]
            facts[f"astra_{tier.lower()}"] = meta
            macros[f"astra{tier}N"] = str(meta["n"])
            macros[f"astra{tier}Cost"] = f"{meta['cost_mean']:.2f}"
            macros[f"astra{tier}CostTotal"] = f"{meta['cost_total']:.2f}"
            macros[f"astra{tier}Seconds"] = f"{meta['seconds_median']:.0f}"
            macros[f"astra{tier}Truncated"] = str(meta["truncated"])
            macros[f"astra{tier}Reasoning"] = _n(int(meta["reasoning_tokens_median"]))

    full_lines = []
    for size in ("1.5b", "7b"):
        for tier in ("main_all", "hard_all"):
            records = ours_runs[size][tier]
            label = f"{size.upper()} {'main test' if tier == 'main_all' else 'hard tier'}"
            if records is None:
                full_lines.append(rf"{label} & \multicolumn{{3}}{{c}}{{pending}} \\")
                continue
            full_lines.append(f"{label} & {_cell(records, 'edit_correct', 'dc_network')} & "
                              f"{_cell(records, 'edit_correct', 'pipe_network')} & {_cell(records, 'end_to_end')} \\\\")
    macros["oursFullRows"] = "\n".join(full_lines)

    kind_lines = []
    reference = ours_runs["1.5b"]["main_all"]
    kinds = sorted({(r["family"], r["edit_kind"]) for r in (reference or [])} |
                   {(r["family"], r["edit_kind"]) for r in (astra_main[0] if astra_main else [])})
    for family, kind in kinds:
        def cell(records, key):
            if records is None:
                return "--"
            return _cell([r for r in records if r["edit_kind"] == kind], key, family)
        kind_lines.append(f"{FAMILY_NAME[family]}: {kind.replace('_', ' ')} & "
                          f"{cell(astra_main[0] if astra_main else None, 'end_to_end')} & "
                          f"{cell(ours_runs['1.5b']['main_all'], 'end_to_end')} & "
                          f"{cell(ours_runs['7b']['main_all'], 'end_to_end')} \\\\")
    macros["kindRows"] = "\n".join(kind_lines)

    text = ["% Generated by scripts/network_paper_results.py -- do not edit by hand."]
    for name, value in macros.items():
        text.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    (PAPER / "results.tex").write_text("\n".join(text) + "\n")
    (PAPER / "results-facts.json").write_text(json.dumps({"macros": macros, "facts": facts}, indent=2,
                                                          ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in macros.items() if "Rows" not in k}, indent=2, ensure_ascii=False))
    for key in ("compareMainRows", "compareHardRows", "oursFullRows"):
        print(macros[key])


if __name__ == "__main__":
    main()
