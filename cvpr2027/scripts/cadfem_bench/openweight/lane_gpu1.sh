#!/bin/bash
# Lane GPU 1 (shared with other users' jobs; 8 GiB headroom): gpt-oss-120b, 4 tasks in parallel so its KV cache holds them.
GPU=1 PORT=8101 HEADROOM_MIB=8192
source ~/cadfem-bench-run/lanes_lib.sh
curl -sf -m 5 http://127.0.0.1:8101/v1/models > /dev/null || serve gpt-oss-120b 72
run_suite primary gpt-oss-120b-high gpt-oss-120b --reasoning-effort high "${COMMON[@]}" --parallel 4
run_suite calibration gpt-oss-120b-high gpt-oss-120b --reasoning-effort high "${COMMON[@]}" --parallel 4
stop_server
log LANE-DONE
