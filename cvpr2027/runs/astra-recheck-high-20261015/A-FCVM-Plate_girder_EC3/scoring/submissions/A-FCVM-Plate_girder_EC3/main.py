import os
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

import sys
import re
import json
import time
import shutil
import platform
import subprocess
import traceback
from pathlib import Path

import numpy as np
import gmsh

START = time.monotonic()
INPUT = Path(os.environ.get("CADFEM_INPUT_DIR", ".")).resolve()
OUTPUT = Path(os.environ.get("CADFEM_OUTPUT_DIR", ".")).resolve()
OUTPUT.mkdir(parents=True, exist_ok=True)
LOG = OUTPUT / "solver.log"


def log(s):
    with LOG.open("a") as f:
        f.write(str(s) + "\n")
    print(s, flush=True)


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False))


def remaining():
    return 580.0 - (time.monotonic() - START)


LOADS = {
    332: -166.15942, 334: -166.15942, 337: -166.15942,
    304: -166.15942, 306: -166.15942, 309: -166.15942,
    240: 30.204082 + 5.423191, 610: 30.204082 + 5.423191,
    286: 5.423191, 320: 5.423191, 348: 5.423191,
    376: 5.423191, 410: 5.423191, 478: 5.423191,
    512: 5.423191, 584: 5.423191, 585: 5.423191,
    586: 5.423191, 587: 5.423191, 588: 5.423191,
    591: 5.423191, 592: 5.423191, 593: 5.423191
}


def surface_records():
    result = {}
    for _, tag in gmsh.model.getEntities(2):
        result[tag] = (
            gmsh.model.occ.getMass(2, tag),
            np.asarray(gmsh.model.occ.getCenterOfMass(2, tag)),
            np.asarray(gmsh.model.getBoundingBox(2, tag))
        )
    return result


def find_original_surfaces(desc, records):
    selected = {}
    for index in LOADS:
        d = desc[index]
        area = float(d["area_mm2"])
        center = np.asarray(d["centroid_mm"], dtype=float)
        hits = [
            tag for tag, (a, c, b) in records.items()
            if abs(a - area) <= max(0.025, area * 2.e-6)
            and np.linalg.norm(c - center) < 0.08
        ]
        if not hits:
            raise RuntimeError("Cannot identify original loaded face %d" % index)
        selected[index] = records[hits[0]]
    return selected


def map_fragment_surfaces(original, records):
    result = {}
    for index, (area, center, box) in original.items():
        exact = [
            tag for tag, (a, c, b) in records.items()
            if abs(a - area) < max(0.025, area * 2.e-6)
            and np.linalg.norm(c - center) < 0.08
        ]
        if exact:
            candidates = [exact[0]]
        else:
            candidates = []
            for tag, (a, c, b) in records.items():
                if (np.all(b[:3] >= box[:3] - 0.002)
                        and np.all(b[3:] <= box[3:] + 0.002)
                        and abs(c[2] - center[2]) < 0.002
                        and abs(b[5] - b[2]) < 0.003):
                    candidates.append(tag)
        total = sum(records[t][0] for t in candidates)
        if abs(total - area) > max(0.05, area * 1.e-5):
            raise RuntimeError("Loaded-face area mismatch on face %d: %g / %g"
                               % (index, total, area))
        result[index] = candidates
    return result


def support_curves():
    groups = [[], []]
    for _, tag in gmsh.model.getEntities(1):
        b = np.asarray(gmsh.model.getBoundingBox(1, tag))
        for k, x in enumerate((50., 29950.)):
            if (abs(b[0] - x) < .002 and abs(b[3] - x) < .002
                    and abs(b[2] - 2100.) < .002
                    and abs(b[5] - 2100.) < .002
                    and b[1] >= 87.5 - .002 and b[4] <= 662.5 + .002
                    and b[4] - b[1] > .001):
                groups[k].append(tag)
    for k, curves in enumerate(groups):
        length = sum(gmsh.model.occ.getMass(1, t) for t in curves)
        if abs(length - 575.) > .01:
            raise RuntimeError("Support %d has incorrect scope: length %g" % (k, length))
    return groups


def cartesian_geometry():
    """Construct an exact cell decomposition only for rectilinear CAD."""
    for dim in (1, 2):
        for _, tag in gmsh.model.getEntities(dim):
            b = np.asarray(gmsh.model.getBoundingBox(dim, tag))
            if np.count_nonzero(b[3:] - b[:3] > 1.e-4) > dim:
                log("Non-rectilinear CAD: retaining conforming tetrahedral meshing.")
                return None
    vertices = np.asarray([
        gmsh.model.getValue(0, tag, [])
        for _, tag in gmsh.model.getEntities(0)
    ])
    additional = ([50., 29950.], [87.5, 367.5, 382.5, 662.5], [2100.])
    axes = [np.unique(np.round(np.r_[vertices[:, k], additional[k]], 6))
            for k in range(3)]
    centers = [(a[:-1] + a[1:]) / 2. for a in axes]
    occupied = np.zeros(tuple(len(a) - 1 for a in axes), dtype=bool)
    cad_volume = 0.
    for _, tag in gmsh.model.getEntities(3):
        b = np.asarray(gmsh.model.getBoundingBox(3, tag))
        lo = [int(np.argmin(abs(axes[k] - b[k]))) for k in range(3)]
        hi = [int(np.argmin(abs(axes[k] - b[k + 3]))) for k in range(3)]
        mass = gmsh.model.occ.getMass(3, tag)
        cad_volume += mass
        box_volume = np.prod([axes[k][hi[k]] - axes[k][lo[k]] for k in range(3)])
        sl = tuple(slice(lo[k], hi[k]) for k in range(3))
        if abs(box_volume - mass) < max(.001, mass * 1.e-8):
            occupied[sl] = True
        else:
            for offset in np.ndindex(*(hi[k] - lo[k] for k in range(3))):
                ijk = tuple(lo[k] + offset[k] for k in range(3))
                if occupied[ijk]:
                    continue
                point = [float(centers[k][ijk[k]]) for k in range(3)]
                occupied[ijk] = gmsh.model.isInside(3, tag, point) > 0
    dx, dy, dz = [np.diff(a) for a in axes]
    volume = float(np.sum(occupied * dx[:, None, None]
                          * dy[None, :, None] * dz[None, None, :]))
    if abs(volume - cad_volume) > max(.01, cad_volume * 1.e-8):
        raise RuntimeError("Cartesian CAD decomposition failed its exact volume check")
    from scipy.ndimage import label
    _, components = label(occupied)
    if components != 1:
        raise RuntimeError("CAD cell decomposition is not one face-connected body")
    log("Exact Cartesian CAD decomposition: %d occupied cells, volume %.12g mm^3"
        % (np.count_nonzero(occupied), volume))
    return axes, occupied


def build_hex_mesh(h, original, geometry, directory):
    """Shared-node quadratic bricks; at least two cells in every CAD slab.

    In particular, the web and flange thicknesses are resolved independently
    of the requested in-plane size, unlike isotropic tetrahedral meshing.
    """
    coarse_axes, coarse_occupied = geometry
    counts = [np.maximum(2, np.ceil(np.diff(a) / h).astype(int))
              for a in coarse_axes]
    axes = []
    occupied = coarse_occupied
    for k, (a, n) in enumerate(zip(coarse_axes, counts)):
        axes.append(np.r_[np.concatenate([
            np.linspace(a[j], a[j + 1], int(n[j]) + 1)[:-1]
            for j in range(len(n))]), a[-1]])
        occupied = np.repeat(occupied, n, axis=k)
    cells = np.column_stack(np.nonzero(occupied)).astype(np.int64)
    # CalculiX/Abaqus C3D20 corner and edge-node ordering.
    local = np.asarray([
        [0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0],
        [0, 0, 2], [2, 0, 2], [2, 2, 2], [0, 2, 2],
        [1, 0, 0], [2, 1, 0], [1, 2, 0], [0, 1, 0],
        [1, 0, 2], [2, 1, 2], [1, 2, 2], [0, 1, 2],
        [0, 0, 1], [2, 0, 1], [2, 2, 1], [0, 2, 1]
    ], dtype=np.int64)
    half_axes = []
    for a in axes:
        v = np.empty(2 * len(a) - 1)
        v[::2] = a
        v[1::2] = (a[:-1] + a[1:]) / 2.
        half_axes.append(v)
    sy, sz = len(half_axes[1]), len(half_axes[2])
    codes = (((2 * cells[:, 0, None] + local[None, :, 0]) * sy
              + 2 * cells[:, 1, None] + local[None, :, 1]) * sz
             + 2 * cells[:, 2, None] + local[None, :, 2])
    node_codes, inverse = np.unique(codes, return_inverse=True)
    conn = inverse.reshape(-1, 20)
    del codes, inverse
    xyz = np.column_stack((
        half_axes[0][node_codes // (sy * sz)],
        half_axes[1][(node_codes // sz) % sy],
        half_axes[2][node_codes % sz]))
    tags = np.arange(1, len(xyz) + 1, dtype=np.int64)
    force = np.zeros_like(xyz)
    report = []
    quad = np.asarray([[0, 0], [2, 0], [2, 2], [0, 2],
                       [1, 0], [2, 1], [1, 2], [0, 1]])
    weights = np.asarray([-1. / 12.] * 4 + [1. / 3.] * 4)
    xc, yc = [(a[:-1] + a[1:]) / 2. for a in axes[:2]]
    dx, dy = np.diff(axes[0]), np.diff(axes[1])
    for index, (area, center, box) in original.items():
        if abs(box[5] - box[2]) > 1.e-4:
            raise RuntimeError("Reference traction is not on a horizontal face")
        kz = int(np.argmin(abs(axes[2] - center[2])))
        if abs(axes[2][kz] - center[2]) > 1.e-5:
            raise RuntimeError("Loaded plane missing from Cartesian mesh")
        # Count a shared face once, even if it is internal to the solid union.
        present = np.zeros(occupied.shape[:2], dtype=bool)
        if kz < occupied.shape[2]:
            present |= occupied[:, :, kz]
        if kz > 0:
            present |= occupied[:, :, kz - 1]
        present &= ((xc >= box[0] - 1.e-5) & (xc <= box[3] + 1.e-5))[:, None]
        present &= ((yc >= box[1] - 1.e-5) & (yc <= box[4] + 1.e-5))[None, :]
        ii, jj = np.nonzero(present)
        areas = dx[ii] * dy[jj]
        integrated_area = float(areas.sum())
        if abs(integrated_area - area) > max(.01, area * 1.e-7):
            raise RuntimeError("Brick loaded-face area mismatch on face %d: %g / %g"
                               % (index, integrated_area, area))
        face_codes = (((2 * ii[:, None] + quad[None, :, 0]) * sy
                       + 2 * jj[:, None] + quad[None, :, 1]) * sz + 2 * kz)
        loc = np.searchsorted(node_codes, face_codes)
        if np.any(loc >= len(node_codes)) or not np.array_equal(node_codes[loc], face_codes):
            raise RuntimeError("Missing shared quadratic face nodes")
        # Exact consistent vector traction on a straight eight-node quadrilateral.
        for j in range(8):
            np.add.at(force[:, 2], loc[:, j], LOADS[index] * areas * weights[j])
        report.append({"face_index": index, "area_mm2": integrated_area,
                       "traction_MPa": [0., 0., LOADS[index]],
                       "force_N": [0., 0., integrated_area * LOADS[index]]})
    bc = []
    for x in (50., 29950.):
        mask = ((abs(xyz[:, 0] - x) < 1.e-5)
                & (abs(xyz[:, 2] - 2100.) < 1.e-5)
                & (xyz[:, 1] >= 87.5 - 1.e-5)
                & (xyz[:, 1] <= 662.5 + 1.e-5))
        bc.append(tags[mask])
    if not all(len(b) for b in bc):
        raise RuntimeError("Empty Cartesian support node set")
    write_json(directory / "loads.json", report)
    with (directory / "model.inc").open("w") as f:
        f.write("*HEADING\nShared-interface quadratic brick plate girder\n*NODE\n")
        for tag, point in zip(tags, xyz):
            f.write("%d,%.12g,%.12g,%.12g\n" % (tag, *point))
        f.write("*ELEMENT,TYPE=C3D20R,ELSET=BODY\n")
        for i, nodes in enumerate(conn + 1, 1):
            f.write(str(i) + "," + ",".join(map(str, nodes)) + "\n")
        f.write("*MATERIAL,NAME=STEEL\n*ELASTIC\n210000.,0.3\n")
        f.write("*SOLID SECTION,ELSET=BODY,MATERIAL=STEEL\n*BOUNDARY\n")
        for tag in bc[0]:
            f.write("%d,1,3,0.\n" % tag)
        for tag in bc[1]:
            f.write("%d,2,3,0.\n" % tag)
    with (directory / "load.inc").open("w") as f:
        f.write("*CLOAD\n")
        for i in np.flatnonzero(force[:, 2]):
            f.write("%d,3,%.14g\n" % (tags[i], force[i, 2]))
    gmsh_local = np.asarray(gmsh.model.mesh.getElementProperties(17)[4]).reshape(-1, 3)
    local_index = {tuple(p): j for j, p in enumerate(local)}
    permutation = np.asarray([local_index[tuple(np.rint(p + 1).astype(int))]
                              for p in gmsh_local])
    gmsh_conn = conn[:, permutation]
    with (directory / "mesh.msh").open("w") as f:
        f.write("$MeshFormat\n2.2 0 8\n$EndMeshFormat\n$Nodes\n%d\n" % len(tags))
        for tag, point in zip(tags, xyz):
            f.write("%d %.12g %.12g %.12g\n" % (tag, *point))
        f.write("$EndNodes\n$Elements\n%d\n" % len(conn))
        for i, nodes in enumerate(gmsh_conn + 1, 1):
            f.write(str(i) + " 17 2 1 1 " + " ".join(map(str, nodes)) + "\n")
        f.write("$EndElements\n")
    np.savez_compressed(directory / "mesh_data.npz", node_ids=tags, points=xyz,
                        connectivity=conn, hexahedron20=conn,
                        gmsh_connectivity=gmsh_conn,
                        element_type=np.asarray("hexahedron20_abaqus_order"),
                        force=force, fixed_node_ids=bc[0], roller_node_ids=bc[1])
    log("Mesh h=%g: %d nodes, %d C3D20R elements; total load %s N"
        % (h, len(tags), len(conn), force.sum(axis=0)))
    return {"h_mm": h, "nodes": len(tags), "elements": len(conn),
            "element_type": "C3D20R", "minimum_cells_per_CAD_slab": 2,
            "directory": str(directory), "loads": report}


def build_mesh(h, face_map, curves, directory):
    gmsh.model.mesh.clear()
    for key, val in {
        "Mesh.MeshSizeMin": h,
        "Mesh.MeshSizeMax": h,
        "Mesh.MeshSizeFromPoints": 0,
        "Mesh.MeshSizeFromCurvature": 0,
        "Mesh.MeshSizeExtendFromBoundary": 0,
        "Mesh.Algorithm": 6,
        "Mesh.Algorithm3D": 1,
        "Mesh.ElementOrder": 1,
        "Mesh.Optimize": 1,
        "Mesh.SaveAll": 1,
        "Mesh.MaxNumThreads1D": 2,
        "Mesh.MaxNumThreads2D": 2,
        "Mesh.MaxNumThreads3D": 2
    }.items():
        gmsh.option.setNumber(key, val)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.setOrder(2)
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    gmsh.write(str(directory / "mesh.msh"))

    tags, xyz, _ = gmsh.model.mesh.getNodes()
    tags = np.asarray(tags, dtype=np.int64)
    xyz = np.asarray(xyz).reshape(-1, 3)
    order = np.argsort(tags)
    tags, xyz = tags[order], xyz[order]
    lookup = np.full(int(tags.max()) + 1, -1, dtype=np.int64)
    lookup[tags] = np.arange(len(tags))
    types, etags, enodes = gmsh.model.mesh.getElements(3)
    blocks = []
    for typ, conn in zip(types, enodes):
        if int(typ) != 11:
            raise RuntimeError("Unexpected solid element type %s" % typ)
        blocks.append(np.asarray(conn, dtype=np.int64).reshape(-1, 10))
    conn = np.vstack(blocks)
    ccx_conn = conn[:, [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]

    force = np.zeros((len(tags), 3))
    report = []
    for index, surfaces in face_map.items():
        integrated_area = 0.
        for surf in surfaces:
            stypes, _, snodes = gmsh.model.mesh.getElements(2, surf)
            for typ, raw in zip(stypes, snodes):
                if int(typ) != 9:
                    raise RuntimeError("Expected quadratic triangular loaded surface")
                triangles = np.asarray(raw, dtype=np.int64).reshape(-1, 6)
                loc = lookup[triangles]
                p = xyz[loc[:, :3]]
                areas = np.linalg.norm(np.cross(p[:, 1] - p[:, 0],
                                               p[:, 2] - p[:, 0]), axis=1) / 2.
                integrated_area += float(areas.sum())
                # Exact consistent nodal traction for a straight six-node triangle.
                for j in (3, 4, 5):
                    np.add.at(force[:, 2], loc[:, j], LOADS[index] * areas / 3.)
        report.append({"face_index": index, "area_mm2": integrated_area,
                       "traction_MPa": [0., 0., LOADS[index]],
                       "force_N": [0., 0., integrated_area * LOADS[index]]})

    bc = []
    for group in curves:
        ids = set()
        for curve in group:
            nt, _, _ = gmsh.model.mesh.getNodes(1, curve, includeBoundary=True)
            ids.update(int(t) for t in nt)
        bc.append(sorted(ids))
    if not all(bc):
        raise RuntimeError("Empty support node set")
    log("Mesh h=%g: %d nodes, %d C3D10 elements; total load %s N"
        % (h, len(tags), len(conn), force.sum(axis=0)))
    write_json(directory / "loads.json", report)

    base = directory / "model.inc"
    with base.open("w") as f:
        f.write("*HEADING\nShared-interface quadratic solid plate girder\n*NODE\n")
        for tag, point in zip(tags, xyz):
            f.write("%d,%.12g,%.12g,%.12g\n" % (tag, *point))
        f.write("*ELEMENT,TYPE=C3D10,ELSET=BODY\n")
        for i, nodes in enumerate(ccx_conn, 1):
            f.write(str(i) + "," + ",".join(map(str, nodes)) + "\n")
        f.write("*MATERIAL,NAME=STEEL\n*ELASTIC\n210000.,0.3\n")
        f.write("*SOLID SECTION,ELSET=BODY,MATERIAL=STEEL\n")
        f.write("*BOUNDARY\n")
        for tag in bc[0]:
            f.write("%d,1,3,0.\n" % tag)
        for tag in bc[1]:
            f.write("%d,2,3,0.\n" % tag)
    with (directory / "load.inc").open("w") as f:
        f.write("*CLOAD\n")
        for i in np.flatnonzero(force[:, 2]):
            f.write("%d,3,%.14g\n" % (tags[i], force[i, 2]))
    np.savez_compressed(directory / "mesh_data.npz", node_ids=tags,
                        points=xyz, tetra10=lookup[conn],
                        connectivity=lookup[conn],
                        element_type=np.asarray("tetra10_gmsh_order"), force=force,
                        fixed_node_ids=np.asarray(bc[0]),
                        roller_node_ids=np.asarray(bc[1]))
    return {"h_mm": h, "nodes": len(tags), "elements": len(conn),
            "directory": str(directory), "loads": report}


def run_ccx(directory, name, buckle, timeout):
    deck = "*INCLUDE,INPUT=model.inc\n*STEP\n"
    if buckle:
        deck += "*BUCKLE\n8,0.00001\n"
    else:
        deck += "*STATIC\n1.,1.\n"
    deck += "*INCLUDE,INPUT=load.inc\n*NODE FILE\nU\n"
    if not buckle:
        deck += "*EL FILE\nS\n"
    deck += "*END STEP\n"
    (directory / (name + ".inp")).write_text(deck)
    outfile = directory / (name + ".stdout")
    log("Starting ccx %s in %s, timeout %.1fs" % (name, directory, timeout))
    t = time.monotonic()
    with outfile.open("w") as out:
        proc = subprocess.Popen(["ccx", "-i", name], cwd=directory,
                                stdout=out, stderr=subprocess.STDOUT,
                                start_new_session=True)
        try:
            rc = proc.wait(timeout=max(1., timeout))
        except subprocess.TimeoutExpired:
            import signal
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            log(outfile.read_text(errors="replace"))
            raise RuntimeError("CalculiX time limit in " + name)
    log(outfile.read_text(errors="replace"))
    log("ccx %s completed in %.2fs, return code %d"
        % (name, time.monotonic() - t, rc))
    if rc != 0:
        raise RuntimeError("CalculiX failed in " + name)
    if not (directory / (name + ".frd")).exists():
        raise RuntimeError("CalculiX did not produce fields")
    return time.monotonic() - t


def eigenvalues(path):
    text = Path(path).read_text(errors="replace")
    number = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[EeDd][-+]?\d+)?"
    row = re.compile(r"^\s*\d+\s+(" + number + r")\s*$")
    values = []
    active = False
    have_rows = False

    for line in text.splitlines():
        compact = re.sub(r"\s+", "", line).upper()
        if "BUCKLINGFACTOR" in compact or (
            "MODENO" in compact and "BUCKLING" in compact
        ):
            active = True
            have_rows = False
            continue

        if not active:
            continue

        match = row.match(line)
        if match:
            values.append(float(re.sub(r"[Dd]", "E", match.group(1))))
            have_rows = True
        elif compact and have_rows:
            active = False
            have_rows = False

    if not values:
        raise RuntimeError("No buckling factors found in " + str(path))
    return np.asarray(values, dtype=float)


def read_frd(path, wanted, node_ids):
    """Read ASCII CalculiX nodal datasets, preserving their dataset order."""
    index = {int(n): i for i, n in enumerate(node_ids)}
    datasets = {key: [] for key in wanted}
    current = None
    entries = {}
    def finish():
        if current in datasets and entries:
            width = max(len(v) for v in entries.values())
            a = np.full((len(node_ids), width), np.nan)
            for node, vals in entries.items():
                if node in index:
                    a[index[node], :len(vals)] = vals
            datasets[current].append(a)
    number = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+)(?:[EeDd][-+]?\d+)?")
    with Path(path).open(errors="replace") as f:
        for line in f:
            code = line[:3].strip()
            if code == "-4":
                finish()
                parts = line.split()
                current = parts[1] if len(parts) > 1 else None
                entries = {}
            elif code == "-1" and current in datasets:
                try:
                    node = int(line[3:13])
                    vals = [float(v.replace("D", "E")) for v in number.findall(line[13:])]
                    if vals:
                        entries[node] = vals
                except ValueError:
                    pass
            elif code == "-3":
                finish()
                current = None
                entries = {}
    finish()
    return datasets


def main():
    LOG.write_text("CAD/FEM plate girder elastic buckling\n")
    if not shutil.which("ccx"):
        raise RuntimeError("ccx is not available")
    env = {
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "gmsh": gmsh.__version__,
        "calculix_executable": shutil.which("ccx"),
        "threads": 2, "units": "mm, N, MPa",
        "formulation": "Conforming quadratic solids; CalculiX linear perturbation buckling", 
        "prebuckling": "Independent linear static solve with the identical reference loads",
        "input_directory": str(INPUT)
    }
    write_json(OUTPUT / "environment.json", env)
    for root in (INPUT, Path.cwd()):
        for name in ("README", "README.md", "README.txt"):
            p = root / name
            if p.exists():
                log("Available artifact instructions (%s):\n%s" %
                    (p, p.read_text(errors="replace")[:20000]))
    raw = json.loads((INPUT / "faces.json").read_text())
    records = raw["face_descriptors"] if isinstance(raw, dict) else raw
    desc = {int(d["face_index"]): d for d in records}
    shutil.copyfile(INPUT / "analysis.step", OUTPUT / "part.step")

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.option.setNumber("General.NumThreads", 2)
    gmsh.logger.start()
    gmsh.model.add("plate_girder")
    gmsh.model.occ.importShapes(str(INPUT / "analysis.step"))
    gmsh.model.occ.synchronize()
    original_vols = gmsh.model.getEntities(3)
    original = find_original_surfaces(desc, surface_records())
    log("Imported %d solid regions" % len(original_vols))
    if len(original_vols) > 1:
        gmsh.model.occ.fragment(original_vols[:1], original_vols[1:],
                               removeObject=True, removeTool=True)
        gmsh.model.occ.synchronize()
    vols = gmsh.model.getEntities(3)
    volume = sum(gmsh.model.occ.getMass(3, t) for _, t in vols)
    log("Fragmented body: %d regions, volume %.9g mm^3" % (len(vols), volume))
    if abs(volume - 3335612900.) / 3335612900. > 0.001:
        raise RuntimeError("CAD volume validation failed")
    fmap = map_fragment_surfaces(original, surface_records())
    curves = support_curves()
    hex_geometry = cartesian_geometry()
    try:
        gmsh.write(str(OUTPUT / "part.step"))
    except Exception as e:
        log("STEP re-export unavailable; original exact STEP retained: " + str(e))
        shutil.copyfile(INPUT / "analysis.step", OUTPUT / "part.step")

    history = []
    successful = []
    # Brick thickness resolution is independent of the in-plane target size.
    # Retain exact conforming tetrahedra if the CAD is not rectilinear.
    sizes = (140., 90., 65.) if hex_geometry is not None else (140., 90., 60., 40.)
    for level, h in enumerate(sizes):
        if level and remaining() < (240. if level > 1 else 170.):
            log("Refinement skipped to reserve time for the required static fields.")
            break
        if len(successful) >= 2:
            delta = abs(successful[-1]["lambda1"] - successful[-2]["lambda1"]) / abs(successful[-1]["lambda1"])
            if delta < .003:
                log("Stopping refinement after a measured mesh-to-mesh change below 0.3%; no asymptotic convergence claim.")
                break
        directory = OUTPUT / ("level_%d" % level)
        directory.mkdir(exist_ok=True)
        rec = {"h_mm": h, "status": "started"}
        history.append(rec)
        try:
            if hex_geometry is not None:
                rec.update(build_hex_mesh(h, original, hex_geometry, directory))
            else:
                rec.update(build_mesh(h, fmap, curves, directory))
            allowance = min(260., remaining() - 95.)
            if allowance <= 10:
                raise RuntimeError("Insufficient remaining time for buckling solve")
            rec["buckling_seconds"] = run_ccx(directory, "buckle", True, allowance)
            vals = eigenvalues(directory / "buckle.dat")
            pos = np.flatnonzero(np.isfinite(vals) & (vals > 0.))
            if not len(pos):
                raise RuntimeError("No positive eigenvalue was computed")
            first = int(pos[np.argmin(vals[pos])])
            rec["eigenvalues"] = vals.tolist()
            rec["lambda1"] = float(vals[first])
            rec["mode_dataset_index"] = first
            rec["status"] = "buckling_complete"
            successful.append(rec)
        except Exception as e:
            rec["status"] = "failed"
            rec["error"] = str(e)
            log(traceback.format_exc())
            if not successful:
                raise
            break
        finally:
            write_json(OUTPUT / "refinement.json",
                       {"levels": history, "convergence_claimed": False})
    log("\nGmsh messages:\n" + "\n".join(gmsh.logger.get()))
    gmsh.finalize()
    if not successful:
        raise RuntimeError("No successful buckling calculation")

    selected = None
    static_errors = []
    for candidate in reversed(successful):
        directory = Path(candidate["directory"])
        try:
            candidate["static_seconds"] = run_ccx(
                directory, "static", False, min(180., remaining() - 5.))
            selected = candidate
            break
        except Exception as e:
            static_errors.append(str(e))
            log(traceback.format_exc())
    if selected is None:
        raise RuntimeError("Could not complete reference static stress solution: "
                           + "; ".join(static_errors))

    directory = Path(selected["directory"])
    data = dict(np.load(directory / "mesh_data.npz"))
    static = read_frd(directory / "static.frd", {"DISP", "STRESS"}, data["node_ids"])
    modes = read_frd(directory / "buckle.frd", {"DISP"}, data["node_ids"])
    if not static["DISP"] or not static["STRESS"]:
        raise RuntimeError("Static displacement/stress datasets missing")
    mode_offset = len(modes["DISP"]) - len(selected["eigenvalues"])
    if mode_offset not in (0, 1):
        raise RuntimeError("Cannot associate buckling displacement datasets with eigenvalues")
    mode_index = selected["mode_dataset_index"] + mode_offset
    if mode_index >= len(modes["DISP"]):
        raise RuntimeError("Selected eigenvector missing from CalculiX output")
    u = static["DISP"][-1][:, :3]
    stress = static["STRESS"][-1][:, :6]
    mode = modes["DISP"][mode_index][:, :3]
    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(stress))
            and np.all(np.isfinite(mode))):
        raise RuntimeError("Non-finite or incomplete nodal fields")
    maxamp = np.max(np.linalg.norm(mode, axis=1))
    if maxamp <= 0:
        raise RuntimeError("Zero buckling mode")
    mode /= maxamp
    data.update({
        "coordinates": data["points"],
        "connectivity": data["connectivity"],
        "displacement": u,
        "prebuckling_displacement_mm": u,
        "stress": stress,
        "prebuckling_stress_MPa": stress,
        "stress_component_order": np.asarray(["xx", "yy", "zz", "xy", "yz", "zx"]),
        "buckling_mode": mode,
        "eigenvalues": np.asarray(selected["eigenvalues"]),
        "lambda1": np.asarray(selected["lambda1"]),
        "element_type": data["element_type"],
        "stress_location": np.asarray("CalculiX extrapolated and averaged nodal stress")
    })
    np.savez_compressed(OUTPUT / "fields.npz", **data)
    shutil.copyfile(directory / "mesh.msh", OUTPUT / "mesh.msh")
    change = None
    selected_index = successful.index(selected)
    if selected_index > 0:
        change = abs(selected["lambda1"] - successful[selected_index - 1]["lambda1"]) / abs(selected["lambda1"])
    write_json(OUTPUT / "refinement.json", {
        "levels": history,
        "selected_h_mm": selected["h_mm"],
        "selected_lambda1": selected["lambda1"],
        "relative_change_last_two": change,
        "convergence_claimed": False,
        "notes": (
            "Exact rectilinear CAD is meshed with shared-node C3D20R bricks and at least two cells across every CAD coordinate slab; non-rectilinear CAD uses conforming C3D10 tetrahedra. "
            "The brick decomposition is checked against CAD volume and face connectivity. Consistent quadratic face tractions are integrated and checked against each specified face area. "
            "The reported factor is the smallest positive computed factor on the selected mesh. "
            "Successively refined meshes are attempted within the runtime budget; failures and skipped refinements are not convergence evidence. "
            "The recorded mesh-to-mesh changes are not an asymptotic convergence proof. "
            "All traction scopes and support curves are geometrically identified and area/length validated."
        ),
        "cad_volume_mm3": volume,
        "static_errors": static_errors
    })
    env["elapsed_seconds"] = time.monotonic() - START
    env["cad_regions_after_fragment"] = len(vols)
    env["selected_element_type"] = str(data["element_type"])
    write_json(OUTPUT / "environment.json", env)
    write_json(OUTPUT / "results.json", {"outputs": {"lambda1": selected["lambda1"]}})
    log("Completed: lambda1=%.12g, elapsed %.1fs"
        % (selected["lambda1"], time.monotonic() - START))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        message = traceback.format_exc()
        log(message)
        write_json(OUTPUT / "error.json", {
            "error": message,
            "elapsed_seconds": time.monotonic() - START,
            "results_fabricated": False
        })
        try:
            if gmsh.isInitialized():
                log("\n".join(gmsh.logger.get()))
                gmsh.finalize()
        except Exception:
            pass
        sys.exit(1)
