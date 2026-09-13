# Controlled editing pilot v1

This generated dataset tests a restricted JSON action policy for solver-linked SVGs. It is intended for implementation validation. It is not a representative benchmark of engineering drafting, scientific reasoning, or visual understanding.

## Construction and splits

`scripts/controlled_editing_data.py` uses random seed 2027. Rectangular heat fields use a finite-difference solve with fixed hot/cold vertical boundaries and insulated horizontal boundaries; every generated solve is checked against the corresponding analytic linear field. Annular cases use the analytic radial Laplace solution. Each drawing contains three contours and bound labels.

| Split | Physical cases | Actions |
|---|---:|---:|
| Train | 60 | 360 |
| Validation | 10 | 60 |
| Test | 10 | 60 |
| Annulus family holdout (`ood`) | 10 | 60 |

All six examples from each physical case stay in one split. The model receives an instruction and compact DOM index; full SVGs and solution records are retained for executor evaluation. The model does not receive a raster image or complete contour geometry. Templates and the action schema are shared across splits, including the annulus holdout. Consequently, `ood` means a limited field-family holdout, not broad out-of-distribution generalization.

## Targets and metrics

The six actions are contour recoloring, bounded visible stroke width, label movement within an annotation panel, routing a changed boundary condition for recomputation, rejecting false numerical relabeling, and rejecting removal of a required contour. Targets come from the generator. A recompute response requests a solve; this pilot does not execute the replacement solve.

Strict exact-action accuracy compares the complete JSON object with the target. A separate sensitivity metric strips only one enclosing Markdown JSON fence. Executor acceptance measures whether the action conforms to the schema; it does not establish instruction fulfillment. Unsafe-edit counts concern a narrow semantic misuse condition and are not a general safety guarantee.

Each evaluation split has ten physical cases, not sixty independent cases. Training seeds do not add new test cases. Use case-level uncertainty for future comparisons. A deterministic instruction parser scores perfectly on both evaluation splits, showing that the shared templates make this task too easy to establish a benefit from learning.

## Provenance and access

The JSONL files contain generated problems, SVGs, instructions and targets. No personal data or model-gateway credentials are needed. Split hashes are in `controlled-editing/manifest.json`. Completed GPU runs retain their own generated data and hashes; use those exact files to reproduce their reported scores, since numerical library versions can affect serialized floating-point values.

The code and data are local research artifacts; no public release or new third-party license grant has been made. Any release must include a license decision, dependency notices and source/model attribution. The adapter base model is [Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct); consult its model card and Apache 2.0 license for redistribution.

## Known gaps

The executor supports its generated schema, preserves protected paths and label text, and limits permitted edits. It does not validate arbitrary SVG semantics, all visibility/occlusion interactions, label collisions, units and legends, or the truth of arbitrary natural-language instructions. Human-written instructions, counterfactual requests, actual solver reruns, richer geometries and multi-step edits are required for a meaningful main benchmark.
