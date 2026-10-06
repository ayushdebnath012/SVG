# Astra + CAD verifier: paired saved-run audit

No completed GRPO-trained verifier or Astra GRPO experiment was found. This comparison uses the existing deterministic target-free verifier: execution, numeric instruction checks, geometry consensus and edit size.

BenchCAD training split, Astra low effort: 10 tasks with 4 candidates and 482 tasks with 2 candidates. Twenty tasks lack successful verifier audits and are excluded from both paired columns. Without = candidate index 0; with = verifier-selected candidate. Success = reference solid IoU >= 0.99999. Reference is used only for scoring, after selection. These are training-set diagnostics, not held-out GRPO results.

| Category | Audited tasks | Without verifier | With verifier | Delta (pp) | Recovered | Regressed | Any candidate correct |
|---|---:|---:|---:|---:|---:|---:|---:|
| T1 | 124 | 103/124 (83.1%) | 103/124 (83.1%) | +0.00 | 0 | 0 | 103 |
| T2 | 62 | 62/62 (100.0%) | 62/62 (100.0%) | +0.00 | 0 | 0 | 62 |
| T3 | 75 | 54/75 (72.0%) | 55/75 (73.3%) | +1.33 | 1 | 0 | 56 |
| T4 | 117 | 99/117 (84.6%) | 99/117 (84.6%) | +0.00 | 0 | 0 | 101 |
| T5 | 94 | 57/94 (60.6%) | 58/94 (61.7%) | +1.06 | 2 | 1 | 59 |
| All | 472 | 375/472 (79.4%) | 377/472 (79.9%) | +0.42 | 3 | 1 | 381 |

Selection uses more candidate generations than the first-candidate baseline, so this is the combined benefit of sampling plus verifier selection. No equal-budget random-selection experiment or GRPO update was performed.

Separate held-out baseline: saved multisource-cad-astra-20261004/summary.json reports Astra strict success 89/124 (71.8%) on all retained BenchCAD tasks, or 89/123 (72.4%) excluding one invalid reference. There is no paired held-out verifier result in these artifacts. Do not compare this directly against the training-set percentages above.

Sources: runs/cad-astra-distill-20261004/*/verify.json, runs/cad-astra-distill-n2-20261005/*/verify.json; scripts/cad_edit_verifier.py.
