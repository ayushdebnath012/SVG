"""Learned expected-response FEM checker: Qwen3.5-4B reads the source program, the instruction and the source part's
FEM response and predicts how the *correct* edit changes it (log compliance ratio, log p95 von Mises ratio). The draft
whose actual response is closest to the prediction is preferred. fem_expected_response.py does the same with a ridge
model over hand-made features (held-out R^2 0.39, 68 % of decisive comparisons); the ceiling with the true target's
response is 92 %.

Targets come from fem-reference-responses.jsonl (BenchCAD training tasks only). The model is trained on training
components; development components choose the switching margin; test tasks are never used for training or tuning.

  python fem_expected_llm.py package              (local: Kaggle dataset + notebook under tmp/kaggle-fem-expected)
  python fem_expected_llm.py train --data DIR      (GPU: LoRA + linear head, writes predictions-{dev,test}.jsonl)
  python fem_expected_llm.py evaluate --pred DIR   (local: R^2, decisive-comparison accuracy, margin, test score)
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ("You predict how a CAD edit changes a part's structural response. The scenario fixes the lowest 5 % of the part "
          "and applies a 1 N axial load to the top 5 %.")


def prompt(row: dict, src: dict, src_fem: dict) -> list[dict]:
    numbered = "\n".join(f"{k}: {l}" for k, l in enumerate(row["code"].splitlines()))
    bb = ", ".join(f"{x:.2f}" for x in src["bbox"])
    user = (f"Instruction: {row['instruction']}\n\nOriginal program:\n{numbered}\n\nOriginal part: volume {src['volume']:.1f} mm^3, "
            f"bounding box ({bb}) mm, {src['faces']} faces; compliance {src_fem['compliance']:.4g} mm/N, p95 von Mises stress "
            f"{src_fem['vm_p95']:.4g} MPa.\n\nHow do compliance and p95 stress change when the instruction is carried out correctly?")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def package() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import dpo_checker as dc
    import fem_expected_response as fe
    rows, trows = dc.train_rows(), dc.test_rows()
    out = ROOT / "tmp/kaggle-fem-expected"
    data = out / "data"
    data.mkdir(parents=True, exist_ok=True)
    split = {"train": [], "dev": []}
    for rec in dc.jl(fe.TARGETS):
        y = fe.response(rec.get("source_fem"), rec.get("reference_fem")) if "error" not in rec else None
        if y is None:
            continue
        row = rows[rec["task"]]
        split[dc.split_of(row["component_id"])].append(dict(task=rec["task"], prompt=prompt(row, rec["source"], rec["source_fem"]), y=list(y)))
    test = []
    for rec in dc.jl(dc.OUT / "evidence.jsonl"):
        if rec.get("split") == "test" and "drafts" in rec and rec.get("source_fem") and rec["source_fem"].get("ok"):
            test.append(dict(task=rec["task"], prompt=prompt(trows[rec["task"]], rec["source"], rec["source_fem"])))
    for name, items in (("train", split["train"]), ("dev", split["dev"]), ("test", test)):
        (data / f"{name}.jsonl").write_text("".join(json.dumps(i) + "\n" for i in items))
    shutil.copy(Path(__file__), data / "fem_expected_llm.py")
    (data / "dataset-metadata.json").write_text(json.dumps(dict(title="CAD expected FEM response", id="ayushdebnath0123/cad-fem-expected-data",
                                                                 licenses=[{"name": "CC0-1.0"}])))
    setup = ('import os, subprocess, sys, pathlib\nos.environ["CUDA_VISIBLE_DEVICES"] = "0"\n'
             'subprocess.run([sys.executable, "-m", "pip", "install", "-q", "transformers==5.18.0", "peft==0.21.2", "accelerate"], check=True)\n'
             'subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"])\n'
             'src = next(pathlib.Path("/kaggle/input").rglob("fem_expected_llm.py")).parent\n'
             'r = subprocess.run([sys.executable, str(src / "fem_expected_llm.py"), "train", "--data", str(src), "--out", "/kaggle/working"])\n'
             'print(open("/kaggle/working/train.log").read()[-4000:]); assert r.returncode == 0\n')
    nb = {"cells": [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": setup}],
          "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    kernel = out / "kernel"
    kernel.mkdir(exist_ok=True)
    (kernel / "fem-expected.ipynb").write_text(json.dumps(nb))
    (kernel / "kernel-metadata.json").write_text(json.dumps(dict(id="ayushdebnath0123/cad-fem-expected", title="CAD FEM expected response",
        code_file="fem-expected.ipynb", language="python", kernel_type="notebook", is_private=True, enable_gpu=True, enable_internet=True,
        dataset_sources=["ayushdebnath0123/cad-fem-expected-data"], competition_sources=[], kernel_sources=[], machine_shape="NvidiaTeslaT4")))
    print(json.dumps({k: len(v) for k, v in (("train", split["train"]), ("dev", split["dev"]), ("test", test))}))


def train(a) -> None:
    import random
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer
    log = open(Path(a.out) / "train.log", "a")

    def say(**kw):
        print(json.dumps(kw), file=log, flush=True); print(json.dumps(kw), flush=True)
    load = lambda n: [json.loads(l) for l in (Path(a.data) / f"{n}.jsonl").read_text().splitlines() if l.strip()]  # noqa: E731
    tr, dv, te = load("train"), load("dev"), load("test")
    tok = AutoTokenizer.from_pretrained(a.model)
    tok.pad_token = tok.pad_token or tok.eos_token
    text = lambda r: tok.apply_chat_template(r["prompt"], add_generation_prompt=True, tokenize=False, enable_thinking=False)  # noqa: E731
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float16, device_map={"": 0}, attn_implementation="sdpa")
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules="all-linear", task_type="CAUSAL_LM"))
    head = torch.nn.Linear(model.config.get_text_config().hidden_size, 2).to(0).float()
    ys = torch.tensor([r["y"] for r in tr], dtype=torch.float32)
    mu, sd = ys.mean(0), ys.std(0).clamp(min=1e-3)

    def embed(r):
        enc = tok([text(r)], return_tensors="pt", add_special_tokens=False, truncation=True, max_length=a.max_length).to(0)
        with torch.autocast("cuda", dtype=torch.float16):
            out = model(**enc, output_hidden_states=True, logits_to_keep=1)
        return out.hidden_states[-1][:, -1, :].float()
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW([{"params": params, "lr": a.lr}, {"params": head.parameters(), "lr": a.lr * 10}])
    scaler = torch.amp.GradScaler("cuda")
    rng, accum, step = random.Random(17), 8, 0

    def predict(items):
        model.eval(); head.eval(); preds = []
        with torch.no_grad():
            for r in items:
                preds.append((head(embed(r))[0].cpu() * sd + mu).tolist())
        model.train(); head.train()
        return preds

    def r2(items, preds):
        y = torch.tensor([r["y"] for r in items]); p = torch.tensor(preds)
        return (1 - ((p - y) ** 2).sum(0) / ((y - y.mean(0)) ** 2).sum(0)).tolist()
    model.train()
    for epoch in range(a.epochs):
        order = rng.sample(range(len(tr)), len(tr)); run = 0.0
        for k, i in enumerate(order):
            r = tr[i]
            pred = head(embed(r))[0]
            loss = torch.nn.functional.smooth_l1_loss(pred, (torch.tensor(r["y"]).to(0) - mu.to(0)) / sd.to(0)) / accum
            if not torch.isfinite(loss):
                raise FloatingPointError("non-finite loss")
            scaler.scale(loss).backward(); run += float(loss) * accum
            if (k + 1) % accum == 0 or k + 1 == len(order):
                scaler.unscale_(opt); torch.nn.utils.clip_grad_norm_(params + list(head.parameters()), 1.0)
                scaler.step(opt); scaler.update(); opt.zero_grad(set_to_none=True); step += 1
        pd = predict(dv)
        say(epoch=epoch + 1, train_loss=run / len(order), dev_r2=r2(dv, pd))
    for name, items in (("dev", dv), ("test", te)):
        preds = predict(items)
        (Path(a.out) / f"predictions-{name}.jsonl").write_text("".join(json.dumps(dict(task=r["task"], pred=p)) + "\n" for r, p in zip(items, preds)))
    say(done=True)


def evaluate(pred_dir: Path) -> None:
    import numpy as np
    sys.path.insert(0, str(ROOT / "scripts"))
    import dpo_checker as dc
    import fem_expected_response as fe
    load = lambda n: {json.loads(l)["task"]: np.array(json.loads(l)["pred"]) for l in (pred_dir / f"predictions-{n}.jsonl").read_text().splitlines()}  # noqa: E731
    pdev, ptest = load("dev"), load("test")
    rows = dc.train_rows()
    ys = {r["task"]: fe.response(r.get("source_fem"), r.get("reference_fem")) for r in dc.jl(fe.TARGETS) if "error" not in r}
    Y = np.array([ys[t] for t in pdev]); P = np.array([pdev[t] for t in pdev])
    r2 = 1 - ((P - Y) ** 2).sum(0) / ((Y - Y.mean(0)) ** 2).sum(0)
    print(f"development R^2: compliance {r2[0]:.3f}, p95 stress {r2[1]:.3f} ({len(pdev)} tasks)")
    dev = []  # Astra's first training draft against its best challenger by distance to the prediction
    for rec in dc.jl(dc.OUT / "evidence.jsonl"):
        if rec.get("split") != "train" or "drafts" not in rec or rec["task"] not in pdev:
            continue
        drafts = [d for d in rec["drafts"] if "error" not in d and "reference" not in d["origins"] and fe.response(rec["source_fem"], d.get("fem"))]
        inc = next((d for d in drafts if "astra0" in d["origins"]), None)
        if inc is None or len(drafts) < 2:
            continue
        dist = {id(d): float(np.abs(np.array(fe.response(rec["source_fem"], d["fem"])) - pdev[rec["task"]]).sum()) for d in drafts}
        ch = min((d for d in drafts if d is not inc), key=lambda d: dist[id(d)])
        dev.append((dist[id(inc)] - dist[id(ch)], ch.get("iou_reference", 0) >= dc.STRICT, inc.get("iou_reference", 0) >= dc.STRICT))
    best = (0, math.inf)
    for m in sorted({x[0] for x in dev} | {math.inf}):
        net = sum(int(c and not i) - int(i and not c) for adv, c, i in dev if adv > m)
        best = max(best, (net, m))
    margin = best[1]
    print(f"development comparisons {len(dev)}: switching could gain {sum(c and not i for _, c, i in dev)}, lose "
          f"{sum(i and not c for _, c, i in dev)}; chosen margin {margin} (net {best[0]})")
    geo = {r["id"]: r["match_strict"] for r in dc.jl(dc.GOT / "all-drafts-predictions-geometry.jsonl")}
    ok = {(r["id"].split("#")[0], r["predicted_code"]): geo[r["id"]] for r in dc.jl(dc.GOT / "all-drafts-predictions.jsonl")}
    astra = {r["id"]: r["match_strict"] for r in dc.jl(dc.ASTRA_TEST)}
    right = wrong = 0; gain = loss = switched = 0
    forced = [0, 0]
    for rec in dc.jl(dc.OUT / "evidence.jsonl"):
        t = rec["task"]
        if rec.get("split") != "test" or "drafts" not in rec or t not in ptest:
            continue
        resp = {d["code"]: fe.response(rec["source_fem"], d.get("fem")) for d in rec["drafts"] if "error" not in d}
        resp = {c: np.array(v) for c, v in resp.items() if v is not None}
        inc = next((d["code"] for d in rec["drafts"] if "vanilla" in d["origins"]), None)
        if inc not in resp:
            continue
        dist = {c: float(np.abs(v - ptest[t]).sum()) for c, v in resp.items()}
        for c in resp:
            if c != inc and ok[(t, c)] != astra[t]:
                if (dist[c] < dist[inc]) == ok[(t, c)]:
                    right += 1
                else:
                    wrong += 1
        ch = min((c for c in resp if c != inc), key=lambda c: dist[c], default=None)
        if ch is not None and dist[inc] - dist[ch] > 0:
            forced[0] += ok[(t, ch)] and not astra[t]; forced[1] += astra[t] and not ok[(t, ch)]
        if ch is not None and dist[inc] - dist[ch] > margin:
            switched += 1; gain += ok[(t, ch)] and not astra[t]; loss += astra[t] and not ok[(t, ch)]
    base = sum(astra[t] for t in dc.test_rows())
    res = dict(dev_r2=[round(float(x), 3) for x in r2], decisive=right + wrong, correct=right, accuracy=round(right / max(1, right + wrong), 3),
               margin=None if margin == math.inf else margin, switched=switched, gained=int(gain), lost=int(loss), score=base + int(gain) - int(loss),
               always_switch_when_closer=dict(gained=int(forced[0]), lost=int(forced[1]), score=base + int(forced[0]) - int(forced[1])))
    print(json.dumps(res))
    (dc.OUT / "fem-expected-llm.json").write_text(json.dumps(res, indent=1))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("package", "train", "evaluate"))
    p.add_argument("--data"); p.add_argument("--out", default="."); p.add_argument("--pred", type=Path)
    p.add_argument("--model", default="Qwen/Qwen3.5-4B")
    p.add_argument("--epochs", type=int, default=4); p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--max-length", type=int, default=3072)
    a = p.parse_args()
    {"package": package, "train": lambda: train(a), "evaluate": lambda: evaluate(a.pred)}[a.cmd]() if a.cmd != "package" else package()


if __name__ == "__main__":
    main()
