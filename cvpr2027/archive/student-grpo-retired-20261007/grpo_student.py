"""GRPO for the PLAN+PATCH CAD student with an objective geometry reward (training split only).

Policy: Qwen2.5-Coder-3B (bf16) + LoRA initialised from the trained plan student; a frozen copy of that adapter is
the KL reference. Each step samples --group answers for --prompts training tasks. Every answer is quote-anchored,
applied to the source program and executed by persistent CadQuery workers (grpo_reward_worker.py); the reward is
1.0 for strict agreement (volume IoU >= 0.99999) with the task's reference program, 0.2 * IoU for a valid but
different solid, 0.0 for a failed execution and -0.2 for an invalid patch. Advantages are group-normalised
(GRPO, Shao et al. 2024); the loss is the on-policy policy gradient plus beta * per-token KL (k3 estimator) to
the reference adapter. Validation and test tasks are never sampled or rewarded here.

  python grpo_student.py --data DATA --adapter INIT_ADAPTER --out RUN --cadq-python PY --steps 150
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import random
import subprocess
import threading
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from anchor_plan_patches import anchor  # noqa: E402
from cad_edit_contracts import apply  # noqa: E402
from cad_edit_verifier import extract  # noqa: E402

REVISION = "488639f1ff808d1d3d0ba301aef8c11461451ec5"
STRICT = 0.99999


class Workers:
    """Pool of persistent CadQuery processes; a request that exceeds the timeout kills and replaces its worker."""

    def __init__(self, python: str, n: int, timeout: float):
        self.python, self.timeout = python, timeout
        self.script = str(Path(__file__).resolve().parent / "grpo_reward_worker.py")
        self.free = [self._spawn() for _ in range(n)]
        self.lock = threading.Condition()

    def _spawn(self):
        return subprocess.Popen([self.python, "-u", self.script], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def ask(self, req: dict) -> dict:
        with self.lock:
            while not self.free:
                self.lock.wait()
            proc = self.free.pop()
        result = dict(executable=False, iou=None, error="timeout")
        try:
            proc.stdin.write(json.dumps(req) + "\n")
            proc.stdin.flush()
            box = {}
            reader = threading.Thread(target=lambda: box.setdefault("line", proc.stdout.readline()), daemon=True)
            reader.start()
            reader.join(self.timeout)
            if "line" in box and box["line"]:
                result = json.loads(box["line"])
            else:
                proc.kill()
                proc = self._spawn()
        except Exception as e:  # noqa: BLE001
            proc.kill()
            proc = self._spawn()
            result["error"] = type(e).__name__
        with self.lock:
            self.free.append(proc)
            self.lock.notify()
        return result


def reward_for(row: dict, text: str, workers: Workers, cache: dict) -> tuple[float, str]:
    try:
        plan, patch = extract(text)
        rebuilt = "PLAN:\n" + plan + "\nPATCH:\n" + json.dumps(patch)
        anchored, _ = anchor(row["code"], rebuilt)
        program = apply(row["code"], anchored, row["representation"])
    except Exception:  # noqa: BLE001
        return -0.2, "invalid"
    key = (row["id"], hashlib.sha256(program.encode()).hexdigest())
    if key not in cache:
        cache[key] = workers.ask(dict(task=row["id"], representation=row["representation"], reference=row["edited_code"],
                                      candidate=program))
    res = cache[key]
    if not res.get("executable"):
        return 0.0, "exec_fail"
    if res["iou"] >= STRICT:
        return 1.0, "strict"
    return 0.2 * res["iou"], "valid"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--adapter", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--cadq-python", required=True)
    p.add_argument("--steps", type=int, default=150)
    p.add_argument("--prompts", type=int, default=8)
    p.add_argument("--group", type=int, default=8)
    p.add_argument("--lr", type=float, default=5e-6)
    p.add_argument("--beta", type=float, default=0.04)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--max-new-tokens", type=int, default=768)
    p.add_argument("--micro", type=int, default=4)
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--seed", type=int, default=17)
    a = p.parse_args()
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.backends.cuda.enable_cudnn_sdp(False)
    random.seed(a.seed)
    torch.manual_seed(a.seed)
    a.out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((a.data / "manifest.json").read_text())
    rows = [json.loads(l) for l in (a.data / "train.jsonl").read_text().splitlines()]
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-3B-Instruct", revision=REVISION)
    tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-3B-Instruct", revision=REVISION, torch_dtype=torch.bfloat16,
                                                device_map={"": 0}, attn_implementation="sdpa")
    model = PeftModel.from_pretrained(base, str(a.adapter), adapter_name="policy", is_trainable=True)
    model.load_adapter(str(a.adapter), adapter_name="ref", is_trainable=False)
    model.set_adapter("policy")
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    params = [p_ for n, p_ in model.named_parameters() if p_.requires_grad and ".policy." in n]
    assert params, "no trainable policy parameters"
    optimizer = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)
    workers = Workers(a.cadq_python, a.workers, timeout=90)
    cache: dict = {}
    (a.out / "config.json").write_text(json.dumps(dict(vars(a), data=str(a.data), adapter=str(a.adapter), out=str(a.out),
                                                       train_rows=len(rows), trainable=sum(x.numel() for x in params),
                                                       reward="1 strict; 0.2*IoU valid; 0 exec fail; -0.2 invalid", sampling="BenchCAD/CAD-Editor alternating 1:1",
                                                       algorithm="on-policy GRPO, group-normalised advantages, k3 KL to frozen init"),
                                       indent=2, default=str) + "\n")
    # balanced sources: BenchCAD (492 rows) and CAD-Editor (2048) alternate, each shuffled; disclosed design choice
    bench = [i for i, r in enumerate(rows) if r["source"] == "BenchCAD"]
    editor = [i for i, r in enumerate(rows) if r["source"] != "BenchCAD"]
    random.shuffle(bench)
    random.shuffle(editor)
    order = [x for pair in zip(editor, bench * (len(editor) // len(bench) + 1)) for x in pair]
    prompt = lambda r: tokenizer.apply_chat_template([dict(role="system", content=manifest["system"]),  # noqa: E731
                                                      dict(role="user", content=r["input"])], tokenize=False,
                                                     add_generation_prompt=True)
    started = time.perf_counter()
    log = (a.out / "train.jsonl").open("w")
    for step in range(a.steps):
        batch = [rows[order[(step * a.prompts + k) % len(rows)]] for k in range(a.prompts)]
        tokenizer.padding_side = "left"
        enc = tokenizer([prompt(r) for r in batch], add_special_tokens=False, padding=True, return_tensors="pt").to("cuda")
        model.eval()
        with torch.inference_mode():
            gen = model.generate(**enc, do_sample=True, temperature=a.temperature, top_p=1.0, num_return_sequences=a.group,
                                 max_new_tokens=a.max_new_tokens, pad_token_id=tokenizer.pad_token_id)
        width = enc.input_ids.shape[1]
        texts = tokenizer.batch_decode(gen[:, width:], skip_special_tokens=True)
        owners = [batch[i // a.group] for i in range(len(texts))]
        with ThreadPoolExecutor(max_workers=a.workers) as pool:
            scored = list(pool.map(lambda ix: reward_for(owners[ix], texts[ix], workers, cache), range(len(texts))))
        rewards = torch.tensor([s[0] for s in scored], dtype=torch.float32).view(a.prompts, a.group)
        std = rewards.std(dim=1, unbiased=False, keepdim=True)
        adv = ((rewards - rewards.mean(dim=1, keepdim=True)) / (std + 1e-4)).view(-1)
        adv[(std.expand(-1, a.group).reshape(-1) < 1e-6)] = 0.0
        # completion mask: generated tokens up to and including the first EOS
        completion = gen[:, width:]
        is_eos = completion == tokenizer.eos_token_id
        first = torch.where(is_eos.any(1), is_eos.float().argmax(1), torch.full_like(is_eos[:, 0], completion.shape[1], dtype=torch.long))
        mask = (torch.arange(completion.shape[1], device=gen.device)[None, :] <= first[:, None]).float()
        attention = torch.cat([enc.attention_mask.repeat_interleave(a.group, 0), mask.long()], dim=1)
        active = [i for i in range(len(texts)) if adv[i] != 0]
        model.train()
        optimizer.zero_grad()
        stats = dict(kl=0.0, pg=0.0)
        for chunk in range(0, len(active), a.micro):
            idx = active[chunk:chunk + a.micro]
            ids, att, m_, ad = gen[idx], attention[idx], mask[idx], adv[idx].to(gen.device)
            pos = (att.cumsum(-1) - 1).clamp(min=0)  # left padding: match generation-time positions
            logits = model(input_ids=ids, attention_mask=att, position_ids=pos).logits[:, width - 1:-1].float()
            logp = torch.log_softmax(logits, -1).gather(-1, ids[:, width:, None]).squeeze(-1)
            with torch.no_grad():
                model.set_adapter("ref")
                ref_logits = model(input_ids=ids, attention_mask=att, position_ids=pos).logits[:, width - 1:-1].float()
                ref_logp = torch.log_softmax(ref_logits, -1).gather(-1, ids[:, width:, None]).squeeze(-1)
                model.set_adapter("policy")
            diff = ref_logp - logp
            kl = (torch.exp(diff) - diff - 1) * m_
            tokens = m_.sum(1).clamp(min=1)
            pg = -(ad[:, None] * logp * m_).sum(1) / tokens
            klm = kl.sum(1) / tokens
            loss = ((pg + a.beta * klm).sum()) / max(1, len(active))
            loss.backward()
            stats["kl"] += klm.detach().sum().item()
            stats["pg"] += pg.detach().sum().item()
        if active:
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            optimizer.step()
        kinds = [s[1] for s in scored]
        record = dict(step=step + 1, reward_mean=rewards.mean().item(), strict=kinds.count("strict") / len(kinds),
                      invalid=kinds.count("invalid") / len(kinds), exec_fail=kinds.count("exec_fail") / len(kinds),
                      active=len(active), groups_with_signal=int((std.view(-1) > 1e-6).sum().item()),
                      kl=stats["kl"] / max(1, len(active)), seconds=round(time.perf_counter() - started, 1))
        with (a.out / "samples.jsonl").open("a") as h:  # every sampled answer with its reward, for auditing
            for ix, (text, (r, kind)) in enumerate(zip(texts, scored)):
                h.write(json.dumps(dict(step=step + 1, task=owners[ix]["id"], source=owners[ix]["source"], reward=r,
                                        kind=kind, text=text)) + "\n")
        log.write(json.dumps(record) + "\n")
        log.flush()
        print(json.dumps(record), flush=True)
        if (step + 1) % 50 == 0 or step + 1 == a.steps:
            model.save_pretrained(str(a.out / f"adapter-step{step + 1}"), selected_adapters=["policy"])
    (a.out / "done.json").write_text(json.dumps(dict(steps=a.steps, seconds=time.perf_counter() - started)) + "\n")


if __name__ == "__main__":
    main()
