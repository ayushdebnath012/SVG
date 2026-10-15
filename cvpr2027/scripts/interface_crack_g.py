"""Independent energy-release-rate check for Code_Aster SSLP311 (central crack on an inclined bimaterial interface in a
finite plate under uniform tension). Validation only, never a reference.

Run in the FEniCSx env:
  tmp/fenicsx/env/bin/python scripts/interface_crack_g.py --theta 15 --level 1 --out DIR
  tmp/fenicsx/env/bin/python scripts/interface_crack_g.py --griffith --level 1 --out DIR   # solver check, known answer

Problem (V-doc v3.02.311 section 1, units mm / MPa / N): plate x in [-W, W], y in [-H, H], H = 2W = 4a, a = 1 mm. The
interface is the straight line through the centre at angle theta; material 1 (E = 2e6 MPa, nu = 0.3) lies above it,
material 2 (E = 2e5 MPa, nu = 0.3) below. The crack is the interface segment of length 2a centred on the plate centre,
with traction-free faces. Plane stress. The top edge carries a uniform traction sigma_0 = 100 MPa in +y; the bottom edge
has u_y = 0 and the bottom-left corner u_x = 0. Quadratic triangles are graded towards both tips. G at each tip comes
from the equivalent domain integral J = int (sigma_ij u_i,k e_k - W e_j) q_,j dA. Here e is the crack-extension
direction, and q = 1 within r1 of the tip, falling linearly to 0 at r2. The material interface is parallel to e, so it
adds no term. J is evaluated on three annuli as a path-independence check. G is reported in J/m^2 (= 1e3 x N/mm).
--griffith replaces the problem by a homogeneous wide plate with a horizontal crack, where G = (1.0 + small width
correction) * sigma^2 pi a / E.
"""
import argparse
import json
import math
import time
from pathlib import Path

import gmsh
import numpy as np
import ufl
from dolfinx import fem, io
from dolfinx.fem.petsc import LinearProblem
from mpi4py import MPI
from petsc4py import PETSc

ap = argparse.ArgumentParser()
ap.add_argument("--theta", type=float, default=15.0)
ap.add_argument("--level", type=int, default=1, help="mesh level; element sizes halve per level")
ap.add_argument("--griffith", action="store_true")
ap.add_argument("--out", type=Path, required=True)
A = ap.parse_args()
A.out.mkdir(parents=True, exist_ok=True)
t0 = time.time()

a = 1.0
if A.griffith:
    W, H, th = 25.0, 25.0, 0.0
    E1 = E2 = 2.0e5
else:
    W, H, th = 2.0 * a, 4.0 * a, math.radians(A.theta)
    E1, E2 = 2.0e6, 2.0e5
nu, s0 = 0.3, 100.0
d = np.array([math.cos(th), math.sin(th)])
tipR, tipL = a * d, -a * d
# interface end points on the left/right edges (theta <= 60 deg keeps them on the side edges for H = 2W)
yE = W * math.tan(th)
assert abs(yE) < H
h_tip = 0.02 * a / 2 ** (A.level - 1)
h_far = 0.25 * a / 2 ** (A.level - 1)

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
gmsh.model.add("crack")
g = gmsh.model.geo
P = lambda x, y: g.addPoint(x, y, 0.0)
pBL, pBR, pTR, pTL = P(-W, -H), P(W, -H), P(W, H), P(-W, H)
pEL, pER = P(-W, -yE), P(W, yE)
pL, pR = P(*tipL), P(*tipR)
# boundary pieces
bot = g.addLine(pBL, pBR)
rlow = g.addLine(pBR, pER)
rup = g.addLine(pER, pTR)
top = g.addLine(pTR, pTL)
lup = g.addLine(pTL, pEL)
llow = g.addLine(pEL, pBL)
iL = g.addLine(pEL, pL)            # bonded interface, left part
iR = g.addLine(pR, pER)            # bonded interface, right part
cU = g.addLine(pL, pR)             # crack face on material 1 (upper)
cD = g.addLine(pL, pR)             # crack face on material 2 (lower): same geometry, separate curve -> open crack
s1 = g.addPlaneSurface([g.addCurveLoop([iL, cU, iR, rup, top, lup])])      # above the interface: material 1
s2 = g.addPlaneSurface([g.addCurveLoop([bot, rlow, -iR, -cD, -iL, llow])])  # below: material 2
g.synchronize()
gmsh.model.addPhysicalGroup(2, [s1], 1)
gmsh.model.addPhysicalGroup(2, [s2], 2)
gmsh.model.addPhysicalGroup(1, [top], 10)
gmsh.model.addPhysicalGroup(1, [bot], 11)
f = gmsh.model.mesh.field
dist = f.add("Distance")
f.setNumbers(dist, "PointsList", [pL, pR])
thr = f.add("Threshold")
f.setNumber(thr, "InField", dist)
f.setNumber(thr, "SizeMin", h_tip)
f.setNumber(thr, "SizeMax", h_far)
f.setNumber(thr, "DistMin", 0.05 * a)
f.setNumber(thr, "DistMax", 1.0 * a)
f.setAsBackgroundMesh(thr)
gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
gmsh.model.mesh.generate(2)
dom, ct, ft = io.gmshio.model_to_mesh(gmsh.model, MPI.COMM_SELF, 0, gdim=2)
gmsh.finalize()

V = fem.functionspace(dom, ("Lagrange", 2, (2,)))
DG0 = fem.functionspace(dom, ("DG", 0))
Ef = fem.Function(DG0)
Ef.x.array[ct.find(1)] = E1
Ef.x.array[ct.find(2)] = E2
mu = Ef / (2 * (1 + nu))
lam_ps = Ef * nu / (1 - nu ** 2)                      # plane stress
eps = lambda w: ufl.sym(ufl.grad(w))
sig = lambda w: lam_ps * ufl.tr(eps(w)) * ufl.Identity(2) + 2 * mu * eps(w)
u_, v_ = ufl.TrialFunction(V), ufl.TestFunction(V)
ds = ufl.Measure("ds", domain=dom, subdomain_data=ft)
Vy, _ = V.sub(1).collapse()
Vx, _ = V.sub(0).collapse()
bcs = [fem.dirichletbc(fem.Function(Vy), fem.locate_dofs_topological((V.sub(1), Vy), 1, ft.find(11)), V.sub(1))]
corner = fem.locate_dofs_geometrical((V.sub(0), Vx), lambda x: np.isclose(x[0], -W) & np.isclose(x[1], -H))
bcs.append(fem.dirichletbc(fem.Function(Vx), corner, V.sub(0)))
L = ufl.dot(fem.Constant(dom, np.array([0.0, s0])), v_) * ds(10)
u = LinearProblem(ufl.inner(sig(u_), eps(v_)) * ufl.dx, L, bcs=bcs,
                  petsc_options={"ksp_type": "preonly", "pc_type": "lu", "pc_factor_mat_solver_type": "mumps"}).solve()


def J(tip, e, r1, r2):
    x = ufl.SpatialCoordinate(dom)
    r = ufl.sqrt((x[0] - tip[0]) ** 2 + (x[1] - tip[1]) ** 2)
    q = ufl.conditional(ufl.lt(r, r1), 1.0, ufl.conditional(ufl.gt(r, r2), 0.0, (r2 - r) / (r2 - r1)))
    ev = ufl.as_vector(list(e))
    s = sig(u)
    Wd = 0.5 * ufl.inner(s, eps(u))
    integrand = ufl.dot(ufl.dot(s, ufl.dot(ufl.grad(u), ev)), ufl.grad(q)) - Wd * ufl.dot(ev, ufl.grad(q))
    # sigma_ij u_i,k e_k q_,j  ->  (grad(u) e)_i sigma_ij q_,j ; sigma symmetric
    return fem.assemble_scalar(fem.form(integrand * ufl.dx(metadata={"quadrature_degree": 6})))


rings = [(0.05, 0.25), (0.1, 0.4), (0.2, 0.5)]
res = {}
for name, tip, e in (("right", tipR, d), ("left", tipL, -d)):
    vals = [1e3 * J(tip, e, r1 * a, r2 * a) for r1, r2 in rings]      # N/mm -> J/m^2
    res[name] = dict(G_J_per_m2=vals[1], rings=vals, ring_spread=(max(vals) - min(vals)) / abs(vals[1]))
rec = dict(case="griffith" if A.griffith else f"SSLP311 theta={A.theta:g}", theta_deg=A.theta, level=A.level, h_tip_mm=h_tip, h_far_mm=h_far,
           cells=dom.topology.index_map(2).size_global, dofs=V.dofmap.index_map.size_global * 2, G=res, runtime_seconds=time.time() - t0,
           model="plane stress, P2 triangles, open crack on the interface, equivalent-domain J-integral", role="independent_validation_only_not_reference")
if A.griffith:
    rec["G_infinite_plate_J_per_m2"] = 1e3 * s0 ** 2 * math.pi * a / E1
(A.out / "result.json").write_text(json.dumps(rec, indent=1) + "\n")
print(json.dumps({k: rec[k] for k in ("case", "level", "cells")} | {t: [round(x, 4) for x in res[t]["rings"]] for t in res}
                 | ({"G_inf": rec["G_infinite_plate_J_per_m2"]} if A.griffith else {})), flush=True)
