"""One execution-feedback repair round for Astra's failed held-out answers (multisource CAD test set).

Tasks: answers whose patch failed validation or whose program failed to execute, among tasks with a valid
reference. Astra sees the original system prompt and input, its own previous answer, and the validator or
executor error -- never the reference -- and returns a corrected patch. Scored with the same geometry scorer.

  run   : API calls with a hard USD budget at list price; every request saved; never re-billed
  score : apply repaired patches, run score_multisource_cad_geometry.py, report the new totals
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cad_edit_contracts import apply, target_match  # noqa: E402
from multisource_cad_astra_benchmark import DATA, ENDPOINT, PRICE_IN, PRICE_OUT, _cost, parse, tasks  # noqa: E402

SCORED = ROOT / "runs/multisource-cad-astra-20261004/scored"
ORIGINAL = ROOT / "runs/multisource-cad-astra-20261004"
FIX = ("{problem}\n\nReturn only the corrected JSON patch in the same format, addressing the ORIGINAL program's "
       "zero-based lines.")


def failures() -> list[dict]:
    preds = {json.loads(l)["id"]: json.loads(l) for l in (SCORED / "astra-predictions.jsonl").read_text().splitlines()}
    geom = {json.loads(l)["id"]: json.loads(l) for l in (SCORED / "astra-predictions-geometry.jsonl").read_text().splitlines()}
    out = []
    for i, p in preds.items():
        if not geom[i]["reference_valid"]:
            continue
        if not p["applicable"]:
            out.append(dict(id=i, problem=f"Applying your patch to the original program failed with: {p['error']}"))
        elif not geom[i]["executable"]:
            out.append(dict(id=i, problem="Your patch applied, but the patched program failed to build a valid solid: "
                                          f"{geom[i].get('error')}"))
    return out


def run(out: Path, effort: str, cap: int, budget: float) -> None:
    key = os.environ.get("OPENAI_API_KEY") or sys.exit("OPENAI_API_KEY unavailable; no calls made")
    system = json.loads((DATA / "manifest.json").read_text())["system"]
    rows = {r["id"]: r for r in tasks()}
    out.mkdir(parents=True, exist_ok=True)
    (out / "protocol.json").write_text(json.dumps(dict(model="gpt-6-astra", effort=effort, cap=cap, rounds=1,
                                                       feedback="validator/executor error only; no reference",
                                                       fix_template=FIX), indent=2) + "\n")
    spent = sum(_cost(json.loads(p.read_text()).get("usage")) for p in out.glob("*/result.json"))
    worst = (4000 * PRICE_IN + cap * PRICE_OUT) / 1e6
    for task in failures():
        folder = out / task["id"][:16]
        if (folder / "result.json").exists():
            continue
        if spent + worst > budget:
            print("BUDGET-STOP", task["id"][:16], flush=True)
            continue
        folder.mkdir(parents=True, exist_ok=True)
        previous = (ORIGINAL / task["id"][:16] / "response.txt").read_text()
        messages = [{"role": "system", "content": system}, {"role": "user", "content": rows[task["id"]]["input"]},
                    {"role": "assistant", "content": previous},
                    {"role": "user", "content": FIX.format(problem=task["problem"])}]
        record = dict(id=task["id"], source=rows[task["id"]]["source"], problem=task["problem"],
                      started_utc=datetime.now(timezone.utc).isoformat())
        started = time.perf_counter()
        request = urllib.request.Request(ENDPOINT, data=json.dumps({"model": "gpt-6-astra", "messages": messages,
                                                                    "reasoning_effort": effort,
                                                                    "max_completion_tokens": cap, "store": False}).encode(),
                                         headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=900) as response:
                raw = json.load(response)
            (folder / "response.txt").write_text(raw["choices"][0]["message"].get("content") or "")
            record.update(status="completed", usage=raw.get("usage"), finish_reason=raw["choices"][0].get("finish_reason"))
        except urllib.error.HTTPError as error:
            record.update(status="api_error", http_status=error.code,
                          error=error.read().decode(errors="replace").replace(key, "[REDACTED]")[:800])
        except Exception as error:  # noqa: BLE001
            record.update(status="client_error", error=str(error).replace(key, "[REDACTED]")[:400])
        record["wall_seconds"] = time.perf_counter() - started
        (folder / "result.json").write_text(json.dumps(record, indent=2) + "\n")
        spent += _cost(record.get("usage"))
        print("END", task["id"][:16], record["source"], record["status"], f"${_cost(record.get('usage')):.4f} "
              f"total ${spent:.3f}", flush=True)


def score(out: Path, python: Path) -> None:
    rows = {r["id"]: r for r in tasks()}
    original = {json.loads(l)["id"]: json.loads(l) for l in (SCORED / "astra-predictions.jsonl").read_text().splitlines()}
    repaired = []
    for res in (json.loads(p.read_text()) for p in out.glob("*/result.json")):
        r, p = rows[res["id"]], dict(original[res["id"]])
        text = (out / res["id"][:16] / "response.txt").read_text() if res.get("status") == "completed" else ""
        try:
            patch, _ = parse(text)
            code = apply(r["code"], patch, r["representation"])
            p.update(prediction=text, applicable=True, error=None, predicted_code=code,
                     target_match=target_match(code, r["edited_code"], r["representation"]))
        except Exception as e:  # noqa: BLE001
            p.update(prediction=text, applicable=False, predicted_code=None, error=type(e).__name__ + ": " + str(e)[:200])
        repaired.append(p)
    path = out / "repaired-predictions.jsonl"
    path.write_text("".join(json.dumps(p) + "\n" for p in repaired))
    subprocess.run([str(python), str(ROOT / "scripts/score_multisource_cad_geometry.py"), str(path)], check=True,
                   stdout=subprocess.DEVNULL)
    geom = [json.loads(l) for l in (out / "repaired-predictions-geometry.jsonl").read_text().splitlines()]
    base = {json.loads(l)["id"]: json.loads(l) for l in (SCORED / "astra-predictions-geometry.jsonl").read_text().splitlines()}
    total = sum(g["match_strict"] for g in base.values()) + sum(g["match_strict"] for g in geom)
    summary = dict(repaired=len(repaired), now_valid=sum(p["applicable"] for p in repaired),
                   now_executable=sum(g["executable"] is True for g in geom), now_strict=sum(g["match_strict"] for g in geom),
                   by_source={s: sum(g["match_strict"] for g in geom if g["source"] == s) for s in ("BenchCAD", "CAD-Editor")},
                   astra_strict_before=sum(g["match_strict"] for g in base.values()), astra_strict_after=total,
                   cost_usd=round(sum(_cost(json.loads(p.read_text()).get("usage")) for p in out.glob("*/result.json")), 4))
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=1))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--effort", default="low")
    r.add_argument("--cap", type=int, default=2500)
    r.add_argument("--budget", type=float, required=True)
    s = sub.add_parser("score")
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--python", type=Path, default=ROOT / "tmp/cad-runtime/bin/python")
    a = p.parse_args()
    if a.cmd == "run":
        run(a.out, a.effort, a.cap, a.budget)
    else:
        score(a.out, a.python)


if __name__ == "__main__":
    main()
