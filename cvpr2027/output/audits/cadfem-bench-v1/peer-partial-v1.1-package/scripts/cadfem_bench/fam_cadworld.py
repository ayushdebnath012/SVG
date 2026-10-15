"""Track A: CADWorld FreeCAD/CalculiX FEM tasks (Zdong104/CADWORLD, Apache-2.0).

Geometry is the final PartDesign body of the publisher's precondition document (no results inside). Constraints
come from the publisher's solved reference document; references are the values the publisher's own evaluator
checks (+/-5 %). freecad-fem-002 is held: its support is a single edge and its load references an auxiliary Box
object, so its 76.6 GPa peak is a singular-support artefact. freecad-fem-003 is excluded: 20 MN on a 30 mm
specimen gives 811 mm of displacement, outside the small-displacement analysis the task prescribes.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import common as C
from fcstd import FCStd

SRC = C.DATA / "web-cadworld-fem"
SOURCE = dict(name="CADWorld FEM benchmark (Zdong104/CADWORLD; HF Zihan1004/CADWORLD)",
              url="https://github.com/Zdong104/CADWORLD", license="Apache-2.0 (publisher HF metadata)", redistributable=True)
CASES = {
    "001": dict(obj="Pocket001", fixed=[6], load=[38], dir=(0, 1, 0), force=200.0, tier="gold", mesh=(2.0, 0.5),
                title="Multi-feature aluminium part, end load"),
}
KEYS = {"Displacement Magnitude": ("max_displacement_mm", "displacement", 1e3, "maximum nodal displacement magnitude"),
        "von Mises Stress": ("max_von_mises_MPa", "stress", 1e-6, "maximum nodal von Mises stress"),
        "Tresca Stress": ("max_tresca_MPa", "stress", 1e-6, "maximum nodal Tresca stress"),
        "Major Principal Stress": ("max_principal_MPa", "stress", 1e-6, "maximum nodal major principal stress")}


def build() -> list:
    cat = {r["id"].split("-")[-1]: r for r in json.loads((SRC / "catalog.json").read_text())["records"]}
    rows = []
    for k, cs in CASES.items():
        rec = cat[k]
        tid = f"A-CADWORLD-{k}"
        pre = FCStd(SRC / f"evaluation_examples/fixtures/precondition/freecad-fem-{k}-precondition.FCStd")
        ref_doc = FCStd(SRC / f"evaluation_examples/fixtures/fem/freecad-fem-{k}.FCStd")
        assert [int(s[4:]) for _, s in ref_doc.links("ConstraintFixed")] == cs["fixed"]
        assert [int(s[4:]) for _, s in ref_doc.links("ConstraintForce")] == cs["load"]
        with tempfile.TemporaryDirectory() as td:
            shape = C.read_shape(pre.extract(pre.shape_member(cs["obj"]), Path(td) / "p.brp"))
        fs = C.faces(shape)
        summ = C.shape_summary(shape)
        step = C.CAND / "tasks" / tid / "part.step"
        C.write_step(shape, step)
        desc = [C.face_descriptor(f, i + 1) for i, f in enumerate(fs)]
        mat = ref_doc.material("MaterialSolid")
        e_mpa = float(mat["YoungsModulus"].split()[0]) / 1e3
        inputs = [dict(path=str(step.relative_to(C.CAND)), role="cad", bytes=step.stat().st_size, sha256=C.sha256(step)),
                  C.write_input(tid, "faces.json", json.dumps(dict(faces=desc), indent=1))]
        img = SRC / f"evaluation_examples/examples/fem/images/freecad-fem-{k}.png"
        if img.exists():
            inputs.append(C.put(tid, img, "publisher-task-image.png", role="figure"))
        f = cs["force"]
        prompt = f"""FreeCAD/CalculiX benchmark part ({cs['title']}). part.step is the single solid in millimetres ({summ['faces']} faces, bounding box {summ['bbox_mm']} mm). faces.json describes every face.

Material: {mat['Name']}, linear isotropic elastic, E = {e_mpa:g} MPa, Poisson ratio {mat['PoissonRatio']}.
Analysis: linear static, small displacements, no gravity.
Supports: fixed (all displacement components zero) on {C.describe_faces([desc[i - 1] for i in cs['fixed']])}.
Load: total force {f:g} N along {cs['dir']} applied uniformly over {C.describe_faces([desc[i - 1] for i in cs['load']])}.
Mesh protocol of the publisher's reference solution (results are compared under this protocol): Gmsh 3-D mesh, first-order (linear) tetrahedra, maximum element size {cs['mesh'][0]} mm, minimum {cs['mesh'][1]} mm, CalculiX solver. Report nodal extrema of that solution."""
        outs, refs = [], {}
        for chk in rec["publisher_evaluator_checks"]:
            if chk["statistic"] != "max":
                continue
            key, kind, scale, definition = KEYS[chk["column"]]
            outs.append(C.out(key, "mm" if kind == "displacement" else "MPa", definition))
            refs[key] = C.refv(chk["published_expected"] * scale, kind, "publisher_evaluator",
                               f"CADWorld reference CSV {rec['fem_csv']} column '{chk['column']}' max (publisher evaluator +/-5 %)",
                               tier=cs["tier"], tol=0.05)
        rows.append(C.task(tid, "A", cs["tier"], "cadworld-freecad-fem", f"CADWorld: {cs['title']}", ["linear static"],
                           prompt, inputs, outs, SOURCE,
                           dict(solids=summ["solids"], faces=summ["faces"], assembly=False, cad_bbox_mm=summ["bbox_mm"]), refs,
                           flags=["protocol-bound: publisher mesh (first-order tets) fixes the reference; publisher tolerance 5 %",
                                  "linear-elastic stresses exceed material yield; computational benchmark, not a strength verdict"]))
    return rows
