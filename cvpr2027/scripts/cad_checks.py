"""Geometry checks on a STEP solid with OpenCASCADE: solid count, volume, bounding box and wall thickness.

Wall thickness: points are sampled over the surface (area-weighted, from a fine triangulation); from each point a ray
is cast along the inward normal and the distance to the first surface it meets is the local wall thickness (the
exact B-rep is intersected, not a mesh). Reported: the thickness percentiles and the share of surface area thinner
than a limit (1.27 mm, the GE bracket challenge minimum feature size).

Run with a Python that has OCP (e.g. the BenchCAD venv):
  python cad_checks.py part.step [more.step ...] [--samples 6000] [--limit 1.27] [--jsonl out.jsonl]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np
from OCP.Bnd import Bnd_Box
from OCP.BRep import BRep_Tool
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing
from OCP.BRepGProp import BRepGProp
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.GProp import GProp_GProps
from OCP.IFSelect import IFSelect_RetDone
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED, TopAbs_SHELL, TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt


def count(shape, kind) -> int:
    ex, n = TopExp_Explorer(shape, kind), 0
    while ex.More():
        n += 1
        ex.Next()
    return n


def load_solid(path: str):
    r = STEPControl_Reader()
    if r.ReadFile(path) != IFSelect_RetDone:
        raise ValueError("cannot read STEP")
    r.TransferRoots()
    s = r.OneShape()
    if count(s, TopAbs_SOLID) == 0 and count(s, TopAbs_SHELL) > 0:  # closed shell only: sew and make a solid
        sew = BRepBuilderAPI_Sewing(1e-3)
        sew.Add(s)
        sew.Perform()
        ex = TopExp_Explorer(sew.SewedShape(), TopAbs_SHELL)
        mk = BRepBuilderAPI_MakeSolid()
        while ex.More():
            mk.Add(TopoDS.Shell_s(ex.Current()))
            ex.Next()
        s = mk.Solid()
    return s


def surface_samples(shape, n: int, seed: int = 0):
    BRepMesh_IncrementalMesh(shape, 0.05, False, 0.2, True)
    P, N, A = [], [], []
    ex = TopExp_Explorer(shape, TopAbs_FACE)
    while ex.More():
        face = TopoDS.Face_s(ex.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is not None:
            trsf = loc.Transformation()
            xyz = np.array([[q.X(), q.Y(), q.Z()] for q in (tri.Node(i).Transformed(trsf) for i in range(1, tri.NbNodes() + 1))])
            T = np.array([tri.Triangle(i).Get() for i in range(1, tri.NbTriangles() + 1)]) - 1
            if face.Orientation() == TopAbs_REVERSED:
                T = T[:, [0, 2, 1]]
            a, b, c = xyz[T[:, 0]], xyz[T[:, 1]], xyz[T[:, 2]]
            cr = np.cross(b - a, c - a)
            area = np.linalg.norm(cr, axis=1) / 2
            ok = area > 1e-12
            P.append((a + b + c)[ok] / 3)
            N.append(cr[ok] / (2 * area[ok, None]))
            A.append(area[ok])
        ex.Next()
    P, N, A = np.vstack(P), np.vstack(N), np.concatenate(A)
    rng = np.random.default_rng(seed)
    k = rng.choice(len(P), size=min(n, len(P)), replace=False, p=A / A.sum())
    return P[k], N[k], float(A.sum())


SELF_HIT = 0.1  # mm; triangulation deflection is 0.05 mm, real walls are far thicker


def thickness(shape, P: np.ndarray, N: np.ndarray) -> np.ndarray:
    """Distance along the inward normal (-N, N outward) to the first surface hit; inf if nothing is hit."""
    isec = IntCurvesFace_ShapeIntersector()
    isec.Load(shape, 1e-6)
    out = np.full(len(P), np.inf)
    for i, (p, n) in enumerate(zip(P, N)):
        try:
            isec.Perform(gp_Lin(gp_Pnt(*p), gp_Dir(*(-n))), 1e-4, 1e4)
        except Exception:  # noqa: BLE001 - OpenCASCADE throws on a few degenerate rays; skip them
            continue
        if isec.IsDone():
            w = [isec.WParameter(j) for j in range(1, isec.NbPnt() + 1)]
            w = [v for v in w if v > SELF_HIT]  # sample points sit up to the triangulation sag off their own face
            if w:
                out[i] = min(w)
    return out


def check(path: str, samples: int, limit: float) -> dict:
    t0 = time.time()
    s = load_solid(path)
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(s, g)
    b = Bnd_Box()
    BRepBndLib.AddOptimal_s(s, b, False, False)
    lo, hi = np.array(b.Get()[:3]), np.array(b.Get()[3:])
    P, N, area = surface_samples(s, samples)
    t = thickness(s, P, N)
    hit = np.isfinite(t)
    return dict(step=path, solids=count(s, TopAbs_SOLID), volume_mm3=g.Mass(), bbox_min=lo.round(3).tolist(),
                bbox_max=hi.round(3).tolist(), area_mm2=area, samples=int(len(P)), rays_without_hit=int((~hit).sum()),
                thickness_p01=float(np.percentile(t[hit], 1)) if hit.any() else None,
                thickness_p05=float(np.percentile(t[hit], 5)) if hit.any() else None,
                thickness_median=float(np.median(t[hit])) if hit.any() else None,
                thin_area_fraction=float((t[hit] < limit).mean()) if hit.any() else None, limit_mm=limit,
                seconds=round(time.time() - t0, 1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("steps", nargs="+")
    ap.add_argument("--samples", type=int, default=6000)
    ap.add_argument("--limit", type=float, default=1.27)
    ap.add_argument("--jsonl")
    a = ap.parse_args()
    out = open(a.jsonl, "a") if a.jsonl else None
    for p in a.steps:
        try:
            r = check(p, a.samples, a.limit)
        except Exception as e:  # noqa: BLE001 - reported per file
            r = dict(step=p, error=f"{type(e).__name__}: {e}"[:300])
        r["id"] = Path(p).stem
        print(json.dumps(r), flush=True)
        if out:
            out.write(json.dumps(r) + "\n")
            out.flush()


if __name__ == "__main__":
    main()
