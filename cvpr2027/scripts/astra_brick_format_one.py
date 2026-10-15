"""Run exactly one task, charge ledger before sandbox, never retry an API call."""
from pathlib import Path
import sys,json,subprocess,shutil
ROOT=Path(__file__).resolve().parents[1];PKG=ROOT.parent/'cadfem-bench-v1.7';tid=sys.argv[1]
r=ROOT/'runs/astra-recheck-format-20261015'/tid
ledger=ROOT/'output/datasets/cadfem-challenge-trials/astra-recheck-20261015.json'
def run(args,log):
 with log.open('w') as f:return subprocess.run([str(x) for x in args],stdout=f,stderr=subprocess.STDOUT).returncode
r.mkdir(parents=True,exist_ok=True)
if (r/'generation.json').exists():raise SystemExit('Existing attempt; manual inspection required, no retry')
rc=run([sys.executable,ROOT/'scripts/astra_brick_format_generate.py',tid],r/'generation.log')
if not (r/'generation.json').exists():raise SystemExit((r/'generation.log').read_text())
g=json.loads((r/'generation.json').read_text());d=json.loads(ledger.read_text());cost=g.get('cost_usd_conservative')
if cost is None:
 pr=json.loads((r/'protocol.json').read_text());cost=pr['call_cost_upper_bound_including_possible_cache_write'];g['cost_usd_conservative']=cost;g['cost_status']='unknown_usage_reserved_preflight_maximum';(r/'generation.json').write_text(json.dumps(g,indent=2)+'\n')
d['session_cost_upper_bound_usd']+=cost
rec={'task_id':tid,'report':str(r/'README.md'),'generation':g,'status':'generated','protocol':'medium-reasoning connectivity-format-only repair of high-reasoning solver, 1800-token cap'}
d.setdefault('hunt_trials',[]).append(rec);ledger.write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({'task':tid,'generation':g,'cumulative_cost':d['session_cost_upper_bound_usd']}),flush=True)
if g.get('finish_reason')!='stop':rec['status']='inconclusive_token_budget' if g.get('finish_reason')=='length' else 'inconclusive_api_error'
elif not g.get('patch_applied'):rec['status']='inconclusive_patch_error'
else:
 py=ROOT/'tmp/cq-env/bin/python';runner=PKG/'evaluator/sandbox_runner.py'
 rc=run([py,runner,'prepare','--package',PKG,'--job',r/'replay','--task-id',tid,'--submission',r/'submission','--model-id','gpt-6-astra','--run-id','recheck-'+tid,'--python',py],r/'prepare.log')
 if rc:rec['status']='inconclusive_runner_prepare_error'
 else:
  rc=run([py,runner,'replay','--package',PKG,'--job',r/'replay','--python',py,'--extra-runtime',ROOT/'tmp/calculix-contact-env','--wall-seconds','600','--cpu-seconds','600','--ram-mb','6000'],r/'replay.log')
  e=json.loads((r/'replay/execution.json').read_text());rec['execution']={k:e.get(k) for k in ['exit_code','elapsed_seconds','termination_reason','execution_verified','frozen_inputs_unchanged']}
  s=r/'scoring';s.mkdir(exist_ok=True);shutil.copytree(r/'replay/outputs',s/'submissions'/tid,dirs_exist_ok=True);shutil.copy2(r/'submission/main.py',s/'submissions'/tid/'main.py')
  for name,src in [('tasks',PKG/'candidate/tasks.jsonl'),('references',PKG/'evaluator/references.jsonl')]:
   (s/(name+'.jsonl')).write_text(''.join(json.dumps(t)+'\n' for t in map(json.loads,src.read_text().splitlines()) if t['task_id']==tid))
  refrow=json.loads((s/'references.jsonl').read_text())
  if refrow.get('geometry_check'):
   rel=Path(refrow['geometry_check']['reference_step']);(s/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PKG/'evaluator'/rel,s/rel)
  rc=run([py,PKG/'evaluator/score.py','--refs',s/'references.jsonl','--tasks',s/'tasks.jsonl','--submissions',s/'submissions','--run-id','recheck-'+tid,'--out',s/'score.json'],r/'score.log')
  rec['status']='awaiting_adjudication';rec['score_path']=str(s/'score.json')
  if (r/'replay/outputs/results.json').exists():
   try:rec['results']=json.loads((r/'replay/outputs/results.json').read_text())
   except Exception:rec['results']='malformed_json'
(r/'outcome.json').write_text(json.dumps(rec,indent=2)+'\n')
d=json.loads(ledger.read_text());d['hunt_trials']=[rec if x['report']==rec['report'] else x for x in d['hunt_trials']];ledger.write_text(json.dumps(d,indent=2)+'\n')
(r/'README.md').write_text('# '+tid+' — Astra single-shot trial\n\nStatus: '+rec['status']+'\n\nSee outcome.json, generation.json, replay/execution.json, and scoring/score.json for evidence. This attempt uses low reasoning and no repair; not comparable to multi-turn agent trials.\n')
print(json.dumps(rec),flush=True)
