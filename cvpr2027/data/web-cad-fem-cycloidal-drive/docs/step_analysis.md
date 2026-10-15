# STEP analysis — Cycloidal Drive 3D Printable DIY

Source file: `Cycloidal Drive - 3D Printable DIY.STEP` (3.0 MB, 216 objects
imported into FreeCAD doc `STEP_Analysis`, assembly axis = X).

## Identity

This is the original HowToMechatronics 15:1 cycloidal reducer assembly —
housing + lid, 16 ring-roller stacks, 2 cycloidal disks, 4-piece eccentric
input shaft, 2-piece output flange with 6 pin stacks, NEMA 17 + mount +
coupler, all bearings, spacers, bolts, and threaded inserts modeled.

## Measured key geometry (mm, from FreeCAD)

| Part | Size | Notes |
|---|---|---|
| Cycloidal disk (×2) | Ø≈79.6 × 5 thick | radius ≈ 39.8 ≈ R−Rr+E = 40 ✓ |
| Ring-roller PCD | Ø90.00 (max pin-center distance) | R = 45 ✓; adjacent pins 17.56 = 2·45·sin(π/16) ✓ |
| Ring pins (×16) | Ø6 × 34.8 | = 6×35 ground rod per BOM |
| Ring rollers | 686, Ø13 × 5 (×44 = 16×2 ring + 6×2 output) | |
| Output pin circle | Ø49 (max center distance) | r = 24.5 |
| Output pins (×6) | Ø6 × 15 | through disk holes |
| Output flanges | Ø60, 13 / 16 thick | p1 (pins) + p2 (back) |
| Housing | Ø115 × 35 | lid Ø115 × 9 |
| Input shaft p1–p4 | stepped sections, cams opposed | COMs offset ±~1–1.3 in Y, opposite senses → E ≈ 1.5, 180° apart ✓ |
| Disks stacked | 8.0 apart in X, COMs offset ±~1 opposite | 180° out of phase ✓ |
| Main bearings | 2× 6807 (35×47×7), 4× 6802 (15×24×5) | counts match article |
| Overall with motor | 144 × 115 × 115 | motor 42×42 NEMA 17 × 60 long |

## Fastener / insert census (from label groups)

- 8× M4×40 (housing), 2× M3×30 (input shaft through-bolts),
  6× M3×20 (output pins), 4× M3×10 + 4× M3×8 (mount/coupler)
- 8× M4 + 9× M3 heat-set inserts
- Spacers: 16 + 32 (ring stacks, 6 mm ID family), 12× 1 mm + 6× 4 mm (output)

## Power path (as modeled)

NEMA 17 → coupler → 4-section eccentric input shaft (6802-supported cams)
→ 2 opposed cycloidal disks walking inside the 16×2 ring rollers
→ 6 output-pin stacks through oversized disk holes → output flanges
(6807-supported) → load. Ratio 15:1, output reversed.

## Views checked

- Isometric full assembly: motor–mount–drum–lid–output flange all concentric.
- Shell hidden: 16 ring stacks ring the disk; input cams centered.
