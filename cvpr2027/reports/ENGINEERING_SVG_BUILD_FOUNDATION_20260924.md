# Engineering SVG generation, editing and analysis: build foundation

Reviewed: 24 September 2026. This is a fresh web literature review and implementation specification, not a completed new system or proof of novelty. Sources include primary papers, conference proceedings, author repositories, dataset/project pages and solver documentation. The search is broad but not exhaustive; inaccessible or undiscovered work remains possible. Reported external results were not reproduced in this review.

## Decision

The product is relevant, but “text to CAD/SVG, edit it, then run FEM” is already an established direction. Build on existing geometry, editing and simulation tools. Investigate a narrower contribution: keeping engineering drawing views, dimensions, requested edits, and numerical analysis consistent over a sequence of edits, including imported SVGs without their original CAD links.

Treat this as a research hypothesis. An architecture assembled from known techniques is useful software, but does not by itself establish a new research method.

## Closest prior work and reuse decisions

| Work and primary source | Verified scope | Consequence / proposed reuse |
|---|---|---|
| [Text2CAD, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/0e5b96f97c1813bb75f6c28532c2ecc7-Abstract-Conference.html) | Text-conditioned parametric CAD sequences; approximately 170K models and 660K annotations | Reuse generation supervision and executable representations. It does not supply our complete drawing/edit/physics tuple. |
| [CAD-Editor, ICML 2025](https://github.com/microsoft/CAD-Editor) | Locate-then-infill editing with synthesized before/after CAD and instruction data | Reuse edit localization and source/target data; our existing local pilot is a starting point. Sequence similarity cannot establish physical correctness. |
| [SketchGraphs](https://github.com/PrincetonLIPS/SketchGraphs) | 15 million CAD sketches represented with geometric constraints | Candidate supervision for geometric relations. Requires conversion to our entity schema; no assumption that it contains loads or materials. |
| [neuralCAD-Edit](https://autodeskailab.github.io/neuralCAD-Edit/) | 192 multimodal requests and 384 edits from ten expert designers; native CAD inputs | Hold out for realistic editing comparisons. Learn from its evaluation of intent and expert alternatives, not just exact code equality. |
| [SVGEditBench](https://github.com/mti-lab/SVGEditBench) | SVG manipulation benchmark including color, contour, compression, orientation, transparency and cropping | Useful SVG editing control; not a substitute for engineering tests. |
| [MM-SVGEdit](https://arxiv.org/abs/2609.06116) | UI-oriented grounding followed by modification; 14,476 question-answer pairs and 11 operation types | Ground-then-edit is prior art. Engineering semantics and physics need separate validation. Abstract reviewed. |
| [FEABench](https://arxiv.org/abs/2504.06260), [release](https://github.com/google/feabench) | Natural-language multiphysics tasks executed through COMSOL APIs | Reuse the evaluation principle: executable simulations and quantitative answers. Direct reproduction depends on COMSOL access. |
| [CADEngBench](https://arxiv.org/html/2608.09296v1) | 300 parts, generation and functional edits, preserved properties, parametric changes, CalculiX FEA; separate assembly track | Closest overlap. Use its evaluation structure as a comparator. Adding physics or preserving untouched features is not novel. Public release usability still needs a download/execution audit. |
| [COSMO-Agent](https://arxiv.org/abs/2605.20190) | Tool-mediated CAD generation, CAE solving, result parsing and geometry revision; RL and 25 component categories | Closed-loop physics-guided design and RL are already proposed. Abstract-level review; code/data availability and reproducibility not established here. |
| [CIT-CAD](https://arxiv.org/abs/2609.07434) | Explicit constraint intent, generation, verification and localized repair | Reuse explicit requirements and mismatch-guided repair. Do not claim intent graphs or solver-backed repair as new. Latest abstract and v1 method reviewed. |
| [ProCAD](https://arxiv.org/abs/2602.03045) | Clarifies missing or conflicting specifications before CadQuery generation | Clarification is existing work. Missing physics inputs should be handled explicitly rather than guessed. Latest abstract reviewed. |
| [CADWorld](https://arxiv.org/abs/2609.16251) | 200 FreeCAD computer-use tasks across 11 workflow categories including technical drawing and FEM | Professional CAD workflow evaluation already exists. Our API-based workflow should not be compared directly with GUI-only scores. |
| [Parametric CAD Bench v3](https://www.gnucleus.ai/cad-bench/news/cad-bench-v3) | September 21 release describes 100 tasks: text generation, create-and-edit, and engineering drawing inputs | Recent adjacent evaluation to track; provider announcement reviewed, not an independently reproduced result. |

Additional overlap from the previous local audit remains important: drawing associativity, constraint-based SVG, Chart2SVG dependency propagation, DrafterBench civil drawing revision, and engineering drawing audit architectures. See [the extended audit](CAD_EXTENDED_DISCOVERY_20260921.md). Those records are prior findings, not all freshly re-reviewed today.

## What our experiments establish

The completed Colab experiments use Qwen2.5-Coder-1.5B-Instruct. They are not Astra evaluations.

| Metric | Text to SVG | SVG edit |
|---|---:|---:|
| SVG extracted by current parser | 17/24 | 20/24 |
| Geometry check | 0/24 | 0/24 |
| Dimension check | 17/24 | 13/24 |
| Claimed analysis check | 0/24 | 1/24 |
| Drawn-frame peak-stress agreement | 1/24 | 3/24 |
| All current strict checks | 0/24 | 0/24 |

Evidence: [saved notebook](../notebooks/EngSVG_Train_A100_resume.ipynb) and [evaluation implementation](../scripts/colab_train_engsvg.py). The current parsed flag initially detects an SVG substring; do not conflate it with a comprehensive SVG validity certificate. The FEM gate compares peak stress, not every field quantity. The restarted runs skipped baseline generation. An earlier text-generation baseline cannot substitute for a matched SVG-edit baseline. Training loss does not establish engineering accuracy. Repeated failures across different tasks are not repeated independent Astra trials on each task.

Previous chat statements that these Qwen results confirmed an Astra-hard set were incorrect. Retain them as failed direct-generation baselines, with model and evaluator version attached. They motivate a structured pipeline but do not prove the pipeline will work.

## Architecture to implement

Maintain one versioned engineering document with explicit units, entities, parameters, geometric constraints, dimensions and their attachments, view projections, material, sections, supports, loads and analysis assumptions. Use stable application IDs; CAD face indices alone may change after rebuilding.

Text request -> specification -> validated design document -> geometry -> SVG views.

Edit request -> target grounding -> typed edit operations -> candidate document -> rebuild -> geometry and preservation checks -> applicable physics -> updated SVG and report.

The language model interprets and proposes edits. Numerical code calculates coordinates and results. Accept the candidate only when required checks pass; retain the prior document if validation fails. Persist each edit and its parent revision for reproducibility.

Two input modes must remain separate:

1. Generated drawings: retain the document alongside SVG. User edits operate on known parameters and relations.
2. Imported detached SVG: recover relations from visible dimensions, primitives and views. Mark unresolved interpretation explicitly. Do not secretly inject the reference design graph. Ambiguous 2D views need not determine a unique 3D physical object.

Each analysis record should contain design revision/hash, relevant entity IDs, method, solver/version, units, material/load/support assumptions, numerical tolerances, result and validity status. Editing a dependency invalidates the affected result. Rendering must not leave old stress/deflection labels attached to new geometry.

## Reuse the engineering tools

[CadQuery](https://cadquery.readthedocs.io/en/stable/) provides parametric geometry and [SVG export](https://github.com/CadQuery/cadquery/blob/master/doc/importexport.rst). Keep the parameters/program and engineering metadata separately: an SVG export alone is not a preserved parametric model. Our layer must attach dimensions, drawing semantics and results.

[CalculiX](https://www.calculix.de/) supports linear/nonlinear, static, dynamic and thermal finite-element calculations. Introduce supported analysis types one at a time, with independent validation. Solver support is not proof that our automatic model setup is correct.

Initially reuse the repository's frame analysis, SVG parsing and reference generators, after numerical/evaluator checks. Choose a simple deterministic geometry implementation for planar frames; use a CAD kernel for solid parts when needed. Avoid replacing mature numerical solvers with model-generated arithmetic.

| Task | Proposed checks | Scope boundary |
|---|---|---|
| Frame or table side-frame | Connectivity, dimensional consistency, static equilibrium, beam/frame FEM, analytical beam controls | Explicit joint/support/load model; a side-frame test does not certify a full 3D table |
| Full table stability | Support polygon and overturning moments | Requires 3D support layout, centre of mass and load positions |
| Mounting plate/bracket | Hole locations, wall/edge clearance, tolerance intervals, contact/interference; optional solid FEM | Manufacturing limits and stress model must be specified |
| Moving assembly | Joint constraints, travel, collision and clearance | Requires explicit motion and joint definitions |
| Thermal or vibration request | Dedicated validated solver setup | Later extension, not covered by static stress checks |
| Building plan | View/dimension/connectivity checks | Structural design and code compliance are separate, domain-specific tasks |

## Data construction and training

Use released training portions of Text2CAD, CAD-Editor and SketchGraphs where suitable. Inspect each dataset's actual license, upstream attribution and train/test terms before incorporating records; code licensing alone is insufficient. No new external training data was downloaded in this review.

Create an adapter into the engineering document format, then generate SVG views from executable reference designs. Add explicit, reproducible analysis scenarios rather than inventing undocumented materials and loads for arbitrary CAD parts. Store source provenance and conversion failures.

Proposed example record: source design and SVG, request, grounded target IDs, typed operations, edited design and SVG, protected properties, analysis specification, verified results, and evidence for missing/inconsistent information. Include multi-step edits that intentionally invalidate prior results.

Split by source design/family before creating variants and edits. Keep all siblings, renders and paraphrases together. Existing published evaluation examples stay out of training. Freeze a general evaluation set and separately report a discovery-selected Astra-hard subset to expose selection bias.

Train target grounding and valid edit/program generation first. Keep numerical analysis deterministic. Do not launch more direct-SVG training until error inspection identifies whether failures come from grounding, geometry execution, preserved constraints or physics setup.

## Research hypothesis and tests

Candidate question: can a system maintain consistent engineering meaning across SVG views, annotations and analysis through successive user edits, including recovery from detached drawings?

Potentially useful experiment: identical starting geometry with different visible anchoring dimensions requires different edits. Remove or contradict one annotation, then test whether the system requests clarification or gives supported alternatives. Follow with a load or section edit and test whether displayed analysis is recomputed from the correct revision. None of these ingredients is individually new; novelty requires empirical comparison of the combined task and method against the closest work.

Compare: unchanged-input baseline; deterministic parser/executor; direct SVG generation; structured design generation; structured editing with solver feedback; Astra with the same allowed tools and information. Ablate relation recovery, preservation checks and analysis invalidation. Use geometry equivalence and numerical tolerances rather than exact source text.

For an Astra-hard candidate, freeze prompt, artifact, model identifier, reasoning/tool budget, evaluator and tolerances before confirmation. Audit the final failure, exclude operational errors and harmless equivalent formatting, and run at least three independent confirmations as an initial screen. Report success counts and uncertainty; 0/3 is limited evidence, not inability. Keep confirmation attempts out of training and never label Qwen failure as Astra failure.

## Implementation sequence and acceptance gates

1. Frame/table-side-frame vertical slice: typed design, deterministic SVG, one width edit, numerical analysis and a before/after explanation. Oracle geometry must satisfy every requested dimension.
2. Versioned edit executor: preserve untouched entities, reject invalid units/constraints, invalidate stale calculations, and save reproducible edit histories.
3. Analysis validation: analytical beam examples, reaction balance, symmetry/scaling controls, and convergence for applicable mesh-based models. Deliberately corrupted inputs/results must fail the checker.
4. Imported-SVG track: limited supported element grammar, visible dimension association, transform-equivalence tests, and explicit ambiguous cases. Evaluate separately from native-document editing.
5. Frozen baseline study: practical drawing families, multi-step edits, equal tool access and audited failure categories. Establish the Astra gap before selecting training targets.
6. Targeted training: supervise the measured failure stage; demonstrate held-out family improvement and unchanged-part preservation. Add solid/thermal/dynamic analysis only after corresponding validators exist.

Deliverables of this review: the source comparison, reuse architecture, dataset plan and experimental gates above. A complete product, new adapter, new Astra test, or confirmed novelty claim was not produced by this literature review.
