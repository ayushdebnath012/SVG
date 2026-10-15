# CADFEM-Bench v1.5: balanced pilot with plasticity and fracture families

Released 2026-10-14. The primary comparison suite has **46 tasks, 95 published numerical targets and 12 engineering-family labels**, capped at five tasks per family: 40 supplied-CAD tasks and 6 drawing/specification-to-CAD tasks. 15 primary tasks have independent reproduction evidence. Calibration (7 tasks), reserved public-source (78) and related (1) suites are evaluator-only and scored separately; 51 tasks are held with reasons. Bracket and holed-plate families contribute 15 of 46 primary tasks. This is a source-backed pilot, not a certified engineering leaderboard; every graded value is published by its source.

## Changes in v1.5

v1.5 adds two physics classes the v1.3 audit found missing, plasticity and fracture. Every v1.4 task, target, tolerance and suite assignment is unchanged. A new case is graded only when an independent solver run settles within a 10 % band around the published value: last mesh change < 1 %, previous < 2 %, band = |finest - published| / published + 2 x last change, tolerance = band, at least 5 %. This is the rule the cycloidal and buckling families already use.

### Plasticity: fcVM plastic collapse (limit) load factors

fcVM's published elastic-perfectly plastic collapse factors (von Mises, no hardening, geometrically linear). Only models whose published load-displacement curve ends on a flat plateau are used: the lug, barrier and train-bridge runs stop while the load is still rising, so their peak is a lower bound and stays held. Each load set is rebuilt from the original FreeCAD constraints and matches the published load sum. The independent check (`scripts/fcvm_plastic_check.py`) is a FEniCSx limit analysis: quadratic tetrahedra, radial return with the consistent tangent, and proportional loading with bisection. The limit factor is bracketed to 0.2 %. Its solver check is the tensile bar, whose closed-form limit 0.5 it reproduces; that bar goes to the calibration suite.

| model | published | finest independent | difference | last change | decision |
|---|---:|---:|---:|---:|---|
| Wyk_Rohrstoss_ring | 1.52 | 1.524 | +0.2 % | 0.03 % | primary, tolerance 5 % |
| tensile | 0.5 | 0.4994 | -0.1 % | 0.00 % | calibration, tolerance 5 % |
| transition | 65.5 | 55.23 | -15.7 % | 2.42 % | held: independent limit load not settled (last change 2.42 %, previous 5.36 %; finest 55.23, -15.7 % from the published factor 65.5); a diagnostic solve on a coarser mesh (3215 elements; fcVM used 4866) gives 65.04: most of the gap closes on coarsening, consistent with a coarse-mesh published value |

### Fracture: Code_Aster SSLP311, crack on an inclined bimaterial interface

A 4 x 8 mm plate made of two elastic materials (E = 2.0e6 and 2.0e5 MPa) is joined along an inclined line through its centre. A 2 mm crack lies on that line, and the plate is in plane-stress tension. Outputs: the energy release rate G at both tips, for 15, 30, 45 and 60 degrees. The reference is the published boundary-element solution of Miyazaki et al. (1993) as tabulated by the source, with a stated uncertainty below 0.1 %. The source test states G directly for 15 degrees. For the other angles, G follows from the tabulated F_I and F_II through the source's G formula, which reproduces the two stated values to 2e-6 (`evidence/interface-crack/reference-derivation.json`). The CAD (`plate.step`, two solids with the crack faces split out) is built from the documented geometry. The independent check (`scripts/interface_crack_g.py`) is a FEniCSx plane-stress model on quadratic triangles with an equivalent-domain J-integral over three rings, run on five mesh levels. It is itself checked against a Griffith crack (within 0.1 %).

| angle | tip | published G (J/m^2) | finest independent | difference | last change | decision |
|---:|---|---:|---:|---:|---:|---|
| 15 | right | 101.2507 | 101.1823 | -0.07 % | 0.07 % | primary, tolerance 5 % |
| 15 | left | 96.7362 | 96.6164 | -0.12 % | 0.04 % | primary, tolerance 5 % |
| 30 | right | 84.8415 | 84.7830 | -0.07 % | 0.03 % | primary, tolerance 5 % |
| 30 | left | 80.0173 | 79.8881 | -0.16 % | 0.06 % | primary, tolerance 5 % |
| 45 | right | 59.4124 | 59.6616 | +0.42 % | 0.00 % | primary, tolerance 5 % |
| 45 | left | 57.3827 | 57.3219 | -0.11 % | 0.04 % | primary, tolerance 5 % |
| 60 | right | 32.2438 | 32.5934 | +1.08 % | 0.06 % | primary, tolerance 5 % |
| 60 | left | 32.8017 | 32.4847 | -0.97 % | 0.17 % | primary, tolerance 5 % |

### Reviewed and held in v1.5

- Code_Aster SSNV104 (Hertz contact of two hemispheres): the analytical reference assumes a contact radius much smaller than the sphere radius, but here a/R = 0.2, and the source's own result differs from it by 13.5 % (source tolerance 14 %). Not a usable target.
- Code_Aster SSNV506 (elastoplastic indentation): the reference is an approximate textbook plasticity estimate for a 100 mm indentation.
- fcVM plastic peaks that are not limit loads (lug, barrier, train bridge) and the geometric-nonlinear post-buckling peaks (plate girder, U100).
- Frictional contact remains absent: the FreeCAD shell-contact pair (under review in `evaluator/source-review/`) and the Code_Aster contact cases are not admitted.
- Scorer: `evaluator/score.py` is the v1.4 scorer (solid-count and analytic-radius gates, reproduced-task summaries); it reports version 1.5.

Registry: new rows `fcvm-plastic` and `codeaster-sslp311`; `fcvm-collapse` and `codeaster-50` are narrowed to what remains held.

## v1.4 release notes (carried over unchanged)

The primary comparison suite has **41 tasks, 86 published numerical targets and 10 engineering-family labels**, capped at five tasks per family. It contains 35 supplied-CAD tasks and six drawing/specification-to-CAD tasks. Ten primary tasks have independent reproduction evidence. This is a pilot, not a certified broad engineering leaderboard.

The original v1.3 pool of 126 tasks/308 targets is retained in `evaluator/task-pool/`. Six NAFEMS calibration tasks are separate, 78 public-source tasks are reserved outside candidate inputs, and one additional rigging task is related to primary CAD. The 50 previously held tasks remain held. These categories must not be added to the primary score. Forty-one tasks do not imply forty-one independent mechanical problems.

### Fixed in this release

- Primary-suite balance: each family contributes at most five tasks, and scoring retains family macro-averages. Bracket/holed-plate families now contribute 15/41 tasks (36.6%), instead of 84/126 (66.7%).
- Source/evaluator separation: only the 41 primary tasks are model-visible in candidate/. Reserved input files are moved under evaluator/. Exact primary CAD hashes do not overlap the reserved suite; related parametric geometries and public-source exposure remain possible.
- Specification geometry gates now also enforce solid count and the stated sphere/cylinder radii (0.01 mm) for the five FEMCAD tasks; a wrong 9.8 mm hole is rejected even though its volume is close.
- Version/readiness labels: the scorer reports 1.4. The current review protocol distinguishes 10 reproduced primary tasks from 16 in the full pool.
- Sandboxed replay: `evaluator/sandbox_runner.py` freezes inputs/source and re-runs main.py offline. The tested macOS mode denies package/home-data reads, outbound network, changes to inputs/source and writes outside output/cache/tmp directories. CPU, elapsed-time and observed process-group memory limits are recorded. Docker support requires an already installed digest-pinned image; it was not run on this machine.
- Automated field consistency: `evaluator/verify_static_fields.py` independently assembles the source-defined cycloidal linear-elastic operator, verifies mesh-to-field node coverage, checks equilibrium and zero fixed DOFs, and extracts maximum displacement. It rejects a field changed by 0.1%. It does **not** yet audit boundary tags against every CAD face or independently validate geometry/convergence. It never fabricates a complete workflow approval.
- Common evaluation protocol: fixed environment, budgets, attempts, provenance and separate numerical/execution/physics/workflow metrics are in `evaluator/evaluation-protocol.json`.

### Actual validation evidence

A trusted software baseline imported the original cycloidal coupler CAD and solved it on three meshes **inside the no-network macOS sandbox** using Gmsh, scikit-fem and SciPy. Its final maximum displacement is 0.007705541 mm, versus the original published 0.007617466 mm (about 1.16% difference, within the existing 6% band). The trusted reassembled weak-form residual is 9.15e-13. Scaling the submitted displacement array by 1.001 produces a residual near 9.99e-4 and is rejected.

The sandbox's six denial probes pass: evaluator reads, another-release reads, writes outside the job, input modification, outbound network and hard-link escape. A deliberately nonterminating program is killed at the wall-time limit and receives no execution approval. Failed setup attempts are preserved as failures, not counted as successful baseline solves.

This is a **software solver baseline**, not a human expert or frontier-model trial. Repeat solves of the already-reproduced coupler do not increase the count of reproduced tasks. Correct answers alone still cannot pass the workflow scorer.

### Run the primary suite

Give the model **only candidate/**. Do not supply this whole package: evaluator/, held/ and scripts/ contain answers and hidden evidence. Generate a main.py submission using the same prompts, image access and tool/runtime capabilities for every participating model. Record exact provider/model/version, reasoning settings, token usage, generation time and cost outside the sandbox. No API credentials are passed to candidate code.

```sh
python evaluator/sandbox_runner.py prepare --package /path/cadfem-bench-v1.5 \
  --job /path/runs/model/task-attempt-1 --task-id A-CYC-Coupler-PETGCF \
  --submission /path/generated-code --model-id provider/exact-model-version --run-id run-001

python evaluator/sandbox_runner.py replay --package /path/cadfem-bench-v1.5 \
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

### Calibration and reservation

Use `--suite calibration` for separate NAFEMS preparation; its tasks/references/inputs are under `evaluator/suites/calibration/`. The other two suites are `reserved-public` and `related-public`. Their filtered scorer directories contain exact geometry-reference copies so the geometry gate resolves correctly. Treat original source evidence paths as pointers to the parent evaluator bundle, not model inputs.

Reservation is **not a genuinely private hold-out**. Every source is public and may have appeared in training. Web crawling cannot by itself establish private provenance. Private hold-out machinery is prepared, but contamination-resistant generalization claims require unpublished or otherwise demonstrably unseen cases. No such claim is made here.

### Complex-physics expansion

`evaluator/source-review/freecad-contact/` adds a newly verified original shell-to-shell contact source pair from FreeCAD: two native cylindrical-shell BREP faces, a CalculiX input deck and saved native result arrays for 15,404 nodes. The published creation script and deck both specify a 5000 N force, E=72000 MPa and 0.5 mm shell thickness. The legacy serialized force value, exact saved-output correspondence and units need further verification. The solid-contact example has CAD/setup but no saved result fields.

This contact data is **held for admission**, not counted as a new primary task. The existing solid-only scorer also needs a shell-specific geometry validator. Plasticity, fracture, forming, crash and fatigue still lack independently admitted primary cases. The existing Code_Aster pool provides source problems and outputs, but lacks native STEP and completed CAD/task correspondence. No missing reference or engineering problem was generated to fill these gaps.

### Remaining limitations

31/41 primary tasks still lack independent reproduction. The scorer now also reports a separate reproduced-tasks-only summary (10 tasks), so exploratory cases need not determine the reproduced subset comparison. Most tolerance bands remain provisional; convergence-derived bands are empirical, not rigorous uncertainty bounds. Fully automatic CAD-face/setup/field/convergence approval is unfinished. No frontier-model or human expert runs have been performed, consistent with the earlier instruction to prepare the benchmark/runner. Public-source contamination and data-specific redistribution restrictions remain; do not publish this package as a whole.

`evaluator/limitations-status.json` records the precise fixed, partial and pending items. v1.3 is preserved unchanged. Build this release with `scripts/cadfem_bench/release_v14.py --source <v1.3> --out <new-folder> --workspace <SVG>`; the original workspace supplies the retained source/replay evidence. Legacy builder scripts are included for historical provenance, not as the v1.4 entry point.

## Release verification (finish_suites.py)

Re-run on the finished folder (no task, target or suite changed):
- Primary suite: 74 candidate inputs hash-checked; 37 distinct STEP/BREP files valid in OpenCASCADE; 544 evidence files hash-checked; no reference value in any prompt or text input. Exact answers alone give 46 numerical passes and 0 passes; answers scaled by 1.3 give 0; four malformed submissions are rejected per task; a reviewed probe passes and fails once an artifact changes; the 6 geometry gates accept the rotated, moved reference and reject it scaled by 3 %; the independent finest-mesh values pass all 14 convergence-study tasks.
- Candidate isolation: candidate/ holds exactly the 46 primary tasks; no calibration or reserved CAD file is model-visible (the related-public task shares 1 CAD file with the primary suite by construction).
- Suite `calibration`: 7 tasks, 7 outputs, 24 inputs hash-checked, no leaks; exact answers 7/7 numerical, 0 passes; scaled answers 0; 3 geometry gates pass the same probes. Scorer reports version 1.5.
- Suite `reserved-public`: 78 tasks, 215 outputs, 84 inputs hash-checked, no leaks; exact answers 78/78 numerical, 0 passes; scaled answers 0. Scorer reports version 1.5.
- Suite `related-public`: 1 tasks, 1 outputs, 2 inputs hash-checked, no leaks; exact answers 1/1 numerical, 0 passes; scaled answers 0. Scorer reports version 1.5.
- Sandbox: the packaged `evaluator/sandbox_runner.py` replayed a denial probe against this folder (macos-seatbelt): reading this package's references, the released v1.3 references and workspace source data, writing outside the job, modifying inputs and outbound network were all denied; the pinned CadQuery/Gmsh/NumPy/SciPy runtime imported inside the sandbox (2.8 s). Record: `evaluator/runtime-validation/finish-v1.5-probe/`.
