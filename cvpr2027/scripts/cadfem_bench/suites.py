"""Create balanced primary, separate calibration and reserved public-source suites.
No new targets/CAD, and no claim public-source reservation is contamination-proof.
"""
import argparse,collections,hashlib,json,shutil
from pathlib import Path

def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def lines(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(''.join(json.dumps(y)+'\n' for y in x))
def apply(p):
 pool=p/'evaluator/task-pool';pool.mkdir(parents=True,exist_ok=True)
 if not (pool/'tasks.jsonl').exists():
  shutil.copy2(p/'candidate/tasks.jsonl',pool/'tasks.jsonl');shutil.copy2(p/'evaluator/references.jsonl',pool/'references.jsonl')
 ts=jl(pool/'tasks.jsonl');refs={r['task_id']:r for r in jl(pool/'references.jsonl')};groups=collections.defaultdict(list)
 for t in ts:groups[t['engineering_family']].append(t)
 primary=[];cal=[]
 for fam,rows in sorted(groups.items()):
  if all(t['tier']=='control' for t in rows):cal.extend(rows);continue
  rows=sorted(rows,key=lambda t:(t['track']!='B',not t.get('readiness',{}).get('independently_reproduced',False),t['task_id']))
  primary.extend(rows[:5])
 ids={t['task_id'] for t in primary};cids={t['task_id'] for t in cal};primary_cad={i['sha256'] for t in primary for i in t['inputs'] if i['role']=='cad'}
 reserved=[];related=[]
 for t in ts:
  if t['task_id'] in ids or t['task_id'] in cids:continue
  if any(i['sha256'] in primary_cad for i in t['inputs'] if i['role']=='cad'):related.append(t)
  else:reserved.append(t)
 for name,rows in [('primary',primary),('calibration',cal),('reserved-public',reserved),('related-public',related)]:
  folder=p/'evaluator/suites'/name;lines(folder/'tasks.jsonl',rows);lines(folder/'references.jsonl',[refs[t['task_id']] for t in rows])
  # Geometry refs resolve inside the filtered evaluator directory. Copy only
  # their exact original bytes; the full original evidence remains in evaluator/.
  for t in rows:
   chk=refs[t['task_id']].get('geometry_check')
   if chk:
    rel=chk['reference_step'];src=p/'evaluator'/rel;dst=folder/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  if name!='primary':
   for t in rows:
    src=p/'candidate/tasks'/t['task_id'];dst=folder/'inputs'/t['task_id']
    if src.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(src),str(dst))
 lines(p/'candidate/tasks.jsonl',primary);lines(p/'evaluator/references.jsonl',[refs[t['task_id']] for t in primary])
 val=json.loads((p/'evaluator/validation.json').read_text());val.update(version='1.4',tasks=len(primary),graded_outputs=sum(len(refs[t['task_id']]['references']) for t in primary),by_track=dict(collections.Counter(t['track'] for t in primary)),by_family=dict(collections.Counter(t['family'] for t in primary)),engineering_families=len(set(t['engineering_family'] for t in primary)),reference_classes=dict(collections.Counter(v['ref_class'] for t in primary for v in refs[t['task_id']]['references'].values())),independently_reproduced_tasks=sum(bool(t.get('readiness',{}).get('independently_reproduced')) for t in primary))
 val['full_pool_geometry_gate_tasks']=val.get('full_pool_geometry_gate_tasks',val['geometry_gate_tasks']);val['geometry_gate_tasks']=sum(bool(refs[t['task_id']].get('geometry_check')) for t in primary)
 val['full_pool_convergence_band_tasks']=val.get('full_pool_convergence_band_tasks',val['convergence_band_tasks']);val['convergence_band_tasks']=sum(t['family']=='cycloidal-drive-components' for t in primary)
 val['suite_counts']={'primary':len(primary),'calibration':len(cal),'reserved_public':len(reserved),'related_public':len(related),'full_source_backed_pool':len(ts)};val['suite_policy']={'maximum_primary_tasks_per_family':5,'reserved_is_public_source':True,'contamination_resistant_private_holdout':False,'reservation_separation':'exact CAD hashes separated; related geometry/parametric family exposure remains possible'}
 save(p/'evaluator/validation.json',val);save(p/'evaluator/suite-manifest.json',{'version':'1.4',**val['suite_counts'],**val['suite_policy']})
 save(p/'evaluator/task-hashes.json',{t['task_id']:hashlib.sha256(json.dumps(t,sort_keys=True,separators=(',',':')).encode()).hexdigest() for t in primary})
 for f in [p/'evaluator/score.py',p/'scripts/cadfem_bench/score.py']:
  s=f.read_text().replace("'version': '1.1'","'version': '1.4'");f.write_text(s)
 f=p/'evaluator/REVIEW_PROTOCOL.md';f.write_text(f.read_text().replace('The pilot has zero independently reproduced reference tasks.',f"The primary suite has {val['independently_reproduced_tasks']} independently reproduced tasks; the full pool has 16. Reproduction is scoped to the stated quantities."))
 return val
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--package',type=Path,required=True);x=a.parse_args();print(json.dumps(apply(x.package),indent=2))
