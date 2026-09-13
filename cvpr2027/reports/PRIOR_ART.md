# Prior art and recommended extension

Research date: 12 September 2026. Scope: the solver-verified engineering SVG proposal and engineering_v4 plan in this repository. This is a targeted literature and public-code audit, not an exhaustive novelty review. Search covered LLM-driven FEM, scientific SVG generation/editing, diagram constraints, physical verification, and PINN baselines. No training was launched during this audit.

## Finding

**The broad idea already exists in several closely related forms.** LLMs invoking and correcting physics solvers, generating editable scientific SVGs, enforcing diagram constraints, and evaluating structural correctness are established research directions. Merely combining an LLM, FEM/PINN, and SVG is not a strong standalone novelty claim.

**The candidate extension is numerical fidelity of the final editable drawing, maintained across edits.** Treat a displayed contour, quantity label, unit, and legend entry as claims linked to a particular numerical solution. Verify those claims after drafting and editing. Report where the verification is incomplete instead of treating successful rendering as physical correctness. I did not identify a work implementing this entire contract in the sources checked; this absence is not proof that none exists.

## Closest work and what to reuse

| Work | Verified overlap | How this project could extend it |
|---|---|---|
| **MechAgents**, Ni and Buehler, preprint 2023; Extreme Mechanics Letters 2024 | Agents write, execute, and correct FEM code for elasticity. Its examples explicitly include plotting the wrong stress quantity and subsequently correcting it. | Reuse its elasticity tasks and solver-agent baseline; automatically check that the displayed quantity and contours agree with the solution, including after user edits. [Paper](https://arxiv.org/abs/2311.08166), [author code and Colab notebooks](https://github.com/lamm-mit/MechAgents). |
| **MCP-SIM**, Park, Moon and Ryu, npj Artificial Intelligence, January 2026 | Natural-language specifications become simulations and explanations through clarification, execution, and correction. Its reported twelve-task success is specific to that evaluation. | Use its workflow as a named simulation baseline. Add explicit solver-to-SVG provenance and post-edit verification. [Paper](https://www.nature.com/articles/s44387-025-00057-z), [author repository](https://github.com/KAIST-M4/MCP-SIM). |
| **SSVG-Bench / LOOP**, *Towards the Generation of Structured Scientific Vector Graphics with Large Language Models*, inspected ICLR 2026 submission | Scripted structural evaluation for plane geometry and molecular diagrams, spanning TikZ, SVG and EPS; reasoning-oriented prompting. The accessed manuscript is labeled under review; acceptance and released code were not verified. | Extend structural checks to numerical PDE fields and edit sequences; do not claim to invent non-visual correctness metrics for scientific diagrams. [Manuscript](https://openreview.net/pdf?id=aWypD2TAaC). |
| **Penrose**, SIGGRAPH 2020 | Separates mathematical meaning and visual styling, uses constraints for layout, and exports SVG. | Borrow the separation of semantics from layout. Physical contours must be computed and bound to the solution; layout constraints alone do not establish PDE accuracy. [Author-hosted paper](https://penrose.ink/media/Penrose_SIGGRAPH2020.pdf), [code](https://github.com/penrose/penrose). |
| **AutoFigure-Edit**, ACL system demonstrations 2026 | Generates editable scientific illustrations with reference-guided styling and an SVG editing interface. | Strong available graphics baseline: test whether its edits preserve solver-derived geometry, field labels and units. [Published paper](https://aclanthology.org/2026.acl-demo.6/), [author code](https://github.com/ResearAI/AutoFigure-Edit). |
| **SciDiagramEdit**, July 2026 preprint | Edits scientific vector sources using instructions derived from paper revisions; improves an editor through skill evolution over execution traces. | Closest editing-learning comparison. Add numerical verification to the editing objective. Its skill evolution is not the same as weight fine-tuning. No official code release was verified in this audit. [Paper](https://arxiv.org/abs/2607.15272). |
| **SVGEditBench V2**, February 2025 preprint | Instruction-based SVG editing on emoji-derived examples, evaluated with visual, semantic and geometric metrics. | Retain it as a general editing control, and add physical-claim checks on engineering cases. It is not a physics benchmark. [Paper](https://arxiv.org/abs/2502.19453). |
| **FMforME**, *A Three-Layer Runtime Constraint Verification Framework…*, Applied Sciences 2026 | Validates structured CAD specifications and feeds detected defects back to the LLM. Its stated future work includes extending through FEA solving. | Compare specification validity with actual solved-field fidelity. Do not copy its domain-specific engineering rules as universal physical laws. [Article](https://www.mdpi.com/2076-3417/16/15/7396). |
| **SciForma**, July 2026 preprint | Scientific methodology-diagram generation with component, arrow and text evaluation and multidimensional preference training. | Borrow the idea that all required correctness dimensions must pass. Its released renderer is a diffusion image model, so it is an adjacent visual baseline rather than a native SVG/PDE implementation. [Paper](https://arxiv.org/abs/2607.18091), [author repository](https://github.com/microsoft/SciForma). |
| **Text2PDE**, October 2024 preprint | Text-conditioned latent-diffusion physics simulation. | Relevant if extending into learned simulation, but much broader than the current need for trustworthy SVG export and editing. [Paper](https://arxiv.org/abs/2410.01153). |

## Public-code feasibility

The inspected MCP-SIM main tree has six agent modules, a README and an MIT license. Several modules import `utils.setup_logger`, but `utils.py` is absent from that tree. A complete orchestration entry point and dependency manifest were also absent. Its executor runs generated Python and scans output for error patterns; that module does not itself establish numerical correctness. The release needs integration work before it can be treated as a reproducible baseline. This observation concerns the public code, not a claim that the paper's private experiments were invalid. [Repository](https://github.com/KAIST-M4/MCP-SIM), [executor](https://github.com/KAIST-M4/MCP-SIM/blob/main/simulation_executor_agent.py).

MechAgents supplies Colab notebooks, but its README specifies older FEniCS, AutoGen and OpenAI versions. Use it as a reproduction source with a separately recorded environment, rather than silently mixing its dependencies into this project. [Repository](https://github.com/lamm-mit/MechAgents).

SciForma's README describes a 9B diffusion backbone and an eight-B200 training setup, with other distributed configurations in its tree. A single Colab GPU would be a reduced adaptation experiment, not an equivalent reproduction of that training setup. [Repository](https://github.com/microsoft/SciForma).

## Recommended research question

**Can a solver-linked SVG representation preserve quantitative physical claims through natural-language edits while retaining drafting quality?**

Build on MechAgents/MCP-SIM for the simulation workflow, AutoFigure-Edit/SciDiagramEdit for the editing comparison, and Penrose/SSVG-Bench for semantic separation and structural checking. Keep the existing scikit-fem references and SVG Patch Lab executor as the local implementation foundation; a wholesale rewrite would discard working components without establishing a new contribution.

The extension should have four concrete parts:

1. A solution record containing geometry, PDE, boundary conditions, units, field name, solver version, mesh/resolution and numerical validation results.
2. An SVG field layer with bound contour levels and a physical-coordinate mapping; enforce protection in code, not only in the model prompt.
3. A post-edit verifier covering curves, quantity labels, units, legends, missing contours, changed ancestor transforms, and hidden or occluded content. An unchanged path string alone is insufficient.
4. A benchmark of edits that preserve the physical problem, edits that change it and require re-solving, and intentionally misleading edits that must be rejected or disclosed.

This is a proposed experimental contribution. A tagged SVG is not a formal proof, and finite numerical sampling is not a mathematical guarantee over an entire curve.

## First experiment before training

Use three existing problem families: Robin conduction, a plate with a hole, and finite-plate electrostatics after validating its reference. Start with twelve distinct physical cases and five edit requests per case: relabel, restyle, rearrange layout, change a physical input, and request a misleading modification. Keep all variants of one physical case in the same split. Publish generated geometry seeds and hold out geometry families for generalization tests.

Compare the same cases under:

- Direct SVG generation/editing.
- Solver information supplied to an unrestricted SVG editor.
- Protected physical geometry with unrestricted annotation semantics.
- Protected geometry plus bound quantities, units, legend semantics, and post-edit verification.
- A deterministic solver plot with template labels, to test whether an LLM adds useful drafting capability at all.

Report field error, required-contour coverage, wrong-quantity rate, wrong-unit rate, render validity, edit success, rejection/disclosure rates and latency separately. Include all attempted cases in denominators. Distinguish numerical reference uncertainty from model error. For plots with contour singularities or incompatible corner data, state exclusions and show full-domain results alongside them.

## Local prerequisite discovered during this audit

The current `scripts/field_fidelity.py` samples only endpoints for straight `L`, `H` and `V` segments; SVG arcs are also reduced to endpoints. It approximates smooth curves without fully implementing reflected control points, applies only element-local transforms, and drops out-of-grid/NaN samples from error averages. These limitations can create false passes and must be addressed before using its scores as training rewards.

A local diagnostic using its actual `sample_path` function returned only `(1,0)` and `(0,1)` for `M 1 0 L 0 1`. In the field `u=x²+y²`, both endpoints have level 1, producing sampled mean error 0. The line midpoint has value 0.5, so its missed error is 0.5. This demonstrates an evaluation vulnerability; it does not by itself quantify errors in the historical runs. Re-score those runs after fixing the verifier before repeating claims of solver-level accuracy.

The existing Colab notebook `1DYcWtnUwE_w_5Tkt_vyemIv8Xoe7pIVQ` contains CPU FEM/FD validation and no neural training loop. Browser access was confirmed, but no runtime was connected and no GPU training was launched.

## Training decision after establishing the baseline

For the central research question, train a small SVG patch model only if verified examples show a useful gap beyond prompting and the deterministic baseline. Use solver-generated training examples and validated successful edits; prevent leakage by splitting physical cases and geometry families before generating edit variants. Evaluate SFT against the untrained base model with the same executor and verifier. A Colab LoRA run is a possible implementation, with model, data volume and stopping rule selected after measuring the baseline.

Train a parametric PINN only for a separate solver-surrogate question, such as generalization across heat-transfer coefficients or geometry parameters. The original PINN formulation and solid-mechanics extensions are established prior work. A systematic comparison found FEM superior in solution time and accuracy for its tested PDEs; fast trained inference must be weighed against training cost. [Raissi et al.](https://www.sciencedirect.com/science/article/pii/S0021999118307125), [Haghighat et al.](https://arxiv.org/abs/2003.02751), [Grossmann et al.](https://arxiv.org/abs/2302.04107).

**Recommendation:** establish and repair the verifier, reproduce a solver-assisted editing baseline, and build the physical-claim-preserving extension. Then use Colab training to test a specific improvement. Do not spend a full training run reproducing generic PINN behavior and call that evidence for the SVG contribution.
# FEM-focused follow-up

The later [FEM literature survey and implemented extension](FEM_LITERATURE_AND_EXTENSION.md) expands this targeted graphics review with FEABench, FEM-Bench, ALL-FEM, PDEAgent-Bench, OASiS, VFEAgent and ModSolAgent. In particular, verified FEM-code fine-tuning and multimodal engineering-drawing-to-FEA workflows already exist. Use both surveys when assessing novelty.
