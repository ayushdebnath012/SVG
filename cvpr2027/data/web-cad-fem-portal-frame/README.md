# Design and Finite Element Analysis of a Rigid Steel Portal Frame 🏗️

![Project Banner](Assets/Assembly)
*An industry-standard portal frame designed in SolidWorks, featuring moment-resisting connections and optimized load paths.*

## 🛠️ Tech Stack
![SolidWorks](https://img.shields.io/badge/CAD-SolidWorks-red)
![FEA](https://img.shields.io/badge/Simulation-Static_Analysis-blue)
![Six Sigma](https://img.shields.io/badge/Methodology-Six_Sigma-green)
![Status](https://img.shields.io/badge/Status-In_Progress-yellow)

## 📖 Project Overview
This project involves the design, failure analysis, and optimization of a structural steel portal frame intended for an industrial warehouse.

Moving beyond basic geometric modeling, this project applies the Six Sigma DMAIC methodology to troubleshoot initial simulation failures (rigid body motion & singularities) and optimize the design to withstand a roof load of $10 \text{ kN}$. The analysis focuses on critical stress concentrations at the eave connections and ensures the structural integrity of the frame through rigorous Finite Element Analysis (FEA).

## ⚙️ Key Design Features (The "Why")

### 1. Haunched Eaves Connection
![Haunch Detail](Assets/Hunch)
* **Problem:** The connection between the column and rafter experiences the highest **Bending Moment** in the entire structure.
* **Solution:** Designed a tapered haunch to increase the beam depth at the joint. This significantly reduces stress concentration and allows for a lighter rafter section elsewhere.

### 2. Internal Column Stiffeners (Continuity Plates)
![Stiffener Detail](Assets/Stiffners)
* **Problem:** The compression force from the haunch flange pushes directly against the column web, creating a risk of **Local Web Buckling**.
* **Solution:** Modeled horizontal continuity plates inside the column to bridge the load path and transfer forces effectively.

### 3. Detailed Bolted Assemblies
* Utilized standard structural bolts with appropriate pre-tension clusters in the tension zones.
* Designed flush end-plates for manufacturability.

## 🧪 Simulation & Analysis (FEA)
🚩 The Challenge (Define & Measure)

Initial simulations using Beam Elements failed due to connectivity errors (resulting in "flying parts"). Subsequent runs utilizing Solid Elements revealed a peak stress of $475 \text{ MPa}$ at the re-entrant corners. This was identified as a Singularity, which exceeded the yield strength of the initial material (ASTM A36, $S_y=250 \text{ MPa}$).

🛠️ The Fix (Analyze & Improve)

To resolve these issues, the design underwent a rigorous optimization process:

Geometry: Converted all members to Solid Bodies to enable accurate face-to-face bonding and contact set definition.

Refinement: Added Fillet Radii ($5 \text{ mm}$) to simulate weld beads. This smoothed stress flow trajectories and eliminated mathematical singularities caused by sharp corners.

Material Upgrade: Upgraded the material specification from ASTM A36 ($S_y=250 \text{ MPa}$) to ASTM A992 ($S_y=345 \text{ MPa}$) to handle higher allowable stresses.

📸 Final Results (Control)

![Stress Final](Assets/StressFinal)
![Stress Almost](Assets/Stress400)
![Stress Fail](Assets/StressAcceptable)

| Metric | Initial Design (Fail) | Optimized Design (Pass) |
| :--- | :--- | :--- |
| **Material** | ASTM A36 ($S_y=250 \text{ MPa}$) | **ASTM A992 (**$S_y=345 \text{ MPa}$**)** |
| **Peak Stress** | $475 \text{ MPa}$ (Singularity) | $317 \text{ MPa}$ **(Safe)** |
| **Deflection** | Infinite (Error) | $5.12 \text{ mm}$ **(Rigid)** |
| **Stability (BLF)** | N/A | $5.05$ **(Extremely Stable)** |

📐 Theoretical Validation

The FEA results were verified against manual Beam Theory calculations to ensure accuracy:

Static Equilibrium: Confirmed $\sum F_y = 0$.

Stress Check: Hand calculations predicted a nominal stress of $106 \text{ MPa}$. The FEA peak of $317 \text{ MPa}$ yields a ratio of $\approx 3.3$. This correlates accurately with the theoretical Stress Concentration Factor ($K_t$) expected for sharp corners and welded joints.

Stiffness Check: The FEA deflection ($5.12 \text{ mm}$) aligns closely with the Fixed-Fixed beam approximation calculation ($3.24 \text{ mm}$), confirming the rigid behavior of the connections.

## 📂 File Structure
- `CAD_Files/`: Native SolidWorks 2024 files.
- `Universal_Formats/`: STEP files for non-SW users.
- `Simulation_Reports/` : Comprehensive report.
- `Drawings/`: 2D Fabrication prints (PDF).

## 👨‍💻 Author
**Karthik V S**
Mechanical Engineering Undergraduate
https://www.linkedin.com/in/karthik-v-s-926b34335
