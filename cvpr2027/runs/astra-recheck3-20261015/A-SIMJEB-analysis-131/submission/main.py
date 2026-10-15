import os
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

import sys
import re
import json
import time
import shutil
import platform
import subprocess
from pathlib import Path

import numpy as np
import gmsh

START = time.time()
INP = Path(os.environ.get("CADFEM_INPUT_DIR", ".")).resolve()
OUT = Path(os.environ.get("CADFEM_OUTPUT_DIR", ".")).resolve()
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = INP / "bracket.step"
shutil.copy2(SOURCE, OUT / "part.step")

KEYS = [
    "vertical_max_displacement_mm",
    "horizontal_max_displacement_mm",
    "diagonal_max_displacement_mm",
    "torsion_max_displacement_mm",
]
BOLTS = np.array([[0., 0.], [52.0472, 1.5805],
                  [0., -148.1248], [38.0833, -146.9684]])
CENTER = np.array([-20.9236, -74.6978, 44.7246])
AXIS = np.array([-0.030352, 0.999539, 0.])
AXIS /= np.linalg.norm(AXIS)
REMOTE = np.array([-21.0359, -75.0647, 44.8010])
LOADS = [
    np.array([0., 0., 35585.77, 0., 0., 0.]),
    np.array([-37809.90, 0., 0., 0., 0., 0.]),
    np.array([-28276.20, 0., 31403.90, 0., 0., 0.]),
    np.array([0., 0., 0., 0., 0., 564924.20]),
]
LOG = []
history = []

def note(s):
    LOG.append(str(s))
    (OUT / "solver.log").write_text("\n".join(LOG) + "\n")

specs = {}
for p in INP.rglob("*"):
    if p.is_file() and p.suffix.lower() in (".md", ".txt", ".json", ".yaml", ".yml"):
        specs[str(p.relative_to(INP))] = p.read_text(errors="replace")
note("Input specification files read:\n" + json.dumps(specs, indent=2))
note("Full supplied STEP is used without geometry redesign. Units: mm, N, MPa.")
note("Quadratic tetrahedral linear elasticity, E=113800 MPa, nu=0.342. "
     "CalculiX incomplete-Cholesky-preconditioned iterative solver; "
     "explicit mesh sizing without curvature-driven interior refinement.")
note("Bolt bore walls fully fixed. Bore load interpolation is a weighted least-squares "
     "rigid-motion (RBE3-type) interpolation, with all six resultant components preserved.")

env = {
    "python": sys.version, "platform": platform.platform(),
    "numpy": np.__version__, "gmsh": gmsh.__version__,
    "ccx": shutil.which("ccx"), "threads": 2,
    "input_files": [str(p.relative_to(INP)) for p in INP.rglob("*") if p.is_file()],
}
(OUT / "environment.json").write_text(json.dumps(env, indent=2))
if not env["ccx"]:
    raise RuntimeError("CalculiX executable not found")

def bore_mask(x):
    d = x - CENTER
    t = d @ AXIS
    radial = np.linalg.norm(d - t[:, None] * AXIS, axis=1)
    # Identify the supplied CAD interface, allowing small differences between
    # nominal challenge dimensions and the published design. Surface-normal
    # tests below exclude the adjacent lug end faces.
    return ((np.abs(radial - 9.5504) < 0.75) &
            (((t >= 11.112 - .75) & (t <= 17.463 + .75)) |
             ((t >= -17.463 - .75) & (t <= -11.113 + .75))))

def generate_mesh(h, directory):
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.option.setNumber("General.NumThreads", 2)
        gmsh.model.add("published_bracket")
        gmsh.model.occ.importShapes(str(SOURCE))
        gmsh.model.occ.synchronize()
        vols = gmsh.model.getEntities(3)
        if not vols:
            raise RuntimeError("STEP has no solid volumes")
        gmsh.model.addPhysicalGroup(3, [t for _, t in vols], 1)
        # Small CAD fillets must not impose their curvature-based size on
        # the entire volume: that previously produced 741k displacement DOFs.
        # Retain the full CAD boundary but control volume resolution explicitly.
        gmsh.option.setNumber("Mesh.MeshSizeMin", h * .65)
        gmsh.option.setNumber("Mesh.MeshSizeMax", h)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MinimumCirclePoints", 16)
        gmsh.option.setNumber("Mesh.Algorithm", 6)
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)
        gmsh.option.setNumber("Mesh.Optimize", 1)
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
        gmsh.model.mesh.generate(3)
        # Curving the imported design's small/sliver faces inverted several
        # quadratic elements. Use straight-sided quadratic tetrahedra instead;
        # independent mesh refinement also refines the geometric approximation.
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
        gmsh.model.mesh.setOrder(2)
        gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
        gmsh.option.setNumber("Mesh.SaveAll", 1)
        gmsh.write(str(directory / "mesh.msh"))
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        tags = np.asarray(tags, dtype=np.int64)
        xyz = np.asarray(xyz).reshape(-1, 3)
        order = np.argsort(tags)
        tags, xyz = tags[order], xyz[order]
        types, etags, enodes = gmsh.model.mesh.getElements(3)
        pieces = []
        for typ, ns in zip(types, enodes):
            if typ != 11:
                raise RuntimeError("Unexpected volume element type " + str(typ))
            pieces.append(np.searchsorted(tags, np.asarray(ns).reshape(-1, 10)))
        tet = np.vstack(pieces)
        # Surface quadrature distributes each triangle's total area equally over
        # its six nodes, ensuring positive RBE interpolation weights.
        weights = np.zeros(len(tags))
        fixed_mask = np.zeros(len(tags), dtype=bool)
        bolt_counts = np.zeros(4, dtype=int)
        for _, surf in gmsh.model.getEntities(2):
            st, _, sn = gmsh.model.mesh.getElements(2, surf)
            for typ, ns in zip(st, sn):
                if typ not in (2, 9):
                    continue
                nper = 3 if typ == 2 else 6
                conn = np.searchsorted(tags, np.asarray(ns).reshape(-1, nper))
                xx = xyz[conn[:, :3]]
                cross = np.cross(xx[:, 1] - xx[:, 0], xx[:, 2] - xx[:, 0])
                twice_area = np.linalg.norm(cross, axis=1)
                normals = cross / np.maximum(twice_area[:, None], 1e-30)
                centroids = xx.mean(axis=1)
                d = centroids - CENTER
                radial = d - (d @ AXIS)[:, None] * AXIS
                radial /= np.maximum(np.linalg.norm(radial, axis=1)[:, None], 1e-30)
                sel = np.all(bore_mask(xx.reshape(-1, 3)).reshape(-1, 3), axis=1)
                sel &= np.abs(np.einsum('ij,ij->i', normals, radial)) > .93
                if np.any(sel):
                    np.add.at(weights, conn[sel].ravel(),
                              np.repeat(.5 * twice_area[sel] / nper, nper))
                # Select complete boundary triangles, including their midside
                # nodes, rather than testing chord-midpoint radii as cylinders.
                for j, bolt in enumerate(BOLTS):
                    rr = np.linalg.norm(xx[:, :, :2] - bolt, axis=2)
                    br = np.zeros_like(centroids)
                    br[:, :2] = centroids[:, :2] - bolt
                    br /= np.maximum(np.linalg.norm(br, axis=1)[:, None], 1e-30)
                    bs = np.all(np.abs(rr - 5.1562) < .25, axis=1)
                    bs &= np.abs(np.einsum('ij,ij->i', normals, br)) > .90
                    fixed_mask[conn[bs].ravel()] = True
                    bolt_counts[j] += int(np.sum(bs))
        if np.any(bolt_counts == 0):
            raise RuntimeError(f"Missing bolt bore boundary triangles: {bolt_counts.tolist()}")
        loaded = np.flatnonzero(weights > 0)
        if len(loaded):
            d = xyz[loaded] - CENTER
            axial = d @ AXIS
            radius = np.linalg.norm(d - axial[:, None] * AXIS, axis=1)
            note(f"Pin interface: {len(loaded)} nodes, area={weights.sum():.6g} mm^2, "
                 f"radius range={radius.min():.6g}..{radius.max():.6g} mm, "
                 f"axial range={axial.min():.6g}..{axial.max():.6g} mm")
            if not (np.any(axial > 0) and np.any(axial < 0)):
                raise RuntimeError("Pin surface identification found only one lug")
        note(f"Bolt boundary triangle counts: {bolt_counts.tolist()}")
        return xyz, tet, weights, np.flatnonzero(fixed_mask)
    finally:
        gmsh.finalize()

def build_forces(x, weights):
    # Membership comes from boundary connectivity. Straight-sided quadratic
    # midside nodes lie on chords, not exactly on the nominal CAD cylinder.
    loaded = np.flatnonzero(weights > 0)
    if len(loaded) < 12:
        raise RuntimeError("Insufficient pin-bore surface nodes")
    w = weights[loaded]
    r = x[loaded] - REMOTE
    B = np.zeros((len(loaded), 3, 6))
    B[:, :, :3] = np.eye(3)
    for i, (rx, ry, rz) in enumerate(r):
        B[i, :, 3:] = [[0., rz, -ry], [-rz, 0., rx], [ry, -rx, 0.]]
    normal = np.einsum("nki,n,nkj->ij", B, w, B)
    forces = []
    for load in LOADS:
        f = w[:, None] * np.einsum("nki,i->nk", B, np.linalg.solve(normal, load))
        resultant = np.r_[f.sum(axis=0), np.cross(r, f).sum(axis=0)]
        if not np.allclose(resultant, load, atol=1e-5, rtol=1e-9):
            raise RuntimeError("Load interpolation equilibrium error")
        forces.append(f)
    return loaded, forces

def write_deck(path, x, tet, fixed, loaded, forces):
    with path.open("w") as f:
        f.write("*HEADING\nSupplied GE bracket; quadratic tetrahedral analysis\n*NODE,NSET=ALLN\n")
        for i, p in enumerate(x, 1):
            f.write(f"{i},{p[0]:.12g},{p[1]:.12g},{p[2]:.12g}\n")
        f.write("*ELEMENT,TYPE=C3D10,ELSET=SOLID\n")
        # Gmsh's final two tetrahedral edge nodes are reversed relative to C3D10.
        cc = tet[:, [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]] + 1
        for i, c in enumerate(cc, 1):
            f.write(str(i) + "," + ",".join(map(str, c)) + "\n")
        f.write("*MATERIAL,NAME=TI64\n*ELASTIC\n113800.,0.342\n"
                "*DENSITY\n4.43e-9\n*SOLID SECTION,ELSET=SOLID,MATERIAL=TI64\n"
                "*NSET,NSET=FIXED\n")
        for k in range(0, len(fixed), 16):
            f.write(",".join(map(str, fixed[k:k+16] + 1)) + "\n")
        f.write("*BOUNDARY\nFIXED,1,3\n")
        for force in forces:
            # Incomplete-Cholesky-preconditioned iterative elasticity solve
            # avoids the memory cost of a large sparse direct factorization.
            f.write("*STEP\n*STATIC,SOLVER=ITERATIVE CHOLESKY\n*CLOAD,OP=NEW\n")
            for node, v in zip(loaded + 1, force):
                for j in range(3):
                    if abs(v[j]) > 1e-14:
                        f.write(f"{node},{j+1},{v[j]:.12g}\n")
            f.write("*NODE PRINT,NSET=ALLN,FREQUENCY=1\nU\n*END STEP\n")

def parse_dat(path, n):
    blocks = []
    current = None
    pattern = re.compile(r"^\s*(\d+)\s+([+\-\d.EeDd]+)\s+([+\-\d.EeDd]+)\s+([+\-\d.EeDd]+)\s*$")
    for line in path.read_text(errors="replace").splitlines():
        if "displacements" in line.lower() and "for set" in line.lower():
            current = np.full((n, 3), np.nan)
            blocks.append(current)
        elif current is not None:
            match = pattern.match(line)
            if match:
                node = int(match[1]) - 1
                if 0 <= node < n:
                    current[node] = [float(match[j].replace("D", "E")) for j in (2, 3, 4)]
    if len(blocks) != 4 or not np.all(np.isfinite(blocks)):
        raise RuntimeError(f"Incomplete displacement output: {len(blocks)} blocks")
    return np.array(blocks)

best = None
for level, h in enumerate([5.0, 3.8]):
    if level and time.time() - START > 310:
        note("Refinement not attempted: insufficient remaining runtime.")
        break
    directory = OUT / ("level_" + str(level))
    directory.mkdir(exist_ok=True)
    t0 = time.time()
    try:
        x, tet, weights, fixed = generate_mesh(h, directory)
        if len(fixed) < 20:
            raise RuntimeError("Bolt bore wall identification failed")
        loaded, forces = build_forces(x, weights)
        note(f"Level {level}: h={h}, nodes={len(x)}, tetrahedra={len(tet)}, "
             f"fixed nodes={len(fixed)}, loaded nodes={len(loaded)}")
        write_deck(directory / "job.inp", x, tet, fixed, loaded, forces)
        timeout = max(20., 565. - (time.time() - START))
        with (directory / "ccx.log").open("w") as log:
            result = subprocess.run([env["ccx"], "-i", "job"], cwd=directory,
                                    stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        note((directory / "ccx.log").read_text(errors="replace"))
        if result.returncode != 0:
            raise RuntimeError(f"CalculiX exited with code {result.returncode}")
        u = parse_dat(directory / "job.dat", len(x))
        maxima = np.linalg.norm(u, axis=2).max(axis=1)
        record = {"level": level, "maximum_mesh_size_mm": h,
                  "nodes": len(x), "elements": len(tet),
                  "seconds": time.time() - t0,
                  "outputs": dict(zip(KEYS, maxima.tolist()))}
        if best is not None:
            record["relative_change_from_previous"] = dict(zip(
                KEYS, (np.abs(maxima - best) / np.maximum(maxima, 1e-30)).tolist()))
        history.append(record)
        best = maxima
        shutil.copy2(directory / "mesh.msh", OUT / "mesh.msh")
        np.savez_compressed(
            OUT / "fields.npz", coordinates=x, nodes=x,
            tetrahedra_gmsh_order=tet, displacements=u,
            vertical_displacement=u[0], horizontal_displacement=u[1],
            diagonal_displacement=u[2], torsion_displacement=u[3],
            fixed_node_indices=fixed, loaded_node_indices=loaded,
            applied_nodal_forces=np.array(forces),
            case_names=np.array(KEYS), interpolation_weights=weights)
        (OUT / "results.json").write_text(json.dumps(
            {"outputs": dict(zip(KEYS, maxima.tolist()))}, indent=2))
    except Exception as exc:
        note(f"Level {level} failed: {type(exc).__name__}: {exc}")
        history.append({"level": level, "maximum_mesh_size_mm": h, "error": str(exc)})
        if best is None:
            raise
        break
    finally:
        (OUT / "refinement.json").write_text(json.dumps({
            "method": "Independent straight-sided quadratic tetrahedral meshes; comparison of displacement maxima, including geometric refinement.",
            "levels": history,
            "convergence_claim": "Observed changes only; no extrapolated or guaranteed converged value.",
            "load_method": "Area-weighted least-squares rigid-motion interpolation on both pin bores.",
            "boundary_method": "All translations fixed on four cylindrical bolt bore walls."
        }, indent=2))
note(f"Completed in {time.time() - START:.2f} seconds. "
     "Reported results use the finest successfully solved mesh.")
