"""Repair loop for CAD edit answers: diagnose -> deterministic repair -> (optional) model repair -> re-verify.

Every step is target-free. A diagnosis runs the answer through the patch contract and the CAD executor and reports
the failing stage (parse, apply, syntax, execute) with the error and, where known, the offending line. Deterministic
repairs are tried first and cost nothing:
  CadQuery     re-indent or de-indent inserted lines (unexpected/expected indent errors)
  CAD-Editor   clamp coordinates to the 6-bit range 0..63, round non-integers, trim surplus fields of curve
               commands, insert missing <curve_end>/<extrude_end> terminators
A repair is accepted only if it moves the answer to a later stage (parse < apply < execute < valid solid), so the
loop never makes an answer worse. Model repair (student or Astra) plugs in through a callable and is optional.

  python cad_repair_loop.py eval --system astra|student      (deterministic layer on saved test answers)
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cad_edit_contracts import apply, validate_sequence  # noqa: E402
from cad_edit_verifier import extract  # noqa: E402

PYTHON = ROOT / "tmp/cad-runtime/bin/python"
STAGES = ("parse", "apply", "execute", "valid")
ARITY = {"line": 3, "arc": 5, "circle": 9, "add": 18, "cut": 18, "intersect": 18}
EXEC = r'''
import json, sys
sys.path.insert(0, sys.argv[2])
job = json.load(open(sys.argv[1]))
try:
    if job["representation"] == "cadquery":
        from verify_mechanical_cad_edits import execute; execute(job["code"])
    else:
        from cad_editor_geometry import execute_sequence; execute_sequence(job["code"])
    print(json.dumps({"ok": True}))
except Exception as e:
    print(json.dumps({"ok": False, "error": type(e).__name__ + ": " + str(e)[:200]}))
'''


def execute(code: str, representation: str) -> dict:
    with tempfile.TemporaryDirectory() as d:
        Path(d, "w.py").write_text(EXEC)
        Path(d, "j.json").write_text(json.dumps(dict(code=code, representation=representation)))
        try:
            p = subprocess.run([str(PYTHON), str(Path(d, "w.py")), str(Path(d, "j.json")), str(ROOT / "scripts")],
                               capture_output=True, text=True, timeout=90)
            return json.loads(p.stdout.strip().splitlines()[-1])
        except Exception as e:  # noqa: BLE001
            return dict(ok=False, error="TimeoutOrWorker: " + type(e).__name__)


def diagnose(row: dict, text: str) -> dict:
    """Furthest stage reached: 0 parse failed, 1 patch/syntax failed, 2 execution failed, 3 valid solid."""
    try:
        _, patch = extract(text)
    except Exception as e:  # noqa: BLE001
        return dict(stage=0, error=f"{type(e).__name__}: {str(e)[:160]}", patch=None, code=None)
    try:
        code = apply(row["code"], patch, row["representation"])
    except Exception as e:  # noqa: BLE001
        return dict(stage=1, error=f"{type(e).__name__}: {str(e)[:160]}", patch=patch, code=None)
    res = execute(code, row["representation"])
    return dict(stage=3 if res["ok"] else 2, error=res.get("error"), patch=patch, code=code)


def fix_sequence_line(line: str) -> str:
    token = line.strip()
    if "," not in token:
        return line
    parts = token.split(",")
    cmd = parts[0]
    if cmd not in ARITY:
        return line
    nums = []
    for x in parts[1:]:
        try:
            nums.append(float(x))
        except ValueError:
            return line
    if cmd in ("line", "arc", "circle") and len(nums) > ARITY[cmd] - 1:
        nums = nums[:ARITY[cmd] - 1]  # surplus fields on a curve command
    fixed = []
    for k, v in enumerate(nums):
        v = round(v)
        coordinate = cmd in ("line", "arc", "circle") or k < 5 or k >= 14  # as validate_sequence: nums[:5] + nums[14:]
        if coordinate:
            v = min(63, max(0, v))
        elif cmd in ("add", "cut", "intersect") and 5 <= k < 14:
            v = min(1, max(-1, v))  # rotation-matrix entries
        fixed.append(str(int(v)))
    return ",".join([cmd] + fixed)


def add_terminators(lines: list[str]) -> list[str]:
    out = []
    for k, line in enumerate(lines):
        out.append(line)
        cmd = line.strip().split(",")[0]
        nxt = lines[k + 1].strip() if k + 1 < len(lines) else ""
        if cmd in ("line", "arc", "circle") and nxt != "<curve_end>":
            out.append("<curve_end>")
        if cmd in ("add", "cut", "intersect") and nxt != "<extrude_end>":
            out.append("<extrude_end>")
    return out


def deterministic_variants(row: dict, diag: dict) -> list[dict]:
    """Candidate repaired patches for a diagnosed failure (most conservative first)."""
    patch = diag.get("patch")
    if not patch or "edits" not in patch:
        return []
    variants = []
    if row["representation"] == "cad-editor-sequence":
        v = {"edits": [dict(op, insert=[fix_sequence_line(x) for x in op["insert"]]) for op in patch["edits"]]}
        variants.append(v)
        variants.append({"edits": [dict(op, insert=add_terminators(op["insert"])) for op in v["edits"]]})
    else:
        lines = row["code"].splitlines()
        for mode in ("dedent", "context"):
            ops = []
            for op in patch["edits"]:
                if mode == "dedent":
                    ins = [x.lstrip() if not x.lstrip().startswith(".") else x for x in op["insert"]]
                else:
                    ref = lines[op["start"]] if op["start"] < len(lines) else (lines[-1] if lines else "")
                    indent = ref[:len(ref) - len(ref.lstrip())]
                    ins = [indent + x.lstrip() for x in op["insert"]]
                ops.append(dict(op, insert=ins))
            variants.append({"edits": ops})
    return variants


def repair(row: dict, text: str, model_repair=None, rounds: int = 3) -> dict:
    """Monotone repair loop; returns the best answer and its trace."""
    best_text, best = text, diagnose(row, text)
    trace = [dict(step="initial", stage=best["stage"], error=best["error"])]
    for r in range(rounds):
        if best["stage"] == 3:
            break
        improved = False
        for v in deterministic_variants(row, best):
            cand = json.dumps(v)
            d = diagnose(row, cand)
            if d["stage"] > best["stage"]:
                best_text, best, improved = cand, d, True
                trace.append(dict(step=f"round{r + 1}-deterministic", stage=d["stage"], error=d["error"]))
                break
        if best["stage"] == 3 or model_repair is None:
            if not improved:
                break
            continue
        cand = model_repair(row, best_text, f"Failure at the {STAGES[best['stage']]} stage: {best['error']}")
        if cand:
            d = diagnose(row, cand)
            trace.append(dict(step=f"round{r + 1}-model", stage=d["stage"], error=d["error"]))
            if d["stage"] > best["stage"]:
                best_text, best = cand, d
    return dict(text=best_text, stage=best["stage"], code=best["code"], trace=trace)


def evaluate(system: str, workers: int) -> None:
    from multisource_cad_astra_benchmark import _local_reference, _reference_index, tasks
    rows = {r["id"]: r for r in tasks()}
    out = ROOT / f"runs/cad-repair-loop-20261007/{system}"
    out.mkdir(parents=True, exist_ok=True)
    if system == "astra":
        answers = {i: (ROOT / "runs/multisource-cad-astra-20261004" / i[:16] / "response.txt").read_text() for i in rows}
    else:  # student greedy answers, quote-anchored as deployed
        from best_of_n_select import anchored_text
        recs = [json.loads(l) for l in (ROOT / "runs/bestofn-student-20261006/samples.jsonl").read_text().splitlines()]
        answers = {r["id"]: anchored_text(rows[r["id"]]["code"], r["greedy"]) for r in recs if r["id"] in rows}
    index = _reference_index()

    def one(i):
        res = repair(rows[i], answers[i])
        return i, res
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = dict(pool.map(one, list(answers)))
    preds = []
    for i, res in results.items():
        r = rows[i]
        preds.append(dict(id=i, source=r["source"], category=r["category"], representation=r["representation"],
                          predicted_code=res["code"], error=None if res["code"] else "unrepaired", applicable=res["code"] is not None,
                          prediction=res["text"], reference_code=r["edited_code"], reference_step_sha256=r.get("reference_step_sha256"),
                          reference_step=_local_reference(r, index) if r.get("reference_step") else None))
    (out / "repaired-predictions.jsonl").write_text("".join(json.dumps(p) + "\n" for p in preds))
    (out / "traces.json").write_text(json.dumps({i: r["trace"] for i, r in results.items()}, indent=1))
    from collections import Counter
    first = Counter(r["trace"][0]["stage"] for r in results.values())
    final = Counter(r["stage"] for r in results.values())
    fixed = sum(r["stage"] > r["trace"][0]["stage"] for r in results.values())
    print(json.dumps(dict(system=system, tasks=len(results), stage_before=dict(first), stage_after=dict(final),
                          repaired=fixed)))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("eval",))
    p.add_argument("--system", choices=("astra", "student"), required=True)
    p.add_argument("--workers", type=int, default=4)
    a = p.parse_args()
    evaluate(a.system, a.workers)


if __name__ == "__main__":
    main()
