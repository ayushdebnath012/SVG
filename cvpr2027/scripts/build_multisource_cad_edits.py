"""Combine pinned online edit sources without pooling incompatible geometry/FEM claims."""
import difflib,json,hashlib,re
from pathlib import Path
from cad_edit_contracts import apply
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/multisource-cad-edits-v1';OUT.mkdir(exist_ok=True)
SYSTEM='You edit mechanical CAD. Return only JSON {"edits":[{"start":0,"delete":0,"insert":["replacement line"]}]}. Indices are zero-based lines of the ORIGINAL input; operations must be ordered, nonoverlapping and in bounds. Preserve unrelated features. The supplied representation determines syntax. Return no explanation or invented physics results. Geometry execution and FEM checks are performed by external tools; never claim verification.'
B=ROOT/'data/benchcad-online-edit-v1';old=ROOT/'runs/benchcad-online-mlx-20261002';C=ROOT/'data/cad-editor-pilot'
assert hashlib.sha256((ROOT/'tmp/cad-editor-source/processed.zip').read_bytes()).hexdigest()==json.loads((C/'manifest.json').read_text())['source_archive_sha256']
retained={split:{r['id'] for r in map(json.loads,(old/f'{split if split!="validation" else "valid"}-retained.jsonl').read_text().splitlines())} for split in []}
# Exact retained IDs are recovered from the completed original run's token-filtered records.
for split,name in [('train','train'),('validation','valid'),('test','test')]:
 retained[split]=set()
 chats=list(map(json.loads,(old/'data'/f'{name}.jsonl').read_text().splitlines()))
 inputs={r['messages'][1]['content'] for r in chats}
 for r in map(json.loads,(B/f'{split}.jsonl').read_text().splitlines()):
  if r['input'] in inputs:retained[split].add(r['id'])
 assert len(retained[split])==len(chats)
source_manifests={name:json.loads((path/'manifest.json').read_text()) for name,path in [('BenchCAD',B),('CAD-Editor',C)]}
def patch(a,b):
 ed=[]
 for op,i,j,k,l in difflib.SequenceMatcher(a=a.splitlines(),b=b.splitlines(),autojunk=False).get_opcodes():
  if op!='equal':ed.append(dict(start=i,delete=j-i,insert=b.splitlines()[k:l]))
 return {'edits':ed}
counts={};rejected=[];splits={}
for split in ['train','validation','test']:
 rows=[]
 for source,path,rep in [('BenchCAD',B,'cadquery'),('CAD-Editor',C,'cad-editor-sequence')]:
  for r in map(json.loads,(path/f'{split}.jsonl').read_text().splitlines()):
   if source=='BenchCAD' and r['id'] not in retained[split]:continue
   if re.search(r'\b(pipe|circuit|resistor|piping)\b',r['instruction'],re.I):rejected.append(dict(id=r['id'],reason='excluded subject',source=source));continue
   code=r['code'] if source=='BenchCAD' else '\n'.join(r['original_sequence'].split())+'\n'
   target=r['edited_code'] if source=='BenchCAD' else '\n'.join(r['target'].split())+'\n'
   try:
    pt=patch(code,target);applied=apply(code,pt,rep);assert applied.rstrip()==target.rstrip()
   except Exception as e:rejected.append(dict(id=r['id'],source=source,reason=str(e)));continue
   item=dict(id=r['id'],source=source,representation=rep,component_id=r.get('component_id',r.get('family')),code=code,edited_code=target,instruction=r['instruction'],target=json.dumps(pt,separators=(',',':')),category=r.get('category',r.get('edit_type')),input=f'Representation: {rep}\nOriginal CAD (line indices are implicit):\n'+code+'Edit instruction:\n'+r['instruction'])
   if source=='BenchCAD':item.update(reference_step=str((B/r['reference_step']).resolve()) if r.get('reference_step') else None,reference_step_sha256=r.get('reference_step_sha256'))
   rows.append(item)
 splits[split]=rows;counts[split]={source:sum(r['source']==source for r in rows) for source in source_manifests}
 (OUT/f'{split}.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
 for source in source_manifests:
  groups=[{r['component_id'] for r in rs if r['source']==source} for rs in splits.values()]
  assert all(not a&b for i,a in enumerate(groups) for b in groups[i+1:])
manifest=dict(system=SYSTEM,status='prepared',sources=source_manifests,counts=counts,rejections=rejected,scope='Two online paired-edit datasets; native representations preserved. No claim that sequence syntax is geometric or FEM verification. No FEM test-case labels used for training.',cross_source_limit='CAD-Editor native sequences and BenchCAD Python programs have no shared design IDs; cross-source equivalent geometry is not proven absent.',files={s:hashlib.sha256((OUT/f'{s}.jsonl').read_bytes()).hexdigest() for s in splits})
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(counts);print('rejected',len(rejected))
