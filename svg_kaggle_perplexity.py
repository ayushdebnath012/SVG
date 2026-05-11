#!/usr/bin/env python
"""SVG Perplexity & Overfitting Check — Kaggle Edition (OmniSVG weights).

Paste into a single Kaggle notebook cell. Requires: GPU T4, Internet ON.

Pipeline:
  1. Installs dependencies
  2. Loads OmniSVG/MMSVG SVG-code datasets from HuggingFace
  3. Remaps OmniSVG checkpoint keys in a subprocess (memory-isolated)
  4. Loads the real OmniSVG model with 4-bit quantization
  5. Computes SVG-token perplexity on train/eval splits
  6. Assesses overfitting and writes reports
"""

from __future__ import annotations

# ── CONFIG ─────────────────────────────────────────────────────────────
OMNISVG_MODEL = "OmniSVG/OmniSVG"
OMNISVG_BASE = "Qwen/Qwen2.5-VL-3B-Instruct"
MAX_ROWS = 1000
EVAL_FRAC = 0.2
MAX_SEQ_LEN = 1024
BATCH_SIZE = 1
OUTPUT_DIR = "./svg_perplexity_check"
OMNISVG_HF_DATASETS = ["OmniSVG/MMSVG-Icon", "OmniSVG/MMSVG-Illustration"]

SYSTEM_PROMPT = (
    "You are an SVG code generator. Given a text description, output ONLY valid "
    "SVG code. Use simple geometric SVG elements, solid colors, and no explanation."
)
PROMPT_KEYS = ("prompt", "text", "caption", "concept", "description", "name")
SVG_KEYS = ("svg", "svg_code", "code", "target", "output", "response", "answer")
# ───────────────────────────────────────────────────────────────────────

import gc
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm


def log(msg: str) -> None:
    print(msg, flush=True)


# ── 0. DEPENDENCIES ──────────────────────────────────────────────────

def ensure_deps():
    log("Installing dependencies...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-U", "--quiet",
         "bitsandbytes>=0.46.1", "accelerate", "transformers", "datasets",
         "peft", "safetensors"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    log("Dependencies OK.")


# ── 1. DATA ──────────────────────────────────────────────────────────

def pick(record, keys):
    for k in keys:
        v = record.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def normalize(record):
    p, s = pick(record, PROMPT_KEYS), pick(record, SVG_KEYS)
    msgs = record.get("messages")
    if (not p or not s) and isinstance(msgs, list):
        for m in msgs:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role", "")).lower()
            c = str(m.get("content", "")).strip()
            if role in {"user", "human"} and not p:
                p = c
            elif role in {"assistant", "model"} and not s:
                s = c
    if not p or not s:
        return None
    if "<svg" not in s.lower() and "<path" not in s.lower():
        return None
    return {"prompt": p, "svg": s}


def load_data(max_rows, ds_names):
    from datasets import load_dataset
    rows = []
    per_ds = math.ceil(max_rows / max(len(ds_names), 1))
    for name in ds_names:
        log(f"  Loading {name}...")
        try:
            ds = load_dataset(name, streaming=True)
        except Exception as e:
            log(f"    Warning: {e}")
            continue
        n = 0
        for split in ds.values():
            for rec in split:
                item = normalize(rec)
                if item:
                    item["source"] = name
                    rows.append(item)
                    n += 1
                if n >= per_ds or len(rows) >= max_rows:
                    break
            if n >= per_ds or len(rows) >= max_rows:
                break
        log(f"    → {n} rows")
        if len(rows) >= max_rows:
            break
    return rows[:max_rows]


def split_data(records, frac):
    if len(records) <= 1:
        return list(records), []
    ec = max(1, min(int(round(len(records) * frac)), len(records) - 1))
    ordered = sorted(records, key=lambda r: hashlib.sha256(
        f"{r.get('prompt','')}\n{r.get('svg','')}".encode()).hexdigest())
    return ordered[ec:], ordered[:ec]


# ── 2. MODEL ─────────────────────────────────────────────────────────

def remap_checkpoint_in_subprocess(weight_file: str, config_file: str, temp_dir: str):
    """Remap OmniSVG keys in isolated subprocess. Kaggle has 16GB RAM — enough."""
    script = f'''
import torch, shutil, os, gc, sys
print("  [subprocess] Loading checkpoint...", flush=True)
sd = torch.load("{weight_file}", map_location="cpu")
if "state_dict" in sd and isinstance(sd["state_dict"], dict):
    sd = sd["state_dict"]
keys = list(sd.keys())
if keys and sum(k.startswith("transformer.") for k in keys[:100]) > len(keys[:100]) // 2:
    sd = {{k.removeprefix("transformer."): v for k, v in sd.items()}}
    print(f"  [subprocess] Remapped {{len(sd)}} keys (stripped transformer. prefix)", flush=True)
else:
    print(f"  [subprocess] No prefix remapping needed ({{len(keys)}} keys)", flush=True)
shutil.copy("{config_file}", os.path.join("{temp_dir}", "config.json"))
out = os.path.join("{temp_dir}", "model.safetensors")
print(f"  [subprocess] Saving as safetensors...", flush=True)
try:
    from safetensors.torch import save_file
    save_file(sd, out)
except Exception as e:
    print(f"  [subprocess] safetensors failed ({{e}}), using torch.save", flush=True)
    out = os.path.join("{temp_dir}", "pytorch_model.bin")
    torch.save(sd, out)
del sd
gc.collect()
print("  [subprocess] Done.", flush=True)
'''
    log("Remapping OmniSVG checkpoint keys (subprocess, memory-isolated)...")
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True,
    )
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            log(line)
    if result.returncode != 0:
        log(f"Subprocess stderr: {result.stderr[-500:] if result.stderr else 'none'}")
        raise RuntimeError(f"Checkpoint remapping failed (exit code {result.returncode})")
    log("Checkpoint remapping complete.")


def load_omnisvg_model():
    from transformers import AutoTokenizer, BitsAndBytesConfig
    from huggingface_hub import hf_hub_download

    # Tokenizer from the base model
    log(f"Loading tokenizer from {OMNISVG_BASE}...")
    tokenizer = AutoTokenizer.from_pretrained(OMNISVG_BASE, trust_remote_code=True, padding_side="right")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    test = tokenizer("hello", padding=False)["input_ids"]
    assert len(test) > 0, "Tokenizer broken!"
    log(f"Tokenizer OK: vocab={tokenizer.vocab_size}")

    # Download OmniSVG weight file + config
    log(f"Downloading OmniSVG weights from {OMNISVG_MODEL}...")
    weight_file = hf_hub_download(repo_id=OMNISVG_MODEL, filename="pytorch_model.bin")
    config_file = hf_hub_download(repo_id=OMNISVG_MODEL, filename="config.json")
    log(f"Weight file: {weight_file} ({os.path.getsize(weight_file) / 1e9:.1f} GB)")

    # Remap keys in subprocess
    temp_dir = tempfile.mkdtemp(prefix="omnisvg_remapped_")
    try:
        remap_checkpoint_in_subprocess(weight_file, config_file, temp_dir)

        # Verify temp dir contents
        contents = os.listdir(temp_dir)
        log(f"Temp dir contents: {contents}")

        # Load with 4-bit quantization
        log("Loading remapped OmniSVG model with 4-bit quantization...")
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        try:
            from transformers import Qwen2_5_VLForConditionalGeneration as QwenCls
        except ImportError:
            from transformers import Qwen2VLForConditionalGeneration as QwenCls

        quant = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
        model = QwenCls.from_pretrained(
            temp_dir,
            quantization_config=quant,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
        )
        model.eval()
        log("OmniSVG model loaded successfully with real weights!")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return model, tokenizer


# ── 3. PERPLEXITY ────────────────────────────────────────────────────

def build_chat(tokenizer, prompt, svg):
    msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Generate SVG for: {prompt}"},
    ]
    ans = {"role": "assistant", "content": svg}
    if getattr(tokenizer, "chat_template", None):
        try:
            pfx = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            full = tokenizer.apply_chat_template(msgs + [ans], tokenize=False, add_generation_prompt=False)
            return pfx, full
        except Exception:
            pass
    pfx = f"{SYSTEM_PROMPT}\n\nGenerate SVG for: {prompt}\nSVG:\n"
    return pfx, pfx + svg


class PPLDataset(Dataset):
    def __init__(self, records, tokenizer, max_len):
        self.samples = []
        skip = 0
        for r in records:
            item = normalize(r)
            if not item:
                continue
            pfx, full = build_chat(tokenizer, item["prompt"], item["svg"])
            f_enc = tokenizer(full, truncation=True, max_length=max_len, padding=False)
            p_enc = tokenizer(pfx, truncation=True, max_length=max_len, padding=False)
            ids = f_enc["input_ids"]
            labels = list(ids)
            pl = min(len(p_enc["input_ids"]), len(labels))
            labels[:pl] = [-100] * pl
            tgt = sum(l != -100 for l in labels)
            if tgt > 0:
                self.samples.append({
                    "input_ids": ids,
                    "attention_mask": f_enc["attention_mask"],
                    "labels": labels,
                    "target_tokens": tgt,
                })
            else:
                skip += 1
        if skip:
            log(f"  Skipped {skip}/{skip + len(self.samples)} records (0 target tokens)")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, i):
        return self.samples[i]


class Collator:
    def __init__(self, pad_id):
        self.pad = pad_id

    def __call__(self, batch):
        ml = max(len(s["input_ids"]) for s in batch)
        def p(v, pv):
            return v + [pv] * (ml - len(v))
        return {
            "input_ids": torch.tensor([p(s["input_ids"], self.pad) for s in batch]),
            "attention_mask": torch.tensor([p(s["attention_mask"], 0) for s in batch]),
            "labels": torch.tensor([p(s["labels"], -100) for s in batch]),
            "target_tokens": torch.tensor([s["target_tokens"] for s in batch]),
        }


@torch.inference_mode()
def compute_ppl(name, records, model, tokenizer):
    ds = PPLDataset(records, tokenizer, MAX_SEQ_LEN)
    if not ds:
        return {"dataset": name, "records": 0, "tokens": 0, "nll": 0, "ppl": 1.0, "nan": 0}

    pad = tokenizer.pad_token_id or tokenizer.eos_token_id or 0
    loader = DataLoader(ds, batch_size=BATCH_SIZE, collate_fn=Collator(pad))
    dev = next(model.parameters()).device
    vocab = tokenizer.vocab_size or 151643

    total_loss = total_tok = nan_n = 0

    for batch in tqdm(loader, desc=f"PPL {name}"):
        tgt = int(batch.pop("target_tokens").sum().item())
        labels = batch.pop("labels").to(dev)
        batch = {k: v.to(dev) for k, v in batch.items()}
        logits = model(**batch).logits
        if logits.shape[-1] > vocab:
            logits = logits[:, :, :vocab]
        sl = logits[:, :-1, :].contiguous()
        slb = labels[:, 1:].contiguous()
        loss = torch.nn.functional.cross_entropy(
            sl.view(-1, sl.size(-1)), slb.view(-1), ignore_index=-100, reduction="sum")
        v = float(loss.item())
        if math.isnan(v) or math.isinf(v):
            if nan_n == 0:
                log(f"  [Debug] NaN batch! Logits min={logits.nan_to_num().min().item():.2f}, max={logits.nan_to_num().max().item():.2f}, has_nan={torch.isnan(logits).any().item()}")
            nan_n += 1
            continue
        total_loss += v
        total_tok += tgt

    nll = total_loss / max(total_tok, 1)
    ppl = math.exp(nll) if nll < 50 else float("inf")
    if nan_n:
        log(f"  {nan_n} NaN batches skipped")
    return {"dataset": name, "records": len(ds), "tokens": total_tok,
            "nll": round(nll, 4), "ppl": round(ppl, 3), "nan": nan_n}


# ── 4. ASSESSMENT ────────────────────────────────────────────────────

def assess(tr, ev, total):
    signals, risks, good = [], [], []
    tp, ep = tr["ppl"], ev["ppl"]
    if tp > 0 and ep > 0 and tp < float("inf") and ep < float("inf"):
        ratio = ep / tp
        if ratio > 2.0:
            signals.append(f"Eval PPL {ratio:.1f}x train — likely overfitting")
        elif ratio > 1.5:
            risks.append(f"Eval PPL {ratio:.1f}x train — borderline")
        else:
            good.append(f"Eval/train PPL ratio healthy ({ratio:.2f}x)")
    if total < 100:
        risks.append(f"Very small dataset ({total})")
    elif total < 500:
        risks.append(f"Small dataset ({total})")
    else:
        good.append(f"Dataset size OK ({total})")
    verdict = "likely_overfitting" if signals else ("some_risk" if risks else "looks_good")
    return {"verdict": verdict, "signals": signals, "risks": risks, "good": good}


# ── 5. REPORT ────────────────────────────────────────────────────────

def write_report(out, tr, ev, asmt, total):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = {"model": OMNISVG_MODEL, "base": OMNISVG_BASE, "datasets": OMNISVG_HF_DATASETS,
              "total": total, "train": tr, "eval": ev, "assessment": asmt}
    jp = out / "report.json"
    jp.write_text(json.dumps(report, indent=2))
    md = [
        "# SVG Perplexity — OmniSVG (Real Weights)\n",
        f"**Model:** `{OMNISVG_MODEL}` (base: `{OMNISVG_BASE}`)\n",
        f"**Datasets:** {', '.join(OMNISVG_HF_DATASETS)}  |  **Total:** {total}\n",
        "", "| Split | Records | Tokens | NLL | PPL |",
        "|-------|---------|--------|-----|-----|",
        f"| Train | {tr['records']} | {tr['tokens']} | {tr['nll']} | {tr['ppl']} |",
        f"| Eval  | {ev['records']} | {ev['tokens']} | {ev['nll']} | {ev['ppl']} |",
        "", f"## Verdict: `{asmt['verdict']}`\n",
    ]
    for s in asmt["signals"]:
        md.append(f"- 🔴 {s}")
    for r in asmt["risks"]:
        md.append(f"- 🟡 {r}")
    for g in asmt["good"]:
        md.append(f"- 🟢 {g}")
    mp = out / "report.md"
    mp.write_text("\n".join(md))
    return jp, mp


# ── MAIN ─────────────────────────────────────────────────────────────

def main():
    ensure_deps()

    log(f"\n{'='*60}\nStep 1/4: Loading OmniSVG datasets\n{'='*60}")
    records = load_data(MAX_ROWS, OMNISVG_HF_DATASETS)
    assert len(records) >= 2, f"Need >=2 records, got {len(records)}"
    train_rec, eval_rec = split_data(records, EVAL_FRAC)
    log(f"Total: {len(records)} → {len(train_rec)} train, {len(eval_rec)} eval")
    del records
    gc.collect()

    log(f"\n{'='*60}\nStep 2/4: Loading OmniSVG model (real weights, 4-bit)\n{'='*60}")
    model, tokenizer = load_omnisvg_model()

    log(f"\n{'='*60}\nStep 3/4: Computing perplexity\n{'='*60}")
    tr = compute_ppl("train", train_rec, model, tokenizer)
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    ev = compute_ppl("eval", eval_rec, model, tokenizer)
    torch.cuda.empty_cache() if torch.cuda.is_available() else None

    total = len(train_rec) + len(eval_rec)
    asmt = assess(tr, ev, total)

    log(f"\n{'='*60}\nStep 4/4: Results\n{'='*60}")
    log(f"{'Split':<8} {'Records':<10} {'Tokens':<10} {'NLL':<10} {'PPL'}")
    log(f"{'train':<8} {tr['records']:<10} {tr['tokens']:<10} {tr['nll']:<10} {tr['ppl']}")
    log(f"{'eval':<8} {ev['records']:<10} {ev['tokens']:<10} {ev['nll']:<10} {ev['ppl']}")
    log(f"\nVerdict: {asmt['verdict']}")
    for x in asmt["signals"]: log(f"  🔴 {x}")
    for x in asmt["risks"]:   log(f"  🟡 {x}")
    for x in asmt["good"]:    log(f"  🟢 {x}")

    jp, mp = write_report(OUTPUT_DIR, tr, ev, asmt, total)
    log(f"\nWrote: {jp}\nWrote: {mp}\nDone!")


if __name__ == "__main__":
    main()
