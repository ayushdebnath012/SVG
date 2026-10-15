# Cycloidal Drive — DIY 3D-Printed 15:1 Reducer

Rebuild of the project from HowToMechatronics:
**"What is Cycloidal Drive? Designing, 3D Printing and Testing"**
<https://howtomechatronics.com/how-it-works/what-is-cycloidal-driver-designing-3d-printing-and-testing/>

A compact single-stage cycloidal speed reducer with ~15:1 reduction,
virtually zero backlash, designed for 3D printing with off-the-shelf
ball bearings instead of plain bushings.

> Original design tool: SOLIDWORKS (Equation Driven Curve).
> This workspace reproduces the same math parametrically in
> Python + FreeCAD so it can be rebuilt, tweaked, and exported to STL
> without SOLIDWORKS.

## How it works (30-second version)

- Input shaft → eccentric cam (`E = 1.5 mm`) → wobbles two cycloidal disks
  around the inside of a fixed ring gear.
- Ring gear has `N = 16` rollers (686 bearings, Ø13 mm) on a Ø90 mm PCD.
- Each disk has `N-1 = 15` lobes. One full input turn advances the disk by
  exactly one lobe → reduction `i = N-1 = 15:1`, output reversed.
- Two disks mounted 180° out of phase cancel imbalance.
- Output pins through oversized holes in the disks pick up the slow rotation.
  Hole Ø = roller Ø + 2·E.

## Key parameters (from the tutorial)

| Symbol | Meaning | Value |
|---|---|---|
| `N` | ring-gear rollers | 16 |
| `R` | ring PCD radius | 45 mm (Ø90) |
| `Rr` | ring roller radius | 6.5 mm (Ø13, 686 bearing) |
| `E` | eccentricity | 1.5 mm |
| `i` | reduction | `N-1 = 15:1` |
| Disk lobes | `N-1` | 15 |

Profile equations (epitrochoid, from Omar Younis / SOLIDWORKS blog,
as quoted in the article):

```text
x = R·cos(t) − Rr·cos(t + atan2(sin((1−N)·t), R/(E·N) − cos((1−N)·t))) − E·cos(N·t)
y = −R·sin(t) + Rr·sin(t + atan2(sin((1−N)·t), R/(E·N) − cos((1−N)·t))) + E·sin(N·t)
t ∈ [0, 2π)
```

Same equations are implemented in `cad/cycloidal_profile.py` and
`cad/freecad_build.py`.

## Workspace layout

```text
.
├── README.md               ← you are here
├── parameters.json         ← single source of truth for N, R, Rr, E + derived dims
├── cad/
│   ├── cycloidal_profile.py  ← numpy profile generator → CSV / DXF / SVG (no CAD dep)
│   ├── freecad_build.py      ← parametric FreeCAD build → FCStd + STLs
│   └── CycloidalDrive.FCStd  ← generated model (after build)
├── models/                 ← exported STLs for slicing (after build)
├── docs/
│   ├── design_notes.md
│   ├── BOM.md
│   ├── printing.md
│   ├── assembly.md
│   └── testing.md
├── electronics/
│   └── nema17_test.ino     ← stepper spin + ratio check sketch
└── slicer/
    └── README.md           ← hole-expansion + print settings from article
```

## Quickstart

1. **Check the math / preview the profile** (only needs Python3 + numpy + matplotlib):

```bash
cd "/home/jagath-srujan/Documents/cyclodial gearbox"
python3 cad/cycloidal_profile.py --plot --export-dxf
```

Outputs: `models/cycloidal_disk_profile.csv`, `.dxf`, `.svg`, `.png`.

2. **Build the 3D model** (via FreeCAD MCP, already configured):

The script `cad/freecad_build.py` is executed inside FreeCAD through the
agent / MCP `execute_code`. It creates `cad/CycloidalDrive.FCStd` and exports
one STL per solid into `models/`.

3. **Slice & print** — see `docs/printing.md` and `slicer/README.md`.
   Critical: `Hole Horizontal Expansion ≈ 0.07 mm`,
   `Horizontal Expansion ≈ 0.02 mm` (tune on your printer).

4. **Assemble** — see `docs/assembly.md` + `docs/BOM.md`.

5. **Test with NEMA 17** — see `docs/testing.md` + `electronics/nema17_test.ino`.
   Expected: output = input/15, reversed. Article measured ~10× torque
   gain (≈66% efficiency) on a budget printer.

## Source & credit

- Design, equations, BOM quantities: Dejan / HowToMechatronics (link above).
- Epitrochoid equations: Omar Younis, SOLIDWORKS Education blog
  (`Building a Cycloidal Drive with SOLIDWORKS` PDF).
- STEP/STL of the original: Thangs `m/40878`, STL pack on the article page.
- This repo is a clean-room parametric re-implementation for FreeCAD +
  Python; it does not redistribute the original STL/STEP.
