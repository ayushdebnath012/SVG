# 🔥 Heat-Assisted-Incremental-Sheet-Forming-of-a-Titanium-grade-5-plate 

📌 **Capstone Project (CP302) – IIT Ropar | Department of Mechanical Engineering**  

---

## 📖 Project Overview  
This repository presents our **Capstone Project** on *Heat-Assisted Incremental Sheet Forming (HA-ISF)* of **Ti-6Al-4V (Grade 5 Titanium alloy)**.  
The project demonstrates how **thermal assistance** enhances the formability of titanium alloys, enabling the production of complex aerospace and biomedical components with improved accuracy and reduced risk of fracture.  

Key focus areas:  
- Simulation-driven exploration of **thermomechanical behavior**.  
- Comparative analysis between **room temperature (25 °C)** and **elevated temperature (600 °C)** forming.  
- Development of a **robust computational workflow** integrating CAD, CAM, and FEM tools.  

---

## 🎯 Objectives  
- Investigate **temperature-dependent stress–strain behavior** of Ti-6Al-4V.  
- Simulate **incremental sheet forming (ISF)** at varying depths (9.5–69.5 mm) and wall angles (20°–60°).  
- Quantify **stress reduction, thickness retention, and forming forces** with heat assistance.  
- Propose **future design strategies** for experimental HA-ISF prototypes.  

---

## 🧩 Methodology  

1. **Material Modeling**  
   - Titanium alloy (Ti-6Al-4V, 1 mm thick).  
   - Johnson–Cook plasticity & damage models with temperature dependency.  

2. **Tool & CAD/CAM Workflow**  
   - **Tool Design:** Conical forming tools designed in *SolidWorks*.  
   - **Trajectory Planning:** Spiral toolpaths generated in *Fusion 360*.  
   - **G-Code Extraction:** G-Code Ripper used for full coordinate data.  

3. **Finite Element Simulations**  
   - Software: *Abaqus/Explicit*.  
   - Element type: S4R shell elements (refined mesh in forming zone).  
   - Contact: Lubricated conditions, μ = 0.1.  
   - Six case studies comparing:  
     - Depth: 9.5–69.5 mm  
     - Temperature: 25 °C vs 600 °C  
     - Wall angle: 20°, 45°, 60°  

---

## 📊 Key Findings  

- ✅ **56% stress reduction** at 600 °C compared to 25 °C.  
- ✅ **Full depth achieved** (59.5 mm & 69.5 mm) at elevated temperature, vs ~39 mm stall at room temp.  
- ✅ **Thickness improvement**: 0.50 mm at 600 °C vs ~0.35 mm at 25 °C.  
- ✅ **Force reduction**: 62–67% lower Z-direction forming forces at elevated temperature.  
- ✅ **Validation**: Thickness predictions matched sine-law within **0.5% error**.  

---

## 🛠️ Tools & Technologies  

- **Simulation & FEA**: Abaqus/Explicit  
- **Design & CAM**: SolidWorks, Fusion 360, G-Code Ripper  
- **Programming/Scripting**: Python (data processing, simulation automation)  
- **Analysis**: MATLAB, Excel  

---

## 👥 Team & Mentorship  

- **Project Team:**  
  - Aditya Kumar (2022MEB1290)  
  - Aryan Daga (2022MEB1300)  
  - Priyanshu Rao (2022MEB1331)  
  - Priyanshu Singh (2022MEB1332)  

- **Supervisor:**  
  - Dr. Anupam Agrawal, Department of Mechanical Engineering, IIT Ropar  

---

## 🚀 Future Work  

- 🏗️ **Prototype Development:** Build HA-ISF experimental setup with induction heating & real-time IR pyrometry.  
- 🔥 **Localized Heating Strategies:** Implement laser/induction-assisted localized heating models.  
- 📐 **Process Optimization:** AI/ML-driven parameter tuning (toolpath, heating profiles, energy efficiency).  
- 🔬 **Validation Framework:** 3D-DIC strain measurements, microstructural analysis (EBSD, TEM).  

---

## 📄 Full Report  

📑 [CapstoneProject_CP302_EndSem_Report.pdf](https://github.com/Priyanshu-Mechanical-Engineer/Heat-Assisted-Incremental-Sheet-Forming-of-a-Titanium-grade-5-plate/blob/39ad2f46eee84782fe789f0a700cb1f708a34aeb/Reports/Heat%20Assisted%20ISF%20of%20grade%205%20titanium%20sheet.pdf)  

---

## 🏆 Highlights for Recruiters  

✔ Demonstrated **strong integration of CAD, CAM, and FEA tools** for solving real-world manufacturing challenges.  
✔ Delivered **quantitative insights** into stress, thickness, and formability improvements for titanium alloys.  
✔ Applied **simulation–based design workflow** transferable to aerospace, automotive, and biomedical manufacturing.  
✔ Experience with **Python automation, Abaqus simulations, and advanced material modeling**.  

---
