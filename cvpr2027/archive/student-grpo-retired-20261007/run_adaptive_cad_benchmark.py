"""Live run of the full experience-guided adaptive CAD graph on the 124 BenchCAD held-out tasks, on top of GPT-6 Astra.

Every stage of the pipeline figure is active: task decomposition, experience retrieval, the saved Astra answer as the
initial CAD state, Astra hypotheses/repairs/backtracking in an adaptive graph (MCTS), the hierarchical verifier
(geometry -> constraints -> semantics -> FEM -> robustness), failure diagnosis with repair-strategy retrieval, the
candidate bank with Pareto selection, a final robustness check with return-to-graph, and successful trajectories
stored in an online memory that later tasks retrieve. Semantics is an Astra judgement of rendered views (no trained
verifier). Memory starts from the 492 retained BenchCAD training edits; held-out successes are judged by the
verifier only, never by references. References enter only `score`.

  prepare : source FEM contracts and the seeded memory (local, no API)
  run     : the live pipeline under one hard USD cap (resumable; finished tasks are skipped, never re-billed)
  score   : predictions, offline geometry scoring and paired statistics against the single Astra answer
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from math import comb
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from adaptive_cad.core import Config, Engine, edit_context  # noqa: E402
from adaptive_cad.live import ASTRA as ASTRA_BACKEND, Ledger, LivePlanner, LockedMemory, ViewSemantic, gemini_backend, open_backend  # noqa: E402
from adaptive_cad.verification import Verifier  # noqa: E402

OUT = ROOT / "runs/adaptive-cad-live-20261007"
PYTHON = ROOT / "tmp/cad-runtime/bin/python"
ASTRA = ROOT / "runs/multisource-cad-astra-20261004/scored/astra-predictions.jsonl"
BACKEND = ASTRA_BACKEND
INITIAL = ASTRA  # single-answer predictions that seed each task's initial CAD state and form the paired baseline
GOT = ROOT / "runs/got-fem-astra-20261007"
TRAIN = ROOT / "runs/multisource-cad-colab-20261002/results-final/train-retained.jsonl"
DIAG_WORKER = r'''
import json, sys
sys.path.insert(0, sys.argv[2])
from verify_mechanical_cad_edits import execute
out = {}
for i, code in json.load(open(sys.argv[1])).items():
    try: out[i] = execute(code).BoundingBox().DiagonalLength
    except Exception: out[i] = None
print(json.dumps(out))
'''


def bench_tasks() -> list[dict]:
    from multisource_cad_astra_benchmark import tasks
    return [t for t in tasks() if t["source"] == "BenchCAD"]


def prepare() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = bench_tasks()
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        Path(d, "w.py").write_text(DIAG_WORKER)
        Path(d, "in.json").write_text(json.dumps({r["id"]: r["code"] for r in rows}))
        diag = json.loads(subprocess.run([str(PYTHON), str(Path(d, "w.py")), str(Path(d, "in.json")), str(ROOT / "scripts")],
                                         capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1])
    contracts = {}
    for r in rows:
        source_fem = json.loads((GOT / r["id"][:16] / "check.json").read_text())["source_fem"]  # target-free source check
        ok = bool(source_fem.get("ok")) and diag.get(r["id"])
        contracts[r["id"]] = dict(young_MPa=210000.0, poisson=0.3, force_N=1.0, axis=[0, 0, 1], band=0.05,
                                  fixture="lower_band_fixed_upper_band_axial_load", mesh_size_mm=max(diag[r["id"]] / 18.0, 0.5),
                                  limits={"connected_components": 1}) if ok else None
    (OUT / "fem-contracts.json").write_text(json.dumps(contracts, indent=1))
    memory = OUT / "memory.jsonl"
    if not memory.exists():
        train = [json.loads(l) for l in TRAIN.read_text().splitlines()]
        seeds = []
        for t in train:
            if t["source"] != "BenchCAD":
                continue
            candidate = json.dumps({"edits": json.loads(t["target"])["edits"]}, sort_keys=True)
            seeds.append(dict(task_id=t["id"], component=t["component_id"], split="train", instruction=t["instruction"],
                              candidate=candidate, context=edit_context(t["code"], candidate), status="PASS", strategies=[]))
        memory.write_text("".join(json.dumps(s) + "\n" for s in seeds))
    print(json.dumps(dict(tasks=len(rows), fem_tasks=sum(c is not None for c in contracts.values()),
                          memory_rows=len(memory.read_text().splitlines()))))


def task_for(row: dict, astra: dict, contract: dict | None) -> dict:
    search = [{"number_scale": 1.005}]
    final = [{"number_scale": 0.995}] + ([{"mesh_scale": 1.25}] if contract else [])
    return dict(id=row["id"], code=row["code"], instruction=row["instruction"], component=row["component_id"], split="heldout",
                candidate=astra["prediction"], instruction_values=True, constraints=[], semantics={}, fem=contract,
                robustness=dict(search_variations=search, final_variations=final),
                required=["geometry", "constraints", "semantics"] + (["fem"] if contract else []) + ["robustness"])


def render(source: str, code: str, png: Path) -> bool:
    from got_full_pipeline import RENDER_WORKER, run_worker
    return run_worker(RENDER_WORKER, dict(source=source, candidate=code), [str(png)]) is not None and png.exists()


def run(cap: float, lanes: int, expansions: int, seconds: float = 1500) -> None:
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ.setdefault(var, "2")
    rows = bench_tasks()
    astra = {r["id"]: r for r in map(json.loads, INITIAL.read_text().splitlines())}
    contracts = json.loads((OUT / "fem-contracts.json").read_text())
    ledger = Ledger(OUT / "ledger.json", cap)
    pending = [r for r in rows if not (OUT / r["id"][:16] / "result.json").exists()]
    started = [0]
    lock = threading.Lock()

    def one(row):
        folder = OUT / row["id"][:16]
        if ledger.dead:
            return
        with lock:
            remaining = len(pending) - started[0]
            started[0] += 1
            budget = min(0.30, max(0.05, (cap - ledger.spent - ledger.outstanding) / max(1, remaining)))  # even pacing
        planner = LivePlanner(folder / "api", ledger, budget, backend=BACKEND)
        verifier = Verifier(PYTHON, ViewSemantic(planner, folder, render), timeout=300, max_jobs=60)
        t0 = time.monotonic()
        try:
            result = Engine(planner, verifier, LockedMemory(OUT / "memory.jsonl", "online"),
                            Config(algorithm="mcts", max_expansions=expansions, max_depth=3, seconds=seconds)).run(
                task_for(row, astra[row["id"]], contracts[row["id"]]))
        except Exception as error:  # noqa: BLE001
            (folder / "error.json").write_text(json.dumps(dict(error=type(error).__name__, detail=str(error)[:500])))
            print("ERROR", row["id"][:16], type(error).__name__, str(error)[:200], flush=True)
            return
        if ledger.dead or any(json.loads(f.read_text())["status"] == "rejected" for f in (folder / "api").glob("call-*.json")):
            # An account-level rejection invalidates this task's search; set it aside so a resumed run repeats it.
            (OUT / "aborted").mkdir(exist_ok=True)
            folder.rename(OUT / "aborted" / f"{folder.name}-{int(time.time())}")
            with LockedMemory.lock:  # its stored trajectory, if any, must not reach later tasks
                memory = OUT / "memory.jsonl"
                memory.write_text("".join(l + "\n" for l in memory.read_text().splitlines() if json.loads(l)["task_id"] != row["id"]))
            print("ABORTED", row["id"][:16], ledger.dead or "rejected request", flush=True)
            return
        result["tool_jobs"] = verifier.jobs
        (folder / "result.json").write_text(json.dumps(result, indent=1))
        print("DONE", row["id"][:16], result["status"], "node", result["selected_node"], "nodes", len(result["nodes"]),
              "stop", result["stop"], f"api ${planner.accounting['cost_usd']:.3f} ({planner.accounting['api_calls']} calls)",
              f"total ${ledger.spent:.2f}", f"{time.monotonic() - t0:.0f}s", flush=True)

    with ThreadPoolExecutor(max_workers=lanes) as pool:
        list(pool.map(one, pending))
    print(json.dumps(dict(spent=round(ledger.spent, 4), calls=ledger.calls, done=sum((OUT / r["id"][:16] / "result.json").exists() for r in rows))))


def single(lanes: int) -> None:
    """One zero-shot answer per task from the backend, with the frontier comparison's system prompt and input."""
    from multisource_cad_astra_benchmark import DATA
    system = json.loads((DATA / "manifest.json").read_text())["system"]
    ledger = Ledger(OUT / "single-ledger.json", 1e9 if not BACKEND["priced"] else 0)

    def one(row):
        folder = OUT / "single" / row["id"][:16]
        if (folder / "response.txt").exists() or ledger.dead:
            return
        planner = LivePlanner(folder, ledger, float("inf"), max_calls=1, backend=BACKEND)
        try:
            text = planner.request("single", [{"role": "system", "content": system}, {"role": "user", "content": row["input"]}], 0)
        except Exception as error:  # noqa: BLE001 - the saved call record keeps the outcome
            print("FAILED", row["id"][:16], type(error).__name__, str(error)[:160], flush=True)
            record = json.loads(next(folder.glob("call-*.json")).read_text())
            if record.get("status") != "completed":  # rejected or timed out: no answer; a later run repeats the task
                folder.rename(folder.with_name(folder.name + f"-rejected-{int(time.time())}"))
                return
            text = record.get("response", "")
        (folder / "response.txt").write_text(text)
        print("SINGLE", row["id"][:16], len(text), flush=True)
    with ThreadPoolExecutor(max_workers=lanes) as pool:
        list(pool.map(one, bench_tasks()))


def score_single() -> None:
    """Score single answers exactly as the frontier comparison scores Astra (parse, apply, offline geometry)."""
    from cad_edit_contracts import apply
    from multisource_cad_astra_benchmark import _local_reference, _reference_index, parse
    index = _reference_index()
    preds = []
    for row in bench_tasks():
        folder = OUT / "single" / row["id"][:16]
        text = (folder / "response.txt").read_text()
        call = json.loads(next(folder.glob("call-*.json")).read_text())
        code = error = None
        try:
            if call.get("finish_reason") != "stop":
                raise ValueError("finish_reason " + str(call.get("finish_reason")))
            code = apply(row["code"], parse(text)[0], row["representation"])
        except Exception as e:  # noqa: BLE001
            error = type(e).__name__ + ": " + str(e)[:250]
        preds.append(dict(id=row["id"], source=row["source"], representation=row["representation"], category=row["category"],
                          component_id=row["component_id"], prediction=text, applicable=error is None, error=error,
                          predicted_code=code, reference_code=row["edited_code"], reference_step=_local_reference(row, index),
                          reference_step_sha256=row.get("reference_step_sha256")))
    path = OUT / "single-predictions.jsonl"
    path.write_text("".join(json.dumps(p) + "\n" for p in preds))
    subprocess.run([str(PYTHON), str(ROOT / "scripts/score_multisource_cad_geometry.py"), str(path)], check=True, stdout=subprocess.DEVNULL)
    geo = [json.loads(l) for l in path.with_name("single-predictions-geometry.jsonl").read_text().splitlines()]
    print(json.dumps(dict(backend=BACKEND["name"], tasks=len(geo), applicable=sum(p["applicable"] for p in preds),
                          executable=sum(g["executable"] for g in geo), strict=sum(g["match_strict"] for g in geo))))


def mcnemar(gain: int, loss: int) -> float:
    n, k = gain + loss, min(gain, loss)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0


def score() -> None:
    from cad_edit_contracts import apply
    from cad_edit_verifier import extract
    from multisource_cad_astra_benchmark import _local_reference, _reference_index
    index = _reference_index()
    astra = {r["id"]: r for r in map(json.loads, INITIAL.read_text().splitlines())}
    preds, stats = [], Counter()
    for row in bench_tasks():
        res = json.loads((OUT / row["id"][:16] / "result.json").read_text())
        stats[res["status"]] += 1
        a = astra[row["id"]]
        if res["status"] != "PASS" or res["selected_node"] == 0:  # the initial Astra answer, scored exactly as before
            code, err, pick = a["predicted_code"] if a["applicable"] in (True, "True") else None, a["error"], "initial"
        else:
            try:
                code, err = apply(row["code"], extract(res["prediction"])[1], "cadquery"), None
            except Exception as e:  # noqa: BLE001
                code, err = None, type(e).__name__
            pick = "graph"
        stats[pick] += 1
        preds.append(dict(id=row["id"], source=row["source"], category=row["category"], representation=row["representation"],
                          predicted_code=code, error=None if code else (err or "no code"), applicable=code is not None,
                          prediction=res["prediction"], reference_code=row["edited_code"],
                          reference_step=_local_reference(row, index), reference_step_sha256=row["reference_step_sha256"]))
    path = OUT / "pipeline-predictions.jsonl"
    path.write_text("".join(json.dumps(p) + "\n" for p in preds))
    subprocess.run([str(PYTHON), str(ROOT / "scripts/score_multisource_cad_geometry.py"), str(path)], check=True, stdout=subprocess.DEVNULL)
    got = {r["id"]: r["match_strict"] for r in map(json.loads, (OUT / "pipeline-predictions-geometry.jsonl").read_text().splitlines())}
    van = {r["id"]: r["match_strict"] for r in map(json.loads, INITIAL.with_name(INITIAL.stem + "-geometry.jsonl").read_text().splitlines())}
    gain = sum(got[i] and not van[i] for i in got)
    loss = sum(van[i] and not got[i] for i in got)
    summary = dict(tasks=len(got), backend=BACKEND["name"], single=sum(van[i] for i in got), pipeline=sum(got.values()), gained=gain, lost=loss,
                   mcnemar_p=round(mcnemar(gain, loss), 4), **stats, ledger=json.loads((OUT / "ledger.json").read_text()))
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary))


def main() -> None:
    global OUT, BACKEND, INITIAL
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("prepare", "single", "score-single", "run", "score"))
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--backend", choices=("astra", "gemini", "open"), default="astra")
    p.add_argument("--rpm", type=float, default=10, help="Gemini requests per minute (free-tier pacing)")
    p.add_argument("--endpoint", default="http://localhost:8000/v1/chat/completions")
    p.add_argument("--model", default="Qwen/Qwen3.5-35B-A3B-FP8")
    p.add_argument("--cap", type=float, default=15.0)
    p.add_argument("--lanes", type=int, default=5)
    p.add_argument("--expansions", type=int, default=4)
    p.add_argument("--limit", type=int, help="smoke test on the first N tasks")
    p.add_argument("--seconds", type=float, default=1500, help="per-task search time limit")
    a = p.parse_args()
    OUT = a.out
    if a.backend in ("open", "gemini"):  # free planners; their own single answers seed the graph and are the baseline
        BACKEND = open_backend(a.endpoint, a.model) if a.backend == "open" else gemini_backend(a.model, a.rpm)
        INITIAL = a.out / "single-predictions.jsonl"
    if a.limit:
        global bench_tasks
        full = bench_tasks
        bench_tasks = lambda: full()[:a.limit]  # noqa: E731
    {"prepare": prepare, "single": lambda: single(a.lanes), "score-single": score_single,
     "run": lambda: run(a.cap, a.lanes, a.expansions, a.seconds), "score": score}[a.cmd]()


if __name__ == "__main__":
    main()
