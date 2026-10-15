from pathlib import Path
import json,shutil,hashlib,zipfile,collections
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'output/datasets/cadfem-challenge-trials';SRC=ROOT/'output/datasets/cadfem-astra-failure-cases-v0.1';OUT=ROOT/'output/datasets/cadfem-astra-failure-cases-v0.2'
f=json.loads((BASE/'failure-list.json').read_text());ledger=json.loads((BASE/'astra-recheck-20261015.json').read_text());rows=[x for x in f['cases'] if x['count_as_distinct_failure']]
latest=[dict(task_id=x['task_id'],**x.get('recheck_format',x.get('recheck_high',x.get('recheck3',x.get('recheck2',x.get('recheck',{'status':'not_rechecked'})))))) for x in rows];assert len(latest)==10 and all(x['status'] not in ['not_rechecked','awaiting_adjudication'] for x in latest)
latest=[dict(task_id=x['task_id'],**x['solver_audit']) if 'solver_audit' in x else result for x,result in zip(rows,latest)]
latest=[dict(task_id=x['task_id'],**x['recheck_solver_feedback']) if 'recheck_solver_feedback' in x else result for x,result in zip(rows,latest)]
known=sum(x['generation']['cost_usd_conservative'] for x in ledger['hunt_trials'] if x['generation'].get('cost_status')!='unknown_usage_reserved_preflight_maximum');reserved=sum(x['generation']['cost_usd_conservative'] for x in ledger['hunt_trials'] if x['generation'].get('cost_status')=='unknown_usage_reserved_preflight_maximum')
assert abs(known+reserved-ledger['session_cost_upper_bound_usd'])<1e-8
summary={'original_single_shot_failed_cases':10,'rechecked_distinct_cases':10,'latest_outcomes':dict(collections.Counter(x['status'] for x in latest)),'known_cost_usd_conservative':known,'unknown_usage_maximum_reservation_usd':reserved,'recheck_total_upper_bound_usd':known+reserved,'authorized_additional_budget_usd':5,'request_count':len(ledger['hunt_trials']),'cases':latest,'scope':'Medium/high reasoning and model-authored repairs, original task and execution feedback, hidden references, 600 seconds/6000 MB local sandbox. Not unrestricted full-agent evaluation.'}
additional=BASE/'astra-hardest-20261015.json'
if additional.exists():
 extra=json.loads(additional.read_text())
 summary['additional_solver_feedback_round']={'authorized_budget_usd':extra['budget_usd'],'cost_upper_bound_usd':extra['session_cost_upper_bound_usd'],'request_count':len(extra['hunt_trials']),'separate_from_earlier_budget':True}
(BASE/'recheck-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
f['count_semantics']='confirmed_distinct_cases records historical restricted-protocol failures, not current persistent failures';f['latest_recheck_summary']=summary;(BASE/'failure-list.json').write_text(json.dumps(f,indent=2)+'\n')
shutil.copytree(SRC,OUT,dirs_exist_ok=True)
def cp(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
audit=ROOT/'runs/girder-free-solver-audit-20261015'
if (audit/'audit.json').exists():
 for name in ['audit.json','README.md','buckle.inp','load.inc','buckle.dat','stdout.txt']:
  cp(audit/name,OUT/'evaluator/solver-audits/girder-20261015'/name)
for group in ['astra-recheck-20261015','astra-recheck2-20261015','astra-recheck3-20261015','astra-recheck-high-20261015','astra-recheck-format-20261015','astra-hardest-20261015']:
 for run in (ROOT/'runs'/group).glob('*'):
  if not run.is_dir():continue
  for rel in ['README.md','outcome.json','request.json','response.json','generation.json','protocol.json','model-patch.json','initial-patch-application-error.json','submission/main.py','replay/execution.json','replay/protocol.json','replay/sandbox.log','scoring/score.json']:
   if (run/rel).is_file():cp(run/rel,OUT/'evaluator/rechecks'/group/run.name/rel)
  for path in (run/'replay/outputs').rglob('*'):
   if path.is_file() and path.suffix in ['.json','.log','.stdout']:cp(path,OUT/'evaluator/rechecks'/group/run.name/'outputs'/path.relative_to(run/'replay/outputs'))
for name in ['failure-list.json','astra-recheck-20261015.json','recheck-summary.json','RECHECK_RESULTS.md']:cp(BASE/name,OUT/name)
if additional.exists():cp(additional,OUT/additional.name)
cp(SRC/'FAILURE_LIST.md',OUT/'ORIGINAL_FAILURE_LIST.md');cp(BASE/'RECHECK_RESULTS.md',OUT/'FAILURE_LIST.md')
manifest=json.loads((OUT/'manifest.json').read_text());manifest.pop('distinct_failed_cases',None);manifest.update(name='CADFEM Astra failure-case rechecks v0.2',historical_single_shot_failures=10,latest_recheck_outcomes=summary['latest_outcomes'],recheck_cost_upper_bound_usd=known+reserved);(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
lines=['# CADFEM Astra failure-case rechecks v0.2','','The ten historical low-budget failures were rechecked with medium reasoning, a high-reasoning girder review, and model-authored repairs. Original attempts remain preserved. The latest outcomes supersede any claim that all ten remain failures after feedback.','','Latest outcomes: '+json.dumps(summary['latest_outcomes'])+'.','',f"Known conservative cost estimate: ${known:.6f}; unresolved API usage reserved up to ${reserved:.6f}; total upper bound ${known+reserved:.6f} of $5 authorized.",'','See RECHECK_RESULTS.md and recheck-summary.json for per-case outcomes. Numerical passes still require trusted workflow review. Source-reference mismatches and resource/API limits are unresolved, not confirmed persistent physics failures. All tests are selected/adaptive diagnostics, not an unbiased overall Astra success rate.','','Candidate inputs and prompts are under candidate/. evaluator/ contains hidden references, original source evidence, code, patches and logs: never expose it to tested models. Full meshes and fields remain in the original local run paths recorded in execution inventories. Original v1.7 reference values remain unchanged.','','Mixed source licences restrict the bundle to local research; do not publish as a whole.']
(OUT/'README.md').write_text('\n'.join(lines)+'\n')
if additional.exists():
 with (OUT/'README.md').open('a') as handle:
  handle.write('\nAdditional solver-feedback round, separate authorization: '+json.dumps(summary['additional_solver_feedback_round'])+'. This is an assisted repair, not a fresh unassisted trial.\n')
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS');(OUT/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(OUT))+'\n' for p in files))
zpath=OUT.with_name(OUT.name+'.zip')
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,OUT.name+'/'+str(p.relative_to(OUT)))
with zipfile.ZipFile(zpath) as z:assert z.testzip() is None
for line in (OUT/'SHA256SUMS').read_text().splitlines():
 h,rel=line.split('  ',1);assert hashlib.sha256((OUT/rel).read_bytes()).hexdigest()==h
print(json.dumps({'summary':summary,'files_verified':len(files),'zip_bytes':zpath.stat().st_size},indent=2))
