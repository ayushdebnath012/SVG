# FEA — All parts in PETG-CF (cycloidal gearbox, STEP reference)

Rerun of `../pla/fea_all_parts.md` with the printed-material card switched
from PLA to generic PETG-CF. Everything else is deliberately identical:
same source solids from `STEP_Analysis`, same fixture/load faces, same
forces, same Netgen settings. Tooling: `petg_setup.py` (mirrors
`../batch_fea_setup.py`, adds explicit `force_direction` + `second_order`
control), `petg_results.py` (load + stats), `petg_figures.py` (pipelines +
screenshots). Sessions: `FEM_<Part>_PETGCF/FEM_<Part>_PETGCF.FCStd`.

## Material card (generic — no spool brand on record, so the README proposal stands)

| Property | Value |
|---|---|
| Name | PETG-CF-Generic |
| Young's modulus | 3000 MPa |
| Poisson's ratio | 0.36 |
| Density | 1300 kg/m³ |
| Design tensile (yield) | **45 MPa** |
| UTS | 55 MPa |

Steel pins stay steel (no rerun). Bearings/bolts/inserts/motor: purchased
parts, analytical only (SF > 40, unchanged). P3/P4 covered by P2 similarity.

## Load cases (identical to PLA — faces preserved on shape copy)

| Part | Src label in STEP_Analysis | Fix faces | Load faces | F (N) | Applied dir (unit, from *CLOAD sums) | Mesh (Max/Min/Order/Fineness) |
|---|---|---|---|---|---|---|
| Disk | Cycloidal disk | Face8, Face13 | Face2, Face19 | 200 | (0, −0.312, +0.950) tangential | 3 mm / – / C3D10 / Moderate |
| Spacer 6 mm ID | Spacer 6mm ID | Face4 | Face3 | 50 | (+1, 0, 0) axial | 2 mm / – / C3D10 / Moderate |
| Dist ring 1 mm ID6 | Distance ring 1mm ID 6mm | Face4 | Face3 | 30 | (+1, 0, 0) axial | 1 mm / – / C3D10 / Moderate |
| Dist ring 4 mm ID6 | Distance ring 4mm ID 6mm | Face4 | Face3 | 30 | (+1, 0, 0) axial | 1 mm / – / C3D10 / Moderate |
| Dist ring 1 mm ID15 | Distance ring 1mm ID 15mm | Face4 | Face3 | 50 | (0, 0, +1) axial | 1 mm / – / C3D10 / Moderate |
| Shaft coupler | Nema 17 shaft coupler | Face5, Face6 | Face14 | 100 | (+1, 0, 0) axial | 2 mm / – / C3D10 / Moderate |
| Input cam P2 (radial) | Input shaft - p2 | Face4, Face5 | Face3, Face8 | 300 | (0, +1, 0) radial — enforced by *CLOAD DOF 1→2 remap before ×1000 fix | 2 mm / – / C3D10 / Moderate |
| Input cam P2 (axial ref) | Input shaft - p2 | Face4, Face5 | Face3, Face8 | 300 | (+1, 0, 0) axial, as written | same mesh |
| Input tail P1 | Input shaft - p1 | Face18 | Face15 | 100 | (0, 0, +1) | 2 mm / – / C3D10 / Moderate |
| NEMA mount | NEMA 17 motor mount | Face22, Face24 | Face12 | 50 | (−1, 0, 0) | 4 mm / – / C3D10 / Moderate |
| Output flange P1 | Output disk flange p1 | Face28, Face1, Face45 | Face2–7 + Face32/34/36/38/40/42 | 180 | (0, +0.385, +0.923) transverse | 3 mm / – / C3D10 / Moderate |
| Output flange P2 | Output disk flange p2 | Face17, Face23 | Face1–6 | 180 | (0, −0.385, −0.923) transverse | 3 mm / – / C3D10 / Moderate |
| Housing lid | Roller pins housing lid | Face52 | Face51, Face53 | 250 | (0, −0.556, +0.831) transverse | 5 mm / – / C3D10 / Coarse |
| Housing base | Roller pins housing | Face117 | Face64, Face81 | 500 | (0, −0.195, +0.981) transverse | 8 mm / 2 mm / **C3D4 linear** / Coarse |

Directions above are the *actually applied* ones (unit vectors of the
summed *CLOAD components in the solved decks), matching the PLA
actually-applied vectors to 6 decimals. The enforced `force_direction`
step exists because FreeCAD re-derives `ConstraintForce.DirectionVector`
from load-face normals on every recompute (e.g. the disk re-derives to
(0, −0.510, +0.860)); the vector is set after the final recompute with no
recompute before deck writing, then verified from *CLOAD sums.

## Results (shock load cases) vs PLA

| Part | Nodes PETG (PLA) | Max VM PETG (MPa) | PLA (MPa) | Δσ | Mean VM (MPa) | dmax PETG (mm) | PLA (mm) | ×d | SF vs 45 MPa |
|---|---|---|---|---|---|---|---|---|---|
| Disk | 16,716 (16,489) | 5.7007 | 5.70 | +0.0 % | 0.9820 | 0.05793 | 0.0500 | 1.167 | 7.9 |
| Spacer 6 mm | 2,562 (2,562) | 1.8050 | 1.81 | −0.3 % | 1.3167 | 0.003268 | 0.0028 | 1.167 | 24.9 |
| Ring 1×6 | 1,717 (1,717) | 1.3206 | 1.32 | +0.0 % | 0.9002 | 0.000391 | 0.0003 | ~1.3¹ | 34.1 |
| Ring 4×6 | 2,271 (2,271) | 1.4373 | 1.44 | −0.2 % | 1.0042 | 0.001279 | 0.0011 | 1.163 | 31.3 |
| Ring 1×15 | 3,608 (3,608) | 0.8952 | 0.90 | −0.5 % | 0.6004 | 0.000258 | 0.0002 | ~1.3¹ | 50.3 |
| Coupler | 16,694 (16,694) | 5.1215 | 5.12 | +0.0 % | 0.7127 | 0.007617 | 0.0065 | 1.172 | 8.8 |
| Cam P2 radial | 12,792 (12,792) | 18.4470 | 18.45 | −0.0 % | 2.6963 | 0.032607 | 0.0279 | 1.169 | 2.4 |
| Cam P2 axial ref | same mesh | 13.2032 | 13.20 | +0.0 % | 2.5697 | 0.028500 | 0.0244 | 1.168 | 3.4 |
| Tail P1 | 22,469 (22,469) | 2.5906 | 2.59 | +0.0 % | 0.5860 | 0.003665 | 0.0031 | 1.18¹ | 17.4 |
| Mount | 34,652 (34,652) | 0.8411 | 0.84 | +0.1 % | 0.1261 | 0.010922 | 0.0094 | 1.162 | 53.5 |
| Flange P1 | 72,142 (72,142) | 1.9065 | 1.91 | −0.2 % | 0.5622 | 0.008251 | 0.0071 | 1.162 | 23.6 |
| Flange P2 | 58,284 (58,284) | 3.0418 | 3.04 | +0.1 % | 0.6223 | 0.015156 | 0.0130 | 1.166 | 14.8 |
| Lid | 82,912 (82,912) | 0.6407 | 0.64 | +0.1 % | 0.0326 | 0.001079 | 0.0009 | ~1.2¹ | 70.2 |
| Housing (lin) | 7,211 (7,211) | 0.9164 | 0.92 | −0.4 % | 0.0589 | 0.001821 | 0.0016 | ~1.1¹ | 49.1 |

¹ Ratio computed against PLA values rounded to 1–2 significant figures in
the PLA table; the unrounded ratios all sit at 3500/3000 = 1.1667.

Expectation check: **PASS on all 14 rows** — stresses identical within
±0.5 % (table rounding), displacements scaled ×1.167. No part deviated, so
no investigation was triggered. Hotspot nodes/coordinates reproduce PLA
(disk node 7 at (104.025, 10.4209, 28.1143), etc.).

Hotspots (unchanged from PLA): cam journal-to-collar fillet (P2), disk
output-hole edge, coupler Ø5 bore, flange P1 pin seats, flange P2 M3
holes/hub fillet; lid/housing peaks negligible and fixture-local.

## Equilibrium record (|fixture reaction| vs applied, from `.dat`)

| Deck | CLOAD lines | Applied (N) | \|F\| (N) | Reaction (N) | \|R\| (N) | Balance |
|---|---|---|---|---|---|---|
| Disk_fixed | 372 | (0, −62.33, +189.80) | 199.772 | (0, +62.334, −189.798) | 199.772 | 0.000 % |
| Spacer6_fixed | 294 | (+50.00, 0, 0) | 50.000 | (−50.000, 0, 0) | 50.000 | 0.000 % |
| Ring1x6_fixed | 402 | (+29.99, 0, 0) | 29.990 | (−29.990, 0, 0) | 29.990 | 0.000 % |
| Ring4x6_fixed | 319 | (+30.00, 0, 0) | 29.997 | (−29.997, 0, 0) | 29.997 | 0.000 % |
| Ring1x15_fixed | 868 | (0, 0, +49.99) | 49.988 | (0, 0, −49.988) | 49.988 | 0.000 % |
| Coupler_fixed | 932 | (+100.05, 0, 0) | 100.052 | (−99.385, 0, 0) | 99.385 | 0.667 %² |
| ShaftP2_fixed (axial) | 888 | (+299.88, 0, 0) | 299.883 | (−299.883, 0, 0) | 299.883 | 0.000 % |
| ShaftP2_radial_fixed | 888 | (0, +299.88, 0) | 299.883 | (0, −299.883, 0) | 299.883 | 0.000 % |
| ShaftP1_fixed | 841 | (0, 0, +100.20) | 100.204 | (0, 0, −100.204) | 100.204 | 0.000 % |
| Mount_fixed | 1584 | (−50.06, 0, 0) | 50.064 | (+50.064, 0, 0) | 50.064 | 0.000 % |
| FlangeP1_fixed | 2872 | (0, +69.13, +165.91) | 179.740 | (0, −69.131, −165.914) | 179.740 | 0.000 % |
| FlangeP2_fixed | 2036 | (0, −69.09, −165.81) | 179.624 | (0, +69.086, +165.807) | 179.624 | 0.000 % |
| Lid_fixed | 1864 | (0, −138.88, +207.84) | 249.973 | (0, +138.877, −207.845) | 249.973 | 0.000 % |
| Housing_fixed (lin) | 430 | (0, −97.49, +490.13) | 499.729 | (0, +97.492, −490.126) | 499.729 | 0.000 % |

² Inherited from the PLA phase: the PLA Coupler deck's own `.dat`
reaction is −99.38477 N against 100.05171 N applied (same digits). Case
property, reproduced exactly — not a PETG-phase artifact.

Every deck went through `fix_cload_units.py` (raw decks apply ~1/1000 of
the setting; the printout `|F| before → after` was checked to equal the
setting each time). ShaftP2 radial: DOF 1→2 remap inside the *CLOAD block
only, then the ×1000 fix (|F| = 299.883 N in +Y).

## Method notes / deviations from PLA (all verified benign)

1. **Node count:** 12 of 13 meshes reproduce PLA node counts exactly. Only
   the disk differs (16,716 vs 16,489, +1.4 %) — Netgen nondeterminism on a
   re-mesh with identical settings; stress agrees to 0.01 %.
2. **CLOAD dust:** PLA Coupler deck carries 932 near-zero DOF-2 lines
   (≤8e-16 N each, sum 1e-13 N) because it was written with the
   face-normal-derived vector (1, 1.1e-15, −3e-17). PETG decks use the
   cleaned intended vectors, so they contain only the loaded DOF(s).
   Statically identical to 1e-13 N.
3. **Figures:** pipeline-only post (Field = von Mises, `updateColorBars()`)
   instead of pipeline→warp→contours. Nesting warp/contour filters from
   Python is broken in FreeCAD 1.1 (`FemPostFilter` proxies expose no bound
   `addObject`), and an empty contour hijacks the scalar bar (±0.5
   placeholder). The pipeline surface + result-mesh wireframe + Pa bar is
   visually identical to the PLA figure style (spot-checked Fig. 1
   min/max labels: 1.001e4 / 5.701e6 Pa vs stats 10008 Pa / 5.7007 MPa).
   Warp factor is 0 in both phases (true scale).
4. **Housing** runs linear C3D4 (8 mm max / 2 mm min / Coarse), same as PLA —
   the 191-face drum fails C3D10 with nonpositive Jacobians.
5. Housing/Lid decks are byte-comparable in structure to PLA (same
   `*Element` line numbers: 7220 / 82921; C3D4 vs C3D10 as in PLA).

## Files and reproduction

- Per part: `FEM_<Part>_PETGCF/` → `<Part>.inp` (raw), `<Part>_fixed.inp`
  (solved deck; ShaftP2 also `<Part>_radial.inp` /
  `<Part>_radial_fixed.inp`), `ccx` outputs (`.frd/.dat/.sta/.cvg`),
  `FEM_<Part>_PETGCF.FCStd` (setup + mesh + loaded results + figure
  pipeline, saved after each stage).
- Rerun any part: `petg_setup.py::setup_petg` (faces/forces above),
  `../../fix_cload_units.py`, `ccx -i`, `petg_results.py::load_and_stats`.
- Figure for any part: `petg_figures.py::make_figure` (one call per figure;
  needs the doc open with results loaded).
