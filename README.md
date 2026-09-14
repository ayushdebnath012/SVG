# SVG — physics-consistent generation and editing of engineering vector drawings

Branch `cvpr2027-research-package` packages a research programme on getting
language models to produce and edit engineering SVG drawings whose numerical
content (field contours, labelled values, geometry) is actually correct and
stays correct across edits. Target venue: CVPR 2027. Nothing has been
submitted; the novelty claim is provisional and the main benchmark is
unfinished. Read the status documents before citing any number.

The repository has grown in three layers, oldest first:

| Layer | Where | Question it answers |
|---|---|---|
| **SVG Patch Lab** | `svgpatchlab/`, `configs/experiments/`, `SVGEditBench/` | Can a small LM edit SVGs more reliably by emitting constrained DOM patches instead of rewriting the file? |
| **Engineering generation harness** | `scripts/eval_generation.py`, `configs/prompts/engineering_v*.json`, `scripts/fd_reference.py`, `scripts/field_fidelity.py`, `runs/gen-astra-*` | When a frontier LM (`gpt-6-astra`) is asked to draw a physics problem, does the drawing carry the right physics? Contours are scored against finite-difference references. |
| **CVPR 2027 research package** | [`cvpr2027/`](cvpr2027/README.md) | Proposal, literature survey, working paper, repaired evaluator, corruption controls, FEM references, A100 LoRA pilot, and a registry of completed vs. planned experiments. |

## Start here

| Read this | For |
|---|---|
| [cvpr2027/README.md](cvpr2027/README.md) | The package guide: document table, what the evidence does and does not establish, and the full reproduction procedure. |
| [cvpr2027/reports/RESEARCH_STATUS.md](cvpr2027/reports/RESEARCH_STATUS.md) | Current conclusions, CVPR 2027 deadlines, completed work, and the correction to earlier proposal claims. |
| [cvpr2027/output/pdf/](cvpr2027/output/pdf/) | Review PDFs: research proposal, experiment protocol, literature survey, results and failure audit, working paper. LaTeX in `cvpr2027/docs/latex/`, Markdown sources in `cvpr2027/docs/source/` and `cvpr2027/paper/`. |
| [reports/plan/engineering_v4_task_design.md](reports/plan/engineering_v4_task_design.md) | The three-paper split (P1 where the physics stops, P2 solver in the loop, P3 mechanism) and the `engineering_v4` task design and build order. |
| [reports/literature/prior_art_and_build_plan_2026-09-12.md](reports/literature/prior_art_and_build_plan_2026-09-12.md) | Prior-art audit (MechAgents, MCP-SIM, Penrose, scientific SVG work) and what to build on. |
| [cvpr2027/papers/README.md](cvpr2027/papers/README.md) | Surveyed paper library: 20 records, 15 downloaded PDFs, BibTeX, download provenance. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Design of the SVG Patch Lab layer: node indexing, skeletons, patch schema, validation policy, executor. |

**Historical documents.** The root-level `astra_*.pdf` files and
`reports/astra_overview/`, `reports/astra_proposal/` predate the evaluator
repair. Their contour-fidelity totals and the capacitor "closed-loop" claim
are superseded; see
[reports/astra_overview/ERRATA_2026-09-13.md](reports/astra_overview/ERRATA_2026-09-13.md)
and
[cvpr2027/reports/ASTRA_FEM_FAILURE_RECHECK.md](cvpr2027/reports/ASTRA_FEM_FAILURE_RECHECK.md).
They are kept intact for provenance only.

## What the evidence currently establishes

Summarised from `cvpr2027/reports/`; details, data paths and caveats are there.

- **Drafting is reliable, physics is not uniformly so.** Over 46 `gpt-6-astra`
  prompts across three rounds, every drawing rendered and closed-form label
  checks passed 20/20 on the physics round. On the six field-contour cases
  without closed-form solutions, the repaired sampled-geometry audit gives 3/6
  strict passes at 0.5 pp of field range; the remaining cases involve
  incompatible Dirichlet corners, masked reference regions, or an empty Robin
  response, and need a stated reference-domain protocol before model error can
  be assigned.
- **The evaluator was wrong and has been repaired.** Endpoint-only contour
  checks were replaced with arc/Bezier sampling under full ancestor transforms,
  arc-length weighting, and explicit invalid-reference coverage. 160
  manufactured corruption controls show the repaired audit accepts 16.7% of
  corruptions versus 66.7% for the old-style baseline. It still accepts every
  wrong-label corruption because it does not verify text semantics.
- **Two new Robin drawings pass direct FEM comparison** (max errors 0.111 °C and
  0.374 °C against a converged scikit-fem reference). The historical Robin
  failure did not reproduce on repeat.
- **A LoRA routing pilot works but proves nothing about learning.** Three A100
  runs (Qwen2.5-Coder-1.5B-Instruct, LoRA r=16, seeds 17/29/41) score 60/60 on
  test and held-out-family splits, and so does a deterministic template-rule
  baseline. The pilot validates the pipeline; the shared instruction templates
  make it unable to show a learned advantage.
- **FEM-Bench integration anchor.** The pinned, unmodified FEM-Bench axial-bar
  solver is vendored under `cvpr2027/vendor/FEM-bench/` with two reference
  tests and 24 solves on original/edited drawings.

## Layout

```text
svgpatchlab/           SVG Patch Lab package: core (XML, skeletons, patches, policies,
                       executor), architectures, model adapters, eval (metrics, render,
                       runner, generation, field_fidelity), decompose, vision
configs/
  experiments/         Patch-lab architecture presets (full_rewrite, skeleton_patch, ...)
  models/              Model presets: Qwen3.5 0.8B/4B/9B (HF + OpenAI-compatible),
                       gpt-6-astra / astra-pro, qwen3.8-27b via gateways
  prompts/             engineering_v1 (drafting), v2_physics (closed-form labels),
                       v3_fields (Laplace/Poisson contours vs. FD reference)
  chains/, train/      Plan A/B/C chain configs; SFT/GRPO decomposer configs
scripts/               Generation harness, prompt generators, FD/FEM references,
                       contour audit, controlled-editing data/train/baseline
train/                 SFT and GRPO decomposer training entry points
tests/                 Standard-library unit tests (81 tests)
runs/                  Committed evidence: SVGEditBench matrices (qwen*), oracle checks,
                       gen-astra-v1/v2/v3 outputs and reports, reference-v3 FD solutions,
                       fem-smoke, and runs/cvpr2027/ (rescores, contour controls)
reports/               Plan, literature audit, Astra overview/proposal (historical) + errata
cvpr2027/              Self-contained research package with its own README, registry,
                       checksums, notebooks, adapters, vendored FEM-Bench and PDFs
SVGEditBench/          Official benchmark, git submodule, read-only
ARCHITECTURE.md        Patch-lab design document
```

## Setup

Python 3.10 or newer. The core patch-lab code and structural evaluation have
no third-party dependencies; optional extras are declared in `pyproject.toml`.

```bash
git clone --branch cvpr2027-research-package https://github.com/ayushdebnath012/SVG.git
cd SVG
git submodule update --init --recursive        # SVGEditBench; 9 tests error without it
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[eval,physics]"   # CairoSVG, numpy, scipy, svgpathtools
.venv/bin/python -m pip install -e ".[fem]"            # scikit-fem, triangle (for fem_smoke.py)
.venv/bin/python -m unittest discover -s tests -v
```

API keys for hosted models are read from `.env` (never committed):

```bash
cp .env.example .env    # fill in OPENAI_API_KEY and/or EXPLABS_API_KEY
set -a; . ./.env; set +a
```

## Running things

**Reproduce the CVPR 2027 CPU diagnostics** (tests, rescoring, contour
controls, saved-training verification, FEM extension) through the registry
runner. Each job writes into a fresh timestamped directory under
`cvpr2027/tmp/reproduction/`:

```bash
cd cvpr2027
python3 -m venv .venv && .venv/bin/python -m pip install -r requirements-local.txt
.venv/bin/python scripts/experiments.py list
.venv/bin/python scripts/experiments.py run C01     # regression tests
.venv/bin/python scripts/experiments.py run C05     # verify saved adapters, recompute scores
.venv/bin/python scripts/experiments.py run C10     # vendored FEM-Bench extension
```

Planned jobs `P01`–`P08` are registered but not implemented; running one exits
with an explanation. GPU training and API repeats are documented in
[cvpr2027/README.md](cvpr2027/README.md).

**Engineering generation harness** (billable; hits the configured endpoint):

```bash
.venv/bin/python scripts/eval_generation.py \
    --model-config configs/models/openai-gpt-6-astra.json \
    --prompts configs/prompts/engineering_v3_fields.json \
    --limit 3 --output-dir runs/gen-astra-smoke
# then open runs/gen-astra-smoke/index.html (failures listed first)
```

Rebuild references and rescore without calling any model:

```bash
.venv/bin/python scripts/fd_reference.py          # runs/reference-v3/<id>.npz + isolines
.venv/bin/python scripts/field_fidelity.py --run-dir runs/gen-astra-v3-fields   # rescore contours vs. reference
.venv/bin/python scripts/fem_smoke.py             # runs/fem-smoke/ (L-plate, Kirsch hole)
.venv/bin/python scripts/benchmark_contour_audit.py   # manufactured corruption controls
```

**SVG Patch Lab on SVGEditBench.** Oracle check (should score perfectly), then
any architecture against any model preset:

```bash
.venv/bin/python -m svgpatchlab.cli evaluate --config configs/experiments/oracle.json
.venv/bin/python -m svgpatchlab.cli evaluate \
    --config configs/experiments/skeleton_patch.json \
    --model-config configs/models/qwen3.5-4b-openai.json --limit 10
.venv/bin/python -m svgpatchlab.cli matrix \
    --model-config configs/models/qwen3.5-4b-openai.json \
    --limit-per-task 2 --output-root runs/my-smoke
```

Use `--no-render` for structural-only checks when Cairo is not installed.
Invalid outputs are kept as failures and receive failure-aware MSE 1 rather
than being dropped from averages.

## Evaluation rules that apply across the repository

- Raw model outputs are never overwritten. Rescoring writes new result files
  next to the old ones; historical evidence stays in place with its errata.
- Empty or invalid responses stay in denominators.
- Splits are by case and geometry family, never by variant of the same
  drawing. The committed 100 SVGEditBench emoji IDs are for final testing only.
- A sampled geometric audit is not a rendered-drawing certificate, and
  manufactured corruption controls are not model-performance estimates. Both
  are labelled as such wherever they are reported.

## Provenance and what is not included

- `cvpr2027/RUN_INDEX.json` and `cvpr2027/SHA256SUMS.json` index and checksum
  the packaged evidence; `cvpr2027/reports/package_verification.json` records
  the packaging checks.
- Final LoRA adapters and trainer states are versioned; intermediate optimizer
  checkpoint archives, the nested `third_party/` checkout, LaTeX build
  binaries, virtual environments and temporary reproduction output are
  ignored (see `.gitignore`).
- No API credentials are included. A fresh inference reload of the saved
  adapters has not been run; `cvpr2027/scripts/check_adapter_reload.py` is the
  GPU smoke check for that.

## Related branches

- `main` — patch lab plus the initial controlled-editing tree, without the
  packaged documents and runs.
- `astra-physics-v4` — the generation-harness work before packaging.
- `agent/svg-group-candidate-v6` — separate set-grounding / group-candidate
  experiments (SVGEditBench editing), developed in a sibling clone.
