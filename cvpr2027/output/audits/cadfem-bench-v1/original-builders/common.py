"""Shared paths, task/reference records, tolerance policy and OpenCASCADE helpers for CADFEM-Bench v1.

Every admitted task is one record in candidate/tasks.jsonl (what a model sees) and one record in
evaluator/references.jsonl (what the grader sees). Reference values are source-published FEM output, a closed
form, a publisher evaluator value, or (SimJEB only, labelled `verifier`) the validated SimJEB FEM grader.
Nothing here runs a solver.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent                      # cvpr2027/
DATA = ROOT / "data"
OUT = ROOT / "output/datasets/cadfem-bench-v1"
CAND = OUT / "candidate"
EVAL = OUT / "evaluator"
META = DATA / "cadfem-bench-v1"
VERSION = "1.0"
DATE = "2026-10-13"

TRACKS = {
    "A": "Supplied CAD -> FEM: the model receives the part/assembly CAD and the source analysis set-up and must "
         "compute the requested results.",
    "B": "Specification/drawing -> CAD -> FEM: the model receives a drawing or written specification, must build "
         "the CAD itself and then run the analysis on its own model.",
    "C": "Design under FEM verification: the model must design or modify a part; the benchmark FEM grader decides "
         "validity, pass/fail and mass.",
}

# Default relative tolerances by quantity kind. A source's own tolerance overrides these (see README).
TOL = {
    "gold": dict(displacement=0.05, frequency=0.05, temperature=0.05, stress=0.10, force=0.05, scalar=0.05, time=0.05),
    "silver": dict(displacement=0.10, frequency=0.10, temperature=0.10, stress=0.20, force=0.10, scalar=0.10, time=0.10),
    "control": dict(displacement=0.05, frequency=0.05, temperature=0.05, stress=0.10, force=0.05, scalar=0.05, time=0.05),
}

REF_CLASSES = {
    "published_raw_field": "maximum/derived value read from the source's own saved solver result file",
    "published_table": "value from a source-published numerical table, CSV or spreadsheet cell",
    "published_legend": "value printed on a source-published result plot legend or report table",
    "publisher_evaluator": "value the publisher's own benchmark evaluator checks against",
    "closed_form": "exact closed-form solution of the stated problem",
    "benchmark_target": "published NAFEMS/solver benchmark output for the stated problem",
    "verifier": "SimJEB FEM grader (FEniCSx replay of SimJEB, matches published OptiStruct displacement within 3 %)",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jdump(o, p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o, indent=2, ensure_ascii=False) + "\n")


def jsonl(rows, p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def put(tid: str, src: Path, name: str | None = None, role: str = "cad") -> dict:
    """Place one model-visible input file under candidate/tasks/<tid>/ (hard link when possible)."""
    src = Path(src)
    dst = CAND / "tasks" / tid / (name or src.name)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)
    return dict(path=str(dst.relative_to(CAND)), role=role, bytes=dst.stat().st_size, sha256=sha256(dst))


def write_input(tid: str, name: str, text: str, role: str = "spec") -> dict:
    dst = CAND / "tasks" / tid / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text)
    return dict(path=str(dst.relative_to(CAND)), role=role, bytes=dst.stat().st_size, sha256=sha256(dst))


def out(key: str, unit: str, definition: str) -> dict:
    return dict(key=key, unit=unit, definition=definition)


def refv(value: float, kind: str, ref_class: str, provenance: str, tier: str = "gold", tol: float | None = None,
         tol_kind: str = "rel", offset: float | None = None, graded: bool = True, note: str | None = None) -> dict:
    """One hidden reference output. tol_kind: rel |pred-ref| <= tol*|ref|; rel_offset compares (x - offset);
    abs |pred-ref| <= tol; bool exact match."""
    r = dict(value=value, kind=kind, ref_class=ref_class, provenance=provenance, graded=graded,
             tol=dict(kind=tol_kind, value=TOL[tier][kind] if tol is None else tol))
    if offset is not None:
        r["tol"]["offset"] = offset
    if note:
        r["note"] = note
    return r


def task(tid: str, track: str, tier: str, family: str, title: str, physics: list[str], prompt: str, inputs: list[dict],
         outputs: list[dict], source: dict, complexity: dict, refs: dict, grader: str = "numeric",
         flags: list[str] | None = None, extra_eval: dict | None = None) -> tuple[dict, dict]:
    assert track in TRACKS and tier in TOL, (track, tier)
    keys = {o["key"] for o in outputs}
    assert set(refs) <= keys, (tid, set(refs) - keys)
    submit = ("Write results.json as {\"outputs\": {" + ", ".join(f"\"{o['key']}\": <number>" for o in outputs)
              + "}} with the units listed.")
    if track in "BC":
        submit += " Also submit the CAD you analysed as part.step (millimetres) and the script that built it."
    t = dict(task_id=tid, track=track, tier=tier, family=family, title=title, physics=physics,
             prompt=prompt.strip() + "\n\nOutputs:\n" + "\n".join(f"- {o['key']} [{o['unit']}]: {o['definition']}" for o in outputs)
             + "\n\n" + submit, inputs=inputs, outputs=outputs, complexity=complexity,
             source=dict(name=source["name"], url=source["url"], license=source.get("license", "not stated"),
                         redistributable=source.get("redistributable", False)))
    e = dict(task_id=tid, grader=grader, tier=tier, family=family, track=track, references=refs,
             flags=flags or [], source=source)
    if extra_eval:
        e.update(extra_eval)
    return t, e


# ------------------------------------------------------------------ OpenCASCADE helpers (tmp/cq-env)
def _occ():
    from OCP import BRep, BRepTools, BRepGProp, GProp, STEPControl, IGESControl, TopAbs, TopExp, TopTools, TopoDS
    from OCP import BRepAdaptor, GeomAbs, Bnd, BRepBndLib, BRepExtrema, BRepBuilderAPI, gp, BRepCheck, Interface
    return locals()


def read_shape(p: Path):
    o = _occ()
    p = Path(p)
    suf = p.suffix.lower()
    if suf in (".brp", ".brep"):
        s = o["TopoDS"].TopoDS_Shape()
        o["BRepTools"].BRepTools.Read_s(s, str(p), o["BRep"].BRep_Builder())
        return s
    r = o["STEPControl"].STEPControl_Reader() if suf in (".step", ".stp") else o["IGESControl"].IGESControl_Reader()
    assert r.ReadFile(str(p)) == 1, p
    r.TransferRoots()
    return r.OneShape()


class quiet:
    """Silence C-level stdout (OpenCASCADE transfer statistics)."""
    def __enter__(self):
        import sys
        sys.stdout.flush()
        self.fd = os.dup(1)
        self.null = os.open(os.devnull, os.O_WRONLY)
        os.dup2(self.null, 1)

    def __exit__(self, *a):
        os.dup2(self.fd, 1)
        os.close(self.null)
        os.close(self.fd)


def write_step(shape, p: Path) -> None:
    with quiet():
        _write_step(shape, p)


def _write_step(shape, p: Path) -> None:
    o = _occ()
    o["Interface"].Interface_Static.SetCVal_s("write.step.unit", "MM")
    w = o["STEPControl"].STEPControl_Writer()
    w.Transfer(shape, o["STEPControl"].STEPControl_AsIs)
    p.parent.mkdir(parents=True, exist_ok=True)
    assert w.Write(str(p)) == 1, p


def shape_summary(shape) -> dict:
    o = _occ()
    TopAbs, TopExp, TopTools = o["TopAbs"], o["TopExp"], o["TopTools"]
    cnt = {}
    for name, kind in (("solids", TopAbs.TopAbs_SOLID), ("faces", TopAbs.TopAbs_FACE)):
        m = TopTools.TopTools_IndexedMapOfShape()
        TopExp.TopExp.MapShapes_s(shape, kind, m)
        cnt[name] = m.Extent()
    props = o["GProp"].GProp_GProps()
    o["BRepGProp"].BRepGProp.VolumeProperties_s(shape, props)
    box = o["Bnd"].Bnd_Box()
    o["BRepBndLib"].BRepBndLib.AddOptimal_s(shape, box, False, False)
    x0, y0, z0, x1, y1, z1 = box.Get()
    valid = o["BRepCheck"].BRepCheck_Analyzer(shape).IsValid()
    return dict(valid=bool(valid), **cnt, volume_mm3=round(props.Mass(), 3),
                bbox_mm=[round(v, 4) for v in (x0, y0, z0, x1, y1, z1)])


def faces(shape) -> list:
    o = _occ()
    m = o["TopTools"].TopTools_IndexedMapOfShape()
    o["TopExp"].TopExp.MapShapes_s(shape, o["TopAbs"].TopAbs_FACE, m)
    cast = getattr(o["TopoDS"].TopoDS, "Face_s", None) or o["TopoDS"].TopoDS.Face
    return [cast(m.FindKey(i)) for i in range(1, m.Extent() + 1)]


def face_descriptor(face, index: int) -> dict:
    """Geometric description of a face that does not depend on any CAD system's face numbering."""
    o = _occ()
    GeomAbs = o["GeomAbs"]
    props = o["GProp"].GProp_GProps()
    o["BRepGProp"].BRepGProp.SurfaceProperties_s(face, props)
    c = props.CentreOfMass()
    ad = o["BRepAdaptor"].BRepAdaptor_Surface(face)
    t = ad.GetType()
    d = dict(face_index=index, area_mm2=round(props.Mass(), 3), centroid_mm=[round(c.X(), 3), round(c.Y(), 3), round(c.Z(), 3)])
    rev = face.Orientation() == o["TopAbs"].TopAbs_REVERSED
    if t == GeomAbs.GeomAbs_Plane:
        n = ad.Plane().Axis().Direction()
        s = -1 if rev else 1
        d.update(type="plane", outward_normal=[round(s * n.X(), 4), round(s * n.Y(), 4), round(s * n.Z(), 4)])
    elif t == GeomAbs.GeomAbs_Cylinder:
        cy = ad.Cylinder()
        a, p = cy.Axis().Direction(), cy.Axis().Location()
        d.update(type="cylinder", radius_mm=round(cy.Radius(), 4), axis_direction=[round(a.X(), 4), round(a.Y(), 4), round(a.Z(), 4)],
                 axis_point_mm=[round(p.X(), 3), round(p.Y(), 3), round(p.Z(), 3)], concave=bool(rev))
    else:
        d["type"] = {GeomAbs.GeomAbs_Cone: "cone", GeomAbs.GeomAbs_Sphere: "sphere", GeomAbs.GeomAbs_Torus: "torus",
                     GeomAbs.GeomAbs_BSplineSurface: "bspline", GeomAbs.GeomAbs_BezierSurface: "bezier",
                     GeomAbs.GeomAbs_SurfaceOfRevolution: "revolution", GeomAbs.GeomAbs_SurfaceOfExtrusion: "extrusion",
                     GeomAbs.GeomAbs_OffsetSurface: "offset"}.get(t, "other")
    box = o["Bnd"].Bnd_Box()
    o["BRepBndLib"].BRepBndLib.Add_s(face, box)
    d["bbox_mm"] = [round(v, 3) for v in box.Get()]
    return d


def describe_faces(desc: list[dict]) -> str:
    lines = []
    for d in desc:
        s = f"face {d['face_index']}: {d['type']}, area {d['area_mm2']:.2f} mm^2, centroid {tuple(d['centroid_mm'])} mm"
        if d["type"] == "plane":
            s += f", outward normal {tuple(d['outward_normal'])}"
        if d["type"] == "cylinder":
            s += f", radius {d['radius_mm']} mm, axis {tuple(d['axis_direction'])} through {tuple(d['axis_point_mm'])}"
            s += " (hole/bore surface)" if d.get("concave") else " (boss/shaft surface)"
        lines.append(s)
    return "; ".join(lines)
