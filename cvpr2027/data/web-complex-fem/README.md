> Benchmark admission audit: only 3 of these 100 source cases are admitted to a source-complete calibration pilot (6 track tasks); none has certified pass/fail scoring. See [audited pilot](../published-fem-pilot-v1/README.md).

> Current 100-case web-sourced collection: see [PUBLISHED-100.md](PUBLISHED-100.md) and [published-100.json](published-100.json). COMSOL-dependent legacy records below are not included. The collection has 100 geometry-result pairs, but only four verified dimensioned illustrations and incomplete realized loads in the 61 SFEM cases.

Included dataset records: **2 published cases** in cases.jsonl: perforated muffler (FEMCAD-ADV-005) and temperature-dependent pressure-vessel plasticity (FEMCAD-ADV-010). Downloaded assets include 6 drawings, 2 native geometry models and 2 solved FEM models. Original figures and documentation are stored in tmp/published-mechanical-cases; manifests preserve source URLs and SHA256 hashes. COMSOL field export and scoring tolerances remain pending.

Active scope: **broad mechanical engineering source collection**, across 11 task families and 50 existing published source studies. See broad-mechanical-collection.json. This is a discovery inventory, not 50 ready-to-score tasks; current diverse solver coverage is COMSOL and needs expansion.

Supplementary dataset: **DeepJEB**, pinned to revision `160424ca2a5095315ff9ead8a5fc36d2667fd3c6`. Original scalar results downloaded for all 2,138 designs. Design `10_30` has a locally downloaded, imported STEP shell geometry (no solid; volume-meshing readiness unverified) matched to its published FEM row. See selected-dataset.json for verified files and remaining preparation.

Existing web data with complex engineering geometry and FEM results

The current scope requires source-published geometry/drawings, source-defined physics, and existing FEM output. No numerical reference solutions or new problem prompts are generated. Model trials remain pending.

| Source | Geometry | Existing FEM output | Current verification |
|---|---|---|---|
| [DeepJEB](https://huggingface.co/datasets/KAIST-SmartDesignLab/DeepJEB) | 2,138 complex brackets; STEP, tetrahedral meshes, multiview images | Scalar CSV and nodal fields; solver decks | Official file inventory and README verified; large archives not downloaded |
| [DeepJEB++](https://huggingface.co/datasets/KAIST-SmartDesignLab/DeepJEB-PP) | 15,360 bracket surface meshes, boundary-condition indices | Four load cases: displacement and von Mises stress; max displacement, p95 and max stress | Full original label CSV downloaded: 15,360 unique design records; metadata defines units and loads |
| [DDACS](https://doi.org/10.18419/DARUS-4801) | Parameterized sheet-metal/tool geometries; forming and cutting stages | Stress, strain, thickness, displacement, springback in HDF5 | Original release v3 inventory verified; small original sample download tracked in tmp |
| COMSOL source studies | Cooled turbine stator, compound gears, perforated muffler, stent, composite wheel rim, composite blade, gearbox | Source-published solved models and documentation plots | Prior audit verified binary mesh and solution archive entries; quantitative fields require COMSOL export |

For varied, complex designs, prioritize the seven COMSOL studies in catalog.json. DeepJEB adds scale but remains bracket-specific. DDACS adds nonlinear contact, plasticity and manufacturing behavior but one parameterized geometry family.

Drawing availability is a separate requirement: STEP files, surface meshes and multiview rendered images are not automatically dimensioned 2D engineering drawings. None of the three large datasets above has been verified to provide dimensioned drawings paired with FEM labels. CADGenBench has drawing-to-CAD inputs, but associated archived FEM outputs have not been verified. CADEngBench is a paper lead; do not claim its dataset is downloaded or available until a release is verified.

Published FEM quantities are reference labels, not Astra performance scores. COMSOL archive presence is not independent convergence certification. No scoring thresholds have been invented.

Original source bytes and download hashes: ../../tmp/web-complex-fem/download-verification.json. Exact COMSOL assets and prior verification are retained in catalog.json. Raw source data stay outside the tracked catalog.
