"""DPO-trained Qwen checker that chooses among GPT-6 Astra drafts on BenchCAD edits.

Astra is the draft model (its saved GoT, MCTS and retrieval drafts on the 124 held-out BenchCAD tasks). A Qwen
checker, trained with DPO, compares two drafts of the same edit and answers which one implements the instruction.
It sees only the source program, the instruction, each draft's edit operations and target-free evidence: execution,
requested values in inserted lines, whether and how the solid changed (volume, bounding box, faces, and the
RealCADBench boundary-voxel Surface IoU against the original, arXiv:2609.03773) and a scenario
FEM response relative to the source (compliance and 95th-percentile von Mises stress ratios). No logits or soft
labels are transferred from Astra.

Training uses BenchCAD *training* tasks only. Pairs put a correct edit (an Astra draft that matches the reference
geometry, else the reference patch) against a draft that builds but is wrong (Astra's own such drafts, plus free
Qwen3.5 drafts). Components are split 80/20 into train and development; the replacement threshold is chosen on
development tasks only. Held-out references enter only the final scoring.

  sample   : Qwen3.5-35B drafts for the training tasks (self-hosted vLLM)
  evidence : labels (training only) and target-free evidence for every draft, FEM where the source part solves
  pairs    : DPO pairs (both answer orders) and the development/test comparison prompts
  select   : apply the checker's verdicts (from dpo_checker_train.py on the GPU host) and score against Astra
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import difflib
import hashlib
import json
from math import comb
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cad_edit_contracts import apply  # noqa: E402
from cad_edit_verifier import extract, numeric_checks  # noqa: E402

OUT = ROOT / "runs/dpo-checker-benchcad-20261008"
PYTHON = ROOT / "tmp/cad-runtime/bin/python"
TRAIN = ROOT / "runs/multisource-cad-colab-20261002/results-final/train-retained.jsonl"
ASTRA_TRAIN = ROOT / "runs/cad-astra-distill-n2-20261005"
GOT = ROOT / "runs/got-fem-astra-20261007"
ASTRA_TEST = ROOT / "runs/multisource-cad-astra-20261004/scored/astra-predictions-geometry.jsonl"
STRICT = 0.99999
SYSTEM = ("You check mechanical CAD edits. You see the original CadQuery program, an edit instruction and two candidate "
          "edits with measurements from executing them. Exactly one candidate implements the instruction correctly. "
          "Answer with the single letter A or B.")
EVIDENCE_WORKER = r'''
import json, sys, tempfile
sys.path.insert(0, sys.argv[2])
from verify_mechanical_cad_edits import execute
job = json.load(open(sys.argv[1]))
def props(s):
    bb = s.BoundingBox()
    return dict(volume=s.Volume(), faces=len(s.Faces()), solids=len(s.Solids()), bbox=[bb.xlen, bb.ylen, bb.zlen])
def iou(a, b):
    i = a.intersect(b).Volume(); u = a.Volume() + b.Volume() - i
    return i / u if u > 0 else 0.0
src = execute(job["source"]); out = dict(source=props(src), candidates=[])
h = max(src.BoundingBox().DiagonalLength / 12.0, 0.5)  # ratios to the source only; a coarser mesh suffices
def fem(s):
    from mechanical_cad_fem import mesh_step, solve
    import cadquery as cq
    try:
        with tempfile.TemporaryDirectory() as d:
            cq.exporters.export(s, d + "/p.step"); xyz, tet = mesh_step(d + "/p.step", d + "/p.msh", h); m, _, _ = solve(xyz, tet)
            return dict(ok=True, compliance=m["compliance_N_mm"], vm_p95=m["vm_p95_MPa"])
    except Exception as e:
        return dict(ok=False, error=type(e).__name__)
ref = None
if job.get("reference"):
    try: ref = execute(job["reference"])
    except Exception: ref = None
out["source_fem"] = fem(src) if job.get("fem") else None
for code in job["candidates"]:
    try:
        s = execute(code); p = props(s); p["iou_source"] = iou(src, s)
        from realcad_metrics import voxel_ious
        p["surface_iou_source"] = voxel_ious(src, s)["surface"]  # RealCADBench boundary IoU against the original
        if ref is not None: p["iou_reference"] = iou(s, ref)
        if job.get("fem") and out["source_fem"] and out["source_fem"]["ok"]: p["fem"] = fem(s)
        out["candidates"].append(p)
    except Exception as e:
        out["candidates"].append(dict(error=type(e).__name__ + ": " + str(e)[:120]))
print(json.dumps(out))
'''


def jl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def train_rows() -> dict:
    return {r["id"]: r for r in jl(TRAIN) if r["source"] == "BenchCAD"}


def test_rows() -> dict:
    from multisource_cad_astra_benchmark import tasks
    return {r["id"]: r for r in tasks() if r["source"] == "BenchCAD"}


def split_of(component: str) -> str:
    return "dev" if int(hashlib.sha256(component.encode()).hexdigest(), 16) % 5 == 0 else "train"


def ops(source: str, code: str) -> list[dict]:
    """Zero-based line operations that turn the source into the candidate program."""
    a, b = source.splitlines(), code.splitlines()
    return [dict(start=i1, delete=i2 - i1, insert=b[j1:j2]) for tag, i1, i2, j1, j2 in
            difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if tag != "equal"]


def sample(endpoint: str, model: str, k: int, workers: int) -> None:
    from multisource_cad_astra_benchmark import DATA
    system = json.loads((DATA / "manifest.json").read_text())["system"]
    path = OUT / "qwen-drafts.jsonl"
    done = {(r["id"], r["k"]) for r in jl(path) if not r["finish"].startswith("error")} if path.exists() else set()
    jobs = [(r, i) for r in train_rows().values() for i in range(k) if (r["id"], i) not in done]
    OUT.mkdir(parents=True, exist_ok=True)

    def one(job):
        row, i = job
        body = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": row["input"]}],
                "temperature": 1.0, "top_p": 0.95, "max_tokens": 16384, "seed": 1000 * i + int(row["id"][:6], 16) % 1000}
        req = urllib.request.Request(endpoint, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                reply = json.load(r)
            text, finish = reply["choices"][0]["message"].get("content") or "", reply["choices"][0].get("finish_reason")
        except Exception as e:  # noqa: BLE001
            text, finish = "", "error: " + type(e).__name__
        return dict(id=row["id"], k=i, text=text, finish=finish)
    from concurrent.futures import as_completed
    with ThreadPoolExecutor(max_workers=workers) as pool, path.open("a") as handle:
        for n, fut in enumerate(as_completed([pool.submit(one, j) for j in jobs]), 1):  # write as each draft finishes
            handle.write(json.dumps(fut.result()) + "\n"); handle.flush()
            if n % 100 == 0:
                print("SAMPLED", n, "/", len(jobs), flush=True)


def worker(source: str, codes: list[str], reference: str | None, fem: bool) -> dict | None:
    with tempfile.TemporaryDirectory() as d:
        Path(d, "w.py").write_text(EVIDENCE_WORKER)
        Path(d, "j.json").write_text(json.dumps(dict(source=source, candidates=codes, reference=reference, fem=fem)))
        try:
            p = subprocess.run([str(PYTHON), str(Path(d, "w.py")), str(Path(d, "j.json")), str(ROOT / "scripts")],
                               capture_output=True, text=True, timeout=1800)
            return json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode == 0 else None
        except Exception:  # noqa: BLE001
            return None


def drafts_for_train() -> dict:
    """task id -> list of {origin, text} (Astra distill drafts, the reference patch, Qwen drafts)."""
    rows = train_rows()
    out = defaultdict(list)
    for folder in ASTRA_TRAIN.glob("*/candidates.json"):
        tid = json.loads((folder.parent / "result.json").read_text())["id"]
        if tid in rows:
            out[tid] += [dict(origin=f"astra{k}", text=t) for k, t in enumerate(json.loads(folder.read_text()))]
    for tid, row in rows.items():
        out[tid].append(dict(origin="reference", text=row["target"]))
    if (OUT / "qwen-drafts.jsonl").exists():
        for r in jl(OUT / "qwen-drafts.jsonl"):
            if r["finish"] == "stop":
                out[r["id"]].append(dict(origin=f"qwen{r['k']}", text=r["text"]))
    return out


def evidence(workers: int, only: str | None = None) -> None:
    """Pass 1: labels and geometry for every training draft. Pass 2: FEM for drafts that can enter a pair, and for
    every test draft."""
    OUT.mkdir(parents=True, exist_ok=True)
    rows, trows = train_rows(), test_rows()
    path = OUT / "evidence.jsonl"
    done = {r["task"] for r in jl(path)} if path.exists() else set()
    jobs = []
    for tid, drafts in drafts_for_train().items():
        codes = {}
        for d in drafts:
            try:
                patch = extract(d["text"])[1]
                code = apply(rows[tid]["code"], patch, "cadquery")
            except Exception:  # noqa: BLE001
                continue
            codes.setdefault(code, []).append(d["origin"])
        jobs.append(dict(task=tid, split="train", source=rows[tid]["code"], codes=codes, reference=rows[tid]["edited_code"]))
    names = json.loads((GOT / "all-drafts-names.json").read_text())
    test = defaultdict(dict)
    for r in jl(GOT / "all-drafts-predictions.jsonl"):
        test[r["id"].split("#")[0]].setdefault(r["predicted_code"], []).append(names[r["id"]])
    for tid, codes in test.items():
        jobs.append(dict(task=tid, split="test", source=trows[tid]["code"], codes=codes, reference=None))
    jobs = [j for j in jobs if j["task"] not in done and (only is None or j["split"] == only)]

    def one(job):
        codes = list(job["codes"])
        first = worker(job["source"], codes, job["reference"], fem=False)
        if first is None:
            return dict(task=job["task"], split=job["split"], error="worker failed")
        cands = first["candidates"]
        if job["split"] == "train":
            ok = [("iou_reference" in c) and c["iou_reference"] >= STRICT for c in cands]
            valid_wrong = [("error" not in c) and not k and c.get("iou_source", 1) < STRICT for c, k in zip(cands, ok)]
            need_fem = any(ok) and any(valid_wrong)
        else:
            need_fem = sum("error" not in c for c in cands) >= 2
        fem = worker(job["source"], codes, None, fem=True) if need_fem else None
        records = []
        for k, (code, c) in enumerate(zip(codes, cands)):
            rec = dict(code=code, origins=job["codes"][code], **c)
            if fem:
                rec["fem"] = fem["candidates"][k].get("fem")
            records.append(rec)
        return dict(task=job["task"], split=job["split"], source=first["source"],
                    source_fem=fem["source_fem"] if fem else None, drafts=records)
    from concurrent.futures import as_completed
    with ThreadPoolExecutor(max_workers=workers) as pool, path.open("a") as handle:
        for n, fut in enumerate(as_completed([pool.submit(one, j) for j in jobs]), 1):  # write as each task finishes
            handle.write(json.dumps(fut.result()) + "\n"); handle.flush()
            if n % 25 == 0:
                print("EVIDENCE", n, "/", len(jobs), flush=True)


def describe(source: str, instruction: str, d: dict, src: dict, src_fem: dict | None, use_fem: bool) -> str:
    patch = dict(edits=ops(source, d["code"]))
    lines = source.splitlines()
    out = []
    for e in patch["edits"]:
        removed = lines[e["start"]:e["start"] + e["delete"]]
        out.append(f"  at line {e['start']}: remove {removed if removed else 'nothing'}; insert {e['insert'] if e['insert'] else 'nothing'}")
    nums = numeric_checks(instruction, source, patch)
    missing = [str(n["value"]) for n in nums if not n["ok"]]
    v0, v1 = src["volume"], d["volume"]
    bb0, bb1 = src["bbox"], d["bbox"]
    ev = [f"executes: yes; solid changed: {'yes' if d['iou_source'] < STRICT else 'no'} (volume overlap with original "
          f"{d['iou_source']:.3f}; boundary overlap with original {d.get('surface_iou_source', 1):.3f})",
          f"volume ratio to original: {v1 / v0:.4f}; faces {src['faces']} -> {d['faces']}; solids {src['solids']} -> {d['solids']}",
          "bounding box change (x, y, z): " + ", ".join(f"{b - a:+.3f}" for a, b in zip(bb0, bb1)),
          "requested values present in inserted lines: " + ("all" if nums and not missing else ("none requested" if not nums else "missing " + ", ".join(missing)))]
    if use_fem:
        f = d.get("fem")
        if src_fem and src_fem.get("ok") and f:
            ev.append(f"FEM (fixed base, 1 N axial top load): {'solves' if f.get('ok') else 'fails'}"
                      + (f"; compliance ratio {f['compliance'] / src_fem['compliance']:.4f}; peak-stress (p95) ratio "
                         f"{f['vm_p95'] / max(src_fem['vm_p95'], 1e-12):.4f}" if f.get("ok") else ""))
        else:
            ev.append("FEM: not available for this part")
    return "\n".join(["  edits:"] + out + ["  evidence:"] + ["    " + e for e in ev])


def prompt(row: dict, src: dict, src_fem, a: dict, b: dict, use_fem: bool) -> list[dict]:
    numbered = "\n".join(f"{k}: {l}" for k, l in enumerate(row["code"].splitlines()))
    user = (f"Instruction: {row['instruction']}\n\nOriginal program:\n{numbered}\n\nCandidate A:\n"
            f"{describe(row['code'], row['instruction'], a, src, src_fem, use_fem)}\n\nCandidate B:\n"
            f"{describe(row['code'], row['instruction'], b, src, src_fem, use_fem)}\n\nWhich candidate implements the instruction? Answer A or B.")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def pairs(use_fem: bool, per_task: int, synthetic: bool = False) -> None:
    rows, trows = train_rows(), test_rows()
    rng = random.Random(17)
    tag = ("fem" if use_fem else "nofem") + ("-syn" if synthetic else "")
    syn = {}
    if synthetic and (OUT / "evidence-synthetic.jsonl").exists():  # dpo_hard_negatives.py: perturbed reference edits
        for r in jl(OUT / "evidence-synthetic.jsonl"):
            syn[r["task"]] = [d for d in r.get("drafts", []) if "error" not in d]
    train, dev_cmp, test_cmp = [], [], []
    for rec in jl(OUT / "evidence.jsonl"):
        if "drafts" not in rec:
            continue
        valid = [d for d in rec["drafts"] if "error" not in d]
        if rec["split"] == "train":
            row = rows[rec["task"]]
            good = [d for d in valid if d.get("iou_reference", 0) >= STRICT]
            bad = [d for d in valid if d.get("iou_reference", 0) < STRICT and d["iou_source"] < STRICT]
            synthetic_bad = syn.get(rec["task"], [])
            if not good or not (bad or synthetic_bad):
                continue
            astra_good = [d for d in good if any(o.startswith("astra") for o in d["origins"])] or good
            bad.sort(key=lambda d: not any(o.startswith("astra") for o in d["origins"]))  # Astra's own errors first
            split = split_of(row["component_id"])
            for w in bad[:per_task] + synthetic_bad[:per_task]:
                c = rng.choice(astra_good)
                natural = not w["origins"][0].startswith("synthetic")
                for first_correct in ((True, False) if natural else (rng.random() < 0.5,)):  # synthetic: one random order
                    a, b = (c, w) if first_correct else (w, c)
                    item = dict(task=rec["task"], prompt=prompt(row, rec["source"], rec["source_fem"], a, b, use_fem),
                                chosen="A" if first_correct else "B", rejected="B" if first_correct else "A")
                    (train if split == "train" else dev_cmp).append(item)
        else:
            row = trows[rec["task"]]
            inc = next((d for d in valid if "vanilla" in d["origins"]), None)
            if inc is None:
                continue
            for ch in valid:
                if ch is inc:
                    continue
                for order in ("AB", "BA"):
                    a, b = (inc, ch) if order == "AB" else (ch, inc)
                    test_cmp.append(dict(task=rec["task"], incumbent=inc["code"], challenger=ch["code"], order=order,
                                         prompt=prompt(row, rec["source"], rec["source_fem"], a, b, use_fem)))
    # development comparisons mirror test use: incumbent = Astra's first draft, challengers = the other drafts
    dev_inc = []
    for rec in jl(OUT / "evidence.jsonl"):
        if rec.get("split") != "train" or "drafts" not in rec or split_of(rows[rec["task"]]["component_id"]) != "dev":
            continue
        row = rows[rec["task"]]
        valid = [d for d in rec["drafts"] if "error" not in d and "reference" not in d["origins"]]
        inc = next((d for d in valid if "astra0" in d["origins"]), None)
        if inc is None:
            continue
        for ch in valid:
            if ch is inc:
                continue
            for order in ("AB", "BA"):
                a, b = (inc, ch) if order == "AB" else (ch, inc)
                dev_inc.append(dict(task=rec["task"], incumbent_ok=inc.get("iou_reference", 0) >= STRICT,
                                    challenger_ok=ch.get("iou_reference", 0) >= STRICT, order=order, challenger=ch["code"],
                                    prompt=prompt(row, rec["source"], rec["source_fem"], a, b, use_fem)))
    rng.shuffle(train)
    for name, items in ((f"dpo-train-{tag}.jsonl", train), (f"dpo-dev-pairs-{tag}.jsonl", dev_cmp),
                        (f"dev-comparisons-{tag}.jsonl", dev_inc), (f"test-comparisons-{tag}.jsonl", test_cmp)):
        (OUT / name).write_text("".join(json.dumps(i) + "\n" for i in items))
    print(json.dumps(dict(variant=tag, train_pairs=len(train), dev_pairs=len(dev_cmp), dev_comparisons=len(dev_inc),
                          test_comparisons=len(test_cmp))))


def mcnemar(gain: int, loss: int) -> float:
    n, k = gain + loss, min(gain, loss)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0


def challenger_probs(path: Path) -> dict:
    """(task, challenger) -> mean probability, over both answer orders, that the challenger is the correct one."""
    acc = defaultdict(list)
    for r in jl(path):
        acc[(r["task"], r["challenger"])].append(r["p_b"] if r["order"] == "AB" else 1 - r["p_b"])
    return {k: sum(v) / len(v) for k, v in acc.items()}


def choose(probs: dict, tau: float) -> dict:
    best = {}
    for (task, code), p in probs.items():
        if p >= tau and p > best.get(task, (None, -1))[1]:
            best[task] = (code, p)
    return best


def select(tag: str) -> None:
    """Pick tau on development tasks, then replace Astra's answer on test tasks only when the checker is that sure."""
    dev = jl(OUT / f"dev-scored-{tag}.jsonl")
    dev_ok = {(r["task"], r["challenger"]): r["challenger_ok"] for r in dev}
    inc_ok = {r["task"]: r["incumbent_ok"] for r in dev}
    probs = challenger_probs(OUT / f"dev-scored-{tag}.jsonl")
    table = []
    for tau in [0.5 + 0.05 * i for i in range(10)]:
        pick = choose(probs, tau)
        gain = sum(dev_ok[(t, c)] and not inc_ok[t] for t, (c, _) in pick.items())
        loss = sum(inc_ok[t] and not dev_ok[(t, c)] for t, (c, _) in pick.items())
        table.append((gain - loss, tau, gain, loss))
    table.append((0, 1.01, 0, 0))  # never replace Astra: the choice whenever no threshold has a net development gain
    net, tau, dgain, dloss = max(table, key=lambda x: (x[0], x[1]))
    test = choose(challenger_probs(OUT / f"test-scored-{tag}.jsonl"), tau)
    geo = {}
    for r in jl(GOT / "all-drafts-predictions-geometry.jsonl"):
        geo[r["id"]] = r["match_strict"]
    code_ok = {}
    for r in jl(GOT / "all-drafts-predictions.jsonl"):
        code_ok[(r["id"].split("#")[0], r["predicted_code"])] = geo[r["id"]]
    astra = {r["id"]: r["match_strict"] for r in jl(ASTRA_TEST)}
    tasks = list(test_rows())
    final = {t: (code_ok[(t, test[t][0])] if t in test else astra[t]) for t in tasks}
    gain = sum(final[t] and not astra[t] for t in tasks)
    loss = sum(astra[t] and not final[t] for t in tasks)
    summary = dict(variant=tag, tau=round(tau, 2), dev_gain=dgain, dev_loss=dloss, replaced=len(test),
                   astra=sum(astra[t] for t in tasks), checker=sum(final.values()), gained=gain, lost=loss,
                   mcnemar_p=round(mcnemar(gain, loss), 4), oracle=98, tasks=len(tasks))
    (OUT / f"summary-{tag}.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("sample", "evidence", "pairs", "select"))
    p.add_argument("--endpoint", default="http://localhost:8011/v1/chat/completions")
    p.add_argument("--model", default="Qwen/Qwen3.5-35B-A3B-FP8")
    p.add_argument("--k", type=int, default=4)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--per-task", type=int, default=4)
    p.add_argument("--no-fem", action="store_true")
    p.add_argument("--only", choices=("train", "test"))
    p.add_argument("--synthetic", action="store_true", help="add dpo_hard_negatives.py negatives to the pairs")
    a = p.parse_args()
    if a.cmd == "sample":
        sample(a.endpoint, a.model, a.k, a.workers)
    elif a.cmd == "evidence":
        evidence(a.workers, a.only)
    elif a.cmd == "pairs":
        pairs(not a.no_fem, a.per_task, a.synthetic)
    else:
        select(("nofem" if a.no_fem else "fem") + ("-syn" if a.synthetic else ""))


if __name__ == "__main__":
    main()
