"""Read-only extraction of fcVM (HarryvL/fcVM-workbench) analysis set-ups from the original FreeCAD documents.

For each model: the meshed analysis shape (the FEM mesh object's `Part` link), material, every constraint mapped onto
the analysis shape's faces/edges by geometry (constraints often reference construction objects such as `Box` that
coincide with fragments of the analysis shape), the reference load vector of each load constraint, and the control
file (yield stress, hardening, gravity, geometric nonlinearity, imperfection). `check()` rebuilds the total applied
load and compares it with the "Sum of loads" printed in the published .out file: agreement shows that the output
belongs to this set-up. No fcVM or FreeCAD code is run.
"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

import numpy as np

import common as C
from fcstd import FCStd

SRC = C.ROOT.parent / "cadfem-bench-v1.1-followup/published-source-expansion"
CTL = ["sig_yield", "grav_x", "grav_y", "grav_z", "nstep", "iterat_max", "error_max", "relax", "scale_re", "scale_up", "scale_dn",
       "disp_output", "ultimate_strain", "Et_E", "target_LF", "csr_option", "averaged_option", "gnl", "maxImp", "ev1", "ev2"]


def mpa(q: str) -> float:
    v, unit = float(q.split()[0]), " ".join(q.split()[1:])
    return {"MPa": 1.0, "kPa": 1e-3, "Pa": 1e-6, "GPa": 1e3, "kg/(mm*s^2)": 1e-3}[unit] * v


def density_kg_mm3(q: str) -> float:
    v, unit = float(q.split()[0]), " ".join(q.split()[1:])
    return {"kg/m^3": 1e-9, "kg/mm^3": 1.0}[unit] * v


def _vector_area(f) -> np.ndarray:
    """Integral of the outward unit normal over a face (triangulated; accounts for face orientation)."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopAbs import TopAbs_REVERSED
    from OCP.TopLoc import TopLoc_Location
    BRepMesh_IncrementalMesh(f, 0.01, False, 0.05, True)
    loc = TopLoc_Location()
    tri = BRep_Tool.Triangulation_s(f, loc)
    tr = loc.Transformation()
    pts = np.array([[q.X(), q.Y(), q.Z()] for q in (tri.Node(k).Transformed(tr) for k in range(1, tri.NbNodes() + 1))])
    acc = np.zeros(3)
    for k in range(1, tri.NbTriangles() + 1):
        a, b, c = tri.Triangle(k).Get()
        acc += 0.5 * np.cross(pts[b - 1] - pts[a - 1], pts[c - 1] - pts[a - 1])
    return -acc if f.Orientation() == TopAbs_REVERSED else acc


def control(name: str) -> dict:
    vals = (SRC / "control files" / f"{name}.inp").read_text().split("\n")
    out = {}
    for k, v in zip(CTL, vals):
        v = v.strip()
        try:
            out[k] = float(v)
        except ValueError:
            out[k] = v
    return out


def published(name: str) -> dict:
    txt = (SRC / "output files" / f"{name}.out").read_text(errors="replace")
    sums = [float(re.search(rf"Sum of loads {c}-direction:\s+(\S+)", txt).group(1)) for c in "xyz"]
    m = re.search(r"elastic buckling factors:\s+\[([^\]]+)\]", txt)
    rows = []
    for line in txt.splitlines():
        p = line.split()
        if len(p) == 12 and p[0].lstrip("-").isdigit():
            rows.append([float(x) for x in p])
    return dict(analysis_type=re.search(r"analysis type:\s+(.+)", txt).group(1).strip(),
                elements=int(re.search(r"No\. of elements:\s+(\d+)", txt).group(1)), load_sum=sums,
                buckling=[float(x) for x in m.group(1).split()] if m else None, rows=rows)


def _sub(shape, kind: str, idx: int):
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
    from OCP.TopExp import TopExp
    from OCP.TopTools import TopTools_IndexedMapOfShape
    m = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(shape, TopAbs_FACE if kind == "Face" else TopAbs_EDGE, m)
    return m.FindKey(idx)


def _dist(a, b) -> float:
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    d = BRepExtrema_DistShapeShape(a, b)
    return d.Value()


def _samples(sub) -> list:
    """Vertices and edge mid-points of a face/edge: points that lie on the sub-shape itself (a curved face's centre of
    mass does not)."""
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_VERTEX
    from OCP.TopExp import TopExp
    from OCP.TopTools import TopTools_IndexedMapOfShape
    pts = []
    for kind in (TopAbs_VERTEX, TopAbs_EDGE):
        m = TopTools_IndexedMapOfShape()
        TopExp.MapShapes_s(sub, kind, m)
        for i in range(1, m.Extent() + 1):
            if kind == TopAbs_VERTEX:
                pts.append(m.FindKey(i))
            else:
                from OCP.TopoDS import TopoDS
                c = BRepAdaptor_Curve((getattr(TopoDS, "Edge_s", None) or TopoDS.Edge)(m.FindKey(i)))
                pts.append(BRepBuilderAPI_MakeVertex(c.Value(0.5 * (c.FirstParameter() + c.LastParameter()))).Vertex())
    return pts


def _surface_normal(f) -> np.ndarray:
    """Normal of the underlying surface at the face's parametric centre, ignoring the face orientation: FreeCAD's
    ConstraintForce uses this direction (confirmed by the published load sums; e.g. IPE400_4's two opposite box faces
    with one constraint reversed sum to zero)."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.gp import gp_Pnt, gp_Vec
    ad = BRepAdaptor_Surface(f)
    u = 0.5 * (ad.FirstUParameter() + ad.LastUParameter())
    v = 0.5 * (ad.FirstVParameter() + ad.LastVParameter())
    p, du, dv = gp_Pnt(), gp_Vec(), gp_Vec()
    ad.D1(u, v, p, du, dv)
    n = np.cross([du.X(), du.Y(), du.Z()], [dv.X(), dv.Y(), dv.Z()])
    return n / np.linalg.norm(n)


def _area(f) -> float:
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    g = GProp_GProps()
    BRepGProp.SurfaceProperties_s(f, g)
    return g.Mass()


def _normal(f) -> np.ndarray:
    """Outward normal at the face centre (accounts for face orientation)."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepGProp import BRepGProp_Face
    from OCP.gp import gp_Pnt, gp_Vec
    from OCP.TopAbs import TopAbs_REVERSED
    ad = BRepAdaptor_Surface(f)
    u = 0.5 * (ad.FirstUParameter() + ad.LastUParameter())
    v = 0.5 * (ad.FirstVParameter() + ad.LastVParameter())
    p, n = gp_Pnt(), gp_Vec()
    BRepGProp_Face(f).Normal(u, v, p, n)
    n = np.array([n.X(), n.Y(), n.Z()])
    return n / np.linalg.norm(n)


def extract(name: str) -> dict:
    doc = FCStd(SRC / "freeCAD files" / f"{name}.FCStd")
    meshes = [n for n, t in doc.types.items() if "FemMesh" in t and "Result" not in n and "Part" in doc.props(n)]
    assert len(meshes) >= 1, (name, "no FEM mesh with a Part link")
    part = re.search(r'value="([^"]+)"', doc.props(meshes[0])["Part"][1]).group(1)
    shapes = {}
    tmp = Path(tempfile.mkdtemp())

    def shape_of(obj):
        if obj not in shapes:
            shapes[obj] = C.read_shape(doc.extract(doc.shape_member(obj), tmp / f"{obj}.brp"))
        return shapes[obj]

    ana = shape_of(part)
    afaces = C.faces(ana)
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.TopExp import TopExp
    from OCP.TopTools import TopTools_IndexedMapOfShape
    em = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(ana, TopAbs_EDGE, em)
    aedges = [em.FindKey(i) for i in range(1, em.Extent() + 1)]
    mat = doc.material(next(n for n, t in doc.types.items() if "Material" in t))
    cons = []
    for n, t in doc.types.items():
        if "Constraint" not in t:
            continue
        refs = doc.links(n)
        if not refs:
            continue
        kind = t.split("::")[-1].replace("Python", "")
        targets = []
        for obj, sub in refs:
            k, idx = re.match(r"(Face|Edge|Vertex)(\d+)", sub).groups()
            r = _sub(shape_of(obj), k, int(idx))
            pool = afaces if k == "Face" else aedges
            hits = [i + 1 for i, s in enumerate(pool) if all(_dist(p, r) < 1e-3 for p in _samples(s))]
            assert hits, (name, n, obj, sub)
            targets += [(k, h) for h in hits]
        c = dict(name=n, type=kind, targets=sorted(set(targets)))
        if kind == "ConstraintForce":
            c["force_N"] = float(doc.value(n, "Force"))
            c["reversed"] = doc.value(n, "Reversed") == "true"
            d = np.array(doc.vector(n, "DirectionVector"))         # FreeCAD's saved direction (includes Reversed), as fcVM uses
            c["direction"] = (d / np.linalg.norm(d)).tolist()
            fs = [(i, afaces[i - 1]) for k, i in c["targets"] if k == "Face"]
            assert len(fs) == len(c["targets"]), (name, n, "force on edges/vertices not handled")
            areas = np.array([_area(f) for _, f in fs])
            c["face_vectors_N"] = {str(i): (c["force_N"] * a / areas.sum() * d / np.linalg.norm(d)).tolist()
                                   for (i, _), a in zip(fs, areas)}
        elif kind == "ConstraintPressure":
            c["pressure_MPa"] = float(doc.value(n, "Pressure"))
            c["reversed"] = doc.value(n, "Reversed") == "true"
            sign = 1.0 if c["reversed"] else -1.0
            c["face_vectors_N"] = {str(i): (sign * c["pressure_MPa"] * _vector_area(afaces[i - 1])).tolist()
                                   for k, i in c["targets"]}
        elif kind == "ConstraintDisplacement":
            c["fixed_components"] = [ax for ax in "xyz" if doc.value(n, f"{ax}Free") == "false"]
            c["prescribed"] = {ax: float(doc.value(n, f"{ax}Displacement")) for ax in c["fixed_components"]}
        cons.append(c)
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(ana, g)
    return dict(name=name, analysis_object=part, shape=ana, faces=afaces, edges=aedges, material=mat,
                E_MPa=mpa(mat["YoungsModulus"]), nu=float(mat["PoissonRatio"]), density_kg_mm3=density_kg_mm3(mat["Density"]),
                volume_mm3=g.Mass(), constraints=cons, control=control(name), published=published(name))


def check(x: dict) -> dict:
    """Rebuild the total applied load; fcVM's gravity term is rho[kg/mm^3] * g[m/s^2, control file] * V in N."""
    total = np.zeros(3)
    for c in x["constraints"]:
        for v in c.get("face_vectors_N", {}).values():
            total += np.array(v)
    ctl = x["control"]
    grav = x["density_kg_mm3"] * np.array([ctl["grav_x"], ctl["grav_y"], ctl["grav_z"]]) * x["volume_mm3"]
    pub = np.array(x["published"]["load_sum"])
    calc = total + grav
    scale = max(np.abs(pub).max(), sum(np.linalg.norm(v) for c in x["constraints"] for v in map(np.array, c.get("face_vectors_N", {}).values())), 1e-9)
    return dict(calculated_load_sum=calc.tolist(), published_load_sum=pub.tolist(), gravity_N=grav.tolist(),
                max_relative_difference=float(np.abs(calc - pub).max() / scale), applied_without_gravity=total.tolist())


if __name__ == "__main__":
    import json
    for f in sorted((SRC / "freeCAD files").glob("*.FCStd")):
        try:
            x = extract(f.stem)
            k = check(x)
            print(f"{f.stem:22s} {x['published']['analysis_type'][:34]:34s} solids={C.shape_summary(x['shape'])['solids']:3d} "
                  f"calc={np.round(k['calculated_load_sum'], 3).tolist()} pub={k['published_load_sum']} rel={k['max_relative_difference']:.1e}")
        except Exception as e:
            print(f"{f.stem:22s} FAILED {type(e).__name__}: {e}")
