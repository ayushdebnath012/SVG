# CVPR 2027 — engineering SVG research package

**Current editor and paper — 1 October 2026.** Editing now uses source-tree parsing and parsed, validated patches throughout, including version-3 structural patches for bridge topology changes. [Evidence, examples and reproduction](reports/ENGINEERING_EDITOR_OVERVIEW_20261001.md); [updated paper](paper/network/main.pdf). The manuscript now shows SVG editing with circuit/hydraulic checks, axial-truss FEM, plate-clearance checks and a separately audited structural-frame example. Five concrete edits were replayed, including a 21-to-29-member bridge and a correctly edited plate that fails its clearance rule. The saved deterministic 40,000-edit audit and the learned network/cross-domain model results are reported separately.

Earlier dated material below is retained as history. Serpentine routing and nesting attempts ended incomplete or with API errors; they are no longer running and provide no confirmed failure claim.

**Continuing 22 September:** [Harder drawing, routing and nesting prompts](reports/ASTRA_DRAWING_ROUTING_DISCOVERY_20260922.md) have verified feasible reference SVGs and independent geometry checks. Six completed conditions pass; dense serpentine routing and irregular-part nesting later ended incomplete or with API errors. No repeatable failure has been admitted yet. The literature registry now has 72 records; no new training has started.

**Completed 22 September:** [Functional design discovery](reports/CAD_FUNCTIONAL_DISCOVERY_20260921.md) tested six new catalog-section designs with FEM, Euler buckling, mass constraints and SVG readback. All six passed Astra; 5,576,554 reference assignments were enumerated. The registry contains 67 records with review levels. No repeatable hard case, established novelty claim or new training. Further API screening stopped to conserve credits.


**Latest evidence (21 September):** [Extended drawing tests and 62-source literature audit](reports/CAD_EXTENDED_DISCOVERY_20260921.md). Five new custom cases passed Astra. Two complex released drawings produced valid CAD solids and passed 38/11 local checks respectively; their full geometry remains unscored. No repeatable Astra-hard shape or established novelty claim was found. New close prior work also covers semantic SVG edit propagation and uncertainty-aware mechanical drawing audit. No new training was started. [Earlier foundation and proposed method](reports/PROJECT_FOUNDATION_20260921.md).

Branch: `cvpr2027-research-package`. This folder contains the proposal, literature survey, working paper, completed diagnostic evidence, saved A100 adapters and experiment plans for CAD-style engineering SVG drawings of objects such as tables, buildings, frames and parts. The intended system generates or edits dimensioned drawings linked to a physical model and checks affected designs with appropriate analysis, including FEM. Existing implementations cover field diagnostics and a limited axial-bar edit/re-solve integration; the first object-drawing pilot now covers idealised frames and solid plates; general CAD generation and validation remain unfinished. The main benchmark and paper are unfinished; no submission has been made.

**Scope clarified on 20 September 2026:** read the [CAD drawing scope](reports/CAD_DRAWING_SCOPE.md). It supersedes the field-plot-centred future-work framing in the earlier proposal, overview, plain-language summary, roadmap and `engineering_v4` plan. Those documents and their recorded experiments remain available, but do not establish table or building design validation.

**New CAD work (20 September):** [25-source internet literature and dataset audit](reports/CAD_WEB_LITERATURE_AND_DATASETS_20260920.md), [Astra CAD pilot results](reports/ASTRA_CAD_PILOT_20260920.md), and [released-data training pilot](data/cad-editor-pilot/README.md). Eight screened drawings passed the implemented geometry checks; one analysis error remains unconfirmed. The failure-only shape benchmark is currently empty.

**Follow-up discovery:** [39-source novelty stress test](reports/CAD_NOVELTY_OVERLAP_20260920.md) finds substantial prior-art overlap. [Ten harder CAD prompt conditions](reports/ASTRA_CAD_HARD_DISCOVERY_20260920.md), including 0.05 mm inspection templates, all passed Astra screening and are excluded from the hard subset. No repeatable shape failure or distinct research contribution has been established yet.

## Read the documents

**Native CAD follow-up:** [49-source novelty audit and four tool-enabled Astra edits](reports/CAD_NATIVE_AND_NOVELTY_20260920.md). All four final edits passed; a transient sweep error was repaired using execution feedback. [Actual SVG projection sheets](runs/astra-cad-native-20260920/screen-responses/gallery.html) and raw API traces are retained. The hard subset remains empty. Recovering lost engineering relationships from detached SVGs is a narrower hypothesis, not an established contribution.

| Document | PDF | Editable LaTeX | Authoring source |
|---|---|---|---|
| Research proposal and alternative ideas | [PDF](output/pdf/research_proposal.pdf) | [LaTeX](docs/latex/research_proposal.tex) | [Markdown](docs/source/research_proposal.md) |
| Experiment protocol, hypotheses and remaining work | [PDF](output/pdf/experiment_protocol.pdf) | [LaTeX](docs/latex/experiment_protocol.tex) | [Markdown](docs/source/experiment_protocol.md) |
| Literature survey and reuse decisions | [PDF](output/pdf/literature_survey.pdf) | [LaTeX](docs/latex/literature_survey.tex) | [FEM survey](reports/FEM_LITERATURE_AND_EXTENSION.md), [graphics survey](reports/PRIOR_ART.md) |
| Completed results and failure audit | [PDF](output/pdf/results_and_failure_audit.pdf) | [LaTeX](docs/latex/results_and_failure_audit.tex) | [Astra/FEM](reports/ASTRA_FEM_FAILURE_RECHECK.md), [training](reports/TRAINING_RESULTS.md), [status](reports/RESEARCH_STATUS.md) |
| Working research paper | [PDF](output/pdf/working_paper.pdf) | [LaTeX](docs/latex/working_paper.tex) | [Markdown](paper/manuscript.md) |
| Consolidated overview: problem, theory, architecture, all experiments and plans | [PDF](output/pdf/research_overview.pdf) | [LaTeX](docs/latex/research_overview.tex) | hand-authored LaTeX (17 Sep 2026) |
| Plain-language summary: problem, data, system, experiments and results without jargon | [PDF](output/pdf/plain_language_summary.pdf) | [LaTeX](docs/latex/plain_language_summary.tex) | hand-authored LaTeX (18 Sep 2026) |
| Roadmap: phases, data engine, models to train per mode, compute, gates and dates | [PDF](output/pdf/roadmap.pdf) | [LaTeX](docs/latex/roadmap.tex) | hand-authored LaTeX (18 Sep 2026) |

[Paper library](papers/README.md): 20 source records, 15 downloaded PDFs, BibTeX and download provenance. Five sources remain links; unavailable downloads are recorded. [Document build instructions](docs/README.md) explain how to regenerate all PDFs.

## What the evidence establishes

- Three A100 LoRA runs completed (seeds 17, 29, 41; three epochs and 90 steps each). All final adapters and 720 saved base/final predictions are included. Final models and the deterministic rule baseline both score 60/60 on test and held-out-family splits. This shared-template pilot validates the pipeline and does not establish a learned advantage. [Zero-shot Astra also scores 60/60 on both splits](reports/ASTRA_CONTROLLED_EDITING_BASELINE.md) (120 calls, $0.61), which is the benchmark reference for the pilot and shows the task has no gap for learning.
- On [twelve harder drawing tasks](reports/ASTRA_HARD_TASKS_20260918.md) (annulus, sinusoidal edge, L-shape, an unseen polygon, a Robin sweep, line charges, cylinder flow, Kirsch, two ill-posed cases), Astra reproduces closed-form fields to solver accuracy, fails clearly on the unseen polygon (4.5 pp mean), degrades at Biot 10, leaves the Kirsch field incomplete, and discloses both ill-posed cases; 6/10 geometric passes, $4.83.
- Four direct Astra API calls were completed. Both new Robin drawings pass direct FEM curve sampling (maximum errors 0.111 and 0.374 degrees Celsius). The old failure did not reproduce. The historical capacitor closed-loop claim was incorrect; the bracket explicitly discloses illustrative stress contours.
- The numerical contour checker accepts 20 of 120 manufactured corruptions because it does not verify visible labels. This is a concrete evaluator limitation to address. It is not a measured Astra failure rate.
- The unchanged, pinned FEM-Bench axial-bar solver supplies an implemented upstream extension: two reference tests and 24 actual solves for original/edited drawings. It is a simple integration anchor.

The proposed contribution is a representation and verifier binding numerical geometry, visible claims and the current physical solution through edits. The novelty claim remains provisional. A nontrivial main benchmark, broader solver-agent comparisons, semantic/visibility verification, and visual usefulness assessment are still required. The working paper is not an official CVPR template or submission-ready manuscript.

## Reproduce locally

Use Python 3.10 or newer. From this folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-local.txt
.venv/bin/python scripts/experiments.py list
.venv/bin/python scripts/experiments.py run C01
.venv/bin/python scripts/experiments.py run C05
.venv/bin/python scripts/experiments.py run C10
```

The runner sets `PYTHONPATH=src`, uses argument lists without a shell, and writes each reproduction into a fresh timestamped directory under `tmp/reproduction/`. `--output-root PATH` selects another destination; `--dry-run` prints the command without execution. C01 runs the 30 regression tests, C05 verifies saved training artifacts and recomputes scores, and C10 runs the vendored solver extension. C02–C04 and C07–C09 reproduce the other CPU diagnostics. C08 copies saved drawings before writing new scores. C07 recomputes all five FEM mesh levels.

[The registry](experiments/registry.json) distinguishes completed C01–C10 from proposed P01–P08. Planned jobs have no executable command until implemented; attempting to run one exits with an explanation. C06 is a saved API record, with no automatic repeat. Numeric checks work without a native Cairo installation. Optional CairoSVG image rendering also needs the system Cairo library.

## GPU training and explicit API repeats

[The Colab reproduction report](reports/COLAB_REPRODUCTION_20260916.md) records a
complete A100 run of the packaged batch on 2026-09-16: regression tests, both
adapter inference reload checks, three fresh LoRA seeds, the FEM references and
the rule baseline. The re-trained adapters are byte-identical to `runs/a100`
and every prediction matches; artifacts are in `runs/colab-a100-20260916/`.
[The remote reproduction report](reports/REMOTE_REPRODUCTION_20260917.md) records
the same batch on the Serveo SSH host's RTX PRO 6000 Blackwell on 2026-09-17: all
stages passed, every final prediction matches the A100 run, and the adapter
weights differ only by cross-architecture rounding (`runs/blackwell-20260917/`).
[The remote batch guide](reports/REMOTE_COMPUTE.md) documents that host.

[The self-contained Colab notebook](notebooks/CVPR2027_controlled_editing.ipynb) embeds the training/data scripts, installs the recorded training dependencies, runs three seeds and exports artifacts. Select an available A100 runtime. The completed runs used NVIDIA A100-SXM4-40GB; the previous runtime is disconnected. GPU availability is not guaranteed by the notebook. [Completed execution logs](notebooks/A100_completed_runs.ipynb) are retained separately.

Training requires CUDA PyTorch plus `requirements-colab.txt`. The saved adapter files have passed structural and checksum validation. `scripts/check_adapter_reload.py` is the GPU smoke check for those adapters; it passed 18/18 on 2026-09-16 (see the Colab reproduction report). No new training is claimed by this packaging commit.

A deliberately requested repeat of the four-case API diagnostic can use:

```sh
# Set OPENAI_API_KEY in your local environment; do not put it in tracked files.
.venv/bin/python scripts/audit_astra_api.py --project . --output tmp/astra-new-run
```

This command makes billable requests to the configured OpenAI endpoint and records every attempted outcome; it is not called by the CPU runner. Its historical model alias may require updating for a future account. Preserve the request configuration and do not overwrite old evidence.

## Package layout and provenance

- `src/`, `scripts/`, `tests/`: supporting modules, runnable experiments and regression checks.
- `data/`, `configs/`: pilot splits, original prompts and historical SVG inputs.
- `runs/`: original API responses, FEM references, CPU audit records, A100 final adapters, predictions and manifests.
- `vendor/FEM-bench/`: selected unmodified MIT-licensed upstream files at commit `d370aef5dbe023b0b86eb3548d24d11fd69328ee`; see `UPSTREAM.json` and `LICENSE`.
- `experiments/`: completed/planned job registry with dependencies and evidence paths.
- `paper/`, `reports/`, `docs/`, `output/pdf/`: manuscript, evidence narratives, editable sources and review PDFs.
- `RUN_INDEX.json`, `SHA256SUMS.json`: evidence index and checksums of packaged files; `reports/package_verification.json` records packaging checks.

Redundant ZIP downloads and intermediate optimizer checkpoints remain local and ignored; final adapters and trainer states are versioned. The upstream nested checkout in `third_party/`, compiler binaries, virtual environments and temporary render/reproduction files are also ignored. A fresh checkout can rerun training from scratch; resuming an intermediate optimizer state requires the local checkpoint archive. No API credential is included.

Historical SVG inputs in `runs/historical-v3/results.jsonl` retain only the fields needed for rescoring. Per-SVG hashes remain reproducible; a historical whole-file hash can refer to the original parent-project record. Earlier proposal PDFs outside this folder predate the evaluator correction. Use the current reports for scientific claims.
