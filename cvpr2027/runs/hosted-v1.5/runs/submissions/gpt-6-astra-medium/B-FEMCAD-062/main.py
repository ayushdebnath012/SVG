"""B-FEMCAD-062. Run: python main.py; deps cadquery, skfem, scipy, meshio.
3D small-strain isotropic elasticity; quadratic isoparametric hexahedra.
Exact symmetry reduction to y in [0,2.5], z in [25,50].
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='2'
os.environ['OMP_NUM_THREADS']='2'
import sys,time,json,platform,logging,shutil
from pathlib import Path
import numpy as np
import scipy, scipy.sparse.linalg as sla
import cadquery as cq
import skfem,meshio
from skfem import MeshHex,MeshHex2,ElementHex2,ElementVector,Basis,FacetBasis,LinearForm,asm
from skfem.models.elasticity import linear_elasticity
from skfem.io.meshio import to_meshio

E=210000.; nu=.3; lam=E*nu/((1+nu)*(1-2*nu)); mu=E/(2*(1+nu))
OUT=Path(os.environ.get('CADFEM_OUTPUT_DIR','.')); OUT.mkdir(exist_ok=True)
logfile=None
def log(s):
    print(s,flush=True)
    if logfile: logfile.write(s+'\n');logfile.flush()

def build_mesh(k):
    a=np.arctan(.5)
    cuts=[0,a,np.pi/2,np.pi-a,np.pi]
    counts=[2*k,5*k,5*k,2*k]
    theta=np.concatenate([np.linspace(cuts[i],cuts[i+1],counts[i]+1)[:-1] for i in range(4)]+[np.array([np.pi])])
    nr=4*k; ny=k
    logical=MeshHex2.from_mesh(MeshHex.init_tensor(np.linspace(0,1,nr+1),theta,np.linspace(0,2.5,ny+1)))
    p=logical.p.copy();s,th,y=p
    c=np.cos(th);si=np.sin(th)
    R=np.minimum(50/np.maximum(abs(c),1e-15),25/np.maximum(si,1e-15))
    # Radial grading puts smaller elements by the hole.
    r=10+(R-10)*s**1.5
    xyz=np.array([50+r*c,y,25+r*si])
    m=MeshHex2(xyz,logical.t)
    bf=m.boundary_facets(); ctr=m.p[:,m.facets[:,bf]].mean(axis=1)
    groups={}
    groups['fixed']=bf[np.isclose(ctr[0],0)]
    groups['traction']=bf[np.isclose(ctr[0],100)]
    groups['symmetry_y']=bf[np.isclose(ctr[1],2.5)]
    groups['symmetry_z']=bf[np.isclose(ctr[2],25)]
    groups['free_y']=bf[np.isclose(ctr[1],0)]
    groups['free_top']=bf[np.isclose(ctr[2],50)]
    groups['hole']=np.setdiff1d(bf,np.concatenate(list(groups.values())))
    return m,groups,counts,nr,ny

def stress_from_grad(g):
    eps=.5*(g+g.swapaxes(0,1));tr=np.einsum('ii...->...',eps)
    sig=2*mu*eps
    for i in range(3):sig[i,i]+=lam*tr
    return np.stack([sig[0,0],sig[1,1],sig[2,2],sig[0,1],sig[1,2],sig[0,2]],axis=-1)
def vm(sig):
    x,y,z,xy,yz,xz=np.moveaxis(sig,-1,0)
    return np.sqrt(.5*((x-y)**2+(y-z)**2+(z-x)**2)+3*(xy**2+yz**2+xz**2))

@LinearForm
def load(v,w):return 4.*v[0]

def analyze(k):
    start=time.time();m,groups,nt,nr,ny=build_mesh(k)
    el=ElementVector(ElementHex2())
    b=Basis(m,el,intorder=4)
    log(f'k={k}: elements={m.nelements}, scalar_nodes={m.p.shape[1]}, dofs={b.N}; assembly')
    K=asm(linear_elasticity(lam,mu),b).tocsc()
    fb=FacetBasis(m,el,facets=groups['traction'],intorder=4)
    f=asm(load,fb)
    D=np.unique(np.concatenate([b.get_dofs(facets=groups['fixed']).all(),b.get_dofs(facets=groups['symmetry_y']).all(['u^2']),b.get_dofs(facets=groups['symmetry_z']).all(['u^3'])]))
    free=np.setdiff1d(np.arange(b.N),D)
    log(f'assembled {time.time()-start:.2f}s, nnz={K.nnz}, applied force={f.reshape(-1,3).sum(axis=0)}; solve')
    u=np.zeros(b.N)
    u[free]=sla.spsolve(K[free][:,free],f[free])
    res=K@u-f
    log(f'solved {time.time()-start:.2f}s; residual={np.linalg.norm(res[free])/np.linalg.norm(f):.3e}')
    # Evaluate one-sided stresses at all local Q2 nodes, then average tensors
    # over incident elements. This is a convergent nodal stress recovery.
    sample=Basis(m,el,quadrature=(ElementHex2().doflocs.T,np.ones(27)))
    s_el=stress_from_grad(sample.interpolate(u).grad) # nelement,27,6
    dofs=m.dofs.element_dofs.T
    sums=np.zeros((m.p.shape[1],6)); count=np.zeros(m.p.shape[1])
    np.add.at(sums,dofs.ravel(),s_el.reshape(-1,6));np.add.at(count,dofs.ravel(),1)
    nodal=sums/count[:,None];v=vm(nodal); raw=vm(s_el)
    imax=np.argmax(v)
    quadrature_stress=stress_from_grad(b.interpolate(u).grad)
    # Scalar/vector node maps are interleaved throughout ElementVector.
    disp=u.reshape(-1,3)
    rec={'level':k,'elements':int(m.nelements),'nodes':int(m.p.shape[1]),'dofs':int(b.N),'angular_elements':sum(nt),'radial_elements':nr,'thickness_elements':ny,'maximum_hole_arc_mm':float(10*max(np.arctan(.5)/(2*k),(np.pi/2-np.arctan(.5))/(5*k))),'max_von_mises_MPa':float(v[imax]),'max_unaveraged_nodal_von_mises_MPa':float(raw.max()),'max_gauss_von_mises_MPa':float(vm(quadrature_stress).max()),'max_location_mm':m.p[:,imax].tolist(),'strain_energy_N_mm':float(.5*u@f),'applied_quarter_force_N':f.reshape(-1,3).sum(axis=0).tolist(),'reaction_quarter_N':res.reshape(-1,3).sum(axis=0).tolist(),'relative_free_residual':float(np.linalg.norm(res[free])/np.linalg.norm(f)),'elapsed_s':time.time()-start}
    edge_lengths=np.linalg.norm(m.p[:,m.edges[1]]-m.p[:,m.edges[0]],axis=0)
    rec.update(minimum_element_edge_mm=float(edge_lengths.min()),maximum_element_edge_mm=float(edge_lengths.max()),integrated_quarter_volume_mm3=float(b.dx.sum()))
    log(json.dumps(rec))
    return rec,(m,groups,disp,nodal,v,s_el,quadrature_stress,np.asarray(b.global_coordinates()).transpose(1,2,0),res.reshape(-1,3),D)

def export(data):
    m,groups,disp,stress,v,s_el,s_gauss,x_gauss,reaction,D=data
    mio=to_meshio(m,encode_cell_data=False)
    # Facet node order for Gmsh quad9: four cyclic vertices, four
    # edge midpoints, then face midpoint.
    edge_lookup={tuple(sorted(m.edges[:,i])):int(m.dofs.edge_dofs[0,i]) for i in range(m.edges.shape[1])}
    quads=[]; tags=[]; names={}
    for tag,(name,facets) in enumerate(groups.items(),2):
        names[name]=[tag,2]
        for face in facets:
            verts=m.facets[:,face].tolist()
            q=verts+[edge_lookup[tuple(sorted((verts[i],verts[(i+1)%4])))] for i in range(4)]+[int(m.dofs.facet_dofs[0,face])]
            quads.append(q);tags.append(tag)
    meshio.write(OUT/'mesh.msh',meshio.Mesh(m.p.T,[('hexahedron27',mio.cells[0].data),('quad9',np.array(quads))],cell_data={'gmsh:physical':[np.ones(m.nelements,dtype=int),np.array(tags)],'gmsh:geometrical':[np.ones(m.nelements,dtype=int),np.array(tags)]},field_data={'plate_quarter':[1,3],**names}),file_format='gmsh22',binary=True)
    masks={}
    for name,faces in groups.items():
        mask=np.zeros(m.p.shape[1],dtype=bool);mask[m.dofs.get_facet_dofs(faces).flatten()]=True;masks[name+'_mask']=mask
    fixed_mask=np.zeros((m.p.shape[1],3),dtype=bool);fixed_mask.ravel()[D]=True
    np.savez_compressed(OUT/'fields.npz',node_ids=np.arange(1,m.p.shape[1]+1),coordinates_mm=m.p.T,displacements_mm=disp,stress_MPa=stress,von_mises_MPa=v,element_ids=np.arange(1,m.nelements+1),element_node_ids=mio.cells[0].data+1,element_local_node_ids=m.dofs.element_dofs.T+1,element_local_stress_MPa=s_el,gauss_coordinates_mm=x_gauss,gauss_stress_MPa=s_gauss,reaction_N=reaction,constrained_dof_mask=fixed_mask,load_factor=np.array([1.]),**masks)
    return {'plate_quarter':[1,3],**names}

def main():
    global logfile
    logfile=open(OUT/'solver.log','w')
    versions={'python':platform.python_version(),'cadquery':cq.__version__,'skfem':skfem.__version__,'scipy':scipy.__version__,'numpy':np.__version__,'meshio':meshio.__version__}
    log('Invocation: python main.py; '+json.dumps(versions))
    plate=cq.Solid.makeBox(100,5,50)
    hole=cq.Solid.makeCylinder(10,5,cq.Vector(50,0,25),cq.Vector(0,1,0))
    part=plate.cut(hole)
    cq.exporters.export(part,str(OUT/'part.step'))
    log(f'CAD volume mm^3: {part.Volume():.10f}; analytic={25000-500*np.pi:.10f}')
    refinements=[];data=None
    for k in [3,4,5]:
        rec,data=analyze(k);refinements.append(rec)
        if len(refinements)>1:
            change=abs(rec['max_von_mises_MPa']/refinements[-2]['max_von_mises_MPa']-1)
            rec['relative_change']=change
    if rec['relative_change']>=.01:
        raise RuntimeError('Refinement criterion not reached')
    mapping=export(data)
    (OUT/'results.json').write_text(json.dumps({'outputs':{'max_von_mises_MPa':rec['max_von_mises_MPa']}},indent=2))
    (OUT/'refinement.json').write_text(json.dumps({'resolutions':refinements,'criterion':'relative change of maximum recovered nodal von Mises stress < 0.01','converged':bool(rec.get('relative_change',1)<.01)},indent=2))
    env={'versions':versions,'command':'python main.py','units':{'geometry':'mm','displacements':'mm','stress':'MPa = N/mm^2','force':'N'},'material':{'E_MPa':E,'poisson_ratio':nu},'analysis':'3D linear static elasticity, Q2 isoparametric hexahedra, 3x3x3 Gauss integration; scipy sparse direct solve','geometry':'STEP is the entire 100 x 5 x 50 mm plate with exact analytic radius-10 cylindrical through hole parallel to y','symmetry_reduction':'Mesh is y=0..2.5 and z=25..50, exact one-quarter reduction. uy=0 at y=2.5; uz=0 at z=25. Reflect through these planes with odd normal displacement and even tangential displacements to recover full solution. No x symmetry imposed.','boundary_conditions':'x=0 all displacement components fixed; x=100 uniform tx=4 MPa (1000 N / 250 mm^2), quarter resultant 250 N; other non-symmetry faces traction-free.','physical_groups':mapping,'extraction':'At all 27 local Q2 nodes compute stress from displacement derivatives using isoparametric Jacobians. Average the six tensor components equally over incident elements at a shared node, then calculate von Mises and take global maximum. Integration-point and unaveraged maxima are also recorded for diagnostics.','field_schema':{'node_ids':'Gmsh 1-based node tags, all quadratic nodes','coordinates_mm':'N x 3, x,y,z','displacements_mm':'N x 3, ux,uy,uz','stress_MPa':'N x 6 recovered nodal tensor [xx,yy,zz,xy,yz,xz]','von_mises_MPa':'N nodal von Mises','element_node_ids':'E x 27, Gmsh/meshio hex27 connectivity','element_local_node_ids':'E x 27, skfem Q2 local sample nodes in same order as element_local_stress','element_local_stress_MPa':'E x 27 x 6, one-sided element-node stress tensors','gauss_coordinates_mm':'E x 27 x 3','gauss_stress_MPa':'E x 27 x 6, unrecovered integration-point tensors','reaction_N':'N x 3, K u - f','constrained_dof_mask':'N x 3 Boolean','*_mask':'N Boolean physical boundary node masks','load_factor':'single static load factor 1'},'assumptions':['Small displacement, homogeneous isotropic elasticity.','Full thickness response retained; no plane-stress approximation.','STEP hole analytic; analysis uses converging quadratic interpolation of the cylindrical boundary.']}
    (OUT/'environment.json').write_text(json.dumps(env,indent=2))
    log('NORMAL TERMINATION; all artifacts written.')
    logfile.close()
    # Also provide the contract's task-named submission directory.  The same
    # eight artifacts remain at the output root for direct artifact consumers.
    bundle=OUT/'B-FEMCAD-062'
    bundle.mkdir(exist_ok=True)
    for name in ['results.json','part.step','mesh.msh','fields.npz','solver.log','refinement.json','environment.json']:
        shutil.copy2(OUT/name,bundle/name)
    shutil.copy2(Path(__file__),bundle/'main.py')
if __name__=='__main__':main()
