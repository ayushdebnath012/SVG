"""Independent linear (eigenvalue) buckling check for fcVM source pairs. Validation only, never a reference.

Run in the FEniCSx env:  tmp/fenicsx/env/bin/python scripts/fcvm_buckling_check.py --case DIR --size H --out DIR
DIR holds analysis.step and setup.json (written by scripts/cadfem_bench/fam_fcvm.py from the original FreeCAD
document; published buckling factors are not in it). Steps: gmsh remesh (solids fragmented into one conforming
mesh), linear elastic prebuckling solve under the reference loads (face tractions, self-weight), geometric stiffness
K_G(u, v) = int sigma0 : (grad u)^T grad v, generalised eigenproblem K phi = lambda (-K_G) phi solved in inverse form (-K_G) phi = mu K phi
(SLEPc GHEP, largest mu); the smallest positive lambda = 1/mu is the first buckling factor.
"""
import argparse
import json
import time
from pathlib import Path

import gmsh
import numpy as np
import ufl
from dolfinx import fem, io
from dolfinx.fem.petsc import assemble_matrix, LinearProblem
from mpi4py import MPI
from petsc4py import PETSc
from slepc4py import SLEPc

ap = argparse.ArgumentParser()
ap.add_argument("--case", type=Path, required=True)
ap.add_argument("--size", type=float, required=True)
ap.add_argument("--out", type=Path, required=True)
ap.add_argument("--nev", type=int, default=6)
a = ap.parse_args()
a.out.mkdir(parents=True, exist_ok=True)
S = json.loads((a.case / "setup.json").read_text())
t0 = time.time()

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
gmsh.model.add("buckling")
gmsh.model.occ.importShapes(str(a.case / "analysis.step"))
vols = gmsh.model.occ.getEntities(3)
if len(vols) > 1:
    gmsh.model.occ.fragment(vols[:1], vols[1:])
gmsh.model.occ.synchronize()
surfs = [t for _, t in gmsh.model.getEntities(2)]
info = {t: (np.array(gmsh.model.occ.getCenterOfMass(2, t)), gmsh.model.occ.getMass(2, t)) for t in surfs}


def match(face):
    c, area = np.array(face["centroid_mm"]), face["area_mm2"]
    best = min(surfs, key=lambda t: np.linalg.norm(info[t][0] - c) / max(np.sqrt(area), 1e-9) + abs(info[t][1] - area) / area)
    err = np.linalg.norm(info[best][0] - c) / max(np.sqrt(area), 1e-9) + abs(info[best][1] - area) / area
    assert err < 1e-3, (face, err)
    return best


bc_surf = [[match(f) for f in bc["faces"]] for bc in S["face_bcs"]]
load_surf = [match(ld["face"]) for ld in S["face_loads"]]      # several loads may share a face (fcVM sums them)
gmsh.model.addPhysicalGroup(3, [t for _, t in gmsh.model.getEntities(3)], 1)
for t in sorted({t for v in bc_surf for t in v} | set(load_surf)):
    gmsh.model.addPhysicalGroup(2, [t], 1000 + t)
for name, v in (("Mesh.MeshSizeMin", a.size), ("Mesh.MeshSizeMax", a.size), ("Mesh.ElementOrder", 1), ("General.NumThreads", 2)):
    gmsh.option.setNumber(name, v)
gmsh.model.mesh.generate(3)
dom, ct, ft = io.gmshio.model_to_mesh(gmsh.model, MPI.COMM_SELF, 0, gdim=3)
gmsh.finalize()

V = fem.functionspace(dom, ("Lagrange", 2, (3,)))
E, nu = S["E_MPa"], S["nu"]
mu, lam = E / (2 * (1 + nu)), E * nu / ((1 + nu) * (1 - 2 * nu))
eps = lambda w: ufl.sym(ufl.grad(w))
sig = lambda w: lam * ufl.tr(eps(w)) * ufl.Identity(3) + 2 * mu * eps(w)
ds = ufl.Measure("ds", domain=dom, subdomain_data=ft)
u, v = ufl.TrialFunction(V), ufl.TestFunction(V)

bcs, dofs_all = [], []
fdim = 2
for k, bc in enumerate(S["face_bcs"]):
    facets = np.unique(np.concatenate([ft.find(1000 + t) for t in bc_surf[k]]))
    for comp in bc["components"]:
        Vc, _ = V.sub(comp).collapse()
        d = fem.locate_dofs_topological((V.sub(comp), Vc), fdim, facets)
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

L = ufl.dot(fem.Constant(dom, np.array(S["body_force_N_mm3"], dtype=PETSc.ScalarType)), v) * ufl.dx
for k, ld in enumerate(S["face_loads"]):
    if ld["kind"] == "traction":
        L = L + ufl.dot(fem.Constant(dom, np.array(ld["traction_MPa"], dtype=PETSc.ScalarType)), v) * ds(1000 + load_surf[k])
    else:   # pressure along the outward normal: p_signed * n
        n = ufl.FacetNormal(dom)
        L = L + ld["signed_pressure_MPa"] * ufl.dot(n, v) * ds(1000 + load_surf[k])
prob = LinearProblem(ufl.inner(sig(u), eps(v)) * ufl.dx, L, bcs=bcs,
                     petsc_options={"ksp_type": "preonly", "pc_type": "lu", "pc_factor_mat_solver_type": "mumps"})
u0 = prob.solve()
s0 = sig(u0)
KG = ufl.inner(ufl.grad(u) * s0, ufl.grad(v)) * ufl.dx       # sigma0_ij du_k/dx_i dv_k/dx_j
A = assemble_matrix(fem.form(ufl.inner(sig(u), eps(v)) * ufl.dx), bcs=bcs, diagonal=1.0)
A.assemble()
B = assemble_matrix(fem.form(-KG), bcs=bcs, diagonal=0.0)
B.assemble()
# Inverse form (-K_G) x = mu K x with K symmetric positive definite (GHEP): the largest positive mu gives the smallest
# positive buckling factor lambda = 1/mu, whatever negative (load-reversal) factors lie closer to zero.
eps_ = SLEPc.EPS().create(MPI.COMM_SELF)
eps_.setOperators(B, A)
eps_.setProblemType(SLEPc.EPS.ProblemType.GHEP)
eps_.setDimensions(a.nev, PETSc.DECIDE)
eps_.setWhichEigenpairs(SLEPc.EPS.Which.LARGEST_REAL)
st = eps_.getST()
st.setType(SLEPc.ST.Type.SHIFT)
st.setShift(0.0)
ksp = st.getKSP()
ksp.setType("preonly")
ksp.getPC().setType("cholesky")
ksp.getPC().setFactorSolverType("mumps")
eps_.setTolerances(1e-10, 1000)
eps_.solve()
mus = sorted((float(eps_.getEigenvalue(i).real) for i in range(eps_.getConverged())), reverse=True)
lams = [1 / m for m in mus if m > 1e-12]
pos = sorted(lams)
rec = dict(case=S["name"], mesh_size_mm=a.size, elements=dom.topology.index_map(3).size_global, dofs=V.dofmap.index_map.size_global * 3,
           mu=mus, eigenvalues=pos, lambda1=pos[0] if pos else None, lambda2=pos[1] if len(pos) > 1 else None,
           max_displacement_mm=float(np.linalg.norm(u0.x.array.reshape(-1, 3), axis=1).max()), runtime_seconds=time.time() - t0,
           solver="FEniCSx 0.9 / PETSc MUMPS / SLEPc Krylov-Schur (inverse form)", role="independent_validation_only_not_reference")
(a.out / "result.json").write_text(json.dumps(rec, indent=1) + "\n")
print(json.dumps({k: rec[k] for k in ("case", "mesh_size_mm", "elements", "lambda1", "lambda2", "runtime_seconds")}), flush=True)
