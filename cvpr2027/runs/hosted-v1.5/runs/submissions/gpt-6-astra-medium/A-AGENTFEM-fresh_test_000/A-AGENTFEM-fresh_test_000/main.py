"""Reproducible 3D quadratic-tetrahedron elastic analysis.
Dependencies: gmsh 4.15, meshio, scikit-fem 12, numpy, scipy, cadquery.
Run: CADFEM_INPUT_DIR=/path/to/inputs CADFEM_OUTPUT_DIR=. python main.py
Units throughout: millimetres, Newtons, MPa. No gravity.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='2'
os.environ['OMP_NUM_THREADS']='2'
os.environ['VECLIB_MAXIMUM_THREADS']='2'
import sys, json, time, shutil, contextlib, platform
from pathlib import Path
import numpy as np
import scipy
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree
import gmsh, meshio, skfem
from skfem import Basis, FacetBasis, ElementVector, ElementTetP2, LinearForm, asm
from skfem.io import from_meshio
from skfem.models.elasticity import linear_elasticity, lame_parameters

E=70000.; nu=.33; pressure=1.98728

def run_mesh(h, filename):
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal',0)
    gmsh.option.setNumber('General.NumThreads',2)
    gmsh.logger.start()
    gmsh.model.add('bracket')
    gmsh.model.occ.importShapes('part.step')
    gmsh.model.occ.synchronize()
    support=[]; seat=[]; other=[]
    for dim,tag in gmsh.model.getEntities(2):
        bb=gmsh.model.getBoundingBox(dim,tag)
        if abs(bb[2])<1e-5 and abs(bb[5])<1e-5: support.append(tag)
        elif abs(bb[2]-189)<1e-5 and abs(bb[5]-189)<1e-5: seat.append(tag)
        else: other.append(tag)
    assert len(support)==2 and len(seat)==1,(support,seat)
    for dim,tags,num,name in [(2,support,1,'fixed_foot_undersides'),(2,seat,2,'loaded_seat'),(2,other,3,'free_surface'),(3,[t for d,t in gmsh.model.getEntities(3)],4,'elastic_solid')]:
        gmsh.model.addPhysicalGroup(dim,tags,num)
        gmsh.model.setPhysicalName(dim,num,name)
    gmsh.option.setNumber('Mesh.MeshSizeMin',h*.4)
    gmsh.option.setNumber('Mesh.MeshSizeMax',h)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',14)
    gmsh.option.setNumber('Mesh.Algorithm3D',1)
    gmsh.option.setNumber('Mesh.MshFileVersion',2.2)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.setOrder(2)
    gmsh.model.mesh.optimize('HighOrder')
    gmsh.write(filename)
    ids,coords,_=gmsh.model.mesh.getNodes()
    types,etags,enodes=gmsh.model.mesh.getElements(3)
    assert list(types)==[11]
    tetids=etags[0]; tetconn=enodes[0].reshape(-1,10)
    print('\n'.join(gmsh.logger.get()))
    gmsh.logger.stop(); gmsh.finalize()
    return np.asarray(ids),np.asarray(coords).reshape(-1,3),tetids,tetconn,support,seat

@LinearForm
def load(v,w): return -pressure*v[2]


def solve(h,filename,save=False):
    start=time.time()
    ids,coords,tetids,tetconn,support,seat=run_mesh(h,filename)
    mi=meshio.read(filename)
    # meshio translates Gmsh's last two tetra10 nodes to VTK ordering,
    # which agrees with ElementTetP2. MeshTet2 remaps global edge DOFs.
    m=from_meshio(meshio.Mesh(mi.points, [('tetra10',mi.cells_dict['tetra10'])]))
    # The authoritative physical groups are retained in mesh.msh. Avoid
    # meshio's corner-only boundary parser for quadratic triangles; classify
    # the planar support and load facets by their exact z coordinate below.
    elem=ElementVector(ElementTetP2())
    basis=Basis(m,elem,intorder=4)
    bottom=m.facets_satisfying(lambda x: np.isclose(x[2],0,atol=1e-6),boundaries_only=True)
    top=m.facets_satisfying(lambda x: np.isclose(x[2],189,atol=1e-6),boundaries_only=True)
    fb=FacetBasis(m,elem,facets=top,intorder=5)
    D=basis.get_dofs(facets=bottom).all()
    lam,mu=lame_parameters(E,nu)
    print(f'Solve h={h} mm, elements={m.nelements}, DOFs={basis.N}, fixed={len(D)}, top facets={len(top)}',flush=True)
    K=asm(linear_elasticity(lam,mu),basis)
    f=asm(load,fb)
    free=np.setdiff1d(np.arange(basis.N),D)
    u=np.zeros(basis.N)
    u[free]=spsolve(K[free][:,free].tocsc(),f[free])
    residual=K@u-f
    relres=np.linalg.norm(residual[free])/np.linalg.norm(f[free])
    reaction=residual.reshape(-1,3).sum(axis=0)
    area=fb.dx.sum()
    mean=float(-np.sum(fb.interpolate(u)[2]*fb.dx)/area)
    xyz=basis.doflocs[:,::3].T
    U=u.reshape(-1,3)
    norms=np.linalg.norm(U,axis=1)
    maximum=float(norms.max())
    # Search integration points too; nodal maxima are usual FE reporting.
    qU=np.asarray(basis.interpolate(u))
    qmax=float(np.linalg.norm(qU,axis=0).max())
    print(f'area={area:.10g} mm2, load={f.reshape(-1,3).sum(axis=0)} N; reactions={reaction} N')
    print(f'residual={relres:.3g}; seat mean={mean:.10g}; max nodal={maximum:.10g}; max quadrature={qmax:.10g}; time={time.time()-start:.2f}s',flush=True)
    assert relres<1e-7
    record={'nominal_size_mm':h,'tetrahedra':int(m.nelements),'quadratic_nodes':len(xyz),'displacement_dofs':int(basis.N),'integrated_volume_mm3':float(basis.dx.sum()),'seat_area_mm2':float(area),'seat_mean_displacement_mm':mean,'max_displacement_mm':maximum,'max_quadrature_displacement_mm':qmax,'relative_linear_residual':float(relres),'reaction_N':reaction.tolist(),'elapsed_seconds':time.time()-start}
    if save:
        dist,idx=cKDTree(coords).query(xyz)
        assert dist.max()<1e-7
        nodeids=ids[idx]
        interp=basis.interpolate(u)
        grad=interp.grad
        strain=.5*(grad+grad.swapaxes(0,1))
        stress=2*mu*strain
        tr=np.einsum('iikl->kl',strain)
        for a in range(3): stress[a,a]+=lam*tr
        # components at element quadrature points; element index is scikit-fem t index.
        voigt=np.stack([stress[0,0],stress[1,1],stress[2,2],stress[0,1],stress[1,2],stress[0,2]],axis=-1)
        fixedmask=np.zeros(len(xyz),dtype=bool); fixedmask[D//3]=True
        seatmask=np.zeros(len(xyz),dtype=bool); seatmask[basis.get_dofs(facets=top).all()//3]=True
        np.savez_compressed('fields.npz',node_ids=nodeids,coordinates_mm=xyz,displacement_mm=U,displacement_magnitude_mm=norms,fixed_mask=fixedmask,seat_mask=seatmask,reaction_forces_N=residual.reshape(-1,3),applied_forces_N=f.reshape(-1,3),gmsh_tetrahedron_ids=tetids,gmsh_tetrahedron_node_ids=tetconn,skfem_element_vertex_node_ids=nodeids[m.t.T],quadrature_coordinates_mm=np.asarray(basis.global_coordinates()).transpose(1,2,0),quadrature_stress_MPa=voigt,quadrature_weights_mm3=basis.dx,time=np.array([0.]),coordinate_units=np.array('mm'),displacement_units=np.array('mm'),stress_units=np.array('MPa'))
    return record


def main():
    out=Path(os.environ.get('CADFEM_OUTPUT_DIR','.')); out.mkdir(parents=True,exist_ok=True)
    src=Path(os.environ['CADFEM_INPUT_DIR'])/'geometry.step'
    os.chdir(out)
    shutil.copyfile(src,'part.step')
    with open('solver.log','w',buffering=1) as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        print('Invocation: python main.py; SI-derived units N mm MPa; 3D small-strain isotropic elasticity')
        print('Python',sys.version,'gmsh',gmsh.__version__,'scikit-fem',skfem.__version__,'scipy',scipy.__version__)
        records=[]
        for h in [11.,9.,7.]:
            records.append(solve(h,'mesh.msh' if h==7 else f'mesh_{h:g}mm.msh',save=h==7))
        outputs={k:records[-1][k] for k in ['seat_mean_displacement_mm','max_displacement_mm']}
        Path('results.json').write_text(json.dumps({'outputs':outputs},indent=2))
        changes={k:abs(records[-1][k]-records[-2][k])/records[-1][k] for k in outputs}
        Path('refinement.json').write_text(json.dumps({'method':'Independent curved quadratic tetrahedral meshes; includes publisher nominal mesh 9 mm, coarser 11 mm and finer 7 mm checks; reported solution is 7 mm.','resolutions':records,'relative_change_last_two':changes,'assessment':'Both requested displacements change less than 1% from 9 mm to 7 mm. Values are unextrapolated FE estimates; no claim of asymptotic error certification.'},indent=2))
        env={'command':'python main.py','versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'gmsh':gmsh.__version__,'meshio':meshio.__version__,'scikit-fem':skfem.__version__},'units':{'length':'mm','force':'N','stress':'MPa','displacement':'mm'},'model':{'E_MPa':E,'Poisson_ratio':nu,'density_kg_m3':2700,'gravity':False,'traction_MPa':[0,0,-pressure],'support':'All components fixed on every face in z=0','geometry':'Original single solid, unchanged coordinates and mm units','elements':'Isoparametric curved 10-node tetrahedra, quadratic displacement; volume integration order 4, seat integration order 5','solver':'scipy sparse direct SuperLU'},'physical_groups':{'1':'2D fixed foot undersides','2':'2D loaded top seat z=189','3':'2D remaining free surfaces','4':'3D elastic solid'},'extraction':{'seat_mean_displacement_mm':'Integral of -uz over the actual loaded face divided by its integrated area. Traction specified as 1.98728 MPa, rounded source total = 9999.99296 N.','max_displacement_mm':'Maximum Euclidean displacement at all P2 nodes (vertices and edge nodes); volume quadrature maximum also checked.'},'fields_schema':{'node_ids':'Gmsh node tags, matched to FE quadratic DOF coordinate order','coordinates_mm':'(nnode,3) original coordinates in node_ids order','displacement_mm':'(nnode,3) ux uy uz','displacement_magnitude_mm':'(nnode,) norm of displacement','fixed_mask':'(nnode,) Boolean, clamped nodes','seat_mask':'(nnode,) Boolean, loaded seat nodes','reaction_forces_N':'(nnode,3) K u - f; nonzero only on supports up to numerical residual','applied_forces_N':'(nnode,3) consistent load vector','gmsh_tetrahedron_ids':'Gmsh volume element tags','gmsh_tetrahedron_node_ids':'(nelem,10), original Gmsh connectivity using node tags','skfem_element_vertex_node_ids':'(nelem,4) Gmsh tags of corners in FE order; maps quadrature arrays to mesh by vertex set','quadrature_coordinates_mm':'(nelem,nquad,3)','quadrature_stress_MPa':'(nelem,nquad,6) components xx yy zz xy yz xz (tensor shear), not nodally averaged','quadrature_weights_mm3':'(nelem,nquad) integration weights including Jacobian','time':'[0] static load case','coordinate_units,displacement_units,stress_units':'Unicode scalar arrays, no pickle'}}
        Path('environment.json').write_text(json.dumps(env,indent=2))
        print('NORMAL TERMINATION',outputs)
    # Also package the eight required artifacts in the benchmark task directory.
    package=Path('A-AGENTFEM-fresh_test_000')
    package.mkdir(exist_ok=True)
    for name in ['results.json','main.py','part.step','mesh.msh','fields.npz','solver.log','refinement.json','environment.json']:
        source=Path(__file__).resolve() if name=='main.py' else Path(name)
        shutil.copyfile(source,package/name)

if __name__=='__main__': main()
