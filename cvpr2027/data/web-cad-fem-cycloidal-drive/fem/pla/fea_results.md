# FEA Results — Cycloidal disk, PLA, 200 N shock load

Solved with CalculiX 2.21 (ccx) from a FreeCAD-generated deck. Session saved
as `FEM_Disk.FCStd` (doc `FEM_Disk`, analysis `Analysis_PLA`).

## Setup (as built in the GUI)

- **Geometry:** `Disk` — cycloidal disk from the STEP (Ø79.6 × 5, 15 lobes,
  Ø24 center bore, 6× Ø16 output holes).
- **Material:** `MaterialPLA_FEM` — generic PLA: E 3500 MPa, ν 0.36,
  ρ 1240 kg/m³. Design yield 50 MPa.
- **Fixture:** `FixedBore` — center bore faces locked (all DOFs).
- **Load:** `ShockLoad` — 200 N tangential on one output hole ≈ 11× the rated
  17.7 N pin force (shock case). 372 nodal CLOADs, area-weighted.
- **Mesh:** `MeshNetgen` — 16,489 nodes / 9,516 C3D10 quadratic tets, 3 mm max.
- **Solver:** `SolverCcx` — *STATIC, spooles, 48,699 equations, ~2.4 s.

## Results (`CCX_Results001`, pipeline `Pipeline_Fixed200N002`)

| Quantity | Value |
|---|---|
| Max von Mises | **5.70 MPa** (hotspot: loaded-hole bore edge, node 7) |
| Mean von Mises | 0.98 MPa |
| Max principal | 5.68 MPa |
| Max displacement | **0.050 mm** (at loaded hole) |
| Bore reaction | (0, +62.3, −189.8) N → 199.77 N, balances applied 200 N ✓ |

## Verdict

- **SF ≈ 8.8 vs PLA yield (50 MPa) at 200 N shock** → at rated 17.7 N the
  stress scales to ≈ 0.5 MPa (SF ≈ 100). Statics confirm the analytical
  prediction: the disk cannot yield in this service; wear/creep govern life.
- Peak sits at the loaded hole edge (bearing-type concentration) with a
  secondary path toward the fixed bore — both expected and conservative
  (a real bearing contact spreads load better than the idealized fixture).

## Known toolchain bug (important for reruns)

FreeCAD 1.1's FEM writer under-applies `ConstraintForce` by **1000×**
(`Quantity(Force.getValueAs("N"))` rebuilds a dimensionless quantity in
`femmesh/meshtools.py`). Symptom: first solve showed 0.0057 MPa max with only
0.2 N applied. Fix used here: `../fix_cload_units.py` rescales the `*CLOAD`
lines ×1000 (`DiskPLA.inp` → `DiskPLA_fixed.inp`, verified |F| = 199.77 N).
Re-check CLOAD totals after every deck rewrite until upstream is fixed.
`CCX_Results` in the saved doc is the buggy 0.2 N run, kept for comparison —
use `CCX_Results001`.
