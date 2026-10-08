"""Learned continuous FEM checker: a pairwise scorer of edit correctness from FEM (and geometry) responses.

The hierarchical verifier uses FEM as a pass/fail gate. Here a linear score s(x) = w.x over target-free response
features of an edited part relative to its source is trained so that, within a training task, the correct edit
scores above a valid-but-wrong one (pairwise logistic loss, L2). Feature groups:

  fem       log compliance ratio, log p95 von Mises ratio, their magnitudes, solve flag, availability
  geometry  log volume ratio, 1 - volume IoU and 1 - Surface IoU with the source, face-count change,
            bounding-box change, requested-values check

Pairs come from dpo_checker.py evidence (BenchCAD training tasks: Astra/Qwen drafts and the reference) plus
dpo_hard_negatives.py negatives, split by component exactly as the DPO checker. Evaluation mirrors the checker:
pairwise accuracy on development pairs, accuracy on test comparisons of Astra's answer against its other drafts
where exactly one is correct, and Astra test score when a challenger replaces the answer only above a margin
chosen on development tasks.

  python fem_score_learned.py
"""
from __future__ import annotations

from collections import defaultdict
import json
import math
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dpo_checker as dc  # noqa: E402
from cad_edit_verifier import numeric_checks  # noqa: E402

GROUPS = {"fem": list(range(0, 6)), "geometry": list(range(6, 15))}


def features(d: dict, src: dict, src_fem: dict | None, row: dict) -> np.ndarray:
    f = d.get("fem") or {}
    have = bool(src_fem and src_fem.get("ok"))
    ok = have and bool(f.get("ok"))
    lc = math.log(f["compliance"] / src_fem["compliance"]) if ok else 0.0
    ls = math.log(max(f["vm_p95"], 1e-12) / max(src_fem["vm_p95"], 1e-12)) if ok else 0.0
    fem = [lc, ls, abs(lc), abs(ls), float(ok), float(have)]
    diag = math.sqrt(sum(x * x for x in src["bbox"])) or 1.0
    nums = numeric_checks(row["instruction"], row["code"], {"edits": dc.ops(row["code"], d["code"])})
    num = 0.5 if not nums else float(all(n["ok"] for n in nums))
    geo = [math.log(max(d["volume"], 1e-9) / max(src["volume"], 1e-9)), 1 - d["iou_source"], 1 - d.get("surface_iou_source", 1.0),
           (d["faces"] - src["faces"]) / 10, abs(d["faces"] - src["faces"]) / 10,
           sum(abs(b - a) for a, b in zip(src["bbox"], d["bbox"])) / diag, float(d["solids"] != src["solids"]), num, float(bool(nums))]
    return np.clip(np.nan_to_num(np.array(fem + geo, dtype=float), nan=0.0, posinf=0.0, neginf=0.0), -20, 20)


def load():
    rows, trows = dc.train_rows(), dc.test_rows()
    syn = defaultdict(list)
    for r in dc.jl(dc.OUT / "evidence-synthetic.jsonl"):
        syn[r["task"]] += [d for d in r.get("drafts", []) if "error" not in d]
    train, dev, dev_cmp, test_cmp = [], [], [], []
    for rec in dc.jl(dc.OUT / "evidence.jsonl"):
        if "drafts" not in rec:
            continue
        valid = [d for d in rec["drafts"] if "error" not in d]
        if rec["split"] == "train":
            row = rows[rec["task"]]
            X = lambda d: features(d, rec["source"], rec["source_fem"], row)  # noqa: E731
            good = [d for d in valid if d.get("iou_reference", 0) >= dc.STRICT]
            bad = [d for d in valid if d.get("iou_reference", 0) < dc.STRICT and d["iou_source"] < dc.STRICT] + syn.get(rec["task"], [])
            split = dc.split_of(row["component_id"])
            for g in good:
                for b in bad:
                    (train if split == "train" else dev).append(X(g) - X(b))
            if split == "dev":
                drafts = [d for d in valid if "reference" not in d["origins"]]
                inc = next((d for d in drafts if "astra0" in d["origins"]), None)
                if inc is not None:
                    for ch in drafts:
                        if ch is not inc:
                            dev_cmp.append((rec["task"], X(ch) - X(inc), ch.get("iou_reference", 0) >= dc.STRICT,
                                            inc.get("iou_reference", 0) >= dc.STRICT))
        else:
            row = trows[rec["task"]]
            X = lambda d: features(d, rec["source"], rec["source_fem"], row)  # noqa: E731
            inc = next((d for d in valid if "vanilla" in d["origins"]), None)
            if inc is not None:
                for ch in valid:
                    if ch is not inc:
                        test_cmp.append((rec["task"], X(ch) - X(inc), ch["code"]))
    return np.array(train), np.array(dev), dev_cmp, test_cmp


def fit(D: np.ndarray, cols: list[int], l2: float = 1e-2, steps: int = 3000, lr: float = 0.1) -> np.ndarray:
    X = D[:, cols]
    scale = np.maximum(np.abs(X).std(0), 1e-6)
    Xs = X / scale
    w = np.zeros(len(cols))
    for _ in range(steps):  # pairwise logistic: P(correct above wrong) = sigmoid(w . (x_correct - x_wrong))
        p = 1 / (1 + np.exp(-Xs @ w))
        w -= lr * (-(Xs.T @ (1 - p)) / len(Xs) + l2 * w)
    return w / scale


def main() -> None:
    train, dev, dev_cmp, test_cmp = load()
    ok = {}
    for r in dc.jl(dc.GOT / "all-drafts-predictions.jsonl"):
        ok[(r["id"].split("#")[0], r["predicted_code"])] = None
    geo = {r["id"]: r["match_strict"] for r in dc.jl(dc.GOT / "all-drafts-predictions-geometry.jsonl")}
    for r in dc.jl(dc.GOT / "all-drafts-predictions.jsonl"):
        ok[(r["id"].split("#")[0], r["predicted_code"])] = geo[r["id"]]
    astra = {r["id"]: r["match_strict"] for r in dc.jl(dc.ASTRA_TEST)}
    print(f"training pairs {len(train)}, development pairs {len(dev)}, development comparisons {len(dev_cmp)}, test comparisons {len(test_cmp)}")
    results = {}
    for name, cols in (("fem", GROUPS["fem"]), ("geometry", GROUPS["geometry"]), ("fem+geometry", GROUPS["fem"] + GROUPS["geometry"])):
        w = fit(train, cols)
        sd = dev[:, cols] @ w
        dev_acc = float(((sd > 0) + 0.5 * (sd == 0)).mean())  # a tie (identical responses) counts as a coin flip
        coverage = float((sd != 0).mean())
        # margin chosen on development comparisons: replace Astra's first draft only when the challenger leads by > m
        best = (0, math.inf)  # (net development gain, margin); margin = inf means never replace Astra
        for m in sorted({float(x[1][cols] @ w) for x in dev_cmp} | {math.inf}):
            by = {}
            for t, diff, c_ok, i_ok in dev_cmp:
                s = float(diff[cols] @ w)
                if s > m and s > by.get(t, (None, -math.inf))[1]:
                    by[t] = ((c_ok, i_ok), s)
            net = sum(c and not i for (c, i), _ in by.values()) - sum(i and not c for (c, i), _ in by.values())
            best = max(best, (net, m))  # ties go to the larger, more conservative margin
        margin = best[1]
        decisive = [(t, float(diff[cols] @ w), ok[(t, code)]) for t, diff, code in test_cmp if ok[(t, code)] != astra[t]]
        acc = sum(0.5 if s == 0 else float((s > 0) == c) for _, s, c in decisive) / len(decisive)
        pick = {}
        for t, diff, code in test_cmp:
            s = float(diff[cols] @ w)
            if s > margin and s > pick.get(t, (None, -math.inf))[1]:
                pick[t] = (code, s)
        gain = sum(ok[(t, c)] and not astra[t] for t, (c, _) in pick.items())
        loss = sum(astra[t] and not ok[(t, c)] for t, (c, _) in pick.items())
        results[name] = dict(dev_pair_accuracy=round(dev_acc, 3), dev_coverage=round(coverage, 3), test_decisive_accuracy=round(acc, 3), decisive=len(decisive),
                             margin=None if margin == math.inf else round(margin, 3), replaced=len(pick), gained=gain, lost=loss,
                             astra=sum(astra[t] for t in dc.test_rows()), score=sum(astra[t] for t in dc.test_rows()) + gain - loss,
                             weights=[round(x, 3) for x in w])
        print(name, json.dumps({k: v for k, v in results[name].items() if k != "weights"}))
    (dc.OUT / "fem-score-learned.json").write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
