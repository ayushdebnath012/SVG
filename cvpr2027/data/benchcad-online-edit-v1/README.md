# BenchCAD published edit pairs: local training and benchmark split

Source: [BenchCAD/BenchCAD](https://huggingface.co/datasets/BenchCAD/BenchCAD),
`edit-bench` configuration, original `edit_bench` split, revision
`5919f578ab09ec283603a082fab07c7639ab56eb`. Zhang et al. 2026; CC-BY-4.0.
Original release: 748 pairs. Excluding pipe/circuit families leaves 710 pairs.

Whole family / numeric-masked source-and-target template components are split
533 train, 50 validation, 127 test before fine-tuning. After the predeclared
3072-token full-chat / 512-token target limits: 492 / 44 / 126.
The author supplies held-out evaluation data; this is an explicit local
repartition for training and benchmarking, not an official leaderboard result.

The model receives original published instructions and source CadQuery code,
without gold line-number hints. Targets are original-coordinate multi-line patches.
Training starts from base weights and does not reuse the earlier localized adapter.

Local one-pass MLX QLoRA completed. Saved adapter, full 126-case predictions and
executed STEP comparisons: `../../runs/benchcad-online-mlx-20261002/`.
77 applicable patches, 12 exact target ASTs; 39 valid predicted solids;
18 broad IoU matches, 12 strict matches. One upstream STEP is invalid, giving
125 valid geometric references. No FEM or certified instruction-compliance claim.
`reference-quality-notes.json` records one contradictory published slot instruction.
`normalization-audit.json` records four docstring-whitespace changes while checking
that all 1496 source/target executable ASTs are preserved.

Use `scripts/benchcad_online_edit_dataset.py` to rebuild from the pinned parquet,
`train_benchcad_online_mlx.py` for local QLoRA, and `score_benchcad_online.py`
with the CAD runtime for reference STEP scoring. Native references remain
unmodified under `reference-step/`. All split hashes are in `manifest.json`.
