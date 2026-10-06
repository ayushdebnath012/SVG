"""Compute target-free tool observations for frozen Astra held-out predictions."""
import json
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/agentic-verifier-grpo-20261006'

def observe(row,candidate):
    task=dict(source=row['code'],instruction=row['instruction'],representation='cadquery',candidates=[candidate])
    assert 'reference_code' not in task
    with tempfile.NamedTemporaryFile('w',suffix='.json') as f:
        json.dump(task,f);f.flush()
        try:
            result=subprocess.run([str(ROOT/'tmp/cad-runtime/bin/python'),str(ROOT/'scripts/cad_edit_verifier.py'),f.name],capture_output=True,text=True,timeout=120)
            if result.returncode:raise RuntimeError(result.stderr[-500:])
            v=json.loads(result.stdout);c=v['candidates'][0]
            return {'execute':{k:c.get(k) for k in ('gates','error','volume','changed')},'numbers':c.get('numbers',[])}
        except Exception as error:
            return {'execute':{'gates':False,'error':'tool_error: '+str(error)[-500:],'volume':None,'changed':None},'numbers':[]}

def main():
    rows=[json.loads(l) for l in (ROOT/'runs/multisource-cad-colab-20261002/results-final/test-retained.jsonl').read_text().splitlines()]
    geom={r['id']:r for r in map(json.loads,(ROOT/'runs/multisource-cad-astra-20261004/scored/astra-predictions-geometry.jsonl').read_text().splitlines())}
    preds={r['id']:r for r in map(json.loads,(ROOT/'runs/multisource-cad-astra-20261004/scored/astra-predictions.jsonl').read_text().splitlines())}
    rows=[r for r in rows if r['source']=='BenchCAD']
    path=OUT/'heldout.jsonl';done={r['id']:r for r in map(json.loads,path.read_text().splitlines())} if path.exists() else {}
    def one(row):
        candidate=preds[row['id']]['prediction']
        return dict(id=row['id'],category=row['category'],code=row['code'],instruction=row['instruction'],candidate=candidate,tools=observe(row,candidate),label=bool(geom[row['id']]['match_strict']),reference_valid=geom[row['id']]['reference_valid'])
    with path.open('a') as f,ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(one,[r for r in rows if r['id'] not in done]):
            f.write(json.dumps(result)+'\n');f.flush();print(result['id'][:12],result['tools']['execute']['gates'],flush=True)
if __name__=='__main__':main()
