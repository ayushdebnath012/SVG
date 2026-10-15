# FEA Report — PETG-CF build, DIY 15:1 cycloidal drive

Rerun of the PLA static study (`../pla/REPORT_PLA.md`) with printed parts
switched to carbon-filled PETG. Method, decks, sessions, figures: this
folder (`fem/petg_cf/`); shared tooling one level up (`fem/`). Analysis
date: Sept 2026, FreeCAD 1.1 + CalculiX 2.21, linear static throughout.

Material card (generic — no spool brand on record): E 3000 MPa, ν 0.36,
ρ 1300 kg/m³, design yield **45 MPa**, UTS 55 MPa. Steel pins unchanged
(no rerun); purchased parts analytical (SF > 40); P3/P4 covered by P2
similarity.

## 1. Headline: the rerun behaved exactly as linear statics says it should

Across all 14 setups, **stress fields reproduce PLA to within ±0.5 %**
(table rounding) and **displacements scale by 3500/3000 = ×1.167**.
Hotspot nodes and coordinates are unchanged (disk node 7, cam fillet
nodes, coupler bore edge). Nothing deviated, so per the phase plan no
investigation was triggered. This is itself the result: in these
statically-determinate fixtures stress is load ÷ area, and the modulus
change only softens the response by one-sixth.

Ranked by danger at the same shock loads (SF now vs the 45 MPa card):

1. **Input cam P2 fillet — 18.45 MPa @ 300 N radial (~1.7× rated). SF 2.4**
   (PLA: 2.7). Still the only printed part within a factor of 3 of yield
   anywhere near service load, still a rotating-bending fatigue site. At
   rated 173 N: ~10.6 MPa → **SF ≈ 4.2**. Same watch-list top spot.
2. **Disk output-hole edge — 5.70 MPa @ 200 N (11×). SF 7.9.** Same
   conclusion: cannot yield in service; life is flank wear + bore creep.
3. **Coupler Ø5 bore — 5.12 MPa @ 100 N. SF 8.8.** Healthy.
4. **Flanges (1.91 / 3.04 MPa), tail P1 (2.59 MPa).** SF 15–24, clean load
   paths, same peaks as PLA.
5. **Housing (0.92), lid (0.64), mount (0.84), spacers/rings (0.9–1.8).**
   SF 25–70: stiffness and tolerance parts, as before.

The whole printed gearbox still **passes statically with margin**, with
exactly one fillet worth worrying about — same sentence as the PLA
report, one material later.

## 2. What PETG-CF actually buys (and what it doesn't)

**Not static strength.** The SF column above is slightly *worse* than
PLA's (yield 45 vs 50 MPa evaluated against identical stresses). Anyone
switching to PETG-CF for higher shock capacity is buying the wrong thing:
at these geometries the stress is set by the load case, not the spool.

**Temperature headroom — the real reason to switch.** PLA softens and
creeps above ~40–60 °C; PETG-CF holds stiffness to ~75–80 °C HDT. The
sustained-duty limit of this gearbox is motor heat soak into the mount,
housing and input-shaft bores — all parts this rerun shows are
stress-idle (SF 17–70) and therefore currently *temperature-limited,
not strength-limited*. The rerun quantifies that split: at rated load
every one of those parts sits at ≤ ~2 MPa, so their failure mode was
never yielding — it is creep/softening at temperature, exactly where
PETG-CF wins and this (or any) static analysis cannot follow. If the duty
cycle is short demos at room temperature, PLA's SF column is already
fine and the switch buys little. If the motor runs hot for tens of
minutes, the switch buys the duty cycle.

**Creep and layer behavior.** Same story one level down: PLA creeps under
sustained load even at moderate temperature (disk bores, ring stack
preload, shaft journals lose tolerance before they lose strength).
PETG-CF creeps less and its chopped fiber stiffens thin features (mount
ribs, ring sections) across print orientations. The displacements in the
table (+17 % from the modulus drop) are the *instantaneous elastic*
response — the long-term print is that PETG-CF holds those numbers while
PLA drifts past them under heat + time.

**Accuracy is still the design driver.** Largest elastic deflection at
shock is 0.058 mm (disk, 11× load); at rated load the stack breathes
single-digit microns — plus 17 % vs PLA, still an order of magnitude
below the ~0.1 mm print-clearance slop (~0.23°) from the earlier budget.
Calibration beats material, again.

## 3. How much to trust these numbers (deltas vs the PLA caveats)

- **Verification is as strong as PLA's.** 13 of 14 decks balance to
  0.001 %; the Coupler's 0.667 % applied-vs-reaction gap reproduces the
  PLA Coupler deck digit-for-digit (inherited case property, not a
  PETG artifact). CLOAD totals equal the settings; directions equal the
  PLA actually-applied vectors to 6 decimals.
- **The material card is now *more* uncertain, not less.** Generic
  PETG-CF spans ~35 MPa (value brands) to ~55–60 MPa (Bambu-class) tensile
  depending on brand, orientation and fiber fraction — a wider band than
  generic PLA. At the cam fillet (18.45 MPa shock / 10.6 MPa rated) that
  band is the whole verdict: SF 1.9/3.3 at 35 MPa, 2.4/4.2 at 45 MPa,
  3.0–3.3/5.2–5.7 at 55–60 MPa. **Lock the card to the spool datasheet
  before using the cam-fillet SF for any duty decision.** Every other
  part passes under the weakest card in the band.
- **Anisotropy cuts both ways for CF grades.** Chopped fiber improves Z
  adhesion vs neat PLA but parts remain strongly anisotropic; the cam
  fillet stress is interlayer tension/compression depending on print
  orientation — orient shaft sections so the fillet sees fiber-aligned
  walls, or the isotropic SF 2.4 overstates reality by up to ~2×, same
  warning as PLA, slightly sharper.
- **Fatigue is still outside the frame.** The cam fillet sees fully
  reversed rotating bending every input revolution; neither the PLA nor
  this rerun says anything about cycle life. PETG-CF's better layer
  adhesion should help, but "should" is not a number — inspect/replace
  cams on interval if the gearbox works hard.
- Fixtures idealized (fixed-end pin singularities N/A here — steel pins
  not rerun), linear statics only, no contact/creep/temperature coupling.
  Same fine print as PLA.

## 4. What I take away (opinion)

- **Same weakest link, more thermal headroom** — exactly the preview in
  the PLA report §5, now with numbers behind it. The upgrade order from
  PLA stands, with one edit: steel ring pins (in BOM) → print quality on
  cams → **spool-locked material card + hot-soak testing** → spare disks
  (wear) → only then exotic materials. The third item is new: the static
  case for PETG-CF is neutral-to-slightly-negative, so the justification
  has to come from measured temperature behavior, and the analysis says
  where to look (mount/housing bores, shaft journals — the hot,
  stress-idle parts).
- **Do not chase stiffness with this swap.** −14 % modulus shows up
  directly as +17 % deflection. Nothing in the stack cares (microns), but
  if a future revision runs thin compliant features near tolerance
  limits, PLA is the stiffer choice at room temperature.
- **For sustained duty, pair the material with a temperature number.**
  The single most valuable follow-up is not more FEA — it is a
  thermocouple on the mount during a 30-minute loaded run, plus a
  sustained-preload creep check on the ring stack. If the housing stays
  under ~60 °C, PLA was already fine; if it soaks past that, PETG-CF
  earns its keep and the SF column in this report is the receipt.

## 5. Files and reproduction

- Per part: `FEM_<Part>_PETGCF/` → setup + mesh in
  `FEM_<Part>_PETGCF.FCStd`, raw deck `<Base>.inp`, solved deck
  `<Base>_fixed.inp` (`ShaftP2_radial*.inp` for the true-radial cam case),
  `ccx` outputs, CLOAD totals printed at solve time.
- `fea_all_parts_PETGCF.md`: load-case table, PETG-vs-PLA comparison,
  equilibrium record, method notes.
- `report_images/` + `README.md`: 15 captioned figures (Fig. 1–15, same
  numbering as PLA; Figs. 2–3 reuse the unchanged steel-pin figures).
- Rerun any part: `petg_setup.py::setup_petg` (faces/forces in
  `fea_all_parts_PETGCF.md`), `../../fix_cload_units.py`, `ccx -i`,
  `petg_results.py::load_and_stats`, `petg_figures.py::make_figure`.
- Known quirks: reopened `.FCStd` files may show stale absolute solver
  paths (harmless — reset WorkingDirectory on rerun); post pipelines are
  pipeline-only (warp/contour nesting is not scriptable in FreeCAD 1.1 —
  see `fea_all_parts_PETGCF.md` §Method notes).
