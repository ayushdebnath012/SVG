# Report figures — FEA von Mises plots (PETG-CF rerun)

Folder: `report_images/`. All 1280×960, isometric, von Mises field with
legend in **Pa** (divide by 10⁶ → MPa). Deformation not scaled (true scale,
warp factor 0). Linear static, CalculiX 2.21; every run equilibrium-verified.
Details + safety factors: `fea_all_parts_PETGCF.md`.

Figs. 01, 04–15 are fresh PETG-CF solves (same faces/forces/meshes as the
PLA phase). Figs. 02–03 are the unchanged steel-pin runs — material did not
change, so the PLA-phase figures are reused verbatim (copies, same pixels).

| # | File | Part / case | Peak | Suggested caption |
|---|---|---|---|---|
| 1 | 01_disk_petgcf_200N.png | Cycloidal disk, PETG-CF, 200 N tangential / hole | 5.70 MPa | Disk at 11× rated shock; peak at loaded-hole edge (SF 7.9 vs 45 MPa) |
| 2 | 02_ring_pin_steel_150N.png | Ring pin Ø6×34.8, steel, 150 N transverse | 74.56 MPa | Reused from PLA phase — steel unchanged (SF 3.4) |
| 3 | 03_output_pin_steel_180N.png | Output pin Ø6×15, steel, 180 N transverse | 18.55 MPa | Reused from PLA phase — steel unchanged (SF 13.5) |
| 4 | 04_spacer_6mm_petgcf_50N.png | Spacer 6 mm ID, PETG-CF, 50 N axial | 1.80 MPa | Uniform clamp compression (SF 25) |
| 5 | 05_dist_ring_1mm_ID6_petgcf_30N.png | Distance ring 1 mm ID6, PETG-CF, 30 N axial | 1.32 MPa | (SF 34) |
| 6 | 06_dist_ring_4mm_ID6_petgcf_30N.png | Distance ring 4 mm ID6, PETG-CF, 30 N axial | 1.44 MPa | (SF 31) |
| 7 | 07_dist_ring_1mm_ID15_petgcf_50N.png | Distance ring 1 mm ID15, PETG-CF, 50 N axial | 0.90 MPa | Quietest part in the assembly (SF 50) |
| 8 | 08_coupler_petgcf_100N.png | Shaft coupler, PETG-CF, 100 N axial | 5.12 MPa | Peak at Ø5 motor-bore edge (SF 8.8) |
| 9 | 09_shaft_cam_P2_radial_petgcf_300N.png | Input cam P2, PETG-CF, 300 N radial bending | 18.45 MPa | Weakest printed part; peak at journal-to-collar fillet (SF 2.4 @ shock, ~4.2 @ rated) |
| 10 | 10_shaft_tail_P1_petgcf_100N.png | Input tail P1, PETG-CF, 100 N axial | 2.59 MPa | Evenly loaded pilots (SF 17) |
| 11 | 11_mount_petgcf_50N.png | NEMA 17 mount, PETG-CF, 50 N | 0.84 MPa | Barely loaded (SF 54) |
| 12 | 12_flange_P1_petgcf_180N.png | Output flange P1, PETG-CF, 180 N on 6 pin seats | 1.91 MPa | Rings around pin seats (SF 24) |
| 13 | 13_flange_P2_petgcf_180N.png | Output flange P2, PETG-CF, 180 N on 6 M3 holes | 3.04 MPa | Peaks at M3 holes/hub fillet (SF 15) |
| 14 | 14_lid_petgcf_250N.png | Housing lid, PETG-CF, 250 N radial on bearing seat | 0.64 MPa | Clean seat ring (SF 70) |
| 15 | 15_housing_petgcf_500N.png | Housing base, PETG-CF, 500 N radial on bearing seat | 0.92 MPa | Linear C3D4 screening run; seat ring only (SF 49) |

Figure-numbering matches the PLA phase 1:1 (Fig. N shows the same part and
case in both materials). For side-by-side comparisons use the same # across
`../pla/report_images/` and this folder.
