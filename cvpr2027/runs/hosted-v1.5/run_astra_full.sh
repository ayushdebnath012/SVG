#!/bin/bash
# Full GPT-6 Astra run on CADFEM-Bench v1.5 under a total USD cap (pilot + earlier invalid attempt count against it).
# Usage: CAP=10 run_astra_full.sh   (re-run with a higher CAP to continue; finished tasks are kept)
set -e
cd ~/SVG/cvpr2027
CAP=${CAP:-10}
H=runs/hosted-v1.5
while pgrep -f "run-id gpt-6-astra-medium-pilot" > /dev/null; do sleep 20; done          # let the pilot finish its tasks
RUN=gpt-6-astra-medium
if [ -d $H/runs/gpt-6-astra-medium-pilot ] && [ ! -d $H/runs/$RUN ]; then              # pilot tasks ran under identical settings: keep them
  cp -R $H/runs/gpt-6-astra-medium-pilot $H/runs/$RUN && mv $H/runs/$RUN/run.json $H/runs/$RUN/pilot-run.json 2>/dev/null || true
  mv $H/runs/$RUN/summary.json $H/runs/$RUN/pilot-summary.json 2>/dev/null || true
  mkdir -p $H/runs/submissions && cp -R $H/runs/submissions/gpt-6-astra-medium-pilot $H/runs/submissions/$RUN
fi
spent() { python3 -c "
import json, glob
s = 1.53                                                       # invalid relative-path attempt (runs/hosted-v1.5/invalid/)
s += sum(json.load(open(f)).get('cost_usd', 0) for f in glob.glob('$H/runs/gpt-6-astra-medium*/*/result.json') if '/gpt-6-astra-medium-pilot/' not in f)
print(f'{s:.2f}')"; }
order=$(python3 -c "
import json, collections
ts = [json.loads(l) for l in open('$H/candidate/tasks.jsonl')]
fam = collections.OrderedDict()
for t in ts: fam.setdefault(t['engineering_family'], []).append(t['task_id'])
out = []
while any(fam.values()):
    for f in fam:
        if fam[f]: out.append(fam[f].pop(0))
print(' '.join(out))")
LEFT=$(python3 -c "print(max(0.0, round($CAP - $(spent), 2)))")
echo "$(date '+%F %T') primary: cap \$$CAP, spent \$$(spent), budget for this pass \$$LEFT"
[ "$(python3 -c "print($LEFT > 0.3)")" = True ] && ENV_FILE=$HOME/SVG/.env.svg_new KEY_VAR=OPENAI_API_KEY_SVG_NEW \
  scripts/cadfem_bench/openweight/run_hosted.sh $RUN gpt-6-astra $LEFT medium --parallel 4 --tasks $order
LEFT=$(python3 -c "print(max(0.0, round($CAP - $(spent), 2)))")
echo "$(date '+%F %T') calibration: spent \$$(spent), budget for this pass \$$LEFT"
[ "$(python3 -c "print($LEFT > 0.3)")" = True ] && SUITE=calibration ENV_FILE=$HOME/SVG/.env.svg_new KEY_VAR=OPENAI_API_KEY_SVG_NEW \
  scripts/cadfem_bench/openweight/run_hosted.sh $RUN-calibration gpt-6-astra $LEFT medium --parallel 4
echo "$(date '+%F %T') ASTRA-DONE total spent \$$(spent) of cap \$$CAP"
