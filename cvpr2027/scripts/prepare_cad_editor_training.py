"""Prepare a bounded CAD-Editor pilot with exact-sequence component isolation.

Reads the official processed.zip without executing archive code. All connected
original/edited sequences share a split; any component touching upstream test is
excluded from training. This does not prove geometric near-duplicate isolation.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import zipfile

SOURCE='https://raw.githubusercontent.com/microsoft/CAD-Editor/main/data/processed.zip'
SYSTEM='You edit parametric CAD construction sequences. Apply the instruction to the original sequence. Return only the complete edited sequence in the same command syntax. Preserve all unrelated geometry. Do not add explanation or Markdown.'

def sha(text): return hashlib.sha256(text.encode()).hexdigest()

def prepare(archive,out,limit=2048):
    with zipfile.ZipFile(archive) as z:
        train=json.loads(z.read('dataset/train.json')); test=json.loads(z.read('dataset/test.json'))
    parent={}
    def find(x):
        parent.setdefault(x,x)
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b: parent[max(a,b)]=min(a,b)
    def norm(s): return ' '.join(s.split())
    for r in train+test: union(sha(norm(r['original_sequence'])),sha(norm(r['edited_sequence'])))
    test_roots={find(sha(norm(r['original_sequence']))) for r in test}
    pools={'train':[],'validation':[],'test':[]}; seen=set()
    for upstream,rows in [('train',train),('test',test)]:
        for r in rows:
            original,target=norm(r['original_sequence']),norm(r['edited_sequence'])
            component=find(sha(original)); rid=sha(original+'\n'+r['instruction']+'\n'+target)
            if rid in seen: continue
            seen.add(rid)
            if upstream=='train' and component in test_roots: continue
            # Shorter sequences permit bounded generation-based before/after checks.
            if len(original)>2600 or len(target)>2600: continue
            split='test' if upstream=='test' else ('validation' if int(component[:8],16)%10==0 else 'train')
            pools[split].append(dict(id=rid,component_id=component,source='CAD-Editor',upstream_split=upstream,
                instruction=r['instruction'],original_sequence=original,target=target,
                edit_type=r.get('type'),annotation_method=r.get('method'),
                input='Original CAD sequence:\n'+original+'\nEdit instruction:\n'+r['instruction']))
    rng=random.Random(17); out.mkdir(parents=True,exist_ok=True); counts={}; selected={}
    for split,rows in pools.items():
        rng.shuffle(rows); rows=rows[:limit if split=='train' else 128];selected[split]=rows
        (out/(split+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rows))
        counts[split]=dict(n=len(rows),components=len({r['component_id'] for r in rows}),edit_types=dict(Counter(r['edit_type'] for r in rows)))
    groups=[{r['component_id'] for r in rows} for rows in selected.values()]
    assert all(not a&b for i,a in enumerate(groups) for b in groups[i+1:])
    manifest=dict(source_url=SOURCE,source_archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        upstream_counts={'train':len(train),'test':len(test)},split_rule='Exact normalized original/edited sequence connected components; all upstream-test components excluded from train/validation; deterministic component holdout for validation.',
        limitation='Source archive lacks native CAD design IDs. Equivalent geometry with different sequences is not deduplicated. This is a training feasibility pilot, not the final geometric-generalization evaluation.',
        selection='Seed 17 shuffle after split; source/target <=2600 characters; bounded counts; no Astra benchmark samples.',
        counts=counts,system=SYSTEM,files={s:hashlib.sha256((out/(s+'.jsonl')).read_bytes()).hexdigest() for s in pools})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); print(json.dumps(counts,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--limit',type=int,default=2048);a=p.parse_args();prepare(a.archive,a.output,a.limit)
