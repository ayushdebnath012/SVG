"""Score a frozen agent-selected repair set without using references for selection."""
import argparse,csv,json,math,random,subprocess
from collections import Counter
from pathlib import Path
from cad_edit_contracts import apply
from multisource_cad_astra_benchmark import parse
ROOT=Path(__file__).resolve().parents[1]


def main():
 p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);p.add_argument('--repair-decisions',type=Path,required=True);a=p.parse_args();out=a.experiment
 initial={r['id']:r for r in map(json.loads,(ROOT/'runs/multisource-cad-astra-20261004/scored/astra-predictions.jsonl').read_text().splitlines()) if r['source']=='BenchCAD'}
 baseline={r['id']:r for r in map(json.loads,(ROOT/'runs/multisource-cad-astra-20261004/scored/astra-predictions-geometry.jsonl').read_text().splitlines()) if r['source']=='BenchCAD'}
 originals={r['id']:r for r in map(json.loads,(out/'heldout.jsonl').read_text().splitlines())}
 decisions={r['id']:r for r in map(json.loads,(out/'grpo-heldout-decisions.jsonl').read_text().splitlines())}
 rd={r['id']:r for r in map(json.loads,a.repair_decisions.read_text().splitlines())}
 repaired=[]
 for id,d in rd.items():
  if not d['accepted']:continue
  assert not decisions[id]['accepted']
  text=(out/'repairs'/id[:16]/'response.txt').read_text();pred=dict(initial[id]);error=None;code=None
  try:
   patch,_=parse(text);code=apply(originals[id]['code'],patch,'cadquery')
  except Exception as e:error=type(e).__name__+': '+str(e)[:200]
  pred.pop('target_match',None) # remove stale baseline program-match metadata
  pred.update(prediction=text,predicted_code=code,applicable=code is not None,error=error)
  # Reference fields are carried exclusively for the downstream scoring process.
  repaired.append(pred)
 predpath=out/'selected-repairs.jsonl';predpath.write_text(''.join(json.dumps(r)+'\n' for r in repaired))
 if repaired:
  subprocess.run([str(ROOT/'tmp/cad-runtime/bin/python'),str(ROOT/'scripts/score_multisource_cad_geometry.py'),str(predpath)],check=True)
  scores={r['id']:r for r in map(json.loads,(out/'selected-repairs-geometry.jsonl').read_text().splitlines())}
 else:scores={}
 rows=[]
 for id,b in baseline.items():
  after=scores.get(id,b)
  rows.append(dict(id=id,category=b['category'],reference_valid=b['reference_valid'],without=bool(b['match_strict']),with_agent=bool(after['match_strict']),verifier_rejected=not decisions[id]['accepted'],repair_selected=id in scores,baseline_iou=b.get('volume_iou'),agent_iou=after.get('volume_iou'),scorer_status=after['status']))
 def summarize(rr):
  n=len(rr);before=sum(r['without'] for r in rr);after=sum(r['with_agent'] for r in rr);g=sum(not r['without'] and r['with_agent'] for r in rr);l=sum(r['without'] and not r['with_agent'] for r in rr)
  return dict(n=n,before=before,after=after,before_rate=before/n if n else None,after_rate=after/n if n else None,delta_pp=100*(after-before)/n if n else None,recovered=g,regressed=l)
 valid=[r for r in rows if r['reference_valid'] is True]
 summary={'all_tasks':summarize(rows),'valid_references':summarize(valid),'categories':{c:summarize([r for r in valid if r['category']==c]) for c in sorted({r['category'] for r in valid})},'invalid_references':[r['id'] for r in rows if r['reference_valid'] is not True],'repair_requested':sum(r['verifier_rejected'] for r in rows),'repair_selected':len(scores),'repair_statuses':dict(Counter(json.loads(p.read_text())['status'] for p in (out/'repairs').glob('*/result.json'))),'api_cost_estimate_usd':sum(json.loads(p.read_text()).get('estimated_cost_usd',0) for p in (out/'repairs').glob('*/result.json'))}
 g,l=summary['valid_references']['recovered'],summary['valid_references']['regressed'];n=g+l
 summary['paired_exact_p']=min(1,2*sum(math.comb(n,i) for i in range(min(g,l)+1))/2**n) if n else 1.0
 rng=random.Random(17);diff=[int(r['with_agent'])-int(r['without']) for r in valid];boot=sorted(100*sum(rng.choices(diff,k=len(diff)))/len(diff) for _ in range(10000));summary['paired_bootstrap_95pct_delta_pp']=[boot[250],boot[9749]]
 (out/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
 with (out/'per-task.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
