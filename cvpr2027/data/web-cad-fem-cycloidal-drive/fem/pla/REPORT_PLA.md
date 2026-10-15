# FEA Report — PLA build, DIY 15:1 cycloidal drive

Reference CAD: `Cycloidal Drive - 3D Printable DIY.STEP` (author's assembly,
216 objects). Method, decks, sessions, figures: this folder (`fem/pla/`);
shared tooling one level up (`fem/`). Analysis date: Sept 2026, FreeCAD 1.1 +
CalculiX 2.21, linear static throughout.

## 1. What was analyzed and why

The article demonstrates 2.6 N·m output from a fully printed reducer, but
never shows whether that is near a limit or far below it. This FEA answers
one question per part: **at a hard shock load, how far is each part from
yielding, and where does it want to break?** Fifteen runs cover every
custom part: 2 disks (1 run, identical), housing, lid, 2 output flanges,
4-section input shaft (P1 tail + P2 cam; P3/P4 same journal family),
coupler, mount, 2 pin types, spacer + 3 distance rings. Bearings, bolts,
inserts and the motor are vendor parts checked analytically (SF > 40).

## 2. How much to trust these numbers

- **Verification, not just colors.** Every run balances: bore/fixture
  reactions equal the applied load to <0.3 % (see `.dat` files). The FreeCAD
  1000× CLOAD under-application bug was caught by this check and corrected
  in all decks. A wrong-direction setup was likewise caught (reaction
  direction ≠ intended) and the cam case re-solved radially.
- **The material card is the weakest link in the analysis.** Isotropic bulk
  PLA (E 3500 MPa, yield 50 MPa) overstates a real FDM print: Z-direction
  strength is typically 50–70 % of X-Y, stiffness drops with infill, and PLA
  creeps under sustained load above ~40 °C. Treat SF 2–3 as "fine for
  occasional shock, watch under continuous duty", SF 8+ as "settled".
- **Fixtures are idealized.** Fixed faces and fixed pin ends create local
  singularities (the pin peaks). Real pressed/bearing contacts spread load
  better, so end-peaks are conservative; membrane/bending fields between
  them are the trustworthy part.
- **Linear statics only.** No contact, no fatigue, no creep, no temperature.
  At rated load everything sits at ≤ ~2 MPa, so geometric nonlinearity is
  irrelevant — but life predictions (wear, creep, layer fatigue) are outside
  what this analysis can say.

## 3. Results in one picture

At shock loads of 2–11× rated, peaks span **0.6–18.5 MPa** against 50 MPa
PLA (pins in steel: 18.6–74.6 vs 250 MPa). Ranked by danger:

1. **Input cam P2 fillet — 18.5 MPa @ 300 N radial (~1.7× rated cam load).**
   The only part within a factor of 3 of yield at anything near service
   load. Bending concentrates exactly where you'd fear: the journal-to-
   collar fillet. At rated 173 N this is ~10.6 MPa (SF ≈ 4.7) — acceptable
   statically, but it is also a rotating-bending fatigue site in printed
   plastic, so it owns the top of the watch-list by a wide margin.
2. **Disk output-hole edge — 5.7 MPa @ 200 N (11×).** SF 8.8 at a load the
   gearbox will likely never see; at rated load ≈ 0.5 MPa. The disk cannot
   yield in service — its life is wear on the lobe flanks and creep around
   the bores, neither of which this (or any static) analysis captures.
3. **Coupler Ø5 bore — 5.1 MPa @ 100 N axial.** SF ~10; the bore edge is the
   only feature working. Boring but healthy.
4. **Flanges (1.9 / 3.0 MPa), tail P1 (2.6 MPa).** Load paths are clean,
   peaks sit on real features (pin seats, M3 holes), margins 16–26×.
5. **Housing (0.92), lid (0.64), mount (0.84), spacers/rings (0.9–1.8).**
   These are stiffness and tolerance parts, not strength parts. The tidy
   bearing-seat rings in Figs. 14–15 are exactly what a healthy drum looks
   like: load goes straight into the seat and dies within millimeters.
6. **Steel pins.** Ring pin 74.6 MPa @ 10× shock (SF 3.4 in steel) vs
   certain death in PLA — the analysis repays the BOM choice quantitatively.
   Output pins coast at SF 13.5.

## 4. What I take away from this (opinion)

- **The printed gearbox is statically overbuilt except for one fillet.**
  That matches the article's experience (it survives 2.6 N·m testing) and
  the hand calcs done earlier — FEA moved the sole concern from "the pins"
  (resolved: steel) to "the cam fillet", which no hand calc isolates as
  cleanly. If this gearbox ever breaks in normal service, my money is on
  the P2/P3 cam collar cracking after many cycles, not on any dramatic
  overload failure.
- **Accuracy, not strength, is the design driver.** The largest computed
  elastic deflection anywhere is 0.05 mm (disk hole at 11× shock); at rated
  load the whole stack breathes single-digit microns. Real-world backlash
  will come from print clearance (0.1 mm ≈ 0.23° slop, per the earlier
  budget) and pin/hole fit — an order of magnitude above elastic effects.
  Money spent on calibration beats money spent on stronger plastic.
- **The upgrade order stands:** steel ring pins (already in BOM) → print
  quality on cams (walls, infill, reamed journals, generous fillets) →
  spare disks (wear) → only then exotic materials. Nothing in these fields
  justifies metal disks or housing for strength.
- **On the direction-overwrite episode:** it cost a re-solve but improved
  the study — the accidental axial cases (coupler pull-out, tail tension,
  mount pull-off) are legitimate secondary load paths worth having on
  record, and all pass.

## 5. What PETG-CF will change (preview for the next phase)

Honestly, less than the material hype suggests — for *static strength*.
Stresses in these fixtures are set by load ÷ area, barely by E, so expect
near-identical stress fields and ~17 % larger deflections (E 3000 vs 3500),
graded against a similar-or-slightly-lower yield. The real PETG-CF payoff
is elsewhere and this analysis can't show it: ~75–80 °C deflection
temperature vs 60 °C PLA (motor heat soak is the sustained-duty limit),
better layer adhesion/creep behavior at temperature, and stiffer thin
features from the chopped fiber. If the PETG-CF rerun shows the cam fillet
at ~18 MPa against a 45 MPa card, the conclusion rhymes with this one —
same weakest link, more thermal headroom. The number to watch in that phase
is not stress but the temperature margin.

## 6. Files and reproduction

- Per part: `FEM_<Part>/` → setup + mesh in `<Part>.FCStd`, deck
  `<Base>.inp`, corrected deck `<Base>_fixed.inp`, `ccx` outputs
  (`.frd/.dat/.sta/.cvg`), CLOAD totals printed at solve time.
- `fea_all_parts.md`: load-case table, equilibrium record, caveats.
- `fea_results.md`: original disk study.
- `report_images/` + `README.md`: 15 captioned figures (Fig. 1–15).
- Rerun any part: `../batch_fea_setup.py::setup_part` (same faces — see
  `fea_all_parts.md`), `../fix_cload_units.py`, `ccx -i`, reload results.
- Known session quirk: reopened `.FCStd` files show stale absolute solver
  paths (pre-reorganization); harmless — reset WorkingDirectory on rerun.
