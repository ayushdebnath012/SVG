# Functional design discovery — completed 22 September 2026

**Result: six new completed Astra designs passed all stipulated checks. No repeatable Astra-hard case was established. The broad novelty claim remains unsupported. Further API screening was stopped after the user requested conservation of remaining credits. No new training was started.**

This batch tested something more demanding than copying dimensions: selecting physical member sections under load, stress, displacement, Euler buckling and a tight mass cap. The model received the complete engineering specification, chose catalog indices, and a deterministic exporter produced the corresponding SVG elevation and section schedule. It was **not** a free-form SVG authoring or visual-perception experiment. We must not use these results to claim that Astra solved every kind of engineering drawing.

## Actual evidence

[Audited results](../runs/astra-functional-sizing-20260921/audited-summary.json), [empty hard selection](../runs/astra-functional-sizing-20260921/hard-selection.json), [protocol and reproduction notes](../data/cad-functional-sizing/README.md).

| Case | Catalog assignments exhaustively checked | Acceptable assignments under mass cap | Astra final result | Four-batch cross-entropy search | Pair-coordinate search |
|---|---:|---:|---|---:|---|
| Frame 1 | 65,536 | 2 | Pass | 9/20 seeds pass | Pass |
| Frame 2 | 65,536 | 7 | Pass | 19/20 | Pass |
| Frame 3 | 65,536 | 1 | Pass | 3/20 | Pass |
| Frame 4 | 65,536 | 5 | Pass | 13/20 | Pass |
| Braced frame | 531,441 | 1 | Pass | 6/20 | Pass |
| Three-bay frame | 4,782,969 | 2 | Pass | 0/20 | Fail |

The six reference searches enumerated **5,576,554 assignments**. Every frozen task had a verified feasible reference before its API test. Caps were set at 101% of the minimum feasible mass. Alternative feasible designs were accepted. The first four cases share a source-frame ancestry; the later two are adaptive extensions created after earlier passes. This is six instances within structural design, not six diverse engineering families.

Astra used `gpt-6-astra`, high reasoning, at most four analysis calls and 256 candidates per call. There were **24 successful API turns and 128,046 reported total tokens**, including repeated/cached context. This is usage telemetry, not a dollar-cost estimate or an account-balance check. All original requests, responses, tool results and final designs remain saved. Two trials included a malformed tool request, then recovered and passed. No intermediate error was counted as a hard case.

The three-bay outcome is particularly informative. Its mass cap was **6,409.844 kg**. Astra's final design weighs **6,346.380 kg**, with peak stress **99.368 MPa** against 120, horizontal displacement **11.9717 mm** against 12, vertical displacement **1.0642 mm** against 4, and Euler utilization **0.2383** against 1. Its assignment differs from the stored optimum but has the same minimum mass. Astra explicitly said its exact final combination had not been tool-verified. Our subsequent offline analysis verified it. We preserve that distinction: the final design passed; the model did not falsely claim a completed verification.

The cross-entropy baseline matches both the four batches and 1,024 evaluation ceiling. Pair-coordinate search matches the evaluation ceiling, but its adaptive rounds are not matched to four tool calls. Neither receives the oracle. The exhaustive search is a feasibility/optimality reference with a much larger budget, not a fair-budget competitor. These six adaptive trials do not establish statistical model superiority over optimizers in general.

## What was built and checked

- [Catalog FEM evaluator, exporter and API runner](../scripts/cad_functional_sizing.py).
- [Classical baselines](../scripts/cad_sizing_baselines.py), with [initial results](../runs/astra-functional-sizing-20260921/classical-baselines.json), [braced results](../runs/astra-functional-sizing-20260921/braced-baselines.json) and [three-bay results](../runs/astra-functional-sizing-20260921/three-bay-baselines.json).
- [Offline audit](../scripts/audit_cad_functional_results.py) re-reads visible SVG line widths and section rectangles, checks correspondence to the saved choices, and re-analyzes every final design with a separate scalar assembly and subdivided elements. All six agree within 1e-6 in the reported metrics. The stiffness primitive is shared, so this is not an independent commercial-solver reproduction.
- [Five evaluator tests](../tests/test_cad_functional_sizing.py) pass, including analytical axial/Euler controls, scalar-versus-batched FEM, invalid catalog-index rejection, SVG section mismatch detection and feasible frozen references.
- Original trial drawings are retained. `presentation.svg` derivatives correct exporter header overlap and improve label contrast; section choices and physics are unchanged. Corrected rendering was visually inspected.

The structural model is linear, in-plane and rigid-jointed, using nodal loads and rectangular sections. The separate buckling inequality uses the stipulated member K=1 value; it is not a global stability check. Self-weight, shear deformation, out-of-plane effects, joints, plasticity and building-code compliance are excluded. This is a research benchmark specification, not a safe-building certificate. FEM plus an independent analytical inequality, geometric readback and exhaustive discrete search satisfy the requested broader validation direction without pretending that all engineering phenomena were checked.

An unused `--repair-interface` option was prepared to allow two malformed-request corrections without consuming analysis calls if a failure needed confirmation. **No API trial used that option**, because the final screen passed. Do not mix this hypothetical confirmation protocol into the reported results.

## Novelty assessment and a defensible project base

The [registry](../data/cad_sources.json) contains **67 actual records** with differing review depths, not 67 reproduced full papers. [This batch's search log](cad-functional-source-audit-20260921/review-log.json) records primary-source evidence and unreviewed leads. New close comparisons further narrow the claim:

| Prior work | Already covered | Consequence |
|---|---|---|
| [EngDesign](https://arxiv.org/html/2509.16204v2) | Functional design evaluated with domain simulators; structural sizing under load/material trade-offs | FEM-verified section synthesis is not a new task concept |
| [StructureClaw](https://arxiv.org/html/2607.14896v2) | Linked structural artifacts, numerical checks, image/DXF reconstruction, clarification and three-trial reliability | Artifact traceability and repeated engineering verification alone are not novel |
| [Sketch-to-CAD with an intermediate representation](https://link.springer.com/article/10.1007/s00170-026-19035-z) | Visible/inferred/assumed/missing provenance before CAD construction | Merely adding explicit uncertainty labels is not novel |
| [Planar truss sketch-to-documentation workflow](https://www.sciencedirect.com/science/article/pii/S0926580526002517) | Sketch interpretation, structural optimization, geometric alignment and documentation with validation | Combining drawing generation and structural checking is already studied |
| [EPICCAD](https://link.springer.com/article/10.1007/s44163-026-01899-5) | Constraint-aware, history-preserving multimodal CAD with intent-aware descriptions | Preserve history/constraints and add semantic annotations is not a defensible standalone novelty claim |

EngDesign and StructureClaw methods/protocol sections and the sketch-IR methodology were read on primary sites. The truss paper was accessible through publisher abstract/introduction/section excerpts; its complete experiments were not reviewed. EPICCAD was reviewed through primary-publisher search excerpts; dataset access and license remain unchecked. These limits are material. No inaccessible paper was treated as fully reviewed.

**Defensible empirical statement now:** this implementation provides reproducible, feasibility-certified structural sizing controls, and Astra solved every tested case under the stated limited solver access. This is a useful negative result for the proposed “train only where Astra cannot draw” premise. It is not evidence of an Astra-hard benchmark, a new optimization algorithm, or learned improvement.

**Candidate project contribution, still a hypothesis:** detached engineering-drawing edits with lost CAD associations, evaluated through matched drawings whose visible dimensioning requirements imply different valid updates, plus claim-by-claim evidence tied to the final SVG. The closest-work comparison belongs in the paper, and solver coupling, provenance and clarification must be credited as established components. A potential distinction is the exact controlled evaluation contract, not a claim that its ingredients are new. Current tiny intent fixtures passed both Astra and a handwritten baseline, so an empirical gap and useful scale still need demonstration.

The practical decision is to retain the six passing cases as controls, keep the requested failure-only subset empty, and **not spend the remaining budget training against an unobserved failure**. The existing CAD-Editor training pilot is separate and remains valid only within its documented scope. A larger failure search, model training or a publication claim requires new evidence; relabeling these successes would not fix the project.
