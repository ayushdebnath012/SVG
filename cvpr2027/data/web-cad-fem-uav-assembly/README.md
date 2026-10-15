# UAV Frame Structural Analysis — ANSYS Static Structural

> **Finite Element Analysis (FEA) of a carbon-fiber UAV frame and its mechanical hardware under distributed motor-thrust loading using ANSYS Mechanical.**

[![ANSYS](https://img.shields.io/badge/ANSYS-Mechanical-red?style=for-the-badge)](https://www.ansys.com/)
[![FEA](https://img.shields.io/badge/Analysis-Static%20Structural-blue?style=for-the-badge)](https://www.ansys.com/products/structures/ansys-mechanical)
[![UAV](https://img.shields.io/badge/Domain-UAV%20Structures-black?style=for-the-badge)](https://en.wikipedia.org/wiki/Unmanned_aerial_vehicle)
[![Status](https://img.shields.io/badge/Status-Solved-success?style=for-the-badge)](#results)

## Project Overview

This repository documents a **3D static structural finite-element analysis of a UAV airframe** developed and solved in **ANSYS Mechanical 2025 R1**.

The model represents a mechanically assembled UAV frame containing:

- Carbon-fiber top and bottom structural plates
- Carbon-fiber composite rods/tubes forming the arms
- ABS motor/structural brackets and printed components
- Steel fasteners and mechanical hardware
- Multiple bonded contact regions between interacting components

The objective is to evaluate how the airframe responds to a simplified propulsion loading case and to identify the locations of high deformation, elastic strain, strain energy, and principal stress.

The analysis is intentionally documented as an engineering FEA study rather than only as a visual simulation. The repository therefore includes the **CAD/FEA project, neutral CAD geometry, exported ANSYS report, mesh image, and post-processing result images**.

---

## Key Results

| Quantity | Result |
|---|---:|
| Analysis type | Static Structural |
| Solver target | Mechanical APDL |
| Model bodies | 62 |
| Total mesh nodes | **545,580** |
| Total mesh elements | **266,057** |
| Contact regions | **132** |
| Applied thrust loads | **4 × 10 N** |
| Total applied force | **40 N** |
| Maximum equivalent elastic strain | **4.5572 × 10⁻³ m/m** |
| Maximum total deformation | **2.3987 mm** |
| Maximum local strain-energy result | **2.1677 × 10⁻⁴ J** |
| Total strain energy | **3.9066 × 10⁻² J** |
| Maximum principal stress | **342.76 MPa** |
| Minimum principal stress | **−56.36 MPa** |
| Average principal stress | **0.970 MPa** |
| Solution status | **Solved** |
| MAPDL elapsed time | **5 min 30 s** |
| MAPDL memory used | **7.2363 GB** |
| Result file size | **205.44 MB** |

> **Important:** The values above describe the **current solved model recorded in `report.mht`**. The archived ANSYS report records **10 N on each of the four force loads**, giving a total applied load of 40 N.

---

## Engineering Objective

The primary engineering question is:

> **Can the UAV frame and its mechanical load path withstand the structural effects produced by four motor thrust loads without excessive deformation or critical stress concentrations?**

The analysis focuses on:

1. Structural stiffness of the carbon-fiber frame
2. Load transfer from motor locations into the arms and central plates
3. Interaction between carbon-fiber members, ABS components, and fasteners
4. Identification of high-strain regions
5. Identification of high principal-stress regions
6. Global deformation of the airframe
7. Stored elastic strain energy
8. Suitability of the current geometry as a baseline for further structural optimization

---

# 1. Model Architecture

The FEA model contains **62 active bodies**.

The structural assembly includes:

### Carbon-fiber structural members

- `TOP-PLATE-X500-V5`
- `BOTTOM-PLATE-X500-V5`
- Carbon-fiber arm/rod components represented by the material **`rod`**

### Polymer components

- Motor brackets
- Structural/mounting components
- ABS components assigned to **`Plastic, ABS (high-impact)`**

### Metallic hardware

The model contains multiple steel hardware bodies, including component names such as:

- `GB70-M3-38`
- `GB70-M25-10`
- `ZSLM-M3-FALAN`

and other mechanical mounting components.

The fasteners and hardware are therefore retained in the structural model instead of treating the frame as an isolated carbon-fiber-only structure.

---

# 2. Geometry

The imported model was created as a **3D DesignModeler geometry** and transferred into ANSYS Mechanical.

### Overall model statistics

| Parameter | Value |
|---|---:|
| Analysis geometry | 3D |
| Length X | 0.40035 m |
| Length Y | 0.0407 m |
| Length Z | 0.40035 m |
| Bounding-box volume | 1.9454 × 10⁻⁴ m³ |
| Model mass | 0.29218 kg |
| Number of bodies | 62 |
| Active bodies | 62 |

The model was imported with:

- Named selections enabled
- Material properties retained
- Coordinate systems retained
- CAD associativity enabled
- Instance handling enabled
- Smart CAD update enabled
- Disjoint geometry decomposition enabled
- 3D structural analysis configuration

---

# 3. Material Definition

The simulation uses four engineering-material definitions:

1. `sheet`
2. `Structural Steel`
3. `Plastic, ABS (high-impact)`
4. `rod`

The carbon-fiber sheet and rod are modeled using **orthotropic elasticity**, while ABS and steel are modeled as **isotropic elastic materials**.

> **Material-data note:** The carbon-fiber elastic constants are engineering input values used for the FEA model. They should be replaced by manufacturer/test-characterized laminate properties when performing a certification-grade analysis.

---

## 3.1 Carbon-Fiber Sheet — `sheet`

### Density

**1550 kg/m³**

### Orthotropic elastic properties

| Property | Value |
|---|---:|
| Young's modulus X | 70 GPa |
| Young's modulus Y | 70 GPa |
| Young's modulus Z | 8 GPa |
| Poisson's ratio XY | 0.06 |
| Poisson's ratio YZ | 0.30 |
| Poisson's ratio XZ | 0.30 |
| Shear modulus XY | 4.5 GPa |
| Shear modulus YZ | 3.0 GPa |
| Shear modulus XZ | 3.0 GPa |

This represents the carbon-fiber plate as an **orthotropic composite material**, rather than incorrectly treating the laminate as an isotropic metal.

---

## 3.2 Carbon-Fiber Rod — `rod`

### Density

**1500 kg/m³**

### Orthotropic elastic properties

| Property | Value |
|---|---:|
| Young's modulus X | 100 GPa |
| Young's modulus Y | 10 GPa |
| Young's modulus Z | 10 GPa |
| Poisson's ratio XY | 0.30 |
| Poisson's ratio YZ | 0.40 |
| Poisson's ratio XZ | 0.30 |
| Shear modulus XY | 5.0 GPa |
| Shear modulus YZ | 3.5 GPa |
| Shear modulus XZ | 3.5 GPa |

For the arm/tube model, the principal material direction should correspond to the **longitudinal axis of the carbon-fiber rod**.

---

## 3.3 ABS — `Plastic, ABS (high-impact)`

| Property | Value |
|---|---:|
| Density | 1030 kg/m³ |
| Young's modulus | 2.09 GPa |
| Poisson's ratio | 0.4089 |
| Tensile yield strength | 27.44 MPa |
| Tensile ultimate strength | 36.26 MPa |
| Reference temperature | 23 °C |
| Thermal expansion coefficient | 1.84 × 10⁻⁴ °C⁻¹ |
| Thermal conductivity | 0.1997 W/m·°C |
| Specific heat | 1400 J/kg·°C |

The ABS components are modeled as isotropic elastic material.

---

## 3.4 Structural Steel

| Property | Value |
|---|---:|
| Density | 7850 kg/m³ |
| Young's modulus | 200 GPa |
| Poisson's ratio | 0.30 |
| Tensile yield strength | 250 MPa |
| Compressive yield strength | 250 MPa |
| Tensile ultimate strength | 460 MPa |
| Thermal expansion coefficient | 1.2 × 10⁻⁵ °C⁻¹ |
| Thermal conductivity | 60.5 W/m·°C |
| Specific heat | 434 J/kg·°C |

Steel is used for the metallic fasteners/hardware represented in the model.

---

# 4. Coordinate System and Units

The analysis uses:

**Metric — m, kg, N, s, V, A**

Additional settings:

- Angle: Degrees
- Rotational velocity: rad/s
- Temperature: Celsius
- Solver unit system: mks
- Global Cartesian coordinate system
- Global origin: `(0, 0, 0)`

The analysis environment temperature is **22 °C**.

---

# 5. Contact Modeling

The model contains a substantial number of mechanical interfaces.

### Contact statistics

| Parameter | Value |
|---|---:|
| Total contacts | 132 |
| Active contacts | 132 |
| Joints | 0 |
| Beams | 0 |
| Bearings | 0 |
| Springs | 0 |
| Body interactions | 0 |

The automatically generated contact regions are predominantly configured as:

**Bonded contacts**

with:

- Automatic scoping
- Program-controlled behavior
- Program-controlled formulation
- Program-controlled detection
- Program-controlled normal stiffness
- Program-controlled pinball region
- Automatic contact trimming

### Contact tolerance

**1.4191 × 10⁻³ m**

or approximately **1.419 mm**.

The bonded-contact strategy represents the assembled frame as mechanically connected at the modeled interfaces.

> For a future high-fidelity joint study, the interfaces could be upgraded to frictional contact, bolt pretension, bolt connectors, or experimentally characterized joint stiffness.

---

# 6. Meshing

The model uses a 3D finite-element mesh generated in ANSYS Mechanical.

### Mesh statistics

| Parameter | Value |
|---|---:|
| Nodes | **545,580** |
| Elements | **266,057** |
| Element order | Program Controlled |
| Physics preference | Mechanical |
| Adaptive sizing | Enabled |
| Resolution | Default (2) |
| Mesh defeaturing | Enabled |
| Transition | Fast |
| Span angle center | Coarse |
| Initial size seed | Assembly |
| Minimum edge length | 1.5687 × 10⁻⁵ m |
| Smoothing | Medium |
| Automatic inflation | None |
| Sheet-body method | Quad Dominant |
| Sweepable-body method | Sweep |
| Topology checking | Enabled |

### Mesh quality

The ANSYS report records:

**Check Mesh Quality: Yes, Errors**

with:

**Error Limits: Aggressive Mechanical**

This is an important engineering limitation of the current result. A converged solver solution does **not automatically mean the mesh is fully mesh-independent**.

The current model should therefore be treated as a **high-detail baseline FEA**, with further mesh-quality inspection and convergence study recommended before making final structural design decisions.

---

## Mesh Visualization

![Finite Element Mesh](<mesh.jpg>)

**Figure — `mesh.jpg`**  
Global finite-element mesh of the UAV frame and hardware.

---

# 7. Boundary Conditions and Loading

The model uses a simplified static representation of motor thrust.

### Applied loads

Four force objects are defined:

- `Force`
- `Force 2`
- `Force 3`
- `Force 4`

Each load is recorded in the ANSYS report as:

**10 N**

Therefore:

\[
F_\text{total}=4(10)=40\text{ N}
\]

The four loads represent the upward thrust reactions generated at the four motor locations.

### Constraint

A **Fixed Support** is applied to:

**1 edge**

This provides the structural restraint required for the static structural solution.

> This boundary condition is a simplified structural test condition. It is not a complete free-flight dynamic model. A higher-fidelity UAV analysis would represent gravity, thrust distribution, motor mounting stiffness, inertia, and the actual fuselage/support constraints explicitly.

---

# 8. Analysis Settings

The study is configured as:

**Static Structural**

using:

**Mechanical APDL**

### Analysis configuration

| Parameter | Setting |
|---|---|
| Analysis type | Static Structural |
| Physics | Structural |
| Solver target | Mechanical APDL |
| Number of steps | 1 |
| Step end time | 1 s |
| Auto time stepping | Program Controlled |
| Weak springs | Off |
| Large deflection | Off |
| Inertia relief | Off |
| Quasi-static solution | Off |
| Solver type | Program Controlled |
| Environment temperature | 22 °C |
| Solver units | mks |

### Output controls

The solution requests:

- Stress
- Strain
- Contact data
- Volume and energy
- Euler angles
- All time points

---

# 9. Solver Performance

The model successfully completed the ANSYS solution.

| Solver metric | Result |
|---|---:|
| Solution status | **Done / Solved** |
| MAPDL elapsed time | **5 min 30 s** |
| MAPDL memory used | **7.2363 GB** |
| Result file size | **205.44 MB** |
| Newton-Raphson residuals | **0** |
| Element violations identified | **0** |
| Load step | 1 |
| Substep | 1 |
| Iteration | 1 |

The report therefore indicates a completed numerical solution with zero reported Newton-Raphson residuals and zero identified element violations.

---

# 10. Post-Processing Results

The following result quantities were evaluated over **all bodies**:

- Equivalent Elastic Strain
- Total Deformation
- Strain Energy
- Maximum Principal Stress

All results are evaluated at the final solution time.

---

## 10.1 Equivalent Elastic Strain

### Result

| Quantity | Value |
|---|---:|
| Minimum | 2.6564 × 10⁻¹⁴ m/m |
| Maximum | **4.5572 × 10⁻³ m/m** |
| Average | 7.5525 × 10⁻⁵ m/m |
| Maximum percentage strain | **0.45572 %** |
| Maximum location/body | `GB70-M3-38` |

![Equivalent Elastic Strain](<equivalent elastic strain.jpg>)

**Figure — `equivalent elastic strain.jpg`**  
Equivalent elastic strain distribution across the UAV assembly.

The result identifies the metallic `GB70-M3-38` component as the location of the maximum reported equivalent elastic strain.

---

## 10.2 Total Deformation

### Result

| Quantity | Value |
|---|---:|
| Minimum | 0 m |
| Maximum | **2.3987 × 10⁻³ m** |
| Maximum | **2.3987 mm** |
| Average | 6.8332 × 10⁻⁴ m |
| Maximum location/body | `BAN-DJ-DIAN-F2` |

![Total Deformation](<total deformation.jpg>)

**Figure — `total deformation.jpg`**  
Total displacement distribution of the UAV frame under the applied loading condition.

The maximum deformation is approximately **2.40 mm**.

---

## 10.3 Strain Energy

### Result

| Quantity | Value |
|---|---:|
| Minimum | 4.4479 × 10⁻²⁸ J |
| Maximum local value | 2.1677 × 10⁻⁴ J |
| Total strain energy | **3.9066 × 10⁻² J** |
| Total | **39.066 mJ** |
| Maximum location/body | `BOTTOM-PLATE-X500-V5` |

![Strain Energy](<strain energy.jpg>)

**Figure — `strain energy.jpg`**  
Strain-energy distribution through the structural assembly.

The total stored elastic strain energy provides an additional global measure of structural compliance under the applied load case.

---

## 10.4 Maximum Principal Stress

### Result

| Quantity | Value |
|---|---:|
| Minimum | **−5.6362 × 10⁷ Pa** |
| Minimum | **−56.36 MPa** |
| Maximum | **3.4276 × 10⁸ Pa** |
| Maximum | **342.76 MPa** |
| Average | 9.7042 × 10⁵ Pa |
| Maximum location/body | `GB70-M3-38` |

![Maximum Principal Stress](<max principle stress.jpg>)

**Figure — `max principle stress.jpg`**  
Maximum principal stress distribution across the UAV structure.

### Engineering interpretation

The maximum reported principal stress is approximately **342.76 MPa**.

The current model assigns a nominal structural-steel tensile yield strength of **250 MPa**. The reported peak is therefore approximately:

\[
\frac{342.76}{250}\approx1.37
\]

or **37% above the nominal yield value**.

This should **not immediately be interpreted as global structural failure** because the peak may be influenced by:

- local geometric discontinuities,
- fastener-hole stress concentration,
- contact formulation,
- sharp edges,
- mesh density,
- bonded interfaces,
- idealized material properties,
- linear-elastic extrapolation beyond yield.

Instead, it identifies `GB70-M3-38` as a **critical region requiring local mesh refinement, geometry inspection, and joint-level validation**.

---

# 11. Result Gallery

### ANSYS Model / Setup Screenshots

The repository contains four additional screenshots documenting the model/setup state.

#### `Screenshot 2026-09-10 215945.jpg`

![ANSYS Screenshot 1](<Screenshot 2026-09-10 215945.jpg>)

#### `Screenshot 2026-09-10 220038.jpg`

![ANSYS Screenshot 2](<Screenshot 2026-09-10 220038.jpg>)

#### `Screenshot 2026-09-10 220115.jpg`

![ANSYS Screenshot 3](<Screenshot 2026-09-10 220115.jpg>)

#### `Screenshot 2026-09-10 220149.jpg`

![ANSYS Screenshot 4](<Screenshot 2026-09-10 220149.jpg>)

These screenshots are retained as visual evidence of the modeling, setup, and/or post-processing workflow.

---

# 12. Complete Result Set

| Result image | Quantity |
|---|---|
| `equivalent elastic strain.jpg` | Equivalent Elastic Strain |
| `total deformation.jpg` | Total Deformation |
| `strain energy.jpg` | Strain Energy |
| `max principle stress.jpg` | Maximum Principal Stress |
| `mesh.jpg` | Finite Element Mesh |

All result images are retained in the repository for direct inspection.

---

# 13. Engineering Workflow

The project follows the standard structural FEA workflow:

```text
CAD Geometry
     │
     ▼
Geometry Import
     │
     ▼
Material Definition
     │
     ▼
Component / Hardware Assignment
     │
     ▼
Contact Generation
     │
     ▼
Finite Element Meshing
     │
     ▼
Boundary Conditions
     │
     ▼
Four Motor-Thrust Loads
     │
     ▼
Static Structural Solution
     │
     ▼
Stress / Strain / Deformation
     │
     ▼
Engineering Interpretation
     │
     ▼
Design Refinement
```

---

# 14. Files in This Repository

| File | Purpose |
|---|---|
| `drone.wbpj` | ANSYS Workbench project |
| `report.mht` | Exported ANSYS Mechanical report |
| `x-500 frame ADDC ansys.step` | Neutral CAD geometry |
| `mesh.jpg` | Mesh visualization |
| `equivalent elastic strain.jpg` | Equivalent elastic strain result |
| `total deformation.jpg` | Total deformation result |
| `strain energy.jpg` | Strain-energy result |
| `max principle stress.jpg` | Maximum principal stress result |
| `Screenshot 2026-09-10 215945.jpg` | ANSYS project/setup screenshot |
| `Screenshot 2026-09-10 220038.jpg` | ANSYS project/setup screenshot |
| `Screenshot 2026-09-10 220115.jpg` | ANSYS project/setup screenshot |
| `Screenshot 2026-09-10 220149.jpg` | ANSYS project/setup screenshot |

---

# 15. How to Open the Project

## ANSYS Workbench

1. Install a compatible ANSYS release.
2. Open `drone.wbpj` using ANSYS Workbench.
3. Open the **Static Structural** system.
4. Review:
   - Geometry
   - Materials
   - Connections
   - Mesh
   - Analysis Settings
   - Loads
   - Solution
5. Regenerate the mesh if required.
6. Re-solve before using the model for any modified geometry or loading condition.

The exported `report.mht` can be opened independently as an HTML/MIME report for reviewing the recorded analysis settings and results.

The STEP file can be opened in compatible CAD software or re-imported into ANSYS/other CAE software.

---

# 16. Engineering Limitations

This project is a **simulation and engineering study**, not a certification analysis.

Important limitations include:

### 1. Material characterization

The carbon-fiber model uses orthotropic engineering constants. Actual stiffness and strength depend strongly on:

- fiber architecture,
- resin system,
- fiber volume fraction,
- laminate stacking sequence,
- manufacturing process,
- fiber orientation,
- defects,
- joints and bonded interfaces.

For a production-level analysis, manufacturer-certified or coupon-test data should be used.

### 2. Linear elastic material modeling

The current structural analysis is fundamentally linear-elastic in its material representation.

The model therefore does not fully capture:

- plasticity,
- progressive composite failure,
- delamination,
- matrix cracking,
- fiber failure,
- post-yield behavior,
- damage accumulation.

### 3. Composite failure criteria

The current results include equivalent elastic strain and maximum principal stress. These are useful for screening and debugging but are **not sufficient for a final composite failure assessment**.

A higher-fidelity composite study should use criteria such as:

- Tsai-Hill
- Tsai-Wu
- Hashin
- Puck
- LaRC-type criteria

and should ideally use laminate-level modeling or ANSYS ACP where appropriate.

### 4. Mesh convergence

The current mesh contains **545,580 nodes and 266,057 elements**, and the report records mesh-quality errors.

A formal mesh-convergence study is therefore required before using the peak stress as a final design value.

### 5. Fastener modeling

The model contains detailed mechanical hardware and many bonded contacts, but it does not represent every possible real-world fastener behavior such as:

- bolt preload,
- thread contact,
- friction,
- slip,
- bearing clearance,
- washer compliance.

A dedicated bolted-joint study would provide higher fidelity.

### 6. Flight dynamics

This is a static structural analysis.

It does not model:

- propeller rotation,
- motor vibration,
- rotor imbalance,
- gyroscopic moments,
- transient acceleration,
- crash impact,
- aerodynamic pressure distribution,
- gust loads,
- flight-control dynamics.

---

# 17. Recommended Next Analysis

The current simulation provides a strong baseline for further aerospace/mechanical analysis.

### Next-level structural studies

- Mesh-convergence study
- Local mesh refinement around fastener holes
- Fastener preload / bolt-pretension analysis
- Frictional contact analysis
- Carbon laminate failure analysis
- Modal analysis
- Harmonic response
- Random vibration
- Buckling analysis
- Transient structural analysis
- Fatigue analysis
- Thermal-structural analysis
- Static load cases at different thrust levels
- Off-axis thrust / motor failure cases
- Asymmetric thrust loading
- Crash/impact simulation

### Design optimization

Potential design variables include:

- carbon plate thickness,
- arm diameter,
- arm wall thickness,
- bracket geometry,
- fastener arrangement,
- hole diameter,
- plate cut-outs,
- arm-to-plate attachment geometry,
- local reinforcement.

The ultimate objective is to maximize:

**stiffness-to-mass ratio**

while maintaining adequate structural margins.

---

# 18. Suggested Load-Case Matrix

A future verification campaign can use:

| Load Case | Description |
|---|---|
| LC-01 | Symmetric hover thrust |
| LC-02 | Maximum continuous thrust |
| LC-03 | 1 motor at reduced thrust |
| LC-04 | 1 motor failure |
| LC-05 | Opposing motor imbalance |
| LC-06 | Forward acceleration |
| LC-07 | Lateral acceleration |
| LC-08 | Vertical landing load |
| LC-09 | Gust / maneuver load |
| LC-10 | Crash/impact load |

This converts the current single static study into a broader UAV structural validation program.

---

# 19. Engineering Significance

This project demonstrates a complete CAE workflow rather than a simple stress plot.

It integrates:

- **3D CAD**
- **Composite material modeling**
- **Orthotropic elasticity**
- **Isotropic polymer modeling**
- **Metallic hardware**
- **Automatic contact generation**
- **High-density finite-element meshing**
- **Static structural loading**
- **Solver execution**
- **Post-processing**
- **Stress/strain interpretation**
- **Structural design review**

The model is particularly useful as a foundation for demonstrating practical understanding of **load paths, composite structures, mechanical joints, FEA setup, meshing, and engineering interpretation**.

---

# 20. Project Status

### Current status: **Solved — Baseline Structural FEA**

Completed:

- [x] 3D UAV frame geometry
- [x] Mechanical hardware included
- [x] Carbon-fiber orthotropic material
- [x] Carbon-fiber rod orthotropic material
- [x] ABS material
- [x] Structural-steel material
- [x] Automatic contact generation
- [x] Finite-element mesh
- [x] Four thrust load cases
- [x] Fixed structural constraint
- [x] Static structural solution
- [x] Equivalent elastic strain
- [x] Total deformation
- [x] Strain energy
- [x] Maximum principal stress
- [x] ANSYS report export
- [ ] Mesh-convergence validation
- [ ] Composite failure criterion
- [ ] Fastener preload validation
- [ ] Modal analysis
- [ ] Buckling analysis
- [ ] Fatigue analysis
- [ ] Experimental correlation

---

# 21. Conclusion

The current ANSYS model successfully solves a detailed static structural representation of the UAV frame under four 10 N motor-thrust loads.

The principal reported outputs are:

- **545,580 nodes**
- **266,057 elements**
- **132 contact regions**
- **2.3987 mm maximum total deformation**
- **4.5572 × 10⁻³ maximum equivalent elastic strain**
- **3.9066 × 10⁻² J total strain energy**
- **342.76 MPa maximum principal stress**

The results indicate that the global frame response can be quantified, but the current **peak principal stress requires further investigation**, particularly around the `GB70-M3-38` hardware region. The combination of stress concentration, contact modeling, mesh-quality limitations, and idealized material data means that the current result should be treated as a **baseline engineering simulation rather than a final structural certification result**.

The next major step is to perform **mesh convergence, local joint refinement, and composite-specific failure analysis**, followed by validation against experimental measurements.

---

# 22. Reproducibility

For reproducible results:

1. Use the same ANSYS release where possible (**2025 R1**).
2. Use the same geometry revision.
3. Preserve the material definitions.
4. Preserve the contact definitions.
5. Preserve the mesh settings.
6. Preserve the global coordinate system.
7. Apply the same four 10 N force loads.
8. Preserve the fixed-support location.
9. Solve using the same analysis configuration.
10. Compare result extrema and locations.

Any change to geometry, material data, contacts, mesh, or boundary conditions should be treated as a **new analysis revision**.

---

# 23. Repository Structure

```text
UAV-Frame-Structural-Analysis/
│
├── drone.wbpj
├── x-500 frame ADDC ansys.step
├── report.mht
│
├── mesh.jpg
├── equivalent elastic strain.jpg
├── total deformation.jpg
├── strain energy.jpg
├── max principle stress.jpg
│
├── Screenshot 2026-09-10 215945.jpg
├── Screenshot 2026-09-10 220038.jpg
├── Screenshot 2026-09-10 220115.jpg
├── Screenshot 2026-09-10 220149.jpg
│
└── README.md
```

---

# 24. Author

**Zayan Abdul Rahman C.A.**

Mechanical Engineering  
Rajagiri School of Engineering & Technology  
Kerala, India

### Project

**UAV Frame Structural Analysis**

### Repository

**UAV-Frame-Structural-Analysis**

---

## Disclaimer

This repository is intended for **academic, research, portfolio, and engineering-development purposes**.

The simulation results should not be interpreted as certification, airworthiness approval, or proof that the physical UAV is safe for flight.

Before manufacturing or flight testing, validate:

- material properties,
- fastener specifications,
- composite layup,
- manufacturing quality,
- mesh convergence,
- structural margins,
- dynamic loads,
- vibration,
- fatigue,
- impact loads,
- and experimentally measured structural behavior.

**Always perform appropriate engineering review and physical validation before operating a UAV based on simulation results.**
