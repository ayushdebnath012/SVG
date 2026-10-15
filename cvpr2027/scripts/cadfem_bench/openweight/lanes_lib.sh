# Shared functions for the two GPU lanes of the CADFEM-Bench open-weight run (sourced by lane_gpu0.sh / lane_gpu1.sh).
# Other users share both GPUs: never touch their processes; leave HEADROOM_MIB free on the GPU for them.
cd ~/cadfem-bench-run
PY=~/miniconda3/envs/cadfem-vllm/bin/python
log() { echo "$(date '+%F %T') [gpu$GPU] $*"; }

stop_server() {   # our own server on this lane only (process group recorded at launch)
  if [ -f "logs/serve-gpu$GPU.pid" ]; then kill -- -"$(cat logs/serve-gpu$GPU.pid)" 2>/dev/null; rm -f "logs/serve-gpu$GPU.pid"; fi
  sleep 30
}

serve() {   # serve <name> <min_free_gib>
  local name=$1 need=$2 util free total
  while true; do
    read free total <<< "$(nvidia-smi -i "$GPU" --query-gpu=memory.free,memory.total --format=csv,noheader,nounits | tr -d ',')"
    util=$(awk -v f="$free" -v t="$total" -v h="$HEADROOM_MIB" 'BEGIN{u=(f-h)/t; if(u>0.88)u=0.88; printf "%.2f", int(u*100)/100}')
    awk -v f="$free" -v n="$need" -v h="$HEADROOM_MIB" 'BEGIN{exit !((f-h)/1024 >= n)}' && break
    log "GPU $GPU has ${free} MiB free (headroom ${HEADROOM_MIB} MiB), need ${need} GiB for $name; waiting"; sleep 300
  done
  log "starting $name on GPU $GPU port $PORT with --gpu-memory-utilization $util"
  GPU=$GPU PORT=$PORT GPU_UTIL=$util setsid ./serve_model.sh "$name" > "logs/serve-$name.log" 2>&1 < /dev/null &
  echo $! > "logs/serve-gpu$GPU.pid"
  for i in $(seq 1 120); do
    curl -sf -m 5 "http://127.0.0.1:$PORT/v1/models" > /dev/null && { log "$name up"; return 0; }
    kill -0 "$(cat logs/serve-gpu$GPU.pid)" 2>/dev/null || { log "$name server died"; tail -5 "logs/serve-$name.log"; return 1; }
    sleep 15
  done
  log "$name did not come up"; return 1
}

run_suite() {   # run_suite primary|calibration <run_id> <served_model> [harness args...]
  local suite=$1 id=$2 model=$3; shift 3
  log "run $id: $suite"
  if [ "$suite" = primary ]; then
    $PY cadfem_agent.py --suite-dir candidate --run-id "$id" --model "$model" --base-url "http://127.0.0.1:$PORT/v1" "$@"
  else
    $PY cadfem_agent.py --suite-dir calibration --suite-kind suite --readme candidate/README.md --run-id "$id-calibration" --model "$model" --base-url "http://127.0.0.1:$PORT/v1" "$@"
  fi
  log "run $id: $suite done"
}

COMMON=(--parallel 8 --max-minutes 45 --max-wall-minutes 180 --max-calls 250 --pass-reasoning)
# Qwen3.8's reasoning effort is a chat-template variable (xhigh default, medium, low), not the OpenAI reasoning_effort field.
QWEN=(--vision --temperature 1.0 --top-p 0.95 --extra-body '{"top_k": 20, "chat_template_kwargs": {"reasoning_effort": "xhigh"}}')
