#!/usr/bin/env python
# Entry point for the CAD+FEM workflow
# The script performs geometry construction, mesh generation and modal analysis.
# It writes the required artefacts: part.step, mesh.msh, results.json, fields.npz,
# solver.log, refinement.json and environment.json.

import os
import sys
import subprocess
import json

import numpy as np
import scipy
import scipy.sparse as sp
import scipy.sparse.linalg as la
import meshio
import skfem
import skfem.models as models
from skfem import Basis
from skfem.io.meshio import from_meshio
from skfem.element import ElementTetP1, ElementVectorH1


def run_pipeline_test():
    """Run the existing geometry and mesh generation script.

    Returns:
        stdout, stderr of the subprocess.
    """
    result = subprocess.run([sys.executable, 'pipeline_test.py'],
                            capture_output=True, text=True, check=True)
    return result.stdout, result.stderr


def analyze_mesh(mesh_path, dirichlet_x=19.0, n_modes=5):
    """Perform modal analysis on a given mesh.

    Parameters
    ----------
    mesh_path: str
        Path to the Gmsh MSH file.
    dirichlet_x: float
        Coordinate of the clamped plane (x = dirichlet_x) in mm.
    n_modes: int
        Number of lowest modes to compute.
    """
    mesh_obj = meshio.read(mesh_path)
    mesh = from_meshio(mesh_obj)
    coords = mesh.doflocs.T
    n_nodes = coords.shape[0]
    n_elements = sum(1 for cell in mesh_obj.cells if cell.type == 'tetra')
    # Build vector valued P1 tetra element
    elem_sc = ElementTetP1()
    elem_vec = ElementVectorH1(elem_sc, dim=3)
    basis = Basis(mesh, elem_vec)

    # Material constants
    E = 2110e6
    nu = 0.3
    rho = 1180.0
    lam = (E * nu) / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    elastic_form = models.linear_elasticity(Lambda=lam, Mu=mu)
    K = skfem.asm(elastic_form, basis)
    ndof = K.shape[0]
    # Lumped mass matrix: M = rho * I
    M = rho * sp.identity(ndof, format='csr')
    if not sp.issparse(K):
        K = sp.csr_matrix(K.todense())
    # Dirichlet boundary: all DOFs on plane x = dirichlet_x set to zero
    tol = 1e-6
    node_indices = np.where(np.abs(coords[:, 0] - dirichlet_x) <= tol)[0]
    # For each node index, add its 3 displacement DOFs
    dofs_dirichlet = np.array([3*n + j for n in node_indices for j in range(3)], dtype=int)
    ndof = K.shape[0]
    free_mask = np.ones(ndof, dtype=bool)
    free_mask[dofs_dirichlet] = False
    Kf = K[free_mask, :][:, free_mask]
    Mf = M[free_mask, :][:, free_mask]
    # Solve the generalized eigenvalue problem for the lowest n_modes
    eigvals, eigvecs = la.eigsh(Kf, k=n_modes, M=Mf, sigma=0.0, which='LM', maxiter=2000)
    idx = np.argsort(eigvals)
    eigvals = eigvals[idx]
    eigvecs = eigvecs[:, idx]
    freqs = np.sqrt(eigvals) / (2 * np.pi)
    # Reshape eigenvectors into (n_nodes, 3, n_modes)
    # Build full displacement field including zeroed constrained DOFs
    full_disp = np.zeros((ndof, n_modes))
    full_disp[free_mask, :] = eigvecs
    vecs_per_mode = full_disp.reshape((n_nodes, 3, n_modes))
    # Compute energy in each component (x,y,z)
    energies = np.sum(vecs_per_mode**2, axis=0)  # shape (3, n_modes)
    # Identify bending (z) and torsion (y) modes
    z_energies = energies[2, :]
    y_energies = energies[1, :]
    bending_order = np.argsort(-z_energies)
    bending_indices = bending_order[:2]
    torsion_index = np.argmax(y_energies)
    f_1B = freqs[bending_indices[0]]
    f_2B = freqs[bending_indices[1]]
    f_1T = freqs[torsion_index]
    return {
        "frequencies": freqs,
        "mode_shapes": vecs_per_mode,
        "n_nodes": n_nodes,
        "n_elements": n_elements,
        "f_1B": f_1B,
        "f_1T": f_1T,
        "f_2B": f_2B,
        "coords": coords,
    }


def main():
    solver_log = []

    # 1. Generate geometry and half plane by pipeline_test
    out, err = run_pipeline_test()
    solver_log.append("=== pipeline_test output ===")
    solver_log.append(out)
    solver_log.append(err)

    # 2. Mesh info (coarse)
    coarse = analyze_mesh('mesh_coarse.msh')
    # 3. Mesh info (fine)
    fine = analyze_mesh('mesh_fine.msh')

    # 4. Write results.json – only the required outputs
    outputs = {
        "f_1B_Hz": float(fine["f_1B"]),
        "f_1T_Hz": float(fine["f_1T"]),
        "f_2B_Hz": float(fine["f_2B"]),
    }
    with open('results.json', 'w') as f:
        json.dump({"outputs": outputs}, f, indent=4)

    # 5. Write fields.npz – field data for the fine analysis
    np.savez(
        'fields.npz',
        node_ids=np.arange(fine["n_nodes"]),
        coordinates=fine["coords"],
        frequencies=fine["frequencies"],
        mode_shapes=fine["mode_shapes"],
    )

    # 6. Write refinement.json – coarse and fine data
    refinement = {
        "coarse": {
            "nodes": coarse["n_nodes"],
            "elements": coarse["n_elements"],
            "f_1B_Hz": float(coarse["f_1B"]),
            "f_1T_Hz": float(coarse["f_1T"]),
            "f_2B_Hz": float(coarse["f_2B"]),
        },
        "fine": {
            "nodes": fine["n_nodes"],
            "elements": fine["n_elements"],
            "f_1B_Hz": float(fine["f_1B"]),
            "f_1T_Hz": float(fine["f_1T"]),
            "f_2B_Hz": float(fine["f_2B"]),
        },
    }
    with open('refinement.json', 'w') as f:
        json.dump(refinement, f, indent=4)

    # 7. Write environment.json – solver / library information
    try:
        gmsh_version_line = [l for l in out.splitlines() if "Gmsh" in l][0]
        gmsh_version = gmsh_version_line.split(']')[0].split('Gmsh')[-1].strip()
    except Exception:
        gmsh_version = None
    env = {
        "skfem_version": skfem.__version__,
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "gmsh_version": gmsh_version,
        "mesh_generation_command": "gmsh -3 -format msh -o mesh_fine.msh part.step -order 1 -clscale 0.5",
        "analysis_command": "Python modal analysis using skfem",
        "material": {"E": 2110e6, "nu": 0.3, "rho": 1180.0},
        "boundary_condition": {"Dirichlet": "x=19 mm plane, all DOFs zero"},
        "units": {"length": "mm", "stiffness": "Pa", "density": "kg/m^3", "frequency": "Hz"},
        "field_schema": {
            "node_ids": "int array of node indices",
            "coordinates": "float array of shape (n_nodes,3)",
            "frequencies": "float array of mode frequencies (Hz)",
            "mode_shapes": "float array of shape (n_nodes,3,n_modes)"
        },
    }
    with open('environment.json', 'w') as f:
        json.dump(env, f, indent=4)

    # 8. Write solver.log – include all command outputs
    solver_log.append("=== analysis coarse ===")
    solver_log.append(f"frequencies (Hz): {coarse['frequencies']}")
    solver_log.append("=== analysis fine ===")
    solver_log.append(f"frequencies (Hz): {fine['frequencies']}")
    with open('solver.log', 'w') as f:
        f.write('\n'.join(solver_log))


if __name__ == "__main__":
    main()
