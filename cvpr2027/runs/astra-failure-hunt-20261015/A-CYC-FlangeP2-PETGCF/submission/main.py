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
import scipy
from scipy.optimize import linear_sum_assignment
import gmsh


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2))


def triangle_weights(x):
    # Seven-point degree-five integration, including the curved geometry Jacobian.
    pts = [(1/3, 1/3, 0.225)]
    for a, b, w in [
        (0.059715871789770, 0.470142064105115, 0.132394152788506),
        (0.797426985353087, 0.101286507323456, 0.125939180544827),
    ]:
        pts.extend([(b, b, w), (a, b, w), (b, a, w)])
    weights = np.zeros(6)
    for r, s, w in pts:
        l = 1-r-s
        n = np.array([l*(2*l-1), r*(2*r-1), s*(2*s-1),
                      4*l*r, 4*r*s, 4*s*l])
        dr = np.array([1-4*l, 4*r-1, 0, 4*(l-r), 4*s, -4*s])
        ds = np.array([1-4*l, 0, 4*s-1, -4*r, 4*r, 4*(l-s)])
        jac = np.linalg.norm(np.cross(dr @ x, ds @ x))
        weights += 0.5*w*jac*n
    return weights


def read_displacements(path, node_ids):
    lines = Path(path).read_text(errors="replace").splitlines()
    found = {}
    active = False
    for line in lines:
        low = line.lower()
        if "displacements" in low and ("node" in low or "set" in low):
            active = True
            continue
        if active:
            bits = line.split()
            if len(bits) == 4:
                try:
                    tag = int(bits[0])
                    val = [float(t.replace("D", "E")) for t in bits[1:]]
                    found[tag] = val
                except ValueError:
                    pass
    missing = [int(i) for i in node_ids if int(i) not in found]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} nodal displacements in {path}")
    return np.array([found[int(i)] for i in node_ids])


def main():
    start = time.time()
    inp = Path(os.environ.get("CADFEM_INPUT_DIR", ".")).resolve()
    out = Path(os.environ.get("CADFEM_OUTPUT_DIR", "output")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(inp / "part.step", out / "part.step")
    specification = json.loads((inp / "faces.json").read_text())
    faces = specification["faces"]
    shutil.copy2(inp / "faces.json", out / "faces.json")
    try:
        if Path(__file__).resolve() != out / "main.py":
            shutil.copy2(__file__, out / "main.py")
    except Exception:
        pass

    logpath = out / "solver.log"

    def log(text):
        with logpath.open("a") as f:
            f.write(str(text) + "\n")

    logpath.write_text("PETG-CF linear static FEM; units N, mm, MPa.\n")
    for directory in [inp, Path.cwd()]:
        for p in directory.glob("*README*"):
            if p.is_file():
                log(f"README {p}:\n{p.read_text(errors='replace')}")
    env = {
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "gmsh": gmsh.__version__, "ccx": shutil.which("ccx"),
        "threads": 2,
        "material": {"E_MPa": 3000.0, "poisson_ratio": 0.36},
    }
    for pkg in ["cadquery", "meshio", "scikit-fem"]:
        try:
            env[pkg] = importlib.metadata.version(pkg)
        except Exception:
            pass
    dump(out / "environment.json", env)

    gmsh.initialize()
    gmsh.option.setNumber("General.NumThreads", 2)
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.add("P2")
    gmsh.model.occ.importShapes(str(inp / "part.step"))
    gmsh.model.occ.synchronize()
    surfaces = gmsh.model.getEntities(2)
    cost = np.zeros((len(faces), len(surfaces)))
    for i, f in enumerate(faces):
        for j, (_, tag) in enumerate(surfaces):
            area = gmsh.model.occ.getMass(2, tag)
            com = np.array(gmsh.model.occ.getCenterOfMass(2, tag))
            cost[i, j] = (
                np.linalg.norm(com - np.array(f["centroid_mm"])) +
                5 * abs(np.log(area / f["area_mm2"]))
            )
    rows, cols = linear_sum_assignment(cost)
    mapping = {int(faces[i]["face_index"]): surfaces[j][1] for i, j in zip(rows, cols)}
    matches = []
    for i, j in zip(rows, cols):
        matches.append({"face_index": int(faces[i]["face_index"]),
                        "gmsh_surface_tag": surfaces[j][1],
                        "matching_cost": float(cost[i, j])})
    dump(out / "face_mapping.json", matches)
    if len(mapping) != len(faces) or max(cost[i, j] for i, j in zip(rows, cols)) > 0.2:
        raise RuntimeError("Geometric face matching failed validation")
    log("Face matching uses all supplied areas and centroids, not CAD face numbering.")
    support_tags = [mapping[17], mapping[23]]
    load_tags = [mapping[i] for i in range(1, 7)]
    gmsh.model.addPhysicalGroup(3, [t for _, t in gmsh.model.getEntities(3)], 100)
    gmsh.model.setPhysicalName(3, 100, "PETG_CF")
    for idx in [1, 2, 3, 4, 5, 6, 17, 23]:
        gmsh.model.addPhysicalGroup(2, [mapping[idx]], idx)
        gmsh.model.setPhysicalName(2, idx, f"face_{idx}")
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    gmsh.option.setNumber("Mesh.SaveAll", 1)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 0)
    gmsh.option.setNumber("Mesh.HighOrderOptimize", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 16)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)

    history = []
    successful = None
    for iteration, h in enumerate([3.0, 2.0]):
        work = out / f"run_{iteration+1}"
        work.mkdir(exist_ok=True)
        try:
            gmsh.model.mesh.clear()
            gmsh.option.setNumber("Mesh.MeshSizeMax", h)
            gmsh.option.setNumber("Mesh.MeshSizeMin", h * 0.30)
            gmsh.model.mesh.setSize(gmsh.model.getEntities(0), h)
            gmsh.model.mesh.generate(3)
            gmsh.write(str(work / "mesh.msh"))
            tags, xyz, _ = gmsh.model.mesh.getNodes()
            order = np.argsort(tags)
            tags = np.asarray(tags, dtype=np.int64)[order]
            xyz = np.asarray(xyz).reshape(-1, 3)[order]
            index = {int(t): i for i, t in enumerate(tags)}
            types, etags, enodes = gmsh.model.mesh.getElements(3)
            chunks = []
            for typ, conn in zip(types, enodes):
                if typ != 11:
                    raise RuntimeError(f"Unexpected volume element type {typ}")
                chunks.append(np.asarray(conn, dtype=np.int64).reshape(-1, 10))
            tet_gmsh = np.vstack(chunks)
            tet_ccx = tet_gmsh[:, [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]

            fixed = set()
            for surf in support_tags:
                ts, _, _ = gmsh.model.mesh.getNodes(2, surf, includeBoundary=True)
                fixed.update(int(t) for t in ts)
            nodal_area = np.zeros(len(tags))
            for surf in load_tags:
                typs, _, conns = gmsh.model.mesh.getElements(2, surf)
                for typ, conn in zip(typs, conns):
                    if typ != 9:
                        raise RuntimeError(f"Unexpected loaded surface element {typ}")
                    for tri in np.asarray(conn).reshape(-1, 6):
                        ids = np.array([index[int(t)] for t in tri])
                        np.add.at(nodal_area, ids, triangle_weights(xyz[ids]))
            loaded_area = float(nodal_area.sum())
            total_force = np.array([0., -69.086, -165.807])
            loads = nodal_area[:, None] * (total_force / loaded_area)
            log(f"Mesh h={h}: nodes={len(tags)}, tetrahedra={len(tet_ccx)}, "
                f"support nodes={len(fixed)}, loaded area={loaded_area}, "
                f"integrated force={loads.sum(axis=0).tolist()}")
            with (work / "job.inp").open("w") as f:
                f.write("*HEADING\nP2 PETG-CF quadratic tetrahedral linear static analysis\n*NODE,NSET=NALL\n")
                for tag, p in zip(tags, xyz):
                    f.write(f"{tag},{p[0]:.12g},{p[1]:.12g},{p[2]:.12g}\n")
                f.write("*ELEMENT,TYPE=C3D10,ELSET=SOLID\n")
                for eid, conn in enumerate(tet_ccx, 1):
                    f.write(str(eid) + "," + ",".join(map(str, conn)) + "\n")
                f.write("*MATERIAL,NAME=PETGCF\n*ELASTIC\n3000.,0.36\n")
                f.write("*SOLID SECTION,ELSET=SOLID,MATERIAL=PETGCF\n")
                f.write("*NSET,NSET=FIXED\n")
                fs = sorted(fixed)
                for k in range(0, len(fs), 16):
                    f.write(",".join(map(str, fs[k:k+16])) + "\n")
                f.write("*BOUNDARY\nFIXED,1,3,0.\n*STEP\n*STATIC\n*CLOAD\n")
                for tag, force in zip(tags, loads):
                    for component in [1, 2]:
                        if abs(force[component]) > 1.e-14:
                            f.write(f"{tag},{component+1},{force[component]:.12g}\n")
                f.write("*NODE PRINT,NSET=NALL\nU\n*NODE FILE\nU\n*END STEP\n")
            remaining = 570 - (time.time() - start)
            if remaining < 30:
                raise RuntimeError("Insufficient remaining runtime for another solve")
            proc = subprocess.run(["ccx", "-i", "job"], cwd=work,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, timeout=remaining)
            (work / "ccx.log").write_text(proc.stdout)
            log(f"\n--- ccx h={h} ---\n{proc.stdout}")
            if proc.returncode != 0:
                raise RuntimeError(f"CalculiX returned {proc.returncode}")
            u = read_displacements(work / "job.dat", tags)
            mag = np.linalg.norm(u, axis=1)
            maximum = float(mag.max())
            cells = np.array([[index[int(t)] for t in row] for row in tet_gmsh])
            np.savez_compressed(
                work / "fields.npz", points=xyz, coordinates_mm=xyz,
                node_ids=tags, tetra10=cells, connectivity=cells,
                displacement=u, displacement_mm=u,
                displacement_magnitude_mm=mag,
                nodal_force_N=loads,
                fixed_node_indices=np.array([index[t] for t in sorted(fixed)]))
            entry = {"maximum_element_size_mm": h, "nodes": len(tags),
                     "quadratic_tetrahedra": len(tet_gmsh),
                     "max_displacement_mm": maximum,
                     "loaded_mesh_area_mm2": loaded_area, "status": "solved"}
            if history:
                entry["relative_change_from_previous"] = abs(
                    maximum - history[-1]["max_displacement_mm"]) / maximum
            history.append(entry)
            successful = work
            shutil.copy2(work / "mesh.msh", out / "mesh.msh")
            shutil.copy2(work / "fields.npz", out / "fields.npz")
            dump(out / "results.json", {"outputs": {"max_displacement_mm": maximum}})
        except Exception as exc:
            log(f"Mesh h={h} failed: {exc!r}")
            history.append({"maximum_element_size_mm": h, "status": "failed",
                            "error": repr(exc)})
            if successful is None:
                raise
            break
    gmsh.finalize()
    solved = [r for r in history if r["status"] == "solved"]
    dump(out / "refinement.json", {
        "method": "Independent quadratic tetrahedral meshes; geometric support matching; "
                  "consistent integrated uniform traction; CalculiX C3D10 static solves.",
        "runs": history,
        "selected_run": str(successful.name) if successful else None,
        "convergence_assessed": len(solved) >= 2,
        "note": "Reported value is from the finest successful mesh, not extrapolated. "
                "Two meshes measure sensitivity but do not establish asymptotic convergence.",
        "elapsed_seconds": time.time() - start,
    })
    log(f"Completed in {time.time()-start:.2f} s.")


if __name__ == "__main__":
    main()
