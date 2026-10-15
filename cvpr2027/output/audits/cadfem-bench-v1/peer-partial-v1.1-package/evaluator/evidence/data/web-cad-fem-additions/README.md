# Published CAD and FEM source collection: 169 additions

Downloaded original web assets. No local engineering geometry, problems, physics assumptions or FEM reference results were generated. CAD PNGs are inspection renders of original CAD; numerical summary maxima are read/calculated from original reference fields.

- 80 GeoPINONet lug STEP instances, each with two ANSYS reference CSVs.
- 80 GeoPINONet holed-plate STEP instances, each with two ANSYS reference CSVs.
- 8 UCSM STEP/mesh/LS-DYNA strain pairs, two examples from each of four families.
- 1 nonlinear anisotropic tricuspid-valve IGES/Rhino geometry + Abaqus model/results, original dimensioned figures, ASCII/VTK/ODB files.

These are 169 CAD/reference pairs in seven families, not 169 different complex engineering task types. Zero new certified benchmark admissions; no frontier model calls or solver replay were run. Only the valve has verified original dimensioned figures in this addition. Other CAD views are not dimensioned drawings.

## Where are CAD and FEM?

`catalog.json` links every source pair to its CAD file and its results. `geopinonet/cad/` contains extracted unmodified STEP members. Original full ZIP archives under `geopinonet/` hold reference CSVs and fixed/loaded surface STL files. Exact CSV ZIP-member names are in each catalog record. CSV fields: x,y,z,ux,uy,uz,sxx,syy,szz,sxy,syz,sxz. CAD bounds (mm) and FEM coordinates (m) agree in all 160 pairs. All 320 reference CSVs contain finite values (17,376,822 total rows).

`ucsm/` contains eight original STEP, OFF mesh and major/minor true-strain JSON triplets. Download manifest includes source archive, exact member, verified member CRC32 and local SHA256. Large source archives were fetched selectively via standard HTTP ranges. One face in 1119_uc3 lacks a strain row (21,632 of 21,633); no missing value is filled. Original solver input/material cards are not supplied here; do not claim deterministic replay readiness.

`valve/Idealized_Geometry/` contains original IGES (a shell surface and curves, not a solid) and Rhino geometry. Original complete `valve/original-supplement.zip` contains five result frames, source VUMAT, solver decks, postprocessing code, ASCII fields, VTK fields and ODB. Five frames are one source problem. Original dimensioned figures 1/2 are included. Original replay requires Abaqus; reading TXT/VTK does not.

## Qualification issues

GeoPINONet source README says holed-plate thickness 20 mm; all downloaded plate STEP and FEM bounds agree on 10 mm. This discrepancy is flagged per record. Source config uses steel E=2e11 Pa, nu=0.3, and demo source documents a 1000 N reference load, but force/BC semantics still need task-by-task benchmark review. Avoid mesh-dependent peak stress scoring without tolerances and convergence evidence.

Published FEM values are reference outputs, not frontier-model scores. Keep supplied-CAD-to-FEM and drawing-to-CAD-to-FEM evaluations separate. Do not expose reference CSV/strain/result fields to a model attempting a held-out FEM task. Source training/validation partitions are preserved; public-data contamination remains possible.

## Source attribution and licenses

All three source collections specify CC BY 4.0. Preserve author attribution and source URLs.

- Vicente Urrutia Valdes, Ivan La Fe-Perdomo, Angel Rodriguez Soto. GeoPINONet. https://zenodo.org/records/21483341 ; https://github.com/v-urrutiav/GeoPINONet . Original source archive and Zenodo metadata preserved.
- Tobias Lehrer, Philipp Stocker, Fabian Duddeck, Marcus Wagner. UCSM. https://zenodo.org/records/15327950 . Publication https://doi.org/10.1016/j.cad.2025.103924 . Published static implicit inverse analysis estimates strain, not a full contact/forming trajectory.
- Devin W. Laurence, Chung-Hao Lee, et al. An in-silico benchmark for the tricuspid heart valve. https://doi.org/10.1016/j.dib.2021.107664 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC8668829/ . Source supplementary CC BY 4.0 statement preserved in article.xml.
