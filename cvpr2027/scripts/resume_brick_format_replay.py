from pathlib import Path
import json,hashlib,ast,subprocess,shutil
ROOT=Path(__file__).resolve().parents[1];PKG=ROOT.parent/'cadfem-bench-v1.7';tid='A-FCVM-Plate_girder_EC3';r=ROOT/'runs/astra-recheck-format-20261015'/tid;prev=ROOT/'runs/astra-recheck-high-20261015'/tid
source=(prev/'submission/main.py').read_text();start=source.index('        f.write("*ELEMENT,TYPE=C3D20R,ELSET=BODY\\n")');end=source.index('        f.write("*MATERIAL',start);fragment=source[start:end];patch=json.loads((r/'response.txt').read_text());patched=fragment
for edit in patch['edits']:
 assert patched.count(edit['old'])==1
 patched=patched.replace(edit['old'],edit['new'],1)
assert source.count(fragment)==1
code=source.replace(fragment,patched,1);ast.parse(code);(r/'submission').mkdir(exist_ok=True);(r/'submission/main.py').write_text(code)
shutil.copy2(r/'generation.json',r/'initial-patch-application-error.json');g=json.loads((r/'generation.json').read_text());g.update(status='completed',patch_applied=True,repaired_sha256=hashlib.sha256(code.encode()).hexdigest(),patch_application_correction='Apply uniquely within supplied C3D20R source fragment; global duplicate writer line is outside repair scope');(r/'generation.json').write_text(json.dumps(g,indent=2)+'\n');(r/'model-patch.json').write_text(json.dumps(patch,indent=2)+'\n')
py=ROOT/'tmp/cq-env/bin/python';runner=PKG/'evaluator/sandbox_runner.py'
def run(args,log):
 with log.open('w') as f:rc=subprocess.run([str(x) for x in args],stdout=f,stderr=subprocess.STDOUT).returncode
 return rc
assert run([py,runner,'prepare','--package',PKG,'--job',r/'replay','--task-id',tid,'--submission',r/'submission','--model-id','gpt-6-astra','--run-id','format-'+tid,'--python',py],r/'prepare.log')==0
run([py,runner,'replay','--package',PKG,'--job',r/'replay','--python',py,'--extra-runtime',ROOT/'tmp/calculix-contact-env','--wall-seconds','600','--cpu-seconds','600','--ram-mb','6000'],r/'replay.log')
e=json.loads((r/'replay/execution.json').read_text());s=r/'scoring';s.mkdir(exist_ok=True);shutil.copytree(r/'replay/outputs',s/'submissions'/tid,dirs_exist_ok=True);shutil.copy2(r/'submission/main.py',s/'submissions'/tid/'main.py')
for name,src in [('tasks',PKG/'candidate/tasks.jsonl'),('references',PKG/'evaluator/references.jsonl')]:
 (s/(name+'.jsonl')).write_text(''.join(json.dumps(t)+'\n' for t in map(json.loads,src.read_text().splitlines()) if t['task_id']==tid))
run([py,PKG/'evaluator/score.py','--refs',s/'references.jsonl','--tasks',s/'tasks.jsonl','--submissions',s/'submissions','--run-id','format-'+tid,'--out',s/'score.json'],r/'score.log')
rec=json.loads((r/'outcome.json').read_text());rec.update(generation=g,status='awaiting_adjudication',execution={k:e.get(k) for k in ['exit_code','elapsed_seconds','termination_reason','execution_verified','frozen_inputs_unchanged']},score_path=str(s/'score.json'))
if (r/'replay/outputs/results.json').exists():rec['results']=json.loads((r/'replay/outputs/results.json').read_text())
(r/'outcome.json').write_text(json.dumps(rec,indent=2)+'\n');ledger=ROOT/'output/datasets/cadfem-challenge-trials/astra-recheck-20261015.json';d=json.loads(ledger.read_text());d['hunt_trials']=[rec if x['report']==rec['report'] else x for x in d['hunt_trials']];ledger.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(rec))
