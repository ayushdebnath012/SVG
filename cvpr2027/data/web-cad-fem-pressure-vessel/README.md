# DESIGN AND ANALYSIS OF PRESSURE VESSEL USING DIFFERENT HEAD CONFIGURATIONS AND MATERIALS (FEA)

---

## 📌 Project Overview
This project explores the field of Finite Element Analysis (FEA) for pressure vessels with different head configurations, while keeping the cylindrical volume and thickness uniform.

The design follows ASME standards (Section VIII, Division I) and focuses on designing a pressure vessel that can withstand an internal pressure of **8 bar** within a volume of **24 liters**.

The main objective of the project is to identify areas of stress concentration for each head design using FEA, and compare the results for different materials.

---

## 📐 Design Specifications

| Parameter | Value |
|----------|-------|
| Shell Outside Diameter | 880 mm |
| Shell Length | 1520 mm |
| Shell Thickness | 20 mm |
| Corrosion Allowance | 1.28 mm |
| Design Pressure | 0.824 MPa |
| Design Temperature | 200 °C |
| Saddle Support Angle | 120° |
| Vessel Orientation | Horizontal |

---

## 🧩 Tools & Software Used
- **ANSYS** (Static & Thermal Analysis)
- **Autodesk Inventor / CATIA** (CAD Modeling)
- **Microsoft Excel** (Calculations & comparison)
- **Python** (optional for graphs)

---

## 🧱 Head Configurations Compared
The pressure vessel is analyzed with different head types:

- **Flat Head**
- **Hemispherical Head**
- **Toriconical Head**
- **Elliptical Head** (if applicable)

---

## 🧠 Objectives
- Design a pressure vessel with constant cylindrical volume and thickness  
- Compare stress distribution for different head configurations  
- Identify stress concentration areas using FEA  
- Compare performance using different materials  
- Select the best head configuration and material for safety and strength  

---

## ⚙️ Methodology
1. Create pressure vessel CAD model in Autodesk Inventor / CATIA  
2. Assign constant thickness and volume  
3. Import the model into ANSYS  
4. Apply boundary conditions and internal pressure of **8 bar**  
5. Perform static structural analysis for each head design  
6. Perform thermal analysis  
7. Compare results for different materials (SA-516 GR.70, Nimonic 75, HSLA, Nimonic 80A)

---

## 📊 Materials Compared

| Material | Application | Key Property |
|----------|-------------|--------------|
| SA-516 GR.70 | Carbon Steel | Common boiler & pressure vessel material |
| Nimonic 75 | High-temperature applications | Nickel-based alloy |
| HSLA | Industrial applications | High strength, low alloy steel |
| Nimonic 80A | High-temperature & high-stress | Nickel-Chromium alloy, age-hardened |

---

## 📈 Thermal Results Summary

| Head Type | Material | Max Temperature (°C) | Total Heat Flux (W/mm²) |
|----------|----------|----------------------|--------------------------|
| Flat Head | SA-516 GR.70 | 200 | 0.92 |
| Hemispherical Head | SA-516 GR.70 | 200 | 0.58 |
| Toriconical Head | SA-516 GR.70 | 200 | 0.71 |
| Flat Head | Nimonic 80A | 200 | 0.41 |
| Hemispherical Head | Nimonic 80A | 200 | 0.26 |
| Toriconical Head | Nimonic 80A | 200 | 0.33 |
| Flat Head | Nimonic 75 | 200 | 0.48 |
| Hemispherical Head | Nimonic 75 | 200 | 0.30 |
| Toriconical Head | Nimonic 75 | 200 | 0.38 |
| Flat Head | HSLA | 200 | 0.67 |
| Hemispherical Head | HSLA | 200 | 0.44 |
| Toriconical Head | HSLA | 200 | 0.53 |

---

## 📌 Thermal Observations
- **Hemispherical heads** show the **lowest heat flux** for all materials.  
- **Nimonic 80A** shows the **lowest heat flux** among all materials, indicating better thermal performance.  
- **SA-516 GR.70** shows the **highest heat flux**, meaning it transfers heat faster and is less efficient under thermal loading.

---

## ✅ Conclusion

From the present work, the following conclusions are drawn:

1. Pressure in a pressure vessel can be generated either from an external source or by the application of heat from a direct or indirect source.

2. Horizontal pressure vessels with different head configurations (Flat head, Hemispherical head, and Toriconical head) were modeled using CATIA / Inventor and imported into ANSYS for structural and thermal analysis.

3. The structural and thermal behavior of the pressure vessel was analyzed for four different materials:  
   - SA-516 GR.70 (Carbon Steel)  
   - Nimonic 75  
   - HSLA (High Strength Low Alloy)  
   - Nimonic 80A

4. The obtained results of Von-Mises stress, strain, total deformation, shear stress, and heat flux were compared for different materials and head configurations.

5. Among the materials studied, **Nimonic 80A showed the lowest stress, deformation, and heat flux values**, indicating better performance under high pressure and thermal conditions.

6. Based on structural and thermal analysis results, **Nimonic 80A is concluded to be the most suitable material** for pressure vessels, especially under high-temperature and high-stress conditions.

7. Nimonic alloys are primarily composed of nickel and chromium, which provide high-temperature strength, low creep, and high performance.  
   Nimonic 80A is a wrought, age-hardened alloy strengthened by additives such as titanium, aluminum, and carbon.  
   It offers excellent corrosion and oxidation resistance, making it suitable for pressure vessel manufacturing.

---

## 📂 Folder Structure

