# Astra-conditioned CAD drawing pilot

This pilot screens **dimensioned drawings of physical objects**, then retains
only repeatable, reviewed failures in `selected_tasks.json`. The initial pool
contains generation and physical-edit tasks for a worktable front frame, a
setback building frame elevation, and a cranked wall shelf (six tasks).
It is a deliberately small 2D structural-elevation pilot, not a finished
benchmark for general solid CAD, complete furniture or complete buildings.

## Checks and techniques

- Geometric constraints: actual SVG member centreline coordinates, straightness,
  shared-joint connectivity and required member inventory.
- Dimension consistency: visible member-length labels against physical geometry.
- Classical mechanics: equilibrium of forces and moments; closed-form axial,
  cantilever and simply supported beam tests.
- Independent analytical solution for the cranked shelf: statics plus a
  unit-load/virtual-work energy integral for displacement and section stress.
- Linear frame FEM for coupled axial and bending response. Member subdivision
  checks response invariance; it does not justify a continuum or 3D safety claim.
- Edit consistency: updated geometry, dimensions and numerical claims; the
  actual extracted drawing is also re-analysed when connectivity permits.
- Visible result consistency: numeric SVG labels against the response's analysis.
- Visual review of rendered outputs before selection. Automated checks alone
  do not verify support/load symbols, section notes, occlusion or drawing quality.

The shelf uses a second method that does not assemble an FEM stiffness matrix.
Other techniques should be added when their tasks require them: collision and
clearance checks for assemblies, constraint solving for multiview drawings,
rigid-body stability checks for freestanding furniture, and appropriate
buckling/dynamic/thermal checks for relevant designs. These are **not implemented
or measured** in this first pilot.

## Fixed screening and selection protocol

1. Freeze `tasks.json`, prompt, reference, tolerances and model configuration
   before requests. Do not send target FEM results to the generation baseline.
   Edit tasks receive a correct *original* SVG and original model; their target
   results are withheld. Original values make stale-result errors observable.
2. Screen all six cases with unaided `gpt-6-astra`, medium reasoning, 16,000
   completion tokens, one independent sample per task. No tool access.
3. Repeat substantive failing cases twice independently at high reasoning with
   a 24,000-token cap. Preserve the exact prompts; provide no evaluator feedback.
4. A task qualifies on a particular track only with at least three evaluable
   samples, at least two failures on that track, and at least one failure among
   the two high-effort confirmations. Render and review the evidence before
   admitting it. Record reviewer identity/type and rationale.
5. Keep separate **drawing** and **physical-analysis** tracks. Incorrect analysis
   is not evidence that Astra cannot draw the shape. Malformed JSON, unsupported
   SVG features, API errors, refusals and truncation are operational/format
   outcomes, not shape failures. A wrong-ID-only case requires review and must
   not be admitted as geometric inability.
6. Keep the full screened pool, passing outputs and excluded outcomes as an
   audit trail. Only the selected failure cases enter `selected_tasks.json`.
   Repeatedly passing tasks remain controls outside the failure benchmark.

Geometry tolerance is 1 mm in model coordinates; dimension tolerance is 1 mm.
Analysis tolerance is the larger of 2% relative error and 0.01 mm displacement
or 0.05 MPa stress. These are benchmark numerical tolerances, not design codes.
Both displacement and stress checks are defined only for the specified idealised
model. The shelf intentionally exceeds its example deflection limit: reporting
a correctly computed failing design is successful model behaviour.

This is **failure discovery**, not a representative estimate of Astra's CAD
ability. All samples concern fixed prompt/model/budget conditions. Before
training or reporting a generalisation result, freeze a larger procedural task
pool and split by geometry family and base design, keeping every edit variant
with its parent. Discovery examples are development data, not an untouched final
test set. Never claim a general failure rate from the filtered hard subset.

## Reproduce from the repository root

```sh
.venv/bin/python -m unittest discover -s cvpr2027/tests -p test_cad_astra_benchmark.py -v
# Existing tasks.json is frozen. To build a NEW pool:
# .venv/bin/python cvpr2027/scripts/cad_astra_benchmark.py build --data /path/to/new-pool
# Billable; reads OPENAI_API_KEY or the ignored root .env. Never logs the key.
.venv/bin/python cvpr2027/scripts/cad_astra_benchmark.py run \
  --output cvpr2027/runs/astra-cad-20260920/screen --effort medium --cap 16000
# For screening failures only; substitute comma-separated task IDs.
.venv/bin/python cvpr2027/scripts/cad_astra_benchmark.py run \
  --output cvpr2027/runs/astra-cad-20260920/confirm --ids TASK_IDS \
  --effort high --cap 24000 --samples 2
.venv/bin/python cvpr2027/scripts/cad_astra_benchmark.py select \
  --runs cvpr2027/runs/astra-cad-20260920/screen cvpr2027/runs/astra-cad-20260920/confirm \
  --review cvpr2027/runs/astra-cad-20260920/review.json \
  --output cvpr2027/runs/astra-cad-20260920/selection.json
```

Every attempted sample has a persisted request, result record and, when
returned, raw API response and extracted SVG. Reruns skip already attempted
samples, including ambiguous timeouts, to avoid accidental rebilling. A different
protocol requires a new output directory. Usage is recorded in tokens; no
unverified pricing estimate is presented.

The SVG evaluator supports straight line/path/polyline member geometry and
ancestor transforms. Unsupported rendering constructs are explicitly unscored.
Section dimensions, material, supports and loads are bound to the task model;
parsing all of those properties back from arbitrary SVG annotations is future
work. The output remains a structural centreline drawing, not a manufacture-ready
solid model. The reference SVG is a scoring fixture, not a drafting-quality oracle.

## Formulation and API references

The beam stiffness follows the cubic Hermite Euler–Bernoulli formulation in
[TU Delft's beam element notes](https://interactivetextbooks.citg.tudelft.nl/computational-modelling/structural_linear/euler_bernouilli.html).
Coordinate rotation and assembly follow the frame approach described in
[TU Delft's frame analysis notes](https://interactivetextbooks.citg.tudelft.nl/computational-modelling/structural_linear/space_frame.html);
this pilot uses Euler–Bernoulli bending, not the notes' shear-deformable element.
The independent energy calculation uses the unit-load approach described in
[Roylance's beam-displacement chapter](https://eng.libretexts.org/Bookshelves/Mechanical_Engineering/Mechanics_of_Materials_%28Roylance%29/04%3A_Bending/4.03%3A_Beam_Displacements).
API requests use the [official Chat Completions reference](https://developers.openai.com/api/reference/resources/chat).
