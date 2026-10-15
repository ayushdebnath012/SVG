import os
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

import sys
import json
import time
import shutil
import subprocess
import platform
import re
from pathlib import Path
import numpy as np
import gmsh

START = time.time()
INPUT = Path(os.environ.get("CADFEM_INPUT_DIR", ".")).resolve()
OUT = Path(os.environ.get("CADFEM_OUTPUT_DIR", ".")).resolve()
OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT / "solver.log"


def log(s):
    with LOG.open("a") as f:
        f.write(str(s) + "\n")


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2))


def run_ccx(directory, job, timeout):
    exe = shutil.which("ccx")
    if not exe:
        raise RuntimeError("CalculiX executable is unavailable")
    with (directory / (job + ".console")).open("w") as f:
        try:
            p = subprocess.run([exe, "-i", job], cwd=directory,
                               stdout=f, stderr=subprocess.STDOUT,
                               timeout=max(1, timeout), env=os.environ.copy())
        except subprocess.TimeoutExpired:
            log((directory / (job + ".console")).read_text(errors="replace"))
            raise RuntimeError("CalculiX timed out: " + job)
    text = (directory / (job + ".console")).read_text(errors="replace")
    log("=== " + str(directory) + "/" + job + " ===\n" + text)
    if p.returncode:
        raise RuntimeError("CalculiX returned " + str(p.returncode))
    return text


def factors_from_dat(path):
    text = path.read_text(errors="replace")
    log(text)
    values = []
    active = False
    for line in text.splitlines():
        compressed = re.sub(r"\s+", "", line).upper()
        if "BUCKLINGFACTOR" in compressed:
            active = True
        if active:
            m = re.match(r"^\s*(\d+)\s+([+-]?\d*\.?\d+(?:[EeDd][+-]?\d+)?)\s*$", line)
            if m:
                values.append(float(m.group(2).replace("D", "E").replace("d", "e")))
    positives = [x for x in values if np.isfinite(x) and x > 0]
    if not positives:
        raise RuntimeError("No positive buckling factor in " + str(path))
    return values, min(positives)


def read_frd(path, node_ids):
    blocks = {}
    index = {int(n): i for i, n in enumerate(node_ids)}
    name = None
    data = {}
    if not path.exists():
        return blocks
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith(" -4"):
            parts = line.split()
            name = parts[1] if len(parts) > 1 else None
            data = {}
        elif name and line.startswith(" -1"):
            try:
                n = int(line[3:13])
                vals = [float(line[i:i + 12].replace("D", "E"))
                        for i in range(13, len(line), 12) if line[i:i + 12].strip()]
                if n in index:
                    data[index[n]] = vals
            except ValueError:
                pass
        elif name and line.startswith(" -3"):
            if data:
                width = max(len(v) for v in data.values())
                arr = np.full((len(node_ids), width), np.nan)
                for i, v in data.items():
                    arr[i, :len(v)] = v
                blocks.setdefault(name, []).append(arr)
            name = None
            data = {}
    return blocks


def mesh_model(h, destination):
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.NumThreads", 2)
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.model.add("steel_column")
        gmsh.model.occ.importShapes(str(INPUT / "analysis.step"))
        gmsh.model.occ.synchronize()
        volumes = gmsh.model.getEntities(3)
        if len(volumes) > 1:
            gmsh.model.occ.fragment(volumes[:1], volumes[1:])
            gmsh.model.occ.synchronize()
        bottom, top = [], []
        for _, tag in gmsh.model.getEntities(2):
            bb = gmsh.model.getBoundingBox(2, tag)
            c = gmsh.model.occ.getCenterOfMass(2, tag)
            if abs(c[2]) < 1.e-4 and abs(bb[5] - bb[2]) < 1.e-3:
                bottom.append(tag)
            if abs(c[2] - 1000) < 1.e-4 and abs(bb[5] - bb[2]) < 1.e-3:
                top.append(tag)
        for tags in (bottom, top):
            area = sum(gmsh.model.occ.getMass(2, t) for t in tags)
            if abs(area - 1207.5) > .05:
                raise RuntimeError("End-face scope does not match specified face area")
        gmsh.model.addPhysicalGroup(3, [t for _, t in gmsh.model.getEntities(3)], 1)
        gmsh.model.addPhysicalGroup(2, bottom, 11)
        gmsh.model.addPhysicalGroup(2, top, 10)
        gmsh.option.setNumber("Mesh.MeshSizeMin", h * .5)
        gmsh.option.setNumber("Mesh.MeshSizeMax", h)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.setOrder(2)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        gmsh.write(str(destination))
        ids, coords, _ = gmsh.model.mesh.getNodes()
        sort = np.argsort(ids)
        ids = np.asarray(ids[sort], dtype=np.int64)
        coords = np.asarray(coords).reshape(-1, 3)[sort]
        xyz = {int(i): x for i, x in zip(ids, coords)}
        etypes, _, enodes = gmsh.model.mesh.getElements(3)
        elems = []
        for typ, nd in zip(etypes, enodes):
            if typ != 11:
                raise RuntimeError("Expected exclusively quadratic tetrahedra")
            a = np.asarray(nd, dtype=np.int64).reshape(-1, 10).copy()
            a[:, [8, 9]] = a[:, [9, 8]]
            elems.append(a)
        elems = np.vstack(elems)
        fixed = set()
        for tag in bottom:
            ns, _, _ = gmsh.model.mesh.getNodes(2, tag, includeBoundary=True)
            fixed.update(map(int, ns))
        loads = {}
        traction = np.array([1.656315, 0., -41.407867])
        total_area = 0.
        for tag in top:
            types, _, nodes = gmsh.model.mesh.getElements(2, tag)
            for typ, nd in zip(types, nodes):
                if typ != 9:
                    raise RuntimeError("Expected quadratic loaded-face triangles")
                for tri in np.asarray(nd).reshape(-1, 6):
                    a, b, c = [xyz[int(i)] for i in tri[:3]]
                    area = np.linalg.norm(np.cross(b-a, c-a)) / 2
                    total_area += area
                    for n in tri[3:]:
                        loads[int(n)] = loads.get(int(n), np.zeros(3)) + traction * area / 3
        log(f"h={h}: nodes={len(ids)}, C3D10={len(elems)}, loaded area={total_area}")
        log("Integrated end load [N]: " + str(sum(loads.values())))
        return ids, coords, elems, sorted(fixed), loads
    finally:
        gmsh.finalize()


def input_deck(data, buckle):
    ids, coords, elems, fixed, loads = data
    lines = ["*HEADING", "Imported STEP continuum; consistent end traction; gravity",
             "*NODE"]
    lines.extend(f"{i},{x[0]:.12g},{x[1]:.12g},{x[2]:.12g}" for i, x in zip(ids, coords))
    lines.append("*ELEMENT,TYPE=C3D10,ELSET=EALL")
    lines.extend(str(i) + "," + ",".join(map(str, e)) for i, e in enumerate(elems, 1))
    lines += ["*MATERIAL,NAME=STEEL", "*ELASTIC", "210000,0.3",
              "*DENSITY", "7.9e-9", "*SOLID SECTION,ELSET=EALL,MATERIAL=STEEL",
              "*BOUNDARY"]
    lines.extend(f"{i},1,3" for i in fixed)
    lines += ["*STEP"]
    if buckle:
        lines += ["*BUCKLE", "8,0.001"]
    else:
        lines += ["*STATIC", "1,1"]
    lines += ["*CLOAD"]
    for n, force in sorted(loads.items()):
        for j in (0, 2):
            lines.append(f"{n},{j+1},{force[j]:.14g}")
    lines += ["*DLOAD", "EALL,GRAV,10000,0,0,-1",
              "*NODE FILE", "U", "*EL FILE", "S", "*END STEP"]
    return "\n".join(lines) + "\n"


def main():
    LOG.write_text("")
    shutil.copy2(INPUT / "analysis.step", OUT / "part.step")
    descriptors = json.loads((INPUT / "faces.json").read_text())
    write_json(OUT / "environment.json", {
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "gmsh": gmsh.__version__,
        "ccx": shutil.which("ccx"), "threads": 2,
        "units": "mm, N, MPa, tonne, second",
        "geometry_source": str(INPUT / "analysis.step"),
        "face_descriptors_read": bool(descriptors)
    })
    history = []
    successful = []
    for level, h in enumerate((12., 8.)):
        directory = OUT / ("level_" + str(level))
        directory.mkdir(exist_ok=True)
        try:
            data = mesh_model(h, directory / "mesh.msh")
            (directory / "buckling.inp").write_text(input_deck(data, True))
            remaining = 555 - (time.time() - START)
            if remaining < 45:
                raise RuntimeError("Insufficient time for another eigensolve")
            run_ccx(directory, "buckling", min(210 if level == 0 else 260, remaining))
            eigs, first = factors_from_dat(directory / "buckling.dat")
            record = {"mesh_size_mm": h, "nodes": len(data[0]),
                      "elements": len(data[2]), "lambda1": first,
                      "computed_factors": eigs, "status": "completed"}
            if successful:
                record["relative_change_lambda1"] = abs(first - successful[-1][2]) / abs(first)
            history.append(record)
            successful.append((directory, data, first))
        except Exception as exc:
            log(repr(exc))
            history.append({"mesh_size_mm": h, "status": "failed", "reason": str(exc)})
    write_json(OUT / "refinement.json", {
        "method": "Two quadratic tetrahedral mesh sizes; no extrapolation.",
        "runs": history,
        "convergence_claimed": False,
        "note": "Reported value is the finest successfully solved mesh; changes are recorded, not assumed negligible."
    })
    if not successful:
        raise RuntimeError("No successful buckling analysis")
    directory, data, first = successful[-1]
    shutil.copy2(directory / "mesh.msh", OUT / "mesh.msh")
    remaining = 580 - (time.time() - START)
    (directory / "prebuckling.inp").write_text(input_deck(data, False))
    if remaining < 10:
        raise RuntimeError("Insufficient time to save the separate reference stress solution")
    run_ccx(directory, "prebuckling", remaining)
    static = read_frd(directory / "prebuckling.frd", data[0])
    modes = read_frd(directory / "buckling.frd", data[0])
    if "DISP" not in static or "STRESS" not in static:
        raise RuntimeError("Reference displacement/stress field was not found in FRD")
    ids, coords, elems, fixed, loads = data
    connectivity = np.searchsorted(ids, elems)
    fields = {
        "node_ids": ids, "points_mm": coords,
        "connectivity_C3D10": connectivity,
        "displacement_mm": static["DISP"][-1],
        "stress_MPa": static["STRESS"][-1],
        "stress_component_order": np.array(["xx", "yy", "zz", "xy", "yz", "zx"]),
        "fixed_node_ids": np.asarray(fixed),
        "traction_node_ids": np.asarray(sorted(loads)),
        "traction_nodal_forces_N": np.asarray([loads[k] for k in sorted(loads)]),
        "body_force_N_per_mm3": np.array([0., 0., -7.9e-5]),
        "lambda1": np.array(first)
    }
    if "DISP" in modes:
        fields["buckling_displacement_records"] = np.stack(modes["DISP"])
    np.savez_compressed(OUT / "fields.npz", **fields)
    write_json(OUT / "results.json", {"outputs": {"lambda1": float(first)}})
    log("Completed. Smallest positive factor: " + str(first))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        log(traceback.format_exc())
        raise
