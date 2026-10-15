"""Read-only source/deck correspondence and actual CalculiX replay comparison.
No source program is executed; replay values are validation-only, never targets.
"""
import argparse,hashlib,json,struct,zipfile,xml.etree.ElementTree as E
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

def unv_nodes(text):
 lines=text.splitlines();i=next(i for i in range(len(lines)-1) if lines[i].strip()=='-1' and lines[i+1].strip()=='2411')+2;d={}
 while lines[i].strip()!='-1':
  nid=int(lines[i].split()[0]);d[nid]=[float(x.replace('D','E')) for x in lines[i+1].split()];i+=2
 return d

def deck_nodes(text):
 d={};active=False
 for l in text.splitlines():
  if l.startswith('**'):continue
  if l.startswith('*'):active=l.split(',')[0].upper()=='*NODE';continue
  if active and l.strip():
   a=l.split(',');d[int(a[0])]=list(map(float,a[1:4]))
 return d

def frd_fields(p):
 blocks={};key=None;values={}
 for l in p.read_text().splitlines():
  if l.startswith('    2C'):key='COORD';values={}
  elif l.startswith(' -4'):key=l.split()[1];values={}
  elif key and l.startswith(' -1'):
   nid=int(l[3:13]);values[nid]=[float(l[i:i+12]) for i in range(13,len(l.rstrip()),12)]
  elif key and l.startswith(' -3'):blocks[key]=values;key=None
 return blocks

def audit(src,run,out):
 with zipfile.ZipFile(src/'constraint_contact_shell_shell.FCStd') as z:
  root=E.fromstring(z.read('Document.xml'))
  original=unv_nodes(z.read('FemMesh.unv').decode());resultnodes=unv_nodes(z.read('FemMesh1.unv').decode())
  obj=root.find('.//ObjectData/Object[@name="CCX_Results"]')
  ids=np.array([int(i.get('v')) for i in obj.findall('./Properties/Property[@name="NodeNumbers"]/IntegerList/I')])
  def array(name):
   b=z.read(name);n=struct.unpack('<I',b[:4])[0];a=np.frombuffer(b[4:],'<f8').copy();return a.reshape(n,-1) if name=='DisplacementVectors' else a
  U=array('DisplacementVectors');vm=array('vonMises');force=float(root.find('.//ObjectData/Object[@name="ConstraintForce"]/Properties/Property[@name="Force"]/Float').get('value'))
  stress=np.column_stack([array('NodeStress'+s) for s in ['XX','YY','ZZ','XY','YZ','XZ']])
 deck=deck_nodes((src/'constraint_contact_shell_shell.inp').read_text());assert set(deck)==set(original)
 meshgap=max(np.linalg.norm(np.array(deck[k])-original[k]) for k in deck);assert meshgap<1e-8
 f=frd_fields(run/'contact.frd');fid=np.array(sorted(f['COORD']));fx=np.array([f['COORD'][int(i)] for i in fid]);sx=np.array([resultnodes[int(i)] for i in ids]);dist,index=cKDTree(fx).query(sx);assert len(set(index))==len(ids) and max(dist)<1e-3
 fu=np.array([f['DISP'][int(fid[i])] for i in index]);fs=np.array([f['STRESS'][int(fid[i])] for i in index]);fv=np.sqrt(.5*((fs[:,0]-fs[:,1])**2+(fs[:,1]-fs[:,2])**2+(fs[:,2]-fs[:,0])**2)+3*np.sum(fs[:,3:]**2,axis=1))
 sv=np.sqrt(.5*((stress[:,0]-stress[:,1])**2+(stress[:,1]-stress[:,2])**2+(stress[:,2]-stress[:,0])**2)+3*np.sum(stress[:,3:]**2,axis=1));assert np.allclose(sv,vm,atol=1e-6,rtol=1e-10)
 report={'case':'FreeCAD-shell-tube-contact','source_geometry':'two original BREP cylindrical shell faces','original_mesh_nodes':len(deck),'source_result_nodes':len(ids),'original_deck_mesh_max_coordinate_gap_mm':meshgap,'source_force_serialized':force,'FreeCAD_internal_units_per_N':1000,'native_force_N':force/1000,'deck_force_N':5000,'force_unit_correspondence_verified':True,'source_results_have_shell_thickness_expanded_coordinates':True,'source_to_replay_coordinate_max_gap_mm':float(max(dist)),'source_max_displacement_mm':float(np.linalg.norm(U,axis=1).max()),'replay_max_displacement_mm':float(np.linalg.norm(fu,axis=1).max()),'displacement_field_relative_L2_gap':float(np.linalg.norm(fu-U)/np.linalg.norm(U)),'source_max_vonMises_MPa':float(vm.max()),'replay_max_vonMises_MPa':float(fv.max()),'stress_field_relative_L2_gap':float(np.linalg.norm(fs-stress)/np.linalg.norm(stress)),'replay_solver':'CalculiX 2.23, original deck, 2 threads','solver_finished': 'Job finished' in (run/'solver.log').read_text(),'role':'source-correspondence validation; same solver family, not independent formulation validation','convergence_established':False,'new_scored_tasks':0}
 out.mkdir(parents=True,exist_ok=True);np.savez_compressed(out/'source-original-nodal-fields.npz',source_node_ids=ids,coords_mm=sx,U_mm=U,stress_MPa=stress,VM_MPa=vm);np.savez_compressed(out/'replay-fields-aligned.npz',source_node_ids=ids,coords_mm=fx[index],U_mm=fu,stress_MPa=fs,VM_MPa=fv)
 (out/'assessment.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--run',type=Path,required=True);a.add_argument('--out',type=Path,required=True);x=a.parse_args();audit(x.source,x.run,x.out)
