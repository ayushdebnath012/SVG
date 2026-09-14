# CVPR 2027 — engineering SVG research package

Branch: `codex/cvpr2027-research-package`. This folder contains the proposal, literature survey, working paper, completed diagnostic evidence, saved A100 adapters and experiment plans for physics-consistent editing of engineering vector drawings. The main benchmark and paper are unfinished; no submission has been made.

## Read the documents

| Document | PDF | Editable LaTeX | Authoring source |
|---|---|---|---|
| Research proposal and alternative ideas | [PDF](output/pdf/research_proposal.pdf) | [LaTeX](docs/latex/research_proposal.tex) | [Markdown](docs/source/research_proposal.md) |
| Experiment protocol, hypotheses and remaining work | [PDF](output/pdf/experiment_protocol.pdf) | [LaTeX](docs/latex/experiment_protocol.tex) | [Markdown](docs/source/experiment_protocol.md) |
| Literature survey and reuse decisions | [PDF](output/pdf/literature_survey.pdf) | [LaTeX](docs/latex/literature_survey.tex) | [FEM survey](reports/FEM_LITERATURE_AND_EXTENSION.md), [graphics survey](reports/PRIOR_ART.md) |
| Completed results and failure audit | [PDF](output/pdf/results_and_failure_audit.pdf) | [LaTeX](docs/latex/results_and_failure_audit.tex) | [Astra/FEM](reports/ASTRA_FEM_FAILURE_RECHECK.md), [training](reports/TRAINING_RESULTS.md), [status](reports/RESEARCH_STATUS.md) |
| Working research paper | [PDF](output/pdf/working_paper.pdf) | [LaTeX](docs/latex/working_paper.tex) | [Markdown](paper/manuscript.md) |

[Paper library](papers/README.md): 20 source records, 15 downloaded PDFs, BibTeX and download provenance. Five sources remain links; unavailable downloads are recorded. [Document build instructions](docs/README.md) explain how to regenerate all PDFs.

## What the evidence establishes

- Three A100 LoRA runs completed (seeds 17, 29, 41; three epochs and 90 steps each). All final adapters and 720 saved base/final predictions are included. Final models and the deterministic rule baseline both score 60/60 on test and held-out-family splits. This shared-template pilot validates the pipeline and does not establish a learned advantage.
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

[The self-contained Colab notebook](notebooks/CVPR2027_controlled_editing.ipynb) embeds the training/data scripts, installs the recorded training dependencies, runs three seeds and exports artifacts. Select an available A100 runtime. The completed runs used NVIDIA A100-SXM4-40GB; the previous runtime is disconnected. GPU availability is not guaranteed by the notebook. [Completed execution logs](notebooks/A100_completed_runs.ipynb) are retained separately.

Training requires CUDA PyTorch plus `requirements-colab.txt`. The saved adapter files have passed structural and checksum validation. A fresh inference reload of those adapters has **not** been run; `scripts/check_adapter_reload.py` provides that GPU smoke check. No new training is claimed by this packaging commit.

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
