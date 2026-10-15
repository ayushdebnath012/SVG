# Go-Kart Chassis FEA (GKDC)

Finite element study of a go-kart tubular chassis designed to GKDC regulations and analyzed in **ANSYS 2019 R1**.

**Author:** Pushkal Garg  
B.Tech Mechanical Engineering, IIT Ropar

## Project Scope

This repository documents structural dynamics and fatigue behavior of an AISI 4130 steel chassis under cyclic loading. The analysis combines:

- **Modal analysis** (first 20 natural frequencies)
- **Harmonic response analysis** (0–50 Hz sweep)
- **Fatigue life estimation** with weld/surface correction factors

## Repository Structure

- `/cad/` – SolidWorks CAD source
  - `chassis_2.0_final.SLDPRT`
- `/reports/` – original ANSYS export/report
  - `ANSYS_Analysis_Report.pdf`
- `/docs/` – technical supporting documentation
  - `analysis-summary.md`
  - `simulation-setup.md`

## Material

The chassis material model used in ANSYS is **AISI 4130 (Chromoly steel)**.

| Property | Value |
|---|---:|
| Density | 7850 kg/m³ |
| Young’s Modulus | 2.016×10¹¹ Pa |
| Poisson’s Ratio | 0.26 |
| Shear Modulus | 8.0×10¹⁰ Pa |
| Yield Strength | 460 MPa |
| Ultimate Strength | 560 MPa |

## Model and Solver Setup

- **Geometry envelope:** 2.28 m (L) × 1.6872 m (W) × 0.88005 m (H)
- **Mass:** 63.953 kg
- **Mesh:** 93,476 elements, 184,374 nodes
- **Element type:** Solid187 (10-node tetrahedral)
- **Modal solver:** Block Lanczos
- **Harmonic solver:** Mode Superposition (MSUP)
- **Excitation:** 1000 N harmonic load on 6 faces in Z-direction
- **Frequency range:** 0–50 Hz

## Key Results

### 1) Modal frequencies (first 20 modes)

The first four modes are near-zero rigid-body modes. First structural mode appears at **17.332 Hz**.

Representative frequencies:

| Mode | Frequency (Hz) |
|---:|---:|
| 5 | 17.332 |
| 6 | 23.767 |
| 7 | 24.903 |
| 8 | 35.873 |
| 9 | 39.547 |
| 10 | 43.561 |
| 11 | 51.600 |
| 20 | 77.771 |

### 2) Harmonic response peaks

| Response metric | Peak value | Frequency |
|---|---:|---:|
| Total deformation | 7.9579×10⁻⁴ m | 40 Hz |
| Equivalent stress (von Mises) | 3.7248×10⁷ Pa (37.248 MPa) | 50 Hz |
| Average stress | 2.3144×10⁶ Pa | Across sweep |

### 3) Fatigue and safety factor

- Fatigue setup used fully reversed loading (**R = -1**)
- Fatigue strength factor: **Kf = 0.65**
- Load scale factor: **1.5**
- Reported minimum life at resonance: **10⁻³² s** (indicates immediate crack initiation risk if continuously operated exactly at resonance)
- Yield safety factor from harmonic peak stress:

$$
FS = \frac{\sigma_{yield}}{\sigma_{max}}
= \frac{460}{37.248}
\approx 12.35
$$

## Engineering Interpretation

- The frame has a strong margin against **yielding** under the analyzed load case.
- The main design risk is **resonance-driven fatigue**, especially around ~40 Hz and as excitation approaches higher modes.
- Engine operating bands should avoid persistent excitation near identified natural frequencies.

## Source

All extracted values and conclusions are taken from:

- `/reports/ANSYS_Analysis_Report.pdf`

For condensed technical notes, see `/docs/analysis-summary.md`.
