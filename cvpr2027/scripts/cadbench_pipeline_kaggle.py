"""Batched Parametric CAD Bench v2+v3 pipeline for one GPU session (Kaggle or Colab): Qwen3.5 (9B when the GPUs hold it
in 16-bit, otherwise 4B; it reads the drawings) served by vLLM (tensor-parallel over every GPU; the transformers path is the
fallback), and FreeCAD 1.1.0 from conda-forge (micromamba) with the pinned validator for the reference-free integrity
gates. Every generated script is cached in the output directory, so a later session resumes from it (--resume) without
regenerating; progress.json there tracks the run. Graders and reference models are never uploaded; scoring happens
afterwards with the official verifiers (cadbench_pipeline.py score).

Rounds: (1) single answer (greedy, the zero-shot baseline) and one sampled alternative for every task; (2..)
diagnosis-driven repair of every failing branch; then selection by geometric agreement among passing candidates
(cadbench_pipeline.solve logic).

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
    for attempt in range(6):  # the GitHub release binary, else the micro.mamba.pm archive; either host can fail for a while
        if mm.exists() and subprocess.run([str(mm), "--version"], capture_output=True).returncode == 0:
            break
        mm.unlink(missing_ok=True)
        if subprocess.run(f"curl -fsSL --retry 3 -o {mm} https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-64"
                          f" && chmod +x {mm}", shell=True).returncode:
            subprocess.run(f"curl -fsSL --retry 3 https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj -C {work} bin/micromamba"
                           f" && mv {work}/bin/micromamba {mm}", shell=True)
        time.sleep(0 if mm.exists() else 30)
    else:
        raise RuntimeError("could not download micromamba")
    subprocess.run([str(mm), "create", "-y", "-q", "-p", str(prefix), "-c", "conda-forge", "python=3.12", "freecad=1.1.0", "numpy=2.4.6",
                    "ocp=7.9.3.1", "scipy", "pydantic"], check=True)
    site = subprocess.run([str(prefix / "bin/python"), "-c", "import site; print(site.getsitepackages()[0])"], capture_output=True,
                          text=True, check=True).stdout.strip()
    Path(site, "freecad.pth").write_text(str(prefix / "lib") + "\n")
    subprocess.run([str(prefix / "bin/python"), "-m", "pip", "install", "-q", "gnucleus-freecad-validator==0.6.0"], check=True)
    subprocess.run([str(prefix / "bin/python"), "-c", "import FreeCAD, freecad_validator; print('FreeCAD', FreeCAD.Version()[:3])"], check=True)


VLLM_WHEEL = ("https://github.com/vllm-project/vllm/releases/download/v0.31.0/vllm-0.31.0+cu129-cp38-abi3-manylinux_2_28_x86_64.whl")


class Cached:
    """Generation cache (one JSON line per finished request, keyed by task and node) and progress.json beside it."""

    def __init__(self, deadline: float, cache: Path):
        self.deadline, self.cache_path = deadline, cache
        self.cache = {json.loads(l)["key"]: json.loads(l)["text"] for l in cache.read_text().splitlines()} if cache.exists() else {}

    def store(self, key: str, text: str) -> None:
        if text:
            self.cache[key] = text
            with self.cache_path.open("a") as h:
                h.write(json.dumps(dict(key=key, text=text)) + "\n")

    def progress(self, info: dict) -> None:
        p = self.cache_path.with_name("progress.json")
        state = json.loads(p.read_text()) if p.exists() else {}
        state.update(info, model=self.name, time=time.strftime("%Y-%m-%d %H:%M:%S"))
        p.write_text(json.dumps(state))


def start_vllm(model: str, work: Path, max_len: int) -> str | None:
    """vLLM in its own venv (the CUDA 12.9 build, for the Kaggle driver), tensor-parallel over every GPU, fp16 (T4 has no
    bf16, so fp16 there). Returns the chat endpoint, or None when it cannot serve (then the transformers path runs instead)."""
    import urllib.request
    venv = work / "vllm-env"
    py, logf = venv / "bin/python", work / "vllm-install.log"
    try:
        if not (venv / "bin/vllm").exists():
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "uv"], check=True)
            # --python names the venv explicitly: the Kaggle image's uv settings otherwise send the install elsewhere
            with logf.open("w") as h:
                subprocess.run(f"uv venv -p {sys.executable} {venv} && uv pip install --python {py} '{VLLM_WHEEL}' "
                               "--extra-index-url https://download.pytorch.org/whl/cu129 --index-strategy unsafe-best-match",
                               shell=True, check=True, timeout=2400, stdout=h, stderr=subprocess.STDOUT)
        # torchcodec (audio only) cannot load on Kaggle, and vLLM tolerates its absence but not a broken install
        subprocess.run(f"uv pip uninstall --python {py} torchcodec", shell=True, capture_output=True)
        check = subprocess.run([str(py), "-c", "import vllm.multimodal.media, torch; print(torch.__version__, torch.cuda.is_available())"],
                               capture_output=True, text=True, timeout=600)
        print("VLLM CHECK", check.stdout.strip(), check.stderr.strip()[-300:], flush=True)
        if check.returncode or not check.stdout.strip().endswith("True") or not (venv / "bin/vllm").exists():
            raise RuntimeError("vllm is not usable in " + str(venv))
    except Exception as e:  # noqa: BLE001
        tail = "\n".join(logf.read_text().splitlines()[-15:]) if logf.exists() else ""
        print("VLLM INSTALL FAILED", type(e).__name__, str(e)[:300], "\n" + tail, flush=True)
        return None
    gpus = len(subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True).stdout.strip().splitlines())
    cap = float(subprocess.run(["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"], capture_output=True,
                               text=True).stdout.split()[0])
    env = dict(os.environ, VLLM_USE_FLASHINFER_SAMPLER="0", PATH=f"{venv}/bin:" + os.environ["PATH"])
    for extra in ([], ["--enforce-eager"]):  # second try without torch.compile / CUDA graphs
        cmd = [str(venv / "bin/vllm"), "serve", model, "--host", "127.0.0.1", "--port", "8000", "--dtype", "bfloat16" if cap >= 8 else "float16",
               "--tensor-parallel-size", str(gpus), "--max-model-len", str(max_len), "--gpu-memory-utilization", "0.9",
               "--max-num-seqs", "32", "--seed", "17", "--limit-mm-per-prompt", '{"image": 2}', *extra]
        print("VLLM START", " ".join(cmd[2:]), flush=True)
        log = (work / "vllm.log").open("a")
        try:
            proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)
        except OSError as e:
            print("VLLM FAILED", e, flush=True)
            return None
        t0 = time.time()
        while proc.poll() is None and time.time() - t0 < 2400:
            try:
                urllib.request.urlopen("http://127.0.0.1:8000/v1/models", timeout=5)
            except Exception:  # noqa: BLE001 - not up yet
                time.sleep(15)
                continue
            body = json.dumps(dict(model=model, messages=[{"role": "user", "content": "Write a FreeCAD script that makes a cube."}],
                                   max_tokens=64, temperature=0, chat_template_kwargs=dict(enable_thinking=False))).encode()
            try:
                req = urllib.request.Request("http://127.0.0.1:8000/v1/chat/completions", body, {"Content-Type": "application/json"})
                text = json.loads(urllib.request.urlopen(req, timeout=600).read())["choices"][0]["message"]["content"] or ""
            except Exception as e:  # noqa: BLE001
                text = f"<{type(e).__name__}: {e}>"
            print(f"VLLM READY after {time.time() - t0:.0f}s; probe: {text[:120]!r}", flush=True)
            if sum(c.isalpha() for c in text) >= 10:  # fp16 overflow shows up as empty or punctuation-only output
                return "http://127.0.0.1:8000/v1/chat/completions"
            break
        proc.kill(); proc.wait()
        print("VLLM FAILED; log tail:\n" + "\n".join((work / "vllm.log").read_text().splitlines()[-25:]), flush=True)
    return None


class ServerGenerator(Cached):
    """Concurrent requests to the local vLLM server; same request format and cache as the transformers Generator."""

    def __init__(self, model: str, endpoint: str, max_new: int, deadline: float, cache: Path, workers: int = 32):
        super().__init__(deadline, cache)
        self.name, self.endpoint, self.max_new, self.workers = model, endpoint, max_new, workers
        self.lock = __import__("threading").Lock()

    def one(self, r: dict) -> str:
        import base64
        import urllib.request
        msgs = [dict(m) for m in r["messages"]]
        if r["images"]:
            msgs[-1] = {"role": "user", "content": [{"type": "image_url", "image_url": {"url": "data:image/png;base64,"
                        + base64.b64encode(Path(p).read_bytes()).decode()}} for p in r["images"]] + [{"type": "text", "text": msgs[-1]["content"]}]}
        body = dict(model=self.name, messages=msgs, max_tokens=r.get("max_new", self.max_new), seed=17,
                    temperature=0.8 if r["sample"] else 0.0, top_p=0.95 if r["sample"] else 1.0, chat_template_kwargs=dict(enable_thinking=False))
        for attempt in range(3):
            try:
                req = urllib.request.Request(self.endpoint, json.dumps(body).encode(), {"Content-Type": "application/json"})
                return json.loads(urllib.request.urlopen(req, timeout=3600).read())["choices"][0]["message"]["content"] or ""
            except Exception as e:  # noqa: BLE001 - a prompt too long for max_tokens gets a shorter budget
                msg = getattr(e, "read", lambda: b"")().decode(errors="replace") if hasattr(e, "read") else str(e)
                print("REQUEST FAILED", type(e).__name__, msg[:300], flush=True)
                body["max_tokens"] = max(1024, body["max_tokens"] // 2)
        return ""

    def __call__(self, requests: list[dict]) -> list[str]:
        out = [self.cache.get(r["key"]) for r in requests]
        todo = [i for i in range(len(requests)) if out[i] is None]
        done = 0

        def work(i):
            nonlocal done
            text = "" if time.time() > self.deadline else self.one(requests[i])
            with self.lock:
                out[i] = text
                self.store(requests[i]["key"], text)
                done += 1
                if done % 10 == 0 or done == len(todo):
                    print(f"GENERATED {done}/{len(todo)}", flush=True)
                    self.progress(dict(generated=done, of=len(todo)))
        with ThreadPoolExecutor(self.workers) as ex:
            list(ex.map(work, todo))
        return out


class Generator(Cached):
    def __init__(self, model: str, max_new: int, batch: int, deadline: float, cache: Path):
        super().__init__(deadline, cache)
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor
        self.torch = torch
        bf16 = torch.cuda.get_device_capability(0)[0] >= 8
        dtype = torch.bfloat16 if bf16 else torch.float16
        while True:
            self.name = model
            print("MODEL", model, dtype, [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())], flush=True)
            self.proc = AutoProcessor.from_pretrained(model)
            self.proc.tokenizer.padding_side = "left"
            # GPU 0 also holds the vision tower and the activations, so it gets less of the weights
            mem = {i: f"{int(torch.cuda.get_device_properties(i).total_memory / 2**30 * (0.62 if i == 0 else 0.85))}GiB"
                   for i in range(torch.cuda.device_count())}
            self.model = AutoModelForImageTextToText.from_pretrained(model, dtype=dtype, device_map="auto", max_memory=mem).eval()
            probe = self.proc(text=[self.proc.apply_chat_template([{"role": "user", "content": "Write a FreeCAD script that makes a cube."}],
                                                                  add_generation_prompt=True, tokenize=False, enable_thinking=False)],
                              return_tensors="pt").to(self.model.device)
            with torch.inference_mode():
                finite = bool(torch.isfinite(self.model(**probe).logits).all())
            print("FP CHECK", model, "finite" if finite else "OVERFLOW", flush=True)
            if finite or bf16 or model == "Qwen/Qwen3.5-4B":  # Qwen3.5 is trained in bf16; fp16 can overflow on a T4
                break
            del self.model; torch.cuda.empty_cache()
            model = "Qwen/Qwen3.5-4B"
        self.max_new, self.batch = max_new, batch

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
            for i in idx:
                self.store(requests[i]["key"], out[i])
            print(f"GENERATED {min(s + self.batch, len(order))}/{len(order)}", flush=True)
            self.progress(dict(generated=min(s + self.batch, len(order)), of=len(order)))
        return out

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
                gen = self.model.generate(**enc, max_new_tokens=max(r.get("max_new", self.max_new) for r in reqs), do_sample=sample, temperature=0.8 if sample else None,
                                          top_p=0.95 if sample else None, pad_token_id=self.proc.tokenizer.pad_token_id)
            return self.proc.batch_decode(gen[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)


def run(a) -> None:
    sys.path.insert(0, str(Path(a.data)))
    import cadbench_pipeline as cp
    work = Path(a.work); work.mkdir(parents=True, exist_ok=True)
    if not os.environ.get("CADBENCH_FC_PYTHON"):  # a machine with FreeCAD set up already keeps cadbench_pipeline's paths
        prefix = work / "fc"
        setup_freecad(prefix, work)
        cp.FC_PYTHON, cp.FREECAD_LIB = prefix / "bin/python", prefix / "lib"
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tasks = [json.loads(l) for l in Path(a.data, "tasks.jsonl").read_text().splitlines()][: a.limit or None]
    for t in tasks:
        t["images"] = [str(Path(a.data) / "images" / p) for p in t["images"]]
        t["user"] = t["instruction"] + ("\n\nThe drawing is attached and is saved next to the script under the same file name." if t["images"] else "")
    t_start = time.time()
    cache = out / "generations.jsonl"
    if a.resume and not cache.exists():  # a previous session's generations: those requests are not generated again
        shutil.copy(a.resume, cache)
        print("RESUMED", sum(1 for _ in cache.open()), "cached generations", flush=True)
    model = a.model
    if model == "auto":  # one T4 cannot hold the 9B model in 16-bit
        mib = [int(x) for x in subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                                              capture_output=True, text=True).stdout.split()]
        model = "Qwen/Qwen3.5-9B" if max(mib) >= 22000 or len(mib) > 1 else "Qwen/Qwen3.5-4B"
    endpoint = a.endpoint or (start_vllm(model, work, a.max_len) if a.engine in ("auto", "vllm") else None)
    if endpoint:
        gen = ServerGenerator(model, endpoint, a.max_new, deadline=t_start + a.hours * 3600, cache=cache)
    else:
        gen = Generator(model, a.max_new, a.batch, deadline=t_start + a.hours * 3600, cache=cache)
    print("ENGINE", "vllm" if endpoint else "transformers", gen.name, flush=True)
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
                                    max_new=a.repair_max_new, key=f"{t['id']}|repair{r}-of-{b[0]['kind']}"))
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
    p.add_argument("--max-new", type=int, default=4096); p.add_argument("--batch", type=int, default=4)
    p.add_argument("--alternatives", type=int, default=1); p.add_argument("--repairs", type=int, default=3)
    p.add_argument("--limit", type=int)
    p.add_argument("--engine", choices=("auto", "vllm", "transformers"), default="auto", help="auto: vLLM, else transformers")
    p.add_argument("--max-len", type=int, default=32768, help="vLLM context length")
    p.add_argument("--repair-max-new", type=int, default=8192, help="token budget of a repair (whole corrected script)")
    p.add_argument("--resume", help="generations.jsonl of an earlier session")
    p.add_argument("--endpoint", help="an already running OpenAI-compatible chat endpoint serving --model")
    p.add_argument("--hours", type=float, default=10.0, help="stop generating after this many hours, then save")
    a = p.parse_args()
    package() if a.cmd == "package" else run(a)


if __name__ == "__main__":
    main()
