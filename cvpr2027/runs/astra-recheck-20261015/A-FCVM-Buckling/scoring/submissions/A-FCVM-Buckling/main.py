import os
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

import sys
import json
import shutil
import platform
import subprocess
import re
import time
from pathlib import Path

import numpy as np
import gmsh

ROOT = Path(os.environ["CADFEM_INPUT_DIR"])
OUT = Path(os.environ["CADFEM_OUTPUT_DIR"])
OUT.mkdir(parents=True, exist_ok=True)
os.chdir(OUT)
started = time.time()

def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2))

spec = json.loads((ROOT / "faces.json").read_text())
descriptors = spec["face_descriptors"]
faces = {int(f["face_index"]): f for f in descriptors}
shutil.copy2(ROOT / "analysis.step", OUT / "part.step")
shutil.copy2(ROOT / "faces.json", OUT / "faces.json")
readmes = []
for p in list(ROOT.glob("*README*")) + list(ROOT.glob("*readme*")):
    readmes.append({"path": str(p), "text": p.read_text(errors="replace")})
dump("environment.json", {
    "python": sys.version, "platform": platform.platform(),
    "gmsh": gmsh.__version__, "numpy": np.__version__,
    "ccx": shutil.which("ccx"), "threads": 2,
    "units": {"length": "mm", "force": "N", "stress": "MPa"},
    "input_face_count": len(descriptors), "candidate_readmes": readmes,
})
log = open(OUT / "solver.log", "w", buffering=1)

def message(s):
    log.write(str(s) + "\n")

def mesh(size, label):
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setNumber("General.NumThreads", 2)
    gmsh.model.add(label)
    imported = gmsh.model.occ.importShapes(str(OUT / "part.step"))
    solids = [v for v in imported if v[0] == 3]
    if not solids:
        raise RuntimeError("STEP has no solid regions")
    if len(solids) > 1:
        gmsh.model.occ.fragment([solids[0]], solids[1:])
    gmsh.model.occ.synchronize()
    vol = sum(gmsh.model.occ.getMass(3, t) for _, t in gmsh.model.getEntities(3))
    message(f"{label}: imported conformal volume {vol:.12g} mm^3")
    matches = {}
    for fid in [1, 2, 7, 13, 18, 9]:
        d = faces[fid]
        center = np.asarray(d["centroid_mm"])
        area = float(d["area_mm2"])
        scores = []
        for _, tag in gmsh.model.getEntities(2):
            c = np.array(gmsh.model.occ.getCenterOfMass(2, tag))
            a = gmsh.model.occ.getMass(2, tag)
            score = np.linalg.norm(c-center) + abs(a-area)/max(1., area)
            scores.append((score, tag, a, c.tolist()))
        best = min(scores)
        if best[0] > 0.01:
            raise RuntimeError(f"Cannot identify prescribed face {fid}: {best}")
        matches[fid] = best[1]
    gmsh.option.setNumber("Mesh.MeshSizeMin", size)
    gmsh.option.setNumber("Mesh.MeshSizeMax", size)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
    gmsh.option.setNumber("Mesh.Optimize", 1)
    gmsh.model.mesh.generate(3)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.write(str(OUT / (label + ".msh")))
    tags, xyz, _ = gmsh.model.mesh.getNodes()
    order = np.argsort(tags)
    tags = tags[order].astype(np.int64)
    xyz = xyz.reshape(-1, 3)[order]
    index = {int(t): i for i, t in enumerate(tags)}
    etypes, etags, enodes = gmsh.model.mesh.getElements(3)
    connectivity = []
    element_tags = []
    for typ, ids, ns in zip(etypes, etags, enodes):
        if typ != 11:
            raise RuntimeError(f"Expected quadratic tetrahedra, got Gmsh type {typ}")
        connectivity.append(np.asarray(ns, dtype=np.int64).reshape(-1, 10))
        element_tags.append(np.asarray(ids, dtype=np.int64))
    conn = np.vstack(connectivity)
    eids = np.concatenate(element_tags)
    support = {}
    for fid in [1, 2, 7, 13, 18]:
        nt, _, _ = gmsh.model.mesh.getNodes(2, matches[fid], includeBoundary=True)
        support[fid] = np.unique(nt.astype(np.int64))
    forces = np.zeros((len(tags), 3))
    ts, ids, ns = gmsh.model.mesh.getElements(2, matches[9])
    integrated_area = 0.
    for typ, nodes in zip(ts, ns):
        if typ != 9:
            raise RuntimeError("Loaded surface is not quadratic triangular")
        for tri in np.asarray(nodes).reshape(-1, 6):
            p = xyz[[index[int(t)] for t in tri[:3]]]
            a = np.linalg.norm(np.cross(p[1]-p[0], p[2]-p[0]))/2
            integrated_area += a
            for n in tri[3:]:
                forces[index[int(n)], 0] -= a/3
    message(f"{label}: nodes={len(tags)}, C3D10={len(conn)}, loaded area={integrated_area}, resultant={forces.sum(axis=0)}")
    gmsh.finalize()
    # Gmsh and Abaqus/CalculiX differ in the last two tetrahedron edges.
    cc = conn[:, [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]
    return tags, xyz, eids, conn, cc, support, forces, vol

def write_deck(path, data, buckle):
    tags, xyz, eids, conn, cc, support, forces, vol = data
    with open(path, "w") as f:
        f.write("*HEADING\nContinuous STEP steel solid; quadratic tetrahedra\n*NODE,NSET=NALL\n")
        for n, p in zip(tags, xyz):
            f.write(f"{n},{p[0]:.12g},{p[1]:.12g},{p[2]:.12g}\n")
        f.write("*ELEMENT,TYPE=C3D10,ELSET=EALL\n")
        for e, c in zip(eids, cc):
            f.write(str(e)+","+",".join(map(str,c))+"\n")
        f.write("*MATERIAL,NAME=STEEL\n*ELASTIC\n210000.,0.3\n")
        f.write("*SOLID SECTION,ELSET=EALL,MATERIAL=STEEL\n")
        for name, ns in [("FIXED", support[1]), ("YSUP", np.unique(np.concatenate([support[i] for i in [2,7,13,18]])))]:
            f.write(f"*NSET,NSET={name}\n")
            for i in range(0, len(ns), 12):
                f.write(",".join(map(str, ns[i:i+12]))+"\n")
        f.write("*BOUNDARY\nFIXED,1,3\nYSUP,2,2\n")
        f.write("*STEP\n")
        if buckle:
            f.write("*BUCKLE\n4,0.0001\n")
        else:
            f.write("*STATIC\n")
        f.write("*CLOAD\n")
        for n, force in zip(tags, forces):
            if force[0] != 0:
                f.write(f"{n},1,{force[0]:.14g}\n")
        f.write("*NODE PRINT,NSET=NALL\nU\n")
        if not buckle:
            f.write("*EL PRINT,ELSET=EALL\nS\n")
        f.write("*NODE FILE\nU\n")
        if not buckle:
            f.write("*EL FILE\nS\n")
        f.write("*END STEP\n")

def run(job):
    remaining = max(30, int(575-(time.time()-started)))
    with open(OUT / (job + ".stdout"), "w") as f:
        p = subprocess.run(["ccx", "-i", job], stdout=f, stderr=subprocess.STDOUT,
                           timeout=remaining, env=os.environ.copy())
    text = (OUT / (job + ".stdout")).read_text(errors="replace")
    message(f"\n=== {job} ===\n{text}")
    if p.returncode:
        raise RuntimeError(f"CalculiX failed: {job}")
    dat = OUT / (job + ".dat")
    if not dat.exists():
        raise RuntimeError(f"No solver data for {job}")
    return dat.read_text(errors="replace")

def eigenvalues(text):
    values = []
    active = False
    number = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][-+]?\d+)?"
    for line in text.splitlines():
        # CalculiX uses a letter-spaced title and can put BUCKLING and
        # FACTOR on separate lines in the column headings.
        compact = re.sub(r"\s+", "", line).upper()
        if "BUCKLING" in compact:
            active = True
            continue
        if not active:
            continue
        m = re.fullmatch(r"\s*(\d+)\s+(" + number + r")\s*", line)
        if m:
            values.append(float(m.group(2).upper().replace("D", "E")))
        elif values and line.strip():
            break
        elif any(word in compact for word in ("DISPLACEMENTS", "STRESSES")):
            break
    positive = sorted(x for x in values if np.isfinite(x) and x > 0)
    if not positive:
        raise RuntimeError("No positive buckling factors in CalculiX .dat buckling table")
    message(f"Parsed CalculiX buckling factors: {values}")
    return positive

def parse_fields(text, tags):
    idx = {int(t): i for i,t in enumerate(tags)}
    blocks = []
    current = None
    stress = []
    reading_stress = False
    for line in text.splitlines():
        low = line.lower()
        if "displacements" in low:
            current = np.full((len(tags), 3), np.nan)
            blocks.append(current)
            reading_stress = False
            continue
        if "stresses" in low:
            current = None
            reading_stress = True
            continue
        a = line.split()
        try:
            if current is not None and len(a) == 4 and int(a[0]) in idx:
                current[idx[int(a[0])]] = [float(v.replace("D","E")) for v in a[1:]]
            elif reading_stress and len(a) == 8:
                stress.append([float(v.replace("D","E")) for v in a])
        except ValueError:
            pass
    return blocks, np.asarray(stress)

history = []
last = None
try:
    for level, size in enumerate([5.0, 3.5]):
        label = f"level{level}"
        data = mesh(size, label)
        job = label + "_buckling"
        write_deck(OUT / (job + ".inp"), data, True)
        text = run(job)
        vals = eigenvalues(text)
        record = {"level": level, "target_size_mm": size, "nodes": len(data[0]),
                  "elements": len(data[2]), "volume_mm3": data[-1],
                  "positive_buckling_factors": vals}
        if history:
            record["relative_change_lambda1"] = abs(vals[0]-history[-1]["positive_buckling_factors"][0])/vals[0]
        history.append(record)
        last = (label, data, text, vals)
        dump("refinement.json", {"method": "conformal quadratic tetrahedral h-refinement",
                                "levels": history, "extrapolation_used": False})
        if time.time()-started > 390:
            break
    label, data, buckling_text, vals = last
    shutil.copy2(OUT / (label + ".msh"), OUT / "mesh.msh")
    write_deck(OUT / "prebuckling.inp", data, False)
    static_text = run("prebuckling")
    displacement, stresses = parse_fields(static_text, data[0])
    modes, _ = parse_fields(buckling_text, data[0])
    if not displacement or not np.all(np.isfinite(displacement[0])):
        raise RuntimeError("Incomplete prebuckling displacement output")
    if stresses.size == 0:
        raise RuntimeError("No prebuckling stress output")
    np.savez_compressed(
        OUT / "fields.npz",
        node_ids=data[0], coordinates_mm=data[1], element_ids=data[2],
        connectivity_gmsh_node_ids=data[3], connectivity_ccx_node_ids=data[4],
        displacement_mm=displacement[0],
        stress_element_integration_point_sxx_syy_szz_sxy_sxz_syz_MPa=stresses,
        reference_nodal_forces_N=data[6],
        buckling_factors=np.asarray(vals),
        buckling_modes=np.asarray(modes),
        fixed_node_ids=data[5][1],
        uy_fixed_node_ids=np.unique(np.concatenate([data[5][i] for i in [2,7,13,18]]))
    )
    dump("results.json", {"outputs": {"lambda1": float(vals[0])}})
    dump("refinement.json", {
        "method": "conformal C3D10 h-refinement; independent reference-load stress solve",
        "levels": history, "reported_level": label, "extrapolation_used": False,
        "convergence_assessment": (
            "Two mesh levels evaluated; relative change reported, not a rigorous error bound."
            if len(history) > 1 else "Only one level completed; mesh convergence not established."),
        "eigenproblem": "K + lambda KG(reference stress) = 0",
        "traction_integration": "Consistent quadratic planar triangle loads; corner weights zero, midside weights area/3",
        "elapsed_seconds": time.time()-started
    })
    message(f"Reported smallest positive eigenvalue: {vals[0]:.12g}")
except Exception as exc:
    message(f"ERROR: {type(exc).__name__}: {exc}")
    raise
finally:
    log.close()
