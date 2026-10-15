#!/usr/bin/env python
'''CADFEM-Bench solution for Task A-CYC-Disk-PETGCF.
This script reads the supplied geometry (part.step) and face specifications (faces.json),
generates a tetrahedral mesh with Gmsh, assembles a linear elastic finite element model
using matrix-free assembly, applies the specified boundary conditions and loads, solves
for displacements, and outputs the requested results and artifacts.'''

import os
import json
import sys
import time
import numpy as np
import scipy
import scipy.sparse as sparse
import scipy.sparse.linalg as spla
import gmsh
import io

__all__ = ['main']

def _read_faces_json():
    '''Read faces.json from the input directory.'''
    inp_dir = os.getenv('CADFEM_INPUT_DIR', '.')
    faces_path = os.path.join(inp_dir, 'faces.json')
    with open(faces_path, 'r') as f:
        data = json.load(f)
    return {face['face_index']: face for face in data['faces']}

def _generate_and_solve(mesh_size_mm, mesh_out_name, log_buf):
    '''Generate mesh, assemble, solve and return displacement data.'''
    start_time = time.time()

    gmsh.initialize()
    inp_dir = os.getenv('CADFEM_INPUT_DIR', '.')
    part_path = os.path.join(inp_dir, 'part.step')
    gmsh.open(part_path)
    # Generate the mesh before accessing elements
    gmsh.model.mesh.generate(3)
    gmsh.option.setNumber('Mesh.MeshSizeMax', mesh_size_mm)
    gmsh.option.setNumber('Mesh.MeshSizeMin', mesh_size_mm * 0.25)
    gmsh.option.setNumber('General.Terminal', 1)
    gmsh.option.setNumber('General.Verbosity', 3)

    faces_dict = _read_faces_json()
    support_surface_tags = [faces_dict[8]['face_index'], faces_dict[13]['face_index']]
    load_surface_tag2 = faces_dict[2]['face_index']
    load_surface_tag19 = faces_dict[19]['face_index']

    # Physical groups
    gmsh.model.addPhysicalGroup(2, support_surface_tags, 1)
    gmsh.model.setPhysicalName(2, 1, 'support')
    gmsh.model.addPhysicalGroup(2, [load_surface_tag2], 2)
    gmsh.model.setPhysicalName(2, 2, 'load_face2')
    gmsh.model.addPhysicalGroup(2, [load_surface_tag19], 3)
    gmsh.model.setPhysicalName(2, 3, 'load_face19')

    gmsh.model.mesh.generate(3)
    # Nodes and coordinates
    node_tags, node_coords_flat, _ = gmsh.model.mesh.getNodes()
    node_coords_mm = node_coords_flat.reshape(-1, 3).astype(np.float64)
    node_coords_m = node_coords_mm / 1000.0
    num_nodes = len(node_tags)
    print(f"[DEBUG] Node count: {num_nodes}, node_coords_flat size: {node_coords_flat.size}")
    # Write the mesh file for the solver artifacts
    try:
        gmsh.write(mesh_out_name)
    except Exception as e:
        print('Error writing mesh file', e)
    tag_to_index = {tag: idx for idx, tag in enumerate(node_tags)}

    # Tetra elements
    tet_tags, tet_node_tags_flat = gmsh.model.mesh.getElementsByType(4)
    tet_conn_tags = tet_node_tags_flat.reshape((-1, 4))
    tet_conn = np.vectorize(tag_to_index.get)(tet_conn_tags)
    num_tets = tet_conn.shape[0]

    # Support nodes
    support_node_tags, _ = gmsh.model.mesh.getNodesForPhysicalGroup(2, 1)
    support_node_idx = np.vectorize(tag_to_index.get)(support_node_tags)

    # Load triangle definitions
    load2_tags, load2_node_tags_flat = gmsh.model.mesh.getElementsByType(2, 2)
    load3_tags, load3_node_tags_flat = gmsh.model.mesh.getElementsByType(2, 3)
    load2_conn = load2_node_tags_flat.reshape((-1, 3))
    load3_conn = load3_node_tags_flat.reshape((-1, 3))
    load2_conn = np.vectorize(tag_to_index.get)(load2_conn)
    load3_conn = np.vectorize(tag_to_index.get)(load3_conn)

    # Finalize gmsh before proceeding with assembly to avoid interfering with SciPy
    try:
        gmsh.finalize()
    except Exception as e:
        print('gmsh finalize error ignored:', e)

    # Material properties
    E = 3000e6
    nu = 0.36
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    D = np.array([
        [lam + 2 * mu, lam, lam, 0, 0, 0],
        [lam, lam + 2 * mu, lam, 0, 0, 0],
        [lam, lam, lam + 2 * mu, 0, 0, 0],
        [0, 0, 0, mu, 0, 0],
        [0, 0, 0, 0, mu, 0],
        [0, 0, 0, 0, 0, mu]
    ], dtype=np.float64)

    ndofs = num_nodes * 3
    print('Creating sparse matrix; ndofs=', ndofs, 'type:', type(ndofs))
    print('sparse module:', sparse)
    K = sparse.lil_matrix((ndofs, ndofs), dtype=np.float64)
    F_vec = np.zeros(ndofs, dtype=np.float64)

    # Load densities (N/m^2)
    area_face_mm2 = 125.664
    area_face_m2 = area_face_mm2 * 1e-6
    t_load2 = np.array([0.0, -31.165, 94.894], dtype=np.float64) / area_face_m2
    t_load3 = np.array([0.0, -31.169, 94.905], dtype=np.float64) / area_face_m2

    def add_triangle_load(conn, traction):
        for tri in conn:
            verts = node_coords_m[tri]
            v1 = verts[1] - verts[0]
            v2 = verts[2] - verts[0]
            area = 0.5 * np.linalg.norm(np.cross(v1, v2))
            nodal_load = traction * area / 3.0
            for node in tri:
                base = node * 3
                F_vec[base:base+3] += nodal_load

    add_triangle_load(load2_conn, t_load2)
    add_triangle_load(load3_conn, t_load3)

    # Assemble element stiffness
    for elem_idx in range(num_tets):
        node_idx = tet_conn[elem_idx]
        coords = node_coords_m[node_idx]
        G_mat = np.vstack((np.ones(4), coords.T))
        invG = np.linalg.inv(G_mat)
        b = invG[1, :]
        c = invG[2, :]
        d = invG[3, :]
        Bm = np.zeros((6, 12), dtype=np.float64)
        # Normal strain components
        Bm[0, 0::3] = b          # ε_xx
        Bm[1, 1::3] = c          # ε_yy
        Bm[2, 2::3] = d          # ε_zz
        # Engineering shear strain components
        Bm[3, 0::3] = c          # γ_xy = 2ε_xy => ∂u/∂y + ∂v/∂x
        Bm[3, 1::3] = b
        Bm[4, 1::3] = d          # γ_yz = 2ε_yz => ∂v/∂z + ∂w/∂y
        Bm[4, 2::3] = c
        Bm[5, 0::3] = b          # γ_xz = 2ε_xz => ∂u/∂z + ∂w/∂x
        Bm[5, 2::3] = d
        v = np.abs(np.linalg.det(np.column_stack((coords[1]-coords[0],
                                                 coords[2]-coords[0],
                                                 coords[3]-coords[0])))) / 6.0
        Ke = (Bm.T @ D @ Bm) * v
        global_dofs = np.hstack((node_idx*3, node_idx*3+1, node_idx*3+2))
        for i_local in range(12):
            i_global = global_dofs[i_local]
            for j_local in range(12):
                j_global = global_dofs[j_local]
                K[i_global, j_global] += Ke[i_local, j_local]

    # Apply Dirichlet BCs (support nodes fixed)
    bc_dofs = np.hstack((support_node_idx*3, support_node_idx*3+1, support_node_idx*3+2))
    free_flag = np.ones(ndofs, dtype=bool)
    free_flag[bc_dofs] = False
    K_free = K[free_flag, :][:, free_flag]
    F_free = F_vec[free_flag]
    U_free = spla.spsolve(K_free.tocsc(), F_free)
    U_global = np.zeros(ndofs, dtype=np.float64)
    U_global[free_flag] = U_free
    displacements_m = U_global.reshape((num_nodes, 3))
    displacements_mm = displacements_m * 1000.0
    max_disp_mm = np.linalg.norm(displacements_mm, axis=1).max()
    elapsed = time.time() - start_time
    try:
        gmsh.finalize()
    except Exception as e:
        # gmsh may occasionally throw errors on finalize; ignore
        print('gmsh finalize error ignored:', e)
    return {
        'max_disp_mm': max_disp_mm,
        'coords_mm': node_coords_mm,
        'displacements_mm': displacements_mm,
        'num_nodes': num_nodes,
        'num_tets': num_tets,
        'mesh_size_mm': mesh_size_mm,
        'elapsed': elapsed,
        'num_load_triangles': load2_conn.shape[0] + load3_conn.shape[0]
    }


def main():
    log_buf = io.StringIO()
    out_dir = os.getcwd()
    # Primary analysis with 2 mm mesh
    mesh_file = os.path.join(out_dir, 'mesh.msh')
    primary = _generate_and_solve(2.0, mesh_file, log_buf)
    # Refinement with 1 mm mesh
    tmp_mesh = os.path.join(out_dir, 'mesh_1mm.msh')
    refinement = _generate_and_solve(1.0, tmp_mesh, log_buf)

    # results.json
    results = {'outputs': {'max_displacement_mm': primary['max_disp_mm']}}
    with open('results.json', 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # fields.npz
    np.savez(
        'fields.npz',
        node_ids=np.arange(primary['num_nodes'], dtype=np.int32),
        coordinates=primary['coords_mm'],
        displacements=primary['displacements_mm'],
        max_displacement_mm=primary['max_disp_mm']
    )

    # solver.log
    solver_log = log_buf.getvalue()
    solver_log += f"\nPrimary analysis: mesh size {primary['mesh_size_mm']} mm, "
    solver_log += f"{primary['num_nodes']} nodes, {primary['num_tets']} tets, "
    solver_log += f"max disp = {primary['max_disp_mm']:.6g} mm, time = {primary['elapsed']:.2f}s"
    solver_log += f"\nRefinement (1mm): mesh size 1 mm, {refinement['num_nodes']} nodes, "
    solver_log += f"{refinement['num_tets']} tets, max disp = {refinement['max_disp_mm']:.6g} mm, time = {refinement['elapsed']:.2f}s"
    with open('solver.log', 'w') as f:
        f.write(solver_log)

    # refinement.json
    refinement_json = {
        "2mm": {
            "nodes": primary['num_nodes'],
            "tets": primary['num_tets'],
            "max_displacement_mm": primary['max_disp_mm'],
            "mesh_size_mm": primary['mesh_size_mm']
        },
        "1mm": {
            "nodes": refinement['num_nodes'],
            "tets": refinement['num_tets'],
            "max_displacement_mm": refinement['max_disp_mm'],
            "mesh_size_mm": refinement['mesh_size_mm']
        }
    }
    with open('refinement.json', 'w') as f:
        json.dump(refinement_json, f, ensure_ascii=False, indent=2)

    # environment.json
    env = {
        "python_version": sys.version,
        "gmsh_version": gmsh.__version__,
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "material": {"E_MPa": 3000.0, "nu": 0.36},
        "analysis": "linear elastic 3D, linear tetrahedral FE",
        "mesh_size_mm": primary['mesh_size_mm'],
        "units": "mm",
        "coordinate_frame": "model (as provided in part.step)",
        "boundary_groups": {
            "support": [8, 13],
            "load_face2": [2],
            "load_face19": [19]
        }
    }
    with open('environment.json', 'w') as f:
        json.dump(env, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
