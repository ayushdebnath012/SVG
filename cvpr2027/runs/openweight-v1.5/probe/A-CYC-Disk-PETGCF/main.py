import os, shutil, json, time
import gmsh
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

# Paths
input_dir = os.getenv('CADFEM_INPUT_DIR')
# Read FACE data
faces_json = json.load(open(os.path.join(input_dir,'faces.json')))
faces_list = faces_json['faces']
faces_dict = {int(f['face_index']):f for f in faces_list}
# Material properties
E = 3000.0  # MPa
nu = 0.36
lam = E*nu/((1+nu)*(1-2*nu))
mu = E/(2*(1+nu))
# Boundary condition definitions
support_faces = [8,13]
load_faces = [2,19]
# Load forces per face in N
face_forces = {
    2: np.array([0.0,-31.165,94.894]),
    19: np.array([0.0,-31.169,94.905])
}
# Compute traction for each load face
traction_dict = {f: face_forces[f]/faces_dict[f]['area_mm2'] for f in load_faces}

# Helper: solve for a given mesh size
def solve_mesh(mesh_size, mesh_name='mesh.msh', write_mesh=False):
    gmsh.initialize()
    gmsh.open(os.path.join(input_dir,'part.step'))
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber('Mesh.MeshSizeMax', mesh_size)
    gmsh.model.mesh.generate(3)
    if write_mesh:
        gmsh.write(mesh_name)

    # Acquire node and element data
    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
    node_coords = node_coords.reshape((-1,3))
    tag_to_idx = {tag: i for i, tag in enumerate(node_tags)}
    num_nodes = len(node_tags)
    num_dofs = 3*num_nodes

    # Get tetrahedron elements (type 4)
    elem_types, elem_tags_list, elem_node_tags_list = gmsh.model.mesh.getElements(3)
    tet_index = None
    for idx, etype in enumerate(elem_types):
        if int(etype) == 4:
            tet_index = idx
            break
    if tet_index is None:
        raise RuntimeError('No tetrahedral elements found')
    elem_tags = elem_tags_list[tet_index]
    elem_nodes = elem_node_tags_list[tet_index]
    n_el = len(elem_tags)
    nodes_per_el = 4

    # Constitutive matrix D
    D = np.array([
        [lam+2*mu, lam, lam, 0, 0, 0],
        [lam, lam+2*mu, lam, 0, 0, 0],
        [lam, lam, lam+2*mu, 0, 0, 0],
        [0, 0, 0, mu, 0, 0],
        [0, 0, 0, 0, mu, 0],
        [0, 0, 0, 0, 0, mu]
    ], dtype=np.float64)

    # Assembly of stiffness matrix
    rows = []
    cols = []
    data = []
    for e in range(n_el):
        nodes = elem_nodes[e*nodes_per_el:(e+1)*nodes_per_el]
        coords = np.array([node_coords[tag_to_idx[n]] for n in nodes])
        A = np.hstack((np.ones((4,1)), coords))
        invA = np.linalg.inv(A)
        grad = invA[1:4,:]
        B = np.zeros((6,12), dtype=np.float64)
        for i in range(4):
            bi, ci, di = grad[:,i]
            col = i*3
            B[0, col]   = bi
            B[1, col+1] = ci
            B[2, col+2] = di
            B[3, col]   = ci
            B[3, col+1] = bi
            B[4, col+1] = di
            B[4, col+2] = ci
            B[5, col]   = di
            B[5, col+2] = bi
        V = abs(np.linalg.det(A)) / 6.0
        ke = B.T @ D @ B * V
        gdofs = []
        for n in nodes:
            idx = tag_to_idx[n]
            gdofs.extend([idx*3, idx*3+1, idx*3+2])
        for a in range(12):
            for b in range(12):
                rows.append(gdofs[a])
                cols.append(gdofs[b])
                data.append(ke[a,b])
    K = sp.coo_matrix((data, (rows, cols)), shape=(num_dofs, num_dofs)).tocsr()

    # Build load vector
    F = np.zeros(num_dofs)
    for leaf_face in load_faces:
        tr = traction_dict[leaf_face]
        _, _, elem_faces = gmsh.model.mesh.getElements(2, leaf_face)
        if not elem_faces:
            continue
        face_nodes = elem_faces[0]
        faces = face_nodes.reshape(-1,3)
        for tri in faces:
            v0 = node_coords[tag_to_idx[tri[0]]]
            v1 = node_coords[tag_to_idx[tri[1]]]
            v2 = node_coords[tag_to_idx[tri[2]]]
            area = 0.5*np.linalg.norm(np.cross(v1-v0, v2-v0))
            f_local = tr*area/3.0
            for k in range(3):
                idx = tag_to_idx[tri[k]]
                F[idx*3 : idx*3+3] += f_local

    # Dirichlet BC: support faces
    fixed_dofs = []
    for sup_face in support_faces:
        _, _, sup_face_nodes = gmsh.model.mesh.getElements(2, sup_face)
        if not sup_face_nodes:
            continue
        nodes_face = sup_face_nodes[0]
        face_tri = nodes_face.reshape(-1,3)
        node_set = set()
        for tri in face_tri:
            node_set.update(tri)
        for n in node_set:
            idx = tag_to_idx[n]
            fixed_dofs.extend([idx*3, idx*3+1, idx*3+2])
    fixed = np.array(fixed_dofs, dtype=int)
    free = np.setdiff1d(np.arange(num_dofs), fixed)

    # Solve linear system
    Kff = K[free,:][:,free]
    Ff = F[free]
    uf = spla.spsolve(Kff, Ff)
    u = np.zeros(num_dofs)
    u[free] = uf

    disp = u.reshape((-1,3))
    max_disp = float(np.max(np.linalg.norm(disp, axis=1)))
    gmsh.finalize()

    return max_disp, n_el, num_nodes, disp, node_tags, node_coords

# -- Main execution -----------------------------------------------------
# Copy part.step to current working directory
shutil.copy(os.path.join(input_dir,'part.step'),'part.step')

# Write mesh files for 1.25 mm and 1.0 mm (intermediate for extrapolation)
# Solve for 1.25 mm (coarser) – write mesh
max_disp_coarse, n_el_coarse, n_nodes_coarse, disp_coarse, node_tags_coarse, coords_coarse = solve_mesh(1.25, mesh_name='mesh_coarse.msh', write_mesh=True)
# Solve for 1.0 mm (finer) – final mesh written as mesh.msh
max_disp_fine, n_el_fine, n_nodes_fine, disp_fine, node_tags_fine, coords_fine = solve_mesh(1.0, mesh_name='mesh.msh', write_mesh=True)

# Extrapolate using Richardson order 2
h_coarse = 1.25
h_fine   = 1.0
p = 2
max_disp_extrapolated = (max_disp_coarse*h_fine**p - max_disp_fine*h_coarse**p)/(h_fine**p - h_coarse**p)

# Save results.json
results = {
    "outputs": {
        "max_displacement_mm": max_disp_extrapolated
    }
}
with open('results.json','w') as f:
    json.dump(results, f, indent=2)

# Save fields.npz (using finest mesh displacement)
np.savez('fields.npz', node_ids=node_tags_fine, coordinates=coords_fine, displacements=disp_fine)

# Save refinement.json
refinement = {
    "mesh_size_mm": [1.25, 1.0],
    "elements": [n_el_coarse, n_el_fine],
    "nodes": [n_nodes_coarse, n_nodes_fine]
}
with open('refinement.json','w') as f:
    json.dump(refinement, f, indent=2)

# Generate solver.log
log_lines = []
log_lines.append('Solver log:')
log_lines.append(f'  GMsh version: {gmsh.__version__}')
log_lines.append(f'  Mesh size (coarse): {h_coarse} mm, elements {n_el_coarse}, nodes {n_nodes_coarse}, max displacement {max_disp_coarse:.6f} mm')
log_lines.append(f'  Mesh size (fine): {h_fine} mm, elements {n_el_fine}, nodes {n_nodes_fine}, max displacement {max_disp_fine:.6f} mm')
log_lines.append(f'  Extrapolated max displacement (order {p}): {max_disp_extrapolated:.6f} mm')
log_lines.append(f'  Used SciPy solver: spsolve, version {spla.__version__ if hasattr(spla, "__version__") else "unknown"}')
with open('solver.log','w') as f:
    f.write("\n".join(log_lines))

# Save environment.json
import scipy
env = {
    "solver": "scipy.sparse.linalg.spsolve",
    "solver_version": scipy.__version__,
    "gmsh_version": gmsh.__version__ if hasattr(gmsh, "__version__") else "unknown",
    "numpy_version": np.__version__,
    "units": {"length": "mm", "force": "N", "stress": "MPa"},
    "material": {"E": E, "nu": nu, "type": "PETG-CF"},
    "analysis_type": "linear_static",
    "mesh_size_mm": 1.0,
    "element_order": "linear_tetra",
    "boundary_conditions": {"supports": support_faces, "loads": {str(f): traction_dict[f].tolist() for f in load_faces}},
    "fields_extracted": ["displacements"]
}
with open('environment.json','w') as f:
    json.dump(env, f, indent=2)

print('All outputs generated.')
