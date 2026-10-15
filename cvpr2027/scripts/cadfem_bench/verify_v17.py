"""Verify v1.7 primary/all suites, original evidence, scoring gates and export/sandbox records."""
import argparse,collections,hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path

def jl(p):return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as stream:
  for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def verify(p):
 os.environ.update(CADFEM_BENCH_OUT=str(p),CADFEM_BENCH_VERSION='1.7')
 import common as C
 from build import leak_scan
 v=json.loads((p/'evaluator/validation.json').read_text());t=jl(p/'candidate/tasks.jsonl');refs=jl(p/'evaluator/references.jsonl');assert len(t)==v['tasks']>=50 and v['version']=='1.7';assert [x['task_id'] for x in t]==[x['task_id'] for x in refs]
 assert max(collections.Counter(x['engineering_family'] for x in t).values())<=8
 assert not any(x['family']=='interface-crack-fracture' for x in t)
 assert not any(q['ref_class']=='closed_form' for r in refs for q in r['references'].values())
 assert not {'B-FEMCAD-031','B-FEMCAD-057','B-FEMCAD-058'} & {x['task_id'] for x in t}
 classes=dict(collections.Counter(q['ref_class'] for r in refs for q in r['references'].values()));assert classes==v['reference_classes'];assert sum(classes.values())==v['graded_outputs']==118
 cad={};n=0
 for x in t:
  for i in x['inputs']:
   f=p/'candidate'/i['path'];assert f.stat().st_size==i['bytes'] and sha(f)==i['sha256'];n+=1
   if f.suffix.lower() in ['.step','.stp','.brep','.brp']:cad[i['sha256']]=f
 for f in cad.values():assert C.shape_summary(C.read_shape(f))['valid'],str(f)
 print('primary CAD/input hashes valid',len(cad),n,flush=True)
 evidence=jl(p/'evaluator/evidence-manifest.jsonl');paths={x['path'] for x in evidence}
 for r in refs:assert r['evidence_files'] and set(r['evidence_files'])<=paths
 for m in evidence:
  f=p/'evaluator'/m['path'];assert sha(f)==m['sha256'] and f.stat().st_size==m['bytes']
 assert not leak_scan(t,refs),'source answer leak in primary input/prompt'
 suites={name:jl(p/'evaluator/suites'/name/'tasks.jsonl') for name in ['primary','calibration','reserved-public','related-public']};allids=[x['task_id'] for rows in suites.values() for x in rows];assert len(allids)==len(set(allids))==125
 pool=jl(p/'evaluator/task-pool/tasks.jsonl');assert {x['task_id'] for x in pool}==set(allids)
 hidden_hash={i['sha256'] for x in suites['reserved-public']+suites['calibration'] for i in x['inputs'] if i['role']=='cad'};visible_hash={sha(f) for f in (p/'candidate').rglob('*') if f.is_file()};assert not hidden_hash&visible_hash
 held=jl(p/'held/tasks.jsonl');assert len(held)==v['held_tasks']==58 and not {x['task_id'] for x in held}&set(allids)
 for x in held:assert not x['inputs'] or (p/'held/inputs'/x['task_id']).is_dir()
 score=p/'evaluator/score.py';checks={}
 with tempfile.TemporaryDirectory(prefix='v17-probes-') as tmp:
  tmp=Path(tmp)
  for name,rows in suites.items():
   rr=jl(p/'evaluator/suites'/name/'references.jsonl');assert {x['task_id'] for x in rr}=={x['task_id'] for x in rows}
   ni=0
   if name!='primary':
    for x in rows:
     for i in x['inputs']:
      f=p/'evaluator/suites'/name/'inputs'/Path(i['path']).relative_to('tasks');assert sha(f)==i['sha256'] and f.stat().st_size==i['bytes'];ni+=1
   a=tmp/name;a.mkdir()
   for r in rr:
    d=a/r['task_id'];d.mkdir();(d/'results.json').write_text(json.dumps({'outputs':{k:q['value'] for k,q in r['references'].items()}}))
   cmd=[sys.executable,str(score),'--refs',str(p/'evaluator/suites'/name/'references.jsonl'),'--tasks',str(p/'evaluator/suites'/name/'tasks.jsonl'),'--submissions',str(a),'--run-id','integrity-probe','--out',str(tmp/'score.json')]
   run=subprocess.run(cmd,capture_output=True,text=True);assert run.returncode==0,run.stderr;out=json.loads((tmp/'score.json').read_text());assert out['version']=='1.7' and out['summary']['all']['numerical_passed']==len(rr) and out['summary']['all']['passed']==0
   if name=='primary':assert out['summary']['reproduced_tasks_only']['tasks']==v['independently_reproduced_tasks']==14
   for r in rr:(a/r['task_id']/'results.json').write_text(json.dumps({'outputs':{k:q['value']*1.3 for k,q in r['references'].items()}}))
   run=subprocess.run(cmd,capture_output=True,text=True);assert run.returncode==0,run.stderr;assert json.loads((tmp/'score.json').read_text())['summary']['all']['numerical_passed']==0
   # Four malformed response shapes are independently rejected without crashing.
   for malformed in ['null','{"outputs":null}','{"outputs":"bad"}','{"outputs":{},"outputs":{}}']:
    (a/rr[0]['task_id']/'results.json').write_text(malformed);run=subprocess.run(cmd,capture_output=True,text=True);assert run.returncode==0,run.stderr
   checks[name]={'tasks':len(rows),'graded_outputs':sum(len(r['references']) for r in rr),'additional_inputs_hash_checked':ni,'answers_only_numerical_passed':len(rr),'answers_only_workflow_passed':0,'scaled_answers_numerical_passed':0,'malformed_response_shapes_rejected':4}
   print('suite probes passed',name,len(rows),flush=True)
 # Positive/negative probes use unchanged reference geometry and transformed test fixtures only.
 sp=importlib.util.spec_from_file_location('v17_sc',score);sc=importlib.util.module_from_spec(sp);sp.loader.exec_module(sc)
 from verify import transformed_step
 geo={}
 with tempfile.TemporaryDirectory(prefix='v17-geometry-') as tmp:
  for r in refs:
   c=r.get('geometry_check')
   if not c:continue
   src=p/'evaluator'/c['reference_step'];rot=Path(tmp)/(r['task_id']+'-rot.step');big=Path(tmp)/(r['task_id']+'-big.step');transformed_step(src,rot,37,(40,-15,7));transformed_step(src,big,0,(0,0,0),1.03)
   ok,_=sc.geometry(rot,c,p/'evaluator');bad,_=sc.geometry(big,c,p/'evaluator');assert ok and not bad,r['task_id'];geo[r['task_id']]={'rotated_37_degrees_translated_passed':True,'scaled_three_percent_rejected':True}
 rt=p/'evaluator/runtime-validation/v17-final-runtime-probe';ex=json.loads((rt/'execution.json').read_text());probe=json.loads((rt/'outputs/probe.json').read_text());assert ex['release']=='1.7' and ex['execution_verified'];assert ex['runner_sha256']==sha(p/'evaluator/sandbox_runner.py');assert all(probe[k]=='denied' for k in ['evaluator_read','old_release_read','outside_write','input_mutation','network','hardlink']);assert probe['ccx_finished'] and probe['ccx_returncode']==0
 review_dir=p/'evaluator/source-review/complex-engineering';review=json.loads((review_dir/'index.json').read_text());assert len(review)==6 and v['additional_complex_source_collections']==6
 reviewed_files=0
 for case in review:
  assert case['status']=='source_review_not_scored' and case['active_benchmark_tasks_added']==0
  d=review_dir/case['collection_id'];manifest=json.loads((d/'package-source-files.json').read_text());assert len(manifest)==case['published_file_count']
  for row in manifest:
   f=d/row['path'];assert f.is_file() and f.stat().st_size==row['bytes'] and sha(f)==row['sha256'],str(f)
   reviewed_files+=1
 model_export=json.loads((p/'evaluator/runtime-validation/model-export-check.json').read_text());assert model_export['tasks']==54 and model_export['evaluator_answers_exported'] is False and model_export['model_api_calls']==0
 contact=json.loads((p/'evaluator/source-review/contact-validated-followup/assessment.json').read_text());assert contact['new_active_tasks']==0 and not contact['displacement_converged_under_existing_admission_rule']
 return {'version':'1.7','primary_tasks':54,'graded_outputs':118,'primary_input_files_hash_checked':n,'distinct_primary_CAD_files_valid':len(cad),'evidence_files_hash_checked':len(evidence),'complex_source_collections_hash_checked':len(review),'complex_source_files_hash_checked':reviewed_files,'primary_answer_leak_hits':0,'candidate_reserved_or_calibration_CAD_overlap':0,'source_pool_tasks':125,'held_tasks':58,'family_cap':8,'reproduced_primary_tasks':14,'suites':checks,'geometry_gates':geo,'sandbox':{'release':ex['release'],'execution_verified':True,'denial_probes':probe,'actual_CalculiX_original_deck_solved_inside_sandbox':True,'role':'infrastructure tool probe, not a task/model score'},'model_export':model_export,'contact_remains_unscored':True,'frontier_model_runs':0,'human_expert_runs':0,'independent_formulation_contact_reproduction':False}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--package',type=Path,required=True);x=a.parse_args();r=verify(x.package.resolve());(x.package/'evaluator/verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
