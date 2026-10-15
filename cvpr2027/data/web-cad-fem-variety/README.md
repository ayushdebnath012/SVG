# Additional web CAD/FEM varieties

Five original source collections, five problem families. CAD and reference files are downloaded from publishers; no geometry, FEM solution or model answer generated. Inspection images render original CAD only. No COMSOL files. No frontier model calls or solver runs.

## What was collected

| Family | Original CAD | Published numerical reference | Status |
|---|---|---|---|
| Hip replacement contact / cement fixation | Six IGES component files | CSV peak cup stress, bearing pressure, cement stresses in MPa | Four wear states have corresponding 40 mm / 45 degree component CAD; one supplied solver setup |
| HIRENASD wing vibration | IGES surface CAD | Ten mode-shape fields, 159,841 nodes each | Modal references; not forced-response/stress fields |
| Turbine mock-blade dovetail | STEP assembly + blade + slot; IGES alternatives | 1968 x 1968 FE mass matrix, 16 stiffness matrices, connectivity | Reduced FE operators, not solved response references |
| Fokker F28 crashworthiness | Three STEP surface variants, paired Abaqus decks | Published acceleration and DRI plots | Plot references; automatic numerical scoring pending digitization |

See catalog.json for source URLs, attribution, license and per-family blockers. Original source files are unchanged; matched-reference-values.json and the five-row excerpt copy published values only. The original hip CSV includes other sizes/angles whose native CAD is not supplied. Do not count those as additional CAD-paired cases. Modes, preloads and frame counts do not increase the number of task families.

## WAAM addition (12 October 2026)

Original STEP wall/baseplate and material/procedure files from https://zenodo.org/records/17608626 (CC BY 4.0) added. Original selected VMAP archive members were downloaded by HTTP ranges, decompressed without changing values and verified against the source ZIP CRC. M1 thermal: 6000 states x 14994 element temperatures. M1 distortion: 115 states with nodal displacement, temperature, stress, strains, force and PE fields. M2 thermal: 5000 states x 12256 element temperatures, retained as a held geometry variant because printed height differs from nominal CAD. Two new subtask types share one nominal CAD design.

Temperature fields have finite values; M1 range 300-1654.91, M2 300-1502.00. VMAP system declares SI, but variable unit IDs are -1. Distortion coordinates match CAD in mm despite a declared SI unit system; raw displacement/stress units and tensor ordering need review. No original executable solver deck was verified. M1 CAD/mesh registration is provisional; M2 is not a verified exact CAD/result pair. No new certified benchmark admission.

## Validation

All selected STEP and IGES geometries import and pass OpenCascade validity checks. Hip pelvis/cement, wing and fuselage are surfaces, not closed solids. Turbine assembly contains three solids. Ten modal arrays contain finite data; each has 159,841 seven-column nodal rows (x,y,z,node-ID,three mode components). Modal-coordinate bounds agree with IGES extents after converting mm to m; this alone does not prove complete registration. Blade matrices, connectivity and preload entries are finite; the mass matrix is symmetric. ZIP source archives pass CRC checks. Download manifests and package-manifest.json record SHA-256.

## Benchmark readiness

Zero new certified admissions. WAAM thermal/distortion candidates also need exact setup, frame and unit review. Hip scalar results are the closest addition to direct numerical scoring; executable wear-state mapping and convergence tolerances remain to audit. Wing modal comparison needs frame, normalization and mode pairing. Blade matrices support reduced-operator evaluation; experimental response is separate and not mislabeled as FEM. Crash plots need digitization with uncertainty. No verified dimensioned drawing in these five sources; supplied original geometry and CAD inspection views support the CAD-input track, while the drawing-input track remains incomplete.

## Rejected or quarantined leads

PHASMA satellite thermal repository: STEP/Elmer setups found, but no published solved temperature arrays verified. Machine-tool thermal data: numerical temperature references found but matching native CAD missing. Metal/resin lattice data: FEM pull-force spreadsheets but native CAD missing. CADWORLD: three FreeCAD/result-CSV cases downloaded in the research cache; excluded from this package pending stress-unit and elastic-validity review (source claims up to terapascal stresses). Mesh-only sources and COMSOL datasets excluded.

## License and attribution

Hip: Hua and Jin, University of Leeds, DOI 10.5518/13, CC BY 4.0. Blade: Botto and Glorioso, DOI 10.17632/xkssd7gr92.1, CC BY 4.0. F28: Desiderio et al., TU Delft, DOI 10.5281/zenodo.7724227, CC BY 4.0. NASA HIRENASD: public distribution; dataset-specific license not stated on inspected pages, retained as unresolved. License link: https://creativecommons.org/licenses/by/4.0/ .
