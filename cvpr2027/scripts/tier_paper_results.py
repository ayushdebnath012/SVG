"""Generate paper/network/tier-results.tex: verifier-selected sampling and easy/moderate/hard tiers.

Reads runs/bestofn-student-20261006/select (greedy + 10 samples per task, verifier verdicts, candidate scores) and
runs/shape-tiers-20261007/features.jsonl (edit and shape tiers from shape_difficulty_tiers.py). Paired tests are
exact two-sided McNemar tests on strict agreement over identical task ids.
"""
from __future__ import annotations

from collections import Counter
import json
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper/network/tier-results.tex"
SEL = ROOT / "runs/bestofn-student-20261006/select"
SCORED = ROOT / "runs/multisource-cad-astra-20261004/scored"
PLAN = ROOT / "runs/cad-distill-v3-kaggle-v2-20261006/results-distill/local/test-anchored-predictions-geometry.jsonl"


def jl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines()]


def mcnemar(a: dict, b: dict, ids: list) -> tuple[int, int, float]:
    x = sum(a[i] and not b[i] for i in ids)
    y = sum(b[i] and not a[i] for i in ids)
    n, k = x + y, min(x, y)
    return x, y, (min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0)


def ptex(p: float) -> str:
    if p >= 0.01:
        return f"{p:.2f}"
    m, e = f"{p:.0e}".split("e")
    return f"{int(m)}\\times10^{{{int(e)}}}"


def main() -> None:
    tasks = {t["id"]: t for t in jl(SEL / "tasks.jsonl")}
    verdicts = {v["id"]: v for v in jl(SEL / "verdicts.jsonl")}
    strict = {g["id"]: g["match_strict"] for s in ("test", "validation") for g in jl(SEL / f"{s}-candidates-geometry.jsonl")}
    ok = lambda t, k: strict[f"{t['id']}#{t['keys'][k]}"]  # noqa: E731
    greedy = {i: ok(t, 0) for i, t in tasks.items()}
    pick = {i: ok(t, verdicts[i].get("selected") or 0) for i, t in tasks.items()}
    oracle = {i: any(ok(t, k) for k in range(len(t["keys"]))) for i, t in tasks.items()}
    majority = {i: strict[f"{i}#{Counter(t['keys']).most_common(1)[0][0]}"] for i, t in tasks.items()}
    astra = {g["id"]: g["match_strict"] for g in jl(SCORED / "astra-predictions-geometry.jsonl")}
    patch = {g["id"]: g["match_strict"] for g in jl(SCORED / "trained-predictions-geometry.jsonl")}
    plan = {g["id"]: g["match_strict"] for g in jl(PLAN)}
    test = [i for i, t in tasks.items() if t["split"] == "test"]
    val = [i for i, t in tasks.items() if t["split"] == "validation"]
    m = {"bonSamples": len(tasks[test[0]]["keys"]) - 1, "bonCandidates": len(tasks[test[0]]["keys"])}
    for tag, ids in (("", test), ("Val", val)):
        m[f"bon{tag}Greedy"] = sum(greedy[i] for i in ids)
        m[f"bon{tag}Pick"] = sum(pick[i] for i in ids)
        m[f"bon{tag}Majority"] = sum(majority[i] for i in ids)
        m[f"bon{tag}Oracle"] = sum(oracle[i] for i in ids)
        g, l, p = mcnemar(pick, greedy, ids)
        m.update({f"bon{tag}Gain": g, f"bon{tag}Loss": l, f"bon{tag}P": ptex(p)})
    editor = [i for i in test if tasks[i]["source"] == "CAD-Editor"]
    m["bonPickBench"] = sum(pick[i] for i in test if tasks[i]["source"] == "BenchCAD")
    m["bonEditorPick"], m["bonEditorAstra"] = sum(pick[i] for i in editor), sum(astra[i] for i in editor)
    g, l, p = mcnemar(pick, astra, editor)
    m.update(bonEditorOursOnly=g, bonEditorAstraOnly=l, bonEditorP=ptex(p))
    teacher = [json.loads(f.read_text()) for f in (ROOT / "runs/cad-astra-distill-n2-20261005").glob("*/verify.json")]
    teacher = [v for v in teacher if "selected" in v and len(v["candidates"]) == 2]
    m.update(teacherN=len(teacher),
             teacherFirst=sum((v["candidates"][0].get("audit_reference_iou") or 0) >= 0.99999 for v in teacher),
             teacherPick=sum(v["audit_selected_strict"] for v in teacher),
             teacherOracle=sum(v["audit_any_strict"] for v in teacher))
    m["bonDistinct"] = f"{sum(len(set(tasks[i]['keys'])) for i in test) / len(test):.1f}"
    agent = ROOT / "experiments/agentic-verifier-grpo-20261006"  # GRPO-trained verifier guiding Astra repair
    comp = json.loads((agent / "comparison.json").read_text())
    diag = json.loads((agent / "verifier-diagnostics.json").read_text())["grpo"]
    run = json.loads((agent / "training/run-v4/manifest.json").read_text())
    dev = json.loads((agent / "training/run-v4/summary.json").read_text())["grpo_dev"]
    a_all, a_val = comp["all_tasks"], comp["valid_references"]
    m.update(agentN=a_all["n"], agentBefore=a_all["before"], agentAfter=a_all["after"], agentRecovered=a_all["recovered"],
             agentRegressed=a_all["regressed"], agentP=f"{comp['paired_exact_p']:.2f}",
             agentRepairs=comp["repair_requested"], agentSelected=comp["repair_selected"],
             agentCost=f"{comp['api_cost_estimate_usd']:.2f}", agentTrain=run["train_candidates"], agentDev=run["dev_candidates"],
             agentGroups=run["groups"], agentGroupSize=run["group_size"],
             agentAcc=f"{100 * (diag['true_accept'] + diag['true_reject']) / diag['n']:.1f}",
             agentAlways=f"{100 * a_val['before'] / a_val['n']:.1f}",
             agentDevAcc=f"{100 * (dev['true_accept'] + dev['true_reject']) / dev['n']:.1f}",
             agentDevAlways=f"{100 * (dev['true_accept'] + dev['false_reject']) / dev['n']:.1f}")
    react = ROOT / "runs/react-student-20261006/zero-shot"
    if (react / "validation-final-geometry.jsonl").exists():  # ReAct repair rounds (zero-shot student)
        history = json.loads((react / "history.json").read_text())
        rounds = max(len(h) for h in history.values())
        for r in range(rounds):
            m[f"reactGates{'ABCD'[r]}"] = sum(h[min(r, len(h) - 1)]["ok"] for h in history.values())
        m["reactTasks"], m["reactRounds"] = len(history), rounds - 1
        final = {g["id"]: g["match_strict"] for s in ("test", "validation") for g in jl(react / f"{s}-final-geometry.jsonl")}
        for tag, ids in (("", test), ("Val", val)):
            m[f"react{tag}Final"] = sum(final[i] for i in ids)
            g, l, p = mcnemar(final, greedy, ids)
            m.update({f"react{tag}Gain": g, f"react{tag}Loss": l, f"react{tag}P": ptex(p)})
    feats = {f["id"]: f for f in jl(ROOT / "runs/shape-tiers-20261007/features.jsonl")}
    rows = []
    names = {"easy": "Easy", "moderate": "Moderate", "hard": "Hard"}
    for tier in ("easy", "moderate", "hard"):
        ids = [i for i in test if feats[i]["tier"] == tier]
        T = tier.capitalize()
        m[f"tier{T}N"] = len(ids)
        cells = []
        for key, res in (("Patch", patch), ("Plan", plan), ("Best", pick), ("Astra", astra)):
            c = sum(res[i] for i in ids)
            m[f"tier{T}{key}"] = c
            cells.append(f"{c} ({100 * c / len(ids):.0f}\\%)")
        g, l, p = mcnemar(pick, astra, ids)
        m.update({f"tier{T}OursOnly": g, f"tier{T}AstraOnly": l, f"tier{T}P": ptex(p)})
        rows.append(f"{names[tier]} ({len(ids)}) & " + " & ".join(cells) + " \\\\")
        sids = [i for i in test if feats[i]["shape_tier"] == tier]
        m[f"shape{T}Astra"] = f"{100 * sum(astra[i] for i in sids) / len(sids):.0f}"
        m[f"shape{T}Best"] = f"{100 * sum(pick[i] for i in sids) / len(sids):.0f}"
    lines = ["% Generated by scripts/tier_paper_results.py from saved scorer outputs. Do not edit manually."]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
    lines.append("\\newcommand{\\tierRows}{" + "\n".join(rows) + "}")
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT)
    for k, v in m.items():
        print(f"  {k} = {v}")


if __name__ == "__main__":
    main()
