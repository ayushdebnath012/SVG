"""Track A, gold (simple geometry): GeoPINONet holed plates, validation split (Zenodo 21483341, CC BY 4.0).

Set-up from the publisher: ANSYS Structural Steel (E = 200 GPa, nu = 0.3), 1000 N per load branch (reviewer demo
`reference_load_n_per_branch`), two load cases. Checked against the published fields: the section force away
from the hole is -1000 N in compression; the field is exactly zero on one end face and loaded on the other.
The archive's fixed/load STL names are swapped relative to the fields, so the prompt states supports and loads
by geometry (the plate is symmetric, so which end is fixed does not change the answer). Lug_3D cases are held
(see registry): their bore load distribution (uniform force vs bearing) is not documented.
"""
from __future__ import annotations

import io
import json
import zipfile

import numpy as np

import common as C

SRC = C.DATA / "web-cad-fem-additions"
ARCH = SRC / "geopinonet/GeoPINONet_Plate_with_a_hole_dataset_v2.zip"
SOURCE = dict(name="GeoPINONet holed-plate FEM dataset (Urrutia Valdes, La Fe-Perdomo, Rodriguez Soto)",
              url="https://zenodo.org/records/21483341", license="CC BY 4.0", redistributable=True)


def build() -> list:
    cat = json.loads((SRC / "catalog.json").read_text())
    z = zipfile.ZipFile(ARCH)
    rows = []
    for r in cat["records"]:
        if r["family"] != "Plate_with_a_hole" or r["source_split"] != "model_val":
            continue
        tid = f"A-GEOPINO-PLATE-{r['source_case']}"
        res, checks = {}, []
        for f in r["fem"]:
            d = np.loadtxt(io.StringIO(z.read(f["archive_member"]).decode()), delimiter=",", skiprows=1)
            p, u = d[:, :3], d[:, 3:6]
            y0, y1 = p[:, 1].min(), p[:, 1].max()
            fixed_end = np.isclose(p[:, 1], y0, atol=1e-7)
            assert np.abs(u[fixed_end]).max() == 0.0, tid
            res[f["load"]] = np.linalg.norm(u, axis=1).max() * 1e3
            free_end = np.isclose(p[:, 1], y1, atol=1e-7)
            if f["load"] == "compression":
                assert u[free_end, 1].mean() < 0, tid             # loaded end moves towards the fixed end (-y)
            else:
                assert u[free_end, 0].mean() > 0, tid             # lateral case moves the free end along +x
            if f["load"] == "compression":
                mid = np.abs(p[:, 1] - (y1 - 0.1 * (y1 - y0))) < 4e-4
                w, t = np.ptp(p[:, 0]), np.ptp(p[:, 2])
                force = d[mid, 7].mean() * w * t
                assert -1060 < force < -940, (tid, force)
                checks.append(force)
        cv = r["cad_validation"]
        b = cv["bounds_mm"]
        inputs = [C.put(tid, SRC / r["cad"], "part.step")]
        prompt = f"""Holed steel plate. part.step is one solid in millimetres: a rectangular plate {b[3] - b[0]:.3f} mm (x) by {b[4] - b[1]:.3f} mm (y) by {b[5] - b[2]:.3f} mm (z) with a through hole along z.
Material: ANSYS default Structural Steel, linear isotropic elastic, E = 200 GPa, Poisson ratio 0.3. Linear static, small displacements, no gravity.
Supports: the end face at y = {b[1]:.4f} mm is fully fixed (all displacement components zero).
Two separate load cases, each a total force of 1000 N applied as a uniform traction over the opposite end face (y = {b[4]:.4f} mm):
  (1) compression: 1000 N along -y (towards the fixed end);
  (2) lateral bending: 1000 N along +x (in-plane shear of the free end)."""
        outs = [C.out("max_displacement_compression_mm", "mm", "maximum displacement magnitude, load case 1"),
                C.out("max_displacement_lateral_mm", "mm", "maximum displacement magnitude, load case 2")]
        prov = "max |u| over the published ANSYS nodal CSV ({}_compression.csv / _lateral_bending.csv)".format(r["source_case"])
        refs = dict(max_displacement_compression_mm=C.refv(res["compression"], "displacement", "published_raw_field", prov),
                    max_displacement_lateral_mm=C.refv(res["lateral_bending"], "displacement", "published_raw_field", prov))
        rows.append(C.task(tid, "A", "gold", "geopinonet-holed-plate", f"Holed plate, GeoPINONet validation case {r['source_case']}",
                           ["linear static"], prompt, inputs, outs, SOURCE,
                           dict(solids=1, faces=cv["faces"], assembly=False, cad_bbox_mm=b, geometry_class="simple"), refs,
                           flags=["source errors not carried over: BCs stated from the verified fields (archive STL names are swapped), thickness from the CAD (README says 20 mm, CAD and FEM 10 mm)"]))
    return rows
