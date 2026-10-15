"""Reference for the keyed-shaft torsion task: Saint-Venant torsion via the Prandtl stress function on the cross-section
(FEniCSx P2, mesh refined at the keyway fillets). Far from the shaft ends the 3D twist rate and shear field equal these."""
import json, sys
import numpy as np
import gmsh, ufl
from mpi4py import MPI
from dolfinx import fem, io
from dolfinx.fem.petsc import LinearProblem
R, b, d, rf, G, T, L = 20.0, 12.0, 5.0, 1.0, 80000.0, 500e3, 100.0     # mm, MPa, N mm; twist measured over L = 100 mm
def solve(h_fil):
    gmsh.initialize(); gmsh.option.setNumber("General.Verbosity", 0); o = gmsh.model.occ
    disk = o.addDisk(0, 0, 0, R, R)
    slot = o.addRectangle(R - d, -b / 2, 0, 2 * d, b)
    sec, _ = o.cut([(2, disk)], [(2, slot)]); o.synchronize()
    # fillet the two concave keyway-root corners (x = R - d, y = +-b/2) with radius rf: 2D fillet via fillet2D on the surface
    corners = [p for p in gmsh.model.getEntities(0) if abs(gmsh.model.getValue(0, p[1], [])[0] - (R - d)) < 1e-6]
    o.remove(sec, recursive=False) if False else None
    gmsh.finalize()
    # rebuild with explicit fillet arcs (exact geometry): boundary = circle arc + slot sides with root arcs
    gmsh.initialize(); gmsh.option.setNumber("General.Verbosity", 0); o = gmsh.model.occ
    yt = np.sqrt(R ** 2 - (b / 2) ** 2)                                  # x where slot sides meet the circle
    P = lambda x, y: o.addPoint(x, y, 0)
    c0 = P(0, 0)
    a1, a2 = P(yt, b / 2), P(yt, -b / 2)                                 # circle / slot-side intersections
    s1a, s1b = P(R - d + rf, b / 2), P(R - d, b / 2 - rf)                # upper root fillet ends
    s2a, s2b = P(R - d, -b / 2 + rf), P(R - d + rf, -b / 2)              # lower root fillet ends
    fc1, fc2 = P(R - d + rf, b / 2 - rf), P(R - d + rf, -b / 2 + rf)      # fillet centres
    big = o.addCircleArc(a1, c0, a2) if False else None
    # circle from a2 (lower) round the far side to a1 (upper): split into two arcs through (-R, 0)
    mid = P(-R, 0)
    arcA, arcB = o.addCircleArc(a1, c0, mid), o.addCircleArc(mid, c0, a2)
    l1 = o.addLine(a2, s2b); f2 = o.addCircleArc(s2b, fc2, s2a); l2 = o.addLine(s2a, s1b); f1 = o.addCircleArc(s1b, fc1, s1a); l3 = o.addLine(s1a, a1)
    loop = o.addCurveLoop([arcA, arcB, l1, f2, l2, f1, l3]); s = o.addPlaneSurface([loop]); o.synchronize()
    gmsh.model.addPhysicalGroup(2, [s], 1); gmsh.model.addPhysicalGroup(1, [arcA, arcB, l1, f2, l2, f1, l3], 2)
    fd = gmsh.model.mesh.field.add("Distance"); gmsh.model.mesh.field.setNumbers(fd, "CurvesList", [f1, f2])
    th = gmsh.model.mesh.field.add("Threshold"); gmsh.model.mesh.field.setNumber(th, "InField", fd)
    for k, v in (("SizeMin", h_fil), ("SizeMax", 1.5), ("DistMin", 0.3), ("DistMax", 6.0)): gmsh.model.mesh.field.setNumber(th, k, v)
    gmsh.model.mesh.field.setAsBackgroundMesh(th)
    for k in ("Mesh.MeshSizeExtendFromBoundary", "Mesh.MeshSizeFromPoints", "Mesh.MeshSizeFromCurvature"): gmsh.option.setNumber(k, 0)
    gmsh.model.mesh.generate(2)
    dom, _, ft = io.gmshio.model_to_mesh(gmsh.model, MPI.COMM_WORLD, 0, gdim=2); gmsh.finalize()
    V = fem.functionspace(dom, ("Lagrange", 2)); u, v = ufl.TrialFunction(V), ufl.TestFunction(V)
    bc = fem.dirichletbc(fem.Constant(dom, 0.0), fem.locate_dofs_topological(V, 1, ft.find(2)), V)
    phi = LinearProblem(ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx, 2.0 * v * ufl.dx, bcs=[bc],
                        petsc_options={"ksp_type": "preonly", "pc_type": "lu"}).solve()     # unit G*theta
    J = fem.assemble_scalar(fem.form(2 * phi * ufl.dx))                       # torsion constant (mm^4) for G theta = 1
    theta = T / (G * J)                                                        # rad per mm
    W = fem.functionspace(dom, ("DG", 1, (2,)))
    gp = fem.Function(W); gp.interpolate(fem.Expression(ufl.grad(phi), W.element.interpolation_points()))
    tau = np.linalg.norm(gp.x.array.reshape(-1, 2), axis=1).max() * G * theta
    return J, np.degrees(theta * L), tau, V.dofmap.index_map.size_global
res = [solve(h) for h in (0.2, 0.1, 0.05)]
for (J, tw, tau, n), h in zip(res, (0.2, 0.1, 0.05)):
    print(f"fillet mesh {h} mm ({n} dofs): J = {J:.1f} mm^4, twist over 100 mm = {tw:.5f} deg, max shear = {tau:.3f} MPa")
J, tw, tau, _ = res[-1]
assert abs(res[-1][1] / res[-2][1] - 1) < 1e-4 and abs(res[-1][2] / res[-2][2] - 1) < 0.01, res
Jfull = np.pi * R ** 4 / 2
print(f"check: full circle J = {Jfull:.1f}; keyed/full = {J / Jfull:.4f}")
out = dict(id="SOLID-KEYED-SHAFT-TORSION", family="3D CAD + FEM: torsion of a keyed shaft",
    prompt=("Solid steel shaft (millimetres): a circular cylinder of radius 20 mm along the z axis from z = 0 to z = 400 mm, with a straight "
            "keyway cut along its whole length: the keyway is 12 mm wide (-6 <= y <= 6) and 5 mm deep (it removes the material with x >= 15), "
            "and its two bottom corners (at x = 15, y = +-6) are rounded with a 1 mm radius. Shear modulus G = 80000 MPa, linear elastic. A torque "
            "of 500 N m about the z axis twists the shaft (one end held, the other end loaded). Away from the ends (Saint-Venant torsion), report "
            "the relative angle of twist between the sections z = 150 and z = 250 mm, and the largest shear stress in the shaft there.\n"
            "JSON keys: twist_angle_deg, max_shear_stress_MPa."),
    reference=dict(twist_angle_deg=tw, max_shear_stress_MPa=tau), tolerance=dict(twist_angle_deg=0.03, max_shear_stress_MPa=0.05),
    check=dict(converged=[dict(fillet_mesh_mm=h, J_mm4=r[0], twist_deg=r[1], tau_MPa=r[2]) for r, h in zip(res, (0.2, 0.1, 0.05))]))
open(sys.argv[1], "w").write(json.dumps(out) + "\n")
