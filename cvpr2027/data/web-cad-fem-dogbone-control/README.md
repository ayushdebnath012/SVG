# Steel-Dogbone-Specimen--fatigue-static-structural-and-buckling-FEA
FEA study of a steel dogbone specimen in ANSYS Workbench 2025 R2. A 50 MPa compressive load was applied to one fixed end to evaluate static stress, fatigue life (1M cycles), and eigenvalue buckling across three linked analyses. Geometry and workflow based on a YouTube tutorial.
# Steel dogbone specimen — fatigue, static structural & buckling FEA

FEA study of a steel dogbone specimen in ANSYS Workbench 2025 R2. A 50 MPa 
compressive load was applied to one fixed end to evaluate static stress, fatigue 
life (1M cycles), and eigenvalue buckling across three linked analyses. 
Geometry and workflow based on a YouTube tutorial.

## Specimen geometry
| Parameter        | Value  |
|------------------|--------|
| Length           | 38 mm  |
| Width (ends)     | 15 mm  |
| Width (waist)    | 5 mm   |
| Fillet radius    | 3 mm   |
| Fillet position  | 8 mm from each end |
| Thickness        | 3 mm   |
| Material         | Structural steel (ANSYS default) |

## Boundary conditions
- Fixed support: bottom face
- Applied load: 50 MPa pressure on top face

## Analyses performed
1. **Static structural** — von Mises stress, total deformation, safety factor
2. **Fatigue** — life, damage, and safety factor at 1,000,000 cycles
3. **Eigenvalue buckling** — 3 modes extracted from pre-stressed state

## Key results
| Analysis | Result                  | Value   |
|----------|-------------------------|---------|
| Buckling | Mode 1 load multiplier  | 0.78173 |
| Buckling | Mode 2 load multiplier  | 2.0094  |
| Buckling | Mode 3 load multiplier  | 5.7321  |

> Mode 1 multiplier < 1 means the specimen buckles before reaching the full 50 MPa load.

## Mesh details
| Parameter       | Value         |
|-----------------|---------------|
| Element size    | 0.5 mm        |
| Mesh method     | Automatic     |
| Element type    | Tetrahedral   |
| Relevance       | Fine          |
## Results summary

### Static structural
- Max equivalent (von Mises) stress: 216.89 MPa 33.11MPa below yield strength of structural
  steel (250 MPa), confirming no static failure
- Max total deformation: 1 mm (at loaded end)
- Min safety factor: 1.1527  

### Fatigue (1,000,000 cycles)
- Min fatigue life: 19101  cycles
- Fatigue safety factor: 0.39743  
- Critical location: fillet root at the waist transition (stress concentration zone)

### Eigenvalue buckling
- Negative load multiplier option was turned off during setup to extract only
  physically meaningful compressive buckling modes
- Mode 1 load multiplier: 0.78173 — critical finding, specimen buckles at only
  78% of the applied 50 MPa load before full load is reached
- Mode 2 load multiplier: 2.0094
- Mode 3 load multiplier: 5.7321
- Max total deformation (Mode 3): 0.88889 mm (normalized, not absolute)

### Overall conclusion
Buckling is the governing failure mode for this specimen geometry under
the applied compressive load. The slender waist (5mm) makes it highly
susceptible to lateral buckling before stress-based or fatigue failure occurs.
## Software
ANSYS Workbench 2025 R2 — Student Edition

## How to open
1. Download `ansys_files/dogbone_analysis.wbpz`
2. Open ANSYS Workbench → File → Restore Archive
3. Pick a working directory and solve
