# Audited published FEM pilot

The 100-case collection has been audited for benchmark admission. **Three source-complete calibration cases are admitted, in six separate track tasks. Zero cases have certified pass/fail scoring.** This is a preparation release, not evidence that frontier models can solve complex industrial engineering problems.

All physical problems, drawings/geometry, materials, loads, supports and numerical references come from published sources. The new code audits and packages source excerpts and defines submission/evaluation rules; it does not invent engineering tasks, complete missing physical inputs, construct CAD, or calculate new FEM references. No model API requests or FEM solves were performed.

The requested minimum is now **50 distinct problems**. A [new 50-case published source expansion](../published-fem-expansion-50/README.md) contains original geometry illustrations, solver inputs, meshes and numerical FEM baselines from Code_Aster. These source pairs require benchmark review and are not yet added to the three admitted pilot cases. Its 28 geometry scripts are not native STEP CAD files.

## Audit outcome

| Source | Cases | Decision | Main evidence or blocker |
|---|---:|---|---|
| SFEM | 61 | Exclude from deterministic FEM solving | Stochastic median fields; realized load locations absent |
| Bath curved links | 18 | Stage for complex geometry/analysis | Original APDL decks now extracted; native IPT import, CAD boundary mapping and DP0 correspondence need verification |
| Morphing-wing specimens | 8 | Hold CAD/FEM correspondence | Each CAD specimen is 19 mm longer than its FEM domain; shell idealization and grip exclusion need verification |
| Auxetic meta-shells | 6 | Hold nonlinear/contact mapping | Original CW/CCW decks now downloaded; fitted Ogden parameters, rotation/CSV mapping and grip geometry need verification; 31/30-degree naming conflict |
| Scan-based steel columns | 3 | Hold physical setup | Full nonlinear material law, joint/contact treatment and loading history unverified |
| NAFEMS LE1, LE10, LE11 | 3 | Admit to calibration pilot | Source geometry, physical declarations, drawings and matching published FEM scalar |
| NAFEMS GNL5 | 1 | Exclude provisional reference | Publisher marks implementation work in progress; duplicate labels in reference table |

The audit verifies **189 distinct collection assets and 611 numerical values** against the original HDF5 fields, workbook rows/cells, CSVs, tables and published HTML. It records per-case hashes, source-card line locators and blockers in [audit.json](audit.json). This is asset/label verification, not an independent convergence or physics certification. Five supplementary drawing-source documents were also reviewed: three lack FEM results; two paper-level drawing/FEM sources lack complete verified analysis specifications.

## Admitted source cases

All three come from the [published FeenoX mechanical examples](https://www.seamplex.com/feenox/examples/mechanical.html), with repository source assets pinned to commit `06965026d6c73919ee02744192ec4b7526bb7e5c`.

| Case | Source problem | Requested FEM output | Supplied geometry |
|---|---|---|---|
| NAFEMS-LE1 | Elliptical membrane under normal traction | Signed sigma_yy at D | Original Gmsh planar geometry definition |
| NAFEMS-LE10 | Thick elliptical plate under pressure | Signed sigma_yy at D | Original STEP and physical-group definitions |
| NAFEMS-LE11 | Cylinder/taper/sphere under a temperature gradient | Signed sigma_zz at A | Original Gmsh solid geometry definition |

These are curved geometry and boundary-condition calibration cases, not complex industrial assemblies. The dimensional drawing typo in LE1 and rounding in LE11 are documented using the original geometry parameters. LE11's zero stress-free reference temperature is taken from the pinned source solver default, not guessed. `.geo` files are published geometry definitions, not native STEP solids; only LE10 supplies a native STEP file.

## Two independent tracks

- `cad_fem`: original source drawing, physical declarations and precision notes; no reference CAD, solver recipe or target values. The model must construct CAD, mesh it and solve the problem.
- `analysis_fem`: the same physical problem, plus original source geometry. The model must set up the FEM analysis, generate/refine its mesh and solve it.

Candidate packs contain cropped source diagrams with answer panels/solver recipes removed, declarative source inputs and submission instructions. These crops were visually inspected. Evaluator packs contain original source assets and held-out numerical contracts. Do not attach the audit, source HTML, evaluator pack or this source-identifying report to the model. Public examples may already appear in model training data; answer separation does not remove that contamination risk.

## Numerical comparison and physical validity

The runner reports signed absolute error and relative error `abs(prediction-reference)/abs(reference)`. Equivalent Pa/kPa/MPa/GPa units are converted explicitly; incompatible units, nonfinite values and missing quantities are rejected. Zero references receive absolute error only. There are no invented 1%, 5% or 10% acceptance thresholds and no overall numerical pass/fail.

A number matching the source does not establish a solver result. The candidate must provide code, mesh, fields, solver log, refinement history and a CAD export in the CAD track. A trusted reviewer must check geometry, materials, loads/supports, CAD-to-mesh correspondence, actual FEM execution, convergence and stress recovery against the source. Reviews bind to exact input/code/output hashes and must remain outside candidate mounts. Wrong physical setup fails physical validity even if the numerical scalar matches. Until an independent baseline and tolerances are approved, `joint_pass` remains null.

Reports separate models and tracks and expose missing outputs, physical failures and infrastructure failures. Macro errors average within physics families rather than pooling hundreds of near-duplicate examples. Numeric errors on reviewed attempts must be reported with coverage and failed-attempt counts; they are not a model success rate.

## Prepared runner

The runner makes **no API calls** and executes candidate code only in a Docker container with no network and no access to evaluator files. Candidate inputs and code mount read-only; outputs have a separate writable mount. There is no host execution fallback. Docker is not installed here, so isolated replay is infrastructure-blocked. A local solver environment alone is not an isolated benchmark runtime.

Extract both delivery archives into the repository root to preserve the catalogue paths. Re-running the collection audit additionally requires the existing original source cache; the delivery ZIPs do not contain all 100 raw collection cases.

From the repository root:

```sh
cvpr2027/tmp/cq-env/bin/python cvpr2027/scripts/audit_published_fem_benchmark.py audit
cvpr2027/tmp/cq-env/bin/python cvpr2027/scripts/audit_published_fem_benchmark.py validate

python3 cvpr2027/scripts/published_fem_runner.py prepare \
  --case NAFEMS-LE10 --track cad_fem --model YOUR_MODEL \
  --out cvpr2027/tmp/published-fem-runs/YOUR_MODEL-LE10-cad-attempt1

python3 cvpr2027/scripts/published_fem_runner.py ingest \
  --out cvpr2027/tmp/published-fem-runs/YOUR_MODEL-LE10-cad-attempt1 \
  --response MODEL_RESPONSE.json

python3 cvpr2027/scripts/published_fem_runner.py replay \
  --out cvpr2027/tmp/published-fem-runs/YOUR_MODEL-LE10-cad-attempt1 \
  --image YOUR_PINNED_SOLVER_IMAGE --timeout 900

python3 cvpr2027/scripts/published_fem_runner.py score \
  --out cvpr2027/tmp/published-fem-runs/YOUR_MODEL-LE10-cad-attempt1 \
  --review TRUSTED_REVIEW.json
```

Use the same verified image, tool access, reasoning/token/time budgets and attempt count across compared models. Record actual model/version and usage when model access becomes available; `--model` currently records metadata only. Generated submissions are frozen before replay, and execution cannot silently retry or overwrite an attempt. The trusted-review schema is in [review-template.json](review-template.json); null fields deliberately do not count as passed checks.

## Complex engineering expansion

The most promising complex candidates are the Bath lattices, meta-shells with self-contact, and scan-based buckling columns. Their original assets remain available and their admission blockers are explicit. [expansion.json](expansion.json) identifies a diverse shortlist and the source evidence needed to promote each case. No missing data are filled with assumptions. None of these staged cases is included in the executable pilot.

Manufacturing/forming, fatigue/fracture, transient dynamics, geared assemblies, complete pump/turbine assemblies and coupled fluid/thermal/structural tasks have no admitted case in this release. The shaft/connecting-rod papers remain discovery leads, while the hoist and wheel sources remain drawing-only. Broad frontier capability claims require additional complete published problems and independently verified scoring contracts.

## Files and provenance

- [audit.json](audit.json): all 100 collection cases plus five supplementary source documents.
- [catalog.json](catalog.json): the six admitted track packages and held-out evaluator locations.
- [validation.json](validation.json): package and answer-separation checks.
- `cvpr2027/output/datasets/published-fem-pilot-v1-candidates.zip`: six candidate input packages only.
- `cvpr2027/output/datasets/published-fem-pilot-v1-evaluator.zip`: held-out contracts and original reference assets; never expose to the candidate.
- `cvpr2027/output/pdf/published-fem-benchmark-audit.pdf`: human-readable audit and source-drawing review, for the evaluator only.

Source code/examples retain their original GPL-3.0-or-later notices and accompanying COPYING. Third-party NAFEMS artwork retains its original attribution; no new blanket license is asserted over that artwork. Original downloads remain in git-ignored `cvpr2027/tmp`; the earlier 100-case PDF/ZIP remain a source collection and have not become a 100-case certified benchmark.
