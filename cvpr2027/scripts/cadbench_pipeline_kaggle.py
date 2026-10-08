"""Batched Parametric CAD Bench v2+v3 pipeline for one GPU session (Kaggle or Colab): Qwen3.5 (9B in bf16 when a GPU
has >= 22 GB, otherwise 4B in fp16; it reads the drawings) and FreeCAD 1.1.0 from conda-forge (micromamba) with the
pinned validator for the reference-free integrity gates. Every generated script is cached in the output directory, so a
disconnected session resumes without regenerating; progress.json there tracks the run. Graders and reference models are never uploaded; scoring happens afterwards with the official
verifiers (cadbench_pipeline.py score).

Rounds keep the GPUs busy: (1) single answer (greedy, the zero-shot baseline) and one sampled alternative for every
task; (2..) diagnosis-driven repair of every failing branch; then selection by geometric agreement among passing
candidates (cadbench_pipeline.solve logic).

  python cadbench_pipeline_kaggle.py package                     (local) tasks.jsonl + drawings -> tmp/kaggle-cadbench/data
  python cadbench_pipeline_kaggle.py run --data DIR --out DIR    (Kaggle)
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def package() -> None:
    sys.path.insert(0, str(HERE))
    import cadbench_pipeline as cp
    data = HERE.parent / "tmp/kaggle-cadbench/data"
    (data / "images").mkdir(parents=True, exist_ok=True)
    rows = []
    for t in cp.tasks(["v2", "v3"]):
        imgs = []
        for img in t["images"]:
            shutil.copy(img, data / "images" / Path(img).name); imgs.append(Path(img).name)
        rows.append({k: t[k] for k in ("id", "bench", "task", "kind", "files", "instruction")} | {"images": imgs})
    (data / "tasks.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    for f in ("cadbench_pipeline.py", "cadbench_pipeline_kaggle.py"):
        shutil.copy(HERE / f, data / f)
    (data / "dataset-metadata.json").write_text(json.dumps(dict(title="CAD bench pipeline inputs", id="ayushdebnath0123/cad-bench-pipeline-inputs",
                                                                 licenses=[{"name": "CC0-1.0"}])))
    print(json.dumps(dict(tasks=len(rows), images=sum(len(r["images"]) for r in rows))))


def setup_freecad(prefix: Path, work: Path) -> None:
    if (prefix / "bin/python").exists():
        return
    mm = work / "micromamba"
    if not mm.exists():
        subprocess.run(f"curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -C {work} bin/micromamba"
                       f" && mv {work}/bin/micromamba {mm}", shell=True, check=True)
    subprocess.run([str(mm), "create", "-y", "-q", "-p", str(prefix), "-c", "conda-forge", "python=3.12", "freecad=1.1.0", "numpy=2.4.6",
                    "ocp=7.9.3.1", "scipy", "pydantic"], check=True)
    site = subprocess.run([str(prefix / "bin/python"), "-c", "import site; print(site.getsitepackages()[0])"], capture_output=True,
                          text=True, check=True).stdout.strip()
    Path(site, "freecad.pth").write_text(str(prefix / "lib") + "\n")
    subprocess.run([str(prefix / "bin/python"), "-m", "pip", "install", "-q", "gnucleus-freecad-validator==0.6.0"], check=True)
    subprocess.run([str(prefix / "bin/python"), "-c", "import FreeCAD, freecad_validator; print('FreeCAD', FreeCAD.Version()[:3])"], check=True)


class Generator:
    def __init__(self, model: str, max_new: int, batch: int, deadline: float, cache: Path):
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor
        self.torch = torch
        big = max(torch.cuda.get_device_properties(i).total_memory for i in range(torch.cuda.device_count())) >= 22e9
        bf16 = torch.cuda.get_device_capability(0)[0] >= 8
        if model == "auto":  # one T4 cannot hold the 9B model in 16-bit
            model = "Qwen/Qwen3.5-9B" if big or torch.cuda.device_count() > 1 else "Qwen/Qwen3.5-4B"
        self.name, dtype = model, (torch.bfloat16 if bf16 else torch.float16)
        print("MODEL", model, dtype, [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())], flush=True)
        self.proc = AutoProcessor.from_pretrained(model)
        self.proc.tokenizer.padding_side = "left"
        self.model = AutoModelForImageTextToText.from_pretrained(model, dtype=dtype, device_map="auto").eval()
        self.max_new, self.batch, self.deadline = max_new, batch, deadline
        self.cache_path = cache
        self.cache = {json.loads(l)["key"]: json.loads(l)["text"] for l in cache.read_text().splitlines()} if cache.exists() else {}

    def __call__(self, requests: list[dict]) -> list[str]:
        """requests: {messages, images (paths), sample}; returns texts in order (batched by length)."""
        from PIL import Image
        out = [self.cache.get(r["key"]) for r in requests]
        order = sorted((i for i in range(len(requests)) if out[i] is None), key=lambda i: len(json.dumps(requests[i]["messages"])))
        for s in range(0, len(order), self.batch):
            idx = order[s:s + self.batch]
            if time.time() > self.deadline:  # leave time to finalize and save before the session limit
                for i in idx:
                    out[i] = ""
                continue
            try:
                for i, t in zip(idx, self._generate([requests[i] for i in idx])):
                    out[i] = t
            except Exception as e:  # noqa: BLE001 - retry one by one; a request that still fails is an empty answer
                print("BATCH FAILED", type(e).__name__, str(e)[:300], flush=True)
                for i in idx:
                    try:
                        out[i] = self._generate([requests[i]])[0]
                    except Exception as e2:  # noqa: BLE001
                        print("REQUEST FAILED", type(e2).__name__, str(e2)[:300], flush=True); out[i] = ""
            with self.cache_path.open("a") as h:
                for i in idx:
                    if out[i]:
                        self.cache[requests[i]["key"]] = out[i]
                        h.write(json.dumps(dict(key=requests[i]["key"], text=out[i])) + "\n")
            print(f"GENERATED {min(s + self.batch, len(order))}/{len(order)}", flush=True)
            self.progress(dict(generated=min(s + self.batch, len(order)), of=len(order)))
        return out

    def progress(self, info: dict) -> None:
        p = self.cache_path.with_name("progress.json")
        state = json.loads(p.read_text()) if p.exists() else {}
        state.update(info, model=self.name, time=time.strftime("%Y-%m-%d %H:%M:%S"))
        p.write_text(json.dumps(state))

    def _generate(self, reqs: list[dict]) -> list[str]:
        from PIL import Image
        texts, images = [], []
        if True:
            for r in reqs:
                msgs = [dict(m) for m in r["messages"]]
                if r["images"]:
                    last = msgs[-1]
                    msgs[-1] = {"role": "user", "content": [{"type": "image"} for _ in r["images"]] + [{"type": "text", "text": last["content"]}]}
                    images += [Image.open(p).convert("RGB") for p in r["images"]]
                texts.append(self.proc.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False, enable_thinking=False))
            enc = self.proc(text=texts, images=images or None, return_tensors="pt", padding=True).to(self.model.device)
            sample = any(r["sample"] for r in reqs)
            with self.torch.inference_mode():
                gen = self.model.generate(**enc, max_new_tokens=self.max_new, do_sample=sample, temperature=0.8 if sample else None,
                                          top_p=0.95 if sample else None, pad_token_id=self.proc.tokenizer.pad_token_id)
            return self.proc.batch_decode(gen[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)


def run(a) -> None:
    sys.path.insert(0, str(Path(a.data)))
    import cadbench_pipeline as cp
    work = Path(a.work); work.mkdir(parents=True, exist_ok=True)
    prefix = work / "fc"
    setup_freecad(prefix, work)
    cp.FC_PYTHON, cp.FREECAD_LIB = prefix / "bin/python", prefix / "lib"
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tasks = [json.loads(l) for l in Path(a.data, "tasks.jsonl").read_text().splitlines()][: a.limit or None]
    for t in tasks:
        t["images"] = [str(Path(a.data) / "images" / p) for p in t["images"]]
        t["user"] = t["instruction"] + ("\n\nThe drawing is attached and is saved next to the script under the same file name." if t["images"] else "")
    t_start = time.time()
    gen = Generator(a.model, a.max_new, a.batch, deadline=t_start + a.hours * 3600, cache=out / "generations.jsonl")
    branches = {t["id"]: [] for t in tasks}  # per task: list of branches, each a list of nodes
    pool = ThreadPoolExecutor(4)

    def evaluate(t, kind, text, branch):
        script = cp.extract_code(text)
        res = cp.execute(t, script)
        node = dict(kind=kind, script=script, res=res, ok=cp.passes(res), diagnosis=cp.diagnosis(res))
        branch.append(node)
        return node
    t0 = time.time()
    reqs, meta = [], []
    for t in tasks:
        for k in range(1 + a.alternatives):
            hint = "" if k == 0 else "\n\nWrite an independent construction: choose the sketch planes, feature order and PartDesign features afresh."
            reqs.append(dict(messages=[{"role": "system", "content": cp.SYSTEM}, {"role": "user", "content": t["user"] + hint}],
                             images=t["images"], sample=k > 0, key=f"{t['id']}|{'single' if k == 0 else f'alternative{k}'}"))
            meta.append((t, "single" if k == 0 else f"alternative{k}"))
    texts = [None] * len(reqs)
    for sample in (False, True):  # greedy single answers and sampled alternatives never share a batch
        sel = [i for i, r in enumerate(reqs) if r["sample"] == sample]
        for i, text in zip(sel, gen([reqs[i] for i in sel])):
            texts[i] = text
    jobs = []
    for (t, kind), text in zip(meta, texts):  # one branch per first-round candidate; the single answer is branch 0
        b = []
        branches[t["id"]].append(b)
        jobs.append(pool.submit(evaluate, t, kind, text, b))
    [j.result() for j in jobs]
    gen.progress(dict(round=0, passing_singles=sum(branches[t["id"]][0][0]["ok"] for t in tasks)))
    print(f"ROUND 0 done in {time.time() - t0:.0f}s; passing singles {sum(branches[t['id']][0][0]['ok'] for t in tasks)}/{len(tasks)}", flush=True)
    for r in range(1, a.repairs + 1):
        if time.time() > gen.deadline:
            print("DEADLINE: skipping further repair rounds", flush=True); break
        reqs, meta = [], []
        for t in tasks:
            for b in branches[t["id"]]:
                cur = b[-1]
                if not cur["ok"]:
                    reqs.append(dict(messages=[{"role": "system", "content": cp.SYSTEM}, {"role": "user", "content": t["user"]},
                                               {"role": "assistant", "content": "```python\n" + cur["script"] + "```"},
                                               {"role": "user", "content": "Checks on this script found:\n- " + "\n- ".join(cur["diagnosis"])[:4000]
                                                + "\n\nReturn the corrected complete script."}], images=t["images"], sample=False,
                                    key=f"{t['id']}|repair{r}-of-{b[0]['kind']}"))
                    meta.append((t, b, f"repair{r}-of-{b[0]['kind']}"))
        if not reqs:
            break
        texts = gen(reqs)
        [f.result() for f in [pool.submit(evaluate, t, kind, text, b) for (t, b, kind), text in zip(meta, texts)]]
        print(f"ROUND {r} done in {time.time() - t0:.0f}s; repaired {len(reqs)} branches", flush=True)
        gen.progress(dict(round=r, repaired=len(reqs)))
    summary = []
    for t in tasks:
        nodes = [n for b in branches[t["id"]] for n in b]
        first = branches[t["id"]][0][0]
        cp.save(out, "single", t, first["script"], first["res"])
        ok = [n for n in nodes if n["ok"]]
        pick = first
        if ok:
            m = cp.ious([n["res"]["breps"].get(t["files"][-1]) for n in ok])
            support = [sum(x >= 0.99 for x in row) for row in m]
            pick = ok[max(range(len(ok)), key=lambda i: (support[i], -nodes.index(ok[i])))]
        cp.save(out, "pipeline", t, pick["script"], pick["res"])
        summary.append(dict(id=t["id"], kind=t["kind"], single_ok=first["ok"], any_ok=bool(ok), picked=pick["kind"],
                            nodes=[dict(kind=n["kind"], ok=n["ok"], diagnosis=n["diagnosis"][:2]) for n in nodes]))
        d = out / "trace" / t["bench"] / t["task"]; d.mkdir(parents=True, exist_ok=True)
        for n in nodes:
            (d / f"{n['kind']}.py").write_text(n["script"])
    (out / "summary.jsonl").write_text("".join(json.dumps(s) + "\n" for s in summary))
    final = dict(tasks=len(tasks), single_ok=sum(s["single_ok"] for s in summary), pipeline_ok=sum(s["any_ok"] for s in summary),
                 seconds=round(time.time() - t0))
    gen.progress(dict(done=True, **final))
    print(json.dumps(final), flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("package", "run"))
    p.add_argument("--data", default="."); p.add_argument("--out", default="/kaggle/working/out")
    p.add_argument("--model", default="auto"); p.add_argument("--work", default="/kaggle/working" if Path("/kaggle").exists() else "/content")
    p.add_argument("--max-new", type=int, default=4096); p.add_argument("--batch", type=int, default=6)
    p.add_argument("--alternatives", type=int, default=1); p.add_argument("--repairs", type=int, default=2)
    p.add_argument("--limit", type=int)
    p.add_argument("--hours", type=float, default=10.0, help="stop generating after this many hours, then save")
    a = p.parse_args()
    package() if a.cmd == "package" else run(a)


if __name__ == "__main__":
    main()
