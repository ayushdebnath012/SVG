#!/usr/bin/env python3
"""
This script performs a linear elastic finite element analysis of the PETG-CF
motor mount geometry supplied in part.step. The analysis uses Gmsh to
generate a tetrahedral mesh, assemble the global stiffness matrix and
solution vector using SciPy. The mesh is generated for a user supplied
characteristic element size. The final solution is produced on the fine
mesh (maximum element size 2 mm). Two mesh resolutions are used for the
refinement.json artifact.

The script produces the following files in the current working directory:
* part.step
* mesh.msh
* fields.npz
* results.json
* solver.log
* refinement.json
* environment.json

All units are in millimetres, forces in Newtons, stresses in MPa.
The linear elastic material has E = 3000 MPa and ν = 0.36.
"""

import os
import json
import numpy as np
import meshio
import gmsh
import shutil
import math
import scipy.sparse as sps
import scipy.sparse.linalg as spla

# -------------------- Settings --------------------
# Material properties (MPa, dimensionless)
E = 3000.0  # MPa
nu = 0.36

# Load and support face indices as provided in faces.json
SUPPORT_FACES = [22, 24]
LOAD_FACE = 12

# Traction total force on load face (N)
TOTAL_TTRACTION_FORCE = np.array([-50.064, 0.0, 0.0])  # -50.064 N in -x direction

# Mesh resolutions to record (units: mm)
MESH_SIZES = {
    'coarse': 4.0,  # coarse: max element size 4 mm
    'fine': 2.0,    # fine: max element size 2 mm (reference solution)
}

# -------------------- Helper Functions --------------------

def read_json_from_input(filename: str):
    """Read a JSON file from the CADFEM_INPUT_DIR directory."""
    input_dir = os.environ['CADFEM_INPUT_DIR']
    path = os.path.join(input_dir, filename)
    with open(path, 'r') as f:
        return json.load(f)


def copy_input_file(filename: str, output_name: str):
    """Copy a file from the input directory to the current directory."""
    input_dir = os.environ['CADFEM_INPUT_DIR']
    src = os.path.join(input_dir, filename)
    shutil.copyfile(src, output_name)


def generate_mesh(step_file: str, mesh_file: str, max_elem_size: float):
    """Generate a Gmsh tetrahedral mesh for the given STEP file.

    Parameters
    ----------
    step_file : str
        Path to the input STEP file.
    mesh_file : str
        Path where the generated Gmsh mesh (*.msh) will be written.
    max_elem_size : float
        Desired maximum element size in mm.

    Returns
    -------
    None
    """
    gmsh.initialize()  # start Gmsh API
    gmsh.option.setNumber('General.Verbosity', 0)
    gmsh.option.setNumber('Mesh.MeshSizeMax', max_elem_size)
    gmsh.open(step_file)
    # Create a size field that enforces the target size (approximate max)
    field = gmsh.model.mesh.field.add("MathEval", 1)
    gmsh.model.mesh.field.setString(field, "F", str(max_elem_size))
    gmsh.model.mesh.field.setAsBackgroundMesh(field)
    gmsh.model.mesh.generate(3)
    gmsh.write(mesh_file)
    gmsh.finalize()


def load_mesh(mesh_file: str):
    """Load a Gmsh mesh using meshio.

    Returns
    -------
    points : np.ndarray
        Node coordinates (N, 3).
    tetra : np.ndarray
        Tetrahedron elements (n_elem, 4).
    triangles : np.ndarray
        Triangle entities representing the mesh surface (m, 3).
    """
    mesh = meshio.read(mesh_file)
    points = mesh.points
    # Gmsh MSH publish: cells are given as a list of tuples (type, data)
    # We can use cells_dict
    tetra = mesh.cells_dict.get('tetra')
    triangles = mesh.cells_dict.get('triangle')
    return points, tetra, triangles


def identify_faces(points, triangles, faces_json):
    """Identify triangles belonging to faces 22, 24 and 12.

    Parameters
    ----------
    points : np.ndarray
        Node coordinates.
    triangles : np.ndarray
        Triangle element indices.
    faces_json : dict
        Parsed faces.json content.

    Returns
    -------
    support_nodes : set of int
        Set of node indices on support faces.
    load_tri_info : list of tuples
        Each tuple contains (triangle nodes (3,), area of triangle)
    """
    # Prepare face data from the JSON
    face_data = {}
    for face in faces_json['faces']:
        idx = face['face_index']
        face_data[idx] = face

    # Helper: compute centroid and normal for a triangle
    def tri_centroid_and_normal(tri_idx):
        n0, n1, n2 = triangles[tri_idx]
        v0 = points[n0]
        v1 = points[n1]
        v2 = points[n2]
        centroid = (v0 + v1 + v2) / 3.0
        v1_v0 = v1 - v0
        v2_v0 = v2 - v0
        normal = np.cross(v1_v0, v2_v0)
        norm_len = np.linalg.norm(normal)
        if norm_len < 1e-12:
            unit = np.array([0.0, 0.0, 0.0])
        else:
            unit = normal / norm_len
        area = 0.5 * norm_len
        return centroid, unit, area

    support_nodes = set()
    load_tri_info = []

    # Extract outward normals and centroids for target faces
    target_centroids = {
        22: np.array(face_data[22]['centroid_mm']),
        24: np.array(face_data[24]['centroid_mm']),
        12: np.array(face_data[12]['centroid_mm']),
    }
    target_normals = {
        22: np.array(face_data[22]['outward_normal']),
        24: np.array(face_data[24]['outward_normal']),
        12: np.array(face_data[12]['outward_normal']),
    }
    # Convert to numpy arrays and normalize
    for k in target_normals:
        n = target_normals[k]
        norm = np.linalg.norm(n)
        if norm > 0:
            target_normals[k] = n / norm
        else:
            target_normals[k] = n

    # Bounding boxes from faces.json (min and max)
    bboxes = {}
    for k in [22, 24, 12]:
        bb = face_data[k]['bbox_mm']
        bboxes[k] = {
            'xmin': bb[0], 'ymin': bb[1], 'zmin': bb[2],
            'xmax': bb[3], 'ymax': bb[4], 'zmax': bb[5]
        }

    # Tolerances for classification (mm)
    tol_centroid = 1.5  # tolerance for centroid location
    tol_normal = 0.99   # cos(theta) tolerance between normals

    n_tri = triangles.shape[0]
    for tri_idx in range(n_tri):
        centroid, unit_norm, area = tri_centroid_and_normal(tri_idx)
        # Check for loading face (face 12)
        c12 = target_centroids[12]
        n12 = target_normals[12]
        bb12 = bboxes[12]
        if (
            abs(centroid[0] - c12[0]) < tol_centroid and
            np.dot(unit_norm, n12) > tol_normal
        ):
            # Detected load face triangle
            n0, n1, n2 = triangles[tri_idx]
            load_tri_info.append(((n0, n1, n2), area))
            continue
        # For support faces, check both 22 and 24
        support_matched = False
        for sf in SUPPORT_FACES:
            csf = target_centroids[sf]
            nsf = target_normals[sf]
            bbsf = bboxes[sf]
            if (
                abs(centroid[0] - csf[0]) < tol_centroid and
                abs(centroid[1] - csf[1]) < tol_centroid and
                abs(centroid[2] - csf[2]) < tol_centroid and
                np.dot(unit_norm, nsf) > tol_normal and
                bbsf['xmin'] - tol_centroid <= centroid[0] <= bbsf['xmax'] + tol_centroid and
                bbsf['ymin'] - tol_centroid <= centroid[1] <= bbsf['ymax'] + tol_centroid and
                bbsf['zmin'] - tol_centroid <= centroid[2] <= bbsf['zmax'] + tol_centroid
            ):
                # Add nodes to support
                n0, n1, n2 = triangles[tri_idx]
                support_nodes.update([n0, n1, n2])
                support_matched = True
                break
        # If not matched anything, ignore
    return support_nodes, load_tri_info


def assemble_and_solve(points, tetra, support_nodes, load_tri_info, traction_per_area):
    """Assemble the global stiffness matrix and solve for displacement.

    Parameters
    ----------
    points : np.ndarray
        Node coordinates (N,3).
    tetra : np.ndarray
        Tetrahedron element indices (n_elem,4).
    support_nodes : set of int
        Node indices on support faces.
    load_tri_info : list of tuples
        Each tuple is (node_tuple, triangle_area).
    traction_per_area : np.ndarray
        Traction vector (N/mm^2) applied to load face.

    Returns
    -------
    u : np.ndarray
        Solution displacement vector, shape (N,3).
    stats : dict
        Dictionary containing number of nodes/elements.
    """
    N_nodes = points.shape[0]
    N_dofs = 3 * N_nodes

    # Material constants
    lam = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    mu = E / (2.0 * (1.0 + nu))
    D = np.zeros((6,6))
    D[0,0] = D[1,1] = D[2,2] = lam + 2.0 * mu
    D[0,1] = D[0,2] = D[1,0] = D[1,2] = D[2,0] = D[2,1] = lam
    D[3,3] = D[4,4] = D[5,5] = mu

    K = sps.lil_matrix((N_dofs, N_dofs), dtype=np.float64)
    f = np.zeros(N_dofs, dtype=np.float64)

    # Load vector from traction on load triangles
    traction = traction_per_area

    # Assemble global stiffness
    n_elem = tetra.shape[0]
    for el in range(n_elem):
        nodes = tetra[el]
        coords = points[nodes]
        # Build matrix for barycentric coordinates
        A_mat = np.column_stack((np.ones(4), coords))
        invA = np.linalg.inv(A_mat)
        grad = invA[1:, :]
        b = grad[0]
        c = grad[1]
        d = grad[2]
        B = np.zeros((6, 12), dtype=np.float64)
        B[0,0::3] = b
        B[1,1::3] = c
        B[2,2::3] = d
        B[3,0::3] = c
        B[3,1::3] = b
        B[4,1::3] = d
        B[4,2::3] = c
        B[5,0::3] = d
        B[5,2::3] = b
        # Volume of tetrahedron
        v = abs(np.dot(np.cross(coords[1] - coords[0], coords[2] - coords[0]), coords[3] - coords[0])) / 6.0
        Ke = v * (B.T @ D @ B)
        # Global DOFs
        dofs = np.empty(12, dtype=int)
        for k, nid in enumerate(nodes):
            dofs[3*k] = 3*nid
            dofs[3*k+1] = 3*nid + 1
            dofs[3*k+2] = 3*nid + 2
        # Add to K
        for ii in range(12):
            ii_dof = dofs[ii]
            for jj in range(12):
                jj_dof = dofs[jj]
                K[ii_dof, jj_dof] += Ke[ii, jj]

    # Apply traction loads on load triangles
    for tri_nodes, area in load_tri_info:
        for node_idx in tri_nodes:
            f[3*node_idx] += traction[0] * area / 3.0
            f[3*node_idx + 1] += traction[1] * area / 3.0
            f[3*node_idx + 2] += traction[2] * area / 3.0

    # Apply Dirichlet constraints on support nodes (U=0)
    fixed_dofs = []
    for nid in support_nodes:
        fixed_dofs.extend([3*nid, 3*nid+1, 3*nid+2])
    fixed_dofs = np.array(sorted(set(fixed_dofs)), dtype=int)
    for dof in fixed_dofs:
        K[dof, :] = 0.0
        K[:, dof] = 0.0
        K[dof, dof] = 1.0
        f[dof] = 0.0

    # Solve linear system
    K_csr = K.tocsr()
    u_vec = spla.spsolve(K_csr, f)
    u = u_vec.reshape((N_nodes, 3))
    return u, {'nodes': N_nodes, 'elements': n_elem}


# ------------ Main Execution --------------
if __name__ == '__main__':
    # Copy geometry to current directory
    copy_input_file('part.step', 'part.step')
    # Read faces.json for geometry information
    faces_json = read_json_from_input('faces.json')
    # Get material properties and define traction
    face_area_load = faces_json['faces'][11]['area_mm2']  # face_index 12 (zero-based 11 in list)
    traction_per_area = TOTAL_TTRACTION_FORCE / face_area_load

    # Store results for multiple resolutions
    refinement_results = []
    max_disp_fine = None
    displacement_fine = None
    points_fine = None

    for key, elem_size in MESH_SIZES.items():
        mesh_file = f'mesh_{key}.msh'
        # Generate mesh
        print(f'Generating {key} mesh with max element size {elem_size} mm...')
        generate_mesh(os.path.join(os.environ['CADFEM_INPUT_DIR'], 'part.step'), mesh_file, elem_size)
        # Load mesh
        points, tetra, triangles = load_mesh(mesh_file)
        # Identify support nodes and load triangles
        support_nodes, load_tri_info = identify_faces(points, triangles, faces_json)
        # Debug: number of identified nodes and triangles
        print(f"Support nodes count: {len(support_nodes)}")
        print(f"Load triangles count: {len(load_tri_info)}")
        # Assemble and solve
        u, stats = assemble_and_solve(points, tetra, support_nodes, load_tri_info, traction_per_area)
        # Compute max displacement
        disp_mags = np.linalg.norm(u, axis=1)
        max_disp = float(np.max(disp_mags))
        size_info = {
            'mesh_name': key,
            'max_element_size_mm': elem_size,
            'num_nodes': stats['nodes'],
            'num_elements': stats['elements'],
            'max_displacement_mm': max_disp
        }
        refinement_results.append(size_info)
        if key == 'fine':
            max_disp_fine = max_disp
            displacement_fine = u
            points_fine = points

    # Write results.json
    with open('results.json', 'w') as f:
        json.dump({'outputs': {'max_displacement_mm': max_disp_fine}}, f)

    # Write fields.npz
    np.savez('fields.npz', node_ids=np.arange(points_fine.shape[0]), coords=points_fine, displacements=displacement_fine)

    # Write mesh.msh as the fine mesh for reference in artifacts
    shutil.move('mesh_fine.msh', 'mesh.msh')

    # Write solver.log
    with open('solver.log', 'w') as f:
        f.write('Linear elastic FEM solution using Gmsh mesh generator (max elem size 2 mm).\n')
        f.write(f'Generated mesh with {refinement_results[1]["num_elements"]} tetra elements and {refinement_results[1]["num_nodes"]} nodes.\n')
        f.write(f'Max displacement: {max_disp_fine:.6f} mm.\n')

    # Write refinement.json
    with open('refinement.json', 'w') as f:
        json.dump({'refinements': refinement_results}, f)

    # Write environment.json
    env = {
        'solver': 'SciPy.sparse.linalg.spsolve',
        'mesher': 'Gmsh 4.15 (Python API)',
        'materials': {'E_MPa': E, 'nu': nu},
        'input_directory': os.environ['CADFEM_INPUT_DIR'],
        'output_directory': os.environ['CADFEM_OUTPUT_DIR'],
        'unit_system': 'mm',
        'traction_per_area_N_per_mm2': traction_per_area.tolist(),
        'boundary_face_definitions': {
            'support_faces': SUPPORT_FACES,
            'load_face': LOAD_FACE
        }
    }
    with open('environment.json', 'w') as f:
        json.dump(env, f, indent=2)

    print('All artifacts written successfully.')
