"""Offline reference scoring, strictly after MCTS has frozen its selections."""
import argparse,csv,json,math,random,subprocess
from pathlib import Path
from collections import Counter
from cad_edit_contracts import apply
from multisource_cad_astra_benchmark import parse
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'experiments/agentic-verifier-grpo-20261006'
def load(p):return [json.loads(l) for l in p.read_text().splitlines()]
def billing_estimate(call):
    if call.get('cost_uncertain'):return call['estimated_cost_usd']
    u=call.get('usage',{});d=u.get('prompt_tokens_details',{})
    cached=d.get('cached_tokens',0);writes=d.get('cache_write_tokens',0)
    plain=max(0,u.get('prompt_tokens',0)-cached-writes)
    return (10*plain+cached+12.5*writes+50*u.get('completion_tokens',0))/1e6
def stats(rows,before='without'):
    n=len(rows);a=sum(r[before] for r in rows);b=sum(r['with_mcts'] for r in rows)
    g=sum(not r[before] and r['with_mcts'] for r in rows);l=sum(r[before] and not r['with_mcts'] for r in rows)
    return dict(n=n,before=a,after=b,recovered=g,regressed=l,delta_pp=100*(b-a)/n if n else None)
def paired(rows,key):
    s=stats(rows,key);n=s['recovered']+s['regressed']
    s['exact_mcnemar_p']=min(1,2*sum(math.comb(n,i) for i in range(min(s['recovered'],s['regressed'])+1))/2**n) if n else 1.
    diffs=[int(r['with_mcts'])-int(r[key]) for r in rows];rng=random.Random(17)
    boot=sorted(100*sum(rng.choices(diffs,k=len(diffs)))/len(diffs) for _ in range(10000))
    s['bootstrap_95pct_delta_pp']=[boot[250],boot[9749]]
    return s
def main():
    p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);a=p.parse_args();out=a.experiment
    selected=load(out/'selected.jsonl');assert len(selected)==124 and len({r['id'] for r in selected})==124
    initial={r['id']:r for r in load(ROOT/'runs/multisource-cad-astra-20261004/scored/astra-predictions.jsonl') if r['source']=='BenchCAD'}
    baseline={r['id']:r for r in load(ROOT/'runs/multisource-cad-astra-20261004/scored/astra-predictions-geometry.jsonl') if r['source']=='BenchCAD'}
    source={r['id']:r for r in load(out/'heldout-target-free.jsonl')}
    previous={r['id']:r for r in csv.DictReader((OLD/'per-task.csv').open())}
    assert set(source)==set(initial)==set(baseline)=={r['id'] for r in selected}
    changed=[]
    for r in selected:
        if not r['replace_original']:continue
        pred=dict(initial[r['id']]);pred.pop('target_match',None)
        try:
            patch,_=parse(r['prediction']);code=apply(source[r['id']]['code'],patch,'cadquery');error=None
        except Exception as e:code=None;error=type(e).__name__
        pred.update(prediction=r['prediction'],predicted_code=code,applicable=code is not None,error=error)
        changed.append(pred)
    pp=out/'selected-replacements.jsonl';pp.write_text(''.join(json.dumps(r)+'\n' for r in changed))
    if changed:
        subprocess.run([str(ROOT/'tmp/cad-runtime/bin/python'),str(ROOT/'scripts/score_multisource_cad_geometry.py'),str(pp)],check=True)
        scores={r['id']:r for r in load(out/'selected-replacements-geometry.jsonl')}
    else:scores={}
    rows=[]
    for r in selected:
        id=r['id'];b=baseline[id];s=scores.get(id,b)
        rows.append(dict(id=id,category=b['category'],reference_valid=b['reference_valid'],
                         without=bool(b['match_strict']),with_single_repair=previous[id]['with_agent']=='True',
                         with_mcts=bool(s['match_strict']),selected_depth=r['selected_depth'],nodes=r['nodes'],
                         replaced=r['replace_original'],baseline_iou=b.get('volume_iou'),mcts_iou=s.get('volume_iou'),
                         scorer_status=s['status']))
    valid=[r for r in rows if r['reference_valid'] is True]
    calls=[json.loads(p.read_text()) for p in (out/'calls').glob('*/*/result.json')]
    comp=dict(all_tasks=stats(rows),valid_references=paired(valid,'without'),
              versus_single_repair_all=stats(rows,'with_single_repair'),versus_single_repair_valid=paired(valid,'with_single_repair'),
              categories={c:stats([r for r in valid if r['category']==c]) for c in sorted({r['category'] for r in valid})},
              tiers={name:stats([r for r in valid if r['category'] in cats]) for name,cats in [('Easy',{'T1','T2'}),('Moderate',{'T3','T4'}),('Hard',{'T5'})]},
              api_attempts=len(calls),api_statuses=dict(Counter(r['status'] for r in calls)),
              api_cost_estimate_usd=sum(billing_estimate(r) for r in calls),
              flat_input_output_estimate_usd=sum(r['estimated_cost_usd'] for r in calls),
              pricing_source='https://developers.openai.com/api/docs/models/gpt-6-astra',
              price_per_million_tokens=dict(input=10,cached_input=1,cache_writes=12.5,output=50),
              cache_write_tokens=sum(r.get('usage',{}).get('prompt_tokens_details',{}).get('cache_write_tokens',0) for r in calls),
              cached_input_tokens=sum(r.get('usage',{}).get('prompt_tokens_details',{}).get('cached_tokens',0) for r in calls),
              replacements=len(changed),selected_depths=dict(Counter(r['selected_depth'] for r in selected)),
              invalid_reference_ids=[r['id'] for r in rows if r['reference_valid'] is not True],
              equal_compute_comparison=False,interpretation='One seed-17 bounded pilot; additional inference and development-calibrated scoring, no causal attribution to MCTS.')
    (out/'comparison.json').write_text(json.dumps(comp,indent=2)+'\n')
    assert comp['api_cost_estimate_usd']+json.loads((out/'api-preflight.json').read_text())['estimated_cost_usd']<=5+1e-9
    with (out/'per-task.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    s=comp['all_tasks'];v=comp['versus_single_repair_all']
    report=f'''# Bounded Astra MCTS pilot\n\nAstra alone: {s['before']}/{s['n']}. MCTS selection: {s['after']}/{s['n']}. Previously completed single-repair loop: {v['before']}/{v['n']}.\n\nAgainst Astra: {s['recovered']} recovered, {s['regressed']} regressed. Against the single-repair loop: {v['recovered']} recovered, {v['regressed']} regressed.\n\n{comp['api_attempts']} new API attempts; estimated incremental cost ${comp['api_cost_estimate_usd']:.5f}. {comp['replacements']} original answers replaced. One invalid reference stays in the 124-task overall denominator and is excluded only from the 123-task valid-reference breakdown.\n\nThis is not an equal-compute comparison. No held-out geometry score was used by search, calibration or selection. Candidate selection was frozen before reference scoring. One seed only; multiple-seed and equal-budget controls remain necessary.\n\nSee comparison.json, calibration.json, manifest.json, selected.jsonl and per-task.csv for evidence.\n'''
    (out/'RESULTS.md').write_text(report)
    print(json.dumps(comp,indent=2))
if __name__=='__main__':main()
