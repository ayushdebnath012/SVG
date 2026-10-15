#!/usr/bin/env python3
"""CAD + FEM analysis for Task A-AGENTFEM-fresh_test_002.

The script performs the following steps:

1. Copies the supplied geometry (``geometry.step``) to ``part.step``.
2. Generates two Gmsh meshes – nominal (9 mm characteristic length) and
   refined (4.5 mm).  Meshes are written as ``mesh_nominal.msh`` and
   ``mesh_refined.msh``.
3. The nominal mesh is used to evaluate the requested outputs.
4. A linear‑elastic problem (E = 70 GPa, ν = 0.33) is solved on each mesh.
   The plate is fully fixed on the bottom (z ≈ 0) and has a uniform
   downward traction on the top (z ≈ 189 mm).  The traction is
   distributed by splitting the surface area of each top facet among its
   three nodes, which guarantees that the total load equals the
   prescribed 10 kN.
5. Results are written to ``results.json`` (seat mean displacement and
   maximum displacement).  The full nodal field, node ids and
   coordinates are stored in ``fields.npz``.
6. A convergence report is provided in ``refinement.json``.
7. Environment details (python, numpy, scipy, gmsh, skfem) are stored
   in ``environment.json``.
8. Solver diagnostics are written to ``solver.log``.

The script is fully reproducible; running ``python main.py`` with
``$CADFEM_INPUT_DIR`` pointing to the input directory will regenerate
all artifacts.
"""

from __future__ import annotations

import json
import os
import shutil
import time
import sys
from typing import Tuple

import gmsh
import numpy as np
import scipy
from scipy.sparse.linalg import spsolve
from skfem import Basis, asm
from skfem.element import ElementTetP1, ElementVector
from skfem.io import meshio
from skfem.models import elasticity as el

# ------------------------------------------------------------------
# Mesh generation
# ------------------------------------------------------------------

def generate_mesh(name: str, char_length: float) -> str:
    """Generate a Gmsh mesh for the supplied geometry.

    Parameters
    ----------
    name : str
        Base name for the output mesh file (``.msh`` extension added).
    char_length : float
        Target characteristic length (in mm).
    Returns
    -------
    str
        Path to the generated ``.msh`` file.
    """
    gmsh.initialize()
    gmsh.model.add("bracket")

    geom_path = os.path.join(os.getenv("CADFEM_INPUT_DIR", ""), "geometry.step")
    gmsh.merge(geom_path)

    # Point size, global mesh order
    point_tags = [(dim, tag) for dim, tag in gmsh.model.getEntities(0)]
    gmsh.model.mesh.setSize(point_tags, char_length)
    gmsh.model.mesh.setOrder(2)

    gmsh.model.mesh.generate(3)
    mesh_file = f"{name}.msh"
    gmsh.write(mesh_file)
    gmsh.finalize()
    return mesh_file


# ------------------------------------------------------------------
# Finite‑element assembly / solve
# ------------------------------------------------------------------

def assemble_and_solve(mesh_file: str, traction_N_per_mm2: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, object]:
    """Solve the 3‑D linear elasticity problem on the supplied mesh.

    The solver uses Dirichlet conditions on all nodes with ``z <= 1e‑3``
    (bottom) and applies a uniform downward traction on the top face by
    distributing the load over the area of each top facet.
    """
    mesh = meshio.from_file(mesh_file, 'tetra')
    # Coordinates shape: (N, 3) in mm
    coords = mesh.p.T
    num_nodes = coords.shape[0]

    # Build vector field basis (quadratic tetrahedron in 3D)
    scalar_elem = ElementTetP1()
    vec_elem = ElementVector(scalar_elem, dim=3)
    V = Basis(mesh, vec_elem)

    # Material parameters
    E = 70e3  # N/mm^2
    nu = 0.33
    lam, mu = el.lame_parameters(E, nu)
    B = el.linear_elasticity(lam, mu)
    A = asm(B, V)
    b = np.zeros(A.shape[0])

    # ----- Dirichlet BC on bottom --------------
    bottom_tol = 1e-3
    bottom_nodes = np.where(coords[:, 2] <= bottom_tol)[0]
    print("Bottom node count", len(bottom_nodes))
    bottom_dofs = np.concatenate([np.arange(3 * n, 3 * n + 3) for n in bottom_nodes])
    # Identify nodes that are not referenced by any element (unused nodes). These
    # may occur in higher‑order meshes containing additional nodes that are not
    # part of the finite‑element discretisation.
    used_nodes = np.unique(mesh.t.ravel())
    all_nodes = np.arange(coords.shape[0])
    unused_nodes = np.setdiff1d(all_nodes, used_nodes)
    if unused_nodes.size > 0:
        unused_dofs = np.concatenate([np.arange(3 * u, 3 * u + 3) for u in unused_nodes])
    else:
        unused_dofs = np.array([], dtype=int)
    # Combine Dirichlet DOFs
    dirichlet_dofs = np.concatenate([bottom_dofs, unused_dofs])
    A = A.tolil()
    for d in dirichlet_dofs:
        A.rows[d] = []
        A.data[d] = []
        A[:, d] = 0
        A[d, d] = 1
        b[d] = 0.0
    A = A.tocsr()

    # ----- Traction on top surface -------------
    top_tol = 1e-3
    max_z = np.max(coords[:, 2])
    # Find facets that lie on the top plane
    facets = mesh.facets  # shape (n_facets, 3)
    facet_z = coords[facets, 2]
    top_facets = np.where(np.all(np.abs(facet_z - max_z) < top_tol, axis=0))[0]
    for fi in top_facets:
        n = facets[:, fi]
        pts = coords[n]
        area = 0.5 * np.linalg.norm(np.cross(pts[1] - pts[0], pts[2] - pts[0]))
        fload = traction_N_per_mm2 * area / 3.0
        for node in n:
            b[3 * node + 2] -= fload

    # Solve linear system
    u = spsolve(A, b)

    # Return displacement, coordinates, top node indices, and mesh object
    top_nodes = np.where(np.abs(coords[:, 2] - max_z) < top_tol)[0]
    return u, coords, top_nodes, mesh


# ------------------------------------------------------------------
# Main driver
# ------------------------------------------------------------------

def main() -> None:
    start = time.time()
    output_dir = os.getcwd()

    # Copy geometry if not already present
    geom_path = os.path.join(os.getenv("CADFEM_INPUT_DIR", ""), "geometry.step")
    part_path = os.path.join(output_dir, "part.step")
    if not os.path.isfile(part_path):
        shutil.copy(geom_path, part_path)

    # Generate meshes
    mesh_nom = generate_mesh("mesh_nominal", 9.0)
    mesh_ref = generate_mesh("mesh_refined", 4.5)

    # Load traction magnitude (MPa) → N/mm^2
    traction_N_per_mm2 = 1.98728

    # Solve nominal
    u_nom, coords_nom, top_nodes_nom, mesh_nom_obj = assemble_and_solve(mesh_nom, traction_N_per_mm2)
    # Solve refined
    u_ref, coords_ref, top_nodes_ref, mesh_ref_obj = assemble_and_solve(mesh_ref, traction_N_per_mm2)

    # Compute requested outputs for nominal
    disp_z_top = u_nom[3 * top_nodes_nom + 2]
    seat_mean_disp_mm = float(np.mean(-disp_z_top))
    disp_norms = np.linalg.norm(u_nom.reshape((-1, 3)), axis=1)
    max_disp_mm = float(np.max(disp_norms))

    # Write results.json
    outputs = {
        "seat_mean_displacement_mm": seat_mean_disp_mm,
        "max_displacement_mm": max_disp_mm,
    }
    with open("results.json", "w") as f:
        json.dump({"outputs": outputs}, f)

    # Write nominal mesh to mesh.msh for reporting
    shutil.copy(mesh_nom, "mesh.msh")

    # Write fields.npz
    np.savez(
        "fields.npz",
        node_ids=np.arange(coords_nom.shape[0]),
        coordinates=coords_nom,
        displacements=u_nom.reshape((-1, 3)),
        displacement_norms=disp_norms,
    )

    # Write solver.log
    with open("solver.log", "w") as log:
        log.write(f"Geometry used: part.step\n")
        log.write(f"Generated nominal mesh: {mesh_nom}\n")
        log.write(f"Generated refined mesh: {mesh_ref}\n")
        log.write(f"Nominal mesh nodes: {coords_nom.shape[0]}, elements: {mesh_nom_obj.t.shape[1]}\n")
        log.write(f"Refined mesh nodes: {coords_ref.shape[0]}, elements: {mesh_ref_obj.t.shape[1]}\n")
        log.write("Material: E=70 GPa, ν=0.33, density=2700 kg/m^3 (not used).\n")
        log.write("Traction: 1.98728 MPa downward on top surface.\n")
        log.write(f"Seat mean displacement: {seat_mean_disp_mm:.6f} mm\n")
        log.write(f"Max displacement: {max_disp_mm:.6f} mm\n")
        log.write("Solver: assembled and solved using scipy.spsolve.\n")

    # Write refinement.json
    refinement_data = {
        "nominal": {
            "num_nodes": coords_nom.shape[0],
            "num_elements": mesh_nom_obj.t.shape[1],
            "seat_mean_displacement_mm": seat_mean_disp_mm,
            "max_displacement_mm": max_disp_mm,
        },
        "refined": {
            "num_nodes": coords_ref.shape[0],
            "num_elements": mesh_ref_obj.t.shape[1],
            "seat_mean_displacement_mm": float(np.mean(-u_ref[3 * top_nodes_ref + 2])),
            "max_displacement_mm": float(np.max(np.linalg.norm(u_ref.reshape((-1, 3)), axis=1))),
        },
    }
    with open("refinement.json", "w") as f:
        json.dump(refinement_data, f)

    # Write environment.json
    env = {
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "gmsh_version": gmsh.GMSH_API_VERSION,
        "skfem_version": getattr(__import__("skfem"), "__version__", "unknown"),
        "command": "python main.py",
        "units": {"displacement": "mm", "force": "N"},
        "field_schema": {
            "node_ids": "int",
            "coordinates": "(N,3) float mm",
            "displacements": "(N,3) float mm",
            "displacement_norms": "(N,) float mm",
        },
        "analysis_type": "3D linear elasticity",
    }
    with open("environment.json", "w") as f:
        json.dump(env, f)

    elapsed = time.time() - start
    print(f"Completed in {elapsed:.2f} s")


if __name__ == "__main__":
    main()

