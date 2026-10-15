from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
for tid in ['A-SIMJEB-analysis-101','A-SIMJEB-analysis-108']:
 r=root/'runs/astra-recheck2-20261015'/tid
 if (r/'dispatch.json').exists():continue
 rc=subprocess.run([sys.executable,str(root/'scripts/astra_recheck2_one.py'),tid]).returncode
 if rc:print('HALT '+tid,flush=True);break
print('Memory-feedback queue ended.',flush=True)
