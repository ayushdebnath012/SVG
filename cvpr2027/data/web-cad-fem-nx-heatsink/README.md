# Computational Thermal Analysis of a Finned Heat Sink

## 📌 Project Overview
This repository details the computational fluid dynamics (CFD) and thermal analysis of a finned heat sink designed for electronic component cooling. The project focuses on evaluating heat dissipation efficiency and identifying design optimizations to prevent thermal throttling and ensure optimal operating temperatures.

**Duration:** Jan 2026 – Feb 2026  

## 🛠️ Tools & Technologies
* **CAD Modeling:** Siemens NX
* **Simulation & FEA:** ANSYS (Steady-State Thermal)
* **Key Techniques:** Computational Meshing, Boundary Condition Application, Thermal Gradient Analysis

## ⚙️ Methodology
1.  **3D Modeling:** Designed a baseline finned heat sink geometry in Siemens NX, prioritizing surface area maximization for convective heat transfer.
2.  **Meshing:** Generated a high-quality computational mesh within ANSYS. Applied localized mesh refinement at critical regions (such as the base-to-fin transition) to capture high-gradient thermal zones accurately.
3.  **Boundary Conditions:** Applied steady-state boundary conditions simulating real-world operating environments, including specific heat flux at the base (representing an electronic component) and natural/forced convection parameters on the fin surfaces.
4.  **Simulation & Solving:** Executed the steady-state thermal analysis to compute temperature distribution and heat flux vectors across the solid body.

## 📊 Key Results & Insights
* **Effective Heat Dissipation:** The simulation demonstrated a successful thermal gradient, reducing the temperature from **~85°C** at the heat source down to **~59°C** at the fin tips.
* **Performance Evaluation:** Analyzed the convective heat transfer across the fins, confirming the structural integrity of the thermal design.
* **Optimization Pathway:** Identified key areas for geometric improvement. Adjusting fin spacing and thickness based on the thermal contours is projected to enhance overall cooling efficiency by an additional **10–15%**.

## 📁 Repository Structure

* `HeatSink1.prt` - The original Siemens NX 3D CAD model file of the finned heat sink.
* `heatsink01.PNG` - Rendered visualizations of the CAD geometry.
* `mesh.PNG` - Visual representation of the localized computational mesh generated for the simulation.
* `temperatures1.PNG` & `temperatures2.PNG` - Steady-state thermal contour plots illustrating the temperature gradient from the heat source to the fin tips.

## 🚀 Future Scope
* Perform transient thermal analysis to understand heat sink behavior under fluctuating power loads.
* Conduct a parametric study comparing different heat sink materials (e.g., Aluminum vs. Copper alloys).
* Integrate fluid flow (conjugate heat transfer) analysis to simulate forced air cooling via an external fan.
