#!/bin/bash
# Run CADFEM-Bench tasks against a hosted model through the same harness (macOS sandbox, pinned cq-env runtime).
# The API key is read from ~/SVG/.env into the environment only; it is never printed or written to run records.
# Usage: [ENV_FILE=~/SVG/.env] [KEY_VAR=OPENAI_API_KEY] run_hosted.sh RUN_ID MODEL BUDGET_USD EFFORT [harness args...]
set -e
cd "$(dirname "$0")/../../.."                      # cvpr2027/
RUN=$1 MODEL=$2 BUDGET=$3 EFFORT=$4; shift 4
ENV_FILE=${ENV_FILE:-$HOME/SVG/.env} KEY_VAR=${KEY_VAR:-OPENAI_API_KEY}
export OPENAI_API_KEY="$(grep -E "^${KEY_VAR}=" "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d "\"' ")"
[ -n "$OPENAI_API_KEY" ] || { echo "$KEY_VAR missing in $ENV_FILE"; exit 1; }
if [ "${SUITE:-primary}" = calibration ]; then SUITE_ARGS=(--suite-dir runs/hosted-v1.5/calibration --suite-kind suite --readme runs/hosted-v1.5/candidate/README.md)
else SUITE_ARGS=(--suite-dir runs/hosted-v1.5/candidate); fi
exec tmp/hosted-harness-env/bin/python scripts/cadfem_bench/openweight/cadfem_agent.py \
  "${SUITE_ARGS[@]}" --run-id "$RUN" --model "$MODEL" --base-url "" --api responses --api-key-env OPENAI_API_KEY \
  --sandbox macos --runtime "$PWD/tmp/cq-env" --vision --reasoning-effort "$EFFORT" \
  --max-calls 250 --max-minutes 45 --max-wall-minutes 180 \
  --price-in 12.5 --price-cached 1 --price-out 50 --budget-usd "$BUDGET" --out runs/hosted-v1.5/runs "$@"
