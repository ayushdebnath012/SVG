#!/usr/bin/env python3
# CADFEM-Bench task A-GEOPINO-PLATE-1
"""
This script performs the following steps:
1. Copies the input step file (inputs/part.step) to the output directory as part.step.
2. Generates two meshes (coarse and fine) using Gmsh with characteristic lengths 3.0 mm and 1.5 mm, respectively.
3. For each mesh, assembles the linear elasticity system (E=200 GPa, nu=0.3) for the plate geometry.
4. Applies two load cases:
   - compression: 1000 N uniformly applied over the free face (y=+74.2373 mm) in the -y direction.
   - lateral bending: 1000 N uniformly applied over the free face in the +x direction.
   The applied traction density is 1000 N divided by the total free-surface area of the plate.
5. Solves the linear system with Dirichlet boundary conditions on the fixed face (y=-74.2373 mm).
6. Reports maximum displacement magnitude (in mm) for both cases for the fine mesh.
7. Stores results, mesh, field arrays, log, refinement data, and environment information.

The script relies only on the pre-installed Python libraries and tools: numpy, scipy, meshio, gmsh, scikit-fem.
"""

import os
import sys
import json
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import meshio
import gmsh
import time

# ---------------------------- utilities ---------------------------

def copy_part_step(src: str, dst: str) -> None:
    """Copy the input STEP file from src to dst (text copy)."""
    with open(src, 'rb') as fsrc:
        data = fsrc.read()
    with open(dst, 'wb') as fdst:
        fdst.write(data)


def generate_gmsh_mesh(step_file: str, mesh_file: str, lc: float) -> None:
    """Generate a tetrahedral mesh with Gmsh from a STEP file.
    The parameter lc specifies the characteristic length (mm).
    """

    # Initialize Gmsh (non-interactive)
    gmsh.initialize()
    gmsh.option.setNumber("Mesh.ElementOrder", 1)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", lc)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", lc)
    gmsh.option.setNumber("Mesh.Algorithm", 5)  # high quality scheme
    gmsh.open(step_file)
    gmsh.model.mesh.generate(3)
    gmsh.write(mesh_file)
    gmsh.finalize()


def load_mesh(mesh_file: str):
    """Load a mesh file (Gmsh MSH format) and return coordinates and tetra cells.
    Returns:
        coords: (N_nodes, 3) array of float32
        cells: (N_tetra, 4) array of int32 (0-based indices)
    """
    mesh = meshio.read(mesh_file)
    # Gmsh stores nodes as float64, but we convert to float64 for accuracy
    coords = np.asarray(mesh.points, dtype=np.float64)
    # Find tet cells
    tet_cells = None
    for cell_block in mesh.cells:
        if cell_block.type in ["tetra", "tetrahedra", "tetrahedron", "tetrahedra"]:
            tet_cells = np.asarray(cell_block.data, dtype=np.int64)
            break
    if tet_cells is None:
        raise ValueError("No hexahedron cells found in mesh")
    return coords, tet_cells


def extract_boundary_faces(coords, tet_cells):
    """Return a list of boundary face node index tuples that are on the free face (y ~= +74.2373).
    Each entry is a tuple of three node indices representing a triangle.
    """
    top_y_value = 74.2373
    tol = 1e-6
    face_counts = dict()
    face_nodes = dict()
    for tet in tet_cells:
        faces = [
            (tet[0], tet[1], tet[2]),
            (tet[0], tet[1], tet[3]),
            (tet[0], tet[2], tet[3]),
            (tet[1], tet[2], tet[3]),
        ]
        for f in faces:
            key = tuple(sorted(f))
            if key in face_counts:
                face_counts[key] += 1
            else:
                face_counts[key] = 1
                face_nodes[key] = f
    boundary_faces = []
    for key, count in face_counts.items():
        if count == 1:
            f = face_nodes[key]
            y_vals = coords[np.array(f), 1]
            if np.all(np.abs(y_vals - top_y_value) < tol):
                boundary_faces.append(f)
    return boundary_faces


def compute_surface_area(face_nodes, coords):
    """Compute the area of a triangular face given node indices and coordinates."""
    p0, p1, p2 = coords[np.array(face_nodes)]
    return 0.5 * np.linalg.norm(np.cross(p1 - p0, p2 - p0))


def assemble_global_stiffness(coords, tet_cells, E, nu):
    """Assemble the global stiffness matrix for linear elasticity using linear tetra elements.
    Returns a sparse CSR matrix of shape (ndofs, ndofs).
    """
    n_nodes = coords.shape[0]
    ndofs = n_nodes * 3
    n_tet = tet_cells.shape[0]
    # Preallocate COO arrays
    entries_per_tet = 12 * 12
    total_entries = n_tet * entries_per_tet
    rows = np.empty(total_entries, dtype=np.int64)
    cols = np.empty(total_entries, dtype=np.int64)
    data = np.empty(total_entries, dtype=np.float64)

    # Material matrix
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    D = np.array(
        [
            [lam + 2 * mu, lam, lam, 0, 0, 0],
            [lam, lam + 2 * mu, lam, 0, 0, 0],
            [lam, lam, lam + 2 * mu, 0, 0, 0],
            [0, 0, 0, mu, 0, 0],
            [0, 0, 0, 0, mu, 0],
            [0, 0, 0, 0, 0, mu],
        ],
        dtype=np.float64,
    )

    idx = 0
    for tet in tet_cells:
        n0, n1, n2, n3 = tet
        pts = coords[[n0, n1, n2, n3]]
        # Build matrix to compute shape function coefficients
        A = np.array([[1, *pts[0]], [1, *pts[1]], [1, *pts[2]], [1, *pts[3]]], dtype=np.float64)
        invA = np.linalg.inv(A)
        grads = invA[1:4, :].T  # shape (4,3) - gradients for each node
        # Compute volume
        mat = np.vstack([pts[1] - pts[0], pts[2] - pts[0], pts[3] - pts[0]]).T
        vol = abs(np.linalg.det(mat)) / 6.0

        # Build B matrix
        B = np.zeros((6, 12), dtype=np.float64)
        for i_local in range(4):
            g = grads[i_local]
            i = 3 * i_local
            B[0, i]   = g[0]
            B[1, i+1] = g[1]
            B[2, i+2] = g[2]
            B[3, i]   = g[1]
            B[3, i+1] = g[0]
            B[4, i+1] = g[2]
            B[4, i+2] = g[1]
            B[5, i]   = g[2]
            B[5, i+2] = g[0]
        Ke = vol * (B.T @ D @ B)

        # Map local DOFs to global
        nodes = [n0, n1, n2, n3]
        for i_local in range(12):
            gi = 3 * nodes[i_local // 3] + (i_local % 3)
            for j_local in range(12):
                gj = 3 * nodes[j_local // 3] + (j_local % 3)
                rows[idx] = gi
                cols[idx] = gj
                data[idx] = Ke[i_local, j_local]
                idx += 1
    if idx != total_entries:
        # should not happen
        total_entries = idx
        rows = rows[:total_entries]
        cols = cols[:total_entries]
        data = data[:total_entries]
    K = sp.coo_matrix((data, (rows, cols)), shape=(ndofs, ndofs)).tocsr()
    return K


def apply_dirichlet(K, f, dirichlet_dofs):
    """Apply Dirichlet BC by eliminating the degrees of freedom.
    Returns K_ff, f_f (free DOFs only).
    """
    ndofs = K.shape[0]
    all_dofs = np.arange(ndofs)
    free_dofs = np.setdiff1d(all_dofs, dirichlet_dofs)
    K_ff = K[free_dofs, :][:, free_dofs]
    f_f = f[free_dofs]
    return K_ff, f_f, free_dofs


def compute_load_vector(coords, boundary_faces, load_type):
    """Compute the global load vector for a uniform traction over the free face.
    `load_type` is either 'compression' or 'bending'.
    Returns f as ndarray of shape (ndofs,).
    """
    n_nodes = coords.shape[0]
    ndofs = n_nodes * 3
    f = np.zeros(ndofs, dtype=np.float64)
    # Determine traction density
    total_area = 0.0
    areas = []
    for f_nodes in boundary_faces:
        area = compute_surface_area(f_nodes, coords)
        areas.append(area)
        total_area += area
    traction_density = 1000.0 / total_area  # in N/mm^2
    if load_type == 'compression':
        t_vec = np.array([0.0, -traction_density, 0.0])
    elif load_type == 'bending':
        t_vec = np.array([traction_density, 0.0, 0.0])
    else:
        raise ValueError("Unknown load type")
    # Distribute load to nodes of each face
    for f_nodes, area in zip(boundary_faces, areas):
        contrib = t_vec * area / 3.0
        for n in f_nodes:
            f[3 * n + 0] += contrib[0]
            f[3 * n + 1] += contrib[1]
            f[3 * n + 2] += contrib[2]
    return f


def find_fixed_dofs(coords, fixed_y=-74.2373, tol=1e-3):
    """Return array of DOF indices for all nodes on the fixed face at y = fixed_y.
    A tolerance of 1e-3 mm is used to account for small coordinate rounding.
    """
    inds = np.where(np.abs(coords[:, 1] - fixed_y) < tol)[0]
    dirichlet_dofs = np.concatenate([inds * 3 + i for i in range(3)])
    return dirichlet_dofs


def solve_case(K, f, dirichlet_dofs):
    # Apply Dirichlet
    K_ff, f_f, free_dofs = apply_dirichlet(K, f, dirichlet_dofs)
    # Solve linear system
    u_f = spla.spsolve(K_ff, f_f)
    # Build full displacement vector
    ndofs = K.shape[0]
    u = np.zeros(ndofs, dtype=np.float64)
    u[free_dofs] = u_f
    return u


def max_displacement(u):
    """Return maximum displacement magnitude (mm) from the displacement vector u."""
    disp = u.reshape((-1, 3))
    mag = np.linalg.norm(disp, axis=1)
    return float(np.max(mag))


def run_analysis(mesh_file, load_type):
    # Load mesh
    coords, cells = load_mesh(mesh_file)
    # Identify boundary faces on the free face
    boundary_faces = extract_boundary_faces(coords, cells)
    # Material constants
    E = 200_000.0  # N/mm^2 (200 GPa)
    nu = 0.3
    # Assemble stiffness
    K = assemble_global_stiffness(coords, cells, E, nu)
    # Fixed DOFs
    dirichlet_dofs = find_fixed_dofs(coords)
    # Load vector
    f = compute_load_vector(coords, boundary_faces, load_type)
    # Solve
    u = solve_case(K, f, dirichlet_dofs)
    # Max displacement
    max_disp = max_displacement(u)
    return max_disp, u

# ---------------------------- main flow ---------------------------

if __name__ == '__main__':
    start_time = time.time()
    # Input step file
    step_in = os.path.join(os.environ.get('CADFEM_INPUT_DIR'), 'part.step')
    # Output step file
    step_out = 'part.step'
    copy_part_step(step_in, step_out)

    # Mesh generation parameters
    coarse_lc = 3.0  # mm
    fine_lc = 1.5    # mm
    coarse_mesh_file = 'coarse.msh'
    fine_mesh_file = 'mesh.msh'  # used for analysis

    print('Generating coarse mesh...')
    generate_gmsh_mesh(step_in, coarse_mesh_file, coarse_lc)
    print('Generating fine mesh...')
    generate_gmsh_mesh(step_in, fine_mesh_file, fine_lc)

    # Perform analysis on fine mesh
    print('Running compression case (fine mesh)...')
    max_disp_compression, u_compression = run_analysis(fine_mesh_file, 'compression')
    print('Running lateral bending case (fine mesh)...')
    max_disp_bending, u_bending = run_analysis(fine_mesh_file, 'bending')

    # Store fields
    coords, cells = load_mesh(fine_mesh_file)
    node_ids = np.arange(coords.shape[0])
    np.savez('fields.npz',
             node_ids=node_ids,
             coordinates=coords,
             displacement_compression=u_compression.reshape((-1, 3)),
             displacement_bending=u_bending.reshape((-1, 3)))

    # Results json (fine mesh results)
    results = {
        'outputs': {
            'max_displacement_compression_mm': max_disp_compression,
            'max_displacement_lateral_mm': max_disp_bending
        }
    }
    with open('results.json', 'w') as fjson:
        json.dump(results, fjson, indent=2)

    # Refinement data (coarse and fine meshes)
    def get_mesh_stats(mesh_file):
        coords_, cells_ = load_mesh(mesh_file)
        # Compute displacement for both cases to compile stats
        max_compr, _ = run_analysis(mesh_file, 'compression')
        max_bend, _ = run_analysis(mesh_file, 'bending')
        return {
            'num_nodes': coords_.shape[0],
            'num_elements': cells_.shape[0],
            'max_displacement_compression_mm': max_compr,
            'max_displacement_lateral_mm': max_bend
        }

    refinement = {
        'coarse': get_mesh_stats(coarse_mesh_file),
        'fine': get_mesh_stats(fine_mesh_file)
    }
    with open('refinement.json', 'w') as fref:
        json.dump(refinement, fref, indent=2)

    # Solver log
    log_lines = []
    log_lines.append(f"Python version: {sys.version}")
    log_lines.append(f"NumPy version: {np.__version__}")
    log_lines.append(f"SciPy version: {spla.__doc__ or 'unknown'}")
    log_lines.append(f"Meshio version: {meshio.__version__}")
    log_lines.append(f"Gmsh API version: {gmsh.GMSH_API_VERSION_MAJOR}.{gmsh.GMSH_API_VERSION_MINOR}.{gmsh.GMSH_API_VERSION_PATCH}")
    log_lines.append(f"Scikit-fem version: { __import__('skfem').__version__ }")
    log_lines.append(f"Number of nodes (fine): {coords.shape[0]}")
    log_lines.append(f"Number of elements (fine): {cells.shape[0]}")
    log_lines.append(f"Compression case max displacement: {max_disp_compression} mm")
    log_lines.append(f"Lateral bending case max displacement: {max_disp_bending} mm")
    with open('solver.log', 'w') as flog:
        flog.write('\n'.join(log_lines))

    # Environment json
    env = {
        'software': {
            'python': sys.version.split('\n')[0],
            'numpy': np.__version__,
            'scipy': spla.__class__.__module__,
            'meshio': meshio.__version__,
            'gmsh': f"{gmsh.GMSH_API_VERSION_MAJOR}.{gmsh.GMSH_API_VERSION_MINOR}.{gmsh.GMSH_API_VERSION_PATCH}",
            'scikit-fem': __import__('skfem').__version__
        },
        'command': 'python main.py',
        'units': {
            'length': 'mm',
            'force': 'N',
            'displacement': 'mm'
        },
        'field_schema': {
            'node_ids': 'int',
            'coordinates': 'float',
            'displacement_compression': 'float',
            'displacement_bending': 'float'
        },
        'physical_group_mapping': {
            'fixed_face': 'y=-74.2373 mm',
            'load_face': 'y=+74.2373 mm'
        },
        'quantity_extraction': {
            'max_displacement': 'computed from displacement field',
            'total_load': '1000 N applied uniformly',
            'boundary_faces': 'identified numerically'
        },
        'modeling_assumptions': {
            'material': 'linear isotropic elastic, E=200 GPa, nu=0.3',
            'boundary_conditions': 'fixed displacement at y=-74.2373 mm, uniform traction at y=+74.2373 mm',
            'gravity': 'none',
            'linear_strain': True
        }
    }
    with open('environment.json', 'w') as fenv:
        json.dump(env, fenv, indent=2)

    elapsed = time.time() - start_time
    print(f'Execution finished in {elapsed:.2f} seconds.')
#"""
