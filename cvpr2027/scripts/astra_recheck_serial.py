from pathlib import Path
import json,subprocess,sys
root=Path(__file__).resolve().parents[1];base=root/'output/datasets/cadfem-challenge-trials'
for t in json.loads((base/'failure-list.json').read_text())['cases']:
 if not t['count_as_distinct_failure']:continue
 tid=t['task_id'];r=root/'runs/astra-recheck-20261015'/tid
 if (r/'dispatch.json').exists():continue
 rc=subprocess.run([sys.executable,str(root/'scripts/astra_recheck_one.py'),tid]).returncode
 if rc:print('HALT at '+tid,flush=True);break
print('Recheck queue ended.',flush=True)
