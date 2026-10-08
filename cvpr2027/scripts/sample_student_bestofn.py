"""Best-of-n sampling from a trained PLAN+PATCH student (GPU host): one greedy answer plus n samples per task.

Loads the base model in NF4 (as in training) with the saved LoRA adapter, uses the dataset manifest's system
prompt and each row's input exactly as in training, and writes one JSON line per task:
{id, split, source, greedy, samples: [...]}. Selection, anchoring and scoring happen offline
(best_of_n_select.py) with the target-free verifier and the geometry scorer.

  python sample_student_bestofn.py --data DATA_DIR --adapter ADAPTER_DIR --out OUT.jsonl --n 10
"""
import argparse
import json
import time
from pathlib import Path

REVISION = "488639f1ff808d1d3d0ba301aef8c11461451ec5"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--adapter", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--splits", default="test,validation")
    p.add_argument("--n", type=int, default=10)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--batch", type=int, default=6)
    p.add_argument("--max-new-tokens", type=int, default=1024)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--no-quant", action="store_true", help="bf16 base instead of NF4 (GRPO adapters)")
    a = p.parse_args()
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    torch.backends.cuda.enable_cudnn_sdp(False)  # H100 cuDNN SDPA produced NaNs in earlier runs on this host
    manifest = json.loads((a.data / "manifest.json").read_text())
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
                               bnb_4bit_compute_dtype=torch.bfloat16)
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-3B-Instruct", revision=REVISION)
    tokenizer.pad_token, tokenizer.padding_side = tokenizer.eos_token, "left"
    base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-3B-Instruct", revision=REVISION,
                                                torch_dtype=torch.bfloat16, quantization_config=None if a.no_quant else quant,
                                                device_map={"": 0}, attn_implementation="sdpa")
    model = PeftModel.from_pretrained(base, str(a.adapter)).eval()
    done = {json.loads(l)["id"] for l in a.out.read_text().splitlines()} if a.out.exists() else set()
    rows = [dict(r, split=s) for s in a.splits.split(",") for r in map(json.loads, (a.data / f"{s}.jsonl").read_text().splitlines())
            if r["id"] not in done]
    prompt = lambda r: tokenizer.apply_chat_template([dict(role="system", content=manifest["system"]),  # noqa: E731
                                                      dict(role="user", content=r["input"])],
                                                     tokenize=False, add_generation_prompt=True)
    started = time.perf_counter()
    with a.out.open("a") as handle:
        for start in range(0, len(rows), a.batch):
            batch = rows[start:start + a.batch]
            inputs = tokenizer([prompt(r) for r in batch], add_special_tokens=False, padding=True,
                               return_tensors="pt").to("cuda")
            width = inputs.input_ids.shape[1]
            with torch.inference_mode():
                greedy = model.generate(**inputs, max_new_tokens=a.max_new_tokens, do_sample=False,
                                        pad_token_id=tokenizer.pad_token_id)[:, width:]
                torch.manual_seed(a.seed + start)
                drawn = greedy[:0] if a.n == 0 else model.generate(**inputs, max_new_tokens=a.max_new_tokens, do_sample=True,
                                       temperature=a.temperature, top_p=a.top_p, num_return_sequences=a.n,
                                       pad_token_id=tokenizer.pad_token_id)[:, width:]
            greedy_text = tokenizer.batch_decode(greedy, skip_special_tokens=True)
            drawn_text = tokenizer.batch_decode(drawn, skip_special_tokens=True) if a.n else []
            for k, r in enumerate(batch):
                handle.write(json.dumps(dict(id=r["id"], split=r["split"], source=r["source"], greedy=greedy_text[k],
                                             samples=drawn_text[k * a.n:(k + 1) * a.n])) + "\n")
            handle.flush()
            print(f"{start + len(batch)}/{len(rows)} {time.perf_counter() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
