# Material selection: PLA vs PETG-CF — FEA comparison over all parts

Side-by-side evidence: `side_by_side/Fig 01–15` (left = PLA, right =
PETG-CF; steel-pin Figs. 02–03 are the identical run in both phases).
Source phases: `fem/pla/` (E 3500 MPa, yield 50 MPa) and `fem/petg_cf/`
(E 3000 MPa, yield 45 MPa, generic card — no spool brand on record).
Same faces, forces and meshes; only the material card changed
(steel pins, bearings, bolts, inserts, motor excluded from both).

## Master table (shock load cases)

| # | Part / case | PLA peak (MPa) | PETG peak (MPa) | Δσ | PLA SF (÷50) | PETG SF (÷45) | PLA dmax (mm) | PETG dmax (mm) | ×d |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Disk, 200 N tangential | 5.70 | 5.70 | +0.0 % | 8.8 | 7.9 | 0.0500 | 0.0579 | 1.17 |
| 2 | Ring pin steel, 150 N | 74.56 | — (same) | — | 3.4 | 3.4 | 0.0021 | — | — |
| 3 | Output pin steel, 180 N | 18.55 | — (same) | — | 13.5 | 13.5 | 0.0004 | — | — |
| 4 | Spacer 6 mm, 50 N axial | 1.81 | 1.80 | −0.3 % | 27 | 25 | 0.0028 | 0.0033 | 1.17 |
| 5 | Dist ring 1 mm ID6, 30 N | 1.32 | 1.32 | +0.0 % | 38 | 34 | 0.0003 | 0.0004 | ~1.3¹ |
| 6 | Dist ring 4 mm ID6, 30 N | 1.44 | 1.44 | −0.2 % | 35 | 31 | 0.0011 | 0.0013 | 1.16 |
| 7 | Dist ring 1 mm ID15, 50 N | 0.90 | 0.90 | −0.5 % | 55 | 50 | 0.0002 | 0.0003 | ~1.3¹ |
| 8 | Coupler, 100 N axial | 5.12 | 5.12 | +0.0 % | 9.8 | 8.8 | 0.0065 | 0.0076 | 1.17 |
| 9 | Cam P2, 300 N radial | 18.45 | 18.45 | −0.0 % | 2.7 | 2.4 | 0.0279 | 0.0326 | 1.17 |
| 10 | Tail P1, 100 N axial | 2.59 | 2.59 | +0.0 % | 19 | 17 | 0.0031 | 0.0037 | 1.18¹ |
| 11 | Mount, 50 N | 0.84 | 0.84 | +0.1 % | 59 | 54 | 0.0094 | 0.0109 | 1.16 |
| 12 | Flange P1, 180 N | 1.91 | 1.91 | −0.2 % | 26 | 24 | 0.0071 | 0.0083 | 1.16 |
| 13 | Flange P2, 180 N | 3.04 | 3.04 | +0.1 % | 16 | 15 | 0.0130 | 0.0152 | 1.17 |
| 14 | Lid, 250 N radial | 0.64 | 0.64 | +0.1 % | 78 | 70 | 0.0009 | 0.0011 | ~1.2¹ |
| 15 | Housing, 500 N radial | 0.92 | 0.92 | −0.4 % | 54 | 49 | 0.0016 | 0.0018 | ~1.1¹ |

¹ ×d computed against PLA values rounded to 1–2 significant figures;
unrounded ratios all sit at 3500/3000 = 1.1667.

Reading the table: the Δσ column is all zeros. That is the finding.

## Part-by-part comparison (what the image pairs show)

- **Fig. 01 disk.** Identical fields: loaded-hole edge hotspot, secondary
  path toward the fixed bore, same legend (5.70 MPa both). Only the SF
  label differs (8.8 → 7.9) because the yardstick changed, not the part.
  Verdict: no material decision here — wear and bore creep govern, and
  neither static run captures them.
- **Figs. 02–03 steel pins.** Same pixels both sides by construction.
  Included so the set covers all parts; the comparison conclusion is that
  there is nothing to compare — steel was already the right call in both
  phases (ring pin SF 3.4 in steel vs certain death in PLA).
- **Figs. 04–07 spacer + rings.** Uniform clamp compression, peak values
  within 0.5 %. These parts are preload spacers; the live question is
  creep under sustained clamp + heat, where PETG-CF is expected to hold
  tolerance better — not visible in statics, noted for the conclusion.
- **Fig. 08 coupler.** Same Ø5 bore-edge peak (5.12 MPa both). SF 9.8 →
  8.8. No decision content.
- **Fig. 09 cam P2 (the one that matters).** Same bending field, same
  journal-to-collar fillet hotspot, same legend (18.45 MPa). SF 2.7 → 2.4
  at shock; ≈4.7 → ≈4.2 at rated 173 N. The pair shows the material swap
  does not move, shrink, or reshape the one stress concentration that
  counts. If this gearbox breaks in service, both materials point at the
  same fillet.
- **Fig. 10 tail P1.** Evenly loaded pilots, 2.59 MPa both. SF 19 → 17.
- **Fig. 11 mount.** Barely loaded both (0.84 MPa). This is a hot part
  (motor face) — its comparison belongs to thermals, not statics.
- **Figs. 12–13 flanges.** Same pin-seat rings (P1) and M3-hole/hub peaks
  (P2). SF 26→24, 16→15. No decision content.
- **Figs. 14–15 lid + housing.** Clean bearing-seat rings both, peaks
  under 1 MPa. The housing pair also confirms the linear-C3D4 screening
  run reproduces across materials (0.92 → 0.92 MPa).

Note on rendering: PLA figures are smooth-shaded, PETG-CF figures show
the mesh wireframe (different post settings between phases). Field,
legend range and hotspot location are directly comparable regardless.

## Conclusion — which material, and why

1. **On static strength alone, PLA wins by a nose and it does not
   matter.** Every SF in the PETG-CF column is ~10 % lower (45 vs 50 MPa
   against identical stress). No part crosses any threshold because of
   it: the weakest link (cam fillet, SF 2.4 @ shock / 4.2 @ rated) keeps
   the same margin class, everything else stays above 7. Switching to
   PETG-CF for higher load capacity would be a mistake — the numbers say
   the capacity does not change.
2. **On temperature and creep — the actual selection criterion — PETG-CF
   is the right call for sustained duty.** The rerun proves the whole
   housing/mount/shaft stack is stress-idle at rated load (≤ ~2 MPa),
   i.e. those parts were never strength-limited; their limit is
   softening/creep at motor-soak temperatures, where ~75–80 °C HDT beats
   ~60 °C PLA. Room-temperature short demos: PLA is fine and 17 %
   stiffer. Hot, long runs: PETG-CF.
3. **The generic-card uncertainty dominates the only close call.** PETG-CF
   spans ~35–60 MPa by brand. At the cam fillet that is SF 1.9 → 3.3 at
   shock. Whichever plastic is chosen, the mitigating actions are the
   same and are geometric, not material: high wall count/infill on shaft
   sections, reamed Ø15 journals, generous collar fillets, print
   orientation that puts fiber/walls across the fillet — plus
   inspect-on-interval for a rotating-bending fatigue site no static
   analysis can clear.
4. **Accuracy, not material, still governs build quality.** +17 %
   deflection keeps elastic effects an order of magnitude below print
   clearance (≈0.1 mm ≈ 0.23°). Calibration effort outranks the spool
   choice.

**Bottom line:** print PLA for prototyping and cool short runs; print
PETG-CF (spool-locked card) for the working gearbox if the motor runs
warm or long. Keep steel pins, keep an eye on the P2/P3 cam fillet, spend
the saved worry on calibration. Back it with the cheapest decisive test
available: a thermocouple on the mount during a 30-minute loaded run.
