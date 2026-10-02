# Astra CAD drawing pilot — 20 September 2026

**No shape has qualified for the failure-only benchmark yet.** The eight-task
screen produced seven complete passes and one physical-analysis error. All eight
passed the implemented drawing geometry checks. Two high-effort confirmations of
the analysis error exhausted their token budgets and are excluded, so the one
candidate is not a confirmed repeatable failure. Empty selected manifests are
intentional, not evidence of a completed hard benchmark.

| Pool | Configuration | Outcome |
|---|---|---|
| Table, setback building and cranked shelf; generation + editing | Six tasks, Astra medium, 16,000-token cap | Five passes; building edit has one stress error |
| Filleted L mounting plate with holes and rotated slot; generation + editing | Two tasks, Astra medium, 16,000-token cap | Two passes |
| Building edit confirmation | Two independent samples, Astra high, 24,000-token cap | Both truncated; excluded |

The building-edit screen reports **179 MPa** peak stress in both JSON and its
visible drawing, versus **20.356447 MPa** from the specified linear frame model.
Its edited geometry and displacements pass. This is an analysis error, not an
inability to draw a building shape. All conclusions concern these exact prompts,
idealised models, unaided model and budgets; they do not establish general CAD
competence or engineering safety.

## Verification beyond FEM

The frame tasks use geometric connectivity and dimension checks, global force
and moment equilibrium, linear frame FEM, subdivision invariance, and independent
statics plus virtual-work integration for the shelf. The solid-plate tasks use
constructive line/arc geometry, boundary comparison, analytic area and mass, and
sampled minimum material clearance. No FEM is needed for the plate's stated
questions. Sixteen automated tests pass, including independent closed-form and
quadrature checks and deliberately corrupted drawings.

Rendered outputs were visually reviewed by **the assistant**, not a human
engineer. The drawings contain legible dimensions and appropriate visible object
geometry. The formal building-error review records its limited conclusion and
both excluded confirmations. The separate selection-policy clarification is
preserved alongside the frozen prompt manifest; no numerical threshold was
changed after inspecting outputs.

## Evidence

- [Frame protocol and tasks](../data/cad-astra-pilot/README.md)
- [Solid-plate task manifest](../data/cad-plate-pilot/tasks.json)
- [Frame screening results](../runs/astra-cad-20260920/screen/summary.json)
- [Plate screening results](../runs/astra-cad-20260920/plate-screen/summary.json)
- [Confirmation results](../runs/astra-cad-20260920/confirm-building-edit/summary.json)
- [Selection and candidate evidence](../runs/astra-cad-20260920/selection.json)
- [Selected drawing tasks: currently empty](../runs/astra-cad-20260920/selected_drawing_tasks.json)
- [Frame gallery](../runs/astra-cad-20260920/screen_gallery.png)
- [Plate gallery](../runs/astra-cad-20260920/plate_gallery.png)

Ten API samples consumed **120,178 tokens**: 18,835 input and 101,343 completion
(including reasoning). Dollar cost is not estimated here. Requests, model IDs,
responses, usage, finish reasons and rendered SVGs are saved with each sample.

The next discovery pool should come from the released CAD/SVG and constraint
sources in the [web literature audit](CAD_WEB_LITERATURE_AND_DATASETS_20260920.md),
with parent-design isolation, verified conversions and executable edits. Increase
actual drawing complexity (multiple views, interacting fillets, assemblies and
constraint propagation); do not relabel calculation errors or token exhaustion
as shape failures. Retain only repeated drawing failures after visual review.
