"""Could simpler selection rules replace the agentic pipeline? Offline ablation over the candidates one run recorded.

Every node a pipeline run generated (single answer, repairs, alternatives) is scored against the reference once; then
selection rules of increasing complexity are replayed on the same candidates, in generation order. Candidates were
generated under the full pipeline's feedback, so this isolates SELECTION, not generation.

  python scripts/pipeline_heuristic_ablation.py score  --run runs/adaptive-cad-open-20261007
  python scripts/pipeline_heuristic_ablation.py report --run runs/adaptive-cad-open-20261007
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PYTHON = ROOT / "tmp/cad-runtime/bin/python"


def results(run: Path) -> dict[str, dict]:
    out = {}
    for f in sorted(run.glob("*/result.json")):
        r = json.loads(f.read_text())
        out[r["task_id"]] = r
    return out


def score(run: Path) -> None:
    from cad_edit_contracts import apply
    from cad_edit_verifier import extract
    refs = {json.loads(l)["id"]: json.loads(l) for l in (run / "pipeline-predictions.jsonl").read_text().splitlines()}
    from multisource_cad_astra_benchmark import tasks
    code = {t["id"]: t["code"] for t in tasks() if t["source"] == "BenchCAD"}
    rows = []
    for tid, r in results(run).items():
        ref = refs[tid]
        for n in r["nodes"]:
            try:
                _, patch = extract(n["candidate"])
                pred, err = apply(code[tid], patch, "cadquery"), None
            except Exception as e:  # noqa: BLE001 - an unusable patch is scored as a miss
                pred, err = None, f"{type(e).__name__}: {e}"[:200]
            rows.append(dict(id=f"{tid}#{n['id']}", source="BenchCAD", category=ref.get("category"), representation="cadquery",
                             predicted_code=pred, error=err, applicable=pred is not None, prediction=n["candidate"],
                             reference_code=ref.get("reference_code"), reference_step=ref["reference_step"],
                             reference_step_sha256=ref["reference_step_sha256"]))
    path = run / "ablation-nodes.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print("nodes", len(rows), flush=True)
    subprocess.run([str(PYTHON), str(ROOT / "scripts/score_multisource_cad_geometry.py"), str(path)], check=True,
                   stdout=subprocess.DEVNULL)


def mcnemar(a: list[bool], b: list[bool]) -> tuple[int, int, float]:
    g = sum(y and not x for x, y in zip(a, b))
    l_ = sum(x and not y for x, y in zip(a, b))
    n, k = g + l_, min(g, l_)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return g, l_, p


def report(run: Path) -> None:
    geo = {json.loads(l)["id"]: json.loads(l) for l in (run / "ablation-nodes-geometry.jsonl").read_text().splitlines()}
    single = {json.loads(l)["id"]: json.loads(l)["match_strict"]
              for l in (run / "single-predictions-geometry.jsonl").read_text().splitlines()}
    pipeline = {json.loads(l)["id"]: json.loads(l)["match_strict"]
                for l in (run / "pipeline-predictions-geometry.jsonl").read_text().splitlines()}
    res = results(run)
    ids = sorted(set(res) & set(single) & set(pipeline))

    def strict(tid, n):
        return bool(geo.get(f"{tid}#{n['id']}", {}).get("match_strict"))

    def stage(n, k):
        return n["verdict"]["stages"].get(k, {}).get("status")

    def first(tid, ok):
        nodes = res[tid]["nodes"]
        hit = next((n for n in nodes if ok(n)), None)
        return strict(tid, hit) if hit else single[tid]

    def agree(tid, ok):
        """Among nodes passing `ok`, the most common built volume (rounded); ties go to the earliest node."""
        nodes = [n for n in res[tid]["nodes"] if ok(n)]
        vols = {n["id"]: geo.get(f"{tid}#{n['id']}", {}).get("predicted_volume") for n in nodes}
        nodes = [n for n in nodes if vols[n["id"]]]
        if not nodes:
            return single[tid]
        key = lambda n: round(vols[n["id"]], 3)  # noqa: E731
        c = Counter(key(n) for n in nodes)
        return strict(tid, max(nodes, key=lambda n: (c[key(n)], -n["id"])))

    builds = lambda n: stage(n, "geometry") == "PASS"  # noqa: E731
    values = lambda n: builds(n) and stage(n, "constraints") == "PASS"  # noqa: E731
    checks = lambda n: n["verdict"]["status"] == "PASS"  # noqa: E731
    final = lambda n: checks(n) and (n.get("final") or {}).get("status") == "PASS"  # noqa: E731
    rules = [
        ("Single answer (no pipeline)", {t: single[t] for t in ids}),
        ("First candidate that builds", {t: first(t, builds) for t in ids}),
        ("First that builds + passes value/changed checks", {t: first(t, values) for t in ids}),
        ("First that passes every search-time check", {t: first(t, checks) for t in ids}),
        ("First that also passes the unseen robustness check", {t: first(t, final) for t in ids}),
        ("Most-agreed geometry among candidates that build", {t: agree(t, builds) for t in ids}),
        ("Most-agreed geometry among fully passing", {t: agree(t, final) for t in ids}),
        ("Full pipeline (Pareto + score)", {t: pipeline[t] for t in ids}),
        ("Oracle: any recorded candidate is correct", {t: any(strict(t, n) for n in res[t]["nodes"]) or single[t] for t in ids}),
    ]
    base = [single[t] for t in ids]
    full = [pipeline[t] for t in ids]
    out = []
    print(f"{'rule':52s} strict  vs single        vs full pipeline")
    for name, picks in rules:
        v = [picks[t] for t in ids]
        g, l_, p = mcnemar(base, v)
        g2, l2, p2 = mcnemar(full, v)
        out.append(dict(rule=name, strict=sum(v), vs_single=[g, l_, round(p, 4)], vs_pipeline=[g2, l2, round(p2, 4)]))
        print(f"{name:52s} {sum(v):3d}/{len(ids)}  +{g:2d}/-{l_:2d} p={p:.4f}   +{g2:2d}/-{l2:2d} p={p2:.4f}")
    nodes = sum(len(res[t]["nodes"]) for t in ids)
    print(f"recorded candidates: {nodes} over {len(ids)} tasks; node scoring statuses:",
          dict(Counter(g["status"] for g in geo.values())))
    (run / "ablation-summary.json").write_text(json.dumps(dict(tasks=len(ids), candidates=nodes, rules=out), indent=1))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("score", "report"))
    p.add_argument("--run", type=Path, default=ROOT / "runs/adaptive-cad-open-20261007")
    a = p.parse_args()
    score(a.run) if a.cmd == "score" else report(a.run)


if __name__ == "__main__":
    main()
