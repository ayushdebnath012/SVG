# Status and rules of interpretation

This document separates completed diagnostics, runnable reproductions and designed future experiments. A planned experiment has no result. A working script is not evidence that a model was trained or that a comparison was completed. The machine-readable registry is `experiments/registry.json`; `scripts/experiments.py list` shows statuses and commands.

The main scientific question concerns numerical and visible semantic correctness after engineering-drawing edits. The existing Qwen compact-DOM pilot is a separate infrastructure check. Every main result must identify the physical case, request, model/configuration, solver reference, artifact and evaluator version.

# Completed experiments

| ID | Scope | Evidence | Important limit |
|---|---|---|---|
| C01 | Evaluator and edit-policy regressions | 30 passing tests | Tests cover implemented scope, not all SVG semantics. |
| C02 | Manufactured contour corruptions | 160 controls; numerical audit accepts 20/120 corruptions | All remaining false accepts are wrong labels. |
| C03 | Historical v3 re-audit | Six attempts, three strict geometric passes | Corner and mask effects prevent blanket physics-failure claims. |
| C04 | Rule baseline | 60/60 test and 60/60 annulus | Shared templates make this pilot trivial. |
| C05 | A100 LoRA training | Three seeds, three epochs, 90 steps each; final adapters saved | Same perfect scores as the rule baseline. |
| C06 | Astra API recheck | Four completed calls with raw responses and token usage | One sample per condition; not a failure-rate estimate. |
| C07 | Independent Robin FEM | Five mesh resolutions, analytic anchor, heat balance | Mesh differences are estimates, not certified error bounds. |
| C08 | Direct FEM contour scoring | Maxima 0.111 and 0.374 degrees Celsius | Finite geometry sampling does not certify the entire drawing. |
| C09 | Historical capacitor path audit | 12 open field paths; no alleged closed loops | Source-specific geometry check, not electrostatic validation. |
| C10 | Upstream FEM-Bench SVG bridge | Two upstream tests and 24 FEM solves | A one-dimensional integration anchor only. |

Rerunning CPU reproductions should write to a new directory. Preserve original measured outputs and manifests. API or GPU repeats require an explicit job command; the default runner never launches them automatically.

# P01: numerical reference suite

**Purpose:** establish trustworthy references before model scoring. Status: designed; Robin anchor implemented, other families incomplete.

Heat: steady two-dimensional conduction on rectangles and nonconvex domains with Dirichlet, Neumann and Robin boundaries. Record conductivity and length units. Validate Robin signs and corner treatment using an analytic manufactured case and boundary-flux balance. Use at least three mesh resolutions; choose the final resolution based on field and relevant contour-point convergence.

Elasticity: finite plates with holes and rounded brackets, with explicit geometry, Young's modulus, Poisson ratio, plane-stress/plane-strain choice, support model and distributed traction. Check displacement, force balance, free-surface traction and stress recovery. Treat sharp-corner peak stress as unresolved unless the problem explicitly asks for a singularity/disclosure response. Use the exact finite geometry rather than substituting a remote infinite-domain formula.

Electrostatics: specify 2-D cross-section or 3-D conductor geometry, thickness, potential values and the exterior boundary model. Perform both mesh and exterior-domain refinement. Check conductor potential, symmetry, charge/flux balance and orthogonality of field lines and equipotentials. An image that ends its contours inside the canvas does not define behavior at infinity.

**Acceptance:** reference metadata, physical-balance checks, convergence tables and numerical-error estimates accompany every case. Cases with unresolved reference uncertainty remain in a separate diagnostic set and do not become hidden failures or exclusions.

# P02: claim schema and complete verifier

**Purpose:** bind visible content to physical quantities. Status: partial geometric implementation; semantic and occlusion coverage planned.

Specify solution identifiers, quantity names, units, contour levels, coordinate maps, label anchors and legend mappings. Define invalidation for geometry, material, loads and boundary-condition changes. Add tests for ancestor transforms, wrong scalar/tensor quantities, altered units, stale solution records, missing contours, hidden layers, clipping and label/legend mismatch.

Measure false acceptance on both malicious and accidental corruptions. Include honest edits that should be permitted, such as changing an incorrect label to the correct value. Do not rely on a string hash as evidence of visible equivalence. Unsupported features receive an explicit status rather than a silent pass.

**Acceptance:** the checker rejects its specified corruptions and accepts matched honest counterfactuals; unsupported features and remaining blind spots are documented. A full-drawing certificate must not be reported until its visible-semantic scope is actually implemented and validated.

# P03: main case and edit collection

**Purpose:** avoid a shared-template benchmark that a rule parser solves. Status: designed.

Proposed initial collection: 240 physical cases across three families, split before generating edit variants into 120 training, 48 validation and 72 test cases. These are planning counts and may change after a reference-only feasibility pilot; record any change before model comparisons. Store separate geometry-family and instruction-template holdouts rather than calling every new parameter value out-of-distribution.

Each case should include presentation edits, label/legend edits, a physical-input edit, an under-specified request and an honest/misleading counterfactual pair where appropriate. Use independent human-written language or externally sourced editing requests for part of evaluation. Retain one instruction provenance record per request. Do not train on the test references' prompts, outputs or inspected failure corrections.

**Acceptance:** no physical-case leakage; reproducible seeds; reference eligibility fixed; editing instructions require context beyond keyword routing; task counts and exclusions are recorded before evaluation.

# P04: primary model and deterministic comparisons

**Purpose:** test whether the proposed representation helps at equal information. Status: designed.

| Baseline | Input and freedom | Main comparison |
|---|---|---|
| Direct Astra | Physical task and drawing; generates/edits SVG | Unaided final-artifact fidelity. |
| Solver-informed unrestricted editor | Same numerical solution supplied; unrestricted SVG edits | Value of enforced protection beyond solver access. |
| Published solver-agent workflow | Pinned runnable MechAgents/MCP-SIM/OASiS adaptation | End-to-end engineering workflow comparison. |
| Protected geometry only | Numerical path protection; weaker annotation binding | Contribution of semantic checking. |
| Joint geometry and semantics | Proposed representation and final verifier | Full proposed method. |
| Deterministic solver plot / template | Solver-owned geometry and labels | Necessity and usefulness of learned drafting. |
| Rigid freeze baseline | Minimal permitted style changes | Safety versus editing flexibility. |

Use identical physical specifications, references and requests where applicable. Label differences in solver access explicitly. Preserve all attempted outputs, including invalid SVG and API failures. API failures are operational outcomes, not evidence of PDE incapability. Record model revision/alias, effort, token cap, endpoint, wall time and usage.

**Acceptance:** per-case results for every baseline and the complete attempted denominator. No aggregate success claim from only successfully rendered or numerically supported cases.

# P05: training study

**Purpose:** test a learned improvement on a task that needs it. Status: designed; the earlier template pilot is complete but does not answer this question.

Start only after P03/P04 show a gap beyond the rule and deterministic controls. Train the base model and final SFT policy with the same executor and information. Record the source, filtering and label-generation process. Use completion-only supervision for structured actions when appropriate. If the main claim is multimodal, select a model that genuinely sees the image or complete graphical representation; do not relabel a compact DOM index as vision input.

Choose a small validation-driven hyperparameter search before a three-seed final configuration. Record every tried configuration. Keep the evaluation set fixed. Report strict output validity, instruction success and physical correctness separately. Compare base, prompting-only, SFT and deterministic policies. Reuse A100 for compatible small-model runs; choose larger hardware only after measuring memory and throughput needs.

**Acceptance:** a reproducible, useful held-out gain; or a documented negative result. Perfect performance on shared templates is not a trigger to scale training.

# P06: sequential physical and visual edits

**Purpose:** expose stale fields and broken bindings across turns. Status: designed.

Create prespecified sequences of five edits: presentation change, physical parameter change, annotation rearrangement, geometry or boundary change, and a request that could reuse an old claim incorrectly. Include shorter two-edit anchors for debugging. Every physical change must invoke a real solver and produce an updated reference record; rerouting alone does not count.

Track per-step success, first failure, stale-solution acceptance and final visible correctness. Also track cumulative latency and solver calls. Reusing cached solutions is permitted only if the physical specification is unchanged and the cache key identifies the complete problem.

**Acceptance:** complete sequence traces, actual solver evidence, and results against a deterministic replotting baseline.

# P07: ablations and robustness

**Purpose:** identify which components explain any improvement. Status: designed.

Remove, one at a time, the solver record, protected geometry, unit binding, legend binding, visibility checks and post-edit verification. Compare path-string freezing to transformed-geometry checking. Evaluate instruction paraphrases, changed element IDs, nested transforms, alternate layout templates and previously unseen geometry families. Include beneficial semantic corrections as well as deceptive edits.

Do not retrofit corruptions solely around known strengths of the proposed verifier. Freeze a public development set and a separately constructed evaluation set. Explain each ablation's changed capabilities so that losing useful edit freedom cannot masquerade as a better safety method.

# P08: drafting and visible correctness assessment

**Purpose:** establish visual usefulness for a CVPR submission. Status: designed.

Prepare anonymized, randomized outputs from matched cases. Ask raters to judge instruction fulfillment, readability, numerical-label consistency and suitability for the specified drafting task. Use three independent raters where feasible, report agreement, and include the exact rubric. Choose the assessed sample before viewing preferred-model outcomes. Report numerical audits separately from visual ratings; an attractive drawing can still be physically wrong.

Use a pilot to estimate time and reliability before fixing the final sample size. The current package contains no completed human study or fabricated ratings.

# Metrics and uncertainty

Report curve-field mean and maximum error normalized by an explicitly specified field range, required-level coverage, unsupported samples, quantity/unit/legend errors, edit fulfillment, render validity, rejection/disclosure correctness, solver calls, latency and tokens. State whether errors come from direct FEM evaluation or regular-grid interpolation.

Use physical cases as the resampling unit. Related edits from one case and repeated seeds on the same test set are not independent cases. Report paired case-level differences and confidence intervals when sample size permits. For sequences, resample complete sequences or their source cases. Publish raw values alongside uncertainty summaries.

Separate reference error, output error and operational failure. Report both full-domain metrics and any prespecified singular-region analysis. A posteriori exclusions are diagnostics and must not silently replace the main score.

# Compute and stopping rules

Begin with a small end-to-end feasibility batch. Estimate tokens per case and wall time from that batch before scheduling a large API study. Record a maximum job count and budget in the run configuration. Training jobs should checkpoint and export automatically; the recovered A100 runs demonstrate why local artifact retention is necessary.

Stop or redesign if references are unresolved, a task is under-specified, deterministic controls solve the main task, or the proposed verifier achieves safety only by refusing useful edits. Use validation for model selection. Do not keep sampling until a preferred outcome appears.

# Submission deliverables and dependencies

P01/P02 precede main scoring. P03 precedes P04/P05. P06/P07/P08 support the final contribution claim. A final package needs complete results, limitations, verified bibliography, figure sources, anonymous paper/supplement, licenses and author review. Official registration, paper and supplement dates should be rechecked before submission.

Current status: the documents and experimental infrastructure are packaged; the main benchmark, stronger learned study, full semantic verifier and human assessment remain to be executed. The working paper is explicitly unfinished.
