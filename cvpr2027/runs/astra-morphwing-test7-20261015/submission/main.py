import os
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

import sys
import json
import time
import shutil
import platform
import subprocess
import re
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import linear_sum_assignment
import gmsh

START = time.time()
OUT = Path(os.environ.get("CADFEM_OUTPUT_DIR", ".")).resolve()
INP = Path(os.environ.get("CADFEM_INPUT_DIR", ".")).resolve()
OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT / "solver.log"


def log(s):
    with LOG.open("a") as f:
        f.write(str(s) + "\n")


def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2))


def mesh_model(h, filename):
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("General.NumThreads", 2)
        gmsh.model.add("free_specimen")
        imported = gmsh.model.occ.importShapes(str(OUT / "part.step"))
        gmsh.model.occ.synchronize()
        solids = gmsh.model.getEntities(3)
        if not solids:
            raise RuntimeError("STEP contains no solids")
        bounds = [gmsh.model.getBoundingBox(d, t) for d, t in solids]
        xmin = min(b[0] for b in bounds)
        ymin = min(b[1] for b in bounds)
        zmin = min(b[2] for b in bounds)
        xmax = max(b[3] for b in bounds)
        ymax = max(b[4] for b in bounds)
        zmax = max(b[5] for b in bounds)
        cutter = gmsh.model.occ.addBox(
            19.0, ymin - 10, zmin - 10,
            xmax - 19 + 10, ymax - ymin + 20, zmax - zmin + 20
        )
        gmsh.model.occ.intersect(solids, [(3, cutter)],
                                 removeObject=True, removeTool=True)
        gmsh.model.occ.synchronize()
        volumes = gmsh.model.getEntities(3)
        if not volumes:
            raise RuntimeError("No free solid after cutting at x=19")
        gmsh.model.addPhysicalGroup(3, [t for d, t in volumes], 1)
        gmsh.option.setNumber("Mesh.MeshSizeMin", h)
        gmsh.option.setNumber("Mesh.MeshSizeMax", h)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.setOrder(2)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        gmsh.write(str(filename))
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        xyz = np.asarray(xyz).reshape(-1, 3)
        tags = np.asarray(tags, dtype=np.int64)
        order = np.argsort(tags)
        tags, xyz = tags[order], xyz[order]
        types, etags, enodes = gmsh.model.mesh.getElements(3)
        blocks = []
        for typ, nodes in zip(types, enodes):
            if typ != 11:
                raise RuntimeError("Expected quadratic tetrahedra, got " + str(typ))
            blocks.append(np.searchsorted(tags, np.asarray(nodes).reshape(-1, 10)))
        conn = np.vstack(blocks)
        used = np.unique(conn)
        renumber = np.full(len(xyz), -1, dtype=int)
        renumber[used] = np.arange(len(used))
        xyz = xyz[used]
        conn = renumber[conn]
        clamp = np.where(np.abs(xyz[:, 0] - 19) < 1.e-5)[0]
        if len(clamp) < 6:
            raise RuntimeError("Clamp nodes were not found")
        volume = sum(gmsh.model.occ.getMass(3, t) for d, t in volumes)
        log(f"Mesh h={h}: nodes={len(xyz)}, tetra10={len(conn)}, "
            f"clamp_nodes={len(clamp)}, CAD_volume_mm3={volume}")
        return xyz, conn, clamp, volume
    finally:
        gmsh.finalize()


def write_input(job, xyz, conn, clamp):
    cc = conn[:, [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]] + 1
    with (OUT / (job + ".inp")).open("w") as f:
        f.write("*HEADING\nFree stepped PLA plate, mm N tonne s\n*NODE,NSET=NALL\n")
        for i, p in enumerate(xyz):
            f.write(f"{i+1},{p[0]:.12g},{p[1]:.12g},{p[2]:.12g}\n")
        f.write("*ELEMENT,TYPE=C3D10,ELSET=SOLID\n")
        for i, row in enumerate(cc):
            f.write(str(i+1) + "," + ",".join(map(str, row)) + "\n")
        f.write("*NSET,NSET=CLAMP\n")
        for k in range(0, len(clamp), 16):
            f.write(",".join(str(i+1) for i in clamp[k:k+16]) + "\n")
        f.write("*MATERIAL,NAME=PLA\n*ELASTIC\n2110.,0.3\n"
                "*DENSITY\n1.18E-9\n"
                "*SOLID SECTION,ELSET=SOLID,MATERIAL=PLA\n"
                "*BOUNDARY\nCLAMP,1,3\n"
                "*STEP\n*FREQUENCY\n12\n"
                "*NODE PRINT,NSET=NALL\nU\n*END STEP\n")


def numbers(line):
    return [float(s.replace("D", "E").replace("d", "e"))
            for s in re.findall(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[EeDd][-+]?\d+)?", line)]


def read_modes(job, nnode):
    lines = (OUT / (job + ".dat")).read_text(errors="replace").splitlines()
    frequencies = []
    active = False
    for line in lines:
        compact = re.sub(r"\s+", "", line).upper()
        if "EIGENVALUEOUTPUT" in compact:
            active = True
            continue
        if active:
            vals = numbers(line)
            if len(vals) >= 4 and re.match(r"^\s*\d+\s+", line):
                mode = int(vals[0])
                if mode == len(frequencies) + 1:
                    frequencies.append(vals[3])
                if len(frequencies) == 12:
                    break
    blocks = []
    i = 0
    while i < len(lines):
        if "displacements" in lines[i].lower() and "set" in lines[i].lower():
            u = np.zeros((nnode, 3))
            count = 0
            i += 1
            while i < len(lines):
                vals = numbers(lines[i])
                if len(vals) == 4 and re.match(r"^\s*\d+\s+", lines[i]):
                    nid = int(vals[0])
                    if 1 <= nid <= nnode:
                        u[nid-1] = vals[1:4]
                        count += 1
                elif count:
                    break
                i += 1
            if count:
                if count != nnode:
                    raise RuntimeError(f"Incomplete modal displacement block: {count}/{nnode}")
                blocks.append(u)
        else:
            i += 1
    if len(frequencies) < 6 or len(blocks) != len(frequencies):
        log((OUT / (job + ".dat")).read_text(errors="replace")[:18000])
        raise RuntimeError(f"Could not parse modes: {len(frequencies)} frequencies, {len(blocks)} fields")
    frequencies = np.asarray(frequencies)
    if np.any(frequencies <= 0):
        raise RuntimeError("Nonpositive frequencies")
    return frequencies, np.asarray(blocks)


def identify(xyz, conn, freq, modes):
    p = xyz[conn[:, :4]]
    vol = np.abs(np.einsum("ij,ij->i",
                          np.cross(p[:, 1]-p[:, 0], p[:, 2]-p[:, 0]),
                          p[:, 3]-p[:, 0])) / 6
    weights = np.zeros(len(xyz))
    for j in range(10):
        np.add.at(weights, conn[:, j], vol / 10)
    weights /= weights.sum()
    center = np.sum(weights[:, None] * xyz, axis=0)
    s = np.clip((xyz[:, 0]-19)/(xyz[:, 0].max()-19), 0, 1)
    templates = []
    for beta in [1.875104068711961, 4.694091132974174]:
        a = (np.cosh(beta)+np.cos(beta))/(np.sinh(beta)+np.sin(beta))
        phi = np.cosh(beta*s)-np.cos(beta*s)-a*(np.sinh(beta*s)-np.sin(beta*s))
        derivative = beta*(np.sinh(beta*s)+np.sin(beta*s)
                           - a*(np.cosh(beta*s)-np.cos(beta*s))) / (xyz[:, 0].max()-19)
        t = np.zeros_like(xyz)
        t[:, 2] = phi
        t[:, 0] = -(xyz[:, 2]-center[2])*derivative
        templates.append(t)
    t = np.zeros_like(xyz)
    t[:, 2] = (xyz[:, 1]-center[1])*np.sin(np.pi*s/2)
    t[:, 1] = -(xyz[:, 2]-center[2])*np.sin(np.pi*s/2)
    templates.insert(1, t)
    mac = np.zeros((3, len(freq)))
    for j, t in enumerate(templates):
        tn = np.sum(weights[:, None]*t*t)
        for k, u in enumerate(modes):
            un = np.sum(weights[:, None]*u*u)
            cross = np.sum(weights[:, None]*t*u)
            mac[j, k] = cross*cross/(tn*un)
    rows, cols = linear_sum_assignment(-mac)
    selected = np.empty(3, dtype=int)
    selected[rows] = cols
    keys = ["f_1B_Hz", "f_1T_Hz", "f_2B_Hz"]
    outputs = {key: float(freq[k]) for key, k in zip(keys, selected)}
    detail = {
        "method": "Volume-weighted displacement MAC against spanwise first/second cantilever bending and first span-axis torsion shapes; unique maximum-total-MAC assignment, not frequency ordering.",
        "MAC_rows": keys,
        "MAC": mac.tolist(),
        "selected_mode_numbers": {key: int(k+1) for key, k in zip(keys, selected)},
        "all_frequencies_Hz": freq.tolist()
    }
    return outputs, detail, weights, selected


def main():
    LOG.write_text("Isotropic 3D quadratic-tetrahedron modal analysis.\n"
                   "Units: mm, N, tonne, s. Grip removed by exact CAD intersection.\n"
                   "Solid elements have translational DOFs only; fixing every section "
                   "node fixes the entire section including its rotation.\n")
    src = INP / "part.step"
    if src.resolve() != (OUT / "part.step").resolve():
        shutil.copy2(src, OUT / "part.step")
    readmes = list(INP.glob("*README*")) + list(INP.glob("*readme*"))
    for path in readmes:
        log("Candidate artifact instructions:\n" + path.read_text(errors="replace"))
    executable = shutil.which("ccx")
    if not executable:
        raise RuntimeError("ccx not found")
    dump("environment.json", {
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "gmsh": gmsh.__version__, "ccx_executable": executable,
        "threads": 2, "solver": "CalculiX, C3D10, undamped frequency extraction",
        "material": {"E_MPa": 2110, "nu": 0.3, "density_kg_m3": 1180}
    })
    history = []
    for iteration, h in enumerate([4.5, 3.0]):
        job = f"modal_{iteration}"
        meshpath = OUT / f"mesh_{iteration}.msh"
        xyz, conn, clamp, volume = mesh_model(h, meshpath)
        write_input(job, xyz, conn, clamp)
        remaining = 570 - (time.time()-START)
        if remaining < 25:
            raise RuntimeError("Insufficient runtime for required refinement solve")
        with (OUT / (job + ".stdout")).open("w") as f:
            run = subprocess.run([executable, job], cwd=OUT, stdout=f,
                                 stderr=subprocess.STDOUT, timeout=remaining)
        transcript = (OUT / (job + ".stdout")).read_text(errors="replace")
        log(f"\n--- {job} ---\n{transcript}")
        if run.returncode != 0:
            raise RuntimeError(f"CalculiX failed with exit status {run.returncode}")
        freq, modes = read_modes(job, len(xyz))
        outputs, identification, weights, selected = identify(xyz, conn, freq, modes)
        record = {"mesh_size_mm": h, "nodes": len(xyz), "elements": len(conn),
                  "CAD_volume_mm3": volume, "outputs": outputs,
                  "mode_identification": identification,
                  "elapsed_seconds": time.time()-START}
        if history:
            record["relative_frequency_change"] = {
                k: abs(outputs[k]-history[-1]["outputs"][k])/outputs[k] for k in outputs}
        history.append(record)
        dump("refinement.json", {
            "studies": history,
            "statement": "Two independently generated quadratic solid meshes. Reported changes are observed mesh sensitivity, not a rigorous error bound.",
            "converged_within_2_percent": bool(len(history) > 1 and
                max(history[-1]["relative_frequency_change"].values()) < .02)
        })
        shutil.copy2(meshpath, OUT / "mesh.msh")
        np.savez_compressed(
            OUT / "fields.npz",
            points=xyz, coordinates=xyz, tetra10=conn, cells=conn,
            node_ids=np.arange(1, len(xyz)+1), clamp_nodes=clamp,
            frequencies_Hz=freq, displacements=modes, mode_shapes=modes,
            modal_node_volume_weights=weights,
            selected_mode_indices=selected,
            selected_labels=np.array(["1B", "1T", "2B"]),
            connectivity_convention=np.array("zero-based Gmsh tetra10"),
            units=np.array("coordinates mm; frequencies Hz; eigenvectors arbitrary normalization")
        )
    dump("results.json", {"outputs": outputs})
    log("Completed. " + json.dumps(outputs))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        log(traceback.format_exc())
        if (OUT / "results.json").exists():
            (OUT / "results.json").unlink()
        raise
