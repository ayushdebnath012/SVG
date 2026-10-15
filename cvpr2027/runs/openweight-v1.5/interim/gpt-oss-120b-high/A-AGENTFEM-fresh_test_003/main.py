#!/usr/bin/env python
"""Finite element analysis for the AgentFEM bracket fresh_test_003.

The script performs the following steps:
  1. Copies the input STEP geometry (geometry.step) to the output as part.step.
  2. Generates two meshes with Gmsh (linear tetrahedra, order 1):
       - coarse mesh with target element size 9 mm (publisher nominal mesh)
       - refined mesh with target element size 6 mm (for a simple convergence check)
  3. For each mesh solves a 3‑D linear elastic problem:
       * Material: E=70 GPa, ν=0.33 (Aluminium‑like)
       * Fixed support on all faces where z≈0 (bottom of the bracket)
       * Uniform downward pressure of 1.98728 N/mm² on the top seat face (z≈189 mm).
  4. Extracts the mean downward displacement on the top seat face and the maximum
     displacement magnitude in the whole part.
  5. Writes the required output files:
       results.json, mesh.msh (refined mesh), fields.npz, solver.log,
       refinement.json (two mesh resolutions) and environment.json.

All geometric units are millimetres (mm); forces are Newtons (N) and stresses are N/mm².
"""

from __future__ import annotations

import os
import json
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Tuple, List, Dict

import numpy as np
import meshio

# scikit‑fem imports
from skfem import Mesh, Basis, ElementVector, ElementTetP1, asm, enforce, solve
from skfem.models.elasticity import linear_elasticity

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def run_gmsh(step_path: Path, mesh_path: Path, clmax: float) -> None:
    """Generate a linear tetrahedral mesh with Gmsh.

    Parameters
    ----------
    step_path: Path
        Input STEP geometry.
    mesh_path: Path
        Destination mesh file (Gmsh version 2 format).
    clmax: float
        Target maximum element size (mm).
    """
    cmd = [
        "gmsh",
        "-3",                 # 3‑D mesh
        "-order", "1",       # linear elements (order 1)
        "-clmax", f"{clmax}",
        "-format", "msh2",
        "-o", str(mesh_path),
        str(step_path),
    ]
    logging.info("Running Gmsh: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def load_mesh(mesh_path: Path) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
    """Read a Gmsh mesh via meshio and discard unused vertices.

    Gmsh may generate additional surface vertices that are not referenced
    by any volume element.  Those vertices lead to zero rows in the stiffness
    matrix and cause a singular system.  This function removes any vertex
    that does not appear in the ``tetra`` connectivity and remaps the indices
    in both the volume and surface cell blocks.

    Returns
    -------
    points : (N_used, 3) ndarray
        Coordinates of the vertices that are part of at least one tetrahedron.
    tets : (M, 4) ndarray
        Linear tetrahedron connectivity using the new compact vertex numbering.
    cell_data : dict
        Additional cell blocks (e.g. ``"triangle"``) with indices remapped to
        the compact vertex set.  Any triangle that references a removed vertex
        is discarded.
    """
    mesh = meshio.read(str(mesh_path))
    points = mesh.points
    if "tetra" not in mesh.cells_dict:
        raise RuntimeError("No linear tetrahedra found in mesh")
    tets = mesh.cells_dict["tetra"]

    # Identify vertices that are actually used by tetrahedra
    used = np.unique(tets)
    # Build a mapping from old to new vertex indices
    mapping = -np.ones(points.shape[0], dtype=int)
    mapping[used] = np.arange(used.size)

    # Compact the point array
    points = points[used]
    # Remap tetrahedron connectivity
    tets = mapping[tets]

    # Process other cell blocks (e.g., surface triangles)
    cell_data: Dict[str, np.ndarray] = {}
    for name, cells in mesh.cells_dict.items():
        if name == "tetra":
            continue
        # Keep only cells whose all vertices are present in the mapping
        valid_mask = np.all(mapping[cells] != -1, axis=1)
        if np.any(valid_mask):
            cell_data[name] = mapping[cells[valid_mask]]
    return points, tets, cell_data


def build_basis(points: np.ndarray, tets: np.ndarray) -> Tuple[Mesh, Basis]:
    """Build a scikit‑fem mesh and vector basis for linear elasticity."""
    # scikit‑fem expects (dim, N) coordinates and (n_vertices, n_elem) connectivity.
    pts_t = points.T          # (3, N)
    conn_t = tets.T           # (4, n_elem)
    sf_mesh = Mesh(pts_t, conn_t, elem=ElementTetP1)
    vec_elem = ElementVector(ElementTetP1())
    basis = Basis(sf_mesh, vec_elem)
    return sf_mesh, basis


def solve_analysis(mesh_path: Path, pressure: float) -> Tuple[float, float, np.ndarray, np.ndarray]:
    """Solve the linear elastic problem for a single mesh.

    Returns
    -------
    seat_mean : float
        Mean downward displacement on the top seat face (mm).
    max_disp : float
        Maximum displacement magnitude in the model (mm).
    points : (N, 3) ndarray
        Node coordinates (mm).
    displacements : (N, 3) ndarray
        Nodal displacement vectors (mm).
    """
    points, tets, cell_data = load_mesh(mesh_path)
    sf_mesh, basis = build_basis(points, tets)

    # Material parameters (Aluminium‑like)
    E = 70_000.0          # N/mm² (70 GPa)
    nu = 0.33
    lam = (E * nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
    mu = E / (2.0 * (1.0 + nu))

    # Stiffness matrix
    # Build the elasticity bilinear form with material parameters
    elastic_form = linear_elasticity(Lambda=lam, Mu=mu)
    K = asm(elastic_form, basis)
    f = np.zeros(basis.N, dtype=float)

    # ---- Dirichlet BC : bottom (z = 0) ----
    z_coords = sf_mesh.doflocs[2, :]
    bottom_mask = np.isclose(z_coords, 0.0, atol=1e-6)
    bottom_node_ids = np.where(bottom_mask)[0]
    fixed_dofs = np.concatenate([
        bottom_node_ids * 3 + 0,
        bottom_node_ids * 3 + 1,
        bottom_node_ids * 3 + 2,
    ])

    # ---- Neumann BC : uniform pressure on top seat face ----
    top_z = np.max(z_coords)
    triangles = cell_data.get("triangle")
    if triangles is None:
        raise RuntimeError("No triangle surface data found for traction application")
    tri_pts = points[triangles]  # (n_tri, 3, 3)
    tol = 1e-3
    top_tri_mask = np.all(np.abs(tri_pts[:, :, 2] - top_z) < tol, axis=1)
    top_triangles = triangles[top_tri_mask]
    # Triangle areas
    v0 = tri_pts[top_tri_mask, 0, :]
    v1 = tri_pts[top_tri_mask, 1, :]
    v2 = tri_pts[top_tri_mask, 2, :]
    cross = np.cross(v1 - v0, v2 - v0)
    areas = 0.5 * np.linalg.norm(cross, axis=1)
    # Consistent nodal loads (pressure * area / 3) in -z direction
    load_per_node = pressure * areas / 3.0
    for tri, load in zip(top_triangles, load_per_node):
        for nid in tri:
            f[nid * 3 + 2] -= load

    # Apply Dirichlet BCs
    K_bc, f_bc = enforce(K, f, D=fixed_dofs)

    # Solve
    U = solve(K_bc, f_bc)

    # Extract nodal displacements
    u_x = U[basis.dofs.nodal_dofs[0, :]]
    u_y = U[basis.dofs.nodal_dofs[1, :]]
    u_z = U[basis.dofs.nodal_dofs[2, :]]
    displacements = np.vstack((u_x, u_y, u_z)).T

    # Post‑processing
    top_node_mask = np.isclose(z_coords, top_z, atol=1e-3)
    top_node_ids = np.where(top_node_mask)[0]
    seat_mean = -np.mean(u_z[top_node_ids])  # downward magnitude
    magnitude = np.sqrt(u_x**2 + u_y**2 + u_z**2)
    max_disp = np.max(magnitude)

    return seat_mean, max_disp, points, displacements


def write_fields_npz(filename: Path, points: np.ndarray, displacements: np.ndarray) -> None:
    """Save node IDs, coordinates and displacement vectors to a .npz file."""
    node_ids = np.arange(points.shape[0], dtype=np.int32)
    np.savez(filename, node_ids=node_ids, coordinates=points, displacements=displacements)


def write_results_json(filename: Path, seat_mean: float, max_disp: float) -> None:
    data = {"outputs": {"seat_mean_displacement_mm": float(seat_mean), "max_displacement_mm": float(max_disp)}}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def write_refinement_json(filename: Path, refinements: List[Dict]) -> None:
    data = {"refinements": refinements}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def write_environment_json(filename: Path) -> None:
    import platform
    import gmsh
    env = {
        "python_version": platform.python_version(),
        "gmsh_version": gmsh.__version__,
        "numpy_version": np.__version__,
        "scikit_fem_version": __import__('skfem').__version__,
        "units": "mm for length, N for force, N/mm^2 for stress",
        "material": {"E": 70000.0, "nu": 0.33},
        "load": {"pressure": 1.98728, "direction": "-z"},
        "boundary_conditions": {"fixed_z": 0.0},
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(env, f, indent=2)


def main() -> None:
    # Set up logging
    logging.basicConfig(filename="solver.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s: %(message)s")

    input_dir = Path(os.getenv("CADFEM_INPUT_DIR", "."))
    output_dir = Path(os.getenv("CADFEM_OUTPUT_DIR", "."))

    # Copy STEP geometry to output (required artifact)
    step_in = input_dir / "geometry.step"
    part_out = output_dir / "part.step"
    # Remove any existing part.step (may be read‑only from a previous run)
    if part_out.exists():
        part_out.unlink()
    shutil.copy(step_in, part_out)
    logging.info("Copied STEP file to %s", part_out)

    pressure = 1.98728  # N/mm^2 (downward)

    # Mesh sizes for convergence study (coarse and refined)
    mesh_sizes = [9.0, 6.0]
    refinements: List[Dict] = []
    final_results = None

    for i, clmax in enumerate(mesh_sizes, start=1):
        mesh_file = output_dir / f"mesh_{clmax:g}.msh"
        run_gmsh(step_in, mesh_file, clmax)
        logging.info("Generated mesh %s with clmax=%.2f", mesh_file.name, clmax)
        seat_mean, max_disp, points, displacements = solve_analysis(mesh_file, pressure)
        logging.info("Results for clmax=%.2f: seat_mean=%.6e mm, max_disp=%.6e mm", clmax, seat_mean, max_disp)
        refinements.append({
            "mesh_size_mm": clmax,
            "num_nodes": int(points.shape[0]),
            "num_elements": int(meshio.read(str(mesh_file)).cells_dict["tetra"].shape[0]),
            "seat_mean_displacement_mm": float(seat_mean),
            "max_displacement_mm": float(max_disp),
        })
        # Keep data from the finest mesh for the main artefacts
        if i == len(mesh_sizes):
            final_results = (seat_mean, max_disp, points, displacements)
            # Save the refined mesh as mesh.msh (required name)
            shutil.copy(mesh_file, output_dir / "mesh.msh")
            # Write fields, results and supporting files
            write_fields_npz(output_dir / "fields.npz", points, displacements)
            write_results_json(output_dir / "results.json", seat_mean, max_disp)
            write_refinement_json(output_dir / "refinement.json", refinements)
            write_environment_json(output_dir / "environment.json")

    if final_results is None:
        raise RuntimeError("Analysis failed – no results produced")

if __name__ == "__main__":
    main()
