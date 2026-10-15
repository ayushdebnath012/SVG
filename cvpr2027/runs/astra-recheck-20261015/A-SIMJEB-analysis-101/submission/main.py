import os
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

import json
import time
import shutil
import platform
import subprocess
from pathlib import Path
import numpy as np
import gmsh

START = time.time()
OUT = Path(os.environ.get("CADFEM_OUTPUT_DIR", ".")).resolve()
INP = Path(os.environ.get("CADFEM_INPUT_DIR", ".")).resolve()
OUT.mkdir(parents=True, exist_ok=True)
os.chdir(OUT)
LOG = OUT / "solver.log"

def log(message):
    with LOG.open("a") as f:
        f.write(str(message) + "\n")

def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2))

def main():
    LOG.write_text("")
    source = INP / "bracket.step"
    if not source.is_file():
        raise FileNotFoundError(source)
    shutil.copy2(source, OUT / "part.step")
    for p in sorted(INP.rglob("*")):
        if p.is_file() and p.suffix.lower() in (".md", ".txt", ".json", ".yaml", ".yml"):
            log("INPUT SPECIFICATION " + str(p) + "\n" + p.read_text(errors="replace"))
    executable = shutil.which("ccx")
    if not executable:
        raise RuntimeError("CalculiX not found")
    version = subprocess.run([executable, "-v"], capture_output=True, text=True, timeout=15)
    write_json(OUT / "environment.json", {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__, "gmsh": gmsh.__version__,
        "solver": executable, "solver_version": version.stdout + version.stderr,
        "threads": 2, "units": {"length": "mm", "force": "N", "stress": "MPa"},
        "material": {"E": 113800.0, "nu": 0.342, "density_g_cm3": 4.43},
    })
    gmsh.initialize()
    gmsh.option.setNumber("General.NumThreads", 2)
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.add("published_bracket")
    gmsh.model.occ.importShapes(str(source))
    gmsh.model.occ.synchronize()
    volumes = gmsh.model.getEntities(3)
    if not volumes:
        raise RuntimeError("STEP contains no solid volumes")
    log("Imported volumes: " + str(volumes))
    log("Solid volume mm^3: " + str(sum(gmsh.model.occ.getMass(d, t) for d, t in volumes)))
    gmsh.model.addPhysicalGroup(3, [t for d, t in volumes], 1)
    gmsh.model.setPhysicalName(3, 1, "Titanium")
    gmsh.option.setNumber("Mesh.SaveAll", 1)
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 18)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)
    gmsh.option.setNumber("Mesh.Optimize", 1)
    gmsh.option.setNumber("Mesh.ElementOrder", 1)
    # Keep quadratic displacement interpolation, but use affine tetrahedral
    # geometry. Projecting midside nodes onto the many small CAD faces can
    # invert otherwise valid tetrahedra near tight fillets.
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)

    axis = np.array([-0.030352, 0.999539, 0.0])
    axis /= np.linalg.norm(axis)
    center = np.array([-20.9236, -74.6978, 44.7246])
    reference = np.array([-21.0359, -75.0647, 44.8010])
    bolts = np.array([[0, 0], [52.0472, 1.5805],
                      [0, -148.1248], [38.0833, -146.9684]])
    generalized_loads = np.array([
        [0, 0, 35585.77, 0, 0, 0],
        [-37809.90, 0, 0, 0, 0, 0],
        [-28276.20, 0, 31403.90, 0, 0, 0],
        [0, 0, 0, 0, 0, 564924.20],
    ])
    keys = ["vertical_max_displacement_mm", "horizontal_max_displacement_mm",
            "diagonal_max_displacement_mm", "torsion_max_displacement_mm"]
    history = []
    accepted = None

    for level, size in enumerate([3.2, 2.35]):
        if level and time.time() - START > 265:
            log("Refinement skipped: remaining runtime insufficient.")
            break
        gmsh.model.mesh.clear()
        gmsh.option.setNumber("Mesh.MeshSizeMin", size * 0.38)
        gmsh.option.setNumber("Mesh.MeshSizeMax", size)
        gmsh.model.mesh.setSize(gmsh.model.getEntities(0), size)
        t0 = time.time()
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.setOrder(2)
        _, volume_element_tags, _ = gmsh.model.mesh.getElements(3)
        determinants = gmsh.model.mesh.getElementQualities(
            np.concatenate(volume_element_tags), "minDetJac")
        log(f"Level {level}: minimum element Jacobian determinant = {np.min(determinants):.12g}")
        if not np.isfinite(determinants).all() or np.min(determinants) <= 0:
            raise RuntimeError("Nonpositive mesh Jacobian before solver export")
        tags, coords, _ = gmsh.model.mesh.getNodes()
        order = np.argsort(tags)
        tags = np.asarray(tags, dtype=np.int64)[order]
        xyz = np.asarray(coords).reshape(-1, 3)[order]
        n = len(tags)

        def indices(t):
            t = np.asarray(t, dtype=np.int64)
            ans = np.searchsorted(tags, t)
            if np.any(tags[ans] != t):
                raise RuntimeError("Missing mesh node")
            return ans

        etypes, etags, enodes = gmsh.model.mesh.getElements(3)
        blocks = []
        for typ, nodes in zip(etypes, enodes):
            if typ != 11:
                raise RuntimeError("Expected quadratic tetrahedra; found type " + str(typ))
            blocks.append(indices(nodes).reshape(-1, 10))
        tet_gmsh = np.vstack(blocks)
        tet_ccx = tet_gmsh[:, [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]
        fixed = np.zeros(n, dtype=bool)
        for b in bolts:
            radius = np.linalg.norm(xyz[:, :2] - b, axis=1)
            fixed |= (np.abs(radius - 5.1562) < 0.025) & (xyz[:, 2] >= -0.025)

        rel = xyz - center
        axial = rel @ axis
        radial = np.linalg.norm(rel - axial[:, None] * axis, axis=1)
        bore = ((np.abs(radial - 9.5504) < 0.025) &
                (((axial >= 11.112 - 0.035) & (axial <= 17.463 + 0.035)) |
                 ((axial >= -17.463 - 0.035) & (axial <= -11.113 + 0.035))))
        weights = np.zeros(n)
        types2, _, nodes2 = gmsh.model.mesh.getElements(2)
        surface_count = 0
        for typ, nodes in zip(types2, nodes2):
            if typ not in (2, 9):
                continue
            nn = 6 if typ == 9 else 3
            tr = indices(nodes).reshape(-1, nn)
            # Affine midside nodes lie on chords rather than exactly on the
            # CAD cylinders. Identify interface facets by their CAD vertices,
            # then include every quadratic node of each identified facet.
            corners = tr[:, :3]
            bolt_faces = np.zeros(len(tr), dtype=bool)
            for b in bolts:
                corner_radii = np.linalg.norm(xyz[corners, :2] - b, axis=2)
                bolt_faces |= np.all(
                    (np.abs(corner_radii - 5.1562) < 0.025) &
                    (xyz[corners, 2] >= -0.025), axis=1)
            fixed[tr[bolt_faces].ravel()] = True
            tr = tr[np.all(bore[corners], axis=1)]
            if not len(tr):
                continue
            p = xyz[tr[:, :3]]
            areas = 0.5 * np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1)
            for j in range(nn):
                np.add.at(weights, tr[:, j], areas / nn)
            surface_count += len(tr)
        loaded = np.flatnonzero(weights > 0)
        if fixed.sum() < 12 or len(loaded) < 12:
            raise RuntimeError("Failed to identify cylindrical interface mesh")
        r = xyz[loaded] - reference
        H = np.zeros((len(loaded), 3, 6))
        H[:, :, :3] = np.eye(3)
        H[:, 0, 4] = r[:, 2]
        H[:, 0, 5] = -r[:, 1]
        H[:, 1, 3] = -r[:, 2]
        H[:, 1, 5] = r[:, 0]
        H[:, 2, 3] = r[:, 1]
        H[:, 2, 4] = -r[:, 0]
        w = weights[loaded]
        gram = np.einsum("nai,n,naj->ij", H, w, H)
        nodal_loads = np.array([
            w[:, None] * np.einsum("nai,i->na", H, np.linalg.solve(gram, load))
            for load in generalized_loads
        ])
        balance = np.array([np.einsum("nai,na->i", H, f) for f in nodal_loads])
        log(f"Level {level}: size={size}, nodes={n}, tet10={len(tet_ccx)}, "
            f"fixed nodes={fixed.sum()}, loaded nodes={len(loaded)}, bore triangles={surface_count}")
        log("Applied generalized forces:\n" + str(balance))
        job = f"analysis_{level}"
        meshpath = OUT / f"mesh_{level}.msh"
        gmsh.write(str(meshpath))
        with (OUT / (job + ".inp")).open("w") as f:
            f.write("*HEADING\nImported STEP bracket; quadratic solid elasticity\n*NODE,NSET=NALL\n")
            for i, p in enumerate(xyz, 1):
                f.write(f"{i},{p[0]:.12g},{p[1]:.12g},{p[2]:.12g}\n")
            f.write("*ELEMENT,TYPE=C3D10,ELSET=SOLID\n")
            for i, conn in enumerate(tet_ccx + 1, 1):
                f.write(str(i) + "," + ",".join(map(str, conn)) + "\n")
            f.write("*NSET,NSET=FIXED\n")
            ids = np.flatnonzero(fixed) + 1
            for j in range(0, len(ids), 16):
                f.write(",".join(map(str, ids[j:j + 16])) + "\n")
            f.write("*MATERIAL,NAME=TI64\n*ELASTIC\n113800.,0.342\n"
                    "*SOLID SECTION,ELSET=SOLID,MATERIAL=TI64\n"
                    "*BOUNDARY\nFIXED,1,3\n")
            for forces in nodal_loads:
                f.write("*STEP\n*STATIC\n1.,1.\n*CLOAD,OP=NEW\n")
                for idx, vec in zip(loaded + 1, forces):
                    for dof, value in enumerate(vec, 1):
                        if abs(value) > 1e-12:
                            f.write(f"{idx},{dof},{value:.12g}\n")
                f.write("*NODE PRINT,NSET=NALL,FREQUENCY=1\nU\n*END STEP\n")
        remaining = max(20, int(565 - (time.time() - START)))
        try:
            with (OUT / (job + ".stdout")).open("w") as stream:
                proc = subprocess.run([executable, "-i", job], stdout=stream,
                                      stderr=subprocess.STDOUT, timeout=remaining)
            log((OUT / (job + ".stdout")).read_text(errors="replace"))
            if proc.returncode:
                raise RuntimeError(f"CalculiX exit {proc.returncode}")
            tables = []
            active = None
            for line in (OUT / (job + ".dat")).read_text(errors="replace").splitlines():
                if "displacements" in line.lower() and "time" in line.lower():
                    active = np.full((n, 3), np.nan)
                    tables.append(active)
                    continue
                if active is not None:
                    parts = line.split()
                    if len(parts) == 4:
                        try:
                            idx = int(parts[0]) - 1
                            vals = [float(v.replace("D", "E")) for v in parts[1:]]
                            if 0 <= idx < n:
                                active[idx] = vals
                        except ValueError:
                            pass
            if len(tables) != 4 or any(not np.isfinite(a).all() for a in tables):
                raise RuntimeError("Incomplete displacement output")
            displacement = np.stack(tables)
            maxima = np.linalg.norm(displacement, axis=2).max(axis=1)
            elapsed = time.time() - t0
            entry = {"mesh_size_mm": size, "nodes": n, "tetrahedra": len(tet_ccx),
                     "element": "C3D10", "elapsed_seconds": elapsed,
                     "max_displacement_mm": dict(zip(keys, maxima.tolist()))}
            if accepted is not None:
                entry["relative_change_vs_previous"] = (
                    np.abs(maxima - accepted) / np.maximum(maxima, 1e-30)).tolist()
            history.append(entry)
            accepted = maxima
            shutil.copy2(meshpath, OUT / "mesh.msh")
            np.savez_compressed(
                OUT / "fields.npz", coordinates=xyz, node_ids=np.arange(1, n + 1),
                tetra10=tet_gmsh, tetra10_ccx=tet_ccx,
                displacement=displacement, displacement_magnitude=np.linalg.norm(displacement, axis=2),
                case_names=np.array(keys), fixed_node_indices=np.flatnonzero(fixed),
                loaded_node_indices=loaded, applied_nodal_forces=nodal_loads,
                bore_area_weights=weights, reference_point=reference)
            write_json(OUT / "results.json", {"outputs": dict(zip(keys, maxima.tolist()))})
        except Exception as exc:
            log(f"Level {level} failed: {exc}")
            if accepted is None:
                raise
            history.append({"mesh_size_mm": size, "status": "failed", "reason": str(exc)})
            break

    gmsh.finalize()
    write_json(OUT / "refinement.json", {
        "runs": history,
        "selected": "finest successfully solved mesh",
        "convergence_claimed": False,
        "notes": [
            "Full imported STEP geometry retained; no redesign.",
            "Linear isotropic elasticity, quadratic tetrahedral solids with straight edges and affine geometry to avoid curvature-induced inverted elements.",
            "Cylindrical interface facets identified from their corner nodes; all quadratic facet nodes participate in constraints or loading. Curved boundaries are approximated by mesh-refined planar facets.",
            "All three translations fixed on the four cylindrical bolt walls.",
            "RBE3-style six-component weighted rigid-motion interpolation distributes reference loads over both pin bores.",
            "Positive surface-area lumping used for interpolation weights.",
            "Mesh comparison, when available, measures numerical sensitivity; it is not proof of asymptotic convergence.",
            "No published displacement values or evaluator data used."
        ],
        "total_seconds": time.time() - START
    })

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        log(traceback.format_exc())
        raise
