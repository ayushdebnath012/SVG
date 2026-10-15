from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'output/datasets/cadfem-challenge-trials';tid,status,note=sys.argv[1:4];r=ROOT/'runs/astra-recheck3-20261015'/tid
rec=json.loads((r/'outcome.json').read_text());rec.update(status=status,adjudication_note=note)
if (r/'scoring/score.json').exists():
 row=json.loads((r/'scoring/score.json').read_text())['tasks'][0];rec['score']=row
(r/'outcome.json').write_text(json.dumps(rec,indent=2)+'\n');(r/'README.md').write_text('# '+tid+' — medium-reasoning recheck\n\n'+status+'\n\n'+note+'\n\nOriginal failure preserved. Recheck uses one model-authored patch with task/code/runtime feedback and no reference answer. Execution and numerical scoring do not establish trusted physics review. See model-patch.json, response.json, replay/execution.json and scoring/score.json.\n')
p=BASE/'astra-recheck-20261015.json';d=json.loads(p.read_text());d['hunt_trials']=[rec if x['report']==rec['report'] else x for x in d['hunt_trials']];p.write_text(json.dumps(d,indent=2)+'\n')
p=BASE/'failure-list.json';f=json.loads(p.read_text())
for x in f['cases']:
 if x['task_id']==tid:x['recheck3']={'status':status,'note':note,'evidence':str(r/'outcome.json'),'cost_usd_conservative':rec['generation']['cost_usd_conservative']}
p.write_text(json.dumps(f,indent=2)+'\n')
rows=[x for x in f['cases'] if x['count_as_distinct_failure']]
lines=['# Astra failure-case rechecks','', 'Original ten low-budget outcomes remain historical observations. Current results below use medium reasoning plus one or two model-authored repairs with execution feedback; reference values are hidden.','', '| Case | Recheck status | Findings |','|---|---|---|']
for x in rows:
 a=x.get('recheck3',x.get('recheck2',x.get('recheck',{})));lines.append(f"| {x['task_id']} | {a.get('status','not yet rechecked')} | {a.get('note','')} |")
lines+=['',f"API cost in this recheck round: ${d['session_cost_upper_bound_usd']:.6f} of ${d['budget_usd']:.2f}.",'','Successful numerical outcomes still require trusted workflow review. Resource/token limits and source-reference ambiguity are excluded from persistent capability-failure counts.']
(BASE/'RECHECK_RESULTS.md').write_text('\n'.join(lines)+'\n')
print(tid,status)
