"""Greedy replies for multi-turn conversations with a trained PLAN+PATCH student (GPU host; ReAct repair rounds).

Input JSONL rows: {"id", "messages": [{"role", "content"}, ...]} ending with a user turn. Output JSONL rows:
{"id", "reply"}. Same NF4 base + LoRA adapter loading as sample_student_bestofn.py.

  python generate_conversations.py --adapter ADAPTER --inp CONVS.jsonl --out REPLIES.jsonl
"""
import argparse
import json
import time
from pathlib import Path

REVISION = "488639f1ff808d1d3d0ba301aef8c11461451ec5"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--adapter", type=Path, required=True)
    p.add_argument("--inp", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--batch", type=int, default=12)
    p.add_argument("--max-new-tokens", type=int, default=1024)
    a = p.parse_args()
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    torch.backends.cuda.enable_cudnn_sdp(False)
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
                               bnb_4bit_compute_dtype=torch.bfloat16)
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-3B-Instruct", revision=REVISION)
    tokenizer.pad_token, tokenizer.padding_side = tokenizer.eos_token, "left"
    base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-3B-Instruct", revision=REVISION, torch_dtype=torch.bfloat16,
                                                quantization_config=quant, device_map={"": 0}, attn_implementation="sdpa")
    model = PeftModel.from_pretrained(base, str(a.adapter)).eval()
    rows = [json.loads(l) for l in a.inp.read_text().splitlines()]
    started, out = time.perf_counter(), []
    for start in range(0, len(rows), a.batch):
        batch = rows[start:start + a.batch]
        prompts = [tokenizer.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=True) for r in batch]
        inputs = tokenizer(prompts, add_special_tokens=False, padding=True, return_tensors="pt").to("cuda")
        with torch.inference_mode():
            generated = model.generate(**inputs, max_new_tokens=a.max_new_tokens, do_sample=False,
                                       pad_token_id=tokenizer.pad_token_id)[:, inputs.input_ids.shape[1]:]
        out += [dict(id=r["id"], reply=t) for r, t in zip(batch, tokenizer.batch_decode(generated, skip_special_tokens=True))]
        print(f"{len(out)}/{len(rows)} {time.perf_counter() - started:.0f}s", flush=True)
    a.out.write_text("".join(json.dumps(r) + "\n" for r in out))


if __name__ == "__main__":
    main()
