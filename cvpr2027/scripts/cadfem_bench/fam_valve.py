"""Track A, gold: FeenoX tutorial #3 power-plant valve, nonlinear transient heat conduction (GPL-3.0).

Geometry: the source valve.brep (4 solids: one carbon-steel nozzle, three stainless bodies). Physical groups are the
source valve.geo surface tags, which equal the OpenCASCADE face indices of valve.brep (checked: face areas agree to
6e-5, centroids to 5e-4 mm). Properties: the source ASME II Part D tables (asme-properties.fee). References: the
published FeenoX history valve-1.csv at the SCL2 (carbon) and SCL4 (stainless) stress classification lines;
through-wall differences are read from the published samples.
"""
from __future__ import annotations

import json

import numpy as np

import common as C

SRC = C.DATA / "web-cad-fem-valve-transient"
SOURCE = dict(name="FeenoX tutorial #3: heat conduction (valve with carbon and stainless steel parts)",
              url="https://www.seamplex.com/feenox/doc/tutorials/320-thermal/", license="GPL-3.0", redistributable=True)
GROUPS = {"internal": [7, 8, 9, 10, 18, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 60, 61, 62, 63, 64, 65, 66, 67, 68, 97, 98, 99, 100, 101, 112],
          "external": [1, 2, 6, 12, 13, 19, 21, 22, 23, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 54, 55, 56, 57, 58, 59,
                       69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 92, 93, 94, 95, 96, 102, 103, 104, 105, 106, 107, 108],
          "symmetry": [3, 4, 15, 17, 20, 25, 91, 110, 111], "end_carbon": [14], "end_stainless": [109]}


def build() -> list:
    tid = "A-VALVE-transient"
    shape = C.read_shape(SRC / "valve.brep")
    summ = C.shape_summary(shape)
    fs = C.faces(shape)
    desc = [C.face_descriptor(f, i + 1) for i, f in enumerate(fs)]
    for g, ids in GROUPS.items():
        for i in ids:
            desc[i - 1]["group"] = g
    A = np.array([[float(x) for x in l.split()] for l in (SRC / "valve-1.csv").read_text().splitlines() if l.strip()])
    t = A[:, 0]
    k100 = np.abs(t - 100).argmin()
    d2, d4 = A[:, 2] - A[:, 4], A[:, 5] - A[:, 7]
    inputs = [C.put(tid, SRC / "valve.brep"), C.put(tid, SRC / "asme-properties.fee", role="spec"),
              C.put(tid, SRC / "valve-internal-1.csv", "internal-temperature.csv", role="spec"),
              C.write_input(tid, "faces.json", json.dumps(dict(note="face_index = OpenCASCADE face order of valve.brep (equal to Gmsh surface tags)", groups=GROUPS, faces=desc), indent=1)),
              C.put(tid, SRC / "valve-surfaces.png", role="figure"), C.put(tid, SRC / "valve-materials.png", role="figure")]
    prompt = f"""Nonlinear transient heat conduction in a power-plant valve: a carbon-steel nozzle welded to stainless-steel valve bodies (half model, symmetry plane y = 0). valve.brep holds 4 solids in millimetres ({summ['faces']} faces). Solid 2 (the nozzle, x from 0 to 65 mm) is carbon steel; solids 1, 3 and 4 are stainless steel SA-312. faces.json lists every face with its index and its boundary group; valve-surfaces.png and valve-materials.png are the source's figures.

Materials: temperature-dependent conductivity k(T) and thermal diffusivity kappa(T) from asme-properties.fee (ASME II Part D tables, T in deg C): carbon steel uses k_carbon and kappa_carbon, stainless uses k_312 and kappa_312. As in the source, k from the tables is in W/(m K) and is multiplied by 1e-3 to W/(mm K); kappa is used as tabulated (mm^2/s). The volumetric heat capacity follows as k/kappa.
Boundary conditions: 'internal' faces: prescribed temperature T = Tint(t) from internal-temperature.csv (linear interpolation: 40 C at t = 0, 250 C from 100 s to 500 s, back to 40 C at 600 s, held to 1000 s). 'external' faces: convection h = 1e-6 W/(mm^2 K) to 50 C. 'symmetry' and both end faces: adiabatic.
Initial condition: the steady-state solution of the same problem at t = 0. Simulate 0 <= t <= 1000 s.
Stress classification lines: SCL2 (in the carbon-steel nozzle) runs from (3, 0, 48.5) mm on the inner wall to (3, 0, 57) mm on the outer wall; SCL4 (stainless body) from (-3, 0, 48.5) to (-3, 0, 57) mm."""
    outs = [C.out("scl2_dT_max_K", "K", "maximum over time of T(inner end) - T(outer end) on SCL2 (heat-up)"),
            C.out("scl2_dT_min_K", "K", "minimum over time of T(inner end) - T(outer end) on SCL2 (cool-down, negative)"),
            C.out("scl4_dT_max_K", "K", "maximum over time of T(inner) - T(outer) on SCL4"),
            C.out("scl4_dT_min_K", "K", "minimum over time of T(inner) - T(outer) on SCL4"),
            C.out("scl2_T_outer_100s_C", "C", f"temperature at the outer end of SCL2 at t = {t[k100]:.3f} s"),
            C.out("scl4_T_outer_100s_C", "C", f"temperature at the outer end of SCL4 at t = {t[k100]:.3f} s")]
    prov = "published FeenoX history valve-1.csv (192 adaptive time samples)"
    refs = dict(scl2_dT_max_K=C.refv(float(d2.max()), "temperature", "published_table", prov, tol=0.10),
                scl2_dT_min_K=C.refv(float(d2.min()), "temperature", "published_table", prov, tol=0.10),
                scl4_dT_max_K=C.refv(float(d4.max()), "temperature", "published_table", prov, tol=0.10),
                scl4_dT_min_K=C.refv(float(d4.min()), "temperature", "published_table", prov, tol=0.10),
                scl2_T_outer_100s_C=C.refv(float(A[k100, 4]), "temperature", "published_table", prov, tol_kind="rel_offset", offset=40.0),
                scl4_T_outer_100s_C=C.refv(float(A[k100, 7]), "temperature", "published_table", prov, tol_kind="rel_offset", offset=40.0))
    return [C.task(tid, "A", "gold", "feenox-valve-transient", "Power-plant valve: nonlinear transient thermal (carbon + stainless)",
                   ["transient thermal", "nonlinear material", "multi-material"], prompt, inputs, outs, SOURCE,
                   dict(solids=summ["solids"], faces=summ["faces"], assembly=True, cad_bbox_mm=summ["bbox_mm"]), refs,
                   flags=["through-wall differences use the published 192-sample history; 10 % tolerance on differences",
                          "temperatures at 100 s graded on the rise above the 40 C initial state"])]
