import os
import sys
import json
import time
import shutil
import subprocess
import re
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

import numpy as np
import gmsh

START = time.time()
IN = Path(os.environ.get("CADFEM_INPUT_DIR", ".")).resolve()
OUT = Path(os.environ.get("CADFEM_OUTPUT_DIR", ".")).resolve()
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = IN / "bracket.step"
if not SOURCE.exists():
    raise FileNotFoundError(SOURCE)

shutil.copy2(SOURCE, OUT / "part.step")
notes = {}
for p in IN.rglob("*"):
    if p.is_file() and p.suffix.lower() in (".txt", ".md", ".json", ".yaml", ".yml"):
        notes[str(p.relative_to(IN))] = p.read_text(errors="replace")

environment = {
    "python": sys.version,
    "numpy": np.__version__,
    "gmsh": gmsh.__version__,
    "ccx": shutil.which("ccx"),
    "threads": 2,
    "input_documents": notes,
    "units": {"length": "mm", "force": "N", "stress": "MPa"},
    "material": {"E": 113800.0, "nu": 0.342, "density_g_cm3": 4.43},
}
(OUT / "environment.json").write_text(json.dumps(environment, indent=2))

axis = np.array([-0.030352, 0.999539, 0.0])
axis /= np.linalg.norm(axis)
pin_origin = np.array([-20.9236, -74.6978, 44.7246])
load_point = np.array([-21.0359, -75.0647, 44.8010])
bolts = np.array([[0., 0.], [52.0472, 1.5805],
                  [0., -148.1248], [38.0833, -146.9684]])
wrenches = np.array([
    [0., 0., 35585.77, 0., 0., 0.],
    [-37809.90, 0., 0., 0., 0., 0.],
    [-28276.20, 0., 31403.90, 0., 0., 0.],
    [0., 0., 0., 0., 0., 564924.20],
])

def make_mesh(folder, size):
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.option.setNumber("General.NumThreads", 2)
        gmsh.model.add("published_bracket")
        gmsh.model.occ.importShapes(str(SOURCE))
        gmsh.model.occ.synchronize()
        solids = gmsh.model.getEntities(3)
        if not solids:
            raise RuntimeError("STEP contains no volumes")
        gmsh.option.setNumber("Mesh.MeshSizeMax", size)
        gmsh.option.setNumber("Mesh.MeshSizeMin", size * 0.45)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 16)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        # Keep quadratic displacement interpolation, but use straight-sided geometry.
        # Projecting midside nodes onto the many small CAD faces inverted tets.
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
        gmsh.model.mesh.generate(3)
        gmsh.write(str(folder / "mesh.msh"))
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        order = np.argsort(tags)
        tags = np.asarray(tags, dtype=np.int64)[order]
        xyz = np.asarray(xyz).reshape(-1, 3)[order]
        def indices(t):
            return np.searchsorted(tags, np.asarray(t, dtype=np.int64))
        tet = []
        types, _, conn = gmsh.model.mesh.getElements(3)
        for typ, c in zip(types, conn):
            if typ != 11:
                raise RuntimeError("Expected quadratic tetrahedra, got " + str(typ))
            tet.append(indices(c).reshape(-1, 10))
        tet = np.vstack(tet)
        corners = xyz[tet[:, :4]]
        determinants = np.linalg.det(np.stack([
            corners[:, 1] - corners[:, 0],
            corners[:, 2] - corners[:, 0],
            corners[:, 3] - corners[:, 0]], axis=2))
        if not np.all(determinants > 0):
            raise RuntimeError("Nonpositive straight-sided tetrahedron Jacobian")
        # Verify the Gmsh edge ordering used by the C3D10 export below.
        edges = [(0, 1), (1, 2), (2, 0), (0, 3), (2, 3), (1, 3)]
        for j, (a, b) in enumerate(edges, 4):
            midpoint = 0.5 * (corners[:, a] + corners[:, b])
            if not np.allclose(xyz[tet[:, j]], midpoint, rtol=0, atol=1e-7):
                raise RuntimeError("Unexpected quadratic tetrahedron edge geometry")
        primary = np.zeros(len(tags), dtype=bool)
        primary[np.unique(tet[:, :4])] = True
        fixed = set()
        weights = np.zeros(len(tags))
        selected = {"bolt_surfaces": [], "pin_surfaces": []}
        for dim, surf in gmsh.model.getEntities(2):
            st, _, _ = gmsh.model.mesh.getNodes(2, surf, includeBoundary=True)
            ids = np.unique(indices(st))
            if len(ids) < 3:
                continue
            # Identify CAD cylinders from their corner nodes. Straight midside
            # nodes lie on chords, not exactly on the analytic cylinder.
            corner_ids = ids[primary[ids]]
            if len(corner_ids) < 3:
                continue
            p = xyz[corner_ids]
            bolt_surface = False
            for center in bolts:
                rad = np.linalg.norm(p[:, :2] - center, axis=1)
                if np.max(np.abs(rad - 5.1562)) < 0.06:
                    bolt_surface = True
                    break
            if bolt_surface:
                fixed.update(ids.tolist())
                selected["bolt_surfaces"].append(int(surf))
            q = p - pin_origin
            axial = q @ axis
            radial = np.linalg.norm(q - axial[:, None] * axis, axis=1)
            if (np.max(np.abs(radial - 9.5504)) < 0.06
                    and np.min(np.abs(axial)) > 10.9
                    and np.max(np.abs(axial)) < 17.7):
                selected["pin_surfaces"].append(int(surf))
                sty, _, sco = gmsh.model.mesh.getElements(2, surf)
                for typ, c in zip(sty, sco):
                    props = gmsh.model.mesh.getElementProperties(typ)
                    nn = props[3]
                    triangles = indices(c).reshape(-1, nn)
                    if props[5] != 3:
                        raise RuntimeError("Unexpected surface element")
                    a, b, d = xyz[triangles[:, 0]], xyz[triangles[:, 1]], xyz[triangles[:, 2]]
                    area = 0.5 * np.linalg.norm(np.cross(b-a, d-a), axis=1)
                    for j in range(nn):
                        np.add.at(weights, triangles[:, j], area / nn)
        if len(fixed) < 24 or np.count_nonzero(weights) < 24:
            raise RuntimeError("Interface surface recognition failed: " + str(selected))
        return xyz, tet, np.array(sorted(fixed)), weights, selected
    finally:
        gmsh.finalize()

def solve(folder, size, timeout):
    folder.mkdir(exist_ok=True)
    xyz, tet, fixed, weights, selected = make_mesh(folder, size)
    loaded = np.flatnonzero(weights)
    r = xyz[loaded] - load_point
    B = np.zeros((len(loaded), 3, 6))
    B[:, :, :3] = np.eye(3)
    B[:, 0, 4] = r[:, 2]
    B[:, 0, 5] = -r[:, 1]
    B[:, 1, 3] = -r[:, 2]
    B[:, 1, 5] = r[:, 0]
    B[:, 2, 3] = r[:, 1]
    B[:, 2, 4] = -r[:, 0]
    w = weights[loaded]
    gram = np.einsum("nki,n,nkj->ij", B, w, B)
    multipliers = np.linalg.solve(gram, wrenches.T)
    forces = np.einsum("nki,ic,n->cnk", B, multipliers, w)
    recovered = np.einsum("nki,cnk->ci", B, forces)
    inp = folder / "bracket.inp"
    with inp.open("w") as f:
        f.write("*HEADING\nImported STEP, quadratic tetrahedral linear elasticity\n*NODE,NSET=NALL\n")
        for i, p in enumerate(xyz, 1):
            f.write(f"{i},{p[0]:.12g},{p[1]:.12g},{p[2]:.12g}\n")
        f.write("*ELEMENT,TYPE=C3D10,ELSET=SOLID\n")
        permutation = [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]
        for i, cell in enumerate(tet, 1):
            f.write(str(i) + "," + ",".join(str(int(v)+1) for v in cell[permutation]) + "\n")
        f.write("*MATERIAL,NAME=TI64\n*ELASTIC\n113800.,0.342\n")
        f.write("*SOLID SECTION,ELSET=SOLID,MATERIAL=TI64\n")
        f.write("*NSET,NSET=FIXED\n")
        for j in range(0, len(fixed), 16):
            f.write(",".join(str(int(v)+1) for v in fixed[j:j+16]) + "\n")
        f.write("*BOUNDARY\nFIXED,1,3\n")
        for case in range(4):
            f.write("*STEP\n*STATIC\n*CLOAD,OP=NEW\n")
            for n, force in zip(loaded, forces[case]):
                for component in range(3):
                    if abs(force[component]) > 1e-13:
                        f.write(f"{n+1},{component+1},{force[component]:.12g}\n")
            f.write("*NODE PRINT,NSET=NALL\nU\n*END STEP\n")
    with (folder / "solver.log").open("w") as log:
        log.write("Surface identification: " + json.dumps(selected) + "\n")
        log.write("Recovered force/moment resultants at load point:\n" + str(recovered) + "\n")
        log.flush()
        remaining = min(timeout, 565 - (time.time() - START))
        if remaining < 10:
            raise RuntimeError("Insufficient runtime left")
        proc = subprocess.run(["ccx", "-i", "bracket"], cwd=folder,
                              stdout=log, stderr=subprocess.STDOUT, timeout=remaining)
        if proc.returncode:
            raise RuntimeError("CalculiX failed; see " + str(folder / "solver.log"))
    dat = (folder / "bracket.dat").read_text(errors="replace")
    blocks = re.split(r"displacements\s+\(.*?\).*?\n", dat, flags=re.I)
    displacement = []
    row_pattern = re.compile(r"^\s*(\d+)\s+([-+\d.EeDd]+)\s+([-+\d.EeDd]+)\s+([-+\d.EeDd]+)\s*$")
    for block in blocks[1:]:
        u = np.full_like(xyz, np.nan)
        for line in block.splitlines():
            m = row_pattern.match(line)
            if m:
                n = int(m.group(1)) - 1
                if 0 <= n < len(xyz):
                    u[n] = [float(s.replace("D", "E").replace("d", "e")) for s in m.groups()[1:]]
        if np.isfinite(u).all():
            displacement.append(u)
    if len(displacement) != 4:
        raise RuntimeError(f"Expected four complete displacement fields, found {len(displacement)}")
    u = np.array(displacement)
    maxima = np.linalg.norm(u, axis=2).max(axis=1)
    np.savez_compressed(folder / "fields.npz", points=xyz, tetra10=tet,
                        displacement=u, displacement_magnitude=np.linalg.norm(u, axis=2),
                        fixed_nodes=fixed, loaded_nodes=loaded,
                        applied_forces=forces, load_case_names=np.array(
                            ["vertical", "horizontal", "diagonal", "torsion"]))
    return {"mesh_size_mm": size, "nodes": len(xyz), "elements": len(tet),
            "max_displacements_mm": maxima.tolist(), "interfaces": selected,
            "directory": folder.name, "elapsed_seconds": time.time()-START}

history = []
best = None
for number, size in enumerate([5.0, 3.4]):
    if number and time.time() - START > 310:
        history.append({"mesh_size_mm": size, "status": "not attempted: runtime budget"})
        break
    folder = OUT / ("run_" + str(number))
    try:
        record = solve(folder, size, 430)
        record["status"] = "completed"
        history.append(record)
        best = record
    except Exception as exc:
        history.append({"mesh_size_mm": size, "status": "failed", "error": str(exc)})
        if best is None:
            (OUT / "refinement.json").write_text(json.dumps({"runs": history}, indent=2))
            raise
        break

best_folder = OUT / best["directory"]
for name in ["mesh.msh", "fields.npz", "solver.log"]:
    shutil.copy2(best_folder / name, OUT / name)
keys = ["vertical_max_displacement_mm", "horizontal_max_displacement_mm",
        "diagonal_max_displacement_mm", "torsion_max_displacement_mm"]
(OUT / "results.json").write_text(json.dumps(
    {"outputs": dict(zip(keys, best["max_displacements_mm"]))}, indent=2))
completed = [h for h in history if h["status"] == "completed"]
refinement = {
    "runs": history,
    "selected_run": best["directory"],
    "method": "Straight-sided quadratic tetrahedra with validated positive Jacobians; full 3D linear elasticity; all bolt-wall translations fixed. Cylindrical boundaries are faceted, with all corner and midside bolt-wall nodes constrained.",
    "load_transfer": "Area-weighted rigid-motion least-squares distributing coupling (RBE3-type), without stiffening the bores. Nodal forces preserve all six applied resultants.",
    "convergence_verified": False,
    "limitations": "Finite mesh estimates, not extrapolated. Published mesh and original RBE3 weighting are unavailable.",
}
if len(completed) > 1:
    a = np.array(completed[-2]["max_displacements_mm"])
    b = np.array(completed[-1]["max_displacements_mm"])
    refinement["relative_change"] = (np.abs(b-a)/b).tolist()
    refinement["convergence_verified"] = bool(np.all(np.abs(b-a)/b < 0.02))
    refinement["criterion"] = "Less than 2 percent change in every maximum between the two meshes."
(OUT / "refinement.json").write_text(json.dumps(refinement, indent=2))
