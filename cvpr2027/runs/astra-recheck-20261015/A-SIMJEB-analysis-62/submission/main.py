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
INPUT = Path(os.environ.get("CADFEM_INPUT_DIR", ".")).resolve()
OUT = Path(os.environ.get("CADFEM_OUTPUT_DIR", ".")).resolve()
OUT.mkdir(parents=True, exist_ok=True)
LOG = []
KEYS = [
    "vertical_max_displacement_mm",
    "horizontal_max_displacement_mm",
    "diagonal_max_displacement_mm",
    "torsion_max_displacement_mm",
]
AXIS = np.array([-0.030352, 0.999539, 0.0])
AXIS /= np.linalg.norm(AXIS)
CENTER = np.array([-20.9236, -74.6978, 44.7246])
LOAD_POINT = np.array([-21.0359, -75.0647, 44.8010])
BOLTS = np.array([[0., 0.], [52.0472, 1.5805],
                  [0., -148.1248], [38.0833, -146.9684]])
LOADS = [
    (np.array([0., 0., 35585.77]), np.zeros(3)),
    (np.array([-37809.90, 0., 0.]), np.zeros(3)),
    (np.array([-28276.20, 0., 31403.90]), np.zeros(3)),
    (np.zeros(3), np.array([0., 0., 564924.20])),
]


def log(message):
    LOG.append(str(message))
    (OUT / "solver.log").write_text("\n".join(LOG) + "\n")


def skew(r):
    x, y, z = r
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def get_mesh(size, directory):
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.NumThreads", 2)
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.model.add("published_bracket")
        gmsh.model.occ.importShapes(str(INPUT / "bracket.step"))
        gmsh.model.occ.synchronize()
        volumes = gmsh.model.getEntities(3)
        if not volumes:
            raise RuntimeError("STEP contains no solid volumes")
        log("Imported solid volumes: " + str(len(volumes)))
        gmsh.option.setNumber("Mesh.MeshSizeMax", size)
        gmsh.option.setNumber("Mesh.MeshSizeMin", size * 0.32)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 20)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)
        gmsh.option.setNumber("Mesh.Optimize", 1)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        # Retain quadratic displacement interpolation, but use straight-sided
        # geometry: projecting midside nodes onto tiny CAD features inverted
        # two curved tetrahedra in the previous mesh.
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
        gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
        gmsh.model.mesh.generate(3)
        _, volume_tags, _ = gmsh.model.mesh.getElements(3)
        quality = np.asarray(gmsh.model.mesh.getElementQualities(
            np.concatenate(volume_tags).tolist(), "minDetJac"))
        log(f"Minimum volume-element Jacobian determinant: {quality.min():.12g}")
        if not np.all(np.isfinite(quality)) or np.any(quality <= 0):
            raise RuntimeError("Mesh contains nonpositive volume-element Jacobians")
        gmsh.write(str(directory / "mesh.msh"))
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        tags = np.asarray(tags, dtype=np.int64)
        xyz = np.asarray(xyz).reshape(-1, 3)
        order = np.argsort(tags)
        tags, xyz = tags[order], xyz[order]
        etypes, etags, enodes = gmsh.model.mesh.getElements(3)
        cells = []
        for typ, nodes in zip(etypes, enodes):
            prop = gmsh.model.mesh.getElementProperties(int(typ))
            if int(typ) != 11:
                raise RuntimeError("Expected quadratic tetrahedra; got " + prop[0])
            cells.append(np.searchsorted(tags, np.asarray(nodes).reshape(-1, 10)))
        cells = np.concatenate(cells)

        rel = xyz - CENTER
        along = rel @ AXIS
        radial = np.linalg.norm(rel - along[:, None] * AXIS, axis=1)
        lug = ((np.abs(radial - 9.5504) < 0.025) &
               (np.abs(along) >= 11.10) & (np.abs(along) <= 17.48))
        fixed = np.zeros(len(tags), dtype=bool)
        for xy in BOLTS:
            fixed |= (np.abs(np.linalg.norm(xyz[:, :2] - xy, axis=1) -
                             5.1562) < 0.025)
        if fixed.sum() < 16 or lug.sum() < 16:
            raise RuntimeError("Unable to identify specified interface bore nodes")
        weights = np.zeros(len(tags))
        stypes, _, snodes = gmsh.model.mesh.getElements(2)
        for typ, nodes in zip(stypes, snodes):
            if typ != 9:
                continue
            tri = np.searchsorted(tags, np.asarray(nodes).reshape(-1, 6))
            # Straight-sided quadratic boundary edges have midside nodes
            # on chords, not exactly on the analytic cylinders. Identify
            # interface triangles by their CAD-projected corner nodes and
            # include every midside node in the boundary condition/load.
            corners = tri[:, :3]
            for xy in BOLTS:
                on_bolt = np.all(np.abs(
                    np.linalg.norm(xyz[corners, :2] - xy, axis=2)
                    - 5.1562) < 0.025, axis=1)
                fixed[tri[on_bolt].ravel()] = True
            tri = tri[np.all(lug[corners], axis=1)]
            if len(tri):
                p = xyz[tri[:, :3]]
                area = np.linalg.norm(np.cross(p[:, 1] - p[:, 0],
                                               p[:, 2] - p[:, 0]), axis=1) / 2
                for j in range(6):
                    np.add.at(weights, tri[:, j], area / 6.)
        if weights.sum() == 0:
            raise RuntimeError("No bore surface triangles identified")
        loaded = np.flatnonzero(weights > 0)
        weights /= weights.sum()
        log(f"Mesh h={size}: {len(tags)} nodes, {len(cells)} C3D10; "
            f"{fixed.sum()} fixed nodes, {len(loaded)} loaded nodes")
        return xyz, cells, fixed, loaded, weights
    finally:
        gmsh.finalize()


def equivalent_loads(xyz, loaded, weights):
    # RBE3-style weighted least-squares rigid motion interpolation.
    # Its transpose maps reference-point force/moment to flexible bore nodes.
    r = xyz[loaded] - LOAD_POINT
    B = np.zeros((len(loaded), 3, 6))
    B[:, :, :3] = np.eye(3)
    for i in range(len(r)):
        B[i, :, 3:] = -skew(r[i])
    w = weights[loaded]
    gram = np.einsum("n,nij,nik->jk", w, B, B)
    forces = []
    for force, moment in LOADS:
        q = np.linalg.solve(gram, np.r_[force, moment])
        f = w[:, None] * np.einsum("nij,j->ni", B, q)
        resultant = np.r_[f.sum(axis=0), np.cross(r, f).sum(axis=0)]
        log("Applied force and moment about reference point: " + str(resultant.tolist()))
        forces.append(f)
    return forces


def write_input(path, xyz, cells, fixed, loaded, forces):
    with path.open("w") as f:
        f.write("*HEADING\nImported GE bracket, quadratic tetrahedral linear elasticity\n")
        f.write("*NODE,NSET=NALL\n")
        for i, p in enumerate(xyz, 1):
            f.write(f"{i},{p[0]:.12g},{p[1]:.12g},{p[2]:.12g}\n")
        f.write("*ELEMENT,TYPE=C3D10,ELSET=SOLID\n")
        # Gmsh and CalculiX use opposite ordering for the last two tetrahedral edges.
        perm = [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]
        for i, c in enumerate(cells[:, perm] + 1, 1):
            f.write(str(i) + "," + ",".join(map(str, c)) + "\n")
        f.write("*MATERIAL,NAME=TI6AL4V\n*ELASTIC\n113800.,0.342\n")
        f.write("*DENSITY\n4.43e-9\n")
        f.write("*SOLID SECTION,ELSET=SOLID,MATERIAL=TI6AL4V\n")
        f.write("*NSET,NSET=FIXED\n")
        ids = np.flatnonzero(fixed) + 1
        for j in range(0, len(ids), 16):
            f.write(",".join(map(str, ids[j:j+16])) + "\n")
        f.write("*BOUNDARY\nFIXED,1,3\n")
        for loads in forces:
            f.write("*STEP\n*STATIC\n*CLOAD,OP=NEW\n")
            for nid, values in zip(loaded + 1, loads):
                for dof, v in enumerate(values, 1):
                    if abs(v) > 1.e-13:
                        f.write(f"{nid},{dof},{v:.12g}\n")
            f.write("*NODE PRINT,NSET=NALL,FREQUENCY=1\nU\n*END STEP\n")


def read_displacements(path, n):
    arrays = []
    current = None
    seen = 0
    with path.open(errors="replace") as f:
        for line in f:
            if "displacements" in line.lower() and "for set" in line.lower():
                if current is not None:
                    if seen != n:
                        raise RuntimeError(f"Incomplete displacement output: {seen}/{n}")
                    arrays.append(current)
                current = np.full((n, 3), np.nan)
                seen = 0
                continue
            if current is None:
                continue
            parts = line.split()
            if len(parts) == 4:
                try:
                    nid = int(parts[0])
                    vals = [float(v.replace("D", "E")) for v in parts[1:]]
                except ValueError:
                    continue
                if 1 <= nid <= n:
                    if np.isnan(current[nid-1, 0]):
                        seen += 1
                    current[nid-1] = vals
    if current is not None:
        if seen != n:
            raise RuntimeError(f"Incomplete displacement output: {seen}/{n}")
        arrays.append(current)
    if len(arrays) != 4:
        raise RuntimeError("Expected four displacement fields, found " + str(len(arrays)))
    return np.stack(arrays)


def main():
    if not (INPUT / "bracket.step").exists():
        raise FileNotFoundError(INPUT / "bracket.step")
    shutil.copy2(INPUT / "bracket.step", OUT / "part.step")
    specs = {}
    for p in sorted(INPUT.rglob("*")):
        if p.is_file() and p.suffix.lower() in (".txt", ".md", ".json", ".yaml", ".yml"):
            specs[str(p.relative_to(INPUT))] = p.read_text(errors="replace")
    (OUT / "environment.json").write_text(json.dumps({
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "gmsh": gmsh.__version__,
        "ccx": shutil.which("ccx"), "threads": 2,
        "input_specifications": specs,
        "units": "mm, N, MPa",
    }, indent=2))
    log("Geometry imported without redesign. Fully fixed bolt bore walls.")
    log("Load transfer: area-weighted rigid-motion interpolation transpose on both lug bores; "
        "no rigidification of lug surfaces. Four independent linear static load cases.")
    history = []
    best = None
    for level, size in enumerate([4.4, 3.1]):
        if level and time.time() - START > 280:
            log("Refinement not attempted: remaining runtime budget insufficient.")
            break
        d = OUT / f"level_{level}"
        d.mkdir(exist_ok=True)
        t = time.time()
        try:
            xyz, cells, fixed, loaded, weights = get_mesh(size, d)
            forces = equivalent_loads(xyz, loaded, weights)
            write_input(d / "solve.inp", xyz, cells, fixed, loaded, forces)
            remaining = 570 - (time.time() - START)
            if remaining < 15:
                raise RuntimeError("Runtime budget exhausted before solve")
            with (d / "ccx.log").open("w") as capture:
                proc = subprocess.run(["ccx", "-i", "solve"], cwd=d,
                                      stdout=capture, stderr=subprocess.STDOUT,
                                      timeout=remaining)
            text = (d / "ccx.log").read_text(errors="replace")
            log(text)
            if proc.returncode:
                raise RuntimeError(f"CalculiX exit status {proc.returncode}")
            u = read_displacements(d / "solve.dat", len(xyz))
            if not np.all(np.isfinite(u)):
                raise RuntimeError("Nonfinite displacement")
            maxima = np.linalg.norm(u, axis=2).max(axis=1)
            entry = {
                "level": level, "nominal_mesh_size_mm": size,
                "nodes": len(xyz), "elements": len(cells),
                "element_type": "C3D10", "max_displacements_mm": maxima.tolist(),
                "elapsed_seconds": time.time() - t,
            }
            if best is not None:
                entry["relative_change_from_previous"] = (
                    np.abs(maxima - best) / np.maximum(maxima, 1.e-30)).tolist()
            history.append(entry)
            best = maxima
            shutil.copy2(d / "mesh.msh", OUT / "mesh.msh")
            np.savez_compressed(
                OUT / "fields.npz", points=xyz, nodes=xyz,
                tetra10=cells, connectivity=cells,
                displacement=u, displacement_magnitude=np.linalg.norm(u, axis=2),
                case_names=np.array(KEYS), fixed_nodes=np.flatnonzero(fixed),
                loaded_nodes=loaded, load_weights=weights,
                nodal_forces=np.stack(forces),
            )
            (OUT / "results.json").write_text(json.dumps(
                {"outputs": dict(zip(KEYS, map(float, maxima)))}, indent=2))
        except Exception as exc:
            log(f"Level {level} failed: {type(exc).__name__}: {exc}")
            history.append({"level": level, "nominal_mesh_size_mm": size,
                            "status": "failed", "reason": str(exc)})
            if best is None:
                raise
            break
        finally:
            (OUT / "refinement.json").write_text(json.dumps({
                "method": "Independent quadratic tetrahedral meshes of the supplied STEP",
                "history": history,
                "convergence_claim": "Only measured mesh-to-mesh changes are reported; "
                                     "no extrapolation or published reference values used.",
                "elapsed_seconds": time.time() - START,
            }, indent=2))
    log("Completed. Results use the finest successfully solved mesh.")


if __name__ == "__main__":
    main()
