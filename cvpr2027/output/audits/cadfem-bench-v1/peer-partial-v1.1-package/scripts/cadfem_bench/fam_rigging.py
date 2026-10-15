"""Silver: OpenRiggingPlate (mpangch/OpenRiggingPlate, CERN-OHL-S-2.0), 7075-T6 rigging plate, seven ANSYS load tests.

Track A: supplied STEP + the source's boundary-condition figure for each test. Track B: the source's dimensioned
manufacturing drawing (PDF) + Test 1 boundary conditions; the model builds the CAD. References are the maximum
equivalent stress printed on each original result legend. Only stress is graded: the source's material card is not
published, and for force loads with fixed/remote supports the stress field does not depend on E.
"""
from __future__ import annotations

import json

import common as C

SRC = C.DATA / "web-cad-fem-rigging-plate"
SOURCE = dict(name="OpenRiggingPlate (mpangch)", url="https://github.com/mpangch/OpenRiggingPlate", license="CERN-OHL-S-2.0",
              redistributable=True)
EXCLUDED = {"4": "README 2222.5 lbf, folder 2225.4 lbf and figure 9899.5 N disagree",
            "5": "result legends read TEST-5R: the saved results belong to a revised set-up"}
SETUP = """Material: aluminium 7075-T6, linear isotropic elastic (standard handbook values; the source did not publish its card, and the graded stress does not depend on Young's modulus for these loads).
Analysis: linear static, small displacements (ANSYS Mechanical in the source).
Boundary conditions: exactly as shown in boundary-conditions.png (the source's own ANSYS figure): each labelled scope (A, B, ...) is a face or set of faces of the plate; 'Force' applies the stated total force uniformly distributed over the scoped faces in the drawn direction; 'Remote Displacement' fixes the scoped faces through a rigid remote point (all displacements and rotations zero). Where only two equal and opposite forces are applied and no support is drawn, the plate is self-equilibrated; remove rigid-body motion without adding load (e.g. weak springs or inertia relief), as the source did."""


def build() -> list:
    cat = json.loads((SRC / "catalog.json").read_text())
    rows = []
    for r in cat["records"]:
        n = r["id"].rsplit("-", 1)[1]
        if n in EXCLUDED:
            continue
        tgt = {t["quantity"]: t for t in r["targets"]}
        vm = tgt["maximum_equivalent_von_mises_stress"]
        folder = SRC / r["source_folder"]
        legend = "; ".join(r["boundary_legend_ocr"][3:])
        for track in ("A", "B") if n == "1" else ("A",):
            tid = f"{track}-RIGGING-test{n}"
            inputs = [C.put(tid, folder / "Boundary Conditions.png", "boundary-conditions.png", role="figure")]
            if track == "A":
                inputs.insert(0, C.put(tid, SRC / r["cad"] if "cad" in r else SRC / cat["cad"], "riggingplate.step"))
                geo = "riggingplate.step is the single solid in millimetres (235.58 x 111.90 x 12 mm, 145 faces)."
            else:
                inputs.insert(0, C.put(tid, SRC / cat["original_dimensioned_drawing"], "rigging-plate-drawing.pdf", role="drawing"))
                geo = ("Build the plate yourself from rigging-plate-drawing.pdf (the source's dimensioned manufacturing drawing, "
                       "millimetres, 12 mm thick, all seams blended) and export it as part.step; then analyse your own model.")
            prompt = f"""Hard-anodised 7075-T6 rigging plate, load test {n} of the source's seven ANSYS load cases ({r['source_folder'].split('/')[-1]}). {geo}
{SETUP}
Legend of this test's figure: {legend}."""
            outs = [C.out("max_von_mises_MPa", "MPa", "maximum equivalent (von Mises) stress in the plate")]
            refs = dict(max_von_mises_MPa=C.refv(vm["value"], "stress", "published_legend",
                                                  f"{vm['original_image']} legend '{vm['source_legend']}'", tier="silver"))
            extra = None
            if track == "B":
                extra = dict(geometry_check=dict(volume_mm3=cat["cad_audit"]["volume_mm3"], bbox_extent_mm=[235.579, 111.904, 12.0],
                                                 rel_tol=0.02, provenance="source STEP riggingplate-14mar2024.step (README volume 92,450.06 mm^3)"))
            rows.append(C.task(tid, track, "silver", "rigging-plate", f"Rigging plate, load test {n}" + (" (from drawing)" if track == "B" else ""),
                               ["linear static"], prompt, inputs, outs, SOURCE, dict(solids=1, faces=145, assembly=False), refs,
                               flags=["load scopes given by the source figure, not by face IDs",
                                      "reference is a rounded legend maximum; peak at load-face edges is mesh-sensitive (20 % tolerance)"],
                               extra_eval=extra))
    return rows
