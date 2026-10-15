"""Evaluator-only reference solids for the drawing/specification -> CAD tasks (v1.3).

Each reference is built from the task's own specification (FEMCAD-Hard text, NAFEMS published geometry definitions)
or taken from the source CAD (NAFEMS LE10), and is accepted only if its OpenCASCADE volume matches an independent
value: a closed form (FEMCAD-Hard, LE1 ring area x exchange thickness, LE10 elliptic-plate volume) or Pappus's theorem
for the revolved LE11 profile. The grader aligns a submitted part.step to the reference (bounding-box centres, the 24
proper axis rotations) and requires a relative symmetric volume difference <= 2 %. Nothing here is a FEM reference.

  tmp/cq-env/bin/python scripts/cadfem_bench/geometry_refs.py     # writes output/geometry-references-v1.3/
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import common as C

OUTDIR = C.ROOT / "output/geometry-references-v1.3"
LE10_STEP = C.ROOT / "tmp/engineering-fem-crawl/repo/examples/nafems-le10.step"
LE1_THICKNESS = 100.0   # exchange convention for the 2-D plane-stress LE1 membrane (does not affect the stress answer)


def _cq():
    import cadquery as cq
    return cq


def femcad_031():
    cq = _cq()
    s = cq.Workplane().sphere(10).cut(cq.Workplane().sphere(3))
    return s.val().wrapped, 4 / 3 * math.pi * (10 ** 3 - 3 ** 3), "spherical shell r 3-10 mm"


def femcad_057():
    cq = _cq()
    up = cq.Workplane().box(10, 20, 50, centered=False)
    foot = cq.Workplane().box(50, 20, 10, centered=False)
    body = up.union(foot)
    body = body.edges(cq.selectors.BoxSelector((9.9, -1, 9.9), (10.1, 21, 10.1))).fillet(3)
    r = 3.0
    return body.val().wrapped, 10 * 20 * 50 + 50 * 20 * 10 - 10 * 20 * 10 + (r * r - math.pi * r * r / 4) * 20, \
        "L-bracket, R3 concave fillet on the inner corner edge"


def femcad_058():
    cq = _cq()
    shell = cq.Workplane().sphere(100).cut(cq.Workplane().sphere(80))
    octant = shell.intersect(cq.Workplane().box(100, 100, 100, centered=False))
    return octant.val().wrapped, math.pi / 6 * (100 ** 3 - 80 ** 3), "octant of a hollow sphere r 80-100 mm"


def femcad_062():
    cq = _cq()
    plate = cq.Workplane().box(100, 5, 50, centered=False)
    hole = cq.Workplane("XZ").center(50, 25).circle(10).extrude(-5)
    return plate.cut(hole).val().wrapped, 100 * 5 * 50 - math.pi * 10 ** 2 * 5, "plate with a through hole r 10 mm"


def femcad_067():
    cq = _cq()
    tube = cq.Workplane().circle(100).circle(20).extrude(140)
    return tube.val().wrapped, math.pi * (100 ** 2 - 20 ** 2) * 140, "tube r 20-100 mm, length 140 mm"


def nafems_le1():
    cq = _cq()
    a, b, c, d = 1000.0, 2750.0, 3250.0, 2000.0      # published geometry definition (nafems-le1.geo)
    outer = cq.Workplane().ellipse(c, b).extrude(LE1_THICKNESS)
    inner = cq.Workplane().ellipse(d, a).extrude(LE1_THICKNESS)
    quad = cq.Workplane().box(c, b, LE1_THICKNESS, centered=False)
    ring = outer.cut(inner).intersect(quad)
    return ring.val().wrapped, math.pi / 4 * (c * b - d * a) * LE1_THICKNESS, \
        f"quarter elliptic ring (inner 2000 x 1000 mm, outer 3250 x 2750 mm) extruded {LE1_THICKNESS:g} mm along +z"


def nafems_le10():
    shape = C.read_shape(LE10_STEP)
    s = C.shape_summary(shape)
    thickness = s["bbox_mm"][5] - s["bbox_mm"][2]
    return shape, math.pi / 4 * (3250 * 2750 - 2000 * 1000) * thickness, \
        f"source STEP: quarter elliptic thick plate, thickness {thickness:g} mm"


def nafems_le11():
    """Revolve the published LE11 profile (nafems-le11.geo, metres) by 90 degrees about z, in millimetres."""
    cq = _cq()
    r_in, r_out = 1000.0, 1400.0
    zs = r_in * math.sin(math.pi / 4)                           # exact spherical junction z = sqrt(0.5) m
    x_out = math.sqrt(r_out ** 2 - zs ** 2)
    z_t, z_top = zs + 345.0 + 345.0, zs + 345.0 + 345.0 + 400.0
    a_in, a_out = math.atan2(zs, zs), math.atan2(zs, x_out)
    mid = lambda r, ang: (r * math.cos(ang / 2), r * math.sin(ang / 2))
    prof = (cq.Workplane("XZ").moveTo(r_in, 0).lineTo(r_out, 0).threePointArc(mid(r_out, a_out), (x_out, zs))
            .lineTo(r_in, z_t).lineTo(r_in, z_top).lineTo(zs, z_top).lineTo(zs, zs).threePointArc(mid(r_in, a_in), (r_in, 0)).close())
    face = prof.val()
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    f = BRepBuilderAPI_MakeFace(face.wrapped).Face()
    g = GProp_GProps()
    BRepGProp.SurfaceProperties_s(f, g)
    pappus = math.pi / 2 * g.Mass() * g.CentreOfMass().X()
    solid = prof.revolve(90, (0, 0, 0), (0, 1, 0))
    return solid.val().wrapped, pappus, "LE11 cylinder/taper/sphere profile revolved 90 deg about z (Pappus check)"


BUILDERS = {"B-FEMCAD-031": femcad_031, "B-FEMCAD-057": femcad_057, "B-FEMCAD-058": femcad_058,
            "B-FEMCAD-062": femcad_062, "B-FEMCAD-067": femcad_067, "B-NAFEMS-LE1": nafems_le1,
            "B-NAFEMS-LE10": nafems_le10, "B-NAFEMS-LE11": nafems_le11}


def build_all() -> dict:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = {}
    for tid, fn in BUILDERS.items():
        shape, expected, desc = fn()
        s = C.shape_summary(shape)
        err = abs(s["volume_mm3"] - expected) / expected
        assert s["valid"] and s["solids"] >= 1 and err < 1e-4, (tid, s, expected, err)
        path = OUTDIR / f"{tid}-reference.step"
        C.write_step(shape, path)
        back = C.shape_summary(C.read_shape(path))
        assert abs(back["volume_mm3"] - expected) / expected < 1e-4, (tid, back)
        out[tid] = dict(task_id=tid, reference_step=str(path.relative_to(C.ROOT.parent)), description=desc,
                        volume_mm3=s["volume_mm3"], independent_volume_mm3=round(expected, 3), relative_volume_error=err,
                        bbox_mm=s["bbox_mm"], solids=s["solids"], faces=s["faces"], sha256=C.sha256(path))
    C.jdump(out, OUTDIR / "references.json")
    return out


if __name__ == "__main__":
    for tid, r in build_all().items():
        print(f"{tid:16s} V={r['volume_mm3']:.6g} vs {r['independent_volume_mm3']:.6g} (err {r['relative_volume_error']:.1e}) "
              f"faces {r['faces']} bbox {r['bbox_mm']}")
