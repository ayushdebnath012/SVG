import json
import os
import sys
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as sla
import gmsh
import meshio

# --------------------------------------------------------------
# Configuration and constants
# --------------------------------------------------------------
# Material properties (Pa)
E_pa = 3000e6  # 3000 MPa
nu = 0.36
lam = E_pa * nu / ((1 + nu) * (1 - 2 * nu))
mu = E_pa / (2 * (1 + nu))
# Cylinder support axis (from problem description)
axis_point = np.array([113.025, 0.0, 20.5])
axis_dir = np.array([1.0, 0.0, 0.0])  # along +x
axis_radius_mm = 30.0
# Loaded face indices and traction vectors (N)
loaded_face_indices = [1, 2, 3, 4, 5, 6]
loaded_face_trac = {
    1: np.array([0.0, -11.516, -27.638]),
    2: np.array([0.0, -11.515, -27.637]),
    3: np.array([0.0, -11.518, -27.643]),
    4: np.array([0.0, -11.516, -27.638]),
    5: np.array([0.0, -11.511, -27.626]),
    6: np.array([0.0, -11.511, -27.626]),
}
# Support face indices
support_faces_indices = [17, 23]
# Tolerances
face_assign_tol_mm = 3.0
cyl_tol_mm = 0.5
# Mesh generation parameters
mesh_sizes_mm = [2.0, 4.0]  # fine and coarse
# --------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------

def read_faces_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data['faces']


def copy_part_step(input_path, output_path):
    import shutil
    shutil.copyfile(input_path, output_path)


def generate_mesh(step_path, mesh_path, size_mm):
    gmsh.initialize()
    gmsh.open(step_path)
    gmsh.option.setNumber('Mesh.MeshSizeMax', size_mm)
    gmsh.option.setNumber('Mesh.MeshSizeMin', size_mm)
    gmsh.model.mesh.generate(3)
    gmsh.write(mesh_path)
    gmsh.finalize()


def load_mesh_data(mesh_path):
    m = meshio.read(mesh_path)
    points = m.points  # mm
    tetra_cells = m.cells_dict['tetra']  # shape (ne,4) 0-based
    triangle_cells = m.cells_dict['triangle']  # shape (ntri,3)
    # geometry tags per triangle for each face
    geom_data = m.cell_data['gmsh:geometrical']
    geom_tags = np.array([int(arr[0]) for arr in geom_data])
    return points, tetra_cells, triangle_cells, geom_tags


def find_support_nodes(points_mm):
    radial = np.sqrt((points_mm[:, 1]) ** 2 + (points_mm[:, 2] - axis_point[2])**2)
    mask = np.abs(radial - axis_radius_mm) <= cyl_tol_mm
    node_ids = np.nonzero(mask)[0]
    return node_ids


def map_triangles_to_faces(tri_centroids, face_centroids, tol_mm):
    mapping = {face: [] for face in face_centroids}
    for i, cent in enumerate(tri_centroids):
        dists = {face: np.linalg.norm(cent - c) for face, c in face_centroids.items()}
        min_face = min(dists, key=dists.get)
        if dists[min_face] <= tol_mm:
            mapping[min_face].append(i)
    return mapping


def assemble_system(points_mm, tetra_cells, tri_cells, tri_centroids, geom_tags, face_maxareas, face_loads, support_node_ids, mapping):
    pts_m = points_mm * 1e-3
    ne = tetra_cells.shape[0]
    nn = points_mm.shape[0]
    ndofs = nn * 3
    K = sp.lil_matrix((ndofs, ndofs), dtype=np.float64)
    f = np.zeros(ndofs, dtype=np.float64)
    D = np.zeros((6, 6), dtype=np.float64)
    D[0, 0] = D[1, 1] = D[2, 2] = lam + 2 * mu
    D[0, 1] = D[0, 2] = D[1, 0] = D[1, 2] = D[2, 0] = D[2, 1] = lam
    D[3, 3] = D[4, 4] = D[5, 5] = mu
    for face_index, load_vec in face_loads.items():
        area_f_mm2 = face_maxareas.get(face_index, None)
        if area_f_mm2 is None:
            continue
        area_f_m2 = area_f_mm2 * 1e-6
        tri_indices = [tri for tri in mapping.get(face_index, [])]
        for tri in tri_indices:
            nodes = tri_cells[tri]
            area_t_mm2 = 0.5 * np.linalg.norm(np.cross(points_mm[nodes[1], :] - points_mm[nodes[0], :], points_mm[nodes[2], :] - points_mm[nodes[0], :]))
            frac = area_t_mm2 / area_f_mm2
            contrib = load_vec * (frac / 3.0)
            for n in nodes:
                f[3*n + 0] += contrib[0]
                f[3*n + 1] += contrib[1]
                f[3*n + 2] += contrib[2]
    for e in range(ne):
        nodes = tetra_cells[e]
        P = pts_m[nodes]  # shape (4,3)
        M = np.vstack((np.ones((1, 4)), P.T)).T
        invM = np.linalg.inv(M)
        G = invM[1:, :]
        B = np.zeros((6, 12), dtype=np.float64)
        for i in range(4):
            g = G[:, i]
            j = 3 * i
            B[0, j] = g[0]
            B[1, j + 1] = g[1]
            B[2, j + 2] = g[2]
            B[3, j] = 0.5 * g[1]
            B[3, j + 1] = 0.5 * g[0]
            B[4, j + 1] = 0.5 * g[2]
            B[4, j + 2] = 0.5 * g[1]
            B[5, j] = 0.5 * g[2]
            B[5, j + 2] = 0.5 * g[0]
        vol = abs(np.linalg.det(M)) / 6.0
        Ke = B.T @ D @ B * vol
        dofs_global = np.array([3*n + c for n in nodes for c in range(3)], dtype=int)
        for i in range(4):
            row_global = dofs_global[3 * i:3 * i + 3]
            for j in range(4):
                col_global = dofs_global[3 * j:3 * j + 3]
                sub = Ke[3 * i:3 * i + 3, 3 * j:3 * j + 3]
                for ii, gd_i in enumerate(row_global):
                    for jj, gd_j in enumerate(col_global):
                        K[gd_i, gd_j] += sub[ii, jj]
    for n in support_node_ids:
        dof_start = 3 * n
        dof_idx = [dof_start, dof_start + 1, dof_start + 2]
        for d in dof_idx:
            K[d, :] = 0
            K[:, d] = 0
            K[d, d] = 1
            f[d] = 0
    return K.tocsr(), f


def solve_system(K, f):
    u = sla.spsolve(K, f)
    return u


def compute_max_disp(u, node_ids=None):
    if node_ids is None:
        nn = u.size // 3
        node_ids = np.arange(nn)
    disp = u.reshape((-1, 3))
    mag = np.linalg.norm(disp, axis=1)
    return np.max(mag) * 1000.0

# --------------------------------------------------------------
# Main workflow
# --------------------------------------------------------------

if __name__ == '__main__':
    inp_dir = os.environ.get('CADFEM_INPUT_DIR', '')
    part_path = os.path.join(inp_dir, 'part.step')
    faces_path = os.path.join(inp_dir, 'faces.json')
    copy_part_step(part_path, 'part.step')
    faces_data = read_faces_json(faces_path)
    face_centroids = {}
    face_area_mm2 = {}
    for fd in faces_data:
        idx = fd['face_index']
        if idx in loaded_face_indices or idx in support_faces_indices:
            face_centroids[idx] = np.array(fd['centroid_mm'])
            face_area_mm2[idx] = fd['area_mm2']
    results = {}
    refinement_list = []
    global mesh_outname
    for size_mm in mesh_sizes_mm:
        mesh_name = f'mesh_{int(size_mm)}.msh'
        generate_mesh(part_path, mesh_name, size_mm)
        points_mm, tetra_cells, tri_cells, geom_tags = load_mesh_data(mesh_name)
        tri_centroids = np.mean(points_mm[tri_cells], axis=1)
        # Determine mapping of triangles to loaded faces using geometry tags
        mapping = {}
        for fid in face_centroids:
            mapping[fid] = [i for i, tag in enumerate(geom_tags) if tag == fid]
        # Compute real area for each loaded face from the mesh triangles
        actual_face_areas_mm2 = {}
        for fid, tris in mapping.items():
            area = 0.0
            for tri in tris:
                nodes = tri_cells[tri]
                area += 0.5 * np.linalg.norm(np.cross(points_mm[nodes[1]] - points_mm[nodes[0]], points_mm[nodes[2]] - points_mm[nodes[0]]))
            actual_face_areas_mm2[fid] = area
        support_nodes = find_support_nodes(points_mm)
        K, f = assemble_system(points_mm, tetra_cells, tri_cells, tri_centroids, geom_tags, actual_face_areas_mm2, loaded_face_trac, support_nodes, mapping)
        u = solve_system(K, f)
        max_disp_mm = compute_max_disp(u)
        if size_mm == mesh_sizes_mm[0]:
            results['max_displacement_mm'] = max_disp_mm
            disp_m = u.reshape((-1, 3)) * 1000.0
            node_ids = np.arange(points_mm.shape[0], dtype=np.int32)
            np.savez('fields.npz', node_ids=node_ids, coordinates=points_mm, displacements=disp_m, displacements_magnitude=np.linalg.norm(disp_m, axis=1))
            with open('solver.log', 'w') as logf:
                logf.write(f'GMsh mesh generated with size {size_mm} mm\n')
                logf.write(f'Number of tetrahedra: {tetra_cells.shape[0]}\n')
                logf.write(f'Number of nodes: {points_mm.shape[0]}\n')
                logf.write(f'Degrees of freedom: {K.shape[0]}\n')
                logf.write(f'Solved linear system, maximum displacement: {max_disp_mm:.6f} mm\n')
        refinement_list.append({'mesh_size_mm': size_mm, 'num_elements': tetra_cells.shape[0], 'max_displacement_mm': max_disp_mm})
        if size_mm == mesh_sizes_mm[0]:
            os.rename(mesh_name, 'mesh.msh')
    with open('results.json', 'w') as fjson:
        json.dump({'outputs': results}, fjson)
    with open('refinement.json', 'w') as fref:
        json.dump({'refinement': refinement_list}, fref)
    env = {
        'python_version': sys.version,
        'gmsh_version': gmsh.__version__ if hasattr(gmsh, '__version__') else 'unknown',
        'skfem_version': __import__('skfem').__version__,
        'numpy_version': np.__version__,
        'scipy_version': __import__('scipy').__version__,
        'meshio_version': __import__('meshio').__version__,
        'units': 'mm for input geometry, meters for computation, outputs in mm',
        'solver': 'scipy sparse direct solve (spsolve)',
    }
    with open('environment.json', 'w') as fenv:
        json.dump(env, fenv)
