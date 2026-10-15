This project is not in its final state.


### **Project Overview & Executive Summary**

This project establishes an automated Model-Based Systems Engineering (MBSE) and Multidisciplinary Design Optimization (MDO) pipeline for a high-pressure, liquid oxygen (LOX) rocket engine turbopump stage. The architecture closes the loop between first-principles analytical sizing, automated heuristic optimization, 3D parametric computer-aided design (CAD), and multi-domain Navier-Stokes computational fluid dynamics (CFD) within an integrated ANSYS Workbench environment. 

Read through the PowerPoint presentation titled "Report.pptx" to get more detailed information than what is written in this description and links to other files produced while working on this project. For the intended experience, please download the presentation and open it in the PowerPoint application. 

---

### **Core Pipeline Methodology**

#### **1. 1D Meanline Analytical Modeling (MATLAB)**

* **Kinematic & Thermodynamic Formulation:** Formulated a meanline solver based on Euler's turbomachinery equations and velocity triangles to predict theoretical Euler head, blade loading, and shaft torque.


* **Real-Fluid Thermophysical Properties:** Coupled the solver with **CoolProp** to evaluate subcooled LOX properties (density $\rho$, kinematic viscosity $\nu$, and saturation vapor pressure $P_{\text{vap}}$) dynamically as functions of local temperature ($T = 85\text{--}90\text{ K}$) and suction pressure, preventing fixed-density sizing errors.


* **Cavitation & Inducer Coupling:** Sized an axial inducer stage preceding the centrifugal impeller eye to provide an initial static head rise ($\Delta P_{\text{ind}} \approx 4.8\text{ bar}$), raising the Net Positive Suction Head Available ($NPSH_A$) to safely exceed the Required Suction Head ($NPSH_R$).


* **Empirical Screening & Deviation:** Solved for blade metal angles ($\beta_{1B}$, $\beta_{2B}$) through an implicit root-finding formulation incorporating El-Naggar and Stodola slip factor corrections, while enforcing the NASA SP-8109 Cordier curve ($0.75 \le D_s / D_{s,\text{opt}} \le 1.35$) to reject unphysical geometries prone to boundary layer stalling.



#### **2. Genetic Algorithm (GA) Optimization**

* **Constrained Fitness Landscape:** Deployed a parallelized Genetic Algorithm (`ga`) using non-dimensional geometric ratios ($b_2/d_2$, $d_{\text{eye}}/d_2$, $b_1/d_{\text{eye}}$) as bounded decision variables, enforcing physically viable velocity triangles across candidate designs.


* **Proportional Penalty Formulation:** Guided convergence through an objective function combining efficiency maximization with continuous proportional penalties targeting pressure rise ($15 \times \vert{}\Delta P_{\text{actual}} - 75.0\text{ bar}\vert{}$), Cordier line deviations, and a step penalty (+200) for cavitation failure.


* **Execution & Output:** Evaluated candidate geometries across 300 generations, isolating a baseline design point:
* **Shaft Speed:** $28,000\text{--}30,896\text{ RPM}$

* **Stage Total Pressure Rise:** $75.0\text{--}76.26\text{ bar}$

* **Impeller Outer Diameter ($d_2$):** $78.0\text{--}81.33\text{ mm}$

* **Impeller Blade Count ($Z$):** 7–8 backward-curved blades


* **Cordier Specific Diameter Ratio ($D_s / D_{s,\text{opt}}$):** $1.05\text{--}1.14$ (PASS)


* **Cavitation Margin:** $NPSH_A \approx 81.9\text{ m}$ vs. $NPSH_R = 4.5\text{ m}$ ($>75\text{ m}$ safety margin).





#### **3. Parametric 3D CAD Generation (CFturbo)**

* **Geometric Translation:** Direct porting of 1D meanline parameters into **CFturbo** to generate fully parametric 3D blade profiles, meridional hub/shroud contours, and a circular cross-section volute collector scaled to conserve angular momentum.


* **Automated Boundary Tagging:** Pre-configured CFturbo Workbench Named Selections (using prefix filtering) to expose geometric faces (blades, hub, shroud, cut-water) directly to downstream meshing modules.



#### **4. Automated 3D Simulation & MDO Loop (ANSYS Workbench)**

* **Multi-Domain Meshing Strategy:** Routed rotating helical inducer passages into **ANSYS TurboGrid** for boundary-layer-resolved hexahedral grids with sector periodicity, while routing the centrifugal impeller and casing into **SpaceClaim / ANSYS Meshing**.


* **Hydrodynamic Verification (ANSYS CFX):** Conducted steady-state 3D Navier-Stokes analyses applying the $k$-$\omega$ SST turbulence model and frozen rotor / mixing-plane interfaces between rotating and stationary domains.


* **Optimization Closure (optiSLang / DesignXplorer):** Formulated a Latin Hypercube Sampling (LHS) Design of Experiments (DoE) driving bi-directional parameter updates in CFturbo (varying blade wrap and trailing-edge angles $\beta_{2,\text{hub}}$, $\beta_{2,\text{shroud}}$) to optimize hydraulic efficiency while monitoring local minimum pressure ($P_{\min} > P_{\text{sat}}$) to eliminate 3D cavitation cores.



---

### **Downstream Multiphysics & Verification**

* **Structural Integrity (ANSYS Mechanical FEA):** One-way Fluid-Structure Interaction (FSI) mapping 3D static pressure fields and centrifugal loads onto solid blade/hub domains to verify yield safety margins at 120% operational overspeed (33,600 RPM).


* **Rotordynamics & Modal Analysis:** Critical speed calculations targeting subcritical operation with a 1st bending critical speed margin $\ge 140\text{--}150\%$ of nominal operating speed, consistent with turbomachinery design practice.


* **Acoustics & NVH:** Spectral evaluation of unsteady blade-pass frequencies ($BPF = Z \times \omega / 60$) to prevent structural acoustic lock-in with volute cut-water pressure pulsations.
