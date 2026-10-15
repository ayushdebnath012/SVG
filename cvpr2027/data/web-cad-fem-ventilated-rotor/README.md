# Disc-Brake-Rotor-FEA-ANSYS-Workbench

**Project type:** Finite Element Analysis (FEA) | **Tools:** ANSYS Workbench 2025 R2

---

## Overview

This repository documents a professional, reproducible Finite Element Analysis of a ventilated disc brake rotor carried out in **ANSYS Workbench**. The study couples a **steady‑state thermal** simulation and a **static structural** analysis to evaluate temperature distribution, thermo‑mechanical stresses, and total deformation under representative braking conditions.

All images referenced below are saved in the repository (temperature, von‑Mises stress, and total deformation contours). A formal summary report is included as `Report.pdf`.

---

## Highlights (Key results)

* **Maximum steady‑state temperature:** 100.0 °C.
* **Maximum equivalent (von‑Mises) stress:** 621.02 MPa.
* **Maximum total deformation:** 0.067061 mm (6.7061e-02 mm).
* **Mesh:** 39,030 nodes, 21,095 elements.

> See the full ANSYS report in `Report.pdf`.

---

## Purpose & Objective

* Assess thermal and structural performance of a ventilated disc rotor during braking.
* Identify critical hot spots and high stress regions to inform design recommendations (fillet radii, ventilation geometry, material choice).
* Demonstrate reproducible simulation setup and reporting suitable for inclusion in portfolios or GitHub.

---

## Repository Structure

```
Disc-Brake-FEA-ANSYS/
├── README.md
├── Report.pdf                
├── mesh_overview.png
├── temp.png
├── equivalent stress.png
├── total def.png
├── dick break.IGS            
```

---

## Model & Simulation Setup (concise)

**Geometry & import**: Rotor imported as IGES/STEP and modelled as a single solid body (ventilated rotor geometry).
**Material:** Structural Steel (as assigned in the model).
**Meshing:** Tetrahedral mesh with local refinement at friction surfaces and vane regions; total nodes/elements as noted above.

**Thermal analysis**

* Type: Steady‑state thermal.
* Initial/ambient temperature: 22 °C.
* Thermal loads: Heat flux and mapped convection (film coefficient tabular data used); results mapped to structural analysis as imported body temperature.

**Structural analysis**

* Type: Static structural (mechanical).
* Mechanical loads: Distributed pressure (imported as a 0.5 MPa pressure on selected pad contact faces) and rotation field (ramped to 100 rad/s).
* Thermal‑structural coupling: Temperature field from thermal analysis was imported and applied as a body temperature in the structural run.

---

## Results (what to look for)

* **Temperature:** Contour plot (`temp.png`) shows a peak of 100 °C concentrated near the frictional contact region.
* **Equivalent stress:** von‑Mises stress contour (`equivalent stress.png`) indicates a peak of 621.02 MPa at geometrically stressed locations (fillets, hub/spoke junctions).
* **Deformation:** Total deformation plot (`total def.png`) shows a maximum displacement of 0.067061 mm.

Interpretation and engineering guidance are provided in the full report and the README’s Results section (mesh sensitivity recommendation, factor of safety check, and suggested design changes).

---

## How to reproduce (high‑level steps)

1. Import the rotor geometry into ANSYS Workbench (Geometry → External Model).
2. Define material properties (Structural Steel or chosen material).
3. Create mesh with local refinement near contact surfaces and vanes.
4. Run **Steady‑State Thermal**: apply heat flux/convection and record temperature field.
5. Link thermal solution to **Static Structural**: import body temperature, apply mechanical pressure/constraints and rotational velocity, and solve.
6. Export contour images for temperature, von‑Mises stress, and total deformation.

---

## Interpretation & Recommendations

* The peak von‑Mises stress (621.02 MPa) exceeds typical yield/tensile strengths of many common rotor materials; verify if structural steel properties used here match the intended manufacturing material and compute Factor of Safety (FoS) accordingly.
* Perform mesh convergence and transient thermal analysis for a more realistic braking pulse (steady‑state underestimates short‑duration peak temperatures).
* If stresses remain high after verification, consider geometric modifications (increasing fillet radii, web thickness), improved ventilation design, or higher‑strength materials.

---

## Notes & Limitations

* The current study uses a steady‑state thermal solution and linear static structural analysis. Real braking events are transient and may require coupled transient thermo‑mechanical simulations with frictional contact for highest fidelity.
* Replace assumed material or load values with test‑measured or design‑specified inputs before publication or design change.

---

## References & Credits

* ANSYS Workbench 2025 R2 — model and automated report generation.
* Full model report: `Report.pdf` (ANSYS generated).

---

## Contact

For questions or to request editable simulation files, contact: **Kanishk L.** (update contact details as preferred).

*Prepared for publication on GitHub — review `Report.pdf` for solver logs and full solution tables before sharing externally.*
