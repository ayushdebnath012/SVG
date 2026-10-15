# Screw Jack – 3D CAD Design & FEA Analysis

## 📌 Project Overview

This project presents the **3D CAD design and Finite Element Analysis (FEA) of a Screw Jack** developed for mechanical lifting applications.

The project covers the development of the 3D assembly, preparation of the model for simulation, mesh generation, application of structural loading and evaluation of the resulting stress, deformation and safety factor.

## 🛠️ Software Used

* **CAD:** 3D CAD modeling software
* **FEA:** ANSYS Mechanical 2026 R1
* **Analysis:** Static Structural
* **File Format:** STEP

## ⚙️ CAD Model

The Screw Jack assembly was imported into ANSYS as a STEP model.

### Model Statistics

| Parameter        |            Value |
| ---------------- | ---------------: |
| Number of Bodies |                7 |
| Mass             |         9.077 kg |
| Volume           | 1.1563 × 10⁶ mm³ |
| X Dimension      |        242.32 mm |
| Y Dimension      |        365.11 mm |
| Z Dimension      |        262.46 mm |

The model consists of components including the screw-spindle, nut, cup, washer, handle/bar and supporting components.

## 🔬 FEA Setup

A **Static Structural Analysis** was performed using ANSYS Mechanical.

### Material

**Structural Steel**

| Property                  |              Value |
| ------------------------- | -----------------: |
| Density                   | 7.85 × 10⁻⁶ kg/mm³ |
| Young's Modulus           |        200,000 MPa |
| Poisson's Ratio           |                0.3 |
| Tensile Yield Strength    |            250 MPa |
| Tensile Ultimate Strength |            460 MPa |

The material properties are taken directly from the ANSYS material definition used in the simulation.

## 🧩 Connections

The assembly contains **8 contact regions**, with the contact behavior defined as bonded and automatically detected across the model.

## 🕸️ Mesh

The model was discretized using ANSYS Mechanical's mesh system.

| Mesh Parameter       |    Value |
| -------------------- | -------: |
| Nodes                |   58,642 |
| Elements             |   33,631 |
| Mesh Sizing          |   Medium |
| Default Element Size | 25.46 mm |
| Refinement Depth     |        2 |

The generated mesh contained **58,642 nodes and 33,631 elements**.

## 🏋️ Loading & Boundary Conditions

A **1000 N ramped force** was applied in the global Y direction.

| Load        |  Value |
| ----------- | -----: |
| X Component |    0 N |
| Y Component | 1000 N |
| Z Component |    0 N |

The model was solved using a single static structural load step.

## 📊 FEA Results

### Equivalent (Von-Mises) Stress

* **Maximum:** 5.5224 MPa
* **Minimum:** 9.7897 × 10⁻¹⁵ MPa
* **Average:** 0.29123 MPa

The maximum equivalent stress was reported on the **Cup** body.

### Total Deformation

* **Maximum:** 1.4249 × 10⁻³ mm
* **Minimum:** 0 mm
* **Average:** 5.8919 × 10⁻⁴ mm

The maximum total deformation was reported on the **Cup** body.

### Safety Factor

The ANSYS Stress Tool reported a **minimum safety factor greater than 10**.

## 📋 Results Summary

| FEA Result                |             Value |
| ------------------------- | ----------------: |
| Applied Force             |            1000 N |
| Maximum Equivalent Stress |    **5.5224 MPa** |
| Maximum Total Deformation |  **0.0014249 mm** |
| Minimum Safety Factor     |           **>10** |
| Material                  |  Structural Steel |
| Analysis Type             | Static Structural |

## 🎯 Engineering Skills Demonstrated

* 3D CAD Modeling
* Mechanical Assembly Design
* STEP Model Preparation
* Finite Element Analysis
* Static Structural Analysis
* Mesh Generation
* Boundary Condition Definition
* Stress Analysis
* Deformation Analysis
* Safety Factor Evaluation
* Engineering Simulation

## 📂 Repository Contents

```text
CAD/
    → 3D CAD and STEP files

FEA/
    → ANSYS FEA report and simulation results

Drawings/
    → Engineering drawings

Images/
    → CAD model and assembly images
```

## 📄 FEA Report

The complete ANSYS Mechanical simulation report is included in the `FEA` folder.

## 👨‍💻 Author

**Gowtham D P**

Mechanical Engineering Student | CAD & FEA | Mechanical Design | Product Development
