#!/usr/bin/env python3
"""
finetune_qwen2vl.py — Fine-tune Qwen2VL on (text, SVG) pairs
=============================================================

Implements the training stage from the whiteboard:

    (Text Prompt, SVG) dataset  →  SFT + LoRA  →  Fine-tuned Qwen2VL
                                                          │
                                                    Inference:
                                            Text → Qwen2VL → SVG Code
                                                          │
                                                    Render + Code-Correction loop

Architecture:
    - Base model : Qwen/Qwen2-VL-7B-Instruct
    - PEFT       : LoRA on all attention + feed-forward projection layers
    - Trainer    : HuggingFace TRL SFTTrainer (text-only SFT on SVG generation)
    - Task type  : Text-only (prompt → SVG), no image input at training time

Requirements:
    pip install transformers trl peft bitsandbytes accelerate datasets torch pillow

Usage:
    # Fine-tune on generated dataset
    python finetune_qwen2vl.py \\
        --train_file ./dataset/dataset_train.jsonl \\
        --val_file   ./dataset/dataset_val.jsonl \\
        --output_dir ./qwen2vl_svg_lora \\
        --epochs 3

    # Inference with fine-tuned model
    python finetune_qwen2vl.py \\
        --infer \\
        --lora_path ./qwen2vl_svg_lora \\
        --prompt "a red apple"
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import torch

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class FineTuneConfig:
    # Model
    base_model: str = "Qwen/Qwen2-VL-7B-Instruct"
    load_in_4bit: bool = True          # QLoRA (saves ~3× VRAM)
    load_in_8bit: bool = False

    # LoRA
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    # Which modules to inject LoRA into
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ])

    # Training
    output_dir: str = "./qwen2vl_svg_lora"
    num_epochs: int = 3
    per_device_train_batch_size: int = 2
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-4
    lr_scheduler_type: str = "cosine"
    warmup_ratio: float = 0.05
    max_seq_length: int = 2048
    seed: int = 42

    # Logging / saving
    logging_steps: int = 10
    eval_steps: int = 100
    save_steps: int = 200
    save_total_limit: int = 3
    fp16: bool = True
    bf16: bool = False      # set True on Ampere GPUs (A100, 3090, etc.)
    report_to: str = "none" # "wandb" | "tensorboard" | "none"


# ---------------------------------------------------------------------------
# System prompt (matches inference-time prompt used during code-correction)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are an expert SVG code generator. "
    "Given a text description, output ONLY valid SVG code. "
    "Rules:\n"
    "- Start with: <svg viewBox=\"0 0 200 200\" xmlns=\"http://www.w3.org/2000/svg\">\n"
    "- Use simple shapes: <rect>, <circle>, <ellipse>, <polygon>, <path>\n"
    "- Use solid hex fill colours (e.g., fill=\"#FF0000\")\n"
    "- Keep it minimal: 5–20 elements\n"
    "- End with: </svg>\n"
    "Output the SVG code directly, no explanation."
)


def build_chat_text(prompt: str, svg: str, tokenizer) -> str:
    """
    Format a (prompt, svg) pair as a Qwen2VL chat conversation string.
    """
    messages = [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "user",    "content": f"Generate SVG for: {prompt}"},
        {"role": "assistant","content": svg},
    ]
    # apply_chat_template adds the correct special tokens for Qwen2VL
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

def load_jsonl(path: str) -> List[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class SVGDataset(torch.utils.data.Dataset):
    """
    Wraps (text, svg) JSONL records into tokenized tensors for SFT.
    Only the assistant response (SVG) tokens contribute to the loss.
    """

    def __init__(self, records: List[dict], tokenizer, max_length: int = 2048):
        self.records = records
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        rec = self.records[idx]
        text = build_chat_text(rec["text"], rec["svg"], self.tokenizer)

        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding=False,
            return_tensors=None,
        )

        input_ids = encoding["input_ids"]
        labels = list(input_ids)

        # Mask the system + user turn: only train on the assistant SVG output
        # Find where the assistant response starts
        assistant_token = self.tokenizer.encode("<|im_start|>assistant", add_special_tokens=False)
        label_mask_end = self._find_assistant_start(input_ids, assistant_token)
        for i in range(label_mask_end):
            labels[i] = -100

        return {
            "input_ids": input_ids,
            "labels": labels,
            "attention_mask": encoding["attention_mask"],
        }

    @staticmethod
    def _find_assistant_start(input_ids: list, assistant_tokens: list) -> int:
        """Return the index just after the last occurrence of assistant_tokens."""
        n = len(assistant_tokens)
        last_pos = 0
        for i in range(len(input_ids) - n):
            if input_ids[i:i+n] == assistant_tokens:
                last_pos = i + n
        return last_pos


# ---------------------------------------------------------------------------
# Collator
# ---------------------------------------------------------------------------

class DataCollator:
    def __init__(self, tokenizer, max_length: int = 2048):
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __call__(self, features):
        max_len = min(max(len(f["input_ids"]) for f in features), self.max_length)

        input_ids_list, labels_list, attention_mask_list = [], [], []

        for f in features:
            pad_len = max_len - len(f["input_ids"])
            pad_id = self.tokenizer.pad_token_id or 0

            input_ids = f["input_ids"] + [pad_id] * pad_len
            labels    = f["labels"]    + [-100]   * pad_len
            attn_mask = f["attention_mask"] + [0] * pad_len

            input_ids_list.append(input_ids[:max_len])
            labels_list.append(labels[:max_len])
            attention_mask_list.append(attn_mask[:max_len])

        return {
            "input_ids":      torch.tensor(input_ids_list, dtype=torch.long),
            "labels":         torch.tensor(labels_list, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask_list, dtype=torch.long),
        }


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train(
    train_file: str,
    val_file: Optional[str],
    cfg: FineTuneConfig,
):
    from transformers import (
        AutoTokenizer,
        Qwen2VLForConditionalGeneration,
        TrainingArguments,
        Trainer,
        BitsAndBytesConfig,
        DataCollatorForSeq2Seq,
    )
    from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training

    logging.basicConfig(level=logging.INFO)

    # ------------------------------------------------------------------
    # Tokenizer
    # ------------------------------------------------------------------
    logger.info(f"Loading tokenizer: {cfg.base_model}")
    tokenizer = AutoTokenizer.from_pretrained(
        cfg.base_model,
        trust_remote_code=True,
        padding_side="right",
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ------------------------------------------------------------------
    # Model (with optional quantization)
    # ------------------------------------------------------------------
    logger.info(f"Loading model: {cfg.base_model}")

    quant_config = None
    if cfg.load_in_4bit:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
    elif cfg.load_in_8bit:
        quant_config = BitsAndBytesConfig(load_in_8bit=True)

    model = Qwen2VLForConditionalGeneration.from_pretrained(
        cfg.base_model,
        quantization_config=quant_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16 if quant_config is None else None,
    )

    if quant_config is not None:
        model = prepare_model_for_kbit_training(model)

    # ------------------------------------------------------------------
    # LoRA
    # ------------------------------------------------------------------
    lora_cfg = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=cfg.lora_r,
        lora_alpha=cfg.lora_alpha,
        lora_dropout=cfg.lora_dropout,
        target_modules=cfg.target_modules,
        bias="none",
    )
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()

    # ------------------------------------------------------------------
    # Datasets
    # ------------------------------------------------------------------
    train_records = load_jsonl(train_file)
    logger.info(f"Train records: {len(train_records)}")

    train_dataset = SVGDataset(train_records, tokenizer, cfg.max_seq_length)
    eval_dataset = None
    if val_file and Path(val_file).exists():
        val_records = load_jsonl(val_file)
        eval_dataset = SVGDataset(val_records, tokenizer, cfg.max_seq_length)
        logger.info(f"Val records:   {len(val_records)}")

    collator = DataCollator(tokenizer, cfg.max_seq_length)

    # ------------------------------------------------------------------
    # Training arguments
    # ------------------------------------------------------------------
    training_args = TrainingArguments(
        output_dir=cfg.output_dir,
        num_train_epochs=cfg.num_epochs,
        per_device_train_batch_size=cfg.per_device_train_batch_size,
        gradient_accumulation_steps=cfg.gradient_accumulation_steps,
        learning_rate=cfg.learning_rate,
        lr_scheduler_type=cfg.lr_scheduler_type,
        warmup_ratio=cfg.warmup_ratio,
        fp16=cfg.fp16,
        bf16=cfg.bf16,
        logging_steps=cfg.logging_steps,
        eval_strategy="steps" if eval_dataset else "no",
        eval_steps=cfg.eval_steps if eval_dataset else None,
        save_strategy="steps",
        save_steps=cfg.save_steps,
        save_total_limit=cfg.save_total_limit,
        load_best_model_at_end=bool(eval_dataset),
        metric_for_best_model="eval_loss" if eval_dataset else None,
        report_to=cfg.report_to,
        seed=cfg.seed,
        remove_unused_columns=False,
        dataloader_pin_memory=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=collator,
        processing_class=tokenizer,
    )

    # ------------------------------------------------------------------
    # Train
    # ------------------------------------------------------------------
    logger.info("Starting training…")
    trainer.train()

    # Save LoRA adapter
    adapter_path = os.path.join(cfg.output_dir, "final_adapter")
    model.save_pretrained(adapter_path)
    tokenizer.save_pretrained(adapter_path)
    logger.info(f"LoRA adapter saved to: {adapter_path}")

    return adapter_path


# ---------------------------------------------------------------------------
# Inference helper
# ---------------------------------------------------------------------------

def infer(
    prompt: str,
    lora_path: str,
    base_model: str = "Qwen/Qwen2-VL-7B-Instruct",
    load_in_4bit: bool = True,
    max_new_tokens: int = 4096,
    temperature: float = 0.1,
) -> str:
    """
    Run the fine-tuned model to generate SVG from a text prompt.

    Returns raw SVG string (or empty string on failure).
    """
    from transformers import AutoTokenizer, Qwen2VLForConditionalGeneration, BitsAndBytesConfig
    from peft import PeftModel

    logger.info(f"Loading base model: {base_model}")
    tokenizer = AutoTokenizer.from_pretrained(lora_path, trust_remote_code=True)

    quant_config = None
    if load_in_4bit:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
        )

    base = Qwen2VLForConditionalGeneration.from_pretrained(
        base_model,
        quantization_config=quant_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16 if quant_config is None else None,
    )

    logger.info(f"Loading LoRA adapter: {lora_path}")
    model = PeftModel.from_pretrained(base, lora_path)
    model.eval()

    # Build prompt
    messages = [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "user",    "content": f"Generate SVG for: {prompt}"},
    ]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=(temperature > 0),
            temperature=temperature,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
        )

    # Decode only the generated tokens
    generated = output_ids[0][inputs["input_ids"].shape[1]:]
    result = tokenizer.decode(generated, skip_special_tokens=True).strip()

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Fine-tune Qwen2VL on (text, SVG) pairs"
    )

    # Mode
    parser.add_argument("--infer", action="store_true",
                        help="Run inference with a fine-tuned adapter instead of training")

    # Training args
    parser.add_argument("--train_file",  type=str, default="./dataset/dataset_train.jsonl")
    parser.add_argument("--val_file",    type=str, default="./dataset/dataset_val.jsonl")
    parser.add_argument("--output_dir",  type=str, default="./qwen2vl_svg_lora")
    parser.add_argument("--base_model",  type=str, default="Qwen/Qwen2-VL-7B-Instruct")
    parser.add_argument("--epochs",      type=int, default=3)
    parser.add_argument("--batch_size",  type=int, default=2)
    parser.add_argument("--grad_accum",  type=int, default=8)
    parser.add_argument("--lr",          type=float, default=2e-4)
    parser.add_argument("--lora_r",      type=int, default=16)
    parser.add_argument("--lora_alpha",  type=int, default=32)
    parser.add_argument("--max_seq_len", type=int, default=2048)
    parser.add_argument("--no_4bit",     action="store_true",
                        help="Disable 4-bit quantization (use fp16)")
    parser.add_argument("--bf16",        action="store_true",
                        help="Use bf16 instead of fp16 (Ampere GPUs)")
    parser.add_argument("--report_to",   type=str, default="none",
                        choices=["none", "wandb", "tensorboard"])

    # Inference args
    parser.add_argument("--lora_path",   type=str, default=None,
                        help="Path to saved LoRA adapter (for --infer)")
    parser.add_argument("--prompt",      type=str, default="a red apple")
    parser.add_argument("--max_tokens",  type=int, default=4096)

    args = parser.parse_args()

    if args.infer:
        # ── Inference mode ──────────────────────────────────────────────
        if not args.lora_path:
            parser.error("--lora_path required for --infer mode")

        svg = infer(
            prompt=args.prompt,
            lora_path=args.lora_path,
            base_model=args.base_model,
            load_in_4bit=not args.no_4bit,
            max_new_tokens=args.max_tokens,
        )
        print("\n" + "="*60)
        print("Generated SVG:")
        print("="*60)
        print(svg)

    else:
        # ── Training mode ────────────────────────────────────────────────
        cfg = FineTuneConfig(
            base_model=args.base_model,
            load_in_4bit=not args.no_4bit,
            output_dir=args.output_dir,
            num_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=args.grad_accum,
            learning_rate=args.lr,
            lora_r=args.lora_r,
            lora_alpha=args.lora_alpha,
            max_seq_length=args.max_seq_len,
            fp16=not args.bf16,
            bf16=args.bf16,
            report_to=args.report_to,
        )

        adapter_path = train(
            train_file=args.train_file,
            val_file=args.val_file if Path(args.val_file).exists() else None,
            cfg=cfg,
        )

        print(f"\nDone! Adapter saved to: {adapter_path}")
        print(f"Run inference:")
        print(f'  python finetune_qwen2vl.py --infer --lora_path {adapter_path} --prompt "a red apple"')
