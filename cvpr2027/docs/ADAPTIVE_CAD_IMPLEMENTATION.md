# Astra-only adaptive CAD patch repair

The active pipeline uses frozen Astra for planning, candidate generation, patch repair and rendered-view semantic judgement. CAD execution, explicit constraints, FEM, robustness, search and memory are implemented as tools. There is no local trained verifier, student model or model-training stage.

## Run

### Two-player repair game

Pass `--repair-game` to enable the instruction-conditioned repair game:

```sh
python3 cvpr2027/scripts/run_adaptive_cad.py \
  --task cvpr2027/experiments/adaptive-cad-integration-20261007/task.json \
  --out cvpr2027/experiments/repair-game-example \
  --memory cvpr2027/experiments/repair-game-memory.jsonl \
  --repair-game --algorithm mcts --api-budget 2 --max-api-calls 12 \
  --max-expansions 4 --seconds 300
```

This command makes paid calls within the supplied cap. Implementation validation
does not execute it. Planning, repair, rendered semantic judgement and the
adversarial role share the existing ledger, call cap and deadline. Astra weights
are unchanged. `--cad-python` selects an alternative native CadQuery runtime.

The GoT plan includes nine feature repair alternatives plus syntax/API repair.
MCTS selects a graph path, expands with a replacement patch against the original
source, evaluates the candidate and backs up its utility. Native execution
checks kernel validity and nonempty positive-volume solids. The worker extracts
ordered Python calls, parameter expressions, reference selectors and variable
dependencies from source and candidate; expressions remain static evidence,
not measured feature positions, frames or dimensions.

After native constraints and the semantic gate pass, a separate adversarial
Astra role checks feature type/count, dimensions, placement, frame, orientation,
reference, operation order, scope, construction, dependency and topology.
It receives both programs, feature graphs and native measurements. Specific
counterexamples contain a category, reason and evidence; these become the
diagnosis supplied to the repairer on its next expansion. Required physics
checks run only after the adversarial gate passes. Missing evidence, malformed
answers, exhausted budgets and incomplete attack coverage remain `UNKNOWN`.
Final verification always requests a fresh attack, even for cached candidates.

Each node's verdict records repairer utility (the existing correctness,
confidence, robustness and edit-cost score), verifier utility (counterexample
count), and `bounded_verification` or `continue_or_unverified`. These are search
utilities, not a solved zero-sum game. A passing result means the candidate
survived the implemented gates under the allotted budget; neither a Nash
equilibrium nor globally minimal repair is proven. Geometry alone does not
establish physical validity; FEM retains its explicit contract requirements.
Replay remains the existing offline contract/kernel mode; `--repair-game`
requires a live adversarial role and cannot be combined with `--replay`.

Run `python3 cvpr2027/scripts/test_repair_game.py` for feature dependencies,
malformed-verdict rejection, fresh final attacks, counterexample feedback and
native CAD checks. Also run the existing `test_adaptive_cad.py` regression suite.

From the repository root:

```sh
python3 cvpr2027/scripts/run_adaptive_cad.py \
  --task cvpr2027/experiments/adaptive-cad-integration-20261007/task.json \
  --replay cvpr2027/experiments/adaptive-cad-integration-20261007/candidates.json \
  --out cvpr2027/experiments/astra-only-example \
  --memory cvpr2027/experiments/astra-only-memory.jsonl \
  --algorithm mcts --max-expansions 4 --seconds 300
```

Replay uses recorded candidates and makes no API calls. Its explicit synthetic semantic contract is suitable only when caller-declared measurable constraints fully specify the task. General-language replay without such a contract remains semantically unverified.

For live Astra, configure `OPENAI_API_KEY`, omit `--replay`, and set an explicitly authorized `--api-budget` and `--max-api-calls`. The runner connects Astra's rendered-view semantic judge automatically. Planning, edits, repairs and semantic calls share one budget ledger. No adapter path, calibration file, SSH model worker or training configuration is used.

The server launcher is `/home/trishita/svg-compute/adaptive-cad-20261007/scripts/server_run_adaptive_cad.sh`. It uses the server CadQuery runtime and the bundle's isolated native dependencies. Use the same task, output, memory and budget arguments. No paid experiment is started by deployment or the tests.

## Processing

1. Decompose the task and retrieve permitted CAD experiences.
2. Execute the original source and saved initial candidate.
3. Generate different edit hypotheses as complete patches against the original source.
4. Explore the candidate graph with MCTS or best-first scheduling. Reuse exact states conservatively and retain edge-specific statistics.
5. Check geometry, constraints, semantics, FEM and robustness in sequence.
6. Diagnose failures, retrieve repair examples and generate replacement patches; backtrack when another branch should be explored.
7. Keep feasible candidates, filter the Pareto front and apply the declared tie-break.
8. Perform final robustness checks; return failures to search while budget remains.
9. Export `final_cad.py` and `final_cad.step`, and store successful trajectories for subsequent tasks.

`result.json` records candidates, edges, diagnoses, paths, evidence, memory version and final selection. An empty verified bank yields `UNVERIFIED` and preserves the initial answer. Failed patches are not stacked: each replacement patch addresses the original CAD source.

## Verification scope

Geometry comes from native CadQuery execution. Explicit measured constraints support volume, area, solid/face counts and bounding-box dimensions, with equality, range or source-preservation checks. Numeric instruction checks are heuristic evidence.

Live semantic verification uses Astra's judgement of source/candidate isometric and top views. It is fallible and cannot see every internal feature. A missing semantic verdict is unknown, never silently accepted.

The physical contract declares material constants, units, force, axis, fixture, mesh size and acceptance limits. The current FEM adapter supports isotropic linear tetrahedral elasticity with a lower fixed band and upper axial load. Equilibrium, energy and anchoring are checked. Robustness supports declared load, material and mesh perturbations; final perturbations must include a case not used in search. Missing required contracts or solver failures remain unknown. Other materials, fixtures or geometric-tolerance models require additional adapters.

Memory is frozen per task. Frozen mode retrieves training/development examples and excludes the current task/component. Held-out successes are quarantined from frozen retrieval. Online memory is a separate chronological protocol and must not be confused with a fixed holdout evaluation. Reference solids and labels are excluded from inference and used only for offline scoring.

## Validation and preservation

Run `python3 cvpr2027/scripts/test_adaptive_cad.py`. The suite exercises search/backtracking, graph sharing, Pareto filtering, isolation, native execution, budget accounting and Astra semantic integration with mocked responses. Native replay examples additionally exercise real CAD/FEM and STEP export without API charges.

The pre-removal implementation, manuscript and verifier interface are preserved under `cvpr2027/archive/student-grpo-retired-20261007`. Original experiment results, checkpoints and logs remain in place. Historical results are not relabelled as results of the current pipeline. The active paper retains the recorded Astra-only comparison: baseline 89/124, full graph pipeline 85/124, and post-hoc retrieval-only 94/124.
