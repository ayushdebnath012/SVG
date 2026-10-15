# Astra harder-task trial — 2026-10-15

Selected three existing web-source tasks: plate-girder buckling, combined-load U-channel buckling, and stepped-wing modal analysis. Ran only the plate girder. These are existing v1.7 tasks, not new source discoveries. Other candidates remain untested.

Plate-girder result: single-shot workflow failure. Generated code imported the 104-region STEP, meshed it and ran CalculiX, which produced eight eigenvalues. The script's parser required contiguous BUCKLING and FACTOR on one line; the native output splits and spaces the heading. It therefore raised "No buckling factors found" and produced no results.json. Sandbox exit 1, elapsed 6.46 s; no wall/CPU/RAM limit termination. Frozen inputs/code unchanged. No manual edits or repair calls.

Canonical scorer: 0 numerical passes, 0 verified workflows, 0 overall passes. Missing results prevented valid numerical scoring. Raw first coarse-mesh factor 1.921969 is retained as diagnostic evidence only; it is not a converged submission. Published reference 0.41191 with provisional convergence-based 5% band was withheld from the model.

Generation: model gpt-6-astra, medium reasoning, one call, 8000-output-token cap, finish_reason stop. Conservative token cost $0.402712; separate cache-write reserve $0.035175. Combined session cost including earlier diagnostic at most $0.467200 of $0.75 at configured ceiling prices; provider invoice not independently reconciled.

This demonstrates a failed single-shot attempt. It does not establish inability after repairs and is not comparable with prior 250-call agent pilots. Prompt, response, submitted script, exact input hashes, solver artifacts, sandbox execution and score are preserved here.
