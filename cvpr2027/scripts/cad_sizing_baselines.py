"""Classical search controls. No oracle solution is supplied to either search."""
import argparse,itertools,json
from pathlib import Path
import numpy as np
import cad_functional_sizing as s

def cem(t,seed):
    rng=np.random.default_rng(seed);n=len(t['model']['members']);k=len(t['catalog_h_mm']);p=np.ones((n,k))/k;history=[]
    for step in range(4):
        ds=np.column_stack([rng.choice(k,256,p=q) for q in p]);ds[0]=[k-1]*n
        if history:ds[1]=history[0]['design']
        rr=s.rows(t,ds);history=sorted(history+rr,key=lambda r:(not r['structurally_feasible'],r['mass_kg'] if r['structurally_feasible'] else r['max_utilization']))
        elite=np.array([r['design'] for r in sorted(rr,key=lambda r:(not r['structurally_feasible'],r['mass_kg'] if r['structurally_feasible'] else r['max_utilization']))[:24]])
        freq=np.stack([(elite==i).mean(axis=0) for i in range(k)],axis=1)
        p=.15*p+.85*(.92*freq+.08/k)
    return {'method':'cross_entropy','seed':seed,'evaluations':1024,'batches':4,'best':history[0]}

def coordinate(t,budget=1024):
    n=len(t['model']['members']);k=len(t['catalog_h_mm']);best=s.rows(t,[[k-1]*n])[0];evaluations=1;seen={tuple(best['design'])}
    while evaluations<budget:
        ds=[]
        for count in (1,2):
            for axes in itertools.combinations(range(n),count):
                for choices in itertools.product(range(k),repeat=count):
                    d=list(best['design'])
                    for a,c in zip(axes,choices):d[a]=c
                    if tuple(d) not in seen and len(ds)<budget-evaluations:seen.add(tuple(d));ds.append(d)
        if not ds:break
        rr=s.rows(t,ds);evaluations+=len(ds)
        candidates=[r for r in rr if r['structurally_feasible'] and r['mass_kg']<best['mass_kg']-1e-8]
        if not candidates:break
        best=min(candidates,key=lambda r:r['mass_kg'])
    return {'method':'coordinate_pair_search','evaluations':evaluations,'note':'Matches evaluation ceiling; adaptive rounds are not matched to Astra tool-call ceiling. No oracle supplied.','best':best}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();records=[]
    for t in json.loads((s.DATA/'tasks.json').read_text())['tasks']:
        public={k:v for k,v in t.items() if k!='oracle'};runs=[cem(public,i) for i in range(20)];coord=coordinate(public)
        records.append({'id':t['id'],'cross_entropy_successes':sum(r['best']['all_constraints_pass'] for r in runs),'cross_entropy_trials':len(runs),'cross_entropy':runs,'coordinate':coord})
        print(t['id'],'CEM',records[-1]['cross_entropy_successes'],'/20; coordinate',coord['best']['all_constraints_pass'],flush=True)
    s.write(a.output,{'protocol':'Frozen four-batch 256-candidate cross-entropy search, seeds 0..19; plus adaptive pair-coordinate descent, <=1024 candidates. Oracle excluded from both.','records':records})
if __name__=='__main__':main()
