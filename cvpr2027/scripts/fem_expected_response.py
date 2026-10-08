"""Expected-response FEM checker: predict how the *correct* edit should change the part's FEM response, then prefer the
draft whose response is closest to that prediction.

With the true target's response known, this rule picks the correct Astra draft in 35 of 38 decisive test comparisons
(fem_score_learned.py ceiling); a learned score of the response alone is at chance. The question here is how much of
that survives when the expected response must be predicted without the target.

  targets   FEM response (log compliance ratio, log p95 von Mises ratio to the source) of the reference edit for every
            BenchCAD training task (scenario of mechanical_cad_fem.py: fixed base, 1 N axial top load)
  predictor ridge regression from target-free inputs: instruction edit type and stated values, BenchCAD category, the
            source's size and FEM response; trained on training components, checked on held-out components
  baselines consensus (median response of a task's drafts) and the oracle (true target response)

  python fem_expected_response.py targets [--workers 9]
  python fem_expected_response.py evaluate
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
from pathlib import Path
import re
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dpo_checker as dc  # noqa: E402

TARGETS = dc.OUT / "fem-reference-responses.jsonl"
WORDS = ["increase", "decrease", "reduce", "enlarge", "shrink", "extend", "shorten", "add", "remove", "delete", "cut", "drill",
         "hole", "bore", "slot", "recess", "pocket", "boss", "rib", "fillet", "chamfer", "bevel", "rotate", "mirror", "move",
         "translate", "scale", "height", "length", "width", "thick", "radius", "diameter", "depth", "through", "blind", "twice",
         "half", "third", "equal"]
CATS = ["T1", "T2", "T3", "T4", "T5"]


def response(src_fem: dict | None, fem: dict | None):
    if not (src_fem and src_fem.get("ok") and fem and fem.get("ok")):
        return None
    return (math.log(fem["compliance"] / src_fem["compliance"]),
            math.log(max(fem["vm_p95"], 1e-12) / max(src_fem["vm_p95"], 1e-12)))


def targets(workers: int) -> None:
    rows = dc.train_rows()
    done = {json.loads(l)["task"] for l in TARGETS.read_text().splitlines()} if TARGETS.exists() else set()
    jobs = [r for r in rows.values() if r["id"] not in done]

    def one(row):
        res = dc.worker(row["code"], [row["edited_code"]], None, fem=True)
        if res is None:
            return dict(task=row["id"], error="worker failed")
        return dict(task=row["id"], source=res["source"], source_fem=res["source_fem"], reference_fem=res["candidates"][0].get("fem"),
                    reference=res["candidates"][0])
    with ThreadPoolExecutor(workers) as pool, TARGETS.open("a") as handle:
        for n, fut in enumerate(as_completed([pool.submit(one, r) for r in jobs]), 1):
            handle.write(json.dumps(fut.result()) + "\n"); handle.flush()
            if n % 50 == 0:
                print("TARGETS", n, "/", len(jobs), flush=True)


def stated_ratio(text: str) -> tuple[float, float]:
    """log(B/A) for 'from A to B' and a flag; 0 otherwise."""
    m = re.search(r"from\s+(-?\d+(?:\.\d+)?)\s*(?:mm|deg|degrees|°)?\s+to\s+(-?\d+(?:\.\d+)?)", text)
    if m and float(m.group(1)) > 0 and float(m.group(2)) > 0:
        return math.log(float(m.group(2)) / float(m.group(1))), 1.0
    return 0.0, 0.0


def inputs(row: dict, src: dict, src_fem: dict) -> np.ndarray:
    t = row["instruction"].lower()
    words = [float(w in t) for w in WORDS]
    cat = [float(row["category"] == c) for c in CATS]
    r, flag = stated_ratio(t)
    bb = sorted(src["bbox"])
    size = [math.log(max(src["volume"], 1e-9)) / 10, math.log(max(bb[2], 1e-9) / max(bb[0], 1e-9)) / 3,
            math.log(src_fem["compliance"]) / 10 if src_fem and src_fem.get("ok") else 0.0]
    inter = [r * w for w in words[:7]]  # stated change interacting with its direction words
    return np.array(words + cat + [r, flag, abs(r)] + size + inter + [1.0])


def ridge(X: np.ndarray, Y: np.ndarray, lam: float) -> np.ndarray:
    return np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ Y)


def evaluate() -> None:
    rows, trows = dc.train_rows(), dc.test_rows()
    tr, dv = [], []
    for rec in dc.jl(TARGETS):
        if "error" in rec:
            continue
        y = response(rec["source_fem"], rec["reference_fem"])
        if y is None:
            continue
        row = rows[rec["task"]]
        (tr if dc.split_of(row["component_id"]) == "train" else dv).append((inputs(row, rec["source"], rec["source_fem"]), np.array(y)))
    Xtr, Ytr = np.array([x for x, _ in tr]), np.array([y for _, y in tr])
    Xdv, Ydv = np.array([x for x, _ in dv]), np.array([y for _, y in dv])
    best = None
    for lam in (0.1, 1.0, 10.0, 100.0):
        W = ridge(Xtr, Ytr, lam)
        err = float(((Xdv @ W - Ydv) ** 2).mean())
        if best is None or err < best[0]:
            best = (err, lam, W)
    err, lam, W = best
    base = float(((Ydv - Ytr.mean(0)) ** 2).mean())
    r2 = 1 - err / base
    W = ridge(np.vstack([Xtr, Xdv]), np.vstack([Ytr, Ydv]), lam)  # refit on all training tasks for test use
    print(f"training targets {len(Xtr)} + {len(Xdv)} held-out; held-out R^2 {r2:.3f} (lambda {lam})")

    geo = {r["id"]: r["match_strict"] for r in dc.jl(dc.GOT / "all-drafts-predictions-geometry.jsonl")}
    ok = {(r["id"].split("#")[0], r["predicted_code"]): geo[r["id"]] for r in dc.jl(dc.GOT / "all-drafts-predictions.jsonl")}
    astra = {r["id"]: r["match_strict"] for r in dc.jl(dc.ASTRA_TEST)}
    ev = {r["task"]: r for r in dc.jl(dc.OUT / "evidence.jsonl") if r.get("split") == "test" and "drafts" in r}
    methods = {"predicted (ridge)": {}, "consensus (median of drafts)": {}}
    for t, rec in ev.items():
        valid = [d for d in rec["drafts"] if "error" not in d and response(rec["source_fem"], d.get("fem")) is not None]
        if len(valid) < 2:
            continue
        resp = {d["code"]: np.array(response(rec["source_fem"], d["fem"])) for d in valid}
        methods["predicted (ridge)"][t] = (inputs(trows[t], rec["source"], rec["source_fem"]) @ W, resp)
        methods["consensus (median of drafts)"][t] = (np.median(np.array(list(resp.values())), axis=0), resp)
    out = {}
    for name, per in methods.items():
        right = wrong = tie = 0
        replace = gain = loss = 0
        for t, (exp, resp) in per.items():
            inc = next((d["code"] for d in ev[t]["drafts"] if "vanilla" in d["origins"]), None)
            if inc not in resp:  # Astra's own answer has no FEM response (does not build or solve): keep it
                continue
            dist = {c: float(np.abs(v - exp).sum()) for c, v in resp.items()}
            for c in resp:
                if c != inc and ok[(t, c)] != astra[t]:  # decisive comparison: exactly one of the two is correct
                    if abs(dist[c] - dist[inc]) < 1e-9:
                        tie += 1
                    elif (dist[c] < dist[inc]) == ok[(t, c)]:
                        right += 1
                    else:
                        wrong += 1
            pick = min(dist, key=dist.get)
            if pick != inc:
                replace += 1; gain += ok[(t, pick)] and not astra[t]; loss += astra[t] and not ok[(t, pick)]
        n = right + wrong + tie
        out[name] = dict(decisive=n, correct=right, wrong=wrong, tie=tie, accuracy=round((right + 0.5 * tie) / max(1, n), 3),
                         replaced=replace, gained=int(gain), lost=int(loss), score=sum(astra[t] for t in trows) + int(gain) - int(loss))
        print(name, json.dumps(out[name]))
    out["held_out_r2"] = round(r2, 3)
    (dc.OUT / "fem-expected-response.json").write_text(json.dumps(out, indent=1))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("targets", "evaluate"))
    p.add_argument("--workers", type=int, default=9)
    a = p.parse_args()
    targets(a.workers) if a.cmd == "targets" else evaluate()


if __name__ == "__main__":
    main()
