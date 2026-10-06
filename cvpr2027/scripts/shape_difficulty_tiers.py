"""Easy / moderate / hard tiers for the 252 held-out CAD edits, with two model-independent definitions.

Edit tiers (primary) group tasks by what the instruction requires:
  easy      new values are stated or geometry is removed: BenchCAD T1 (explicit value), T2 (explicit rigid
            transform), CAD-Editor delete
  moderate  a value must be derived or a standard feature added/removed: BenchCAD T3, T4
  hard      new geometry must be invented from a description: BenchCAD T5 (shape/topology replacement),
            CAD-Editor add and modify
Shape tiers (secondary) are equal-size tertiles within each source by B-rep face count of the executed SOURCE
solid (ties broken by task id). Strict agreement (volume IoU >= 0.99999) per tier is reported for every system.

  tmp/cad-runtime/bin/python scripts/shape_difficulty_tiers.py      (needs CadQuery for the source solids)
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "runs/shape-tiers-20261007"
TEST = ROOT / "runs/multisource-cad-colab-20261002/results-final/test-retained.jsonl"
SCORED = ROOT / "runs/multisource-cad-astra-20261004/scored"
SYSTEMS = {
    "Fresh 3B base": SCORED / "base-predictions-geometry.jsonl",
    "3B patch only": SCORED / "trained-predictions-geometry.jsonl",
    "3B plan + anchoring": ROOT / "runs/cad-distill-v3-kaggle-v2-20261006/results-distill/local/test-anchored-predictions-geometry.jsonl",
    "GPT-6 Astra": SCORED / "astra-predictions-geometry.jsonl",
}


def features(row: dict) -> dict:
    from verify_mechanical_cad_edits import execute
    from cad_editor_geometry import execute_sequence
    out = dict(id=row["id"], source=row["source"], category=row["category"], lines=len(row["code"].splitlines()))
    try:
        solid = (execute if row["representation"] == "cadquery" else execute_sequence)(row["code"])
        out.update(faces=len(solid.Faces()), edges=len(solid.Edges()), solids=len(solid.Solids()))
    except Exception as e:  # noqa: BLE001
        out.update(faces=None, error=type(e).__name__ + ": " + str(e)[:120])
    return out


def best_of_n() -> dict:
    sel = ROOT / "runs/bestofn-student-20261006/select"
    tasks = {json.loads(l)["id"]: json.loads(l) for l in (sel / "tasks.jsonl").read_text().splitlines()}
    verdicts = {json.loads(l)["id"]: json.loads(l) for l in (sel / "verdicts.jsonl").read_text().splitlines()}
    strict = {json.loads(l)["id"]: json.loads(l)["match_strict"] for l in (sel / "test-candidates-geometry.jsonl").read_text().splitlines()}
    return {i: strict[f"{i}#{t['keys'][verdicts[i].get('selected') or 0]}"] for i, t in tasks.items() if t["split"] == "test"}


def main() -> None:
    rows = [json.loads(l) for l in TEST.read_text().splitlines()]
    OUT.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(max_workers=4) as pool:
        feats = list(pool.map(features, rows))
    tiers = {}
    cuts = {}
    for source in ("BenchCAD", "CAD-Editor"):
        ranked = sorted((f for f in feats if f["source"] == source and f["faces"] is not None),
                        key=lambda f: (f["faces"], f["id"]))
        n = len(ranked)
        for k, f in enumerate(ranked):
            tiers[f["id"]] = ("easy", "moderate", "hard")[min(2, 3 * k // n)]
        cuts[source] = {t: [min(f["faces"] for f in ranked if tiers[f["id"]] == t),
                            max(f["faces"] for f in ranked if tiers[f["id"]] == t)] for t in ("easy", "moderate", "hard")}
    edit_tier = {"T1": "easy", "T2": "easy", "delete": "easy", "T3": "moderate", "T4": "moderate",
                 "T5": "hard", "add": "hard", "modify": "hard"}
    for f in feats:
        f["shape_tier"] = tiers.get(f["id"], "unexecutable")
        f["tier"] = edit_tier[f["category"]]
    results = {name: {json.loads(l)["id"]: json.loads(l)["match_strict"] for l in path.read_text().splitlines()}
               for name, path in SYSTEMS.items()}
    results["3B plan + anchoring, best of 11 (verifier)"] = best_of_n()
    order = ["Fresh 3B base", "3B patch only", "3B plan + anchoring", "3B plan + anchoring, best of 11 (verifier)", "GPT-6 Astra"]
    summary = dict(cuts=cuts, unexecutable=sum(f["shape_tier"] == "unexecutable" for f in feats))
    for key in ("tier", "shape_tier"):
        table = tabulate(feats, results, order, key)
        summary["edit_tiers" if key == "tier" else "shape_tiers"] = table
        print(f"\n{'EDIT tiers' if key == 'tier' else 'SHAPE tiers (faces)'}")
        print(f"{'system':44s} " + "  ".join(f"{t:>16s}" for t in table))
        for name in order:
            print(f"{name:44s} " + "  ".join(f"{table[t][name]:>3d}/{table[t]['tasks']:<3d} ({100 * table[t][name] / table[t]['tasks']:4.1f}%)" for t in table))
    (OUT / "features.jsonl").write_text("".join(json.dumps(f) + "\n" for f in feats))
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(cuts), "unexecutable sources:", summary["unexecutable"])


def tabulate(feats: list, results: dict, order: list, key: str) -> dict:
    table = {}
    for tier in ("easy", "moderate", "hard"):
        ids = [f["id"] for f in feats if f[key] == tier]
        table[tier] = dict(tasks=len(ids), bench=sum(f["source"] == "BenchCAD" for f in feats if f[key] == tier),
                           editor=sum(f["source"] == "CAD-Editor" for f in feats if f[key] == tier),
                           **{name: sum(results[name][i] for i in ids) for name in order},
                           **{f"{name} | {s}": sum(results[name][i] for i in ids if next(x for x in feats if x["id"] == i)["source"] == s)
                              for name in order for s in ("BenchCAD", "CAD-Editor")})
    return table

if __name__ == "__main__":
    main()
