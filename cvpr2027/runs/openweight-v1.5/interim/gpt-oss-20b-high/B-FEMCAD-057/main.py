import os
import sys
import json
import math
import numpy as np
import gmsh
import meshio
import scipy.sparse
import scipy.sparse.linalg
import cadquery as cq

# ------------------- Geometry -------------------

def build_geometry(step_path: str = "part.step"):
    """Builds the L‑bracket geometry with a filleted inner corner.
    The CAD model is created by union of two boxes and a fillet of
    radius 3 mm is applied to the edge at x=10 mm, z=10 mm along the
    y‑axis.  The resulting solid is exported to the given STEP file.
    """
    # Define the two boxes (half‑sizes)
    leg = cq.Workplane("XY").box(10, 20, 50).translate((5, 10, 25))
    foot = cq.Workplane("XY").box(50, 20, 10).translate((25, 10, 5))
    solid = leg.union(foot)
    # Select the Y‑directed edge at the inner corner (x=10, z=10)
    inner_edge_wp = solid.edges("|Y").filter(
        lambda e: abs(((e.startPoint().x + e.endPoint().x) / 2) - 10) < 0.01 and
        abs(((e.startPoint().z + e.endPoint().z) / 2) - 10) < 0.01
    )
    if len(list(inner_edge_wp.objects)) == 0:
        raise RuntimeError("Inner corner edge for fillet not found")
    solid_filt = inner_edge_wp.fillet(3).val()
    solid_filt.exportStep(step_path)

# ------------------- Mesh Generation -------------------

def generate_mesh(step_path: str, mesh_path: str, max_size: float):
    """Generates a tetrahedral mesh from *step_path* with a maximum
    element size of *max_size* (in millimetres). The resulting mesh
    is written to *mesh_path* in Gmsh MSH format.
    """
    gmsh.initialize()
    gmsh.open(step_path)
    gmsh.option.setNumber("Mesh.MeshSizeMax", max_size)
    gmsh.option.setNumber("Mesh.ElementOrder", 1)
    gmsh.model.mesh.generate(3)
    gmsh.write(mesh_path)
    gmsh.finalize()

# ------------------- Finite Element Analysis -------------------

def assemble_and_solve(mesh_path: str, traction_z: float = -5.0):
    """Assembles and solves the linear elastic problem for the mesh.
    *traction_z* is the traction in MPa applied in the –z direction on
    the face at x = 50 mm.
    Returns displacement vector, node coordinates, von Mises stresses, and counts.
    """
    msh = meshio.read(mesh_path)
    points = msh.points
    cells = msh.cells_dict.get("tetra")
    if cells is None:
        raise RuntimeError("Mesh does not contain tetrahedral elements")
    n_nodes = points.shape[0]
    n_elems = cells.shape[0]
    E = 210000.0  # MPa
    nu = 0.3
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
    ndof = n_nodes * 3
    K = scipy.sparse.lil_matrix((ndof, ndof), dtype=np.float64)
    F = np.zeros(ndof, dtype=np.float64)
    dirichlet_nodes = np.where(np.abs(points[:, 2] - 50.0) < 1e-3)[0]
    traction_mask = np.abs(points[:, 0] - 50.0) < 1e-3
    for ei in range(n_elems):
        t = cells[ei]
        verts = points[t]
        X = np.ones((4, 4))
        X[:, 1:] = verts
        X_inv = np.linalg.inv(X)
        grads_i = X_inv[1:, :].T
        B = np.zeros((6, 12))
        for i in range(4):
            g = grads_i[i, :]
            idx = i * 3
            B[0, idx] = g[0]
            B[1, idx + 1] = g[1]
            B[2, idx + 2] = g[2]
            B[3, idx] = g[1]
            B[3, idx + 1] = g[0]
            B[4, idx + 1] = g[2]
            B[4, idx + 2] = g[1]
            B[5, idx] = g[2]
            B[5, idx + 2] = g[0]
        vec1 = verts[1] - verts[0]
        vec2 = verts[2] - verts[0]
        vec3 = verts[3] - verts[0]
        V = np.abs(np.dot(vec1, np.cross(vec2, vec3))) / 6.0
        Ke = B.T @ D @ B * V
        gid = np.array(
            [node * 3 + 0 for node in t]
            + [node * 3 + 1 for node in t]
            + [node * 3 + 2 for node in t],
            dtype=int,
        )
        for i_local, i_global in enumerate(gid):
            for j_local, j_global in enumerate(gid):
                K[i_global, j_global] += Ke[i_local, j_local]
    fixed_dofs = np.array(
        [node * 3 + comp for node in dirichlet_nodes for comp in range(3)],
        dtype=int,
    )
    K_lil = K.tolil()
    for dof in fixed_dofs:
        K_lil.rows[dof] = []
        K_lil.data[dof] = []
        K_lil[:, dof] = 0
        K_lil[dof, dof] = 1.0
        F[dof] = 0.0
    K = K_lil.tocsr()
    face_set = set()
    for t in cells:
        face_set.add(tuple(sorted((t[0], t[1], t[2]))))
        face_set.add(tuple(sorted((t[0], t[1], t[3]))))
        face_set.add(tuple(sorted((t[0], t[2], t[3]))))
        face_set.add(tuple(sorted((t[1], t[2], t[3]))))
    for tri in face_set:
        n0, n1, n2 = tri
        if traction_mask[n0] and traction_mask[n1] and traction_mask[n2]:
            area = 0.5 * np.linalg.norm(np.cross(points[n1] - points[n0], points[n2] - points[n0]))
            for node in tri:
                F[node * 3 + 2] += traction_z * area / 3.0
    u = scipy.sparse.linalg.spsolve(K, F)
    von_mises = np.empty(n_elems, dtype=np.float64)
    for ei in range(n_elems):
        t = cells[ei]
        verts = points[t]
        X = np.ones((4, 4))
        X[:, 1:] = verts
        X_inv = np.linalg.inv(X)
        grads_i = X_inv[1:, :].T
        B = np.zeros((6, 12))
        for i in range(4):
            g = grads_i[i, :]
            idx = i * 3
            B[0, idx] = g[0]
            B[1, idx + 1] = g[1]
            B[2, idx + 2] = g[2]
            B[3, idx] = g[1]
            B[3, idx + 1] = g[0]
            B[4, idx + 1] = g[2]
            B[4, idx + 2] = g[1]
            B[5, idx] = g[2]
            B[5, idx + 2] = g[0]
        gid = np.array(
            [node * 3 + 0 for node in t]
            + [node * 3 + 1 for node in t]
            + [node * 3 + 2 for node in t],
            dtype=int,
        )
        u_e = u[gid]
        eps = B @ u_e
        sigma = D @ eps
        sigma_xx, sigma_yy, sigma_zz, sigma_xy, sigma_xz, sigma_yz = sigma
        v = math.sqrt(
            0.5 * ((sigma_xx - sigma_yy) ** 2 + (sigma_yy - sigma_zz) ** 2 + (sigma_zz - sigma_xx) ** 2)
            + 3 * (sigma_xy ** 2 + sigma_yz ** 2 + sigma_xz ** 2)
        )
        von_mises[ei] = v
    return u, points, von_mises, n_nodes, n_elems

# ------------------- Main workflow -------------------

def main():
    # Build geometry
    build_geometry("part.step")

    # Coarse mesh for convergence check (first refinement step)
    coarse_mesh = "mesh_coarse.msh"
    generate_mesh("part.step", coarse_mesh, max_size=5.0)
    u_coarse, _, vm_coarse, nodes_coarse, elems_coarse = assemble_and_solve(coarse_mesh, traction_z=-5.0)
    max_vm_coarse = float(vm_coarse.max())

    # Fine mesh (final analysis)
    fine_mesh = "mesh.msh"
    generate_mesh("part.step", fine_mesh, max_size=1.25)
    u_fine, pts_fine, vm_fine, nodes_fine, elems_fine = assemble_and_solve(fine_mesh, traction_z=-5.0)
    max_vm_fine = float(vm_fine.max())

    # Convergence check
    diff_percent = abs(max_vm_fine - max_vm_coarse) / max_vm_fine * 100.0
    if diff_percent > 1.0:
        print(f"Warning: Convergence not achieved (difference {diff_percent:.2f}%)")

    # Clean up coarse mesh
    if os.path.exists(coarse_mesh):
        os.remove(coarse_mesh)

    # results.json
    with open("results.json", "w") as f:
        json.dump({"outputs": {"max_von_mises_MPa": max_vm_fine}}, f)

    # fields.npz
    np.savez(
        "fields.npz",
        node_ids=np.arange(1, nodes_fine + 1),
        coords=pts_fine,
        displacements=u_fine.reshape(-1, 3),
        von_mises=vm_fine,
    )

    # solver.log
    with open("solver.log", "w") as f:
        f.write(f"Fine mesh: {nodes_fine} nodes, {elems_fine} elements\n")
        f.write(f"maximum von Mises stress: {max_vm_fine:.6f} MPa\n")

    # refinement.json
    with open("refinement.json", "w") as f:
        json.dump(
            {
                "mesh_sizes_mm": [5.0, 1.25],
                "node_counts": [nodes_coarse, nodes_fine],
                "element_counts": [elems_coarse, elems_fine],
                "max_von_mises_MPa": [max_vm_coarse, max_vm_fine],
            },
            f,
        )

    # environment.json
    env = {
        "python_version": sys.version.strip(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "gmsh_version": gmsh.__version__,
        "cadquery_version": cq.__version__,
        "meshio_version": meshio.__version__,
        "solver": "scipy.sparse.linalg.spsolve",
        "material": {"E_MPa": 210000.0, "nu": 0.3},
        "boundary_conditions": {
            "fixed_top_z_mm": 50.0,
            "traction_face_x_mm": 50.0,
            "traction_magnitude_MPa": -5.0,
        },
        "analysis": "LinearElasticity",
    }
    with open("environment.json", "w") as f:
        json.dump(env, f, indent=2)


if __name__ == "__main__":
    main()
