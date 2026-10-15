"""Re-test Astra on chosen circuit/pipe-network edit tasks, one call at a time under a strict USD cap.

Same request as network_astra_benchmark.py (system prompt, task prompt, model, effort, store=false, no tools); the only
difference is that a call's max_completion_tokens is lowered when the remaining budget could not pay for the full cap,
so the cap can never be exceeded. A call is started only while at least --reserve-usd remains. Costs are counted at
conservative prices ($12.50/M uncached input, $1/M cached input, $50/M output). Each answer is scored on arrival with
network_astra_benchmark.score_answer against the drawing-recovered truth. Saved samples are never re-billed.

  OPENAI_API_KEY=... python scripts/network_astra_confirm.py --output runs/network-astra-confirm-20261015 \
      --budget-usd 2 --plan ID1 ID2 ...          # repeat an id to request another sample of it
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import network_astra_benchmark as B  # noqa: E402

DATA = [ROOT / "data/engsvg-network-edit-v1/test.jsonl.gz", ROOT / "data/engsvg-network-edit-hard-v1/test.jsonl.gz"]
P_IN, P_CACHED, P_OUT = 12.5, 1.0, 50.0
INPUT_ESTIMATE = 3500            # tokens; generous for the hard-set prompts (largest main-set pipe prompt seen: 2,409)


def cost(usage: dict | None) -> float:
    u = usage or {}
    cached = (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0
    return ((u.get("prompt_tokens", 0) - cached) * P_IN + cached * P_CACHED + u.get("completion_tokens", 0) * P_OUT) / 1e6


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--plan", nargs="+", required=True)
    ap.add_argument("--budget-usd", type=float, required=True)
    ap.add_argument("--reserve-usd", type=float, default=0.65, help="start a call only while this much remains")
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--cap", type=int, default=32000)
    ap.add_argument("--model", default="gpt-6-astra")
    a = ap.parse_args()
    key = os.environ.get("OPENAI_API_KEY") or sys.exit("OPENAI_API_KEY unavailable; no calls made")
    rows = {}
    for path in DATA:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            rows.update({r["id"]: r for r in map(json.loads, fh)})
    missing = [i for i in a.plan if i not in rows]
    if missing:
        sys.exit(f"unknown task ids: {missing}")
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "protocol.json").write_text(json.dumps(dict(
        model=a.model, endpoint=B.ENDPOINT, effort=a.effort, cap=a.cap, store=False, tools=[], system=B.SYSTEM,
        prompt="network_astra_benchmark.prompt(row), identical to the 2026-09-27 runs",
        budget_usd=a.budget_usd, reserve_usd=a.reserve_usd, prices_usd_per_million=dict(input=P_IN, cached=P_CACHED, output=P_OUT),
        plan=a.plan), indent=2) + "\n")
    spent = sum(cost(json.loads(p.read_text()).get("usage")) for p in out.glob("*/result.json"))
    seen: dict[str, int] = {}
    for tid in a.plan:
        seen[tid] = seen.get(tid, 0) + 1
        folder = out / f"{tid.replace(':', '_')}__s{seen[tid]}"
        if (folder / "result.json").exists() and json.loads((folder / "result.json").read_text()).get("status") != "started":
            continue
        remaining = a.budget_usd - spent
        if remaining < a.reserve_usd:
            print(f"BUDGET-STOP before {tid} (spent ${spent:.3f} of ${a.budget_usd:.2f})", flush=True)
            break
        cap = min(a.cap, int((remaining - INPUT_ESTIMATE * P_IN / 1e6) / (P_OUT / 1e6)))
        row = rows[tid]
        payload = {"model": a.model, "messages": [{"role": "system", "content": B.SYSTEM}, {"role": "user", "content": B.prompt(row)}],
                   "reasoning_effort": a.effort, "max_completion_tokens": cap, "store": False}
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "request.json").write_text(json.dumps(payload, indent=1) + "\n")
        record = {"id": tid, "sample": seen[tid], "status": "started", "max_completion_tokens": cap,
                  "started_utc": datetime.now(timezone.utc).isoformat()}
        (folder / "result.json").write_text(json.dumps(record, indent=1) + "\n")
        t0 = time.perf_counter()
        req = urllib.request.Request(B.ENDPOINT, data=json.dumps(payload).encode(),
                                     headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        stop = False
        try:
            with urllib.request.urlopen(req, timeout=1500) as resp:
                raw = json.load(resp)
            (folder / "response.json").write_text(json.dumps(raw, indent=1) + "\n")
            choice = raw["choices"][0]
            text = choice["message"].get("content") or ""
            (folder / "response.txt").write_text(text)
            record.update(status="completed", model=raw.get("model"), response_id=raw.get("id"), usage=raw.get("usage"),
                          finish_reason=choice.get("finish_reason"), refusal=choice["message"].get("refusal"))
            svg, data = B._blocks(text)
            grade = B.score_answer(row, svg, data)
            truth = row["after_verification"]
            if row["family"] == "pipe_network":
                name, value = min(truth["pressure_heads_m"].items(), key=lambda kv: kv[1])
                grade["true_min_pressure_head"] = {"name": name, "value": round(value, 4)}
                grade["reported_min_pressure_head"] = (data or {}).get("min_pressure_head_m")
            grade["true_verdict"] = "pass" if truth["pass"] else "fail"
            grade["reported_verdict"] = (data or {}).get("verdict")
            grade["truncated"] = choice.get("finish_reason") == "length"
            record["grade"] = grade
        except urllib.error.HTTPError as err:
            body = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", err.read().decode(errors="replace").replace(key, "[REDACTED]"))
            record.update(status="api_error", http_status=err.code, error=body[:800])
            stop = "insufficient_quota" in body or err.code in (401, 403)
        except Exception as err:  # noqa: BLE001 - recorded, never retried silently
            record.update(status="client_error", error_type=type(err).__name__, error=str(err).replace(key, "[REDACTED]")[:500])
        record["wall_seconds"] = round(time.perf_counter() - t0, 1)
        record["cost_usd"] = round(cost(record.get("usage")), 4)
        (folder / "result.json").write_text(json.dumps(record, indent=1) + "\n")
        spent += record["cost_usd"]
        g = record.get("grade", {})
        print(f"END {tid} s{seen[tid]} {record['status']} {record.get('finish_reason')} cap={cap} ${record['cost_usd']:.3f} total ${spent:.3f} | "
              f"verdict {g.get('reported_verdict')} (true {g.get('true_verdict')}) correct={g.get('verdict_correct')} "
              f"e2e={g.get('end_to_end')} min-head reported={g.get('reported_min_pressure_head')} true={g.get('true_min_pressure_head')}", flush=True)
        if stop:
            print("STOP: account or key error", flush=True)
            break
    summary = []
    for p in sorted(out.glob("*/result.json")):
        r = json.loads(p.read_text())
        summary.append({k: r.get(k) for k in ("id", "sample", "status", "finish_reason", "cost_usd", "max_completion_tokens")} | {"grade": r.get("grade")})
    (out / "summary.json").write_text(json.dumps(dict(spent_usd=round(spent, 4), budget_usd=a.budget_usd, samples=summary), indent=1) + "\n")
    print(json.dumps(dict(spent_usd=round(spent, 4), samples=len(summary)), indent=1))


if __name__ == "__main__":
    main()
