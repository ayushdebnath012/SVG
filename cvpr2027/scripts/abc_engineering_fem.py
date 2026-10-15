"""Engineering FEM tasks on ABC CAD models (arXiv 1812.06216): real units, feature-based supports and loads, converged answers.

Per STEP file (one solid, longest side 5-2000 mm, units mm / N / MPa):
  1. CAD faces are classified by fitting their mesh facets (plane; cylinder axis, radius, concave or convex), with exact
     areas and centroids from OpenCASCADE. Coaxial cylinder faces are merged into features; a hole is a concave
     cylinder feature covering >= 300 degrees.
  2. Supports: the largest set (>= 2) of parallel small holes (radius <= 10 % of the part's longest side) is bolted
     (u = 0 on the hole walls); a part without one is clamped on its largest planar face.
  3. Load: the hole or planar face (>= 2 % of the surface area) farthest from the supports. A hole takes a pin
     (bearing) load on the half of its wall facing the load, either along or across the lever arm; a planar face takes
     a uniform push normal to it.
  4. Material: aluminium 6061-T6, steel S355 or Ti-6Al-4V (chosen from the file hash).
  5. Linear elasticity with quadratic (P2) tets on two meshes (size longest side / 12 with curvature refinement, then every size halved).
     Answers: maximum displacement, mean displacement of the loaded surface along the load, peak von Mises stress
     outside a zone of 5 % of the longest side around the supports and the loaded surface (where idealised boundary
     conditions make stress singular), and the safety factor against yield. A part is kept only when both meshes
     agree (displacements within 5 %, peak stress within 10 %; answers are graded at 10 % and 20 %) and the deflection is small (< 1 % of the longest side).
  6. The force is a rounded value chosen so the safety factor falls between 0.7 and 4 (linear: fields scale with it).

  python abc_engineering_fem.py run --ids ids.txt --steps tmp/abc/step-0000 --out tmp/abc-eng/pilot [--workers 2]
  python abc_engineering_fem.py render --out tmp/abc-eng/pilot

Needs gmsh and FEniCSx 0.9 (tmp/fenicsx/env).
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np  # noqa: E402

MATERIALS = [  # name, E [MPa], nu, yield [MPa]
    ("aluminium 6061-T6", 68900.0, 0.33, 276.0),
    ("structural steel S355", 210000.0, 0.30, 355.0),
    ("titanium Ti-6Al-4V", 113800.0, 0.342, 880.0),
]
F0 = 1000.0  # N, unit-load solve; results are rescaled to the task force
COARSE, FINE_FACTOR, MAX_NODES = 12, 0.5, 30000  # fine mesh: every element size halved
ZONE, TOL_U, TOL_S, MAX_DEFL = 0.05, 0.05, 0.10, 0.01
GRADE_TOL = dict(max_displacement_mm=0.10, load_displacement_mm=0.10, peak_von_mises_MPa=0.20, safety_factor=0.20)  # relative
PART_TIMEOUT = 900


# ---------------------------------------------------------------- geometry
def faces_info(gmsh) -> dict:
    """Area and centroid of every CAD face (exact, from OpenCASCADE)."""
    return {s: dict(area=gmsh.model.occ.getMass(2, s), centroid=list(gmsh.model.occ.getCenterOfMass(2, s)))
            for _, s in gmsh.model.getEntities(2)}


def boundary(domain, ft):
    """Boundary facets: vertex coordinates, outward unit normals, areas, CAD face tag."""
    from dolfinx.mesh import entities_to_geometry
    top = domain.topology
    top.create_connectivity(2, 3)
    x = domain.geometry.x
    fac = ft.indices
    nodes = entities_to_geometry(domain, 2, fac)
    f2c = top.connectivity(2, 3)
    cells = entities_to_geometry(domain, 3, np.array([f2c.links(f)[0] for f in fac], np.int32))
    P = x[nodes]
    nA = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]) / 2
    nA *= np.where(np.einsum("ij,ij->i", nA, P.mean(1) - x[cells].mean(1)) < 0, -1.0, 1.0)[:, None]
    area = np.linalg.norm(nA, axis=1)
    return dict(facets=fac, tag=ft.values, P=P, c=P.mean(1), n=nA / area[:, None], area=area)


def classify(bnd: dict) -> dict:
    """Plane or cylinder per CAD face, fitted to its mesh facets (gmsh reports many ABC faces as type 'Unknown').
    Cylinder: every normal is perpendicular to one axis e and the facet centroids satisfy p = a + k n across the axis;
    k < 0 means the outward normal points at the axis, i.e. a concave (hole) wall. The radius is the vertices' mean
    distance from the axis (they lie on the true surface; facet centroids sit inside it)."""
    out = {}
    for s in np.unique(bnd["tag"]):
        m = bnd["tag"] == s
        n, c, w, V = bnd["n"][m], bnd["c"][m], bnd["area"][m], bnd["P"][m].reshape(-1, 3)
        nm = (n * w[:, None]).sum(0)
        if np.linalg.norm(nm) / w.sum() > 0.9995:
            nrm = nm / np.linalg.norm(nm)
            out[int(s)] = dict(kind="plane", normal=nrm.tolist(), offset=float(nrm @ ((c * w[:, None]).sum(0) / w.sum())))
            continue
        if m.sum() < 4:
            continue
        e = np.linalg.eigh((n * w[:, None]).T @ n)[1][:, 0]
        if np.abs(n @ e).max() > 0.08:
            continue
        P, N = c - np.outer(c @ e, e), n - np.outer(n @ e, e)
        Pc, Nc = P - P.mean(0), N - N.mean(0)
        if (Nc * Nc).sum() < 1e-6 * len(n):
            continue
        k = (Pc * Nc).sum() / (Nc * Nc).sum()
        a = (P - k * N).mean(0)
        if np.linalg.norm(P - k * N - a, axis=1).max() > 0.1 * abs(k):
            continue
        r = V - a
        r -= np.outer(r @ e, e)
        out[int(s)] = dict(kind="cylinder", axis=e.tolist(), point=a.tolist(), radius=float(np.linalg.norm(r, axis=1).mean()),
                           concave=bool(k < 0))
    return out


def features(info: dict, bnd: dict, L: float) -> list[dict]:
    """Merge coaxial cylinder faces; a concave feature covering >= 300 degrees is a hole."""
    shapes = classify(bnd)
    groups: list[dict] = []
    for s, d in shapes.items():
        if d["kind"] != "cylinder":
            continue
        c = dict(faces=[s], R=d["radius"], e=np.array(d["axis"]), a=np.array(d["point"]), concave=d["concave"],
                 p=bnd["c"][bnd["tag"] == s], area=info[s]["area"])
        for g in groups:
            if g["concave"] == c["concave"] and abs(g["R"] - c["R"]) < 0.03 * g["R"] and abs(g["e"] @ c["e"]) > 0.999:
                da = c["a"] - g["a"]
                if np.linalg.norm(da - (da @ g["e"]) * g["e"]) < 0.05 * g["R"] + 1e-3 * L:
                    g["faces"] += c["faces"]
                    g["p"] = np.vstack([g["p"], c["p"]])
                    g["area"] += c["area"]
                    break
        else:
            groups.append(c)
    out = []
    for g in groups:
        e, a = g["e"], g["a"]
        r = g["p"] - a
        r -= np.outer(r @ e, e)
        u = np.cross(e, [1, 0, 0] if abs(e[0]) < 0.9 else [0, 1, 0])
        u /= np.linalg.norm(u)
        ang = np.arctan2(r @ np.cross(e, u), r @ u)
        cover = len(np.unique(np.floor((ang + np.pi) / (2 * np.pi) * 24).astype(int) % 24)) / 24
        t = (g["p"] - a) @ e
        out.append(dict(kind="hole" if g["concave"] and cover >= 300 / 360 else "cylinder", faces=g["faces"],
                        radius=g["R"], axis=e.tolist(), centre=(a + e * (t.max() + t.min()) / 2).tolist(),
                        length=float(t.max() - t.min()), coverage=cover, area=g["area"]))
    for s, d in shapes.items():
        if d["kind"] == "plane":
            out.append(dict(kind="plane", faces=[s], area=info[s]["area"], centre=info[s]["centroid"],
                            normal=d["normal"], offset=d["offset"]))
    return out


def choose_bcs(info, feats, bnd, L, rng) -> dict | None:
    holes = [f for f in feats if f["kind"] == "hole"]
    small = [h for h in holes if h["radius"] <= 0.10 * L]
    best: list[dict] = []
    for h in small:
        par = [k for k in small if abs(np.dot(h["axis"], k["axis"])) > 0.999]
        if len(par) > len(best):
            best = par
    total = sum(d["area"] for d in info.values())
    planes = [f for f in feats if f["kind"] == "plane"]
    if len(best) >= 2:
        support = dict(kind="bolted holes", faces=sum((h["faces"] for h in best), []), holes=best)
    elif planes:
        p = max(planes, key=lambda q: q["area"])
        support = dict(kind="clamped face", faces=p["faces"], plane=p)
    else:
        return None
    sm = np.isin(bnd["tag"], support["faces"])
    s_pts = bnd["c"][sm]
    s_ctr = (bnd["c"][sm] * bnd["area"][sm, None]).sum(0) / bnd["area"][sm].sum()
    cands = [h for h in holes if h["radius"] <= 0.25 * L and not set(h["faces"]) & set(support["faces"])]
    cands += [p for p in planes if p["area"] >= 0.02 * total and not set(p["faces"]) & set(support["faces"])]
    best_c, best_d = None, 0.0
    for c in cands:
        m = np.isin(bnd["tag"], c["faces"])
        gap = np.min(np.linalg.norm(bnd["c"][m][:, None] - s_pts[None, ::max(1, len(s_pts) // 400)], axis=2))
        if gap < 0.1 * L:
            continue
        d = np.linalg.norm(np.array(c["centre"]) - s_ctr)
        if d > best_d:
            best_c, best_d = c, d
    if best_c is None:
        return None
    lever = np.array(best_c["centre"]) - s_ctr
    if best_c["kind"] == "hole":
        e = np.array(best_c["axis"])
        along = lever - (lever @ e) * e
        across = np.cross(e, along)
        variant = "along" if rng.random() < 0.5 else "across"
        d = along if variant == "along" else across
        if np.linalg.norm(d) < 1e-9 * L:
            d = np.cross(e, [1, 0, 0] if abs(e[0]) < 0.9 else [0, 1, 0])
        d /= np.linalg.norm(d)
        load = dict(kind="pin load in hole", faces=best_c["faces"], direction=d.tolist(), hole=best_c,
                    variant=f"{variant} the lever arm")
    else:
        m = np.isin(bnd["tag"], best_c["faces"])
        nrm = (bnd["n"][m] * bnd["area"][m, None]).sum(0)
        nrm /= np.linalg.norm(nrm)
        load = dict(kind="normal push on face", faces=best_c["faces"], direction=(-nrm).tolist(), plane=best_c)
    return dict(support=support, load=load, lever_mm=float(best_d), support_centre=s_ctr.tolist())


# ---------------------------------------------------------------- FEM
def solve(domain, ft, bcs, mat, L) -> dict:
    import ufl
    from dolfinx import fem, mesh as dmesh
    from dolfinx.fem.petsc import apply_lifting, assemble_matrix, assemble_vector, set_bc
    from dolfinx.mesh import entities_to_geometry
    from petsc4py import PETSc
    from scipy.spatial import cKDTree

    _, E, nu, _ = mat
    lam, mu = E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))
    bnd = boundary(domain, ft)
    sup = np.isin(bnd["tag"], bcs["support"]["faces"])
    d = np.array(bcs["load"]["direction"])
    if bcs["load"]["kind"] == "pin load in hole":
        ld = np.isin(bnd["tag"], bcs["load"]["faces"]) & (bnd["n"] @ d < -0.2)
    else:
        ld = np.isin(bnd["tag"], bcs["load"]["faces"])
    A_load = bnd["area"][ld].sum()
    if A_load <= 0 or not sup.any():
        raise ValueError("empty support or load surface")
    V = fem.functionspace(domain, ("Lagrange", 2, (3,)))
    u, v = ufl.TrialFunction(V), ufl.TestFunction(V)
    eps = lambda w: ufl.sym(ufl.grad(w))  # noqa: E731
    sig = lambda w: lam * ufl.nabla_div(w) * ufl.Identity(3) + 2 * mu * eps(w)  # noqa: E731
    tags = np.zeros(len(bnd["facets"]), np.int32)
    tags[ld] = 1
    order = np.argsort(bnd["facets"])
    mt = dmesh.meshtags(domain, 2, bnd["facets"][order], tags[order])
    ds = ufl.Measure("ds", domain=domain, subdomain_data=mt)
    t = fem.Constant(domain, PETSc.ScalarType(tuple(F0 * d / A_load)))
    a_f, L_f = fem.form(ufl.inner(sig(u), eps(v)) * ufl.dx), fem.form(ufl.inner(t, v) * ds(1))
    bc = fem.dirichletbc(np.zeros(3, dtype=PETSc.ScalarType), fem.locate_dofs_topological(V, 2, bnd["facets"][sup]), V)
    A = assemble_matrix(a_f, bcs=[bc])
    A.assemble()
    b = assemble_vector(L_f)
    apply_lifting(b, [a_f], bcs=[[bc]])
    b.ghostUpdate(addv=PETSc.InsertMode.ADD, mode=PETSc.ScatterMode.REVERSE)
    set_bc(b, [bc])
    # rigid-body near-null space for algebraic multigrid
    X = V.tabulate_dof_coordinates() - domain.geometry.x.mean(0)
    nb = X.shape[0]
    B = np.zeros((3 * nb, 6))
    for i in range(3):
        B[i::3, i] = 1
    B[0::3, 3], B[1::3, 3] = -X[:, 1], X[:, 0]
    B[0::3, 4], B[2::3, 4] = X[:, 2], -X[:, 0]
    B[2::3, 5], B[1::3, 5] = X[:, 1], -X[:, 2]
    Q = np.linalg.qr(B)[0]
    vecs = [PETSc.Vec().createWithArray(np.ascontiguousarray(Q[:, k]), bsize=3, comm=PETSc.COMM_SELF) for k in range(6)]
    A.setNearNullSpace(PETSc.NullSpace().create(vectors=vecs))
    uh = fem.Function(V)
    ksp = PETSc.KSP().create(PETSc.COMM_SELF)
    ksp.setOperators(A)
    ksp.setType("cg")
    ksp.getPC().setType("gamg")
    ksp.setTolerances(rtol=1e-10, max_it=3000)
    ksp.solve(b, uh.x.petsc_vec)
    solver = "cg+gamg"
    if ksp.getConvergedReason() <= 0:
        ksp.setType("preonly")
        ksp.getPC().setType("lu")
        ksp.getPC().setFactorSolverType("mumps")
        ksp.solve(b, uh.x.petsc_vec)
        solver = "mumps"
    uh.x.scatter_forward()
    U = uh.x.array.reshape(-1, 3)
    W = fem.functionspace(domain, ("Discontinuous Lagrange", 1))
    s = sig(uh) - ufl.tr(sig(uh)) / 3 * ufl.Identity(3)
    ip = W.element.interpolation_points
    vm = fem.Function(W)
    vm.interpolate(fem.Expression(ufl.sqrt(1.5 * ufl.inner(s, s)), ip() if callable(ip) else ip))
    cell_dofs = W.dofmap.list
    xc = W.tabulate_dof_coordinates()[cell_dofs]  # (cells, 4, 3)
    vmc = vm.x.array[cell_dofs]
    tree = cKDTree(np.vstack([bnd["P"][sup].reshape(-1, 3), bnd["P"][ld].reshape(-1, 3)]))
    far = tree.query(xc.mean(1))[0] > ZONE * L
    if not far.any():
        raise ValueError("no material outside the support/load zone")
    k = np.argmax(np.where(far[:, None], vmc, -1).ravel())
    # mean displacement of the loaded surface along the load (area-weighted, displacement at facet vertices)
    ux = fem.Function(fem.functionspace(domain, ("Lagrange", 1, (3,))))
    ux.interpolate(uh)
    Vp1 = ux.function_space
    node_of = np.empty(len(domain.geometry.x), np.int64)
    node_of[Vp1.dofmap.list.ravel()] = domain.geometry.dofmap.ravel()
    Un = np.empty((len(domain.geometry.x), 3))
    Un[node_of] = ux.x.array.reshape(-1, 3)
    ln = entities_to_geometry(domain, 2, bnd["facets"][ld])
    u_load = float((Un[ln].mean(1) @ d * bnd["area"][ld]).sum() / A_load)
    return dict(max_u=float(np.linalg.norm(U, axis=1).max()), u_load=u_load, peak_vm=float(vmc.ravel()[k]),
                peak_at=xc.reshape(-1, 3)[k].tolist(), dofs=int(3 * nb), solver=solver,
                load_area=float(A_load), field=(domain.geometry.x.copy(), Un, vm, W))


def mesh_model(gmsh, L: float, factor: float) -> int:
    gmsh.model.mesh.clear()
    gmsh.option.setNumber("Mesh.MeshSizeFactor", factor)
    gmsh.option.setNumber("Mesh.MeshSizeMax", L / COARSE)
    gmsh.option.setNumber("Mesh.MeshSizeMin", L / (COARSE * 40))
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
    gmsh.option.setNumber("Mesh.ElementOrder", 1)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    try:
        gmsh.option.setNumber("Mesh.Algorithm3D", 10)
        gmsh.model.mesh.generate(3)
    except Exception:  # noqa: BLE001 - HXT failed; Delaunay
        gmsh.model.mesh.clear()
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)
        gmsh.model.mesh.generate(3)
    return len(gmsh.model.mesh.getNodes()[0])


def one_part(step: str, out_dir: str) -> dict:
    import gmsh
    from mpi4py import MPI
    from dolfinx.io import gmshio

    sha = hashlib.sha256(Path(step).read_bytes()).hexdigest()
    rng = np.random.default_rng(int(sha[:8], 16))
    mat = MATERIALS[int(sha[8:16], 16) % len(MATERIALS)]
    row = dict(id=Path(step).stem, step=step, sha256=sha)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setString("Geometry.OCCTargetUnit", "MM")
    try:
        gmsh.model.occ.importShapes(step)
        gmsh.model.occ.synchronize()
        vols = gmsh.model.getEntities(3)
        if len(vols) != 1:
            return dict(row, status="skipped:solids", n_volumes=len(vols))
        lo, hi = np.array(gmsh.model.getBoundingBox(-1, -1)[:3]), np.array(gmsh.model.getBoundingBox(-1, -1)[3:])
        L = float((hi - lo).max())
        row.update(size_mm=(hi - lo).round(3).tolist(), n_faces=len(gmsh.model.getEntities(2)))
        if not 5 <= L <= 2000:
            return dict(row, status="skipped:size")
        info = faces_info(gmsh)
        gmsh.model.addPhysicalGroup(3, [vols[0][1]], tag=1)
        for _, s in gmsh.model.getEntities(2):
            gmsh.model.addPhysicalGroup(2, [s], tag=s)
        res, bcs = {}, None
        for name, factor in (("coarse", 1.0), ("fine", FINE_FACTOR)):
            nodes = mesh_model(gmsh, L, factor)
            if nodes > MAX_NODES:
                return dict(row, status="skipped:nodes", **{f"{name}_nodes": nodes})
            domain, _, ft = gmshio.model_to_mesh(gmsh.model, MPI.COMM_SELF, 0, gdim=3)
            if bcs is None:
                feats = features(info, boundary(domain, ft), L)
                bcs = choose_bcs(info, feats, boundary(domain, ft), L, rng)
                if bcs is None:
                    return dict(row, status="skipped:no_bcs", n_holes=sum(f["kind"] == "hole" for f in feats))
            res[name] = solve(domain, ft, bcs, mat, L)
            res[name]["nodes"] = nodes
    finally:
        gmsh.finalize()
    c, f = res["coarse"], res["fine"]
    rel = {k: abs(f[k] - c[k]) / abs(f[k]) for k in ("max_u", "u_load", "peak_vm")}
    row.update(material=dict(name=mat[0], E_MPa=mat[1], nu=mat[2], yield_MPa=mat[3]), L_mm=L,
               convergence=dict(rel_change=rel, coarse={k: c[k] for k in ("max_u", "u_load", "peak_vm", "dofs", "nodes", "solver")},
                                fine={k: f[k] for k in ("max_u", "u_load", "peak_vm", "dofs", "nodes", "solver")}))
    if max(rel["max_u"], rel["u_load"]) > TOL_U or rel["peak_vm"] > TOL_S:
        return dict(row, status="rejected:not_converged", bcs=strip(bcs))
    sf_target = float(np.exp(rng.uniform(np.log(0.7), np.log(4.0))))
    F = float(f"{F0 * mat[3] / (sf_target * f['peak_vm']):.2g}")
    k = F / F0
    ref = dict(max_displacement_mm=k * f["max_u"], load_displacement_mm=k * f["u_load"], peak_von_mises_MPa=k * f["peak_vm"],
               peak_location_mm=f["peak_at"], safety_factor=mat[3] / (k * f["peak_vm"]))
    if ref["max_displacement_mm"] > MAX_DEFL * L:
        return dict(row, status="rejected:large_deflection", bcs=strip(bcs), force_N=F)
    row.update(status="ok", force_N=F, bcs=strip(bcs), reference=ref, tolerance=GRADE_TOL, zone_mm=ZONE * L)
    row["prompt"] = prompt(row)
    x, Un, vm, W = f["field"]
    import h5py
    with h5py.File(Path(out_dir) / "fields" / f"{row['id']}.h5", "w") as h:
        h.create_dataset("Vertices", data=x)
        h.create_dataset("u_mm", data=k * Un)
        h.create_dataset("VonMises_cell_vertices_MPa", data=k * vm.x.array[W.dofmap.list])
        h.create_dataset("Cell_Points_mm", data=W.tabulate_dof_coordinates()[W.dofmap.list])
        h.attrs.update(force_N=F, units="mm, N, MPa")
    return row


def strip(bcs: dict) -> dict:
    def clean(d):
        if isinstance(d, dict):
            return {k: clean(v) for k, v in d.items() if k not in ("p",)}
        if isinstance(d, list):
            return [clean(v) for v in d]
        if isinstance(d, np.ndarray):
            return d.tolist()
        if isinstance(d, (np.floating, np.integer)):
            return d.item()
        return d
    return clean(bcs)


def fmt(v) -> str:
    return "(" + ", ".join(f"{x:.3g}" for x in v) + ")"


def prompt(r: dict) -> str:
    m, s, ld = r["material"], r["bcs"]["support"], r["bcs"]["load"]
    if s["kind"] == "bolted holes":
        hs = s["holes"]
        sup = (f"the {len(hs)} holes of diameter {2 * hs[0]['radius']:.3g} mm with axes along {fmt(hs[0]['axis'])}, centred at "
               + "; ".join(fmt(h["centre"]) for h in hs) + f" (STEP faces {s['faces']}), are bolted: their walls are fully fixed")
    else:
        sup = (f"the planar face of area {s['plane']['area']:.4g} mm^2 centred at {fmt(s['plane']['centre'])} "
               f"(STEP face {s['faces'][0]}) is fully fixed")
    if ld["kind"] == "pin load in hole":
        h = ld["hole"]
        lo = (f"a pin in the hole of diameter {2 * h['radius']:.3g} mm centred at {fmt(h['centre'])} with axis {fmt(h['axis'])} "
              f"(STEP faces {ld['faces']}) pulls with {r['force_N']:.4g} N in direction {fmt(ld['direction'])}, "
              "bearing uniformly on the half of the hole wall that faces the load")
    else:
        lo = (f"a uniform pressure pushes on the planar face of area {ld['plane']['area']:.4g} mm^2 centred at "
              f"{fmt(ld['plane']['centre'])} (STEP face {ld['faces'][0]}) with a total force of {r['force_N']:.4g} N "
              f"in direction {fmt(ld['direction'])}")
    return (f"Linear static stress check of a part made of {m['name']} (E = {m['E_MPa']:.6g} MPa, nu = {m['nu']}, "
            f"yield strength {m['yield_MPa']:.4g} MPa). Geometry: the attached STEP file, in millimetres "
            f"(bounding box {' x '.join(f'{v:.4g}' for v in r['size_mm'])} mm). Supports: {sup}. Load: {lo}. "
            "Assume small deformations and linear elasticity; ignore gravity. Report (1) the maximum displacement "
            "magnitude in mm, (2) the mean displacement of the loaded surface along the load direction in mm, (3) the "
            f"peak von Mises stress in MPa excluding material within {r['zone_mm']:.3g} mm of the supports and of the "
            "loaded surface, and (4) the safety factor against yield based on (3).")


# ---------------------------------------------------------------- driver
def run(a) -> None:
    out = Path(a.out)
    (out / "fields").mkdir(parents=True, exist_ok=True)
    man = out / "manifest.jsonl"
    done = {json.loads(line)["id"] for line in man.open()} if man.exists() else set()
    ids = [i.strip() for i in Path(a.ids).read_text().split() if i.strip()]
    steps = [next(Path(a.steps).glob(f"{i.split('_')[0]}/{i}.step")) for i in ids]
    todo = [s for s in steps if s.stem not in done]
    print(f"{len(steps)} parts, {len(todo)} to run", flush=True)

    def work(step: Path) -> dict:
        t0 = time.time()
        try:
            r = subprocess.run([sys.executable, "-I", __file__, "one", str(step), str(out)], capture_output=True,
                               text=True, timeout=PART_TIMEOUT)
            lines = [ln for ln in r.stdout.splitlines() if ln.startswith("{")]
            row = json.loads(lines[-1]) if r.returncode == 0 and lines else \
                dict(id=step.stem, status="failed", error=(r.stderr or "")[-400:])
        except subprocess.TimeoutExpired:
            row = dict(id=step.stem, status="skipped:timeout")
        row["seconds"] = round(time.time() - t0, 1)
        return row

    with ThreadPoolExecutor(a.workers) as ex, man.open("a") as h:
        for i, row in enumerate(ex.map(work, todo), 1):
            h.write(json.dumps(row) + "\n")
            h.flush()
            print(f"{i}/{len(todo)} {row['id'][:8]} {row['status']} {row['seconds']}s", flush=True)
    rows = [json.loads(line) for line in man.open()]
    (out / "tasks.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows if r["status"] == "ok"))
    stat: dict[str, int] = {}
    for r in rows:
        stat[r["status"]] = stat.get(r["status"], 0) + 1
    (out / "summary.json").write_text(json.dumps(dict(parts=len(rows), status=stat), indent=1))
    print(json.dumps(stat), flush=True)


def render(a) -> None:
    """Part with supports (blue), loaded faces (red) and load arrow; von Mises on the fine mesh."""
    import gmsh
    import h5py
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from scipy.spatial import cKDTree

    out = Path(a.out)
    (out / "figures").mkdir(exist_ok=True)
    for r in (json.loads(line) for line in (out / "tasks.jsonl").open()):
        png = out / "figures" / f"{r['id']}.png"
        if png.exists() and not a.force:
            continue
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setString("Geometry.OCCTargetUnit", "MM")
        gmsh.model.occ.importShapes(r["step"])
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMax", r["L_mm"] / 40)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
        gmsh.model.mesh.generate(2)
        tris, tag = [], []
        for _, s in gmsh.model.getEntities(2):
            _, _, nt = gmsh.model.mesh.getElements(2, s)
            for block in nt:
                tris.append(np.array(block).reshape(-1, 3))
                tag += [s] * (len(block) // 3)
        ntag, xyz, _ = gmsh.model.mesh.getNodes()
        gmsh.finalize()
        idx = {int(t): i for i, t in enumerate(ntag)}
        X = np.array(xyz).reshape(-1, 3)
        P = X[np.vectorize(idx.get)(np.vstack(tris))]
        tag = np.array(tag)
        with h5py.File(out / "fields" / f"{r['id']}.h5") as h:
            pts, vals = h["Cell_Points_mm"][:].reshape(-1, 3), h["VonMises_cell_vertices_MPa"][:].ravel()
        vm = vals[cKDTree(pts).query(P.mean(1))[1]]
        nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-30
        light = np.array([0.4, -0.5, 0.75]) / np.linalg.norm([0.4, -0.5, 0.75])
        shade = 0.45 + 0.55 * np.abs(nrm @ light)
        sup, ld = r["bcs"]["support"]["faces"], r["bcs"]["load"]["faces"]
        base = np.full((len(P), 3), 0.78)
        base[np.isin(tag, sup)] = (0.2, 0.4, 0.85)
        base[np.isin(tag, ld)] = (0.85, 0.25, 0.2)
        hi = r["reference"]["peak_von_mises_MPa"]
        cm = plt.get_cmap("turbo")(np.clip(vm / hi, 0, 1))[:, :3]
        ctr, half = (P.reshape(-1, 3).max(0) + P.reshape(-1, 3).min(0)) / 2, r["L_mm"] / 2
        fig = plt.figure(figsize=(9, 4.2), dpi=110)
        for k, (cols, title) in enumerate(((base, "supports (blue), loaded surface (red)"),
                                           (cm, f"von Mises, 0-{hi:.3g} MPa (peak outside zone)"))):
            ax = fig.add_subplot(1, 2, k + 1, projection="3d")
            ax.add_collection3d(Poly3DCollection(P, facecolors=np.clip(cols * shade[:, None], 0, 1),
                                                 edgecolors=(0, 0, 0, 0.08), linewidths=0.15))
            if k == 0:
                m = np.isin(tag, ld)
                c0 = P[m].reshape(-1, 3).mean(0)
                d = np.array(r["bcs"]["load"]["direction"]) * 0.35 * r["L_mm"]
                ax.quiver(*(c0 - d), *d, color="k", linewidth=2, arrow_length_ratio=0.25)
            ax.set_xlim(ctr[0] - half, ctr[0] + half)
            ax.set_ylim(ctr[1] - half, ctr[1] + half)
            ax.set_zlim(ctr[2] - half, ctr[2] + half)
            ax.set_box_aspect((1, 1, 1))
            ax.view_init(24, -58)
            ax.set_axis_off()
            ax.set_title(title, fontsize=9)
        fig.suptitle(f"{r['id'][:8]}  {r['material']['name']}, {r['force_N']:.4g} N, SF {r['reference']['safety_factor']:.2f}", fontsize=9)
        fig.savefig(png, bbox_inches="tight")
        plt.close(fig)
    print("figures in", out / "figures", flush=True)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "one":  # child process, one part
        print(json.dumps(one_part(sys.argv[2], sys.argv[3])))
        return
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--ids", required=True)
    r.add_argument("--steps", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=2)
    g = sub.add_parser("render")
    g.add_argument("--out", required=True)
    g.add_argument("--force", action="store_true")
    a = p.parse_args()
    dict(run=run, render=render)[a.cmd](a)


if __name__ == "__main__":
    main()
