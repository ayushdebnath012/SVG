"""Reference for the stepped-shaft task: axisymmetric linear elasticity (FEniCSx P2), shoulder fillet refined; peak axial
stress (at the fillet) and the elongation of the shaft axis between its end faces."""
import json, sys
import numpy as np
import gmsh, ufl
from mpi4py import MPI
from dolfinx import fem, io, geometry
from dolfinx.fem.petsc import LinearProblem
E, nu, F, RD, Rd, rf, L1, L2 = 200000.0, 0.3, 100e3, 30.0, 20.0, 3.0, 100.0, 100.0
def solve(h_fil):
    gmsh.initialize(); gmsh.option.setNumber("General.Verbosity", 0); o = gmsh.model.occ
    P = lambda r, z: o.addPoint(r, z, 0)
    p0, p1, p2 = P(0, 0), P(RD, 0), P(RD, L1)
    f_a, f_c, f_b = P(Rd + rf, L1), P(Rd + rf, L1 + rf), P(Rd, L1 + rf)        # fillet from the shoulder face to the small cylinder
    p5, p6 = P(Rd, L1 + L2), P(0, L1 + L2)
    lines = [o.addLine(p0, p1), o.addLine(p1, p2), o.addLine(p2, f_a), o.addCircleArc(f_a, f_c, f_b), o.addLine(f_b, p5), o.addLine(p5, p6), o.addLine(p6, p0)]
    s = o.addPlaneSurface([o.addCurveLoop(lines)]); o.synchronize()
    gmsh.model.addPhysicalGroup(2, [s], 1); gmsh.model.addPhysicalGroup(1, [lines[0]], 2); gmsh.model.addPhysicalGroup(1, [lines[5]], 3)
    fd = gmsh.model.mesh.field.add("Distance"); gmsh.model.mesh.field.setNumbers(fd, "CurvesList", [lines[3]])
    th = gmsh.model.mesh.field.add("Threshold"); gmsh.model.mesh.field.setNumber(th, "InField", fd)
    for k, v in (("SizeMin", h_fil), ("SizeMax", 3.0), ("DistMin", 0.5), ("DistMax", 15.0)): gmsh.model.mesh.field.setNumber(th, k, v)
    gmsh.model.mesh.field.setAsBackgroundMesh(th)
    for k in ("Mesh.MeshSizeExtendFromBoundary", "Mesh.MeshSizeFromPoints", "Mesh.MeshSizeFromCurvature"): gmsh.option.setNumber(k, 0)
    gmsh.model.mesh.generate(2)
    dom, _, ft = io.gmshio.model_to_mesh(gmsh.model, MPI.COMM_WORLD, 0, gdim=2); gmsh.finalize()
    V = fem.functionspace(dom, ("Lagrange", 2, (2,))); u, v = ufl.TrialFunction(V), ufl.TestFunction(V)
    x = ufl.SpatialCoordinate(dom); r = x[0]
    lam, mu = E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))
    eps = lambda w: ufl.as_vector([w[0].dx(0), w[1].dx(1), w[0] / r, w[0].dx(1) + w[1].dx(0)])
    def sig(w):
        e = eps(w); tr = e[0] + e[1] + e[2]
        return ufl.as_vector([lam * tr + 2 * mu * e[0], lam * tr + 2 * mu * e[1], lam * tr + 2 * mu * e[2], mu * e[3]])
    ds = ufl.Measure("ds", domain=dom, subdomain_data=ft)
    q = F / (np.pi * Rd ** 2)
    V1, _ = V.sub(1).collapse()
    zfix = fem.locate_dofs_topological((V.sub(1), V1), 1, ft.find(2))
    bc = fem.dirichletbc(fem.Function(V1), zfix, V.sub(1))
    uh = LinearProblem(ufl.dot(sig(u), eps(v)) * r * ufl.dx, q * v[1] * r * ds(3), bcs=[bc],
                       petsc_options={"ksp_type": "preonly", "pc_type": "lu"}).solve()
    W = fem.functionspace(dom, ("DG", 1)); szz = fem.Function(W)
    szz.interpolate(fem.Expression(sig(uh)[1], W.element.interpolation_points()))
    tree = geometry.bb_tree(dom, 2)
    pt = np.array([[0.0, L1 + L2 - 1e-6, 0.0]])
    c = geometry.compute_colliding_cells(dom, geometry.compute_collisions_points(tree, pt), pt)
    elong = uh.eval(pt, [c.links(0)[0]])[1]
    xy = W.tabulate_dof_coordinates()
    off_axis = xy[:, 0] > 1.0                                  # u_r / r is 0/0 on the axis; the peak is at the fillet anyway
    k = np.argmax(np.where(off_axis, szz.x.array, -np.inf))
    print(f"   peak at r = {xy[k, 0]:.3f}, z = {xy[k, 1]:.3f} mm")
    return szz.x.array[k], elong, q, V.dofmap.index_map.size_global
res = [solve(h) for h in (0.2, 0.1, 0.05)]
for (sm, el, q, n), h in zip(res, (0.2, 0.1, 0.05)):
    print(f"fillet mesh {h} mm ({n} dofs): peak axial stress {sm:.3f} MPa (Kt = {sm / q:.4f} on {q:.2f} MPa nominal), elongation {el:.6f} mm")
sm, el, q, _ = res[-1]
assert abs(res[-1][0] / res[-2][0] - 1) < 0.005 and abs(res[-1][1] / res[-2][1] - 1) < 1e-4, res
print(f"check: bar elongation by PL/EA = {F * L1 / (E * np.pi * RD ** 2) + F * L2 / (E * np.pi * Rd ** 2):.6f} mm")
out = dict(id="SOLID-STEPPED-SHAFT", family="3D CAD + FEM: stepped shaft, shoulder fillet",
    prompt=("Solid round steel shaft (millimetres) along the z axis: diameter 60 mm for 0 <= z <= 100 and diameter 40 mm for "
            "100 <= z <= 200, with the shoulder's inside corner (between the shoulder face z = 100 and the 40 mm cylinder) rounded with a 3 mm "
            "fillet. E = 200000 MPa, Poisson ratio 0.3, linear elastic. The end face z = 0 is held against axial movement only (free to expand "
            "radially); a 100 kN axial tensile force acts on the end face z = 200 as a uniform traction. Report the largest axial normal stress in the "
            "shaft and the elongation of the shaft's centre line between its two end faces.\nJSON keys: max_axial_stress_MPa, elongation_mm."),
    reference=dict(max_axial_stress_MPa=sm, elongation_mm=el), tolerance=dict(max_axial_stress_MPa=0.05, elongation_mm=0.03),
    check=dict(converged=[dict(fillet_mesh_mm=h, peak_MPa=r[0], elongation_mm=r[1]) for r, h in zip(res, (0.2, 0.1, 0.05))]))
open(sys.argv[1], "w").write(json.dumps(out) + "\n")
