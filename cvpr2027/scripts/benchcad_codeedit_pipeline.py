"""BenchCAD CodeEdit with an open model: edit -> execute -> diagnose -> repair, MCTS over code edits, GEPA on the repair prompt.

Works on the benchmark's own CadQuery programs (BenchCAD/BenchCAD edit-bench, downloaded with the official
CodeEdit/tools/download_edit_bench.py) and scores every candidate with BenchCAD's official CodeEdit evaluator, imported
from the BenchCAD-main repository (benchcad_core.scoring): code extraction, execution to STEP, voxel IoU on the
normalised 64^3 grid against the ground-truth STEP, and norm_iou = clip((I_pred - I_base) / (1 - I_base), 0, 1) with
I_base the record's published baseline IoU. The first edit uses the official CodeEdit prompt (pipeline/modes.py).

The repair agent is reference-blind: its feedback is the instruction, the original program, its own attempt, execution
errors and checks against the ORIGINAL program's solid (no change made, same solid as before, target value missing,
large rewrite). The ground-truth STEP is read only by the official evaluator.

MCTS explores alternative code edits and ranks candidates by the evaluator's norm_iou; the output is the best repaired
program, its STEP file, its official score and execution status. Because the ranking reads the ground truth through the
evaluator, the held-out score is an evaluator-guided (oracle) result.

GEPA evolves the repair agent's instructions on training tasks with the official score as the metric; the result is
frozen and passed to the held-out evaluation with --repair-prompt.

Run with the BenchCAD-main environment's Python (it executes the model's CadQuery code with that interpreter):
  python scripts/benchcad_codeedit_pipeline.py eval --bench BenchCAD-main --data BenchCAD-main/CodeEdit/data \
      --split data/benchcad-codeedit-split.json --part test --endpoint http://localhost:8000/v1 --model Qwen/Qwen3.5-9B \
      --repair-prompt runs/benchcad-codeedit-qwen/gepa/repair_prompt.txt --out runs/benchcad-codeedit-qwen/test
  python scripts/benchcad_codeedit_pipeline.py gepa ... --part train --val-part validation --budget 240 \
      --out runs/benchcad-codeedit-qwen/gepa          # writes repair_prompt.txt
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
import difflib
import json
import math
from pathlib import Path
import random
import re
import sys
import threading
import time
import urllib.request

REPAIR_PROMPT = """You are an expert CadQuery engineer repairing an attempted edit of a CAD program.
You are given the edit instruction, the original program, an attempted edited program and a diagnosis from running it.
Return the corrected full program. It must execute, keep the final solid in `result`, apply the instruction exactly,
and leave every other feature, dimension and operation of the original unchanged.
Output only executable Python code, no explanation, no markdown fences."""

OFFICIAL = {}  # filled by load_official()
LOCK = threading.Lock()


def load_official(bench: Path) -> None:
    sys.path[:0] = [str(bench), str(bench / "CodeEdit")]
    from benchcad_core.scoring import iou as iou_mod
    from benchcad_core.scoring.exec_cq import execute_cq_to_step, extract_code
    from pipeline.modes import SYSTEM_PROMPT

    OFFICIAL.update(execute=execute_cq_to_step, extract=extract_code, iou=iou_mod.iou_step_vs_step,
                    norm_iou=iou_mod.norm_iou, system=SYSTEM_PROMPT, iou_mod=iou_mod)


# ---------------------------------------------------------------------------------------------------------------- model
class LLM:
    """OpenAI-compatible chat endpoint (vLLM), thinking disabled as in the earlier Qwen runs."""

    def __init__(self, endpoint: str, model: str, max_tokens: int = 4096, timeout: int = 600):
        self.url, self.model, self.max_tokens, self.timeout = endpoint.rstrip("/") + "/chat/completions", model, max_tokens, timeout
        self.calls = self.tokens = 0

    def __call__(self, system: str, user: str, temperature: float = 0.0) -> str:
        body = dict(model=self.model, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                    temperature=temperature, top_p=0.95 if temperature else 1.0, max_tokens=self.max_tokens,
                    chat_template_kwargs=dict(enable_thinking=False))
        for attempt in range(4):
            try:
                req = urllib.request.Request(self.url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    out = json.loads(r.read())
                with LOCK:
                    self.calls += 1
                    self.tokens += out.get("usage", {}).get("total_tokens", 0)
                return out["choices"][0]["message"]["content"] or ""
            except Exception as e:  # noqa: BLE001 - transient server errors are retried
                if attempt == 3:
                    raise
                print("retry", type(e).__name__, str(e)[:120], flush=True)
                time.sleep(5 * (attempt + 1))
        return ""


# ------------------------------------------------------------------------------------------------------------ candidates
@dataclass
class Cand:
    cid: int
    code: str
    origin: str  # initial / sample / repair
    parent: int | None = None
    depth: int = 0
    status: str = "pending"  # ok / exec_fail / no_code
    error: str | None = None
    flags: list = field(default_factory=list)
    model_iou: float = 0.0
    norm_iou: float = 0.0
    visits: int = 0


def numbers_after_to(instruction: str) -> list[str]:
    """Target values named by the instruction: 'from 26.8 to 34.84' -> ['34.84']."""
    return re.findall(r"\bto\s+(-?\d+(?:\.\d+)?)", instruction)


def changed_lines(a: str, b: str) -> int:
    return sum(1 for d in difflib.ndiff(a.strip().splitlines(), b.strip().splitlines()) if d[:1] in "+-")


class Task:
    """One CodeEdit record: generation, execution, the official score and the reference-blind checks."""

    def __init__(self, record: dict, data: Path, out: Path, llm: LLM, repair_prompt: str, exec_timeout: int):
        self.r, self.data, self.out, self.llm = record, data, out, llm
        self.repair_prompt, self.exec_timeout = repair_prompt, exec_timeout
        self.orig = (data / record["orig_code_path"]).read_text(errors="ignore")
        self.orig_step, self.gt_step = data / record["orig_step_path"], data / record["gt_step_path"]
        self.base = float(record.get("iou", 0.0))
        self.cands: list[Cand] = []
        self.out.mkdir(parents=True, exist_ok=True)

    # -- generation
    def first_edit(self, temperature: float) -> str:
        user = f"Instruction: {self.r['instruction']}\n\nOriginal code:\n```python\n{self.orig}\n```"
        return self.llm(OFFICIAL["system"], user, temperature)

    def repair(self, c: Cand, temperature: float) -> str:
        user = (f"Instruction: {self.r['instruction']}\n\nOriginal program:\n```python\n{self.orig}\n```\n\n"
                f"Attempted edited program:\n```python\n{c.code}\n```\n\nDiagnosis:\n{self.diagnosis(c)}")
        return self.llm(self.repair_prompt, user, temperature)

    def diagnosis(self, c: Cand) -> str:
        """Reference-blind feedback: execution and checks against the original program only."""
        lines = []
        if c.status == "no_code":
            lines.append("The response contained no CadQuery program.")
        elif c.status == "exec_fail":
            lines.append(f"The program fails to execute: {c.error}")
        for f in c.flags:
            lines.append({"no_change": "The program is identical to the original: the instruction was not applied.",
                          "same_solid": "The program runs but builds exactly the same solid as the original: the requested "
                                        "change has no geometric effect.",
                          "large_rewrite": "The edit rewrites much more of the program than the instruction asks for; "
                                           "only the feature named in the instruction may change."}.get(f, f))
        return "\n".join(f"- {x}" for x in lines) or "- The program executes and passes the automatic checks; re-check that " \
                                                     "it applies exactly the instruction and nothing else."

    # -- evaluation
    def evaluate(self, c: Cand) -> Cand:
        code = OFFICIAL["extract"](c.code) if c.code else ""
        c.code = code or c.code
        step = self.out / f"cand{c.cid:02d}.step"
        (self.out / f"cand{c.cid:02d}.py").write_text(c.code or "")
        if not code.strip():
            c.status, c.error = "no_code", "no parseable code in response"
        else:
            try:
                OFFICIAL["execute"](code, step, timeout=self.exec_timeout)
                c.status = "ok"
            except Exception as e:  # noqa: BLE001 - the official runner records the failure, it does not crash
                c.status, c.error = "exec_fail", f"{type(e).__name__}: {e}"
        if c.status == "ok":
            c.model_iou = OFFICIAL["iou"](step, self.gt_step)  # official evaluator (ground truth)
        c.norm_iou = OFFICIAL["norm_iou"](c.model_iou, self.base)
        # reference-blind checks (original program and its solid only)
        if c.status == "ok":
            if re.sub(r"\s+", "", c.code) == re.sub(r"\s+", "", self.orig):
                c.flags.append("no_change")
            elif OFFICIAL["iou"](step, self.orig_step) >= 0.999:
                c.flags.append("same_solid")
            for v in numbers_after_to(self.r["instruction"]):
                if not re.search(rf"(?<![\d.]){re.escape(v)}(?![\d])", c.code):
                    c.flags.append(f"The instruction's target value {v} does not appear in the program.")
            if changed_lines(self.orig, c.code) > max(8, len(self.orig.splitlines()) // 2):
                c.flags.append("large_rewrite")
        return c

    def add(self, code: str, origin: str, parent: Cand | None = None) -> Cand:
        c = Cand(cid=len(self.cands), code=code, origin=origin, parent=None if parent is None else parent.cid,
                 depth=0 if parent is None else parent.depth + 1)
        self.cands.append(self.evaluate(c))
        return c


def solve(task: Task, k: int, budget: int, c_uct: float = 0.7, max_depth: int = 3) -> dict:
    """First edits (greedy + k-1 samples), then up to `budget` MCTS repair expansions ranked by the evaluator's norm_iou;
    returns the best candidate's row."""
    task.add(task.first_edit(0.0), "initial")
    for _ in range(k - 1):
        task.add(task.first_edit(0.8), "sample")
    for _ in range(budget):
        if max(c.norm_iou for c in task.cands) >= 1.0:
            break
        n = sum(c.visits for c in task.cands) + 1
        pool = [c for c in task.cands if c.depth < max_depth]
        node = max(pool, key=lambda c: c.norm_iou + c_uct * math.sqrt(math.log(n + 1) / (1 + c.visits)))
        node.visits += 1
        task.add(task.repair(node, 0.0 if node.visits == 1 else 0.8), "repair", node)
        p = task.cands[node.parent] if node.parent is not None else None
        while p is not None:  # backpropagate visits along the path
            p.visits += 1
            p = task.cands[p.parent] if p.parent is not None else None
    pick = max(task.cands, key=lambda c: (c.norm_iou, -c.cid))
    first = task.cands[0]
    row = dict(record_id=task.r["record_id"], category=task.r.get("category"), edit_type=task.r.get("edit_type"),
               family=task.r.get("family"), baseline_iou=task.base, status=pick.status, model_iou=round(pick.model_iou, 4),
               norm_iou=round(pick.norm_iou, 4), pick=pick.cid, pick_origin=pick.origin, first_status=first.status,
               first_norm_iou=round(first.norm_iou, 4), n_candidates=len(task.cands),
               n_exec=sum(c.status == "ok" for c in task.cands))
    (task.out / "tree.json").write_text(json.dumps(dict(row=row, candidates=[asdict(c) for c in task.cands]), indent=1))
    if pick.status == "ok":  # the output: best repaired program + STEP
        (task.out / "best.py").write_text(pick.code)
        (task.out / "best.step").write_bytes((task.out / f"cand{pick.cid:02d}.step").read_bytes())
    return row


# --------------------------------------------------------------------------------------------------------------- driver
def records_for(data: Path, split: Path, part: str, limit: int | None) -> list[dict]:
    recs = {r["record_id"]: r for r in map(json.loads, (data / "records.jsonl").read_text().splitlines())}
    ids = json.loads(split.read_text())[part] if split else list(recs)
    rows = [recs[i] for i in ids if i in recs]
    return rows[:limit] if limit else rows


def run_eval(a, repair_prompt: str) -> list[dict]:
    llm = LLM(a.endpoint, a.model, a.max_tokens)
    rows = records_for(a.data, a.split, a.part, a.limit)
    out = Path(a.out)
    done = {}
    res_path = out / "results.jsonl"
    if res_path.exists():
        done = {r["record_id"]: r for r in map(json.loads, res_path.read_text().splitlines())}
    todo = [r for r in rows if r["record_id"] not in done]
    print(f"{len(rows)} records ({len(todo)} to run), k={a.k}, budget={a.budget}", flush=True)

    def one(rec):
        t = Task(rec, a.data, out / "tasks" / rec["record_id"], llm, repair_prompt, a.exec_timeout)
        try:
            row = solve(t, a.k, a.budget)
        except Exception as e:  # noqa: BLE001 - an infrastructure failure scores 0, like an api_fail row
            row = dict(record_id=rec["record_id"], status="pipeline_fail", error=str(e)[:300], norm_iou=0.0, first_norm_iou=0.0)
        with LOCK:
            with res_path.open("a") as f:
                f.write(json.dumps(row) + "\n")
            done[rec["record_id"]] = row
            n = len(done)
            mean = sum(r["norm_iou"] for r in done.values()) / n
            print(f"[{n}/{len(rows)}] {rec['record_id'][:40]:40s} {row['status']} norm_iou {row['norm_iou']} "
                  f"({row.get('n_candidates')} cands)  mean {mean:.4f}", flush=True)
        return row

    out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(one, todo))
    final = [done[r["record_id"]] for r in rows if r["record_id"] in done]
    summary = dict(model=a.model, part=a.part, n=len(final), k=a.k, budget=a.budget,
                   norm_iou=round(sum(r["norm_iou"] for r in final) / len(final), 4),
                   exec_rate=round(sum(r.get("status") == "ok" for r in final) / len(final), 4),
                   first_pass_norm_iou=round(sum(r["first_norm_iou"] for r in final) / len(final), 4),
                   llm_calls=llm.calls, llm_tokens=llm.tokens,
                   repair_prompt=repair_prompt)
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k != "repair_prompt"}, indent=1), flush=True)
    return final


def run_gepa(a) -> None:
    """Evolve the repair instructions on training tasks (official norm_iou of the pipeline's output as the metric)."""
    import gepa
    from gepa.core.adapter import EvaluationBatch

    llm = LLM(a.endpoint, a.model, a.max_tokens)
    random.seed(0)
    train = records_for(a.data, a.split, a.part, None)
    val = records_for(a.data, a.split, a.val_part, None)
    random.shuffle(train)
    train, val = train[:a.train_n], val[:a.val_n]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    counter = iter(range(10 ** 9))

    class Adapter:
        propose_new_texts = None  # GEPA's reflective proposal with reflection_lm

        def evaluate(self, batch, candidate, capture_traces=False):
            def one(rec):
                t = Task(rec, a.data, out / "rollouts" / f"{next(counter):06d}", llm, candidate["repair_instructions"],
                         a.exec_timeout)
                try:
                    row = solve(t, a.k, a.budget)
                    trace = dict(record=rec, row=row, cands=[asdict(c) for c in t.cands], diag=[t.diagnosis(c) for c in t.cands])
                except Exception as e:  # noqa: BLE001
                    row, trace = dict(norm_iou=0.0), dict(record=rec, error=str(e)[:300])
                return row["norm_iou"], trace

            with ThreadPoolExecutor(a.workers) as ex:
                res = list(ex.map(one, batch))
            return EvaluationBatch(outputs=[t for _, t in res], scores=[s for s, _ in res],
                                   trajectories=[t for _, t in res] if capture_traces else None)

        def make_reflective_dataset(self, candidate, eval_batch, components_to_update):
            items = []
            for score, tr in zip(eval_batch.scores, eval_batch.trajectories):
                rec = tr["record"]
                gt = (a.data / rec["gt_code_path"]).read_text(errors="ignore")
                orig = (a.data / rec["orig_code_path"]).read_text(errors="ignore")
                ref_diff = "\n".join(d for d in difflib.unified_diff(orig.splitlines(), gt.splitlines(), lineterm="", n=0)
                                     if d[:1] in "+-" and not d.startswith(("+++", "---")))
                repairs = [c for c in tr.get("cands", []) if c["origin"] == "repair"]
                last = repairs[-1] if repairs else (tr.get("cands") or [{}])[-1]
                items.append({
                    "Inputs": f"Instruction: {rec['instruction']} (category {rec.get('category')}, {rec.get('edit_type')})\n"
                              f"Diagnosis shown to the repair agent: {tr.get('diag', [''])[max(0, len(tr.get('diag', [''])) - 2)]}",
                    "Generated Outputs": (last.get("code") or "")[:1500],
                    "Feedback": (f"Official CodeEdit score of the selected program: norm_iou {score:.3f} (baseline IoU "
                                 f"{rec.get('iou', 0):.3f}). Candidates executed: {tr.get('row', {}).get('n_exec')} of "
                                 f"{tr.get('row', {}).get('n_candidates')}. Reference edit (training data): {ref_diff[:600]}")})
            return {"repair_instructions": items}

    def reflect(prompt: str) -> str:
        return llm("You improve instructions for a CAD code repair agent.", prompt, 0.7)

    result = gepa.optimize(seed_candidate={"repair_instructions": REPAIR_PROMPT}, trainset=train, valset=val,
                           adapter=Adapter(), reflection_lm=reflect, max_metric_calls=a.gepa_budget,
                           reflection_minibatch_size=a.minibatch, candidate_selection_strategy="pareto",
                           run_dir=str(out / "gepa"), seed=0)
    best = result.best_candidate["repair_instructions"]
    (out / "repair_prompt.txt").write_text(best)
    (out / "gepa_summary.json").write_text(json.dumps(dict(
        model=a.model, train=len(train), val=len(val), budget=a.gepa_budget, val_scores=list(result.val_aggregate_scores),
        best_index=result.best_idx, best_val=result.val_aggregate_scores[result.best_idx], seed_val=result.val_aggregate_scores[0],
        llm_calls=llm.calls, llm_tokens=llm.tokens), indent=1))
    print("frozen repair prompt ->", out / "repair_prompt.txt", flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("stage", choices=["eval", "gepa"])
    p.add_argument("--bench", type=Path, required=True, help="BenchCAD-main checkout")
    p.add_argument("--data", type=Path, required=True, help="edit-bench data dir (records.jsonl, codes/, steps/)")
    p.add_argument("--split", type=Path, help="JSON {train, validation, test: [record_id, ...]}")
    p.add_argument("--part", default="test")
    p.add_argument("--val-part", default="validation")
    p.add_argument("--endpoint", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--k", type=int, default=3, help="first edits per record (greedy + k-1 samples)")
    p.add_argument("--budget", type=int, default=6, help="MCTS repair expansions per record")
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--limit", type=int)
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("--exec-timeout", type=int, default=120)
    p.add_argument("--repair-prompt", type=Path, help="frozen repair instructions (GEPA output)")
    p.add_argument("--out", required=True)
    p.add_argument("--train-n", type=int, default=40)
    p.add_argument("--val-n", type=int, default=20)
    p.add_argument("--gepa-budget", type=int, default=240)
    p.add_argument("--minibatch", type=int, default=4)
    a = p.parse_args()
    load_official(a.bench)
    if a.stage == "gepa":
        run_gepa(a)
    else:
        run_eval(a, a.repair_prompt.read_text() if a.repair_prompt else REPAIR_PROMPT)


if __name__ == "__main__":
    main()
