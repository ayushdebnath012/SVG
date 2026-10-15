#!/usr/bin/env python
"""
CADFEM benchmark task: A-GEOPINO-PLATE-13

This script:
  1) Copies the supplied ``part.step`` from the inputs directory.
  2) Generates two tetrahedral meshes with Gmsh (coarse and fine).
  3) Performs a linear static elasticity calculation for two loading
     cases (compression and lateral bending) on the fine mesh.
  4) Stores the maximum displacement magnitudes (in mm) required by
     the benchmark, along with all other artifacts that the evaluator
     expects.

All units are in millimetres (length) and newtons (force).  Material
properties are specified in N/mm².
"""

import os
import shutil
import json
import time

import numpy as np
import scipy
import scipy.sparse.linalg as sla

import meshio
import gmsh

from skfem import Basis, asm
from skfem.models.elasticity import linear_elasticity
from skfem.element import ElementTetP1, ElementVector
from skfem.mesh import Mesh
from skfem.io import from_meshio

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
E = 200.0e3  # N/mm^2 (200 GPa)
nu = 0.3
lam = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
mu = E / (2.0 * (1.0 + nu))

total_force = 1000.0  # N

Y_FIXED = -95.0894
Y_FREE = 95.0894
TOL = 1e-3

SIZE_COARSE = 8.0
SIZE_FINE = 4.0

INPUT_STEP = os.path.join(os.environ['CADFEM_INPUT_DIR'], 'part.step')
OUTPUT_STEP = 'part.step'
COARSE_MESH = 'mesh_coarse.msh'
FINE_MESH = 'mesh_fine.msh'
USE_MESH = 'mesh.msh'
FIELDS_FILE = 'fields.npz'
RESULTS_FILE = 'results.json'
ENV_FILE = 'environment.json'
REFINE_FILE = 'refinement.json'
SOLVER_LOG = 'solver.log'

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def copy_step_file():
    shutil.copyfile(INPUT_STEP, OUTPUT_STEP)

def generate_mesh(step_file, mesh_file, size):
    gmsh.initialize()
    gmsh.open(step_file)
    gmsh.option.setNumber('Mesh.MeshSizeMax', size)
    gmsh.option.setNumber('Mesh.MeshSizeMin', size)
    gmsh.model.mesh.generate(3)
    gmsh.write(mesh_file)
    gmsh.finalize()

def extract_boundary_facet_info(points, tets, y_load, y_fixed, tol=TOL):
    face_counts = {}
    for tet in tets:
        faces = [
            (tet[0], tet[1], tet[2]),
            (tet[0], tet[1], tet[3]),
            (tet[0], tet[2], tet[3]),
            (tet[1], tet[2], tet[3]),
        ]
        for face in faces:
            key = tuple(sorted(face))
            face_counts[key] = face_counts.get(key, 0) + 1

    boundary_faces = [face for face, cnt in face_counts.items() if cnt == 1]
    load_faces = []
    fixed_faces = []
    total_area_load = 0.0
    for face in boundary_faces:
        coord = points[list(face)]
        y_centroid = np.mean(coord[:, 1])
        area = 0.5 * np.linalg.norm(np.cross(coord[1] - coord[0], coord[2] - coord[0]))
        if abs(y_centroid - y_load) < tol:
            load_faces.append(face)
            total_area_load += area
        elif abs(y_centroid - y_fixed) < tol:
            fixed_faces.append(face)
    return load_faces, fixed_faces, total_area_load

def assemble_load_vector(points, faces, dir_vec, total_force, total_area):
    n_nodes = points.shape[0]
    node_area = np.zeros(n_nodes, dtype=np.float64)
    for face in faces:
        i0, i1, i2 = face
        p0, p1, p2 = points[[i0, i1, i2]]
        area = 0.5 * np.linalg.norm(np.cross(p1 - p0, p2 - p0))
        node_area[i0] += area / 3.0
        node_area[i1] += area / 3.0
        node_area[i2] += area / 3.0

    traction = total_force / total_area
    load = np.zeros(n_nodes * 3, dtype=np.float64)
    for idx in range(n_nodes):
        if node_area[idx] > 1e-12:
            load[3 * idx:3 * idx + 3] = traction * dir_vec * node_area[idx]
    return load

def assemble_stiffness_matrix(meshio_mesh):
    """Assemble global stiffness matrix for a meshio mesh.

    Parameters
    ----------
    meshio_mesh : meshio.Mesh
        Meshio mesh containing tetrahedra.
    """
    sk_mesh = from_meshio(meshio_mesh)
    elem = ElementVector(ElementTetP1())
    basis = Basis(sk_mesh, elem)
    weak = linear_elasticity(lam, mu)
    return asm(weak, basis, basis)

def solve_K_b(K, b, fixed):
    n = K.shape[0]
    mask = np.ones(n, dtype=bool)
    mask[fixed] = False
    A = K[mask][:, mask]
    rhs = b[mask]
    sol = sla.spsolve(A, rhs)
    u = np.zeros(n)
    u[mask] = sol
    return u

def output_results(max_c, max_l):
    data = {"outputs": {"max_displacement_compression_mm": float(max_c),
                         "max_displacement_lateral_mm": float(max_l)}}
    with open(RESULTS_FILE, 'w') as f:
        json.dump(data, f, separators=(',', ':'))

def output_environment(coarse_nodes, coarse_elems, fine_nodes, fine_elems):
    env = {
        "solver": "scikit-fem",
        "solver_version": "12.0.2",
        "scipy_version": scipy.__version__,
        "numpy_version": np.__version__,
        "python_version": os.sys.version.split()[0],
        "mesh_size_coarse_mm": SIZE_COARSE,
        "mesh_size_fine_mm": SIZE_FINE,
        "nodes_coarse": coarse_nodes,
        "elements_coarse": coarse_elems,
        "nodes_fine": fine_nodes,
        "elements_fine": fine_elems,
        "material_properties": {"E_N_per_mm2": E, "nu": nu},
        "units": {"length": "mm", "force": "N", "stress": "N/mm^2"},
        "boundary_mapping": {"fixed_y": Y_FIXED, "free_y": Y_FREE}
    }
    with open(ENV_FILE, 'w') as f:
        json.dump(env, f, separators=(',', ':'))

def output_refinement(coarse_nodes, coarse_elems, fine_nodes, fine_elems,
                       coarse_max_c, coarse_max_l, fine_max_c, fine_max_l):
    data = {
        "coarse": {"num_nodes": coarse_nodes, "num_elements": coarse_elems,
                    "max_disp_compression_mm": float(coarse_max_c),
                    "max_disp_lateral_mm": float(coarse_max_l)},
        "fine": {"num_nodes": fine_nodes, "num_elements": fine_elems,
                  "max_disp_compression_mm": float(fine_max_c),
                  "max_disp_lateral_mm": float(fine_max_l)}
    }
    with open(REFINE_FILE, 'w') as f:
        json.dump(data, f, separators=(',', ':'))

def output_solver_log(K_fine, dirichlet_dofs):
    lines = ["Solver log generated by main.py",
             f"NumPy version: {np.__version__}",
             f"Scipy version: {scipy.__version__}",
             f"Gmsh version: {gmsh.__version__}",
             f"Fine matrix shape: {K_fine.shape}",
             f"Fine matrix nnz: {K_fine.nnz}",
             f"Dirichlet DOFs applied: {len(dirichlet_dofs)}"]
    with open(SOLVER_LOG, 'w') as f:
        f.write("\n".join(lines))

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
if __name__ == "__main__":
    copy_step_file()
    generate_mesh(INPUT_STEP, COARSE_MESH, SIZE_COARSE)
    generate_mesh(INPUT_STEP, FINE_MESH, SIZE_FINE)
    shutil.move(FINE_MESH, USE_MESH)

    # Load meshes
    coarse_mesh = meshio.read(COARSE_MESH)
    fine_mesh = meshio.read(USE_MESH)

    pts_coarse, tets_coarse = coarse_mesh.points, coarse_mesh.cells_dict['tetra']
    pts_fine, tets_fine = fine_mesh.points, fine_mesh.cells_dict['tetra']
    coarse_nodes, coarse_elems = pts_coarse.shape[0], tets_coarse.shape[0]
    fine_nodes, fine_elems = pts_fine.shape[0], tets_fine.shape[0]

    # coarse
    K_coarse = assemble_stiffness_matrix(coarse_mesh)
    fixed_nodes_coarse = np.where(np.abs(pts_coarse[:, 1] - Y_FIXED) < TOL)[0]
    fixed_dofs_coarse = np.concatenate([3 * fixed_nodes_coarse,
                                       3 * fixed_nodes_coarse + 1,
                                       3 * fixed_nodes_coarse + 2])
    load_faces_coarse, _, area_load_coarse = extract_boundary_facet_info(
        pts_coarse, tets_coarse, Y_FREE, Y_FIXED)
    load_c_coarse = assemble_load_vector(pts_coarse, load_faces_coarse,
                                         np.array([0.0, -1.0, 0.0]),
                                         total_force, area_load_coarse)
    load_l_coarse = assemble_load_vector(pts_coarse, load_faces_coarse,
                                         np.array([1.0, 0.0, 0.0]),
                                         total_force, area_load_coarse)
    disp_c_coarse = solve_K_b(K_coarse, load_c_coarse, fixed_dofs_coarse)
    disp_l_coarse = solve_K_b(K_coarse, load_l_coarse, fixed_dofs_coarse)
    coarse_max_c = np.linalg.norm(disp_c_coarse.reshape(-1, 3), axis=1).max()
    coarse_max_l = np.linalg.norm(disp_l_coarse.reshape(-1, 3), axis=1).max()

    # fine mesh
    K_fine = assemble_stiffness_matrix(fine_mesh)
    fixed_nodes_fine = np.where(np.abs(pts_fine[:, 1] - Y_FIXED) < TOL)[0]
    fixed_dofs_fine = np.concatenate([3 * fixed_nodes_fine,
                                     3 * fixed_nodes_fine + 1,
                                     3 * fixed_nodes_fine + 2])
    load_faces_fine, _, area_load_fine = extract_boundary_facet_info(
        pts_fine, tets_fine, Y_FREE, Y_FIXED)
    load_c_fine = assemble_load_vector(pts_fine, load_faces_fine,
                                       np.array([0.0, -1.0, 0.0]),
                                       total_force, area_load_fine)
    load_l_fine = assemble_load_vector(pts_fine, load_faces_fine,
                                       np.array([1.0, 0.0, 0.0]),
                                       total_force, area_load_fine)
    disp_c_fine = solve_K_b(K_fine, load_c_fine, fixed_dofs_fine)
    disp_l_fine = solve_K_b(K_fine, load_l_fine, fixed_dofs_fine)
    fine_max_c = np.linalg.norm(disp_c_fine.reshape(-1, 3), axis=1).max()
    fine_max_l = np.linalg.norm(disp_l_fine.reshape(-1, 3), axis=1).max()

    # Save results
    output_results(fine_max_c, fine_max_l)
    np.savez(FIELDS_FILE,
             node_ids=np.arange(fine_nodes, dtype=np.int32),
             coordinates=pts_fine,
             disp_compression=disp_c_fine.reshape(-1, 3),
             disp_lateral=disp_l_fine.reshape(-1, 3))
    output_environment(coarse_nodes, coarse_elems, fine_nodes, fine_elems)
    output_refinement(coarse_nodes, coarse_elems, fine_nodes, fine_elems,
                      coarse_max_c, coarse_max_l, fine_max_c, fine_max_l)
    output_solver_log(K_fine, fixed_dofs_fine)
