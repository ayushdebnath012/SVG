"""Sequential trials only. Stops on budget preflight rejection or unknown cost."""
from pathlib import Path
import json,subprocess,sys
root=Path(__file__).resolve().parents[1];base=root/'output/datasets/cadfem-challenge-trials'
for t in json.loads((base/'failure-hunt-queue.json').read_text()):
 tid=t['task_id'];r=root/'runs/astra-failure-hunt-20261015'/tid
 if (base/'STOP_HUNT').exists():break
 if json.loads((base/'failure-list.json').read_text())['confirmed_distinct_cases']>=10:break
 if (r/'dispatch.json').exists():continue
 rc=subprocess.run([sys.executable,str(root/'scripts/astra_hunt_one.py'),tid]).returncode
 if rc:print('HALTED at '+tid,flush=True);break
print('Serial queue ended; no further calls.',flush=True)
