"""Complete v1.6 package: source-only primary pool, cap 8, audited contact supplement.
No geometry/targets are generated. Existing B-task evaluator reconstructions remain labeled.
"""
import argparse,collections,hashlib,json,shutil
from pathlib import Path
from breadth_v16 import add as add_complex_sources
VERSION='1.6';SUITES=['primary','calibration','reserved-public','related-public']
def jl(p):return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
def lines(p,rows):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
def save(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+'\n')
def build(source,out,contact,breadth_data,runtime_probe):
 if out.exists():raise ValueError('fresh release folder required')
 shutil.copytree(source,out)
 ev=out/'evaluator';historical=ev/'history/v1.5';historical.mkdir(parents=True)
 for f in ['README.md','evaluator/DATASET_CARD.md','evaluator/validation.json','evaluator/verification.json','evaluator/suite-manifest.json']:
  q=out/f;dest=historical/f;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(q,dest)
 tasks=jl(ev/'task-pool/tasks.jsonl');refs={r['task_id']:r for r in jl(ev/'task-pool/references.jsonl')}
 generated=[t for t in tasks if t['family']=='interface-crack-fracture'];generated_ids={t['task_id'] for t in generated}
 source_tasks=[t for t in tasks if t['task_id'] not in generated_ids]
 oldprimary=jl(source/'candidate/tasks.jsonl');primary=[t for t in oldprimary if t['task_id'] not in generated_ids];cal=jl(source/'evaluator/suites/calibration/tasks.jsonl')
 chosen={t['task_id'] for t in primary+cal};groups=collections.defaultdict(list)
 for t in source_tasks:
  if t['task_id'] not in chosen:groups[t['engineering_family']].append(t)
 counts=collections.Counter(t['engineering_family'] for t in primary)
 primary_cad={i['sha256'] for t in primary for i in t['inputs'] if i['role']=='cad'}
 for fam,rows in sorted(groups.items()):
  # Preserve the former primary tasks; add source cases using readiness then fixed ID hash.
  rows.sort(key=lambda t:(not t.get('readiness',{}).get('independently_reproduced',False),hashlib.sha256(t['task_id'].encode()).hexdigest()))
  for t in rows:
   if counts[fam]>=8:break
   hashes={i['sha256'] for i in t['inputs'] if i['role']=='cad'}
   if hashes&primary_cad:continue
   primary.append(t);chosen.add(t['task_id']);counts[fam]+=1;primary_cad.update(hashes)
 primary.sort(key=lambda t:t['task_id']);assert len(primary)>=50 and max(counts.values())<=8
 reserve=[];related=[]
 for t in source_tasks:
  if t['task_id'] in chosen:continue
  (related if any(i['sha256'] in primary_cad for i in t['inputs'] if i['role']=='cad') else reserve).append(t)
 def input_dir(tid):
  d=source/'candidate/tasks'/tid
  if d.exists():return d
  for name in SUITES[1:]:
   d=source/'evaluator/suites'/name/'inputs'/tid
   if d.exists():return d
  raise ValueError('missing original task inputs '+tid)
 # Reconstruct only placement of existing files; their bytes/hashes remain unchanged.
 shutil.rmtree(out/'candidate/tasks');(out/'candidate/tasks').mkdir()
 for name in SUITES:
  d=ev/'suites'/name
  if d.exists():shutil.rmtree(d)
 for name,rows in [('primary',primary),('calibration',cal),('reserved-public',reserve),('related-public',related)]:
  d=ev/'suites'/name;lines(d/'tasks.jsonl',rows);lines(d/'references.jsonl',[refs[t['task_id']] for t in rows])
  for t in rows:
   if t['inputs']:
    dest=out/'candidate/tasks'/t['task_id'] if name=='primary' else d/'inputs'/t['task_id'];shutil.copytree(input_dir(t['task_id']),dest)
   chk=refs[t['task_id']].get('geometry_check')
   if chk:
    dst=d/chk['reference_step'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ev/chk['reference_step'],dst)
 lines(out/'candidate/tasks.jsonl',primary);lines(ev/'references.jsonl',[refs[t['task_id']] for t in primary])
 held_t=jl(out/'held/tasks.jsonl');held_r=jl(out/'held/references.jsonl')
 for t in generated:
  tid=t['task_id'];t['status']='held';t['hold_reason']='Source specification reconstructed locally as supplied CAD; some G targets locally derived from published factors. Excluded from original-web-CAD-only scoring.'
  r=refs[tid];r['status']='held';r['hold_reason']=t['hold_reason']
  for q in r['references'].values():q['graded']=False
  held_t.append(t);held_r.append(r);dst=out/'held/inputs'/tid;shutil.copytree(input_dir(tid),dst)
 lines(out/'held/tasks.jsonl',held_t);lines(out/'held/references.jsonl',held_r)
 lines(ev/'task-pool/tasks.jsonl',source_tasks);lines(ev/'task-pool/references.jsonl',[refs[t['task_id']] for t in source_tasks])
 shutil.copytree(contact,ev/'source-review/contact-validated-followup',dirs_exist_ok=True)
 reviewed=add_complex_sources(breadth_data,out)
 shutil.copytree(runtime_probe,ev/'runtime-validation/v16-final-runtime-probe')
 assets=Path(__file__).with_name('assets_v16')
 for rel in ['README.md','candidate/README.md','evaluator/DATASET_CARD.md','evaluator/REVIEW_PROTOCOL.md','evaluator/run-manifest-template.json']:
  target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(assets/rel,target)
 shutil.copy2(assets/'evaluator/runtime-validation/model-export-check.json',ev/'runtime-validation/model-export-check.json')
 for name in ['release_v16.py','breadth_v16.py','verify_v16.py','report_v16.py','export_run.py','sandbox_runner_v16.py','finalize_v16.py']:
  f=Path(__file__).with_name(name)
  if f.exists():shutil.copy2(f,out/'scripts/cadfem_bench'/name)
 for src,dst in [('export_run.py','export_run.py'),('sandbox_runner_v16.py','sandbox_runner.py')]:
  shutil.copy2(Path(__file__).with_name(src),ev/dst)
 # Keep admitted evidence unchanged; additional contact evidence is not a target source.
 man=jl(ev/'evidence-manifest.jsonl');evrefs=[refs[t['task_id']] for t in primary]
 val={'version':VERSION,'tasks':len(primary),'graded_outputs':sum(len(r['references']) for r in evrefs),'by_track':dict(collections.Counter(t['track'] for t in primary)),'by_family':dict(collections.Counter(t['family'] for t in primary)),'by_engineering_family':dict(counts),'engineering_families':len(counts),'held_tasks':len(held_t),'unadmitted_contact_pairs':1,'excluded_local_targets':190,'reference_classes':dict(collections.Counter(q['ref_class'] for r in evrefs for q in r['references'].values())),'independently_reproduced_tasks':sum(bool(t.get('readiness',{}).get('independently_reproduced')) for t in primary),'model_calls':0,'source_evidence_files':len(man),'source_evidence_bytes':sum(x['bytes'] for x in man),'geometry_gate_tasks':sum(bool(r.get('geometry_check')) for r in evrefs),'additional_complex_source_collections':len(reviewed),'suite_counts':{'primary':len(primary),'calibration':len(cal),'reserved_public':len(reserve),'related_public':len(related),'full_source_backed_pool':len(source_tasks)},'suite_policy':{'maximum_primary_tasks_per_family':8,'reserved_is_public_source':True,'contamination_resistant_private_holdout':False,'reservation_separation':'exact source CAD hashes disjoint; public pretraining and related-family exposure remain possible'},'readiness':'source-backed pilot; reproduced subset separately reported; remaining tolerances provisional','generated_v15_fracture_tasks_removed_from_active_pool':len(generated),'new_CAD_or_targets_generated':0}
 save(ev/'validation.json',val);save(ev/'suite-manifest.json',{'version':VERSION,**val['suite_counts'],**val['suite_policy']});save(ev/'task-hashes.json',{t['task_id']:hashlib.sha256(json.dumps(t,sort_keys=True,separators=(',',':')).encode()).hexdigest() for t in primary});(ev/'reproduced-task-ids.txt').write_text(''.join(t['task_id']+'\n' for t in primary if t.get('readiness',{}).get('independently_reproduced')))
 registries=[]
 for url in sorted({t['source']['url'] for t in source_tasks}):
  pool=[t for t in source_tasks if t['source']['url']==url];pr=[t for t in primary if t['source']['url']==url];registries.append({'source':pool[0]['source'],'full_pool_tasks':len(pool),'primary_tasks':len(pr),'primary_reproduced_tasks':sum(bool(t.get('readiness',{}).get('independently_reproduced')) for t in pr),'families':sorted({t['engineering_family'] for t in pool}),'status':'source_backed_pilot'})
 lines(ev/'registry.jsonl',registries)
 protocol=json.loads((ev/'evaluation-protocol.json').read_text());protocol.update(release=VERSION,primary_suite=f'{len(primary)} tasks, cap 8 per family',calibration=f'{len(cal)} separate tasks',reserved_suite=f'{len(reserve)} reserved public-source cases; not contamination-proof');save(ev/'evaluation-protocol.json',protocol)
 save(ev/'limitations-status.json',{'release_packaging':'complete','web_source_integrity':'verified at packaging; no new geometry or targets synthesized','geometry_origin':'supplied-CAD track uses source CAD or documented conversion; existing B-task hidden specification reconstructions remain evaluator-only','balance':'primary family cap8; tasks are not all independent geometries/problems','reproduction':f"{val['independently_reproduced_tasks']} of {len(primary)} primary tasks; qualified subset separately scored",'contact':'source correspondence and shell gate resolved; five-mesh study fails admission; held evidence only','complex_physics':'published plastic-collapse case admitted; locally generated fracture CAD removed; no admitted frictional contact, forming, crash or fatigue','workflow_automation':'sandbox replay tested; full geometry/setup/fields/convergence review remains required','frontier_trials':'none; runner prepared in accordance with prior user instruction','private_holdout':'public source reservation cannot establish private uncontaminated data','redistribution':'mixed source rights; local research package, no blanket public redistribution permission'})
 return val
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--contact',type=Path,required=True);a.add_argument('--breadth-data',type=Path,required=True);a.add_argument('--runtime-probe',type=Path,required=True);x=a.parse_args();print(json.dumps(build(x.source.resolve(),x.out.resolve(),x.contact.resolve(),x.breadth_data.resolve(),x.runtime_probe.resolve()),indent=2))
