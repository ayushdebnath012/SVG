# Engineering Simulation and Model Evaluation (ANSYS)

This repository contains structured ANSYS Workbench studies focusing on finite element modeling, mesh evaluation, and engineering interpretation of simulation results.

The projects emphasize:
- Mesh sensitivity and convergence behavior
- Model dimensionality comparison (1D / 2D shell / 3D solid)
- Contact modeling and bolt pretension
- Thermal and structural simulation
- Quantitative evaluation of stress, deformation, and temperature fields

---

## Key Skills Demonstrated

- Finite Element Modeling in ANSYS Workbench
- Mesh refinement and convergence assessment
- Frictional contact modeling (μ-based contact definition)
- Multi-step loading with bolt pretension
- Interpretation of von Mises stress, total deformation, and temperature distributions
- Structured simulation reporting and result validation

---

## Project 1 — Composite Rod Thermal Analysis

**Focus:** 1D vs 3D model comparison and convection parameter study

Report:  
`reports/composite_rod_thermal_analysis_report.pdf`

Workbench archive:  
`workbench_archives/composite_rod_thermal_analysis.wbpz`

### Highlights
- Composite rod consisting of multiple material segments
- Compared temperature distributions between 1D and full 3D models
- Investigated influence of convection coefficient α on interface temperatures
- Evaluated agreement and deviation between reduced and full models

---

## Project 2 — Mesh Sensitivity Study (1D vs 2D vs 3D)

**Focus:** Influence of element size on deformation, stress, and runtime

Report:  
`reports/mesh_sensitivity_study_report.pdf`

Workbench archives:  
- `workbench_archives/mesh_sensitivity_study_1d_2d_3d_full.wbpz`  
- `workbench_archives/mesh_sensitivity_study_1d_2d_3d_low_res.wbpz`

### Highlights
- Investigated convergence behavior for different model dimensionalities
- Evaluated:
  - Maximum total deformation
  - Maximum von Mises stress
  - Computational time
- Compared convergence thresholds across 1D, 2D (shell), and 3D (solid) models
- Identified and analyzed anomalous design points in 2D simulations

---

## Project 3 — Bolted Shelf Support Assembly

**Focus:** Pretensioned bolts with frictional contact under external loading

Report:  
`reports/bolted_shelf_support_pretension_contact_report.pdf`

Workbench archive:  
`workbench_archives/bolted_shelf_support_pretension_contact.wbpz`

### Highlights
- Two-step simulation:
  1. Bolt pretension (locked)
  2. Application of external load (~500 N)
- Frictional contacts with defined coefficient (μ = 0.15)
- Evaluated maximum bolt stress and estimated safety factor relative to yield strength
- Identified critical stress regions and structural load paths

---

## Repository Structure

    ansys-simulation-model-evaluation/
    ├── reports/              (PDF reports)
    ├── workbench_archives/   (ANSYS Workbench *.wbpz archives)
    ├── assets/               (optional figures for documentation)
    ├── README.md
    └── .gitignore

---

## Notes

- Workbench archives are provided for reproducibility.
- Some results may be simplified to meet repository size constraints.
- The emphasis of this repository is on simulation setup quality, evaluation methodology, and engineering interpretation rather than purely graphical output.