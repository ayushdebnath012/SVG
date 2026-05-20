#!/usr/bin/env bash
# Full Pipeline: IntroSVG SFT → DiffusionSVG GRPO
# =================================================
# Stage 1 (IntroSVG): trains the VLM to write clean SVG code on simple+general prompts
# Stage 2 (DiffusionSVG): extends to complex multi-object prompts via GRPO,
#   rewarded by visual similarity to diffusion model reference PNGs
#
# Hardware: 8 × A100 80 GB for Stage 1, 1 × A100 40–80 GB for Stage 2
# Total wall time: ~3–5 hrs (SFT) + ~6–10 hrs (GRPO)
#
# Usage:
#   bash run_full_pipeline.sh
#   bash run_full_pipeline.sh --prompts my_prompts.txt   # custom input prompts

set -euo pipefail

PROMPTS_FILE="${1:-prompts.txt}"   # complex prompt source
NPROC="${NPROC:-8}"                # GPUs for SFT (DeepSpeed)
INTROSVG_DIR="IntroSVG"
DIFFSVG_DIR="DiffusionSVG"

echo "=========================================================="
echo "  STAGE 1 — IntroSVG: build data + SFT"
echo "=========================================================="

cd "$INTROSVG_DIR"

# Step 1: standardise SVG datasets → d_g_direct.jsonl (~200K rows)
echo "[1/5] Standardising SVG data..."
python 01_standardize_data.py

# Step 2: GPT-4o critic loop → d_sft.jsonl (requires OPENAI_API_KEY)
echo "[2/5] Building SFT data (GPT-4o)..."
python 02_build_sft_data.py

# Step 3: SFT training via LLaMA-Factory (8 × A100 80 GB)
echo "[3/5] SFT training → checkpoints/m_sft/epoch_3"
NPROC=$NPROC bash train_sft.sh

cd ..

echo ""
echo "=========================================================="
echo "  STAGE 2 — DiffusionSVG: build data + GRPO"
echo "=========================================================="

cd "$DIFFSVG_DIR"

# Step 0: filter complex prompts from source file
echo "[4a/5] Filtering complex prompts..."
python 00_filter_prompts.py \
    --input  "../${PROMPTS_FILE}" \
    --output data/complex_prompts.jsonl \
    --min-score 2

# Step 1: diffusion model → reference PNGs
echo "[4b/5] Generating reference PNGs (diffusion)..."
python 01_generate_pngs.py \
    --input  data/complex_prompts.jsonl \
    --output data/ref_pngs/

# Step 2: vectorize PNGs → SVGs
echo "[4c/5] Vectorizing PNGs → SVGs..."
python 02_vectorize_svgs.py \
    --input   data/complex_prompts_with_ids.jsonl \
    --png-dir data/ref_pngs/ \
    --svg-dir data/ref_svgs/

# Step 3: build GRPO dataset
echo "[4d/5] Building GRPO dataset..."
python 03_build_dataset.py

# Step 4: GRPO training starting from IntroSVG M_SFT (1 × A100 40–80 GB)
echo "[5/5] GRPO training → checkpoints/grpo_svg"
python 04_grpo_train.py \
    --model  "../IntroSVG/checkpoints/m_sft/epoch_3" \
    --data   data/grpo_train.jsonl \
    --output checkpoints/grpo_svg \
    --epochs 2 \
    --n-samples 4 \
    --beta 0.04 \
    --grad-accum 16

cd ..

echo ""
echo "=========================================================="
echo "  DONE"
echo "  Final model: DiffusionSVG/checkpoints/grpo_svg/epoch_2"
echo ""
echo "  Run inference:"
echo "    python IntroSVG/inference_loop.py \\"
echo "        --MODEL_NAME DiffusionSVG/checkpoints/grpo_svg/epoch_2 \\"
echo "        --CSV_FILE prompts.csv \\"
echo "        --OUTPUT_DIR results/"
echo "=========================================================="
