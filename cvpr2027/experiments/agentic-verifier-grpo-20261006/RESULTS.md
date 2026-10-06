# Astra + GRPO-trained agentic verifier on BenchCAD

Completed 6 October 2026. All-task strict success: **89/124 (71.8%) without the verifier → 91/124 (73.4%) with verifier-guided repair**, a change of **+1.61 percentage points**.

Valid-reference result: 89/123 → 91/123; 2 recovered, 0 regressed. One upstream reference is invalid and excluded from the category table below.

| Category | Valid-reference tasks | Astra alone | Astra + agent | Change (pp) | Recovered | Regressed |
|---|---:|---:|---:|---:|---:|---:|
| T1 | 31 | 28/31 (90.3%) | 29/31 (93.5%) | +3.23 | 1 | 0 |
| T2 | 17 | 16/17 (94.1%) | 16/17 (94.1%) | +0.00 | 0 | 0 |
| T3 | 17 | 12/17 (70.6%) | 12/17 (70.6%) | +0.00 | 0 | 0 |
| T4 | 33 | 18/33 (54.5%) | 19/33 (57.6%) | +3.03 | 1 | 0 |
| T5 | 25 | 15/25 (60.0%) | 15/25 (60.0%) | +0.00 | 0 | 0 |

## What was trained

A separate Qwen2.5-Coder-1.5B-Instruct verifier received LoRA GRPO updates; Astra remained frozen. The policy chooses execution, numeric checks, acceptance or rejection, with at least one tool observation required before a verdict. This is a constrained action policy using cached target-free tool observations, not an unrestricted agent that invents verification programs. Training reward is reference agreement; reference geometry and labels are absent from model observations and repair requests.

Training used 726 candidates, with 238 component-disjoint development candidates; none of the 124 held-out tasks entered training. Final run: 600 groups of eight trajectories, 880 optimizer updates, seed 17, float32 on one H100 NVL, 15.8 minutes, 10.6 GiB peak allocated memory. Reload verification passed. Earlier failed pilots and numerical fixes are recorded in PROTOCOL.md and the training archive.

## Verifier quality on held-out valid references

| Verifier | Correct accept | Correct reject | False accept | False reject | Accuracy |
|---|---:|---:|---:|---:|---:|
| Untrained | 0 | 34 | 0 | 89 | 27.6% |
| GRPO | 50 | 21 | 13 | 39 | 57.7% |

Always accepting the initial Astra answer achieves 72.4% verdict accuracy. Compare against that class-imbalance control as well as the untrained policy. Development accuracy was 81.9%, versus 81.5% for always accepting. The trained policy used execution only on the initial held-out answers, never requesting numeric checks.

## Repair and evaluation protocol

The policy requested 60 repairs; 6 repaired candidates were accepted for final output. Repair API statuses: {'completed': 60}. New API cost estimate: $0.7926, using repository list-price estimates ($10/M input, $50/M output), not a billing receipt. A rejected repair retains its original answer. All selection decisions were frozen before the native geometry scorer accessed references.

Success uses strict solid-volume IoU ≥ 0.99999 against pinned released STEP files. It does not establish full instruction compliance, mechanical tolerances or FEM validity. All outputs use the same local BenchCAD holdout; this is not an official leaderboard evaluation.

Paired exact McNemar p=0.5; task bootstrap 95% interval for change: [+0.00, +4.07] pp. This interval resamples tasks, not correlated CAD families; it is descriptive. One seed and adaptive development pilots do not establish a robust GRPO benefit. The end-to-end comparison also adds Astra calls and therefore does not isolate the contribution of GRPO from extra inference compute.

## Artifacts

- `comparison.json`: exact aggregates and uncertainty calculations.
- `per-task.csv`: every task, before/after success, selection and scorer status.
- `training/run-v4/adapter/`: saved GRPO LoRA weights.
- `training/run-v4/manifest.json`: model revision and training settings.
- `training-artifacts.tar.gz`: logs, failed pilots, final weights and training code.
- `repairs/`: API requests, outputs and target-free observations.
- `PROTOCOL.md`: full protocol and development changes.
- `implementation-sha256.json`: implementation checksums.

Server artifacts: `/home/trishita/svg-compute/agentic-verifier-grpo-20261006`. API credentials and SSH passwords are not stored in these artifacts.

## Recovered tasks

- **T4**, `511b48e9304b4f209992476550c822f4f358ec8ccf7756369073dc67ffa908dc`: Add a 45-degree chamfer to all top edges of the connecting rod. The chamfer width equals half the small-end bore radius. The base geometry, big-end through-hole, and small-end bore are unchanged. Final IoU: 1.0.
- **T1**, `1bb334960dd158817d9ab53b44a9ebe04a8719e547ebe807e0884c8a38718119`: Reduce the throat radius from 58.7 mm to 40.0 mm, decreasing the throat diameter from 117.4 mm to 80.0 mm. Final IoU: 1.0.
