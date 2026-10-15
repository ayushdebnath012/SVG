#!/usr/bin/env python3
"""SSLP311 theta=15 deg: P2 plane-stress FEM and domain J-integrals.
Dependencies: Python 3.12, numpy, scipy, gmsh, scikit-fem, meshio, cadquery.
Run: CADFEM_INPUT_DIR=/path/to/inputs CADFEM_OUTPUT_DIR=/path/to/output python main.py
Lengths: mm; stresses: MPa; unit out-of-plane thickness for the 2-D analysis.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
import sys, json, time, shutil, platform
from pathlib import Path
import numpy as np
import scipy
from scipy.sparse.linalg import spsolve
import gmsh
import meshio
import skfem
from skfem import MeshTri, Basis, FacetBasis, ElementTriP2, ElementVector, BilinearForm, LinearForm, asm, condense
from skfem.helpers import sym_grad, ddot, trace

TASK = 'A-ASTER-SSLP311-theta15'
ROOT = Path(os.environ.get('CADFEM_OUTPUT_DIR', '.')).resolve()
INPUT = Path(os.environ['CADFEM_INPUT_DIR']).resolve()
OUT = ROOT / TASK
OUT.mkdir(parents=True, exist_ok=True)
LOG = None

def log(*args):
    text = ' '.join(map(str, args))
    print(text, flush=True)
    if LOG is not None:
        LOG.write(text+'\n'); LOG.flush()

def dump(name, obj):
    with open(OUT/name, 'w') as f: json.dump(obj, f, indent=2, allow_nan=False)

# Coordinates from the CAD at z=0, including its split at the crack tips.
def cad_section():
    import cadquery as cq
    part = cq.importers.importStep(str(INPUT/'plate.step'))
    sols = part.solids().vals()
    assert len(sols) == 2
    vertices = []
    for s in sols:
        vertices.append(np.array([v.toTuple()[:2] for v in s.Vertices() if abs(v.Z)<1.e-7]))
    upper = vertices[0] if np.mean(vertices[0][:,1]) > 0 else vertices[1]
    tipr = upper[np.argmin(np.linalg.norm(upper-np.array([.965925826289,.258819045103]),axis=1))]
    tipl = -tipr
    inter = upper[np.argmin(np.linalg.norm(upper-np.array([-2.,-.535898384862]),axis=1))]
    log('CAD validation: two solids, volumes mm^3', [s.Volume() for s in sols])
    log('CAD tip coordinates mm:', tipl.tolist(), tipr.tolist())
    return tipr, inter


def make_mesh(level, tip, inter):
    """Separate coincident curves on the crack; shared bonded curves and tips.
    Returns P1 topology, subsequently used with quadratic displacement bases.
    """
    scale = level['scale']
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal', 0)
    gmsh.option.setNumber('General.NumThreads', 2)
    gmsh.logger.start()
    gmsh.model.add('inclined_bimaterial_crack')
    geo = gmsh.model.geo
    xy = [inter, -tip, tip, -inter, [2.,4.],[-2.,4.],[-2.,-4.],[2.,-4.]]
    p = [geo.addPoint(float(x),float(y),0.) for x,y in xy]
    # upper loop CCW: left bond, top crack face, right bond, right side, top, left
    bl=geo.addLine(p[0],p[1]); ct=geo.addLine(p[1],p[2]); br=geo.addLine(p[2],p[3])
    ru=geo.addLine(p[3],p[4]); top=geo.addLine(p[4],p[5]); lu=geo.addLine(p[5],p[0])
    su=geo.addPlaneSurface([geo.addCurveLoop([bl,ct,br,ru,top,lu])])
    # Lower crack curve is intentionally distinct, with only the tips shared.
    cb=geo.addLine(p[1],p[2])
    bottom=geo.addLine(p[6],p[7]); rl=geo.addLine(p[7],p[3]); ll=geo.addLine(p[0],p[6])
    sl=geo.addPlaneSurface([geo.addCurveLoop([bottom,rl,-br,-cb,-bl,ll])])
    geo.synchronize()
    group_defs = {1:(2,[su],'material_1'), 2:(2,[sl],'material_2'),
                  11:(1,[top],'top_traction'),12:(1,[bottom],'bottom_uy'),
                  13:(1,[ct],'crack_upper'),14:(1,[cb],'crack_lower'),
                  15:(1,[bl,br],'bonded_interface'),16:(1,[ru,rl,lu,ll],'free_sides'),
                  21:(0,[p[6]],'bottom_left_ux'),22:(0,[p[2]],'right_tip'),23:(0,[p[1]],'left_tip')}
    for tag,(dim,ents,name) in group_defs.items():
        gmsh.model.addPhysicalGroup(dim,ents,tag)
        gmsh.model.setPhysicalName(dim,tag,name)
    d=gmsh.model.mesh.field.add('Distance')
    gmsh.model.mesh.field.setNumbers(d,'PointsList',[p[1],p[2]])
    f=gmsh.model.mesh.field.add('MathEval')
    gmsh.model.mesh.field.setString(f,'F',f'Min({0.18*scale}, {0.006*scale}+{0.12*scale}*F{d})')
    gmsh.model.mesh.field.setAsBackgroundMesh(f)
    gmsh.option.setNumber('Mesh.MeshSizeFromPoints',0)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',0)
    gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
    gmsh.option.setNumber('Mesh.Algorithm',6)
    gmsh.model.mesh.generate(2)
    ntags, coords, _ = gmsh.model.mesh.getNodes()
    order=np.argsort(ntags); ntags=ntags[order]; coords=coords.reshape(-1,3)[order]
    def idx(tags):
        ii=np.searchsorted(ntags,tags)
        assert np.all(ntags[ii]==tags)
        return ii
    triangles=[]; material=[]; orig_eids=[]
    for ent,mat in [(su,1),(sl,2)]:
        types, tags, nodes = gmsh.model.mesh.getElements(2,ent)
        assert list(types)==[2]
        tt=idx(nodes[0]).reshape(-1,3)
        triangles.append(tt); material.extend([mat]*len(tt)); orig_eids.extend(tags[0])
    triangles=np.vstack(triangles)
    lines=[]; line_group=[]; line_entity=[]
    for tag,(dim,ents,name) in group_defs.items():
        if dim != 1: continue
        for ent in ents:
            types,tags,nodes=gmsh.model.mesh.getElements(1,ent)
            assert list(types)==[1]
            lines.extend(idx(nodes[0]).reshape(-1,2))
            line_group.extend([tag]*len(tags[0])); line_entity.extend([ent]*len(tags[0]))
    point_nodes={tag:int(idx(gmsh.model.mesh.getNodes(0,ents[0])[0])[0])
                 for tag,(dim,ents,name) in group_defs.items() if dim==0}
    gmsh_messages=gmsh.logger.get(); gmsh.logger.stop(); gmsh.finalize()
    log('Gmsh level',level['name'], 'vertices',len(coords), 'triangles',len(triangles))
    for msg in gmsh_messages:
        if 'Warning' in msg or 'Error' in msg: log(msg)
    m = MeshTri(coords[:,:2].T,triangles.T)
    assert m.t.shape[1]==len(material)
    # MeshTri sorts vertex indices within elements, but keeps element order.
    return m, np.array(material), np.array(lines), np.array(line_group), np.array(line_entity), point_nodes, np.array(orig_eids), group_defs

@BilinearForm
def elasticity(u,v,w):
    return 2*w.mu*ddot(sym_grad(u),sym_grad(v))+w.lam*trace(sym_grad(u))*trace(sym_grad(v))

@LinearForm
def top_load(v,w):
    return 100.*v[1]


def energy_difference_check(m, tip, mu, lam, f, fixed):
    """Independent compliance derivative after re-solving perturbed crack lengths.
    Transport vertices tangentially using a compact radial weight. Outer edges
    and supports are unchanged; crack-face independence and material IDs persist.
    """
    h=1.e-4  # mm, central finite difference
    values=[]; energies=[]
    e=tip/np.linalg.norm(tip)
    for p,direction in [(tip,e),(-tip,-e)]:
        r=np.linalg.norm(m.p-p[:,None],axis=0)
        t=np.clip((r-.2)/.2,0,1)
        q=1-3*t*t+2*t*t*t
        pair=[]
        for da in [-h,h]:
            mm=MeshTri(m.p+da*direction[:,None]*q[None,:],m.t)
            bb=Basis(mm,ElementVector(ElementTriP2()),intorder=6)
            kk=asm(elasticity,bb,mu=mu[:,None],lam=lam[:,None])
            aa,ff,uu,ii=condense(kk,f,D=fixed)
            uu[ii]=spsolve(aa,ff)
            pair.append(.5*float(f@uu))
        values.append((pair[1]-pair[0])/(2*h)*1000.)
        energies.append(pair)
    log('Independent re-solved compliance derivatives, medium mesh [right,left] J/m^2',values)
    return {'extension_increment_mm':h,'G_right_tip_J_per_m2':values[0],
            'G_left_tip_J_per_m2':values[1],'strain_energies_N_mm':energies,
            'method':'Central derivative of U=0.5 f dot u at fixed load. Mesh vertices transported along each tip advance direction with q=1 at r<=0.2 mm, smooth cubic decay to zero at r=0.4 mm. Re-solved both positive and negative extensions independently. Unit numerical thickness=1 mm, then converted N/mm to J/m^2.',
            'energy_order':'rows right,left; columns a-h,a+h. Auxiliary meshes only; reported results remain direct domain integrals on unperturbed finest mesh.'}


def solve_level(level, tip, inter, final=False):
    start=time.time()
    m, mats, lines, lg, le, pn, orig_eids, groups=make_mesh(level,tip,inter)
    elem=ElementVector(ElementTriP2())
    basis=Basis(m,elem,intorder=6)
    scalar=Basis(m,ElementTriP2(),intorder=6)
    young=np.where(mats==1,2.e6,2.e5)
    nu=.3
    mu=young/(2*(1+nu))
    lam=young*nu/(1-nu**2)  # reduced plane-stress lambda
    K=asm(elasticity,basis,mu=mu[:,None],lam=lam[:,None])
    topfac=m.facets_satisfying(lambda x:np.isclose(x[1],4.,atol=1.e-9))
    botfac=m.facets_satisfying(lambda x:np.isclose(x[1],-4.,atol=1.e-9))
    f=asm(top_load,FacetBasis(m,elem,facets=topfac,intorder=4))
    dy=basis.get_dofs(facets=botfac).all('u^2')
    dx=basis.get_dofs(nodes=np.array([pn[21]])).all('u^1')
    fixed=np.unique(np.r_[dx,dy])
    A,b,u,free=condense(K,f,D=fixed)
    log('P2 displacement system',level['name'], 'DOFs',basis.N,'free',len(free),'nonzeros',A.nnz)
    u[free]=spsolve(A,b)
    resid=K@u-f
    strain_energy=.5*float(u@(K@u))
    relative_residual=float(np.linalg.norm(resid[free])/np.linalg.norm(f[free]))
    reaction=np.array([resid[fixed[fixed%2==c]].sum() for c in [0,1]])
    log('Energy N mm per unit mm thickness',strain_energy,'relative residual',relative_residual,'reactions N',reaction)
    assert relative_residual < 1.e-6
    assert np.allclose(reaction,[0.,-400.],rtol=1.e-7,atol=1.e-6)
    assert np.allclose(basis.dx.sum(),32.,rtol=1.e-10)
    field=basis.interpolate(u)
    grad=field.grad
    strain=.5*(grad+np.swapaxes(grad,0,1))
    tr=strain[0,0]+strain[1,1]
    stress=2*mu[None,None,:,None]*strain
    stress[0,0]+=lam[:,None]*tr
    stress[1,1]+=lam[:,None]*tr
    W=.5*np.einsum('ijeq,ijeq->eq',stress,strain)
    pos=np.asarray(basis.global_coordinates())
    e=tip/np.linalg.norm(tip)
    rings=np.array([[.08,.16],[.10,.25],[.20,.40],[.30,.60],[.45,.80]])
    jall=[]; q_masks=[]
    for name,tippos,direction in [('right',tip,e),('left',-tip,-e)]:
        relative=pos-tippos[:,None,None]
        r=np.sqrt(np.sum(relative**2,axis=0))
        # configurational flux opposite to Eshelby: sigma_ij du_i/ds - W e_j
        du_ds=np.einsum('ikeq,k->ieq',grad,direction)
        flux=np.einsum('ijeq,ieq->jeq',stress,du_ds)-direction[:,None,None]*W
        js=[]
        for rin,rout in rings:
            t=(r-rin)/(rout-rin)
            mask=(t>0)&(t<1)
            dq_dr=np.where(mask,-6*np.clip(t,0,1)*(1-np.clip(t,0,1))/(rout-rin),0.)
            dq=relative*(dq_dr/np.maximum(r,1.e-30))[None,:,:]
            val=float(np.sum(np.einsum('jeq,jeq->eq',flux,dq)*basis.dx)*1000.)
            js.append(val); q_masks.append(mask)
        jall.append(js)
        log('J',name,'J/m^2, radii mm',rings.tolist(),':',js)
    jall=np.array(jall)
    # The two middle/large local rings are well-separated from tip and plate boundary.
    result=np.mean(jall[:,2:4],axis=1)
    record={'name':level['name'],'far_target_size_mm':.18*level['scale'],
            'tip_target_size_mm':.006*level['scale'],'size_distance_slope':.12*level['scale'],
            'vertices':int(m.nvertices),'triangles':int(m.nelements),'quadratic_nodes':int(scalar.N),'displacement_dofs':int(basis.N),
            'J_ring_radii_mm':rings.tolist(),'J_right_rings_J_per_m2':jall[0].tolist(),
            'J_left_rings_J_per_m2':jall[1].tolist(),
            'G_right_tip':float(result[0]),'G_left_tip':float(result[1]),
            'strain_energy_N_mm_per_unit_thickness':strain_energy,
            'reaction_N_per_unit_thickness':reaction.tolist(),'relative_free_residual':relative_residual,
            'wall_seconds':time.time()-start}
    if level['name']=='medium':
        record['independent_energy_derivative']=energy_difference_check(m,tip,mu,lam,f,fixed)
    if final:
        save_fields_mesh(m,scalar,basis,u,stress,strain,W,pos,mats,lines,lg,le,pn,orig_eids,groups,fixed,f,resid,rings,jall,np.array(q_masks))
    return record


def save_fields_mesh(m,scalar,basis,u,stress,strain,W,pos,mats,lines,lg,le,pn,orig_eids,groups,fixed,f,resid,rings,jall,q_masks):
    # P2 scalar DOFs provide exactly the Gmsh triangle6 node convention.
    coords=np.column_stack([scalar.doflocs.T,np.zeros(scalar.N)])
    tri=scalar.element_dofs.T.copy()
    facet_map={tuple(sorted(v)):k for k,v in enumerate(m.facets.T)}
    line3=[]
    for n1,n2 in lines:
        fi=facet_map[tuple(sorted([int(n1),int(n2)]))]
        line3.append([n1,n2,int(scalar.facet_dofs[0,fi])])
    pts=np.array([[pn[k]] for k in [21,22,23]])
    nc=[len(pts),len(line3),len(tri)]
    # Node indices in memory are zero based; exported Gmsh node IDs are index+1.
    cell_data={'gmsh:physical':[np.array([21,22,23]),lg,mats],
               'gmsh:geometrical':[np.array([21,22,23]),le,mats]}
    fd={name:np.array([tag,dim]) for tag,(dim,_,name) in groups.items()}
    meshio.write(str(OUT/'mesh.msh'),meshio.Mesh(coords,[('vertex',pts),('line3',np.array(line3)),('triangle6',tri)],cell_data=cell_data,field_data=fd),file_format='gmsh22',binary=False)
    uv=np.zeros((scalar.N,2))
    for comp, indices in enumerate(basis.split_indices()): uv[:,comp]=u[indices]
    bc_mask=np.zeros((scalar.N,2),dtype=bool)
    for comp,indices in enumerate(basis.split_indices()): bc_mask[:,comp]=np.isin(indices,fixed)
    boundary_mask=np.zeros((scalar.N,6),dtype=bool)
    for col,tag in enumerate([11,12,13,14,15,16]):
        boundary_mask[np.unique(np.array(line3)[lg==tag]),col]=True
    offset=nc[0]+nc[1]
    np.savez_compressed(OUT/'fields.npz',
        node_ids=np.arange(1,scalar.N+1,dtype=np.int64),coordinates_mm=coords,
        triangle6_node_ids=tri+1,element_ids=np.arange(offset+1,offset+len(tri)+1,dtype=np.int64),
        source_gmsh_triangle_ids=orig_eids,material_id=mats,
        displacement_mm=uv,prescribed_displacement_mask=bc_mask,boundary_masks=boundary_mask,
        quadrature_coordinates_mm=pos.transpose(1,2,0),quadrature_weights_mm2=basis.dx,
        strain_at_quadrature=strain.transpose(2,3,0,1),stress_at_quadrature_MPa=stress.transpose(2,3,0,1),
        strain_energy_density_MPa=W,forces_N_per_unit_thickness=f.reshape(-1,2),
        reactions_N_per_unit_thickness=resid.reshape(-1,2),
        integral_radii_mm=rings,J_integrals_J_per_m2=jall,integral_annulus_masks=q_masks.reshape(2,len(rings),m.nelements,-1),
        load_factor=np.array([1.]),length_unit=np.array('mm'),stress_unit=np.array('MPa'),
        energy_release_rate_unit=np.array('J/m^2'))


def main():
    global LOG
    LOG=open(OUT/'solver.log','w')
    start=time.time()
    log(TASK,'invocation: python main.py')
    log('Versions:',platform.python_version(), 'numpy',np.__version__, 'scipy',scipy.__version__, 'gmsh',gmsh.__version__, 'skfem',skfem.__version__, 'meshio',meshio.__version__)
    shutil.copyfile(INPUT/'plate.step',OUT/'part.step')
    if Path(__file__).resolve() != (OUT/'main.py').resolve(): shutil.copyfile(__file__,OUT/'main.py')
    tip,inter=cad_section()
    levels=[{'name':'coarse','scale':1.}, {'name':'medium','scale':.65}, {'name':'fine','scale':.4225},
            {'name':'very_fine','scale':.274625}]
    records=[]
    for i,level in enumerate(levels):
        records.append(solve_level(level,tip,inter,final=i==len(levels)-1))
    final=records[-1]
    outputs={k:final[k] for k in ['G_right_tip','G_left_tip']}
    dump('results.json',{'outputs':outputs})
    changes={k:abs(records[-1][k]-records[-2][k])/abs(records[-1][k]) for k in outputs}
    dump('refinement.json',{'method':'Independent Gmsh meshes; conforming quadratic triangles, plane stress; refinement reduces all size parameters by 0.65.',
                           'levels':records,'relative_change_last_two':changes,
                           'reported_value':'Arithmetic mean of domain J over annuli [0.20,0.40] and [0.30,0.60] mm on finest mesh; no extrapolation.'})
    dump('environment.json',environment(records))
    log('Results',outputs,'last relative changes',changes)
    log('NORMAL TERMINATION. Wall seconds',time.time()-start)
    LOG.close()


def environment(records):
    return {'task_id':TASK,'command':'python main.py','python':platform.python_version(),
      'libraries':{'numpy':np.__version__,'scipy':scipy.__version__,'gmsh':gmsh.__version__,'scikit-fem':skfem.__version__,'meshio':meshio.__version__,'cadquery':'2.8.0'},
      'units':{'CAD':'mm','coordinates':'mm','displacement':'mm','stress':'MPa = N/mm^2','J_internal':'N/mm','G_output':'J/m^2; 1 N/mm = 1000 J/m^2'},
      'geometry':'part.step is an unchanged copy of input plate.step, two 0.1 mm extruded solids. FEM is the z=0 cross-section. Geometry vertices are read from CAD. No 0.1 mm thickness factor enters G per unit thickness.',
      'materials':{'1':{'E_MPa':2000000.,'nu':.3,'region':'above inclined interface'},'2':{'E_MPa':200000.,'nu':.3,'region':'below inclined interface'}},
      'formulation':'Small-strain linear isotropic plane stress, conforming six-node triangles with quadratic displacement and affine geometry. Quadrature order 6. Direct sparse solve (scipy SuperLU). lambda_ps=E nu/(1-nu^2), mu=E/(2(1+nu)).',
      'boundary_conditions':{'top':'t=(0,100) MPa at y=4','bottom':'uy=0 at y=-4; ux free except bottom-left','bottom_left':'ux=0 at (-2,-4)','crack':'Two independent coincident curves, separate nodes/displacements except shared tip nodes. Both crack faces traction-free. No contact.','bonded_interface':'Shared mesh nodes and P2 edge DOFs outside the crack, guaranteeing perfect bond.','other_edges':'traction free'},
      'physical_groups':{1:'material_1, surface',2:'material_2, surface',11:'top_traction, line',12:'bottom_uy, line',13:'crack_upper, line',14:'crack_lower, line',15:'bonded_interface, line',16:'free_sides, line',21:'bottom_left_ux, point',22:'right_tip, point',23:'left_tip, point'},
      'quantity_extraction':{'equation':'G = integral_A [sigma_ij (du_i/ds) - W e_j] q_,j dA, e = outward tangent to the interface from each tip, W = 0.5 sigma:epsilon.',
        'q':'Radial q=1 within rin; q=1-3t^2+2t^3 with t=(r-rin)/(rout-rin) in annulus; q=0 beyond rout. Exact analytical gradient evaluated at quadrature points.',
        'interface_terms':'No additional material-gradient term is needed: the virtual crack advance direction e is tangent to the straight interface; elasticity is constant along that direction. Bonded interface contributions cancel; traction-free crack has n dot e=0.',
        'reported':'Mean of finest-mesh rings [0.20,0.40] and [0.30,0.60] mm. Five rings checked independently for path independence. Left advance direction is negative interface tangent; right is positive.',
        'conversion':'Calculated integral in MPa mm = N/mm, multiplied by 1000 for J/m^2.'},
      'field_schema':{
        'node_ids':'N int64 IDs in mesh.msh, one based; row order for all nodal arrays.',
        'coordinates_mm':'N x 3, z=0, includes quadratic midside nodes.',
        'triangle6_node_ids':'T x 6 IDs (v0,v1,v2,mid01,mid12,mid20); actual FEM connectivity, same as MSH.',
        'element_ids':'T one-based element IDs in mesh.msh. Point and line elements precede triangles.',
        'source_gmsh_triangle_ids':'Original linear Gmsh triangle tags before deterministic quadratic-node export; diagnostic only.',
        'material_id':'T array, 1 upper stiff or 2 lower compliant, matches physical group.',
        'displacement_mm':'N x 2, ux,uy at P2 nodes.',
        'prescribed_displacement_mask':'N x 2 Boolean mask of zero displacement constraints.',
        'boundary_masks':'N x 6 Boolean columns for physical line groups 11,12,13,14,15,16.',
        'quadrature_coordinates_mm':'T x Q x 2. Evaluation coordinates of FEM integration points.',
        'quadrature_weights_mm2':'T x Q. Physical area weights.',
        'strain_at_quadrature':'T x Q x 2 x 2 tensor strain, dimensionless; not engineering shear.',
        'stress_at_quadrature_MPa':'T x Q x 2 x 2 Cauchy stress, sigma_zz=0 by plane stress.',
        'strain_energy_density_MPa':'T x Q, W=0.5 sigma:epsilon.',
        'forces_N_per_unit_thickness':'N x 2 consistent applied forces, integrated using numerical thickness=1 mm.',
        'reactions_N_per_unit_thickness':'N x 2 residual K u-f, reactions at constrained components; near zero on free DOFs.',
        'integral_radii_mm':'5 x 2 inner,outer radii.',
        'J_integrals_J_per_m2':'2 x 5, rows right tip,left tip; columns ring order.',
        'integral_annulus_masks':'2 x 5 x T x Q, masks of integration annuli.',
        'load_factor':'[1.0], one static load state. No physical time dependence.',
        '*_unit':'Unicode scalar unit metadata, no object arrays.'},
      'limitations':['No contact between crack faces (as specified).','J convergence assessed with independent mesh resolutions and finite annuli; no singular crack-tip enrichment or extrapolation used.','Small-strain, plane-stress idealization; exchange-solid thickness is not a physical multiplier on reported G.']}

if __name__ == '__main__': main()
