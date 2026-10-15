"""Apply the SFEM data-generation method (github.com/cmudrc/SFEM @ ba1e7b8) to ABC CAD models (arXiv 1812.06216).

Per STEP file, as in SFEM's mesh_generation.py + simulation.py:
  gmsh linear tets (MeshSizeMax 0.1, Frontal-Delaunay 2-D, HXT 3-D, Netgen optimisation, 60 s limit, <= 2000 nodes),
  one physical group per CAD face -> fixed = the face group with the most triangles (u = 0), the other faces are free ->
  load classes small / medium / large = 5 / 10 / 20 clumps of 3-10 / 6-20 / 10-30 consecutive free facets under a
  pressure of 200 / 2000 / 20000 (traction -p n) -> 50 iterations each -> FEniCSx P1 linear elasticity,
  E = 2.303 GPa, nu = 0.4002 -> per-vertex medians of u, von Mises and the deviatoric stress -> one H5 per load class
  with SFEM's datasets (Vertices, u, VonMises, StressTensor, Cell_Faces, Facets, Load_Class, Fixed_Facet).

Deliberate differences from SFEM's scripts (each is recorded in the H5 attributes and the manifest):
  * ABC parts come in their designers' units; SFEM's parts (BrepGen) lie in [-1, 1]^3 and were meshed with an absolute
    size of 0.1. Each part is therefore centred and scaled so its longest half-extent is 1 (scale and centre stored).
  * the RNG is seeded per model and every iteration's loaded facets are stored, so each result can be re-run.
  * SFEM solves each clump on its own and its arrays keep only the last clump of an iteration. The SFEM-format
    datasets reproduce that; the group /all_clumps holds the medians with every clump of an iteration applied at once.
  * one LU factorisation per model; load vectors are assembled in closed form (P1 on flat triangles: -p n A / 3 per
    vertex), which equals SFEM's ufl form exactly. Stresses are interpolated with dolfinx exactly as SFEM does.
  * only single-solid models are kept (a loose body has no support, so SFEM's LU solve fails on it).

  python sfem_abc_generate.py run --steps tmp/abc/step-0000 --out tmp/abc-sfem/chunk-0000 [--limit 50] [--workers 8]
  python sfem_abc_generate.py render --out tmp/abc-sfem/chunk-0000
  python sfem_abc_generate.py package --out tmp/abc-sfem/chunk-0000 --dest tmp/abc-sfem/dataset

Needs gmsh, FEniCSx 0.9 (dolfinx), h5py, scipy, matplotlib (see tmp/fenicsx/env).
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")  # one core per model; the pool runs models in parallel
import numpy as np  # noqa: E402

SFEM_COMMIT = "ba1e7b8"
E, NU = 2.303e9, 0.4002
LC, MESH_TIMEOUT, MAX_NODES, ITERATIONS = 0.1, 60, 2000, 50
LOAD_CLASSES = {  # SFEM simulation.py
    "small_Load": dict(force=200, num_clumps=5, min_size=3, max_size=10),
    "medium_Load": dict(force=2000, num_clumps=10, min_size=6, max_size=20),
    "large_Load": dict(force=20000, num_clumps=20, min_size=10, max_size=30),
}


# ---------------------------------------------------------------- meshing (own process: gmsh can hang)
def mesh_step(step: str, msh: str) -> dict:
    import gmsh
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
        gmsh.option.setNumber("Mesh.MeshSizeMax", LC)
        gmsh.option.setNumber("Mesh.Algorithm", 6)
        gmsh.option.setNumber("Mesh.Algorithm3D", 10)
        gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
        gmsh.merge(step)
        gmsh.model.mesh.createGeometry()
        gmsh.model.occ.synchronize()
        ents = next(e for e in (gmsh.model.occ.getEntities(d) for d in (3, 2, 1, 0)) if e)  # top-level shapes only
        lo = np.array(gmsh.model.getBoundingBox(-1, -1)[:3])
        hi = np.array(gmsh.model.getBoundingBox(-1, -1)[3:])
        centre, half = (lo + hi) / 2, float((hi - lo).max() / 2)
        if half <= 0:
            return dict(status="skipped:empty")
        gmsh.model.occ.translate(ents, *(-centre))
        gmsh.model.occ.dilate(ents, 0, 0, 0, 1 / half, 1 / half, 1 / half)
        gmsh.model.occ.synchronize()
        gmsh.model.occ.removeAllDuplicates()
        gmsh.model.occ.synchronize()
        vols = gmsh.model.occ.getEntities(dim=3)
        info = dict(scale=1 / half, centre=centre.tolist(), bbox_units=(hi - lo).tolist(), n_volumes=len(vols),
                    n_faces=len(gmsh.model.occ.getEntities(dim=2)))
        if len(vols) != 1:
            return dict(info, status="skipped:solids")
        gmsh.model.addPhysicalGroup(3, [v[1] for v in vols], tag=1)
        for _, s in gmsh.model.occ.getEntities(dim=2):
            gmsh.model.addPhysicalGroup(2, [s], tag=s)
        gmsh.model.occ.synchronize()
        gmsh.model.mesh.generate(3)
        nodes = len(gmsh.model.mesh.getNodes()[0])
        info["n_nodes"] = nodes
        if nodes > MAX_NODES:
            return dict(info, status="skipped:nodes")
        gmsh.write(msh)
        return dict(info, status="meshed")
    finally:
        gmsh.finalize()


# ---------------------------------------------------------------- simulation
def clumps(rng, free_facets, num_clumps, min_size, max_size):
    """SFEM generate_random_clumps with a seeded generator."""
    sizes = rng.integers(min_size, max_size + 1, num_clumps)
    starts = rng.integers(0, len(free_facets) - sizes + 1)
    return [free_facets[s:s + n] for s, n in zip(starts, sizes)]


def simulate(msh: str, h5_prefix: str, seed: int, info: dict) -> dict:
    import h5py
    from mpi4py import MPI
    from scipy.sparse.linalg import splu
    import ufl
    from dolfinx import fem
    from dolfinx.io import gmshio
    from dolfinx.mesh import entities_to_geometry

    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    domain, _, ft = gmshio.read_from_msh(msh, MPI.COMM_SELF, 0, gdim=3)
    tdim, x = 3, domain.geometry.x
    n = x.shape[0]
    top = domain.topology
    for a, b in ((2, 0), (2, 3), (3, 0)):
        top.create_connectivity(a, b)
    n_facets, n_cells = top.index_map(2).size_local, top.index_map(3).size_local
    facet_nodes = entities_to_geometry(domain, 2, np.arange(n_facets, dtype=np.int32))
    cell_nodes = entities_to_geometry(domain, 3, np.arange(n_cells, dtype=np.int32))

    tags, counts = np.unique(ft.values, return_counts=True)
    fixed_tag = tags[np.argmax(counts)]
    fixed_facets = ft.find(fixed_tag)
    free_facets = np.concatenate([ft.find(t) for t in np.setdiff1d(tags, fixed_tag)] or [np.zeros(0, np.int32)])
    if len(free_facets) < max(p["max_size"] for p in LOAD_CLASSES.values()):  # e.g. a one-face part (sphere)
        return dict(status="skipped:free_facets")

    # outward unit normal x area / 3 for every boundary facet (P1, flat triangle: int phi_i dA = A / 3)
    f2c = top.connectivity(2, 3)
    p0, p1, p2 = (x[facet_nodes[:, i]] for i in range(3))
    nA = np.cross(p1 - p0, p2 - p0) / 2
    own = np.array([f2c.links(f)[0] for f in range(n_facets)])
    centre = x[cell_nodes[own]].mean(1)
    nA *= np.where(np.einsum("ij,ij->i", nA, (p0 + p1 + p2) / 3 - centre) < 0, -1.0, 1.0)[:, None]
    area = np.linalg.norm(nA, axis=1)

    lam, mu = E * NU / ((1 + NU) * (1 - 2 * NU)), E / (2 * (1 + NU))
    V = fem.functionspace(domain, ("Lagrange", 1, (3,)))
    Vs = fem.functionspace(domain, ("Lagrange", 1))
    Vt = fem.functionspace(domain, ("Lagrange", 1, (3, 3)))
    node_of = {}
    for name, sp in (("V", V), ("Vs", Vs), ("Vt", Vt)):  # dof block -> geometry node
        m = np.empty(n, np.int64)
        m[sp.dofmap.list.ravel()] = domain.geometry.dofmap.ravel()
        node_of[name] = m
    blk = np.empty(n, np.int64)
    blk[node_of["V"]] = np.arange(n)  # geometry node -> dof block of V

    eps = lambda w: ufl.sym(ufl.grad(w))  # noqa: E731
    sig = lambda w: lam * ufl.nabla_div(w) * ufl.Identity(3) + 2 * mu * eps(w)  # noqa: E731
    u, v = ufl.TrialFunction(V), ufl.TestFunction(V)
    K = fem.assemble_matrix(fem.form(ufl.inner(sig(u), eps(v)) * ufl.dx)).to_scipy().tocsr()
    fixed_nodes = np.unique(facet_nodes[fixed_facets])
    bc = (3 * blk[fixed_nodes][:, None] + np.arange(3)).ravel()
    keep = np.ones(3 * n)
    keep[bc] = 0
    from scipy.sparse import diags
    K = (diags(keep) @ K @ diags(keep) + diags(1 - keep)).tocsc()
    lu = splu(K)

    uh = fem.Function(V)
    s = sig(uh) - 1.0 / 3 * ufl.tr(sig(uh)) * ufl.Identity(3)
    ip = lambda sp: sp.element.interpolation_points() if callable(sp.element.interpolation_points) else sp.element.interpolation_points  # noqa: E731
    vm_f, s_f = fem.Function(Vs), fem.Function(Vt)
    vm_e, s_e = fem.Expression(ufl.sqrt(3.0 / 2 * ufl.inner(s, s)), ip(Vs)), fem.Expression(s, ip(Vt))

    def fields(U):  # U: dof vector -> (u, vM, dev stress) in geometry-node order, via dolfinx interpolation as SFEM
        uh.x.array[:] = U
        vm_f.interpolate(vm_e)
        s_f.interpolate(s_e)
        out_u, out_vm, out_s = np.empty((n, 3)), np.empty(n), np.empty((n, 9))
        out_u[node_of["V"]] = U.reshape(n, 3)
        out_vm[node_of["Vs"]] = vm_f.x.array
        out_s[node_of["Vt"]] = s_f.x.array.reshape(n, 9)
        return out_u, out_vm, out_s

    def load(facets, p):
        F = np.zeros((n, 3))
        for i in range(3):
            np.add.at(F, blk[facet_nodes[facets, i]], -p * nA[facets] / 3)
        F = F.ravel()
        F[bc] = 0
        return F

    fixed_free = np.zeros((n, 2), int)
    fixed_free[facet_nodes[fixed_facets].ravel(), 0] = 1
    fixed_free[facet_nodes[np.sort(free_facets)].ravel(), 1] = 1
    bnd = ft.indices
    out = dict(status="ok", n_nodes=n, n_cells=n_cells, fixed_tag=int(fixed_tag),
               fixed_area_fraction=float(area[fixed_facets].sum() / area[bnd].sum()), classes={})
    for ci, (lc_name, prm) in enumerate(LOAD_CLASSES.items()):
        rng = np.random.default_rng([seed, ci])
        last, every, zones = [], [], np.full((ITERATIONS, prm["num_clumps"], prm["max_size"], 3), -1, np.int32)
        for it in range(ITERATIONS):
            cl = clumps(rng, free_facets, prm["num_clumps"], prm["min_size"], prm["max_size"])
            for k, c in enumerate(cl):
                zones[it, k, :len(c)] = facet_nodes[c]
            Fs = np.stack([load(c, prm["force"]) for c in cl], 1)
            U = lu.solve(Fs)
            last.append(fields(U[:, -1]))
            every.append(fields(U.sum(1)))
        med = lambda rows, j: np.median(np.stack([r[j] for r in rows]), axis=0)  # noqa: E731
        with h5py.File(f"{h5_prefix}_{lc_name}.h5", "w") as f:
            f.create_dataset("Vertices", data=x)
            f.create_dataset("u", data=med(last, 0))
            f.create_dataset("VonMises", data=med(last, 1)[:, None])
            f.create_dataset("StressTensor", data=med(last, 2).reshape(n, 3, 3))
            f.create_dataset("Cell_Faces", data=facet_nodes.astype(np.int32))
            f.create_dataset("Facets", data=cell_nodes.astype(np.int32))
            f.create_dataset("Load_Class", data=np.array([lc_name], dtype="S"))
            f.create_dataset("Fixed_Facet", data=fixed_free)
            g = f.create_group("all_clumps")
            g.create_dataset("u", data=med(every, 0))
            g.create_dataset("VonMises", data=med(every, 1)[:, None])
            g.create_dataset("StressTensor", data=med(every, 2).reshape(n, 3, 3))
            f.create_dataset("Boundary_Faces", data=facet_nodes[bnd].astype(np.int32))
            f.create_dataset("Boundary_Face_Tag", data=ft.values.astype(np.int32))
            f.create_dataset("Load_Zones", data=zones, compression="gzip")
            f.attrs.update(dict(method=f"SFEM {SFEM_COMMIT} applied to ABC", seed=seed, load_class_index=ci,
                                scale=info["scale"], centre=info["centre"], E=E, nu=NU, iterations=ITERATIONS,
                                fixed_tag=int(fixed_tag), sfem_datasets="last clump of each iteration (as SFEM)",
                                all_clumps="every clump of an iteration applied together"))
        out["classes"][lc_name] = dict(vm_max=float(med(last, 1).max()), vm_median=float(np.median(med(last, 1))),
                                       vm_max_all=float(med(every, 1).max()),
                                       u_max=float(np.linalg.norm(med(last, 0), axis=1).max()))
    return out


# ---------------------------------------------------------------- driver
def one_model(step: Path, out: Path) -> dict:
    mid = step.stem
    row = dict(id=mid, step=str(step), sha256=hashlib.sha256(step.read_bytes()).hexdigest())
    (out / "msh").mkdir(parents=True, exist_ok=True)
    (out / "h5").mkdir(parents=True, exist_ok=True)
    msh = out / "msh" / f"{mid}.msh"
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "-I", __file__, "mesh", str(step), str(msh)], capture_output=True, text=True,
                           timeout=MESH_TIMEOUT)
        info = json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 and r.stdout.strip() else \
            dict(status="failed:mesh", error=(r.stderr or "")[-300:])
    except subprocess.TimeoutExpired:
        info = dict(status="skipped:mesh_timeout")
    row.update(info, mesh_s=round(time.time() - t0, 2))
    if info["status"] != "meshed":
        msh.unlink(missing_ok=True)
        return row
    t1 = time.time()
    seed = int(row["sha256"][:8], 16)
    try:
        row.update(simulate(str(msh), str(out / "h5" / mid), seed, info), seed=seed)
    except Exception as e:  # noqa: BLE001 - recorded per model
        row.update(status="failed:sim", error=f"{type(e).__name__}: {e}"[:300])
    row["sim_s"] = round(time.time() - t1, 2)
    return row


def run(a) -> None:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    man = out / "manifest.jsonl"
    done = {json.loads(line)["id"] for line in man.open()} if man.exists() else set()
    steps = sorted(Path(a.steps).rglob("*.step"))[: a.limit or None]
    todo = [p for p in steps if p.stem not in done]
    print(f"{len(steps)} STEP files, {len(done)} done, {len(todo)} to run", flush=True)
    with ProcessPoolExecutor(a.workers) as ex, man.open("a") as h:
        futs = {ex.submit(one_model, p, out): p for p in todo}
        for i, fu in enumerate(as_completed(futs), 1):
            try:
                row = fu.result()
            except Exception as e:  # noqa: BLE001
                row = dict(id=futs[fu].stem, status="failed:worker", error=str(e)[:300])
            h.write(json.dumps(row) + "\n")
            h.flush()
            if i % 25 == 0 or i == len(todo):
                print(f"{i}/{len(todo)} last={row['id']} {row['status']}", flush=True)
    rows = [json.loads(line) for line in man.open()]
    stat: dict[str, int] = {}
    for r in rows:
        stat[r["status"]] = stat.get(r["status"], 0) + 1
    (out / "summary.json").write_text(json.dumps(dict(models=len(rows), status=stat, method=__doc__.split("\n\n")[0]), indent=1))
    print(json.dumps(stat), flush=True)


def render(a) -> None:
    """Part render (CAD faces shaded, fixed face blue) and the median von Mises field (large load, all clumps)."""
    import h5py
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    out = Path(a.out)
    fig_dir = out / "figures"
    fig_dir.mkdir(exist_ok=True)
    rows = [json.loads(line) for line in (out / "manifest.jsonl").open()]
    for r in (r for r in rows if r["status"] == "ok"):
        png = fig_dir / f"{r['id']}.png"
        if png.exists() and not a.force:
            continue
        with h5py.File(out / "h5" / f"{r['id']}_large_Load.h5") as f:
            x, tri, tag = f["Vertices"][:], f["Boundary_Faces"][:], f["Boundary_Face_Tag"][:]
            vm = f["all_clumps/VonMises"][:, 0]
            fixed = int(f.attrs["fixed_tag"])
        P = x[tri]
        nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-30
        shade = 0.45 + 0.55 * np.abs(nrm @ np.array([0.4, -0.5, 0.75]) / np.linalg.norm([0.4, -0.5, 0.75]))
        base = np.where((tag == fixed)[:, None], [[0.25, 0.45, 0.85]], [[0.78, 0.78, 0.8]])
        lo, hi = np.percentile(vm, [2, 98])
        cm = plt.get_cmap("turbo")((np.clip(vm[tri].mean(1), lo, hi) - lo) / (hi - lo + 1e-30))[:, :3]
        fig = plt.figure(figsize=(8, 4), dpi=110)
        for k, (cols, title) in enumerate(((base * shade[:, None], "part mesh (fixed face blue)"),
                                           (cm * shade[:, None], "median von Mises, large load"))):
            ax = fig.add_subplot(1, 2, k + 1, projection="3d")
            ax.add_collection3d(Poly3DCollection(P, facecolors=np.clip(cols, 0, 1), edgecolors=(0, 0, 0, 0.15), linewidths=0.2))
            ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1)  # noqa: E702
            ax.set_box_aspect((1, 1, 1)); ax.view_init(24, -58); ax.set_axis_off()  # noqa: E702
            ax.set_title(title, fontsize=9)
        fig.suptitle(r["id"], fontsize=9)
        fig.savefig(png, bbox_inches="tight")
        plt.close(fig)
    print("figures in", fig_dir, flush=True)


def package(a) -> None:
    """Lay the results out like huggingface.co/datasets/cmudrc/SFEM (Step_Files/ + Pytorch_Geometric_Files/raw/{train,val}/),
    so SFEM's dataloader.SFEMInMemoryDataset reads it directly. Files are hard links into the run directory.
    The split is by Onshape document (2nd token of the ABC id): parts of one document never straddle train and val."""
    import random

    import h5py

    out, dest = Path(a.out), Path(a.dest)
    rows = [json.loads(line) for line in (out / "manifest.jsonl").open()]
    ok = []
    for r in (r for r in rows if r["status"] == "ok"):
        h5s = [out / "h5" / f"{r['id']}_{c}.h5" for c in LOAD_CLASSES]
        if all(p.exists() for p in h5s) and not any(np.isnan(h5py.File(p)["VonMises"][:]).any() for p in h5s):
            ok.append((r, h5s))
    docs = sorted({r["id"].split("_")[1] for r, _ in ok})
    random.Random(a.seed).shuffle(docs)
    val_docs = set(docs[: round(a.val * len(docs))])

    def link(src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            os.link(src, dst)

    split_rows = []
    for r, h5s in ok:
        split = "val" if r["id"].split("_")[1] in val_docs else "train"
        link(Path(r["step"]), dest / "Step_Files" / f"{r['id']}.step")
        for p in h5s:
            link(p, dest / "Pytorch_Geometric_Files/raw" / split / p.name)
        if (out / "figures" / f"{r['id']}.png").exists():
            link(out / "figures" / f"{r['id']}.png", dest / "figures" / f"{r['id']}.png")
        split_rows.append(dict(r, split=split))
    (dest / "manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in split_rows))
    n = {s: sum(r["split"] == s for r in split_rows) for s in ("train", "val")}
    status: dict[str, int] = {}
    for r in rows:
        status[r["status"]] = status.get(r["status"], 0) + 1
    (dest / "summary.json").write_text(json.dumps(dict(models_tried=len(rows), status=status, parts=n,
                                                       h5_files={s: 3 * k for s, k in n.items()},
                                                       documents=len(docs), val_documents=len(val_docs)), indent=1))
    print(json.dumps(dict(parts=n, documents=len(docs))), flush=True)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "mesh":  # child process
        print(json.dumps(mesh_step(sys.argv[2], sys.argv[3])))
        return
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--steps", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--workers", type=int, default=8)
    g = sub.add_parser("render")
    g.add_argument("--out", required=True)
    g.add_argument("--force", action="store_true")
    k = sub.add_parser("package")
    k.add_argument("--out", required=True)
    k.add_argument("--dest", required=True)
    k.add_argument("--val", type=float, default=0.15)  # SFEM's 85 / 15 split
    k.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    dict(run=run, render=render, package=package)[a.cmd](a)


if __name__ == "__main__":
    main()
