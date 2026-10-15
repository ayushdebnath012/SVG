#!/bin/bash
# Serve one model on one GPU of the shared host for the CADFEM-Bench open-weight run.
# Usage: [GPU=0|1] [PORT=8100] [GPU_UTIL=0.9] serve_model.sh gpt-oss-120b|gpt-oss-20b|qwen3.8-27b
set -e
V=~/miniconda3/envs/cadfem-vllm/bin
export CUDA_VISIBLE_DEVICES=${GPU:-0} HF_HUB_OFFLINE=1 PATH="$V:$PATH"   # the env is not activated; JIT builds look for ninja on PATH
export TIKTOKEN_RS_CACHE_DIR=~/cadfem-bench-run/cache/tiktoken-rs TMPDIR=~/cadfem-bench-run/cache/tmp   # /tmp caches on this shared host belong to other users
mkdir -p $TIKTOKEN_RS_CACHE_DIR $TMPDIR
COMMON="--host 127.0.0.1 --port ${PORT:-8100} --gpu-memory-utilization ${GPU_UTIL:-0.90} --max-model-len 131072 --enable-auto-tool-choice"
case "$1" in
  gpt-oss-120b) exec $V/vllm serve openai/gpt-oss-120b --served-model-name gpt-oss-120b $COMMON --tool-call-parser openai ;;
  gpt-oss-20b)  exec $V/vllm serve openai/gpt-oss-20b  --served-model-name gpt-oss-20b  $COMMON --tool-call-parser openai ;;
  qwen3.8-27b)  exec $V/vllm serve Qwen/Qwen3.8-27B   --served-model-name qwen3.8-27b  $COMMON --tool-call-parser qwen3_coder --reasoning-parser qwen3 --kv-cache-dtype fp8 --limit-mm-per-prompt '{"image": 6, "video": 0}' --gdn-prefill-backend triton ;;   # FlashInfer's GDN kernel needs nvcc, absent here
  *) echo "unknown model $1"; exit 2 ;;
esac
