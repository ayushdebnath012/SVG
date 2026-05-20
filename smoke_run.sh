#!/usr/bin/env bash
# Smoke Run — full pipeline in ~12–15 hours on 1 × A100 80 GB
# ============================================================
# Validates the entire pipeline end-to-end with reduced dataset sizes.
# NOT for production — use run_full_pipeline.sh for full quality training.
#
# Time budget (A100 80 GB):
#   Step 1  standardize      5 000 SVGs          ~45 min
#   Step 2  build SFT data     500 prompts        ~1.5 hrs
#   Step 3  SFT LoRA          1 epoch            ~1.5 hrs
#   Step 4  build DPO data    200 prompts        ~45 min
#   Step 5  DPO               1 epoch            ~30 min
#   Step 6  diffusion PNGs    300 prompts        ~15 min
#   Step 7  vectorize         300 SVGs           ~10 min
#   Step 8  GRPO              1 epoch            ~1.5 hrs
#   Model downloads (first run)                  ~2 hrs
#   ─────────────────────────────────────────────────────
#   Total                                        ~10–15 hrs
#
# Usage:
#   export OPENAI_API_KEY="sk-..."
#   bash smoke_run.sh

set -euo pipefail

PROMPTS_FILE="${1:-prompts.txt}"

echo "=========================================================="
echo "  SMOKE RUN — IntroSVG + DiffusionSVG"
echo "  Target: ~12-15 hrs on 1 × A100 80 GB"
echo "=========================================================="

# ── STAGE 1: IntroSVG ─────────────────────────────────────────────────────────

cd IntroSVG

# Step 1 — standardise 5 000 SVGs (stops early via --max-samples)
echo "[1/8] Standardising SVG data (capped at 5 000)..."
python 01_standardize_data.py \
    --max-samples 5000 \
    --workers 8

# Step 2 — build SFT data: 500 draft generations + GPT-4o critiques
echo "[2/8] Building SFT data (500 prompts)..."
python 02_build_sft_data.py \
    --n-prompts 500

# Step 3 — SFT LoRA, 1 epoch
echo "[3/8] SFT training (LoRA, 1 epoch)..."
llamafactory-cli train \
    --model_name_or_path    Qwen/Qwen2.5-VL-7B-Instruct \
    --dataset               d_sft \
    --dataset_dir           ./data \
    --template              qwen2_vl \
    --stage                 sft \
    --finetuning_type       lora \
    --lora_rank             64 \
    --lora_alpha            128 \
    --lora_target           all \
    --cutoff_len            2048 \
    --per_device_train_batch_size  1 \
    --gradient_accumulation_steps  16 \
    --lr_scheduler_type     cosine \
    --warmup_ratio          0.03 \
    --learning_rate         5e-5 \
    --num_train_epochs      1.0 \
    --bf16                  true \
    --output_dir            checkpoints/m_sft/epoch_1 \
    --save_steps            200 \
    --logging_steps         20 \
    --report_to             none

# Step 4 — build DPO data: 200 prompts, 2 candidates each
echo "[4/8] Building DPO data (200 prompts, 2 candidates)..."
python 04_build_dpo_data.py \
    --sft-ckpt checkpoints/m_sft/epoch_1 \
    --n-prompts 200 \
    --n-candidates 2

# Step 5 — DPO, 1 epoch
echo "[5/8] DPO training (1 epoch)..."
python 05_dpo_train.py \
    --sft-ckpt checkpoints/m_sft/epoch_1 \
    --epochs   1 \
    --per-device-batch 1 \
    --grad-accum 8

cd ..

# ── STAGE 2: DiffusionSVG ────────────────────────────────────────────────────

cd DiffusionSVG

# Step 6 — filter + generate 300 reference PNGs
echo "[6/8] Filtering complex prompts..."
python 00_filter_prompts.py \
    --input     "../${PROMPTS_FILE}" \
    --output    data/complex_prompts.jsonl \
    --min-score 2

echo "[7/8] Generating reference PNGs (300 prompts, SD-Turbo)..."
# Limit to first 300 rows
head -300 data/complex_prompts.jsonl > data/complex_prompts_smoke.jsonl
python 01_generate_pngs.py \
    --input  data/complex_prompts_smoke.jsonl \
    --output data/ref_pngs/

python 02_vectorize_svgs.py \
    --input   data/complex_prompts_with_ids.jsonl \
    --png-dir data/ref_pngs/ \
    --svg-dir data/ref_svgs/ \
    --workers 8

python 03_build_dataset.py

# Step 8 — GRPO, 1 epoch
echo "[8/8] GRPO training (1 epoch)..."
python 04_grpo_train.py \
    --model     "../IntroSVG/checkpoints/m_sft/epoch_1" \
    --data      data/grpo_train.jsonl \
    --output    checkpoints/grpo_svg_smoke \
    --epochs    1 \
    --n-samples 2 \
    --beta      0.04 \
    --grad-accum 4

cd ..

echo ""
echo "=========================================================="
echo "  SMOKE RUN COMPLETE"
echo "  Final model: DiffusionSVG/checkpoints/grpo_svg_smoke/epoch_1"
echo ""
echo "  Test inference:"
echo "    python IntroSVG/inference_loop.py \\"
echo "        --MODEL_NAME DiffusionSVG/checkpoints/grpo_svg_smoke/epoch_1 \\"
echo "        --CSV_FILE   prompts.csv \\"
echo "        --OUTPUT_DIR smoke_results/"
echo "=========================================================="
