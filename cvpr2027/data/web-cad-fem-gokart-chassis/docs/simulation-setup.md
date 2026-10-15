# Simulation Setup and Assumptions

## Software

- ANSYS 2019 R1

## Geometry and Mass

- Chassis modeled as a continuous solid body
- Overall dimensions:
  - Length (Z): 2.28 m
  - Width (X): 1.6872 m
  - Height (Y): 0.88005 m
- Total mass: 63.953 kg

## Material Model (AISI 4130)

- Isotropic elastic material definition
- Density: 7850 kg/m³
- Young's modulus: 2.016×10¹¹ Pa
- Poisson's ratio: 0.26
- Bulk modulus: 1.4×10¹¹ Pa
- Shear modulus: 8.0×10¹⁰ Pa
- Yield strength: 460 MPa
- Ultimate strength: 560 MPa

## Meshing

- Patch conforming tetrahedral mesh
- Element type: Solid187 (10-node)
- Global element size: 0.01 m
- Local refinements at tubular joints
- Mesh count:
  - Nodes: 184,374
  - Elements: 93,476

## Solvers

1. Modal analysis with Block Lanczos eigensolver
2. Harmonic response with mode superposition (MSUP)

## Load Case

- Harmonic force: 1000 N
- Applied in Z-direction over six selected faces
- Sweep frequency: 0 to 50 Hz

## Fatigue Inputs

- Fully reversed loading, R = -1
- Fatigue strength factor (Kf): 0.65
- Load scaling factor: 1.5

## Notes

This repository preserves analyzed results and setup metadata from the original report for traceability and future redesign iterations.
