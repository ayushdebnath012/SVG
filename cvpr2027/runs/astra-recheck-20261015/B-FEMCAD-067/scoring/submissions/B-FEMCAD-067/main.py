import os
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

import sys
import json
import time
import hashlib
import platform
from pathlib import Path

import numpy as np
import scipy
import scipy.sparse.linalg
import cadquery as cq
import gmsh
import meshio
import skfem
from skfem import MeshTri, Basis, FacetBasis, ElementTriP1, BilinearForm, LinearForm, asm
from skfem.helpers import dot, grad


def main():
    out = Path(os.environ.get("CADFEM_OUTPUT_DIR", ".")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    log = open(out / "solver.log", "w", buffering=1)

    def report(s):
        print(s, flush=True)
        log.write(str(s) + "\n")

    start = time.time()
    inputs = Path(os.environ.get("CADFEM_INPUT_DIR", ".")).resolve()
    inventory = []
    if inputs.exists():
        for p in sorted(inputs.rglob("*")):
            if not p.is_file() or out in p.parents and out != inputs:
                continue
            if p.suffix.lower() in (".gif", ".png", ".jpg", ".txt", ".md", ".json", ".yaml", ".yml", ".pdf"):
                data = p.read_bytes()
                inventory.append({
                    "name": str(p.relative_to(inputs)),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data)
                })
                if p.suffix.lower() in (".txt", ".md", ".json", ".yaml", ".yml"):
                    report("INPUT FILE " + str(p) + "\n" + data.decode("utf-8", errors="replace"))

    report("CAD units mm; axisymmetric conduction calculation in SI units.")
    report("Single isotropic solid; k=52 W/(m K); bore-band inward heat flux=500000 W/m^2.")
    report("Dirichlet T=273.15 K on both ends and outer cylinder; other bore faces insulated.")

    # Keeping the collinear profile edges is intentional: their revolutions
    # create three distinct bore faces without introducing material interfaces.
    profile = [(20., 0.), (100., 0.), (100., 140.),
               (20., 140.), (20., 100.), (20., 40.)]
    part = (cq.Workplane("XZ")
            .polyline(profile).close()
            .revolve(360., (0., 0.), (0., 1.), clean=False))
    shape = part.val()
    if len(shape.Solids()) != 1 or not shape.isValid():
        raise RuntimeError("Invalid CAD solid")
    cq.exporters.export(part, str(out / "part.step"))
    report("CAD volume (mm^3): %.12g; faces: %d" % (shape.Volume(), len(shape.Faces())))

    # Independently inspect the exported STEP and retain its face inventory.
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("exported_CAD")
    gmsh.model.occ.importShapes(str(out / "part.step"))
    gmsh.model.occ.synchronize()
    face_info = []
    for dim, tag in gmsh.model.getEntities(2):
        face_info.append({
            "tag": tag,
            "type": gmsh.model.getType(dim, tag),
            "bbox_mm": list(gmsh.model.getBoundingBox(dim, tag)),
            "area_mm2": gmsh.model.occ.getMass(dim, tag)
        })
    report("Exported STEP face inventory: " + json.dumps(face_info))
    if len(gmsh.model.getEntities(3)) != 1:
        raise RuntimeError("Exported STEP must contain one solid")
    gmsh.finalize()

    k = 52.
    q = 5.e5
    tref = 273.15

    @BilinearForm
    def conduction(u, v, w):
        return 2. * np.pi * k * w.x[0] * dot(grad(u), grad(v))

    @LinearForm
    def heating(v, w):
        return 2. * np.pi * q * w.x[0] * v

    history = []
    converged = False
    previous = None

    for h_mm in (2., 1., 0.5, 0.25):
        tic = time.time()
        nr = int(round(80. / h_mm))
        nz = int(round(140. / h_mm))
        mesh = MeshTri.init_tensor(
            np.linspace(.020, .100, nr + 1),
            np.linspace(0., .140, nz + 1))
        basis = Basis(mesh, ElementTriP1(), intorder=3)

        bore_heat = mesh.facets_satisfying(
            lambda x: np.isclose(x[0], .020, atol=1.e-12) &
            (x[1] > .040 - 1.e-12) & (x[1] < .100 + 1.e-12),
            boundaries_only=True)
        fbasis = FacetBasis(mesh, ElementTriP1(), facets=bore_heat, intorder=3)
        A = asm(conduction, basis).tocsr()
        b = asm(heating, fbasis)
        fixed = np.flatnonzero(
            np.isclose(mesh.p[0], .100, atol=1.e-12) |
            np.isclose(mesh.p[1], 0., atol=1.e-12) |
            np.isclose(mesh.p[1], .140, atol=1.e-12))
        free = np.setdiff1d(np.arange(basis.N), fixed)
        rise = np.zeros(basis.N)
        rise[free] = scipy.sparse.linalg.spsolve(A[free][:, free].tocsc(), b[free])
        temperature = tref + rise
        probe = (basis.probes(np.array([[.040], [.040]])) @ temperature).item()
        residual = A @ rise - b
        input_power = float(b.sum())
        output_power = float(-residual[fixed].sum())
        rel = None if previous is None else abs(probe - previous) / abs(probe)
        rel_rise = None if previous is None else abs(probe - previous) / abs(probe - tref)
        record = {
            "h_mm": h_mm,
            "nodes": int(basis.N),
            "triangles": int(mesh.t.shape[1]),
            "T_probe_K": probe,
            "relative_change": rel,
            "relative_change_temperature_rise": rel_rise,
            "input_heat_W": input_power,
            "dirichlet_heat_out_W": output_power,
            "relative_energy_imbalance": abs(input_power - output_power) / input_power,
            "free_residual_norm": float(np.linalg.norm(residual[free])),
            "seconds": time.time() - tic
        }
        history.append(record)
        report(json.dumps(record))
        # Check the requested temperature and, more strictly, its rise.
        if len(history) >= 3 and rel < .01 and rel_rise < .01:
            converged = True
            break
        previous = probe

    if not converged:
        report("WARNING: refinement limit reached; see actual convergence history.")

    # Computational mesh: meridional r-z section, embedded as (r,z,0).
    # Millimetres in mesh.msh, matching the dimensional scale of the STEP.
    points_mm = np.column_stack((mesh.p.T * 1000., np.zeros(basis.N)))
    boundary_facets = mesh.boundary_facets()
    lines = mesh.facets[:, boundary_facets].T
    mid = mesh.p[:, lines].mean(axis=2)
    tags = np.zeros(len(lines), dtype=np.int32)
    for i, (r, z) in enumerate(mid.T):
        if abs(z) < 1.e-10:
            tags[i] = 11
        elif abs(z - .140) < 1.e-10:
            tags[i] = 12
        elif abs(r - .100) < 1.e-10:
            tags[i] = 13
        elif .040 < z < .100:
            tags[i] = 14
        else:
            tags[i] = 15
    tri_tags = np.ones(mesh.t.shape[1], dtype=np.int32)
    exported = meshio.Mesh(
        points_mm,
        [("triangle", mesh.t.T), ("line", lines)],
        point_data={"T_K": temperature},
        cell_data={
            "gmsh:physical": [tri_tags, tags],
            "gmsh:geometrical": [tri_tags, tags]
        },
        field_data={
            "solid_axisymmetric": np.array([1, 2]),
            "bottom_T": np.array([11, 1]),
            "top_T": np.array([12, 1]),
            "outer_T": np.array([13, 1]),
            "bore_heat_flux": np.array([14, 1]),
            "bore_insulated": np.array([15, 1])
        })
    meshio.write(out / "mesh.msh", exported, file_format="gmsh22", binary=False)

    interp = basis.interpolate(temperature)
    flux = -k * interp.grad.mean(axis=2).T
    np.savez_compressed(
        out / "fields.npz",
        points=points_mm, points_mm=points_mm,
        rz_m=mesh.p.T, triangles=mesh.t.T,
        temperature=temperature, T_K=temperature,
        heat_flux_rz_W_m2=flux,
        boundary_lines=lines, boundary_tags=tags,
        fixed_nodes=fixed,
        probe_rz_m=np.array([.040, .040]),
        T_probe_K=np.array(probe),
        coordinate_description=np.array("Axisymmetric meridional mesh: mesh coordinates (r_mm,z_mm,0); STEP global axis is z.")
    )

    (out / "results.json").write_text(json.dumps({"outputs": {"T_probe_K": probe}}, indent=2))
    (out / "refinement.json").write_text(json.dumps({
        "method": "Axisymmetric P1 triangular FEM using scikit-fem; exact 2*pi*r weak-form weight",
        "converged": converged,
        "criterion": "At least three meshes; successive probe temperature and temperature-rise changes both below 1%",
        "levels": history
    }, indent=2))
    (out / "environment.json").write_text(json.dumps({
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "cadquery": cq.__version__, "gmsh": gmsh.__version__,
        "meshio": meshio.__version__, "skfem": skfem.__version__,
        "input_files": inventory,
        "CAD_units": "mm", "FEM_assembly_units": "m,W,K",
        "mesh_representation": "2D axisymmetric meridional section (r,z,0), in mm; full 3D CAD in part.step",
        "STEP_faces": face_info,
        "elapsed_seconds": time.time() - start
    }, indent=2))
    report("Completed in %.3f seconds." % (time.time() - start))
    log.close()


if __name__ == "__main__":
    main()
