import os
import json
import shutil
import time
import numpy as np
import gmsh
import meshio
import scipy.sparse.linalg as spla
from skfem import MeshTet, CellBasis, asm, BilinearForm
from skfem.element import ElementVector, ElementTetP1
from skfem.helpers import sym_grad, trace, eye, ddot

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_faces_json():
    """Load faces.json from the CADFEM_INPUT_DIR directory.

    The evaluator provides the path to input files via the environment variable
    ``CADFEM_INPUT_DIR``. If the variable is not set, we fall back to a relative
    ``inputs`` directory (useful for local testing).
    """
    input_dir = os.getenv("CADFEM_INPUT_DIR", "inputs")
    path = os.path.join(input_dir, "faces.json")
    with open(path, "r") as f:
        data = json.load(f)
    faces = {}
    for rec in data["faces"]:
        idx = rec["face_index"]
        faces[idx] = {
            "area": rec["area_mm2"],
            "centroid": np.array(rec["centroid_mm"], dtype=float),
        }
    return faces

def compute_traction(force_vec, area):
    # force_vec is a length-3 list/array of total force (N)
    # area in mm^2, traction in N/mm^2 (MPa)
    return np.array(force_vec, dtype=float) / area

def triangle_area(p0, p1, p2):
    # p0,p1,p2 shape (3, ntri)
    cross = np.cross(p1 - p0, p2 - p0, axis=0)
    return 0.5 * np.linalg.norm(cross, axis=0)

def run_analysis(mesh_size, faces_dict, load_faces, support_faces, fine=False):
    """Run a single analysis for a given mesh size.
    Returns a dict with results and writes mesh and fields.
    """
    start_total = time.time()
    log_lines = []
    # ---------------------------------------------------------------------
    # Initialize Gmsh and import geometry
    # ---------------------------------------------------------------------
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    # Load the part STEP file
    input_dir = os.getenv("CADFEM_INPUT_DIR", "inputs")
    part_path = os.path.join(input_dir, "part.step")
    model_tag = gmsh.model.add("part")
    gmsh.model.occ.importShapes(part_path)
    gmsh.model.occ.synchronize()
    # ---------------------------------------------------------------------
    # Set meshing options (linear tetrahedra)
    # ---------------------------------------------------------------------
    gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
    gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size * 0.5)
    gmsh.option.setNumber("Mesh.ElementOrder", 1)  # linear elements
    # Generate the 3D mesh
    gmsh.model.mesh.generate(3)

    # Export mesh to file (for output artifact)
    mesh_file = f"mesh_{mesh_size:.2f}.msh"
    gmsh.write(mesh_file)
    log_lines.append(f"Generated mesh with max element size {mesh_size} mm: {mesh_file}")

    # ---------------------------------------------------------------------
    # Extract node coordinates and connectivity
    # ---------------------------------------------------------------------
    # All nodes (dim=0)
    node_tags_all, node_coords_all, _ = gmsh.model.mesh.getNodes()
    node_coords_all = np.array(node_coords_all, dtype=float).reshape(-1, 3).T  # shape (3, n_nodes)
    tag_to_index = {int(tag): i for i, tag in enumerate(node_tags_all)}
    n_nodes = node_coords_all.shape[1]
    # Volume elements (tetrahedra)
    etypes, etags, elemNodeTags = gmsh.model.mesh.getElements(dim=3)
    # Find element type 4 (linear tetra)
    conn = None
    for et, tn in zip(etypes, elemNodeTags):
        if et == 4:
            conn = np.array(tn, dtype=int).reshape(-1, 4).T
            # Convert Gmsh node tags (1-based) to zero‑based indices used by scikit‑fem
            conn = np.vectorize(tag_to_index.get)(conn)
            break
    if conn is None:
        raise RuntimeError("No linear tetrahedra found in mesh.")
    # Filter out any potentially degenerate (zero-volume) tetrahedra
    def tetra_volumes(indices):
        a = node_coords_all[:, indices[0]]
        b = node_coords_all[:, indices[1]]
        c = node_coords_all[:, indices[2]]
        d = node_coords_all[:, indices[3]]
        # Compute signed volume using scalar triple product: (b-a)·((c-a)×(d-a)) / 6
        cross = np.cross(c - a, d - a, axis=0)
        vol = np.abs(np.einsum('ij,ij->j', b - a, cross)) / 6.0
        return vol
    vols = tetra_volumes(conn)
    valid = vols > 1e-12
    conn = conn[:, valid]
    n_elems = conn.shape[1]
    log_lines.append(f"Mesh nodes: {n_nodes}, tetrahedra (valid): {n_elems}")
    # Build scikit-fem mesh
    mesh = MeshTet(node_coords_all, conn)

    # ---------------------------------------------------------------------
    # Helper: map face_index (from faces.json) to Gmsh surface tag using geometry centroid
    # ---------------------------------------------------------------------
    surface_entities = gmsh.model.getEntities(dim=2)  # list of (dim, tag)
    # Compute centroid of each surface (geometric, not mesh) via OCC
    surface_centroids = {}
    for dim, tag in surface_entities:
        com = gmsh.model.occ.getCenterOfMass(dim, tag)
        surface_centroids[tag] = np.array(com, dtype=float)
    # Map required faces
    face_to_tag = {}
    for face_idx in list(load_faces.keys()) + support_faces:
        target_cent = faces_dict[face_idx]["centroid"]
        best_tag = None
        best_dist = 1e9
        for tag, cen in surface_centroids.items():
            d = np.linalg.norm(cen - target_cent)
            if d < best_dist:
                best_dist = d
                best_tag = tag
        if best_tag is None:
            raise RuntimeError(f"Could not map face {face_idx} to a surface tag.")
        face_to_tag[face_idx] = best_tag
    log_lines.append(f"Mapped {len(face_to_tag)} faces to surface tags.")

    # ---------------------------------------------------------------------
    # Identify support (Dirichlet) nodes
    # ---------------------------------------------------------------------
    support_node_tags = set()
    for f_idx in support_faces:
        tag = face_to_tag[f_idx]
        n_tags, _coords, _ = gmsh.model.mesh.getNodes(dim=2, tag=tag)
        support_node_tags.update([int(t) for t in n_tags])
    support_node_indices = np.array([tag_to_index[t] for t in support_node_tags], dtype=int)
    log_lines.append(f"Support nodes count: {len(support_node_indices)}")

    # ---------------------------------------------------------------------
    # Build finite element system (linear elasticity)
    # ---------------------------------------------------------------------
    element = ElementVector(ElementTetP1())
    basis = CellBasis(mesh, element)
    E = 3000.0  # MPa = N/mm^2
    nu = 0.36
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))

    def bilinear_form(u, v, w):
        eps_u = sym_grad(u)
        tr_u = trace(eps_u)
        sigma_u = lam * eye(tr_u, 3) + 2 * mu * eps_u
        return ddot(sigma_u, sym_grad(v))

    K = asm(bilinear_form, basis)  # scipy CSR matrix
    log_lines.append(f"Stiffness matrix assembled: shape {K.shape}, nnz {K.nnz}")

    # ---------------------------------------------------------------------
    # Assemble load vector from traction on specified faces
    # ---------------------------------------------------------------------
    F = np.zeros(K.shape[0])
    # For each loaded face, compute traction and distribute to nodes via triangle integration
    for f_idx, force_vec in load_faces.items():
        area = faces_dict[f_idx]["area"]
        traction = compute_traction(force_vec, area)  # N/mm^2
        tag = face_to_tag[f_idx]
        # Get surface triangles (type 2)
        etypes_s, etags_s, eNodeTags_s = gmsh.model.mesh.getElements(dim=2, tag=tag)
        if not etypes_s:
            continue
        # Assuming first element type is triangle (type 2)
        tri_node_tags = np.array(eNodeTags_s[0], dtype=int).reshape(-1, 3)
        # Convert to mesh node indices
        tri_node_ix = np.vectorize(tag_to_index.get)(tri_node_tags)
        # Compute area for each triangle using node coordinates
        p0 = node_coords_all[:, tri_node_ix[:, 0]]
        p1 = node_coords_all[:, tri_node_ix[:, 1]]
        p2 = node_coords_all[:, tri_node_ix[:, 2]]
        tri_areas = triangle_area(p0, p1, p2)
        # Distribute traction to nodes (consistent nodal forces)
        for tri, a in zip(tri_node_ix, tri_areas):
            f_per_node = traction * (a / 3.0)
            for n in tri:
                dof_idxs = basis.dofs.nodal_dofs[:, n]  # shape (3,)
                F[dof_idxs] += f_per_node
    log_lines.append("Load vector assembled.")

    # ---------------------------------------------------------------------
    # Apply Dirichlet boundary conditions (zero displacement on support nodes)
    # ---------------------------------------------------------------------
    fixed_dofs = basis.dofs.nodal_dofs[:, support_node_indices].flatten(order='F')
    all_dofs = np.arange(K.shape[0])
    free_dofs = np.setdiff1d(all_dofs, fixed_dofs)
    log_lines.append(f"Number of fixed DOFs: {len(fixed_dofs)}; free DOFs: {len(free_dofs)}")

    # Solve linear system
    K_ff = K[free_dofs, :][:, free_dofs]
    b_f = F[free_dofs]
    t_solve_start = time.time()
    u_f = spla.spsolve(K_ff, b_f)
    t_solve_end = time.time()
    log_lines.append(f"Linear solve time: {t_solve_end - t_solve_start:.3f} s")
    # Construct full displacement vector
    U = np.zeros(K.shape[0])
    U[free_dofs] = u_f
    # Extract nodal displacement vectors (3 components per node)
    disp = U.reshape(3, -1, order='F').T  # shape (n_nodes, 3)
    # Compute maximum displacement magnitude
    disp_magn = np.linalg.norm(disp, axis=1)
    max_disp = float(disp_magn.max())
    log_lines.append(f"Maximum nodal displacement magnitude: {max_disp:.6e} mm")

    # ---------------------------------------------------------------------
    # Write outputs for this mesh (if fine mesh)
    # ---------------------------------------------------------------------
    if fine:
        # Write mesh file (rename to mesh.msh as final artifact)
        shutil.copy(mesh_file, "mesh.msh")
        # Write fields.npz (node tags, coordinates, displacement)
        np.savez(
            "fields.npz",
            node_tags=node_tags_all,
            coords=node_coords_all.T,  # (n_nodes, 3)
            displacement=disp,
        )
        # Write solver.log
        with open("solver.log", "w") as f_log:
            for line in log_lines:
                f_log.write(line + "\n")
        # Write part.step (copy from input). Overwrite if already present.
        if os.path.exists("part.step"):
            os.remove("part.step")
        shutil.copy(part_path, "part.step")
    # Cleanup Gmsh
    gmsh.finalize()
    total_time = time.time() - start_total
    log_lines.append(f"Total analysis time: {total_time:.3f} s")
    # Return data for refinement report
    return {
        "mesh_size": mesh_size,
        "num_nodes": n_nodes,
        "num_elements": n_elems,
        "max_displacement_mm": max_disp,
        "log": "\n".join(log_lines),
    }


def main():
    # Load faces data
    faces = load_faces_json()
    # Define loads per face (in N)
    load_faces = {
        2: (0.0, 5.760, 13.825),
        3: (0.0, 5.761, 13.825),
        4: (0.0, 5.760, 13.823),
        5: (0.0, 5.763, 13.832),
        6: (0.0, 5.759, 13.821),
        7: (0.0, 5.760, 13.824),
        32: (0.0, 5.762, 13.828),
        34: (0.0, 5.762, 13.828),
        36: (0.0, 5.761, 13.826),
        38: (0.0, 5.761, 13.826),
        40: (0.0, 5.762, 13.828),
        42: (0.0, 5.761, 13.827),
    }
    support_faces = [1, 28, 45]

    # Run analyses for two mesh resolutions
    coarse = run_analysis(5.0, faces, load_faces, support_faces, fine=False)
    fine = run_analysis(2.0, faces, load_faces, support_faces, fine=True)

    # Write results.json with final (fine) result
    results = {
        "outputs": {
            "max_displacement_mm": fine["max_displacement_mm"]
        }
    }
    with open("results.json", "w") as f_res:
        json.dump(results, f_res, indent=2)

    # Write refinement.json
    refinement = {
        "refinements": [
            {"mesh_size_mm": coarse["mesh_size"], "num_nodes": coarse["num_nodes"], "num_elements": coarse["num_elements"], "max_displacement_mm": coarse["max_displacement_mm"]},
            {"mesh_size_mm": fine["mesh_size"], "num_nodes": fine["num_nodes"], "num_elements": fine["num_elements"], "max_displacement_mm": fine["max_displacement_mm"]}
        ]
    }
    with open("refinement.json", "w") as f_ref:
        json.dump(refinement, f_ref, indent=2)

    # Write environment.json
    env = {
        "software": {
            "python": "3.12",
            "gmsh": getattr(gmsh, "__version__", "unknown"),
            "scikit_fem": __import__("skfem").__version__,
            "numpy": np.__version__,
            "scipy": __import__("scipy").__version__,
        },
        "units": "mm, N, MPa",
        "material": {
            "name": "PETG-CF",
            "E_MPa": 3000.0,
            "nu": 0.36
        },
        "analysis": {
            "type": "linear_static",
            "solver": "scipy.sparse.linalg.spsolve",
            "element": "Linear tetrahedron (P1) with vector displacement"
        }
    }
    with open("environment.json", "w") as f_env:
        json.dump(env, f_env, indent=2)

    # Save solver log from fine run
    with open("solver.log", "w") as f_log:
        f_log.write(fine["log"])

    # Clean up intermediate mesh files and temporary directories that are not part of the contract
    for fname in ["mesh_5.00.msh", "mesh_2.00.msh"]:
        try:
            if os.path.exists(fname):
                os.remove(fname)
        except Exception:
            pass
    for dname in ["cache", "tmp"]:
        try:
            if os.path.isdir(dname):
                shutil.rmtree(dname)
        except Exception:
            pass

if __name__ == "__main__":
    main()
