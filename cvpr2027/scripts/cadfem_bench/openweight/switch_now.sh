#!/bin/bash
# 2026-10-15 01:1x: start qwen3.8-27b on GPU 1 now; gpt-oss-120b pauses and resumes on GPU 0 when gpt-oss-20b is done.
cd ~/cadfem-bench-run
PY=~/miniconda3/envs/cadfem-vllm/bin/python
log() { echo "$(date '+%F %T') [switch] $*"; }
log "stopping lane_gpu0.sh controller only (gpt-oss-20b keeps running)"
pkill -u "$USER" -f "^/bin/bash ./lane_gpu0.sh"
log "stopping the gpt-oss-120b lane on GPU 1"
pkill -u "$USER" -f "^/bin/bash ./lane_gpu1.sh"
pkill -u "$USER" -f "^$PY cadfem_agent.py --suite-dir (candidate|calibration) .*--run-id gpt-oss-120b-high"
sleep 5
for p in $(pgrep -u "$USER" -x landlock_run); do tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | grep -q "gpt-oss-120b-high" && kill "$p"; done
[ -f logs/serve-gpu1.pid ] && kill -- -"$(cat logs/serve-gpu1.pid)" 2>/dev/null; rm -f logs/serve-gpu1.pid
sleep 40
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader
setsid nohup ./lane2_gpu1.sh > logs/lane2_gpu1.log 2>&1 < /dev/null &
log "qwen lane started on GPU 1"
setsid nohup ./phase2.sh > logs/phase2.log 2>&1 < /dev/null &
log "phase2 waiting for gpt-oss-20b, then gpt-oss-120b on GPU 0"
