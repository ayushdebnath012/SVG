# SVG Patch Lab

SVG Patch Lab tests whether a small language model can edit SVGs more reliably
by emitting constrained DOM patches instead of regenerating complete files. The
official `SVGEditBench/` clone is treated as read-only evaluation data.

## What is implemented

- Loader for all 600 SVGEditBench prompt/answer pairs.
- Deterministic preorder node IDs (`n0`, `n1`, ...).
- Compact DOM skeletons that replace `d` and `points` values with hashes and
  character counts.
- Versioned JSON patch schema, task-specific allowlists, and protected geometry.
- Deterministic patch executor.
- Gold-patch derivation from SVGEditBench references.
- Full-rewrite, full-context patch, skeleton patch, visual skeleton, two-stage,
  oracle-target, rule-based, and deterministic oracle architectures.
- Interchangeable local Transformers, OpenAI-compatible server, and replay
  model adapters.
- Structural, locality, patch precision/recall, and SVGEditBench-compatible MSE
  evaluation.

Compression is kept in the full-rewrite and oracle evaluations. It is excluded
from localized patch presets because compression is an inherently global edit.

## Layout

```text
svgpatchlab/
  architectures/  Experiment strategies and prompts
  core/           SVG parsing, skeletons, patches, policies, executor
  data/           SVGEditBench adapter
  eval/           Rendering, metrics, experiment runner
  models/         Swappable model adapters
configs/
  experiments/    Architecture presets
  models/         Model/runtime presets
docs/              Rendered architecture document
tests/             Standard-library regression tests
SVGEditBench/      Unmodified official benchmark clone
```

## Setup

If you cloned this repository normally, fetch the benchmark submodule first:

```bash
git submodule update --init --recursive
```

Core and structural evaluation have no third-party dependencies:

```bash
python3 -m svgpatchlab.cli inspect SVGEditBench
python3 -m unittest discover -s tests -v
```

Install raster evaluation support for CairoSVG MSE:

```bash
python3 -m pip install -r requirements-eval.txt
```

For in-process Hugging Face inference:

```bash
python3 -m pip install -r requirements-hf.txt
```

## Run Plan A/B/C on Kaggle

The Kaggle preset uses local Hugging Face inference with 4-bit loading for
`Qwen/Qwen3.5-4B`:

```bash
git pull
python3 -m pip install -r requirements-hf.txt
python3 scripts/run_kaggle_plans.py --no-render
```

Outputs are written under `runs/kaggle-plans/`:

```text
runs/kaggle-plans/plans-summary.json
runs/kaggle-plans/plan_a_visual_node_understanding/
runs/kaggle-plans/plan_b_basic_tasks/
runs/kaggle-plans/plan_c_chain/
```

Use `--limit-per-task 5` for the same smoke size as the Kaggle run log. Set
`HF_TOKEN` in Kaggle secrets for better Hub download limits.

## Validate the entire benchmark pipeline

The oracle derives the minimal attribute patch from each reference and should
score perfectly:

```bash
python3 -m svgpatchlab.cli evaluate --config configs/experiments/oracle.json
```

Use `--no-render` for structural-only development checks when CairoSVG is not
installed.

Results are written as per-case JSONL plus a summary under `runs/oracle/`.
Invalid model outputs are retained as failures and receive failure-aware MSE 1,
rather than being omitted from averages.

## Run Qwen3.5-4B through an OpenAI-compatible server

Start Qwen using vLLM, SGLang, llama.cpp, or another compatible server at
`http://localhost:8000/v1`, then run:

```bash
python3 -m svgpatchlab.cli evaluate \
  --config configs/experiments/skeleton_patch.json \
  --limit 10
```

Run all principal comparisons by changing only the experiment config:

```bash
configs/experiments/full_rewrite.json
configs/experiments/rule_based.json
configs/experiments/full_context_patch.json
configs/experiments/skeleton_patch.json
configs/experiments/two_stage_patch.json
configs/experiments/visual_skeleton_patch.json
configs/experiments/oracle_target_patch.json
```

## Switch models

Model configuration is isolated from architecture configuration. Override it at
the command line:

```bash
python3 -m svgpatchlab.cli evaluate \
  --config configs/experiments/skeleton_patch.json \
  --model-config configs/models/qwen3.5-4b-huggingface.json
```

To add another model, either create a JSON preset using an existing adapter or
implement one class conforming to `svgpatchlab.models.base.ModelAdapter`, then
register it in `svgpatchlab/models/factory.py`. No architecture, SVG, or metric
code needs to change.

Useful CLI overrides:

```bash
python3 -m svgpatchlab.cli evaluate \
  --config configs/experiments/skeleton_patch.json \
  --architecture full_context_patch \
  --model-config configs/models/my-model.json \
  --limit 25 \
  --output-dir runs/my-model-full-context
```

Run the complete architecture matrix against one model endpoint:

```bash
python3 -m svgpatchlab.cli matrix \
  --model-config configs/models/qwen3.5-4b-openai.json \
  --limit-per-task 2 \
  --output-root runs/qwen3.5-4b-smoke
```

Remove `--limit-per-task` for the complete five-task localized-edit evaluation.
The matrix deliberately uses the same cases for every architecture so results
are paired.

## Evaluation protocol

Use the committed 100 SVGEditBench emoji IDs only for final testing. If SFT or
LoRA is added, generate training and validation examples from other Twemoji
files and split by emoji identity. Do not place different tasks for the same SVG
across train and test.

Primary reported metrics should include:

- valid and executable output rate;
- gold-patch exactness and patch precision/recall;
- protected-geometry preservation;
- number of changed nodes;
- per-task MSE and failure-aware MSE;
- latency, model calls, and token usage where available.
