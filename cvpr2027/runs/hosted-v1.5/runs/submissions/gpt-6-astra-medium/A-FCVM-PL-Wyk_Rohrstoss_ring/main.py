"""Small-strain quadratic-tetrahedral J2 plasticity. Python 3.12, gmsh, numpy, scipy.
Run: CADFEM_INPUT_DIR=... CADFEM_OUTPUT_DIR=... python main.py
Quarter model: X=(x-y)/sqrt(2), Y=(x+y)/sqrt(2). Symmetry at Y=0,
antisymmetry at X=0. Full supplied physical solid is retained in part.step.
"""
import os,time,json,shutil,sys
os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['VECLIB_MAXIMUM_THREADS']='2';os.environ['OMP_NUM_THREADS']='2'
import numpy as np, scipy, scipy.sparse as sp, scipy.sparse.linalg as sla
import gmsh
from threadpoolctl import threadpool_limits
threadpool_limits(2)
E=210000.; nu=.3; sy=235.; mu=E/(2*(1+nu)); bulk=E/(3*(1-2*nu))
i6=np.array([1.,1.,1.,0,0,0]); P=np.eye(6)-np.outer(i6,i6)/3
C=bulk*np.outer(i6,i6)+2*mu*P
ROT=np.array([[1,-1,0],[1,1,0],[0,0,2**.5]])/2**.5
start=time.time()
def log(*x):print(*x,flush=True)
def mesh(h,filename):
 gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',1)
 v=gmsh.model.occ.importShapes(os.environ['CADFEM_INPUT_DIR']+'/analysis.step')
 gmsh.model.occ.rotate(v,0,0,0,0,0,1,np.pi/4)
 b=gmsh.model.occ.addBox(0,0,-1,300,300,402)
 v,_=gmsh.model.occ.intersect(v,[(3,b)])
 v,_=gmsh.model.occ.fragment(v[:1],v[1:]);gmsh.model.occ.synchronize()
 groups={'fixed':[], 'symmetry_Y':[], 'antisymmetry_X':[], 'traction_minus_z':[], 'traction_plus_X':[]}
 for d,t in gmsh.model.getEntities(2):
  c=np.array(gmsh.model.occ.getCenterOfMass(d,t)); a=gmsh.model.occ.getMass(d,t); typ=gmsh.model.getType(d,t)
  if typ=='Cylinder' and abs(c[2]-10)<1e-5:groups['fixed'].append(t)
  if typ=='Plane':
   bb=gmsh.model.getBoundingBox(d,t)
   if abs(bb[1])<1e-5 and abs(bb[4])<1e-5:groups['symmetry_Y'].append(t)
   if abs(bb[0])<1e-5 and abs(bb[3])<1e-5:groups['antisymmetry_X'].append(t)
   if abs(c[0]-65)<1e-5 and abs(c[2]-390)<1e-5:groups['traction_minus_z'].append(t)
   if abs(c[2]-400)<1e-5:groups['traction_plus_X'].append(t)
 for tag,(name,s) in enumerate(groups.items(),1):gmsh.model.addPhysicalGroup(2,s,tag,name)
 gmsh.model.addPhysicalGroup(3,[t for d,t in v],10,'steel_continuous_body')
 gmsh.option.setNumber('Mesh.MeshSizeMin',min(3,h/6));gmsh.option.setNumber('Mesh.MeshSizeMax',h)
 gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',max(16,round(340/h)))
 gmsh.option.setNumber('Mesh.Algorithm3D',1);gmsh.model.mesh.generate(3);gmsh.model.mesh.setOrder(2)
 ids,coords,_=gmsh.model.mesh.getNodes(); order=np.argsort(ids);ids=ids[order];xyz=coords.reshape(-1,3)[order]
 et,eid,conn=gmsh.model.mesh.getElements(3); ix=list(et).index(11); tet=np.searchsorted(ids,conn[ix].reshape(-1,10)); eid=eid[ix]
 n=len(ids); fixed=np.zeros((n,3),bool);force=np.zeros((n,3)); surf={}
 for name,tags in groups.items():
  sn=[];tris=[]
  for t in tags:
   nd=gmsh.model.mesh.getNodes(2,t,True)[0];sn.extend(np.searchsorted(ids,nd))
   types,_,nodes=gmsh.model.mesh.getElements(2,t)
   for typ,nd in zip(types,nodes):
    if typ==9:tris.extend(np.searchsorted(ids,nd.reshape(-1,6)))
  sn=np.unique(sn);surf[name]=sn
  if name=='fixed':fixed[sn,:]=True
  if name=='symmetry_Y':fixed[sn,1]=True
  if name=='antisymmetry_X':fixed[np.ix_(sn,[1,2])]=True
  if name.startswith('traction'):
   tr=np.array(tris);pt=xyz[tr[:,:3]];a=np.linalg.norm(np.cross(pt[:,1]-pt[:,0],pt[:,2]-pt[:,0]),axis=1)/2
   vec=np.array([0.,0.,-43.521099]) if name=='traction_minus_z' else np.array([np.sqrt(2)*.213062,0,0])
   for j in [3,4,5]:np.add.at(force,tr[:,j],a[:,None]*vec/3)
   log(name,'CAD/mesh area',sum(gmsh.model.occ.getMass(2,t) for t in tags),a.sum(),'resultant',vec*a.sum())
 # actual analysis mesh exported in original frame
 for tag,p in zip(ids,xyz@ROT):gmsh.model.mesh.setNode(int(tag),p.tolist(),[])
 gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.write(filename);gmsh.finalize()
 log('mesh',h,n,len(tet),'fixed dofs',fixed.sum(),'vol target',2577880/4)
 return ids,xyz,tet,eid,fixed,force,surf,groups

def operators(xyz,tet,fixed):
 # Four-point symmetric rule on reference tetrahedron, Gmsh tet10 ordering.
 a=.5854101966249685;b=.1381966011250105
 L=np.full((4,4),b);np.fill_diagonal(L,a)
 dL=np.array([[-1.,-1,-1],[1,0,0],[0,1,0],[0,0,1]])
 pairs=[(0,1),(1,2),(2,0),(0,3),(2,3),(1,3)]
 dN=np.empty((4,10,3))
 for q in range(4):
  dN[q,:4]=(4*L[q,:]-1)[:,None]*dL
  for k,(i,j) in enumerate(pairs,4):dN[q,k]=4*(L[q,i]*dL[j]+L[q,j]*dL[i])
 jac=np.einsum('eni,qnj->eqij',xyz[tet],dN)
 det=np.linalg.det(jac);weights=np.abs(det)/24
 grad=np.einsum('qnj,eqjk->eqnk',dN,np.linalg.inv(jac))
 ne=len(tet);B=np.zeros((ne,4,6,30));rt=np.sqrt(2)
 B[:,:,0,0::3]=grad[:,:,:,0];B[:,:,1,1::3]=grad[:,:,:,1];B[:,:,2,2::3]=grad[:,:,:,2]
 B[:,:,3,0::3]=grad[:,:,:,1]/rt;B[:,:,3,1::3]=grad[:,:,:,0]/rt
 B[:,:,4,1::3]=grad[:,:,:,2]/rt;B[:,:,4,2::3]=grad[:,:,:,1]/rt
 B[:,:,5,2::3]=grad[:,:,:,0]/rt;B[:,:,5,0::3]=grad[:,:,:,2]/rt
 ed=(3*tet[:,:,None]+np.arange(3)).reshape(ne,30)
 free=np.flatnonzero(~fixed.ravel());renum=np.full(xyz.size,-1);renum[free]=np.arange(len(free));edfree=renum[ed]
 rows=np.broadcast_to(np.arange(ne*4*6).reshape(ne,4,6,1),B.shape).ravel()
 cols=np.broadcast_to(edfree[:,None,None,:],B.shape).ravel();vals=B.ravel();ok=(cols>=0)&(vals!=0)
 Bs=sp.coo_matrix((vals[ok],(rows[ok],cols[ok])),shape=(ne*24,len(free))).tocsr()
 log('quadrature volume',weights.sum(),'Jacobian range',det.min(),det.max(),'free',len(free))
 N=np.empty((4,10));N[:,:4]=L*(2*L-1)
 for k,(i,j) in enumerate(pairs,4):N[:,k]=4*L[:,i]*L[:,j]
 qxyz=np.einsum('qn,eni->eqi',N,xyz[tet])
 return Bs,weights.ravel(),free,ed,B,qxyz

def constitutive(eps,ep):
 trial=(eps-ep)@C;dev=trial-(trial[:,:3].sum(1)/3)[:,None]*i6
 norm=np.linalg.norm(dev,axis=1);vm=np.sqrt(1.5)*norm;fac=np.minimum(1,sy/np.maximum(vm,1e-30))
 sigma=(trial[:,:3].sum(1)/3)[:,None]*i6+fac[:,None]*dev
 nn=dev/np.maximum(norm[:,None],1e-30);plastic=vm>sy
 D=bulk*np.outer(i6,i6)[None,:,:]+(2*mu*fac)[:,None,None]*(P[None,:,:]-plastic[:,None,None]*np.einsum('qi,qj->qij',nn,nn))
 return sigma,D,plastic,vm

def solve(h,filename,targets):
 ids,xyz,tet,eid,fixed,force,surf,groups=mesh(h,filename)
 B,w,free,ed,Bloc,qxyz=operators(xyz,tet,fixed);f=force.ravel()[free];nd=len(f);nq=len(w)
 # block diagonal constitutive operator
 rr=np.repeat(np.arange(nq*6),6);cc=(np.arange(nq)[:,None,None]*6+np.arange(6)[None,None,:]+np.zeros((1,6,1),int)).ravel()
 def stiff(D):
  Db=sp.coo_matrix(((D*w[:,None,None]).ravel(),(rr,cc)),shape=(6*nq,6*nq)).tocsr()
  return (B.T@Db@B).tocsc()
 K0=stiff(np.broadcast_to(C,(nq,6,6))); log('stiffness nnz',K0.nnz)
 ts=time.time();lu=sla.splu(K0,permc_spec='MMD_AT_PLUS_A');uel=lu.solve(f);log('elastic factor',time.time()-ts)
 compliance=f@uel;log('reference compliance Nmm',compliance,'peak disp',max(abs(uel)))
 u=np.zeros(nd);lam=0.;ep=np.zeros((nq,6));history=[];all_u=[];all_lam=[];last_vm=None;prev_du=uel.copy();prev_dl=1.;prev_dt=1.;prev_target=0.;eqp=np.zeros(nq)
 for target in targets:
  old=u.copy();oldlam=lam; goal=target*compliance
  # Secant predictor respecting prescribed generalized displacement
  dt=target-prev_target;u+=prev_du*(dt/prev_dt);lam+=prev_dl*(dt/prev_dt)
  converged=False
  for it in range(40):
   eps=(B@u).reshape(-1,6);sigma,D,pl,vm=constitutive(eps,ep)
   fint=B.T@(sigma*w[:,None]).ravel();r=lam*f-fint
   residual=np.linalg.norm(r)/max(np.linalg.norm(lam*f),1.)
   if residual<2e-6 and abs(goal-f@u)<1e-7*max(goal,1.):converged=True;break
   K=stiff(D);lu=sla.splu(K,permc_spec='MMD_AT_PLUS_A')
   both=lu.solve(np.column_stack([r,f]));du0,duf=both.T
   dl=(goal-f@u-f@du0)/(f@duf);du=du0+dl*duf
   # backtracking on residual + work constraint (generally full Newton)
   alpha=1.;rnorm=np.linalg.norm(r)
   for ls in range(9):
    un=u+alpha*du;ln=lam+alpha*dl
    sn,_,_,_=constitutive((B@un).reshape(-1,6),ep)
    rn=ln*f-B.T@(sn*w[:,None]).ravel()
    if np.linalg.norm(rn)<rnorm*(1-1e-4*alpha) or alpha<=1/256:break
    alpha*=.5
   u=un;lam=ln
  eps=(B@u).reshape(-1,6);sigma,D,pl,vm=constitutive(eps,ep)
  ep_old=ep.copy()
  ep=eps-((sigma-(sigma[:,:3].sum(1)/3)[:,None]*i6)/(2*mu)+(sigma[:,:3].sum(1)/(9*bulk))[:,None]*i6)
  eqp+=np.sqrt(2/3)*np.linalg.norm(ep-ep_old,axis=1)
  full=np.zeros(xyz.size);full[free]=u
  top=surf['traction_plus_X'];ux=full.reshape(-1,3)[top,0].mean()
  hist={'control_multiple':target,'load_factor':float(lam),'mean_top_displacement_X_mm':float(ux),'work_displacement_mm':float(f@u/np.linalg.norm(force.sum(0))), 'peak_displacement_mm':float(np.max(abs(u))), 'newton_iterations':it,'relative_residual':float(residual),'converged':converged,'yielded_volume_fraction':float(w[pl].sum()/w.sum())}
  prev_du=u-old;prev_dl=lam-oldlam;prev_dt=dt;prev_target=target
  history.append(hist);all_u.append(full.reshape(-1,3));all_lam.append(lam)
  log('STEP',h,hist,'elapsed',time.time()-start)
  if not converged:raise RuntimeError('nonlinear equilibrium did not converge')
 fint_element=np.einsum('eqsa,eqs,eq->ea',Bloc,sigma.reshape(-1,4,6),w.reshape(-1,4))
 internal=np.zeros(xyz.size);np.add.at(internal,ed.ravel(),fint_element.ravel())
 reactions=internal.reshape(-1,3)-lam*force
 actual_vm=np.sqrt(1.5)*np.linalg.norm(sigma-(sigma[:,:3].sum(1)/3)[:,None]*i6,axis=1)
 log('Final diagnostics: max von Mises MPa',actual_vm.max(),'max trace plastic strain',np.abs(ep[:,:3].sum(1)).max(),'free equilibrium residual N',np.linalg.norm(reactions.ravel()[free]))
 return {'h_mm':h,'nodes':len(ids),'tetrahedra':len(tet),'dofs':nd,'quadrature_volume_mm3':w.sum(),'limit_load_factor':float(lam),'plateau_last_relative_change':float(lam/all_lam[-2]-1),'elastic_reference_compliance_N_mm':float(compliance),'curve':history},(ids,xyz,tet,eid,fixed,force,np.array(all_u),np.array(all_lam),sigma,ep,w,surf,reactions,eqp,qxyz,actual_vm)

def main():
 out=os.environ.get('CADFEM_OUTPUT_DIR','.');os.chdir(out)
 sys.stdout=open('solver.log','w',buffering=1);sys.stderr=sys.stdout
 log('Python',sys.version,'numpy',np.__version__,'scipy',scipy.__version__,'gmsh',gmsh.__version__)
 shutil.copyfile(os.environ['CADFEM_INPUT_DIR']+'/analysis.step','part.step')
 targets=[.2,.6,1,1.3,1.6,2,2.5,3,4,5,6,8,10,15,20,30,50,80,120]
 refs=[]
 for h in [12.,9.]:
  ref,fields=solve(h,'mesh.msh',targets);refs.append(ref)
 ids,xyz,tet,eid,fixed,force,us,lams,stress,ep,w,surf,reactions,eqp,qxyz,actual_vm=fields
 # Mandel stresses and plastic strains are in the analysis X,Y,Z frame.
 np.savez_compressed('fields.npz',node_ids=ids,coordinates_mm=xyz@ROT,solver_coordinates_mm=xyz,element_ids=eid,tetrahedra_node_ids=ids[tet],displacement_mm=us@ROT,load_factors=lams,force_reference_N=force@ROT,fixed_mask_solver_frame=fixed,stress_Mandel_MPa=stress.reshape(-1,4,6),plastic_strain_Mandel=ep.reshape(-1,4,6),equivalent_plastic_strain=eqp.reshape(-1,4),von_Mises_MPa=actual_vm.reshape(-1,4),reaction_N=reactions@ROT,quadrature_coordinates_mm=qxyz@ROT,quadrature_weights_mm3=w.reshape(-1,4),**{k+'_node_ids':ids[v] for k,v in surf.items()})
 json.dump({'outputs':{'limit_load_factor':refs[-1]['limit_load_factor']}},open('results.json','w'),indent=2)
 json.dump({'resolutions':refs,'relative_mesh_change':abs(refs[-1]['limit_load_factor']/refs[-2]['limit_load_factor']-1),'acceptance':'Two actual quadratic meshes; final load change across last displacement increment <0.1%, relative mesh change <0.5%. No Richardson extrapolation applied.'},open('refinement.json','w'),indent=2)
 env={'invocation':'python main.py','versions':{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'gmsh':gmsh.__version__},'units':{'length':'mm','stress':'MPa','force':'N'},'material':{'E_MPa':E,'poisson_ratio':nu,'yield_stress_MPa':sy,'hardening':0},'formulation':'Isoparametric 10-node tetrahedra, 4-point quadrature. Small-strain incremental associated von Mises plasticity, backward-Euler radial return and consistent tangent. Work-conjugate displacement control with unknown load multiplier; all loads scale together.','symmetry':'Full solid in part.step; mesh is quarter body X>=0,Y>=0 where [X,Y,Z]=ROT*[x,y,z]. ROT is +45deg about z. At Y=0 uY=0; at X=0 uY=uZ=0 (antisymmetry in bending). J2 invariance under stress sign change allows antisymmetric quarter. Mesh and exported displacements use original physical frame.','rotation_matrix':ROT.tolist(),'physical_groups':{'1':'fixed cylindrical shaft surfaces','2':'Y=0 symmetry','3':'X=0 antisymmetry','4':'face52 half, traction -43.521099 MPa z','5':'face55 quarter, traction (0.213062,-0.213062,0) MPa','10':'continuous steel, shared nodes on all region interfaces'},'extraction':'Largest computed equilibrated load factor at large work-controlled displacement; plateau checked at final increments. See actual curves and mesh convergence in refinement.json.','field_schema':{'equivalent_plastic_strain':'element x 4, accumulated sqrt(2/3)*norm(plastic strain increments), final','von_Mises_MPa':'element x 4 final equivalent stress','reaction_N':'node x 3, final internal minus external nodal force, original frame; unconstrained entries are equilibrium residuals','quadrature_coordinates_mm':'element x 4 x 3 physical integration locations in original frame; tetra barycentric rule diagonal 0.5854101966 and off-diagonal 0.1381966011','node_ids':'Gmsh global node IDs, sorted','coordinates_mm':'n x 3 original frame','solver_coordinates_mm':'n x 3 rotated frame','tetrahedra_node_ids':'e x 10 Gmsh tet10 connectivity','element_ids':'Gmsh 3D element IDs','displacement_mm':'step x node x 3 original frame','load_factors':'step, proportional applied load factor','force_reference_N':'node x 3 assembled equivalent nodal reference loads in original frame','fixed_mask_solver_frame':'node x 3 boolean essential BC mask in X Y Z','stress_Mandel_MPa':'element x 4 quadrature points x [XX,YY,ZZ,sqrt2 XY,sqrt2 YZ,sqrt2 ZX], final state, rotated solver frame','plastic_strain_Mandel':'same order/frame as stress, dimensionless','quadrature_weights_mm3':'element x 4 physical integration volumes','*_node_ids':'boundary-set nodes as named'},'limitations':'Four-point integration and quarter symmetry; no geometric nonlinearity, no hardening. Finite displacement plateau is an approximation to asymptotic limit. The very large formal displacements used to approach the plateau do not update geometry; they are a numerical limit-load device, not a prediction of geometrically nonlinear deformation.'}
 json.dump(env,open('environment.json','w'),indent=2);log('SUCCESS',time.time()-start)
if __name__=='__main__':main()
