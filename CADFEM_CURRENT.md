# Current CADFEM release

Use **cadfem-bench-v1.7/** or **cadfem-bench-v1.7.zip** for the corrected source-only pilot: 54 primary tasks and 118 graded outputs. The matching folder and ZIP are in cvpr2027/output/datasets/. The 64-page atlas is cvpr2027/output/pdf/cadfem-bench-v1.7.pdf.

The earlier cadfem-bench-final and v1.6 packages are preserved historical snapshots, superseded after the provenance and general-rotation audit. They must not be described as the corrected release.

Existing 46-task GPU runs use v1.5. Preserve and report them as historical pilots. Do not mix their totals or timings with a v1.7 leaderboard. The updated local openweight/score_openweight.py reports dataset version, task-set hash, numerical pass, replay-verified numerical pass and trusted workflow pass separately; shared-GPU timing is descriptive unless comparable resource conditions are independently established.

Only 14 of the 54 primary tasks have independent FEM reproduction. Remaining tolerances are provisional, workflow review is still required, and the public reserve is not a contamination-proof private holdout. These limitations are not claimed solved.

## Challenge extension (2026-10-15)

`cvpr2027/output/datasets/cadfem-challenges-v0.1/` and its ZIP add 10 held challenge candidates curated from the existing web source library: six nonlinear fcVM paths, Fin Ray contact, Kresling snap-through, bolted-flange thermal contact, and layered-pipe response. Original CAD/setup/result assets are bundled evaluator-only. These are untested difficulty hypotheses, not confirmed Astra failures; no additions to the 54 scored primary tasks. See the extension README and per-task admission blockers.

Challenge extension update: `cvpr2027/output/datasets/cadfem-challenges-v0.2/` supersedes v0.1 for challenge collection work. It contains 18 held candidates (8 added), including composite impact/random vibration/thermal/cyclic cases, quadcopter modal analysis with original dimensioned drawings, wing prestressed modes, brake thermal response and a nozzled pressure vessel. These curate previously collected web sources; none is yet scored or an observed Astra failure.

## Astra failure cases (2026-10-15)

`cvpr2027/output/datasets/astra-failure-cases-v0.1/` (+ ZIP) collects every recorded GPT-6 Astra miss, re-checked against the saved runs: 5 admitted failures (3 CAD-edit answers that do not run or parse, one of which still leaves its boss floating after repair; one silent wrong pipe-network verdict; frame analysis declined on 3 of 4 samples at 21 members), 1 unconfirmed, 36 excluded. Of the 35 audited CAD-edit misses, 32 are our reference defects, impossible tasks or ambiguous instructions; this reclassifies the connecting-rod and twisted-bracket cases in output/audits/astra-failure-search-20261015. The challenge candidates above remain untested on Astra and are not failure cases. Rebuild: `tmp/cq-env/bin/python scripts/build_astra_failure_cases.py` (from cvpr2027/).
