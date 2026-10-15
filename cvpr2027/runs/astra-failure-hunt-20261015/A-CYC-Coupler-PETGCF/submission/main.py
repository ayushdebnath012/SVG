import os
import sys
import json
import shutil
import time
import platform
import subprocess
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

import numpy as np
import scipy
from scipy.optimize import linear_sum_assignment
import gmsh


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False))


def main():
    started = time.time()
    inp = Path(os.environ.get("CADFEM_INPUT_DIR", ".")).resolve()
    out = Path(os.environ.get("CADFEM_OUTPUT_DIR", ".")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if inp / "part.step" != out / "part.step":
        shutil.copy2(inp / "part.step", out / "part.step")
    try:
        if Path(__file__).resolve() != out / "main.py":
            shutil.copy2(__file__, out / "main.py")
    except Exception:
        pass
    spec = json.loads((inp / "faces.json").read_text())
    shutil.copy2(inp / "faces.json", out / "geometry_faces.json") if inp / "faces.json" != out / "geometry_faces.json" else None
    readmes = {}
    for folder in (inp, Path.cwd()):
        for p in folder.glob("*README*"):
            if p.is_file():
                readmes[str(p)] = p.read_text(errors="replace")
    write_json(out / "environment.json", {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "gmsh": gmsh.__version__,
        "ccx": shutil.which("ccx"),
        "threads": 2,
        "units": {"length": "mm", "force": "N", "stress": "MPa"},
        "material": {"E_MPa": 3000.0, "poisson_ratio": 0.36},
        "readme_files_read": readmes,
    })
    log = open(out / "solver.log", "w", buffering=1)

    def report(s):
        log.write(str(s) + "\n")
        print(s, flush=True)

    records = []
    successful = None
    for level, h in enumerate((2.0, 1.4)):
        if level and time.time() - started > 330:
            report("Refinement skipped because of remaining runtime.")
            break
        work = out / ("run_%d" % level)
        work.mkdir(exist_ok=True)
        gmsh.initialize()
        try:
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.option.setNumber("General.NumThreads", 2)
            gmsh.model.add("coupler")
            gmsh.model.occ.importShapes(str(inp / "part.step"))
            gmsh.model.occ.synchronize()
            volumes = gmsh.model.getEntities(3)
            if len(volumes) != 1:
                raise RuntimeError("Expected exactly one solid.")
            entities = gmsh.model.getEntities(2)
            faces = spec["faces"]
            if len(faces) != len(entities):
                raise RuntimeError("Imported face count differs from specification.")
            areas = np.array([gmsh.model.occ.getMass(2, t) for _, t in entities])
            centers = np.array([gmsh.model.occ.getCenterOfMass(2, t) for _, t in entities])
            costs = np.zeros((len(faces), len(entities)))
            for i, f in enumerate(faces):
                c = np.array(f["centroid_mm"])
                a = float(f["area_mm2"])
                costs[i] = np.linalg.norm(centers - c, axis=1) + np.abs(areas - a) / max(1.0, np.sqrt(a))
            rows, cols = linear_sum_assignment(costs)
            mapping = {}
            match_report = []
            for i, j in zip(rows, cols):
                f = faces[i]
                mapping[int(f["face_index"])] = entities[j][1]
                match_report.append({
                    "face_index": int(f["face_index"]),
                    "gmsh_surface": int(entities[j][1]),
                    "area_mm2": float(areas[j]),
                    "centroid_mm": centers[j].tolist(),
                    "match_cost": float(costs[i, j]),
                })
                if costs[i, j] > 0.15:
                    raise RuntimeError("Ambiguous geometric face match: " + str(match_report[-1]))
            write_json(work / "face_matching.json", match_report)
            report("Level %d: geometric face matching complete; solid volume %.8g mm^3" %
                   (level, gmsh.model.occ.getMass(3, volumes[0][1])))
            gmsh.option.setNumber("Mesh.MeshSizeMax", h)
            gmsh.option.setNumber("Mesh.MeshSizeMin", h * 0.12)
            gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 14)
            gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)
            gmsh.option.setNumber("Mesh.Algorithm3D", 1)
            gmsh.option.setNumber("Mesh.ElementOrder", 2)
            gmsh.option.setNumber("Mesh.SecondOrderLinear", 0)
            gmsh.option.setNumber("Mesh.Optimize", 1)
            gmsh.model.mesh.generate(3)
            gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
            gmsh.write(str(work / "mesh.msh"))
            tags, xyz, _ = gmsh.model.mesh.getNodes()
            order = np.argsort(tags)
            tags = np.asarray(tags, dtype=np.int64)[order]
            xyz = np.asarray(xyz).reshape(-1, 3)[order]
            n = len(tags)

            def indices(t):
                t = np.asarray(t, dtype=np.int64)
                ix = np.searchsorted(tags, t)
                if not np.all(tags[ix] == t):
                    raise RuntimeError("Unknown mesh node.")
                return ix

            tet_type = 11
            etags, enodes = gmsh.model.mesh.getElementsByType(tet_type)
            tets_gmsh = indices(np.asarray(enodes).reshape(-1, 10))
            if len(etags) == 0:
                raise RuntimeError("No quadratic tetrahedra.")
            props = gmsh.model.mesh.getElementProperties(tet_type)
            loc = np.array(props[4]).reshape(-1, 3)
            edge_pairs = [(0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)]
            permutation = list(range(4))
            for a, b in edge_pairs:
                permutation.append(int(np.argmin(np.linalg.norm(loc - (loc[a] + loc[b]) / 2, axis=1))))
            tets = tets_gmsh[:, permutation]
            fixed = []
            for fi in (5, 6):
                nt, _, _ = gmsh.model.mesh.getNodes(2, mapping[fi], includeBoundary=True)
                fixed.extend(indices(nt).tolist())
            fixed = np.unique(fixed)
            _, tri_nodes = gmsh.model.mesh.getElementsByType(9, mapping[14])
            triangles = indices(np.asarray(tri_nodes).reshape(-1, 6))
            if not len(triangles):
                raise RuntimeError("Loaded surface has no quadratic triangles.")

            # Seven-point integration on the quadratic isoparametric triangles.
            quadrature = [(1 / 3, 1 / 3, 0.225)]
            for a, b, weight in [
                (0.059715871789770, 0.470142064105115, 0.132394152788506),
                (0.797426985353087, 0.101286507323456, 0.125939180544827),
            ]:
                quadrature.extend([(b, b, weight), (a, b, weight), (b, a, weight)])
            nodal_area = np.zeros(n)
            p = xyz[triangles]
            surface_area = 0.0
            for r, s, w in quadrature:
                l = 1 - r - s
                shape = np.array([l * (2*l-1), r*(2*r-1), s*(2*s-1),
                                  4*l*r, 4*r*s, 4*s*l])
                dr = np.array([1-4*l, 4*r-1, 0, 4*(l-r), 4*s, -4*s])
                ds = np.array([1-4*l, 0, 4*s-1, -4*r, 4*r, 4*(l-s)])
                jac = np.linalg.norm(np.cross(np.einsum("tij,i->tj", p, dr),
                                             np.einsum("tij,i->tj", p, ds)), axis=1)
                da = 0.5*w*jac
                surface_area += float(da.sum())
                np.add.at(nodal_area, triangles.ravel(), (da[:, None]*shape).ravel())
            forces = nodal_area * (100.052 / surface_area)
            report("Level %d: %d nodes, %d C3D10 elements, load area %.9g mm^2, force %.9g N" %
                   (level, n, len(tets), surface_area, forces.sum()))
        finally:
            gmsh.finalize()

        deck = work / "analysis.inp"
        with open(deck, "w") as f:
            f.write("*HEADING\nQuadratic solid linear elastic coupler analysis\n*NODE,NSET=ALLNODES\n")
            for i, p in enumerate(xyz, 1):
                f.write("%d,%.12g,%.12g,%.12g\n" % (i, *p))
            f.write("*ELEMENT,TYPE=C3D10,ELSET=SOLID\n")
            for i, conn in enumerate(tets, 1):
                f.write(str(i) + "," + ",".join(map(str, conn + 1)) + "\n")
            f.write("*MATERIAL,NAME=PETGCF\n*ELASTIC\n3000.,0.36\n")
            f.write("*SOLID SECTION,ELSET=SOLID,MATERIAL=PETGCF\n")
            f.write("*NSET,NSET=FIXED\n")
            for start in range(0, len(fixed), 16):
                f.write(",".join(map(str, fixed[start:start+16] + 1)) + "\n")
            f.write("*BOUNDARY\nFIXED,1,3,0.\n*STEP\n*STATIC\n*CLOAD\n")
            for i in np.flatnonzero(np.abs(forces) > 1e-16):
                f.write("%d,1,%.14g\n" % (i+1, forces[i]))
            f.write("*NODE PRINT,NSET=ALLNODES\nU\n*NODE FILE\nU\n*END STEP\n")
        timeout = min(235, max(30, int(560 - (time.time()-started))))
        try:
            proc = subprocess.run(["ccx", "-i", "analysis"], cwd=work,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, timeout=timeout)
            (work / "ccx.log").write_text(proc.stdout)
            report(proc.stdout)
            if proc.returncode != 0:
                raise RuntimeError("CalculiX failed with exit code %d" % proc.returncode)
            u = np.full((n, 3), np.nan)
            active = False
            for line in (work / "analysis.dat").read_text().splitlines():
                if "displacements" in line.lower():
                    active = True
                    continue
                if active:
                    fields = line.split()
                    if len(fields) == 4:
                        try:
                            node = int(fields[0])
                            values = [float(v.replace("D", "E")) for v in fields[1:]]
                        except ValueError:
                            continue
                        if 1 <= node <= n:
                            u[node - 1] = values
            if not np.isfinite(u).all():
                raise RuntimeError("Incomplete nodal displacement output.")
            magnitude = np.linalg.norm(u, axis=1)
            maximum = float(magnitude.max())
            record = {
                "level": level, "max_element_size_mm": h,
                "nodes": n, "elements": len(tets),
                "element_type": "C3D10",
                "max_displacement_mm": maximum,
                "loaded_mesh_area_mm2": surface_area,
                "total_applied_force_N": [float(forces.sum()), 0.0, 0.0],
                "elapsed_seconds": time.time()-started,
                "status": "completed",
            }
            if successful is not None:
                record["relative_change_from_previous"] = abs(maximum-successful) / maximum
            records.append(record)
            successful = maximum
            shutil.copy2(work / "mesh.msh", out / "mesh.msh")
            force_vectors = np.zeros((n, 3))
            force_vectors[:, 0] = forces
            np.savez_compressed(out / "fields.npz",
                                points=xyz, nodes=xyz, node_ids=tags,
                                cells=tets, elements=tets,
                                displacement=u, displacement_mm=u,
                                displacement_magnitude=magnitude,
                                fixed_nodes=fixed, applied_nodal_forces_N=force_vectors,
                                loaded_triangles=triangles,
                                connectivity_index_base=np.array(0))
            write_json(out / "results.json", {"outputs": {"max_displacement_mm": maximum}})
            report("Maximum displacement: %.10g mm" % maximum)
        except Exception as exc:
            report("Run failure: " + repr(exc))
            records.append({"level": level, "max_element_size_mm": h,
                            "status": "failed", "error": repr(exc)})
            if successful is None:
                raise
            break

    write_json(out / "refinement.json", {
        "method": "Independent quadratic tetrahedral meshes; geometrically matched CAD surfaces.",
        "runs": records,
        "reported_solution": "Finest successfully completed mesh.",
        "convergence_claim": "Observed mesh change only; no extrapolation or guaranteed error bound.",
        "traction_integration": "Seven-point quadratic surface integration, normalized to prescribed total force.",
        "elapsed_seconds": time.time()-started,
    })
    log.close()
    if successful is None:
        raise RuntimeError("No completed analysis.")


if __name__ == "__main__":
    main()
