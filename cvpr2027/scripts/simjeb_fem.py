"""Re-solve a SimJEB bracket (GE jet engine bracket challenge, doi:10.7910/DVN/XFUWJG) with FEniCSx and compare with
SimJEB's published OptiStruct results.

The model is read from SimJEB's own OptiStruct deck (<id>.fem): first-order tets (GRID / CTETRA), Ti-6Al-4V (MAT1),
four bolt holes tied by RBE2 spiders to fixed points (here: u = 0 on those nodes, which is what a rigid spider to a
fully fixed point imposes), and the pin interface loaded through an RBE3 (here: the equivalent nodal forces,
f_i = w_i (F / W + J^-1 M_c x r_i), r_i from the weighted centroid, M_c the load's moment about it). Four subcases:
vertical, horizontal, diagonal (42 deg) and torsion, exactly as in the deck.

  python simjeb_fem.py <id>.fem <id>field.csv [--out result.json]

Needs FEniCSx 0.9 (tmp/fenicsx/env).
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np

CASES = ("ver", "hor", "dia", "tor")


def nastran_float(s: str) -> float:
    s = s.strip()
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:  # 4.43-9 style exponent
        for i in range(len(s) - 1, 0, -1):
            if s[i] in "+-" and s[i - 1] not in "eE":
                return float(s[:i] + "e" + s[i:])
        raise


def parse_fem(path: str) -> dict:
    cards, cur = [], None
    for line in open(path, errors="replace"):
        if line.startswith("$") or not line.strip():
            continue
        if line.startswith("+") or (cur is not None and line[:8].strip() == "" and cur[0] in ("RBE2", "RBE3")):
            cur += [line[i:i + 8] for i in range(8, 72, 8)]
            continue
        f = [line[i:i + 8] for i in range(0, 72, 8)]
        cur = [f[0].strip()] + f[1:]
        cards.append(cur)
    grid, tets, rbe2, rbe3, force, moment, spc, mat = {}, [], [], None, {}, {}, set(), None
    for c in cards:
        k = c[0]
        if k == "GRID":
            grid[int(c[1])] = [nastran_float(c[3]), nastran_float(c[4]), nastran_float(c[5])]
        elif k == "CTETRA":
            tets.append([int(c[3]), int(c[4]), int(c[5]), int(c[6])])
        elif k == "RBE2":
            rbe2.append(dict(ref=int(c[2]), nodes=[int(v) for v in c[4:] if v.strip()]))
        elif k == "RBE3":
            rest = [v.strip() for v in c[5:] if v.strip()]
            rbe3 = dict(ref=int(c[3]), weight=nastran_float(rest[0]), comps=rest[1], nodes=[int(v) for v in rest[2:]])
        elif k == "FORCE":
            force[int(c[1])] = nastran_float(c[4]) * np.array([nastran_float(v) for v in c[5:8]])
        elif k == "MOMENT":
            moment[int(c[1])] = nastran_float(c[4]) * np.array([nastran_float(v) for v in c[5:8]])
        elif k == "SPC":
            spc.add(int(c[2]))
        elif k == "MAT1":
            mat = dict(E=nastran_float(c[2]), nu=nastran_float(c[4]))
    return dict(grid=grid, tets=np.array(tets), rbe2=rbe2, rbe3=rbe3, force=force, moment=moment, spc=spc, mat=mat)


def rbe3_forces(x: np.ndarray, ref: np.ndarray, F: np.ndarray, M: np.ndarray, w: np.ndarray | None = None) -> np.ndarray:
    """Nodal forces at points x (n, 3) equivalent to force F and moment M at ref, distributed as an RBE3 (translations)."""
    w = np.ones(len(x)) if w is None else w
    W = w.sum()
    c = (x * w[:, None]).sum(0) / W
    r = x - c
    J = np.einsum("i,ij,ik->jk", w, r, r)
    J = np.trace(J) * np.eye(3) - J
    Mc = M + np.cross(ref - c, F)
    b = np.linalg.solve(J, Mc)
    return w[:, None] * (F / W + np.cross(b, r))


def von_mises(s: np.ndarray) -> np.ndarray:
    dev = s - np.trace(s, axis1=-2, axis2=-1)[..., None, None] / 3 * np.eye(3)
    return np.sqrt(1.5 * np.einsum("...ij,...ij->...", dev, dev))


def solve(x: np.ndarray, tets: np.ndarray, fixed: np.ndarray, loads: list[np.ndarray], E: float, nu: float) -> list[np.ndarray]:
    """P1 linear elasticity on the given tets; u = 0 at `fixed` nodes; nodal force arrays (n, 3) per load case."""
    import basix.ufl
    import ufl
    from mpi4py import MPI
    from dolfinx import fem, mesh
    from dolfinx.fem.petsc import assemble_matrix
    from petsc4py import PETSc

    dom = mesh.create_mesh(MPI.COMM_SELF, tets.astype(np.int64), x, ufl.Mesh(basix.ufl.element("Lagrange", "tetrahedron", 1, shape=(3,))))
    orig = dom.geometry.input_global_indices  # dolfinx geometry node -> input node
    V = fem.functionspace(dom, ("Lagrange", 1, (3,)))
    node = np.empty(len(orig), np.int64)
    node[V.dofmap.list.ravel()] = dom.geometry.dofmap.ravel()  # dof block -> geometry node
    blk_of_input = np.empty(len(orig), np.int64)
    blk_of_input[np.asarray(orig)[node]] = np.arange(len(orig))  # input node -> dof block
    lam, mu = E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))
    u, v = ufl.TrialFunction(V), ufl.TestFunction(V)
    eps = lambda w: ufl.sym(ufl.grad(w))  # noqa: E731
    a = fem.form(ufl.inner(lam * ufl.nabla_div(u) * ufl.Identity(3) + 2 * mu * eps(u), eps(v)) * ufl.dx)
    bdofs = (3 * blk_of_input[fixed][:, None] + np.arange(3)).ravel().astype(np.int32)
    A = assemble_matrix(a)
    A.assemble()
    A.zeroRowsColumns(bdofs, 1.0)
    X = V.tabulate_dof_coordinates() - x.mean(0)
    B = np.zeros((3 * len(X), 6))
    for i in range(3):
        B[i::3, i] = 1
    B[0::3, 3], B[1::3, 3] = -X[:, 1], X[:, 0]
    B[0::3, 4], B[2::3, 4] = X[:, 2], -X[:, 0]
    B[2::3, 5], B[1::3, 5] = X[:, 1], -X[:, 2]
    Q = np.linalg.qr(B)[0]
    A.setNearNullSpace(PETSc.NullSpace().create(vectors=[PETSc.Vec().createWithArray(np.ascontiguousarray(Q[:, k]), bsize=3, comm=PETSc.COMM_SELF) for k in range(6)]))
    ksp = PETSc.KSP().create(PETSc.COMM_SELF)
    ksp.setOperators(A)
    ksp.setType("cg")
    ksp.getPC().setType("gamg")
    ksp.setTolerances(rtol=1e-10, max_it=5000)
    out = []
    for f in loads:
        b = np.zeros(3 * len(X))
        b.reshape(-1, 3)[blk_of_input] = f
        b[bdofs] = 0.0
        bv, xv = PETSc.Vec().createWithArray(b), A.createVecRight()
        ksp.solve(bv, xv)
        if ksp.getConvergedReason() <= 0:
            raise RuntimeError(f"solver did not converge ({ksp.getConvergedReason()})")
        out.append(xv.getArray().reshape(-1, 3)[blk_of_input].copy())  # (n_input_nodes, 3)
    return out


def element_stress(x: np.ndarray, tets: np.ndarray, U: np.ndarray, E: float, nu: float) -> np.ndarray:
    P = x[tets]
    D = np.stack([P[:, 1] - P[:, 0], P[:, 2] - P[:, 0], P[:, 3] - P[:, 0]], 2)  # columns = edges
    G = np.linalg.inv(D)  # rows: gradients of barycentric coords 1..3
    grads = np.concatenate([-G.sum(1, keepdims=True), G], 1)  # (e, 4, 3)
    Gu = np.einsum("eai,eaj->eij", U[tets], grads)  # du_i/dx_j
    eps = (Gu + Gu.transpose(0, 2, 1)) / 2
    lam, mu = E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))
    return lam * np.trace(eps, axis1=1, axis2=2)[:, None, None] * np.eye(3) + 2 * mu * eps


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("fem")
    p.add_argument("csv")
    p.add_argument("--out")
    a = p.parse_args()
    t0 = time.time()
    m = parse_fem(a.fem)
    ids = np.array(sorted(i for i in m["grid"] if i not in m["spc"] and i != m["rbe3"]["ref"]))
    idx = {g: i for i, g in enumerate(ids)}
    x = np.array([m["grid"][g] for g in ids])
    tets = np.vectorize(idx.get)(m["tets"])
    fixed = np.array(sorted({idx[n] for r in m["rbe2"] for n in r["nodes"]}))
    load_nodes = np.array([idx[n] for n in m["rbe3"]["nodes"]])
    ref = np.array(m["grid"][m["rbe3"]["ref"]])
    E, nu = m["mat"]["E"], m["mat"]["nu"]
    sids = sorted(set(m["force"]) | set(m["moment"]))  # load sets 2..5 = subcases 1..4
    loads = []
    for s in sids:
        f = np.zeros((len(ids), 3))
        f[load_nodes] = rbe3_forces(x[load_nodes], ref, m["force"].get(s, np.zeros(3)), m["moment"].get(s, np.zeros(3)))
        loads.append(f)
    print(f"parsed: {len(ids)} nodes, {len(tets)} tets, {len(fixed)} fixed, {len(load_nodes)} RBE3 nodes, E={E}, nu={nu}, "
          f"load sets {sids} ({time.time() - t0:.0f}s)", flush=True)
    U = solve(x, tets, fixed, loads, E, nu)
    ref_csv = np.genfromtxt(a.csv, delimiter=",", names=True)
    order = np.array([idx[int(i)] for i in ref_csv["id"]])
    res = {}
    for case, u in zip(CASES, U):
        s = element_stress(x, tets, u, E, nu)
        vm_e = von_mises(s)
        cnt = np.bincount(tets.ravel(), minlength=len(x))
        vm_avg = np.bincount(tets.ravel(), np.repeat(vm_e, 4), minlength=len(x)) / np.maximum(cnt, 1)
        s_avg = np.stack([np.bincount(tets.ravel(), np.repeat(s[:, i, j], 4), minlength=len(x)) for i in range(3) for j in range(3)], 1).reshape(-1, 3, 3) / np.maximum(cnt, 1)[:, None, None]
        vm_tavg = von_mises(s_avg)
        mag = np.linalg.norm(u, axis=1)
        r_mag, r_vm = ref_csv[f"{case}_magdisp"], ref_csv[f"{case}_stress"]
        res[case] = dict(
            max_disp=float(mag.max()), ref_max_disp=float(r_mag.max()),
            disp_rel_l2=float(np.linalg.norm(mag[order] - r_mag) / np.linalg.norm(r_mag)),
            max_vm_element=float(vm_e.max()), max_vm_nodal_avg=float(vm_avg.max()), max_vm_tensor_avg=float(vm_tavg.max()),
            ref_max_vm=float(r_vm.max()),
            vm_rel_l2_nodal_avg=float(np.linalg.norm(vm_avg[order] - r_vm) / np.linalg.norm(r_vm)),
            vm_rel_l2_tensor_avg=float(np.linalg.norm(vm_tavg[order] - r_vm) / np.linalg.norm(r_vm)))
        print(case, {k: round(v, 4) for k, v in res[case].items()}, flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
