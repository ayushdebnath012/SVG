# CAD Model Understanding — Cycloidal Drive 3D Printable DIY

Reference for future work on `Cycloidal Drive - 3D Printable DIY.STEP`.
All data measured in FreeCAD (doc `STEP_Analysis`, 216 objects).
Assembly axis = **X**. Stack: motor → mount → housing → lid → output flange.
Overall envelope with motor: **144 × 115 × 115 mm**. Units: mm.

Conventions below: "Ø" diameters and bore lists are measured cylinder-face
inventories (r→face count; each through-bore contributes 2 faces), so
`r3.0 ×32 faces` = 16× Ø6 through-holes. Volumes are solid material volumes.

---

## 1. Printed parts

### 1.1 Roller pins housing (base) — ×1
- **Size:** Ø115 × 35 deep (X 84–119). Volume ≈ 126,859 mm³. Largest print.
- **Features (measured bores):** 16× Ø6 pin bores on Ø90 PCD (through floor);
  Ø47 main-bearing seat (r23.5); M4 bolt circle (8× M4×40 close it to the lid);
  M4 insert pockets; outer Ø115 register (r57.5).
- **Interfaces:** 16 ring-pin stacks press into floor; 6807 bearing in center;
  NEMA mount bolts to back; lid bolts to front; carries all ring-gear torque.
- **Print:** flat on back face, pin bores vertical. Highest accuracy need
  (pin circle + bearing seat). 4–5 walls, 40–60% infill.

### 1.2 Roller pins housing lid — ×1
- **Size:** Ø115 × 9 (X 119–128). Volume ≈ 74,715 mm³.
- **Features:** matching 16× Ø6 pin seats on Ø90 PCD; Ø47 bearing seat;
  8× M4 clearance holes.
- **Interfaces:** caps all 16 ring pins (tight simultaneous fit — even pressure);
  retains front 6807 bearing.
- **Print:** flat, bores vertical. Same tolerance care as base.

### 1.3 Cycloidal disk — ×2 (identical solid, different instance)
- **Size:** Ø≈79.6 (r_max ≈ 39.8 = R−Rr+E ✓) × 5 thick (X 99–104 / 107–112).
  Volume ≈ 15,590 mm³ each.
- **Features:** 15 lobes; center bore Ø24 (r12, seats the 6802 OD24 ring);
  6× Ø16 output holes (r8.0) on Ø49 circle (24.5 radius);
  1× Ø2 witness/timing hole (r1.0) for 180° phasing.
- **Interfaces:** rolls inside the 32 ring rollers; rides the eccentric cams
  via 6802 bearings in its center bore; output pins pass through the Ø16 holes
  (hole = 13 + 2×1.5 ✓).
- **Mounting:** the two instances sit 8.0 apart in X with mass centers offset
  to opposite sides — 180° out of phase. Match witness marks on assembly.
- **Print:** flat. Most tolerance-critical profile in the build; verify
  Hole Horizontal Expansion with a test bore first. Print a spare.

### 1.4 Input shaft p1 – p2 – p3 – p4 (×1 each, assembled as one shaft)
- **Sizes:** all Ø20 collars; journals Ø15 (r7.5); thicknesses Z/X 12 / 9 / 8 / 8.
  Volumes ≈ 2449 / 1762 / 1460 / 1446 mm³.
- **Features:** 2× M3 through-holes total (r1.35, printed undersize so bolts
  self-tap — clamps all 4 sections); p1 adds coupler-side holes (r2.0);
  p4 adds register holes (r2.8). Cam journals run offset ±E (≈1.5) in opposite
  senses (measured COM offsets oppose each other).
- **Bearings on shaft:** 4× 6802 (15 ID on the Ø15 journals, 24 OD into the
  disk bores) with 1 mm ID15 distance rings between/around them (×6 total).
- **Interfaces:** tail end → shaft coupler (M3 inserts); cams → disk bores via
  6802s; shaft body → supported inside output-flange bores.
- **Print:** axis vertical if possible; ream Ø15 journals after print.
  Assemble the stack *through* the disks — disks cannot be added afterwards.

### 1.5 Output disk flange p1 (pin side) — ×1
- **Size:** Ø60 × 13 (X 85–98, lives inside housing rear). Volume ≈ 16,002 mm³.
- **Features:** 6× Ø6 output-pin seats on Ø49 circle (r3.0); 6× M3 insert
  pilots (r1.5); stepped center bore (Ø21–37 registers for input-shaft support
  bearings); OD Ø60 register (r30).
- **Interfaces:** 6 output-pin stacks (pin + 2× 686 + 1/4 mm rings on M3×20)
  press here and pass through the disk Ø16 holes.

### 1.6 Output disk flange p2 (back/outer side) — ×1
- **Size:** Ø60 × 16 (X 113–129, spans housing front + lid zone).
  Volume ≈ 18,891 mm³.
- **Features:** 6× M3 bolt holes (r2.0) mating the pin stacks; center bore for
  input shaft clearance; front face takes M3 inserts for load horn/wheel.
- **Interfaces:** closes the 6 pin stacks (6× M3×20); runs in the front 6807.

### 1.7 NEMA 17 motor mount — ×1
- **Size:** 74 × 42 footprint × 24 tall (X 60–84). Volume ≈ 24,198 mm³.
- **Features:** NEMA 17 31 mm PCD hole pattern (M3); Ø24 center clearance;
  M4 interface to housing back.
- **Print:** flat on mounting face.

### 1.8 NEMA 17 shaft coupler — ×1
- **Size:** Ø20 × 15 (X 69–84). Volume ≈ 2,063 mm³.
- **Features:** Ø5 motor-shaft bore (r2.5 ✓ NEMA 17 shaft); clamp/screw holes
  (M3); register to input-shaft tail inserts.
- **Note:** motor-shape dependent — remodel if motor changes.

### 1.9 Small printed parts
| Part | Qty | Measured size | Role |
|---|---|---|---|
| 6 mm shaft, roller pins | 16 | Ø6 × 34.8 | ring-pin cores (use ground Ø6 rod if PLA shears) |
| 6 mm shaft, output pins | 6 | Ø6 × 15 | output-pin cores |
| Spacer 6 mm ID | 48 (16 + 32 same geometry) | Ø9 OD × 7 long | ring-stack spacers (7 mm stations) |
| Distance ring 1 mm ID 6 | 12 | Ø8.4 × 1 | output-stack shims |
| Distance ring 4 mm ID 6 (measures 3.0) | 6 | Ø8.4 × 3 | output-stack mid spacers — verify thickness before reorder |
| Distance ring 1 mm ID 15 | 6 | Ø17.6 × 1 | input-shaft bearing shims |

---

## 2. Purchased parts (as modeled)

| Part | Qty | Measured | Role |
|---|---|---|---|
| 686-2RS | 44 | Ø13 × 5 | 16 ring × 2 + 6 output × 2 rollers |
| 6802-2RS (15×24×5) | 4 | Ø24 × 5 | input cams → disk bores |
| 6807-2RS (35×47×7) | 2 | Ø47 × 7 | housing ↔ output flanges |
| NEMA 17, 20 mm shaft | 1 | 42 × 42 × 60 | test drive (≈26 N·cm class) |
| M4×40 | 8 | 44 long w/ head | housing ↔ lid |
| M3×30 | 2 | 33 long | input-shaft clamp |
| M3×20 (DIN 912) | 6 | 23 long | output-pin stacks |
| M3×10 / M3×8 | 4 / 4 | — | mount + coupler |
| M4 inserts L5 | 8 | Ø5.6 × 5 | housing/lid |
| M3 inserts L5 | 9 | Ø4 × 5 | flanges, coupler, output face |

---

## 3. Power path & key relationships (do-not-break list)

1. **Ratio = 15:1, reversed.** 16 ring rollers → 15-lobe disks. Verified:
   pin PCD Ø90.00, adjacent spacing 17.56 = 2·45·sin(π/16).
2. **E ≈ 1.5 < Rr/2 = 3.25** — required for the epitrochoid to exist.
3. **Disk holes Ø16 = roller Ø13 + 2E** — the mesh clearance. Do not resize
   independently.
4. **Two disks, 180° apart, 8.0 stack pitch** — balance; witness holes aligned.
5. **Ring stack order per pin:** 7 mm spacer / 686 / mid spacer / 686 / 7 mm.
6. **Output stack per pin:** pin + 2× 686 + 1/4 mm rings on M3×20, flanges both ends.
7. **Fit hierarchy (tightest first):** disk profile → 686 bores → Ø6 pin seats →
   Ø47/Ø24 bearing seats → M4/M3 patterns.

## 4. If you remodel

- Drive everything from N, R, Rr, E (`parameters.json`).
- Keep disk thickness 5, stack pitch 8, output circle Ø49 unless you re-derive
  pin/hole engagement.
- Coupler + mount are the only motor-specific parts.
- Slicer: Hole Horizontal Expansion ≈ 0.07, Horizontal Expansion ≈ 0.02;
  test coupon Ø6/Ø13/Ø16/Ø24 before committing to disks + housing.
