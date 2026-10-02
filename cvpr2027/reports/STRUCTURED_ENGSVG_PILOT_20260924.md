# Structured engineering SVG pilot

This is a bounded planar portal/table-side-frame prototype. It reuses the existing Euler–Bernoulli frame solver and SVG exporter. It is not a general CAD generator, detached-SVG interpreter, or an Astra-hard result.

## Implemented

- Strict parameter schema with units for width, height, rectangular section, elastic modulus and applied loads.
- Create/edit/clarify action interpreter; unknown fields, nonfinite values and invalid dimensions rejected.
- Immutable edits and design hashes; SVG and analysis are rebuilt from the edited parameters.
- Deterministic before/after SVG examples and FEM results.
- Independent cantilever deflection/stress checks, force/moment equilibrium and member-subdivision controls.
- 800 synthetic examples: 600 train, 100 validation, 100 test, with source-design groups separated. This is parameter-instance separation within one topology, not held-out-family generalization.
- GPU training runner for Qwen2.5-Coder-1.5B with LoRA, 3 epochs, matched 36-case base/trained evaluation: 12 create, 12 edit, 12 clarify. Evaluate short structured actions; physics is computed by code.
- Partial predictions saved after every evaluated case; epoch checkpoints, final adapter and ZIP artifact bundle.

## Local verification

`../../.venv/bin/python scripts/structured_engsvg.py verify --out runs/structured-engsvg-local`

All 800 target actions passed the pipeline checks. This is an oracle/control result, not a learned-model score. Negative checks include invalid values and an inappropriate create operation on an existing design.

## Reproduce

Open `notebooks/EngSVG_Structured_Colab.ipynb` in VS Code and select its Colab kernel. The notebook embeds the local runner so it does not need a Git push. It fetches existing project dependencies, validates, evaluates base, trains and evaluates the trained model. Outputs are under `/content/engsvg-structured-run`; download `/content/engsvg-structured-run-artifacts.zip` before runtime expiry.

The completed hard-evaluation notebook is `notebooks/EngSVG_Structured_Hard_Eval.ipynb`. The downloaded run is preserved in `runs/structured-engsvg-hard-colab/`, and the original ZIP is `runs/structured-engsvg-hard-colab-artifacts.zip`. Its SHA-256 is `cd85b205169f3707f5988155db6838d298ec1fa3cf03738468fab8dadf1f46af`. All 20 files covered by the run's checksum manifest were re-hashed locally with zero mismatches. The adapter is included.

## Limitations

The dataset uses template requests and one frame topology. The generic schema handles clarification, but only a single omitted create parameter is trained in this pilot. Drawings come from retained parameters, not inference from arbitrary SVG. Static linear 2D rigid-jointed frame assumptions exclude self-weight, joint flexibility, tipping, buckling and out-of-plane behaviour. The current renderer is a centreline prototype, not a complete standards-compliant technical sheet.

## Completed matched GPU results

NVIDIA L4, 3 epochs, 592.48 seconds training, final reported training loss 0.0022638. Saved notebook output contains all 72 base/trained case outcomes; aggregate counts independently reconciled.

| Task | Base | Trained |
|---|---:|---:|
| Create parameters | 12/12 | 12/12 |
| Edit parameters | 12/12 | 12/12 |
| Clarify missing field | 0/12 | 12/12 |
| Total | 24/36 | 36/36 |

Training improves the clarification policy on this template distribution. Generation and editing were already solved by the base model under the structured contract. These results cannot be directly compared with the previous direct-SVG percentages: the task, representation and evaluation examples changed. Physics is supplied by the deterministic solver, not learned.

The adapter, predictions and ZIP are now verified locally. The matched 36/36 score is not the main result because those requests closely follow the training distribution.

## Frozen hard benchmark

`structured-engsvg-hard-v1` was authored separately and frozen before evaluation. Its 22 independent cases contain mixed units, relative arithmetic, composite edits and multiple missing fields. It also has three three-step edit trajectories. None of these cases is used for training.

| Task | Base | Trained |
|---|---:|---:|
| Mixed-unit create | 1/6 | 0/6 |
| Relative/composite edit | 6/10 | 4/10 |
| Multiple-field clarification | 0/6 | 2/6 |
| Rollout steps | 1/9 | 3/9 |
| Complete three-step trajectories | 0/3 | 1/3 |

These are repeatable hard cases for the Qwen2.5-Coder-1.5B structured interpreter. Training improved multi-field clarification and completed the geometry/load trajectory, but it regressed hard create and edit accuracy. The adapter learned the narrow training pattern and did not reliably learn unit conversion or arithmetic.

The most consistent failure groups are:

- Unit normalization: metres, centimetres, kilonewtons and gigapascals are often copied without conversion. Examples include 1.4 m becoming 140 mm and 200 GPa becoming 200 MPa.
- Quantity binding: dimensions or load directions are sometimes assigned to the wrong schema field.
- Relative arithmetic: requests such as “add 0.2 m” are treated as 20 mm, or load deltas are added without converting kN to N.
- Composite edits: the model may update one requested field and omit the other.
- Complete missing-field sets: the trained model often returns only a subset of the missing parameters.
- JSON reliability: several failures are malformed JSON or invalid numeric values.
- Multi-turn recovery: once a rollout step fails, later steps cannot be fairly executed on the intended state.

Every successfully interpreted design still passed the deterministic FEM equilibrium check. This means the present bottleneck is language-to-parameter interpretation rather than the frame solver.

## Engineering decision

The next version should make conversions and arithmetic deterministic tools instead of expecting a small language model to calculate them inside JSON. A practical pipeline is:

1. Parse quantities into value, unit, direction and referenced object.
2. Convert all quantities to canonical millimetres, newtons and megapascals with a tested unit library.
3. Resolve relative edits against the retained design state with explicit arithmetic.
4. Validate the complete action against the schema and ask for all missing fields together.
5. Rebuild the SVG from the updated design model.
6. Run deterministic analysis and report equilibrium, displacement, stress, buckling and stability checks that apply to the selected drawing type.

Training should then focus on entity binding, intent and ambiguity, with balanced hard examples and regression tests for the already solved simple cases. Keep this frozen benchmark untouched and add separate held-out topology families before making a general engineering-SVG claim.

## Implemented corrective layer

The first corrective version is now implemented in `scripts/engsvg_rule_interpreter.py` and connected to `structured_engsvg.py` request mode. It performs deterministic conversion to millimetres, newtons and megapascals; applies absolute, relative, percentage and composite edits against retained state; returns the complete missing-field set; and produces a visible change summary. The rebuilt SVG embeds the canonical design parameters, nodes, member IDs, supports and loads in versioned metadata. The pipeline then runs FEM again for the exact edited revision.

The corrected benchmark is `structured-engsvg-hard-v2`. It removes the contradictory “Supplied canonical values” suffix from the six clarification cases and saves each target and expected design beside the prediction. The original v1 GPU artifact remains unchanged as historical evidence.

| Corrected v2 rule evaluation | Passed |
|---|---:|
| Mixed-unit create | 6/6 |
| Relative/composite edit | 10/10 |
| Multiple-field clarification | 6/6 |
| Stateful rollout steps | 9/9 |
| Complete trajectories | 3/3 |

Six automated tests cover canonical units, complete clarification sets, every individual hard case, all stateful trajectories and auditable saved outputs. The original pipeline verification also passes after metadata integration. A full create example and a composite edit example are preserved under `runs/structured-engsvg-v2-demo/`; both regenerate valid SVG and have FEM equilibrium residuals below `2.4e-10` in the stored units.

This is a deterministic bounded-domain baseline, not evidence that general natural-language engineering editing is solved. Its value is architectural: arithmetic and unit conversion no longer consume model capacity, and future model evaluation can focus on entity binding, ambiguity and unfamiliar drawing structure.

## Detached SVG importer

The bounded portal pipeline now imports an SVG after its `engsvg-design` metadata has been removed. The importer reads the rendered member geometry, checks that the two legs and top member form a connected portal, reads visible dimension and section annotations, and recovers visibly stated material and load values. It attaches field-level evidence and confidence values to the recovered design.

Material modulus and loads were previously present only in metadata, so the renderer now prints them as visible, tagged drawing annotations. For older SVGs without those notes, the importer returns `needs_clarification` with the complete missing-field list. It also reports conflicting section annotations as ambiguities and rejects scripts, external images, unsupported compositing and unsafe SVG declarations through the existing strict geometry reader.

A preserved end-to-end example removes the metadata, recovers all seven canonical parameters from visible evidence with minimum field confidence 0.95, applies “Make it 0.2 m wider and remove the lateral load,” regenerates the SVG and reruns FEM. The final force/moment equilibrium residual is below `2.3e-13` in the stored units. Thirteen focused tests now pass, including metadata-free recovery, clarification for invisible physics, conflicting annotations, unsafe SVG rejection and detached editing.

This importer is intentionally limited to the three-member portal grammar. General recovery from arbitrary paths, dimension extension lines, furniture, buildings, mechanical parts and multi-view sheets remains a separate research step.

## Common representation and untagged truss

`engsvg-ir-v1` now provides a shared validated representation for frames, trusses, plates and planar mechanical parts. It stores canonical units, nodes, materials, sections, members, plates, holes, dimensions, supports, loads, modelling assumptions and provenance. References are checked, identifiers must be unique, and invalid or nonfinite engineering values are rejected. A provenance-independent engineering hash allows an authored model and a recovered model to be compared without treating different evidence histories as different physical designs.

The first second-family implementation is a five-node, seven-member triangular truss. Its SVG contains ordinary visible lines and text, with no `data-member`, `data-dimension` or embedded model metadata. The importer clusters line endpoints into nodes, infers the connectivity graph, checks the supported topology, derives drawing scale from visible span and height annotations, and reads the section, material, load and support statements.

The authored and recovered engineering hashes match exactly. Geometry and topology comparisons pass. A separate axial-truss FEM solver gives symmetric vertical reactions of 10,000 N at both supports under the 20,000 N central load, peak absolute member stress of 24.296 MPa, and maximum global equilibrium residual of `1.49e-8` in N/N mm units. Missing material text, inconsistent drawing scales and executable SVG content are rejected.

The combined focused suite now has 21 passing tests: 13 portal/interpreter tests and 8 common-IR/untagged-truss tests. The saved truss run includes the SVG, authored IR, recovered IR, analysis, summary and checksum manifest.

The remaining limitation is grammar dependence: structural lines are recognized by their visible drawing style, and the current topology classifier expects this triangular truss. The next generalization should handle transformed paths, dimension extension-line association and unknown connectivity graphs before adding plates and mechanical parts.

## Transform-aware multi-family upgrade

The geometry layer now resolves nested SVG transforms for straight lines, paths, polylines, rectangles, circles and positioned text. It rejects scripts, external images, `use` references, nested SVG, clipping, masks and filters. Bare numeric dimension labels such as “4000 mm” are associated with nearby horizontal or vertical dimension lines by position, so recovery no longer requires `data-dimension` attributes or “Span:” wording.

Truss recovery now constructs a graph from clustered visible endpoints, associates node labels spatially, checks graph connectivity and accepts different connected topologies. Undirected member orientation is canonicalized for engineering comparison. A second six-node, nine-member topology passes recovery and FEM equilibrium checks in addition to the original five-node fixture.

An untagged mechanical-plate family is also implemented. It recovers a transformed rectangular outline, transformed hole circles, width and height dimension lines, hole count and diameter, edge offsets, thickness and material modulus. Drawing-specific verification checks boundary crossings, hole overlap, minimum edge distance, minimum ligament, net area and volume. The reference four-hole plate has 20 mm minimum edge distance, 120 mm minimum ligament and passes the stated manufacturing geometry criteria. Its authored and recovered engineering hashes match.

`engsvg-multifamily-v1` freezes 30 recovery drawings across truss and mechanical-plate families plus 100 held-out natural-language edit requests. All 30 recovery cases match their authored engineering hashes. Each of the 100 edit records includes its source hash, request, expected structured action, full target IR and target hash. The benchmark checksum manifest currently covers 92 files.

The focused suite now has 30 tests across the portal, common IR, transform-aware geometry, multiple truss topologies, mechanical plates and frozen benchmark construction. This remains synthetic evidence from two object families. The 100 edit requests have references but have not yet been scored with Qwen, the LoRA or Astra.

## Multi-family training launch

A leakage-controlled IR-action dataset is now frozen under `data/engsvg-multifamily-train-v1/`. It contains 10,000 examples from 2,000 distinct source drawings: 8,000 edits, 1,000 clarification responses and 1,000 unsupported-request rejections. The split is performed by source drawing rather than instruction, producing 8,000 training, 1,000 validation and 1,000 test rows. None of the training, validation or test source hashes occurs in the frozen 100-case edit benchmark. The dataset manifest passes all recorded SHA-256 checks.

The LoRA runner uses `Qwen/Qwen2.5-Coder-1.5B-Instruct`, trains for one epoch on the 8,000-row training split, and evaluates exact structured-action accuracy on all 100 frozen edits both before and after training. A prompt-construction defect found during review was corrected before launch: held-out relative edits now receive the original source state, never the already-edited target state. A specific regression check verifies that the first prompt contains the original 10,000 N load and expects an 11,000 N action.

The run was launched on a Colab NVIDIA L4 on 25 September 2026. At launch verification, the payload had unpacked, dependencies were installed, the repository was cloned, the training program was executing, and its output directory existed. Final before/after scores are pending completion; they must be read from `summary.json` in the downloaded run artifact before making an improvement claim.

## Direct SVG dataset v2

The earlier structured pilot and the multi-family v1 training set teach short JSON actions; they do not train direct drawing generation. `engsvg-dataset-factory-v2` fixes that data gap. It contains 10,000 source designs, 30,000 stored SVG renderings and 140,000 tasks. The full SVG XML is embedded in 130,000 prompts and 50,000 targets. The drawing targets comprise 10,000 text-to-SVG examples and 40,000 SVG-to-SVG edits. Other rows train SVG recovery, physics or geometry analysis, exact edit actions, constrained edits, clarification and scope rejection.

Every canonical drawing passed bounded importer round-trip recovery. Every source passed its stated axial-truss FEM equilibrium or plate manufacturing-geometry check. A complete streaming audit parsed all 130,000 SVG prompts and all 50,000 SVG targets, confirmed lineage-exclusive 80/10/10 splits, verified all stored content hashes and found zero overlap with the 2,030 excluded hashes from the frozen benchmark and earlier dataset. Sixteen unpacked SVGs and an HTML gallery are included for visual review.

This v2 dataset remains procedural and limited to two truss topologies and two perforated-plate layouts. It does not support a claim about arbitrary CAD, buildings, furniture or real human editing histories. The already launched L4 job uses v1 JSON-action data; v2 needs a separate long-context SVG training run.

## Claim boundary

This run confirms a repeatable hard benchmark for the Qwen pilot. It does not evaluate Astra, arbitrary detached SVG editing, buildings, tables beyond this side-frame abstraction, or standards-compliant CAD sheets. An Astra-specific claim requires running the same frozen prompts through an identified Astra model and preserving its raw outputs under the same exact evaluator.
