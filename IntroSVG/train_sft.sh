#!/usr/bin/env bash
# IntroSVG — SFT training via LLaMA-Factory (official approach)
# =============================================================
# Prerequisites:
#   pip install llamafactory
#   # Data must already be built:
#   python 01_standardize_data.py
#   python 02_build_sft_data.py
#
# The dataset_info.json and d_sft.jsonl produced by step 2 are consumed here.
# LLaMA-Factory reads images from data/images/ referenced in d_sft.jsonl.
#
# Hardware: 8 × A100/A800 80 GB (matches paper §5.4)
# For fewer GPUs: reduce --num_processes and increase --gradient_accumulation_steps
#   so effective batch = per_device_batch × grad_accum × num_gpus = 16

set -euo pipefail

NPROC=${NPROC:-1}
MODEL=${BASE_MODEL:-"Qwen/Qwen2.5-VL-7B-Instruct"}
DATA_DIR="data"
OUTPUT_DIR="checkpoints/m_sft"

# ── LLaMA-Factory SFT (full fine-tune, DeepSpeed ZeRO-3) ─────────────────────
torchrun --nproc_per_node="${NPROC}" \
  --master_port=29500 \
  $(python -c "import llamafactory; import os; print(os.path.join(os.path.dirname(llamafactory.__file__), 'train.py'))") \
  --model_name_or_path    "${MODEL}" \
  --dataset               d_sft \
  --dataset_dir           "${DATA_DIR}" \
  --template              qwen2_vl \
  --stage                 sft \
  --finetuning_type       lora \
  --lora_rank             64 \
  --lora_alpha            128 \
  --lora_target           all \
  --cutoff_len            4096 \
  --per_device_train_batch_size  1 \
  --gradient_accumulation_steps  128 \
  --lr_scheduler_type     cosine \
  --warmup_ratio          0.03 \
  --learning_rate         5e-5 \
  --num_train_epochs      3.0 \
  --bf16                  true \
  --deepspeed             ds_z3_config.json \
  --output_dir            "${OUTPUT_DIR}" \
  --save_steps            500 \
  --logging_steps         50 \
  --save_total_limit      3 \
  --report_to             none

echo "SFT complete → ${OUTPUT_DIR}"
