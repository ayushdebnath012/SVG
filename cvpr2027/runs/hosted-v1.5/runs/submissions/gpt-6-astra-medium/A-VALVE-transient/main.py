"""A-VALVE-transient. Run: python main.py
Dependencies: gmsh 4.15, numpy, scipy, cadquery/OCP; Python 3.12.
3D conforming linear-tetrahedron nonlinear heat conduction; mm, s, W, deg C.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import sys,time,json,re,platform
from pathlib import Path
import numpy as np
import scipy, scipy.sparse as sp
from scipy.sparse.linalg import splu
from scipy.interpolate import CubicHermiteSpline
import gmsh
ROOT=Path(os.environ.get('CADFEM_OUTPUT_DIR','.'))
INP=Path(os.environ['CADFEM_INPUT_DIR'])
LOG=None
def log(s):
 print(s,flush=True)
 if LOG: LOG.write(str(s)+'\n');LOG.flush()
def mesh_build(hlocal,hglobal,filename):
 gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
 gmsh.option.setNumber('General.NumThreads',2)
 gmsh.model.add('valve')
 gmsh.model.occ.importShapes(str(INP/'valve.brep'));gmsh.model.occ.synchronize()
 groups=json.load(open(INP/'faces.json'))['groups']
 for i,(name,tags) in enumerate(groups.items(),1):
  gmsh.model.addPhysicalGroup(2,tags,i,name)
 gmsh.model.addPhysicalGroup(3,[2],11,'carbon')
 gmsh.model.addPhysicalGroup(3,[1,3,4],12,'stainless_SA312')
 gmsh.model.addPhysicalGroup(2,[5,11,16],6,'bonded_interfaces')
 gmsh.option.setNumber('Mesh.MeshSizeFromPoints',1)
 gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',0)
 gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',1)
 f=gmsh.model.mesh.field.add('MathEval')
 gmsh.model.mesh.field.setString(f,'F',f'Min({hglobal}, {hlocal}+0.12*Sqrt(x*x+y*y+(z-53)^2))')
 gmsh.model.mesh.field.setAsBackgroundMesh(f)
 gmsh.option.setNumber('Mesh.Algorithm',1)
 gmsh.option.setNumber('Mesh.Algorithm3D',1)
 gmsh.option.setNumber('Mesh.Optimize',1)
 gmsh.option.setNumber('Mesh.MshFileVersion',4.1)
 gmsh.logger.start()
 gmsh.model.mesh.generate(3)
 gmsh.write(str(filename))
 tags,coords,_=gmsh.model.mesh.getNodes();coords=coords.reshape(-1,3)
 ix=np.argsort(tags);tags=tags[ix];coords=coords[ix]
 tet=[];eid=[];mat=[];solid=[]
 for v in range(1,5):
  et,ids,ns=gmsh.model.mesh.getElements(3,v)
  for typ,ids0,ns0 in zip(et,ids,ns):
   assert typ==4
   tet.append(np.searchsorted(tags,ns0.reshape(-1,4)));eid.extend(ids0);mat.extend([int(v==2)]*len(ids0));solid.extend([v]*len(ids0))
 tri={}
 for name,faces in {**groups,'bonded_interfaces':[5,11,16]}.items():
  arr=[]
  for face in faces:
   typ,ids,ns=gmsh.model.mesh.getElements(2,face)
   for t,n in zip(typ,ns):
    assert t==2
    arr.append(np.searchsorted(tags,n.reshape(-1,3)))
  tri[name]=np.concatenate(arr)
 messages=gmsh.logger.get();gmsh.logger.stop()
 for m in messages:
  if 'Warning' in m or 'Error' in m:log(m)
 gmsh.finalize()
 return coords,np.concatenate(tet),np.array(mat,dtype=bool),tags,np.array(eid),np.array(solid),tri

def props_load():
 text=(INP/'asme-properties.fee').read_text()
 fun={}
 for name in ['k_carbon','kappa_carbon','k_312','kappa_312']:
  data=re.search(r'FUNCTION '+name+r'\(temp\).*?DATA\s*\{(.*?)\}',text,re.S).group(1)
  a=np.array([list(map(float,l.split())) for l in data.strip().splitlines()]);x,y=a.T
  h=np.diff(x);s=np.diff(y)/h;p=(s[:-1]*h[1:]+s[1:]*h[:-1])/(h[:-1]+h[1:])
  der=np.r_[s[0],(np.sign(s[:-1])+np.sign(s[1:]))*np.minimum(np.minimum(abs(s[:-1]),abs(s[1:])),.5*abs(p)),s[-1]]
  fun[name]=CubicHermiteSpline(x,y,der)
 return fun

class Solver:
 def __init__(self,data):
  self.xyz,self.tet,self.carbon,self.tags,self.eids,self.solid,self.tri=data
  self.n=len(self.xyz);self.ne=len(self.tet)
  t=self.tet; xyz=self.xyz[t]
  J=np.transpose(xyz[:,1:]-xyz[:,:1],(0,2,1));self.vol=abs(np.linalg.det(J))/6
  grad=np.empty((len(t),4,3));grad[:,1:,:]=np.linalg.inv(J);grad[:,0,:]=-grad[:,1:,:].sum(axis=1)
  self.kbase=self.vol[:,None,None]*np.einsum('eik,ejk->eij',grad,grad)
  self.mbase=self.vol[:,None,None]*(np.ones((4,4))+np.eye(4))/20
  self.rows=np.broadcast_to(t[:,:,None],(len(t),4,4)).ravel();self.cols=np.broadcast_to(t[:,None,:],(len(t),4,4)).ravel()
  self.D=np.unique(self.tri['internal']);self.free=np.setdiff1d(np.arange(self.n),self.D)
  tri=self.tri['external'];p=self.xyz[tri];area=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)*.5
  rr=np.broadcast_to(tri[:,:,None],(len(tri),3,3)).ravel();cc=np.broadcast_to(tri[:,None,:],(len(tri),3,3)).ravel()
  self.H=sp.coo_matrix(((area[:,None,None]*1e-6/12*(np.ones((3,3))+np.eye(3))).ravel(),(rr,cc)),shape=(self.n,self.n)).tocsr()
  self.f=self.H@np.full(self.n,50.)
  self.fun=props_load()
  self.ramp=np.loadtxt(INP/'internal-temperature.csv')
  self.P=self.probes()
 def probes(self):
  # Locate endpoints using barycentric coordinates in the actual tetrahedra.
  pts=np.array([[3,0,48.5],[3,0,57],[-3,0,48.5],[-3,0,57]])
  v=self.xyz[self.tet];J=np.transpose(v[:,1:]-v[:,:1],(0,2,1));inv=np.linalg.inv(J)
  rows=[];cols=[];vals=[]
  for j,p in enumerate(pts):
   b=np.einsum('eij,ej->ei',inv,p-v[:,0]);w=np.column_stack((1-b.sum(axis=1),b));pen=np.maximum(-w,0).sum(axis=1)
   e=np.argmin(pen)
   log(f'Probe {p.tolist()} element {self.eids[e]} barycentric {w[e].tolist()} violation {pen[e]:.4g}')
   if pen[e]>0.01: raise RuntimeError('Probe outside mesh')
   rows.extend([j]*4);cols.extend(self.tet[e]);vals.extend(w[e])
  return sp.csr_matrix((vals,(rows,cols)),shape=(4,self.n))
 def matrices(self,T):
  # Element-centroid material evaluation. Exact P1 gradients, consistent capacity.
  te=T[self.tet].mean(axis=1)
  k=np.empty(self.ne);c=np.empty(self.ne)
  for mask,suffix in [(self.carbon,'carbon'),(~self.carbon,'312')]:
   k[mask]=.001*self.fun['k_'+suffix](te[mask]);c[mask]=k[mask]/self.fun['kappa_'+suffix](te[mask])
  K=sp.coo_matrix(((k[:,None,None]*self.kbase).ravel(),(self.rows,self.cols)),shape=(self.n,self.n)).tocsr()+self.H
  M=sp.coo_matrix(((c[:,None,None]*self.mbase).ravel(),(self.rows,self.cols)),shape=(self.n,self.n)).tocsr()
  return K,M
 def linear(self,A,rhs,td):
  rhs=rhs[self.free]-np.asarray(A[self.free][:,self.D].sum(axis=1)).ravel()*td
  v=np.full(self.n,td);v[self.free]=splu(A[self.free][:,self.free].tocsc()).solve(rhs)
  return v
 def run(self,dt,save=False):
  start=time.time();T=np.full(self.n,40.)
  for it in range(20):
   K,M=self.matrices(T);new=self.linear(K,self.f,40.)
   err=np.max(abs(new-T));T=new
   if err<1e-7:break
  log(f'Steady state converged {it+1} iterations, T range {T.min():.6f} {T.max():.6f}')
  # Crank-Nicolson with nonlinear Picard iteration; split at all ramp knots and queried time.
  knots=sorted(set(self.ramp[:,0].tolist()+[99.936]))
  times=[0.]
  for a,b in zip(knots[:-1],knots[1:]):
   times.extend(np.linspace(a,b,int(np.ceil((b-a)/dt))+1)[1:])
  times=np.array(times)
  hist=[self.P@T];fields=[T.copy()] if save else []
  maxit=0;maxerr=0.;maxres=0.
  for step,(a,b) in enumerate(zip(times[:-1],times[1:]),1):
   stepdt=b-a;td=float(np.interp(b,self.ramp[:,0],self.ramp[:,1]))
   old=T.copy()
   for it in range(12):
    K,M=self.matrices((T+old)*.5)
    # Conductivity midpoint and capacity midpoint (implicit midpoint rule).
    A=M/stepdt+.5*K
    rhs=(M/stepdt-.5*K)@old+self.f
    new=self.linear(A,rhs,td)
    err=np.max(abs(new-T));T=new
    if err<2e-6:break
   maxit=max(maxit,it+1);maxerr=max(maxerr,err)
   if err>=2e-6: raise RuntimeError('Picard iteration did not converge')
   maxres=max(maxres,float(np.max(abs((A@T-rhs)[self.free]))))
   hist.append(self.P@T)
   if save:fields.append(T.copy())
   if step%50==0:log(f't={b:.3f}, step {step}/{len(times)-1}, nonlinear {it+1}, residual update {err:.2g}, elapsed {time.time()-start:.1f}s')
  hist=np.array(hist);diff=hist[:,[0,2]]-hist[:,[1,3]]
  at=np.argmin(abs(times-99.936))
  out={}
  for j,num in enumerate([2,4]):
   out[f'scl{num}_dT_max_K']=float(diff[:,j].max());out[f'scl{num}_dT_min_K']=float(diff[:,j].min())
   out[f'scl{num}_T_outer_100s_C']=float(hist[at,2*j+1])
  log(f'Completed {len(times)-1} steps in {time.time()-start:.1f}s, max iterations {maxit}, final update max {maxerr:.3g}; outputs {out}')
  return out,times,hist,np.array(fields),{'max_picard_iterations':maxit,'max_final_update_C':maxerr,'max_free_node_algebraic_residual_W':maxres}

def main():
 global LOG
 ROOT.mkdir(exist_ok=True,parents=True);os.chdir(ROOT)
 LOG=open('solver.log','w');log('python main.py; nonlinear 3D thermal FEM; '+platform.platform())
 log(f'Python {sys.version}; numpy {np.__version__}; scipy {scipy.__version__}; gmsh {gmsh.__version__}')
 # Gmsh retains all original analytic CAD surfaces and four shared-face solids.
 gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.model.occ.importShapes(str(INP/'valve.brep'));gmsh.model.occ.synchronize();gmsh.write('part.step');gmsh.finalize()
 studies=[]
 for j,(hl,hg,dt) in enumerate([(1.5,17.,2.5),(.5,11.,2.5),(.5,11.,1.25)]):
  if j<2:
   start=time.time();data=mesh_build(hl,hg,'mesh.msh' if j==1 else 'mesh_coarse.msh');log(f'Mesh {j}: {len(data[0])} nodes {len(data[1])} tets, {time.time()-start:.1f}s')
   s=Solver(data)
   log(f'Volume by solid mm^3: {[float(s.vol[s.solid==v].sum()) for v in range(1,5)]}; min tetra volume {s.vol.min():.6g}')
  out,times,hist,fields,diag=s.run(dt,save=j==2)
  studies.append(dict(local_size_mm=hl,global_size_mm=hg,dt_max_s=dt,nodes=s.n,tetrahedra=s.ne,mesh_volume_mm3=float(s.vol.sum()),outputs=out,diagnostics=diag))
  if j==2:
   np.savez_compressed('fields.npz',node_ids=s.tags,coordinates_mm=s.xyz,tetra_node_indices=s.tet,element_ids=s.eids,solid_ids=s.solid,carbon_element_mask=s.carbon,times_s=times,temperature_C=fields,probe_temperature_C=hist,probe_coordinates_mm=np.array([[3,0,48.5],[3,0,57],[-3,0,48.5],[-3,0,57]]),internal_node_mask=np.isin(np.arange(s.n),s.D),external_triangles=s.tri['external'],symmetry_triangles=s.tri['symmetry'],end_triangles=np.concatenate([s.tri['end_carbon'],s.tri['end_stainless']]),length_unit=np.array('mm'),temperature_unit=np.array('deg C'),time_unit=np.array('s'))
 json.dump({'outputs':out},open('results.json','w'),indent=2)
 spatial={key:studies[1]['outputs'][key]-studies[0]['outputs'][key] for key in out}
 temporal={key:studies[2]['outputs'][key]-studies[1]['outputs'][key] for key in out}
 log(f'Spatial refinement differences: {spatial}; time-step differences: {temporal}')
 json.dump({'studies':studies,'spatial_refinement_change':spatial,'time_refinement_change':temporal,'method':'Two independent mesh resolutions at identical dt, then dt halved on finer mesh; reported values from finer mesh and time step, no extrapolation.'},open('refinement.json','w'),indent=2)
 env={'command':'python main.py','versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'gmsh':gmsh.__version__},'units':{'length':'mm','time':'s','temperature':'deg C','conductivity':'W/(mm K)','diffusivity':'mm^2/s','capacity':'W s/(mm^3 K)'},'model':'Full supplied four-solid half model, conforming P1 tetrahedra and perfect welded contact. No geometric reduction. Adiabatic symmetry and ends. Internal Dirichlet from supplied ramp; external h=1e-6 to 50 C. Steady state at t=0.', 'material':'Solid 2 carbon, solids 1/3/4 SA312. Steffen monotone cubic interpolation of supplied k and kappa, k multiplied by 0.001, volumetric heat capacity k/kappa. Material evaluated at tetrahedron centroid temperature.', 'time_integration':'Nonlinear implicit midpoint with consistent mass; Picard iteration to maximum nodal update <2e-6 C. Steps split at ramp breakpoints and 99.936s.', 'physical_groups':{'1':'internal','2':'external','3':'symmetry','4':'end_carbon','5':'end_stainless','6':'bonded_interfaces','11':'carbon volume 2','12':'stainless volumes 1,3,4'}, 'field_schema':{'node_ids':'Gmsh tags, array row order for nodal fields','coordinates_mm':'(nodes,3), original coordinate frame','tetra_node_indices':'(elements,4), zero-based row indices in coordinates_mm','element_ids':'Gmsh tetrahedron element tags','solid_ids':'original CAD solid tags 1..4','carbon_element_mask':'boolean material mask','times_s':'all time steps, includes initial steady state','temperature_C':'(times,nodes), computed nodal values','probe_temperature_C':'(times,4): SCL2 inner,outer,SCL4 inner,outer; tetrahedral barycentric interpolation','probe_coordinates_mm':'(4,3) exact requested locations','internal_node_mask':'boolean Dirichlet node mask','external_triangles':'zero-based nodal indices for Robin facets','symmetry_triangles':'zero-based nodal indices for adiabatic symmetry facets'},'extraction':'Maximum/minimum of inner minus outer over all computed time steps; outer temperatures at explicitly included 99.936 s; no averaging across SCLs.'}
 env['field_schema'].update({'end_triangles':'zero-based nodal indices for the two adiabatic end surfaces','length_unit':'Unicode scalar mm','temperature_unit':'Unicode scalar deg C','time_unit':'Unicode scalar s'})
 env['mesh_protocol']='Gmsh MeshAdapt surfaces, Delaunay tetrahedra, linear geometry. Original BREP face tags preserved. Mesh size background min(global_size, local_size+0.12*sqrt(x^2+y^2+(z-53)^2)), with boundary extension enabled. Fine mesh is shared between the final two time-step studies.'
 env['limitations']='P1 straight-sided tetrahedra approximate curved CAD; constitutive coefficients use centroid quadrature. Spatial and temporal sensitivity is quantified in refinement.json. Time extrema are maxima/minima of discrete time histories, including exact ramp knots.'
 env['threads']={'gmsh':2,'linear_algebra':1}
 json.dump(env,open('environment.json','w'),indent=2);log('Normal termination');LOG.close()
if __name__=='__main__':main()
