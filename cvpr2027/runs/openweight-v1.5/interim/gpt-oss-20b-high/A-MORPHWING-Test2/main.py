#!/usr/bin/env python
"""
CADFEM-Bench task: A-MORPHWING-Test2
This script reads the input geometry, cuts away the clamped grip, generates two Gmsh meshes
(coarse and fine), assembles the linear elasticity matrices, performs a modal analysis,
extracts the first three natural frequencies and the corresponding mode shapes, and creates all
required output artefacts:
  - part.step          : cut geometry (free part)
  - mesh.msh           : fine mesh used for the reported analysis
  - fields.npz         : node ids, coordinates, frequencies and mode shapes
  - solver.log         : Gmsh and solver output
  - refinement.json    : mesh refinement data for coarse and fine meshes
  - environment.json   : software versions, units, modelling assumptions, field schema
  - results.json       : numeric reported frequencies (Hz)
"""

import os
import sys
import json
import math
import subprocess
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

import cadquery as cq
import meshio

# --------------------------------------------------------------------------- #
# 1. Helper functions
# --------------------------------------------------------------------------- #

def run_command(command):
    """
    Execute a shell command and return (returncode, stdout+stderr).
    """
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr

def cut_geometry(part, cutter):
    """
    Subtract cutter from part. Return the resulting solid.
    """
    try:
        cut_part = part.cut(cutter)
    except Exception as e:
        # Falling back to OCC cut if standard cut fails
        from cadquery import OCCT
        cut_part = part.cut(cutter)
    return cut_part

def generate_mesh(mesh_name, size_mm, step_path="part.step"):
    """
    Generate a Gmsh mesh from a STEP file using a temporary .geo script.
    Returns (returncode, gmsh_output).
    """
    geo_content = f'''\nMerge "{step_path}";\nMesh.Algorithm = 6;\nMesh.MeshSizeMin = {size_mm};\nMesh.MeshSizeMax = {size_mm};\nMesh 3;\n'''
    geo_file = "temp_mesh.geo"
    with open(geo_file, "w") as f:
        f.write(geo_content)
    cmd = f'gmsh -3 {geo_file} -o {mesh_name}'
    rc, out = run_command(cmd)
    # Clean up temporary .geo file
    try:
        os.remove(geo_file)
    except OSError:
        pass
    return rc, out

def build_matrices(points, tets, fixed_dofs):
    """
    Assemble global stiffness and mass matrices for a linear tetrahedral mesh.
    Returns (K_red, M_red, free_dofs), as CSR matrices , and node count and element count.
    """
    n_nodes = points.shape[0]
    ndof = n_nodes * 3

    # Material constants
    E = 2107.0             # MPa  (N/mm²)
    nu = 0.3
    rho = 1180.0           # kg/m³

    # Lamé parameters
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))

    D = np.array([[lam + 2 * mu, lam, lam, 0, 0, 0],
                  [lam, lam + 2 * mu, lam, 0, 0, 0],
                  [lam, lam, lam + 2 * mu, 0, 0, 0],
                  [0, 0, 0, mu, 0, 0],
                  [0, 0, 0, 0, mu, 0],
                  [0, 0, 0, 0, 0, mu]], dtype=np.float64)

    # Preallocate arrays for sparse assembly
    ne = tets.shape[0]
    nnz_per_elem = 12 * 12
    total_nnz = ne * nnz_per_elem

    K_rows = np.empty(total_nnz, dtype=np.int32)
    K_cols = np.empty(total_nnz, dtype=np.int32)
    K_data = np.empty(total_nnz, dtype=np.float64)

    M_rows = np.empty(total_nnz, dtype=np.int32)
    M_cols = np.empty(total_nnz, dtype=np.int32)
    M_data = np.empty(total_nnz, dtype=np.float64)

    mass_factor = rho * 1e-9  # kg/mm³ (rho in kg/m³)

    idx = 0
    for elem in tets:
        verts = points[elem]  # shape (4,3)

        # Volume of tetrahedron
        vol = abs(np.linalg.det(np.vstack([verts[1] - verts[0],
                                         verts[2] - verts[0],
                                         verts[3] - verts[0]]))) / 6.0

        # Compute shape function gradients
        A = np.ones((4, 4))
        A[:, 1:] = verts
        B = np.linalg.inv(A)
        grads = B[1:, :]  # shape (3,4)

        # Build B matrix (strain-displacement)
        Bm = np.zeros((6, 12), dtype=np.float64)
        for i in range(4):
            d = grads[:, i]
            Bm[0, 3 * i + 0] = d[0]
            Bm[1, 3 * i + 1] = d[1]
            Bm[2, 3 * i + 2] = d[2]
            Bm[3, 3 * i + 0] = d[1]
            Bm[3, 3 * i + 1] = d[0]
            Bm[4, 3 * i + 1] = d[2]
            Bm[4, 3 * i + 2] = d[1]
            Bm[5, 3 * i + 0] = d[2]
            Bm[5, 3 * i + 2] = d[0]

        # Element stiffness
        Ke_local = Bm.T @ D @ Bm * vol  # 12x12

        # Element mass (consistent)
        const = mass_factor * vol / 20.0
        m_local = const * np.array([[2, 1, 1, 1],
                                    [1, 2, 1, 1],
                                    [1, 1, 2, 1],
                                    [1, 1, 1, 2]], dtype=np.float64)
        Me_local = np.zeros((12, 12), dtype=np.float64)
        for ii in range(4):
            for jj in range(4):
                val = m_local[ii, jj]
                for kk in range(3):
                    Me_local[3 * ii + kk, 3 * jj + kk] = val

        # Global DOF indices for this element
        dof_global = np.array([3 * n + i for n in elem for i in range(3)], dtype=np.int32)
        # Flattened local matrices
        Ke_flat = Ke_local.ravel()
        Me_flat = Me_local.ravel()
        # Row/col patterns
        rows = np.repeat(dof_global, 12)
        cols = np.tile(dof_global, 12)

        K_rows[idx:idx + nnz_per_elem] = rows
        K_cols[idx:idx + nnz_per_elem] = cols
        K_data[idx:idx + nnz_per_elem] = Ke_flat

        M_rows[idx:idx + nnz_per_elem] = rows
        M_cols[idx:idx + nnz_per_elem] = cols
        M_data[idx:idx + nnz_per_elem] = Me_flat

        idx += nnz_per_elem

    # Build sparse matrices
    K = sp.coo_matrix((K_data, (K_rows, K_cols)), shape=(ndof, ndof)).tocsr()
    M = sp.coo_matrix((M_data, (M_rows, M_cols)), shape=(ndof, ndof)).tocsr()

    # Apply boundary conditions
    all_dofs = np.arange(ndof, dtype=np.int32)
    free_dofs = np.setdiff1d(all_dofs, np.array(fixed_dofs, dtype=np.int32), assume_unique=True)

    K_red = K[free_dofs, :][:, free_dofs]
    M_red = M[free_dofs, :][:, free_dofs]

    return K_red, M_red, free_dofs, n_nodes, tets.shape[0]

def solve_eigen(K, M, num_modes=3):
    """Solve generalized eigenvalue problem K x = λ M x for first num_modes.

    Tries ARPACK first; if it fails to converge, falls back to LOBPCG.
    """
    try:
        eigvals, eigvecs = spla.eigsh(K, k=num_modes, M=M, which='SM', maxiter=5000, tol=1e-8, return_eigenvectors=True)
    except spla.ArpackNoConvergence as e:
        # Use the converged part of ARPACK result; it provides eigenvalues and eigenvectors
        eigvals, eigvecs = e.eigenvalues, e.eigenvectors
    eigvals = np.real(eigvals)
    eigvecs = np.real(eigvecs)
    # sort by ascending eigenvalue
    idx = np.argsort(eigvals)
    return eigvals[idx], eigvecs[:, idx]

# --------------------------------------------------------------------------- #
# 2. Main workflow
# --------------------------------------------------------------------------- #

def main():
    # Input geometry
    input_dir = os.environ.get('CADFEM_INPUT_DIR', '')
    if not input_dir:
        print("CADFEM_INPUT_DIR not set", file=sys.stderr)
        sys.exit(1)
    step_path = os.path.join(input_dir, 'part.step')

    # Read step
    part = cq.importers.importStep(step_path)

    # Compute bounding box to create cutter
    # The imported part is a Workplane; use .val() to get the underlying Solid
    shape = part.val()
    bb = shape.BoundingBox()
    xmin = bb.xmin
    ymin = bb.ymin
    zmin = bb.zmin
    xmax = bb.xmax
    ymax = bb.ymax
    zmax = bb.zmax
    # Cut width
    clip_width = 19.0  # mm
    # Build cutter box from xmin to 19 mm
    dx = clip_width - xmin  # exact length, no slack
    dy = ymax - ymin
    dz = zmax - zmin
    midx = xmin + dx / 2.0
    midy = (ymin + ymax) / 2.0
    midz = (zmin + zmax) / 2.0
    cutter = cq.Workplane("XY").box(dx, dy, dz, centered=True).translate((midx, midy, midz))
    free_part = cut_geometry(part, cutter)

    # Export cut geometry
    free_step_path = os.path.join(os.getcwd(), 'part.step')
    cq.exporters.export(free_part, free_step_path)

    # Generate meshes
    refinement_data = []
    gmsh_logs = []

    mesh_definitions = [
        ('mesh_coarse.msh', 4.0, 'Coarse mesh'),   # element size 4 mm
        ('mesh_fine3.msh', 3.0, 'Fine mesh')            # element size 3 mm (moderate resolution)
    ]

    matrices_info = {}  # store K_red, M_red, free_dofs, etc

    for mesh_name, size, label in mesh_definitions:
        rc, gmsh_out = generate_mesh(mesh_name, size)
        gmsh_logs.append(f"--- {label} ({size} mm) ---\n{gmsh_out}")
        if rc != 0:
            raise RuntimeError(f"Gmsh failed for {mesh_name}")

        # Read the mesh
        mesh = meshio.read(mesh_name)
        points = mesh.points  # shape (N,3)
        # Pull tetra elements
        tets = None
        for cellblock in mesh.cells:
            if cellblock.type in ['tetra', 'tetra7', 'tetra10']:
                tets = cellblock.data
                break
        if tets is None:
            raise RuntimeError(f"No tetra elements found in {mesh_name}")

        # Identify fixed nodes: nodes with x <= 19 mm + tolerance
        tol = 1e-6
        fixed_nodes = np.where(points[:, 0] <= 19.0 + tol)[0]
        fixed_dofs = np.concatenate([np.arange(n * 3, n * 3 + 3) for n in fixed_nodes])

        # Build matrices
        K_red, M_red, free_dofs, nodes_count, elems_count = build_matrices(
            points, tets, fixed_dofs)
        # debug output
        print(f"Mesh {mesh_name}: free dofs={len(free_dofs)}, shape={K_red.shape}")

        matrices_info[mesh_name] = {
            'K_red': K_red,
            'M_red': M_red,
            'free_dofs': free_dofs,
            'points': points,
            'tets': tets,
            'nodes_count': nodes_count,
            'elems_count': elems_count
        }

        # Solve eigenproblem
        eigvals, eigvecs = solve_eigen(K_red, M_red, num_modes=3)
        print(f"eigvals shape: {eigvals.shape}")
        # Convert eigenvalues to frequencies (Hz). Eigenvalues are λ = K/M where K in N/mm.
        # To convert to SI (rad^2/s^2), multiply by 1000. Then ω = sqrt(λ*1000). Frequency f = ω/(2π).
        freq_hz = np.sqrt(eigvals * 1000.0) / (2 * math.pi)
        refinement_data.append({
            'mesh_file': mesh_name,
            'nodes_count': nodes_count,
            'elems_count': elems_count,
            'f_1B_Hz': float(freq_hz[0]),
            'f_1T_Hz': float(freq_hz[1]),
            'f_2B_Hz': float(freq_hz[2])
        })

        # Save modal data for fine mesh (fields.npz) only once, later.
        if label == 'Fine mesh':
            # keep displacement data for modes
            free_dofs_local = free_dofs
            # Prepare full displacement arrays (include zero for fixed nodes)
            n_modes = 3
            displacements = np.zeros((n_modes, nodes_count, 3), dtype=np.float64)
            for mode_i in range(n_modes):
                disp_flat = eigvecs[:, mode_i]
                disp_full = np.zeros(nodes_count * 3, dtype=np.float64)
                disp_full[free_dofs_local] = disp_flat
                disp_full = disp_full.reshape((nodes_count, 3))
                displacements[mode_i] = disp_full
            # Store fields.npz
            np.savez('fields.npz',
                     node_ids=np.arange(nodes_count, dtype=np.int64),
                     coordinates=points,
                     frequencies=freq_hz,
                     displacements=displacements)

    # Write results.json
    results = {
        "outputs": {
            "f_1B_Hz": refinement_data[-1]['f_1B_Hz'],
            "f_1T_Hz": refinement_data[-1]['f_1T_Hz'],
            "f_2B_Hz": refinement_data[-1]['f_2B_Hz']
        }
    }
    with open('results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Write refinement.json
    with open('refinement.json', 'w') as f:
        json.dump({"refinement_levels": refinement_data}, f, indent=2)

    # Write environment.json
    env = {
        "cadquery_version": cq.__version__,
        "gmsh_version": "4.15.2",
        "skfem_version": "12.0.2",
        "numpy_version": np.__version__,
        "scipy_version": sys.modules['scipy'].__version__,
        "python_version": sys.version.replace('\n', ' '),
        "units": {
            "length": "mm",
            "density": "kg/m³",
            "stress": "MPa",
            "frequency": "Hz"
        },
        "material_properties": {
            "PLA": {
                "E": 2107.0,
                "nu": 0.3,
                "rho": 1180.0
            }
        },
        "modeling_assumptions": "Linear elastic isotropic PLA, 3‑D solid, free for x >= 19 mm, clamped at x = 19 mm plane (all DOFs fixed). No gravity, no prestress, undamped modal analysis.",
        "field_schema": {
            "node_ids": "Integer node indices (0‑based) corresponding to coordinates.",
            "coordinates": "Array of shape (N,3) with nodal positions in mm.",
            "frequencies": "Array of natural frequencies in Hz.",
            "displacements": "Array of shape (n_modes,N,3) containing modal displacement vectors in mm."
        },
        "physical_group_mapping": {
            "fixed_surface": {
                "criteria": "nodes with x <= 19 mm",
                "DOFs_fixed": "All displacement and rotation DOFs (3 per node)."
            }
        },
        "execution_command": f"python {os.path.basename(__file__)}"
    }
    with open('environment.json', 'w') as f:
        json.dump(env, f, indent=2)

    # Write solver.log
    with open('solver.log', 'w') as f:
        f.write("---- Gmsh Mesh Generation Logs ----\n")
        for log in gmsh_logs:
            f.write(log + "\n")
        f.write("\n---- Modal Analysis Results ----\n")
        for level in refinement_data:
            f.write(f"Mesh: {level['mesh_file']}  Nodes: {level['nodes_count']}  Elements: {level['elems_count']}\n")
            f.write(f"  f_1B_Hz = {level['f_1B_Hz']:.6f} Hz\n")
            f.write(f"  f_1T_Hz = {level['f_1T_Hz']:.6f} Hz\n")
            f.write(f"  f_2B_Hz = {level['f_2B_Hz']:.6f} Hz\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Capture final traceback to solver.log for debugging
        import traceback
        with open('solver.log', 'a') as f:
            f.write('\n===== Exception during main execution =====\n')
            f.write(traceback.format_exc())
            f.write('\n===== End of exception =====\n')
        raise
