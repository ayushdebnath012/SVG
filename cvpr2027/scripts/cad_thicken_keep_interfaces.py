"""Reference redesign for the CAD + FEM redesign tasks: thicken a solid, then restore its interfaces exactly.

The solid is offset outward by delta (OpenCASCADE offset, rounded joins). Interface holes are then re-drilled at their
original radius along their original axis, and interface planes are cut flat again at their original position, so
bolt holes, load holes and clamped / loaded faces are where they were. Only through holes and extreme planes (nothing
of the part lies beyond them) can be restored this way; the caller checks that.

Run with a Python that has OCP (OpenCASCADE bindings), e.g. the BenchCAD venv:
  python cad_thicken_keep_interfaces.py in.step out.step spec.json delta_mm
spec.json: {"L": ..., "holes": [{"centre", "axis", "radius", "length"}], "planes": [{"normal", "offset"}]}
Prints one JSON line: {"ok", "volume_in", "volume_out", "error"}.
"""
from __future__ import annotations

import json
import sys

import numpy as np
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.BRepOffset import BRepOffset_Skin
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeOffsetShape
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.GeomAbs import GeomAbs_Arc
from OCP.GProp import GProp_GProps
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Reader, STEPControl_Writer
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt


def read(path: str):
    r = STEPControl_Reader()
    if r.ReadFile(path) != IFSelect_RetDone:
        raise ValueError("cannot read STEP")
    r.TransferRoots()
    return r.OneShape()


def volume(s) -> float:
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(s, g)
    return g.Mass()


def solids(s) -> int:
    ex, n = TopExp_Explorer(s, TopAbs_SOLID), 0
    while ex.More():
        n += 1
        ex.Next()
    return n


def cut(a, b):
    op = BRepAlgoAPI_Cut(a, b)
    if not op.IsDone():
        raise ValueError("boolean cut failed")
    return op.Shape()


def frame(n: np.ndarray) -> np.ndarray:
    x = np.cross(n, [1, 0, 0] if abs(n[0]) < 0.9 else [0, 1, 0])
    return x / np.linalg.norm(x)


def main() -> None:
    src, dst, spec_path, delta = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
    spec = json.load(open(spec_path))
    L = spec["L"]
    out = dict(ok=False)
    try:
        shape = read(src)
        out["volume_in"] = volume(shape)
        mk = BRepOffsetAPI_MakeOffsetShape()
        mk.PerformByJoin(shape, delta, 1e-4 * L, BRepOffset_Skin, False, False, GeomAbs_Arc)
        if not mk.IsDone():
            raise ValueError("offset failed")
        s = mk.Shape()
        for h in spec["holes"]:
            e, c = np.array(h["axis"]), np.array(h["centre"])
            half = h["length"] / 2 + 2 * delta + 1e-3 * L
            base = c - e * half
            s = cut(s, BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(*base), gp_Dir(*e)), h["radius"], 2 * half).Shape())
        for p in spec["planes"]:
            n = np.array(p["normal"])
            x = frame(n)
            y = np.cross(n, x)
            ctr = np.array(spec.get("centre", [0, 0, 0]))
            p0 = ctr - (n @ ctr - p["offset"]) * n
            S = 4 * L
            origin = p0 - S * x - S * y
            box = BRepPrimAPI_MakeBox(gp_Ax2(gp_Pnt(*origin), gp_Dir(*n), gp_Dir(*x)), 2 * S, 2 * S, S).Shape()
            s = cut(s, box)
        if solids(s) != 1:
            raise ValueError(f"{solids(s)} solids after the edit")
        if not BRepCheck_Analyzer(s).IsValid():
            raise ValueError("invalid shape after the edit")
        w = STEPControl_Writer()
        w.Transfer(s, STEPControl_AsIs)
        w.Write(dst)
        out.update(ok=True, volume_out=volume(s))
    except Exception as e:  # noqa: BLE001 - reported to the caller
        out["error"] = f"{type(e).__name__}: {e}"[:300]
    print(json.dumps(out))


if __name__ == "__main__":
    main()
