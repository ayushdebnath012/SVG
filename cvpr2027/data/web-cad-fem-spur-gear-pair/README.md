# Spur Gear Static Structural FEA

## Overview

This project presents the **static structural finite element analysis (FEA)** of a two-gear spur gear mechanism. The gear pair was modeled in **SolidWorks** and analyzed using **ANSYS Workbench 2026 R1 – Static Structural**.

The analysis focuses on evaluating the structural response of the gear assembly under the applied loading condition and identifying the critical region of the gear mesh.

## Software Used

* **SolidWorks** – CAD modeling of the spur gear pair
* **ANSYS Workbench 2026 R1** – Finite Element Analysis
* **Static Structural Analysis**
* **STEP (AP214)** – CAD geometry transfer format

## Analysis Parameters

The model consists of a smaller **pinion gear** meshed with a larger **driven gear**. The larger gear was constrained to represent its support condition, while loading/rotation was applied through the smaller gear to establish the meshing condition.

The following results were evaluated:

1. Total Deformation
2. Equivalent Elastic Strain
3. Equivalent (von-Mises) Stress

## Results

| Result                        |                   Maximum Value | Location             |
| ----------------------------- | ------------------------------: | -------------------- |
| Total Deformation             |             **6.1668 × 10⁻⁶ m** | Pinion tooth tip     |
| Equivalent Elastic Strain     |           **7.8558 × 10⁻⁵ m/m** | Tooth contact region |
| Equivalent (von-Mises) Stress | **1.2379 × 10⁷ Pa (≈12.4 MPa)** | Tooth contact region |

The maximum deformation occurs at the outer tooth tip of the pinion, while the maximum strain and von-Mises stress are concentrated at the tooth-to-tooth contact region.

## Key Findings

* The **pinion gear** experiences greater deformation than the larger driven gear.
* The **gear tooth contact region** is the critical structural location.
* Stress and strain are highly localized around the gear mesh.
* The maximum von-Mises stress obtained is approximately **12.4 MPa**.
* Under the analyzed loading condition, the predicted stress is below the typical yield-strength range stated in the report for common structural/alloy steels.

## Conclusion

The FEA successfully demonstrates the structural behavior of the spur gear pair under static loading. The results indicate that the tooth contact region is the most critical area, with maximum stress and strain occurring at the gear mesh, while the maximum deformation occurs at the pinion tooth tip.

## Project Files

* `Spur_Gear_FEA_Report.pdf` – FEA report and results
* `STEP/CAD files` – Gear geometry
* `ANSYS Workbench files` – Simulation setup and analysis
* `README.md` – Project documentation
# Spur-Gear-Mechanism-Stress-Analysis
Static structural FEA of a spur gear pair using SolidWorks and ANSYS Workbench, evaluating deformation, strain, and von-Mises stress.
