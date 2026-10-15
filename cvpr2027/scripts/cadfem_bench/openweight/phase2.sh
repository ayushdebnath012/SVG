#!/bin/bash
# Phase 2: when gpt-oss-20b (GPU 0) has finished primary + calibration, gpt-oss-120b resumes on GPU 0 (lane2_gpu0.sh).
cd ~/cadfem-bench-run
PY=~/miniconda3/envs/cadfem-vllm/bin/python
log() { echo "$(date '+%F %T') [phase2] $*"; }
P=$(pgrep -u "$USER" -f "^$PY cadfem_agent.py --suite-dir candidate --run-id gpt-oss-20b-high ")
if [ -n "$P" ]; then log "waiting for gpt-oss-20b primary (pid $P)"; while kill -0 "$P" 2>/dev/null; do sleep 30; done; fi
GPU=0 PORT=8100 HEADROOM_MIB=2048; source ./lanes_lib.sh
[ -f runs/gpt-oss-20b-high-calibration/summary.json ] || run_suite calibration gpt-oss-20b-high gpt-oss-20b --reasoning-effort high "${COMMON[@]}"
log "gpt-oss-20b done; stopping its server"
pkill -u "$USER" -f "vllm serve openai/gpt-oss-20b"; sleep 40
setsid nohup ./lane2_gpu0.sh > logs/lane2_gpu0.log 2>&1 < /dev/null &
log "gpt-oss-120b lane started on GPU 0"
