"""Independent family convergence audit. Numerical references are never overwritten.
Two CAD/FE orders, source conventions and finite mesh maxima remain model-dependent.
Acceptance bands are empirical proposals, not certified uncertainty bounds.
"""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,math,os,subprocess,sys,time

ROOT=Path(__file__).resolve().parents[2]
PY=ROOT/'cvpr2027/tmp/fenicsx/env/bin/python'
WORKER=ROOT/'cvpr2027/scripts/converge_cycloidal_worker.py'
OUT=ROOT/'cvpr2027/output/cycloidal-convergence-study'
PKG=ROOT/'cadfem-bench-v1.1'
TS=[json.loads(l) for l in (PKG/'candidate/tasks.jsonl').read_text().splitlines()]
TASKS=[t for t in TS if t['family']=='cycloidal-drive-components']
REFS={r['task_id']:r for r in map(json.loads,(PKG/'evaluator/references.jsonl').read_text().splitlines())}


def run_task(t):
 tid=t['task_id'];folder=OUT/tid;folder.mkdir(parents=True,exist_ok=True)
 # All start at the source's nominal 2 mm. Decrease uniformly; thin rings
 # are resolved by gmsh curvature/topology and the quadratic approximation.
 sizes=[2.,1.4,1.,.7,.5,.35]
 runs=[];failures=[]
 for h in sizes:
  dest=folder/f'h{h:g}';dest.mkdir(exist_ok=True)
  cache=dest/'result.json'
  if not cache.exists():
   with (dest/'solver.log').open('w') as log:
    env=os.environ.copy();env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',VECLIB_MAXIMUM_THREADS='2')
    start=time.time()
    try:
     p=subprocess.run([str(PY),str(WORKER),'--package',str(PKG),'--task',tid,'--size',str(h),'--geometry-degree','2','--max-elements','220000','--out',str(dest)],stdout=log,stderr=subprocess.STDOUT,env=env,timeout=600)
     if p.returncode:failures.append({'h':h,'exit_code':p.returncode,'log':str((dest/'solver.log').relative_to(OUT))})
    except subprocess.TimeoutExpired:failures.append({'h':h,'error':'600 second solve timeout','log':str((dest/'solver.log').relative_to(OUT))})
   if not cache.exists():break
  r=json.loads(cache.read_text());r['worker_sha256']=hashlib.sha256(WORKER.read_bytes()).hexdigest();r['task_sha256']=hashlib.sha256(json.dumps(t,sort_keys=True,separators=(',',':')).encode()).hexdigest();cache.write_text(json.dumps(r,indent=2)+'\n');runs.append(r)
  print(json.dumps({'task':tid,'h':h,'elements':r['elements'],'u_mm':r['outputs']['max_displacement_mm'],'seconds':r['runtime_seconds']}),flush=True)
  if len(runs)>=3:
   vals=[x['outputs']['max_displacement_mm'] for x in runs]
   d=abs(vals[-1]-vals[-2])/abs(vals[-1]);dprev=abs(vals[-2]-vals[-3])/abs(vals[-2])
   if d<.01 and dprev<.02:break
 ref=REFS[tid]['references']['max_displacement_mm']['value'];row={'task_id':tid,'published_reference_mm':ref,'old_tolerance':REFS[tid]['references']['max_displacement_mm']['tol']['value'],'mesh_runs':runs,'failures':failures,'new_reference_generated':False,'geometry_degree':2,'certified_uncertainty':False}
 if len(runs)>=3:
  uf,up,upp=[r['outputs']['max_displacement_mm'] for r in runs[-3:]][::-1]
  d=abs(uf-up)/abs(uf);dp=abs(up-upp)/abs(up);bias=abs(uf-ref)/abs(ref)
  passes=d<.01 and dp<.02 and all(r['force_balance_relative']<1e-8 for r in runs)
  # Conservative empirical allowance: observed source/independent discrepancy
  # plus twice the last refinement change relative to the source. Rounded up
  # to one percentage point; 2% minimum. Above 10% requires source review.
  band=max(.02,math.ceil((bias+2*abs(uf-up)/abs(ref))*100)/100)
  row.update(finest_independent_mm=uf,relative_source_difference=bias,last_mesh_change=d,previous_mesh_change=dp,convergence_indicator_passed=passes,empirical_band=band,
   status=('band_review_ready' if passes and band<=.10 else 'held_for_source_or_convergence_review'))
 else:row.update(status='held_for_failed_or_incomplete_study',convergence_indicator_passed=False)
 (folder/'study.json').write_text(json.dumps(row,indent=2)+'\n');return row


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=2);a=ap.parse_args();OUT.mkdir(parents=True,exist_ok=True)
 rows=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
  for r in pool.map(run_task,TASKS):
   rows.append(r);(OUT/'summary.json').write_text(json.dumps({'family':'cycloidal-drive-components','studied_parts':len(rows),'required_parts':15,'records':rows},indent=2)+'\n');print('FINISHED '+r['task_id']+' '+r['status'],flush=True)
 print('ALL_PARTS_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
