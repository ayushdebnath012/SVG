import os
import sys
import json
import time
import shutil
import platform
import subprocess
import traceback
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

import numpy as np
import gmsh

START = time.time()
INPUT = Path(os.environ.get("CADFEM_INPUT_DIR", ".")).resolve()
OUTPUT = Path(os.environ.get("CADFEM_OUTPUT_DIR", ".")).resolve()
OUTPUT.mkdir(parents=True, exist_ok=True)
LOG = OUTPUT / "solver.log"


def log(s):
    with LOG.open("a") as f:
        f.write(str(s) + "\n")


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False))


def surface_weights(x, triangles):
    # Degree-five Dunavant quadrature; weights normalized to unit area.
    quadrature = [
        (1 / 3, 1 / 3, 0.225),
        (0.470142064105115, 0.470142064105115, 0.132394152788506),
        (0.059715871789770, 0.470142064105115, 0.132394152788506),
        (0.470142064105115, 0.059715871789770, 0.132394152788506),
        (0.101286507323456, 0.101286507323456, 0.125939180544827),
        (0.797426985353087, 0.101286507323456, 0.125939180544827),
        (0.101286507323456, 0.797426985353087, 0.125939180544827),
    ]
    result = np.zeros(len(x))
    p = x[triangles]
    for r, s, w in quadrature:
        a = 1 - r - s
        n = np.array([a * (2*a-1), r*(2*r-1), s*(2*s-1),
                      4*a*r, 4*r*s, 4*s*a])
        dr = np.array([1-4*a, 4*r-1, 0, 4*(a-r), 4*s, -4*s])
        ds = np.array([1-4*a, 0, 4*s-1, -4*r, 4*r, 4*(a-s)])
        tangent_r = np.einsum("ijk,j->ik", p, dr)
        tangent_s = np.einsum("ijk,j->ik", p, ds)
        da = 0.5*w*np.linalg.norm(np.cross(tangent_r, tangent_s), axis=1)
        np.add.at(result, triangles.ravel(), (da[:, None]*n).ravel())
    return result


def run_mesh(h, label):
    directory = OUTPUT / label
    directory.mkdir(exist_ok=True)
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("General.NumThreads", 2)
        gmsh.logger.start()
        gmsh.model.add(label)
        gmsh.model.occ.importShapes(str(OUTPUT / "part.step"))
        gmsh.model.occ.synchronize()
        volumes = gmsh.model.getEntities(3)
        if len(volumes) != 1:
            raise RuntimeError(f"Expected one solid; found {len(volumes)}")
        top, bottom = [], []
        for dim, tag in gmsh.model.getEntities(2):
            box = gmsh.model.getBoundingBox(dim, tag)
            if abs(box[2]-189) < 1e-4 and abs(box[5]-189) < 1e-4:
                top.append(tag)
            if abs(box[2]) < 1e-4 and abs(box[5]) < 1e-4:
                bottom.append(tag)
        if not top or not bottom:
            raise RuntimeError("Could not identify seat and foot planes.")
        for dim, tags, name in [(3, [v[1] for v in volumes], "solid"),
                                (2, top, "seat"), (2, bottom, "fixed_feet")]:
            pg = gmsh.model.addPhysicalGroup(dim, tags)
            gmsh.model.setPhysicalName(dim, pg, name)
        gmsh.option.setNumber("Mesh.MeshSizeMin", h)
        gmsh.option.setNumber("Mesh.MeshSizeMax", h)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 16)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 0)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        gmsh.option.setNumber("Mesh.SaveAll", 1)
        gmsh.model.mesh.generate(3)
        gmsh.write(str(directory / "mesh.msh"))
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        order = np.argsort(tags)
        tags = np.asarray(tags, dtype=np.int64)[order]
        xyz = np.asarray(xyz).reshape(-1, 3)[order]

        def index(a):
            a = np.asarray(a, dtype=np.int64)
            ix = np.searchsorted(tags, a)
            if not np.array_equal(tags[ix], a):
                raise RuntimeError("Missing mesh node")
            return ix

        tet_parts = []
        types, _, nodes = gmsh.model.mesh.getElements(3)
        for typ, nod in zip(types, nodes):
            if typ != 11:
                raise RuntimeError(f"Unexpected volume element type {typ}")
            tet_parts.append(index(nod).reshape(-1, 10))
        tetra = np.concatenate(tet_parts)
        tri_parts = []
        fixed_parts = []
        for face in top:
            types, _, nodes = gmsh.model.mesh.getElements(2, face)
            for typ, nod in zip(types, nodes):
                if typ != 9:
                    raise RuntimeError(f"Unexpected seat element type {typ}")
                tri_parts.append(index(nod).reshape(-1, 6))
        for face in bottom:
            ids, _, _ = gmsh.model.mesh.getNodes(2, face, includeBoundary=True)
            fixed_parts.append(index(ids))
        seat = np.concatenate(tri_parts)
        fixed = np.unique(np.concatenate(fixed_parts))
        gmsh_messages = gmsh.logger.get()
        for msg in gmsh_messages:
            log(label + ": " + msg)
        log(f"{label}: top faces={top}, bottom faces={bottom}")
    finally:
        gmsh.finalize()

    weights = surface_weights(xyz, seat)
    area = float(weights.sum())
    force = -1.98728*weights
    job = directory / "elastic.inp"
    with job.open("w") as f:
        f.write("*HEADING\nQuadratic tetrahedral bracket, mm N MPa\n*NODE,NSET=ALLN\n")
        for i, p in enumerate(xyz):
            f.write(f"{i+1},{p[0]:.12g},{p[1]:.12g},{p[2]:.12g}\n")
        f.write("*ELEMENT,TYPE=C3D10,ELSET=BODY\n")
        # Gmsh edges 12,23,31,14,34,24 -> CalculiX 12,23,31,14,24,34.
        ccx_tetra = tetra[:, [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]
        for i, t in enumerate(ccx_tetra):
            f.write(str(i+1) + "," + ",".join(str(int(v)+1) for v in t) + "\n")
        f.write("*NSET,NSET=FIXED\n")
        for start in range(0, len(fixed), 16):
            f.write(",".join(str(int(v)+1) for v in fixed[start:start+16]) + "\n")
        f.write("*MATERIAL,NAME=ALUMINUM\n*ELASTIC\n70000.,0.33\n")
        f.write("*SOLID SECTION,ELSET=BODY,MATERIAL=ALUMINUM\n")
        f.write("*BOUNDARY\nFIXED,1,3\n*STEP\n*STATIC\n*CLOAD\n")
        for i in np.flatnonzero(abs(force) > 1e-13):
            f.write(f"{i+1},3,{force[i]:.12g}\n")
        f.write("*NODE PRINT,NSET=ALLN\nU\n*NODE FILE\nU\n*END STEP\n")

    log(f"{label}: h={h} mm, nodes={len(xyz)}, tetrahedra={len(tetra)}, "
        f"seat area={area:.10g} mm^2, force={force.sum():.10g} N")
    remaining = 570 - (time.time() - START)
    timeout = max(10, min(260, remaining))
    with (directory / "ccx.stdout").open("w") as out:
        proc = subprocess.run(["ccx", "-i", "elastic"], cwd=directory,
                              stdout=out, stderr=subprocess.STDOUT,
                              timeout=timeout, env=os.environ.copy())
    log((directory / "ccx.stdout").read_text(errors="replace"))
    if proc.returncode:
        raise RuntimeError(f"CalculiX exited with code {proc.returncode}")
    dat = (directory / "elastic.dat").read_text(errors="replace")
    log(dat[:1500])
    u = np.full((len(xyz), 3), np.nan)
    active = False
    for line in dat.splitlines():
        if "displacements" in line.lower() and "alln" in line.lower():
            active = True
            continue
        if active:
            parts = line.split()
            if len(parts) == 4:
                try:
                    k = int(parts[0])-1
                    values = [float(v.replace("D", "E")) for v in parts[1:]]
                    if 0 <= k < len(u):
                        u[k] = values
                except ValueError:
                    pass
    if not np.isfinite(u).all():
        raise RuntimeError("Incomplete displacement output from CalculiX")
    mean = float(-np.dot(weights, u[:, 2])/area)
    maximum = float(np.linalg.norm(u, axis=1).max())
    outputs = {"seat_mean_displacement_mm": mean, "max_displacement_mm": maximum}
    np.savez_compressed(directory / "fields.npz",
                        points=xyz, coordinates_mm=xyz,
                        tetra10=tetra, cells=tetra,
                        displacement=u, displacement_mm=u,
                        displacement_magnitude_mm=np.linalg.norm(u, axis=1),
                        seat_tri6=seat, seat_integration_weights_mm2=weights,
                        fixed_node_indices=fixed, gmsh_node_tags=tags,
                        node_ids=np.arange(1, len(xyz)+1))
    return {"label": label, "nominal_mesh_size_mm": h,
            "nodes": len(xyz), "quadratic_tetrahedra": len(tetra),
            "seat_area_mm2": area, "applied_force_z_N": float(force.sum()),
            "outputs": outputs, "status": "completed"}


def main():
    LOG.write_text("3-D small-strain isotropic linear elasticity; units N, mm, MPa.\n")
    # Retain and read any locally supplied artifact instructions/specifications.
    read_files = []
    for parent in {INPUT, INPUT.parent, Path.cwd()}:
        for pattern in ["*README*", "*readme*", "*specification*.txt", "*specification*.json"]:
            for path in parent.glob(pattern):
                if path.is_file() and path.stat().st_size < 2_000_000:
                    text = path.read_text(errors="replace")
                    log(f"Instruction file {path}:\n{text}")
                    read_files.append(str(path))
    source = INPUT / "geometry.step"
    shutil.copyfile(source, OUTPUT / "part.step")
    try:
        here = Path(__file__).resolve()
        if here != OUTPUT / "main.py":
            shutil.copyfile(here, OUTPUT / "main.py")
    except Exception:
        pass
    import scipy
    environment = {
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "gmsh": gmsh.__version__, "ccx_executable": shutil.which("ccx"),
        "threads": 2, "instruction_files_read": sorted(set(read_files)),
        "units": {"length": "mm", "force": "N", "stress": "MPa"},
        "material": {"E_MPa": 70000, "poisson_ratio": 0.33},
        "gravity_applied": False,
    }
    write_json(OUTPUT / "environment.json", environment)
    runs = []
    coarse = run_mesh(9.0, "nominal")
    runs.append(coarse)
    selected = coarse
    if time.time()-START < 310:
        try:
            fine = run_mesh(6.5, "refined")
            runs.append(fine)
            selected = fine
        except Exception as exc:
            log(traceback.format_exc())
            runs.append({"label": "refined", "nominal_mesh_size_mm": 6.5,
                         "status": "failed", "error": str(exc)})
    differences = None
    converged = False
    if selected is not coarse:
        differences = {
            key: abs(selected["outputs"][key]-coarse["outputs"][key]) /
                 max(abs(selected["outputs"][key]), 1e-30)
            for key in selected["outputs"]
        }
        converged = all(v < 0.02 for v in differences.values())
    write_json(OUTPUT / "refinement.json", {
        "runs": runs, "selected_run": selected["label"],
        "relative_changes": differences, "two_mesh_2_percent_check_passed": converged,
        "notes": [
            "No extrapolation or reference-answer calibration.",
            "Seat mean uses consistent quadratic surface integration.",
            "Maximum displacement is the maximum magnitude over all quadratic mesh nodes.",
            "A two-mesh comparison is an empirical check, not a proof of convergence."
        ]
    })
    for name in ["mesh.msh", "fields.npz"]:
        shutil.copyfile(OUTPUT / selected["label"] / name, OUTPUT / name)
    write_json(OUTPUT / "results.json", {"outputs": selected["outputs"]})
    log(f"Selected {selected['label']}; elapsed {time.time()-START:.2f} seconds")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log(traceback.format_exc())
        raise
