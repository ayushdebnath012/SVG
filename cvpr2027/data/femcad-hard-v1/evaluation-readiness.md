# Astra evaluation readiness audit

Verdict: **not ready for a scored benchmark of the hardest FEM tasks**. The dataset is a useful published-source collection, with sufficient assets to prepare a qualitative generation pilot. Collecting solved model files did not complete the evaluator.

## Packaging update

Candidate/reference separation and local dependency packaging have now been implemented; see [input-packaging-report.md](input-packaging-report.md). The original findings below describe the pre-packaging audit. The new package statuses supersede its input-packaging statements: 42 have no known dependency/settings blocker, eight are blocked, and all still require final semantic/workflow review and numerical scoring work. The old leakage-prone pilot is disabled.

## Verified assets

- 50 unique studies and source URLs; 82 reference images.
- 213 recorded asset/page hashes checked, with no missing local files or mismatches.
- 50 published model archive inventories contain binary mesh and solution entries, with matching tutorial versions.
- Two primary solved models are downloaded locally; the remaining primary models are remote links with inspected archive directories.
- Four standalone reference tables cover three studies (005, 021, 026). Other text files often contain inputs or evaluation expressions rather than outputs.

## Blocking findings

1. **No numerical scoring contract.** All 50 rows lack structured quantities of interest, output keys, comparison locations/load steps, and an implemented evaluator. Acceptance tolerances and mesh-convergence criteria have not been established. A solved MPH archive is not yet a usable, independently validated grading target. Zero rows are currently wired for numerical grading; this is not a model performance score.
2. **Inputs are not frozen or self-contained.** There is no final evaluation prompt in any combined row; 45 rows have a generic model-formulation field. Thirty-five tutorials mention external files. The pilot supplies stripped tutorial text and selected geometry figures, but does not supply the newly crawled supporting material/geometry files. Stripping HTML can also omit equations stored as images. Each task needs a verified set of dimensions, material laws, boundary selections, units and load steps from existing source evidence. Unresolved items must be marked underdetermined rather than filled in.
3. **Reference answers are mixed with potential inputs.** Forty-nine tutorials have a Results and Discussion section. The pilot includes the entire tutorial text, and the combined rows carry solved-model URLs. Decide whether the evaluation measures source-assisted reproduction or reconstruction with held-out answers. For the latter, create separate input and reference manifests and keep solved MPH files, result tables and answer sections inaccessible to the candidate. Public tutorial availability also prevents a clean claim of unseen-data performance without further evidence.
4. **The runner does not evaluate these 50 tasks on Astra.** `scripts/fem_open_model_pilot.py` hard-codes tasks 001 and 011, has no Astra dispatch branch, does not consume `advanced-tasks.jsonl`, and labels a parsed JSON response as generated without requiring nonempty valid code. It has no integrated execution/physics/numerical scorer or budget-aware, resumable 50-task run. Other Astra scripts in this workspace target different datasets.
5. **The solver/reference workflow is incomplete.** Gmsh is installed in the pilot virtual environment, but no COMSOL execution/export workflow is configured. No COMSOL/Abaqus/CalculiX executable was found in the checked locations. MFEM source is present; it is not a validated implementation of these tasks. Establish the permitted solver/version, dependencies, memory and runtime limits, then verify existing published references can be read/exported without generating substitute answers.
6. **A known reference ambiguity remains.** Study 002 records 60 V in the results narrative versus 50 V in Figure 4. Resolve the operating point from the source model before using the reported contact pressure as an evaluation target.
7. **The hardest-task label is uncalibrated.** Difficulty is an editorial selection based on physics and geometry. No Astra result exists for these 50 studies. The two-task DeepSeek pilot does not establish that Astra fails these tasks or that they are the hardest FEM tasks. Syntax errors, missing inputs, API blocks, absent solvers and token truncation must be separated from FEM reasoning failures.

## Readiness by evaluation level

| Level | Current readiness |
|---|---|
| Source/asset integrity | Passed local checks |
| Qualitative source-assisted generation pilot | Preparation possible; runner and access changes needed |
| Automated code execution across 50 tasks | Not ready |
| Geometry reproduction score | No calibrated geometry evaluator wired |
| Physics and numerical FEM correctness score | Not ready |
| Claim that tasks defeat Astra or represent the hardest tier | Unsupported |

## Required before a scored run

Freeze source-derived inputs per task and declare which answers are held out. Define and implement per-task output comparisons against existing published data, with externally justified acceptance criteria; do not invent reference values. Reconcile ambiguous source settings and verify solver exports. Add an Astra runner with separate provider, truncation, execution and numerical outcomes, and a recorded budget/effort/attempt policy. Conduct a stratified pilot before expanding to all 50; use its outcomes to calibrate difficulty without cherry-picking an undisclosed test set.

The earlier 8,000-token pilot exhausted its output allowance on both tasks before answering. A small token budget can support a limited generation check, but truncated outputs cannot establish inability to solve the FEM problem.

The last recorded Astra access check on 2026-10-10 failed due to a gateway purchase lock and exhausted official API credits; access was not re-probed here. No billable generation was performed during this audit. No simulations, numerical answers or grading tolerances were generated.

Machine-readable evidence and per-study flags: `evaluation-readiness.json`.
