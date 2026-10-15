"""Feasibility check for the Hertz task: elastic hemisphere (R) on a rigid frictionless flat, axisymmetric P2, penalty
contact solved by Newton, gmsh mesh refined at the contact. Analytic Hertz (rigid flat): a = (3FR/4E*)^(1/3),
p0 = 3F/(2 pi a^2), E* = E/(1-nu^2)."""
import sys
import numpy as np
import gmsh
import ufl
from mpi4py import MPI
from dolfinx import fem, io, mesh
from dolfinx.fem.petsc import NonlinearProblem
from dolfinx.nls.petsc import NewtonSolver
from petsc4py import PETSc

R, E, nu, F = 50.0, 210000.0, 0.3, 10000.0
hmin = float(sys.argv[1]) if len(sys.argv) > 1 else 0.03
Es = E / (1 - nu ** 2)
a_ex = (3 * F * R / (4 * Es)) ** (1 / 3)
p0_ex = 3 * F / (2 * np.pi * a_ex ** 2)
gmsh.initialize(); gmsh.option.setNumber("General.Verbosity", 0)
o = gmsh.model.occ
c = o.addPoint(0, R, 0); p_bot = o.addPoint(0, 0, 0); p_rt = o.addPoint(R, R, 0); p_top = o.addPoint(0, R, 0)
arc = o.addCircleArc(p_bot, c, p_rt); top = o.addLine(p_rt, p_top); axis = o.addLine(p_top, p_bot)
s = o.addPlaneSurface([o.addCurveLoop([arc, top, axis])]); o.synchronize()
gmsh.model.addPhysicalGroup(2, [s], 1); gmsh.model.addPhysicalGroup(1, [arc], 2); gmsh.model.addPhysicalGroup(1, [top], 3)
f1 = gmsh.model.mesh.field.add("Distance"); gmsh.model.mesh.field.setNumbers(f1, "PointsList", [p_bot])
f2 = gmsh.model.mesh.field.add("Threshold"); gmsh.model.mesh.field.setNumber(f2, "InField", f1)
for k, v in (("SizeMin", hmin), ("SizeMax", 4.0), ("DistMin", 2.5 * a_ex), ("DistMax", 30.0)):
    gmsh.model.mesh.field.setNumber(f2, k, v)
gmsh.model.mesh.field.setAsBackgroundMesh(f2)
for k in ("Mesh.MeshSizeExtendFromBoundary", "Mesh.MeshSizeFromPoints", "Mesh.MeshSizeFromCurvature"):
    gmsh.option.setNumber(k, 0)
gmsh.model.mesh.generate(2)
dom, _, ft = io.gmshio.model_to_mesh(gmsh.model, MPI.COMM_WORLD, 0, gdim=2)
gmsh.finalize()
V = fem.functionspace(dom, ("Lagrange", 2, (2,)))
u, v = fem.Function(V), ufl.TestFunction(V)
x = ufl.SpatialCoordinate(dom); r = x[0]
def eps(w):   # (rr, zz, tt, rz) axisymmetric strains
    return ufl.as_vector([w[0].dx(0), w[1].dx(1), w[0] / r, w[0].dx(1) + w[1].dx(0)])
lam, mu = E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))
def sig(w):
    e = eps(w); tr = e[0] + e[1] + e[2]
    return ufl.as_vector([lam * tr + 2 * mu * e[0], lam * tr + 2 * mu * e[1], lam * tr + 2 * mu * e[2], mu * e[3]])
ds = ufl.Measure("ds", domain=dom, subdomain_data=ft)
kpen = fem.Constant(dom, PETSc.ScalarType(1e8))
q = F / (np.pi * R ** 2)
gap = x[1] + u[1]
pen = kpen * ufl.conditional(ufl.lt(gap, 0), -gap, 0)
Res = ufl.dot(sig(u), eps(v)) * r * ufl.dx - pen * v[1] * r * ds(2) + q * v[1] * r * ds(3)
# rigid-body z is held by contact only; r-axis symmetry is natural (u_r = 0 on the axis)
V0, _ = V.sub(0).collapse()
axis_dofs = fem.locate_dofs_geometrical((V.sub(0), V0), lambda X: np.isclose(X[0], 0.0))
zero = fem.Function(V0)
bc = fem.dirichletbc(zero, axis_dofs, V.sub(0))
u.x.array[:] = 0.0
uz0 = fem.Function(V)
# start pressed in by the Hertz approach so the first Newton iterate is in contact
u.interpolate(lambda X: np.vstack([0 * X[0], -(a_ex ** 2 / R) * np.ones_like(X[0])]))
prob = NonlinearProblem(Res, u, [bc])
sol = NewtonSolver(MPI.COMM_WORLD, prob)
sol.convergence_criterion, sol.rtol, sol.atol, sol.max_it = "incremental", 1e-10, 1e-14, 100
n, ok = sol.solve(u)
assert ok
# contact pressure along the curved surface near the axis
rs = np.linspace(0, 2.0 * a_ex, 801)
zb = np.array([R - np.sqrt(R ** 2 - rr ** 2) for rr in rs])
pts = np.array([[max(rr, 1e-6), z + 1e-4, 0.0] for rr, z in zip(rs, zb)])       # just inside; the gap uses the true surface
from dolfinx import geometry
tree = geometry.bb_tree(dom, 2)
coll = geometry.compute_colliding_cells(dom, geometry.compute_collisions_points(tree, pts), pts)
uz = np.array([u.eval(p, [coll.links(i)[0]])[1] for i, p in enumerate(pts)])
gapv = zb + uz
p = 1e8 * np.maximum(-gapv, 0)
a_fe = rs[np.flatnonzero(p > 0).max()] if (p > 0).any() else 0
print(f"hmin {hmin} mm, {dom.topology.index_map(2).size_local} cells: a = {a_fe:.4f} mm (exact {a_ex:.4f}, {100 * (a_fe / a_ex - 1):+.2f}%), "
      f"p0 = {p[0]:.1f} MPa (exact {p0_ex:.1f}, {100 * (p[0] / p0_ex - 1):+.2f}%), Newton {n}")
