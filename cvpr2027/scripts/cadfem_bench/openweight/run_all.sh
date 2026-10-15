#!/bin/bash
# CADFEM-Bench v1.5 open-weight queue on the shared H100 host, GPU 0 only:
# gpt-oss-20b (already being served) -> gpt-oss-120b -> qwen3.8-27b; primary (46) then calibration (7) tasks per model.
# Never touches other users' processes: if GPU 0 lacks free memory for the next model, it waits.
cd ~/cadfem-bench-run
PY=~/miniconda3/envs/cadfem-vllm/bin/python
log() { echo "$(date '+%F %T') $*"; }

stop_server() {   # only our own vLLM server (pid recorded at launch, or the gpt-oss-20b server started by hand)
  if [ -f logs/serve.pid ]; then kill -- -"$(cat logs/serve.pid)" 2>/dev/null; rm -f logs/serve.pid; fi
  pkill -u "$USER" -f "[v]llm serve openai/gpt-oss-20b" 2>/dev/null
  sleep 30
}

serve() {   # serve <name> <min_gib>
  local name=$1 need=$2 util
  while true; do
    read free total <<< "$(nvidia-smi -i 0 --query-gpu=memory.free,memory.total --format=csv,noheader,nounits | tr -d ',')"
    util=$(awk -v f="$free" -v t="$total" 'BEGIN{u=(f-2048)/t; if(u>0.88)u=0.88; printf "%.2f", int(u*100)/100}')
    awk -v f="$free" -v n="$need" 'BEGIN{exit !(f/1024 >= n)}' && break
    log "GPU 0 has ${free} MiB free, need ${need} GiB for $name; waiting"; sleep 300
  done
  log "starting $name with --gpu-memory-utilization $util"
  GPU_UTIL=$util setsid ./serve_model.sh "$name" > "logs/serve-$name.log" 2>&1 < /dev/null &
  echo $! > logs/serve.pid
  for i in $(seq 1 120); do
    curl -sf -m 5 http://127.0.0.1:8100/v1/models > /dev/null && { log "$name up"; return 0; }
    kill -0 "$(cat logs/serve.pid)" 2>/dev/null || { log "$name server died"; tail -5 "logs/serve-$name.log"; return 1; }
    sleep 15
  done
  log "$name did not come up"; return 1
}

run() {     # run <run_id> <served_model> [harness args...]
  local id=$1 model=$2; shift 2
  log "run $id: primary"
  $PY cadfem_agent.py --suite-dir candidate --run-id "$id" --model "$model" "$@"
  log "run $id: calibration"
  $PY cadfem_agent.py --suite-dir calibration --suite-kind suite --readme candidate/README.md --run-id "$id-calibration" --model "$model" --out runs "$@"
  log "run $id: done"
}

COMMON=(--parallel 8 --max-minutes 45 --max-calls 250 --pass-reasoning)
run gpt-oss-20b-high gpt-oss-20b --reasoning-effort high "${COMMON[@]}"
stop_server
serve gpt-oss-120b 74 && run gpt-oss-120b-high gpt-oss-120b --reasoning-effort high "${COMMON[@]}"
stop_server
serve qwen3.8-27b 68 && run qwen3.8-27b-xhigh qwen3.8-27b --vision --reasoning-effort xhigh --temperature 1.0 --top-p 0.95 --extra-body '{"top_k": 20}' "${COMMON[@]}"
stop_server
log ALL-DONE
