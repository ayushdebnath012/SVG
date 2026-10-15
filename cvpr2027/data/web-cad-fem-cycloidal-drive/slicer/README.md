# Slicer notes

- Printer used in the article: budget FDM, PLA.
- **Hole Horizontal Expansion: 0.07 mm** (Cura). This is the single most
  important setting — without it the 6/13/24/47 mm bores seize.
- **Horizontal Expansion: 0.02 mm.**
- Print a calibration coupon first (Ø6 / Ø13 / Ø16 / Ø24 holes), measure
  with calipers, then adjust.
- PrusaSlicer/Orca equivalent: `XY hole compensation` / `hole clearance`.
  Start at +0.07 mm hole / +0.02 mm contour and iterate.
- 0.15–0.2 mm layers, 4–5 perimeters, 40–60% infill for structural parts.
