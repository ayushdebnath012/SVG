# CVPR 2027 research status

Updated 13 September 2026. Target confirmed by the user: **CVPR 2027**.

## Main conclusion

The broad LLM + solver + SVG idea has substantial prior art. The candidate extension is checking the numerical claims in the final SVG and maintaining them across edits. Novelty is not established by a targeted search, and the project is not yet submission-ready.

Read the [prior-art audit](PRIOR_ART.md). Build on MechAgents/MCP-SIM for simulation workflows, Penrose for semantic/presentation separation, and scientific SVG generation/editing work for graphics baselines. The current implementation extends this repository's numerical evaluator and constrained editing machinery; it does **not** yet reproduce those external systems.

The follow-up [FEM-focused survey](FEM_LITERATURE_AND_EXTENSION.md) adds FEABench, FEM-Bench, ALL-FEM, PDEAgent-Bench, OASiS, VFEAgent and ModSolAgent. These substantially overlap the broad proposed solver/training workflow. A pinned FEM-Bench bar solver is now reused directly for a 24-solve SVG integration anchor with actual load-edit recomputation. This is narrower than a full published-system reproduction.

The [fresh Astra API recheck](ASTRA_FEM_FAILURE_RECHECK.md) corrects the earlier failure narrative: both new Robin SVGs pass direct FEM contour evaluation (maximum errors 0.111 and 0.374 °C), the saved capacitor paths do not contain the alleged closed field loops, and the bracket explicitly discloses its illustrative stress map. The project needs stronger, well-posed physics and visual-edit experiments rather than treating these three cases as established capability limits.

All three A100 pilot runs have completed and their weights/checkpoints are saved locally. See [verified training results](TRAINING_RESULTS.md). This is action-policy training, not FEM-solver training.

## Venue and schedule

The [official CVPR 2027 dates](https://cvpr.thecvf.com/Conferences/2027/Dates) list:

| Milestone | Deadline, Anywhere on Earth |
|---|---|
| Paper registration | 10 November 2026 |
| Main paper | 16 November 2026 |
| Supplement | 23 November 2026 |

The [2027 call](https://cvpr.thecvf.com/Conferences/2027/CallForPapers) is authoritative. The linked author guidelines were unavailable during this audit; recheck formatting and the finalized LLM policy before submission. Use institutional OpenReview profiles early. All authors, affiliations, contributions, licenses and final submission approval remain to be supplied/confirmed by the authors. Nothing has been submitted or publicly released.

| Working period | Required outcome |
|---|---|
| 13–20 September | Correct evaluator, calibrate numerical references, define claim schema and freeze experiment protocol |
| 21 September–4 October | Harder engineering/edit benchmark, split by case and geometry family; baseline reproduction |
| 5–18 October | Main prompting and constrained-editor comparisons; train only objectives with useful baseline gaps |
| 19 October–1 November | Multiple seeds, ablations, sequential edits, numerical mesh convergence, blinded drafting assessment |
| 2–9 November | Complete results, failure analysis, anonymized paper and reproducibility package |
| 10–16 November | Register, recheck current rules, finalize and submit after author approval |
| 17–23 November | Final supplementary material and code/data documentation |

These are work targets, not a promise of acceptance or guaranteed experimental success.

## Completed, reproducible work

1. Replaced endpoint-only contour checks with arc/Bezier sampling, full ancestor SVG transforms, arc-length weighting, and explicit invalid-reference coverage. Missing required levels and unsupported rendering features cannot silently pass. This remains a **sampled geometric audit**, not a full rendered-drawing certificate.
2. Added 22 evaluator regression tests and 8 solver/edit-policy tests. All 30 passed locally.
3. Re-scored all six historical v3 attempts, preserving original raw outputs and including the empty response in denominators.
4. Ran 160 manufactured contour controls: 20 quadratic fields, two honest variants and six corruption types each.
5. Built a self-contained Colab training notebook, deterministic synthetic data, completion-only LoRA training, base/final evaluation, raw prediction retention, configuration hashes and resumable checkpoints.
6. Ran a template-rule baseline on the pilot test and held-out-family splits. It scores 60/60 exact actions on each. Thus this pilot cannot demonstrate that learned routing is necessary.

## Correction to historical proposal claims

Earlier proposal PDFs and TeX files predate the evaluator repair. Their claims of universally validated contour fidelity and their preliminary success totals must **not** be copied into a submission without re-audit. Historical files remain intact for provenance.

At a maximum sampled error threshold of 0.5 percentage points of the specified field range:

| Historical attempt | Mean error, pp | Maximum error, pp | Invalid reference samples | Strict geometry pass |
|---|---:|---:|---:|---|
| L-shaped Laplace | 0.3537 | 80.0000 | 0 | No |
| Square torsion | 0.0701 | 0.3330 | 0 | Yes |
| Plate with square hole | 0.0693 | 0.2677 | 0 | Yes |
| Channel step streamlines | 0.0140 | 0.2459 | 0 | Yes |
| Square conductor in shell | 0.2167 | 0.3791 | 1,528 | No |
| Convective-edge plate | — | — | — | No SVG returned |

Interpretation: 3/6 strict passes are **not** evidence of three incorrect physical solutions. The L-shaped case's largest discrepancies lie at incompatible Dirichlet corners. The shell's boundary contours encounter unsupported/masked raster reference data; its required interior contours have valid samples. These require a stated reference-domain protocol and mesh/reference convergence before assigning model error. Neither dropped samples nor retrospective corner exclusions should improve the headline score silently.

Data: `runs/rescore-v3/{summary.json,results.jsonl}`.

## Manufactured corruption controls

| Checker | Honest accepted (40 cases) | Corrupt accepted (120 cases) |
|---|---:|---:|
| Explicit weak endpoint/local-coordinate baseline | 100% | 66.7% |
| Existing path-string hash protection | 100% | 66.7% |
| Repaired numerical geometry audit | 100% | 16.7% |
| Rigid document freeze except contour color | 100% | 0% |

The numerical audit still accepts every wrong-label corruption because it does not verify text semantics. The freeze baseline supports only the narrow color edit tested here. These are intentionally simple implementation controls, **not** performance estimates on natural model errors or real editing requests. The endpoint baseline is explicitly constructed and is not labeled an exact reproduction of the old evaluator.

Data: `runs/contour-controls/`. Command: `.venv/bin/python scripts/benchmark_contour_audit.py`.

## Training pilot scope

Model: [Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct). LoRA rank 16 on attention projections; 4,358,144 trainable parameters. FP16 base weights, completion-only labels, fixed 3 epochs, seeds 17, 29 and 41, effective batch size 12 (A100 run; the interrupted T4 diagnostic used 16). Model revision and package versions are captured by the run. No remote experiment logging or secret API key is required.

Data: 60 training cases × 6 edits = 360 examples; 10 validation, 10 test, 10 held-out annulus cases × 6 = 60 examples each. Rectangular heat references are FD solves with analytic checks. Annulus references are analytic. The model sees a compact DOM index, **not raster input or complete contour paths**. Instruction templates are shared across splits. All variants of a case stay together. This establishes case disjointness, not language-template generalization. Annular family transfer is limited because the action schema and instructions stay the same.

Actions: contour color, visible stroke width, label position within an annotation panel, route a changed boundary to the solver, reject falsified numeric relabeling, reject removing a required contour. The whitelist executor preserves geometry and bound label text for its generated schema. It does not automatically run a new solve, validate arbitrary incoming SVG, prevent every possible label collision, or prove that a permitted action fulfills the natural-language request.

The rule baseline is perfect on this restricted pilot. Any neural result must be described as pipeline validation or imitation of a simple policy, not as a new graphics capability. A meaningful paper needs diverse visual drafting tasks, context-dependent counterexamples, human-written edits, and strong prompting/deterministic baselines.

Notebook: [Colab GPU experiment](https://colab.research.google.com/drive/1sLxx7qfxd06BDl8FPmpevlJnlKOawVjy). Local self-contained notebook: `notebooks/CVPR2027_controlled_editing.ipynb`. All three seeds completed three epochs and 90 steps on A100, with 60/60 strict exact actions on each evaluation split. The rule baseline also scores 60/60. Adapters, optimizer checkpoints, 720 raw base/final generations and source/data hashes were downloaded and verified; see `reports/training_verified.json`. The runtime is disconnected. A separate inference reload smoke check was prepared but not executed.

## Required before claiming a CVPR contribution

- A real computer-vision/graphics contribution beyond a language-only action router.
- Public-code reproduction or clearly labeled reimplementation of the closest runnable baseline; preserve its license and environment.
- Harder PDE geometry, Robin/elasticity cases, post-edit solver reruns, reference convergence, quantity/unit/legend binding, visibility and occlusion checks.
- Comparable drafting quality and edit success, including layout flexibility beyond a frozen template.
- Human-written or independently sourced instructions and held-out templates, multi-step edits, adversarial requests and honest counterfactuals.
- Prompt-only versus SFT with the same executor, unconstrained versus constrained editor, geometry-only versus semantic checks, deterministic plot/freeze/template controls.
- All attempted cases counted, per-task results, uncertainty grouped by physical case, multiple training seeds, compute and latency measurements.
- Completed manuscript, verified citations, actual figures/results, artifact licenses, anonymization, author review and final submission.
