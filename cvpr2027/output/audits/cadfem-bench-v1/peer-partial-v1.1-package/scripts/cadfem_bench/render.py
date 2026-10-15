"""Shaded inspection renders of task CAD (OpenCASCADE tessellation + matplotlib). Read-only; no geometry is changed."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import common as C


def triangles(shape, rel_defl: float = 0.003):
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopAbs import TopAbs_REVERSED
    from OCP.TopLoc import TopLoc_Location
    box = C.shape_summary(shape)["bbox_mm"]
    diag = float(np.linalg.norm(np.subtract(box[3:], box[:3])))
    BRepMesh_IncrementalMesh(shape, rel_defl * diag, False, 0.4, True)
    out = []
    for i, f in enumerate(C.faces(shape)):
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(f, loc)
        if tri is None:
            continue
        tr = loc.Transformation()
        pts = np.array([[p.X(), p.Y(), p.Z()] for p in (tri.Node(k).Transformed(tr) for k in range(1, tri.NbNodes() + 1))])
        rev = f.Orientation() == TopAbs_REVERSED
        for k in range(1, tri.NbTriangles() + 1):
            a, b, c = tri.Triangle(k).Get()
            t = pts[[a - 1, c - 1, b - 1]] if rev else pts[[a - 1, b - 1, c - 1]]
            out.append((i + 1, t))
    return out


def render(cad: Path, png: Path, highlight: dict | None = None, view=(24, -58), size=(4.2, 3.2)) -> Path:
    shape = C.read_shape(cad)
    tris = triangles(shape)
    T = np.array([t for _, t in tris])
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-30
    light = np.array([0.4, -0.5, 0.75]) / np.linalg.norm([0.4, -0.5, 0.75])
    shade = 0.35 + 0.65 * np.abs(n @ light)
    base = np.array([0.62, 0.66, 0.72])
    cols = np.clip(shade[:, None] * base, 0, 1)
    if highlight:
        for j, (fid, _) in enumerate(tris):
            if fid in highlight:
                cols[j] = np.clip(shade[j] * np.array(highlight[fid]), 0, 1)
    fig = plt.figure(figsize=size, dpi=170)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(T, facecolors=cols, edgecolors="none", linewidths=0))
    lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
    c, r = (lo + hi) / 2, (hi - lo).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(*view)
    ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1)
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, transparent=False, facecolor="white")
    plt.close(fig)
    return png
