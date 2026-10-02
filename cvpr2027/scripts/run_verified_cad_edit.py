"""Apply a model patch, execute CAD, and audit FEM under a user-supplied physical contract."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
import cadquery as cq
from cad_edit_contracts import apply
from cad_editor_geometry import execute_sequence
from verify_mechanical_cad_edits import execute

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--patch',type=Path,required=True);p.add_argument('--representation',choices=['cadquery','cad-editor-sequence'],required=True);p.add_argument('--contract',type=Path,required=True);p.add_argument('--target-step',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise ValueError('Use a fresh output directory')
 a.output.mkdir(parents=True);record=dict(status='started',safe_for_operation='not_assessed',representation=a.representation)
 def save(): (a.output/'verification.json').write_text(json.dumps(record,indent=2)+'\n')
 try:
  c=json.loads(a.contract.read_text());assert c['units']=='mm,N,MPa';E=c['material']['E_MPa'];nu=c['material']['poisson_ratio'];force=c['total_force_N'];axis=c['axis'];band=c['band_fraction'];hs=c['mesh_sizes_mm']
  if E<=0 or not -1<nu<.5 or force<=0 or len(axis)!=3 or np.linalg.norm(axis)==0 or not 0<band<.5 or len(hs)<2 or any(h<=0 for h in hs):raise ValueError('Invalid physical contract')
  if a.representation=='cad-editor-sequence' and 'native_length_scale_mm' not in c:raise ValueError('Normalized sequence requires explicitly specified native_length_scale_mm')
  record['contract']=c;record['contract_sha256']=hashlib.sha256(a.contract.read_bytes()).hexdigest();record['source_sha256']=hashlib.sha256(a.source.read_bytes()).hexdigest()
  code=apply(a.source.read_text(),json.loads(a.patch.read_text()),a.representation);(a.output/'edited.txt').write_text(code)
  solid=execute(code) if a.representation=='cadquery' else execute_sequence(code).scale(c['native_length_scale_mm'])
  if not solid.isValid() or not solid.Solids() or solid.Volume()<=0:raise ValueError('Invalid predicted solid')
  step=a.output/'prediction.step';cq.exporters.export(solid,str(step));record['solid_count']=len(solid.Solids());record['step_sha256']=hashlib.sha256(step.read_bytes()).hexdigest();record['geometry_valid']=True
  views={'front':(0,-1,0),'top':(0,0,1),'right':(1,0,0),'isometric':(1,-1,1)}
  for name,direction in views.items():cq.exporters.export(solid,str(a.output/(name+'.svg')),opt={'projectionDir':direction,'showHidden':False,'width':600,'height':400})
  if a.target_step:
   target=cq.importers.importStep(str(a.target_step)).val()
   if not target.isValid() or not target.Solids() or target.Volume()<=0:raise ValueError('Invalid reference STEP')
   intersection=solid.intersect(target).Volume();record['volume_iou']=intersection/(solid.Volume()+target.Volume()-intersection)
  record['fem']={}
  for role,path in [('prediction',step)]+([('target',a.target_step)] if a.target_step else []):
   history=[];converged=False
   for i,h in enumerate(hs):
    dest=a.output/f'{role}-mesh-{i}';cmd=[sys.executable,str(Path(__file__).with_name('mechanical_cad_fem.py')),'--step',str(path),'--output',str(dest),'--h',str(h),'--axis',*map(str,axis),'--young',str(E),'--poisson',str(nu),'--force',str(force),'--band',str(band)]
    dest.mkdir()
    with (dest/'solver.log').open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=240)
    if r.returncode:raise ValueError(f'{role} FEM mesh/solver failed; see {dest}/solver.log')
    m=json.loads((dest/'metrics.json').read_text());exact=cq.importers.importStep(str(path)).val().Volume();m['relative_mesh_volume_error']=abs(m['mesh_volume_mm3']/exact-1);history.append(m)
    if len(history)>1:
     change=abs(history[-1]['compliance_N_mm']/history[-2]['compliance_N_mm']-1)
     if change<=c['compliance_mesh_tolerance'] and m['relative_mesh_volume_error']<=c['mesh_volume_tolerance']:converged=True;break
   record['fem'][role]=dict(compliance_mesh_checked=converged,history=history);save()
  checked=all(v['compliance_mesh_checked'] for v in record['fem'].values());m=record['fem']['prediction']['history'][-1];record['fem_numerical_checks_pass']=checked
  if a.target_step:
   tm=record['fem']['target']['history'][-1];err=abs(m['compliance_N_mm']/tm['compliance_N_mm']-1);record['relative_target_compliance_error']=err;record['edit_reference_check_pass']=checked and record['volume_iou']>=c['geometry_iou_threshold'] and err<=c['response_agreement_tolerance']
  if 'max_load_weighted_displacement_mm' in c:record['displacement_limit_pass']=m['load_weighted_displacement_mm']<=c['max_load_weighted_displacement_mm']
  # Peak stress is diagnostic only. No mesh-converged strength verdict is invented.
  record['status']='completed' if checked else 'not_verified_mesh_sensitivity';save()
 except Exception as e:record.update(status='not_verified',error=type(e).__name__+': '+str(e));save();print(json.dumps(record));sys.exit(1)
 print(json.dumps(record))
if __name__=='__main__':main()
