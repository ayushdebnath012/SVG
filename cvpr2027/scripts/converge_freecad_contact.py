"""Remesh unchanged original cylindrical-shell CAD for validation-only contact solves.
Boundary/load/contact/material data come from the original published deck. No targets generated.
"""
import argparse,hashlib,json,os,resource,subprocess,time
from pathlib import Path
import gmsh,numpy as np
from audit_freecad_contact import frd_fields

def run(src,root,ccx,h):
 d=root/f'h-{h:g}';d.mkdir(parents=True,exist_ok=True);gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('original_source_shells')
 entities=[]
 for name in ['Lower_tube','Upper_tube']:
  a=gmsh.model.occ.importShapes(str(src/'extracted-original'/(name+'.brep')));assert len(a)==1 and a[0][0]==2,a;entities.append(a[0][1])
 # Partition only topology along the upper cylinder's axial mid-plane: unchanged source surface.
 corners=[gmsh.model.occ.addPoint(x,51,z) for x,z in [(-26,440),(476,440),(476,510),(-26,510)]]
 edges=[gmsh.model.occ.addLine(corners[i],corners[(i+1)%4]) for i in range(4)]
 plane=gmsh.model.occ.addPlaneSurface([gmsh.model.occ.addCurveLoop(edges)])
 parts,_=gmsh.model.occ.fragment([(2,entities[1])],[(2,plane)])
 gmsh.model.occ.synchronize()
 curved=[tag for dim,tag in parts if dim==2 and gmsh.model.occ.getMass(2,tag)>1 and gmsh.model.getBoundingBox(2,tag)[4]-gmsh.model.getBoundingBox(2,tag)[1]>1]
 unwanted=[(dim,tag) for dim,tag in parts if dim==2 and tag not in curved]
 gmsh.model.occ.remove(unwanted,recursive=True);gmsh.model.occ.synchronize()
 assert len(curved)>=2,curved
 assert abs(sum(gmsh.model.occ.getMass(2,tag) for tag in curved)-2*np.pi*25*500)<1e-5
 entities=[[entities[0]],curved]
 pt=gmsh.model.occ.addPoint(0,76,475,h)
 parts,maps=gmsh.model.occ.fragment([(2,tag) for tag in curved],[(0,pt)])
 gmsh.model.occ.synchronize();entities[1]=[tag for dim,tag in parts if dim==2];pt=maps[-1][0][1]
 for name in ['Mesh.MeshSizeMin','Mesh.MeshSizeMax']:gmsh.option.setNumber(name,h)
 gmsh.option.setNumber('Mesh.ElementOrder',1);gmsh.option.setNumber('General.NumThreads',2);gmsh.model.mesh.generate(2)
 nt,coords,_=gmsh.model.mesh.getNodes();nodes={int(k):v for k,v in zip(nt,np.array(coords).reshape(-1,3))};load,_,_=gmsh.model.mesh.getNodes(0,pt);assert len(load)==1
 groups=[];eid=1
 for ishell,tags in enumerate(entities):
  triangles=[]
  for tag in tags:
   types,es,ns=gmsh.model.mesh.getElements(2,tag);assert list(types)==[2],types;triangles.extend(np.array(ns[0]).reshape(-1,3))
  els=[]
  for tri in triangles:
   x=np.array([nodes[int(k)] for k in tri]);c=x.mean(0);rad=np.array([c[0],c[1],0]) if ishell==0 else np.array([0,c[1]-51,c[2]-475])
   if np.cross(x[1]-x[0],x[2]-x[0])@rad<0:tri=tri[[0,2,1]]
   els.append((eid,*map(int,tri)));eid+=1
  groups.append(els)
 gmsh.write(str(d/'mesh.msh'));gmsh.finalize()
 bc=[k for k,x in nodes.items() if abs(x[2])<1e-7 or abs(x[0]-475)<1e-7];assert len(bc)>20
 s=['** Validation-only remesh of original source BREP. Original targets unchanged.','*NODE,NSET=Nall']+[f'{k},{x[0]:.13g},{x[1]:.13g},{x[2]:.13g}' for k,x in sorted(nodes.items())]+['*ELEMENT,TYPE=S3,ELSET=Eall']+[','.join(map(str,t)) for g in groups for t in g]+['*NSET,NSET=Displacement']
 for i in range(0,len(bc),12):s.append(','.join(map(str,bc[i:i+12])))
 for name,g in zip(['DEPContact','INDContact'],groups):s+=['*SURFACE,NAME='+name]+[f'{t[0]},S2' for t in g]
 s+=['*MATERIAL,NAME=MechanicalMaterial','*ELASTIC','72000,0.3','*SHELL SECTION,ELSET=Eall,MATERIAL=MechanicalMaterial,OFFSET=0','0.5','*CONTACT PAIR,INTERACTION=INTContact,TYPE=SURFACE TO SURFACE','DEPContact,INDContact','*SURFACE INTERACTION,NAME=INTContact','*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR','1000000','*STEP,INC=2000','*STATIC','*BOUNDARY','Displacement,1,3,0','*CLOAD',f'{int(load[0])},2,-5000','*NODE FILE,OUTPUT=3d','U','*EL FILE','S','*NODE PRINT,NSET=Displacement,TOTALS=ONLY','RF','*CONTACT PRINT,MASTER=INDContact,SLAVE=DEPContact','CF, CFN, CFS','*OUTPUT,FREQUENCY=1','*END STEP']
 (d/'contact.inp').write_text('\n'.join(s)+'\n');t=time.monotonic();env=dict(os.environ);env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2');log=d/'solver.log'
 def limit():resource.setrlimit(resource.RLIMIT_CPU,(600,610));resource.setrlimit(resource.RLIMIT_FSIZE,(1024**3,1024**3))
 with log.open('w') as f:
  try:r=subprocess.run([str(ccx.resolve()),'-i','contact'],cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600,preexec_fn=limit)
  except subprocess.TimeoutExpired:r=None
 finished=r is not None and r.returncode==0 and 'Job finished' in log.read_text();a={'h_mm':h,'nodes':len(nodes),'shell_elements':eid-1,'elapsed_seconds':time.monotonic()-t,'solver_finished':finished,'role':'independent mesh validation, same solver family; not benchmark reference','original_geometry_files_sha256':{n:hashlib.sha256((src/'extracted-original'/(n+'.brep')).read_bytes()).hexdigest() for n in ['Lower_tube','Upper_tube']},'constraints':'lower z=0, upper x=475, all translations zero; 5000N downward at (0,76,475); frictionless surface-surface penalty 1e6, 0.5mm S3 shells, E72000 nu0.3, no NLGEOM'}
 if finished:
  b=frd_fields(d/'contact.frd');U=np.array(list(b['DISP'].values()));S=np.array(list(b['STRESS'].values()));vm=np.sqrt(.5*((S[:,0]-S[:,1])**2+(S[:,1]-S[:,2])**2+(S[:,2]-S[:,0])**2)+3*np.sum(S[:,3:]**2,axis=1));a.update(max_displacement_mm=float(np.linalg.norm(U,axis=1).max()),max_vonMises_MPa=float(vm.max()))
 (d/'result.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a),flush=True);return a
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--ccx',type=Path,required=True);p.add_argument('--sizes',type=float,nargs='+',default=[6.4,5.12,4.096]);a=p.parse_args();a.source=a.source.resolve();a.out=a.out.resolve();a.ccx=a.ccx.resolve();a.out.mkdir(parents=True,exist_ok=True)
 for h in a.sizes:run(a.source,a.out,a.ccx,h)
