

# aerospace-wing-box-fea
# ANSYS APDL simulation workflow evaluating high-g aeroload sizing, spatial grid convergence, multi-material trade-offs, and Block Lanczos eigenmode extraction for an aerospace wing box.

**Author:** Muhammad Yousuf Baig  
**Domain:** Computational Structural Mechanics / Aerospace Finite Element Analysis  
**Tools:** ANSYS APDL, Python, Solid Mechanics  
**License:** MIT License  

---

## Overview

This repository contains a computational structural mechanics study of an aerospace wing box subjected to high-g aerodynamic loading.

The project covers:

- Aerodynamic loading and initial structural sizing
- Static stress and deformation analysis
- Mesh sensitivity and convergence
- SHELL181 vs. SHELL281 element comparison
- Material selection and cost comparison
- Free-vibration and modal analysis

The complete FEA workflow was carried out using native ANSYS Parametric Design Language (APDL) scripts. Python was used where required for data processing and comparison.

---

## 1. Aerodynamic Loading and Baseline Sizing

The aerodynamic loading was calculated for supersonic/transonic flight conditions and applied to the wing-box structural model.

### Loading and Geometry

| Parameter | Value |
|---|---:|
| Dynamic Pressure (q∞) | 31,184.5 kPa |
| Peak Aerodynamic Lift Force | 1,491,779.51 kN |
| Wing Span (L) | 10.92 m |
| Chord (c) | 4.87 m |
| Surface Area (A) | 56.95 m² |

The peak aerodynamic lift force corresponds to the Wing-Up +g maneuver case.

### Initial Structural Sizing

An initial analytical beam calculation gave a required thickness of:

```text
11.949 m
````

When this thickness was used in the structural model, the maximum von Mises stress was approximately:

```text
988 MPa
```

The yield strength of Aluminium 2024-T3 used in the analysis is:

```text
345 MPa
```

Therefore:

```text
988 MPa > 345 MPa
```

The initial design therefore did not satisfy the yield criterion.

The thickness was then increased during the structural sizing process.

A thickness of:

```text
31.5 m
```

resulted in a maximum von Mises stress of approximately:

```text
340 MPa
```

which is below the 345 MPa yield limit used for Aluminium 2024-T3.

### Shell Theory Limitation

The 31.5 m thickness is not physically representative of a conventional thin aerospace wing structure.

For the model:

```text
Wing span = 10.92 m
Thickness = 31.5 m
```

the resulting ratio was:

```text
R/t = 0.366
```

This is below the commonly used thin-shell requirement of approximately:

```text
R/t > 10
```

Therefore, the 31.5 m thickness does not satisfy the assumptions of thin-shell theory.

This limitation was documented because the model was being used to satisfy the 2D shell-element requirements in ANSYS. The thickness should therefore be treated as a modeling workaround rather than a practical aerospace structural thickness.

---

## 2. Mesh Sensitivity Analysis

Mesh sensitivity was investigated using the 4-node linear shell element:

```text
SHELL181
```

Three mesh densities were tested for the Wing-Up loading case.

| Mesh       | Element Size | Max Stress | Max Displacement |  CPU Time |        RAM |
| ---------- | -----------: | ---------: | ---------------: | --------: | ---------: |
| **Coarse** |       0.10 m |  143.0 MPa |       0.004464 m | 1341.35 s | 1693.87 MB |
| **Medium** |       0.05 m |  143.0 MPa |       0.004567 m | 1866.06 s | 2090.52 MB |
| **Fine**   |       0.01 m |  143.0 MPa |       0.004657 m | 2415.87 s | 2016.18 MB |

The maximum stress remained approximately 143.0 MPa for all three mesh sizes.

The maximum displacement changed as follows:

```text
0.004464 m → 0.004567 m → 0.004657 m
```

as the mesh was refined.

The 0.05 m medium mesh was selected for the remaining analyses because it provided a good balance between displacement convergence and computational cost.

---

## 3. Element Sensitivity Analysis

Two shell element formulations were compared:

* SHELL181
* SHELL281

### SHELL181

SHELL181 is a 4-node linear shell element and was used for the main mesh sensitivity and material studies.

### SHELL281

SHELL281 is an 8-node quadratic shell element. It was evaluated to investigate the effect of higher-order element interpolation on the structural solution.

### ANSYS Student Version Node Limit

The quadratic SHELL281 model generated a significantly larger number of degrees of freedom as the mesh was refined.

This approached the ANSYS Student version limit of approximately:

```text
250,000 nodes
```

To allow the element formulations to be compared, the SHELL281 analysis was performed using a larger element size:

```text
0.10 m
```

This allowed the effect of the element formulation to be investigated separately from the finer mesh density.

### Matrix Singularity

Using the original 31.5 m thickness with the quadratic element model caused solver matrix instability.

To allow the SHELL281 model to solve successfully, the thickness was scaled to:

```text
0.0026 m
```

for the quadratic-element runs.

This adjustment was made specifically to allow the element formulation to be evaluated and should be considered when comparing the SHELL181 and SHELL281 results.

---

## 4. Material Comparison

Three structural materials were compared using a constant-volume model.

The volume was kept constant at:

```text
749.07 m³
```

The comparison was performed using the Medium Mesh with the SHELL181 element.

| Material               |     Density | Yield Strength | Max Stress | Max Displacement |   Total Weight | Raw Material Cost |
| ---------------------- | ----------: | -------------: | ---------: | ---------------: | -------------: | ----------------: |
| **Aluminium 2024-T3**  | 2,780 kg/m³ |        345 MPa |  143.0 MPa |       0.004567 m | 2,082,414.6 kg |     $9,370,865.70 |
| **Aluminium 7075-T6**  | 2,810 kg/m³ |        503 MPa |  250.0 MPa |       0.009440 m | 2,104,886.7 kg |    $10,945,410.80 |
| **Titanium Ti-6Al-4V** | 4,430 kg/m³ |        880 MPa |  631.0 MPa |       0.019843 m | 3,318,379.1 kg |   $132,735,164.00 |

### Material Selection

Based on the comparison, Aluminium 7075-T6 was selected as the preferred material for the final model.

Compared with Aluminium 2024-T3:

| Parameter         | Aluminium 2024-T3 | Aluminium 7075-T6 |
| ----------------- | ----------------: | ----------------: |
| Yield Strength    |           345 MPa |           503 MPa |
| Total Weight      |    2,082,414.6 kg |    2,104,886.7 kg |
| Raw Material Cost |     $9,370,865.70 |    $10,945,410.80 |

The yield strength increase is:

```text
(503 - 345) / 345 × 100
= 45.80%
```

The increase in total mass is:

```text
(2,104,886.7 - 2,082,414.6) / 2,082,414.6 × 100
= 1.08%
```

Therefore, Aluminium 7075-T6 provides approximately 45.8% higher yield strength than 2024-T3 with only a 1.08% increase in mass.

The raw material cost increases from:

```text
$9,370,865.70 → $10,945,410.80
```

Aluminium 7075-T6 was selected as the preferred material based on its higher yield strength and relatively small increase in mass compared with Aluminium 2024-T3.

---

## 5. Free Vibration and Modal Analysis

A free-vibration modal analysis was performed on the wing-box model using:

* **Material:** Aluminium 7075-T6
* **Mesh:** Medium, 0.05 m
* **Element:** SHELL181
* **Solver:** Block Lanczos

The model was analyzed as a cantilever wing box under free-vibration conditions.

The first four natural frequencies obtained from the analysis were:

|  Mode | Natural Frequency | Mode Description                                                                    |
| ----: | ----------------: | ----------------------------------------------------------------------------------- |
| **1** |    **46.6976 Hz** | 1st mode torsion; tip-dominant rotational twist                                     |
| **2** |    **72.1800 Hz** | 1st mode bending; cantilever flexural deformation                                   |
| **3** |    **98.9160 Hz** | 2nd mode torsion; higher-order torsional deformation with internal inflection nodes |
| **4** |   **132.2590 Hz** | 2nd mode bending; higher-order multi-nodal flexural deformation                     |

The modal results provide the first four natural frequencies and corresponding deformation patterns of the wing-box structure.

---

## 6. Summary of Results

* The initial analytical thickness of 11.949 m resulted in a maximum stress of approximately 988 MPa, exceeding the 345 MPa yield strength of Aluminium 2024-T3.
* Increasing the modeled thickness to 31.5 m reduced the maximum stress to approximately 340 MPa.
* The 31.5 m thickness violates thin-shell assumptions and was documented as a modeling workaround.
* Mesh refinement from 0.10 m to 0.01 m produced approximately the same maximum stress of 143 MPa.
* The 0.05 m medium mesh was selected as the best compromise between convergence and computational cost.
* SHELL281 was evaluated separately because its higher number of degrees of freedom approached the 250,000-node ANSYS Student limit.
* The SHELL281 model used a 0.10 m mesh and a 0.0026 m thickness to avoid solver matrix instability.
* Aluminium 7075-T6 was selected over 2024-T3 and Ti-6Al-4V based on the material comparison.
* Aluminium 7075-T6 provided approximately 45.8% higher yield strength than 2024-T3 with approximately 1.08% higher mass.
* The first four natural frequencies of the selected wing-box model were 46.6976 Hz, 72.1800 Hz, 98.9160 Hz, and 132.2590 Hz.

---

## Repository Structure

```text
/
├── APDL/
│   ├── Geometry
│   ├── Material definitions
│   ├── Mesh generation
│   ├── Boundary conditions
│   ├── Static analysis
│   ├── Mesh sensitivity
│   ├── Element sensitivity
│   └── Modal analysis
│
├── CAD/
│   └── Model link and geometric specifications
│
├── FEA-Analysis/
│   ├── Section 1 (Initial Sizing & Boundary Conditions)
│   ├── Section 2 (Mesh Sensitivity Contours & Graphs)
│   ├── Section 3 (Linear vs. Quadratic Element Contours)
│   ├── Section 4 (Material Trade-Off Contours)
│   └── Section 5 (Modal Vibration Mode Shapes)
│
├── Python/
│   └── process_fea_results.py
│
├── Results/
│   ├── forces.xlsx
│   ├── details.txt
│   └── Infographics
│
└── Report/
    └── Project report and supporting documentation
```

---

## Files and Folders

### `/APDL`

Contains the APDL scripts used to build the model, define materials, generate the mesh, apply loads and boundary conditions, and run the structural analyses.

### `/CAD`

Contains the CAD model download link and geometric information for the wing box.

### `/FEA-Analysis`

Contains the visual results from the different analysis sections, including stress contours, displacement plots, mesh comparisons, material comparisons, and modal deformation plots.

### `/Python`

Contains scripts used for processing and comparing the numerical results.

### `/Results`

Contains the numerical output from the different analysis cases, including mesh, element, material, static structural, and modal studies.

### `/Report`

Contains the complete project report and supporting documentation.

---

## License

This project is distributed under the MIT License.

```
