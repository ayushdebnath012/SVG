"""Export model-visible primary tasks only. No model API call is made."""
import argparse,hashlib,json,shutil
from pathlib import Path

def export(package,out,model_id,run_id,task_ids=None):
 if out.exists():raise ValueError('fresh model export folder required')
 tasks=[json.loads(l) for l in (package/'candidate/tasks.jsonl').read_text().splitlines() if l.strip()]
 if task_ids:
  unknown=set(task_ids)-{t['task_id'] for t in tasks}
  if unknown:raise ValueError('unknown primary task IDs: '+str(sorted(unknown)))
  tasks=[t for t in tasks if t['task_id'] in task_ids]
 out.mkdir(parents=True)
 for t in tasks:
  d=out/'tasks'/t['task_id'];d.mkdir(parents=True)
  (d/'task.json').write_text(json.dumps(t,indent=2)+'\n');(d/'prompt.txt').write_text(t['prompt']+'\n')
  for i in t['inputs']:
   f=package/'candidate'/i['path'];rel=Path(i['path']).relative_to(Path('tasks')/t['task_id']);dest=d/rel
   if f.is_symlink() or hashlib.sha256(f.read_bytes()).hexdigest()!=i['sha256']:raise ValueError('candidate input hash mismatch')
   dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
 for name in ['README.md','submission.schema.json']:shutil.copy2(package/'candidate'/name,out/name)
 (out/'tasks.jsonl').write_text(''.join(json.dumps(t)+'\n' for t in tasks))
 files={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()}
 manifest={'release':json.loads((package/'evaluator/validation.json').read_text())['version'],'model_id':model_id,'run_id':run_id,'tasks':len(tasks),'task_ids':[t['task_id'] for t in tasks],'export_file_sha256':files,'task_set_sha256':hashlib.sha256(json.dumps(tasks,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'generation_status':'prepared_not_executed','model_api_calls':0,'evaluator_answers_exported':False,'source_contamination':'public-source exposure possible; no guarantee of unseen tasks'}
 (out/'generation-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--package',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--model-id',required=True);a.add_argument('--run-id',required=True);a.add_argument('--task-id',action='append');x=a.parse_args();m=export(x.package.resolve(),x.out.resolve(),x.model_id,x.run_id,x.task_id);print(json.dumps({k:m[k] for k in ['release','model_id','run_id','tasks','model_api_calls','evaluator_answers_exported']},indent=2))
