# CADFEM-Bench v1 audit — 2026-10-13

**Verdict: useful research pilot; not ready to certify frontier models' end-to-end ability to solve complex mechanical engineering problems.** The files contain real CAD and numerical reference values, but task completion is mostly scored as numerical answer matching. The package also mixes published references with locally computed references, which conflicts with the requested published-data-only scope.

Audited package: `/Users/ayushdebnath/SVG/cadfem-bench-v1`. The package was not changed. This audit performed no FEM solves, model calls, CAD generation, or execution of downloaded geometry/solver programs. It imported existing STEP/BREP files read-only and tested the inspected numeric scoring code using temporary answer files. Source spot checks used existing publisher data in `cvpr2027/data` and existing SimJEB records in `cvpr2027/tmp`.

## Verified inventory

| Check | Observed result |
|---|---|
| Tasks / matching reference records | 168 / 168; unique IDs and aligned order |
| Tracks | A: 119 supplied-geometry tasks; B: 9 reconstruction tasks; C: 40 design tasks |
| Scored outputs | 506 scalar/Boolean outputs across 128 numeric tasks; C uses an external evaluator |
| Registry | 10 admitted collections, 73 held, 8 excluded |
| Package checksum manifest | All 267 listed files match |
| Task input manifests | All 239 input entries match SHA-256 and byte size |
| CAD inputs | 145 file instances; 116 byte-distinct files: 113 STEP/BREP, 3 `.geo` definitions |
| Independent CAD import | All 113 STEP/BREP files import; 111 pass OpenCASCADE validity, 2 fail |
| Multi-solid supplied CAD | One byte-distinct model: the four-solid thermal valve; the other 112 have one solid each |
| Explicit reconstruction geometry checks | 1 of 9 B tasks |
| Saved solver-field files in this package | No RST/RTH/FRD/ODB/VTU/VTK/H5/HDF5/NPZ files; hidden references are extracted JSON values |

Byte-distinct files are not necessarily distinct engineering geometries. Parametric variants, load cases, track variants and CAD formatting differences must not be called independent engineering families. A `.geo` file is a geometry program, not an independently imported solid in this audit.

## Findings requiring action

### 1. High — numerical answers pass without evidence of CAD construction or a FEM workflow

The actual grader accepted **127 tasks using only `results.json` files populated with the exact reference numbers**. No CAD, code, mesh, field data, refinement study or solver log was submitted. This includes **8 of 9 track B tasks**: all three B-NAFEMS tasks and all five B-FEMCAD tasks. The sole B failure was the rigging plate, which has a geometry check.

This is a controlled grader regression probe using evaluator-visible answers, not a model result or evidence that a model knows those answers. It demonstrates that the evaluator cannot distinguish solving from answer reproduction. The current built-in 127/127 oracle test has the same limitation and excludes the task requiring geometry.

Evidence: `evaluator/score.py:96`, `:110`; `scripts/cadfem_bench/build.py` oracle and self-test filtering; `answers-only-score.json` in this audit directory.

Required correction: gate workflow completion on the requested artifacts, validate B geometry against its specification, and link result quantities to the submitted mesh/field and execution record. Report numerical accuracy separately from verified workflow completion. File existence alone will not establish that the workflow produced the answer. The rigging geometry check uses only volume and sorted extents; these do not establish holes, topology, interfaces or shape equivalence.

### 2. High — 190 of 506 targets are locally computed, not source-published results

The reference class counts are: 249 published-table, 47 published-raw-field, 6 published-legend, 4 publisher-evaluator, 6 benchmark-target, 4 closed-form and **190 verifier**. The verifier targets are 152 SimJEB peak stresses plus 38 pass verdicts. They come from the existing local `simjeb_tasks.py` pipeline, which remeshes CAD and solves it; the adapter copies these values into the release.

Thus 37.5% of the targets do not satisfy the user's published-results-only requirement. The README discloses the exception, but its opening 'no FEM reference was produced for this release' and `solver_runs: 0` describe the build invocation rather than the complete provenance of its inputs. Closed-form targets also need their own category rather than being described as saved FEM results.

Evidence: `scripts/cadfem_bench/fam_simjeb.py:46`; existing workspace `cvpr2027/scripts/simjeb_tasks.py:177` and `:231`; `evaluator/references.jsonl`. No new solves were run for this audit.

Required correction: separate the locally computed SimJEB supplement from the published-results benchmark, or replace its outputs with properly defined original publisher quantities. A published-only filter would leave 316 scalar targets, but this count does **not** certify the remaining tasks or fix the other findings.

### 3. High — two supplied gold STEP models fail geometric validity

`A-SIMJEB-analysis-15` (195 faces) and `A-SIMJEB-analysis-120` (910 faces) import as single solids but fail `BRepCheck_Analyzer.IsValid()`. Identical files are also supplied in `C-SIMJEB-lighten-15` and `C-SIMJEB-lighten-120`: four task instances are affected.

Evidence: `cad-inspection.json`. Checks were made after standard STEP import with no additional repair. This does not prove every mesher will reject them; it establishes that unconditional valid-CAD admission is unsupported.

Required correction: hold the four affected task instances pending a documented defect diagnosis and repair/import policy. Retain originals and identify any repaired derivative explicitly.

### 4. High — complexity and breadth claims exceed the composition

**126/168 tasks (75%) belong to SimJEB (78), AgentFEM brackets (32), or GeoPINONet holed plates (16).** SimJEB alone supplies 342/506 targets (67.6%). Of the 13 task-family labels, four are the same SimJEB source/design domain in different task modes. Their separate weighting in an overall family macro-average also gives that domain multiple votes.

The package has useful component studies, eight wing plate variants and a four-solid transient thermal valve. The cycloidal tasks explicitly have no contact and test separate components, not a working gearbox assembly. Only the valve declares an assembly. The admitted task metadata does not provide frictional contact, plasticity, forming, crash, fatigue or coupled assembly mechanics coverage. Complexity is not determined solely by solid count, but these facts do not establish 50 diverse complex engineering problems.

Required correction: publish counts by engineering family, unique geometry, load case and track separately. Report controls and parametric families separately. Add independently specified and validated complex cases before making broad mechanical-engineering capability claims.

### 5. Medium — CADWorld's Tresca quantity is ambiguous by a factor of two

The target `max_tresca_MPa = 397.017` matches the publisher's CSV label, but examining all **100,279 rows** shows that this column is `(major principal stress - minor principal stress)/2`, i.e. maximum shear stress. The maximum full principal difference is **794.0342 MPa**. The half-difference maximum is **397.0171 MPa**, agreeing with the rounded publisher value. The rowwise relative discrepancy from the half-difference is at most about 7.21e-6.

The candidate prompt only says 'maximum nodal Tresca stress'. A solver reporting the full principal difference for Tresca equivalent stress can therefore be physically consistent and fail by 100%.

Evidence: `scripts/cadfem_bench/fam_cadworld.py:27`; publisher `evaluation_examples/fixtures/fem/freecad-fem-001.csv`; `source-spot-checks.json`.

Required correction: explicitly request maximum shear stress `(sigma1 - sigma3)/2`, retaining 397.017 MPa, or explicitly define the full-difference quantity and use the corresponding original-field extraction. Do not silently mix conventions. The case also has 31.145 mm displacement for a 260 mm overall part and a small-displacement linear formulation; it should be described as reproducing that source model, not a validated physical strength assessment.

### 6. Medium — track C cannot run from this folder alone

All 40 design tasks need `scripts/simjeb_bench.py`, its solver environment, grading dependencies and human reference data. These are not packaged under `cadfem-bench-v1`. The README acknowledges using the surrounding project. `evaluator/score.py:90` only imports the success flag and score from an external JSONL record keyed by task ID; it does not execute FEM or verify a submission hash, model/run identity or environment.

Required correction: supply a pinned evaluator environment and dependencies, and bind trusted evaluator results to the exact submission hash and run ID. Treat the imported JSONL as trusted evaluator output, not candidate input. Do not describe this folder as a standalone runnable design benchmark.

### 7. Medium — one malformed submission crashes the complete scoring run

Replacing one answer with valid JSON `{"outputs": null}` makes the scorer exit with `AttributeError: 'NoneType' object has no attribute 'get'` at line 107. The included JSON schema is not enforced by the scorer.

Required correction: validate record and output types, reject invalid values per task, and continue scoring the remaining tasks. Preserve strict numeric/Boolean handling and return structured validation errors.

### 8. Medium — 'gold' does not establish independent FEM validation

The stated checks test hashes, selected values and oracle arithmetic. They do not demonstrate independent reproduction of each source setup, convergence, solver-version equivalence or justified tolerances. The AgentFEM adapter expressly notes the source's 9 mm mesh is unconverged. Rigging uses a missing material card and figure-defined supports; its silver tier is appropriate as a limitation, but assumptions about remote coupling and stabilization remain model-defining choices. Wing references use shell idealizations while candidate geometry is solid CAD.

The SimJEB README says the verifier reproduces fields exactly on the source mesh. That claim must not be extended to the remeshed references: existing local-versus-published displacement pairs differ by up to **7.6662%** across 152 load cases (all within the stated 10% tolerance). This is an existing-data comparison, not an independent solver validation. Its same-source-mesh exactness claim was not independently tested here.

The evaluator package also lacks the raw publisher fields/decks supporting its extracted values and a self-contained, pinned source-to-reference mapping. Many are available elsewhere in this workspace, but path descriptions in JSON alone do not make the release reproducible.

Required correction: retain original files in an evaluator-only evidence bundle, record source revisions/hashes and extraction locators, and distinguish 'source-backed pilot' from 'independently reproduced'. Justify each tolerance against source precision, model idealization and mesh effects.

## What is useful now

The candidate/evaluator separation, per-input hashes, explicit units, provenance classes and held-source registry are good foundations. Supplied geometry is real, and most imported STEP/BREP files pass validity. The strongest variety in the admitted set comes from the thermal valve, cycloidal components, modal wing plates and rigging drawing; these are worth retaining with accurate readiness labels. Public answers and source URLs imply contamination risk; restrictions on browsing do not prove a model has not previously seen a source.

Use this release for **exploratory numerical-answer evaluation** with clearly reported limitations. Do not interpret its current pass rate as proof of CAD reconstruction, FEM execution or broad complex-engineering competence. This audit does not certify any task as independently solved and validated.

## Evidence and reproduction

- `audit.py`: package hashes, counts, exact-file deduplication, scalar-only scorer probe, malformed JSON probe and read-only CAD import. Run from the workspace root with `cvpr2027/tmp/cq-env/bin/python cvpr2027/output/audits/cadfem-bench-v1/audit.py`.
- `audit-results.json`: machine-readable findings and task lists.
- `cad-inspection.json`: per-file OpenCASCADE results and all task instances.
- `answers-only-score.json`: full controlled scoring probe; not model performance.
- `source-spot-checks.json`: original CADWorld scalar convention and existing SimJEB displacement comparisons.
- `figure-review.png`: review contact sheet of the seven B-FEMCAD input figures. These and the CADWorld task image were inspected; no numerical answer legend was observed in those inspected images. This was not an exhaustive image/PDF leakage audit.

Primary source pages spot-checked online: [CADWorld](https://github.com/Zdong104/CADWORLD), [AgentFEM Bracket Elasticity](https://huggingface.co/datasets/HaomingLuo/AgentFEM-Bracket-Elasticity), [FeenoX valve tutorial](https://www.seamplex.com/feenox/doc/tutorials/320-thermal/). Source correctness conclusions above rely on the identified package and local original-file checks; online existence alone was not treated as validation.
