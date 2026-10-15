"""Independent CAD-remeshed linear-elastic validation, not new dataset references.
Uses candidate CAD/prompts only during solve; a separate comparison reads targets.
"""
import argparse,json,re,time,hashlib
from pathlib import Path
import numpy as np
import gmsh,ufl
from mpi4py import MPI
from petsc4py import PETSc
from dolfinx import fem,io
from dolfinx.fem.petsc import LinearProblem

ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,required=True);ap.add_argument('--task',required=True);ap.add_argument('--size',type=float,required=True);ap.add_argument('--geometry-degree',type=int,default=2);ap.add_argument('--max-elements',type=int,default=220000);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
t=next(json.loads(x) for x in (a.package/'candidate/tasks.jsonl').read_text().splitlines() if json.loads(x)['task_id']==a.task)
step=a.package/'candidate'/next(i['path'] for i in t['inputs'] if i['role']=='cad');start=time.time()
gmsh.initialize();gmsh.option.setNumber('General.Terminal',1);gmsh.model.add('independent')
gmsh.model.occ.importShapes(str(step));gmsh.model.occ.synchronize()
vols=[tag for _,tag in gmsh.model.getEntities(3)];gmsh.model.addPhysicalGroup(3,vols,1)
surfs=[tag for _,tag in gmsh.model.getEntities(2)];forces={};fixed=[];mapping={};total_forces={}
if t['family']=='agentfem-bracket':
 E=70000.;nu=.33;z=float(re.search(r'height ([\d.]+) mm',t['prompt']).group(1));traction=float(re.search(r'traction of ([\d.]+) MPa',t['prompt']).group(1));loaded=[]
 for tag in surfs:
  b=gmsh.model.getBoundingBox(2,tag)
  if abs(b[2])<1e-5 and abs(b[5])<1e-5:fixed.append(tag)
  if abs(b[2]-z)<1e-5 and abs(b[5]-z)<1e-5:loaded.append(tag)
 assert fixed and loaded
 for tag in loaded:forces[tag]=np.array([0.,0.,-traction])
elif t['family']=='cycloidal-drive-components':
 E=float(re.search(r'E = ([\d.]+) MPa',t['prompt']).group(1));nu=float(re.search(r'Poisson ratio ([\d.]+)',t['prompt']).group(1).rstrip('.'))
 desc=json.loads((step.parent/'faces.json').read_text())['faces']
 # Match CAD surfaces by area and centroid, independently of face ordering.
 for d in desc:
  idx=d.get('face_index',d.get('index'));center=np.array(d['centroid_mm']);area=d['area_mm2']
  scores=[(np.linalg.norm(np.array(gmsh.model.occ.getCenterOfMass(2,tag))-center)+abs(gmsh.model.occ.getMass(2,tag)-area)/max(area,1),tag) for tag in surfs]
  score,tag=min(scores);assert score<.005,(d,score);mapping[idx]=tag
 assert len(set(mapping.values()))==len(mapping)
 block=t['prompt'].split('Supports:')[1].split('Load:')[0];fixed=[mapping[int(x)] for x in re.findall(r'face (\d+):',block)]
 for n,v in re.findall(r'face (\d+) carries \(([^)]+)\) N',t['prompt']):
  tag=mapping[int(n)];total_forces[tag]=np.array([float(x) for x in v.split(',')]);forces[tag]=total_forces[tag]/gmsh.model.occ.getMass(2,tag)
 assert fixed and forces
else:raise ValueError('unsupported family')
gmsh.model.addPhysicalGroup(2,fixed,10)
loadgroups={};group_totals={}
for j,(tag,tr) in enumerate(forces.items(),20):
 gmsh.model.addPhysicalGroup(2,[tag],j);loadgroups[j]=tr
 if tag in total_forces:group_totals[j]=total_forces[tag]
for name,v in [('Mesh.MeshSizeMin',a.size),('Mesh.MeshSizeMax',a.size),('Mesh.ElementOrder',a.geometry_degree),('Mesh.Algorithm3D',1),('General.NumThreads',2)]:gmsh.option.setNumber(name,v)
gmsh.model.mesh.generate(3)
nel=sum(len(x) for x in gmsh.model.mesh.getElements(3)[1])
if nel>a.max_elements:
 (a.out/'mesh-limit.json').write_text(json.dumps({'elements':nel,'limit':a.max_elements,'mesh_size_mm':a.size}));gmsh.finalize();raise RuntimeError('mesh exceeds per-process direct-solver guardrail')
gmsh.write(str(a.out/'mesh.msh'))
dom,ct,ft=io.gmshio.model_to_mesh(gmsh.model,MPI.COMM_SELF,0,gdim=3)
gmsh.finalize();V=fem.functionspace(dom,('Lagrange',2,(3,)))
dofs=fem.locate_dofs_topological(V,2,ft.find(10));bc=fem.dirichletbc(np.zeros(3,dtype=PETSc.ScalarType),dofs,V)
u=ufl.TrialFunction(V);v=ufl.TestFunction(V);mu=E/(2*(1+nu));lam=E*nu/((1+nu)*(1-2*nu))
def eps(x):return ufl.sym(ufl.grad(x))
def sig(x):return lam*ufl.tr(eps(x))*ufl.Identity(3)+2*mu*eps(x)
ds=ufl.Measure('ds',domain=dom,subdomain_data=ft)
for g,force in group_totals.items():loadgroups[g]=force/fem.assemble_scalar(fem.form(1*ds(g)))
L=sum(ufl.dot(fem.Constant(dom,np.asarray(tr,dtype=PETSc.ScalarType)),v)*ds(g) for g,tr in loadgroups.items())
problem=LinearProblem(ufl.inner(sig(u),eps(v))*ufl.dx,L,bcs=[bc],petsc_options={'ksp_type':'preonly','pc_type':'lu','pc_factor_mat_solver_type':'mumps'})
sol=problem.solve();assert problem.solver.getConvergedReason()>0
xyz=V.tabulate_dof_coordinates();uvals=sol.x.array.reshape((-1,3));assert np.isfinite(uvals).all();q={'max_displacement_mm':float(np.linalg.norm(uvals,axis=1).max())}
if t['family']=='agentfem-bracket':
 top=np.isclose(xyz[:,2],z,atol=1e-6);q['seat_mean_displacement_mm']=float(-uvals[top,2].mean());q['seat_area_mean_mm']=float(fem.assemble_scalar(fem.form(sum(-sol[2]*ds(g) for g in loadgroups))))/sum(float(fem.assemble_scalar(fem.form(1*ds(g)))) for g in loadgroups)
# Independent global reaction check using residual of unconstrained weak form.
res=fem.petsc.assemble_vector(fem.form(ufl.inner(sig(sol),eps(v))*ufl.dx-L));res.ghostUpdate(addv=PETSc.InsertMode.ADD_VALUES,mode=PETSc.ScatterMode.REVERSE)
reactions=res.array.reshape((-1,3))[dofs].sum(axis=0)
load=np.zeros(3)
for g,tr in loadgroups.items():load+=tr*fem.assemble_scalar(fem.form(1*ds(g)))
balance=np.linalg.norm(reactions+load)/max(np.linalg.norm(load),1e-30)
np.savez_compressed(a.out/'fields.npz',coordinates_mm=xyz,displacement_mm=uvals,fixed_dof_nodes=dofs,reaction_N=reactions,applied_force_N=load)
record={'task_id':a.task,'cad_sha256':hashlib.sha256(step.read_bytes()).hexdigest(),'mesh_size_mm':a.size,'element':'quadratic tetrahedral displacement', 'geometry_degree':a.geometry_degree,'geometry_nodes':len(dom.geometry.x),'displacement_nodes':len(xyz),'elements':dom.topology.index_map(3).size_global,'solver':'FEniCSx 0.9.0 / PETSc MUMPS','gmsh':gmsh.__version__,'outputs':q,'reaction_N':reactions.tolist(),'applied_force_N':load.tolist(),'force_balance_relative':float(balance),'surface_mapping':mapping,'runtime_seconds':time.time()-start,'reference_values_used_during_solve':False,'role':'independent_validation_only_not_reference'}
(a.out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
