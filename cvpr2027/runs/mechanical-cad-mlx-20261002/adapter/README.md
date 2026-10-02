# Mechanical CAD patch QLoRA pilot

Base: mlx-community/Qwen2.5-Coder-1.5B-Instruct-4bit.
MLX adapter trained for 100 iterations on 92 geometry-verified code edits from
BenchCAD (Zhang et al. 2026, CC-BY-4.0). Whole mechanical families held out.
Input: CadQuery code + explicitly localized numeric feature edit.
Output: JSON full-source-line patch. SVG views follow deterministic CAD export.

12/12 fixed held-out exact patches and matching executed solids. The base model
already matches 11/12 solids with a relaxed fragment parser; the small pilot
mainly improves formatting, not established engineering reasoning.
No drawing-perception training or FEM validation. Physical specifications absent.
See ../run_manifest.json and ../../../reports/MECHANICAL_CAD_DATA_AND_TRAINING_20261002.md.
