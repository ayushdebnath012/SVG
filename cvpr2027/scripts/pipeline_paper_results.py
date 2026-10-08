"""Generate paper/network/pipeline-results.tex: the experience-guided graph-search pipeline on top of GPT-6 Astra.

Reads runs/got-fem-astra-20261007 (got_fem_astra.py branch/check/mcts and got_full_pipeline.py rag/analyse/semantic/
select on the 124 BenchCAD held-out tasks) and runs/cad-repair-loop-20261007/astra (cad_repair_loop.py on all 252
Astra answers). Each configuration is scored offline against the released targets; paired tests are exact two-sided
McNemar tests on strict agreement against the single Astra answer over identical task ids.
"""
from __future__ import annotations

from collections import Counter
import json
from math import comb
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from got_fem_astra import passes  # noqa: E402

OUT = ROOT / "paper/network/pipeline-results.tex"
RUN = ROOT / "runs/got-fem-astra-20261007"
ASTRA = ROOT / "runs/multisource-cad-astra-20261004/scored/astra-predictions-geometry.jsonl"
REPAIR = ROOT / "runs/cad-repair-loop-20261007/astra"
LIVE = ROOT / "runs/adaptive-cad-live-20261007"
PRICE_IN, PRICE_OUT = 10, 50
# configuration -> scored predictions; rows of the ablation table in pipeline order
CONFIGS = [("Rag", "rag-alone"), ("Got", "selected-check"), ("Mcts", "selected-mcts"), ("Pareto", "full-pareto-core"),
           ("Exp", "full-rag"), ("Robust", "full-rag-robust"), ("Full", "full-full")]


def strict(path: Path) -> dict:
    return {r["id"]: r["match_strict"] for r in map(json.loads, path.read_text().splitlines())}


def mcnemar(a: dict, b: dict) -> tuple[int, int, float]:
    x = sum(a[i] and not b[i] for i in a)
    y = sum(b[i] and not a[i] for i in a)
    n, k = x + y, min(x, y)
    return x, y, (min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0)


def live_macros(astra_all: dict) -> dict:
    """The live run of the complete pipeline (run_adaptive_cad_benchmark.py)."""
    summary = json.loads((LIVE / "summary.json").read_text())
    got = strict(LIVE / "pipeline-predictions-geometry.jsonl")
    gain, loss, p = mcnemar(got, {i: astra_all[i] for i in got})
    calls, kinds, events, nodes = Counter(), Counter(), Counter(), []
    held_retrieved = repair_retrieved = expansions = 0
    root_wrong = root_wrong_pass = root_right = root_right_fail = 0
    stops, sem_root_fail = Counter(), 0
    for folder in sorted(p_ for p_ in LIVE.iterdir() if (p_ / "result.json").exists()):
        r = json.loads((folder / "result.json").read_text())
        nodes.append(len(r["nodes"]))
        stops[r["stop"]] += 1
        for f in (folder / "api").glob("call-*.json"):
            c = json.loads(f.read_text())
            calls[c["kind"]] += 1
            kinds[c["kind"]] += c.get("cost_usd", 0)
        for e in r["events"]:
            events[e["event"] if e["event"] != "expand" else "expand-" + e["strategy"]] += 1
            if e["event"] == "decompose":
                held_retrieved += any(len(x["task_id"]) and x.get("context") is not None and x["task_id"] in astra_all
                                      for x in e.get("retrieved", []))
            if e["event"] == "expand":
                expansions += 1
                repair_retrieved += bool(e.get("retrieved_repairs"))
        root = r["nodes"][0]
        ok = root["verdict"]["status"] == "PASS" and (root["final"] or {}).get("status") == "PASS"
        sem_root_fail += root["verdict"]["stages"]["semantics"]["status"] == "FAIL"
        if astra_all[r["task_id"]]:
            root_right, root_right_fail = root_right + 1, root_right_fail + (not ok)
        else:
            root_wrong, root_wrong_pass = root_wrong + 1, root_wrong_pass + ok
    stored = sum(1 for l in (LIVE / "memory.jsonl").read_text().splitlines() if json.loads(l)["split"] == "heldout")
    ledger = json.loads((LIVE / "ledger.json").read_text())
    return dict(liveStrict=sum(got.values()), liveGain=gain, liveLoss=loss, liveP=f"{p:.2f}",
                livePass=summary.get("PASS", 0), liveUnverified=summary.get("UNVERIFIED", 0), liveGraph=summary.get("graph", 0),
                liveCost=f"{ledger['spent']:.2f}", liveCalls=ledger["calls"], liveDecompose=calls["decompose"],
                liveGenerate=calls["generate"], liveSemantic=calls["semantic"],
                liveDecomposeCost=f"{kinds['decompose']:.2f}", liveGenerateCost=f"{kinds['generate']:.2f}",
                liveSemanticCost=f"{kinds['semantic']:.2f}", liveNodes=f"{sum(nodes) / len(nodes):.1f}",
                liveExpansions=expansions, liveRepairs=events["expand-repair"], liveDiversify=events["expand-diversify"],
                liveBacktracks=events["backtrack"], liveReturns=events["return_to_graph"], liveGenErrors=events["generation_error"],
                liveStored=stored, liveHeldRetrieved=held_retrieved, liveRepairRetrieved=repair_retrieved,
                liveRootWrong=root_wrong, liveRootWrongPass=root_wrong_pass, liveRootRight=root_right,
                liveRootRightFail=root_right_fail, liveSemRootFail=sem_root_fail,
                liveBudgetStops=stops["planner_or_api_budget_exhausted"])


def main() -> None:
    astra_all = strict(ASTRA)
    m = {}
    base = None
    for name, stem in CONFIGS:
        got = strict(RUN / f"{stem}-predictions-geometry.jsonl")
        base = {i: astra_all[i] for i in got}
        gain, loss, p = mcnemar(got, base)
        m[f"pipe{name}"], m[f"pipe{name}Gain"], m[f"pipe{name}Loss"], m[f"pipe{name}P"] = sum(got.values()), gain, loss, f"{p:.2f}"
    m["pipeN"], m["pipeAstra"] = len(base), sum(base.values())

    calls, cost = Counter(), Counter()
    for f in RUN.glob("*/*-result.json"):
        r = json.loads(f.read_text())
        u = r.get("usage") or {}
        kind = "mcts" if r["call"].startswith("mcts") else r["call"]
        calls[kind] += 1
        cost[kind] += (u.get("prompt_tokens", 0) * PRICE_IN + u.get("completion_tokens", 0) * PRICE_OUT) / 1e6
    for kind, name in (("branches", "Branch"), ("mcts", "Mcts"), ("rag", "Rag"), ("semantic", "Semantic")):
        m[f"pipe{name}Calls"], m[f"pipe{name}Cost"] = calls[kind], f"{cost[kind]:.2f}"
    m["pipeCost"] = f"{sum(cost.values()):.2f}"

    expanded, kinds, cands, nopass, disagree = 0, Counter(), [], 0, 0
    wrong = wrong_pass = right = right_fail = 0
    for folder in sorted(p for p in RUN.iterdir() if (p / "check.json").exists()):
        chk = json.loads((folder / "check.json").read_text())
        cands.append(len(chk["candidates"]))
        ok = [c for c in chk["candidates"] if passes(c, chk["source_fem"])]
        nopass += not ok
        disagree += bool(ok) and max(c["consensus"] for c in ok) < len(chk["candidates"])  # passing branches differ
        first = next(c for c in chk["candidates"] if c["name"] == "vanilla")
        ok = passes(first, chk["source_fem"])
        if astra_all[chk["id"]]:
            right, right_fail = right + 1, right_fail + (not ok)
        else:
            wrong, wrong_pass = wrong + 1, wrong_pass + ok
        nodes = [n["name"] for n in json.loads((folder / "mcts.json").read_text())["nodes"] if n["name"].startswith("mcts")]
        expanded += bool(nodes)
        kinds.update(n.split("-", 1)[1] for n in nodes)
    m.update(pipeCandidates=f"{sum(cands) / len(cands):.1f}", pipeNoPass=nopass, pipeDisagree=disagree,
             pipeEligible=nopass + disagree, pipeExpanded=expanded,
             pipeRepairs=kinds["refine"], pipeBacktracks=kinds["diversify"], pipeWrong=wrong, pipeWrongPass=wrong_pass,
             pipeRight=right, pipeRightFail=right_fail)

    repaired = [json.loads(l) for l in (REPAIR / "changed-predictions-geometry.jsonl").read_text().splitlines()]
    m.update(pipeFixTasks=len(astra_all), pipeFixChanged=len(repaired),
             pipeFixExec=sum(r["executable"] for r in repaired), pipeFixStrict=sum(r["match_strict"] for r in repaired))

    if (LIVE / "summary.json").exists():
        m.update(live_macros(astra_all))

    lines = ["% Generated by scripts/pipeline_paper_results.py from runs/got-fem-astra-20261007, runs/cad-repair-loop-20261007"
             " and runs/adaptive-cad-live-20261007."]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT.read_text())


if __name__ == "__main__":
    main()
