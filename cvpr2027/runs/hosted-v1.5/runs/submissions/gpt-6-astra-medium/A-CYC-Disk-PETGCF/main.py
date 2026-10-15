"""Reproduce 3D quadratic-tetrahedron PETG-CF disk analysis.
Dependencies: gmsh 4.15, scikit-fem 12, numpy, scipy, meshio.
Invoke: CADFEM_INPUT_DIR=/path/to/inputs CADFEM_OUTPUT_DIR=/path/to/output python main.py
Units: mm, N, MPa. No dimensional reduction.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='2'
os.environ['OMP_NUM_THREADS']='2'
import sys, json, shutil, time, platform, logging
from pathlib import Path
import numpy as np
import scipy
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree
import gmsh, meshio, skfem
from skfem import MeshTet2, Basis, FacetBasis, ElementTetP2, ElementVector, LinearForm, asm
from skfem.models.elasticity import linear_elasticity

class Tee:
    def __init__(self, f): self.f=f
    def write(self,s): self.f.write(s); self.f.flush(); sys.__stdout__.write(s); sys.__stdout__.flush()
    def flush(self): self.f.flush()

def dump(name, data):
    Path(name).write_text(json.dumps(data,indent=2,default=lambda x: x.item() if isinstance(x,np.generic) else x.tolist()))

def run_mesh(h, spec, export=False):
    t0=time.time()
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal',1)
    gmsh.option.setNumber('General.NumThreads',2)
    gmsh.logger.start()
    gmsh.model.add('Disk')
    gmsh.model.occ.importShapes('part.step')
    gmsh.model.occ.synchronize()
    # Face correspondence uses area and centre of mass, never STEP face enumeration.
    remaining=set(t for d,t in gmsh.model.getEntities(2))
    faces={}; matches={}
    for f in spec['faces']:
        target=np.array(f['centroid_mm']); area=f['area_mm2']
        def distance(t):
            return np.linalg.norm(np.array(gmsh.model.occ.getCenterOfMass(2,t))-target)+abs(gmsh.model.occ.getMass(2,t)-area)/max(1,area)
        tag=min(remaining,key=distance)
        assert distance(tag)<0.025,(f,tag,distance(tag))
        remaining.remove(tag)
        i=f['face_index']; faces[i]=tag
        matches[str(i)]={'gmsh_surface':tag,'area_mm2':gmsh.model.occ.getMass(2,tag),'centroid_mm':gmsh.model.occ.getCenterOfMass(2,tag),'type':gmsh.model.getType(2,tag)}
        gmsh.model.addPhysicalGroup(2,[tag],i)
        gmsh.model.setPhysicalName(2,i,'face_'+str(i))
    assert not remaining
    volumes=[t for d,t in gmsh.model.getEntities(3)]
    gmsh.model.addPhysicalGroup(3,volumes,101)
    gmsh.model.setPhysicalName(3,101,'PETG_CF')
    gmsh.option.setNumber('Mesh.MeshSizeMax',h)
    gmsh.option.setNumber('Mesh.MeshSizeMin',h*0.12)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',18)
    gmsh.option.setNumber('Mesh.Algorithm3D',1)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.setOrder(2)
    gmsh.option.setNumber('Mesh.MshFileVersion',2.2)
    name='mesh.msh' if export else 'mesh_h'+str(h)+'.msh'
    gmsh.write(name)
    node_ids, coords, _=gmsh.model.mesh.getNodes()
    coords=coords.reshape(-1,3)
    eltypes, eids, enodes=gmsh.model.mesh.getElements(3)
    assert list(eltypes)==[11]
    tet_ids=eids[0]; tet_node_ids=enodes[0].reshape(-1,10)
    print('\nGMSH LOG\n'+'\n'.join(gmsh.logger.get()))
    gmsh.logger.stop(); gmsh.finalize()
    print('Mesh generation seconds',time.time()-t0)
    mi=meshio.read(name)
    tet=mi.cells_dict['tetra10']
    # Check connectivity and field element ordering against exported original Gmsh tags.
    _, point_to_original=cKDTree(coords).query(mi.points)
    assert np.array_equal(node_ids[point_to_original[tet]],tet_node_ids[:,[0,1,2,3,4,5,6,7,9,8]])
    m=MeshTet2(mi.points.T,tet.T)
    dist, sk_to_gm=cKDTree(coords).query(m.p.T)
    assert max(dist)<1e-7
    # Map meshio's corner nodes to internal vertex numbering to find exact boundary facets.
    dist, mi_to_sk=cKDTree(m.p.T).query(mi.points)
    assert max(dist)<1e-7
    facet_lookup={tuple(sorted(f)):i for i,f in enumerate(m.facets.T)}
    triangles=mi.cells_dict['triangle6']
    surface_tags=mi.cell_data_dict['gmsh:physical']['triangle6']
    boundary={}
    for i in faces:
        tri=mi_to_sk[triangles[surface_tags==i,:3]]
        boundary[i]=np.array([facet_lookup[tuple(sorted(t))] for t in tri])
    elem=ElementVector(ElementTetP2())
    b=Basis(m,elem,intorder=4)
    print('Resolution',h,'tetrahedra',m.nelements,'nodes',m.p.shape[1],'DOFs',b.N,flush=True)
    E=3000.; nu=.36
    mu=E/(2*(1+nu)); lam=E*nu/((1+nu)*(1-2*nu))
    K=asm(linear_elasticity(lam,mu),b)
    F=np.zeros(b.N)
    loads={2:np.array([0.,-31.165,94.894]),19:np.array([0.,-31.169,94.905])}
    integration={}
    for i,force in loads.items():
        fb=FacetBasis(m,elem,facets=boundary[i],intorder=5)
        discrete_area=float(fb.dx.sum())
        # Normalize by integrated curved mesh area to apply the specified total force exactly.
        traction=force/discrete_area
        @LinearForm
        def load(v,w): return sum(traction[j]*v[j] for j in range(3))
        F+=asm(load,fb)
        integration[str(i)]={'cad_area_mm2':matches[str(i)]['area_mm2'],'integrated_area_mm2':discrete_area,'traction_MPa':traction.tolist(),'force_N':force.tolist()}
    D=b.get_dofs(facets=np.concatenate([boundary[8],boundary[13]])).all()
    free=np.setdiff1d(np.arange(b.N),D)
    print('Assembly done, seconds',time.time()-t0,'matrix nnz',K.nnz,flush=True)
    u=np.zeros(b.N)
    u[free]=spsolve(K[free][:,free].tocsc(),F[free])
    print('Solved, seconds',time.time()-t0,flush=True)
    residual=K@u-F
    relative_residual=np.linalg.norm(residual[free])/np.linalg.norm(F[free])
    assert relative_residual<1e-6
    nodal_u=u.reshape(-1,3)
    assert np.allclose(b.doflocs[:,::3],m.p)
    norm=np.linalg.norm(nodal_u,axis=1)
    maximum=float(norm.max())
    forces=F.reshape(-1,3).sum(axis=0)
    reactions=residual.reshape(-1,3).sum(axis=0)
    print('maximum displacement',maximum,'at',m.p[:,norm.argmax()], 'force',forces,'reaction',reactions,'residual',relative_residual,flush=True)
    rec={'mesh_size_max_mm':h,'tetrahedron_order':2,'tetrahedra':m.nelements,'nodes':m.p.shape[1],'dofs':b.N,'max_displacement_mm':maximum,'max_location_mm':m.p[:,norm.argmax()].tolist(),'strain_energy_Nmm':float(.5*u@(K@u)),'force_N':forces.tolist(),'reaction_N':reactions.tolist(),'free_relative_residual':float(relative_residual),'seconds':time.time()-t0,'load_integration':integration}
    if export:
        fixed=np.zeros(m.p.shape[1],dtype=np.uint8); fixed[np.unique(D//3)]=1
        loaded=np.zeros((m.p.shape[1],2),dtype=np.uint8)
        for j,i in enumerate(loads): loaded[np.unique(b.get_dofs(facets=boundary[i]).all()//3),j]=1
        # Quadrature-point symmetric Cauchy stress, original (not averaged) FEM result.
        uh=b.interpolate(u)
        grad=uh.grad
        eps=.5*(grad+grad.swapaxes(0,1))
        sigma=2*mu*eps
        trace=sum(eps[i,i] for i in range(3))
        for i in range(3): sigma[i,i]+=lam*trace
        mises=np.sqrt(.5*((sigma[0,0]-sigma[1,1])**2+(sigma[1,1]-sigma[2,2])**2+(sigma[2,2]-sigma[0,0])**2)+3*(sigma[0,1]**2+sigma[0,2]**2+sigma[1,2]**2))
        # Order of the volume elements in meshio is the original gmsh element order.
        np.savez_compressed('fields.npz',node_ids=node_ids[sk_to_gm],coordinates_mm=m.p.T,displacement_mm=nodal_u,displacement_magnitude_mm=norm,fixed_mask=fixed,loaded_masks=loaded,applied_nodal_force_N=F.reshape(-1,3),reaction_nodal_force_N=residual.reshape(-1,3),element_ids=tet_ids,element_node_ids_gmsh=tet_node_ids,stress_MPa=sigma.transpose(2,3,0,1),von_mises_MPa=mises,quadrature_coordinates_mm=b.global_coordinates().transpose(1,2,0),static_load_factor=np.array([1.]),coordinate_units=np.array('mm'),stress_units=np.array('MPa'))
    return rec,matches

def main():
    start=time.time()
    inputs=Path(os.environ['CADFEM_INPUT_DIR'])
    out=Path(os.environ.get('CADFEM_OUTPUT_DIR','.')).resolve(); out.mkdir(exist_ok=True,parents=True); os.chdir(out)
    with open('solver.log','w') as log:
        sys.stdout=Tee(log)
        print('Invocation: python main.py; linear static 3D isotropic PETG-CF; mm,N,MPa')
        print('Python',sys.version,'gmsh',gmsh.__version__,'skfem',skfem.__version__,'numpy',np.__version__,'scipy',scipy.__version__,'meshio',meshio.__version__)
        shutil.copyfile(inputs/'part.step','part.step')
        spec=json.loads((inputs/'faces.json').read_text())
        records=[]
        for h,export in [(2.7,False),(2.0,False),(1.5,True)]:
            r,mapping=run_mesh(h,spec,export); records.append(r)
        change=abs(records[-1]['max_displacement_mm']-records[-2]['max_displacement_mm'])/records[-1]['max_displacement_mm']
        dump('results.json',{'outputs':{'max_displacement_mm':records[-1]['max_displacement_mm']}})
        dump('refinement.json',{'resolutions':records,'relative_change_last_two':change,'protocol':'Three independently generated Gmsh quadratic tetrahedral meshes, including source maximum size 2 mm and further refinement to 1.5 mm. Gmsh rather than Netgen.'})
        dump('environment.json',{'python':platform.python_version(),'gmsh':gmsh.__version__,'scikit_fem':skfem.__version__,'numpy':np.__version__,'scipy':scipy.__version__,'meshio':meshio.__version__,'command':'python main.py','units':{'length':'mm','force':'N','stress':'MPa'},'material':{'E_MPa':3000,'poisson_ratio':.36},'model':'Full 3D small-displacement isotropic linear elasticity, curved isoparametric quadratic tetrahedra; no gravity, no contact. Degree-4 volume and degree-5 surface quadrature. Direct sparse solution. All components fixed on both halves of central bore. Source geometry copied unchanged.','boundary_conditions':{'fixed_faces':[8,13],'loaded_faces':[2,19],'loads_N':{'2':[0,-31.165,94.894],'19':[0,-31.169,94.905]},'load_rounding':'Face forces are used as given; their sum differs by 0.001 N from rounded headline total.','traction':'Constant global-direction traction separately on each half-cylinder. Divided by integrated curved area; areas agree with CAD within discretization error.'},'physical_groups':{'surfaces':'tag i = geometry-matched source face i (1..20)','volume':{'101':'PETG_CF'}},'geometry_matching':mapping,'quantity_extraction':'Maximum Euclidean displacement norm over all quadratic FE nodes, including mid-edge nodes, at load factor 1.','field_schema':{'node_ids':'Gmsh node tags; all nodal arrays share this row ordering.','coordinates_mm':'N x 3 original coordinates x,y,z','displacement_mm':'N x 3 solved displacement','displacement_magnitude_mm':'N vector','fixed_mask':'N uint8, 1 on fixed faces','loaded_masks':'N x 2 uint8, columns face 2 and face 19','applied_nodal_force_N':'N x 3 consistent nodal traction loads','reaction_nodal_force_N':'N x 3 residual K u - f; physical reactions on fixed nodes, numerical residual otherwise','element_ids':'Gmsh tetrahedron element tags, ordering of stress and quadrature arrays','element_node_ids_gmsh':'elements x 10 original Gmsh connectivity, Gmsh tetra10 ordering','stress_MPa':'elements x quadrature points x 3 x 3 Cauchy stress tensor, no smoothing','von_mises_MPa':'elements x quadrature points','quadrature_coordinates_mm':'elements x quadrature points x 3','static_load_factor':'single solved static load factor 1','coordinate_units':'unicode scalar mm','stress_units':'unicode scalar MPa'},'mesh_convergence_relative_change':change})
        print('Successful termination; total wall seconds',time.time()-start,'relative refinement change',change)
        sys.stdout=sys.__stdout__

if __name__=='__main__': main()
