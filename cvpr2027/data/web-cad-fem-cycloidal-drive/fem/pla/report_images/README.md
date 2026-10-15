# Report figures — FEA von Mises plots (all parts)

Folder: `report_images/`. All 1280×960, isometric, von Mises field with
legend in **Pa** (divide by 10⁶ → MPa). Deformation not scaled (true scale).
Linear static, CalculiX 2.21; every run equilibrium-verified. Details +
safety factors: `fea_all_parts.md`.

| # | File | Part / case | Peak | Suggested caption |
|---|---|---|---|---|
| 1 | 01_disk_pla_200N.png | Cycloidal disk, PLA, 200 N tangential / hole | 5.70 MPa | Disk at 11× rated shock; peak at loaded-hole edge (SF 8.8) |
| 2 | 02_ring_pin_steel_150N.png | Ring pin Ø6×34.8, steel, 150 N transverse | 74.56 MPa | Bending pattern; fixed-end peak is a fixture singularity (SF 3.4) |
| 3 | 03_output_pin_steel_180N.png | Output pin Ø6×15, steel, 180 N transverse | 18.55 MPa | End peaks are fixture singularities (SF 13.5) |
| 4 | 04_spacer_6mm_50N.png | Spacer 6 mm ID, PLA, 50 N axial | 1.81 MPa | Uniform clamp compression (SF 27) |
| 5 | 05_dist_ring_1mm_ID6_30N.png | Distance ring 1 mm ID6, PLA, 30 N axial | 1.32 MPa | (SF 38) |
| 6 | 06_dist_ring_4mm_ID6_30N.png | Distance ring 4 mm ID6, PLA, 30 N axial | 1.44 MPa | (SF 35) |
| 7 | 07_dist_ring_1mm_ID15_50N.png | Distance ring 1 mm ID15, PLA, 50 N axial | 0.90 MPa | Quietest part in the assembly (SF 55) |
| 8 | 08_coupler_100N.png | Shaft coupler, PLA, 100 N axial | 5.12 MPa | Peak at Ø5 motor-bore edge (SF 9.8) |
| 9 | 09_shaft_cam_P2_radial_300N.png | Input cam P2, PLA, 300 N radial bending | 18.45 MPa | Weakest printed part; peak at journal-to-collar fillet (SF 2.7 @ shock, ~4.7 @ rated) |
| 10 | 10_shaft_tail_P1_100N.png | Input tail P1, PLA, 100 N axial | 2.59 MPa | Evenly loaded pilots (SF 19) |
| 11 | 11_mount_50N.png | NEMA 17 mount, PLA, 50 N | 0.84 MPa | Barely loaded (SF 59) |
| 12 | 12_flange_P1_180N.png | Output flange P1, PLA, 180 N on 6 pin seats | 1.91 MPa | Rings around pin seats (SF 26) |
| 13 | 13_flange_P2_180N.png | Output flange P2, PLA, 180 N on 6 M3 holes | 3.04 MPa | Peaks at M3 holes/hub fillet (SF 16) |
| 14 | 14_lid_250N.png | Housing lid, PLA, 250 N radial on bearing seat | 0.64 MPa | Clean seat ring (SF 78) |
| 15 | 15_housing_500N.png | Housing base, PLA, 500 N radial on bearing seat | 0.92 MPa | Linear C3D4 screening run; seat ring only (SF 54) |

Figure-numbering suggestion for the report: use the # column (Fig. 1–15).
Show Figs. 9, 1, 2 large (the three highest-stress parts); group 4–7 + 11 +
14 + 15 as small multiples ("parts with SF > 25").
