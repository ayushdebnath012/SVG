"""A-CADWORLD-001. Run: python main.py
Dependencies: Python 3.12, numpy, scipy, gmsh 4.15, scikit-fem 12.
Uses CADFEM_INPUT_DIR and CADFEM_OUTPUT_DIR. Units throughout: mm, N, MPa.
Linear tetrahedron displacement FEM (same C3D4 formulation as CalculiX).
CalculiX executable is not available; SciPy sparse direct solver is used.
"""
import os
os.environ['OMP_NUM_THREADS']='2'
os.environ['OPENBLAS_NUM_THREADS']='2'
os.environ['MKL_NUM_THREADS']='2'
import json, shutil, time, platform, sys
from pathlib import Path
import numpy as np
import scipy
from scipy.sparse.linalg import spsolve
import gmsh
import skfem
from skfem import MeshTet, Basis, ElementVector, ElementTetP1, asm
from skfem.models.elasticity import linear_elasticity

OUT=Path(os.environ.get('CADFEM_OUTPUT_DIR','.')).resolve()
IN=Path(os.environ['CADFEM_INPUT_DIR'])
OUT.mkdir(parents=True,exist_ok=True)
os.chdir(OUT)
log=[]
def say(s):
    print(s,flush=True); log.append(str(s))
def dump(name,data):
    Path(name).write_text(json.dumps(data,indent=2))

def make_mesh(h, filename):
    gmsh.clear()
    gmsh.model.add('CADWorld')
    gmsh.model.occ.importShapes(str(IN/'part.step'))
    gmsh.model.occ.synchronize()
    surf=gmsh.model.getEntities(2)
    def findface(x):
        found=[tag for _,tag in surf if abs(gmsh.model.occ.getMass(2,tag)-100)<1.e-5 and np.linalg.norm(np.array(gmsh.model.occ.getCenterOfMass(2,tag))-np.array([x,0,0]))<1.e-4]
        assert len(found)==1, found
        return found[0]
    fixed= findface(-127.5); loaded=findface(127.5)
    say(f'Identified fixed surface {fixed}, loaded surface {loaded}; areas 100 mm^2 each')
    gmsh.model.addPhysicalGroup(3,[tag for _,tag in gmsh.model.getEntities(3)],1)
    gmsh.model.setPhysicalName(3,1,'AlMg3F24')
    gmsh.model.addPhysicalGroup(2,[fixed],6); gmsh.model.setPhysicalName(2,6,'fixed_face_6')
    gmsh.model.addPhysicalGroup(2,[loaded],38); gmsh.model.setPhysicalName(2,38,'force_face_38')
    other=[t for _,t in surf if t not in (fixed,loaded)]
    gmsh.model.addPhysicalGroup(2,other,100); gmsh.model.setPhysicalName(2,100,'traction_free')
    gmsh.option.setNumber('Mesh.MeshSizeMin',0.5)
    gmsh.option.setNumber('Mesh.MeshSizeMax',h)
    gmsh.option.setNumber('Mesh.ElementOrder',1)
    gmsh.option.setNumber('Mesh.Algorithm',6)
    gmsh.option.setNumber('Mesh.Algorithm3D',1)
    gmsh.option.setNumber('Mesh.Optimize',1)
    gmsh.option.setNumber('Mesh.MshFileVersion',4.1)
    gmsh.option.setNumber('General.NumThreads',1)
    gmsh.option.setNumber('Mesh.MaxNumThreads1D',1)
    gmsh.option.setNumber('Mesh.MaxNumThreads2D',1)
    gmsh.option.setNumber('Mesh.MaxNumThreads3D',1)
    gmsh.model.mesh.generate(3)
    gmsh.write(filename)
    ids,xyz,_=gmsh.model.mesh.getNodes()
    order=np.argsort(ids); ids=ids[order]; xyz=xyz.reshape(-1,3)[order]
    eids,conn=gmsh.model.mesh.getElementsByType(4)
    tet=np.searchsorted(ids,conn.reshape(-1,4))
    def tris(s):
        _,c=gmsh.model.mesh.getElementsByType(2,s)
        return np.searchsorted(ids,c.reshape(-1,3))
    return ids,xyz,eids,tet,tris(fixed),tris(loaded)

def solve(h,name,save=False):
    start=time.time()
    ids,p,eids,t,tf,tl=make_mesh(h,name)
    nn=len(p); ne=len(t)
    say(f'Mesh hmax={h}: {nn} nodes, {ne} C3D4 tetrahedra')
    mesh=MeshTet(p.T,t.T,sort_t=False)
    basis=Basis(mesh,ElementVector(ElementTetP1()),intorder=1)
    E=70000.; nu=.3
    mu=E/(2*(1+nu)); lam=E*nu/((1+nu)*(1-2*nu))
    K=asm(linear_elasticity(lam,mu),basis).tocsr()
    f=np.zeros(3*nn)
    area=np.linalg.norm(np.cross(p[tl[:,1]]-p[tl[:,0]],p[tl[:,2]]-p[tl[:,0]]),axis=1)*.5
    assert abs(area.sum()-100)<1.e-6
    for j in range(3): np.add.at(f,3*tl[:,j]+1,area*2./3.)
    fixed=np.unique(tf); loaded=np.unique(tl)
    D=(3*fixed[:,None]+np.arange(3)).ravel()
    free=np.setdiff1d(np.arange(3*nn),D)
    u=np.zeros(3*nn)
    say(f'Assembled {basis.N} DOFs; {len(D)} constrained; K nnz={K.nnz}; total applied {f.reshape(-1,3).sum(axis=0)} N')
    u[free]=spsolve(K[free,:][:,free].tocsc(),f[free])
    r=K@u-f
    residual=float(np.linalg.norm(r[free])/np.linalg.norm(f))
    disp=u.reshape(-1,3)
    # Constant strain tetrahedra. Jacobian columns x1-x0,x2-x0,x3-x0.
    J=np.transpose(p[t[:,1:]]-p[t[:,0,None]],(0,2,1))
    invJ=np.linalg.inv(J)
    g=np.empty((ne,4,3)); g[:,1:]=invJ; g[:,0]=-invJ.sum(axis=1)
    grad=np.einsum('eai,eaj->eij',disp[t],g)
    eps=.5*(grad+np.transpose(grad,(0,2,1)))
    stress=2*mu*eps+lam*np.trace(eps,axis1=1,axis2=2)[:,None,None]*np.eye(3)
    # C3D4 has one constant stress tensor per element; extrapolation is constant.
    # Equal-weight average of all incident element tensors, then principal values.
    sn=np.zeros((nn,3,3)); counts=np.zeros(nn)
    for j in range(4):
        np.add.at(sn,t[:,j],stress)
        np.add.at(counts,t[:,j],1.)
    sn/=counts[:,None,None]
    principal=np.linalg.eigvalsh(sn)
    vm=np.sqrt(.5*((principal[:,2]-principal[:,1])**2+(principal[:,1]-principal[:,0])**2+(principal[:,2]-principal[:,0])**2))
    shear=.5*(principal[:,2]-principal[:,0])
    umag=np.linalg.norm(disp,axis=1)
    vals={'max_displacement_mm':float(umag.max()),'max_von_mises_MPa':float(vm.max()),'max_shear_stress_MPa':float(shear.max()),'max_principal_MPa':float(principal[:,2].max())}
    reactions=r.reshape(-1,3)
    react=reactions[fixed].sum(axis=0)
    moment=np.cross(p,reactions+f.reshape(-1,3)).sum(axis=0)
    volume=np.abs(np.linalg.det(J))/6
    energy=float(.5*u@(K@u))
    say(f'Results: {vals}')
    say(f'Free residual relative={residual:.3e}; reaction N={react}; moment balance Nmm={moment}; energy Nmm={energy}; time={time.time()-start:.2f}s')
    assert residual<1.e-6
    stats={'max_size_mm':h,'min_size_mm':.5,'nodes':nn,'tetrahedra':ne,'DOFs':3*nn,'quantities':vals,'relative_free_residual':residual,'total_reaction_N':react.tolist(),'moment_balance_Nmm':moment.tolist(),'strain_energy_N_mm':energy,'mesh_volume_mm3':float(volume.sum()),'force_area_mm2':float(area.sum()),'extremum_node_ids':{k:int(ids[np.argmax(v)]) for k,v in zip(vals,[umag,vm,shear,principal[:,2]])}}
    if save:
        maskfix=np.zeros(nn,dtype=bool); maskfix[fixed]=True
        maskload=np.zeros(nn,dtype=bool); maskload[loaded]=True
        np.savez_compressed('fields.npz',node_ids=ids,coordinates_mm=p,element_ids=eids,tetrahedra_node_ids=ids[t],displacement_mm=disp,nodal_stress_MPa=sn,element_stress_MPa=stress,nodal_principal_MPa=principal,nodal_von_mises_MPa=vm,nodal_max_shear_MPa=shear,fixed_mask=maskfix,loaded_mask=maskload,applied_force_N=f.reshape(-1,3),reaction_N=reactions,element_volume_mm3=volume,stress_average_element_count=counts,load_factor=np.array([1.]),coordinate_units=np.array('mm'),stress_units=np.array('MPa'),force_units=np.array('N'))
    return stats

def main():
    t0=time.time()
    say('Invocation: python main.py. Linear static small-displacement 3-D isotropic elasticity. No gravity.')
    say(f'Python {platform.python_version()}, NumPy {np.__version__}, SciPy {scipy.__version__}, scikit-fem {skfem.__version__}, Gmsh {gmsh.__version__}')
    say('CalculiX is not installed: equivalent C3D4 formulation assembled with scikit-fem; SciPy SuperLU direct solution. Nodal tensors recovered by unweighted incident-element averaging.')
    shutil.copyfile(IN/'part.step','part.step')
    gmsh.initialize()
    gmsh.logger.start()
    coarse=solve(2.7,'coarse.msh')
    target=solve(2.0,'mesh.msh',save=True)
    fine=solve(1.5,'fine.msh')
    gmshlog=gmsh.logger.get()
    gmsh.logger.stop(); gmsh.finalize()
    dump('results.json',{'outputs':target['quantities']})
    diff={k:100*(target['quantities'][k]-coarse['quantities'][k])/target['quantities'][k] for k in target['quantities']}
    dump('refinement.json',{'resolutions':[coarse,target,fine],'reported_resolution_mm':2.,'relative_change_percent_using_reported_denominator':diff,'fine_vs_reported_change_percent':{k:100*(fine['quantities'][k]-target['quantities'][k])/target['quantities'][k] for k in target['quantities']},'protocol':'Reported mesh: Gmsh 3D Delaunay, optimized first-order tetrahedra, maximum 2 mm and minimum 0.5 mm. Comparison meshes maximum 2.7 mm and 1.5 mm. Reported outputs deliberately remain at publisher-prescribed 2 mm rather than the finest mesh.','limitations':'Publisher exact Gmsh version, mesh and stress recovery details unavailable. CalculiX unavailable, so independently implemented equivalent linear C3D4 elasticity and arithmetic nodal tensor averaging used. Stress maxima at sharp boundaries can be mesh dependent; this is a protocol-resolution reproduction, not an assertion of asymptotic stress convergence.'})
    dump('environment.json',{'task_id':'A-CADWORLD-001','command':'python main.py','versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'scikit-fem':skfem.__version__,'gmsh':gmsh.__version__},'units':{'length':'mm','force':'N','stress':'MPa = N/mm^2'},'solver':'scikit-fem linear elasticity assembly, SciPy SuperLU; C3D4-equivalent (not CalculiX executable)','material':{'name':'AlMg3F24','E_MPa':70000,'Poisson_ratio':.3},'physical_groups':{'3:1':'entire aluminium solid','2:6':'fully fixed face 6, centroid [-127.5,0,0], area 100 mm2','2:38':'face 38, centroid [127.5,0,0], area 100 mm2; uniform traction [0,2,0] N/mm2','2:100':'remaining traction-free faces'},'modeling_assumptions':['Full supplied 3D solid in original mm frame, no dimensional reduction.','Linear isotropic small displacement, no gravity.','First order tetrahedra, constant strain and stress.','Fully fixed nodes on face 6 including its boundary. Consistent surface traction on all face 38 triangles.','Reported mesh maximum size 2 mm, minimum 0.5 mm. No accuracy claim beyond source linear model.'], 'field_schema':{'mapping':'Arrays use ascending Gmsh node_ids. element_ids and tetrahedra_node_ids preserve original Gmsh tags in mesh.msh; element arrays have same row order as element_ids. No node or element renumbering in exported mesh.','node_ids':'(N,) original Gmsh tags','coordinates_mm':'(N,3) original global x,y,z coordinates','element_ids':'(T,) Gmsh tetrahedron IDs','tetrahedra_node_ids':'(T,4) Gmsh node IDs, not zero-based indices','displacement_mm':'(N,3), global components','nodal_stress_MPa':'(N,3,3) symmetric Cauchy tensor, averaged element tensors','element_stress_MPa':'(T,3,3) constant unaveraged Cauchy tensors','nodal_principal_MPa':'(N,3) ascending principal stresses; last is major','nodal_von_mises_MPa':'(N,) invariant of averaged stress tensor','nodal_max_shear_MPa':'(N,) half principal range, NOT full Tresca equivalent stress','fixed_mask':'(N,) support-node Boolean mask','loaded_mask':'(N,) loaded-face Boolean mask','applied_force_N':'(N,3) consistent nodal forces','reaction_N':'(N,3) K*u-f, includes roundoff residual on free nodes','element_volume_mm3':'(T,) absolute tetrahedral volumes','stress_average_element_count':'(N,) count of incident tetrahedra','load_factor':'[1] static load factor','coordinate_units,stress_units,force_units':'Unicode arrays; no pickled objects'},'quantity_extraction':{'max_displacement_mm':'Maximum Euclidean norm of nodal displacements','max_von_mises_MPa':'Maximum von Mises invariant of the equal-weight average of incident tetrahedral stress tensors','max_shear_stress_MPa':'Maximum half-difference of major and minor principal nodal stress','max_principal_MPa':'Maximum major principal value of recovered nodal stress'},'limitations':'CalculiX not present. Equivalent linear tetrahedral equations solved independently; mesh/version and nodal recovery differences can alter extrema.'})
    say(f'NORMAL TERMINATION. Total elapsed {time.time()-t0:.2f}s')
    Path('solver.log').write_text('\n'.join(log)+'\n\nGMSH LOG\n'+'\n'.join(gmshlog))
    # Deliver the requested task-named directory as well as top-level artifacts.
    task=OUT/'A-CADWORLD-001'; task.mkdir(exist_ok=True)
    for name in ['results.json','part.step','mesh.msh','fields.npz','solver.log','refinement.json','environment.json']:
        shutil.copyfile(OUT/name,task/name)
    shutil.copyfile(Path(__file__).resolve(),task/'main.py')

if __name__=='__main__': main()
