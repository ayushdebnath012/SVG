"""Independent plastic limit-load check for fcVM source pairs. Validation only, never a reference.

Run in the FEniCSx env:  tmp/fenicsx/env/bin/python scripts/fcvm_plastic_check.py --case DIR --size H --out DIR
DIR holds analysis.step and setup.json written by scripts/cadfem_bench/fam_fcvm.py from the original FreeCAD document
(published load factors are not in it). Model: small strain and small displacement, elastic-perfectly plastic von Mises
material with the control file's yield stress, quadratic tetrahedra (no volumetric locking under isochoric plastic flow),
radial return with the consistent tangent at quadrature points, full Newton. The reference load set is applied
proportionally, lambda * F_ref. Load stepping is adaptive and bisects on non-convergence. The limit load factor is
bracketed between the last converged lambda and the first lambda that cannot be equilibrated; the bracket closes to
--rel-tol.
Mesh generation, face matching and boundary conditions are the ones of scripts/fcvm_buckling_check.py.
"""
import argparse
import json
import time
from pathlib import Path

import basix.ufl
import gmsh
import numpy as np
import ufl
from dolfinx import fem, io
from dolfinx.fem.petsc import apply_lifting, assemble_matrix, assemble_vector, set_bc
from mpi4py import MPI
from petsc4py import PETSc

ap = argparse.ArgumentParser()
ap.add_argument("--case", type=Path, required=True)
ap.add_argument("--size", type=float, required=True)
ap.add_argument("--out", type=Path, required=True)
ap.add_argument("--sigma-y", type=float, required=True, help="yield stress (MPa) from the fcVM control file")
ap.add_argument("--rel-tol", type=float, default=2e-3, help="close the limit-load bracket to this relative width")
ap.add_argument("--max-steps", type=int, default=400)
a = ap.parse_args()
a.out.mkdir(parents=True, exist_ok=True)
S = json.loads((a.case / "setup.json").read_text())
t0 = time.time()

# ---------------------------------------------------------------- mesh and tags (as in fcvm_buckling_check.py)
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
gmsh.model.add("plastic")
gmsh.model.occ.importShapes(str(a.case / "analysis.step"))
vols = gmsh.model.occ.getEntities(3)
if len(vols) > 1:
    gmsh.model.occ.fragment(vols[:1], vols[1:])
gmsh.model.occ.synchronize()
surfs = [t for _, t in gmsh.model.getEntities(2)]
info = {t: (np.array(gmsh.model.occ.getCenterOfMass(2, t)), gmsh.model.occ.getMass(2, t)) for t in surfs}


def match(face):
    c, area = np.array(face["centroid_mm"]), face["area_mm2"]
    key = lambda t: np.linalg.norm(info[t][0] - c) / max(np.sqrt(area), 1e-9) + abs(info[t][1] - area) / area
    best = min(surfs, key=key)
    assert key(best) < 1e-3, (face, key(best))
    return best


bc_surf = [[match(f) for f in bc["faces"]] for bc in S["face_bcs"]]
load_surf = [match(ld["face"]) for ld in S["face_loads"]]
gmsh.model.addPhysicalGroup(3, [t for _, t in gmsh.model.getEntities(3)], 1)
for t in sorted({t for v in bc_surf for t in v} | set(load_surf)):
    gmsh.model.addPhysicalGroup(2, [t], 1000 + t)
for name, v in (("Mesh.MeshSizeMin", a.size), ("Mesh.MeshSizeMax", a.size), ("Mesh.ElementOrder", 1), ("General.NumThreads", 2)):
    gmsh.option.setNumber(name, v)
gmsh.model.mesh.generate(3)
dom, ct, ft = io.gmshio.model_to_mesh(gmsh.model, MPI.COMM_SELF, 0, gdim=3)
gmsh.finalize()

V = fem.functionspace(dom, ("Lagrange", 2, (3,)))
E, nu, sy = S["E_MPa"], S["nu"], a.sigma_y
mu, lmbda = E / (2 * (1 + nu)), E * nu / ((1 + nu) * (1 - 2 * nu))
v_, du_ = ufl.TestFunction(V), ufl.TrialFunction(V)
eps = lambda w: ufl.sym(ufl.grad(w))
sigma_el = lambda e: lmbda * ufl.tr(e) * ufl.Identity(3) + 2 * mu * e
ds = ufl.Measure("ds", domain=dom, subdomain_data=ft)

bcs = []
for k, bc in enumerate(S["face_bcs"]):
    facets = np.unique(np.concatenate([ft.find(1000 + t) for t in bc_surf[k]]))
    for comp in bc["components"]:
        Vc, _ = V.sub(comp).collapse()
        d = fem.locate_dofs_topological((V.sub(comp), Vc), 2, facets)
        bcs.append(fem.dirichletbc(fem.Function(Vc), d, V.sub(comp)))
for e in S["edge_bcs"]:
    P = np.array(e["polyline_mm"])
    tol = max(1e-3, 1e-4 * a.size)

    def on_edge(x, P=P, tol=tol):
        dmin = np.full(x.shape[1], np.inf)
        for p0, p1 in zip(P[:-1], P[1:]):
            seg = p1 - p0
            t = np.clip(((x.T - p0) @ seg) / max(seg @ seg, 1e-30), 0, 1)
            dmin = np.minimum(dmin, np.linalg.norm(x.T - (p0 + np.outer(t, seg)), axis=1))
        return dmin < tol
    for comp in e["components"]:
        Vc, _ = V.sub(comp).collapse()
        d = fem.locate_dofs_geometrical((V.sub(comp), Vc), on_edge)
        assert len(d[0]) > 0, ("no dofs on edge", e)
        bcs.append(fem.dirichletbc(fem.Function(Vc), d, V.sub(comp)))

Lref = ufl.dot(fem.Constant(dom, np.array(S["body_force_N_mm3"], dtype=PETSc.ScalarType)), v_) * ufl.dx
for k, ld in enumerate(S["face_loads"]):
    if ld["kind"] == "traction":
        Lref = Lref + ufl.dot(fem.Constant(dom, np.array(ld["traction_MPa"], dtype=PETSc.ScalarType)), v_) * ds(1000 + load_surf[k])
    else:
        Lref = Lref + ld["signed_pressure_MPa"] * ufl.dot(ufl.FacetNormal(dom), v_) * ds(1000 + load_surf[k])

# ---------------------------------------------------------------- quadrature-point state
deg = 2
dxq = ufl.dx(metadata={"quadrature_degree": deg, "quadrature_scheme": "default"})
Q6 = fem.functionspace(dom, basix.ufl.quadrature_element(dom.basix_cell(), value_shape=(6,), scheme="default", degree=deg))
Q1 = fem.functionspace(dom, basix.ufl.quadrature_element(dom.basix_cell(), value_shape=(), scheme="default", degree=deg))
sig, sig_old, n_el = fem.Function(Q6), fem.Function(Q6), fem.Function(Q6)
beta, p_old, dp = fem.Function(Q1), fem.Function(Q1), fem.Function(Q1)
Du, du, u = fem.Function(V), fem.Function(V), fem.Function(V)


def T6(s):
    return ufl.as_matrix([[s[0], s[3], s[4]], [s[3], s[1], s[5]], [s[4], s[5], s[2]]])


def V6(t):
    return ufl.as_vector([t[0, 0], t[1, 1], t[2, 2], t[0, 1], t[0, 2], t[1, 2]])


ppos = lambda x: (x + abs(x)) / 2
sig_elas = T6(sig_old) + sigma_el(eps(Du))
s_dev = ufl.dev(sig_elas)
seq = ufl.sqrt(1.5 * ufl.inner(s_dev, s_dev))
f_el = seq - sy
dp_expr = ppos(f_el) / (3 * mu)
safe = ufl.conditional(ufl.gt(seq, 1e-12 * sy), seq, 1e-12 * sy)
yielding = ufl.conditional(ufl.gt(f_el, 0), 1.0, 0.0)
n_expr = yielding * s_dev / safe
beta_expr = 3 * mu * dp_expr / safe
pts = Q6.element.interpolation_points()
X_sig = fem.Expression(V6(sig_elas - beta_expr * s_dev), pts)
X_n = fem.Expression(V6(n_expr), pts)
X_beta = fem.Expression(beta_expr, pts)
X_dp = fem.Expression(dp_expr, pts)


def update_state():
    sig.interpolate(X_sig)
    n_el.interpolate(X_n)
    beta.interpolate(X_beta)
    dp.interpolate(X_dp)


N = T6(n_el)
# perfectly plastic consistent tangent (Simo & Taylor radial return, H = 0)
tang = lambda e: sigma_el(e) - 3 * mu * (1 - beta) * ufl.inner(N, e) * N - 2 * mu * beta * ufl.dev(e)
a_form = fem.form(ufl.inner(eps(v_), tang(eps(du_))) * dxq)
fint_form = fem.form(ufl.inner(eps(v_), T6(sig)) * dxq)
F_ref = assemble_vector(fem.form(Lref))
F_ref.ghostUpdate(addv=PETSc.InsertMode.ADD, mode=PETSc.ScatterMode.REVERSE)
set_bc(F_ref, bcs)
fnorm = F_ref.norm()

A = assemble_matrix(a_form, bcs=bcs)
A.assemble()
ksp = PETSc.KSP().create(MPI.COMM_SELF)
ksp.setOperators(A)
ksp.setType("preonly")
ksp.getPC().setType("cholesky")   # the perfectly plastic consistent tangent is symmetric
ksp.getPC().setFactorSolverType("mumps")


def residual(lam):
    fi = assemble_vector(fint_form)
    fi.ghostUpdate(addv=PETSc.InsertMode.ADD, mode=PETSc.ScatterMode.REVERSE)
    r = F_ref.copy()
    r.scale(lam)
    r.axpy(-1.0, fi)
    set_bc(r, bcs, alpha=0.0)
    return r


def newton(lam, max_it=25, tol=1e-8):
    """Equilibrate lambda * F_ref from the last converged state. Returns iterations, or None if it fails."""
    Du.x.array[:] = 0.0
    update_state()
    r = residual(lam)
    r0 = max(r.norm(), 1e-30)
    for it in range(1, max_it + 1):
        A.zeroEntries()
        assemble_matrix(A, a_form, bcs=bcs)
        A.assemble()
        ksp.setOperators(A)
        ksp.solve(r, du.x.petsc_vec)
        du.x.scatter_forward()
        if not np.all(np.isfinite(du.x.array)):
            return None
        Du.x.array[:] += du.x.array
        update_state()
        r = residual(lam)
        rn = r.norm()
        if not np.isfinite(rn):
            return None
        if rn < tol * max(abs(lam) * fnorm, 1e-30):
            return it
        if it > 6 and rn > 1e3 * r0:
            return None
    return None


def commit():
    sig_old.x.array[:] = sig.x.array
    p_old.x.array[:] += dp.x.array
    u.x.array[:] += Du.x.array


# elastic solution under F_ref -> first-yield factor
assert newton(1e-9) is not None
seq_el = fem.Expression(ufl.sqrt(1.5 * ufl.inner(ufl.dev(T6(sig)), ufl.dev(T6(sig)))), pts)
probe = fem.Function(Q1)
probe.interpolate(seq_el)
lam_y = 1e-9 * sy / float(probe.x.array.max())
sig.x.array[:] = 0.0
n_el.x.array[:] = 0.0
beta.x.array[:] = 0.0
dp.x.array[:] = 0.0

lam, dlam, curve, iters, steps = 0.0, 0.9 * lam_y, [], 0, 0
lam_fail = None
while steps < a.max_steps:
    steps += 1
    trial = lam + dlam
    k = newton(trial)
    if k is None:
        lam_fail = trial if lam_fail is None else min(lam_fail, trial)
        dlam /= 2
        if dlam < a.rel_tol * max(lam, lam_y) / 2:
            break
        continue
    iters += k
    commit()
    lam = trial
    umax = float(np.linalg.norm(u.x.array.reshape(-1, 3), axis=1).max())
    curve.append([lam, umax, k])
    print(json.dumps({"lambda": lam, "max_disp_mm": umax, "newton": k, "dlam": dlam}), flush=True)
    if lam_fail is not None and lam_fail - lam < a.rel_tol * lam:
        break
    if lam_fail is None:
        dlam *= 1.5 if k <= 5 else 1.0
    else:
        dlam = min(dlam, (lam_fail - lam) / 2)

closed = lam_fail is not None and (lam_fail - lam) <= a.rel_tol * lam
rec = dict(case=S["name"], mesh_size_mm=a.size, elements=dom.topology.index_map(3).size_global, dofs=V.dofmap.index_map.size_global * 3,
           sigma_y_MPa=sy, first_yield_factor=lam_y, lambda_limit=lam if closed else None, lambda_last_converged=lam, lambda_first_failed=lam_fail,
           bracket_closed=closed, rel_tol=a.rel_tol, steps=steps, newton_iterations=iters, curve=curve,
           runtime_seconds=time.time() - t0,
           model="small strain, elastic-perfectly plastic von Mises, P2 tetrahedra, radial return + consistent tangent, proportional loading",
           solver="FEniCSx 0.9 / PETSc MUMPS", role="independent_validation_only_not_reference")
(a.out / "result.json").write_text(json.dumps(rec, indent=1) + "\n")
print(json.dumps({k: rec[k] for k in ("case", "mesh_size_mm", "elements", "first_yield_factor", "lambda_limit", "lambda_last_converged",
                                      "lambda_first_failed", "steps", "newton_iterations", "runtime_seconds")}), flush=True)
