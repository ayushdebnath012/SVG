"""OpenCASCADE helpers for the mechanism-design grader: STEP loading, planar poses, interference, pin detection and
cross-section properties of submitted parts."""
from __future__ import annotations

import math

import cadquery as cq
import numpy as np
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps


def load(path) -> cq.Shape:
    return cq.importers.importStep(str(path)).val()


def valid(shape: cq.Shape) -> dict:
    solids = shape.Solids()
    return dict(valid=bool(BRepCheck_Analyzer(shape.wrapped).IsValid()), solids=len(solids),
                volume_mm3=float(sum(s.Volume() for s in solids)))


def moved(shape: cq.Shape, t: np.ndarray, phi: float) -> cq.Shape:
    """Planar pose (x, z translation, rotation phi in the x-z plane) -> 3D move: rotation about +y by -phi."""
    return shape.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), -math.degrees(phi)).translate(cq.Vector(float(t[0]), 0, float(t[1])))


def overlap(a: cq.Shape, b: cq.Shape) -> float:
    ba, bb = a.BoundingBox(), b.BoundingBox()
    if ba.xmin > bb.xmax or bb.xmin > ba.xmax or ba.ymin > bb.ymax or bb.ymin > ba.ymax or ba.zmin > bb.zmax or bb.zmin > ba.zmax:
        return 0.0
    try:
        return float(a.intersect(b).Volume())
    except Exception:                                            # noqa: BLE001 - a failed boolean is reported, not hidden
        return float("nan")


def cylinders_on_axis(shape: cq.Shape, x: float, z: float, tol: float = 0.3) -> list[float]:
    """Diameters of cylindrical faces whose axis is parallel to y and passes within tol of (x, z)."""
    out = []
    for f in shape.Faces():
        if f.geomType() != "CYLINDER":
            continue
        cyl = f._geomAdaptor().Cylinder()
        ax = cyl.Axis()
        d, o = ax.Direction(), ax.Location()
        if abs(abs(d.Y()) - 1.0) > 1e-3:
            continue
        if math.hypot(o.X() - x, o.Z() - z) <= tol:
            out.append(2.0 * cyl.Radius())
    return sorted(set(round(v, 4) for v in out))


def section(shape: cq.Shape, origin: np.ndarray, u: np.ndarray, s: float, delta: float = 0.5) -> dict | None:
    """Properties of the cross-section of `shape` cut perpendicular to the in-plane direction u (x-z) at distance s
    from origin (x, z): area, centroid offset along the in-plane normal n, in-plane bending inertia I_y (about y),
    minimum principal inertia, and extreme-fibre distance along n."""
    n = np.array([-u[1], u[0]])
    big = 4000.0
    slab = cq.Solid.makeBox(delta, big, big, cq.Vector(-delta / 2, -big / 2, -big / 2))
    ang = math.degrees(math.atan2(u[1], u[0]))
    c0 = origin + s * u
    slab = slab.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), -ang).translate(cq.Vector(float(c0[0]), 0, float(c0[1])))
    try:
        cut = shape.intersect(slab)
    except Exception:                                            # noqa: BLE001
        return None
    vol = cut.Volume()
    if vol <= 1e-9:
        return None
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(cut.wrapped, g)
    cg = g.CentreOfMass()
    M = g.MatrixOfInertia()                                      # about the centroid, off-diagonals = -products
    mat = np.array([[M.Value(i, j) for j in (1, 2, 3)] for i in (1, 2, 3)])
    ey = np.array([0.0, 1.0, 0.0])
    en = np.array([n[0], 0.0, n[1]])
    eu = np.array([u[0], 0.0, u[1]])
    # second moments of area: I about an axis a through the centroid = a^T M a, divided by the slab thickness;
    # the slab-thickness term (delta^2/12 * A) is removed for axes lying in the section plane
    area = vol / delta
    corr = area * delta ** 2 / 12.0
    I_y = (ey @ mat @ ey) / delta - corr                         # bending in the mechanism plane (axis along y)
    I_n = (en @ mat @ en) / delta - corr                         # out-of-plane bending (axis along n)
    P = -(ey @ mat @ en) / delta                                 # product of area
    I_min = 0.5 * (I_y + I_n) - math.sqrt((0.5 * (I_y - I_n)) ** 2 + P ** 2)
    pts = [v.toTuple() for v in cut.Vertices()]
    for e in cut.Edges():
        pts += [e.positionAt(k / 8).toTuple() for k in range(9)]
    cen = np.array([cg.X(), cg.Z()])
    c = max(abs((np.array([p_[0], p_[2]]) - cen) @ n) for p_ in pts) if pts else 0.0
    return dict(area=area, I_y=I_y, I_min=I_min, c=c, centroid_offset=float((cen - c0) @ n), solids=len(cut.Solids()))
