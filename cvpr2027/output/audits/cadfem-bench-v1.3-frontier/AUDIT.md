# CADFEM-Bench v1.3 suitability for frontier-model comparisons

**Verdict: usable as a controlled, tool-assisted CAD/FEM pilot; not yet a validated, broad complex-mechanical-engineering leaderboard.** The data and answer contract are provider-neutral. Fair comparison still requires a common execution harness and review procedure; the dataset alone does not supply those.

This audit read the v1.3 package, verified its checksum manifest and ran the shipped numerical scorer with exact evaluator-visible answers and no workflow artifacts. It made no model calls, no FEM solves and no changes to the released package. The answer probe is a scorer test, not model performance. Build-time CAD validity and convergence-study results were inspected in their records, not independently rerun here.

## Verified data

| Property | Checked result |
|---|---:|
| Checksummed files | 779, all match |
| Active tasks / graded outputs | 126 / 308 |
| Engineering-family labels | 11 |
| Supplied-CAD track A / reconstruction track B | 117 / 9 |
| Reconstruction tasks with geometry gates | 9 / 9 |
| Tasks marked independently reproduced | 16 / 126 (12.7%) |
| Original evidence files in release records | 477 |
| Exact-answer-only probe | 126 numerical matches, 0 workflow verifications, 0 passes |
| Task source metadata marked nonredistributable | 56 / 126 |

The raw source evidence is hidden under evaluator/, while candidate/ contains CAD or problem/drawing inputs and output definitions. Raw FEM fields are not necessary in the model-visible inputs, but they must stay available to the evaluator. Some references are source field extrema or rounded plot legends, some are publisher tables, six are calibration targets and four are closed forms. They should not all be described as full saved FEM solutions.

The current active physics include linear static analysis, modal analysis, elastic buckling and nonlinear transient heat conduction. Four fcVM tasks are **linear eigenvalue buckling**, not validated plastic-collapse or nonlinear post-buckling tasks. A thermal valve and multi-region structural models provide useful complexity. Solid-region counts, such as the plate girder's 104, are not proof of 104 physical assembly parts or contact mechanics.

## Readiness gaps

1. **No common multi-model runner or automatic execution sandbox is included.** score.py checks scalar values, files, CAD and trusted reviews. It does not execute candidate code, verify solver logs or extract quantities itself. Human review can support a pilot if reviewers are blinded to model identity and apply the same checklist. It is not an automated evaluation.
2. **The mix remains dominated by three bracket/plate families:** SimJEB 36, AgentFEM 32 and GeoPINONet 16 = 84/126 (66.7%). A family macro-average helps weighting but does not add physics or engineering diversity. Contact, plasticity, fracture, forming, crash and fatigue are absent from the active scored set.
3. **110 tasks lack recorded independent reproduction.** Empirical convergence bands on selected parts are useful evidence, not rigorous uncertainty bounds. Most other tolerances remain provisional. Reproduction of selected displacement/eigenvalue quantities does not validate every field, geometry interpretation or source-model assumption.
4. **Geometry gates are necessary rather than complete validators.** They check volume overlap after translation and one of 24 proper axis rotations. They do not accept arbitrary orientation, establish exact topology/features, or prove that the FEM mesh and boundary conditions correspond to the submitted part. A 2% relative symmetric-volume threshold can tolerate small but mechanically significant feature changes. These must be checked in the workflow review.
5. **No private hold-out or model/expert comparison is recorded.** Public sources can be memorized or present in training data. Separating public task IDs into another file does not make them private. Calibration tasks should be reported separately.
6. **Two stale release labels remain:** the actual scorer emits `version: 1.1` on a v1.3 evaluation, and REVIEW_PROTOCOL.md says zero tasks independently reproduced despite metadata listing 16. Correct these before using result files in a leaderboard. The previous reference-class-count discrepancy is fixed: active classes total 308.
7. **The standard artifact contract does not guarantee identical model capabilities.** Python main.py is a common entry point, but models need equal access to CAD import, meshing, FEM solvers, code execution and image inspection. A text-only model without image tools cannot be evaluated on drawing tasks under the same capability assumptions as a vision-capable agent.

The working interpretation of “all frontier models” should therefore be **all participating model versions under the same defined agent/tool protocol**, not a claim that every current model/provider has already been connected or evaluated. No such coverage was tested in this audit.

## Recommended common evaluation protocol

- Pin a model identifier/version, provider, date, agent scaffold, prompts and tool definitions. Record reasoning settings where available and disclose differences that cannot be equated across providers.
- Use one isolated CAD/FEM environment with fixed solver/kernel versions, CPU/RAM, installed libraries, working-directory rules and network policy. Give each task a fresh workspace containing only its candidate files. Keep evaluator targets, evidence and reviews inaccessible to the agent.
- Separate supplied-CAD and drawing/specification reconstruction scores. Keep NAFEMS calibration separate from challenge scores. If input/tool capability differs, label a separate condition rather than comparing an unassisted text model to a tool-enabled agent.
- Fix wall-clock limits, tool-call budget, retry policy and sampling seeds/repetitions. Record tokens, elapsed time, API cost and failure type. Raw token counts alone are not equivalent compute budgets across model families.
- Require the same eight artifacts and quantity definitions. Evaluate numerical accuracy, geometry quality and reviewed workflow completion separately; report end-to-end pass only when all required checks pass. Until a sandbox runner exists, use blinded, reproducible reviewer decisions tied to run/task/artifact hashes.
- Publish per-task results, family macro-averages and uncertainty across repeated model runs. Do not infer independent statistical samples from load cases, meshes, modes or related CAD variants.
- Add an expert baseline under the same task/tool/time constraints. An existing solver-reference study is not a human expert baseline or a frontier-model run.
- Build a genuinely unpublished/private evaluation pool with documented CAD/FEM provenance and rights before making contamination-resistant generalization claims.

## Balanced pilot preview

This audit provides `balanced-pilot-task-ids.txt`: a deterministic **41-task selection across 10 non-calibration family labels**, capped at five tasks per family. It preserves reconstruction tasks and reproduced cases first, then uses task ID order. Six NAFEMS calibration IDs are in `calibration-task-ids.txt`.

This is a **selection preview**, not a validated diversity sample, new official release or standalone scorer input. Forty-one tasks do not mean forty-one distinct engineering problems. Geometry-based diversity selection within the large families and an explicit model-run protocol are still needed. To score a subset correctly, tasks and references must be filtered together while preserving the evaluator evidence paths and unchanged task hashes.

## Outcome

Start comparative pilot runs only under a fixed common environment and review protocol. The package supports CAD/FEM accuracy experiments today. Broad claims that a model can solve all kinds of complex engineering problems, or a fair ranking of all frontier models, are not supported yet.

Evidence: `audit.json` contains the verified counts and actual answers-only probe. The frozen v1.3 package was left unchanged.
