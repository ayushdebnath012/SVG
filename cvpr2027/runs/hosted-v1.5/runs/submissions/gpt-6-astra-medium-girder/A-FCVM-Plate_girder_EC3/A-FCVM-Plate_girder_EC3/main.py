"""Plate girder elastic buckling. Python 3.12, numpy/scipy, meshio, cadquery.
Run: CADFEM_INPUT_DIR=... CADFEM_OUTPUT_DIR=... python main.py
Flat MITC4 shell reduction of the supplied bonded steel plates; exact STEP retained.
"""
import os,time,json,shutil,sys,platform
os.environ['OPENBLAS_NUM_THREADS']='2'
os.environ['OMP_NUM_THREADS']='2'
import numpy as np
import scipy, scipy.sparse as sp
from scipy.sparse.linalg import splu, eigsh, LinearOperator
import meshio
from pathlib import Path
E=210000.; nu=.3
C=E/(1-nu**2)*np.array([[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]])
OUT=Path(os.environ.get('CADFEM_OUTPUT_DIR','.')); OUT.mkdir(exist_ok=True)
log=None
def say(*a):
 print(*a,flush=True)
 if log: print(*a,file=log,flush=True)
def split(v,h):
 v=sorted(set(v)); return np.concatenate([np.linspace(a,b,int(np.ceil((b-a)/h))+1)[:-1] for a,b in zip(v[:-1],v[1:])]+[np.array([v[-1]])])
def build(h):
 nodes=[]; lookup={}; elems=[]; typ=[]; thick=[]; ecc=[]; grp=[]
 def node(p):
  k=tuple(np.round(p,7))
  if k not in lookup: lookup[k]=len(nodes); nodes.append(p)
  return lookup[k]
 def panel(a,b,kind,pos,t,g):
  nn=np.empty((len(a),len(b)),int)
  for i,x in enumerate(a):
   for j,y in enumerate(b):
    p=([x,y,pos] if kind==0 else [x,pos,y] if kind==1 else [pos,x,y]); nn[i,j]=node(p)
  for i in range(len(a)-1):
   for j in range(len(b)-1):
    tt=t; ee=0.
    if kind==0 and pos==25 and (9262.5<(a[i]+a[i+1])/2<9437.5 or 20562.5<(a[i]+a[i+1])/2<20737.5) and 287.5<(b[j]+b[j+1])/2<462.5: tt=100.;ee=-25.
    elems.append([nn[i,j],nn[i+1,j],nn[i+1,j+1],nn[i,j+1]]);typ.append(kind);thick.append(tt);ecc.append(ee);grp.append(g)
 xs=[0,50,62,74,1550,5450,9262.5,9350,9437.5,15000,20562.5,20650,20737.5,24550,28450,29926,29938,29950,30000]
 x=split(xs,h); y=split([0,87.5,287.5,367.5,375,382.5,462.5,662.5,750],h); z=split([25,510,2075],h)
 panel(x,y,0,25,50,1);panel(x,y,0,2075,50,2)
 panel(x,z,1,375,15,3)
 panel(x[(x>=62)&(x<=29938)],y[(y>=287.5)&(y<=462.5)],0,510,20,4)
 for p in [62,1550,5450,9350,15000,20650,24550,28450,29938]:
  end=p in [62,29938]; lo,hi=(87.5,662.5) if end else (287.5,462.5)
  panel(y[(y>=lo)&(y<=hi)],z,2,p,24 if end else 15,5 if end else 6)
 p=np.array(nodes); e=np.array(elems); typ=np.array(typ); thick=np.array(thick);ecc=np.array(ecc);grp=np.array(grp)
 # local-to-global index maps (right handed frames)
 maps=np.array([[0,1,2,3,4,5],[0,2,1,3,5,4],[1,2,0,4,5,3]])
 signs=np.array([[1,1,1,1,1,1],[1,1,-1,1,1,-1],[1,1,1,1,1,1]])
 dofs=(e[:,:,None]*6+maps[typ,None,:]).reshape(-1,24); signs=np.tile(signs[typ],(1,4))
 hx=np.linalg.norm(p[e[:,1]]-p[e[:,0]],axis=1);hy=np.linalg.norm(p[e[:,3]]-p[e[:,0]],axis=1)
 return p,e,typ,thick,ecc,grp,dofs,signs,hx,hy

def shapes(x,y):
 sx=np.array([-1,1,1,-1]);sy=np.array([-1,-1,1,1]);return (1+sx*x)*(1+sy*y)/4,sx*(1+sy*y)/4,sy*(1+sx*x)/4

def matrices(hx,hy,x,y):
 n=len(hx);N,dx,dy=shapes(x,y); dx=2*dx[None,:]/hx[:,None];dy=2*dy[None,:]/hy[:,None]
 bm=np.zeros((n,3,24));bb=bm.copy(); bd=np.zeros((n,1,24))
 bm[:,0,0::6]=dx;bm[:,1,1::6]=dy;bm[:,2,0::6]=dy;bm[:,2,1::6]=dx
 bb[:,0,4::6]=dx;bb[:,1,3::6]=-dy;bb[:,2,4::6]=dy;bb[:,2,3::6]=-dx
 bd[:,0,5::6]=N;bd[:,0,1::6]=-.5*dx;bd[:,0,0::6]=.5*dy
 bs=np.zeros((n,2,24))
 # MITC4 covariant shear interpolation; rectangles have constant Jacobian.
 for eta in [-1,1]:
  nt,dxt,dyt=shapes(0,eta);w=(1+y*eta)/2
  bs[:,0,2::6]+=w*2*dxt[None,:]/hx[:,None];bs[:,0,4::6]+=w*nt
 for xi in [-1,1]:
  nt,dxt,dyt=shapes(xi,0);w=(1+x*xi)/2
  bs[:,1,2::6]+=w*2*dyt[None,:]/hy[:,None];bs[:,1,3::6]-=w*nt
 return bm,bb,bs,bd,dx,dy

def prod(a,c,b): return np.einsum('eia,ij,ejb->eab',a,c,b,optimize=True)
def sparsemat(v,dof,nd):
 return sp.coo_matrix((v.ravel(),(np.broadcast_to(dof[:,:,None],v.shape).ravel(),np.broadcast_to(dof[:,None,:],v.shape).ravel())),shape=(nd,nd)).tocsc()
def stiffness(hx,hy,t,ec,dof,sg,nd):
 ne=len(t); ke=np.zeros((ne,24,24));area=hx*hy/4
 for x in [-1/np.sqrt(3),1/np.sqrt(3)]:
  for y in [-1/np.sqrt(3),1/np.sqrt(3)]:
   bm,bb,bs,bd,dx,dy=matrices(hx,hy,x,y)
   ke+=prod(bm,C,bm)*(area*t)[:,None,None]
   a=prod(bm,C,bb);ke+=(a+a.swapaxes(1,2))*(area*t*ec)[:,None,None]
   ke+=prod(bb,C,bb)*(area*(t**3/12+t*ec**2))[:,None,None]
   ke+=prod(bs,np.eye(2),bs)*(area*E/(2*(1+nu))*t*5/6)[:,None,None]
   ke+=prod(bd,np.eye(1),bd)*(area*E*t*1e-4)[:,None,None]
 ke*=sg[:,:,None]*sg[:,None,:]
 return sparsemat(ke,dof,nd)

def geometric(hx,hy,t,ec,dof,sg,nd,ul):
 ne=len(t);kg=np.zeros((ne,24,24));area=hx*hy/4; stress=[]
 for x in [-1/np.sqrt(3),1/np.sqrt(3)]:
  for y in [-1/np.sqrt(3),1/np.sqrt(3)]:
   bm,bb,bs,bd,dx,dy=matrices(hx,hy,x,y)
   eps=np.einsum('eij,ej->ei',bm,ul);kap=np.einsum('eij,ej->ei',bb,ul)
   sm=eps@C.T;sk=kap@C.T
   stress.append(np.stack([sm+(ec-t/2)[:,None]*sk,sm+(ec+t/2)[:,None]*sk],axis=1))
   for zz in [-1/np.sqrt(3),1/np.sqrt(3)]:
    z=ec+zz*t/2;s=sm+z[:,None]*sk
    S=np.empty((ne,2,2));S[:,0,0]=s[:,0];S[:,1,1]=s[:,1];S[:,0,1]=S[:,1,0]=s[:,2]
    for comp in range(3):
     bg=np.zeros((ne,2,24));bg[:,0,comp::6]=dx;bg[:,1,comp::6]=dy
     if comp<2:
      rc=4 if comp==0 else 3;ss=1 if comp==0 else -1
      bg[:,0,rc::6]=ss*z[:,None]*dx;bg[:,1,rc::6]=ss*z[:,None]*dy
     kg+=np.einsum('eia,eij,ejb->eab',bg,S,bg,optimize=True)*(area*t/2)[:,None,None]
 kg*=sg[:,:,None]*sg[:,None,:]
 return sparsemat(kg,dof,nd),np.stack(stress,axis=1)

def loading(p,e,typ,grp,hx,hy):
 F=np.zeros((len(p),6));cent=p[e].mean(axis=1)
 # Pressure on the 15-mm bottom-flange strip; exclude the two bearing plates.
 bot=grp==1;top=grp==2
 patch=((cent[:,0]>9262.5)&(cent[:,0]<9437.5))|((cent[:,0]>20562.5)&(cent[:,0]<20737.5))
 strip=bot&(cent[:,0]>50)&(cent[:,0]<29950)&(cent[:,1]>367.5)&(cent[:,1]<382.5)&~patch
 bear=bot&patch&(cent[:,1]>287.5)&(cent[:,1]<462.5)
 end=top&(((cent[:,0]>50)&(cent[:,0]<74))|((cent[:,0]>29926)&(cent[:,0]<29950)))&(cent[:,1]>87.5)&(cent[:,1]<662.5)
 pressure=5.423191*strip+(30.204082+5.423191)*bear-166.15942*end
 for i in range(4): np.add.at(F[:,2],e[:,i],pressure*hx*hy/4)
 return F.ravel(),np.stack([strip,bear,end],axis=1)

def constraints(p):
 nd=len(p)*6; left=np.isclose(p[:,0],50)&np.isclose(p[:,2],2075)&(p[:,1]>=87.5)&(p[:,1]<=662.5)
 right=np.isclose(p[:,0],29950)&np.isclose(p[:,2],2075)&(p[:,1]>=87.5)&(p[:,1]<=662.5)
 fixed=np.zeros(nd,bool);relations={}
 for i in np.flatnonzero(left|right):
  fixed[6*i+1:6*i+3]=True;relations[6*i+1]=(6*i+3,25.)
  if left[i]: fixed[6*i]=True;relations[6*i]=(6*i+4,-25.)
 free=np.flatnonzero(~fixed);inv=np.full(nd,-1,int);inv[free]=np.arange(len(free)); scale=np.ones(nd);scale[np.arange(nd)%6>=3]=.01
 rows=list(free);cols=list(range(len(free)));vals=list(scale[free])
 for i,(j,v) in relations.items():rows.append(i);cols.append(inv[j]);vals.append(v*scale[j])
 T=sp.coo_matrix((vals,(rows,cols)),shape=(nd,len(free))).tocsc()
 return T,left,right,fixed.reshape(-1,6)

def run(h,save=False):
 start=time.time();p,e,typ,t,ec,grp,dof,sg,hx,hy=build(h);nd=len(p)*6
 say('Mesh h',h,'nodes',len(p),'quads',len(e),'DOFs',nd)
 K=stiffness(hx,hy,t,ec,dof,sg,nd);say('K assembly',time.time()-start)
 F,loadmask=loading(p,e,typ,grp,hx,hy);T,left,right,bc=constraints(p)
 A=(T.T@K@T).tocsc(); f=T.T@F
 lu=splu(A,permc_spec='MMD_AT_PLUS_A',diag_pivot_thresh=0.0,options={'SymmetricMode':True});say('Factorized',time.time()-start,'nnz factors',lu.L.nnz+lu.U.nnz)
 assert np.all(lu.U.diagonal()>0), 'Elastic stiffness must be positive definite'
 q=lu.solve(f);u=T@q;res=K@u-F
 say('Static residual',np.linalg.norm(A@q-f)/np.linalg.norm(f),'Fz',F[2::6].sum(),'max translation',np.abs(u.reshape(-1,6)[:,:3]).max())
 G,stress=geometric(hx,hy,t,ec,dof,sg,nd,u[dof]*sg);B=-(T.T@G@T).tocsc()
 say('Geometric assembly',time.time()-start)
 vals,vec=eigsh(B,k=6,M=A,Minv=LinearOperator(A.shape,matvec=lu.solve),which='LA',tol=2e-7,ncv=26,maxiter=1000)
 idx=np.argsort(vals)[::-1];vals=vals[idx];vec=vec[:,idx];lams=1/vals
 errors=[float(np.linalg.norm(A@vec[:,i]-lams[i]*(B@vec[:,i]))/np.linalg.norm(A@vec[:,i])) for i in range(len(vals))]
 say('Buckling factors',lams,'residuals',errors,'seconds',time.time()-start)
 assert lams[0]>0 and max(errors)<1e-4
 areas=(hx*hy)@loadmask
 assert np.allclose(areas,[443250,61250,27600])
 data={'h_mm':h,'nodes':len(p),'elements':len(e),'dofs':nd,'lambda1':float(lams[0]),'positive_factors':lams.tolist(),'eigen_relative_residuals':errors,'seconds':time.time()-start,'max_displacement_mm':float(np.abs(u.reshape(-1,6)[:,:3]).max()),'total_force_N':F.reshape(-1,6)[:,:3].sum(axis=0).tolist(),'loaded_areas_mm2_strip_bearings_ends':areas.tolist(),'shell_integrated_volume_mm3':float(np.sum(hx*hy*t)),'static_relative_residual':float(np.linalg.norm(A@q-f)/np.linalg.norm(f))}
 if save:
  modes=(T@vec).reshape(len(p),6,-1);modes/=np.max(np.linalg.norm(modes[:,:3,:],axis=1),axis=0)[None,None,:]
  np.savez_compressed(OUT/'fields.npz',node_ids=np.arange(1,len(p)+1),coordinates_mm=p,element_ids=np.arange(1,len(e)+1),connectivity=e+1,physical_group=grp,thickness_mm=t,eccentricity_mm=ec,local_frame_type=typ,reference_displacement_mm=u.reshape(-1,6)[:,:3],reference_rotation_rad=u.reshape(-1,6)[:,3:],reference_stress_MPa=stress,reference_nodal_load_N_Nmm=F.reshape(-1,6),reference_residual_N_Nmm=res.reshape(-1,6),buckling_factors=lams,buckling_modes=modes,support_left=left,support_right=right,constrained_dof_mask=bc,load_element_masks=loadmask)
  meshio.write(OUT/'mesh.msh',meshio.Mesh(p,[('quad',e)],cell_data={'gmsh:physical':[grp],'gmsh:geometrical':[grp]},field_data={n:np.array([i,2]) for i,n in enumerate(['bottom_flange','top_flange','web','longitudinal_stiffener','end_stiffeners','interior_stiffeners'],1)}),file_format='gmsh22',binary=True)
 return data

def main():
 global log
 log=open(OUT/'solver.log','w');say('Python',sys.version,'numpy',np.__version__,'scipy',scipy.__version__,'meshio',meshio.__version__)
 say('Invocation python main.py; E =',E,'MPa; nu =',nu,'; MITC4 linear shell buckling')
 shutil.copyfile(Path(os.environ['CADFEM_INPUT_DIR'])/'analysis.step',OUT/'part.step')
 import cadquery as cq
 solid=cq.importers.importStep(str(OUT/'part.step')).val()
 cad_info={'cadquery':cq.__version__,'solid_regions':len(solid.Solids()),'volume_mm3':solid.Volume()}
 say('CAD validation',cad_info)
 assert cad_info['solid_regions']==104 and abs(cad_info['volume_mm3']/3335612900-1)<1e-6
 del solid
 hs=[float(x) for x in os.environ.get('MESH_H','65,45').split(',')]
 results=[run(h,i==len(hs)-1) for i,h in enumerate(hs)]
 json.dump({'outputs':{'lambda1':results[-1]['lambda1']}},open(OUT/'results.json','w'),indent=2)
 json.dump({'resolutions':results,'relative_change':abs(results[-1]['lambda1']/results[-2]['lambda1']-1) if len(results)>1 else 0,'method':'Actual connected MITC4 shell mesh refinements; geometry and loading unchanged.'},open(OUT/'refinement.json','w'),indent=2)
 json.dump({'command':'python main.py','python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'meshio':meshio.__version__,'units':{'length':'mm','force':'N','stress':'MPa','rotation':'rad','buckling_factor':'dimensionless'},'material':{'E_MPa':E,'nu':nu},'element':'Four-node flat MITC4 shell, full 2x2 membrane/bending integration, mixed interpolated transverse shear; weak drilling rotation/curl penalty 1e-4 E t. Six DOFs per node.','physical_groups':{1:'bottom flange',2:'top flange',3:'web',4:'longitudinal stiffener',5:'end stiffeners',6:'interior transverse stiffeners'},'modeling_assumptions':['All interfaces welded, shared shell nodes with all six DOFs continuous. Exact 104-region physical solid retained in part.step; mesh.msh is the midsurface reduction.','Web thickness 15; flange thickness 50; longitudinal stiffener 20; transverse stiffeners 15 except end plates 24 mm. Web and stiffeners extend to flange midplanes, neglecting joint overlap volume.','Bottom 175x175 bearing plates represented by 100-mm-thick eccentric flange patches: reference z=25, section centroid z=0.','Supports mapped from z=2100 to z=2075 with exact rigid offset (25 mm): ux+25 theta_y=0 on left; uy-25 theta_x=0 and uz=0 both ends. All other rotations free.','All prescribed tractions integrated at their original plan locations, preserving areas, sums, and load moments; duplicate lower-patch pressures add. No self weight.','Geometric matrix integrates initial in-plane stresses and bending stresses through thickness, acting on gradients of all three displacement components and two bending rotations. Initial transverse shear/normal stress neglected in the shell reduction.'],'quantity_extraction':'Solve Ku=F, then generalized symmetric eigenproblem -KG v = mu K v, six largest algebraic mu; lambda1 = 1 / max positive mu. Entire reference load scales together.','field_schema':{'node_ids':'One-based mesh.msh node tags; row order matches coordinates','connectivity':'One-based node IDs of each quad, matching element row order','element_ids':'One-based mesh element tags','coordinates_mm':'N x 3 global XYZ on reference shell surface','reference_displacement_mm':'N x 3 translations in global frame','reference_rotation_rad':'N x 3 rotation vectors in global frame','reference_stress_MPa':'Ne x 4 in-plane Gauss points x 2 section surfaces (bottom,top) x 3 local stresses (xx,yy,xy). Gauss loop x then y ascending.','buckling_modes':'N x 6 x 6 modes, global translations then rotations, normalized to maximum translational vector magnitude = 1 mm','buckling_factors':'Six positive elastic load factors, ascending','reference_nodal_load_N_Nmm':'N x 6 consistent forces and moments','reference_residual_N_Nmm':'Ku-F in full DOFs, including support reaction force/couple','support_left, support_right':'Node masks at support reference lines','constrained_dof_mask':'N x 6 masks of eliminated DOFs; offset constraints described above','load_element_masks':'Ne x 3: bottom strip, bearing patch, top end load masks','physical_group':'Ne group IDs matching MSH physical tags','thickness_mm, eccentricity_mm':'Ne shell thickness and centroid offset along local normal','local_frame_type':'0: (X,Y,Z); 1: (X,Z,-Y); 2: (Y,Z,X)'}},open(OUT/'environment.json','w'),indent=2)
 ep=OUT/'environment.json'
 env=json.load(open(ep));env['source_CAD']=cad_info
 env['reduction_limitations']='Shell midsurfaces extend to intersecting plate midplanes. Their integrated section volume is 1.16% greater than the exact solid because joint overlaps are not subtracted. Convergence is numerical shell-mesh convergence, not an estimate of 3D-to-shell modeling error. Local through-thickness stresses at loads and constrained edges are not resolved.'
 env['source_face_mapping']={'top_end_pressure_-166.15942_MPa':[332,334,337,304,306,309],'bearing_pressure_30.204082_MPa':[240,610],'additional_pressure_5.423191_MPa':[240,286,320,348,376,410,478,512,584,585,586,587,588,591,592,593,610],'support_left_edges':[459,463,464],'support_right_edges':[517,528,529]}
 env['load_sign_convention']='Top end traction is global -z; all bottom strip and bearing tractions are global +z. End faces have total area 27600 mm2; bearings 61250 mm2; remaining bottom strip 443250 mm2. Rounded input tractions leave net -0.11 N.'
 json.dump(env,open(ep,'w'),indent=2)
 say('NORMAL TERMINATION')
 log.close();log=None
 # Both a flat replay output and the benchmark's named delivery directory.
 dest=OUT/'A-FCVM-Plate_girder_EC3';dest.mkdir(exist_ok=True)
 for name in ['results.json','part.step','mesh.msh','fields.npz','solver.log','refinement.json','environment.json']:
  shutil.copyfile(OUT/name,dest/name)
 shutil.copyfile(Path(__file__),dest/'main.py')
if __name__=='__main__':main()
