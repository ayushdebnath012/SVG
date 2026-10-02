# Functional structural drawing synthesis pilot

Created 21–22 September 2026. This is a separate track from detached SVG editing.
The model receives an explicit frame specification and chooses catalog sections;
a deterministic exporter produces the corresponding SVG elevation and section
schedule. This tests section-design search, not free-form SVG coding or visual
interpretation. Original API responses and exported trial drawings are retained.

Verification includes linear frame FEM (three load cases, end-fibre stress and
all-node displacement), a separate member Euler buckling inequality, mass, and
readback of actual SVG line widths and section rectangles. These are idealized
research models, not checks of construction-code compliance or whole-building
safety. Buckling uses the stipulated K=1 member criterion, not global stability.

Each task has an exhaustively enumerated feasible reference. The mass cap is
101% of minimum feasible mass. Every satisfying design passes; matching the
reference assignment is not required. The oracle object is excluded from API
inputs. Four analysis calls permit at most 256 candidate evaluations each;
Astra uses high reasoning and at most 16,000 output tokens per API turn. This
budget is part of the result, not an intrinsic capability limit.

The four initial variants share one source-frame ancestry. The braced and
three-bay extensions were created after earlier passes and stored in separate
frozen manifests under `../cad-functional-braced` and
`../cad-functional-three-bay`. Report the adaptive selection process. These
variants do not provide three independent engineering domains or families.

Preflight calibration: the initial unbraced catalog had no feasible design and
was rejected before API testing. The first braced draft admitted the all-small
assignment and was revised before completion/freeze/API testing. Neither draft
is an Astra failure. Frozen tasks were not changed after API observations.

A candidate requires three independent completed functional failures and a
reference/interface audit for repeatable failure admission. API errors,
truncation and valid alternative solutions are excluded. A failure here must
be labeled resource-bounded functional design failure, not an Astra-incapable
shape class. Do not mix this gate with the original geometry-edit hard set.

Reproduction (from workspace root):

```
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m unittest discover -s cvpr2027/tests -p 'test_cad_functional_sizing.py'
OPENBLAS_NUM_THREADS=1 .venv/bin/python cvpr2027/scripts/cad_sizing_baselines.py --output /tmp/cad-sizing-baselines.json
```

An API run requires configured OpenAI access and a NEW output directory:

```
OPENBLAS_NUM_THREADS=1 .venv/bin/python cvpr2027/scripts/cad_functional_sizing.py run --data cvpr2027/data/cad-functional-three-bay --output /tmp/cad-three-bay-new-trial --sample 4
```

The cross-entropy control uses the same four batches and 1,024 evaluations.
Pair-coordinate descent has the same evaluation ceiling but adaptive rounds
are not matched to the four-call restriction. Neither receives the oracle.
The exhaustive reference has a larger budget and must not be presented as a
budget-matched competitor. These are classical baselines, not new methods.

Rendering correction: early exporter output could put the tallest frame across
the header. `presentation.svg` derivatives fix margins and text contrast,
without changing selected sections or original trial artifacts. Version-aware
readback verifies both renderings. Drawings are schematic elevations with a
separately scaled section schedule; a fabrication detail sheet is not produced.

No training uses these discovery/evaluation cases. See the linked research
report for actual trial results and limitations.
