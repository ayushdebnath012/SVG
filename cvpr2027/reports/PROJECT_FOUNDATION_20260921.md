# Project foundation: engineering SVG edits with explicit evidence

**Follow-up:** the [extended audit and new tests](CAD_EXTENDED_DISCOVERY_20260921.md) supersede the source count and experimental status below. Additional close prior work also weakens novelty based solely on an evidence/uncertainty architecture.

Date: 21 September 2026. Status: working research foundation, **not an established novelty claim or completed hard benchmark**.

The strongest current direction is to edit detached, dimensioned engineering SVGs while keeping their views, measurements and engineering checks consistent. When the input leaves an important choice unspecified, the system should expose two admissible alternatives and identify which requested checks still have a definite answer. Start with mechanical parts; expand to furniture and building drawings only after the representation and evaluators work. Broad CAD generation, constraint recovery, solver-assisted repair and FEM integration already have substantial prior art.

The practical example is a mounting panel that becomes wider. Depending on its dimensioning scheme, its holes should either stay where they are or spread apart. Both outputs can have identical outer dimensions and volume. The drawing's instructions determine which is correct. If the anchoring instruction is missing, a system should not silently invent one. It may still be able to establish the hole pitch or a clearance bound.

## 1. What could be different, and what cannot be claimed

**Candidate research question:** Can an editor recover enough relationships from an unlinked engineering drawing to make a requested change, keep the whole drawing consistent, and produce checkable evidence for the engineering claims that remain determined by the input?

The candidate contribution is the evaluated combination of:

1. Detached engineering SVG input, without the original CAD history or an injected ground-truth constraint graph.
2. Matched starting geometry with different visible dimensional requirements, producing different correct edits; missing and contradictory information are separate conditions.
3. Evaluation of updated geometry, cross-view correspondence, dimension values and their attachments, protected content, and supported engineering claims together.
4. Evidence at the level of each requested edit/check: a verified result, two feasible alternatives showing ambiguity, an inconsistency, or an unsupported analysis.

This search did not locate a reviewed system evaluating that exact complete contract. That is a bounded observation, **not proof that nobody has done it**. The following work rules out easier novelty claims. The full registry now contains 54 paper, dataset, project and documentation records, not 54 fully reproduced papers.

| Closest work | Established overlap | Remaining distinction to test |
|---|---|---|
| [Vitruvion](https://lips.cs.princeton.edu/vitruvion/) and [constraint/design-intent alignment](https://arxiv.org/abs/2504.13178) | Inferring parametric sketch constraints and preserving intent during edits | Engineering sheet annotations and several linked views must supply the missing relationships; constraint inference itself is not new |
| [Drawing2CAD](https://github.com/lllssc/Drawing2CAD) | Engineering drawing-to-CAD reconstruction | Requested edits and the consistency of the resulting complete drawing, rather than reconstruction alone |
| [CAD-Editor](https://github.com/microsoft/CAD-Editor) and [neuralCAD-Edit](https://autodeskailab.github.io/neuralCAD-Edit/) | Instruction-following CAD edits, including expert multimodal requests | Detached sheet input and explicit evidence connecting final annotations to the edited design |
| [CIT-CAD](https://arxiv.org/html/2609.07434v1) | Explicit intent, deterministic constraint verification, localized repair preserving satisfied constraints | Recover relations from the drawing and assess alternative admissible interpretations; an intent graph plus repair is not new |
| [ProCAD](https://arxiv.org/html/2602.03045v1) | Detecting ambiguous/conflicting instructions and asking targeted questions before generating CAD | Numerical witnesses of drawing ambiguity and checking a determined quantity despite other ambiguity; clarification by itself is not new |
| [DepthBenchCAD](https://github.com/HongyeYangGT/DepthBenchCAD) | Counterfactual parameter edits and audit allocation | Annotation-conditioned changes with the same starting shape and complete drawing consistency; counterfactual CAD evaluation itself is not new |
| [Wrong Design Intent Is Worse Than None](https://arxiv.org/html/2607.23191v1) | Correct/wrong/masked intent interventions, independent geometry evaluation and a shuffled training control | Visible drawing relationships and subsequent engineering edits; causal intent controls alone are not new |
| [CADEngBench](https://arxiv.org/html/2608.09296v1) and [CADWorld](https://arxiv.org/html/2609.16251v1) | Functional engineering tasks, CAD execution and physical-analysis workflows | Evidence must correspond to the edited SVG and its stated assumptions; adding FEM does not establish novelty |
| [SVG360](https://arxiv.org/html/2511.16766v3), [MM-SVGEdit](https://arxiv.org/html/2609.06116v1), [Vector-Bench](https://arxiv.org/abs/2607.19056) | Multiview vector editing, visual grounding and protected-content preservation | Engineering dimensional meaning and analysis-linked correctness; SVG patching itself is not new |
| [Classical drawing associativity](https://care.dptlab.com/Content/Help/language/drawing/OVfile/T_OV_associativity.htm) | Linked drawings already update with their CAD model | The proposed input has lost those links; their recovery and uncertainty must be evaluated |

DepthBenchCAD was reviewed as a public repository release; its performance and publication status were not independently reproduced. Its README says candidate programs and provider prompts/telemetry are omitted. Do not cite its reported results as reproduced baselines.

Adjacent formal-methods work also limits the framing: [verification with incomplete specifications](https://arxiv.org/abs/2004.09503) and [Partial Contracts Suffice](https://arxiv.org/abs/2607.10291) already study reasoning with incomplete specifications. These two were reviewed at primary-abstract level only. Query-specific verification, linear programming and ambiguity witnesses are established techniques, not algorithms invented here. The remaining opportunity is a useful engineering-drawing task, reliable implementation and demonstrated empirical gap.

## 2. What was actually built and tested

| Artifact | Completed result | Important limit |
|---|---|---|
| [Detached SVG fixtures](../data/cad-intent-probe/tasks.json) | One mounting panel, two dimensioning intentions, two coordinate encodings = four conditions | One underlying design, not four independent objects |
| [Astra raw screen](../runs/astra-cad-intent-20260921/screen/summary.json) | **4/4 passed**, high reasoning effort, four successful API calls, 18,762 reported tokens | Inspection and algebra tools were offered, but Astra used neither; no failure confirmations were needed |
| [SVG-only rule baseline](../scripts/cad_intent_rule_baseline.py) | **4/4 passed** using visible dimension text/lines and linear constraints | Handwritten parser for this single fixture grammar; no hidden target or task-mode input to `edit()` |
| [Edit evaluator](../scripts/cad_intent_probe.py) | Checks shape coordinates, all hidden edges, dimension/witness geometry, numeric labels and protected notes | Limited SVG elements and canonical annotation placement; not a general drafting or standards checker |
| [Query evidence module](../scripts/cad_query_evidence.py) | Identifiable/ambiguous/inconsistent/unbounded results with feasible witnesses and numerical LP dual evidence | Authored linear constraints; automatic recovery of ambiguous interpretations is not implemented |
| [Rendered comparison](../runs/astra-cad-intent-20260921/gallery.html) | Source, reference and Astra SVGs rendered and visually inspected | Research fixtures; no production drafting certification |
| Regression checks | Six edit-evaluator tests and five query-evidence tests passed | Verifier controls, not learned-model performance claims |

The width changes from 180 to 234 mm. Under fixed chain dimensions, hole centers stay at 18, 54, 90, 126 and 162 mm. Under fixed 18 mm edge offsets and equal spacing, they become 18, 67.5, 117, 166.5 and 216 mm. Astra correctly updated both the top and front views and the dimension annotations in all four conditions. Parenthesized reference dimensions are explicitly defined by the prompt; we are not testing implicit knowledge of a drafting standard.

The nested encoding preserves physical geometry and text positioning but changes the hidden-line dash appearance slightly. It is a coordinate-equivalence control, not a claim of pixel-identical rendering. The evaluator uses 0.05 mm coordinate tolerance and tolerates equivalent numeric formatting within 0.01. Its current annotation-position comparison is deliberately narrower than all acceptable drafting layouts. A future failure caused only by a different valid layout must not be counted as an engineering failure.

The new query control omits the hole-row anchor while fixing the 234 mm width and 36 mm pitch. Explicit bounds require 5 mm minimum edge clearance for 9 mm holes. It obtains:

| Requested quantity/check | Result over the supplied feasible designs |
|---|---|
| Panel width | Always 234 mm |
| Hole pitch | Always 36 mm |
| First hole coordinate | Between 9.5 and 80.5 mm; two feasible layouts saved |
| Left edge clearance at least 5 mm | Holds throughout the supplied bounds; this is a consistency control, not an independent design discovery |
| First hole at least 30 mm from datum | Depends on the interpretation |
| Minimum pitch of 40 mm | Violated throughout |
| Add explicit 18 mm left anchorage | Hole-row position becomes determined |

This uses standard linear programming with numerical primal/dual residual checks, not exact formal proof. All statements are conditional on the completeness and correctness of the supplied linear constraint model. It does not establish general identifiability of 3D solids or nonlinear mechanics.

**Decision:** exclude all four solved conditions from the Astra-hard subset. The [selection record](../runs/astra-cad-intent-20260921/hard_selection.json) is empty. Earlier native-CAD and harder geometry screens also did not establish a repeatable unsolved object shape. No new model training was started on these solved cases.

## 3. System contract and implementation boundary

Proposed input: an engineering SVG sheet, an edit request, units/projection convention, and any explicitly supplied material, load, support or manufacturing assumptions. The hidden reference CAD model is evaluator-only. Native CAD input is a separate easier setting and must not be mixed into the detached-drawing headline.

Proposed output: an edited SVG patch, a relationship model with references to visible source evidence, and a record for each requested engineering check. Every record contains the affected entities, units, assumptions, input hashes, method, numerical tolerance, result and witness or supporting calculation. An image looking plausible is insufficient evidence.

| Stage | Reuse/build choice | Current state |
|---|---|---|
| SVG parsing and coordinate normalization | Reuse existing transform-aware parser; expand to paths, symbols, clipping and view frames | Primitive panel subset works |
| View/feature/dimension association | Learn or infer links, including the feature a dimension refers to | One handwritten grammar works; general module missing |
| Constraint interpretation | Reuse sketch constraints; retain alternatives when the drawing does not decide | Single linear graph works; alternative-graph recovery missing |
| Edit solving | Linear solver first; geometric constraint/CAD kernel for richer parts | Linear panel edits and earlier CadQuery edits work separately |
| Check selection and execution | Choose a method from the actual claim and available inputs | Linear query checks work; earlier frame FEM/statics are separate pilots |
| SVG update and audit | Update affected views, labels and attachments; preserve unrelated elements | Restricted patch executor works; general sheet update missing |

The front-end relationship recovery is the prospective learned task. The numerical solver remains a reliable reused component. Only train if a general baseline demonstrably fails at relationship recovery or consistent editing.

## 4. Validation beyond FEM

The following is the planned check coverage, not a claim that all modules exist:

| Object/edit | Appropriate checks | Information required |
|---|---|---|
| Plate holes, brackets, dimensions | Exact/robust geometry predicates, topology, clearances, view correspondence, interval tolerance calculations | Units, geometry, tolerance convention and process limits |
| Table or shelf | Statics, support polygon/tipping, beam formulas where valid; frame/solid FEM for deformation when needed | Loads, support/joint model, sections and material |
| Mechanism or assembly | Kinematic constraints, contact/interference and clearance over motion | Joint definitions, intended motion and contact assumptions |
| Building drawing | Plan/section consistency, connectivity, areas and stated geometric requirements; structural analysis as a separate check | Projection/layout semantics; loads, sections and supports for mechanics |
| Stress/deflection claim | Independently recompute the affected analysis, with convergence/reference checks | Complete physical assumptions and a model appropriate to the claim |

Missing material or loads must not be silently filled in to produce a stress number. Conversely, missing material need not prevent a purely geometric clearance check. A valid solid or passing FEM run does not establish that every engineering requirement is satisfied.

## 5. Data foundation and leakage controls

Build on existing data for geometry and editing; add the missing engineering-sheet supervision. None of the reviewed releases has yet been verified to provide the whole proposed tuple of detached annotated SVG, intent alternatives, edit outcome and analysis evidence.

| Source | Intended use | Actual local status |
|---|---|---|
| [CAD-Editor](https://github.com/microsoft/CAD-Editor) | Edit instruction and before/after geometry foundation | Downloaded; completed 2,048-pair training pilot with 128 validation/128 test pairs. On 32 evaluated test examples, exact sequence matches rose 1→6; no SVG/physics improvement established |
| [SketchGraphs](https://github.com/PrincetonLIPS/SketchGraphs), [CPTSketchGraphs](https://github.com/cvi2snt/CPTSketchGraphs) | Primitive constraints and edit-preserving augmentation | Release links reviewed; not downloaded for this turn's experiment |
| [Drawing2CAD](https://github.com/lllssc/Drawing2CAD) | Paired engineering views and CAD geometry | Release links reviewed; archive not downloaded or audited here |
| [Fusion Gallery](https://github.com/AutodeskAILab/Fusion360GalleryDataset) | Later assembly/joint extension | Reviewed source; custom terms and subset availability apply |
| [FloorPlanCAD](https://floorplancad.github.io/) | Later building-sheet semantics | Reviewed source; no new download/training; cannot supply structural ground truth by itself |
| [BenchCAD](https://huggingface.co/datasets/BenchCAD/BenchCAD), neuralCAD-Edit and engineering benchmarks | Evaluation anchors | BenchCAD: 110 records downloaded and four audited derivatives tested earlier. **Held out from training** |
| Original panel fixtures | Evaluator controls | Four frozen conditions generated and tested; not a training dataset |

Code licenses do not automatically license drawings. Preserve upstream identifiers, exact revisions, archive checksums and data-specific terms. The registry records actual access and training use.

For the next corpus, create dimension/feature/view bindings from native sources, export an ordinary SVG, and remove internal constraint metadata from the model input. Retain the native bindings only as hidden labels. Independently check the exported sheet and every reference edit: the earlier BenchCAD audit found target/instruction inconsistencies, so upstream labels cannot be trusted blindly.

Split by connected components of source-model ancestry **before** making instructions, views, edit sequences or SVG variants. Keep related DeepCAD/Onshape derivatives together across datasets. Near-duplicate geometry and assembly relatives need additional checks. A random pair split is insufficient. Human-authored requests and different exporter conventions belong in held-out tests; they are not replaced by a single procedural template.

Planned training targets are feature/view associations, dimension attachments, constraint status and minimal edits with verified results. Candidate-error repair traces may be used only after the verifier accepts the correction. Never train on the final Astra-hard test objects, their alternative annotations or their family variants.

## 6. Benchmark admission and a decision before larger training

The prospective protocol is [frozen separately](../configs/cad-foundation-protocol.json). These decisions were made after the four panel results and must not be presented as preregistered rules for that pilot.

1. Discover on 30 distinct source objects across at least three geometry families, with realistic annotation/view dependencies. Do not count coordinate variants as new objects.
2. Save all screening outcomes, including passing and invalid cases. The requested hard benchmark contains only confirmed failures; the complete ledger discloses selection bias.
3. For a candidate failure, check the reference, task sufficiency, grader and rendering. Supply Astra with the same allowed tools and feedback budget as competing systems.
4. Admit only a substantive failure remaining in **three independent completed high-effort runs** under the frozen protocol. Truncation, API rejection, invalid references, legitimate ambiguity disclosure and repaired intermediate errors do not establish a shape limitation. State the model/version/date and budget: this is repeatable failure under a protocol, not proof of absolute incapability.
5. Separate shape/edit errors from annotation, analysis, format and ambiguity-handling errors. The user-requested shape subset requires a geometry/edit failure. An ambiguous task whose correct response is clarification is not an unsolved shape.
6. Freeze the selected test set before method tuning. Select by the baseline failure rule, never by whether our system succeeds. Use separate failure discovery/training objects and separate held-out test objects.

**Feasibility gate:** at least ten confirmed shape/edit failures spanning three families, plus an evaluator that accepts valid alternatives, before launching larger task-specific training. This is a project decision threshold, not a statistical power calculation. If the 30-object screen cannot meet it, expand only for a concrete new failure mechanism or revise the research question; do not manufacture difficulty through missing information or arbitrary formatting.

Required comparisons are Astra with equal tool/budget access; the transparent constraint baseline; direct SVG editing; reconstruction followed by an associative CAD edit; and our proposed relationship-and-evidence system. Include geometry-only, annotation-masked, wrong-annotation and nested-coordinate controls. Report complete drawing success, substantive geometry failures, unsupported claims, useful verified coverage, unintended changes and cost. Cluster uncertainty estimates by original source object; do not treat variants as independent samples.

## 7. Reproduce the completed foundation

From the workspace root, using the existing environment:

```sh
.venv/bin/python -m unittest discover -s cvpr2027/tests -p 'test_cad_intent_probe.py' -v
.venv/bin/python -m unittest discover -s cvpr2027/tests -p 'test_cad_query_evidence.py' -v
.venv/bin/python cvpr2027/scripts/cad_intent_rule_baseline.py
.venv/bin/python cvpr2027/scripts/cad_query_evidence.py
.venv/bin/python cvpr2027/scripts/review_cad_intent.py
```

These commands do not call Astra. API prompts, responses, offered tools, model configuration and usage are already retained under `runs/astra-cad-intent-20260921/screen/`. Do not overwrite the frozen task manifest or count rerendering as a new model trial.

**Present conclusion:** there is now an executable foundation and a narrower, falsifiable research direction. There is still no confirmed novel contribution, demonstrated learned advantage on engineering SVGs, or repeatable Astra-hard object shape. Those are the next empirical requirements, not completed results.
