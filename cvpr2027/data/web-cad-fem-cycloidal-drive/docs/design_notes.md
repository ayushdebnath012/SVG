# Design notes — cycloidal profile math

Source: HowToMechatronics cycloidal-drive tutorial, equations originally
combined by Omar Younis (SOLIDWORKS Education blog,
"Building a Cycloidal Drive with SOLIDWORKS").

## Inputs

- `N` = number of ring-gear rollers = 16
- `R` = ring PCD radius = 45 mm
- `Rr` = roller radius = 6.5 mm (686 bearing Ø13)
- `E` = eccentricity = 1.5 mm (must satisfy `E < Rr/2 = 3.25`)

## Curve

Epitrochoid with roller-radius offset:

```text
phi(t) = atan2( sin((1−N)·t),  R/(E·N) − cos((1−N)·t) )
x(t)   = R·cos t − Rr·cos(t + phi) − E·cos(N·t)
y(t)   = −R·sin t + Rr·sin(t + phi) + E·sin(N·t)
```

- `t ∈ [0, 2π)`. Sample with ≥1000 points (2000 used here).
- In SOLIDWORKS the Equation Driven Curve refuses `t2 = 2π` exactly;
  stop slightly short and close with a spline. Here we sample
  `endpoint=False`, so the polygon closes cleanly (gap ≈ one step ≈ 0.12 mm
  at r≈38, closed by the wire).
- Disk has `N−1 = 15` lobes; verify with FFT of `r(t)` (see `--check`).

## Reduction

One input turn advances the disk by one lobe:

```text
i = N − 1 = 15   →   15:1, output reversed
```

Disk size, roller size, and `E` do **not** change the ratio.

## Output holes

Eccentric motion means a fixed output pin sweeps a circle of radius `E`
inside the disk hole, so:

```text
D_hole = D_pin_roller + 2·E  →  13 + 3 = 16 mm
```

This workspace uses 6 output pins on PCD Ø54 (`r = 27`), holes Ø16.

## Two disks, 180° apart

Balances the eccentric mass. Alignment witness holes in the original;
here disk B is the same solid rotated 180° about Z.

## Tolerances for print

Bearings are nominal; printed bores come out small. Article uses:

- Hole Horizontal Expansion ≈ +0.07 mm
- Horizontal Expansion ≈ +0.02 mm

Tune with a 13 mm / 6 mm test bore before printing the disks/housing.
A light negative profile offset (−0.05…−0.1 mm) on the disk OD can free
a tight mesh; keep backlash small.
