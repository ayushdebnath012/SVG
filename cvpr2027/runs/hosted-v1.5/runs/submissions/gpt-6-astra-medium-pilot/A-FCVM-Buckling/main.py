"""3-D elastic solid prebuckling and initial-stress eigenproblem.
Dependencies: numpy, scipy, scikit-fem, gmsh, cadquery. Run: python main.py.
Inputs from CADFEM_INPUT_DIR; artifacts in CADFEM_OUTPUT_DIR/A-FCVM-Buckling.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='2'
os.environ['OMP_NUM_THREADS']='2'
import sys, json, time, shutil, platform
from pathlib import Path
import numpy as np
import scipy
from scipy.sparse.linalg import splu, eigsh, LinearOperator
import skfem
from skfem import MeshHex, Basis, FacetBasis, ElementHex2, ElementVector, asm, BilinearForm, LinearForm
from skfem.helpers import sym_grad, ddot, trace
import gmsh

E=210000.; nu=.3
mu=E/(2*(1+nu)); lam=E*nu/((1+nu)*(1-2*nu))
@BilinearForm
def elastic(u,v,w):
    eu=sym_grad(u); ev=sym_grad(v)
    return 2*mu*ddot(eu,ev)+lam*trace(eu)*trace(ev)
@BilinearForm
def geometric(u,v,w):
    return np.einsum('ij...,ki...,kj...->...',w.sigma,u.grad,v.grad)
@LinearForm
def traction(v,w):
    return -v[0]

def build_mesh(nx,nc):
    x=np.r_[np.linspace(0,1000,nx+1),np.linspace(1000,1010,nc+1)[1:]]
    y=np.linspace(0,10,nc+1)
    z=np.linspace(-10,20,3*nc+1)
    m=MeshHex.init_tensor(x,y,z)
    c=m.p[:,m.t].mean(axis=1)
    bad=(c[0]<1000-1e-5)&((c[2]<0)|(c[2]>10))
    return m.remove_elements(np.flatnonzero(bad))

def run(nx,nc,log):
    t0=time.time()
    m=build_mesh(nx,nc)
    s=Basis(m,ElementHex2(),intorder=4)
    b=Basis(m,ElementVector(ElementHex2()),intorder=4)
    log('mesh',nx,nc,'elements',m.nelements,'nodes',s.N,'dofs',b.N)
    xyz=s.doflocs.T
    fixed=np.zeros((s.N,3),bool)
    fixed[np.isclose(xyz[:,0],0),:]=True
    fixed[np.isclose(xyz[:,1],0),1]=True
    free=np.flatnonzero(~fixed.ravel())
    K=asm(elastic,b).tocsc()
    log('assembled K',time.time()-t0)
    lf=m.facets_satisfying(lambda x:np.isclose(x[0],1010)&(x[2]>0)&(x[2]<10),boundaries_only=True)
    fb=FacetBasis(m,ElementVector(ElementHex2()),facets=lf,intorder=4)
    f=asm(traction,fb)
    assert abs(f.sum()+100)<1e-7
    k=K[free][:,free].tocsc()
    lu=splu(k)
    u=np.zeros(b.N); u[free]=lu.solve(f[free])
    residual=K@u-f
    strain=sym_grad(b.interpolate(u))
    stress=2*mu*strain+lam*np.eye(3)[:,:,None,None]*trace(strain)[None,None,:,:]
    G=asm(geometric,b,sigma=stress).tocsc()
    g=G[free][:,free].tocsc()
    log('preload solved, G assembled',time.time()-t0,'max u',np.max(np.abs(u)))
    inv=LinearOperator(k.shape,matvec=lu.solve,dtype=float)
    vals,vecs=eigsh(-g,k=4,M=k,Minv=inv,which='LA',tol=1e-9,maxiter=500,ncv=20,v0=np.random.default_rng(44).standard_normal(len(free)))
    idx=np.argsort(1/vals); vals=vals[idx]; vecs=vecs[:,idx]
    factors=1/vals
    modes=np.zeros((4,b.N)); eigres=[]
    for j in range(4):
        v=vecs[:,j]; v/=np.max(np.abs(v))
        a=k@v; c=factors[j]*(g@v)
        eigres.append(float(np.linalg.norm(a+c)/(np.linalg.norm(a)+np.linalg.norm(c))))
        modes[j,free]=v
    reactions=residual.reshape(-1,3).sum(axis=0)
    st_res=np.linalg.norm(residual[free])/np.linalg.norm(f[free])
    record=dict(axial_elements_main=nx,cross_section_divisions=nc,max_axial_size_mm=1000/nx,cross_section_size_mm=10/nc,elements=int(m.nelements),nodes=int(s.N),dofs=int(b.N),lambda1=float(factors[0]),eigenvalues=factors.tolist(),eigen_relative_residuals=eigres,static_relative_residual=float(st_res),reaction_N=reactions.tolist(),reference_load_N=f.reshape(-1,3).sum(axis=0).tolist(),strain_energy_N_mm=float(.5*u@f),elapsed_s=time.time()-t0)
    log('result',record)
    return record,dict(mesh=m,scalar=s,xyz=xyz,displacement=u.reshape(-1,3),stress=stress,strain=strain,quadrature_xyz=np.asarray(b.global_coordinates()),quadrature_weights=b.dx,mode=modes.reshape(4,-1,3),fixed=fixed,force=f.reshape(-1,3),reactions=residual.reshape(-1,3),factors=factors)

def write_mesh(out,d):
    """Write the actual 27-node FE mesh; local permutations from reference coordinates."""
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal',0)
    gmsh.model.add('analysis_mesh')
    xyz=d['xyz']; m=d['mesh']; s=d['scalar']
    # Map scikit-fem reference-node ordering to Gmsh Hex27.
    _,_,_,_,loc,_=gmsh.model.mesh.getElementProperties(12)
    loc=np.asarray(loc).reshape(-1,3)
    ref=(loc+1)/2
    # skfem's reference-to-physical mapping of init_tensor Hexes reverses
    # orientation. Reflect one reference coordinate to write positive-J Gmsh
    # elements; this changes local ordering only, not nodes or FE spaces.
    ref[:,0]=1-ref[:,0]
    skref=ElementHex2().doflocs
    perm=np.argmin(((ref[:,None,:]-skref[None,:,:])**2).sum(axis=2),axis=1)
    assert len(set(perm.tolist()))==27
    con=s.element_dofs[perm].T+1
    ctr=xyz[con-1].mean(axis=1)
    reg=np.ones(len(con),int)
    end=ctr[:,0]>1000
    reg[end]=2; reg[end&(ctr[:,2]<0)]=3; reg[end&(ctr[:,2]>10)]=4
    # All nodes retain exact scalar-DOF IDs, even where regions share nodes.
    for r in range(1,5):
        gmsh.model.addDiscreteEntity(3,r)
        gmsh.model.addPhysicalGroup(3,[r],r)
        gmsh.model.setPhysicalName(3,r,'solid_region_'+str(r))
    gmsh.model.mesh.addNodes(3,1,np.arange(1,len(xyz)+1),xyz.ravel())
    for r in range(1,5):
        ids=np.flatnonzero(reg==r)
        gmsh.model.mesh.addElementsByType(r,12,ids+1,con[ids].ravel())
    # Export all external faces as Q9 with geometrical face indices from input.
    desc=json.loads((Path(os.environ['CADFEM_INPUT_DIR'])/'faces.json').read_text())['face_descriptors']
    bfac=m.boundary_facets()
    eid=len(con)+1
    for fd in desc:
        tag=fd['face_index']; lo=np.array(fd['bbox_mm'][:3]); hi=np.array(fd['bbox_mm'][3:])
        matches=[]
        for fi in bfac:
            verts=m.p[:,m.facets[:,fi]].T
            if np.all(verts>=lo-1e-7) and np.all(verts<=hi+1e-7): matches.append(fi)
        if not matches: continue
        axis=int(np.argmin(hi-lo)); axes=[a for a in range(3) if a!=axis]
        conn=[]
        qpat=np.array([[0,0],[1,0],[1,1],[0,1],[.5,0],[1,.5],[.5,1],[0,.5],[.5,.5]])
        for fi in matches:
            elem=int(m.f2t[0,fi]); en=s.element_dofs[:,elem]
            verts=m.p[:,m.facets[:,fi]].T
            vl=verts.min(axis=0); vh=verts.max(axis=0)
            pts=np.tile(vl,(9,1)); pts[:,axes]=vl[axes]+qpat*(vh-vl)[axes]
            nearest=np.argmin(((pts[:,None,:]-xyz[en][None,:,:])**2).sum(axis=2),axis=1)
            assert np.max(np.linalg.norm(xyz[en[nearest]]-pts,axis=1))<1e-6
            conn.append(en[nearest]+1)
        gmsh.model.addDiscreteEntity(2,tag)
        gmsh.model.addPhysicalGroup(2,[tag],100+tag)
        name='face_'+str(tag)
        if tag==1:name+='_clamp'
        if tag in [2,7,13,18]:name+='_uy_zero'
        if tag==9:name+='_traction_minus_x_1MPa'
        gmsh.model.setPhysicalName(2,100+tag,name)
        gmsh.model.mesh.addElementsByType(tag,10,np.arange(eid,eid+len(conn)),np.array(conn).ravel())
        eid+=len(conn)
    gmsh.option.setNumber('Mesh.MshFileVersion',4.1)
    _, det, _ = gmsh.model.mesh.getJacobians(12,[0.,0.,0.])
    assert np.min(det)>0, 'Exported hex orientation must be positive'
    assert abs(np.sum(det)*8-103000)<1e-5
    gmsh.write(str(out/'mesh.msh'))
    gmsh.finalize()
    return con,reg

def main():
    out=Path(os.environ.get('CADFEM_OUTPUT_DIR','.'))/'A-FCVM-Buckling';out.mkdir(parents=True,exist_ok=True)
    logf=open(out/'solver.log','w')
    def log(*args):
        print(*args,flush=True);print(*args,file=logf,flush=True)
    versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,skfem=skfem.__version__,gmsh=gmsh.__version__)
    log('Invocation: python main.py; versions:',versions)
    shutil.copyfile(Path(os.environ['CADFEM_INPUT_DIR'])/'analysis.step',out/'part.step')
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal',0)
    gmsh.model.add('CAD_validation')
    cad=gmsh.model.occ.importShapes(str(out/'part.step'))
    gmsh.model.occ.synchronize()
    solids=gmsh.model.getEntities(3)
    cadvol=sum(gmsh.model.occ.getMass(3,t) for _,t in solids)
    log('CAD validation: solids',len(solids),'volume mm^3',cadvol)
    assert len(solids)==4 and abs(cadvol-103000)<1e-5
    gmsh.finalize()
    records=[]
    for nx,nc in [(100,2),(150,3),(200,4)]:
        rec,d=run(nx,nc,log);records.append(rec)
    con,reg=write_mesh(out,d)
    log('Export verified: positive Hex27 Jacobians; mesh volume mm^3',float(np.sum(d['quadrature_weights'])))
    np.savez_compressed(out/'fields.npz',node_ids=np.arange(1,len(d['xyz'])+1),coordinates_mm=d['xyz'],element_ids=np.arange(1,len(con)+1),connectivity_hex27=con,region_ids=reg,displacement_mm=d['displacement'],stress_MPa=d['stress'].transpose(2,3,0,1),strain=d['strain'].transpose(2,3,0,1),quadrature_coordinates_mm=d['quadrature_xyz'].transpose(1,2,0),quadrature_volume_weights_mm3=d['quadrature_weights'],buckling_modes=d['mode'],load_factors=d['factors'],fixed_dof_mask=d['fixed'],reference_force_N=d['force'],nodal_residual_N=d['reactions'],coordinate_units=np.array('mm'),stress_units=np.array('MPa'),mode_units=np.array('arbitrary; max absolute component 1'))
    (out/'results.json').write_text(json.dumps({'outputs':{'lambda1':records[-1]['lambda1']}},indent=2))
    change=abs(records[-1]['lambda1']/records[-2]['lambda1']-1)
    (out/'refinement.json').write_text(json.dumps(dict(meshes=records,relative_change_lambda1=change,reported='finest mesh without extrapolation',element='conforming triquadratic 27-node hexahedron; 3x3x3 Gauss rule'),indent=2))
    env=dict(versions=versions,command='python main.py',analysis='3-D small-strain linear elasticity and initial-stress eigenbuckling',units=dict(length='mm',force='N',stress='MPa',eigenvalue='dimensionless'),material=dict(E_MPa=E,poisson=nu),geometry='Input STEP unchanged: four shared-interface regions. Tensor-product mesh conforms to all region interfaces; common DOFs ensure full displacement and traction continuity.',boundary_conditions={'face_1':'ux=uy=uz=0','faces_2_7_13_18':'uy=0','face_9':'traction [-1,0,0] MPa; total [-100,0,0] N'},formulation='K from isotropic linear elasticity. Reference stress sigma=C:sym(grad u). G_ab=int sigma_ij (dN_a/dx_i)(dN_b/dx_j) dV for each displacement component. Solve -G phi=mu K phi, lambda=1/mu. Report smallest positive lambda. Dead reference traction, no follower load stiffness or self-weight.',quantity_extraction='Four largest positive reciprocal buckling eigenvalues with sparse generalized symmetric ARPACK; smallest positive load factor reported. Mode normalization max absolute displacement component=1. No beam or shell reduction.',physical_groups={'volume_1':'main beam x=0..1000','volume_2':'end central x=1000..1010,z=0..10','volume_3':'end bottom z=-10..0','volume_4':'end top z=10..20','surface_100_plus_face_index':'external faces from faces.json, including support/load faces; internal interfaces not boundary elements'},field_schema={'node_ids':'1-based scalar FE DOF number; identical to Gmsh node tags','coordinates_mm':'(nnode,3), all Q2 nodes','element_ids':'Gmsh volume element tags, 1-based','connectivity_hex27':'(nelement,27), Gmsh type 12 node ordering; entries are node_ids','region_ids':'physical volume group per element','displacement_mm':'(nnode,3), reference load displacement','stress_MPa':'(nelement,27,3,3), reference Cauchy stress at Gauss points, no averaging','strain':'(nelement,27,3,3), infinitesimal strain','quadrature_coordinates_mm':'(nelement,27,3), locations of stress/strain samples','quadrature_volume_weights_mm3':'(nelement,27), Jacobian-weighted integration weights','buckling_modes':'(4,nnode,3), modes sorted ascending load factor','load_factors':'(4,), dimensionless eigenvalues corresponding to modes','fixed_dof_mask':'(nnode,3), True at constrained DOFs','reference_force_N':'consistent surface force vector (nnode,3)','nodal_residual_N':'K u - f; reactions at constrained DOFs'},assumptions=['Exact axis-aligned geometry represented by conforming quadratic solid elements.','Conventional full 27-point hexahedral integration for stiffness and geometric stiffness.','Linearized initial-stress buckling, not nonlinear collapse.'],convergence_relative_change=change)
    (out/'environment.json').write_text(json.dumps(env,indent=2))
    shutil.copyfile(Path(__file__),out/'main.py')
    log('SUCCESS; lambda1 =',records[-1]['lambda1'],'refinement relative change',change)
    logf.close()
if __name__=='__main__':main()
