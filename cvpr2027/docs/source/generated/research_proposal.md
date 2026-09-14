# Proposed title and status

**Physics-consistent editing of engineering vector drawings**

Target: CVPR 2027. This is a proposal backed by limited diagnostic experiments, not an accepted contribution or completed submission. Author list and affiliations are pending. The repository branch packages the evidence, implementation, alternatives and remaining experiments together.

# Research question

Can an editable engineering drawing preserve the meaning of its numerical claims through natural-language presentation and physical edits, while remaining useful for drafting?

A curve marked 40 degrees Celsius is a numerical assertion about every point on that curve. A stress legend asserts a quantity, unit and scale. Changing a load invalidates a previous solution even when its plot still looks plausible. Changing an ancestor SVG transform can invalidate geometry without changing the path string. The output to evaluate is the final drawing, together with the physical problem and numerical evidence supporting it.

# What prior work already establishes

MechAgents, MCP-SIM and OASiS connect language models to numerical simulation. FEABench and PDEAgent-Bench evaluate simulation and solver generation. FEM-Bench evaluates FEM functions and tests. ALL-FEM and ModSolAgent already fine-tune models for engineering solver workflows. VFEAgent addresses image/text-to-FEA. Penrose separates mathematical semantics from visual style; scientific SVG generation and editing have their own benchmarks and methods.

Therefore, LLM plus FEM, verified-code fine-tuning, multi-agent orchestration, and multimodal input are not sufficient novelty claims. The proposed contribution concerns consistency between the solved physical problem and the final editable artifact, particularly across a sequence of edits. The companion literature survey gives source links, reuse choices and known release limitations. It does not prove that the proposed combination is absent from all prior work.

# Proposed representation

Each artifact has four associated records:

1. **Physical specification:** domain, dimensional assumptions, PDE, material law, loads, supports, boundary conditions, units and requested quantities. Unknown values remain explicit.
2. **Numerical solution:** solver and version, discretization, mesh, tolerances, fields, reactions/fluxes, convergence checks and provenance.
3. **Drawing claims:** SVG element IDs, physical-coordinate mapping, field quantity, contour level, associated text, unit and legend binding.
4. **Edit record:** instruction, parsed operation, affected physical inputs or presentation properties, numerical invalidation, solver execution and verifier outcome.

Content hashes record identity; they do not prove that a solution is correct. A reference solution must pass its own physical and numerical checks. The representation must distinguish a computed field, a sampled geometric check, a schematic illustration and an unsupported claim.

# Proposed system

The planner resolves the engineering specification and requests missing information only when necessary for a well-posed problem. A solver executes the specified model. A deterministic exporter creates the numerical field geometry. The editor proposes changes to geometry, annotations or presentation through a structured interface. The verifier checks the final artifact and either accepts it within a stated scope, reports a limitation, or requests a repair/re-solve.

Presentation edits preserve the physical solution but may change layout, line style and annotation position. Physical edits create a new specification and trigger a new solve. Unsupported semantic changes cannot retain the old verification status. Requests that contradict the specification must be rejected or clearly marked as illustrative.

For the main study, the system must inspect visible labels, units, legends and occlusion in addition to stored metadata. Merely attaching a solution ID to an SVG is insufficient. Both useful layout flexibility and numerical/semantic consistency must be measured.

# Hypotheses and falsification

| ID | Hypothesis | Evidence required | Result that would weaken it |
|---|---|---|---|
| H1 | Joint geometric and semantic checking reduces false acceptance after edits. | Fewer accepted wrong-field, wrong-unit and stale-solution outputs at comparable edit success. | Geometry-only or deterministic controls perform equally well. |
| H2 | A structured physical-edit path prevents reuse of stale fields. | Actual solver reruns and correct updated plots after load, material, boundary and geometry changes. | Provenance IDs change but plotted numbers remain stale. |
| H3 | Flexible protected editing is more useful than freezing the drawing. | Blinded drafting and instruction-fulfillment ratings improve without weakening numerical checks. | A simple plotting template matches quality and success. |
| H4 | Learning helps on context-dependent, visually grounded edits. | SFT improves over the same base model, executor and information on held-out cases/templates. | A rule parser or prompting closes the gap. |
| H5 | The method generalizes beyond a single PDE or SVG template. | Independent geometry-family, instruction-template and sequential-edit holdouts. | Gains disappear when templates or layouts change. |

The study should report negative results. A strong deterministic baseline is useful evidence about the necessity of learned components, not a baseline to weaken artificially.

# Evidence already available

The repaired contour evaluator samples curves and composes ancestor transforms, retains unsupported-reference samples, and checks required levels. Thirty regression tests pass. It remains a sampled geometric audit; arbitrary labels, units, legends and occlusion are not fully covered.

On 160 manufactured controls, the geometric checker accepts 20 of 120 corrupted examples, all wrong-label cases. A rigid freeze baseline accepts none. This identifies missing semantic checks, but does not establish superiority over the rigid baseline.

Re-auditing six historical drawings gives three strict geometric passes. The other outcomes include incompatible-corner reference ambiguity, masked boundary coverage and an empty response. They are not three demonstrated incorrect physical solutions.

Four fresh Astra API calls revisit the suspected failures. Both Robin heat drawings pass direct FEM contour sampling, with maximum errors 0.111 and 0.374 degrees Celsius. The old closed-loop claim about the capacitor is contradicted by its saved paths. The bracket discloses its illustrative stress field. These corrections rule out an unqualified claim that these cases demonstrate general FEM incapability.

Three A100 LoRA runs completed on the compact-DOM action pilot. Every final adapter and the deterministic rule parser score 60/60 on both evaluation splits. This is training infrastructure validation, not evidence of a new engineering or visual capability.

A working extension imports the unchanged FEM-Bench axial-bar solver and performs 24 actual FEM solves, including load edits. It passes the two upstream reference tests, analytic displacement and force-balance checks. It is an elementary integration anchor, not the main benchmark.

# Main benchmark proposal

Begin with well-posed Robin conduction, finite-domain linear elasticity and electrostatics. Each family needs analytic anchors, converged numerical references and seeded geometry/material variants. Specify plane stress versus plane strain or 3-D assumptions, traction distributions, supports, fillets and far-boundary treatment. Do not grade an infinite-plate formula as exact for a finite square plate.

Keep all variants of a physical case in one split. Separate unseen geometry from unseen language templates. Include honest counterfactuals and misleading requests, as well as ordinary restyling and layout changes. Multi-step sequences should alternate physical changes and presentation changes so that stale claims can be exposed.

Compare direct Astra editing, unrestricted solver-informed editing, a published solver-agent workflow, protected geometry, joint protection and deterministic solver plotting. Use equal numerical information where the comparison requires it. Human evaluation should assess readability, instruction fulfillment and visible claim correctness on anonymized, randomized outputs.

# Training proposal

Do not scale the current perfect-template pilot as the main experiment. First establish a difficult task and an improvement opportunity beyond deterministic and prompt-only controls. Construct training examples from verified solver records and successful edits, with rejected edits and corrective feedback represented separately.

Use the current small open-weight model as an initial cost-bounded baseline. Add image/complete-SVG context only with a model and representation that actually support those inputs. Freeze the evaluation protocol before hyperparameter selection. Use validation for selection and three seeds for a final justified configuration. Test-time cases, failed-example inspection and human instructions used in evaluation must not silently enter training.

# Alternative proposals

**A. Benchmark and audit contribution.** Build a carefully calibrated benchmark of numerical/semantic failures in engineering drawings. This can remain valuable if no new learned method is needed. Its strength would be reference quality, realistic editing tasks and reproducible assessment, not a large synthetic sample count alone.

**B. Solver-linked graphical representation.** Focus on the representation and verifier, comparing useful edits to rigid freezing and deterministic plotting. This is the preferred initial direction because it connects the numerical and graphical parts of the existing implementation.

**C. Learned solver-code assistant.** Extend ALL-FEM or FEM-Bench with training on engineering programs. This overlaps strongly with existing work and has a weaker CVPR fit unless a substantive visual component is established. Do not present it as a novel fallback merely because GPU training is available.

**D. Learned numerical surrogate.** Train a PINN or field surrogate for a specific parametric family and compare its total cost and accuracy with FEM. This is a separate scientific question and should not be added solely to include a neural solver.

# Risks and decision gates

The principal risks are reference error masquerading as model error, under-specified engineering tasks, trivial templated edits, visual quality lost through over-restriction, and overlap with prior systems. Address these through independent checks, explicit task specifications, strong deterministic controls, blinded evaluation and a full baseline audit.

Gate 1: references and elementary integration pass before main model comparisons. Gate 2: the benchmark exposes a useful gap before large training. Gate 3: a visual/graphics contribution survives the strongest controls before claiming CVPR readiness. If these gates fail, narrow the claim or change venue rather than inflate the result.

# Delivery and schedule

The official CVPR 2027 dates currently list registration on 10 November 2026, main paper on 16 November and supplementary material on 23 November, all Anywhere on Earth. Recheck the current call and author instructions before submission: <https://cvpr.thecvf.com/Conferences/2027/Dates>.

September: lock references, claim schema, realistic task protocol and baseline environments. October: main comparisons, justified training, sequential edits, ablations and human assessment. Early November: complete results, anonymous paper, figures, limitations and artifact instructions. Submission requires authorship information, author review and final approval; none is implied by this package.

Deliverables include source code, exact experiment configurations, input/reference/output records, per-case metrics, compute accounting, licenses, paper sources and a reproducibility guide. The companion experiment protocol translates these goals into explicit jobs and acceptance criteria.
