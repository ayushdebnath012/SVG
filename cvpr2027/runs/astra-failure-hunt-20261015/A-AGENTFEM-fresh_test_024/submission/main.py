import os
import sys
import json
import time
import shutil
import platform
import subprocess
import traceback
from pathlib import Path

import numpy as np
import gmsh

START = time.time()
OUT = Path(os.environ.get("CADFEM_OUTPUT_DIR", ".")).resolve()
INP = Path(os.environ.get("CADFEM_INPUT_DIR", ".")).resolve()
OUT.mkdir(parents=True, exist_ok=True)
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
logs = []


def save_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False))


def triangle_weights(x):
    # Degree-five triangle quadrature; weights sum to one.
    a, b = 0.470142064105115, 0.059715871789770
    c, d = 0.101286507323456, 0.797426985353087
    quadrature = [
        ((1/3, 1/3, 1/3), 0.225),
        ((a, a, b), 0.132394152788506),
        ((a, b, a), 0.132394152788506),
        ((b, a, a), 0.132394152788506),
        ((c, c, d), 0.125939180544827),
        ((c, d, c), 0.125939180544827),
        ((d, c, c), 0.125939180544827),
    ]
    result = np.zeros((len(x), 6))
    for (l0, l1, l2), w in quadrature:
        n = np.array([
            l0*(2*l0-1), l1*(2*l1-1), l2*(2*l2-1),
            4*l0*l1, 4*l1*l2, 4*l2*l0
        ])
        dr = np.array([1-4*l0, 4*l1-1, 0,
                       4*(l0-l1), 4*l2, -4*l2])
        ds = np.array([1-4*l0, 0, 4*l2-1,
                       -4*l1, 4*l1, 4*(l0-l2)])
        jac = np.linalg.norm(np.cross(
            np.einsum("tij,i->tj", x, dr),
            np.einsum("tij,i->tj", x, ds)), axis=1)
        result += (0.5*w*jac)[:, None]*n[None, :]
    return result


def solve_level(h, level):
    folder = OUT / ("level_%d" % level)
    folder.mkdir(exist_ok=True)
    gmsh.clear()
    gmsh.model.add("bracket")
    gmsh.model.occ.importShapes(str(OUT / "part.step"))
    gmsh.model.occ.synchronize()
    solids = gmsh.model.getEntities(3)
    if len(solids) != 1:
        raise RuntimeError("Expected exactly one solid, found %d" % len(solids))
    top, bottom = [], []
    face_info = []
    for _, tag in gmsh.model.getEntities(2):
        bb = gmsh.model.getBoundingBox(2, tag)
        face_info.append({"tag": tag, "bbox_mm": list(bb)})
        if abs(bb[2]-189) < 1e-4 and abs(bb[5]-189) < 1e-4:
            top.append(tag)
        if abs(bb[2]) < 1e-4 and abs(bb[5]) < 1e-4:
            bottom.append(tag)
    if not top or not bottom:
        raise RuntimeError("Could not identify planar seat and underside faces")
    for faces, name in [(top, "seat"), (bottom, "fixed")]:
        pg = gmsh.model.addPhysicalGroup(2, faces)
        gmsh.model.setPhysicalName(2, pg, name)
    pg = gmsh.model.addPhysicalGroup(3, [v[1] for v in solids])
    gmsh.model.setPhysicalName(3, pg, "solid")
    gmsh.option.setNumber("Mesh.MeshSizeMin", h)
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.ElementOrder", 1)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.setOrder(2)
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    gmsh.write(str(folder / "mesh.msh"))
    tags, coords, _ = gmsh.model.mesh.getNodes()
    tags = np.asarray(tags, dtype=np.int64)
    coords = np.asarray(coords).reshape(-1, 3)
    order = np.argsort(tags)
    tags, coords = tags[order], coords[order]

    def indices(raw):
        raw = np.asarray(raw, dtype=np.int64)
        out = np.searchsorted(tags, raw)
        if not np.array_equal(tags[out], raw):
            raise RuntimeError("Unknown mesh node")
        return out

    types, _, conn = gmsh.model.mesh.getElements(3)
    tet_list = []
    for typ, nodes in zip(types, conn):
        if typ != 11:
            raise RuntimeError("Expected quadratic tetrahedra; got type %s" % typ)
        tet_list.append(indices(nodes).reshape(-1, 10))
    tets = np.concatenate(tet_list)

    def surface(faces):
        triangles = []
        for face in faces:
            ty, _, co = gmsh.model.mesh.getElements(2, face)
            for tt, nn in zip(ty, co):
                if tt != 9:
                    raise RuntimeError("Expected six-node surface triangles")
                triangles.append(indices(nn).reshape(-1, 6))
        return np.concatenate(triangles)

    seat = surface(top)
    fixed = np.unique(surface(bottom))
    local_weights = triangle_weights(coords[seat])
    weights = np.zeros(len(tags))
    np.add.at(weights, seat.ravel(), local_weights.ravel())
    area = float(weights.sum())
    ccx_tets = tets[:, [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]] + 1
    with (folder / "bracket.inp").open("w") as f:
        f.write("*HEADING\nBracket, mm N MPa, quadratic tetrahedra\n*NODE\n")
        for i, xyz in enumerate(coords, 1):
            f.write("%d,%.12g,%.12g,%.12g\n" % (i, *xyz))
        f.write("*ELEMENT,TYPE=C3D10,ELSET=SOLID\n")
        for i, row in enumerate(ccx_tets, 1):
            f.write(str(i)+","+",".join(map(str, row))+"\n")
        f.write("*NSET,NSET=NALL,GENERATE\n1,%d,1\n" % len(tags))
        f.write("*NSET,NSET=FIXED\n")
        for j in range(0, len(fixed), 16):
            f.write(",".join(str(int(k)+1) for k in fixed[j:j+16])+"\n")
        f.write("*MATERIAL,NAME=ALUMINIUM\n*ELASTIC\n70000.,0.33\n")
        f.write("*SOLID SECTION,ELSET=SOLID,MATERIAL=ALUMINIUM\n")
        f.write("*BOUNDARY\nFIXED,1,3\n*STEP\n*STATIC\n*CLOAD\n")
        for node in np.flatnonzero(np.abs(weights) > 1e-12):
            f.write("%d,3,%.14g\n" % (node+1, -1.98728*weights[node]))
        f.write("*NODE PRINT,NSET=NALL\nU\n*END STEP\n")
    remaining = 565 - (time.time()-START)
    if remaining < 15:
        raise RuntimeError("Insufficient remaining runtime for solve")
    env = dict(os.environ)
    env["CCX_NPROC_RESULTS"] = "2"
    env["CCX_NPROC_EQUATION_SOLVER"] = "2"
    run = subprocess.run(
        ["ccx", "-i", "bracket"], cwd=folder, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=max(10, remaining))
    logs.append("LEVEL %d, h=%g mm\n%s" % (level, h, run.stdout))
    (OUT / "solver.log").write_text("\n\n".join(logs))
    if run.returncode != 0:
        raise RuntimeError("CalculiX returned %d" % run.returncode)
    u = np.full((len(tags), 3), np.nan)
    for line in (folder / "bracket.dat").read_text().splitlines():
        fields = line.split()
        if len(fields) != 4:
            continue
        try:
            node = int(fields[0])
            value = [float(s.replace("D", "E")) for s in fields[1:]]
        except ValueError:
            continue
        if 1 <= node <= len(tags):
            u[node-1] = value
    if not np.all(np.isfinite(u)):
        raise RuntimeError("Incomplete displacement output")
    answer = {
        "seat_mean_displacement_mm": float(-np.dot(weights, u[:, 2])/area),
        "max_displacement_mm": float(np.linalg.norm(u, axis=1).max())
    }
    np.savez_compressed(
        folder / "fields.npz",
        coordinates=coords, points=coords, node_ids=tags,
        displacement=u, displacements=u, tetra10=tets,
        cells=tets, seat_tri6=seat, fixed_node_indices=fixed,
        seat_integration_weights=weights,
        displacement_magnitude=np.linalg.norm(u, axis=1),
        coordinate_units=np.array("mm"), displacement_units=np.array("mm"))
    record = {
        "level": level, "nominal_size_mm": h, "nodes": len(tags),
        "quadratic_tetrahedra": len(tets), "seat_area_mm2": area,
        "applied_force_z_N": -1.98728*area,
        "fixed_nodes": len(fixed), "seat_faces": top,
        "fixed_faces": bottom, "outputs": answer,
        "elapsed_seconds": time.time()-START,
    }
    save_json(folder / "summary.json", record)
    return folder, record


def main():
    shutil.copyfile(INP / "geometry.step", OUT / "part.step")
    specifications = {}
    for p in sorted(INP.rglob("*")):
        if p.is_file() and (p.suffix.lower() in (".txt", ".md", ".json", ".yaml", ".yml")
                            or p.name.lower().startswith("readme")):
            specifications[str(p.relative_to(INP))] = p.read_text(errors="replace")
    save_json(OUT / "input_specifications.json", specifications)
    environment = {
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "gmsh": gmsh.__version__,
        "ccx_path": shutil.which("ccx"), "threads": 2,
        "units": {"length": "mm", "force": "N", "stress": "MPa"},
        "material": {"E_MPa": 70000, "poisson_ratio": 0.33},
        "gravity": False,
        "method": "CalculiX C3D10 linear static elasticity; consistent integrated quadratic seat loads",
    }
    save_json(OUT / "environment.json", environment)
    gmsh.initialize()
    gmsh.option.setNumber("General.NumThreads", 2)
    records = []
    final_folder = None
    try:
        for level, h in enumerate([9.0, 6.5]):
            try:
                folder, record = solve_level(h, level)
                records.append(record)
                final_folder = folder
            except Exception:
                error = traceback.format_exc()
                logs.append(error)
                if final_folder is None:
                    raise
                records.append({"level": level, "nominal_size_mm": h,
                                "status": "failed", "error": error})
                break
    finally:
        gmsh.finalize()
        (OUT / "solver.log").write_text("\n\n".join(logs))
    successful = [r for r in records if "outputs" in r]
    last = successful[-1]
    refinement = {
        "levels": records,
        "selected_level": last["level"],
        "mean_definition": "Surface integral of -u_z divided by seat area",
        "maximum_definition": "Maximum displacement magnitude over all quadratic mesh nodes",
        "convergence_note": "Two mesh levels are compared when feasible; no extrapolated or reference values used."
    }
    if len(successful) >= 2:
        p, q = successful[-2]["outputs"], successful[-1]["outputs"]
        refinement["relative_changes"] = {
            k: abs(q[k]-p[k])/max(abs(q[k]), 1e-30) for k in q}
    for name in ("mesh.msh", "fields.npz"):
        shutil.copyfile(final_folder / name, OUT / name)
    save_json(OUT / "refinement.json", refinement)
    save_json(OUT / "results.json", {"outputs": last["outputs"]})
    environment["elapsed_seconds"] = time.time()-START
    save_json(OUT / "environment.json", environment)


if __name__ == "__main__":
    main()
