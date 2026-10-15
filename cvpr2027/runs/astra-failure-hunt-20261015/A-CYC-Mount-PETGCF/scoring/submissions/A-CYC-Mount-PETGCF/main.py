import os
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"

import sys
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
OUTPUT = Path(os.environ.get("CADFEM_OUTPUT_DIR", ".")).resolve()
OUTPUT.mkdir(parents=True, exist_ok=True)
LOG = OUTPUT / "solver.log"


def log(message):
    with LOG.open("a") as f:
        f.write(str(message) + "\n")


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2))


def surface_force(coords, triangles, total_force):
    # Seven-point degree-five integration on the quadratic reference triangle.
    rules = [(1 / 3, 1 / 3, 0.225)]
    for a, b, w in [
        (0.059715871789770, 0.470142064105115, 0.132394152788506),
        (0.797426985353087, 0.101286507323456, 0.125939180544827),
    ]:
        rules += [(a, b, w), (b, a, w), (b, b, w)]
    lump = np.zeros(len(coords))
    area = 0.0
    xyz = coords[triangles]
    for r, s, w in rules:
        l = 1 - r - s
        N = np.array([l * (2*l-1), r*(2*r-1), s*(2*s-1),
                      4*l*r, 4*r*s, 4*s*l])
        dr = np.array([1-4*l, 4*r-1, 0, 4*(l-r), 4*s, -4*s])
        ds = np.array([1-4*l, 0, 4*s-1, -4*r, 4*r, 4*(l-s)])
        xr = np.einsum("tij,i->tj", xyz, dr)
        xs = np.einsum("tij,i->tj", xyz, ds)
        da = np.linalg.norm(np.cross(xr, xs), axis=1) * w * 0.5
        area += float(da.sum())
        np.add.at(lump, triangles.ravel(), (da[:, None] * N).ravel())
    return lump[:, None] * np.asarray(total_force)[None, :] / area, area


def parse_displacements(path, count):
    result = np.full((count, 3), np.nan)
    active = False
    for line in path.read_text(errors="replace").splitlines():
        if "displacements" in line.lower():
            active = True
            continue
        if not active:
            continue
        tokens = line.split()
        if len(tokens) == 4:
            try:
                n = int(tokens[0])
                values = [float(v.replace("D", "E")) for v in tokens[1:]]
                if 1 <= n <= count:
                    result[n-1] = values
            except ValueError:
                pass
    if not np.isfinite(result).all():
        raise RuntimeError("Incomplete displacement output from CalculiX")
    return result


def run_mesh(h, label, face_map):
    gmsh.model.mesh.clear()
    gmsh.option.setNumber("Mesh.MeshSizeMin", h * 0.35)
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.ElementOrder", 1)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.setOrder(2)
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    meshfile = OUTPUT / (label + ".msh")
    gmsh.write(str(meshfile))
    tags, rawcoords, _ = gmsh.model.mesh.getNodes()
    sort = np.argsort(tags)
    tags = tags[sort]
    coords = rawcoords.reshape(-1, 3)[sort]

    def indices(raw):
        raw = np.asarray(raw, dtype=np.int64)
        idx = np.searchsorted(tags, raw)
        if np.any(tags[idx] != raw):
            raise RuntimeError("Unknown mesh node")
        return idx

    types, _, connect = gmsh.model.mesh.getElements(3)
    blocks = []
    for typ, conn in zip(types, connect):
        if int(typ) != 11:
            raise RuntimeError("Expected ten-node tetrahedra")
        blocks.append(indices(conn).reshape(-1, 10))
    tet = np.vstack(blocks)
    fixed = []
    for face in (22, 24):
        nn, _, _ = gmsh.model.mesh.getNodes(2, face_map[face], True)
        fixed.extend(indices(nn).tolist())
    fixed = np.unique(fixed)
    types, _, connect = gmsh.model.mesh.getElements(2, face_map[12])
    triangles = []
    for typ, conn in zip(types, connect):
        if int(typ) != 9:
            raise RuntimeError("Expected quadratic traction triangles")
        triangles.append(indices(conn).reshape(-1, 6))
    triangles = np.vstack(triangles)
    force, area = surface_force(coords, triangles, [-50.064, 0, 0])
    job = OUTPUT / label
    ccx_tet = tet[:, [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]] + 1
    with job.with_suffix(".inp").open("w") as f:
        f.write("*HEADING\nPETG-CF motor mount; mm N MPa\n*NODE,NSET=ALLN\n")
        for n, xyz in enumerate(coords, 1):
            f.write(f"{n},{xyz[0]:.12g},{xyz[1]:.12g},{xyz[2]:.12g}\n")
        f.write("*ELEMENT,TYPE=C3D10,ELSET=BODY\n")
        for n, nodes in enumerate(ccx_tet, 1):
            f.write(str(n) + "," + ",".join(map(str, nodes)) + "\n")
        f.write("*MATERIAL,NAME=PETGCF\n*ELASTIC\n3000.,0.36\n")
        f.write("*SOLID SECTION,ELSET=BODY,MATERIAL=PETGCF\n")
        f.write("*NSET,NSET=FIXED\n")
        for i in range(0, len(fixed), 16):
            f.write(",".join(map(str, fixed[i:i+16] + 1)) + "\n")
        f.write("*BOUNDARY\nFIXED,1,3,0.\n*STEP\n*STATIC\n*CLOAD\n")
        for node in np.flatnonzero(np.abs(force[:, 0]) > 1e-16):
            f.write(f"{node+1},1,{force[node,0]:.14g}\n")
        f.write("*NODE PRINT,NSET=ALLN\nU\n*END STEP\n")
    log(f"{label}: h={h}, nodes={len(coords)}, C3D10={len(tet)}, "
        f"fixed_nodes={len(fixed)}, loaded_area={area}, resultant={force.sum(axis=0)}")
    timeout = max(20, int(565 - (time.time() - START)))
    start = time.time()
    with (OUTPUT / (label + "_ccx.log")).open("w") as f:
        proc = subprocess.run(["ccx", "-i", label], cwd=OUTPUT,
                              stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
    log((OUTPUT / (label + "_ccx.log")).read_text(errors="replace"))
    if proc.returncode != 0:
        raise RuntimeError(f"CalculiX failed: {proc.returncode}")
    u = parse_displacements(job.with_suffix(".dat"), len(coords))
    magnitude = np.linalg.norm(u, axis=1)
    value = float(magnitude.max())
    np.savez_compressed(
        OUTPUT / (label + "_fields.npz"),
        coordinates=coords, points=coords, node_ids=np.arange(1, len(coords)+1),
        tetra10=tet, cells=tet, displacement=u, displacement_mm=u,
        displacement_magnitude_mm=magnitude, fixed_nodes=fixed,
        loaded_triangles=triangles, nodal_force_N=force)
    return {
        "label": label, "maximum_element_size_mm": h,
        "nodes": len(coords), "elements": len(tet),
        "max_displacement_mm": value,
        "loaded_area_mm2": area, "solve_seconds": time.time()-start,
        "element_type": "C3D10"
    }


def main():
    LOG.write_text("Linear isotropic static elasticity, N-mm-MPa; no gravity or contact.\n")
    if INPUT / "part.step" != OUTPUT / "part.step":
        shutil.copy2(INPUT / "part.step", OUTPUT / "part.step")
    spec = json.loads((INPUT / "faces.json").read_text())
    dump(OUTPUT / "faces.json", spec)
    for directory in (INPUT, Path.cwd()):
        for name in ("README", "README.md", "README.txt"):
            path = directory / name
            if path.is_file():
                log(f"Artifact instructions {path}:\n{path.read_text()}")
    faces = {int(f["face_index"]): f for f in spec["faces"]}
    dump(OUTPUT / "environment.json", {
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "gmsh": gmsh.__version__,
        "ccx_executable": shutil.which("ccx"), "threads": 2,
        "material": {"E_MPa": 3000, "poisson_ratio": 0.36},
        "units": {"length": "mm", "force": "N", "stress": "MPa"},
    })
    gmsh.initialize()
    gmsh.option.setNumber("General.NumThreads", 2)
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.logger.start()
    gmsh.model.add("mount")
    gmsh.model.occ.importShapes(str(INPUT / "part.step"))
    gmsh.model.occ.synchronize()
    surfaces = []
    for _, tag in gmsh.model.getEntities(2):
        surfaces.append((tag, gmsh.model.occ.getMass(2, tag),
                         np.array(gmsh.model.occ.getCenterOfMass(2, tag))))
    face_map = {}
    for index in (12, 22, 24):
        face = faces[index]
        area = float(face["area_mm2"])
        centroid = np.array(face["centroid_mm"])
        ranked = sorted(surfaces, key=lambda s:
                        np.linalg.norm(s[2]-centroid) + abs(s[1]-area)/max(1, area))
        tag, measured_area, measured_center = ranked[0]
        if np.linalg.norm(measured_center-centroid) > 0.05 or abs(measured_area-area) > max(0.1, area*0.001):
            raise RuntimeError(f"No geometric match for face {index}")
        face_map[index] = tag
        log(f"Geometrically matched face {index}: surface={tag}, "
            f"area={measured_area}, centroid={measured_center.tolist()}")
    history = []
    history.append(run_mesh(3.2, "coarse", face_map))
    try:
        history.append(run_mesh(2.0, "fine", face_map))
    except Exception as exc:
        log(f"Fine solve unsuccessful; retaining completed coarse solution: {exc}")
    selected = history[-1]
    label = selected["label"]
    shutil.copy2(OUTPUT / (label + ".msh"), OUTPUT / "mesh.msh")
    shutil.copy2(OUTPUT / (label + "_fields.npz"), OUTPUT / "fields.npz")
    change = None
    if len(history) > 1:
        change = abs(history[-1]["max_displacement_mm"] -
                     history[-2]["max_displacement_mm"]) / history[-1]["max_displacement_mm"]
    dump(OUTPUT / "refinement.json", {
        "runs": history, "selected": label,
        "relative_change_max_displacement": change,
        "convergence_claim": "Two-mesh comparison only; no extrapolation or guaranteed error bound."
        if len(history) > 1 else "Only one successful mesh; convergence not established."
    })
    dump(OUTPUT / "results.json", {
        "outputs": {"max_displacement_mm": selected["max_displacement_mm"]}
    })
    log("\n".join(gmsh.logger.get()))
    gmsh.finalize()
    log(f"Total elapsed seconds: {time.time()-START:.3f}")


if __name__ == "__main__":
    main()
