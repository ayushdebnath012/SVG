# Formula SAE Chassis Structural Analysis

This project focuses on the **structural analysis of a Formula SAE chassis** using **ANSYS Workbench (SpaceClaim + Mechanical)**. The objective was to evaluate the **stiffness, strength, and load-carrying capability** of the spaceframe chassis under multiple realistic loading conditions.

---

## Project Overview

The chassis was analyzed under **torsion**, **cornering**, **aero + cornering**, and **frontal impact** load cases.
The workflow followed a step-by-step approach from geometry simplification and beam extraction to joint setup, meshing, boundary condition application, and post-processing.

---

# Formula SAE Spaceframe Chassis — Structural Analysis (ANSYS Workbench)

This project presents the **static structural analysis of a Formula SAE spaceframe chassis** using **ANSYS Workbench 2025 R2 (SpaceClaim + Mechanical)**. The analysis evaluates **strength, stiffness, and load-bearing capability** under real race conditions: **torsion, cornering, aero-cornering, and frontal impact**.

---

## Project Highlights

| Feature | Description |
|---------|-------------|
| **Chassis Type** | Tubular Spaceframe |
| **Analysis Method** | Beam-based FEA |
| **Software** | ANSYS Workbench 2025 R2 |
| **Material** | Structural Steel (Yield ≈ 250 MPa) |
| **Suspension Representation** | Joints + Springs + Upright Constraints |
| **Load Cases** | Torsion, Cornering, Aero + Cornering, Frontal Impact |

---

## Modeling Workflow Summary

### **1) Beam Extraction & Section Assignment**
- CAD imported to **SpaceClaim**.
- Members converted into **beam elements**.
- Connectivity corrected using **Connect Tool** (`max gap = 25 mm`).
- Beam profile (for all tubes):

| Property | Value |
|----------|-------|
| Outer Diameter | **16 mm** |
| Inner Diameter | **12.5 mm** |

---

### **2) Suspension & Upright Construction**
- Wishbones generated via imported **pickup point coordinates**.
- Geometry mirrored for symmetry.
- Splits added at upright contacts for joint definitions.
- **Point masses** added:
  - Driver: **70 kg**
  - Engine/Rear Unit: **25 kg**
- Applied via remote attachments to chassis nodes.

---

### **3) Joints, Springs & Meshing**
- **Material:** Structural Steel.
- **Joints:** Spherical + Revolute via Object Generator (`search distance = 5 mm`).
- **Spring elements:** Suspension stiffness ≈ **40 N/mm** axial.
- **Mesh:** Global beam element sizing = **5 mm** (uniform discretization).

---

## Load Case Analysis & Results

---

### **1) Torsion Test**

| Parameter | Value |
|-----------|-------|
| Load | ±1500 N at front uprights (opposite direction) |
| Rear Constraints | Simply supported (translations fixed, free rotations) |

**Results**

| Output | Value |
|--------|-------|
| Max Deformation | **2.268 mm** |
| Max Direct Stress | **11.176 MPa** |
| Max Combined Stress | **≈ 202 MPa** |

> **Conclusion:** High torsional rigidity, stresses below yield → **safe under race torque loads**.

*Torsional stiffness calculation can be added if track width is provided.*

---

### **2) Cornering Test (1 g Lateral)**

| Parameter | Value |
|-----------|-------|
| Lateral Acceleration | **9800 mm/s² (≈1 g)** |
| Gravity | Included |
| Supports | All Uprights Fixed |

**Results**

| Output | Value |
|--------|-------|
| Max Deformation | **0.825 mm** |
| Max Axial Force | **1475.3 N** |
| Max Direct Stress | **4.711 MPa** |
| Max Combined Stress | **≈ 90.23 MPa** |

> **Conclusion:** Very small lateral deformation (<1 mm). Safe with large stress margin.

---

### **3) Aero + Cornering Test (2 g Downforce + 1 g Cornering)**

| Parameter | Value |
|-----------|-------|
| Lateral Aero Acceleration | **19600 mm/s² (≈2 g)** |
| Gravity | Included |
| Supports | All Uprights Fixed |

**Results**

| Output | Value |
|--------|-------|
| Max Deformation | **0.89088 mm** |
| Max Direct Stress | **5.2027 MPa** |
| Max Combined Stress | **≈ 96.849 MPa** |

> **Conclusion:** Aero load slightly increases deformation but remains <1 mm; stresses far below yield.

---

### **4) Frontal Impact (Static Approximation)**

| Parameter | Value |
|-----------|-------|
| Front Load | **30,000 N** applied at bulkhead |
| Rear Nodes | Simply Supported |

**Results**

| Output | Value |
|--------|-------|
| Max Deformation | **10.52 mm** |
| Max Bending Moment | **6.8211 × 10⁵ N·mm** |
| Max Direct Stress | **7.043 MPa** |
| Max Combined Stress | **315.34 MPa** |

> **Observation:** Combined stresses exceed structural steel yield here, indicating the need for **localized reinforcement at front crash nodes** for severe impacts.

*Recommendation:* thicker crash tubes + additional triangular bracing + explicit crash simulation.

---
## Summary Table (All Load Cases)

| Load Case | Max Deformation | Max Combined Stress | Safety Evaluation |
|-----------|-----------------|--------------------|-------------------|
| **Torsion** | 2.268 mm | 202 MPa | Safe |
| **Cornering** | 0.825 mm | 90.23 MPa | Safe |
| **Aero + Cornering** | 0.891 mm | 96.85 MPa | Safe |
| **Frontal Impact** | 10.52 mm | 315.34 MPa | ⚠ Local Overstress |

---

## Key Learnings

- Efficient beam FEA enables fast and realistic validation of **racecar frames**.
- Suspension loads must be modeled using **springs + joints + upright constraints**, not just fixed bodies.
- Combined stresses (not just von-Mises) should be checked in beam studies.
- Static frontal loading highlights **reinforcement needs** even when torsional and cornering loads are safe.

---

## Tools Used

- **ANSYS SpaceClaim**
- **ANSYS Mechanical (Static Structural)**
- **Beam, Joint, Spring, Remote Loads & Point Masses**
- **Stress/Deformation/Load Path Extraction via Beam Tool**

---

## Results Visualization

---
<img width="756" height="419" alt="FSAE" src="https://github.com/user-attachments/assets/50c74872-24f0-40ff-8f78-c592a18d7fc1" />


---

## Mesh

<img width="1624" height="643" alt="Mesh" src="https://github.com/user-attachments/assets/142dea09-2def-4924-90f7-f73237f60956" />

---

## Torsion Test


<img width="1626" height="633" alt="Tortion Test" src="https://github.com/user-attachments/assets/d94ffe50-f033-481f-ad23-ca0e9263b7ea" />




https://github.com/user-attachments/assets/4da9d7c4-24f4-495a-b828-9308eb6f3f71



https://github.com/user-attachments/assets/63342edc-1288-4a07-b9cf-999541a4201b



https://github.com/user-attachments/assets/a66a56ea-d420-425b-bc28-45cec74be1a8



https://github.com/user-attachments/assets/5f4800ea-6a1d-4420-a5d8-ba2611da757e




---


## Cornering Test


<img width="1625" height="647" alt="Cornering Test" src="https://github.com/user-attachments/assets/87989242-064f-4076-bd38-b6028da0fac8" />



https://github.com/user-attachments/assets/7a3b465f-8112-4d7a-8155-477ec235718d



https://github.com/user-attachments/assets/4a05a36a-43f2-4208-a59e-854dcd92e088



https://github.com/user-attachments/assets/f36ace55-61c6-4d74-a427-7fbe6e6a4c48



https://github.com/user-attachments/assets/526cacb4-80b9-4e4e-8545-1edc0d8362c2



https://github.com/user-attachments/assets/515cb4d5-5187-4946-b071-b268490d2f64



---

## Aero+Cornering Test



<img width="1625" height="637" alt="Aero+Cornering Test" src="https://github.com/user-attachments/assets/e680ced7-5fc3-41ad-91ea-6385d5b1a9e1" />



https://github.com/user-attachments/assets/a5f32eff-e223-4a44-8752-c8ea27b2e019



https://github.com/user-attachments/assets/6a9ad24e-6c03-45a8-8fb0-e2aa7f100633



https://github.com/user-attachments/assets/027fcfb7-717a-4523-a9b0-6763cc694d7f



https://github.com/user-attachments/assets/c7361a27-7bc0-4a9d-a2e7-918f18341153




---

## Frontal Impact Test


<img width="1626" height="635" alt="Frontal Impact Test" src="https://github.com/user-attachments/assets/068aafee-f165-4af7-82bf-771a1f4f59a5" />




https://github.com/user-attachments/assets/99520482-5e3e-4650-84bf-d4591e729680



https://github.com/user-attachments/assets/0de76065-df44-4fff-966d-eceb817f387f



https://github.com/user-attachments/assets/db54f99e-ddcb-4f65-a603-14c2cbd2f4e7



https://github.com/user-attachments/assets/5235b682-80e8-4c4b-b76f-a3aaedc8ae3b



https://github.com/user-attachments/assets/4890b35a-2bd1-45b2-90b1-019527b10514




---



### Author
**Mohammad Haris** — Mechanical Engineer | FEA & CFD Engineer

GitHub: [github.com/MohammadHaris13](https://github.com/MohammadHaris13)

   
[Linkedin Profile](https://linkedin.com/in/mohammad-haris-13032002) | [Email](mailto:mohammaddharis1303@gmail.com)

---














