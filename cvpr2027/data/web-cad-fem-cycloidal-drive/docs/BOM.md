# Bill of Materials — 15:1 cycloidal drive (per article)

Quantities below are the article's. Buy a few spares of the small bearings.

## Bearings

| Part | Spec | Qty | Used for |
|---|---|---|---|
| Ring + output rollers | 686-2RS, 6×13×5 mm | 44 | 16 ring positions × 2 stacked = 32, plus 6 output pins × 2 = 12 |
| Input/output shaft support | 6802-2RS, 15×24×5 mm | 4 | input shaft sections + output shaft |
| Main output support | 6807-2RS, 35×47×7 mm | 2 | housing ↔ output shaft |

## Shafts / hardware

| Part | Qty / size | Notes |
|---|---|---|
| Ground steel rod Ø6 mm | 35 mm long pins for ring gear (16×); article also tried 3 mm rod inside hollow printed pins | Must be true 6.00 mm — an M6 bolt is undersize and wobbles in the 686 bore |
| M3 × 20 mm bolts | 6+ | output roller pins through bearings + spacers |
| M3 through-bolts | 2 | clamp the 4 input-shaft sections (holes printed slightly undersize so bolts self-tap) |
| M4 × 40 mm bolts | 4+ | housing ↔ lid |
| Heat-set threaded inserts | M3 + M4 | output flange face, input-shaft coupler face, housing back, front output face |
| Spacer / distance rings (printed) | 7 mm + 3 mm stacks | ring rollers: 7 / bearing / 3 / bearing / 7 per pin; same idea on output pins |
| NEMA 17 stepper (e.g. 34 mm, ~26 N·cm) | 1 | test motor; any motor works with a matching coupler |
| Printed coupler + motor mount | 1 each | article prints both; coupler bolts to input-shaft inserts |

## Printed parts (this workspace, `models/*.stl`)

| STL | Count | Notes |
|---|---|---|
| `cycloidal_disk` | 2 | identical, mount 180° apart |
| `housing_base` | 1 | ring-gear housing |
| `housing_lid` | 1 | closes the 16 ring pins |
| `ring_pin` | 16 | Ø6 pin seats; add steel rod if worried about PLA shear |
| `input_shaft` | 1 set | eccentric cam(s), E = 1.5 mm |
| `output_flange` (+ back plate) | 1 + 1 | 6 output pins on Ø54 PCD |
| `motor_coupler`, `motor_mount` | 1 each | adapt to your motor |

## Tools / consumables

3D printer + PLA/PETG, slicer with Hole Horizontal Expansion, calipers,
M3/M4 taps or soldering iron for inserts, Allen keys, light grease.
