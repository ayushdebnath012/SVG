"""Track A, gold: AgentFEM double-arm bracket family (HF HaomingLuo/AgentFEM-Bracket-Elasticity, CC BY 4.0).

Publisher test split only (32 fresh geometries). Unit fix: the source STEP header says millimetres but its numbers are
metres (they coincide with the FEM coordinates in metres). The task ships a copy scaled by 1000 so that the file is in
true millimetres; the scaled bounding box is checked against the published FEM node coordinates (x 1000).
References: the publisher's summary.json (seat_mean = mean of -u_z over the top-seat nodes, max |u|).
"""
from __future__ import annotations

import json

import numpy as np

import common as C

SRC = C.DATA / "web-agentfem-brackets"
SOURCE = dict(name="AgentFEM Bracket Elasticity (Haoming Luo, 2026)",
              url="https://huggingface.co/datasets/HaomingLuo/AgentFEM-Bracket-Elasticity", license="CC BY 4.0",
              redistributable=True)


def _scaled(shape, k: float):
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Pnt, gp_Trsf
    t = gp_Trsf()
    t.SetScale(gp_Pnt(0, 0, 0), k)
    return BRepBuilderAPI_Transform(shape, t, True).Shape()


def build() -> list:
    cat = json.loads((SRC / "catalog.json").read_text())
    rows = []
    for r in cat["records"]:
        if r["split"] != "test":
            continue
        summ = json.loads((SRC / r["source_summary"]).read_text())
        tid = f"A-AGENTFEM-{r['id']}"
        t_pa = r["boundary_conditions"]["traction_Pa"][2]
        z_top = r["boundary_conditions"]["traction_plane_m"].split("=")[1]
        load = r["physical_load_N"]
        step = C.CAND / "tasks" / tid / "geometry.step"
        shape = _scaled(C.read_shape(SRC / r["cad"]), 1000.0)
        C.write_step(shape, step)
        pts = np.load(SRC / r["fem_fields"])["points"] * 1e3
        bb = C.shape_summary(C.read_shape(step))["bbox_mm"]
        assert np.abs(np.array(bb) - np.r_[pts.min(0), pts.max(0)]).max() < 0.2, (tid, bb)
        z_mm = float(z_top) * 1e3
        inputs = [dict(path=str(step.relative_to(C.CAND)), role="cad", bytes=step.stat().st_size, sha256=C.sha256(step))]
        prompt = f"""Support bracket (one member of a parametric double-arm bracket family). geometry.step holds one solid in millimetres (height {z_mm:g} mm).

Material: linear isotropic elastic, E = 70 GPa, Poisson ratio 0.33 (density 2700 kg/m^3, gravity not applied).
Supports: the foot undersides, i.e. every face lying in the plane z = 0, are fully fixed (all displacement components zero).
Load: a uniform downward traction of {-t_pa / 1e6:.6g} MPa in the -z direction over the top seat face (the face in the plane z = {z_mm:g} mm); total {load:g} N.
Analysis: 3-D linear elasticity, small displacements. The publisher used quadratic tetrahedra with a nominal 9 mm mesh."""
        outs = [C.out("seat_mean_displacement_mm", "mm", f"mean of the downward displacement -u_z over the top seat face (z = {z_mm:g} mm)"),
                C.out("max_displacement_mm", "mm", "maximum displacement magnitude anywhere in the bracket")]
        prov = f"publisher {r['source_summary']}"
        refs = {k: C.refv(summ[k], "displacement", "published_table", prov, tol=0.10,
                          note="publisher states the 9 mm reference mesh is not mesh-converged")
                for k in ("seat_mean_displacement_mm", "max_displacement_mm")}
        rows.append(C.task(tid, "A", "gold", "agentfem-bracket", f"AgentFEM bracket {r['id']} ({load:g} N seat load)",
                           ["linear static"], prompt, inputs, outs, SOURCE,
                           dict(solids=r["geometry"]["solids"], faces=r["geometry"]["faces"], assembly=False), refs,
                           flags=["source STEP unit error fixed: shipped copy scaled x1000 to true millimetres and checked against the FEM nodes",
                                  "one parametric family: report as a family macro-average"]))
    return rows
