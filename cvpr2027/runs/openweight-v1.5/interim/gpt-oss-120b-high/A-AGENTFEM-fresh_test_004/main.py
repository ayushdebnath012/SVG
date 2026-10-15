'''main.py
Finite element analysis for the AgentFEM bracket (task A-AGENTFEM-fresh_test_004).

The script performs the following steps:

1. Read the CAD geometry (STEP) from the input directory and copy it to the
   output as part.step.
2. Generate a quadratic tetrahedral volume mesh using Gmsh. Two meshes are
   generated for a simple mesh‑convergence study (clmax = 14 mm coarse, and
   clmax = 9 mm nominal – the one used for the reported results). The nominal
   mesh is saved as mesh.msh.
3. Import the mesh into scikit‑fem (MeshTet2) which provides the quadratic
   element ``ElementTetP2``.
4. Build a vector valued finite‑element basis by wrapping ``ElementTetP2`` in
   ``ElementVector``. This yields three displacement components (u_x, u_y, u_z)
   with both vertex and edge degrees‑of‑freedom.
5. Assemble the linear elasticity stiffness matrix using the material’s
   Lame parameters derived from E = 70 GPa and ν = 0.33.
6. Apply Dirichlet boundary conditions – all nodes (including edge mid‑nodes)
   lying on the plane ``z = 0`` are fixed (zero displacement).
7. Apply a uniform downward traction ``p = 1.98728 MPa`` on the top face
   (plane ``z = 189 mm``). The traction vector is ``t = [0, 0, -p]``.
8. Solve the linear system for the displacement field.
9. Post‑process the solution to obtain:
   * ``seat_mean_displacement_mm`` – mean of ``-u_z`` over the top surface.
   * ``max_displacement_mm`` – maximum norm of the displacement vector over
     the whole model.
10. Store the results in the required artefacts:
    * ``results.json`` – the two requested output quantities.
    * ``mesh.msh`` – the quadratic mesh used for the final analysis.
    * ``fields.npz`` – node IDs, coordinates, and displacements.
    * ``solver.log`` – a short log of the solver steps and library versions.
    * ``refinement.json`` – data for the coarse and nominal meshes.
    * ``environment.json`` – library versions, units, and modelling assumptions.

The script is deterministic and reproducible; it does not rely on any external
network resources. All generated artefacts are written to the current working
directory, which is set by the evaluation framework to ``CADFEM_OUTPUT_DIR``.
''' 

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import meshio
import skfem.io as skfem_io
from skfem import CellBasis, LinearForm
from skfem.element import ElementTetP2, ElementVector
from skfem.models import linear_elasticity
from skfem.utils import condense, solve

# ---------------------------------------------------------------------------
# Configuration / material data
# ---------------------------------------------------------------------------
E_GPa = 70.0  # Young's modulus in GPa
E = E_GPa * 1e3  # Convert to N/mm^2 (since 1 GPa = 1000 N/mm²)
nu = 0.33
# Lame parameters (N/mm²)
Lambda = E * nu / ((1 + nu) * (1 - 2 * nu))
Mu = E / (2 * (1 + nu))

# Load (traction) on the top seat face
traction_pressure_MPa = 1.98728  # MPa = N/mm²
traction = traction_pressure_MPa  # N/mm² (downward)

# Geometry / boundary locations (mm)
Z_BOTTOM = 0.0
Z_TOP = 189.0
TOL_Z = 1.0e-3  # tolerance for identifying planar faces (mm)

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
log.addHandler(handler)

def run_gmsh(clmax: float, mesh_path: Path, step_path: Path) -> None:
    '''Generate a quadratic tetrahedral mesh with Gmsh.

    Parameters
    ----------
    clmax:
        Target maximum element size (characteristic length) in mm.
    mesh_path:
        Destination file for the generated .msh mesh.
    step_path:
        Path to the input STEP geometry.
    '''
    # Gmsh command line options:
    #   -3      : 3‑D mesh generation
    #   -order 2: second‑order (quadratic) elements
    #   -clmax  : target maximum element size
    #   -format msh2 : write Gmsh v2 ASCII format (easier for skfem.io)
    cmd = [
        'gmsh',
        '-3',
        '-order',
        '2',
        '-clmax',
        f'{clmax}',
        '-format',
        'msh2',
        '-o',
        str(mesh_path),
        str(step_path),
    ]
    log.info('Running Gmsh: %s', ' '.join(cmd))
    subprocess.run(cmd, check=True)

def build_basis(mesh) -> CellBasis:
    '''Create a vector‑valued quadratic tetrahedral basis.

    The underlying scalar element is ElementTetP2 (10‑node tetrahedron).
    ElementVector replicates the scalar element for the three displacement
    components.
    '''
    scalar_elem = ElementTetP2()
    vec_elem = ElementVector(scalar_elem, dim=3)
    return CellBasis(mesh, vec_elem)

def identify_boundary_nodes(mesh, z_value: float) -> np.ndarray:
    '''Return the global node indices whose z coordinate equals z_value.

    Both vertex nodes and edge mid‑nodes are considered because the mesh
    contains them in mesh.p (the array is ordered as vertices first, then
    edge nodes). A simple absolute tolerance is used.
    '''
    z_coords = mesh.p[2, :]
    return np.where(np.abs(z_coords - z_value) < TOL_Z)[0]

def identify_top_facets(mesh) -> np.ndarray:
    '''Return facet indices belonging to the top z = Z_TOP plane.

    The mesh stores all boundary facets in mesh.facets; mesh.boundary_facets()
    returns the indices of those facets that lie on the external boundary.
    A facet is accepted if all its corner vertices have a z coordinate
    within TOL_Z of Z_TOP.
    '''
    boundary_facet_ids = mesh.boundary_facets()
    facet_vertices = mesh.facets[:, boundary_facet_ids]  # shape (3, n_facets)
    facet_z = mesh.p[2, facet_vertices]  # shape (3, n_facets)
    top_mask = np.all(np.abs(facet_z - Z_TOP) < TOL_Z, axis=0)
    return boundary_facet_ids[top_mask]

def assemble_system(basis: CellBasis, mesh, top_facet_ids: np.ndarray) -> tuple:
    '''Assemble stiffness matrix, load vector, and Dirichlet DOF list.

    Returns
    -------
    A : scipy.sparse.csr_matrix
       Global stiffness matrix.
    f : np.ndarray
       Global load vector (Neumann traction on the top surface).
    fixed_dofs : np.ndarray
       Indices of DOFs that are prescribed (zero displacement on the bottom).
    '''
    # Stiffness matrix (linear elasticity)
    weak = linear_elasticity(Lambda, Mu)
    A = weak.assemble(basis)

    # Neumann traction on top surface
    @LinearForm
    def traction_form(v, w):
        # Apply constant traction vector t = [0, 0, -traction]
        return -traction * v[2]

    facet_basis = basis.boundary(facets=top_facet_ids)
    f = traction_form.assemble(facet_basis)

    # Dirichlet conditions – all DOFs at nodes on the bottom plane are zero
    bottom_node_indices = identify_boundary_nodes(mesh, Z_BOTTOM)
    n_vertices = mesh.nvertices
    fixed_dofs: List[int] = []
    for nid in bottom_node_indices:
        if nid < n_vertices:
            fixed_dofs.extend(basis.dofs.nodal_dofs[:, nid])
        else:
            edge_id = nid - n_vertices
            # Some higher‑order nodes (e.g., interior bubble nodes) may be
            # present beyond the edge nodes; they do not have associated DOFs
            # in the quadratic element and are therefore ignored for Dirichlet
            # constraints.
            if edge_id < mesh.nedges:
                fixed_dofs.extend(basis.dofs.edge_dofs[:, edge_id])
    fixed_dofs = np.array(fixed_dofs, dtype=np.int32)

    return A, f, fixed_dofs

def solve_system(A, f, fixed_dofs, basis: CellBasis) -> np.ndarray:
    '''Solve the linear system with Dirichlet boundary conditions.

    Parameters
    ----------
    A, f:
        System matrix and load vector.
    fixed_dofs:
        Indices of DOFs that are prescribed (zero displacement).
    basis:
        The finite‑element basis (required only for shape of the solution vector).

    Returns
    -------
    u : np.ndarray
        Full displacement vector (including prescribed DOFs).
    '''
    x_known = np.zeros(basis.N, dtype=np.float64)
    A_cond, f_cond, x_known, I = condense(A, f, D=fixed_dofs, x=x_known)
    u_unknown = solve(A_cond, f_cond)
    u = x_known.copy()
    u[I] = u_unknown
    return u

def postprocess_results(u: np.ndarray, basis: CellBasis, mesh) -> Dict[str, float]:
    '''Compute the requested output quantities.

    Returns a dictionary containing seat_mean_displacement_mm and max_displacement_mm.
    '''
    n_vertices = mesh.nvertices
    # Vertex DOFs (3 per vertex)
    ux_vert = u[basis.dofs.nodal_dofs[0, :]]
    uy_vert = u[basis.dofs.nodal_dofs[1, :]]
    uz_vert = u[basis.dofs.nodal_dofs[2, :]]
    # Edge DOFs (3 per edge)
    ux_edge = u[basis.dofs.edge_dofs[0, :]]
    uy_edge = u[basis.dofs.edge_dofs[1, :]]
    uz_edge = u[basis.dofs.edge_dofs[2, :]]

    disp = np.vstack(
        (
            np.concatenate([ux_vert, ux_edge]),
            np.concatenate([uy_vert, uy_edge]),
            np.concatenate([uz_vert, uz_edge]),
        )
    )
    disp_norm = np.linalg.norm(disp, axis=0)
    max_disp = float(np.max(disp_norm))

    top_facet_ids = identify_top_facets(mesh)
    facet_basis = basis.boundary(facets=top_facet_ids)
    u_top = facet_basis.interpolate(u)
    dz = u_top[2]
    integral = np.sum(-dz * facet_basis.dx)
    area = np.sum(facet_basis.dx)
    seat_mean = float(integral / area)

    return {
        'seat_mean_displacement_mm': seat_mean,
        'max_displacement_mm': max_disp,
    }

def write_fields_npz(mesh, u, basis: CellBasis, filename: Path) -> None:
    """Write node IDs, coordinates, and displacement vectors to a compressed NPZ.
    The arrays are:
    * ``node_id`` – integer IDs (zero based) for *all* mesh nodes.
    * ``coords`` – ``(N, 3)`` array of node coordinates in mm.
    * ``displacement`` – ``(N, 3)`` array of displacement components in mm.
    Nodes that do not possess degrees of freedom in the quadratic tetrahedral
    element (e.g., higher‑order surface nodes) receive a zero displacement.
    """
    total_nodes = mesh.p.shape[1]
    n_vertices = mesh.nvertices
    n_edges = mesh.nedges

    # Vertex DOFs (3 per vertex)
    ux_vert = u[basis.dofs.nodal_dofs[0, :]]
    uy_vert = u[basis.dofs.nodal_dofs[1, :]]
    uz_vert = u[basis.dofs.nodal_dofs[2, :]]
    # Edge DOFs (3 per edge)
    ux_edge = u[basis.dofs.edge_dofs[0, :]]
    uy_edge = u[basis.dofs.edge_dofs[1, :]]
    uz_edge = u[basis.dofs.edge_dofs[2, :]]

    # Assemble a full displacement field sized to the total number of mesh nodes.
    disp_full = np.zeros((total_nodes, 3), dtype=np.float64)
    # Assign vertex displacements (indices 0 .. n_vertices-1)
    disp_full[:n_vertices, 0] = ux_vert
    disp_full[:n_vertices, 1] = uy_vert
    disp_full[:n_vertices, 2] = uz_vert
    # Assign edge displacements (indices n_vertices .. n_vertices+n_edges-1)
    edge_start = n_vertices
    edge_end = n_vertices + n_edges
    disp_full[edge_start:edge_end, 0] = ux_edge
    disp_full[edge_start:edge_end, 1] = uy_edge
    disp_full[edge_start:edge_end, 2] = uz_edge
    # Remaining nodes (e.g., face mid‑nodes) keep zero displacement.

    node_id = np.arange(total_nodes, dtype=np.int32)
    coords = mesh.p.T
    np.savez_compressed(filename, node_id=node_id, coords=coords, displacement=disp_full)

def write_results_json(results: Dict[str, float], filename: Path) -> None:
    """Write the required ``results.json`` file.

    The benchmark contract mandates that only the explicitly requested
    output quantities appear under the ``outputs`` key. ``results`` may contain
    auxiliary data (e.g., mesh statistics) used for the refinement report, but
    these must be omitted from ``results.json``.
    """
    # The task requests exactly two scalar results.
    required_keys = (
        "seat_mean_displacement_mm",
        "max_displacement_mm",
    )
    out = {"outputs": {k: results[k] for k in required_keys if k in results}}
    filename.write_text(json.dumps(out, indent=2))

def write_refinement_json(coarse: Dict[str, float], fine: Dict[str, float], filename: Path) -> None:
    '''Write a simple refinement report with two mesh resolutions.

    coarse and fine are dictionaries that already contain the keys
    'seat_mean_displacement_mm' and 'max_displacement_mm' as well as
    'node_count' and 'element_count'.
    '''
    report = {
        'refinements': [
            {'name': 'coarse', **coarse},
            {'name': 'nominal', **fine},
        ]
    }
    filename.write_text(json.dumps(report, indent=2))

def write_environment_json(filename: Path) -> None:
    '''Document library versions and modelling assumptions.
    The content is intentionally concise but contains the fields required by
    the benchmark contract.
    '''
    env = {
        'libraries': {
            'python': sys.version.split()[0],
            'numpy': np.__version__,
            'scipy': sys.modules['scipy'].__version__,
            'meshio': sys.modules['meshio'].__version__,
            'skfem': sys.modules['skfem'].__version__,
            'gmsh': '4.15',
        },
        'units': {
            'length': 'mm',
            'force': 'N',
            'stress': 'MPa',
        },
        'material': {
            'type': 'linear isotropic elastic',
            'E': E,
            'nu': nu,
        },
        'boundary_conditions': {
            'fixed': 'z=0 plane (all displacement components = 0)',
            'traction': {
                'magnitude': traction,
                'direction': '-z',
                'applied_on': 'z=189 plane (top seat face)',
            },
        },
        'element': 'quadratic tetrahedron (10-node) – ElementTetP2',
        'analysis': 'static linear elasticity',
    }
    filename.write_text(json.dumps(env, indent=2))

def main() -> None:
    # Resolve input / output paths
    input_dir = Path(os.getenv('CADFEM_INPUT_DIR', '.'))
    geometry_path = input_dir / 'geometry.step'
    if not geometry_path.is_file():
        log.error('Input geometry file %s not found', geometry_path)
        sys.exit(1)

    # Output files (written to the current working directory which is the
    # designated CADFEM_OUTPUT_DIR)
    part_step_path = Path('part.step')
    mesh_nominal_path = Path('mesh.msh')
    results_json_path = Path('results.json')
    fields_path = Path('fields.npz')
    solver_log_path = Path('solver.log')
    refinement_json_path = Path('refinement.json')
    environment_json_path = Path('environment.json')

    # Copy the STEP geometry to part.step (required artefact)
    part_step_path.write_bytes(geometry_path.read_bytes())
    log.info('Copied input geometry to %s', part_step_path)

    # Perform analyses for two mesh resolutions (coarse and nominal)
    mesh_sizes = {'coarse': 14.0, 'nominal': 9.0}
    analysis_data: Dict[str, Dict] = {}

    for label, clmax in mesh_sizes.items():
        log.info('Generating %s mesh (clmax=%.1f mm)', label, clmax)
        mesh_path = Path(f'mesh_{label}.msh')
        run_gmsh(clmax, mesh_path, geometry_path)

        mesh = skfem_io.from_meshio(meshio.read(str(mesh_path)))
        basis = build_basis(mesh)
        top_facet_ids = identify_top_facets(mesh)
        A, f, fixed_dofs = assemble_system(basis, mesh, top_facet_ids)
        u = solve_system(A, f, fixed_dofs, basis)
        results = postprocess_results(u, basis, mesh)
        results.update({'node_count': int(mesh.p.shape[1]), 'element_count': int(mesh.t.shape[1])})
        analysis_data[label] = results

        if label == 'nominal':
            mesh_path.rename(mesh_nominal_path)
            write_fields_npz(mesh, u, basis, fields_path)
            solver_log_path.write_text(
                f'Mesh generation (clmax={clmax} mm) and static linear elasticity solution.\n'
                f'Number of vertices: {mesh.nvertices}\n'
                f'Number of edges (mid‑nodes): {mesh.nedges}\n'
                f'Total DOFs (vector problem): {basis.N}\n'
                f'Maximum element size (target): {clmax} mm\n'
                f'Linear solver: direct sparse (SciPy)\n'
            )
            write_environment_json(environment_json_path)

    # Write the primary results (from the nominal mesh) and refinement data
    write_results_json(analysis_data['nominal'], results_json_path)
    write_refinement_json(analysis_data['coarse'], analysis_data['nominal'], refinement_json_path)
    log.info('All artefacts generated successfully.')
    # Remove the temporary coarse mesh file – it is not part of the required artefacts.
    coarse_mesh_path = Path('mesh_coarse.msh')
    if coarse_mesh_path.is_file():
        try:
            coarse_mesh_path.unlink()
            log.debug('Deleted temporary coarse mesh file %s', coarse_mesh_path)
        except Exception as e:
            log.warning('Failed to delete temporary coarse mesh file %s: %s', coarse_mesh_path, e)

if __name__ == '__main__':
    main()
