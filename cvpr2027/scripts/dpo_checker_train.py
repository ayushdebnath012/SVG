"""GPU side of dpo_checker.py: DPO training of the Qwen checker (LoRA) and scoring of comparison prompts.

  train : TRL DPO on dpo-train-<tag>.jsonl (prompt, chosen, rejected), evaluated on dpo-dev-pairs-<tag>.jsonl
  score : P(answer = B) for every comparison prompt, with the trained adapter or the untrained base (--adapter none)

Prompts are rendered with the model's chat template in non-thinking mode; the answer is a single letter.
"""
import argparse
import json
from pathlib import Path

import torch


def render(tok, messages):
    return tok.apply_chat_template(messages, add_generation_prompt=True, tokenize=False, enable_thinking=False)


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
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, device_map={"": 0}, attn_implementation="sdpa")
    cfg = DPOConfig(output_dir=a.out, beta=a.beta, learning_rate=a.lr, num_train_epochs=a.epochs, per_device_train_batch_size=2,
                    gradient_accumulation_steps=8, per_device_eval_batch_size=2, max_length=6144, bf16=True,
                    gradient_checkpointing=True, logging_steps=5, eval_strategy="epoch", save_strategy="no",
                    lr_scheduler_type="cosine", warmup_steps=3, seed=17, report_to=[])
    peft = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules="all-linear", task_type="CAUSAL_LM")
    trainer = DPOTrainer(model=model, args=cfg, train_dataset=ds(a.train), eval_dataset=ds(a.dev), processing_class=tok,
                         peft_config=peft)
    trainer.train()
    trainer.model.save_pretrained(Path(a.out) / "adapter")
    Path(a.out, "log_history.json").write_text(json.dumps(trainer.state.log_history, indent=1))


@torch.inference_mode()
def score(a):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)
    tok.pad_token = tok.pad_token or tok.eos_token
    tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, device_map={"": 0}, attn_implementation="sdpa")
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
            logits = model(**enc).logits[:, -1, :].float()
            p_b = torch.softmax(logits[:, [ta, tb]], dim=-1)[:, 1].tolist()
            for r, p in zip(batch, p_b):
                r = {k: v for k, v in r.items() if k != "prompt"}
                out.write(json.dumps(dict(r, p_b=p)) + "\n")
            print("SCORED", s + len(batch), "/", len(rows), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("cmd", choices=("train", "score"))
    p.add_argument("--model", default="Qwen/Qwen3.5-9B")
    p.add_argument("--train"); p.add_argument("--dev"); p.add_argument("--out")
    p.add_argument("--beta", type=float, default=0.1); p.add_argument("--lr", type=float, default=2e-5)
    p.add_argument("--epochs", type=float, default=2)
    p.add_argument("--adapter", default="none"); p.add_argument("--input"); p.add_argument("--output")
    p.add_argument("--batch", type=int, default=8)
    a = p.parse_args()
    train(a) if a.cmd == "train" else score(a)


if __name__ == "__main__":
    main()
