# CADFEM-Bench v1.0

The final CAD + FEM benchmark for frontier AI models, assembled on 2026-10-13 from every CAD/FEM source collected in this project. **168 tasks, 506 graded numerical outputs, 13 task families, 10 admitted source collections.** A further 73 held and 8 excluded collections are listed with their blockers in `registry.jsonl`. No FEM reference was produced for this release and no model has been run on it.

## Tracks

- **A** - Supplied CAD -> FEM: the model receives the part/assembly CAD and the source analysis set-up and must compute the requested results.
- **B** - Specification/drawing -> CAD -> FEM: the model receives a drawing or written specification, must build the CAD itself and then run the analysis on its own model.
- **C** - Design under FEM verification: the model must design or modify a part; the benchmark FEM grader decides validity, pass/fail and mass.

## Tiers

- **gold**: open CAD (STEP/BREP) or a complete specification, fully stated set-up, reference from a saved solver result, a publisher table/CSV, a publisher evaluator, a closed form, or the validated SimJEB grader.
- **silver**: reference read from a published result legend; part of the set-up is given by the source's own boundary-condition figure. Reported separately.
- **control**: public NAFEMS benchmarks; they calibrate the harness and may be answerable from memory.

## Error policy

Tasks with a known error in their source data were fixed where the fix is verifiable and left out otherwise. Fixed: AgentFEM STEP files (metre values under a mm header) are shipped scaled to true mm and checked against the FEM nodes; GeoPINONet boundary conditions are stated from the verified fields (the archive's fixed/load STL names are swapped). Left out: DeepWheel (CAD/CSV mass mismatch, unknown density), CADWorld 002 (singular edge support) and 003 (811 mm displacement of a 30 mm specimen), rigging-plate tests 4 and 5 (conflicting load labels, revised results), cycloidal stress outputs (source error estimate 11-49 %), and 13 SimJEB redesign/lighten tasks without a passing human design proving feasibility. Every decision is in `registry.jsonl`.

## Composition

| family | track | tier | tasks | graded outputs | geometry | physics | reference classes | licence |
|---|---|---|---:|---:|---|---|---|---|
| agentfem-bracket | A | gold | 32 | 64 | Double-arm support bracket family | linear static | published_table | CC BY 4.0 |
| cadworld-freecad-fem | A | gold | 1 | 4 | Multi-feature aluminium part | linear static, mesh protocol | publisher_evaluator | Apache-2.0 (publisher HF metadata) |
| cycloidal-drive-components | A | gold | 15 | 15 | Cycloidal gearbox parts (PETG-CF, steel pins) | linear static | published_raw_field | No repository license; FCStd metadata 'A |
| feenox-valve-transient | A | gold | 1 | 6 | Power-plant valve, carbon + stainless | nonlinear transient thermal | published_table | GPL-3.0 |
| geopinonet-holed-plate | A | gold | 16 | 32 | Steel plate with a through hole | two static load cases | published_raw_field | CC BY 4.0 |
| morphing-wing-plates | A | gold | 8 | 24 | Uniform/stepped PLA morphing-wing plates | modal | published_table | CC BY 4.0 |
| nafems-calibration | A/B | control | 6 | 6 | NAFEMS LE1/LE10/LE11 | plane stress, 3-D static, thermoelastic | benchmark_target | GPL-3.0-or-later (examples) |
| rigging-plate | A/B | silver | 6 | 6 | 7075-T6 rigging plate (5 load tests, drawing) | linear static, figure-specified BCs | published_legend | CERN-OHL-S-2.0 |
| simjeb-analysis | A | gold | 38 | 342 | GE jet-engine bracket, real competition designs | 4-case linear static | published_table, verifier | Dataverse CC0 / README ODC-By; GE bracke |
| femcad-hard | B | gold | 5 | 7 | Capacitor shell, L-bracket, pressure hull, holed plate, heated tube | electrostatics, static, thermal | closed_form, published_table | Wolfram documentation (copyright Wolfram |
| simjeb-design | C | gold | 15 | 0 | GE bracket from specification (incl. material/load variants) | design, 4-case static | SimJEB grader | Dataverse CC0 / README ODC-By; GE bracke |
| simjeb-lighten | C | gold | 19 | 0 | Passing GE bracket designs | remove >= 15 % mass, still pass | SimJEB grader | Dataverse CC0 / README ODC-By; GE bracke |
| simjeb-redesign | C | gold | 6 | 0 | Failing GE bracket designs | redesign to pass, mass cap | SimJEB grader | Dataverse CC0 / README ODC-By; GE bracke |

## Reference policy

References are values published by the source: maxima of the source's own saved result files (CalculiX FRD, ANSYS/FEM CSV), cells of publisher spreadsheets or CSVs, values checked by the publisher's own evaluator, closed-form solutions, or NAFEMS targets. One exception is labelled `verifier`: for SimJEB analysis tasks the peak stress outside 2 mm of the bolt and pin walls and the pass verdict are not published, and come from the benchmark's FEM grader, which reproduces SimJEB's published OptiStruct fields exactly on SimJEB's mesh; SimJEB's published displacements are used directly.

Every reference record carries its provenance (file, column, cell or legend). Classes in this release: published_table 249, verifier 190, published_raw_field 47, benchmark_target 6, published_legend 6, publisher_evaluator 4, closed_form 4.

## Tolerances

Relative error |pred - ref| / |ref| unless stated. Defaults (gold): displacement, frequency, temperature, force 5 %; stress 10 %. Silver: 10 % / 20 %. A source's own tolerance overrides the default: CADWorld 5 %, SimJEB 10 % displacement / 15 % stress, FEMCAD-Hard 1 % (closed forms). Legend peak stresses at load edges (rigging plate) get 20 %; temperatures in transients are graded on the rise above the initial state; through-wall temperature differences get 10 %. The pass verdict is exact.

## Scoring

A task passes when all graded outputs are within tolerance (and, for the track B rigging task, the submitted part matches the source CAD volume and extents within 2 %). Report the pass rate per track and tier and the **family macro-average** so that large parametric families (SimJEB, AgentFEM, GeoPINONet) do not dominate. Track C uses the SimJEB harness verdicts (valid, passes, mass limit; design tasks also report the share of human designs beaten).

```
python evaluator/score.py --refs evaluator/references.jsonl --submissions runs/<model> --simjeb-results results.jsonl --out score.json
```

Grader self-test at build time: the exact references pass 127/127 numeric tasks; references scaled by 1.3 pass 0.
Leak scan: no reference number appears in any prompt or text input (0 hits). Image inputs were reviewed by eye: problem and boundary-condition figures only.

## Held and excluded sources

73 collections are held: they contain real CAD and FEM data, but a specific blocker would make a graded answer ambiguous. The most common blockers:

- CAD only in a proprietary native format: 19
- supports/loads/materials not recoverable as CAD-face set-up: 19
- conflicting or unmatched source references: 18
- no deterministic, mesh-independent numerical reference: 8
- no B-rep CAD (mesh, scan or paper geometry only): 5
- needs a proprietary solver/material model to define the problem: 4

Largest held pools that could become tasks with further work: Code_Aster validation cases (50 cases, 761 checks; prompts must be transcribed from the V-documents and geometry built from their figures), SFEM (61, needs realised loads), Bath auxetics (18, Inventor CAD), GeoPINONet lugs (80, bore-load distribution).

## Limitations

- All sources are public; a model may have seen them. NAFEMS tasks are calibration only.
- Several references come from unconverged source meshes (flagged per task); tolerances absorb typical discretisation differences, not modelling errors.
- Licences differ: some sources are CC BY / Apache / GPL, others carry no licence and are for local research only (`source.redistributable` is false). Do not publish the candidate package as a whole.
- No frontier-model results yet.

## Files

- `candidate/` (give to the model): `tasks.jsonl`, `tasks/<task_id>/` inputs, `README.md`, `submission.schema.json`.
- `evaluator/` (keep hidden): `references.jsonl`, `registry.jsonl`, `score.py`, `validation.json`, this card.
- Builder: `cvpr2027/scripts/cadfem_bench/` (`build.py` and one adapter per source family).

## Folder layout

| path | contents | who sees it |
|---|---|---|
| `candidate/tasks.jsonl` | one task per line: prompt, input files, output keys and units, source and licence | model |
| `candidate/tasks/<task_id>/` | CAD (STEP/BREP), `faces.json` face descriptors, drawings, boundary-condition figures, property tables | model |
| `candidate/README.md`, `candidate/submission.schema.json` | rules and answer format | model |
| `evaluator/references.jsonl` | hidden reference values, tolerances, provenance, flags | grader only |
| `evaluator/registry.jsonl` | every collected source: admitted / held / excluded with its blocker | grader only |
| `evaluator/score.py` | grader (numeric outputs, track B geometry check, SimJEB verdict merge) | grader only |
| `evaluator/validation.json` | build checks: hashes, leak scan, grader self-test | grader only |
| `report/cadfem-bench-v1.pdf` | composition, policies, one page per family, source registry | everyone |
| `scripts/cadfem_bench/` | builder (`build.py`, one `fam_*.py` per source family), `report.py`, `package.py` | maintainers |
| `SHA256SUMS.txt` | SHA-256 of every file | everyone |

## Quick start

1. Give a model only `candidate/` (or one `candidate/tasks/<task_id>/` folder plus its line of `tasks.jsonl`).
2. Collect answers as `runs/<model>/<task_id>/results.json` = `{"outputs": {key: value}}`; tracks B and C also `part.step`.
3. Track C: run `python scripts/simjeb_bench.py evaluate --family <design|redesign|lighten> --id <simjeb id> --step part.step --results results.jsonl --model <model>` from the project (needs the SimJEB CAD and the FEniCSx environment).
4. Score: `python evaluator/score.py --refs evaluator/references.jsonl --submissions runs/<model> --simjeb-results results.jsonl --out score.json`.

The builder scripts read the original source collections under `cvpr2027/data` and `cvpr2027/tmp`; they are included for provenance and are not needed to run the benchmark.
