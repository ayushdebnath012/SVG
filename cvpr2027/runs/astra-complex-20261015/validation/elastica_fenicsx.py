"""Feasibility check for the large-deflection cantilever task: total-Lagrangian St Venant-Kirchhoff, plane stress
(nu = 0, so identical to the 3D bar), P2 triangles, dead tip load in 40 steps. Reference: exact elastica 8.1032 / 5.5440 m."""
import sys
import numpy as np
import ufl
from mpi4py import MPI
from dolfinx import fem, mesh
from dolfinx.fem.petsc import NonlinearProblem
from dolfinx.nls.petsc import NewtonSolver
from petsc4py import PETSc

L, H, B, E, nu, P = 10.0, 0.10261, 0.3, 100e6, 0.0, 269.35
nx, ny = int(sys.argv[1]), int(sys.argv[2])
dom = mesh.create_rectangle(MPI.COMM_WORLD, [[0, 0], [L, H]], [nx, ny], mesh.CellType.triangle)
V = fem.functionspace(dom, ("Lagrange", 2, (2,)))
u, v = fem.Function(V), ufl.TestFunction(V)
root = fem.locate_dofs_geometrical(V, lambda x: np.isclose(x[0], 0.0))
bc = fem.dirichletbc(np.zeros(2, dtype=PETSc.ScalarType), root, V)
tdim = dom.topology.dim
facets = mesh.locate_entities_boundary(dom, tdim - 1, lambda x: np.isclose(x[0], L))
mt = mesh.meshtags(dom, tdim - 1, facets, np.full(len(facets), 1, dtype=np.int32))
ds = ufl.Measure("ds", domain=dom, subdomain_data=mt)
lam_, mu = E * nu / (1 - nu ** 2), E / (2 * (1 + nu))          # plane stress
F_ = ufl.Identity(2) + ufl.grad(u)
Egl = 0.5 * (F_.T * F_ - ufl.Identity(2))
S = lam_ * ufl.tr(Egl) * ufl.Identity(2) + 2 * mu * Egl
t = fem.Constant(dom, PETSc.ScalarType((0.0, 0.0)))               # dead traction per unit area of the end face
R = ufl.inner(F_ * S, ufl.grad(v)) * B * ufl.dx - ufl.dot(t, v) * B * ds(1)
prob = NonlinearProblem(R, u, [bc])
solver = NewtonSolver(MPI.COMM_WORLD, prob)
solver.convergence_criterion = "incremental"
solver.rtol, solver.atol, solver.max_it = 1e-9, 1e-12, 50
steps = 100
for k in range(1, steps + 1):
    t.value = (0.0, -P * k / steps / (B * H))
    n, ok = solver.solve(u)
    assert ok
pt = np.array([[L, H / 2, 0.0]])
from dolfinx import geometry
tree = geometry.bb_tree(dom, tdim)
cells = geometry.compute_colliding_cells(dom, geometry.compute_collisions_points(tree, pt), pt)
val = u.eval(pt, [cells.links(0)[0]])
print(f"mesh {nx}x{ny} P2: tip (centroid of end face) vertical {-val[1]:.4f} m, horizontal {-val[0]:.4f} m | exact elastica 8.1032 / 5.5440")
