# GPT-6 Astra spend on CADFEM-Bench v1.5 (cap: $10 total; prices counted conservatively: $12.50/M uncached in, $1/M cached, $50/M out)

| item | USD |
|---|---:|
| invalid attempt (harness relative-path bug), 4 tasks, discarded | 1.53 |
| pilot, 5 tasks (all scored) | 3.09 |
| stopped full-run tasks (CADWORLD, Coupler, Bar_buckling, GEOPINO-1), not scored | 1.38 |
| first, stopped attempt at A-VALVE-transient (transcript removed on restart; cost recorded here) | 1.01 |
| hardest-task run: A-VALVE-transient 1.32 + A-FCVM-PL-Wyk_Rohrstoss_ring 1.65 (B-RIGGING-test1 not run: cap reached) | 2.97 |
| **total** | **9.98** |

## Known task defect found during the Astra run (2026-10-15)

A-CADWORLD-001's prompt (v1.0-v1.5) states the publisher mesh used first-order tetrahedra. The publisher FCStd stores
ElementOrder as enumeration index 1 of ["1st", "2nd"], i.e. second-order. Independent check on the supplied part with the
stated loads: first-order 20.27 mm (= Astra's submitted value), second-order 31.03 mm (publisher 31.1 mm). Astra followed the
prompt correctly; its CADWORLD-001 "failure" is a benchmark error and is excluded for every model in this round. Builder fixed
(scripts/cadfem_bench/fam_cadworld.py); the next release must carry the corrected prompt.

## Astra (medium effort) results, scored with the v1.5 evaluator (2026-10-15)

| task | result |
|---|---|
| A-CYC-Disk-PETGCF | PASS, +0.6 % |
| A-AGENTFEM-fresh_test_000 | PASS, -2.1 % / -2.0 % |
| A-FCVM-Buckling | PASS, -0.6 % (outputs in <task_id>/ subfolder) |
| B-FEMCAD-062 | PASS, +2.2 %, geometry gate OK |
| A-ASTER-SSLP311-theta15 | PASS, -0.1 % / -0.1 % (outputs in <task_id>/ subfolder) |
| A-VALVE-transient | PASS, all 6 outputs within 1.4 % |
| A-FCVM-PL-Wyk_Rohrstoss_ring | PASS, +0.4 % (clean replay) |
| A-CADWORLD-001 | excluded (task defect above) |

7/7 valid tasks pass numerically. No genuine Astra failure was found within the $10 cap. Budget exhausted; no further paid calls.

## Separate $2 budget: pipe-network confirmation (2026-10-15, user-approved "spend 2")

runs/network-astra-confirm-20261015 (scripts/network_astra_confirm.py; same prompt, model, medium effort, no tools as 27 Sep).
Hard stop: no call started with < $0.65 left; per-call token cap lowered to fit the remainder. Spent $1.59 of $2.00.

| task | result | cost |
|---|---|---:|
| net-pipe_network-0003371ea274123f:edit-4 (the 27 Sep miss), sample 2 | correct: J4 19.23 m, fail | 0.53 |
| net-pipe_network-3a475478acab117e:edit-4 (hard, 8 loops, -2.6% margin) | correct | 0.73 |
| net-pipe_network-5e15f34bdaf61a92:edit-1 (4 loops, -1.9% margin) | correct | 0.34 |

The 27 Sep miss did not reproduce (1 wrong of 2 samples). No new failure found.

## Agentic recheck of Codex's single-shot failure (2026-10-15; user: "check with astra, use as few credits as possible")

runs/hosted-v1.5/runs/gpt-6-astra-medium-girder, same harness/protocol as the v1.5 Astra runs (medium effort, tools, feedback), $2 cap.

| task | result | cost |
|---|---|---:|
| A-FCVM-Plate_girder_EC3 | PASS: lambda1 0.41406 vs published 0.41191 (+0.5 %, tol 5 %); 12 calls, 15.5 min | 1.14 |

Codex's single-shot, low-reasoning, 6,500-token, no-repair attempt reported 1.92 (the second mode). Under the agentic
protocol Astra finds the first mode, so this is a restricted-protocol failure, not a capability failure.
| MechDesign-Bench SJ-1500-HP-TIGHT (runs/mechbench-astra), scissor-jack design | PASS all 7 grader checks: 2.414 kg <= 2.62 kg, yield FS 1.72, buckling FS 3.27, 1 DOF, 104-385 mm; 12 calls, 7.8 min | 1.24 |

Harness bug found: the clean replay ran `python -I -B main.py`; -I drops the script's folder from sys.path, so helper .py
files next to main.py (allowed by the contract) could not be imported. Astra's jack failed replay only for this reason.
Fixed to `-E -s -B` in scripts/cadfem_bench/openweight/cadfem_agent.py; the saved submission was re-replayed (no API
call) and passes. The original replay is kept as replay-isolated-flag-bug/. The H100 server's frozen harness copy still
has -I: open-weight replays that import helpers must be re-replayed.

Today's check total: $2.38 (girder 1.14 + jack 1.24).

## SimJEB adjudication and corrected-prompt Astra run (2026-10-15; user: "use credits only when necessary")

| item | result | cost |
|---|---|---:|
| SJB-ANALYSIS-101-FIXED (runs/astra-complex-20261015): v1.7 prompt with only bolt 1 corrected to 10.668 mm | 3 of 4 within 10 %; diagonal +11.0 % vs published, but within 0.5 % of our extrapolated converged value | 1.78 |
| SJB-REDESIGN-121 | not started: watcher stopped the harness before its first API call | 0.00 |

Findings (free local checks): (1) the v1.7 SimJEB prompts state 10.3124 mm for all four bolt holes, but hole 1 at (0, 0)
is 10.668 mm in the supplied STEP; Astra's radius filter therefore left bolt 1 unconstrained (0 of 517 wall nodes
fixed), doubling the displacements in Codex's rechecks. (2) The published OptiStruct maxima are first-order values about
5-10 % stiffer than the converged solution (our P1 re-solve rises 1.6-2.8 % from 1.2 to 0.9 mm). Neither is an Astra
capability failure. Evidence: runs/astra-complex-20261015/refstudy/.

Today's Astra check total: $4.16 (girder 1.14 + jack 1.24 + SimJEB 1.78).

## Pattern-based failure hunt (2026-10-15; user: "credits only when necessary"; round cap $2)

| item | result | cost |
|---|---|---:|
| 15 ghost-geometry CAD-edit traps (scripts/astra_traps/ghost_geometry.py; one-shot, medium, 6k cap) | 13 pass; 2 bored-apex flags are threshold calls (boss deliberately sunk 1.3-1.6 mm), not clear failures | 0.24 |
| eng-frame-bench-xxl fivebay_five_generate (55 members, indeterminacy 75; no tools, 16k cap) | declined: status "unavailable", no numbers | 0.60 |
| eng-frame-bench-xxl fourbay_four_generate (36 members, indeterminacy 48) | declined: status "unavailable" after 1,153 reasoning tokens | 0.50 |

Round total $1.33. Unaided frame analysis is the one failure that reproduces: declined 3/4 at 21 members, 1/1 at 36, 1/1 at 55.

## Ten-task large-frame check + two nonlinear tasks (2026-10-15; user: "find 10 such tasks and chk with astra")

| item | result | cost |
|---|---|---:|
| 8 large frames (36-55 members, no tools, 16k cap; runs/astra-frames10-20261015) | 8 of 8 declined (status "unavailable"); 2 setback frames not run (cap) | 5.16 |
| NL-ELASTICA-CANTILEVER (agentic; exact elastica 8103.2 / 5544.0 mm, SOFiSTiK BE7) | PASS +0.02 % / +0.02 %, 6 calls | 0.28 |
| NL-HERTZ-HEMISPHERE (agentic; Hertz a = 1.1757 mm, p0 = 3454 MPa) | PASS +0.07 % / -0.09 %, own active-set contact solver, 9 calls | 0.41 |

Large unaided frame analysis: declined 10 of 10 (36-55 members). With tools, Astra passed every complex task tried.

## Varied single-call tasks, no tools (2026-10-15; user: "variety ... use as few credits as possible"; cap $3)

runs/astra-variety-20261015 (scripts/astra_traps/variety_tasks.py, heat_fin_fenicsx.py); references checked by equilibrium,
mass orthogonality, subdivision convergence (and the Euler cantilever), and FEniCSx P2 mesh convergence.

| task | result | cost |
|---|---|---:|
| VAR-SPACE-TRUSS (78-member 3D tower) | correct to 0.0 % | 0.47 |
| VAR-SHEAR-BUILDING-MODES (8 DOF) | correct to 4 decimals | 0.18 |
| VAR-PORTAL-BUCKLING (2-bay frame, lambda 9.8696) | correct (9.87) | 0.55 |
| VAR-L-FIN-HEAT (2D conduction + convection) | correct (+0.1 % / -0.1 %) | 0.42 |

Round total $1.62. Without tools Astra solves these; it declines only the large rigid-jointed frames (36-55 members).

## 3D CAD + FEM no-tools check (2026-10-16)

| task | result | cost |
|---|---|---:|
| SOLID-L-BRACKET (filleted L-bracket; ref 0.4468 mm, 161.3 MPa, FEniCSx P2 converged) | declined both values: "Not computed; a numerical elasticity solution is needed" | 0.03 |
| SOLID-KEYED-SHAFT-TORSION, SOLID-STEPPED-SHAFT | not run: API returned "no credits remaining" (no charge) | 0.00 |

The OpenAI account behind OPENAI_API_KEY_SVG_NEW is now out of credit. api_error records were removed so a later run retries both tasks.
