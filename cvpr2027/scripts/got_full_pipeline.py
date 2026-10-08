"""Full hierarchical pipeline on top of GoT+MCTS+FEM for Astra (BenchCAD held-out tasks).

Adds the remaining components of the agentic design, each target-free:
  rag       retrieve the 2 most similar BenchCAD TRAINING edits (bag-of-words cosine over instruction + component)
            and ask Astra for one more candidate with them as worked examples
  robust    perturb the numbers in each candidate's inserted lines by +/-0.5 % and re-execute; robustness is the
            fraction of perturbations that still give a valid solid with the same face count
  semantic  for tasks whose passing candidates disagree on geometry, render source and each distinct candidate
            (isometric + top views) and ask Astra which candidate's edit matches the instruction
  select    Pareto selection: hard gates (applies, executes, FEM) then the Pareto front over semantic vote,
            consensus, instruction numbers and robustness; ties keep vanilla Astra
References enter only the final scorer. API calls share got_fem_astra.call (hard budget, list price).
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from got_fem_astra import PYTHON, bench_tasks, call, fem, node_eval, passes, spent  # noqa: E402
from multisource_cad_astra_benchmark import DATA, _local_reference, _reference_index  # noqa: E402

OUT = ROOT / "runs/got-fem-astra-20261007"
TRAIN = ROOT / "runs/multisource-cad-colab-20261002/results-final/train-retained.jsonl"
WORDS = re.compile(r"[a-z]+")
CLUSTER_WORKER = r'''
import json, sys
sys.path.insert(0, sys.argv[2])
from verify_mechanical_cad_edits import execute
codes = json.load(open(sys.argv[1]))
solids = []
for c in codes:
    try: solids.append(execute(c))
    except Exception: solids.append(None)
def iou(a, b):
    i = a.intersect(b).Volume(); u = a.Volume() + b.Volume() - i
    return i / u if u > 0 else 0.0
parent = list(range(len(codes)))
def find(i):
    while parent[i] != i: i = parent[i]
    return i
for i in range(len(codes)):
    for j in range(i + 1, len(codes)):
        if solids[i] is not None and solids[j] is not None and find(i) != find(j) and iou(solids[i], solids[j]) >= 0.99999:
            parent[find(j)] = find(i)
print(json.dumps([find(i) for i in range(len(codes))]))
'''
ROBUST_WORKER = r'''
import json, re, sys
sys.path.insert(0, sys.argv[2])
from verify_mechanical_cad_edits import execute
job = json.load(open(sys.argv[1]))
def faces(code):
    try: return len(execute(code).Faces())
    except Exception: return None
base = faces(job["code"])
ok = 0; tried = 0
if base is not None:
    for factor in (1.005, 0.995):
        lines = job["code"].splitlines()
        for k in job["changed_lines"]:
            if 0 <= k < len(lines):
                lines[k] = re.sub(r"(?<![\w.])(\d+\.\d+|\d+)(?![\w.])", lambda m: repr(float(m.group(1)) * factor) if float(m.group(1)) not in (0.0, 1.0) else m.group(1), lines[k])
        tried += 1; ok += faces("\n".join(lines)) == base
print(json.dumps(dict(base_faces=base, robustness=(ok / tried) if tried else 0.0)))
'''
RENDER_WORKER = r'''
import json, sys
sys.path.insert(0, sys.argv[2])
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from verify_mechanical_cad_edits import execute
job = json.load(open(sys.argv[1]))
src, cand = execute(job["source"]), execute(job["candidate"])
def mesh(s):
    v, f = s.tessellate(0.4); return np.array([p.toTuple() for p in v]), np.array(f)
ms = [mesh(src), mesh(cand)]
allv = np.vstack([m[0] for m in ms]); lo, hi = allv.min(0), allv.max(0); c = (lo + hi) / 2; r = (hi - lo).max() / 2 * 1.05
fig = plt.figure(figsize=(6.4, 6.4), dpi=80)
for row, (elev, azim, name) in enumerate(((28, -55, "isometric"), (90, -90, "top"))):
    for col, (v, f) in enumerate(ms):
        ax = fig.add_subplot(2, 2, row * 2 + col + 1, projection="3d")
        tri = v[f]; n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        shade = 0.35 + 0.65 * np.clip(np.abs(n @ np.array([0.3, -0.5, 0.8])), 0, 1)
        ax.add_collection3d(Poly3DCollection(tri, facecolors=plt.cm.Blues(shade * 0.8 + 0.2), edgecolor="none"))
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.view_init(elev, azim); ax.set_axis_off(); ax.set_box_aspect((1, 1, 1), zoom=1.45)
        ax.set_title(("original " if col == 0 else "edited ") + name, fontsize=9)
fig.tight_layout(); fig.savefig(sys.argv[3]); print("ok")
'''


def run_worker(script: str, payload, extra: list[str] = [], timeout: int = 300) -> str | None:
    with tempfile.TemporaryDirectory() as d:
        Path(d, "w.py").write_text(script)
        Path(d, "in.json").write_text(json.dumps(payload))
        try:
            p = subprocess.run([str(PYTHON), str(Path(d, "w.py")), str(Path(d, "in.json")), str(ROOT / "scripts"), *extra],
                               capture_output=True, text=True, timeout=timeout)
            return p.stdout.strip().splitlines()[-1] if p.returncode == 0 and p.stdout.strip() else None
        except subprocess.TimeoutExpired:
            return None


def bag(text: str) -> Counter:
    return Counter(WORDS.findall(text.lower()))


def cosine(a: Counter, b: Counter) -> float:
    dot = sum(a[k] * b[k] for k in a if k in b)
    return dot / (math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values())) + 1e-9)


def rag(budget: float, workers: int) -> None:
    system = json.loads((DATA / "manifest.json").read_text())["system"]
    train = [json.loads(l) for l in TRAIN.read_text().splitlines() if json.loads(l)["source"] == "BenchCAD"]
    bags = [bag(t["instruction"] + " " + t["component_id"].replace("_", " ")) for t in train]

    def one(row):
        q = bag(row["instruction"] + " " + row["component_id"].replace("_", " "))
        best = sorted(range(len(train)), key=lambda i: -cosine(q, bags[i]))[:2]
        shots = []
        for i in best:
            t = train[i]
            lines = t["code"].splitlines()
            changed = sorted({k for e in json.loads(t["target"])["edits"] for k in range(e["start"], min(len(lines), e["start"] + max(1, e["delete"])))})
            context = "\n".join(f"{k}: {lines[k]}" for k in changed)
            shots.append(f"Instruction: {t['instruction']}\nOriginal lines (index: text):\n{context}\nCorrect patch: {t['target']}")
        (OUT / row["id"][:16] / "rag-examples.json").write_text(json.dumps([train[i]["id"] for i in best]))
        user = ("Worked examples of similar edits from other parts:\n\n" + "\n\n".join(shots) + "\n\nNow the task:\n" + row["input"])
        call(OUT, row, "rag", [{"role": "system", "content": system}, {"role": "user", "content": user}], budget, 2500)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, bench_tasks()))


def pool_nodes(row: dict) -> tuple[list[dict], dict]:
    """All candidate nodes of a task (GoT + MCTS + RAG) with their target-free evaluations."""
    folder = OUT / row["id"][:16]
    st = json.loads((folder / "mcts.json").read_text())
    nodes = [dict(name=c["name"], code=c["code"], gates=c["gates"], fem=c["fem"], numbers_ok=c["numbers_ok"],
                  changed=c["changed"]) for c in st["candidates"]]
    if (folder / "rag.txt").exists():
        e = node_eval(row, (folder / "rag.txt").read_text(), st["source_fem"])
        nodes.append(dict(name="rag", code=e["code"], gates=e["gates"], fem=e["fem"], numbers_ok=e["numbers_ok"], changed=e["changed"]))
    return nodes, st["source_fem"]


def analyse(workers: int) -> None:
    """Cluster passing candidates by geometry and measure robustness (local, no API)."""
    def one(row):
        nodes, source_fem = pool_nodes(row)
        ok = [n for n in nodes if passes(dict(n, consensus=0), source_fem)]
        codes = sorted({n["code"] for n in ok})
        labels = json.loads(run_worker(CLUSTER_WORKER, codes, timeout=900) or "[]") if codes else []
        cluster = {c: l for c, l in zip(codes, labels)}
        robust = {}
        for code in codes:
            src = row["code"].splitlines()
            changed = [k for k, line in enumerate(code.splitlines()) if k >= len(src) or line != src[k]]
            out = run_worker(ROBUST_WORKER, dict(code=code, changed_lines=changed))
            robust[code] = json.loads(out)["robustness"] if out else 0.0
        for n in nodes:
            n["cluster"] = cluster.get(n["code"])
            n["robustness"] = robust.get(n["code"])
        (OUT / row["id"][:16] / "full.json").write_text(json.dumps(dict(source_fem=source_fem, nodes=nodes), indent=1))
        return row["id"], len(set(cluster.values()))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, k in pool.map(one, bench_tasks()):
            print("ANALYSED", i[:16], "passing clusters", k, flush=True)


def semantic(budget: float, workers: int) -> None:
    def one(row):
        folder = OUT / row["id"][:16]
        full = json.loads((folder / "full.json").read_text())
        reps = {}
        for n in full["nodes"]:
            if n.get("cluster") is not None and n["cluster"] not in reps:
                reps[n["cluster"]] = n
        if len(reps) < 2:
            return
        content = [{"type": "text", "text": f"Edit instruction: {row['instruction']}\n\nEach image shows the ORIGINAL part "
                    "(left) and one candidate EDITED part (right), isometric (top row) and top (bottom row) views. Which "
                    "candidate's edit matches the instruction? Return only JSON {\"best\": \"A\", \"matches\": "
                    "{\"A\": true, ...}}."}]
        letters = {}
        for k, (cid, n) in enumerate(sorted(reps.items())):
            letter = "ABCDEFGH"[k]
            png = folder / f"semantic-{letter}.png"
            if not png.exists() and run_worker(RENDER_WORKER, dict(source=row["code"], candidate=n["code"]), [str(png)]) is None:
                continue
            letters[letter] = cid
            content += [{"type": "text", "text": f"Candidate {letter}:"},
                        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode()}}]
        if len(letters) < 2:
            return
        text = call(OUT, row, "semantic", [{"role": "system", "content": "You verify mechanical CAD edits from rendered views."},
                                           {"role": "user", "content": content}], budget, 2000)
        try:
            ans = json.loads(text[text.find("{"):text.rfind("}") + 1])
            (folder / "semantic.json").write_text(json.dumps(dict(letters=letters, answer=ans)))
        except Exception:  # noqa: BLE001
            pass
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, bench_tasks()))


def select(tag: str, use: set[str]) -> dict:
    """Pareto selection over the enabled objectives among nodes passing the hard gates."""
    index = _reference_index()
    preds = []
    for row in bench_tasks():
        folder = OUT / row["id"][:16]
        full = json.loads((folder / "full.json").read_text())
        nodes = [n for n in full["nodes"] if "rag" in use or n["name"] != "rag"]
        sem = json.loads((folder / "semantic.json").read_text()) if (folder / "semantic.json").exists() and "semantic" in use else None
        ok = [n for n in nodes if passes(dict(n, consensus=0), full["source_fem"])]
        counts = Counter(n["cluster"] for n in ok)
        def objectives(n):
            semantic_ok = 0.0
            if sem:
                best = sem["letters"].get(sem["answer"].get("best"))
                semantic_ok = 1.0 if n["cluster"] == best else 0.0
            return (semantic_ok, counts[n["cluster"]], 1.0 if n["numbers_ok"] else 0.0,
                    (n.get("robustness") or 0.0) if "robust" in use else 0.0)
        if ok:
            objs = {id(n): objectives(n) for n in ok}
            front = [n for n in ok if not any(all(a >= b for a, b in zip(objs[id(m)], objs[id(n)])) and objs[id(m)] != objs[id(n)] for m in ok)]
            pick = max(front, key=lambda n: (objs[id(n)], n["name"] == "vanilla"))
        else:
            pick = nodes[0]
        preds.append(dict(id=row["id"], source=row["source"], category=row["category"], representation=row["representation"],
                          predicted_code=pick["code"], error=None if pick["code"] else "no executable selection",
                          applicable=pick["code"] is not None, prediction=pick["name"], reference_code=row["edited_code"],
                          reference_step=_local_reference(row, index), reference_step_sha256=row["reference_step_sha256"]))
    path = OUT / f"full-{tag}-predictions.jsonl"
    path.write_text("".join(json.dumps(p) + "\n" for p in preds))
    subprocess.run([str(PYTHON), str(ROOT / "scripts/score_multisource_cad_geometry.py"), str(path)], check=True,
                   stdout=subprocess.DEVNULL)
    got = {json.loads(l)["id"]: json.loads(l)["match_strict"] for l in (OUT / f"full-{tag}-predictions-geometry.jsonl").read_text().splitlines()}
    van = {json.loads(l)["id"]: json.loads(l)["match_strict"]
           for l in (ROOT / "runs/multisource-cad-astra-20261004/scored/astra-predictions-geometry.jsonl").read_text().splitlines()}
    g = sum(got[i] and not van[i] for i in got)
    l_ = sum(van[i] and not got[i] for i in got)
    n, k = g + l_, min(g, l_)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    res = dict(variant=tag, objectives=sorted(use), strict=sum(got.values()), vanilla=sum(van[i] for i in got), recovered=g,
               regressed=l_, mcnemar_p=round(p, 4), chosen=dict(Counter(pp["prediction"].split("-")[0] for pp in preds)))
    print(json.dumps(res))
    return res


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("rag", "analyse", "semantic", "select"))
    p.add_argument("--extra-budget", type=float, default=4.0, help="USD on top of what this run directory already spent")
    p.add_argument("--workers", type=int, default=4)
    a = p.parse_args()
    cap_file = OUT / "full-budget.json"  # one shared cap for rag + semantic: spend at first use + extra budget
    if a.cmd in ("rag", "semantic") and not cap_file.exists():
        cap_file.write_text(json.dumps(dict(base=spent(OUT), extra=a.extra_budget)))
    cap = json.loads(cap_file.read_text()) if cap_file.exists() else dict(base=0, extra=0)
    budget = cap["base"] + cap["extra"]
    if a.cmd == "rag":
        rag(budget, a.workers)
    elif a.cmd == "analyse":
        analyse(a.workers)
    elif a.cmd == "semantic":
        semantic(budget, a.workers)
    else:
        results = [select("pareto-core", set()), select("rag", {"rag"}), select("rag-robust", {"rag", "robust"}),
                   select("full", {"rag", "robust", "semantic"})]
        (OUT / "full-summary.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
