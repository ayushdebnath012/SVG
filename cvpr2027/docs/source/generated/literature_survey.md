Updated 13 September 2026. This supplements the earlier graphics survey with the user's clarified focus: engineering problems solved using physics and FEM.

# Conclusion

**The broad idea already exists, including FEM agents, solver verification, and fine-tuning on verified FEM programs.** A paper cannot claim those combinations as new. The candidate extension is maintaining numerical and semantic correctness in the final editable engineering drawing, including after physical and presentation edits. This remains a hypothesis to test against existing simulation and graphics systems; the search does not establish unique novelty.

# Closest primary sources

| Work | What overlaps | What to reuse or compare |
|---|---|---|
| **MechAgents**, Ni & Buehler, Extreme Mechanics Letters, 2024 | LLM agents formulate, execute and correct FEM elasticity programs. | A historical solver-agent baseline; published Colab notebooks require older FEniCS/AutoGen dependencies. Do not call a modern reimplementation an exact reproduction. [Paper](https://arxiv.org/abs/2311.08166), [author code](https://github.com/lamm-mit/MechAgents). |
| **MCP-SIM**, npj Artificial Intelligence, 2026 | Language-driven simulation through tools and solver workflows. | Closest earlier simulation orchestration comparison from the first survey; runnable-release limitations are recorded there. [Paper](https://www.nature.com/articles/s44387-025-00057-z), [code](https://github.com/KAIST-M4/MCP-SIM). |
| **FEABench**, Mudur et al., arXiv 2025; paper notes NeurIPS 2024 workshop acceptance | End-to-end natural-language engineering problems solved through COMSOL APIs, with iterative tool feedback. | Reuse the distinction between an executable solver call and a quantitatively correct solution. COMSOL availability is a dependency for faithful reproduction. [Paper and linked code](https://arxiv.org/abs/2504.06260). |
| **FEM-Bench**, Mohammadzadeh et al., December 2025, revised May 2026 | FEM function generation and test generation against reference and deliberately broken implementations. | **Selected for immediate code reuse.** MIT-licensed tasks provide auditable numerical anchors. Its 33-task results are not directly comparable to our SVG editing scores. [Paper](https://arxiv.org/abs/2512.20732), [repository](https://github.com/elejeune11/FEM-bench). |
| **ALL-FEM**, Deotale et al., CMAME 457:118985, 2026 | Fine-tuned models generate FEniCS code in an agentic, feedback-driven workflow. The authors report over 1,000 verified scripts, models from 3B to 120B, and 39 engineering benchmarks. | The most direct precedent for the proposed training component. Training a small solver agent alone is not a new contribution. Its reported code-level success is not a final-drawing correctness metric. [Paper](https://arxiv.org/abs/2603.21011), [author project and journal citation](https://fenics-llm.github.io/). |
| **PDEAgent-Bench**, May 2026 | 645 PDE instances across 11 families, with DOLFINx, Firedrake and deal.II tracks; numerical accuracy and efficiency beyond mere execution. | Use its calibrated-reference philosophy and PDE families when expanding beyond elementary anchors. Keep benchmark test cases out of training. [Paper](https://arxiv.org/abs/2605.09636), [code](https://github.com/YusanX/pde-agent-bench). |
| **OASiS / Open FEM Agent**, 2026 software | MCP access to multiple FEM solvers, numerical verification, convergence studies and visualization. | A current open-source orchestration baseline; its scikit-fem backend matches our local solver ecosystem. This is software prior art, not an assumed peer-reviewed performance result. We have inspected its documentation, not reproduced its full agent evaluation. [Repository and citation](https://github.com/Hereon-InstituteMS/OASiS), [archived earlier release](https://zenodo.org/records/20388035). |
| **VFEAgent**, May 2026, revised August 2026, preprint | Images and text are converted into structured FEA specifications, then simulation code with verification and debugging. | Directly relevant to CVPR positioning: multimodal engineering-drawing-to-FEA workflows already exist. Compare perception, physical specification and final artifact separately. [Paper](https://arxiv.org/abs/2605.28978). |
| **ModSolAgent**, IEEE Transactions on Industrial Informatics, June 2026 | Abaqus script generation with retrieval and iterative verification, plus distilled fine-tuning data. | Another direct precedent for training engineering code models. Abaqus licensing and released assets must be checked before reproduction. [Publisher](https://ieeexplore.ieee.org/document/11452232/). |

The prior [graphics survey](../../reports/PRIOR_ART.md) remains relevant for Penrose, scientific SVG generation and diagram editing. The engineering papers establish the solver side; graphics papers establish the editable-artifact side. Their combination still needs a precisely defined, experimentally justified contribution.

# What has actually been built on top of prior work

The vendored source snapshot `vendor/FEM-bench` is pinned to commit `d370aef5dbe023b0b86eb3548d24d11fd69328ee`; its MIT license is retained. The new `scripts/fem_bench_svg_extension.py` directly imports the author's unchanged `FEM_1D_linear_elastic_CC0_H0_T0` reference function.

The bridge passes both upstream reference tests, solves 12 generated axial-bar cases, and performs 12 additional FEM solves after a 50% load increase. It writes displacements, reactions, provenance IDs and editable SVG plots for both states. All 24 solves agree with the analytic bar solution to below 2 $\times$ 10$^{-18}$ m in this run; maximum relative force imbalance is below 4.2 $\times$ 10$^{-14}$. These are elementary numerical checks, not evidence of general engineering capability. A stale old tip displacement would be 33.3% low relative to the edited-load solution.

This is a working integration anchor. It does not reproduce the full FEM-Bench leaderboard, train a model on FEM-Bench, or demonstrate a new visual reasoning result. No upstream agent framework has been silently relabeled as ours. Results are in `runs/fem-bench-svg-anchor/`.

Separately, `scripts/robin_fem_reference.py` uses scikit-fem to implement the weak form for the exact historical convective-plate problem. It checks an analytic Robin anchor, discrete heat balance and five mesh resolutions. This is an independent FEM implementation, not a reproduction of MechAgents or ALL-FEM. See the [Astra recheck](../../reports/ASTRA_FEM_FAILURE_RECHECK.md).

# Next contribution to test

Use a structured physical specification and solver-produced numerical record as the source for an editable drawing. A physical change must cause an actual new solve; a presentation change must preserve the numerical claim and visible meaning. Measure errors after the final SVG is rendered and edited, not only in a solver array or API response.

The main comparison should include direct Astra SVG generation, a published solver-agent workflow, deterministic solver plotting, unrestricted solver-informed SVG editing, and protected numerical/semantic editing. Equalize available physical information and count every attempted case. Test real geometry and material changes, not only load scaling. Include human-written requests, multi-step edits, quantity/unit/legend errors, and visual layout quality. Training is justified only after a stronger task shows a gap that simple prompting or a deterministic parser does not already close.

Prioritize well-posed Robin heat transfer, finite-domain elasticity with explicit material/support/load assumptions, and electrostatics with a stated dimensional and far-boundary model. A sharp-corner stress singularity has no finite mesh-independent peak, so it is a disclosure/identifiability test unless a fillet and load/support model are specified. Reference uncertainty and singular regions must be declared before model scoring.

For CVPR, a language-only code router is insufficient evidence. The study needs an actual visual or graphics contribution and comparisons to multimodal FEA and scientific diagram-editing work. The completed A100 pilot is useful infrastructure; it is not the main FEM experiment.

\clearpage

# Graphics and adjacent prior art


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

# Public-code feasibility

The inspected MCP-SIM main tree has six agent modules, a README and an MIT license. Several modules import `utils.setup_logger`, but `utils.py` is absent from that tree. A complete orchestration entry point and dependency manifest were also absent. Its executor runs generated Python and scans output for error patterns; that module does not itself establish numerical correctness. The release needs integration work before it can be treated as a reproducible baseline. This observation concerns the public code, not a claim that the paper's private experiments were invalid. [Repository](https://github.com/KAIST-M4/MCP-SIM), [executor](https://github.com/KAIST-M4/MCP-SIM/blob/main/simulation_executor_agent.py).

MechAgents supplies Colab notebooks, but its README specifies older FEniCS, AutoGen and OpenAI versions. Use it as a reproduction source with a separately recorded environment, rather than silently mixing its dependencies into this project. [Repository](https://github.com/lamm-mit/MechAgents).

SciForma's README describes a 9B diffusion backbone and an eight-B200 training setup, with other distributed configurations in its tree. A single Colab GPU would be a reduced adaptation experiment, not an equivalent reproduction of that training setup. [Repository](https://github.com/microsoft/SciForma).


# Paper archive

The catalog and bibliography are in `papers/`. Downloaded PDFs retain their original authorship and publication notices. The download manifest distinguishes bundled PDFs from source links and unavailable downloads. This package does not bypass publisher access controls.
