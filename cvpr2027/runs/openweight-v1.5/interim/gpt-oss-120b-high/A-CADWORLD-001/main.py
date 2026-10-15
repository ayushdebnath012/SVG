#!/usr/bin/env python
# Linear static analysis of the CADWorld part.
import os, json, numpy as np, meshio, gmsh, skfem
from skfem import MeshTet, Basis, ElementVector, ElementTetP1, asm, condense, solve
from skfem.models.elasticity import linear_elasticity, lame_parameters, linear_stress
from skfem.helpers import sym_grad

def write_log(msg):
    with open('solver.log','a') as f:
        f.write(msg+'\n')

def generate_mesh(max_elem_size, filename):
    gmsh.initialize()
    gmsh.model.add('part')
    gmsh.model.occ.importShapes('part.step')
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber('Mesh.CharacteristicLengthMin',0.5)
    gmsh.option.setNumber('Mesh.CharacteristicLengthMax',max_elem_size)
    gmsh.model.mesh.generate(3)
    gmsh.write(filename)
    gmsh.finalize()
    write_log(f'Generated mesh {filename} with max size {max_elem_size} mm')

def load_mesh(filename):
    m = meshio.read(filename)
    pts = m.points[:,:3].T
    tets = m.cells_dict['tetra'].T
    mesh = MeshTet(pts,tets)
    return mesh,m

def get_face_nodes(pts, bbox, tol=1e-3):
    # bbox format: [xmin, ymin, zmin, xmax, ymax, zmax]
    x,y,z = pts
    xmin, ymin, zmin, xmax, ymax, zmax = bbox
    mask = (x>=xmin-tol)&(x<=xmax+tol)&(np.abs(y - ((ymin+ymax)/2))<=tol)&(z>=zmin-tol)&(z<=zmax+tol)
    return np.where(mask)[0]

def compute_load_vector(meshio_mesh, pts, load_face, traction):
    N = pts.shape[1]
    F = np.zeros(3*N)
    tris = meshio_mesh.cells_dict.get('triangle')
    if tris is None:
        return F
    xmin, ymin, zmin, xmax, ymax, zmax = load_face['bbox_mm']
    tol = 1e-3
    for tri in tris:
        verts = pts[:,tri]
        centroid = verts.mean(axis=1)
        if (centroid[0]>=xmin-tol) and (centroid[0]<=xmax+tol) and (abs(centroid[1] - ((ymin+ymax)/2))<=tol) and (centroid[2]>=zmin-tol) and (centroid[2]<=zmax+tol):
            v0,v1,v2 = verts[:,0],verts[:,1],verts[:,2]
            area = 0.5*np.linalg.norm(np.cross(v1-v0,v2-v0))
            node_force = traction*area/3.0
            for nid in tri:
                F[3*nid] += node_force[0]
                F[3*nid+1] += node_force[1]
                F[3*nid+2] += node_force[2]
    return F

def compute_results(basis, U, pts):
    ux,uy,uz = U[0::3],U[1::3],U[2::3]
    disp = np.sqrt(ux**2+uy**2+uz**2)
    max_disp = disp.max()
    u_field = basis.interpolate(U)
    strain = sym_grad(u_field)
    E = 70000.0; nu = 0.3
    lam,mu = lame_parameters(E,nu)
    C = linear_stress(lam,mu)
    stress = C(strain)
    nelem = stress.shape[2]; nqp = stress.shape[3]
    stress_flat = stress.reshape(3,3,nelem*nqp).transpose(2,0,1)
    eig = np.linalg.eigvalsh(stress_flat)
    sigma1 = eig[:,2]; sigma2 = eig[:,1]; sigma3 = eig[:,0]
    vm = np.sqrt(0.5*((sigma1-sigma2)**2+(sigma2-sigma3)**2+(sigma3-sigma1)**2))
    max_vm = vm.max()
    max_principal = sigma1.max()
    max_shear = ((sigma1-sigma3)/2.0).max()
    return max_disp, max_vm, max_shear, max_principal, stress_flat, vm, sigma1, sigma3

def main():
    coarse='mesh_coarse.msh'; refined='mesh.msh'
    if not os.path.isfile(coarse):
        generate_mesh(2.0,coarse)
    if not os.path.isfile(refined):
        generate_mesh(1.0,refined)
    faces_path = os.path.join(os.getenv('CADFEM_INPUT_DIR'),'faces.json')
    with open(faces_path) as f:
        faces = json.load(f)
    f6 = next(f for f in faces['faces'] if f['face_index']==6)
    f38 = next(f for f in faces['faces'] if f['face_index']==38)
    refinement = []
    final = None
    for label,mesh_file,maxsize in [('coarse',coarse,2.0),('refined',refined,1.0)]:
        mesh,meshio_mesh = load_mesh(mesh_file)
        basis = Basis(mesh, ElementVector(ElementTetP1()))
        pts = mesh.p
        fixed_nodes = get_face_nodes(pts, f6['bbox_mm'])
        traction = np.array([0.0,2.0,0.0])
        F = compute_load_vector(meshio_mesh, pts, f38, traction)
        lam,mu = lame_parameters(70000.0,0.3)
        a = linear_elasticity(lam,mu)
        K = asm(a,basis)
        fixed_dofs = basis.nodal_dofs[:,fixed_nodes].flatten('F')
        Kc,Fc,x0,I = condense(K,F,D=fixed_dofs)
        Ufree = solve(Kc,Fc)
        U = x0.copy(); U[I]=Ufree
        max_disp,max_vm,max_shear,max_principal,stress_flat,vm_arr,s1_arr,s3_arr = compute_results(basis,U,pts)
        entry = {'label':label,'max_element_size_mm':maxsize,'node_count':int(mesh.nvertices),'element_count':int(mesh.nelements),
                 'max_displacement_mm':float(max_disp),'max_von_mises_MPa':float(max_vm),
                 'max_shear_stress_MPa':float(max_shear),'max_principal_MPa':float(max_principal)}
        refinement.append(entry)
        if label=='refined':
            final = {'max_displacement_mm':float(max_disp),'max_von_mises_MPa':float(max_vm),
                     'max_shear_stress_MPa':float(max_shear),'max_principal_MPa':float(max_principal)}
            np.savez('fields.npz',coords=pts.T,displacements=U.reshape(-1,3),von_mises=vm_arr,
                     max_shear=np.maximum((s1_arr-s3_arr)/2.0,0.0),principal_max=s1_arr)
    with open('results.json','w') as f:
        json.dump({'outputs':final},f,indent=2)
    with open('refinement.json','w') as f:
        json.dump(refinement,f,indent=2)
    env = {'gmsh_version':gmsh.__version__,'skfem_version':skfem.__version__,'meshio_version':meshio.__version__,'numpy_version':np.__version__,
           'material':{'E_MPa':70000.0,'nu':0.3},'units':'mm length, MPa stress'}
    with open('environment.json','w') as f:
        json.dump(env,f,indent=2)
    with open('solver.log','w') as f:
        f.write('Linear static analysis of CADWorld part\n')
        f.write(f'Generated meshes: {coarse} (2.0 mm), {refined} (1.0 mm)\n')
        f.write('Material: E=70000 MPa, nu=0.3\n')
        f.write('Boundary: fixed face 6, traction 2 MPa on face 38 (+y)\n')
        f.write('Final results (refined mesh):\n')
        for k,v in final.items():
            f.write(f'  {k}: {v}\n')

if __name__=='__main__':
    main()
