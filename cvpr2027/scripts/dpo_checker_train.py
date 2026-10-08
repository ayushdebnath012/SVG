"""GPU side of dpo_checker.py: DPO training of the Qwen checker (LoRA) and scoring of comparison prompts.

  train : TRL DPO on dpo-train-<tag>.jsonl (prompt, chosen, rejected), evaluated on dpo-dev-pairs-<tag>.jsonl
  train-letter : the same DPO objective written for single-token answers. With completions "A"/"B" after one prompt,
          log pi(c|x) - log pi(r|x) is the logit difference at the last prompt position (normalisation cancels), so
          loss = -log sigmoid(beta * ((z_c - z_r) - (zref_c - zref_r))) needs one forward pass per example and only two
          logits; the reference differences are precomputed with the LoRA adapter disabled. This fits a 16 GB T4.
  score : P(answer = B) for every comparison prompt, with the trained adapter or the untrained base (--adapter none)

Prompts are rendered with the model's chat template in non-thinking mode; the answer is a single letter.
--dtype fp16 serves GPUs without bfloat16 (Kaggle T4); a forward pass is checked for finite logits before training
and on every scoring batch, so an fp16 overflow stops the run instead of producing silent garbage.
"""
import argparse
import json
from pathlib import Path

import torch


def render(tok, messages):
    return tok.apply_chat_template(messages, add_generation_prompt=True, tokenize=False, enable_thinking=False)


DTYPES = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}


def finite_check(model, tok, text):
    enc = tok([text], return_tensors="pt", add_special_tokens=False).to(model.device)
    with torch.inference_mode():
        logits = model(**enc).logits[:, -1, :].float()
    if not torch.isfinite(logits).all():
        raise FloatingPointError("non-finite logits in a forward pass; use another dtype")


def load_rows(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def train(a):
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import DPOConfig, DPOTrainer
    tok = AutoTokenizer.from_pretrained(a.model)
    tok.pad_token = tok.pad_token or tok.eos_token

    def ds(path):
        rows = load_rows(path)
        return Dataset.from_list([dict(prompt=render(tok, r["prompt"]), chosen=r["chosen"], rejected=r["rejected"]) for r in rows])
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=DTYPES[a.dtype], device_map={"": 0}, attn_implementation="sdpa")
    finite_check(model, tok, render(tok, load_rows(a.train)[0]["prompt"]))
    cfg = DPOConfig(output_dir=a.out, beta=a.beta, learning_rate=a.lr, num_train_epochs=a.epochs,
                    per_device_train_batch_size=a.micro_batch, gradient_accumulation_steps=16 // a.micro_batch,
                    per_device_eval_batch_size=a.micro_batch, max_length=a.max_length, bf16=a.dtype == "bf16",
                    fp16=a.dtype == "fp16", max_grad_norm=1.0,
                    gradient_checkpointing=True, logging_steps=5, eval_strategy="epoch", save_strategy="no",
                    lr_scheduler_type="cosine", warmup_steps=3, seed=17, report_to=[])
    peft = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules="all-linear", task_type="CAUSAL_LM")
    trainer = DPOTrainer(model=model, args=cfg, train_dataset=ds(a.train), eval_dataset=ds(a.dev), processing_class=tok,
                         peft_config=peft)
    trainer.train()
    trainer.model.save_pretrained(Path(a.out) / "adapter")
    Path(a.out, "log_history.json").write_text(json.dumps(trainer.state.log_history, indent=1))


def letter_logits(model, tok, texts, ids):
    enc = tok(texts, return_tensors="pt", padding=True, add_special_tokens=False).to(model.device)
    return model(**enc, logits_to_keep=1).logits[:, -1, ids].float()  # [batch, 2]: logits of "A" and "B"


def train_letter(a):
    import math
    import random
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)
    tok.pad_token = tok.pad_token or tok.eos_token
    tok.padding_side = "left"
    ids = [tok.encode(x, add_special_tokens=False)[0] for x in ("A", "B")]
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=DTYPES[a.dtype], device_map={"": 0}, attn_implementation="sdpa")
    finite_check(model, tok, render(tok, load_rows(a.train)[0]["prompt"]))
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules="all-linear", task_type="CAUSAL_LM"))

    def prep(path, limit=None):
        rows = load_rows(path)[:limit] if limit else load_rows(path)
        out = []
        for r in rows:
            text = render(tok, r["prompt"])
            n = len(tok.encode(text, add_special_tokens=False))
            if n <= a.max_length:  # longer prompts are skipped rather than truncated (the answer comes last)
                out.append(dict(text=text, c=0 if r["chosen"] == "A" else 1))
        return out
    train_rows, dev_rows = prep(a.train, a.limit), prep(a.dev, a.limit)
    model.eval()
    with torch.no_grad(), model.disable_adapter():  # reference = the frozen base model
        for rows in (train_rows, dev_rows):
            for r in rows:
                z = letter_logits(model, tok, [r["text"]], ids)[0]
                r["ref"] = float(z[r["c"]] - z[1 - r["c"]])
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)
    accum = 16
    steps = max(1, math.ceil(len(train_rows) * a.epochs / accum))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 3) * 0.5 * (1 + math.cos(math.pi * min(s, steps) / steps)))
    scaler = torch.amp.GradScaler("cuda", enabled=a.dtype == "fp16")
    log, rng, step = [], random.Random(17), 0

    def evaluate():
        model.eval(); losses, wins = [], 0
        with torch.no_grad():
            for r in dev_rows:
                z = letter_logits(model, tok, [r["text"]], ids)[0]
                m = a.beta * (float(z[r["c"]] - z[1 - r["c"]]) - r["ref"])
                losses.append(-math.log(1 / (1 + math.exp(-m)) + 1e-12)); wins += float(z[r["c"]] > z[1 - r["c"]])
        model.train()
        return dict(eval_loss=sum(losses) / max(1, len(losses)), eval_accuracy=wins / max(1, len(dev_rows)))
    model.train()
    order = [i for _ in range(math.ceil(a.epochs)) for i in rng.sample(range(len(train_rows)), len(train_rows))][:steps * accum]
    run_loss = 0.0
    for k, i in enumerate(order):
        r = train_rows[i]
        with torch.autocast("cuda", dtype=DTYPES[a.dtype], enabled=a.dtype != "fp32"):
            z = letter_logits(model, tok, [r["text"]], ids)[0]
        margin = a.beta * ((z[r["c"]] - z[1 - r["c"]]) - r["ref"])
        loss = torch.nn.functional.softplus(-margin) / accum  # -log sigmoid(margin)
        if not torch.isfinite(loss):
            raise FloatingPointError("non-finite DPO loss; use another dtype")
        scaler.scale(loss).backward(); run_loss += float(loss) * accum
        if (k + 1) % accum == 0:
            scaler.unscale_(opt); torch.nn.utils.clip_grad_norm_(params, 1.0)
            scaler.step(opt); scaler.update(); opt.zero_grad(set_to_none=True); sched.step(); step += 1
            log.append(dict(step=step, loss=run_loss / accum, lr=sched.get_last_lr()[0])); run_loss = 0.0
            print(json.dumps(log[-1]), flush=True)
    log.append(dict(step=step, **evaluate())); print(json.dumps(log[-1]), flush=True)
    model.save_pretrained(Path(a.out) / "adapter")
    Path(a.out, "log_history.json").write_text(json.dumps(log, indent=1))


@torch.inference_mode()
def score(a):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)
    tok.pad_token = tok.pad_token or tok.eos_token
    tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=DTYPES[a.dtype], device_map={"": 0}, attn_implementation="sdpa")
    if a.adapter != "none":
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, a.adapter)
    model.eval()
    ids = [tok.encode(x, add_special_tokens=False) for x in ("A", "B")]
    assert all(len(i) == 1 for i in ids), ids
    ta, tb = ids[0][0], ids[1][0]
    rows = load_rows(a.input)
    with open(a.output, "w") as out:
        for s in range(0, len(rows), a.batch):
            batch = rows[s:s + a.batch]
            enc = tok([render(tok, r["prompt"]) for r in batch], return_tensors="pt", padding=True, add_special_tokens=False).to(0)
            logits = model(**enc, logits_to_keep=1).logits[:, -1, :].float()
            if not torch.isfinite(logits[:, [ta, tb]]).all():
                raise FloatingPointError("non-finite answer logits while scoring; use another dtype")
            p_b = torch.softmax(logits[:, [ta, tb]], dim=-1)[:, 1].tolist()
            for r, p in zip(batch, p_b):
                r = {k: v for k, v in r.items() if k != "prompt"}
                out.write(json.dumps(dict(r, p_b=p)) + "\n")
            print("SCORED", s + len(batch), "/", len(rows), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("cmd", choices=("train", "train-letter", "score"))
    p.add_argument("--model", default="Qwen/Qwen3.5-9B")
    p.add_argument("--train"); p.add_argument("--dev"); p.add_argument("--out")
    p.add_argument("--beta", type=float, default=0.1); p.add_argument("--lr", type=float, default=2e-5)
    p.add_argument("--epochs", type=float, default=2)
    p.add_argument("--adapter", default="none"); p.add_argument("--input"); p.add_argument("--output")
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--dtype", choices=tuple(DTYPES), default="bf16")
    p.add_argument("--max-length", type=int, default=6144)
    p.add_argument("--micro-batch", type=int, default=2, help="per-device batch; accumulation keeps 16 examples per step")
    p.add_argument("--limit", type=int, help="train-letter smoke test on the first N examples")
    a = p.parse_args()
    {"train": train, "train-letter": train_letter, "score": score}[a.cmd](a)


if __name__ == "__main__":
    main()
