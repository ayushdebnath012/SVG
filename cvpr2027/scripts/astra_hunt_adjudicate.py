from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'output/datasets/cadfem-challenge-trials';tid,kind,note=sys.argv[1:4];r=ROOT/'runs/astra-failure-hunt-20261015'/tid
rec=json.loads((r/'outcome.json').read_text());rec.update(status=kind,adjudication_note=note,count_as_distinct_failure=kind in ['observed_script_failure','observed_numerical_failure'])
score=r/'scoring/score.json'
if score.exists():rec['numerical_passed']=json.loads(score.read_text())['tasks'][0]['numerical_passed']
(r/'outcome.json').write_text(json.dumps(rec,indent=2)+'\n');(r/'README.md').write_text('# '+tid+'\n\n'+kind+'\n\n'+note+'\n\nProtocol: single-shot low reasoning; no repair. Outcome is specific to this protocol. Cost: $'+str(rec['generation']['cost_usd_conservative'])+'. See outcome.json, original response, submitted code, sandbox execution and scoring records.\n')
p=base/'astra-20261015.json';d=json.loads(p.read_text());d['hunt_trials']=[rec if x['task_id']==tid else x for x in d['hunt_trials']];p.write_text(json.dumps(d,indent=2)+'\n')
p=base/'failure-list.json';d=json.loads(p.read_text());d['cases']=[x for x in d['cases'] if x['task_id']!=tid]+[{'task_id':tid,'classification':kind,'count_as_distinct_failure':rec['count_as_distinct_failure'],'evidence':str(r/'outcome.json'),'note':note}];d['confirmed_distinct_cases']=sum(x['count_as_distinct_failure'] for x in d['cases']);p.write_text(json.dumps(d,indent=2)+'\n')
lines=['# Astra CAD+FEM failure search','',f"Target: 10 distinct confirmed cases. Observed failures under restricted protocols: {d['confirmed_distinct_cases']}. Budget, runtime and source-reference ambiguity are not capability failures.",'','| Case | Classification | Counted | Evidence |','|---|---|---|---|']
for x in d['cases']:lines.append(f"| {x['task_id']} | {x['classification']} | {'Yes' if x['count_as_distinct_failure'] else 'No'} | {x['note']} |")
lines+=['','All successes and inconclusive trials retained. Public-source contamination is possible. These results do not imply failure with more reasoning, tools or repair feedback. See failure-list.json for evidence paths and astra-20261015.json for API usage.']
(base/'FAILURE_LIST.md').write_text('\n'.join(lines)+'\n')
print(kind,tid,'confirmed cases:',d['confirmed_distinct_cases'])
