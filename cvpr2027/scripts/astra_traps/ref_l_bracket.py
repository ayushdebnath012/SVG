"""Reference for the L-bracket task: 3D linear elasticity, FEniCSx P2 tets, gmsh OCC geometry with the inner fillet,
mesh refined on the fillet; tip deflection and the peak von Mises stress on the fillet surface (sampled just inside)."""
import json, sys
import numpy as np
import gmsh, ufl
from mpi4py import MPI
from dolfinx import fem, io, geometry
from dolfinx.fem.petsc import LinearProblem
E, nu, F, rf = 200000.0, 0.3, 2000.0, 5.0
def solve(h_fil, h_max):
    gmsh.initialize(); gmsh.option.setNumber("General.Verbosity", 0); o = gmsh.model.occ
    leg = o.addBox(0, 0, 0, 20, 30, 100); arm = o.addBox(0, 0, 80, 100, 30, 20)
    vol, _ = o.fuse([(3, leg)], [(3, arm)]); o.synchronize()
    def ebb(c): return gmsh.model.getBoundingBox(1, c)
    edge = [c for _, c in gmsh.model.getEntities(1) if all(abs(ebb(c)[i] - v) < 1e-5 for i, v in ((0, 20), (3, 20), (2, 80), (5, 80)))]
    assert len(edge) == 1, edge
    vol = o.fillet([v[1] for v in vol], edge, [rf]); o.synchronize()
    vtag = vol[0][1]
    faces = gmsh.model.getBoundary(vol, oriented=False)
    def bb(t): return gmsh.model.getBoundingBox(2, t)
    base = [t for _, t in faces if abs(bb(t)[2]) < 1e-6 and abs(bb(t)[5]) < 1e-6]
    tip = [t for _, t in faces if abs(bb(t)[0] - 100) < 1e-6 and abs(bb(t)[3] - 100) < 1e-6]
    fil = [t for _, t in faces if gmsh.model.getType(2, t) == "Cylinder"]
    assert len(base) == 1 and len(tip) == 1 and len(fil) == 1
    gmsh.model.addPhysicalGroup(3, [vtag], 1); gmsh.model.addPhysicalGroup(2, base, 2); gmsh.model.addPhysicalGroup(2, tip, 3)
    fd = gmsh.model.mesh.field.add("Distance"); gmsh.model.mesh.field.setNumbers(fd, "SurfacesList", fil)
    th = gmsh.model.mesh.field.add("Threshold"); gmsh.model.mesh.field.setNumber(th, "InField", fd)
    for k, v in (("SizeMin", h_fil), ("SizeMax", h_max), ("DistMin", 1.0), ("DistMax", 15.0)): gmsh.model.mesh.field.setNumber(th, k, v)
    gmsh.model.mesh.field.setAsBackgroundMesh(th)
    for k in ("Mesh.MeshSizeExtendFromBoundary", "Mesh.MeshSizeFromPoints", "Mesh.MeshSizeFromCurvature"): gmsh.option.setNumber(k, 0)
    gmsh.model.mesh.generate(3)
    dom, _, ft = io.gmshio.model_to_mesh(gmsh.model, MPI.COMM_WORLD, 0, gdim=3); gmsh.finalize()
    V = fem.functionspace(dom, ("Lagrange", 2, (3,)))
    u, v = ufl.TrialFunction(V), ufl.TestFunction(V)
    lam, mu = E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))
    eps = lambda w: ufl.sym(ufl.grad(w)); sig = lambda w: lam * ufl.tr(eps(w)) * ufl.Identity(3) + 2 * mu * eps(w)
    ds = ufl.Measure("ds", domain=dom, subdomain_data=ft)
    t = fem.Constant(dom, np.array([0.0, 0.0, -F / (30 * 20)]))
    bc = fem.dirichletbc(np.zeros(3), fem.locate_dofs_topological(V, 2, ft.find(2)), V)
    uh = LinearProblem(ufl.inner(sig(u), eps(v)) * ufl.dx, ufl.dot(t, v) * ds(3), bcs=[bc],
                       petsc_options={"ksp_type": "preonly", "pc_type": "lu", "pc_factor_mat_solver_type": "mumps"}).solve()
    s = sig(uh); dev = s - ufl.tr(s) / 3 * ufl.Identity(3)
    W = fem.functionspace(dom, ("DG", 1)); vm = fem.Function(W)
    vm.interpolate(fem.Expression(ufl.sqrt(1.5 * ufl.inner(dev, dev)), W.element.interpolation_points()))
    tree = geometry.bb_tree(dom, 3)
    def ev(f, pts):
        cells = geometry.compute_colliding_cells(dom, geometry.compute_collisions_points(tree, pts), pts)
        return np.array([f.eval(p, [cells.links(i)[0]]) for i, p in enumerate(pts)])
    # fillet: centre line at x = 20 + rf, z = 80 - rf; surface points at angle a from (20, z=80-rf) to (x=20+rf, 80); 0.02 mm inside
    # explicit parametrisation: centre (20 + rf, 80 - rf); surface = centre + rf*(-cos a, +sin a) ... material lies outside the circle
    pts = np.array([[20 + rf - (rf + 0.02) * np.cos(a), y, 80 - rf + (rf + 0.02) * np.sin(a)] for a in np.linspace(0, np.pi / 2, 61) for y in np.linspace(0.02, 29.98, 31)])
    peak = ev(vm, pts).max()
    tipc = ev(uh, np.array([[99.98, 15.0, 90.0]]))[0]
    return -tipc[2], peak, V.dofmap.index_map.size_global
res = [solve(hf, hm) for hf, hm in ((1.0, 6.0), (0.7, 5.0), (0.5, 4.0))]
for (dz, pk, n), hf in zip(res, (1.0, 0.7, 0.5)):
    print(f"fillet mesh {hf} mm ({n} dofs): tip deflection {dz:.5f} mm, peak von Mises on fillet {pk:.2f} MPa")
dz, pk, _ = res[-1]
assert abs(res[-1][0] / res[-2][0] - 1) < 2e-3 and abs(res[-1][1] / res[-2][1] - 1) < 0.02, res
out = dict(id="SOLID-L-BRACKET", family="3D CAD + FEM: filleted L-bracket",
    prompt=("Solid steel L-bracket (millimetres): a vertical leg 0 <= x <= 20, 0 <= y <= 30, 0 <= z <= 100 joined to a horizontal arm "
            "0 <= x <= 100, 0 <= y <= 30, 80 <= z <= 100 (one solid). The inside corner between the leg face x = 20 and the arm face z = 80 is "
            "rounded with a 5 mm fillet along its whole length in y. E = 200000 MPa, Poisson ratio 0.3, linear elastic, small displacements. "
            "The bottom face z = 0 is fully fixed. A total force of 2000 N acts downward (-z) as a uniform traction on the arm's end face x = 100. "
            "Report the downward deflection at the centre of the end face (x = 100, y = 15, z = 90) and the largest von Mises stress on the fillet "
            "surface.\nJSON keys: tip_deflection_mm, max_von_mises_fillet_MPa."),
    reference=dict(tip_deflection_mm=dz, max_von_mises_fillet_MPa=pk), tolerance=dict(tip_deflection_mm=0.03, max_von_mises_fillet_MPa=0.05),
    check=dict(converged=[dict(fillet_mesh_mm=hf, tip_deflection_mm=r[0], fillet_peak_MPa=r[1], dofs=r[2]) for r, hf in zip(res, (1.0, 0.7, 0.5))]))
open(sys.argv[1], "w").write(json.dumps(out) + "\n")
