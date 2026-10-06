# CVPR positioning and evidence

The revised paper is titled **ReSolve: Instruction-Guided 3D CAD Editing with Geometry and View Evaluation**. Its focus is structured 3D shape editing and evaluation. This connects to the [official CVPR 2027 topics](https://cvpr.thecvf.com/Conferences/2027/CallForPapers), including 3D geometry, vision and graphics, and datasets/evaluation. Topic fit alone does not establish novelty or submission readiness.

## Completed changes

- Rewrote the title, abstract, introduction, related work, methods, dataset protocol, experiments and conclusion around instruction-guided executable shape editing.
- Promoted the completed Qwen2.5-Coder-3B Colab T4 experiment to the primary result: 2,540 train / 172 validation / 252 test tasks from two public sources, strict target agreement 1/252 fresh base and 39/252 final adapter. Kept native representations and reference construction distinct.
- Separated applicability (173), execution (139) and strict agreement (39), with the full held-out denominator and unavailable comparisons retained.
- Added a reproducible post-hoc common-camera silhouette and source-relative change-mask audit on the fixed six previously illustrated tasks. Six earlier H100 outputs and four completed final 3B outputs are available. These unequal subsets and different training protocols are not a fair model comparison or benchmark-wide visual accuracy.
- Added a feature-localization figure from saved flange solids. The older prediction has top silhouette IoU 0.908 and change-mask IoU 0.516; the final 3B output is approximately 1.000 for each. The request changes four mounting holes to six, preserving diameter and bolt-circle radius.
- Documented a one-pixel isometric reference change that makes projected edit averages misleading even for an essentially exact output. Raw view counts and two raster resolutions are retained; no post-hoc area filter hides this limitation.
- Kept scenario-defined FEM checks for mechanical examples, explicitly post-edit and separate from training. Four final 3B prediction/target pairs complete combined checks; two attempts remain unverified.
- Moved older single-source data/training results and deterministic truss/clearance controls to the supplement, preserving their factual contracts and figures.

## Reproduction

- Visual audit: `tmp/cad-runtime/bin/python scripts/evaluate_cad_multiview_edits.py`.
- Raw visual record: `runs/cad-multiview-audit-20261003/results.json` includes per-view metrics, reference-change pixel counts, STEP hashes and rendering contract.
- Paper build: `cd paper/network && /Users/ayushdebnath/.local/bin/tectonic main.tex --keep-logs`.
- Existing Colab model artifacts: `runs/multisource-cad-colab-20261002/results-final`.
- No additional model training was performed for this framing revision; it uses the completed training and saved unmodified predictions.

## Remaining research requirements

A stronger submission requires matched CAD-editing method baselines on the same splits/backends, repeat training seeds, and full-test feature/view evaluation with a preregistered visibility contract. A learned visual input or drawing-conditioned branch would require actual implementation, training and evaluation; the current model reads CAD programs and text only. Supervised QLoRA, program patches, CAD projections and FEM are not presented as new algorithms. Physical conclusions require independent real analysis contracts and broader numerical validation, rather than diagnostic synthetic loads. No official BenchCAD score, manufacturing safety or acceptance claim is made.
