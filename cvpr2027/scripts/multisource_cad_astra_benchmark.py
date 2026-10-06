"""Astra (OpenAI API) on the 252-task multisource CAD-edit holdout, under the 3B model's exact interface.

Astra receives the same system prompt and user input as the fine-tuned Qwen2.5-Coder-3B
(data/multisource-cad-edits-v1/manifest.json system, test-retained.jsonl input) and must return the same
zero-based line-patch JSON. Its patches are applied with cad_edit_contracts.apply and executed by
score_multisource_cad_geometry.py, the scorer used for the 3B results. The only interface difference is a
lenient parse: a fenced or prose-wrapped JSON object is accepted, which can only help Astra.

  run   : call the API in a stratified hash order; a task starts only if its worst-case cost still fits
          the USD budget at list price, so the budget cannot be exceeded. Every request is saved and an
          attempted task is never re-billed.
  score : write scorer-format predictions for Astra and for the saved 3B base/final predictions restricted
          to the tasks Astra attempted, then run the geometry scorer on all of them with the same runtime.
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
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cad_edit_contracts import apply, target_match  # noqa: E402

VERSION = "multisource-cad-astra-v1"
ENDPOINT = "https://api.openai.com/v1/chat/completions"
RESULTS = ROOT / "runs/multisource-cad-colab-20261002/results-final"
DATA = ROOT / "data/multisource-cad-edits-v1"
PRICE_IN, PRICE_OUT = 10.0, 50.0  # USD per million tokens, gpt-6-astra list price
INPUT_TOKEN_BOUND = 2500  # every test input is under 4,400 characters plus a 450-character system prompt


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _cost(usage: dict | None) -> float:
    usage = usage or {}
    return (usage.get("prompt_tokens", 0) * PRICE_IN + usage.get("completion_tokens", 0) * PRICE_OUT) / 1e6


def _round_robin(queues: list[list]) -> list:
    ordered = []
    while any(queues):
        for queue in queues:
            if queue:
                ordered.append(queue.pop(0))
    return ordered


def tasks() -> list[dict]:
    """All 252 retained test rows: sources alternate; categories rotate within a source; sha256(id) order."""
    rows = [json.loads(line) for line in (RESULTS / "test-retained.jsonl").read_text().splitlines()]
    strata: dict[tuple, list] = {}
    for row in sorted(rows, key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest()):
        strata.setdefault((row["source"], row["category"]), []).append(row)
    per_source = [_round_robin([strata[k] for k in sorted(strata) if k[0] == source])
                  for source in ("BenchCAD", "CAD-Editor")]
    return _round_robin(per_source)


def api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY unavailable; no calls made")
    return key


def run(out: Path, model: str, effort: str, cap: int, workers: int, budget: float, limit: int | None) -> None:
    system = json.loads((DATA / "manifest.json").read_text())["system"]
    todo = tasks()[:limit]
    key = api_key()
    out.mkdir(parents=True, exist_ok=True)
    protocol = {"version": VERSION, "model": model, "endpoint": ENDPOINT, "effort": effort, "cap": cap,
                "system_sha256": hashlib.sha256(system.encode()).hexdigest(),
                "test_sha256": hashlib.sha256((RESULTS / "test-retained.jsonl").read_bytes()).hexdigest(),
                "order": "sources alternate; categories round-robin within source; sha256(id) within stratum",
                "price_usd_per_million": {"input": PRICE_IN, "output": PRICE_OUT},
                "tools": [], "store": False}
    path = out / "protocol.json"
    if path.exists() and json.loads(path.read_text()) != protocol:
        raise SystemExit("protocol mismatch; use a fresh output directory")
    _write(path, protocol)
    worst = (INPUT_TOKEN_BOUND * PRICE_IN + cap * PRICE_OUT) / 1e6
    lock = threading.Lock()
    state = {"spent": sum(_cost(json.loads(p.read_text()).get("usage")) for p in out.glob("*/result.json")),
             "reserved": 0.0}

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
        payload = {"model": model, "messages": [{"role": "system", "content": system},
                                                {"role": "user", "content": row["input"]}],
                   "reasoning_effort": effort, "max_completion_tokens": cap, "store": False}
        record = {"id": row["id"], "source": row["source"], "category": row["category"], "status": "started",
                  "started_utc": datetime.now(timezone.utc).isoformat()}
        _write(folder / "result.json", record)
        started = time.perf_counter()
        request = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
                                         headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=900) as response:
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
            state["reserved"] -= worst
            state["spent"] += _cost(record.get("usage"))
            total = state["spent"]
        print("END", row["id"][:16], row["source"], row["category"], record["status"], record.get("finish_reason"),
              f"${_cost(record.get('usage')):.4f} total ${total:.3f}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, todo))


def parse(text: str):
    """Return (patch, lenient) where lenient marks output the 3B parser would have rejected."""
    st = text.strip()
    if st.startswith("```"):
        st = "\n".join(st.splitlines()[1:-1])
    try:
        return json.loads(st), False
    except ValueError:
        pass
    for match in re.finditer(r"\{", text):
        try:
            value, _ = json.JSONDecoder().raw_decode(text[match.start():])
            if isinstance(value, dict) and "edits" in value:
                return value, True
        except ValueError:
            continue
    raise ValueError("No JSON patch object")


def _reference_index() -> dict[str, Path]:
    found = {}
    for path in (ROOT / "data").glob("**/*.step"):
        found.setdefault(path.name, []).append(path)
    return found


def _local_reference(row: dict, index: dict) -> str | None:
    if not row.get("reference_step"):
        return None
    for path in index.get(Path(row["reference_step"]).name, []):
        if hashlib.sha256(path.read_bytes()).hexdigest() == row["reference_step_sha256"]:
            return str(path)
    raise SystemExit(f"reference STEP missing for {row['id']}")


def score(out: Path, python: Path) -> None:
    rows = {r["id"]: r for r in tasks()}
    results = {json.loads(p.read_text())["id"]: json.loads(p.read_text()) for p in out.glob("*/result.json")}
    attempted = [i for i in rows if i in results]
    index = _reference_index()
    predictions = []
    for i in attempted:
        r, res = rows[i], results[i]
        text = (out / i[:16] / "response.txt").read_text() if (out / i[:16] / "response.txt").exists() else ""
        error = patch = code = None
        lenient = match = False
        try:
            if res["status"] != "completed":
                raise ValueError("API " + res["status"])
            if res.get("finish_reason") != "stop":
                raise ValueError("finish_reason " + str(res.get("finish_reason")))
            patch, lenient = parse(text)
            code = apply(r["code"], patch, r["representation"])
            match = target_match(code, r["edited_code"], r["representation"])
        except Exception as e:  # noqa: BLE001
            error = type(e).__name__ + ": " + str(e)[:250]
        predictions.append(dict(id=i, source=r["source"], representation=r["representation"],
                                component_id=r["component_id"], category=r["category"], prediction=text,
                                applicable=error is None, exact_patch=patch == json.loads(r["target"]),
                                target_match=match, lenient_parse=lenient, error=error, predicted_code=code,
                                reference_code=r["edited_code"], reference_step=_local_reference(r, index),
                                reference_step_sha256=r.get("reference_step_sha256"),
                                generation_cap_hit=res.get("finish_reason") == "length"))
    scored = out / "scored"
    scored.mkdir(exist_ok=True)
    (scored / "astra-predictions.jsonl").write_text("".join(json.dumps(p) + "\n" for p in predictions))
    for label in ("base", "trained"):
        saved = {json.loads(line)["id"]: json.loads(line)
                 for line in (RESULTS / f"{label}-predictions.jsonl").read_text().splitlines()}
        subset = []
        for i in attempted:
            p = dict(saved[i])
            p["reference_step"] = _local_reference(p, index)
            subset.append(p)
        (scored / f"{label}-predictions.jsonl").write_text("".join(json.dumps(p) + "\n" for p in subset))
    for label in ("astra", "trained", "base"):
        subprocess.run([str(python), str(ROOT / "scripts/score_multisource_cad_geometry.py"),
                        str(scored / f"{label}-predictions.jsonl")], check=True, stdout=subprocess.DEVNULL)
    summarize(out)


def summarize(out: Path) -> None:
    scored = out / "scored"
    results = [json.loads(p.read_text()) for p in out.glob("*/result.json")]
    usage = Counter()
    for r in results:
        for k in ("prompt_tokens", "completion_tokens"):
            usage[k] += (r.get("usage") or {}).get(k, 0)
    summary = {"attempted": len(results), "statuses": dict(Counter(r["status"] for r in results)),
               "finish_reasons": dict(Counter(str(r.get("finish_reason")) for r in results)),
               "usage": dict(usage), "cost_usd_list_price": round(sum(_cost(r.get("usage")) for r in results), 4),
               "systems": {}}
    for label in ("astra", "trained", "base"):
        preds = [json.loads(line) for line in (scored / f"{label}-predictions.jsonl").read_text().splitlines()]
        geom = {json.loads(line)["id"]: json.loads(line)
                for line in (scored / f"{label}-predictions-geometry.jsonl").read_text().splitlines()}

        def counts(ps):
            return dict(n=len(ps), applicable=sum(p["applicable"] for p in ps),
                        executed=sum(geom[p["id"]]["executable"] is True for p in ps),
                        match_95=sum(geom[p["id"]]["match_95"] for p in ps),
                        match_strict=sum(geom[p["id"]]["match_strict"] for p in ps),
                        exact_patch=sum(p["exact_patch"] for p in ps),
                        program_match=sum(p["target_match"] for p in ps),
                        lenient_parse=sum(p.get("lenient_parse", False) for p in ps))
        entry = counts(preds)
        entry["sources"] = {s: counts([p for p in preds if p["source"] == s]) for s in ("BenchCAD", "CAD-Editor")}
        summary["systems"][label] = entry
    # paired strict-match table, Astra versus final 3B, on identical tasks
    a = {json.loads(l)["id"]: json.loads(l)["match_strict"]
         for l in (scored / "astra-predictions-geometry.jsonl").read_text().splitlines()}
    t = {json.loads(l)["id"]: json.loads(l)["match_strict"]
         for l in (scored / "trained-predictions-geometry.jsonl").read_text().splitlines()}
    summary["paired_strict"] = {"both": sum(a[i] and t[i] for i in a), "astra_only": sum(a[i] and not t[i] for i in a),
                                "trained_only": sum(t[i] and not a[i] for i in a),
                                "neither": sum(not a[i] and not t[i] for i in a)}
    _write(out / "summary.json", summary)
    print(json.dumps(summary, indent=1))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--model", default="gpt-6-astra")
    r.add_argument("--effort", default="medium")
    r.add_argument("--cap", type=int, default=6000)
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--budget", type=float, required=True)
    r.add_argument("--limit", type=int)
    s = sub.add_parser("score")
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--python", type=Path, default=ROOT / "tmp/cad-runtime/bin/python")
    a = p.parse_args()
    if a.cmd == "run":
        run(a.out, a.model, a.effort, a.cap, a.workers, a.budget, a.limit)
    else:
        score(a.out, a.python)


if __name__ == "__main__":
    main()
