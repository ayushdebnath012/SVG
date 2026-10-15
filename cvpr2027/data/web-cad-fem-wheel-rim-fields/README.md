# Structural and Modal Analysis of a Wheel Rim

Finite element analysis of a multi-spoke automotive wheel rim, performed in **Ansys
Mechanical**. The rim geometry was modelled in **SolidWorks**, imported via **SpaceClaim**,
and analysed under both static structural loading and free-vibration (modal) conditions.

## Contents

- **Part I — Static Structural Analysis**
  - Simplified radial load (4000 N), representing vehicle weight through the tire contact patch
  - SAE J328 cornering bending moment (2000 N·m), the industry-standard wheel fatigue qualification load
  - Comparison of stress, deformation, and safety factor between the two load cases

- **Part II — Modal Analysis**
  - Mesh convergence study
  - Free-free modal analysis (baseline / validation via rigid-body modes)
  - Constrained modal analysis (bolt-hole fixed support, representing the mounted wheel)
  - Simplified tire-loaded extension (distributed mass + radial springs)

## Key Results

| Case | Max. Stress | Max. Deformation | Safety Factor |
|---|---|---|---|
| Radial load (4000 N) | 20.9 MPa | 26.16 µm | 13.4 |
| SAE J328 bending (2000 N·m) | 131.1 MPa | 244.3 µm | 2.1 |

| Configuration | 2-ND Flange Bending | 3-ND Flange Bending |
|---|---|---|
| Free-free | 381.4 Hz | 771.8 Hz |
| Constrained (bolted) | 433.7–443.7 Hz | 780.5 Hz |
| Tire-loaded | 283.8–284.0 Hz | 613.2 Hz |

Full methodology, assumptions, mode-shape figures, and discussion are in the report.

## Repository Structure

```
.
├── Structural_and_Modal_Analysis_Wheel_Rim_Report.tex   # LaTeX source
├── Structural_and_Modal_Analysis_Wheel_Rim_Report.pdf   # Compiled report
├── images/                                              # Result plots & mode-shape figures
├── Rim.SLDPRT                                           # SolidWorks part file
├── Rim.scdocx                                           # SpaceClaim import
└── README.md
```

## Tools Used

- **SolidWorks** — CAD geometry
- **Ansys SpaceClaim 2026 R1** — geometry cleanup / import
- **Ansys Mechanical (Student)** — static structural & modal (Block Lanczos) solvers

## Building the Report

```bash
pdflatex Structural_and_Modal_Analysis_Wheel_Rim_Report.tex
pdflatex Structural_and_Modal_Analysis_Wheel_Rim_Report.tex   # second pass for TOC/refs
```

## Notes & Limitations

- Loads are applied as remote loads at a single point rather than distributed over a
  realistic tire contact patch.
- The SAE J328 case is a static snapshot of a rotating fatigue test, not a full
  cyclic fatigue-life simulation.
- The tire model (distributed mass + 4 discrete radial springs) is a first-order
  lumped approximation, not a full 3-D tire model with contact.
- Mesh limited to the practical size cap of the Ansys Student license
  (final converged mesh: 0.0115 m element size, 116,074 nodes).

See the report's **Modelling Assumptions and Limitations** sections for full details.

## Author

Ranit Das

M.Tech - Solid Mechanics and Design

IIT Kanpur
