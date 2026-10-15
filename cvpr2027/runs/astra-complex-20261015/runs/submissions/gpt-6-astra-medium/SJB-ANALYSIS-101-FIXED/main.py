import os,time,json
os.environ['OMP_NUM_THREADS']='2'
os.environ['OPENBLAS_NUM_THREADS']='2'
os.environ['VECLIB_MAXIMUM_THREADS']='2'
import numpy as np
import gmsh
from skfem import MeshTet2, Basis, FacetBasis, ElementTetP2, ElementVector, asm, LinearForm
from skfem.models.elasticity import linear_elasticity

def mesh(h):
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal',1)
    gmsh.option.setNumber('General.NumThreads',2)
    gmsh.model.occ.importShapes(os.path.join(os.environ['CADFEM_INPUT_DIR'],'bracket.step'))
    gmsh.model.occ.synchronize()
    # Imported OCC surface order matches STEP face order; verify analytical areas.
    bolt=[90,91,98,99,100,101,102,103]
    lug=[310,311,312,313]
    for tag in bolt+lug: print('interface',tag,gmsh.model.getType(2,tag),gmsh.model.occ.getMass(2,tag),flush=True)
    gmsh.option.setNumber('Mesh.MeshSizeMax',h)
    gmsh.option.setNumber('Mesh.MeshSizeMin',h/5)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',12)
    gmsh.option.setNumber('Mesh.MeshSizeFromPoints',0)
    gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
    gmsh.option.setNumber('Mesh.Algorithm3D',1)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.setOrder(2)
    gmsh.model.mesh.optimize("HighOrder")
    tags,xyz,_=gmsh.model.mesh.getNodes()
    xyz=xyz.reshape(-1,3)
    idx=np.empty(tags.max()+1,dtype=int);idx[tags]=np.arange(len(tags))
    typ,et,en=gmsh.model.mesh.getElements(3)
    tet=idx[en[list(typ).index(11)].reshape(-1,10)][:,[0,1,2,3,4,5,6,7,9,8]]
    surfaces={}
    for name,faces in [('bolt',bolt),('lug',lug)]:
        ts=[]
        for f in faces:
            ty,_,nn=gmsh.model.mesh.getElements(2,f)
            ts.append(idx[nn[list(ty).index(9)].reshape(-1,6)[:,:3]])
        surfaces[name]=np.concatenate(ts)
    gmsh.finalize()
    return xyz,tet,surfaces

def solve(h):
    start=time.time()
    p,t,sur=mesh(h)
    print('mesh',p.shape,t.shape,'time',time.time()-start,flush=True)
    m=MeshTet2(p.T,t.T)
    remap=np.full(p.shape[0],-1,dtype=int)
    remap[np.unique(t[:,:4])]=np.arange(m.nvertices)
    sur={k:remap[v] for k,v in sur.items()}
    facets={tuple(sorted(f)):i for i,f in enumerate(m.facets.T)}
    boundary={key:np.array([facets[tuple(sorted(f))] for f in tris]) for key,tris in sur.items()}
    b=Basis(m,ElementVector(ElementTetP2()),elements=np.array([],dtype=np.int32),intorder=1)
    print('DOFs',b.N,flush=True)
    E=113800.;nu=.342
    K=None
    invalid=0;volume=0.
    elast=linear_elasticity(E*nu/((1+nu)*(1-2*nu)),E/(2*(1+nu)))
    for first in range(0,m.nelements,10000):
        bk=Basis(m,ElementVector(ElementTetP2()),elements=np.arange(first,min(first+10000,m.nelements)),intorder=4)
        jac=bk.mapping.detDF(bk.X,tind=bk.tind)
        invalid+=int(np.sum(jac.min(axis=1)*jac.max(axis=1)<0))
        volume+=float(bk.dx.sum())
        kk=asm(elast,bk).tocsc()
        K=kk if K is None else K+kk
        bk.mapping._cache.clear()
    del bk,kk
    print('assembled',time.time()-start,'volume',volume,'invalid',invalid,flush=True)
    assert invalid==0
    fixed=b.get_dofs(facets=boundary['bolt']).all()
    free=np.setdiff1d(np.arange(b.N),fixed)
    # Work-equivalent distributed loading: least-squares rigid-motion extraction
    # on the two complete bores (RBE3, area-weighted).
    fb=FacetBasis(m,ElementVector(ElementTetP2()),facets=boundary['lug'],intorder=4)
    point=np.array([-21.0359,-75.0647,44.8010])
    def rigid(x):
        r=x-point.reshape((3,)+(1,)*(x.ndim-1))
        A=np.zeros((6,3)+x.shape[1:])
        for i in range(3):A[i,i]=1
        A[3,1]=-r[2];A[3,2]=r[1]
        A[4,0]=r[2];A[4,2]=-r[0]
        A[5,0]=-r[1];A[5,1]=r[0]
        return A
    A=rigid(fb.global_coordinates())
    G=np.einsum('icfq,jcfq,fq->ij',A,A,fb.dx)
    loads=np.zeros((6,4));loads[2,0]=35585.77;loads[0,1]=-37809.90;loads[:3,2]=[-28276.2,0,31403.9];loads[5,3]=564924.2
    co=np.linalg.solve(G,loads)
    F=np.zeros((b.N,4))
    for case in range(4):
        @LinearForm
        def form(v,w):
            tr=np.einsum('i,ic...->c...',co[:,case],rigid(w.x))
            return np.einsum('i...,i...->...',tr,v)
        F[:,case]=asm(form,fb)
    b.basis=[]
    fb.basis=[]
    b.mapping._cache.clear()
    print('factor',len(free),'nnz',K.nnz,'time',time.time()-start,flush=True)
    from accelerate_solver import cholesky_solve
    K=K[free,:][:,free]
    u=np.zeros((b.N,4));u[free]=cholesky_solve(K,F[free])
    print('solved',time.time()-start,flush=True)
    vals=np.max(np.linalg.norm(u.reshape(-1,3,4),axis=1),axis=0)
    print('RESULT',h,vals,'time',time.time()-start,flush=True)
    np.savez('solution.npz',p=m.p,t=m.dofs.element_dofs.T,u=u,doflocs=b.doflocs)
    residual=np.linalg.norm(K@u[free]-F[free],axis=0)/np.linalg.norm(F[free],axis=0)
    with open('analysis_details.json','w') as f:
        json.dump({'mesh_size_mm':h,'elements':int(m.nelements),'dofs':int(b.N),'volume_mm3':volume,'relative_residuals':residual.tolist(),'maximum_displacements_mm':vals.tolist()},f,indent=2)
    return vals

if __name__=='__main__':
    vals=solve(float(os.environ.get('MESH_H','1.8')))
    keys=['vertical_max_displacement_mm','horizontal_max_displacement_mm','diagonal_max_displacement_mm','torsion_max_displacement_mm']
    with open('results.json','w') as f:json.dump({'outputs':dict(zip(keys,map(float,vals)))},f,indent=2)
