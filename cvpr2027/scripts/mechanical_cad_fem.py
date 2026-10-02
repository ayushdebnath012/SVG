"""Reproducible scenario-defined 3-D linear tetrahedral elasticity, not dataset operating loads."""
import argparse,hashlib,json,time,warnings
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve,MatrixRankWarning
import gmsh,meshio


def mesh_step(step,out,h,curvature=16,algorithm=1):
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',2)
    try:
        gmsh.model.occ.importShapes(str(step));gmsh.model.occ.synchronize()
        gmsh.option.setNumber('Mesh.MeshSizeMax',h);gmsh.option.setNumber('Mesh.MeshSizeMin',h/5)
        gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',curvature);gmsh.option.setNumber('Mesh.ElementOrder',1)
        gmsh.option.setNumber('Mesh.Algorithm3D',algorithm);gmsh.option.setNumber('Mesh.RandomSeed',17)
        gmsh.model.mesh.generate(3);gmsh.model.mesh.optimize('Netgen')
        tags,xyz,_=gmsh.model.mesh.getNodes();xyz=np.array(xyz).reshape(-1,3)
        typ,_,nodes=gmsh.model.mesh.getElements(3);j=list(typ).index(4);raw=np.array(nodes[j]).reshape(-1,4)
        order=np.argsort(tags);idx=order[np.searchsorted(np.array(tags)[order],raw)]
        # Remove any nodes unused by volume elements.
        used,inverse=np.unique(idx,return_inverse=True);xyz=xyz[used];tet=inverse.reshape(-1,4)
        gmsh.write(str(out));return xyz,tet
    finally:gmsh.finalize()


def boundary_faces(tet):
    faces=np.concatenate([tet[:,[0,1,2]],tet[:,[0,1,3]],tet[:,[0,2,3]],tet[:,[1,2,3]]])
    unique,counts=np.unique(np.sort(faces,axis=1),axis=0,return_counts=True)
    return unique[counts==1]


def solve(xyz,tet,axis=np.array([0.,0.,1.]),E=210000.,nu=.3,force=1.,band=.05,exact_planes=False):
    axis=np.asarray(axis,dtype=float);axis/=np.linalg.norm(axis)
    n=len(xyz);ne=len(tet)
    if n>40000 or ne>220000:raise ValueError('Mesh exceeds documented local solver resource budget')
    pts=xyz[tet];A=np.concatenate([np.ones((ne,4,1)),pts],axis=2);det=np.linalg.det(A);vol=np.abs(det)/6
    if np.any(vol<1e-15):raise ValueError('Degenerate tetrahedron')
    grad=np.linalg.inv(A)[:,1:,:].transpose(0,2,1)
    B=np.zeros((ne,6,12))
    for i in range(4):
        gx,gy,gz=grad[:,i,:].T;j=3*i
        B[:,0,j]=gx;B[:,1,j+1]=gy;B[:,2,j+2]=gz
        B[:,3,j]=gy;B[:,3,j+1]=gx;B[:,4,j+1]=gz;B[:,4,j+2]=gy;B[:,5,j]=gz;B[:,5,j+2]=gx
    lam=E*nu/((1+nu)*(1-2*nu));mu=E/(2*(1+nu));D=np.zeros((6,6));D[:3,:3]=lam;D[np.arange(3),np.arange(3)]+=2*mu;D[3:,3:]=np.eye(3)*mu
    ke=np.einsum('eki,kl,elj,e->eij',B,D,B,vol,optimize=True)
    dofs=(tet[:,:,None]*3+np.arange(3)).reshape(ne,12)
    K=sp.coo_matrix((ke.ravel(),(np.repeat(dofs,12,axis=1).ravel(),np.tile(dofs,(1,12)).ravel())),shape=(3*n,3*n)).tocsr()
    faces=boundary_faces(tet);surface=np.unique(faces);q=xyz@axis;lo,hi=float(q.min()),float(q.max());span=hi-lo
    tol=1e-8*max(1,span)
    fixed_nodes=surface[q[surface]<=lo+(tol if exact_planes else band*span)]
    centres=xyz[faces].mean(axis=1);loaded=faces[centres@axis>=hi-(tol if exact_planes else band*span)]
    if len(fixed_nodes)<3 or not len(loaded):raise ValueError('Insufficient support or loaded facets')
    if np.linalg.matrix_rank(xyz[fixed_nodes]-xyz[fixed_nodes].mean(axis=0),tol=1e-8)<2:raise ValueError('Collinear support nodes')
    areas=np.linalg.norm(np.cross(xyz[loaded[:,1]]-xyz[loaded[:,0]],xyz[loaded[:,2]]-xyz[loaded[:,0]]),axis=1)/2
    weights=np.zeros(n);np.add.at(weights,loaded.ravel(),np.repeat(areas/3,3));weights/=weights.sum()
    f=(weights[:,None]*axis[None,:]*force).ravel();fixed=(fixed_nodes[:,None]*3+np.arange(3)).ravel();free=np.setdiff1d(np.arange(3*n),fixed)
    # Every disconnected volume component must be anchored.
    graph=sp.coo_matrix((np.ones(ne*16),(np.repeat(tet,4,axis=1).ravel(),np.tile(tet,(1,4)).ravel())),shape=(n,n)).tocsr()
    nc,labels=sp.csgraph.connected_components(graph,directed=False)
    if set(labels[fixed_nodes])!=set(range(nc)):raise ValueError('Unanchored disconnected component')
    u=np.zeros(3*n)
    with warnings.catch_warnings():
        warnings.simplefilter('error',MatrixRankWarning);u[free]=spsolve(K[free][:,free],f[free])
    if not np.isfinite(u).all():raise ValueError('Nonfinite solution')
    residual=K@u-f;reactions=np.zeros_like(f);reactions[fixed]=residual[fixed];ud=u.reshape(-1,3)
    stress=np.einsum('ij,ejk,ek->ei',D,B,u[dofs],optimize=True)
    xx,yy,zz,xy,yz,xz=stress.T;vm=np.sqrt(.5*((xx-yy)**2+(yy-zz)**2+(zz-xx)**2)+3*(xy**2+yz**2+xz**2))
    sort=np.argsort(vm);p95=float(vm[sort][np.searchsorted(np.cumsum(vol[sort])/vol.sum(),.95)])
    compliance=float(f@u);energy=float(u@(K@u)/2)
    force_error=float(np.linalg.norm((f+reactions).reshape(-1,3).sum(axis=0))/force)
    moment_error=float(np.linalg.norm(np.cross(xyz,(f+reactions).reshape(-1,3)).sum(axis=0))/(force*max(span,1)))
    res=float(np.linalg.norm(residual[free])/np.linalg.norm(f[free]))
    energy_error=abs(2*energy-compliance)/max(abs(compliance),1e-30)
    if compliance<=0 or max(force_error,moment_error,res,energy_error)>1e-6:raise ValueError('Equilibrium / energy checks failed')
    metrics=dict(nodes=n,tetrahedra=ne,connected_components=nc,mesh_volume_mm3=float(vol.sum()),fixed_nodes=len(fixed_nodes),loaded_facets=len(loaded),loaded_area_mm2=float(areas.sum()),axis=axis.tolist(),projection_min_mm=lo,projection_max_mm=hi,compliance_N_mm=compliance,load_weighted_displacement_mm=compliance/force,max_displacement_mm=float(np.linalg.norm(ud,axis=1).max()),strain_energy_N_mm=energy,vm_p95_MPa=p95,vm_peak_MPa=float(vm.max()),relative_free_residual=res,relative_force_balance_error=force_error,relative_moment_balance_error=moment_error,relative_energy_error=energy_error)
    return metrics,ud,vm


def main():
    p=argparse.ArgumentParser();p.add_argument('--step',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--h',type=float,default=4);p.add_argument('--axis',type=float,nargs=3,default=[0,0,1]);p.add_argument('--young',type=float,default=210000.);p.add_argument('--poisson',type=float,default=.3);p.add_argument('--force',type=float,default=1.);p.add_argument('--band',type=float,default=.05);p.add_argument('--algorithm',type=int,default=1);p.add_argument('--curvature',type=int,default=16);p.add_argument('--cube-test',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    if a.cube_test:
        gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.model.occ.addBox(0,0,0,10,10,10);gmsh.model.occ.synchronize();step=a.output/'cube.step';gmsh.write(str(step));gmsh.finalize()
    else:step=a.step
    start=time.monotonic();xyz,tet=mesh_step(step,a.output/'mesh.msh',a.h,a.curvature,a.algorithm)
    metrics,u,vm=solve(xyz,tet,axis=np.array(a.axis),E=a.young,nu=0 if a.cube_test else a.poisson,force=a.force,band=a.band,exact_planes=a.cube_test)
    metrics.update(status='solved',mesh_size_mm=a.h,elapsed_seconds=time.monotonic()-start,step_sha256=hashlib.sha256(step.read_bytes()).hexdigest(),gmsh_version=gmsh.__version__,mesher_algorithm=a.algorithm,curvature_elements_per_2pi=a.curvature)
    if a.cube_test:
        expected=1*10/(210000*100);error=abs(metrics['load_weighted_displacement_mm']/expected-1);assert error<1e-8;metrics['analytic_extension_relative_error']=error
    np.savez_compressed(a.output/'solution.npz',points=xyz,tetrahedra=tet,displacement=u,vm_MPa=vm)
    meshio.write(a.output/'solution.vtu',meshio.Mesh(xyz,[('tetra',tet)],point_data={'displacement_mm':u},cell_data={'von_mises_MPa':[vm]}))
    (a.output/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');print(json.dumps(metrics),flush=True)

if __name__=='__main__':main()
