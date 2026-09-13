# FEM-focused literature survey and implemented extension

Updated 13 September 2026. This supplements the earlier graphics survey with the user's clarified focus: engineering problems solved using physics and FEM.

## Conclusion

**The broad idea already exists, including FEM agents, solver verification, and fine-tuning on verified FEM programs.** A paper cannot claim those combinations as new. The candidate extension is maintaining numerical and semantic correctness in the final editable engineering drawing, including after physical and presentation edits. This remains a hypothesis to test against existing simulation and graphics systems; the search does not establish unique novelty.

## Closest primary sources

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

The prior [graphics survey](PRIOR_ART.md) remains relevant for Penrose, scientific SVG generation and diagram editing. The engineering papers establish the solver side; graphics papers establish the editable-artifact side. Their combination still needs a precisely defined, experimentally justified contribution.

## What has actually been built on top of prior work

The local checkout `third_party/FEM-bench` is pinned to commit `d370aef5dbe023b0b86eb3548d24d11fd69328ee`; its MIT license is retained. The new `scripts/fem_bench_svg_extension.py` directly imports the author's unchanged `FEM_1D_linear_elastic_CC0_H0_T0` reference function.

The bridge passes both upstream reference tests, solves 12 generated axial-bar cases, and performs 12 additional FEM solves after a 50% load increase. It writes displacements, reactions, provenance IDs and editable SVG plots for both states. All 24 solves agree with the analytic bar solution to below 2 × 10⁻¹⁸ m in this run; maximum relative force imbalance is below 4.2 × 10⁻¹⁴. These are elementary numerical checks, not evidence of general engineering capability. A stale old tip displacement would be 33.3% low relative to the edited-load solution.

This is a working integration anchor. It does not reproduce the full FEM-Bench leaderboard, train a model on FEM-Bench, or demonstrate a new visual reasoning result. No upstream agent framework has been silently relabeled as ours. Results are in `runs/fem-bench-svg-anchor/`.

Separately, `scripts/robin_fem_reference.py` uses scikit-fem to implement the weak form for the exact historical convective-plate problem. It checks an analytic Robin anchor, discrete heat balance and five mesh resolutions. This is an independent FEM implementation, not a reproduction of MechAgents or ALL-FEM. See the [Astra recheck](ASTRA_FEM_FAILURE_RECHECK.md).

## Next contribution to test

Use a structured physical specification and solver-produced numerical record as the source for an editable drawing. A physical change must cause an actual new solve; a presentation change must preserve the numerical claim and visible meaning. Measure errors after the final SVG is rendered and edited, not only in a solver array or API response.

The main comparison should include direct Astra SVG generation, a published solver-agent workflow, deterministic solver plotting, unrestricted solver-informed SVG editing, and protected numerical/semantic editing. Equalize available physical information and count every attempted case. Test real geometry and material changes, not only load scaling. Include human-written requests, multi-step edits, quantity/unit/legend errors, and visual layout quality. Training is justified only after a stronger task shows a gap that simple prompting or a deterministic parser does not already close.

Prioritize well-posed Robin heat transfer, finite-domain elasticity with explicit material/support/load assumptions, and electrostatics with a stated dimensional and far-boundary model. A sharp-corner stress singularity has no finite mesh-independent peak, so it is a disclosure/identifiability test unless a fillet and load/support model are specified. Reference uncertainty and singular regions must be declared before model scoring.

For CVPR, a language-only code router is insufficient evidence. The study needs an actual visual or graphics contribution and comparisons to multimodal FEA and scientific diagram-editing work. The completed A100 pilot is useful infrastructure; it is not the main FEM experiment.
