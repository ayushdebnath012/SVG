# Bounded Astra MCTS pilot

Astra alone: 89/124. MCTS selection: 89/124. Previously completed single-repair loop: 91/124.

Against Astra: 0 recovered, 0 regressed. Against the single-repair loop: 0 recovered, 2 regressed.

240 new API attempts; estimated incremental cost $3.25854. 0 original answers replaced. One invalid reference stays in the 124-task overall denominator and is excluded only from the 123-task valid-reference breakdown.

This is not an equal-compute comparison. No held-out geometry score was used by search, calibration or selection. Candidate selection was frozen before reference scoring. One seed only; multiple-seed and equal-budget controls remain necessary.

See comparison.json, calibration.json, manifest.json, selected.jsonl and per-task.csv for evidence.

Selection failure: 0/240 generated candidates passed the frozen probability threshold 0.901613; the highest fresh calibrated probability was 0.899741. No replacements were eligible. This does not show that all generated CAD candidates were incorrect, or that MCTS generally fails. Candidate geometry correctness was not used to change the gate after the run. Including the successful credential diagnostic, the estimated total charged-project API cost was $3.258853.

All 124 final prediction strings exactly match the saved baseline predictions. Therefore final scoring reuses the baseline pinned-reference native geometry results; no fresh STEP comparison was required. This is an executed search with zero selected replacements, not a new zero-shot Astra generation run.
