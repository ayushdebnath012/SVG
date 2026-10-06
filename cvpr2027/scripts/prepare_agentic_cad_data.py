"""Package saved training candidates with target-free observations and isolated reward labels."""
import hashlib
import json
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'experiments/agentic-verifier-grpo-20261006'


def build():
    original = ROOT/'runs/multisource-cad-colab-20261002/results-final'
    train = {r['id']:r for r in map(json.loads,(original/'train-retained.jsonl').read_text().splitlines())}
    test = list(map(json.loads,(original/'test-retained.jsonl').read_text().splitlines()))
    heldout = {r['id'] for r in test}
    heldout_components = {r['component_id'] for r in test if r['source']=='BenchCAD'}
    records = []
    for run in ('cad-astra-distill-20261004','cad-astra-distill-n2-20261005'):
        for path in sorted((ROOT/'runs'/run).glob('*/verify.json')):
            v = json.loads(path.read_text())
            if 'audit_selected_strict' not in v:
                continue
            row=train[v['id']]
            assert row['id'] not in heldout and row['component_id'] not in heldout_components
            candidates=json.loads((path.parent/'candidates.json').read_text())
            split='dev' if int(hashlib.sha256(str(row['component_id']).encode()).hexdigest(),16)%10==0 else 'train'
            for c in v['candidates']:
                records.append(dict(id=row['id']+'#'+str(c['index']),task_id=row['id'],component_id=row['component_id'],category=row['category'],split=split,code=row['code'],instruction=row['instruction'],candidate=candidates[c['index']],tools={'execute':{k:c.get(k) for k in ('gates','error','volume','changed')},'numbers':c.get('numbers',[])},label=(c.get('audit_reference_iou') or 0)>=.99999))
    OUT.mkdir(parents=True,exist_ok=True)
    for split in ('train','dev'):
        (OUT/(split+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in records if r['split']==split))
    assert not ({r['component_id'] for r in records if r['split']=='train'} & {r['component_id'] for r in records if r['split']=='dev'})
    summary={'candidates':len(records),'tasks':len({r['task_id'] for r in records}),'by_split':dict(Counter(r['split'] for r in records)),'labels':dict(Counter(str(r['label']) for r in records)),'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (original/'train-retained.jsonl',original/'test-retained.jsonl')}}
    (OUT/'data-manifest.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':build()
