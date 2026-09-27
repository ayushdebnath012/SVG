"""Astra (OpenAI API) on held-out circuit and pipe-network edits, scored by re-solving its drawing.

Astra works in its natural mode: it returns the complete edited SVG plus its own engineering
analysis of the edited design. Both are scored against the drawing-recovered ground truth:
  edit     -- engsvg_networks.physics_match(edited SVG, family, target model)
  verdict  -- its pass/fail and violating components vs. the solver's
  numbers  -- source currents / pipe velocities and the governing extreme value
Every request, response and usage record is saved; an attempted sample is never re-billed.

  build : pick a stratified task set from the test split
  run   : call the API (hard budget cap in USD at list prices)
  score : score saved responses
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import engsvg_networks as networks  # noqa: E402
from cad_astra_benchmark import api_key  # noqa: E402

VERSION = "network-astra-benchmark-v1"
ENDPOINT = "https://api.openai.com/v1/chat/completions"
DATA = ROOT / "data/engsvg-network-edit-v1"
PRICE_IN, PRICE_OUT = 10.0, 50.0  # USD per million tokens, gpt-6-astra list price

SYSTEM = ("You are an engineering drafting and analysis assistant. Use your own reasoning; no external tools "
          "are provided. Do not claim you ran a solver.")

CONVENTIONS = {
    "dc_network": (
        "Drawing conventions: straight lines are ideal wires. A wire that ends on another wire (a T) is connected "
        "to it; a filled dot also marks a connection; wires that cross without a dot are NOT connected. Rectangles "
        "are resistors and circles are ideal DC voltage sources; the '+' inside a source marks its positive "
        "terminal. Labels give component names and values.\n"
        "Criteria (from the drawing notes): every resistor's dissipated power must not exceed the stated rating, "
        "and the magnitude of every source's current must not exceed the stated supply fuse rating.",
        '{"verdict": "pass" or "fail", "violations": [names of every resistor or source that violates a '
        'criterion], "source_currents_A": {"V1": current delivered out of its + terminal, ...}, '
        '"max_resistor_power_W": {"name": "R?", "value": watts}}'),
    "pipe_network": (
        "Drawing conventions: heavy lines are pipes; filled dots are junctions. A pipe runs between junctions or "
        "reservoirs and may turn through 90-degree elbows; each elbow adds the minor-loss coefficient K given in "
        "the notes. 'P# L m ØD' gives a pipe's length (m) and internal diameter (mm); 'J# q=.. L/s z=.. m' gives "
        "the demand withdrawn at a junction and its elevation; 'R# H=.. m' is a reservoir's fixed total head.\n"
        "Analysis model: steady incompressible water, density 998 kg/m3, dynamic viscosity 1.002e-3 Pa s, "
        "g = 9.80665 m/s2; Darcy-Weisbach head loss with the Churchill (1977) friction factor and the pipe "
        "roughness in the notes; tee and junction losses neglected; pressure head at a junction = hydraulic "
        "head minus elevation.\n"
        "Criteria (from the drawing notes): every pipe velocity must not exceed the maximum velocity, and every "
        "junction pressure head must be at least the minimum pressure head.",
        '{"verdict": "pass" or "fail", "violations": [names of every pipe or junction that violates a '
        'criterion], "pipe_velocities_m_s": {"P1": speed, ...}, "min_pressure_head_m": {"name": "J?", '
        '"value": metres}}'),
}


def prompt(row: dict) -> str:
    conventions, schema = CONVENTIONS[row["family"]]
    return (f"Instruction: {row['instruction']}\n\n{conventions}\n\n"
            "Tasks:\n1. Apply the instruction to the drawing, changing nothing else, and return the complete "
            "edited SVG.\n2. Analyse the EDITED design and report whether it meets every criterion.\n\n"
            "Answer with exactly two fenced blocks and nothing else: first ```svg containing the full edited "
            f"SVG, then ```json containing {schema}\n\nSource SVG:\n{row['source_svg']}")


def _load(split: str = "test", data: Path = DATA) -> list[dict]:
    with gzip.open(data / f"{split}.jsonl.gz", "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def build(out: Path, per_kind: int, data: Path = DATA) -> dict:
    rows = sorted(_load("test", data), key=lambda row: row["id"])
    chosen, counts = [], {}
    for row in rows:
        key = (row["family"], row["edit_kind"])
        if counts.get(key, 0) < per_kind:
            counts[key] = counts.get(key, 0) + 1
            chosen.append(row)
    tasks = [{"id": row["id"], "family": row["family"], "edit_kind": row["edit_kind"],
              "instruction": row["instruction"], "prompt": prompt(row)} for row in chosen]
    manifest = {"version": VERSION, "data": str(data.resolve().relative_to(ROOT)), "split": "test",
                "selection": f"first {per_kind} rows by id for every (family, edit_kind)",
                "system": SYSTEM, "tasks": tasks,
                "counts": {f"{f}/{k}": n for (f, k), n in sorted(counts.items())}}
    out.mkdir(parents=True, exist_ok=True)
    (out / "tasks.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return {"tasks": len(tasks), "counts": manifest["counts"]}


def _cost(usage: dict | None) -> float:
    usage = usage or {}
    return (usage.get("prompt_tokens", 0) * PRICE_IN + usage.get("completion_tokens", 0) * PRICE_OUT) / 1e6


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def run(tasks_dir: Path, out: Path, model: str, effort: str, cap: int, workers: int, budget: float,
        ids: str | None) -> None:
    manifest = json.loads((tasks_dir / "tasks.json").read_text())
    tasks = [t for t in manifest["tasks"] if not ids or t["id"] in ids.split(",")]
    key = api_key()
    out.mkdir(parents=True, exist_ok=True)
    protocol = {"version": VERSION, "model": model, "endpoint": ENDPOINT, "effort": effort, "cap": cap,
                "tasks_sha256": hashlib.sha256((tasks_dir / "tasks.json").read_bytes()).hexdigest(),
                "tools": [], "store": False}
    path = out / "protocol.json"
    if path.exists() and json.loads(path.read_text()) != protocol:
        raise SystemExit("protocol mismatch; use a fresh output directory")
    _write(path, protocol)
    lock = threading.Lock()
    spent = [sum(_cost(json.loads(p.read_text()).get("usage")) for p in out.glob("*/result.json"))]

    def one(task):
        folder = out / task["id"].replace(":", "_")
        if (folder / "result.json").exists():
            return
        with lock:
            if spent[0] >= budget:
                print("BUDGET-STOP", task["id"], flush=True)
                return
        folder.mkdir(parents=True, exist_ok=True)
        payload = {"model": model, "messages": [{"role": "system", "content": manifest["system"]},
                                                {"role": "user", "content": task["prompt"]}],
                   "reasoning_effort": effort, "max_completion_tokens": cap, "store": False}
        record = {"id": task["id"], "status": "started", "started_utc": datetime.now(timezone.utc).isoformat()}
        _write(folder / "result.json", record)
        started = time.perf_counter()
        request = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
                                         headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=1200) as response:
                raw = json.load(response)
            _write(folder / "response.json", raw)
            choice = raw["choices"][0]
            (folder / "response.txt").write_text(choice["message"].get("content") or "")
            record.update(status="completed", model=raw.get("model"), response_id=raw.get("id"),
                          usage=raw.get("usage"), finish_reason=choice.get("finish_reason"),
                          refusal=choice["message"].get("refusal"))
        except urllib.error.HTTPError as error:
            body = error.read().decode(errors="replace").replace(key, "[REDACTED]")
            record.update(status="api_error", http_status=error.code,
                          error=re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", body)[:1000])
        except Exception as error:  # noqa: BLE001 - recorded, never retried silently
            record.update(status="client_error", error_type=type(error).__name__,
                          error=str(error).replace(key, "[REDACTED]")[:500])
        record["wall_seconds"] = time.perf_counter() - started
        _write(folder / "result.json", record)
        with lock:
            spent[0] += _cost(record.get("usage"))
            total = spent[0]
        print("END", task["id"], record["status"], record.get("finish_reason"),
              f"${_cost(record.get('usage')):.3f} total ${total:.2f}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, tasks))


def _blocks(text: str):
    svg = re.search(r"```(?:svg|xml)?\s*(<svg[\s\S]*?</svg>)\s*```", text)
    if svg is None:
        svg = re.search(r"(<svg[\s\S]*?</svg>)", text)
    data = None
    for block in re.findall(r"```json\s*([\s\S]*?)```", text):
        try:
            data = json.loads(block)
        except ValueError:
            continue
    return (svg.group(1) if svg else None), data


def _names(violations: list[str]) -> set[str]:
    return {re.match(r"\s*([A-Z]\d+)", item).group(1) for item in violations if re.match(r"\s*([A-Z]\d+)", item)}


def _rel(value, truth, floor=1e-9):
    try:
        return abs(float(value) - truth) / max(abs(truth), floor)
    except (TypeError, ValueError):
        return float("inf")


def _close(value, truth, rel, absolute) -> bool:
    """Within a relative tolerance, or within an absolute one for near-zero quantities.

    The absolute floor was added after the first scoring pass: velocities under 0.1 m/s reported to three
    decimals (0.003 vs 0.00265) were counted as 13 % errors, which is rounding, not physics.
    """
    try:
        return abs(float(value) - truth) <= max(rel * abs(truth), absolute)
    except (TypeError, ValueError):
        return False


def score_answer(row: dict, svg: str | None, data: dict | None) -> dict:
    """Score an edited drawing and an analysis against the drawing-recovered ground truth."""
    truth = row["after_verification"]
    result = {"svg_found": svg is not None, "json_found": isinstance(data, dict), "edit_correct": False,
              "verdict_correct": False, "violations_correct": False, "numbers_correct": False}
    if svg is not None:
        match = networks.physics_match(svg, row["family"], row["target_model"])
        result["edit_correct"] = bool(match.get("topology_equal") and match["physics_equal"])
        result["edit_detail"] = {k: v for k, v in match.items() if k in ("recovered", "reason", "topology_equal")}
    if isinstance(data, dict):
        verdict = str(data.get("verdict", "")).strip().lower()
        result["verdict_correct"] = verdict in ("pass", "fail") and (verdict == "pass") == truth["pass"]
        result["violations_correct"] = _names([str(v) for v in data.get("violations") or []]) == _names(truth["violations"])
        if row["family"] == "dc_network":
            currents = data.get("source_currents_A") or {}
            ok = all(_close(currents.get(name), value, 0.01, 1e-4) for name, value in truth["source_currents_A"].items()
                     if abs(value) > 1e-9) and bool(currents)
            name, value = max(truth["resistor_powers_W"].items(), key=lambda item: item[1])
            reported = data.get("max_resistor_power_W") or {}
            result["numbers_correct"] = ok and reported.get("name") == name and _close(reported.get("value"), value, 0.01, 1e-4)
            result["worst_relative_error"] = max([_rel(currents.get(n), v) for n, v in truth["source_currents_A"].items()
                                                  if abs(v) > 1e-9] + [_rel(reported.get("value"), value)])
        else:
            speeds = data.get("pipe_velocities_m_s") or {}
            errors = [_rel(speeds.get(name), value, 1e-3) for name, value in truth["pipe_velocities_m_s"].items()]
            speeds_ok = bool(speeds) and all(_close(speeds.get(name), value, 0.02, 0.01)
                                             for name, value in truth["pipe_velocities_m_s"].items())
            name, value = min(truth["pressure_heads_m"].items(), key=lambda item: item[1])
            reported = data.get("min_pressure_head_m") or {}
            head_ok = reported.get("name") == name and _close(reported.get("value"), value, 0.02, 0.2)
            result["numbers_correct"] = speeds_ok and head_ok
            result["worst_relative_error"] = max(errors + [_rel(reported.get("value"), value)])
    result["end_to_end"] = result["edit_correct"] and result["verdict_correct"] and result["violations_correct"]
    return result


def score(tasks_dir: Path, out: Path) -> dict:
    manifest = json.loads((tasks_dir / "tasks.json").read_text())
    rows = {row["id"]: row for row in _load("test", ROOT / manifest["data"])}
    records, usage = [], {"prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0}
    for task in manifest["tasks"]:
        folder = out / task["id"].replace(":", "_")
        if not (folder / "result.json").exists():
            continue
        result = json.loads((folder / "result.json").read_text())
        for key in ("prompt_tokens", "completion_tokens"):
            usage[key] += (result.get("usage") or {}).get(key, 0)
        usage["reasoning_tokens"] += ((result.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
        record = {"id": task["id"], "family": task["family"], "edit_kind": task["edit_kind"],
                  "status": result["status"], "finish_reason": result.get("finish_reason")}
        if result["status"] == "completed":
            svg, data = _blocks((folder / "response.txt").read_text())
            record.update(score_answer(rows[task["id"]], svg, data))
        records.append(record)
    completed = [r for r in records if r["status"] == "completed"]

    def rate(subset, key):
        return {"n": len(subset), key: sum(bool(r.get(key)) for r in subset)}

    metrics = ("edit_correct", "verdict_correct", "violations_correct", "numbers_correct", "end_to_end")
    summary = {"version": VERSION, "attempted": len(records), "completed": len(completed),
               "truncated": sum(r.get("finish_reason") == "length" for r in completed),
               "usage": usage, "estimated_cost_usd": round(_cost(usage), 2),
               "overall": {m: sum(bool(r.get(m)) for r in completed) for m in metrics},
               "by_family": {}, "by_edit_kind": {}}
    for key, field in (("by_family", "family"), ("by_edit_kind", "edit_kind")):
        for value in sorted({r[field] for r in completed}):
            subset = [r for r in completed if r[field] == value]
            summary[key][value] = {"n": len(subset), **{m: sum(bool(r.get(m)) for r in subset) for m in metrics}}
    _write(out / "scores.json", {"summary": summary, "records": records})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "run", "score"])
    parser.add_argument("--tasks", type=Path, default=ROOT / "data/network-astra-bench-v1")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--per-kind", type=int, default=10)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--model", default="gpt-6-astra")
    parser.add_argument("--effort", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--cap", type=int, default=32000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--budget", type=float, default=40.0, help="stop starting calls past this USD estimate")
    parser.add_argument("--ids")
    args = parser.parse_args()
    if args.command == "build":
        print(json.dumps(build(args.tasks, args.per_kind, args.data), indent=2))
    elif args.output is None:
        parser.error("--output required")
    elif args.command == "run":
        run(args.tasks, args.output, args.model, args.effort, args.cap, args.workers, args.budget, args.ids)
        print(json.dumps(score(args.tasks, args.output), indent=2))
    else:
        print(json.dumps(score(args.tasks, args.output), indent=2))
