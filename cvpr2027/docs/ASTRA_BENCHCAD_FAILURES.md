# Astra's 35 BenchCAD misses: failure analysis

GPT-6 Astra (medium effort, one answer per task) is exactly right on 89 of the 124 held-out BenchCAD edits (strict volume IoU >= 0.99999 against the released target). This file classifies the other 35 by reading Astra's patch against the reference patch, line by line. Classification is manual (one annotator) and should be checked before it is cited.

Data: `runs/astra-failure-analysis-20261008/cases.json` (per-case record), `runs/multisource-cad-astra-20261004` (answers and scores), `runs/got-fem-astra-20261007` (other Astra drafts and target-free checks), `runs/adaptive-cad-open-20261007` (Qwen3.5 runs). Surface IoU follows RealCADBench (arXiv:2609.03773).

## Summary

| Group | Category | Cases | Pass every target-free check | Another Astra draft is right |
|---|---|---|---|---|
| Benchmark (Astra follows the instruction) | A1: Reference defect: Astra matches the reference program | 4 | 4 | 0 |
| Benchmark (Astra follows the instruction) | A2: Instruction rounds the reference value | 3 | 3 | 0 |
| Benchmark (Astra follows the instruction) | A3: Reference contradicts the instruction | 6 | 4 | 1 |
| Astra error | B: Invalid or non-executable output | 3 | 0 | 1 |
| Astra error | C: Placement, frame or operation order | 8 | 5 | 1 |
| Astra error | D: Derived geometry or construction | 5 | 4 | 2 |
| Astra error | E: Edit scope: extra or propagated change | 6 | 4 | 4 |

**13 of the 35 misses (37 %) are benchmark issues, not Astra errors.** In 4 the answer equals the reference program but the released target STEP disagrees with it or is invalid; in 3 the instruction states a rounded value (21 mm) while the target uses the precise one (20.98 mm); in 6 the reference contradicts its own instruction (it removes a slot the instruction asks to cut, adds no dome, or mis-computes across-flats). Counting only the first two groups as correct puts Astra at 96/124; counting all three at 102/124 (82 %).

**22 misses are genuine Astra errors**, in four kinds:

- **Placement, frame or operation order (8).** The right feature at the right size, in the wrong place: a recess positioned with `workplane()` inside the build chain rather than at the bounding-box centre, a ring at the wrong height, holes along the wrong axis, a rotation inserted before later features. Median volume IoU 0.98, so whole-shape volume barely registers them.
- **Edit scope (6).** Astra changes more than the reference: it keeps a wall thickness or keeps a raised face attached when a height changes (4 cases; defensible design-intent readings the reference does not share), removes a second hole, or deletes one call too many so later features inherit an offset.
- **Derived geometry or construction (5).** Multi-step arithmetic or shape construction: dependent offsets recomputed wrongly, a ratio applied to every profile point, cross arms rebuilt as arcs, a bevel built as a loft.
- **Invalid output (3).** A patch that cannot be applied, no parsable patch, or a chamfer the kernel rejects.

## What this means for verification and search

- 24 of the 35 misses pass every target-free check (geometry, requested values, change, FEM). That includes 11 of the 13 benchmark cases, which is expected because Astra followed the instruction there, and 13 of the 22 genuine errors, which is why the verifiers, GoT/MCTS and the DPO checker could not separate them from correct answers.
- Repair helps only the 3 invalid outputs, the one failure type Astra rarely makes; with the Qwen planner (whose misses are mostly invalid patches) the same pipeline gained 13 tasks.
- Another saved Astra draft is right on 9 misses. Four are edit-scope errors, three of them fixed by the retrieval draft, whose worked examples follow the dataset's convention of changing only the named dimension.
- Tiers: T4 feature edits 15, T5 new geometry 10, T3 derived values 5, T1 3, T2 2. Simple literal and transform edits (T1/T2) rarely fail, and 4 of those 5 failures are benchmark or scope issues.

## Per-case table

| # | Task | Tier | Part | Category | Volume IoU | Surface IoU | Passes checks | Instruction | What happened |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `277d8aa207505807` | T3 | twisted_bracket | D | 0.5751 | 0.551 | yes | Set each flange plate length equal to twice the plate width; the twist segment, plate thickness, and hole pattern (relative to plate ends) stay the same. | plate length doubled; dependent plate and hole offsets propagated with wrong arithmetic, one hole offset not moved |
| 2 | `5349e2901f1920ed` | T5 | hex_standoff | D | 0.9913 | 0.926 | no | Bevel the six straight outer edges of the top face at 30 degrees from horizontal, 2 mm wide on the top. | bevel built as a lofted hexagon intersection instead of a 30-degree chamfer; close but not the same solid |
| 3 | `0a16dd8acdfcef6b` | T3 | connecting_rod | A1 | 1.0000 | 1.000 | yes | Set the small-end outer radius equal to one third of the big-end outer radius; the shank, big-end bore, and counterbore stay the same. | exact 9.4/3 versus the reference rounded to 3.133; IoU 1.0000 at four decimals, just under the strict threshold |
| 4 | `d000c8c09d558154` | T5 | propeller | B | invalid | 0.000 | no | Add a small flat round boss on top of the central hub, 16 mm in diameter and 3 mm thick, centered on the central axis above the existing tapered top of the hub. | union chain inserted after a completed statement; patch invalid |
| 5 | `bc48c07fbbe8a300` | T3 | bellows | D | 0.9266 | 0.551 | yes | Set the outer radius equal to three times the inner radius; the number of convolutions and convolution height stay the same. | outer radius = 3x inner applied as a linear rescale of every profile point, reference changes only the peak radii |
| 6 | `78ed9867fdc028e6` | T4 | knob | C | 0.9934 | 0.893 | no | Add a centered hexagonal blind recess on the top face of the tapered knob, with a 4.00 mm size and a 5.43 mm depth. | hexagonal recess placed with workplane() inside the build chain instead of the bounding-box centre after it |
| 7 | `511b48e9304b4f20` | T4 | connecting_rod | B | invalid | 0.000 | no | Add a 45-degree chamfer to all top edges of the connecting rod. The chamfer width equals half the small-end bore radius. The base geometry, big-end through-hole, and small-end bore are unchanged. | chamfer on every +Z edge fails in the kernel; no solid |
| 8 | `15eccb8909e47128` | T4 | capsule | A3 | 0.9299 | 0.811 | yes | Remove the upper hemispherical end cap (the sphere at +Z); the cylinder body, the lower hemispherical cap at -Z, and the central bore stay the same. The result is a flat-topped half-capsule. | reference also deletes the central bore that the instruction says stays; Astra keeps it |
| 9 | `02f4de6321541a5c` | T5 | knob | C | 0.9799 | 0.920 | yes | Add a round flat cap on top of the knob, 8 mm in diameter and 1.5 mm thick, centred on the central axis and sitting flush above the existing top face. | cap union inserted mid-chain, so later operations also act on it |
| 10 | `a5b5cc677cadf72d` | T2 | rivet | A1 | invalid | 0.755 | yes | Rotate the entire part by 90° about the X axis. | patch identical to the reference program; released reference STEP is invalid |
| 11 | `51b6a18ad24356d6` | T5 | bellows | C | 0.7471 | 0.696 | no | Add a flat annular ring around the mid-height of the bellows, with outer radius 35 mm, inner radius 26 mm, and thickness 6 mm, lying flat against the central waist. | ring placed at y=49 and extruded one-sided instead of centred at mid-height y=23.5 |
| 12 | `ca142e3a04e88741` | T1 | bellows | E | 0.0000 | 0.774 | yes | Increase the inlet-end outer radius from 100.0 mm to 130.0 mm, changing the upstream outer wall from a straight cylindrical section to a tapered conical section. | inlet radius changed and the opposite wall point moved too (123.2 to 153.2); profile breaks |
| 13 | `de5dd311e2060f59` | T5 | cruciform | D | 0.7200 | 0.531 | yes | Modify the original cross-shaped CAD part by replacing the four rectangular protrusions with semicircular rounded protrusions, where each arc has a diameter equal to the original protrusion width. | cross arms rebuilt as four corner-to-corner arcs; straight arm sides lost |
| 14 | `1918890a624c01e6` | T3 | round_flange | E | 0.8838 | 0.713 | yes | Set the outer cylinder height equal to half the outer radius; the bolt holes, raised face, and neck stay the same. | height changed and raised face and neck moved down to stay attached; instruction says they stay |
| 15 | `43b8a23fd4235e98` | T4 | stepped_shaft | A3 | 0.9673 | 0.925 | no | Cut a centered obround blind slot into the top face of the upper cylindrical section, with a length of 18.16 mm, a width of 6.81 mm, and a depth of 7.06 mm. | instruction says cut a slot but the reference removes the existing slot; Astra returns no edit |
| 16 | `b2096df2210f9ba0` | T2 | knob | C | 0.9935 | 0.913 | yes | Rotate the entire part by 60 degrees about the axis (1, 1, 0). | rotation inserted mid-chain, before later features, instead of rotating the finished part |
| 17 | `36fbd041eb815d50` | T5 | locator_block | C | 0.9593 | 0.901 | yes | Add a raised round boss centered on the top face of the locator block, 30 mm in diameter and 14 mm tall, sitting flush above the existing top and flanking the rectangular pocket. | boss placed on the centre of mass of the +X-most top face, not the part centre |
| 18 | `9137a0ea501a2de0` | T3 | hex_standoff | A3 | 0.8660 | 0.812 | yes | Set the standoff height equal to twice the across-flats size; the bore and hex profile stay the same. | 2 x across-flats computed correctly (15.012 x sqrt 3 = 26.0); reference uses 2 x circumscribed diameter (30.0) |
| 19 | `1bb334960dd15881` | T1 | bellows | E | 0.7936 | 0.657 | no | Reduce the throat radius from 58.7 mm to 40.0 mm, decreasing the throat diameter from 117.4 mm to 80.0 mm. | throat radius reduced and the inner wall moved to keep thickness; reference changes the outer points only |
| 20 | `5eb603a43d1d4c21` | T5 | twisted_bracket | B | invalid | 0.000 | no | Add 3 extra bolt through-passages to each of the two flat end plates, so each plate now has a 2 by 2 grid of 4 bolt holes of 6.5 mm diameter, evenly arranged on the plate around its existing single hole. | no parsable patch |
| 21 | `478c058d89cf5ac9` | T4 | hex_standoff | A3 | 0.8053 | 0.812 | yes | On the top, add a spherical dome of 5.5 mm radius centered on the central axis. | instruction adds a dome but the reference deletes the existing spherical cut; Astra adds a hemisphere |
| 22 | `b61bd7f12f1b5e94` | T5 | connecting_rod | C | 0.9318 | 0.854 | yes | Drill 4 round through-passages of 4 mm diameter through the flat middle section of the rod, in a single straight line at 25 mm, 40 mm, 55 mm, and 70 mm along the length, perpendicular to the wide flat faces. | holes drilled along Y (XZ workplane) instead of through the wide faces along Z |
| 23 | `76ca895fdaf81169` | T4 | stepped_shaft | A3 | 0.9467 | 0.875 | no | Add a centered hexagonal blind recess on the top face, with a polygon radius of 9.08 mm and a depth of 8.00 mm. | polygon radius 9.08 read as diameter 18.16 (CadQuery polygon takes a diameter); reference uses 9.08 directly |
| 24 | `af5c96f6ae6060d3` | T5 | stepped_shaft | C | 0.9318 | 0.789 | yes | Add 2 round cross-holes of 8 mm diameter through the middle thicker step of the shaft, both perpendicular to the central axis, at 25 mm and 45 mm from the bottom face of the shaft. | cross-hole heights shifted by half a step height (frame assumption); direction X versus Y |
| 25 | `c2b9c8d36d164d83` | T4 | motor_end_cap | A2 | 0.9980 | 0.968 | yes | Drill a 33 diameter through-hole along the Z axis. | instruction says 33 mm; reference hole is 33.4 mm (radius 16.70) |
| 26 | `4e9651f30263c884` | T4 | motor_end_cap | E | 0.9502 | 0.921 | no | Remove a 33 diameter through-hole along the Z axis. | removes the requested hole and a second, existing 32.9 mm hole |
| 27 | `99705d173001fd23` | T4 | knob | A1 | 0.9935 | 0.887 | yes | Remove the centered hexagonal blind recess on the top face of the tapered knob. | patch identical to the reference program; released STEP differs from that program |
| 28 | `96c09e186858d9e9` | T5 | parallel_key | A3 | 0.2505 | 0.139 | yes | Change the straight rectangular key body into a longer rounded slot-shaped body with semicircular ends, while keeping other parameters unchanged. | reference slot is not longer and not re-centred; Astra lengthens it and re-centres it |
| 29 | `ecf0700cefb8d74e` | T4 | knob | C | 0.9930 | 0.887 | no | Add a centered obround blind recess on the top face of the tapered knob, with a length of 10.00 mm, a width of 3.00 mm, and a depth of 4.34 mm. | obround recess placed with workplane() inside the chain, off the reference centre |
| 30 | `3352116bd60064e5` | T4 | bellows | D | 0.8760 | 0.808 | yes | Remove the topmost convolution of the bellows so it has four peaks instead of five; the bottom and the lower four convolutions stay the same. | top convolution removed with a different end profile than the reference |
| 31 | `401745921cc1b509` | T4 | knob | A1 | 0.9935 | 0.887 | yes | Remove the centered obround blind recess on the top face of the tapered knob. | patch identical to the reference program; released STEP differs from that program |
| 32 | `8faf5ad46eb9869e` | T1 | round_flange | E | 0.9733 | 0.877 | yes | Increase the height of the main flange body from 22.90 mm to 29.77 mm. | height changed and raised face and neck moved up to stay attached; reference leaves them in place |
| 33 | `6689506209c6d6ff` | T4 | stepped_shaft | A2 | 0.9988 | 0.998 | yes | Cut a 18×7 slot 7 deep into the top face. | instruction gives 18 x 7 x 7; reference uses 18.16 x 6.81 x 7.06 |
| 34 | `75843f475cb19d81` | T4 | mounting_angle | E | 0.9654 | 0.751 | yes | Remove the central rectangular through-cut and the vertical-edge fillet. The two mounting-hole rows on the top face are kept. | deletion span off by one workplane call; remaining hole rows inherit the 1.5 mm centre offset |
| 35 | `d4b7105feb7f1c04` | T4 | capsule | A2 | 0.9998 | 1.000 | yes | Drill a 21 diameter through-hole along the Z axis. | instruction says 21 mm; reference hole is 20.98 mm |
