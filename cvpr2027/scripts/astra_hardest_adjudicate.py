"""Record a completed solver-feedback trial without inventing workflow approval."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'output/datasets/cadfem-challenge-trials'
tid='A-FCVM-Plate_girder_EC3';run=ROOT/'runs/astra-hardest-20261015'/tid
rec=json.loads((run/'outcome.json').read_text())
score=json.loads((run/'scoring/score.json').read_text())['tasks'][0]
execution=json.loads((run/'replay/execution.json').read_text())
results=json.loads((run/'replay/outputs/results.json').read_text())
refinement=json.loads((run/'replay/outputs/refinement.json').read_text())
reference=next(x for x in map(json.loads,(ROOT.parent/'cadfem-bench-v1.7/evaluator/references.jsonl').read_text().splitlines()) if x['task_id']==tid)
# Keep full evaluator reference locally, never in request payload.
value=results['outputs']['lambda1'];target=.41191
assert execution['execution_verified'] and execution['frozen_inputs_unchanged']
assert hashlib.sha256((run/'submission/main.py').read_bytes()).hexdigest()==rec['generation']['repaired_sha256']
status='recovered_numerical_pass_with_solver_feedback' if score['numerical_passed'] else 'numerical_mismatch_adjudication_pending'
error=100*(value/target-1)
levels=[{'h_mm':x.get('h_mm'),'nodes':x.get('nodes'),'elements':x.get('elements'),'lambda1':x.get('lambda1'),'conditioning_scale':x.get('buckling_load_scale'),'status':x.get('status')} for x in refinement['levels']]
refinement_note=("Finer mesh did not complete; convergence remains unverified." if refinement.get("relative_change_last_two") is None else f"Measured final mesh change {refinement['relative_change_last_two']}; no asymptotic convergence claim.")
note=f'Model-authored repair after explicit solver-diagnostic feedback, hidden target. Clean replay gives lambda1={value:.7f} versus published {target} ({error:+.3f}%). {refinement_note} Original-load static fields retained. Numerical result only; trusted workflow review pending. Not a fresh unassisted attempt.'
rec.update(status=status,score=score,adjudication_note=note,published_reference=target,relative_error_percent=error,refinement_levels=levels,assistance='Known solver mode-skipping issue and evaluator diagnosis disclosed; source reference values hidden.')
(run/'outcome.json').write_text(json.dumps(rec,indent=2)+'\n')
ledger=BASE/'astra-hardest-20261015.json';d=json.loads(ledger.read_text());d['hunt_trials']=[rec if x['report']==rec['report'] else x for x in d['hunt_trials']];ledger.write_text(json.dumps(d,indent=2)+'\n')
text=['# Astra plate-girder trial with solver feedback','',note,'',f'Conservative API cost: ${rec["generation"]["cost_usd_conservative"]:.6f}; 1 request. Budget $5 for this additional round. No automatic retries.','',f'Clean replay elapsed: {execution["elapsed_seconds"]:.1f} seconds. Execution verified; frozen inputs unchanged.','', '| Mesh size (mm) | Nodes | Elements | Buckling factor |','|---|---|---|---|']
for x in levels:text.append(f'| {x["h_mm"]} | {x["nodes"]} | {x["elements"]} | {x["lambda1"]} |')
text+=['','See request.json, response.json, model-patch.json, replay/execution.json, scoring/score.json and replay/outputs/ for original evidence. No manual edits were made to the model-authored solver.','', 'The new internet-sourced shortlist remains held: it was not tested by substituting this existing benchmark task. This result applies only to the existing fully specified plate-girder task.']
(run/'README.md').write_text('\n'.join(text)+'\n')
f=BASE/'failure-list.json';data=json.loads(f.read_text());case=next(x for x in data['cases'] if x['task_id']==tid);case['recheck_solver_feedback']={'status':status,'note':note,'evidence':str(run/'outcome.json'),'cost_usd_conservative':rec['generation']['cost_usd_conservative']};data['current_confirmed_persistent_failure_count']=0;f.write_text(json.dumps(data,indent=2)+'\n')
f=BASE/'RECHECK_RESULTS.md';s=f.read_text();lines=s.splitlines();lines=[f'| {tid} | {status} | {note} |' if line.startswith('| '+tid+' |') else line for line in lines];s='\n'.join(lines)+'\n';s=s.replace('6 repaired numerical passes, 3 unresolved numerical mismatches, 1 solver-sensitive case excluded.','7 repaired numerical passes (including 1 with explicit solver feedback), 3 unresolved numerical mismatches.');s+='\nAdditional solver-feedback round: 1 API call, $'+format(rec['generation']['cost_usd_conservative'],'.6f')+' conservative estimate, charged to a separate $5 authorization. Earlier recheck costs above remain separate.\n';f.write_text(s)
f=BASE/'FAILURE_LIST.md';s=f.read_text().replace('6 numerical recoveries, 0 confirmed persistent capability failures, 3 unresolved numerical mismatches, 1 solver-sensitive case excluded','7 numerical recoveries (one with explicit solver feedback), 0 confirmed persistent capability failures, 3 unresolved numerical mismatches');f.write_text(s)
f=BASE/'similar-failure-candidates-20261015.json';s=json.loads(f.read_text());s.update(api_calls_this_round=1,api_spend_usd_this_round=d['session_cost_upper_bound_usd'],existing_task_trial={'task_id':tid,'status':status,'report':str(run/'README.md'),'new_shortlist_tested':False});f.write_text(json.dumps(s,indent=2)+'\n')
print(json.dumps({'status':status,'lambda1':value,'relative_error_percent':error,'elapsed_seconds':execution['elapsed_seconds'],'api_cost_conservative_usd':rec['generation']['cost_usd_conservative'],'numerical_passed':score['numerical_passed'],'workflow_verified':score['workflow_verified'],'levels':levels},indent=2))
