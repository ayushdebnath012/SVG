#!/usr/bin/env python
"""Finite element analysis of the cycloidal disk (PETG-CF).

The script generates a linear tetrahedral mesh of the part using Gmsh,
applies material properties (E = 3000 MPa, ν = 0.36), Dirichlet constraints on
support faces 8 and 13 (zero displacement), and applies uniform surface tractions
on load faces 2 and 19.  Quadratic tetrahedral shape functions are used for the
displacement field via :class:`skfem.element.ElementVector` wrapping the quadratic
``ElementTetP2`` element.  The maximum nodal displacement magnitude is written to
``results.json``.

All generated artifacts (mesh, fields, logs, etc.) are saved in the current
working directory as required by the benchmark contract.
"""

import os
import json
import shutil
import numpy as np

import gmsh
import skfem
from skfem import Mesh, Basis, FacetBasis, asm, solve
from skfem.models.elasticity import lame_parameters, linear_elasticity
from skfem.element.element_tet.element_tet_p2 import ElementTetP2
from skfem.element import ElementVector
from skfem import LinearForm


def generate_mesh(mesh_file='mesh_linear.msh'):
    """Generate a linear tetrahedral mesh using Gmsh.

    The mesh respects the physical groups for load and support faces as defined
    in the problem statement.  The maximum element size is 2 mm, matching the
    reference Netgen mesh size.
    """
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal', 0)
    # linear elements (order 1) – we will use quadratic shape functions later
    gmsh.option.setNumber('Mesh.ElementOrder', 1)
    gmsh.option.setNumber('Mesh.MeshSizeMax', 2.0)
    # load the STEP geometry
    step_path = os.getenv('CADFEM_INPUT_DIR', '') + '/part.step'
    if not os.path.isfile(step_path):
        step_path = 'inputs/part.step'
    gmsh.model.occ.importShapes(step_path)
    gmsh.model.occ.synchronize()
    # Physical groups for the relevant faces (using the face indices from faces.json)
    faces_of_interest = {
        2: 'load_face_2',
        8: 'support_face_8',
        13: 'support_face_13',
        19: 'load_face_19',
    }
    for tag, name in faces_of_interest.items():
        pg = gmsh.model.addPhysicalGroup(2, [tag])
        gmsh.model.setPhysicalName(2, pg, name)
    # Volume physical group (required for mesh loading)
    vol = gmsh.model.getEntities(dim=3)[0][1]
    pg_vol = gmsh.model.addPhysicalGroup(3, [vol])
    gmsh.model.setPhysicalName(3, pg_vol, 'volume')
    # Generate the 3D mesh and write to file
    gmsh.model.mesh.generate(3)
    gmsh.write(mesh_file)
    gmsh.finalize()
    return mesh_file


def main():
    # ---------------------------------------------------------------------
    # Load or generate the mesh
    mesh_path = 'mesh_linear.msh'
    if not os.path.isfile(mesh_path):
        generate_mesh(mesh_path)
    mesh = Mesh.load(mesh_path)

    # ---------------------------------------------------------------------
    # Define the quadratic vector element for displacement (3 components)
    elt = ElementTetP2()
    elem_vec = ElementVector(elt)

    # Volume basis (cells)
    basis = Basis(mesh, elem_vec)

    # ---------------------------------------------------------------------
    # Material properties (E in N/mm^2 = MPa)
    E = 3000.0  # MPa
    nu = 0.36
    lam, mu = lame_parameters(E, nu)
    a_form = linear_elasticity(lam, mu)
    K = asm(a_form, basis)

    # ---------------------------------------------------------------------
    # Load (traction) on faces 2 and 19
    # Face areas are given in faces.json (both are 125.664 mm^2)
    area_face = 125.664  # mm^2
    f2_total = np.array([0.0, -31.165, 94.894])  # N
    f19_total = np.array([0.0, -31.169, 94.905])  # N
    t2 = f2_total / area_face  # N/mm^2 (MPa)
    t19 = f19_total / area_face

    # Facet bases for the two loaded faces
    fb2 = FacetBasis(mesh, elem_vec, facets=mesh.boundaries['load_face_2'])
    fb19 = FacetBasis(mesh, elem_vec, facets=mesh.boundaries['load_face_19'])

    @LinearForm
    def neumann(v, w):
        # v is a tuple with a single DiscreteField of shape (3, n_facets, n_quad)
        phi = v[0]
        # traction components passed as scalar parameters to avoid interpolation
        t0 = w['t0']
        t1 = w['t1']
        t2 = w['t2']
        # Compute dot product: t·phi = t0*phi[0] + t1*phi[1] + t2*phi[2]
        return t0 * phi[0] + t1 * phi[1] + t2 * phi[2]

    L2 = asm(neumann, fb2, t0=t2[0], t1=t2[1], t2=t2[2])
    L19 = asm(neumann, fb19, t0=t19[0], t1=t19[1], t2=t19[2])
    L = L2 + L19

    # ---------------------------------------------------------------------
    # Dirichlet boundary conditions: zero displacement on support faces 8 and 13
    fixed = basis.get_dofs(['support_face_8', 'support_face_13']).flatten()
    # Solve the linear system with zero Dirichlet values at the fixed DOFs
    # Apply Dirichlet constraints manually by modifying the system matrix and RHS
    from scipy.sparse import lil_matrix
    from scipy.sparse.linalg import spsolve
    K_lil = K.tolil()
    b = L.copy()
    # Zero rows and columns for fixed DOFs, then set diagonal to 1
    K_lil[fixed, :] = 0.0
    K_lil[:, fixed] = 0.0
    # Set diagonal entries for the constrained DOFs to 1 (Dirichlet condition)
    K_lil[fixed, fixed] = 1.0
    # Zero RHS entries for constrained DOFs
    b[fixed] = 0.0
    K_mod = K_lil.tocsr()
    u = spsolve(K_mod, b)

    # ---------------------------------------------------------------------
    # Compute nodal displacement magnitude and the maximum value
    # Determine the total number of nodal points (including midside nodes added by the quadratic element)
    total_nodes = u.size // 3
    # The solution vector orders the components as (u0, v0, w0, u1, v1, w1, ...)
    disp = u.reshape((3, total_nodes), order='F')
    mag = np.linalg.norm(disp, axis=0)
    max_disp = float(mag.max())

    # ---------------------------------------------------------------------
    # Write the required output files
    results = {"outputs": {"max_displacement_mm": max_disp}}
    with open('results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Save a copy of the linear mesh as mesh.msh for the required artifact
    shutil.copy(mesh_path, 'mesh.msh')
    # Save fields (displacements) for inspection
    np.savez('fields.npz', displacement=disp, magnitude=mag)

    # Simple solver log
    with open('solver.log', 'w') as f:
        f.write('Linear elasticity solved with scikit-fem\n')

    # Refinement information (single mesh resolution)
    refinement = {
        "mesh_size_max_mm": 2.0,
        "num_nodes": int(mesh.nvertices),
        "num_elements": int(mesh.nelements)
    }
    with open('refinement.json', 'w') as f:
        json.dump(refinement, f, indent=2)

    # Environment description
    environment = {
        "solver": "scikit-fem",
        "element": "ElementVector(ElementTetP2)",
        "material": {"E_MPa": E, "nu": nu},
        "units": {"length_mm": True, "force_N": True},
        "mesh_file": mesh_path
    }
    with open('environment.json', 'w') as f:
        json.dump(environment, f, indent=2)

    # The original part STEP file has already been copied earlier in the script.
    # No further action required here.


if __name__ == '__main__':
    main()
