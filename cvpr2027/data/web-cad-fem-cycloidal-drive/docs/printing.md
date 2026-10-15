# Printing guide

From the article, plus practical minimums.

## Settings that matter

- **Hole Horizontal Expansion ≈ 0.07 mm** — holes print small; this
  compensates bores for 6 mm pins / 13 mm / 24 mm / 47 mm bearings.
- **Horizontal Expansion ≈ 0.02 mm** — outer-dimension trim.
- Calibrate on your printer: print a small test plate with Ø6.0 / Ø13.0 /
  Ø16.0 holes and adjust until bearings are a firm press fit.
- Layer height 0.15–0.2 mm, 4–5 walls, 40–60% infill (gyroid/cubic) for
  disks, housing, flanges. 100% for pins/spacers if small.
- Material: PLA works for demo; PETG/ASA better for sustained load.
  Keep the disks cool — friction is the killer.

## Part orientation

- Disks flat on the bed (profile in XY). No supports.
- Housing base + lid flat, pin bores vertical.
- Input shaft sections with axis vertical if possible; ream/bore after print.
- Output flange flat, pin holes vertical.

## Before assembly

- Test-fit: disk should drop into the ring of 32 bearings and roll
  backwards when you push it around eccentrically by hand.
- If the mesh binds: increase Hole Horizontal Expansion slightly or apply
  a −0.05 mm XY offset to the disk profile and re-export.
- If it is sloppy: reduce expansion; backlash should be near zero.
