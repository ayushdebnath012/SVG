#!/bin/bash
# Phase 2, GPU 1 (shared with other users; 8 GiB headroom): qwen3.8-27b primary + calibration.
GPU=1 PORT=8101 HEADROOM_MIB=8192
source ~/cadfem-bench-run/lanes_lib.sh
serve qwen3.8-27b 66 || exit 1
# one tool-calling request with the run's settings must succeed before any task starts
body='{"model": "qwen3.8-27b", "max_tokens": 4096, "messages": [{"role": "user", "content": "Call the bash tool with the command: echo ok"}], "tools": [{"type": "function", "function": {"name": "bash", "description": "Run a shell command", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}}], "top_k": 20, "chat_template_kwargs": {"reasoning_effort": "xhigh"}}'
r=$(curl -s -m 600 -w '\n%{http_code}' "http://127.0.0.1:$PORT/v1/chat/completions" -H 'Content-Type: application/json' -d "$body")
log "smoke test HTTP $(tail -1 <<< "$r"): $(head -1 <<< "$r" | grep -oE '"tool_calls":\[[^]]{0,160}' | head -1)"
[ "$(tail -1 <<< "$r")" = 200 ] && grep -q '"tool_calls":\[{' <<< "$r" || { log "smoke test failed: $(head -c 600 <<< "$r")"; stop_server; exit 1; }
run_suite primary qwen3.8-27b-xhigh qwen3.8-27b "${QWEN[@]}" "${COMMON[@]}" --parallel 6
run_suite calibration qwen3.8-27b-xhigh qwen3.8-27b "${QWEN[@]}" "${COMMON[@]}" --parallel 6
stop_server
log LANE-DONE
