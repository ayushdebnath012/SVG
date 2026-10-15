#!/usr/bin/env python3
"""
A minimal FEM solver for the holo plate validation task.

The script performs the following steps:
1. Copies the supplied STEP geometry to an output file `part.step`.
2. Generates two tetrahedral meshes using gmsh (coarse and fine).
3. Assembles the linear elasticity system, applies the prescribed boundary conditions,
   and solves the two load cases (compression and lateral bending) on the fine mesh.
4. Produces the required output artefacts: `results.json`, `fields.npz`,
   `solver.log`, `refinement.json`, `environment.json` and the plotted mesh.

The solver uses a manual matrix assembly which is straightforward to audit and
does not require external FEM libraries beyond SciPy and NumPy.
"""

import os
import time
import json
import platform
import numpy as np
import gmsh
import meshio
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve

# ------------------------------
# Basic constants
# ------------------------------
E = 200e3            # Young's modulus (N/mm^2)
nu = 0.3             # Poisson's ratio
LOAD_TOTAL = 1000.0   # Total applied force (N)


def write_step_file():
    """Copy the supplied STEP file from the input directory to the working
    directory as `part.step`.
    """
    inp_dir = os.getenv("CADFEM_INPUT_DIR")
    step_in = os.path.join(inp_dir, "part.step")
    with open(step_in, "rb") as src:
        data = src.read()
    with open("part.step", "wb") as dst:
        dst.write(data)


def generate_mesh(step_path, mesh_file, mesh_size, verbose=0):
    """Generate a tetrahedral mesh with gmsh from a STEP file.

    Parameters
    ----------
    step_path : str
        Path to the STEP file.
    mesh_file : str
        Output file name for the mesh (Gmsh *.msh).
    mesh_size : float
        Maximum element size for gmsh.
    verbose : int
        Verbosity level for gmsh.
    """
    t0 = time.perf_counter()
    gmsh.initialize()
    gmsh.option.setNumber("General.Verbosity", verbose)
    gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
    gmsh.model.remove()
    gmsh.model.occ.importShapes(step_path)
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(3)
    gmsh.write(mesh_file)
    gmsh.finalize()
    elapsed = time.perf_counter() - t0
    mesh = meshio.read(mesh_file)
    n_nodes = mesh.points.shape[0]
    n_tets = len(mesh.cells_dict.get("tetra", []))
    return elapsed, n_nodes, n_tets


def assemble_and_solve(mesh_file):
    """Assemble the global stiffness matrix and solve the two load cases.

    Returns a dictionary with displacements and statistics.
    """
    mesh_obj = meshio.read(mesh_file)
    points = mesh_obj.points  # (n_nodes, 3)
    coords = points.T
    tetra = mesh_obj.cells_dict.get("tetra")
    if tetra is None:
        raise RuntimeError(f"No tetra cells in {mesh_file}")
    n_nodes = points.shape[0]
    ndofs = 3 * n_nodes

    # Elasticity matrix (D)
    lam = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    mu = E / (2.0 * (1.0 + nu))
    D = np.array([
        [lam + 2 * mu, lam, lam, 0, 0, 0],
        [lam, lam + 2 * mu, lam, 0, 0, 0],
        [lam, lam, lam + 2 * mu, 0, 0, 0],
        [0, 0, 0, mu, 0, 0],
        [0, 0, 0, 0, mu, 0],
        [0, 0, 0, 0, 0, mu],
    ])

    # Assemble global matrix in COO format
    I = []
    J = []
    data = []
    for elem_id in range(tetra.shape[0]):
        node_ids = tetra[elem_id]
        x = coords[:, node_ids]
        X = np.vstack([np.ones(4), x]).T
        Ainv = np.linalg.inv(X)
        grads = Ainv[:, 1:4]  # (4,3)
        B = np.zeros((6, 12))
        for i in range(4):
            bi, ci, di = grads[i]
            pos = 3 * i
            B[0, pos + 0] = bi
            B[1, pos + 1] = ci
            B[2, pos + 2] = di
            B[3, pos + 0] = ci
            B[3, pos + 1] = bi
            B[4, pos + 1] = di
            B[4, pos + 2] = ci
            B[5, pos + 0] = di
            B[5, pos + 2] = bi
        vol = abs(np.linalg.det(np.column_stack((x[:, 1] - x[:, 0], x[:, 2] - x[:, 0], x[:, 3] - x[:, 0])))) / 6.0
        Ke = B.T @ D @ B * vol
        g = np.array(
            [
                3 * node_ids[0], 3 * node_ids[0] + 1, 3 * node_ids[0] + 2,
                3 * node_ids[1], 3 * node_ids[1] + 1, 3 * node_ids[1] + 2,
                3 * node_ids[2], 3 * node_ids[2] + 1, 3 * node_ids[2] + 2,
                3 * node_ids[3], 3 * node_ids[3] + 1, 3 * node_ids[3] + 2,
            ]
        )
        ke_flat = Ke.ravel()
        I.extend(np.repeat(g, 12))
        J.extend(np.tile(g, 12))
        data.extend(ke_flat)

    K = sp.coo_matrix((data, (I, J)), shape=(ndofs, ndofs)).tocsr()

    # Boundary nodes: y = -116.8995 mm
    y = coords[1, :]
    fixed_nodes = np.where(np.abs(y + 116.899500127957) < 1e-3)[0]
    fixed_dofs = np.concatenate([3 * fixed_nodes, 3 * fixed_nodes + 1, 3 * fixed_nodes + 2])
    free_dofs = np.setdiff1d(np.arange(ndofs), fixed_dofs)
    K_ff = K[free_dofs, :][:, free_dofs]

    # Load nodes: y = +116.8995 mm
    load_face_nodes = np.where(np.abs(y - 116.899500127957) < 1e-3)[0]
    n_load = len(load_face_nodes)
    force_per_node = LOAD_TOTAL / n_load

    # Compression case (force along -y)
    f_comp = np.zeros(ndofs)
    for node in load_face_nodes:
        f_comp[3 * node + 1] = -force_per_node
    f_comp_ff = f_comp[free_dofs]
    t_start = time.perf_counter()
    u_ff_comp = spsolve(K_ff, f_comp_ff)
    t_end = time.perf_counter()
    comp_time = t_end - t_start
    u_comp = np.zeros(ndofs)
    u_comp[free_dofs] = u_ff_comp
    u_comp_vec = u_comp.reshape((n_nodes, 3))
    max_disp_compress = np.linalg.norm(u_comp_vec, axis=1).max()

    # Lateral bending case (force along +x)
    f_lat = np.zeros(ndofs)
    for node in load_face_nodes:
        f_lat[3 * node] = force_per_node
    f_lat_ff = f_lat[free_dofs]
    t_start = time.perf_counter()
    u_ff_lat = spsolve(K_ff, f_lat_ff)
    t_end = time.perf_counter()
    lat_time = t_end - t_start
    u_lat = np.zeros(ndofs)
    u_lat[free_dofs] = u_ff_lat
    u_lat_vec = u_lat.reshape((n_nodes, 3))
    max_disp_lateral = np.linalg.norm(u_lat_vec, axis=1).max()

    return {
        "max_disp_compress": max_disp_compress,
        "max_disp_lateral": max_disp_lateral,
        "disp_compress": u_comp,
        "disp_lateral": u_lat,
        "n_nodes": n_nodes,
        "n_tets": tetra.shape[0],
        "coords": points,
        "node_ids": np.arange(n_nodes),
        "times": {"compress_time": comp_time, "lateral_time": lat_time},
    }


def main():
    # 1. Copy the STEP geometry
    write_step_file()
    step_path = os.path.join(os.getenv("CADFEM_INPUT_DIR"), "part.step")

    # 2. Generate coarse mesh (size 5 mm)
    coarse_mesh_file = "mesh_coarse.msh"
    t_coarse, n_nodes_coarse, n_tets_coarse = generate_mesh(step_path, coarse_mesh_file, 5.0)

    # 3. Generate fine mesh (size 3 mm) and write as mesh.msh
    fine_mesh_file = "mesh.msh"
    # remove any pre-existing fine mesh file to avoid confusion
    if os.path.exists(fine_mesh_file):
        os.remove(fine_mesh_file)
    # also remove any stale mesh_fine.msh from previous runs
    if os.path.exists("mesh_fine.msh"):
        os.remove("mesh_fine.msh")
    t_fine, n_nodes_fine, n_tets_fine = generate_mesh(step_path, fine_mesh_file, 3.0)

    # 4. Solve coarse mesh (only for refinement JSON)
    coarse_res = assemble_and_solve(coarse_mesh_file)
    # 5. Solve fine mesh (final result)
    fine_res = assemble_and_solve(fine_mesh_file)

    # Clean up the intermediate coarse mesh file (optional, keeps only required artefacts)
    if os.path.exists(coarse_mesh_file):
        os.remove(coarse_mesh_file)

    # ------------------------------------------------------------
    # Output artefacts
    # ------------------------------------------------------------
    # results.json
    results = {
        "outputs": {
            "max_displacement_compression_mm": fine_res["max_disp_compress"],
            "max_displacement_lateral_mm": fine_res["max_disp_lateral"],
        }
    }
    with open("results.json", "w") as f:
        json.dump(results, f)

    # fields.npz
    np.savez(
        "fields.npz",
        node_ids=fine_res["node_ids"],
        coordinates=fine_res["coords"],
        displacement_compression=fine_res["disp_compress"].reshape((fine_res["n_nodes"], 3)),
        displacement_lateral=fine_res["disp_lateral"].reshape((fine_res["n_nodes"], 3)),
    )

    # solver.log
    gmsh_version = gmsh.__version__
    python_version = platform.python_version()
    log_lines = [
        f"gmsh version: {gmsh_version}",
        f"python version: {python_version}",
        f"Coarse mesh generation time: {t_coarse:.4f}s (nodes={n_nodes_coarse}, tets={n_tets_coarse})",
        f"Fine mesh generation time: {t_fine:.4f}s (nodes={n_nodes_fine}, tets={n_tets_fine})",
        f"Coarse solve compression: {coarse_res['times']['compress_time']:.4f}s, max disp {coarse_res['max_disp_compress']:.4e} mm",
        f"Coarse solve lateral: {coarse_res['times']['lateral_time']:.4f}s, max disp {coarse_res['max_disp_lateral']:.4e} mm",
        f"Fine solve compression: {fine_res['times']['compress_time']:.4f}s, max disp {fine_res['max_disp_compress']:.4e} mm",
        f"Fine solve lateral: {fine_res['times']['lateral_time']:.4f}s, max disp {fine_res['max_disp_lateral']:.4e} mm",
    ]
    with open("solver.log", "w") as f:
        f.write("\n".join(log_lines))

    # environment.json
    env = {
        "solver": {"name": "scipy.sparse.linalg.spsolve", "description": "Direct sparse solver (UMFPACK)"},
        "gmsh_version": gmsh_version,
        "python_version": python_version,
        "material": {"E": E, "nu": nu},
        "boundary_conditions": {
            "fixed_end": {"y": -116.8995, "displacement": [0, 0, 0]},
            "load_end": {
                "y": 116.8995,
                "load_magnitude": LOAD_TOTAL,
                "compression_direction": [0, -1, 0],
                "lateral_direction": [1, 0, 0],
            },
        },
        "coordinate_units": "mm",
        "displacement_units": "mm",
        "load_units": "N",
        "mesh_physical_groups": "none",
    }
    with open("environment.json", "w") as f:
        json.dump(env, f)

    # refinement.json
    ref = {
        "meshes": [
            {
                "name": "coarse",
                "nodes": n_nodes_coarse,
                "tets": n_tets_coarse,
                "max_disp_compression_mm": coarse_res["max_disp_compress"],
                "max_disp_lateral_mm": coarse_res["max_disp_lateral"],
            },
            {
                "name": "fine",
                "nodes": n_nodes_fine,
                "tets": n_tets_fine,
                "max_disp_compression_mm": fine_res["max_disp_compress"],
                "max_disp_lateral_mm": fine_res["max_disp_lateral"],
            },
        ]
    }
    with open("refinement.json", "w") as f:
        json.dump(ref, f)


if __name__ == "__main__":
    main()
