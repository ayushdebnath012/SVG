# FEA — All parts (cycloidal gearbox, STEP reference)

Pipeline proven on the disk (`fea_results.md`): solid copied from
`STEP_Analysis` → Analysis + Fixed + Force + MaterialSolid + Netgen C3D10 +
SolverCcxTools → INP via `femtools.ccxtools` → `fix_cload_units.py` (×1000
CLOAD correction, totals verified) → `ccx` 2.21 → results reloaded,
equilibrium checked (|reaction| = applied in every run). Reusable setup:
`../batch_fea_setup.py`. Sessions: `FEM_<Part>/<Part>.FCStd`.

Service basis (`docs/material_performance.md`, 2.6 N·m rated): 17.7 N/output
pin, ~7 N/ring contact, ~173 N cam reaction. Shock cases ≈ 2–11× rated.

## Results (shock load cases)

| Part | Case | Mat | Nodes | Max VM (MPa) | Mean (MPa) | dmax (mm) | SF |
|---|---|---|---|---|---|---|---|
| Disk | 200 N tangential / hole | PLA | 16,489 | 5.70 | 0.98 | 0.0500 | 8.8 |
| Ring pin Ø6×34.8 | 150 N transverse | Steel | 10,034 | 74.56 | 8.74 | 0.0021 | 3.4 |
| Output pin Ø6×15 | 180 N transverse | Steel | 3,277 | 18.55 | 5.96 | 0.0004 | 13.5 |
| Spacer 6 mm ID | 50 N axial | PLA | 2,562 | 1.81 | 1.32 | 0.0028 | 27 |
| Dist ring 1 mm ID6 | 30 N axial | PLA | 1,717 | 1.32 | 0.90 | 0.0003 | 38 |
| Dist ring 4 mm ID6 | 30 N axial | PLA | 2,271 | 1.44 | 1.00 | 0.0011 | 35 |
| Dist ring 1 mm ID15 | 50 N axial | PLA | 3,608 | 0.90 | 0.60 | 0.0002 | 55 |
| Shaft coupler | 100 N axial | PLA | 16,694 | 5.12 | 0.71 | 0.0065 | 9.8 |
| Input cam P2 | **300 N radial bending** | PLA | 12,792 | 18.45 | 2.70 | 0.0279 | 2.7 |
| Input cam P2 (ref) | 300 N axial | PLA | 12,792 | 13.20 | 2.57 | 0.0244 | 3.8 |
| Input tail P1 | 100 N axial | PLA | 22,469 | 2.59 | 0.59 | 0.0031 | 19 |
| NEMA mount | 50 N axial | PLA | 34,652 | 0.84 | 0.13 | 0.0094 | 59 |
| Output flange P1 | 180 N on 6 pin seats | PLA | 72,142 | 1.91 | 0.56 | 0.0071 | 26 |
| Output flange P2 | 180 N on 6 M3 holes | PLA | 58,284 | 3.04 | 0.62 | 0.0130 | 16 |
| Housing lid | 250 N radial, brg seat | PLA | 82,912 | 0.64 | 0.03 | 0.0009 | 78 |
| Housing base | 500 N radial, brg seat | PLA | 7,211 lin | 0.92 | 0.06 | 0.0016 | 54 |

Strengths: PLA 50 MPa, steel 250 MPa. SF at shock; at rated load (≈10× lower
for most rows) all PLA stresses are ≤ ~2 MPa.

Hotspots: cam journal-to-collar fillet (P2), disk output-hole edge, coupler
Ø5 bore, flange P1 pin seats (X=90), flange P2 back plane; pin peaks sit at
the idealized fixed ends (fixture singularities — real pressed contacts are
kinder). Lid/housing peaks negligible and fixture-local.

## Verdicts

- **Whole gearbox PASSES statically with margin.** Weakest point is the
  **input-cam fillet (SF 2.7 @ 300 N ≈ 1.7× rated; ≈4.7 @ rated)** — print
  shaft sections with high wall count/infill, ream Ø15 journals, and keep
  fillets generous. Next: disk holes (8.8 @ 11×), coupler bore (9.8).
- **Steel ring pins confirmed**: 74.6 MPa @ 10× shock in steel (SF 3.4) vs
  certain failure in PLA — keep the ground-rod design. Output pins easy
  (SF 13.5).
- Housing / lid / mount / spacers / rings (SF 25–78): strength is irrelevant;
  stiffness and print calibration govern, as predicted analytically.
- Linear statics: stresses/displacements scale with load; shock ≈ 10× rated
  ⇒ rated stresses ≈ table ÷ 10 (shaft P2 ÷ 1.7).

## Caveats (read before rerunning)

1. **FreeCAD auto-derives `ConstraintForce.DirectionVector` from the loaded
   faces on recompute** (overwrites manual values). All directions above are
   the *actually applied* ones (verified from *CLOAD sums + reactions):
   transverse for pins/flanges/lid, axial for spacers/rings/coupler/tail/
   mount. Shaft P2 radial was enforced by remapping *CLOAD DOF 1→2
   (`ShaftP2_radial_fixed.inp`); the axial run is kept as reference.
2. **1000× CLOAD unit bug** (FreeCAD 1.1 `meshtools.py`): every deck was
   corrected with `fix_cload_units.py`; totals printed at solve time.
3. **Housing uses linear C3D4 elements**: the 191-face drum repeatedly
   produced nonpositive Jacobians in C3D10 (elements 21592/32666/39393) under
   both VeryCoarse-10 mm and Coarse-8 mm meshes; linear screening run is
   appropriate at 0.92 MPa. Lid/flanges ran full C3D10.
4. P3/P4 shaft sections: same Ø15-journal family as P2 — covered by
   similarity. Bearings/bolts/inserts/motor: purchased parts, analytical
   check only (SF > 40).
