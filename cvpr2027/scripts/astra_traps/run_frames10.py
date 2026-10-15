"""Run Astra once on each of ten large frame tasks, sequentially, under a hard USD cap; classify each answer.

Outcomes: declined (analysis status 'unavailable' / null numbers), correct (ux, uy and peak stress within 2 % or the
benchmark's absolute tolerances), wrong (numbers outside), no_json (no parseable analysis), truncated.

  OPENAI_API_KEY=... PYTHONPATH=src ../.venv/bin/python scripts/astra_traps/run_frames10.py --budget-usd 6
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/astra-frames10-20261015"
PLAN = [("data/eng-frame-bench-xxl", t) for t in ("fourbay_four_edit", "threebay_six_generate", "threebay_six_edit", "fivebay_five_edit")] + \
       [("data/eng-frame-bench-xxl2", t) for t in ("sixbay_three_generate", "sixbay_three_edit", "twobay_eight_generate", "twobay_eight_edit",
                                                   "fourbay_six_setback_generate", "fourbay_six_setback_edit")]
P_IN, P_OUT, CAP = 12.5, 50.0, 16000


def analysis(txt: str):
    """The analysis object, from a bare JSON answer or from the last fenced json block."""
    try:
        d = json.loads(txt)
        if isinstance(d, dict):
            return d.get("analysis", d)
    except Exception:                                             # noqa: BLE001
        pass
    blocks = re.findall(r"```(?:json|JSON)?\s*(.*?)```", txt, re.S)
    for b in reversed(blocks):
        try:
            d = json.loads(b)
        except Exception:                                         # noqa: BLE001
            continue
        return d.get("analysis", d)
    return None


def close(v, ref, rtol, atol):
    return isinstance(v, (int, float)) and abs(v - ref) <= max(rtol * abs(ref), atol)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget-usd", type=float, required=True)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rows, spent = [], 0.0
    for data, tid in PLAN:
        run = OUT / tid
        res = run / tid / "sample-0" / "response.json"
        if not res.exists():
            worst = (12000 * P_IN + CAP * P_OUT) / 1e6
            if spent + worst > a.budget_usd:
                print(f"BUDGET-STOP before {tid}: spent ${spent:.3f}, worst-case call ${worst:.2f}", flush=True)
                break
            subprocess.run([sys.executable, str(ROOT / "scripts/cad_astra_benchmark.py"), "run", "--data", str(ROOT / data), "--output", str(run),
                            "--samples", "1", "--workers", "1", "--cap", str(CAP), "--ids", tid], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        if not res.exists():
            rows.append(dict(id=tid, outcome="api_or_harness_error"))
            print(f"{tid}: no response", flush=True)
            continue
        raw = json.loads(res.read_text())
        u = raw.get("usage") or {}
        cost = (u.get("prompt_tokens", 0) * P_IN + u.get("completion_tokens", 0) * P_OUT) / 1e6
        spent += cost
        task = next(t for t in json.loads((ROOT / data / "tasks.json").read_text())["tasks"] if t["id"] == tid)
        ref, lim = task["reference"], json.loads((ROOT / data / "tasks.json").read_text())["criteria"]
        choice = raw["choices"][0]
        an = analysis(choice["message"].get("content") or "")
        if choice.get("finish_reason") != "stop":
            outcome = "truncated"
        elif an is None:
            outcome = "no_json"
        elif str(an.get("status", "")).lower() == "unavailable" or an.get("uy_mm") is None:
            outcome = "declined"
        else:
            ok = (close(an.get("ux_mm"), ref["ux_mm"], lim["numeric_rtol"], lim["displacement_atol_mm"]) and
                  close(an.get("uy_mm"), ref["uy_mm"], lim["numeric_rtol"], lim["displacement_atol_mm"]) and
                  close(an.get("peak_stress_mpa"), ref["peak_stress_mpa"], lim["numeric_rtol"], lim["stress_atol_mpa"]))
            outcome = "correct" if ok else "wrong"
        row = dict(id=tid, members=task["members"], indeterminacy=task["indeterminacy"], mode=task["mode"], outcome=outcome,
                   reported={k: (an or {}).get(k) for k in ("ux_mm", "uy_mm", "peak_stress_mpa", "status")},
                   reference={k: round(ref[k], 4) for k in ("ux_mm", "uy_mm", "peak_stress_mpa")},
                   completion_tokens=u.get("completion_tokens"), reasoning_tokens=(u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                   cost_usd=round(cost, 4))
        rows.append(row)
        print(f"{tid:30s} {task['members']:3d} members  {outcome:9s} ${cost:.3f}  total ${spent:.3f}", flush=True)
    (OUT / "summary.json").write_text(json.dumps(dict(spent_usd=round(spent, 4), rows=rows), indent=1) + "\n")
    print(json.dumps({o: sum(r["outcome"] == o for r in rows) for o in ("declined", "correct", "wrong", "no_json", "truncated", "api_or_harness_error")}))


if __name__ == "__main__":
    main()
