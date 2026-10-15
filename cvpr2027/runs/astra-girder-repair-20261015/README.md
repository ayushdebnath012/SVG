# Astra plate-girder follow-up — 2026-10-15

Astra supplied one replacement eigenvalue-parser function after seeing its previous parser and actual CalculiX output. No reference factor or evaluator solution was provided. The replacement was applied mechanically to a copy; all other generated code was unchanged. Original submission remains preserved in the prior run.

Full sandbox replay exited 0 in 20.16 s and produced results, fields, CAD, mesh, log, environment and refinement artifacts. Frozen inputs/code remained unchanged. No resource termination occurred.

Submitted lambda1: 1.919935. Published factor: 0.41191. Relative error: +366.11%, outside the 5% reference band. Canonical scorer: numerical_passed 0, workflow_verified 0, overall passed 0. Thus the parser-only repair removes the execution failure but leaves a numerical failure. Physics/root cause is not independently diagnosed here.

Mesh results: [{"h_mm": 300.0, "lambda1": 1.924299, "status": "buckling_complete"}, {"h_mm": 210.0, "lambda1": 1.919935, "status": "buckling_complete"}]. Model explicitly did not claim asymptotic convergence. Do not treat close agreement of these two coarse meshes as proof of correct setup or sufficient resolution.

Repair call conservative cost: $0.029738. Cumulative session upper-bound spend: $0.496938 of $0.75, including diagnostic, initial code generation and separate cache-write reserve. No further calls made.

This is one hard task after one narrow repair, not a new task and not an unrestricted multi-turn agent evaluation. Selected U-channel and stepped-wing cases remain untested.
