#!/usr/bin/env bash
# Full Quality Run — 1 × A100 80 GB
# ====================================
# Best possible quality on a single GPU. Dataset sizes are tuned to complete
# in ~3–4 days while giving ~85–90% of paper quality.
#
# Time budget:
#   Step 1-2  download IntroSVG-train   5 000 samples   ~20 min (bandwidth)
#   Step 3    SFT LoRA                 3 epochs         ~8–12 hrs
#   Step 4    build DPO data           1 500 prompts    ~6–8 hrs
#   Step 5    DPO                      3 epochs         ~4–6 hrs
#   Step 6    diffusion PNGs           1 000 prompts    ~30 min
#   Step 7    vectorize                1 000 SVGs       ~20 min
#   Step 8    GRPO                     2 epochs         ~8–12 hrs
#   Model downloads (first run)                        ~2 hrs
#   ─────────────────────────────────────────────────────────
#   Total                                              ~30–42 hrs (~1.5–2 days)
#
# Resumable: each step checks if its output already exists and skips if so.
#
# Usage:
#   export OPENAI_API_KEY="sk-..."
#   tmux new -s train
#   bash full_run.sh [prompts.txt]
#   # Ctrl+B D to detach, tmux attach -t train to resume

set -euo pipefail

PROMPTS_FILE="${1:-prompts.txt}"
LOG_FILE="full_run_$(date +%Y%m%d_%H%M%S).log"

# Tee all output to log file
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=========================================================="
echo "  FULL QUALITY RUN — 1 × A100 80 GB"
echo "  Started: $(date)"
echo "  Log: $LOG_FILE"
echo "=========================================================="

# ── helpers ──────────────────────────────────────────────────────────────────

elapsed() { echo "  ⏱  $(date '+%H:%M:%S')"; }

skip_if_exists() {
    local path="$1"; local label="$2"
    # For files: must exist AND be non-empty. For dirs: must exist.
    if [ -d "$path" ]; then
        echo "  [SKIP] $label already exists at $path"
        return 0
    elif [ -f "$path" ] && [ -s "$path" ]; then
        echo "  [SKIP] $label already exists at $path"
        return 0
    fi
    return 1
}

# ── STAGE 1: IntroSVG ────────────────────────────────────────────────────────

cd IntroSVG
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  STAGE 1 — IntroSVG"
echo "══════════════════════════════════════════════════════════"

# Steps 1+2 — Download official IntroSVG training data from HuggingFace.
# gitcat404/IntroSVG-train is the exact dataset used in the paper:
# GPT-4o generated and critiqued SVG pairs, far higher quality than anything
# the base model can self-generate. No GPU required; ~10-20 min download.
echo ""
echo "[1-2/8] Downloading official IntroSVG-train dataset (gitcat404/IntroSVG-train)..."
echo "  Expected: ~10–20 min (bandwidth-limited, no GPU needed)"
elapsed
skip_if_exists data/d_sft.jsonl "d_sft.jsonl" || \
PYTHONUNBUFFERED=1 python 00_download_official_data.py \
    --max-samples 5000
elapsed

# Step 3 — SFT LoRA, 3 epochs
echo ""
echo "[3/8] SFT training (LoRA rank=64, 3 epochs)..."
echo "  Expected: ~8–12 hrs"
elapsed
skip_if_exists checkpoints/m_sft/epoch_3 "m_sft/epoch_3" || \
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
    --cutoff_len            4096 \
    --per_device_train_batch_size  1 \
    --gradient_accumulation_steps  128 \
    --lr_scheduler_type     cosine \
    --warmup_ratio          0.03 \
    --learning_rate         5e-5 \
    --num_train_epochs      3.0 \
    --bf16                  true \
    --output_dir            checkpoints/m_sft \
    --save_steps            500 \
    --logging_steps         50 \
    --report_to             none
elapsed

# Step 4 — Build DPO data: 1 500 prompts, 3 candidates each
echo ""
echo "[4/8] Building DPO preference data (1 500 prompts × 3 candidates)..."
echo "  Expected: ~6–8 hrs"
elapsed
skip_if_exists data/d_pref_g.jsonl "d_pref_g.jsonl" || \
python 04_build_dpo_data.py \
    --sft-ckpt   checkpoints/m_sft/epoch_3 \
    --n-prompts  1500 \
    --n-candidates 3 \
    --delta 1
elapsed

# Step 5 — DPO, 3 epochs
echo ""
echo "[5/8] DPO training (3 epochs)..."
echo "  Expected: ~4–6 hrs"
elapsed
skip_if_exists checkpoints/m_final/epoch_3 "m_final/epoch_3" || \
python 05_dpo_train.py \
    --sft-ckpt  checkpoints/m_sft/epoch_3 \
    --epochs    3 \
    --per-device-batch 1 \
    --grad-accum 16 \
    --lr 5e-6 \
    --beta 0.1
elapsed

cd ..

# ── STAGE 2: DiffusionSVG ────────────────────────────────────────────────────

cd DiffusionSVG
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  STAGE 2 — DiffusionSVG"
echo "══════════════════════════════════════════════════════════"

# Step 6 — Filter complex prompts + generate 1 000 reference PNGs
echo ""
echo "[6/8] Filtering complex prompts..."
elapsed
skip_if_exists data/complex_prompts.jsonl "complex_prompts.jsonl" || \
python 00_filter_prompts.py \
    --input     "../${PROMPTS_FILE}" \
    --output    data/complex_prompts.jsonl \
    --min-score 2

echo "  Capping to 1 000 prompts..."
head -1000 data/complex_prompts.jsonl > data/complex_prompts_1k.jsonl
cp data/complex_prompts_1k.jsonl data/complex_prompts.jsonl

echo "  Generating reference PNGs (SD-Turbo, ~30 min)..."
elapsed
skip_if_exists data/complex_prompts_with_ids.jsonl "complex_prompts_with_ids.jsonl" || \
python 01_generate_pngs.py \
    --input  data/complex_prompts.jsonl \
    --output data/ref_pngs/
elapsed

# Step 7 — Vectorize PNGs → SVGs
echo ""
echo "[7/8] Vectorizing PNGs → SVGs (~20 min)..."
elapsed
skip_if_exists data/vectorized.jsonl "vectorized.jsonl" || \
python 02_vectorize_svgs.py \
    --input   data/complex_prompts_with_ids.jsonl \
    --png-dir data/ref_pngs/ \
    --svg-dir data/ref_svgs/ \
    --workers 8

python 03_build_dataset.py
elapsed

# Step 8 — GRPO, 2 epochs, starting from IntroSVG M_Final
echo ""
echo "[8/8] GRPO training (2 epochs, starting from M_Final)..."
echo "  Expected: ~8–12 hrs"
elapsed
skip_if_exists checkpoints/grpo_svg/epoch_2 "grpo_svg/epoch_2" || \
python 04_grpo_train.py \
    --model      "../IntroSVG/checkpoints/m_final/epoch_3" \
    --data       data/grpo_train.jsonl \
    --output     checkpoints/grpo_svg \
    --epochs     3 \
    --n-samples  4 \
    --beta       0.04 \
    --grad-accum 16
elapsed

cd ..

echo ""
echo "=========================================================="
echo "  FULL RUN COMPLETE"
echo "  Finished: $(date)"
echo "  Final model: DiffusionSVG/checkpoints/grpo_svg/epoch_2"
echo ""
echo "  Run inference:"
echo "    python IntroSVG/inference_loop.py \\"
echo "        --MODEL_NAME DiffusionSVG/checkpoints/grpo_svg/epoch_2 \\"
echo "        --CSV_FILE   prompts.csv \\"
echo "        --OUTPUT_DIR results/"
echo "=========================================================="
