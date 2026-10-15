"""Compare independent validation outputs to unchanged published references."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[2];base=root/'cadfem-bench-v1.1';src=root/'cvpr2027/output/reproduction-v1.1';out=root/'cvpr2027/output/datasets/cadfem-bench-v1.1-followup';out.mkdir(parents=True,exist_ok=True)
refs={r['task_id']:r for r in map(json.loads,(base/'evaluator/references.jsonl').read_text().splitlines())}
summary=[]
for tid,prefix in [('A-AGENTFEM-fresh_test_000','agentfem'),('A-CYC-Coupler-PETGCF','coupler')]:
 runs=sorted([json.loads(f.read_text()) for f in src.glob(prefix+'-*/result.json')],key=lambda r:-r['mesh_size_mm']);last,prev=runs[-1],runs[-2];checks={}
 for key,ref in refs[tid]['references'].items():
  pred=last['outputs'][key];err=abs(pred-ref['value'])/abs(ref['value']);delta=abs(pred-prev['outputs'][key])/abs(pred)
  checks[key]={'published_reference':ref['value'],'independent_fine_mesh_value':pred,'unit':'mm','relative_reference_error':err,'last_refinement_relative_change':delta,'existing_tolerance':ref['tol']['value'],'within_existing_tolerance':err<=ref['tol']['value'],'last_refinement_below_one_percent':delta<.01}
 assert all(v['within_existing_tolerance'] and v['last_refinement_below_one_percent'] for v in checks.values())
 assert all(r['force_balance_relative']<1e-8 for r in runs)
 summary.append({'task_id':tid,'status':'independently_reproduced_requested_displacements','checks':checks,'runs':runs,'limits':['This validates the stated displacement quantities, not every field, stress or the entire source family.','Last-mesh change is an empirical convergence indicator, not a rigorous discretization error bound.','Published reference values and tolerances are unchanged.']})
 fig,ax=plt.subplots(figsize=(7,3.5),layout='constrained')
 for key,ref in refs[tid]['references'].items():
  ax.plot([r['displacement_nodes'] for r in runs],[100*(r['outputs'][key]/ref['value']-1) for r in runs],'o-',label=key.replace('_mm','').replace('_',' '))
 ax.axhline(0,color='black',lw=.8);ax.set_xscale('log');ax.set_xlabel('Displacement nodes (log scale)');ax.set_ylabel('Difference from published reference (%)');ax.grid(alpha=.25);ax.legend(fontsize=8);fig.savefig(src/(prefix+'-convergence.png'),dpi=170);plt.close(fig)
report={'date':'2026-10-14','baseline':'CADFEM-Bench v1.1','baseline_reference_sha256':hashlib.sha256((base/'evaluator/references.jsonl').read_bytes()).hexdigest(),'active_tasks':118,'published_targets':298,'independently_reproduced_task_count':len(summary),'reproduction_scope':'Independent CAD remeshing and quadratic-displacement FEniCSx solves; requested displacement quantities only','remaining_tasks_without_independent_reproduction':116,'runs_completed':sum(len(x['runs']) for x in summary),'new_dataset_references_generated':0,'validation_solver_runs_generated':sum(len(x['runs']) for x in summary),'records':summary}
(src/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copytree(src,out/'independent-reproduction',dirs_exist_ok=True)
for run in src.iterdir():
 if run.is_dir():
  log=root/'cvpr2027/tmp'/('reproduce-'+run.name+'.log')
  if log.exists():shutil.copy2(log,out/'independent-reproduction'/run.name/'solver.log')
for n in ['collect_fcvm_breadth.py','audit_fcvm_breadth.py','reproduce_cadfem_pilot.py','summarize_cadfem_followup.py']:
 (out/'scripts').mkdir(exist_ok=True);shutil.copy2(root/'cvpr2027/scripts'/n,out/'scripts'/n)
shutil.copytree(root/'cvpr2027/data/web-cad-fem-fcvm-breadth',out/'published-source-expansion',dirs_exist_ok=True)
shutil.copy2(root/'cvpr2027/output/audits/cadfem-bench-v1.1-followup/integrity.json',out/'baseline-integrity.json')
shutil.copy2(base/'evaluator/verification.json',out/'baseline-verification.json')
print(json.dumps({'tasks_reproduced':len(summary),'runs':report['runs_completed'],'checks':[{r['task_id']:r['checks']} for r in summary]},indent=2))
