"""GEPA prompt evolution for Astra on BenchCAD edits: does a reflectively evolved system prompt beat Astra's 89/124?

The only thing optimized is the system prompt (no weights). GEPA (Agrawal et al., 2025; `gepa` 0.1.4) runs the task
model with a candidate prompt on minibatches of the 492 BenchCAD TRAINING edits, shows a reflection model what went
wrong (patch errors, volume IoU, size differences and the reference edit, which is legitimate on training data), and
keeps a Pareto set of prompts scored on the 44 VALIDATION edits. The 124 TEST edits are used once, at the end, with
the official geometry scorer, for the seed prompt (a same-day baseline) and the evolved prompt.

Seed = the exact Astra baseline prompt (data/multisource-cad-edits-v1/manifest.json), user turn = the task input,
gpt-6-astra, reasoning_effort medium, 6,000 completion tokens: the setting behind Astra's 89/124.

  python scripts/gepa_astra.py optimize --backend astra --budget-usd 25 --max-metric-calls 700 --run runs/gepa-astra-DATE
  python scripts/gepa_astra.py test     --backend astra --run runs/gepa-astra-DATE --prompt best   (and --prompt seed)
  python scripts/gepa_astra.py compare  --run runs/gepa-astra-DATE
  dry run, free: --backend gemini (gemini-3.5-flash-lite) with --train-limit/--val-limit and a small --max-metric-calls
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
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
sys.path.insert(0, str(ROOT / "scripts"))
from cad_edit_contracts import apply  # noqa: E402
from multisource_cad_astra_benchmark import parse  # noqa: E402

DATA = ROOT / "runs/multisource-cad-colab-20261002/results-final"
SEED = json.loads((ROOT / "data/multisource-cad-edits-v1/manifest.json").read_text())["system"]
CAD_PYTHON = ROOT / "tmp/cad-runtime/bin/python"
BASELINE = ROOT / "runs/multisource-cad-astra-20261004/scored/astra-predictions-geometry.jsonl"
BACKENDS = {
    "astra": dict(endpoint="https://api.openai.com/v1/chat/completions", model="gpt-6-astra", key="OPENAI_API_KEY",
                  params={"reasoning_effort": "medium", "max_completion_tokens": 6000, "store": False}, price=(10.0, 50.0)),
    "gemini": dict(endpoint="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                   model="gemini-3.5-flash-lite", key="GEMINI_API_KEY", params={"max_tokens": 6000}, price=(0.0, 0.0)),
}

GEO_WORKER = r'''
import json, sys
sys.path.insert(0, sys.argv[2])
from verify_mechanical_cad_edits import execute
job = json.load(open(sys.argv[1])); out = {}
def box(s):
    b = s.BoundingBox(); return [round(b.xlen, 3), round(b.ylen, 3), round(b.zlen, 3)]
ref = execute(job["ref"]); out["ref_volume"] = round(ref.Volume(), 3); out["ref_bbox"] = box(ref)
try:
    s = execute(job["pred"])
    inter = s.intersect(ref).Volume(); union = s.Volume() + ref.Volume() - inter
    out.update(executed=True, volume=round(s.Volume(), 3), bbox=box(s), iou=max(0.0, min(1.0, inter / union)) if union > 0 else 0.0)
except Exception as e:
    out.update(executed=False, error=(type(e).__name__ + ": " + str(e))[:400])
print(json.dumps(out))
'''


def rows(split: str) -> list[dict]:
    path = DATA / f"{split}-retained.jsonl"
    return [r for r in map(json.loads, path.read_text().splitlines()) if r["source"] == "BenchCAD"]


class LM:
    """One chat backend with a hard USD cap at list price; every request and response is saved."""

    def __init__(self, backend: str, run: Path, budget_usd: float, rpm: float = 0.0):
        self.cfg, self.run, self.budget = BACKENDS[backend], run, budget_usd
        self.key = os.environ.get(self.cfg["key"]) or sys.exit(f"{self.cfg['key']} is not set; no calls made")
        self.lock, self.spent, self.calls, self.gap, self.last = threading.Lock(), 0.0, 0, 60.0 / rpm if rpm else 0.0, 0.0
        ledger = run / "ledger.json"
        if ledger.exists():
            state = json.loads(ledger.read_text())
            self.spent, self.calls = state["spent_usd"], state["calls"]
        (run / "calls").mkdir(parents=True, exist_ok=True)

    def worst(self, max_out: int) -> float:
        p_in, p_out = self.cfg["price"]
        return (6000 * p_in + max_out * p_out) / 1e6

    def __call__(self, system: str, user: str, kind: str, max_out: int | None = None) -> str:
        params = dict(self.cfg["params"])
        if max_out:
            params["max_completion_tokens" if "max_completion_tokens" in params else "max_tokens"] = max_out
        cap = params.get("max_completion_tokens", params.get("max_tokens", 6000))
        with self.lock:
            if self.spent + self.worst(cap) > self.budget:
                raise BudgetExhausted(f"spent ${self.spent:.2f} of ${self.budget:.2f}")
            wait = self.last + self.gap - time.time()
            self.last = max(time.time(), self.last + self.gap)
        if wait > 0:
            time.sleep(wait)
        body = dict(model=self.cfg["model"], messages=([{"role": "system", "content": system}] if system else [])
                    + [{"role": "user", "content": user}], **params)
        for attempt in range(6):
            req = urllib.request.Request(self.cfg["endpoint"], json.dumps(body).encode(),
                                         {"Authorization": "Bearer " + self.key, "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=900) as r:
                    raw = json.load(r)
                break
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="replace").replace(self.key, "[REDACTED]")[:600]
                if e.code == 429 and re.search(r"insufficient_quota|credit|PerDay|free_tier_requests", msg):
                    raise BudgetExhausted("provider quota: " + msg[:200])
                if e.code in (429, 500, 502, 503, 504) and attempt < 5:
                    time.sleep(10 * 2 ** attempt)
                    continue
                raise RuntimeError(f"HTTP {e.code}: {msg}")
            except (TimeoutError, urllib.error.URLError) as e:
                if attempt < 5:
                    time.sleep(10 * 2 ** attempt)
                    continue
                raise RuntimeError(type(e).__name__)
        usage = raw.get("usage") or {}
        p_in, p_out = self.cfg["price"]
        cost = (usage.get("prompt_tokens", 0) * p_in + usage.get("completion_tokens", 0) * p_out) / 1e6
        text = raw["choices"][0]["message"].get("content") or ""
        with self.lock:
            self.spent += cost
            self.calls += 1
            n = self.calls
            (self.run / "ledger.json").write_text(json.dumps(dict(spent_usd=round(self.spent, 4), calls=self.calls,
                                                                   budget_usd=self.budget, model=self.cfg["model"])))
        (self.run / "calls" / f"{n:05d}-{kind}.json").write_text(json.dumps(dict(kind=kind, usage=usage, cost_usd=cost,
                                                                                  system=system, user=user, text=text)))
        return text


class BudgetExhausted(Exception):
    pass


def readable(code: str, patch: dict) -> str:
    """A patch as old -> new lines of the original program."""
    lines, out = code.splitlines(), []
    for e in patch.get("edits", []):
        old = lines[e["start"]:e["start"] + e["delete"]]
        out.append(f"at line {e['start']}: " + (" | ".join(o.strip() for o in old) or "(insert)") + "  ->  "
                   + (" | ".join(s.strip() for s in e["insert"]) or "(delete)"))
    return "; ".join(out) or "(no edits)"


def geometry(pred: str, ref: str) -> dict:
    with tempfile.TemporaryDirectory() as d:
        Path(d, "w.py").write_text(GEO_WORKER)
        Path(d, "job.json").write_text(json.dumps(dict(pred=pred, ref=ref)))
        try:
            p = subprocess.run([str(CAD_PYTHON), str(Path(d, "w.py")), str(Path(d, "job.json")), str(ROOT / "scripts")],
                               capture_output=True, text=True, timeout=90)
            return json.loads(p.stdout.strip().splitlines()[-1])
        except Exception as e:  # noqa: BLE001 - a hung or crashed execution is a failed candidate
            return dict(executed=False, error=f"execution failed: {type(e).__name__}")


def evaluate_one(row: dict, text: str) -> tuple[float, str, str | None]:
    """Score in [0, 1] (1 = strict match), the textual feedback for reflection, and the predicted program."""
    label = readable(row["code"], json.loads(row["target"]))
    try:
        patch, _ = parse(text)
        pred = apply(row["code"], patch, "cadquery")
    except Exception as e:  # noqa: BLE001
        return 0.0, (f"The patch could not be used ({type(e).__name__}: {str(e)[:200]}). Reference edit: {label}."), None
    g = geometry(pred, row["edited_code"])
    mine = readable(row["code"], patch)
    if not g.get("executed"):
        return 0.0, f"Your edit ({mine}) does not build: {g.get('error')}. Reference edit: {label}.", pred
    iou = g["iou"]
    if iou >= 0.99999:
        return 1.0, f"Correct: your edit ({mine}) matches the reference solid (volume IoU {iou:.5f}).", pred
    return 0.5 * iou, (f"Wrong solid: your edit ({mine}) builds but has volume IoU {iou:.4f} with the reference. "
                       f"Your volume {g['volume']} vs reference {g['ref_volume']} mm^3; bounding box {g['bbox']} vs "
                       f"{g['ref_bbox']} mm. Reference edit: {label}. Category {row['category']}."), pred


class Adapter:
    """gepa.GEPAAdapter for one component, `system`: the task model's system prompt."""

    propose_new_texts = None  # GEPA's default reflective proposal (reflection_lm) is used

    def __init__(self, lm: LM, workers: int):
        self.lm, self.workers = lm, workers

    def evaluate(self, batch, candidate, capture_traces=False):
        from gepa.core.adapter import EvaluationBatch

        def one(row):
            try:
                text = self.lm(candidate["system"], row["input"], "task")
            except BudgetExhausted:
                raise
            except Exception as e:  # noqa: BLE001 - a failed call is a failed example, never a crash
                return 0.0, f"The model call failed: {str(e)[:200]}", "", row
            score, feedback, _ = evaluate_one(row, text)
            return score, feedback, text, row
        with ThreadPoolExecutor(self.workers) as ex:
            res = list(ex.map(one, batch))
        traj = [dict(instruction=r["instruction"], program=r["code"], output=t, feedback=f, score=s) for s, f, t, r in res]
        return EvaluationBatch(outputs=[t for _, _, t, _ in res], scores=[s for s, _, _, _ in res],
                               trajectories=traj if capture_traces else None)

    def make_reflective_dataset(self, candidate, eval_batch, components_to_update):
        items = []
        for t in eval_batch.trajectories or []:
            program = t["program"] if len(t["program"]) < 3500 else t["program"][:3500] + "\n# ... truncated"
            items.append({"Inputs": f"Instruction: {t['instruction']}\nOriginal CadQuery program (zero-based lines):\n{program}",
                          "Generated Outputs": t["output"][:2000], "Feedback": t["feedback"]})
        return {c: items for c in components_to_update}


def optimize(a) -> None:
    import gepa
    run = Path(a.run)
    run.mkdir(parents=True, exist_ok=True)
    lm = LM(a.backend, run, a.budget_usd, a.rpm)
    train, val = rows("train")[: a.train_limit or None], rows("validation")[: a.val_limit or None]

    def reflect(prompt: str) -> str:
        return lm("", prompt, "reflect", max_out=a.reflect_tokens)
    (run / "protocol.json").write_text(json.dumps(dict(backend=a.backend, model=BACKENDS[a.backend]["model"],
        params=BACKENDS[a.backend]["params"], seed_sha256=hashlib.sha256(SEED.encode()).hexdigest(), train=len(train),
        val=len(val), max_metric_calls=a.max_metric_calls, budget_usd=a.budget_usd, minibatch=a.minibatch), indent=1))
    try:
        result = gepa.optimize(seed_candidate={"system": SEED}, trainset=train, valset=val, adapter=Adapter(lm, a.workers),
                               reflection_lm=reflect, max_metric_calls=a.max_metric_calls, reflection_minibatch_size=a.minibatch,
                               candidate_selection_strategy="pareto", run_dir=str(run / "gepa"), seed=0,
                               raise_on_exception=False, display_progress_bar=False, cache_evaluation=True)
    except BudgetExhausted as e:
        print("STOPPED:", e, flush=True)
        result = None
    if result is not None:
        best = result.best_candidate["system"]
        scores = getattr(result, "val_aggregate_scores", None)
        (run / "best-prompt.txt").write_text(best)
        (run / "gepa-summary.json").write_text(json.dumps(dict(
            candidates=len(result.candidates), val_scores=scores, best_idx=result.best_idx,
            seed_val=scores[0] if scores else None, best_val=scores[result.best_idx] if scores else None,
            spent_usd=round(lm.spent, 4), calls=lm.calls), indent=1))
        print(json.dumps(json.loads((run / "gepa-summary.json").read_text()), indent=1))
        print("BEST PROMPT:\n" + best)


def test(a) -> None:
    from got_fem_astra import _local_reference, _reference_index
    run = Path(a.run)
    prompt = SEED if a.prompt == "seed" else (run / "best-prompt.txt").read_text() if a.prompt == "best" else Path(a.prompt).read_text()
    out = run / f"test-{a.prompt if a.prompt in ('seed', 'best') else Path(a.prompt).stem}"
    out.mkdir(parents=True, exist_ok=True)
    lm = LM(a.backend, run, a.budget_usd, a.rpm)
    test_rows, index = rows("test")[: a.limit or None], _reference_index()

    def one(row):
        f = out / f"{row['id'][:16]}.json"
        if f.exists():
            return json.loads(f.read_text())
        try:
            text = lm(prompt, row["input"], "test")
        except BudgetExhausted:
            raise
        except Exception as e:  # noqa: BLE001
            text = ""
            print("CALL FAILED", row["id"][:16], str(e)[:150], flush=True)
        try:
            patch, _ = parse(text)
            code, err = apply(row["code"], patch, "cadquery"), None
        except Exception as e:  # noqa: BLE001
            code, err = None, f"{type(e).__name__}: {e}"[:200]
        rec = dict(id=row["id"], source=row["source"], category=row["category"], representation="cadquery",
                   predicted_code=code, error=err, applicable=code is not None, prediction=text,
                   reference_code=row["edited_code"], reference_step=_local_reference(row, index),
                   reference_step_sha256=row["reference_step_sha256"])
        f.write_text(json.dumps(rec))
        return rec
    with ThreadPoolExecutor(a.workers) as ex:
        recs = list(ex.map(one, test_rows))
    path = run / f"{out.name}-predictions.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in recs))
    subprocess.run([str(CAD_PYTHON), str(ROOT / "scripts/score_multisource_cad_geometry.py"), str(path)], check=True,
                   stdout=subprocess.DEVNULL)
    geo = [json.loads(l) for l in path.with_name(path.stem + "-geometry.jsonl").read_text().splitlines()]
    print(json.dumps(dict(prompt=a.prompt, tasks=len(geo), strict=sum(g["match_strict"] for g in geo), spent_usd=round(lm.spent, 4))))


def mcnemar(a: list[bool], b: list[bool]) -> tuple[int, int, float]:
    g = sum(y and not x for x, y in zip(a, b))
    l_ = sum(x and not y for x, y in zip(a, b))
    n, k = g + l_, min(g, l_)
    return g, l_, (min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0)


def compare(a) -> None:
    run = Path(a.run)

    def load(p):
        return {r["id"]: r["match_strict"] for r in map(json.loads, Path(p).read_text().splitlines())}
    base = {k: v for k, v in load(BASELINE).items() if k in {r["id"] for r in rows("test")}}
    systems = {"Astra, original prompt (4 Oct, 89)": base}
    model = json.loads((run / "protocol.json").read_text())["model"] if (run / "protocol.json").exists() else "model"
    for name in ("seed", "best"):
        p = run / f"test-{name}-predictions-geometry.jsonl"
        if p.exists():
            systems[f"{model}, {'original prompt' if name == 'seed' else 'GEPA-evolved prompt'}"] = load(p)
    ids = sorted(set.intersection(*(set(s) for s in systems.values())))
    ref = systems["Astra, original prompt (4 Oct, 89)"]
    for name, s in systems.items():
        g, l_, p = mcnemar([ref[i] for i in ids], [s[i] for i in ids])
        print(f"{name:45s} {sum(s[i] for i in ids):3d}/{len(ids)}   vs 89-run: +{g}/-{l_} p={p:.4f}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("optimize", "test", "compare"))
    p.add_argument("--backend", choices=tuple(BACKENDS), default="astra")
    p.add_argument("--run", default=str(ROOT / "runs/gepa-astra"))
    p.add_argument("--budget-usd", type=float, default=25.0)
    p.add_argument("--max-metric-calls", type=int, default=700)
    p.add_argument("--minibatch", type=int, default=5)
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--rpm", type=float, default=0.0, help="request pacing (free tiers)")
    p.add_argument("--reflect-tokens", type=int, default=16000)
    p.add_argument("--train-limit", type=int)
    p.add_argument("--val-limit", type=int)
    p.add_argument("--prompt", default="best", help="seed | best | path to a prompt file")
    p.add_argument("--limit", type=int)
    a = p.parse_args()
    {"optimize": optimize, "test": test, "compare": compare}[a.cmd](a)


if __name__ == "__main__":
    main()
