#!/bin/bash
# Lane GPU 0 (budget v2: tool calls + command-execution minutes): gpt-oss-20b (server already up on 8100) -> qwen3.8-27b.
GPU=0 PORT=8100 HEADROOM_MIB=2048
source ~/cadfem-bench-run/lanes_lib.sh
curl -sf -m 5 http://127.0.0.1:8100/v1/models > /dev/null || serve gpt-oss-20b 20
run_suite primary gpt-oss-20b-high gpt-oss-20b --reasoning-effort high "${COMMON[@]}"
run_suite calibration gpt-oss-20b-high gpt-oss-20b --reasoning-effort high "${COMMON[@]}"
pkill -u "$USER" -f "[v]llm serve openai/gpt-oss-20b"; sleep 30          # the 20b server was started by hand
stop_server
serve qwen3.8-27b 66 && { run_suite primary qwen3.8-27b-xhigh qwen3.8-27b "${QWEN[@]}" "${COMMON[@]}"; run_suite calibration qwen3.8-27b-xhigh qwen3.8-27b "${QWEN[@]}" "${COMMON[@]}"; }
stop_server
log LANE-DONE
