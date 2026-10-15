#!/usr/bin/env python3
"""
Finite element elastic buckling analysis for fcVM buckling_U100_3D.

The script reads the geometry from ``inputs/analysis.step`` and the face
information from ``inputs/faces.json``.  Two meshes are generated with
Gmsh: a coarse mesh for convergence reporting and a fine mesh that is
used for the final solution.  The fine mesh is written to ``mesh.msh``.

The analysis performs the following steps for each mesh:
1. Generate the mesh with a global element size.
2. Extract node coordinates, tetrahedral element connectivity and
   surface information from the Gmsh Python API.
3. Assemble the linear elastic stiffness matrix ``K`` and the force
   vector ``f`` including:
   - Body force (self‑weight).
   - Distributed traction on the top face (face 10 in the input data).
4. Apply a full Dirichlet condition on the bottom face (face 11).
5. Solve the linear system ``K*u = f`` to obtain the pre‑buckling
   displacement field.
6. Compute the element stress field.
7. Assemble the geometric stiffness matrix ``K_G`` from the stress
   field.
8. Solve the generalized eigenvalue problem ``K*u = λ*(-K_G)*u`` to
   obtain the buckling eigenvalues and extract the smallest positive
   one, ``lambda1``.

The script writes the following artefacts in the current working
directory (``CADFEM_OUTPUT_DIR``):

* ``results.json`` – The required output key.
* ``part.step`` – The input geometry, in the same file format.
* ``mesh.msh`` – The fine Gmsh mesh used for the analysis.
* ``fields.npz`` – Node coordinates, displacements and element stresses.
* ``solver.log`` – A text log of the run.
* ``refinement.json`` – Mesh resolution data for coarse and fine meshes.
* ``environment.json`` – Metadata about the workflow and solver.
"""

import os
import json
import shutil
import numpy as np
import scipy
import scipy.sparse as sp
import scipy.sparse.linalg as spl
import gmsh
from math import fabs

# -------------------------------------------------------------------------
# Material and load constants (all in SI except for coordinates which are
# in millimetres; all stresses and forces are expressed in MPa / N/mm²).
# -------------------------------------------------------------------------
E = 210_000.0       # Young's modulus [MPa]
nu = 0.3            # Poisson's ratio
lam = E * nu / ((1 + nu) * (1 - 2 * nu))   # Lame
mu = E / (2 * (1 + nu))                   # Lame
# Body force – density 7900 kg/m³, gravity 10 m/s².
# Convert to N/mm³: ρ g = 7900 kg/m³ * 10 m/s² = 79000 N/m³ = 7.9e-05 N/mm³
body_force = np.array([0.0, 0.0, -7.9e-05], dtype=float)
# Traction on top face (face 10) – sum of the two specified loads.
traction_top = np.array([1.656315, 0.0, -41.407867], dtype=float)
# Small tolerance for matching face centroids (in mm)
CENTROID_TOL = 1e-3

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def read_faces(json_path):
    """Read faces.json and return a dict indexed by face_index."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return {face['face_index']: face for face in data['face_descriptors']}


def element_B(coords):
    """Return the strain–displacement matrix B for a linear tetra.
    coords – (4,3) array of node coordinates in mm.
    """
    p0, p1, p2, p3 = coords
    # Derivatives of shape functions w.r.t. local coordinates
    grad_ref = np.array(
        [[-1, -1, -1],
         [1, 0, 0],
         [0, 1, 0],
         [0, 0, 1]]
    )  # shape (4,3)
    J = np.column_stack((p1 - p0, p2 - p0, p3 - p0))
    invJT = np.linalg.inv(J).T
    grads_phys = invJT @ grad_ref.T  # shape (3,4)
    # Build B 6x12
    B = np.zeros((6, 12), dtype=float)
    for i in range(4):
        g = grads_phys[:, i]
        # Primary normal strains
        B[0, 3 * i]     = g[0]  # εx
        B[1, 3 * i + 1] = g[1]  # εy
        B[2, 3 * i + 2] = g[2]  # εz
        # Engineering shear strains
        B[3, 3 * i]     = g[1]
        B[3, 3 * i + 1] = g[0]
        B[4, 3 * i + 1] = g[2]
        B[4, 3 * i + 2] = g[1]
        B[5, 3 * i]     = g[2]
        B[5, 3 * i + 2] = g[0]
    return B


def map_surface_tags(face_map, gmsh_surfaces):
    """Map Gmsh surface tags to the given face_index numbers.
    Returns a dict {surface_tag: face_index}."""
    mapping = {}
    for dim, tag in gmsh_surfaces:
        cmx, cmy, cmz = gmsh.model.occ.getCenterOfMass(2, tag)
        cm = np.array([cmx, cmy, cmz])
        for fidx, face in face_map.items():
            fcm = np.array(face['centroid_mm'])
            if np.linalg.norm(cm - fcm) < CENTROID_TOL:
                mapping[tag] = fidx
                break
    return mapping


def assemble_stiffness_and_load(node_coords, tets_idx, volumes,
                                dirichlet_nodes, top_triangles,
                                lambda_eigs=False):
    """Assemble system matrices and load vector.
    node_coords – (N,3) array, in mm.
    tets_idx    – (n_tets,4) array of node indices.
    volumes     – (n_tets,) array of tetra volumes in mm³.
    dirichlet_nodes – set/list of node indices (zero‑based) for which all DOFs are fixed.
    top_triangles  – list of tuples (n1, n2, n3) with node indices (zero‑based) of each triangle.
    Returns K (CSR), f (array), and an array of element stresses (will be computed later)."""
    n_nodes = node_coords.shape[0]
    n_dofs = 3 * n_nodes
    # Material matrix C (6x6)
    C = np.array([
        [lam + 2 * mu, lam, lam, 0, 0, 0],
        [lam, lam + 2 * mu, lam, 0, 0, 0],
        [lam, lam, lam + 2 * mu, 0, 0, 0],
        [0, 0, 0, mu, 0, 0],
        [0, 0, 0, 0, mu, 0],
        [0, 0, 0, 0, 0, mu]
    ], dtype=float)
    # Prepare arrays for COO assembly
    rows, cols, data = [], [], []
    f = np.zeros(n_dofs, dtype=float)
    # body force contribution
    for ei in range(tets_idx.shape[0]):
        ndx = tets_idx[ei]
        vol = volumes[ei]
        # Body force per node (lin‑interpolated)
        f_local = body_force * vol / 4.0
        for local_i, node in enumerate(ndx):
            dof_start = 3 * node
            f[dof_start:dof_start+3] += f_local
    # traction on top surface
    if top_triangles:
        for (n1, n2, n3) in top_triangles:
            p1, p2, p3 = node_coords[n1], node_coords[n2], node_coords[n3]
            area = 0.5 * np.linalg.norm(np.cross(p2 - p1, p3 - p1))
            f_tri = traction_top * area / 3.0
            for n in (n1, n2, n3):
                dof_start = 3 * n
                f[dof_start:dof_start+3] += f_tri
    # Dirichlet nodes: enforce zero displacement (already zero in f)
    dirichlet_dofs = []
    for nd in dirichlet_nodes:
        dirichlet_dofs.extend([3 * nd, 3 * nd + 1, 3 * nd + 2])
    # assemble stiffness matrix
    for ei in range(tets_idx.shape[0]):
        ndx = tets_idx[ei]
        vol = volumes[ei]
        coords_elem = node_coords[ndx]
        B = element_B(coords_elem)
        K_e = vol * (B.T @ C @ B)
        # Map local DOFs to global indices
        elem_dofs = np.empty(12, dtype=int)
        for local_i, node in enumerate(ndx):
            elem_dofs[3 * local_i]     = 3 * node
            elem_dofs[3 * local_i + 1] = 3 * node + 1
            elem_dofs[3 * local_i + 2] = 3 * node + 2
        for i_l, ii in enumerate(elem_dofs):
            for j_l, jj in enumerate(elem_dofs):
                rows.append(ii)
                cols.append(jj)
                data.append(K_e[i_l, j_l])
    K = sp.coo_matrix((data, (rows, cols)), shape=(n_dofs, n_dofs)).tocsr()
    return K, f, dirichlet_dofs


def assemble_geometric_stiffness(node_coords, tets_idx, volumes,
                                 stresses, dirichlet_dofs):
    """Assemble geometric stiffness matrix K_G.
    node_coords – (N,3) array.
    tets_idx    – (n_tets,4) array of node indices.
    volumes     – (n_tets,) volumes.
    stresses    – (n_tets,6) stress vectors ([σxx,σyy,σzz,τxy,τyz,τzx]).
    Returns sparse CSR matrix K_G."""
    n_nodes = node_coords.shape[0]
    n_dofs = 3 * n_nodes
    # Pre‑compute element local DOFs matrix
    elem_local_dofs = np.empty((tets_idx.shape[0], 12), dtype=int)
    for ei in range(tets_idx.shape[0]):
        ndx = tets_idx[ei]
        for local_i, node in enumerate(ndx):
            elem_local_dofs[ei, 3 * local_i]     = 3 * node
            elem_local_dofs[ei, 3 * local_i + 1] = 3 * node + 1
            elem_local_dofs[ei, 3 * local_i + 2] = 3 * node + 2
    rows, cols, data = [], [], []
    for ei in range(tets_idx.shape[0]):
        ndx = tets_idx[ei]
        vol = volumes[ei]
        sigma = stresses[ei]
        # Construct stress matrix for geometric stiffness
        S = np.zeros((6, 6))
        S[0, 0] = sigma[0]
        S[1, 1] = sigma[1]
        S[2, 2] = sigma[2]
        S[3, 3] = sigma[1] + sigma[2]
        S[4, 4] = sigma[0] + sigma[2]
        S[5, 5] = sigma[0] + sigma[1]
        # Compute local geometric stiffness
        coords_elem = node_coords[ndx]
        B = element_B(coords_elem)
        K_e_g = vol * (B.T @ S @ B)
        elem_dofs = elem_local_dofs[ei]
        for i_l, ii in enumerate(elem_dofs):
            for j_l, jj in enumerate(elem_dofs):
                rows.append(ii)
                cols.append(jj)
                data.append(K_e_g[i_l, j_l])
    K_G = sp.coo_matrix((data, (rows, cols)), shape=(n_dofs, n_dofs)).tocsr()
    return K_G


# -------------------------------------------------------------------------
# Main workflow
# -------------------------------------------------------------------------

if __name__ == "__main__":
    # Determine input and output directories
    CADFEM_INPUT_DIR = os.getenv('CADFEM_INPUT_DIR')
    if CADFEM_INPUT_DIR is None:
        raise RuntimeError("CADFEM_INPUT_DIR not set")
    step_input_path = os.path.join(CADFEM_INPUT_DIR, 'analysis.step')
    faces_path = os.path.join(CADFEM_INPUT_DIR, 'faces.json')

    # Read face descriptors
    face_map = read_faces(faces_path)

    # Mesh sizes for coarse and fine meshes (mm)
    mesh_specs = [
        ("coarse", 250.0),  # coarse mesh size
        ("fine", 50.0)      # fine mesh size
    ]

    refinement = {}
    fields = None
    lambda1_fine = None

    for label, mesh_size in mesh_specs:
        gmsh.initialize()
        gmsh.option.setNumber('General.Terminal', 0)
        gmsh.open(step_input_path)
        gmsh.model.occ.synchronize()
        # Add physical volume
        vol_entities = gmsh.model.occ.getEntities(3)
        if not vol_entities:
            raise RuntimeError("No 3D volume found in geometry")
        vol_tag = vol_entities[0][1]
        gmsh.model.addPhysicalGroup(3, [vol_tag], tag=1)
        gmsh.model.setPhysicalName(3, 1, 'solid')
        # Mesh sizing
        gmsh.option.setNumber('Mesh.MeshSizeMin', mesh_size)
        gmsh.option.setNumber('Mesh.MeshSizeMax', mesh_size)
        gmsh.model.mesh.generate(3)
        # Extract node data and elements before generating 2D
        node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
        node_coords = node_coords.reshape((-1, 3))
        # Map node tag -> index
        node_tag_to_index = {tag: idx for idx, tag in enumerate(node_tags)}
        # Tetrahedral elements
        tet_types, tet_tags, tet_node_tags = gmsh.model.mesh.getElements(3)
        tets_idx = []
        volumes = []
        for etype, tags, nodes in zip(tet_types, tet_tags, tet_node_tags):
            if etype == 4:
                nt = len(tags)
                nodes_arr = nodes.reshape((nt, 4))
                for row in nodes_arr:
                    tets_idx.append([node_tag_to_index[t] for t in row])
                    # Compute volume using node coordinates
                    coords_elem = node_coords[[node_tag_to_index[t] for t in row]]
                    v = np.abs(np.linalg.det(np.column_stack((coords_elem[1] - coords_elem[0],
                                                             coords_elem[2] - coords_elem[0],
                                                             coords_elem[3] - coords_elem[0])))) / 6.0
                    volumes.append(v)
        tets_idx = np.array(tets_idx, dtype=int)
        volumes = np.array(volumes, dtype=float)
        # Generate 2D surface mesh for load extraction
        gmsh.model.mesh.generate(2)
        # Write mesh file for fine mesh only
        mesh_file = f"mesh_{label}.msh"
        gmsh.write(mesh_file)
        # Extract surfaces for load application
        surfaces = gmsh.model.occ.getEntities(2)
        surf_mapping = map_surface_tags(face_map, surfaces)
        # Get Tag for faces 10 and 11
        try:
            top_tag = [tag for tag, fid in surf_mapping.items() if fid == 10][0]
            bottom_tag = [tag for tag, fid in surf_mapping.items() if fid == 11][0]
        except Exception as e:
            gmsh.finalize()
            raise RuntimeError("Could not find face tags 10 or 11 in surface mapping")
        # Dirichlet nodes (bottom surface)
        bottom_node_tags, _, _ = gmsh.model.mesh.getNodes(2, bottom_tag)
        dirichlet_nodes = set(bottom_node_tags)
        # Dirichlet nodes (bottom surface)
        bottom_node_tags, _, _ = gmsh.model.mesh.getNodes(2, bottom_tag)
        dirichlet_nodes = set(bottom_node_tags)
        # Top surface triangles
        top_e_types, top_e_tags, top_node_tags = gmsh.model.mesh.getElements(2, top_tag)
        top_triangles = []
        if top_e_types:
            # All top surface elements are triangles (type 2)
            nodesarr = top_node_tags[0]
            n_tri = len(nodesarr) // 3
            for i in range(n_tri):
                n1 = node_tag_to_index[nodesarr[3 * i]]
                n2 = node_tag_to_index[nodesarr[3 * i + 1]]
                n3 = node_tag_to_index[nodesarr[3 * i + 2]]
                top_triangles.append((n1, n2, n3))
        # Assemble K and load vector
        C = np.array([
            [lam + 2 * mu, lam, lam, 0, 0, 0],
            [lam, lam + 2 * mu, lam, 0, 0, 0],
            [lam, lam, lam + 2 * mu, 0, 0, 0],
            [0, 0, 0, mu, 0, 0],
            [0, 0, 0, 0, mu, 0],
            [0, 0, 0, 0, 0, mu]
        ], dtype=float)
        K, f_vec, dirichlet_dofs = assemble_stiffness_and_load(
            node_coords, tets_idx, volumes,
            dirichlet_nodes, top_triangles, lambda_eigs=False)
        # Apply Dirichlet by condensation
        all_dofs = np.arange(K.shape[0])
        free_dofs = np.array([d for d in all_dofs if d not in dirichlet_dofs])
        K_ff = K[free_dofs][:, free_dofs]
        f_ff = f_vec[free_dofs]
        u_free = spl.spsolve(K_ff, f_ff)
        u_global = np.zeros(K.shape[0])
        u_global[free_dofs] = u_free
        # Compute element stresses
        stresses = []
        u_global_reshaped = u_global.reshape(-1, 3)
        for ei in range(tets_idx.shape[0]):
            ndx = tets_idx[ei]
            coords_elem = node_coords[ndx]
            B = element_B(coords_elem)
            ue = u_global_reshaped[ndx].reshape(-1)
            estrain = B @ ue
            sigma = C @ estrain
            stresses.append(sigma)
        stresses = np.array(stresses, dtype=float)
        # Assemble geometric stiffness
        K_G = assemble_geometric_stiffness(node_coords, tets_idx, volumes, stresses, dirichlet_dofs)
        # Solve generalized eigenvalue problem K u = λ (-K_G) u
        M = -K_G
        try:
            eig_vals, _ = spl.eigs(K, M, k=5, sigma=0.0, which='LM')
            eig_vals = np.real(eig_vals)
        except Exception as e:
            warn_msg = f"eig failure {e}; falling back to dense solver"
            print(warn_msg)
            K_dense = K.toarray()
            M_dense = M.toarray()
            invM = np.linalg.inv(M_dense)
            eig_vals = np.linalg.eigvalsh(invM @ K_dense)
        pos_vals = eig_vals[eig_vals > 1e-8]
        lamb1 = float(pos_vals.min()) if pos_vals.size > 0 else None
        if label == "coarse":
            refinement["coarse"] = {"num_nodes": int(node_coords.shape[0]),
                                    "num_tetrahedra": int(tets_idx.shape[0]),
                                    "lambda1": lamb1}
        elif label == "fine":
            refinement["fine"] = {"num_nodes": int(node_coords.shape[0]),
                                  "num_tetrahedra": int(tets_idx.shape[0]),
                                  "lambda1": lamb1}
            lambda1_fine = lamb1
            fields = {"node_coords": node_coords,
                      "displacements": u_global.reshape((-1, 3)),
                      "element_stress": stresses}
        gmsh.finalize()
        # Remove intermediate files; keep only final mesh
        if label == "fine":
            os.rename(mesh_file, "mesh.msh")
        else:
            os.remove(mesh_file)

    # Write results.json
    results = {"outputs": {"lambda1": lambda1_fine}}
    with open('results.json', 'w') as f:
        json.dump(results, f)
    # Copy part.step
    shutil.copyfile(step_input_path, 'part.step')
    # Save fields.npz
    np.savez('fields.npz', **fields)
    # Write solver.log
    log_lines = [
        f"Finite element buckling analysis for fcVM buckling_U100_3D",
        f"Python {os.sys.version.split()[0]}",
        f"NumPy {np.__version__}",
        f"SciPy {scipy.__version__}",
        f"Gmsh 4.15.2",
        f"Material: E={E} MPa, ν={nu}",
        f"Mesh sizes: coarse={mesh_specs[0][1]} mm, fine={mesh_specs[1][1]} mm",
        f"Coarse mesh: {refinement['coarse']['num_tetrahedra']} tetrahedra",
        f"Fine mesh: {refinement['fine']['num_tetrahedra']} tetrahedra",
        f"Computed λ1 (fine mesh): {lambda1_fine}"
    ]
    with open('solver.log', 'w') as f:
        f.write("\n".join(log_lines))
    # Write refinement.json
    with open('refinement.json', 'w') as f:
        json.dump(refinement, f)
    # Write environment.json
    env = {
        "python_version": os.sys.version.split()[0],
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "gmsh_version": "4.15.2",
        "material": {"E(MPa)": E, "nu": nu},
        "body_force_N_per_mm3": body_force.tolist(),
        "traction_top_N_per_mm2": traction_top.tolist(),
        "mesh": {
            "coarse_elements": refinement["coarse"]["num_tetrahedra"],
            "fine_elements": refinement["fine"]["num_tetrahedra"]
        },
        "solver": "spsolve + eigs"
    }
    with open('environment.json', 'w') as f:
        json.dump(env, f)

    print("Analysis completed. lambda1 fine =", lambda1_fine)
