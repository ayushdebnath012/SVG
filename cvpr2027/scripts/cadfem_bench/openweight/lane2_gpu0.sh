#!/bin/bash
# Phase 2, GPU 0: gpt-oss-120b (resume), then re-run its tasks that were stopped by the 3-h wall-clock cap.
GPU=0 PORT=8100 HEADROOM_MIB=2048
source ~/cadfem-bench-run/lanes_lib.sh
serve gpt-oss-120b 72 || exit 1
run_suite primary gpt-oss-120b-high gpt-oss-120b --reasoning-effort high "${COMMON[@]}"
run_suite calibration gpt-oss-120b-high gpt-oss-120b --reasoning-effort high "${COMMON[@]}"
for RUN in gpt-oss-120b-high gpt-oss-120b-high-calibration; do
  WALL=$($PY - "$RUN" <<'PY'
import json, sys
from pathlib import Path
run = sys.argv[1]
meta = json.loads((Path("runs") / run / "run.json").read_text())
out = []
for f in sorted((Path("runs") / run).glob("*/result.json")):
    r = json.loads(f.read_text())
    if r["status"] == "budget_exhausted" and r["tool_calls"] < meta["max_calls"] and r.get("command_seconds", 0) < meta["max_minutes"] * 60:
        out.append(r["task_id"])
print(" ".join(out))
PY
)
  if [ -n "$WALL" ]; then
    log "re-running wall-capped $RUN tasks on GPU 0: $WALL"
    mkdir -p runs/wallcap-archive/$RUN
    for t in $WALL; do chmod -R u+w runs/$RUN/$t; mv runs/$RUN/$t runs/wallcap-archive/$RUN/; rm -rf runs/submissions/$RUN/$t; done
    SUITE=primary; [[ $RUN == *-calibration ]] && SUITE=calibration
    run_suite $SUITE gpt-oss-120b-high gpt-oss-120b --reasoning-effort high "${COMMON[@]}" --tasks $WALL
  fi
done
stop_server
log LANE-DONE
