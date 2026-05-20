"""
IntroSVG — Step 3: SFT Capability Training  → M_SFT
=====================================================
Paper §4.1:
  Trains a unified VLM on D_SFT with two parallel NLL objectives:
    L_SFT-G  (generator + corrector, text-only)
    L_SFT-C  (critic, vision + text)

  Hyperparams (§5.4):
    Base model : Qwen/Qwen2.5-VL-7B-Instruct
    Optimizer  : AdamW, lr = 5e-5, cosine decay
    Epochs     : 3
    Hardware   : 8 × A100/A800 80 GB  (use DeepSpeed ZeRO-3)

RECOMMENDED — use train_sft.sh (LLaMA-Factory, matches official repo):
    bash train_sft.sh

Fallback — custom Accelerate loop (requires same JSONL format from step 2):
    accelerate launch \\
        --config_file deepspeed_zero3.json \\
        --num_processes 8 \\
        03_sft_train.py

    # Single GPU (testing):
    python 03_sft_train.py --per-device-batch 1 --grad-accum 32

Data format (from 02_build_sft_data.py):
  Text-only rows: {"messages": [{"role":"user","content":"..."}, {"role":"assistant","content":"..."}]}
  Vision rows:    same + {"images": ["images/000001.png"]}  with <image> in content
"""

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import torch
from PIL import Image

log = logging.getLogger("step3")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DATA_DIR  = Path("data")
D_SFT     = DATA_DIR / "d_sft.jsonl"
OUT_DIR   = Path("checkpoints/m_sft")

BASE_MODEL  = "Qwen/Qwen2.5-VL-7B-Instruct"
LR          = 5e-5
EPOCHS      = 3
MAX_SEQ_LEN = 4096


# ─────────────────────────────────────────────────────────────────────────────
# Dataset
# ─────────────────────────────────────────────────────────────────────────────

class SFTDataset(torch.utils.data.Dataset):
    """
    Loads d_sft.jsonl (LLaMA-Factory sharegpt format from 02_build_sft_data.py).
    Handles both text-only (generator/corrector) and vision (critic) rows.

    Vision rows have:
      - "images": ["images/000001.png"]  (relative to DATA_DIR)
      - first user content contains "<image>" placeholder
    """

    def __init__(self, jsonl_path: str, processor, max_len: int = MAX_SEQ_LEN,
                 data_dir: str = "data"):
        self.rows: List[dict] = []
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.rows.append(json.loads(line))
        self.processor = processor
        self.max_len   = max_len
        self.data_dir  = Path(data_dir)

    def __len__(self):
        return len(self.rows)

    def _load_images(self, image_paths: List[str]) -> List[Image.Image]:
        imgs = []
        for p in image_paths:
            full = self.data_dir / p
            imgs.append(Image.open(full).convert("RGB"))
        return imgs

    @staticmethod
    def _inject_image_tokens(content: str) -> List[dict]:
        """
        Split a string containing '<image>' into a list of text/image dicts
        for the Qwen2.5-VL processor.
        e.g. "<image>\nYou are..." → [{"type":"image"}, {"type":"text","text":"\nYou are..."}]
        """
        parts = content.split("<image>")
        result = []
        for i, part in enumerate(parts):
            if i > 0:
                result.append({"type": "image"})
            if part:
                result.append({"type": "text", "text": part})
        return result

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        row      = self.rows[idx]
        messages = row["messages"]
        img_paths: List[str] = row.get("images", [])

        # Split into prompt turns and assistant response
        prompt_msgs  = messages[:-1]
        response_msg = messages[-1]
        assert response_msg["role"] == "assistant"

        if img_paths:
            # Vision row: convert "<image>" in user content to list format
            pms = []
            for msg in prompt_msgs:
                content = msg["content"]
                if isinstance(content, str) and "<image>" in content:
                    content = self._inject_image_tokens(content)
                pms.append({"role": msg["role"], "content": content})

            images = self._load_images(img_paths)
            prompt_text = self.processor.apply_chat_template(
                pms, tokenize=False, add_generation_prompt=True,
            )
            prompt_enc = self.processor(
                text=[prompt_text], images=images,
                return_tensors="pt", padding=False,
            )
        else:
            # Text-only row
            prompt_text = self.processor.apply_chat_template(
                prompt_msgs, tokenize=False, add_generation_prompt=True,
            )
            prompt_enc = self.processor(
                text=[prompt_text], return_tensors="pt", padding=False,
            )

        # Encode assistant response
        resp_text = response_msg["content"] + self.processor.tokenizer.eos_token
        resp_ids  = self.processor.tokenizer.encode(
            resp_text, add_special_tokens=False, return_tensors="pt",
        )

        input_ids = torch.cat(
            [prompt_enc["input_ids"][0], resp_ids[0]], dim=0,
        )[:self.max_len]

        prompt_len = prompt_enc["input_ids"].shape[1]
        labels = input_ids.clone()
        labels[:prompt_len] = -100   # mask prompt tokens

        out = {
            "input_ids":      input_ids,
            "labels":         labels,
            "attention_mask": torch.ones_like(input_ids),
        }
        if "pixel_values" in prompt_enc:
            out["pixel_values"] = prompt_enc["pixel_values"][0]
            if "image_grid_thw" in prompt_enc:
                out["image_grid_thw"] = prompt_enc["image_grid_thw"][0]
        return out


def _collate_fn(batch: List[Dict[str, Any]], pad_id: int) -> Dict[str, Any]:
    """Pad a batch of variable-length sequences."""
    max_len = max(b["input_ids"].shape[0] for b in batch)

    input_ids = torch.full((len(batch), max_len), pad_id, dtype=torch.long)
    labels    = torch.full((len(batch), max_len), -100,   dtype=torch.long)
    attn_mask = torch.zeros(len(batch), max_len,           dtype=torch.long)

    has_vision = any("pixel_values" in b for b in batch)
    pv_list, thw_list = [], []

    for i, b in enumerate(batch):
        n = b["input_ids"].shape[0]
        input_ids[i, :n] = b["input_ids"]
        labels[i,    :n] = b["labels"]
        attn_mask[i, :n] = b["attention_mask"]
        if "pixel_values" in b:
            pv_list.append(b["pixel_values"])
            if "image_grid_thw" in b:
                thw_list.append(b["image_grid_thw"])

    out = {"input_ids": input_ids, "labels": labels, "attention_mask": attn_mask}
    if pv_list:
        out["pixel_values"]    = torch.cat(pv_list, dim=0)
    if thw_list:
        out["image_grid_thw"]  = torch.cat(thw_list, dim=0)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Training loop
# ─────────────────────────────────────────────────────────────────────────────

def main(args):
    from transformers import (
        Qwen2_5_VLForConditionalGeneration,
        AutoProcessor,
        get_cosine_schedule_with_warmup,
    )
    from torch.utils.data import DataLoader
    from torch.optim import AdamW

    # ── Accelerate ────────────────────────────────────────────────────────────
    from accelerate import Accelerator
    accelerator = Accelerator(gradient_accumulation_steps=args.grad_accum)
    device = accelerator.device
    is_main = accelerator.is_main_process

    if is_main:
        log.info(f"SFT training  |  {accelerator.num_processes} GPU(s)")
        log.info(f"  base model : {args.base_model}")
        log.info(f"  data       : {args.data}")
        log.info(f"  output     : {args.output}")

    # ── Model + Processor ─────────────────────────────────────────────────────
    processor = AutoProcessor.from_pretrained(args.base_model)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.base_model,
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",  # remove if FA2 not installed
    )
    model.gradient_checkpointing_enable()

    # ── Dataset + DataLoader ──────────────────────────────────────────────────
    pad_id  = processor.tokenizer.pad_token_id or processor.tokenizer.eos_token_id
    dataset = SFTDataset(args.data, processor, max_len=args.max_seq_len,
                         data_dir=str(Path(args.data).parent))
    loader  = DataLoader(
        dataset,
        batch_size=args.per_device_batch,
        shuffle=True,
        num_workers=4,
        pin_memory=True,
        collate_fn=lambda b: _collate_fn(b, pad_id),
    )

    # ── Optimizer + Scheduler ─────────────────────────────────────────────────
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps   = len(loader) * args.epochs // args.grad_accum
    warmup_steps  = int(0.03 * total_steps)
    scheduler = get_cosine_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )

    # ── Accelerate prepare ────────────────────────────────────────────────────
    model, optimizer, loader, scheduler = accelerator.prepare(
        model, optimizer, loader, scheduler
    )

    # ── Train ─────────────────────────────────────────────────────────────────
    global_step = 0
    for epoch in range(args.epochs):
        model.train()
        total_loss = 0.0

        for step, batch in enumerate(loader):
            with accelerator.accumulate(model):
                outputs = model(**batch)
                loss    = outputs.loss
                accelerator.backward(loss)

                if accelerator.sync_gradients:
                    accelerator.clip_grad_norm_(model.parameters(), 1.0)

                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

            if accelerator.sync_gradients:
                global_step += 1
                total_loss  += loss.item()
                if is_main and global_step % 50 == 0:
                    avg = total_loss / max(global_step, 1)
                    lr  = scheduler.get_last_lr()[0]
                    log.info(f"Epoch {epoch+1} step {global_step}  loss={avg:.4f}  lr={lr:.2e}")

        # ── Save checkpoint after each epoch ──────────────────────────────────
        if is_main:
            ckpt = Path(args.output) / f"epoch_{epoch+1}"
            accelerator.wait_for_everyone()
            unwrapped = accelerator.unwrap_model(model)
            unwrapped.save_pretrained(ckpt)
            processor.save_pretrained(ckpt)
            log.info(f"Saved checkpoint → {ckpt}")

    if is_main:
        log.info("SFT training complete → M_SFT saved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model",       default=BASE_MODEL)
    parser.add_argument("--data",             default=str(D_SFT))
    parser.add_argument("--output",           default=str(OUT_DIR))
    parser.add_argument("--lr",               type=float, default=LR)
    parser.add_argument("--epochs",           type=int,   default=EPOCHS)
    parser.add_argument("--per-device-batch", type=int,   default=2)
    parser.add_argument("--grad-accum",       type=int,   default=8)
    parser.add_argument("--max-seq-len",      type=int,   default=MAX_SEQ_LEN)
    args = parser.parse_args()
    main(args)
