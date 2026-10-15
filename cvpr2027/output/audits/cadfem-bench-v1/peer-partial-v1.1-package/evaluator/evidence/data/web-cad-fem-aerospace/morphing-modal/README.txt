================================================================================
README for dataset: Experimental and numerical data from comparative analysis
of candidate structural models for active camber morphing wings
================================================================================

Authors: Ke Huang, Jiaying Zhang
Corresponding author: Jiaying Zhang (jiaying.zhang@buaa.edu.cn)
Repository: Mendeley Data
DOI: [10.17632/8jxw5533py.1]

Last update: 2026-06-01

================================================================================
1. OVERVIEW
================================================================================

This dataset supports the Data in Brief article "Experimental and numerical
data from comparative analysis of candidate structural models for active
camber morphing wings" and the companion research article [1]. It contains:

- Modal test data for 10 uniform and 20 stepped cantilever plates
  (FDM-printed PLA and CNC-machined aluminum)
- Raw frequency response spectra from scanning laser Doppler vibrometry
- Material characterization (tensile tests on 21 PLA specimens, 7 orientations)
- Manufacturing tolerance measurements (25 calibration cubes + specimen dimensions)
- Finite element model files (ABAQUS and Nastran)
- 3D CAD models (STP format)
- Modal shape animations (video files)

[1] K. Huang, J. Zhang, Comparative modal analysis of beam-plate coupled models
    for isotropic active camber morphing wings, Aerospace Science and Technology
    178 (2026) 112449.

================================================================================
2. FILE AND FOLDER STRUCTURE
================================================================================

Root directory:
│
├── 1-1 Modal Test Experiment and Numerical Results.xlsx
├── 1-2 Original data of modal tests.xlsx
├── 2-1 Tolerance inspection of FDM 3D printer.xlsx
├── 2-2 Specimen tolerance.xlsx
├── 3-1 Material property.xlsx
├── 3-2 Original data of material tests.xlsx
├── 4-1 FEM Detail.xlsx
├── ABAQUS inp Files/
├── Nastran bdf Files/
├── FDM Stp Files/
├── Modal Animation Video Files/
└── README.txt (this file)

================================================================================
3. EXCEL FILE DESCRIPTIONS
================================================================================

3.1 1-1 Modal Test Experiment and Numerical Results.xlsx
--------------------------------------------------------
Contains modal frequencies (Hz) and nondimensional frequencies for all specimens.

Worksheets:
- "Uniform": uniform cantilever plates (AR=1.8,2.5,5.0)
- "Stepped": stepped cantilever plates (AR=3,4,5,6; fef=25%,50%,75%)
- "Comparison_lit" (optional): comparison with literature (if present)

Columns include:
- Specimen ID, mode number, mode type (B/T/FB)
- Experimental frequency (mean ± SD, from 3 replicates)
- Numerical frequencies for each model type:
    * Uniform: EB, SB, TP, SP, SD
    * Stepped: BB, BP, PP
- Dimensionless frequency ratio λ = Ω_num/Ω_exp
- Relative error (%) = (λ - 1)*100

Units:
- Frequency: Hz
- Nondimensional: dimensionless

3.2 1-2 Original data of modal tests.xlsx
----------------------------------------
Raw frequency response spectra from Polytec PSV-400.

Columns: Frequency (Hz), Vibration velocity magnitude (m/s), Phase (degrees)
Each worksheet corresponds to one test specimen (Test X-Y).

3.3 2-1 Tolerance inspection of FDM 3D printer.xlsx
---------------------------------------------------
Dimensional accuracy assessment using 25 calibration cubes (20 mm edge).

Columns:
- Cube number
- Measured X, Y, Z dimensions (mm)
- Deviation from nominal (mm)
- Mean, standard deviation, and CV (%) for each axis

3.4 2-2 Specimen tolerance.xlsx
-------------------------------
Actual measured dimensions of every test specimen.

Columns:
- Specimen ID
- Nominal dimensions (mm)
- Five independent measurements per specimen (mm)
- Mean, tolerance (max-min), and dimensional error (%)

Used to correct nominal dimensions in FE models.

3.5 3-1 Material property.xlsx
------------------------------
Mechanical properties of 3D-printed PLA for each print orientation.

Print orientations: X-flat, X-on-edge, Y-flat, Y-on-edge, 45°-flat, 45°-on-edge, Z-upright.

Columns:
- Maximum tensile strength (MPa) – mean ± SD
- Elastic modulus (MPa) – mean ± SD
- Coefficient of variation (CV%) for each orientation

Also includes overall mean and SD across all 21 specimens.

3.6 3-2 Original data of material tests.xlsx
--------------------------------------------
Raw uniaxial tensile test data for 21 specimens.

Each worksheet corresponds to one specimen (orientation + replicate number).

Columns:
- Force (N)
- Crosshead displacement (mm)
- Extensometer deformation (mm)
- Engineering stress (MPa) = Force / initial cross-sectional area
- Engineering strain (mm/mm) = Extensometer deformation / gauge length

3.7 4-1 FEM Detail.xlsx
-----------------------
Summary of finite element model details.

Columns:
- Model type (EB, SB, TP, SP, SD for uniform; BB, BP, PP for stepped)
- Element type (B33, B32, S8R5, S8R, C3D8R, CBEAM, CQUAD4, etc.)
- Number of elements, nodes, and degrees of freedom
- Computation time (s) on Intel i7-12700 (two cores) / Patran default
- Maximum error (%) for bending and torsion modes (first 5 or 6 modes)

================================================================================
4. FOLDERS
================================================================================

4.1 ABAQUS inp Files
--------------------
Finite element input files for uniform cantilever plates (Abaqus/Standard 2024).

Naming: AR(X)_(Y).inp, where X = aspect ratio (1.8,2.5,5.0), Y = model type
(EB, SB, TP, SP, SD). Solid element models include mesh size in name.

All models use element size 0.5 mm. Boundary conditions: fixed at root face
(UX=UY=UZ=RX=RY=RZ=0).

4.2 Nastran bdf Files
---------------------
Finite element input files for stepped cantilever plates (Nastran 2020).

Naming: AR(X)fef(Y)(Z)Model.bdf, where X = AR, Y = fef (25,50,75), Z = model type
(BB, BP, PP). Element size 0.5 mm. Rigid connections between rigid and flexible
sections use RBAR elements.

4.3 FDM Stp Files
-----------------
3D CAD models (STEP format) of all specimens used for FDM printing and CNC machining.

Files: Test_X.stp, where X = specimen index (1-9, see Table 1 in the manuscript).
Also includes: XYZ Calibration cube.STEP, ASTM D638-22_TYPE1_Test Specimen.STEP.

4.4 Modal Animation Video Files
-------------------------------
Animated mode shapes (MP4 format) for all tested specimens.

Subfolders: "Uniform cantilever plate" and "Stepped cantilever plate".
Naming: AR(X)_(Y)(Z).mp4 (uniform) or AR(X)fef(K)_(Y)(Z).mp4 (stepped),
where X = AR, K = fef, Y = mode order, Z = mode type (B, T, FB).

================================================================================
5. SOFTWARE AND VERSIONS
================================================================================

- 3D printing slicing: Bambu Studio (version not recorded, but settings provided)
- FDM 3D printer: Bambu X1C
- CNC machining: standard 3-axis mill (6061 aluminum)
- CAD: Solidworks 2024
- Material testing: SUNS UTM4503 (load cell accuracy 0.03, extensometer 2mV/V)
- Modal testing: Polytec PSV-400 with PSV-I-400 MR head, software PSV 9.0
- Finite element (uniform plates): Abaqus/Standard 2024
- Finite element (stepped plates): Nastran 2020 with Patran pre-processor
- Post-processing: Microsoft Excel

================================================================================
6. VARIABLE DEFINITIONS (common abbreviations)
================================================================================

AR = aspect ratio
fef = flexible segment ratio (%)
BB = beam-beam model
BP = beam-plate coupled model
PP = plate-plate model
B  = spanwise bending mode
T  = torsion mode
FB = chordwise bending mode
EB = Euler beam (Abaqus B33)
SB = shear beam (Abaqus B32)
TP = thin shell (Abaqus S8R5)
SP = thick shell (Abaqus S8R)
SD = solid element (Abaqus C3D8R)
CBEAM = Nastran beam element
CQUAD4 = Nastran quadrilateral shell element
DOF = degree of freedom
CV = coefficient of variation (%)
E = Young's modulus (GPa or MPa)
σ = stress (MPa)
ε = strain (mm/mm)
ρ = density (kg/m³)
ν = Poisson's ratio
Ωu = nondimensional angular frequency for uniform plate
Ωs = nondimensional angular frequency for stepped plate
λ = frequency ratio (numerical / experimental)

================================================================================
7. CONTACT AND CITATION
================================================================================

If you use this dataset, please cite:
[1] K. Huang, J. Zhang, Experimental and numerical data from comparative
    analysis of candidate structural models for active camber morphing wings,
    Data in Brief, 2026, DOI: [10.17632/8jxw5533py.1]

For questions, contact: jiaying.zhang@buaa.edu.cn

================================================================================
END OF README
================================================================================