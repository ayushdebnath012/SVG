"""Instruction-conditioned semantic verifier: the go/no-go test for the two-player repair game on Astra.

The repair game can only help Astra if a verifier flags Astra's genuine errors (wrong placement, frame, scope or
construction; 19 valid-but-wrong answers among the 35 BenchCAD misses) without flagging its 89 correct answers. This
script measures exactly that on Astra's saved answers, with no new Astra calls and no reference geometry in any prompt.

  extract   feature extraction from the executed source C0 and Astra's edited part P (CAD kernel): material removed and
            added as separate components (volume, bounds, centre, cylindrical features with radius and axis), the
            source frame (bounds, which source faces a component touches) and the bounding-box change
  package   neutral and adversarial verifier prompts plus a Kaggle notebook (Qwen3.5-9B over two T4s)
  generate  (GPU) one verdict per prompt: brief notes, then {"correct": true|false, "violations": [...]}
  evaluate  flag rates on the failure-analysis groups (genuine valid errors, correct answers, benchmark issues)

  python semantic_verifier.py extract [--workers 8]
  python semantic_verifier.py package
  python semantic_verifier.py evaluate --verdicts DIR
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/semantic-verifier-astra-20261008"
PYTHON = ROOT / "tmp/cad-runtime/bin/python"
ASTRA = ROOT / "runs/multisource-cad-astra-20261004/scored"
CASES = ROOT / "runs/astra-failure-analysis-20261008/cases.json"
FEATURE_WORKER = r'''
import json, sys
from collections import Counter
sys.path.insert(0, sys.argv[2])
from verify_mechanical_cad_edits import execute
from OCP.BRepAdaptor import BRepAdaptor_Surface
job = json.load(open(sys.argv[1]))
r3 = lambda v: [round(x, 3) for x in v]
def frame(s):
    bb = s.BoundingBox()
    return dict(min=r3([bb.xmin, bb.ymin, bb.zmin]), max=r3([bb.xmax, bb.ymax, bb.zmax]), volume=round(s.Volume(), 3), faces=len(s.Faces()))
def cylinders(s):
    out = []
    for f in s.Faces():
        if f.geomType() == "CYLINDER":
            cy = BRepAdaptor_Surface(f.wrapped).Cylinder(); ax = cy.Axis(); d, p = ax.Direction(), ax.Location()
            c = dict(radius=round(cy.Radius(), 3), axis=r3([d.X(), d.Y(), d.Z()]), through_point=r3([p.X(), p.Y(), p.Z()]))
            if c not in out: out.append(c)
    return out[:6]
def component(s, src_bb, tol):
    bb = s.BoundingBox(); c = s.Center()
    faces = []
    for name, val, side in (("x-min", src_bb.xmin, bb.xmin), ("x-max", src_bb.xmax, bb.xmax), ("y-min", src_bb.ymin, bb.ymin),
                            ("y-max", src_bb.ymax, bb.ymax), ("z-min", src_bb.zmin, bb.zmin), ("z-max", src_bb.zmax, bb.zmax)):
        if abs(val - side) <= tol: faces.append(name)
    return dict(volume=round(s.Volume(), 3), min=r3([bb.xmin, bb.ymin, bb.zmin]), max=r3([bb.xmax, bb.ymax, bb.zmax]),
                size=r3([bb.xlen, bb.ylen, bb.zlen]), centre=r3([c.x, c.y, c.z]), at_source_bounds=faces,
                face_types=dict(Counter(f.geomType() for f in s.Faces())), cylinders=cylinders(s))
try:
    src = execute(job["source"]); cand = execute(job["candidate"])
    sb = src.BoundingBox(); tol = max(sb.DiagonalLength * 1e-4, 1e-4); vmin = src.Volume() * 1e-6
    inter = src.intersect(cand).Volume(); union = src.Volume() + cand.Volume() - inter
    res = dict(source=frame(src), edited=frame(cand), volume_iou_with_source=round(inter / union, 5) if union > 0 else 0.0)
    if res["volume_iou_with_source"] < 0.5:
        res["note"] = "most of the part moved or changed (whole-part transform or rebuild); components not itemised"
    else:
        res["removed"] = [component(x, sb, tol) for x in src.cut(cand).Solids() if x.Volume() > vmin][:8]
        res["added"] = [component(x, sb, tol) for x in cand.cut(src).Solids() if x.Volume() > vmin][:8]
    print(json.dumps(res))
except Exception as e:
    print(json.dumps(dict(error=type(e).__name__ + ": " + str(e)[:200])))
'''
CHECKS = ("feature type; feature count; dimensions (size, depth, angle); placement (location); coordinate frame; "
          "orientation (axis, normal, rotation); reference face/edge/plane; operation order and dependencies; edit scope "
          "(anything changed that the instruction does not ask for); geometric construction")
SYSTEM = {
    "neutral": ("You verify CAD edits. Decide whether the edited part implements the instruction exactly, using the original "
                "program, the edit and the measured change. Check: " + CHECKS + ". Write at most five short lines of notes, "
                "then a final line with only JSON: {\"correct\": true or false, \"violations\": [\"...\"]}."),
    "adversarial": ("You are an adversarial CAD reviewer. Your job is to find a concrete reason the edit does NOT implement the "
                    "instruction. Check: " + CHECKS + ". Report a violation only if the program or the measurements support "
                    "it; if you cannot find one, the edit is correct. Write at most five short lines of notes, then a final "
                    "line with only JSON: {\"correct\": true or false, \"violations\": [\"...\"]}."),
}


def rows() -> dict:
    sys.path.insert(0, str(ROOT / "scripts"))
    from multisource_cad_astra_benchmark import tasks
    return {r["id"]: r for r in tasks() if r["source"] == "BenchCAD"}


def extract(workers: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    preds = {json.loads(l)["id"]: json.loads(l) for l in (ASTRA / "astra-predictions.jsonl").read_text().splitlines()}
    path = OUT / "features.jsonl"
    done = {json.loads(l)["id"] for l in path.read_text().splitlines()} if path.exists() else set()
    jobs = [(i, r, preds[i]) for i, r in rows().items() if i not in done]

    def one(job):
        i, r, p = job
        if not p.get("predicted_code"):
            return dict(id=i, error="no applicable patch: " + str(p.get("error"))[:200])
        with tempfile.TemporaryDirectory() as d:
            Path(d, "w.py").write_text(FEATURE_WORKER)
            Path(d, "j.json").write_text(json.dumps(dict(source=r["code"], candidate=p["predicted_code"])))
            try:
                out = subprocess.run([str(PYTHON), str(Path(d, "w.py")), str(Path(d, "j.json")), str(ROOT / "scripts")],
                                     capture_output=True, text=True, timeout=600)
                feat = json.loads(out.stdout.strip().splitlines()[-1])
            except Exception as e:  # noqa: BLE001
                feat = dict(error="feature worker: " + type(e).__name__)
        return dict(id=i, **feat)
    with ThreadPoolExecutor(workers) as pool, path.open("a") as h:
        for n, fut in enumerate(as_completed([pool.submit(one, j) for j in jobs]), 1):
            h.write(json.dumps(fut.result()) + "\n"); h.flush()
            if n % 25 == 0:
                print("FEATURES", n, "/", len(jobs), flush=True)


def edit_ops(source: str, code: str) -> str:
    import difflib
    a, b = source.splitlines(), code.splitlines()
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != "equal":
            out.append(f"  at line {i1}: remove {[x.strip() for x in a[i1:i2]] or 'nothing'}; insert {[x.strip() for x in b[j1:j2]] or 'nothing'}")
    return "\n".join(out) or "  (no change)"


def package() -> None:
    preds = {json.loads(l)["id"]: json.loads(l) for l in (ASTRA / "astra-predictions.jsonl").read_text().splitlines()}
    feats = {json.loads(l)["id"]: json.loads(l) for l in (OUT / "features.jsonl").read_text().splitlines()}
    data = ROOT / "tmp/kaggle-semver/data"
    data.mkdir(parents=True, exist_ok=True)
    items = []
    for i, r in rows().items():
        f = feats.get(i, {})
        if "error" in f or not preds[i].get("predicted_code"):
            continue  # the kernel validator catches these before the semantic verifier
        numbered = "\n".join(f"{k}: {l}" for k, l in enumerate(r["code"].splitlines()))
        meas = json.dumps({k: v for k, v in f.items() if k != "id"}, separators=(",", ":"))
        user = (f"Instruction: {r['instruction']}\n\nOriginal program:\n{numbered}\n\nEdit applied:\n{edit_ops(r['code'], preds[i]['predicted_code'])}"
                f"\n\nMeasured change (lengths in mm; 'removed'/'added' are material components of the edited part relative to "
                f"the original; at_source_bounds lists original bounding faces a component reaches):\n{meas}")
        for variant, system in SYSTEM.items():
            items.append(dict(id=i, variant=variant, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}]))
    (data / "prompts.jsonl").write_text("".join(json.dumps(x) + "\n" for x in items))
    shutil.copy(Path(__file__), data / "semantic_verifier.py")
    (data / "dataset-metadata.json").write_text(json.dumps(dict(title="CAD semantic verifier prompts", id="ayushdebnath0123/cad-semver-data",
                                                                 licenses=[{"name": "CC0-1.0"}])))
    setup = ('import os, subprocess, sys, pathlib\n'
             'subprocess.run([sys.executable, "-m", "pip", "install", "-q", "transformers==5.18.0", "accelerate"], check=True)\n'
             'subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"])\n'
             'src = next(pathlib.Path("/kaggle/input").rglob("semantic_verifier.py")).parent\n'
             'r = subprocess.run([sys.executable, str(src / "semantic_verifier.py"), "generate", "--prompts", str(src / "prompts.jsonl"), '
             '"--out", "/kaggle/working/verdicts.jsonl"])\n'
             'assert r.returncode == 0\n')
    nb = {"cells": [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": setup}],
          "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    kernel = ROOT / "tmp/kaggle-semver/kernel"
    kernel.mkdir(parents=True, exist_ok=True)
    (kernel / "semver.ipynb").write_text(json.dumps(nb))
    (kernel / "kernel-metadata.json").write_text(json.dumps(dict(id="ayushdebnath0123/cad-semantic-verifier", title="CAD semantic verifier",
        code_file="semver.ipynb", language="python", kernel_type="notebook", is_private=True, enable_gpu=True, enable_internet=True,
        dataset_sources=["ayushdebnath0123/cad-semver-data"], competition_sources=[], kernel_sources=[], machine_shape="NvidiaTeslaT4")))
    print(json.dumps(dict(prompts=len(items), tasks=len({x["id"] for x in items}))))


def generate(a) -> None:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)
    tok.pad_token = tok.pad_token or tok.eos_token
    tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float16, device_map="auto", attn_implementation="sdpa").eval()
    items = [json.loads(l) for l in Path(a.prompts).read_text().splitlines() if l.strip()]
    done = {(json.loads(l)["id"], json.loads(l)["variant"]) for l in Path(a.out).read_text().splitlines()} if Path(a.out).exists() else set()
    items = [x for x in items if (x["id"], x["variant"]) not in done]
    items.sort(key=lambda x: len(json.dumps(x["messages"])))  # similar lengths per batch
    with open(a.out, "a") as h:
        for s in range(0, len(items), a.batch):
            batch = items[s:s + a.batch]
            texts = [tok.apply_chat_template(x["messages"], add_generation_prompt=True, tokenize=False, enable_thinking=False) for x in batch]
            enc = tok(texts, return_tensors="pt", padding=True, add_special_tokens=False).to(model.device)
            with torch.inference_mode():
                out = model.generate(**enc, max_new_tokens=a.max_new_tokens, do_sample=False, pad_token_id=tok.pad_token_id)
            for x, o in zip(batch, tok.batch_decode(out[:, enc.input_ids.shape[1]:], skip_special_tokens=True)):
                h.write(json.dumps(dict(id=x["id"], variant=x["variant"], text=o)) + "\n")
            h.flush()
            print("GENERATED", s + len(batch), "/", len(items), flush=True)


def verdict(text: str):
    for m in reversed(list(re.finditer(r"\{.*\}", text, re.S))):
        try:
            return bool(json.loads(m.group(0))["correct"])
        except Exception:  # noqa: BLE001
            continue
    m = re.search(r'"correct"\s*:\s*(true|false)', text)
    return None if m is None else m.group(1) == "true"


def evaluate(vdir: Path) -> None:
    cases = {c["id"]: c for c in json.loads(CASES.read_text())}
    geo = {json.loads(l)["id"]: json.loads(l)["match_strict"] for l in (ASTRA / "astra-predictions-geometry.jsonl").read_text().splitlines()}
    group = {}
    for i in rows():
        if geo[i]:
            group[i] = "correct (89)"
        elif cases[i[:16]]["category"].startswith("A"):
            group[i] = "benchmark issue (13)"
        elif cases[i[:16]]["category"] == "B":
            group[i] = "invalid (3)"
        else:
            group[i] = "genuine valid error (19)"
    verdicts = [json.loads(l) for l in (vdir / "verdicts.jsonl").read_text().splitlines()]
    res = {}
    for variant in ("neutral", "adversarial"):
        stats = {}
        for v in verdicts:
            if v["variant"] != variant:
                continue
            g = group[v["id"]]; s = stats.setdefault(g, dict(n=0, flagged=0, unparsed=0))
            ok = verdict(v["text"]); s["n"] += 1
            if ok is None:
                s["unparsed"] += 1
            elif not ok:
                s["flagged"] += 1
        res[variant] = stats
        print(variant, json.dumps(stats))
    (OUT / "summary.json").write_text(json.dumps(res, indent=1))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("extract", "package", "generate", "evaluate"))
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--prompts"); p.add_argument("--out"); p.add_argument("--verdicts", type=Path)
    p.add_argument("--model", default="Qwen/Qwen3.5-9B")
    p.add_argument("--batch", type=int, default=4); p.add_argument("--max-new-tokens", type=int, default=384)
    a = p.parse_args()
    if a.cmd == "extract":
        extract(a.workers)
    elif a.cmd == "package":
        package()
    elif a.cmd == "generate":
        generate(a)
    else:
        evaluate(a.verdicts)


if __name__ == "__main__":
    main()
