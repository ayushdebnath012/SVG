"""Release checks against actual suites and retained sandbox/field evidence."""
import argparse,collections,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path

def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(p):
 t=jl(p/'candidate/tasks.jsonl');r=jl(p/'evaluator/references.jsonl');v=json.loads((p/'evaluator/validation.json').read_text());assert [x['task_id'] for x in t]==[x['task_id'] for x in r];assert len(t)==41
 assert max(collections.Counter(x['engineering_family'] for x in t).values())<=5
 classes=dict(collections.Counter(q['ref_class'] for x in r for q in x['references'].values()));assert sum(classes.values())==v['graded_outputs']==86;assert classes==v['reference_classes']
 n=0
 for x in t:
  for i in x['inputs']:
   f=p/'candidate'/i['path'];assert sha(f)==i['sha256'] and f.stat().st_size==i['bytes'];n+=1
 groups={name:jl(p/'evaluator/suites'/name/'tasks.jsonl') for name in ['primary','calibration','reserved-public','related-public']};ids=[x['task_id'] for rows in groups.values() for x in rows];assert len(ids)==len(set(ids))==126
 core={i['sha256'] for x in groups['primary'] for i in x['inputs'] if i['role']=='cad'};reserve={i['sha256'] for x in groups['reserved-public'] for i in x['inputs'] if i['role']=='cad'};assert not core&reserve
 for name,rows in groups.items():
  if name=='primary':continue
  for x in rows:
   assert not (p/'candidate/tasks'/x['task_id']).exists();assert (p/'evaluator/suites'/name/'inputs'/x['task_id']).exists()
 # Source evidence remains exact.
 evidence=jl(p/'evaluator/evidence-manifest.jsonl')
 for x in evidence:assert sha(p/'evaluator'/x['path'])==x['sha256']
 with tempfile.TemporaryDirectory(prefix='v14-score-') as td:
  td=Path(td)
  for x in r:
   f=td/'answers'/x['task_id']/'results.json';f.parent.mkdir(parents=True);f.write_text(json.dumps({'outputs':{k:q['value'] for k,q in x['references'].items()}}))
  out=td/'score.json';cmd=[sys.executable,str(p/'evaluator/score.py'),'--refs',str(p/'evaluator/references.jsonl'),'--tasks',str(p/'candidate/tasks.jsonl'),'--submissions',str(td/'answers'),'--run-id','v14-probe','--out',str(out)];proc=subprocess.run(cmd,capture_output=True,text=True);assert proc.returncode==0,proc.stderr
  result=json.loads(out.read_text());assert result['version']=='1.4';assert result['summary']['all']['numerical_passed']==41 and result['summary']['all']['passed']==0;assert result['summary']['reproduced_tasks_only']['tasks']==10
  # A malformed single response does not invalidate the other 40 scores.
  (td/'answers'/r[0]['task_id']/'results.json').write_text('{"outputs":null}');proc=subprocess.run(cmd,capture_output=True,text=True);assert proc.returncode==0,proc.stderr;assert json.loads(out.read_text())['summary']['all']['numerical_passed']==40
 rt=p/'evaluator/runtime-validation';probe=json.loads((rt/'probe-job-hardened-003/outputs/probe.json').read_text());assert len(probe)==6 and all(x=='denied' for x in probe.values())
 assert json.loads((rt/'probe-job-hardened-003/execution.json').read_text())['execution_verified']
 assert json.loads((rt/'solver-job-hardened/execution.json').read_text())['execution_verified']
 assert json.loads((rt/'timeout-job/execution.json').read_text())['termination_reason']=='wall_time_limit'
 good=json.loads((rt/'solver-job-002/field-check.json').read_text());bad=json.loads((rt/'tampered-field-check.json').read_text());assert good['field_equilibrium_passed'] and not bad['field_equilibrium_passed']
 geo=json.loads((rt/'geometry-checks-v14.json').read_text());assert len([k for k in geo if k.startswith('B-')])==6;assert 'radius mismatch' in geo['wrong_hole_9_8_mm_rejected']['error']
 return {'version':'1.4','primary_tasks':41,'graded_outputs':86,'primary_input_files_checked':n,'maximum_tasks_per_family':5,'suite_counts':{name:len(rows) for name,rows in groups.items()},'exact_CAD_hash_split_disjoint':True,'evidence_files_hash_checked':len(evidence),'answers_only_numerical_passed':41,'answers_only_workflow_passed':0,'malformed_response_rejected_without_crash':True,'reproduced_summary_tasks':10,'sandbox_denial_probes':probe,'actual_sandboxed_solver_execution':True,'timeout_enforced':True,'trusted_field_residual_relative':good['source_operator_residual_relative'],'tampered_field_rejected':True,'geometry_gates_positive_checked':6,'wrong_hole_radius_rejected':True,'model_calls':0,'human_expert_runs':0,'private_contamination_resistant_holdout':False}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--package',type=Path,required=True);x=a.parse_args();r=verify(x.package);(x.package/'evaluator/verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
