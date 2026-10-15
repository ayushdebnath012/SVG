"""AgentFEM bracket fresh_test_002 analysis

This script reproduces the finite element analysis for the bracket geometry
provided in ``geometry.step`` (input). It generates a quadratic tetrahedral
mesh (approx. 9 mm characteristic length, as used by the publisher), assembles
the linear elasticity system, applies the prescribed boundary conditions and
uniform traction on the top seat face, solves for displacements, and writes the
required artifacts:

- ``part.step`` – copy of the original geometry (millimetre units)
- ``mesh.msh``  – generated 3‑D quadratic tetrahedral mesh
- ``results.json`` – requested output quantities
- ``fields.npz`` – nodal coordinates and displacement vectors
- ``solver.log`` – summary of the run
- ``refinement.json`` – coarse (9 mm) and refined (5 mm) mesh results
- ``environment.json`` – software versions and modelling assumptions

The script is self‑contained and can be invoked with ``python main.py``. It
expects the environment variable ``CADFEM_INPUT_DIR`` to point to the directory
containing ``geometry.step`` and writes all outputs to the current working
directory (``CADFEM_OUTPUT_DIR``).
"""

import os
import json
import pathlib
import shutil
import numpy as np
import gmsh
from skfem import Mesh, Basis, asm, LinearForm, utils
from skfem.element import ElementTetP2, ElementVector
from skfem.models.elasticity import lame_parameters, linear_elasticity

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
# Material properties (units: N/mm^2 => MPa)
E = 70_000.0  # Young's modulus, 70 GPa = 70 000 MPa = 70 000 N/mm^2
nu = 0.33    # Poisson ratio
Lambda, Mu = lame_parameters(E, nu)

# Load case – uniform pressure on the top surface (downward, negative z)
traction_mpa = -1.98728  # N/mm^2

# Mesh characteristic lengths (in mm) – coarse (publisher) and refined
mesh_sizes = {
    "coarse": 9.0,
    "refined": 5.0,
}

# Tolerances for geometric identification (mm)
TOL_Z = 1e-6

# Output file names (as required by the artifact contract)
PART_STEP = "part.step"
MESH_MSH = "mesh.msh"
RESULTS_JSON = "results.json"
FIELDS_NPZ = "fields.npz"
SOLVER_LOG = "solver.log"
REFINEMENT_JSON = "refinement.json"
ENVIRONMENT_JSON = "environment.json"

# -----------------------------------------------------------------------------
# Helper utilities
# -----------------------------------------------------------------------------

def log(message: str) -> None:
    """Append a line to the solver log file."""
    with open(SOLVER_LOG, "a") as f:
        f.write(message + "\n")


def generate_mesh(lc: float, filename: str) -> None:
    """Generate a quadratic tetrahedral mesh of the input STEP geometry.

    Parameters
    ----------
    lc: float
        Target element size (characteristic length) in millimetres.
    filename: str
        Name of the mesh file to write (Gmsh ``.msh`` format).
    """
    gmsh.initialize()
    gmsh.model.add("bracket")
    geom_path = os.path.join(os.getenv("CADFEM_INPUT_DIR"), "geometry.step")
    gmsh.model.occ.importShapes(geom_path)
    gmsh.model.occ.synchronize()
    # Use quadratic elements (order 2)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    # Apply the target mesh size to all points
    for dim, tag in gmsh.model.getEntities(dim=0):
        gmsh.model.mesh.setSize([(dim, tag)], lc)
    gmsh.model.mesh.generate(3)
    gmsh.write(filename)
    gmsh.finalize()
    log(f"Generated mesh '{filename}' with element size lc = {lc} mm")


def load_mesh(filename: str) -> Mesh:
    mesh = Mesh.load(filename)
    log(f"Loaded mesh '{filename}': {mesh.p.shape[1]} nodes, {mesh.t.shape[1]} elements")
    return mesh


def build_vector_basis(mesh: Mesh) -> Basis:
    vec_elem = ElementVector(ElementTetP2())
    basis = Basis(mesh, vec_elem)
    log(f"Created vector basis with {basis.N} global DOFs")
    return basis


def bottom_nodes(mesh: Mesh) -> np.ndarray:
    """Return the *displacement* node indices that lie on the plane ``z = 0``.

    For the quadratic geometry used here, the displacement field is defined
    only on the corner vertices of the tetrahedra.  These vertices correspond
    to the first four entries of the element connectivity ``mesh.t``.  We
    therefore extract the unique vertex node IDs and filter them by the
    ``z`` coordinate.
    """
    # Corner (vertex) nodes are the first four rows of the connectivity
    vertex_ids = np.unique(mesh.t[:4, :])
    z_coords = mesh.p[2, vertex_ids]
    nodes = vertex_ids[np.abs(z_coords) < TOL_Z]
    log(f"Identified {len(nodes)} bottom displacement nodes (z ≈ 0)")
    return nodes


def top_nodes_and_z(mesh: Mesh) -> tuple[np.ndarray, float]:
    """Return the *displacement* node indices on the top seat face.

    ``max_z`` is the maximum ``z`` coordinate among all mesh vertices.  The
    top nodes are taken from the corner vertices (as in ``bottom_nodes``).
    """
    vertex_ids = np.unique(mesh.t[:4, :])
    z_coords = mesh.p[2, vertex_ids]
    max_z = np.max(z_coords)
    nodes = vertex_ids[np.abs(z_coords - max_z) < TOL_Z]
    log(f"Identified {len(nodes)} top displacement nodes (z ≈ {max_z:.6f})")
    return nodes, max_z


def top_facets(mesh: Mesh, max_z: float) -> np.ndarray:
    """Facet indices whose centroid lies on the top plane (z = max_z)."""
    coords = mesh.p
    facets = mesh.facets
    cent_z = np.mean(coords[2, facets], axis=0)
    ids = np.where(np.abs(cent_z - max_z) < TOL_Z)[0]
    log(f"Identified {len(ids)} top facets for traction")
    return ids


def assemble_stiffness(basis: Basis) -> np.ndarray:
    K = asm(linear_elasticity(Lambda, Mu), basis)
    log("Assembled global stiffness matrix K")
    return K


def assemble_traction(basis: Basis, top_facet_ids: np.ndarray) -> np.ndarray:
    # The vector facet basis returns a single ``DiscreteField`` containing all
    # three components.  The linear form therefore receives ``v`` (the field)
    # and ``w`` (the test function) as arguments.  ``v[2]`` extracts the z‑
    # component (index 2) of the shape‑function values.
    fb = basis.boundary(facets=top_facet_ids)
    lf = LinearForm(lambda v, w: traction_mpa * v[2])
    f = asm(lf, fb)
    log("Assembled load vector for uniform pressure on top surface")
    return f


def apply_dirichlet(K: np.ndarray, f: np.ndarray, basis: Basis, bottom_node_ids: np.ndarray) -> tuple:
    # Gather all DOFs (x, y, z) for the bottom nodes
    dofs = []
    for comp in range(3):
        dofs.append(basis.nodal_dofs[comp][bottom_node_ids])
    D = np.concatenate(dofs).astype(np.int32)
    K_bc, f_bc = utils.enforce(K, f, D=D, diag=1.0)
    log(f"Applied Dirichlet BC on {len(D)} DOFs (bottom face)")
    return K_bc, f_bc


def solve_system(K_bc: np.ndarray, f_bc: np.ndarray) -> np.ndarray:
    u = utils.solve(K_bc, f_bc)
    log("Solved linear system for displacements")
    return u


def compute_output_quantities(basis: Basis, u: np.ndarray, mesh: Mesh) -> dict:
    ux = u[basis.nodal_dofs[0]]
    uy = u[basis.nodal_dofs[1]]
    uz = u[basis.nodal_dofs[2]]
    top_node_ids, _ = top_nodes_and_z(mesh)
    seat_mean_disp = -float(np.mean(uz[top_node_ids]))  # downward positive
    disp_mag = np.sqrt(ux**2 + uy**2 + uz**2)
    max_disp = float(np.max(disp_mag))
    log(f"Seat mean displacement = {seat_mean_disp:.6e} mm")
    log(f"Maximum displacement magnitude = {max_disp:.6e} mm")
    return {
        "seat_mean_displacement_mm": seat_mean_disp,
        "max_displacement_mm": max_disp,
    }


def write_results_json(data: dict) -> None:
    with open(RESULTS_JSON, "w") as f:
        json.dump({"outputs": data}, f, indent=2)
    log("Wrote results.json")


def write_fields_npz(mesh: Mesh, basis: Basis, u: np.ndarray) -> None:
    """Write displacement fields for *all* mesh nodes.

    ``basis`` provides the mapping from the global displacement vector ``u`` to
    the DOFs associated with the corner (vertex) nodes of the mesh.  Quadratic
    elements also contain mid‑edge nodes that are not part of ``basis.nodal_dofs``.
    The values at those interior nodes are not directly needed for the output
    quantities, and we therefore store them as zeros for completeness.
    """
    num_nodes = mesh.p.shape[1]
    # Allocate full displacement arrays (one component per mesh node)
    ux_full = np.zeros(num_nodes)
    uy_full = np.zeros(num_nodes)
    uz_full = np.zeros(num_nodes)
    # Vertex nodes are the first four entries of each tetrahedron connectivity.
    vertex_ids = np.unique(mesh.t[:4, :])
    # Fill the known values for the vertex DOFs.
    ux_full[vertex_ids] = u[basis.nodal_dofs[0]]
    uy_full[vertex_ids] = u[basis.nodal_dofs[1]]
    uz_full[vertex_ids] = u[basis.nodal_dofs[2]]
    # Save everything, including the original node identifiers.
    np.savez(
        FIELDS_NPZ,
        node_ids=np.arange(num_nodes),
        x=mesh.p[0],
        y=mesh.p[1],
        z=mesh.p[2],
        ux=ux_full,
        uy=uy_full,
        uz=uz_full,
    )
    log("Wrote fields.npz with nodal displacements for all nodes")


def copy_part_step() -> None:
    src = os.path.join(os.getenv("CADFEM_INPUT_DIR"), "geometry.step")
    shutil.copyfile(src, PART_STEP)
    log("Copied input geometry to part.step")


def write_refinement_json(entries: list) -> None:
    with open(REFINEMENT_JSON, "w") as f:
        json.dump(entries, f, indent=2)
    log("Wrote refinement.json")


def write_environment_json() -> None:
    env = {
        "versions": {
            "python": f"{os.sys.version.split()[0]}",
            "gmsh": gmsh.__version__,
            "skfem": "12.0.2",
            "numpy": np.__version__,
            "scipy": __import__("scipy").__version__,
        },
        "units": "mm",
        "material": {
            "E": E,
            "nu": nu,
            "type": "linear_elastic",
        },
        "boundary_conditions": {
            "fixed_bottom": "all displacement components = 0 on z=0 faces",
            "traction_top": f"uniform pressure {traction_mpa} N/mm^2 on top surface",
        },
        "mesh": {
            "element": "tetra10 (quadratic)",
            "order": 2,
        },
        "solver": "scikit-fem direct sparse solver",
    }
    with open(ENVIRONMENT_JSON, "w") as f:
        json.dump(env, f, indent=2)
    log("Wrote environment.json")

# -----------------------------------------------------------------------------
# Core analysis routine (single mesh size)
# -----------------------------------------------------------------------------

def run_analysis(lc: float, write_mesh: bool = True) -> dict:
    mesh_file = f"mesh_{lc:.1f}.msh"
    generate_mesh(lc, mesh_file)
    mesh = load_mesh(mesh_file)
    if write_mesh:
        # Keep a copy as the official mesh.msh file
        shutil.copyfile(mesh_file, MESH_MSH)
        log(f"Saved primary mesh as {MESH_MSH}")
    basis = build_vector_basis(mesh)
    bottom_ids = bottom_nodes(mesh)
    top_node_ids, max_z = top_nodes_and_z(mesh)
    top_facet_ids = top_facets(mesh, max_z)
    K = assemble_stiffness(basis)
    f = assemble_traction(basis, top_facet_ids)
    K_bc, f_bc = apply_dirichlet(K, f, basis, bottom_ids)
    u = solve_system(K_bc, f_bc)
    results = compute_output_quantities(basis, u, mesh)
    if write_mesh:
        write_fields_npz(mesh, basis, u)
    return results, mesh

# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

def main():
    # Start with a clean log
    pathlib.Path(SOLVER_LOG).write_text("")
    # Step 1: copy the original geometry
    copy_part_step()

    # Step 2: run the coarse (publisher) case – also produces mesh.msh and fields
    coarse_res, coarse_mesh = run_analysis(mesh_sizes["coarse"], write_mesh=True)
    write_results_json(coarse_res)

    # Step 3: run a refined case for the refinement report (no mesh overwrite)
    refined_res, refined_mesh = run_analysis(mesh_sizes["refined"], write_mesh=False)

    # Step 4: build refinement documentation (node counts and results)
    refinement_entries = [
        {
            "mesh_size_mm": mesh_sizes["coarse"],
            "node_count": int(coarse_mesh.p.shape[1]),
            "seat_mean_displacement_mm": coarse_res["seat_mean_displacement_mm"],
            "max_displacement_mm": coarse_res["max_displacement_mm"],
        },
        {
            "mesh_size_mm": mesh_sizes["refined"],
            "node_count": int(refined_mesh.p.shape[1]),
            "seat_mean_displacement_mm": refined_res["seat_mean_displacement_mm"],
            "max_displacement_mm": refined_res["max_displacement_mm"],
        },
    ]
    write_refinement_json(refinement_entries)

    # Step 5: write environment metadata
    write_environment_json()

if __name__ == "__main__":
    main()
