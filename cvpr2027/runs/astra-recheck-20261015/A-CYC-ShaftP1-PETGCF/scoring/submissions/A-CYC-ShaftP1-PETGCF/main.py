import os
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

import sys
import json
import time
import shutil
import platform
import subprocess
import importlib.metadata
from pathlib import Path

import numpy as np
import gmsh

START = time.time()
INPUT = Path(os.environ.get("CADFEM_INPUT_DIR", ".")).resolve()
OUTPUT = Path(os.environ.get("CADFEM_OUTPUT_DIR", "output")).resolve()
OUTPUT.mkdir(parents=True, exist_ok=True)
LOG = []


def log(message):
    LOG.append(str(message))
    (OUTPUT / "solver.log").write_text("\n".join(LOG) + "\n")


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False))


def match_surface(record, surfaces):
    area = float(record["area_mm2"])
    center = np.asarray(record["centroid_mm"], dtype=float)
    candidates = []
    for tag in surfaces:
        a = gmsh.model.occ.getMass(2, tag)
        c = np.asarray(gmsh.model.occ.getCenterOfMass(2, tag))
        score = abs(a - area) / max(area, 1.0) + np.linalg.norm(c - center) / max(np.sqrt(area), 1.0)
        candidates.append((score, tag, a, c))
    candidates.sort(key=lambda v: v[0])
    score, tag, actual_area, actual_center = candidates[0]
    if abs(actual_area - area) > max(0.025, 0.002 * area) or np.linalg.norm(actual_center - center) > 0.025:
        raise RuntimeError("No reliable geometry match for face " + str(record["face_index"]))
    log("Face %s matched geometrically to surface %s: area %.9g, centroid %s; score %.6g"
        % (record["face_index"], tag, actual_area, actual_center.tolist(), score))
    return tag


def triangle_forces(x):
    # Degree-five symmetric triangle rule, normalized to the reference area 1/2.
    quadrature = [(1/3, 1/3, 0.225)]
    for a, b, w in [(0.059715871789770, 0.470142064105115, 0.132394152788506),
                    (0.797426985353087, 0.101286507323456, 0.125939180544827)]:
        quadrature.extend([(a, b, w), (b, a, w), (b, b, w)])
    weights = np.zeros(6)
    area = 0.0
    for r, s, w in quadrature:
        l = 1-r-s
        n = np.array([l*(2*l-1), r*(2*r-1), s*(2*s-1), 4*l*r, 4*r*s, 4*s*l])
        dr = np.array([1-4*l, 4*r-1, 0, 4*(l-r), 4*s, -4*s])
        ds = np.array([1-4*l, 0, 4*s-1, -4*r, 4*r, 4*(l-s)])
        da = 0.5*w*np.linalg.norm(np.cross(dr @ x, ds @ x))
        weights += n*da
        area += da
    return weights, area


def parse_displacements(path, n):
    lines = Path(path).read_text(errors="replace").splitlines()
    u = np.full((n, 3), np.nan)
    active = False
    for line in lines:
        if "displacements" in line.lower():
            active = True
            continue
        if not active:
            continue
        tokens = line.split()
        if len(tokens) == 4:
            try:
                node = int(tokens[0])
                vals = [float(t.replace("D", "E")) for t in tokens[1:]]
                if 1 <= node <= n:
                    u[node-1] = vals
            except ValueError:
                pass
    if not np.isfinite(u).all():
        raise RuntimeError("Incomplete displacement output: %d of %d nodes" %
                           (np.isfinite(u[:, 0]).sum(), n))
    return u


def solve_mesh(h, iteration, records):
    run = OUTPUT / ("run_%02d" % iteration)
    run.mkdir(exist_ok=True)
    gmsh.clear()
    gmsh.model.add("P1")
    gmsh.model.occ.importShapes(str(OUTPUT / "part.step"))
    gmsh.model.occ.synchronize()
    volumes = gmsh.model.getEntities(3)
    if len(volumes) != 1:
        raise RuntimeError("Expected exactly one solid")
    surfaces = [t for d, t in gmsh.model.getEntities(2)]
    fixed = match_surface(records[18], surfaces)
    loaded = match_surface(records[15], surfaces)
    gmsh.option.setNumber("General.NumThreads", 2)
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
    gmsh.option.setNumber("Mesh.MeshSizeMin", h / 5)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 28)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 1)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.ElementOrder", 1)
    # Keep midside nodes on their straight edges. Projecting them onto CAD
    # inverted several otherwise valid tetrahedra in the previous mesh.
    # Displacement interpolation remains quadratic; finer surface sampling
    # controls the piecewise-planar geometry approximation.
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.setOrder(2)
    _, volume_element_tags, _ = gmsh.model.mesh.getElements(3)
    determinants = np.asarray(gmsh.model.mesh.getElementQualities(
        np.concatenate(volume_element_tags), "minDetJac"))
    if not len(determinants) or not np.isfinite(determinants).all() or np.min(determinants) <= 0:
        raise RuntimeError("Nonpositive or invalid tetrahedral Jacobian before solver export")
    log("Straight-sided quadratic mesh: minimum Jacobian determinant %.12g mm^3; curvature sampling 28 elements per full circle"
        % np.min(determinants))
    gmsh.write(str(run / "mesh.msh"))
    tags, xyz, _ = gmsh.model.mesh.getNodes()
    ordering = np.argsort(tags)
    tags = np.asarray(tags)[ordering]
    xyz = np.asarray(xyz).reshape(-1, 3)[ordering]

    def index(a):
        a = np.asarray(a, dtype=np.int64)
        indices = np.searchsorted(tags, a)
        if not np.array_equal(tags[indices], a):
            raise RuntimeError("Node mapping error")
        return indices

    types, _, nodes = gmsh.model.mesh.getElements(3)
    blocks = []
    for typ, nd in zip(types, nodes):
        if typ != 11:
            raise RuntimeError("Expected quadratic tetrahedra, got Gmsh type %s" % typ)
        blocks.append(index(nd).reshape(-1, 10))
    tet = np.vstack(blocks)
    fixed_tags, _, _ = gmsh.model.mesh.getNodes(2, fixed, includeBoundary=True)
    fixed_indices = np.unique(index(fixed_tags))
    types, _, nodes = gmsh.model.mesh.getElements(2, loaded)
    force = np.zeros_like(xyz)
    loaded_area = 0.0
    loaded_triangles = []
    for typ, nd in zip(types, nodes):
        if typ != 9:
            raise RuntimeError("Expected quadratic surface triangles")
        triangles = index(nd).reshape(-1, 6)
        loaded_triangles.append(triangles)
        for tri in triangles:
            w, area = triangle_forces(xyz[tri])
            force[tri, 2] += w
            loaded_area += area
    force *= 100.204 / loaded_area
    log("Run %d: h=%g mm, %d nodes, %d tetrahedra, %d fixed nodes, loaded area %.10g mm^2, force %s N"
        % (iteration, h, len(xyz), len(tet), len(fixed_indices), loaded_area, force.sum(axis=0).tolist()))
    ccx_tet = tet[:, [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]] + 1
    with (run / "analysis.inp").open("w") as f:
        f.write("*HEADING\nP1 PETG-CF linear elastic static, units mm N MPa\n*NODE,NSET=NALL\n")
        for i, x in enumerate(xyz, 1):
            f.write("%d,%.12g,%.12g,%.12g\n" % (i, *x))
        f.write("*ELEMENT,TYPE=C3D10,ELSET=SOLID\n")
        for i, conn in enumerate(ccx_tet, 1):
            f.write(str(i) + "," + ",".join(map(str, conn)) + "\n")
        f.write("*NSET,NSET=FIXED\n")
        for start in range(0, len(fixed_indices), 16):
            f.write(",".join(map(str, fixed_indices[start:start+16]+1)) + "\n")
        f.write("*MATERIAL,NAME=PETGCF\n*ELASTIC\n3000.,0.36\n"
                "*SOLID SECTION,ELSET=SOLID,MATERIAL=PETGCF\n"
                "*BOUNDARY\nFIXED,1,3,0.\n*STEP\n*STATIC\n*CLOAD\n")
        for i in np.flatnonzero(force[:, 2]):
            f.write("%d,3,%.14g\n" % (i+1, force[i, 2]))
        f.write("*NODE PRINT,NSET=NALL\nU\n*END STEP\n")
    remaining = 555 - (time.time() - START)
    if remaining < 20:
        raise RuntimeError("Insufficient time remaining for solve")
    with (run / "ccx.log").open("w") as f:
        p = subprocess.run(["ccx", "-i", "analysis"], cwd=run, stdout=f,
                           stderr=subprocess.STDOUT, timeout=min(remaining, 270))
    log((run / "ccx.log").read_text(errors="replace"))
    if p.returncode != 0:
        raise RuntimeError("CalculiX failed with exit code %d" % p.returncode)
    u = parse_displacements(run / "analysis.dat", len(xyz))
    maximum = float(np.linalg.norm(u, axis=1).max())
    np.savez_compressed(run / "fields.npz",
                        points=xyz, nodes=xyz, node_ids=np.arange(1, len(xyz)+1),
                        gmsh_node_tags=tags, tetra10=tet, cells=tet,
                        displacement=u, displacement_mm=u,
                        displacement_magnitude_mm=np.linalg.norm(u, axis=1),
                        applied_nodal_force_N=force,
                        fixed_node_indices=fixed_indices,
                        loaded_tri6=np.vstack(loaded_triangles))
    return run, dict(mesh_size_mm=h, nodes=len(xyz), elements=len(tet),
                     element_type="quadratic tetrahedron C3D10",
                     max_displacement_mm=maximum, loaded_mesh_area_mm2=loaded_area,
                     elapsed_seconds=time.time()-START)


def main():
    shutil.copy2(INPUT / "part.step", OUTPUT / "part.step")
    specification = json.loads((INPUT / "faces.json").read_text())
    shutil.copy2(INPUT / "faces.json", OUTPUT / "faces.json")
    records = {int(r["face_index"]): r for r in specification["faces"]}
    log("Read complete faces.json: %d faces. Material E=3000 MPa, nu=0.36; fixed face 18; uniform global +Z traction on face 15, total 100.204 N." % len(records))
    readmes = list(INPUT.glob("*README*")) + list(INPUT.glob("*readme*"))
    for p in readmes:
        log("Input documentation %s:\n%s" % (p.name, p.read_text(errors="replace")))
    versions = {}
    for package in ["numpy", "scipy", "gmsh", "cadquery", "meshio", "scikit-fem"]:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    dump(OUTPUT / "environment.json", {
        "python": sys.version, "platform": platform.platform(), "packages": versions,
        "solver": "CalculiX", "ccx_path": shutil.which("ccx"), "threads": 2,
        "units": {"length": "mm", "force": "N", "stress": "MPa"},
        "element_connectivity": "fields.npz tetra10 uses zero-based Gmsh ordering",
        "field_location": "nodes"
    })
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    history = []
    last = None
    failure = None
    try:
        for k, h in enumerate([2.0, 1.4], 1):
            try:
                run, result = solve_mesh(h, k, records)
                if history:
                    result["relative_change_from_previous"] = abs(
                        result["max_displacement_mm"]-history[-1]["max_displacement_mm"]
                    ) / result["max_displacement_mm"]
                history.append(result)
                last = run
                for filename in ["mesh.msh", "fields.npz"]:
                    shutil.copy2(run / filename, OUTPUT / filename)
                dump(OUTPUT / "results.json", {
                    "outputs": {"max_displacement_mm": result["max_displacement_mm"]}
                })
                log("Completed run: " + json.dumps(result))
            except Exception as exc:
                failure = repr(exc)
                log("Run failed: " + failure)
                if last is None:
                    raise
                break
    finally:
        gmsh.finalize()
        dump(OUTPUT / "refinement.json", {
            "runs": history,
            "method": "Independent straight-sided quadratic tetrahedral meshes with 28 elements per full circle for curvature sizing; positive Jacobians checked before export. Surface-consistent nodal traction integrated with seven-point triangle quadrature and normalized to the specified total force.",
            "convergence_test": "Relative change in maximum nodal displacement below 2 percent",
            "converged": bool(len(history) > 1 and history[-1].get("relative_change_from_previous", 1) < 0.02),
            "selected_run": last.name if last else None,
            "failure": failure,
            "note": "Two meshes estimate discretization sensitivity; no extrapolated or reference result is used."
        })
    log("Finished in %.3f seconds." % (time.time()-START))


if __name__ == "__main__":
    main()
