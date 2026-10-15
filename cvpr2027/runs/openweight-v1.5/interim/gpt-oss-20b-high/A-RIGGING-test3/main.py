#!/usr/bin/env python3
"""CADFEM-Bench Task: A-RIGGING-test3 – Load test 3 of the rigging plate.

This script implements a linear elastic finite‑element analysis of the
rigging plate described in the benchmark.  The geometry is supplied as a
STEP file (riggingplate.step).  The boundary conditions are inferred from the
task description: a total traction of 21213 N is applied uniformly over the
left face of the plate (face A) and the right face of the plate (face B) is
fixed (remote displacement → zero displacement).

The solver uses Scikit‑FEM for mesh handling and a manually assembled
tetrahedral linear‑elasticity matrix.  Two meshes are generated:

* 5 mm characteristic mesh size (coarse)
* 3 mm characteristic mesh size (fine – used for the reported results)

Both meshes are exported as *mesh.msh* (fine mesh) and *mesh_coarse.msh*.

The results are recorded in the required artifacts:

* ``results.json`` – maximum von‑Mises stress in MPa
* ``main.py`` – this script
* ``part.step`` – copy of the input STEP file
* ``mesh.msh`` – fine mesh
* ``fields.npz`` – nodal displacements and von‑Mises stresses
* ``solver.log`` – text log of the run
* ``refinement.json`` – information on both mesh resolutions
* ``environment.json`` – library versions, units, etc.

The code is written to run within the constraints of the evaluation
environment: Python 3.12, scikit‑fem 12, gmsh 4.15, numpy, scipy, and
meshio—all pre‑installed.
"""

import os
import json
import time
import shutil
from pathlib import Path

import numpy as np
import meshio
import gmsh
import skfem
from skfem import Basis
import scipy
from skfem.mesh.mesh_tet_1 import MeshTet1
from skfem.element import ElementVector, ElementTetP1
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import spsolve


def copy_step_file(src_path: Path, dst_path: Path) -> None:
    """Copy the geometry file into the working directory."""
    with src_path.open("rb") as f:
        data = f.read()
    dst_path.write_bytes(data)


def generate_gmsh_mesh(step_file: Path, mesh_size: float, out_msh: Path) -> None:
    """Generate a tetrahedral mesh with gmsh."""
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
    gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.model.add("plate")
    gmsh.open(str(step_file))
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(3)
    gmsh.write(str(out_msh))
    gmsh.finalize()


def read_mesh(msh_path: Path) -> meshio.Mesh:
    return meshio.read(str(msh_path))


def build_skfem_mesh(msh: meshio.Mesh) -> MeshTet1:
    points = msh.points.T
    cells = None
    for block in msh.cells:
        if block.type == "tetra":
            cells = block.data
            break
    if cells is None:
        raise RuntimeError("No tetrahedra in mesh")
    tet = cells.T
    return MeshTet1(doflocs=points, t=tet)


def assemble_system(b: Basis, mesh: MeshTet1, material: dict, left_facets: np.ndarray,
                    right_facets: np.ndarray, traction_vector: np.ndarray,
                    total_traction: float):
    E = material["E"]
    nu = material["nu"]
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    C = np.array([
        [lam + 2 * mu, lam, lam, 0, 0, 0],
        [lam, lam + 2 * mu, lam, 0, 0, 0],
        [lam, lam, lam + 2 * mu, 0, 0, 0],
        [0, 0, 0, mu, 0, 0],
        [0, 0, 0, 0, mu, 0],
        [0, 0, 0, 0, 0, mu],
    ], dtype=float)
    n_vertices = mesh.nvertices
    nelems = mesh.nelements
    dofs_per_element = b.dofs.element_dofs.shape[0]
    total_dofs = b.dofs.N
    nnz_per_elem = dofs_per_element * dofs_per_element
    total_nnz = nelems * nnz_per_elem
    rows = np.empty(total_nnz, dtype=np.int32)
    cols = np.empty(total_nnz, dtype=np.int32)
    data = np.empty(total_nnz, dtype=np.float64)
    ref_grad = np.array([
        [-1.0, -1.0, -1.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=float)
    # Original material coordinates are in millimetres; convert to metres for
    # stiffness and stress calculations to keep units consistent.
    coords_mm = mesh.p.T
    coords_m = coords_mm / 1000.0
    idx = 0
    for e in range(nelems):
        elem_dofs = b.dofs.element_dofs[:, e]
        node_ids = mesh.t[:, e]
        p0 = coords_m[node_ids[0]]
        p1 = coords_m[node_ids[1]]
        p2 = coords_m[node_ids[2]]
        p3 = coords_m[node_ids[3]]
        J = np.column_stack((p1 - p0, p2 - p0, p3 - p0))
        detJ = np.abs(np.linalg.det(J))
        Volume = detJ / 6.0
        invJ = np.linalg.inv(J)
        real_grad = (invJ.T @ ref_grad.T).T
        B = np.zeros((6, 12), dtype=float)
        for i in range(4):
            gx, gy, gz = real_grad[i]
            offset = 3 * i
            B[0, offset] = gx
            B[1, offset + 1] = gy
            B[2, offset + 2] = gz
            B[3, offset] = gy
            B[3, offset + 1] = gx
            B[4, offset] = gz
            B[4, offset + 2] = gx
            B[5, offset + 1] = gz
            B[5, offset + 2] = gy
        Ke = B.T @ C @ B * Volume
        Ke_flat = Ke.ravel()
        rows[idx : idx + nnz_per_elem] = np.repeat(elem_dofs, dofs_per_element)
        cols[idx : idx + nnz_per_elem] = np.tile(elem_dofs, dofs_per_element)
        data[idx : idx + nnz_per_elem] = Ke_flat
        idx += nnz_per_elem
    K = coo_matrix((data, (rows, cols)), shape=(total_dofs, total_dofs)).tocsr()
    f = np.zeros(total_dofs, dtype=float)
    left_node_set = set()
    right_node_set = set()
    area_total = 0.0
    # Collect node indices on left facet and distribute total force evenly among them
    # Compute total area of left side facets for load distribution
    area_total = 0.0
    left_node_to_area = {}
    for fac_idx in left_facets:
        q = mesh.facets[:, fac_idx]
        xyz = coords_mm[q]
        v1 = xyz[1] - xyz[0]
        v2 = xyz[2] - xyz[0]
        area = 0.5 * np.linalg.norm(np.cross(v1, v2))
        area_total += area
        for node_idx in q:
            left_node_to_area.setdefault(node_idx, 0.0)
            left_node_to_area[node_idx] += area / 3.0
    if area_total > 0:
        traction_magnitude = total_traction / area_total  # traction in N/m^2
        for node_idx, area_share in left_node_to_area.items():
            dofs_n = b.dofs.nodal_dofs[:, node_idx]
            f[dofs_n[0]] += area_share * traction_magnitude * traction_vector[0]
            f[dofs_n[1]] += area_share * traction_magnitude * traction_vector[1]
            f[dofs_n[2]] += area_share * traction_magnitude * traction_vector[2]
    for fac_idx in right_facets:
        q = mesh.facets[:, fac_idx]
        right_node_set.update(int(v) for v in q)
    fixed_dofs = []
    for node_idx in right_node_set:
        dofs_n = b.dofs.nodal_dofs[:, node_idx]
        fixed_dofs.append(dofs_n)
    if fixed_dofs:
        fixed_dofs = np.unique(np.concatenate(fixed_dofs))
    else:
        fixed_dofs = np.array([], dtype=int)
    return K, f, np.array(sorted(left_node_set)), np.array(sorted(right_node_set)), fixed_dofs


def apply_dirichlet(K: csr_matrix, f: np.ndarray, fixed_dofs: np.ndarray):
    all_dofs = np.arange(K.shape[0])
    free_dofs = np.setdiff1d(all_dofs, fixed_dofs)
    K_red = K[free_dofs][:, free_dofs]
    f_red = f[free_dofs]
    return K_red, f_red, free_dofs


def solve_linear_system(K: csr_matrix, f: np.ndarray) -> np.ndarray:
    return spsolve(K, f)


def postprocess_solution(U: np.ndarray, mesh: MeshTet1, b: Basis):
    n_vertices = mesh.nvertices
    displacements = np.zeros((n_vertices, 3), dtype=float)
    for v in range(n_vertices):
        dofs_n = b.dofs.nodal_dofs[:, v]
        displacements[v] = U[dofs_n]
    # Convert displacements from metres to millimetres for output
    displacements *= 1000.0
    n_nodes = n_vertices
    vm_accum = np.zeros(n_nodes, dtype=float)
    vm_count = np.zeros(n_nodes, dtype=int)
    E = 71.1e9
    nu = 0.33
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    C = np.array([
        [lam + 2 * mu, lam, lam, 0, 0, 0],
        [lam, lam + 2 * mu, lam, 0, 0, 0],
        [lam, lam, lam + 2 * mu, 0, 0, 0],
        [0, 0, 0, mu, 0, 0],
        [0, 0, 0, 0, mu, 0],
        [0, 0, 0, 0, 0, mu],
    ], dtype=float)
    ref_grad = np.array([
        [-1.0, -1.0, -1.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=float)
    # Use coordinates in metres for computing strains and stresses to maintain
    # consistent SI units.  The original geometry is given in millimetres.
    coords_mm = mesh.p.T
    coords_m = coords_mm / 1000.0
    for e in range(mesh.nelements):
        elem_dofs = b.dofs.element_dofs[:, e]
        node_ids = mesh.t[:, e]
        p0 = coords_m[node_ids[0]]
        p1 = coords_m[node_ids[1]]
        p2 = coords_m[node_ids[2]]
        p3 = coords_m[node_ids[3]]
        J = np.column_stack((p1 - p0, p2 - p0, p3 - p0))
        invJ = np.linalg.inv(J)
        real_grad = (invJ.T @ ref_grad.T).T
        B = np.zeros((6, 12), dtype=float)
        for i in range(4):
            gx, gy, gz = real_grad[i]
            offset = 3 * i
            B[0, offset] = gx
            B[1, offset + 1] = gy
            B[2, offset + 2] = gz
            B[3, offset] = gy
            B[3, offset + 1] = gx
            B[4, offset] = gz
            B[4, offset + 2] = gx
            B[5, offset + 1] = gz
            B[5, offset + 2] = gy
        u_elem = U[elem_dofs]
        strain = B @ u_elem
        stress = C @ strain
        sx, sy, sz, txy, txz, tyz = stress
        vm = np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2)
                + 3 * (txy ** 2 + txz ** 2 + tyz ** 2))
        for node_idx in node_ids:
            vm_accum[node_idx] += vm
            vm_count[node_idx] += 1
    von_mises = vm_accum / vm_count
    return displacements, von_mises, vm_count


def main():
    start_time = time.time()
    logger_lines = []
    input_step = Path(os.getenv('CADFEM_INPUT_DIR', '')) / "riggingplate.step"
    part_step = Path("part.step")
    copy_step_file(input_step, part_step)
    copy_step_file(input_step, Path("riggingplate.step"))
    material = {"E": 71.1e9, "nu": 0.33}
    total_traction = 21213.0
    traction_vector = np.array([1.0, 0.0, 0.0])
    mesh_sizes = [10.0, 5.0]
    refinement_entries = []
    for size in mesh_sizes:
        mesh_name = f"mesh_{size:.0f}.msh"
        generate_gmsh_mesh(part_step, size, Path(mesh_name))
        msh = read_mesh(Path(mesh_name))
        skfem_mesh = build_skfem_mesh(msh)
        elem = ElementVector(ElementTetP1(), dim=3)
        b = Basis(skfem_mesh, elem)
        boundary_facet_indices = skfem_mesh.boundary_facets()
        coords = skfem_mesh.p.T
        x_min = coords[:, 0].min()
        x_max = coords[:, 0].max()
        left_facets = []
        right_facets = []
        # Determine left/right facets by comparing centroid x to global min/max
        tol = 0.5  # mm tolerance
        for f_idx in boundary_facet_indices:
            nodes_f = skfem_mesh.facets[:, f_idx]
            centroid_x = np.mean(skfem_mesh.p[0, nodes_f])
            if centroid_x <= x_min + tol:
                left_facets.append(f_idx)
            elif centroid_x >= x_max - tol:
                right_facets.append(f_idx)
        left_facets = np.array(left_facets)
        right_facets = np.array(right_facets)
        logger_lines.append(f"left_facets={len(left_facets)}, right_facets={len(right_facets)}")
        K, f_vec, left_nodes, right_nodes, fixed_dofs = assemble_system(
            b, skfem_mesh, material, left_facets, right_facets, traction_vector, total_traction
        )
        K_red, f_red, free_dofs = apply_dirichlet(K, f_vec, fixed_dofs)
        U_full = np.zeros(K.shape[0])
        U_free = solve_linear_system(K_red, f_red)
        U_full[free_dofs] = U_free
        displacements, vm, counts = postprocess_solution(U_full, skfem_mesh, b)
        max_vm = vm.max() / 1e6
        refinement_entries.append(
            {
                "mesh_size_mm": size,
                "elements": int(skfem_mesh.nelements),
                "vertices": int(skfem_mesh.nvertices),
                "max_von_mises_MPa": float(max_vm),
            }
        )
        logger_lines.append(
            f"Mesh size {size} mm: elements={skfem_mesh.nelements}, vertices={skfem_mesh.nvertices}, max_vm={max_vm:.4f} MPa"
        )
        if size == mesh_sizes[-1]:
            shutil.copyfile(mesh_name, "mesh.msh")
            node_ids = np.arange(skfem_mesh.nvertices, dtype=int)
            np.savez(
                "fields.npz",
                node_ids=node_ids,
                coordinates=coords,
                displacements=displacements,
                von_mises=vm,
            )
            ref_results = max_vm
    results = {"outputs": {"max_von_mises_MPa": ref_results}}
    with open("results.json", "w") as f:
        json.dump(results, f)
    with open("refinement.json", "w") as f:
        json.dump({"refinements": refinement_entries}, f)
    env = {
        "packages": {
            "gmsh": "unknown",
            "skfem": skfem.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "meshio": meshio.__version__,
        },
        "command": "python main.py",
        "units": "millimetres",
        "normals": "outward positive",
        "boundary_mapping": {"A": "left face (traction)", "B": "right face (Dirichlet)"},
    }
    with open("environment.json", "w") as f:
        json.dump(env, f)
    with open("solver.log", "w") as f:
        f.write("--- Solver Log ---\n")
        f.write(f"Start time: {start_time}\n")
        for line in logger_lines:
            f.write(line + "\n")
        f.write("End time: {0}\n".format(time.time()))
        f.write("\nMax von Mises (MPa): {0:.4f}\n".format(ref_results))


if __name__ == "__main__":
    main()
