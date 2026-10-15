"""Reference for the L-shaped fin task (FEniCSx, P2, mesh refinement). Writes runs/astra-variety-20261015/heat_fin_reference.json."""
import json
from pathlib import Path
import numpy as np
import gmsh
import ufl
from mpi4py import MPI
from dolfinx import fem, io
from dolfinx.fem.petsc import LinearProblem

k, t, h, Tinf, Tb = 200.0, 0.002, 25.0, 20.0, 100.0                 # SI
def solve(size):
    gmsh.initialize(); gmsh.option.setNumber("General.Verbosity", 0)
    o = gmsh.model.occ
    s = o.fuse([(2, o.addRectangle(0, 0, 0, 0.1, 0.04))], [(2, o.addRectangle(0, 0, 0, 0.04, 0.1))])[0]
    o.synchronize()
    gmsh.model.addPhysicalGroup(2, [e[1] for e in s], 1)
    base, other = [], []
    for _, c in gmsh.model.getEntities(1):
        x0, y0, _, x1, y1, _ = gmsh.model.getBoundingBox(1, c)
        (base if (abs(x0) < 1e-5 and abs(x1) < 1e-5) else other).append(c)
    assert base, 'base edge not found'
    gmsh.model.addPhysicalGroup(1, base, 2); gmsh.model.addPhysicalGroup(1, other, 3)
    gmsh.option.setNumber("Mesh.MeshSizeMax", size); gmsh.model.mesh.generate(2)
    dom, _, ft = io.gmshio.model_to_mesh(gmsh.model, MPI.COMM_WORLD, 0, gdim=2); gmsh.finalize()
    V = fem.functionspace(dom, ("Lagrange", 2))
    T, v = ufl.TrialFunction(V), ufl.TestFunction(V)
    ds = ufl.Measure("ds", domain=dom, subdomain_data=ft)
    a = k * t * ufl.dot(ufl.grad(T), ufl.grad(v)) * ufl.dx + 2 * h * T * v * ufl.dx + h * t * T * v * ds(3)
    L = 2 * h * Tinf * v * ufl.dx + h * t * Tinf * v * ds(3)
    assert len(ft.find(2)) > 0
    bdofs = fem.locate_dofs_topological(V, 1, ft.find(2))
    bc = fem.dirichletbc(fem.Constant(dom, Tb), bdofs, V)
    Th = LinearProblem(a, L, bcs=[bc], petsc_options={"ksp_type": "preonly", "pc_type": "lu"}).solve()
    # heat leaving through faces and convective edges = heat entering at the base
    Q = fem.assemble_scalar(fem.form(2 * h * (Th - Tinf) * ufl.dx + h * t * (Th - Tinf) * ds(3)))
    return Q, Th.x.array.min(), V.dofmap.index_map.size_global
res = [solve(sz) for sz in (0.004, 0.002, 0.001)]
for (Q, Tm, n), sz in zip(res, (4, 2, 1)):
    print(f"mesh {sz} mm: {n} dofs, Q = {Q:.5f} W, T_min = {Tm:.5f} C")
Q, Tm, _ = res[-1]
assert Q > 0.1 and 20 < Tm < 100, (Q, Tm)
assert abs(res[-1][0] - res[-2][0]) / Q < 1e-4 and abs(res[-1][1] - res[-2][1]) < 1e-2
out = Path(__file__).resolve().parents[2] / "runs/astra-variety-20261015"; out.mkdir(parents=True, exist_ok=True)
(out / "heat_fin_reference.json").write_text(json.dumps(dict(
    id="VAR-L-FIN-HEAT", family="steady heat conduction with convection (2D fin)",
    prompt=("Thin aluminium cooling fin: an L-shaped plate in the x-y plane made of the rectangles 0 <= x <= 100, 0 <= y <= 40 mm and "
            "0 <= x <= 40, 0 <= y <= 100 mm (arms 40 mm wide), thickness 2 mm, thermal conductivity 200 W/(m K). The whole edge x = 0 "
            "(0 <= y <= 100 mm) is held at 100 C. Every other edge and both large faces lose heat by convection, h = 25 W/(m^2 K), to air at "
            "20 C. Steady state; temperature uniform through the thickness. Report the heat flow entering through the edge x = 0 and the "
            "lowest temperature in the fin.\nJSON keys: heat_flow_W, min_temperature_C."),
    reference=dict(heat_flow_W=Q, min_temperature_C=Tm), tolerance=dict(heat_flow_W=0.03, min_temperature_C=0.02),
    check=dict(converged=[dict(mesh_mm=sz, heat_flow_W=r[0], min_temperature_C=r[1]) for r, sz in zip(res, (4, 2, 1))]))) + "\n")
