# CVPR 2027 — SVG Patch Lab

This is the dedicated research folder requested on 13 September 2026. The project studies numerical fidelity of engineering SVGs through edits. It is a work in progress, not a completed CVPR submission.

- [Research status and deadlines](reports/RESEARCH_STATUS.md)
- [FEM literature survey and implemented upstream extension](reports/FEM_LITERATURE_AND_EXTENSION.md)
- [Fresh Astra API and FEM failure recheck](reports/ASTRA_FEM_FAILURE_RECHECK.md)
- [Verified A100 training results and saved adapters](reports/TRAINING_RESULTS.md)
- [Prior-art review](reports/PRIOR_ART.md)
- [Working manuscript](paper/manuscript.md)
- [Self-contained Colab notebook](notebooks/CVPR2027_controlled_editing.ipynb)
- [Live Colab experiment](https://colab.research.google.com/drive/1sLxx7qfxd06BDl8FPmpevlJnlKOawVjy)
- `scripts/`: dataset generator, training and evaluation scripts
- `src/`: snapshot of supporting SVG Patch Lab modules
- `data/controlled-editing/`: case-disjoint pilot splits and hashes
- `runs/`: completed A100 adapters/checkpoints, Astra API responses, FEM references and controls
- `third_party/FEM-bench/`: pinned MIT-licensed upstream solver and benchmark code
- `tests/`: solver, executor and contour-audit regression tests

## Local verification

From this folder, with the project's existing Python environment:

```sh
PYTHONPATH=src ../.venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src ../.venv/bin/python scripts/benchmark_contour_audit.py --output runs/contour-controls
../.venv/bin/python scripts/eval_controlled_rule_baseline.py --data data/controlled-editing --output runs/rule-baseline
```

For a new environment install `requirements-local.txt`. Training needs CUDA-enabled PyTorch and `requirements-colab.txt`; use the notebook with an A100 GPU. Base and final-model generations, optimizer checkpoints, adapter weights, package versions and hashes are retained by each completed run. Downloaded artifacts are saved here before ending the runtime.

## Interpretation

The synthetic pilot uses shared instruction templates and a compact DOM index. A simple rule parser already gets 100% on its 60 test and 60 held-out-family examples. Neural scores on this task are pipeline validation, not evidence of a new visual reasoning capability. The numeric contour checker does not verify arbitrary rendered labels, units, legends or occlusion.

The older proposal PDFs elsewhere in SVG precede the evaluator correction. Use the current research status for the corrected historical audit and remaining requirements. No paper has been submitted or publicly released.

The fresh Astra recheck does not reproduce the old Robin failure: both new contour drawings pass direct FEM sampling. The historical capacitor closed-loop claim was incorrect, and the bracket labels its stress field as illustrative. Read the recheck before using older failure claims.

The first implemented FEM-Bench extension imports the author's unchanged axial-bar solver, runs its reference tests, and generates original/edited SVGs from 24 actual FEM solves. It is a simple integration anchor, not the main CVPR experiment.

```sh
../.venv/bin/python scripts/fem_bench_svg_extension.py --output runs/fem-bench-svg-anchor
PYTHONPATH=src ../.venv/bin/python scripts/score_astra_robin_fem.py --runs runs/astra-api-recheck-20260913 --reference runs/robin-fem-reference
../.venv/bin/python scripts/summarize_training.py --runs runs/a100 --output reports/training_verified.json
```

Historical SVG inputs in `runs/historical-v3/results.jsonl` are a projection of the original run retaining only fields needed for re-scoring. Per-SVG hashes remain reproducible; the original whole-file hash in the archived summary refers to the parent project source. References and prompt levels are included.

```sh
PYTHONPATH=src ../.venv/bin/python scripts/field_fidelity.py --run-dir runs/historical-v3 --output-dir runs/rescore-reproduction
```
