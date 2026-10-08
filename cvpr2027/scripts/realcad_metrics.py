"""Solid and Surface IoU as defined by RealCADBench (arXiv:2609.03773, Appendix A.2), for CadQuery/OCC solids.

Both IoUs share one cubic grid of resolution R = 96 with 2 % padding around the union of the two shapes. Solid IoU
compares filled occupancy; Surface IoU compares boundary occupancy (filled voxels with an empty 6-neighbour), which
is more sensitive to thin structures and local detail. RealCADBench first removes pose and uniform scale with a
signed-PCA alignment because its predictions are generated from scratch; edits share the source coordinate frame,
so we compare in that frame and translation or scale errors still count.

Filled occupancy is computed by ray parity along z through every column centre of the tessellated solid.
"""
import numpy as np
from scipy.ndimage import binary_erosion

R = 96
PAD = 0.02


def mesh(shape, rel_tol=1e-3):
    bb = shape.BoundingBox()
    v, t = shape.tessellate(max(rel_tol * bb.DiagonalLength, 1e-4))
    return np.array([p.toTuple() for p in v], dtype=float), np.array(t, dtype=np.int64)


def grid_for(*meshes):
    lo = np.min([m[0].min(0) for m in meshes], axis=0)
    hi = np.max([m[0].max(0) for m in meshes], axis=0)
    side = float((hi - lo).max()) * (1 + 2 * PAD)
    centre = (lo + hi) / 2
    return centre - side / 2, side / R


def filled(vertices, triangles, origin, h):
    """Boolean R^3 occupancy by z-ray parity at column centres (offset slightly to avoid edge hits)."""
    occ = np.zeros((R, R, R), dtype=bool)
    eps = np.array([0.31e-6, 0.17e-6]) * h
    cx = origin[0] + (np.arange(R) + 0.5) * h + eps[0]
    cy = origin[1] + (np.arange(R) + 0.5) * h + eps[1]
    hits = [[] for _ in range(R * R)]
    tri = vertices[triangles]
    for a, b, c in tri:
        xmin, xmax = min(a[0], b[0], c[0]), max(a[0], b[0], c[0])
        ymin, ymax = min(a[1], b[1], c[1]), max(a[1], b[1], c[1])
        i0, i1 = np.searchsorted(cx, xmin), np.searchsorted(cx, xmax, side="right")
        j0, j1 = np.searchsorted(cy, ymin), np.searchsorted(cy, ymax, side="right")
        if i0 >= i1 or j0 >= j1:
            continue
        X, Y = np.meshgrid(cx[i0:i1], cy[j0:j1], indexing="ij")
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-18:
            continue  # vertical triangle: no z-ray crosses its interior
        l1 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / d
        l2 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / d
        l3 = 1 - l1 - l2
        inside = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
        if not inside.any():
            continue
        z = l1 * a[2] + l2 * b[2] + l3 * c[2]
        for i, j in zip(*np.nonzero(inside)):
            hits[(i0 + i) * R + (j0 + j)].append(z[i, j])
    cz = origin[2] + (np.arange(R) + 0.5) * h
    for k, zs in enumerate(hits):
        if len(zs) < 2:
            continue
        zs = np.sort(zs)
        for z0, z1 in zip(zs[0::2], zs[1::2]):
            occ[k // R, k % R, (cz >= z0) & (cz <= z1)] = True
    return occ


def boundary(occ):
    return occ & ~binary_erosion(occ, border_value=0)


def voxel_ious(shape_a, shape_b):
    """{'solid': ..., 'surface': ...} between two OCC/CadQuery shapes on one shared grid."""
    ma, mb = mesh(shape_a), mesh(shape_b)
    origin, h = grid_for(ma, mb)
    fa, fb = filled(*ma, origin, h), filled(*mb, origin, h)
    ba, bb = boundary(fa), boundary(fb)

    def iou(x, y):
        u = np.logical_or(x, y).sum()
        return float(np.logical_and(x, y).sum() / u) if u else 1.0
    return dict(solid=iou(fa, fb), surface=iou(ba, bb))
