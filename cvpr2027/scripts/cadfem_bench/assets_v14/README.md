# CADFEM-Bench v1.4 — balanced, isolated-replay pilot

The primary comparison suite has **41 tasks, 86 published numerical targets and 10 engineering-family labels**, capped at five tasks per family. It contains 35 supplied-CAD tasks and six drawing/specification-to-CAD tasks. Ten primary tasks have independent reproduction evidence. This is a pilot, not a certified broad engineering leaderboard.

The original v1.3 pool of 126 tasks/308 targets is retained in `evaluator/task-pool/`. Six NAFEMS calibration tasks are separate, 78 public-source tasks are reserved outside candidate inputs, and one additional rigging task is related to primary CAD. The 50 previously held tasks remain held. These categories must not be added to the primary score. Forty-one tasks do not imply forty-one independent mechanical problems.

## Fixed in this release

- Primary-suite balance: each family contributes at most five tasks, and scoring retains family macro-averages. Bracket/holed-plate families now contribute 15/41 tasks (36.6%), instead of 84/126 (66.7%).
- Source/evaluator separation: only the 41 primary tasks are model-visible in candidate/. Reserved input files are moved under evaluator/. Exact primary CAD hashes do not overlap the reserved suite; related parametric geometries and public-source exposure remain possible.
- Specification geometry gates now also enforce solid count and the stated sphere/cylinder radii (0.01 mm) for the five FEMCAD tasks; a wrong 9.8 mm hole is rejected even though its volume is close.
- Version/readiness labels: the scorer reports 1.4. The current review protocol distinguishes 10 reproduced primary tasks from 16 in the full pool.
- Sandboxed replay: `evaluator/sandbox_runner.py` freezes inputs/source and re-runs main.py offline. The tested macOS mode denies package/home-data reads, outbound network, changes to inputs/source and writes outside output/cache/tmp directories. CPU, elapsed-time and observed process-group memory limits are recorded. Docker support requires an already installed digest-pinned image; it was not run on this machine.
- Automated field consistency: `evaluator/verify_static_fields.py` independently assembles the source-defined cycloidal linear-elastic operator, verifies mesh-to-field node coverage, checks equilibrium and zero fixed DOFs, and extracts maximum displacement. It rejects a field changed by 0.1%. It does **not** yet audit boundary tags against every CAD face or independently validate geometry/convergence. It never fabricates a complete workflow approval.
- Common evaluation protocol: fixed environment, budgets, attempts, provenance and separate numerical/execution/physics/workflow metrics are in `evaluator/evaluation-protocol.json`.

## Actual validation evidence

A trusted software baseline imported the original cycloidal coupler CAD and solved it on three meshes **inside the no-network macOS sandbox** using Gmsh, scikit-fem and SciPy. Its final maximum displacement is 0.007705541 mm, versus the original published 0.007617466 mm (about 1.16% difference, within the existing 6% band). The trusted reassembled weak-form residual is 9.15e-13. Scaling the submitted displacement array by 1.001 produces a residual near 9.99e-4 and is rejected.

The sandbox's six denial probes pass: evaluator reads, another-release reads, writes outside the job, input modification, outbound network and hard-link escape. A deliberately nonterminating program is killed at the wall-time limit and receives no execution approval. Failed setup attempts are preserved as failures, not counted as successful baseline solves.

This is a **software solver baseline**, not a human expert or frontier-model trial. Repeat solves of the already-reproduced coupler do not increase the count of reproduced tasks. Correct answers alone still cannot pass the workflow scorer.

## Run the primary suite

Give the model **only candidate/**. Do not supply this whole package: evaluator/, held/ and scripts/ contain answers and hidden evidence. Generate a main.py submission using the same prompts, image access and tool/runtime capabilities for every participating model. Record exact provider/model/version, reasoning settings, token usage, generation time and cost outside the sandbox. No API credentials are passed to candidate code.

```sh
python evaluator/sandbox_runner.py prepare --package /path/cadfem-bench-v1.4 \
  --job /path/runs/model/task-attempt-1 --task-id A-CYC-Coupler-PETGCF \
  --submission /path/generated-code --model-id provider/exact-model-version --run-id run-001

python evaluator/sandbox_runner.py replay --package /path/cadfem-bench-v1.4 \
  --job /path/runs/model/task-attempt-1 --backend macos --python /trusted/runtime/bin/python \
  --wall-seconds 600 --cpu-seconds 600 --ram-mb 8192
```

The submitted program reads files from `CADFEM_INPUT_DIR` and writes artifacts to `CADFEM_OUTPUT_DIR` (also its working directory). Replay uses a clean environment and a frozen submission. Each new attempt needs a fresh job directory. A failed sandbox or missing Docker runtime never falls back to unrestricted execution. The macOS profile is a local pilot mechanism: it protects home/package data and restricts writes/network, but permits system data outside home to be read. Docker is the preferred portable backend with a read-only root, network disabled, dropped capabilities and PID/resource limits; supply `--image name@sha256:<digest>`.

Copy or reference the eight completed output artifacts for scoring, follow REVIEW_PROTOCOL.md for checks still requiring review, and use:

```sh
python evaluator/score.py --refs evaluator/references.jsonl --tasks candidate/tasks.jsonl \
  --submissions runs/model --run-id run-001 --reviews trusted-reviews.jsonl --out score.json
```

Execution success and a weak residual check are reported separately from end-to-end workflow completion. Human review is still needed for unsupported geometry, setup, field extraction and convergence. Do not automatically set review flags true because a program ran.

## Calibration and reservation

Use `--suite calibration` for separate NAFEMS preparation; its tasks/references/inputs are under `evaluator/suites/calibration/`. The other two suites are `reserved-public` and `related-public`. Their filtered scorer directories contain exact geometry-reference copies so the geometry gate resolves correctly. Treat original source evidence paths as pointers to the parent evaluator bundle, not model inputs.

Reservation is **not a genuinely private hold-out**. Every source is public and may have appeared in training. Web crawling cannot by itself establish private provenance. Private hold-out machinery is prepared, but contamination-resistant generalization claims require unpublished or otherwise demonstrably unseen cases. No such claim is made here.

## Complex-physics expansion

`evaluator/source-review/freecad-contact/` adds a newly verified original shell-to-shell contact source pair from FreeCAD: two native cylindrical-shell BREP faces, a CalculiX input deck and saved native result arrays for 15,404 nodes. The published creation script and deck both specify a 5000 N force, E=72000 MPa and 0.5 mm shell thickness. The legacy serialized force value, exact saved-output correspondence and units need further verification. The solid-contact example has CAD/setup but no saved result fields.

This contact data is **held for admission**, not counted as a new primary task. The existing solid-only scorer also needs a shell-specific geometry validator. Plasticity, fracture, forming, crash and fatigue still lack independently admitted primary cases. The existing Code_Aster pool provides source problems and outputs, but lacks native STEP and completed CAD/task correspondence. No missing reference or engineering problem was generated to fill these gaps.

## Remaining limitations

31/41 primary tasks still lack independent reproduction. The scorer now also reports a separate reproduced-tasks-only summary (10 tasks), so exploratory cases need not determine the reproduced subset comparison. Most tolerance bands remain provisional; convergence-derived bands are empirical, not rigorous uncertainty bounds. Fully automatic CAD-face/setup/field/convergence approval is unfinished. No frontier-model or human expert runs have been performed, consistent with the earlier instruction to prepare the benchmark/runner. Public-source contamination and data-specific redistribution restrictions remain; do not publish this package as a whole.

`evaluator/limitations-status.json` records the precise fixed, partial and pending items. v1.3 is preserved unchanged. Build this release with `scripts/cadfem_bench/release_v14.py --source <v1.3> --out <new-folder> --workspace <SVG>`; the original workspace supplies the retained source/replay evidence. Legacy builder scripts are included for historical provenance, not as the v1.4 entry point.

## Retained release verification

Re-run on the finished folder (no task, target or suite changed):
- Primary suite: 64 candidate inputs hash-checked; 32 distinct STEP/BREP files valid in OpenCASCADE; 477 evidence files hash-checked; no reference value in any prompt or text input. Exact answers alone give 41 numerical passes and 0 passes; answers scaled by 1.3 give 0; four malformed submissions are rejected per task; a reviewed probe passes and fails once an artifact changes; the 6 geometry gates accept the rotated, moved reference and reject it scaled by 3 %; the independent finest-mesh values pass all 9 convergence-study tasks.
- Candidate isolation: candidate/ holds exactly the 41 primary tasks; no calibration or reserved CAD file is model-visible (the related-public task shares 1 CAD file with the primary suite by construction).
- Suite `calibration`: 6 tasks, 6 outputs, 22 inputs hash-checked, no leaks; exact answers 6/6 numerical, 0 passes; scaled answers 0; 3 geometry gates pass the same probes. Scorer reports version 1.4.
- Suite `reserved-public`: 78 tasks, 215 outputs, 84 inputs hash-checked, no leaks; exact answers 78/78 numerical, 0 passes; scaled answers 0. Scorer reports version 1.4.
- Suite `related-public`: 1 tasks, 1 outputs, 2 inputs hash-checked, no leaks; exact answers 1/1 numerical, 0 passes; scaled answers 0. Scorer reports version 1.4.
- Sandbox: the packaged `evaluator/sandbox_runner.py` replayed a denial probe against this folder (macos-seatbelt): reading this package's references, the released v1.3 references and workspace source data, writing outside the job, modifying inputs and outbound network were all denied; the pinned CadQuery/Gmsh/NumPy/SciPy runtime imported inside the sandbox (5.06 s). Record: `evaluator/runtime-validation/finish-v14-probe/`.

## Folder layout

| path | contents | who sees it |
|---|---|---|
| `candidate/` | primary suite only: `tasks.jsonl`, `tasks/<task_id>/` inputs, `README.md` (artifact contract), `submission.schema.json` | model |
| `evaluator/references.jsonl`, `evaluator/score.py` | primary-suite hidden references and the scorer (never runs candidate code; reports the release version) | evaluator only |
| `evaluator/suites/<suite>/` | `tasks.jsonl`, `references.jsonl` and inputs of `primary`, `calibration`, `reserved-public`, `related-public`; score each suite separately with its own files | evaluator only |
| `evaluator/task-pool/` | the full v1.3 source-backed pool with its card and report | evaluator only |
| `evaluator/sandbox_runner.py`, `evaluation-protocol.json`, `runtime-lock.json`, `requirements-runtime.txt` | offline replay of a submitted `main.py` and the common run protocol | evaluator only |
| `evaluator/verify_static_fields.py`, `evaluator/runtime-validation/` | cycloidal field-equilibrium checker; sandbox denial, timeout and solver-baseline records | evaluator only |
| `evaluator/evidence/`, `evidence-manifest.jsonl` | original source files behind every reference, with SHA-256 | evaluator only |
| `evaluator/source-review/` | collected sources still under review (not tasks) | evaluator only |
| `evaluator/registry.jsonl`, `validation.json`, `verification.json`, `suite-manifest.json`, `task-hashes.json`, `limitations-status.json` | source registry, release counts, build-time verification, suite policy, task hashes, open limitations | evaluator only |
| `held/` | held tasks with their inputs and reasons; `excluded-local-targets.jsonl` lists the 190 removed v1.0 targets | evaluator only |
| `report/<release>.pdf` | composition, suites, validation and remaining limitations | everyone |
| `scripts/cadfem_bench/` | builders: `release.py` (full pool), `release_v14.py` + `suites.py` (suites), `finish_v14.py` (verification and packaging), `report_v14.py` (report) | maintainers |
| `SHA256SUMS.txt` | SHA-256 of every file | everyone |
