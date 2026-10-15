#!/usr/bin/env python3
"""
CADFEM-Bench Task A-CYC-FlangeP1-PETGCF
This script generates the required CFD/FE solution for the
cycloidal gearbox output flange P1.
It performs the following steps:
  1. Mesh generation using Gmsh (resolution 2mm).
  2. Construction of a FEM mesh using scikit-fem.
  3. Identification of support and load faces from faces.json.
  4. Formulation of the 3‑D linear elasticity problem.
  5. Application of Dirichlet BCs on faces 1,28,45.
  6. Application of uniform traction on the loaded faces.
  7. Assembly, solution and extraction of the maximum displacement.
  8. Generation of the required artefact files.
"""

import os
import json
import shutil
import subprocess
import numpy as np
import meshio
import skfem
import skfem.element as element
from skfem import Basis, solve
import skfem.models.elasticity as mu_elastic
from skfem.utils import enforce

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def run_gmsh(input_step, output_mesh, mshsize):
    """Run gmsh to generate a 3‑D mesh file.

    Parameters
    ----------
    input_step : str
        Path to the STEP file.
    output_mesh : str
        Path of the generated mesh file.
    mshsize : float
        Maximum element size in millimetres.
    """
    cmd = [
        'gmsh', input_step, '-3', '-order', '2', '-o', output_mesh,
        '-setnumber', 'Mesh.MeshSizeMax', str(mshsize)
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc


def build_mesh(mesh_obj):
    """Create a skfem Mesh from a meshio mesh.

    The mesh file must contain tetrahedron elements of type ``tetra10`` –
    the first four nodes correspond to the linear tetrahedral connectivity.
    """
    tet_cells = None
    for cellblock in mesh_obj.cells:
        if cellblock.type == 'tetra10':
            tet_cells = cellblock.data
            break
    if tet_cells is None:
        raise RuntimeError('No tetra10 cells found in mesh')

    points = mesh_obj.points
    conn = tet_cells[:, :4]  # linear connectivity (N_tets, 4)
    # Remap node indices to be contiguous starting from 0
    used_nodes = np.unique(conn)
    indices_map = np.full(points.shape[0], -1, dtype=int)
    indices_map[used_nodes] = np.arange(used_nodes.shape[0])
    conn_new = indices_map[conn]
    points_new = points[used_nodes]
    # skfem.Mesh.from_dict expects point matrix (N,3) and connectivity
    # matrix (N_tets, 4). It will transpose internally.
    mesh_dict = {
        'p': points_new,
        't': conn_new,
        'subdomains': None,
        'boundaries': None,
    }
    mesh = skfem.mesh.Mesh.from_dict(mesh_dict)
    # set correct element for reference domain compatibility
    mesh.elem = element.element_tet.element_tet_p1.ElementTetP1()
    return mesh, points_new, conn_new, indices_map


def assemble_and_solve(mesh, points, support_dofs, load_vector):
    """Assemble stiffness matrix, enforce BCs and solve the linear system.

    Returns the displacement vector (global DOFs) and the maximum
    displacement magnitude.
    """
    vec_elem = element.ElementVector(element.element_tet.element_tet_p1.ElementTetP1())
    basis = Basis(mesh, vec_elem)

    # Material constants (MPa = N/mm^2, units consistent with mm)
    E = 3000.0  # MPa
    nu = 0.36
    Lambda = E * nu / ((1 + nu) * (1 - 2 * nu))
    Mu = E / (2 * (1 + nu))

    A = mu_elastic.linear_elasticity(Lambda, Mu).assemble(basis)
    # Apply Dirichlet BCs
    if support_dofs.size > 0:
        A_bc, b_bc = enforce(A, load_vector, D=support_dofs)
    else:
        A_bc, b_bc = A, load_vector
    u = solve(A_bc, b_bc)
    disp = u.reshape(-1, 3)
    max_disp = np.linalg.norm(disp, axis=1).max()
    return u, disp, max_disp


def process_mesh(mesh_file, mesh_size, support_faces, loaded_face_forces, face_centroids, face_tractions):
    """Complete processing of a mesh: load, assemble, apply loads and BC.

    Returns displacement array, max displacement, number of elements and nodes.
    """
    mesh_obj = meshio.read(mesh_file)
    mesh, points, conn, indices_map = build_mesh(mesh_obj)
    # DEBUG: print mesh connectivity details
    print('DEBUG: mesh.t shape', mesh.t.shape, 'unique nodes from t', np.unique(mesh.t).size)
    num_nodes = points.shape[0]
    num_elements = conn.shape[0]

    # Build facet list from triangle6 cells
    facet_nodes = []
    for cellblock in mesh_obj.cells:
        if cellblock.type == 'triangle6':
            facet_nodes.append(cellblock.data[:, :3])  # first 3 nodes
        elif cellblock.type == 'triangle':
            facet_nodes.append(cellblock.data)  # they are already 3 nodes
    if len(facet_nodes) == 0:
        raise RuntimeError('No surface facets found')
    facets_orig = np.vstack(facet_nodes)
    # Convert facet node indices from original to local mesh indices
    facets = indices_map[facets_orig]
    if np.any(facets < 0):
        raise RuntimeError('Facet contains node that is not part of the mesh')

    # Centroids of facets
    facet_centroids = points[facets].mean(axis=1)

    # Assign each facet to the nearest face centroid (simple clustering)
    face_idx_list = sorted(face_centroids.keys())
    centroids_arr = np.array([face_centroids[i] for i in face_idx_list])
    dists = np.linalg.norm(facet_centroids[:, None, :] - centroids_arr[None, :, :], axis=2)
    nearest_face_idx = np.argmin(dists, axis=1)
    facet_to_face = np.array([face_idx_list[idx] for idx in nearest_face_idx])

    # Support nodes (collect all nodes belonging to support faces)
    support_nodes_global = set()
    for f in support_faces:
        fac_mask = facet_to_face == f
        if np.any(fac_mask):
            support_nodes_global.update(facets_orig[fac_mask].flatten())
    # Map mesh nodes to local indices used by the FEM mesh
    unique_nodes = np.unique(mesh.t)
    # indices_map is mapping from original global index to new local index
    support_nodes_local = [indices_map[n] for n in support_nodes_global if indices_map[n] >= 0]
    support_dofs = []
    for ln in support_nodes_local:
        support_dofs.extend([3 * ln, 3 * ln + 1, 3 * ln + 2])
    support_dofs = np.array(sorted(support_dofs))
    # DEBUG: print sizes
    print('DEBUG: unique_nodes', unique_nodes.shape[0], 'support_dofs', support_dofs.shape[0])

    # Initialize load vector (local DOFs only)
    n_nodes_local = unique_nodes.shape[0]
    b = np.zeros((n_nodes_local * 3,))
    print('DEBUG: local DOFs', n_nodes_local * 3)

    # Add traction loads
    for f, traction in face_tractions.items():
        fac_mask = facet_to_face == f
        if not np.any(fac_mask):
            continue
        fac = facets[fac_mask]
        p0 = points[fac[:, 0]]
        p1 = points[fac[:, 1]]
        p2 = points[fac[:, 2]]
        # triangle area
        area = 0.5 * np.linalg.norm(np.cross(p1 - p0, p2 - p0), axis=1)
        for i in range(fac.shape[0]):
            nodes = fac[i]
            # map global nodes to local indices
            local_nodes = indices_map[nodes]
            # filter out nodes that are not part of the mesh
            valid = local_nodes >= 0
            if not np.any(valid):
                continue
            load_per_node = traction * area[i] / 3.0
            for ln in local_nodes[valid]:
                dof_start = 3 * ln
                b[dof_start:dof_start + 3] += load_per_node

    # Solve
    u, disp, max_disp = assemble_and_solve(mesh, points, support_dofs, b)
    return disp, max_disp, num_elements, num_nodes

# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

def main():
    # Paths
    input_dir = os.environ.get('CADFEM_INPUT_DIR')
    if not input_dir:
        raise RuntimeError('CADFEM_INPUT_DIR environment variable not set')
    src_step = os.path.join(input_dir, 'part.step')
    src_faces_json = os.path.join(input_dir, 'faces.json')

    # Copy part.step to output directory
    shutil.copyfile(src_step, 'part.step')
    # Read faces.json
    with open(src_faces_json, 'r') as f:
        faces_data = json.load(f)

    # Extract face information
    face_centroids = {int(f['face_index']): np.array(f['centroid_mm']) for f in faces_data['faces']}  # mm
    face_areas = {int(f['face_index']): f['area_mm2'] for f in faces_data['faces']}  # mm^2

    # Support faces (Dirichlet BC)
    support_faces = [1, 28, 45]
    # Load forces per face (given in N)
    loaded_face_forces = {
        2: np.array([0.000, 5.760, 13.825]),
        3: np.array([0.000, 5.761, 13.825]),
        4: np.array([0.000, 5.760, 13.823]),
        5: np.array([0.000, 5.763, 13.832]),
        6: np.array([0.000, 5.759, 13.821]),
        7: np.array([0.000, 5.760, 13.824]),
        32: np.array([0.000, 5.762, 13.828]),
        34: np.array([0.000, 5.762, 13.828]),
        36: np.array([0.000, 5.761, 13.826]),
        38: np.array([0.000, 5.761, 13.826]),
        40: np.array([0.000, 5.762, 13.828]),
        42: np.array([0.000, 5.761, 13.827]),
    }
    # Compute traction (force per unit area) for loaded faces
    face_tractions = {fi: loaded_face_forces[fi] / face_areas[fi] for fi in loaded_face_forces}

    # ---------------------------------------------------------------------
    # Generate fine mesh (mesh_size = 2 mm) and solve
    # ---------------------------------------------------------------------
    fine_mesh_file = 'mesh.msh'
    gmsh_proc = run_gmsh(src_step, fine_mesh_file, mshsize=2.0)
    # Log gmsh output
    with open('solver.log', 'w') as logf:
        logf.write('Gmsh command: ' + ' '.join(gmsh_proc.args) + '\n')
        logf.write('Gmsh stdout:\n' + gmsh_proc.stdout + '\n')
        logf.write('Gmsh stderr:\n' + gmsh_proc.stderr + '\n')

    # Process fine mesh
    disp_fine, max_disp_fine, n_elem_fine, n_node_fine = process_mesh(
        fine_mesh_file, 2.0, support_faces, loaded_face_forces, face_centroids, face_tractions)

    # Write results.json
    with open('results.json', 'w') as f_res:
        json.dump({"outputs": {"max_displacement_mm": float(max_disp_fine)}}, f_res, indent=2)

    # Write fields.npz (node ids, coordinates, displacements)
    np.savez('fields.npz', node_ids=np.arange(n_node_fine), coords=meshio.read(fine_mesh_file).points, displacements=disp_fine)

    # Write environment.json
    env = {
        "CADFEM": {
            "skfem_version": skfem.__version__
        },
        "material": {
            "E_MPa": 3000.0,
            "nu": 0.36
        },
        "units": {
            "displacement": "mm",
            "force": "N",
            "stress": "N/mm^2",
            "area": "mm^2"
        },
        "supports": {
            "faces": support_faces,
            "condition": "zero full displacement"
        },
        "loads": {
            "faces": list(face_tractions.keys()),
            "traction_N_per_mm2": {str(k): (list(v)) for k, v in face_tractions.items()},
            "area_mm2": face_areas
        },
        "mesh": {
            "fine": {"mesh_size_mm": 2.0, "n_elements": int(n_elem_fine), "n_nodes": int(n_node_fine)},
        }
    }
    with open('environment.json', 'w') as f_env:
        json.dump(env, f_env, indent=2)

    # ---------------------------------------------------------------------
    # Produce refinement.json with coarse mesh data
    # ---------------------------------------------------------------------
    coarse_mesh_file = 'mesh_coarse.msh'
    gmsh_proc_coarse = run_gmsh(src_step, coarse_mesh_file, mshsize=4.0)
    disp_coarse, max_disp_coarse, n_elem_coarse, n_node_coarse = process_mesh(
        coarse_mesh_file, 4.0, support_faces, loaded_face_forces, face_centroids, face_tractions)
    # Remove coarse mesh file after analysis
    os.remove(coarse_mesh_file)

    refinement = {
        "refinements": [
            {
                "mesh_size_mm": 2.0,
                "n_elements": int(n_elem_fine),
                "n_nodes": int(n_node_fine),
                "max_displacement_mm": float(max_disp_fine)
            },
            {
                "mesh_size_mm": 4.0,
                "n_elements": int(n_elem_coarse),
                "n_nodes": int(n_node_coarse),
                "max_displacement_mm": float(max_disp_coarse)
            }
        ]
    }
    with open('refinement.json', 'w') as f_ref:
        json.dump(refinement, f_ref, indent=2)

if __name__ == '__main__':
    main()
