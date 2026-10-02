"""FEM source/target/prediction triples for the six paper examples under frozen synthetic contracts."""
import json,hashlib,subprocess,sys,time
from pathlib import Path
import numpy as np
import cadquery as cq
from verify_mechanical_cad_edits import execute
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'runs/mechanical-cad-fem-20261002';OUT.mkdir(exist_ok=True)
data=ROOT/'data/benchcad-online-edit-v1';run=ROOT/'runs/benchcad-online-h100-20261002'
examples=json.loads((ROOT/'runs/benchcad-prediction-figures-20261002/manifest.json').read_text())
rows={r['id']:r for r in map(json.loads,(data/'test.jsonl').read_text().splitlines())};pred={r['id']:r for r in map(json.loads,(run/'trained-predictions.jsonl').read_text().splitlines())}
contracts=[]
for ex in examples:
 r=rows[ex['id']];folder=OUT/r['source_record_id'];folder.mkdir(exist_ok=True)
 solids={'source':execute(r['code']),'target':cq.importers.importStep(str(data/r['reference_step'])).val(),'prediction':execute(pred[r['id']]['predicted_code'])}
 maxspan=0
 for role,solid in solids.items():
  if not solid.Solids() or not solid.isValid():raise ValueError('Expected valid positive-volume solids')
  cq.exporters.export(solid,str(folder/(role+'.step')))
  b=solid.BoundingBox();maxspan=max(maxspan,b.xlen,b.ylen,b.zlen)
 axis=[0.,0.,1.];targetaxis=axis
 if 'rot_diag60' in r['source_record_id']:
  v=np.array([1.,0.,1.])/np.sqrt(2);z=np.array(axis);theta=np.pi/3;targetaxis=(z*np.cos(theta)+np.cross(v,z)*np.sin(theta)+v*(v@z)*(1-np.cos(theta))).tolist()
 contract=dict(solid_counts={role:len(solid.Solids()) for role,solid in solids.items()},id=r['id'],source_record_id=r['source_record_id'],instruction=r['instruction'],units='mm,N,MPa',material=dict(label='hypothetical homogeneous isotropic steel-like test material, not author-specified',E_MPa=210000.,poisson_ratio=.3),total_force_N=1.,load='Uniform vector traction parallel to analysis axis on exterior triangles whose centroids lie in upper 5% projected span; normalized to 1 N resultant',support='All displacement components fixed for exterior nodes in lower 5% projected span',band_fraction=.05,source_axis=axis,target_axis=targetaxis,prediction_axis=targetaxis,rotation_case='Fixture and load axis co-rotate by the requested 60 degrees for edited shapes' if targetaxis!=axis else None,mesh_sizes_mm=[maxspan/12,maxspan/18,maxspan/27,maxspan/40.5],compliance_relative_mesh_tolerance=.05,response_agreement_tolerance=.1,scope='post-hoc diagnostic scenarios for six illustrative cases; not author operating conditions or a safety criterion',role_step_sha256={role:hashlib.sha256((folder/(role+'.step')).read_bytes()).hexdigest() for role in solids})
 contracts.append(contract)
# Freeze every condition before examining any model FEM responses.
(OUT/'contracts.json').write_text(json.dumps(contracts,indent=2)+'\n')
results=[]
for c in contracts:
 case=dict(id=c['id'],source_record_id=c['source_record_id'],roles={})
 for role in ['source','target','prediction']:
  folder=OUT/c['source_record_id'];history=[];status='not_converged'
  for level,h in enumerate(c['mesh_sizes_mm']):
   dest=folder/f'{role}-mesh-{level}';cmd=[sys.executable,str(ROOT/'scripts/mechanical_cad_fem.py'),'--step',str(folder/(role+'.step')),'--output',str(dest),'--h',str(h),'--axis',*map(str,c[role+'_axis'])]
   print('FEM',c['source_record_id'],role,'level',level,flush=True)
   try:
    if not (dest/'metrics.json').exists():
     dest.mkdir(exist_ok=True)
     with (dest/'solver.log').open('w') as log:
      res=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=240)
     if res.returncode:raise ValueError((dest/'solver.log').read_text()[-1200:])
    m=json.loads((dest/'metrics.json').read_text());history.append(m)
    if len(history)>1:
     change=abs(history[-1]['compliance_N_mm']/history[-2]['compliance_N_mm']-1)
     m['compliance_mesh_change']=change
     if change<=c['compliance_relative_mesh_tolerance']:status='compliance_mesh_checked';break
   except Exception as e:
    status='solver_or_mesh_failure';case.setdefault('errors',{})[role]=str(e)[-1200:];break
  case['roles'][role]=dict(status=status,history=history,final=history[-1] if history else None)
  (OUT/'progress.json').write_text(json.dumps(dict(completed_cases=results,current=case),indent=2)+'\n')
 if all(case['roles'][role]['final'] for role in ['source','target','prediction']):
  s,t,p=[case['roles'][role]['final'] for role in ['source','target','prediction']]
  err=abs(p['compliance_N_mm']/t['compliance_N_mm']-1);stresserr=abs(p['vm_p95_MPa']/t['vm_p95_MPa']-1)
  checked=all(case['roles'][role]['status']=='compliance_mesh_checked' for role in ['source','target','prediction'])
  case.update(relative_prediction_target_compliance_error=err,relative_prediction_target_vm_p95_error=stresserr,target_source_compliance_ratio=t['compliance_N_mm']/s['compliance_N_mm'],all_roles_compliance_mesh_checked=checked,response_agreement=(err<=c['response_agreement_tolerance']) if checked else None,geometry_iou=next(e['volume_iou'] for e in examples if e['id']==c['id']))
 results.append(case);(OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print('Completed',len(results),'FEM triples',flush=True)
