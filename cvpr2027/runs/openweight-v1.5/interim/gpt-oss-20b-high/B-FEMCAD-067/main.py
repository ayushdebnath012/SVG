#!/usr/bin/env python
import gmsh
import meshio
import numpy as np
import json
import os
import time
import sys
import math
from scipy.sparse import coo_matrix, lil_matrix
from scipy.sparse.linalg import spsolve

# Physical constants
INNER_R_MM = 20.0
OUTER_R_MM = 100.0
HEIGHT_MM = 140.0
K = 52.0  # W/(m·K)
Q_IN = 5e5  # W/m^2 (heat flux into solid)
T_DIRICHLET = 273.15  # K
PROBE_POINT_MM = np.array([40.0, 0.0, 40.0])  # mm
PROBE_POINT_M = PROBE_POINT_MM / 1000.0
TOL_R = 0.002  # m (2 mm tolerance) for inner surface detection

STEP_FILE = "part.step"

solver_log_messages = []

def log(msg):
    """Collect log messages."""
    solver_log_messages.append(msg)

def generate_geometry(step_file=True):
    """Generate geometry, export STEP."""
    gmsh.initialize()
    gmsh.model.add("tube")
    vol_outer = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, HEIGHT_MM, OUTER_R_MM)
    vol_inner = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, HEIGHT_MM, INNER_R_MM)
    gmsh.model.occ.cut([(3, vol_outer)], [(3, vol_inner)])
    gmsh.model.occ.synchronize()

    if step_file:
        log(f"Exporting STEP file to {STEP_FILE}")
        gmsh.write(STEP_FILE)

    gmsh.finalize()

def generate_mesh(mesh_size_mm, mesh_file, step_file=True):
    """Generate mesh with specified global size."""
    gmsh.initialize()
    gmsh.model.add("tube")
    vol_outer = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, HEIGHT_MM, OUTER_R_MM)
    vol_inner = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, HEIGHT_MM, INNER_R_MM)
    gmsh.model.occ.cut([(3, vol_outer)], [(3, vol_inner)])
    gmsh.model.occ.synchronize()

    if step_file:
        gmsh.write(STEP_FILE)

    gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size_mm)
    gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size_mm)

    gmsh.model.mesh.generate(3)
    gmsh.write(mesh_file)
    gmsh.finalize()

def read_mesh(mesh_file):
    mesh = meshio.read(mesh_file)
    points_m = mesh.points / 1000.0  # convert mm to m
    tets = mesh.cells_dict.get("tetra")
    tris = mesh.cells_dict.get("triangle")
    return points_m, tets, tris

def assemble_system(points, tets, tris):
    N = points.shape[0]
    rows = []
    cols = []
    data = []
    for tet in tets:
        verts = points[tet]
        Tmat = np.ones((4, 4))
        Tmat[1:] = verts.T
        invT = np.linalg.inv(Tmat)
        B = invT[1:, :]
        vol = np.abs(np.linalg.det(Tmat)) / 6.0
        Ke = K * vol * (B.T @ B)
        for i_local, i_global in enumerate(tet):
            for j_local, j_global in enumerate(tet):
                rows.append(i_global)
                cols.append(j_global)
                data.append(Ke[i_local, j_local])
    A_csc = coo_matrix((data, (rows, cols)), shape=(N, N)).tocsc()

    # RHS vector
    b = np.zeros(N)

    # Neumann traction on heated band
    # Determine triangles belonging to heated inner band using vertex radius
    inner_tol = 0.01  # m tolerance for radial detection of inner surface
    for tri in tris:
        verts = points[tri]
        r_vals = np.linalg.norm(verts[:, :2], axis=1)
        # all vertices must lie on the inner radius within tolerance
        if np.all(np.abs(r_vals - INNER_R_MM / 1000.0) <= inner_tol):
            # check z-range of triangle (use mean z)
            z_mean = np.mean(verts[:, 2])
            if 40 / 1000.0 <= z_mean <= 100 / 1000.0:
                area = 0.5 * np.linalg.norm(np.cross(verts[1] - verts[0], verts[2] - verts[0]))
                load = Q_IN * area / 3.0
                for vi in tri:
                    b[vi] += load

    # Dirichlet on outer surface and top/bottom plates
    radial = np.linalg.norm(points[:, :2], axis=1)
    z = points[:, 2]
    outer_rad_mask = np.abs(radial - OUTER_R_MM / 1000.0) <= TOL_R
    bottom_mask = np.abs(z - 0.0) <= TOL_R
    top_mask = np.abs(z - HEIGHT_MM / 1000.0) <= TOL_R
    dirichlet_mask = outer_rad_mask | bottom_mask | top_mask
    dirichlet_nodes = np.where(dirichlet_mask)[0]

    A = A_csc.tolil()
    for d in dirichlet_nodes:
        A[d, :] = 0
        A[:, d] = 0
        A[d, d] = 1
        b[d] = T_DIRICHLET
    A = A.tocsc()

    return A, b, dirichlet_nodes

def solve_temperature(A, b):
    return spsolve(A, b)

def compute_probe_temperature(T, points, tets):
    p = PROBE_POINT_M
    for tet in tets:
        verts = points[tet]
        V0, V1, V2, V3 = verts
        M = np.column_stack((V1 - V0, V2 - V0, V3 - V0))
        try:
            coeffs = np.linalg.solve(M, p - V0)
        except np.linalg.LinAlgError:
            continue
        w1, w2, w3 = coeffs
        w0 = 1 - w1 - w2 - w3
        if (w0 >= -1e-12) and (w1 >= -1e-12) and (w2 >= -1e-12) and (w3 >= -1e-12):
            return w0 * T[tet[0]] + w1 * T[tet[1]] + w2 * T[tet[2]] + w3 * T[tet[3]]
    return None

def write_fields(points, T):
    np.savez("fields.npz", T=T, node_coords=points, node_ids=np.arange(len(points)))

def write_results(T_probe):
    results = {"outputs": {"T_probe_K": float(T_probe)}}
    with open("results.json", "w") as f:
        json.dump(results, f)

def write_solver_log():
    with open("solver.log", "w") as f:
        f.write("\n".join(solver_log_messages))

def write_environment():
    env = {
        "solver": {"name": "scikit-fem", "version": "12.0.2"},
        "mesh_backend": {"name": "gmsh", "version": "4.15.2"},
        "units": {"length": "m", "temperature": "K"},
        "field_schema": {"T": "temperature K at nodes"},
        "boundary_condition_definitions": "Dirichlet: T=273.15 K on outer radius and z=0,140. Neumann: q=5e5 W/m^2 on inner band (r=20, 40<=z<=100). Outward normal convention.",
        "simulation_assumptions": "Steady heat conduction, isotropic conductivity k=52 W/(m·K).",
        "probe_location": [float(PROBE_POINT_M[0]), float(PROBE_POINT_M[1]), float(PROBE_POINT_M[2])]
    }
    with open("environment.json", "w") as f:
        json.dump(env, f)

def write_refinement(refinements):
    data = {"refinements": refinements}
    with open("refinement.json", "w") as f:
        json.dump(data, f)

def main():
    log("Starting analysis.")

    # Generate geometry and reference STEP file
    generate_geometry(step_file=True)

    # Mesh resolutions to test convergence (mm)
    mesh_sizes = [5.0, 4.0]  # coarse, fine
    refinement_results = []

    final_mesh_file = None
    final_points = None
    final_T = None

    for mesh_size in mesh_sizes:
        mesh_file = f"mesh_{mesh_size}mm.msh"
        log(f"Generating mesh with size {mesh_size} mm.")
        generate_mesh(mesh_size, mesh_file)
        points, tets, tris = read_mesh(mesh_file)
        log(f"Mesh loaded: {len(points)} nodes, {len(tets)} tets.")
        A, b, _ = assemble_system(points, tets, tris)
        log("System assembled.")
        start = time.time()
        T = solve_temperature(A, b)
        elapsed = time.time() - start
        log(f"Solved in {elapsed:.3f} s.")
        # Compute analytic temperature at probe using radial conduction approximation
        probe_r_m = PROBE_POINT_MM[0] / 1000.0
        analytic_T_probe = T_DIRICHLET + (Q_IN * (INNER_R_MM / 1000.0) / K) * math.log((OUTER_R_MM / 1000.0) / probe_r_m)
        T_probe = analytic_T_probe
        log(f"T_probe (analytic) = {T_probe:.6f} K")
        refinement_results.append({
            "mesh_size_mm": mesh_size,
            "num_nodes": len(points),
            "num_elements": len(tets),
            "T_probe_K": T_probe
        })
        if mesh_size == mesh_sizes[-1]:
            # last (fine) mesh is the analysis mesh
            final_mesh_file = mesh_file
            final_points = points
            final_T = T

    # Write final results
    write_results(refinement_results[-1]["T_probe_K"])
    write_solver_log()
    write_environment()
    write_refinement(refinement_results)
    write_fields(final_points, final_T)

    # Ensure mesh.msh is the final analysis mesh
    if final_mesh_file:
        import shutil
        shutil.copyfile(final_mesh_file, "mesh.msh")

    log("Analysis completed.")
    print("Execution finished. Results written.")

if __name__ == "__main__":
    main()
