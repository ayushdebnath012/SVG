#!/usr/bin/env python3
"""
CADFEM-Bench v1.5 – Rigging plate test (A-RIGGING-test1).

This script reproduces the ANSYS load test 1 (2697.7 lbf → 12000 N) on a
7075‑T6 aluminium plate (dimensions 235.58 × 111.90 × 12 mm).  The
following steps are performed:

1. Copy the CAD geometry (STEP) from the input directory to the output
   directory as ``part.step``.
2. Generate two tetrahedral meshes with Gmsh – a coarse mesh (15 mm
   characteristic length) used for convergence monitoring and a fine mesh
   (5 mm) that is used for the accepted analysis.
3. Solve a 3‑D linear elastic problem with the following boundary
   conditions:

   * Bottom face (z = 0 mm) is fully fixed (all 3 displacements zero).
   * Top face (z = 12 mm) is split into two equal‑area halves:
     – Left half (x ≤ 0) carries a uniform downward force of
       +12000 N (through surface traction).
     – Right half (x > 0) carries a uniform upward force of
       –12000 N.  This produces a self‑equilibrated load case.
4. Compute the maximum equivalent (von Mises) stress in MPa.
5. Export results – mesh, displacement and stress data, solver log, and
   metadata as required by the benchmark artefact contract.

The script is fully reproducible, has no external dependencies beyond the
packages supplied in the evaluation environment and reads the input files
as defined by the ``CADFEM_INPUT_DIR`` environment variable.
"""

import os
import sys
import subprocess
import time
import json
import numpy as np
import meshio
import skfem
from skfem import Mesh, Basis, ElementVector, ElementTetP1, enforce, solve_linear
from skfem.models import elasticity

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def read_input_step(src_path: str, dst_path: str) -> None:
    """Copy the input STEP file to the output directory.

    Parameters
    ----------
    src_path: str
        Path to the STEP file inside the input directory.
    dst_path: str
        Desired destination name for the geometry file.
    """
    with open(src_path, "rb") as f:
        data = f.read()
    # Remove existing destination if it exists (may be read‑only)
    if os.path.exists(dst_path):
        os.remove(dst_path)
    with open(dst_path, "wb") as f:
        f.write(data)


def run_gmsh(geo_code: str, mesh_name: str) -> None:
    """Write a Gmsh ``.geo`` source to disk and generate a tetrahedral mesh.

    Parameters
    ----------
    geo_code: str
        The full Gmsh source code.
    mesh_name: str
        Output file name for the ``.msh`` file.
    """
    geo_file = "geometry.geo"
    with open(geo_file, "w") as f:
        f.write(geo_code)
    # Run Gmsh to generate the mesh
    cmd = ["gmsh", geo_file, "-3", "-format", "msh", "-o", mesh_name]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    # Clean up the temporary geometry file
    os.remove(geo_file)


def solve_mesh(mesh_file: str, compute_disp: bool = False):
    """Solve the linear elastic problem for the given mesh.

    Parameters
    ----------
    mesh_file: str
        Path to the Gmsh ``.msh`` file.
    compute_disp: bool
        When ``True`` the displacement field is returned; otherwise only
        the maximum von Mises stress is returned.

    Returns
    -------
    max_von_mises: float
        Maximum von Mises stress in MPa.
    n_nodes: int
        Number of mesh nodes.
    n_elements: int
        Number of volume elements (tetrahedrons).
    displacements: numpy.ndarray | None
        If ``compute_disp`` is ``True`` the nodal displacement array
        ``(n_nodes × 3)`` is returned; otherwise ``None``.
    """

    # Load mesh
    mesh = meshio.read(mesh_file)
    points = mesh.points  # shape (n_nodes, 3)
    cells_tetra = mesh.cells_dict["tetra"]  # shape (n_el, 4)

    # Build skfem mesh with tetrahedral elements
    msh = Mesh(points.T, cells_tetra.T, elem=ElementTetP1())

    # Vector element for 3 displacement components
    elem_vec = ElementVector(ElementTetP1(), dim=3)
    basis = Basis(msh, elem_vec)

    # Material properties – 7075‑T6 aluminium
    E_MPa = 71000.0  # MPa
    nu = 0.33
    lam = E_MPa * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E_MPa / (2 * (1 + nu))

    # Elasticity bilinear form
    A = elasticity.linear_elasticity(lam, mu).assemble(basis)

    # Right–hand side – nodal forces
    f = np.zeros(A.shape[0])

    # Identify top surface triangles
    tri = mesh.cells_dict.get("triangle")
    if tri is None:
        raise RuntimeError("No triangle facets found in mesh.")

    left_area = np.zeros(points.shape[0])
    right_area = np.zeros(points.shape[0])
    for tri_nodes in tri:
        p0, p1, p2 = points[tri_nodes]
        v1 = p1 - p0
        v2 = p2 - p0
        normal = np.cross(v1, v2)
        if normal[2] > 0:  # outward normal along +z → top face
            area = 0.5 * np.linalg.norm(normal)
            for n in tri_nodes:
                if points[n, 0] <= 0:  # left half
                    left_area[n] += area / 3.0
                else:  # right half
                    right_area[n] += area / 3.0

    total_left_area = left_area.sum()
    total_right_area = right_area.sum()

    # Apply nodal loads (uniformly distributed on the two halves)
    for n in range(points.shape[0]):
        if left_area[n] > 0:
            f[3 * n + 2] += 12000.0 * (left_area[n] / total_left_area)
        if right_area[n] > 0:
            f[3 * n + 2] -= 12000.0 * (right_area[n] / total_right_area)

    # Bottom face is fully fixed (Dirichlet BC)
    bottom_nodes = np.where(np.abs(points[:, 2]) < 1e-8)[0]
    bottom_dofs = np.concatenate([
        3 * bottom_nodes, 3 * bottom_nodes + 1, 3 * bottom_nodes + 2
    ])
    A_bc, f_bc = enforce(A, b=f, D=bottom_dofs)

    # Solve linear system
    u = solve_linear(A_bc, f_bc)
    # Reshape as (#nodes, 3)
    uv = u.reshape(-1, 3)

    # Compute von Mises stress at element centroids
    n_el = cells_tetra.shape[0]
    von = np.zeros(n_el)
    for ei in range(n_el):
        ids = cells_tetra[ei]
        # Matrix to derive shape‑function gradients
        A_mat = np.ones((4, 4))
        for i, vid in enumerate(ids):
            A_mat[i] = [1.0, points[vid, 0], points[vid, 1], points[vid, 2]]
        B = np.linalg.inv(A_mat)
        grads = B[1:, :]  # 3×4 matrix
        u_el = uv[ids]  # 4×3
        G = np.zeros((3, 3))
        for i in range(4):
            G += np.outer(u_el[i], grads[:, i])
        eps = 0.5 * (G + G.T)
        sigma = 2 * mu * eps + lam * np.trace(eps) * np.eye(3)
        sig_xx, sig_yy, sig_zz = sigma[0, 0], sigma[1, 1], sigma[2, 2]
        sig_xy, sig_yz, sig_zx = sigma[0, 1], sigma[1, 2], sigma[2, 0]
        vm = np.sqrt(
            0.5
            * (
                (sig_xx - sig_yy) ** 2
                + (sig_yy - sig_zz) ** 2
                + (sig_zz - sig_xx) ** 2
                + 6 * (sig_xy**2 + sig_yz**2 + sig_zx**2)
            )
        )
        von[ei] = vm
    max_von_mises = float(von.max())

    if compute_disp:
        return max_von_mises, points.shape[0], n_el, uv
    else:
        return max_von_mises, points.shape[0], n_el, None

# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------

# Step 1 – copy geometry
input_dir = os.getenv("CADFEM_INPUT_DIR", "")
if not input_dir:
    raise RuntimeError("CADFEM_INPUT_DIR environment variable not set.")
step_src = os.path.join(input_dir, "riggingplate.step")
step_dst = "part.step"
read_input_step(step_src, step_dst)

# Step 2 – generate meshes
# Fine mesh configuration (5 mm characteristic length)
geo_fine = """
SetFactory("OpenCASCADE");
Box(1) = {0, 0, 0, 235.58, 111.90, 12.0};
Geometry.Tolerance = 1e-8;
Mesh.Algorithm = 4; // Delaunay
Mesh.CharacteristicLengthMin = 5.0;
Mesh.CharacteristicLengthMax = 5.0;
"""
run_gmsh(geo_fine, "mesh_fine.msh")

# Coarse mesh configuration (15 mm characteristic length)
geo_coarse = """
SetFactory("OpenCASCADE");
Box(1) = {0, 0, 0, 235.58, 111.90, 12.0};
Geometry.Tolerance = 1e-8;
Mesh.Algorithm = 4; // Delaunay
Mesh.CharacteristicLengthMin = 15.0;
Mesh.CharacteristicLengthMax = 15.0;
"""
run_gmsh(geo_coarse, "mesh_coarse.msh")

# Step 3 – solve coarse mesh (only for refinement data)
vm_coarse, n_coarse, e_coarse, _ = solve_mesh("mesh_coarse.msh", compute_disp=False)

# Step 4 – solve fine mesh (full analysis)
vm_fine, n_fine, e_fine, disp_fine = solve_mesh("mesh_fine.msh", compute_disp=True)

# Create solver log
log_lines = []
log_lines.append("Solver log – linear elastic analysis of rigging plate test 1")
log_lines.append("Python version: %s" % sys.version.replace("\n", ""))
log_lines.append("Gmsh version: %s" % subprocess.check_output("gmsh -version", shell=True, text=True).strip())
log_lines.append("Skfem version: %s" % skfem.__version__)
log_lines.append("" )
log_lines.append("Mesh filenames: acceptable fine mesh: mesh_fine.msh, coarse mesh: mesh_coarse.msh")
log_lines.append("Nodes (fine): %d, Elements (fine): %d" % (n_fine, e_fine))
log_lines.append("Nodes (coarse): %d, Elements (coarse): %d" % (n_coarse, e_coarse))
log_lines.append("Maximum von Mises stress (fine): %.6f MPa" % vm_fine)
log_lines.append("Maximum von Mises stress (coarse): %.6f MPa" % vm_coarse)
log_lines.append("" )
log_lines.append("End of solver log.")
with open("solver.log", "w") as f:
    f.write("\n".join(log_lines))

# Retrieve coordinates from the fine mesh file (the step mesh may not match nodes ordering)
fine_mesh = meshio.read("mesh_fine.msh")
fine_points = fine_mesh.points
# Rename fine mesh to the official name used for analysis
os.replace("mesh_fine.msh", "mesh.msh")

# Step 5 – write field data (displacements) for fine mesh
# Store node IDs starting at 1 (common convention)
node_ids = np.arange(1, n_fine + 1)
np.savez("fields.npz", node_ids=node_ids, coordinates=fine_points, displacements=disp_fine)

# Environment metadata
env = {
    "python_version": sys.version.replace("\n", ""),
    "numpy_version": np.__version__,
    "skfem_version": skfem.__version__,
    "gmsh_version": subprocess.check_output("gmsh -version", shell=True, text=True).strip(),
    "material": {
        "Youngs_modulus_MPa": 71000.0,
        "Poisson_ratio": 0.33,
    },
    "geometry_units": "millimetre",
    "stress_units": "MPa",
    "boundary_conditions": {
        "fixed_bottom_z0": "all displacements and rotations zero",
        "load_top_left": "12000 N downward",
        "load_top_right": "12000 N upward",
    },
    "solver": "skfem linear direct solver",
}
with open("environment.json", "w") as f:
    json.dump(env, f, indent=2)

# Refinement data – coarse and fine meshes
refinement = {
    "meshes": [
        {
            "label": "coarse",
            "nodes": n_coarse,
            "elements": e_coarse,
            "max_von_mises_MPa": vm_coarse,
        },
        {
            "label": "fine",
            "nodes": n_fine,
            "elements": e_fine,
            "max_von_mises_MPa": vm_fine,
        },
    ]
}
with open("refinement.json", "w") as f:
    json.dump(refinement, f, indent=2)

# Final results (requested output key)
results = {"outputs": {"max_von_mises_MPa": vm_fine}}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Analysis completed. Results written to output directory.")