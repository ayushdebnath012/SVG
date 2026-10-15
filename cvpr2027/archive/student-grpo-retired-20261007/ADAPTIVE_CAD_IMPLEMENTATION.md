# Experience-guided adaptive CAD graph

This is an executable implementation of the requested CAD pipeline. The entry point is `cvpr2027/scripts/run_adaptive_cad.py`. It includes live Astra planning and patch generation, a persistent frozen-GRPO verifier adapter, and an offline replay mode. Replay runs exercise orchestration with recorded/scripted candidates and **are not fresh Astra benchmark results**.

## Implemented stages

| Requested step | Implementation |
|---|---|
| Decomposition | Live Astra produces edit steps, invariants and dependencies; replay uses instruction clauses |
| Experience retrieval | Deterministic lexical similarity over versioned successful task/repair records |
| Initial CAD state | Native CadQuery execution of the source and saved initial patch |
| Diverse hypotheses | Astra proposes a feature/operation hypothesis and a complete original-index patch; siblings are included to discourage duplicates |
| Adaptive GoT | Directed acyclic state graph, exact candidate+depth reuse, progressive widening |
| MCTS / best-first | Selectable frontier controller; UCT updates only traversed edges, including when a node has multiple parents |
| Hierarchical verification | Geometry and explicit constraints, then semantics, then conditional FEM and robustness |
| Candidate scoring | Hard feasibility gates, semantic confidence, robustness and edit-size objectives |
| Failure / repair / backtrack | Structured failed-stage diagnoses, repair retrieval, parent/sibling frontier selection and new branches |
| Candidate bank / Pareto | Store feasible alternatives; remove dominated objective vectors; deterministic score/depth/id tie-break |
| Final robustness | Fresh execution and separately declared perturbations; failed candidates return to graph search |
| Final CAD | Original-index patch, executable `final_cad.py`, and `final_cad.step` |
| Experience updates | Successful verified trajectory persisted; future tasks can retrieve it under the chosen memory policy |

MCTS is part of graph exploration. Pareto selection chooses among verified graph results. Full-state reuse is conservative: exact patch bytes at the same depth can share a node; merely similar geometry cannot. Edge statistics are separate, and depth prevents cycles. A final verification failure excludes that node from the final bank while leaving repair possible.

## Run a real CAD/FEM integration example without API charges

From the repository root, use a fresh output path:

```sh
python3 cvpr2027/scripts/run_adaptive_cad.py \
  --task cvpr2027/experiments/adaptive-cad-integration-20261007/task.json \
  --replay cvpr2027/experiments/adaptive-cad-integration-20261007/candidates.json \
  --out cvpr2027/experiments/adaptive-cad-example \
  --memory cvpr2027/experiments/adaptive-cad-example-memory.jsonl \
  --algorithm mcts --max-expansions 4 --seconds 300
```

Use `--algorithm best-first` for the other controller. `result.json` contains every state, edge, diagnosis, search path, final check, memory version and selected candidate. With no fully verified candidate, status is `UNVERIFIED`, the saved initial patch is retained, and no successful trajectory is written.

## Live Astra and frozen GRPO

Configure `OPENAI_API_KEY` in the process environment. Omit `--replay`, set an explicit `--api-budget` and `--max-api-calls`, and supply the same task/output/memory options. Both decomposition and generation count against the API budget. No paid calls are made by the tests or replay mode. Credentials are never written to the request ledger.

For general language tasks, use `--semantic-command` with a JSON array of command arguments that starts the existing `mcts_verifier_worker.py`, locally or through SSH, and `--calibration` with a frozen development calibration. For example, an already-authenticated SSH command can start:

```text
cd /home/trishita/svg-compute/agentic-verifier-grpo-20261006/scripts && CUDA_VISIBLE_DEVICES=1 /home/trishita/miniconda3/envs/engsvg/bin/python -u mcts_verifier_worker.py /home/trishita/svg-compute/agentic-verifier-grpo-20261006/run-v4/adapter
```

The command must use the worker's JSONL ready/rows/results protocol. SSH authentication must be configured separately. The worker is closed when the run ends. A failed or missing semantic verifier yields `UNKNOWN`. This implementation reuses the frozen GRPO verifier; it does not retrain Astra, the verifier or a new search controller.

API rates used by the ledger are the verified Astra rates ($10 input, $1 cached input, $12.50 cache-write, $50 output per million tokens), from https://developers.openai.com/api/docs/models/gpt-6-astra. Reservations use the higher input rate and maximum output allowance; uncertain failed requests retain their reservation and are not silently retried. Pricing is an estimate rather than an invoice. HTTP integration is tested with mocked responses; no new live API experiment was performed for this implementation.

## Task and physical contracts

See the saved example `task.json` for the complete schema. Mandatory fields are `id`, `code`, and `instruction`. Optional `candidate` is the saved complete patch; otherwise the root is a no-op patch. Top-level reference code, geometry scores and correctness labels are discarded at ingestion.

Explicit constraints support `volume`, `area`, `solids`, `faces`, and `bbox_x/y/z`, with `equals` plus absolute/relative tolerance, `min`, `max`, or `preserve_source`. They are measured from the executed solid. Numeric literals found in the instruction are only heuristic evidence for the learned verifier.

For fully specified synthetic tasks, `semantics: {"mode":"explicit_constraints","complete":true}` asserts that the caller's measurable constraints cover the entire instruction. This is an explicit contract, not a learned semantic verdict, and must not be used for underspecified BenchCAD tasks. The planner cannot grant itself this assertion.

All five stages are required by default. A task may explicitly restrict `required` to geometry, constraints and semantics if physical certification is outside its scope. Missing required contracts or solver failures never become passes.

The FEM backend currently supports isotropic linear tetrahedral elasticity, with a fixed lower band and axial force distributed on an upper band. The contract declares Young's modulus (MPa), Poisson ratio, force (N), axis, band fraction, mesh size (mm), fixture name and metric limits. It reuses the existing solver's validity, equilibrium, energy and anchored-component checks. It does not infer operating loads or claim nonlinear/contact/fatigue validation.

Robustness varies `force_scale`, `young_scale` and `mesh_scale`. `search_variations` and `final_variations` are declared before search; final verification requires at least one perturbation absent from search. An empty or unsupported perturbation set remains unknown. Geometry-tolerance perturbations and other fixture families require additional adapters.

## Memory and evaluation isolation

Memory is loaded once per task. Frozen mode retrieves only training/development successes and excludes the current task/component. Held-out successes are written to a separate `.quarantine.jsonl`, never added to frozen retrieval. Online mode permits prior task successes and must be reported as a chronological protocol. Memory writes are intended for serial task execution; concurrent writers need a database/lock adapter. Retrieval is lexical and can be replaced with embeddings later.

The planner receives only whitelisted source/instruction/contracts and permitted experiences. Reference scoring remains a separate offline procedure. No held-out threshold tuning or benchmark improvement is claimed. The existing completed results remain Astra 89/124, earlier single repair 91/124, and bounded MCTS 89/124.

## Validation

```sh
python3 cvpr2027/scripts/test_adaptive_cad.py
```

Tests cover graph sharing, path-only statistics, backtracking after a final-check failure, Pareto filtering, unknown propagation, frozen-memory exclusion, reference-field filtering, budget refusal before dispatch, API usage accounting and JSONL verifier integration. Native integration runs use real CadQuery and FEM with scripted candidates; task/response fixtures and measured results are saved under `experiments/adaptive-cad-integration-20261007`.

The existing CAD executor uses AST restrictions and process timeouts. It is designed for the trusted CAD corpus and is not an operating-system sandbox for arbitrary hostile programs.

## Server installation

Installed under `/home/trishita/svg-compute/adaptive-cad-20261007` on `10.71.9.40`. The server's existing CadQuery interpreter is reused; missing FEM packages live only in this bundle's `dependencies` directory. `scripts/server_run_adaptive_cad.sh` sets the interpreter and dependency path. Supply normal task/replay/output/memory arguments to that launcher.

The first server smoke run recorded UNKNOWN for FEM because the pip target layout omitted Gmsh's native library. The matching library was extracted from the downloaded wheel into the isolated dependency directory; `server-native-verified` then passed all stages and exported STEP. The failed setup record is retained separately.

A separate `server-grpo-smoke` run exercised the real frozen 1.5B GRPO adapter on one development task with a replayed candidate. Geometry, constraints and calibrated semantic gating passed; this task explicitly excluded physical certification because no physical contract was supplied. The final calibrated confidence was 0.901813 against the unchanged threshold 0.901613. No live Astra calls or new benchmark evaluation were involved.
