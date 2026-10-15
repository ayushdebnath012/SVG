"""Track A, gold: component studies of a 3D-printable 15:1 cycloidal drive (FreeCAD 1.1 + CalculiX 2.21).

Geometry: the B-Rep stored in each source FCStd, exported unchanged to STEP. Supports: the FCStd ConstraintFixed
faces, checked against the deck's fixed node set. Loads: per-face CLOAD resultants of the source-corrected deck
(the source author multiplied FreeCAD's CLOAD entries by 1000; both decks are kept in the source collection).
References: maxima of the saved FRD fields (catalog `max_translation_mm`, `derived_max_averaged_nodal_vm_MPa`).
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np

import common as C
from fcstd import FCStd, nodes_on_faces, read_ccx

SRC = C.DATA / "web-cad-fem-cycloidal-drive"
SOURCE = dict(name="3D-printable cycloidal drive FEA (jagathsrujan/3d-printable-cycloidal-drive)",
              url="https://github.com/jagathsrujan/3d-printable-cycloidal-drive",
              license="No repository license; FCStd metadata 'All rights reserved'. Local research only.",
              redistributable=False)
NAMES = {"Coupler": "output coupler", "Disk": "cycloidal disk", "DiskPLA": "cycloidal disk", "FlangeP1": "output flange P1",
         "FlangeP2": "output flange P2", "Housing": "ring-gear housing", "Housing_lin": "ring-gear housing",
         "Lid": "housing lid", "Mount": "motor mount", "Ring1x15": "spacer ring 1x15", "Ring1x6": "spacer ring 1x6",
         "Ring4x6": "spacer ring 4x6", "ShaftP1": "input shaft P1", "ShaftP2_radial": "input eccentric-cam shaft P2 (radial cam load)",
         "Spacer6": "spacer 6", "OutPin": "output pin", "RingPin": "ring pin"}


def build() -> list:
    cat = json.loads((SRC / "catalog.json").read_text())
    rows, seen = [], set()
    for r in cat["records"]:
        if not r.get("primary_component_candidate"):
            continue
        frd = SRC / r["file"]
        stem = frd.stem.replace("_fixed", "")
        folder = "pla" if "/pla/" in r["file"] else "petg_cf"
        e_mod = float(r["elastic_card"][1].split(",")[0])
        material = "steel" if e_mod > 1e5 else ("PETG-CF" if folder == "petg_cf" else "PLA")
        if folder == "pla" and material != "steel":
            continue                                # PLA reruns duplicate the PETG-CF geometry and load set
        key = (stem, material)
        if key in seen:
            continue
        seen.add(key)
        fc_path = next(frd.parent.glob("*.FCStd"))
        doc = FCStd(fc_path)
        deck = read_ccx(frd.with_suffix(".inp"))
        tid = f"A-CYC-{stem.replace('_', '-')}-{material.replace('-', '')}"
        fixed_obj = doc.of_type("ConstraintFixed")
        assert fixed_obj, tid
        part = doc.links(fixed_obj[0])[0][0]
        fixed = sorted({int(s.replace("Face", "")) for fo in fixed_obj for o, s in doc.links(fo)})
        loads = {int(k.replace("Face", "")): v for k, v in deck["face_loads"].items()}
        with tempfile.TemporaryDirectory() as td:
            brp = doc.extract(doc.shape_member(part), Path(td) / "part.brp")
            shape = C.read_shape(brp)
        fs = C.faces(shape)
        summ = C.shape_summary(shape)
        step = C.CAND / "tasks" / tid / "part.step"
        C.write_step(shape, step)
        coords = np.array([deck["nodes"][n] for k, v in deck["nsets"].items() if k.startswith(tuple(fixed_obj)) for n in v])
        on_fixed = nodes_on_faces(coords, [fs[i - 1] for i in fixed])
        assert on_fixed == 1.0, (tid, on_fixed)
        desc = [C.face_descriptor(f, i + 1) for i, f in enumerate(fs)]
        total = np.sum([v for v in loads.values()], axis=0)
        assert np.allclose(total, r["CLOAD_resultant_N"], rtol=1e-6, atol=1e-6), (tid, total, r["CLOAD_resultant_N"])
        load_txt = "; ".join(f"face {i} carries ({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f}) N" for i, v in sorted(loads.items()))
        name = NAMES.get(stem, stem)
        inputs = [dict(path=str(step.relative_to(C.CAND)), role="cad", bytes=step.stat().st_size, sha256=C.sha256(step)),
                  C.write_input(tid, "faces.json", json.dumps(dict(note="face_index = 1-based order of TopExp::MapShapes(TopAbs_FACE) on part.step", faces=desc), indent=1))]
        prompt = f"""Component analysis: the {name} of an open-source, 3D-printable 15:1 cycloidal gearbox. part.step holds the single solid in millimetres ({summ['faces']} faces, volume {summ['volume_mm3']:.0f} mm^3). faces.json lists every face with its index, type, area, centroid and normal/axis; use the geometry, not a CAD system's own face numbering.

Material: {material}, linear isotropic elastic, E = {e_mod:g} MPa, Poisson ratio {r['elastic_card'][1].split(',')[1]}.
Analysis: linear static, small displacements, no gravity, no contact.
Supports: all three displacement components are zero on {C.describe_faces([desc[i - 1] for i in fixed])}.
Load: total force ({total[0]:.3f}, {total[1]:.3f}, {total[2]:.3f}) N applied as a uniform surface traction (constant force per unit area) over the loaded face(s): {load_txt}.
For reference, the source solved this with second-order tetrahedra (Netgen, maximum element size 2 mm)."""
        outs = [C.out("max_displacement_mm", "mm", "maximum nodal displacement magnitude in the part")]
        prov = f"{r['file']} (saved CalculiX FRD of the source-corrected deck)"
        # Stress is not graded: the source's own CalculiX error estimate at the stress peaks is 11-49 %.
        refs = dict(max_displacement_mm=C.refv(r["max_translation_mm"], "displacement", "published_raw_field", prov))
        rows.append(C.task(tid, "A", "gold", "cycloidal-drive-components", f"Cycloidal drive: {name} ({material})",
                           ["linear static"], prompt, inputs, outs, SOURCE,
                           dict(solids=summ["solids"], faces=summ["faces"], assembly=False, cad_bbox_mm=summ["bbox_mm"]), refs,
                           flags=["source author corrected FreeCAD CLOAD units by 1000x; loads stated from the corrected deck"]))
    return rows
