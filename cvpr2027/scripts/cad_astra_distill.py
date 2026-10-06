"""Verifier-guided distillation, teacher side: Astra candidates on BenchCAD TRAIN tasks, chosen by a CAD verifier.

The teacher answers with a short PLAN (quoted original lines with their zero-based indices) followed by the
patch; the plan is what a student can learn beyond the reference patch. Only the training split is sent to
the API. cad_edit_verifier.py ranks the candidates without the reference edit; the reference is executed
only for audit fields that measure how often the verifier's choice is correct.

  sample : n candidates per task, hard USD budget at list price, every request saved, never re-billed
  verify : run the verifier on every sampled task under the CadQuery runtime
  report : selection accuracy of the verifier against the reference (audit), per acceptance rule
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "runs/multisource-cad-colab-20261002/results-final"
ENDPOINT = "https://api.openai.com/v1/chat/completions"
PRICE_IN, PRICE_OUT = 10.0, 50.0  # USD per million tokens, gpt-6-astra list price
INPUT_TOKEN_BOUND = 2500
VERSION = "cad-astra-distill-v1"

SYSTEM = (
    "You edit mechanical CAD. First write a short plan, then the patch, in exactly this format:\n"
    "PLAN:\n- [i] `exact original line i` -> what changes (at most 20 words)\n"
    "(one bullet per edit operation; i is the zero-based ORIGINAL line index where the operation starts; "
    "for an insertion at the end write [END])\n"
    'PATCH:\n{"edits":[{"start":0,"delete":0,"insert":["replacement line"]}]}\n'
    "Indices are zero-based lines of the ORIGINAL input; operations must be ordered, nonoverlapping and in "
    "bounds. Preserve unrelated features. The supplied representation determines syntax. Return no other "
    "text and no invented physics results. Geometry execution and FEM checks are performed by external "
    "tools; never claim verification.")


def train_tasks(source: str = "BenchCAD") -> list[dict]:
    """Training rows of one source: categories round-robin, sha256(id) order within a category."""
    rows = [json.loads(l) for l in (RESULTS / "train-retained.jsonl").read_text().splitlines()]
    by_category: dict[str, list] = {}
    for row in sorted((r for r in rows if r["source"] == source),
                      key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest()):
        by_category.setdefault(row["category"], []).append(row)
    ordered, queues = [], [by_category[k] for k in sorted(by_category)]
    while any(queues):
        for queue in queues:
            if queue:
                ordered.append(queue.pop(0))
    return ordered


def _cost(usage: dict | None) -> float:
    usage = usage or {}
    return (usage.get("prompt_tokens", 0) * PRICE_IN + usage.get("completion_tokens", 0) * PRICE_OUT) / 1e6


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _post(payload: dict, key: str) -> dict:
    request = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
                                     headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=900) as response:
        return json.load(response)


def sample(out: Path, n: int, effort: str, cap: int, workers: int, budget: float, limit: int | None,
           skip: int) -> None:
    key = os.environ.get("OPENAI_API_KEY") or sys.exit("OPENAI_API_KEY unavailable; no calls made")
    todo = train_tasks()[skip:skip + limit if limit else None]
    out.mkdir(parents=True, exist_ok=True)
    protocol = dict(version=VERSION, model="gpt-6-astra", endpoint=ENDPOINT, effort=effort, cap=cap, n=n,
                    split="train", source="BenchCAD", system_sha256=hashlib.sha256(SYSTEM.encode()).hexdigest(),
                    train_sha256=hashlib.sha256((RESULTS / "train-retained.jsonl").read_bytes()).hexdigest(),
                    price_usd_per_million=dict(input=PRICE_IN, output=PRICE_OUT), tools=[], store=False)
    path = out / "protocol.json"
    if path.exists() and json.loads(path.read_text()) != protocol:
        raise SystemExit("protocol mismatch; use a fresh output directory")
    _write(path, protocol)
    (out / "system.txt").write_text(SYSTEM)
    worst = (INPUT_TOKEN_BOUND * PRICE_IN + n * cap * PRICE_OUT) / 1e6
    lock = threading.Lock()
    state = dict(spent=sum(_cost(json.loads(p.read_text()).get("usage")) for p in out.glob("*/result.json")),
                 reserved=0.0, n_supported=None)

    def one(row):
        folder = out / row["id"][:16]
        if (folder / "result.json").exists():
            return
        with lock:
            if state["spent"] + state["reserved"] + worst > budget:
                print("BUDGET-STOP", row["id"][:16], flush=True)
                return
            state["reserved"] += worst
        folder.mkdir(parents=True, exist_ok=True)
        base = {"model": "gpt-6-astra", "messages": [{"role": "system", "content": SYSTEM},
                                                     {"role": "user", "content": row["input"]}],
                "reasoning_effort": effort, "max_completion_tokens": cap, "store": False}
        record = dict(id=row["id"], category=row["category"], status="started",
                      started_utc=datetime.now(timezone.utc).isoformat())
        _write(folder / "result.json", record)
        started = time.perf_counter()
        texts, usage, finishes, raw_ids = [], Counter(), [], []

        def collect(raw):
            texts.extend(c["message"].get("content") or "" for c in raw["choices"])
            finishes.extend(c.get("finish_reason") for c in raw["choices"])
            usage.update({k: v for k, v in raw["usage"].items() if isinstance(v, int)})
            raw_ids.append(raw.get("id"))
        try:
            if n > 1 and state["n_supported"] is not False:
                try:
                    collect(_post(dict(base, n=n), key))
                    state["n_supported"] = True
                except urllib.error.HTTPError as error:
                    if error.code != 400:
                        raise
                    state["n_supported"] = False  # n>1 rejected (unbilled): fall back to single calls
                    record["n_fallback"] = error.read().decode(errors="replace")[:300]
            while len(texts) < n:
                collect(_post(base, key))
            _write(folder / "candidates.json", texts)
            record.update(status="completed", usage=dict(usage), finish_reasons=finishes, response_ids=raw_ids)
        except urllib.error.HTTPError as error:
            body = error.read().decode(errors="replace").replace(key, "[REDACTED]")
            record.update(status="api_error", http_status=error.code,
                          error=re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", body)[:1000],
                          usage=dict(usage) if usage else None)
        except Exception as error:  # noqa: BLE001 - recorded, never retried silently
            record.update(status="client_error", error_type=type(error).__name__,
                          error=str(error).replace(key, "[REDACTED]")[:500], usage=dict(usage) if usage else None)
        record["wall_seconds"] = time.perf_counter() - started
        _write(folder / "result.json", record)
        with lock:
            state["reserved"] -= worst
            state["spent"] += _cost(record.get("usage"))
            total = state["spent"]
        print("END", row["id"][:16], row["category"], record["status"], len(texts), "cands",
              f"${_cost(record.get('usage')):.4f} total ${total:.3f}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, todo))


def verify(out: Path, python: Path, workers: int) -> None:
    rows = {r["id"]: r for r in train_tasks()}
    folders = [p.parent for p in out.glob("*/candidates.json") if not (p.parent / "verify.json").exists()]

    def one(folder):
        result = json.loads((folder / "result.json").read_text())
        row = rows[result["id"]]
        task = dict(source=row["code"], instruction=row["instruction"], representation=row["representation"],
                    candidates=json.loads((folder / "candidates.json").read_text()),
                    reference_code=row["edited_code"])
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(task, handle)
        try:
            proc = subprocess.run([str(python), str(ROOT / "scripts/cad_edit_verifier.py"), handle.name],
                                  capture_output=True, text=True, timeout=300)
            verdict = json.loads(proc.stdout.splitlines()[-1]) if proc.returncode == 0 else \
                dict(status="verifier_error", error=proc.stderr[-500:])
        except subprocess.TimeoutExpired:
            verdict = dict(status="verifier_timeout")
        finally:
            os.unlink(handle.name)
        verdict.update(id=row["id"], category=row["category"])
        _write(folder / "verify.json", verdict)
        print("VERIFIED", row["id"][:16], verdict.get("status", "ok"), verdict.get("clusters"),
              "selected_ok=", verdict.get("audit_selected_strict"), flush=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, folders))


def report(out: Path) -> dict:
    verdicts = [json.loads(p.read_text()) for p in out.glob("*/verify.json")]
    ok = [v for v in verdicts if "selected" in v]
    rules = {
        "any_executed": lambda v: v["selected"] is not None,
        "consensus>=2": lambda v: v["selected_consensus"] >= 2,
        "consensus>=2_and_numbers": lambda v: v["selected_consensus"] >= 2
        and v["selected_numbers_fraction"] in (None, 1.0),
        "numbers_all_or_consensus>=2": lambda v: v["selected"] is not None
        and (v["selected_consensus"] >= 2 or v["selected_numbers_fraction"] == 1.0),
    }
    per_candidate = [c for v in ok for c in v["candidates"]]
    summary = dict(
        tasks=len(verdicts), verified=len(ok), statuses=dict(Counter(v.get("status", "ok") for v in verdicts)),
        candidates=len(per_candidate),
        candidate_strict_rate=round(sum((c.get("audit_reference_iou") or 0) >= 0.99999 for c in per_candidate)
                                    / max(1, len(per_candidate)), 4),
        oracle_any_strict=sum(v["audit_any_strict"] for v in ok),
        reference_unchanged=sum(not v["audit_reference_changed"] for v in ok),
        cost_usd=round(sum(_cost(json.loads(p.read_text()).get("usage")) for p in out.glob("*/result.json")), 4),
        rules={})
    for name, rule in rules.items():
        accepted = [v for v in ok if rule(v)]
        summary["rules"][name] = dict(accepted=len(accepted),
                                      correct=sum(v["audit_selected_strict"] for v in accepted),
                                      precision=round(sum(v["audit_selected_strict"] for v in accepted)
                                                      / max(1, len(accepted)), 4))
    _write(out / "report.json", summary)
    print(json.dumps(summary, indent=1))
    return summary


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--n", type=int, default=4)
    s.add_argument("--effort", default="low")
    s.add_argument("--cap", type=int, default=4000)
    s.add_argument("--workers", type=int, default=6)
    s.add_argument("--budget", type=float, required=True)
    s.add_argument("--limit", type=int)
    s.add_argument("--skip", type=int, default=0)
    v = sub.add_parser("verify")
    v.add_argument("--out", type=Path, required=True)
    v.add_argument("--python", type=Path, default=ROOT / "tmp/cad-runtime/bin/python")
    v.add_argument("--workers", type=int, default=3)
    r = sub.add_parser("report")
    r.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.cmd == "sample":
        sample(a.out, a.n, a.effort, a.cap, a.workers, a.budget, a.limit, a.skip)
    elif a.cmd == "verify":
        verify(a.out, a.python, a.workers)
    else:
        report(a.out)


if __name__ == "__main__":
    main()
