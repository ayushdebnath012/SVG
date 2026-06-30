# DiffuSVG

DiffuSVG is a text-to-SVG training pipeline. It fine-tunes an SVG generator with
filtered SVGX data, improves it with preference training, then applies
render-aware GRPO rewards against diffusion-generated reference images.

This checkout also includes `svgpatchlab/`, merged from
`DebdanSamanta02/EditSVG`. SVG Patch Lab evaluates localized SVG editing through
constrained DOM patches, SVGEditBench cases, model adapters, and committed run
summaries. See `README_SVGPATCHLAB.md` for that workflow.

## Current pipeline

1. `IntroSVG/data/d_sft_svgx.jsonl` provides 3,000 gradient- and detail-filtered
   SVGX-SFT examples.
2. `IntroSVG/` runs SFT and DPO training for direct SVG generation.
3. `DiffusionSVG/` generates reference PNGs, vectorizes them, builds the GRPO
   dataset, and trains with rendering feedback.

The canonical end-to-end entry point is:

```bash
bash full_run.sh prompts.txt
```

It targets one A100 80 GB GPU, is resumable, and writes checkpoints and generated
data into ignored directories. Install the dependencies listed in
`IntroSVG/requirements_training.txt` and `DiffusionSVG/requirements.txt` first.

For a reduced validation run, use `smoke_run.sh`. The large
`kaggle_patchsvg_t4_smoke.py` runner is the self-contained Colab/Kaggle path for
a T4 GPU.

## Repository layout

- `IntroSVG/`: SFT, DPO, inference, and SVG utilities.
- `DiffusionSVG/`: diffusion references, vectorization, rewards, and GRPO.
- `Hybrid/`: experimental combined pipeline.
- `OmniSVG/` and `Text2SVG/`: comparison and baseline implementations.
- `svgpatchlab/`, `configs/`, `tests/`, and `runs/`: SVG Patch Lab package,
  experiment presets, regression tests, and imported evaluation artifacts.
- `SVGEditBench/`: benchmark submodule used by SVG Patch Lab.
- `dataset_samples/` and `svgx_samples/`: small, reviewable SVG examples.
- `DiffuSVG_Project_Report.md`: methodology and evaluation notes.

Root-level versioned `DiffuSVG_Pipeline_v*.py` files are retained as historical
experiments; new work should use `full_run.sh` and the two maintained pipeline
directories above.
