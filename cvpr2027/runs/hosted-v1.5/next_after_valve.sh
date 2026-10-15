#!/bin/bash
# After A-VALVE-transient is recorded, stop the hard-task run (before Wyk ring) and spend what is left of the $10 cap on A-FCVM-PL-Wyk_Rohrstoss_ring (independently verified reference; CADWORLD-001 has a prompt defect).
cd ~/SVG/cvpr2027
R=runs/hosted-v1.5/runs/gpt-6-astra-medium
until [ -f $R/A-VALVE-transient/result.json ] || ! pgrep -f "cadfem_agent.py.*gpt-6-astra-medium" > /dev/null; do sleep 3; done
pkill -f "cadfem_agent.py.*gpt-6-astra-medium"; sleep 3
LEFT=$(python3 -c "
import json, glob
hard = 0.0
for t in ('A-VALVE-transient', 'A-FCVM-PL-Wyk_Rohrstoss_ring', 'B-RIGGING-test1'):
    for f in glob.glob('$R/' + t + '/transcript.jsonl') + glob.glob('$R/_interrupted/' + t + '-*.jsonl'):
        hard += sum(json.loads(l).get('cost_usd') or 0 for l in open(f))
print(round(10 - 7.01 - hard - 0.04, 2))")
echo "$(date '+%F %T') valve recorded; budget left under \$10: \$$LEFT"
python3 -c "import sys; sys.exit(0 if $LEFT >= 0.5 else 1)" && ENV_FILE=$HOME/SVG/.env.svg_new KEY_VAR=OPENAI_API_KEY_SVG_NEW \
  scripts/cadfem_bench/openweight/run_hosted.sh gpt-6-astra-medium gpt-6-astra $LEFT medium --parallel 1 --task-reserve-usd 0.5 --tasks A-FCVM-PL-Wyk_Rohrstoss_ring
echo "$(date '+%F %T') NEXT-DONE"
