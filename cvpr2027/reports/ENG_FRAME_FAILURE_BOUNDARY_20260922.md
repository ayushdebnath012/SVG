# Where Astra actually fails on engineering drawings — 22 September 2026

**Result: on dimensioned structural elevations checked with frame FEM, Astra declines to produce the
required engineering quantities on 4 of 7 samples once the frame reaches 20 members, against 1 of 35
below that (Fisher exact p = 0.0015). It does not print wrong numbers: across 42 completed samples
exactly one quantity was outside tolerance, and that one did not reproduce. The failure mode is
refusal, not fabrication.** Credits were exhausted mid-study; one confirmation is outstanding.

## What was asked and why the direction changed

The task was to find Astra failure cases on engineering drawings — buildings, tables, CAD-style SVGs
that are generated or edited and then checked with FEM — and turn them into a benchmark. An earlier
pass in this session built a benchmark on Laplace isotherm drawings; that was the wrong target, since
a field-contour plot is not an engineering drawing. It was stopped after $1.18 and is kept separately.

## The two recorded leads, and what they were worth

| Lead | Recorded result | On re-test |
|---|---|---|
| `building_edit`, 20 Sep pilot | peak stress **179 MPa** against a reference of **20.356 MPa** | **3 of 3 fresh samples correct** (20.4 MPa) |
| `threebay_edit`, this session's screen | analysis declined | **3 of 3 fresh samples correct** |

The 179 MPa case was the most diagnostic artefact in the repository: the drawing and dimensions were
correct, the model named the correct governing member end (`col_EH, end E`, genuinely the maximum at
20.356 MPa), stated the correct extreme-fibre formula, and got both displacements right to 0.3 % —
then printed a number 8.8 times too large. It is a real defect and it is **not reproducible**. Under
the pilot's own admission rule it does not qualify as an Astra-hard case, and it should not be cited
as one.

The general lesson is that single-sample screening manufactures failures that evaporate. Three of the
first four anomalies found in this session disappeared on repetition.

## A scorer defect that was nearly reported as a model failure

Three screen results were filed as `unscored_format` for "missing mm unit" on every dimension label.
Inspection of the drawings shows they each declare units once, for example *"Structural elevation ·
dimensions in mm · member centrelines"* and *"Rigid-jointed 2D frame · undeformed member centrelines ·
dimensions in mm"*. Stating units once in the notes is standard ISO/ASME drafting practice; the
harness required the literal string `mm` inside every `data-dimension` text and so rejected correct
drafting. [`eng_frame_bench.adjudicate`](../scripts/eng_frame_bench.py) withdraws that complaint only
when the drawing declares its units and nothing else fails; it can never turn a failure into a pass
for any other reason. One of those three, `twobay_four_generate`, turned out to have declined its
analysis as well — the unit complaint was masking the real defect.

## The benchmark

[`eng_frame_bench.py`](../scripts/eng_frame_bench.py) generates dimensioned structural elevations of
planar building frames procedurally and orders them by **degree of static indeterminacy**, 3m + r − 3j.
That axis is not invented for the occasion: the pilot's three hand-made families fall on it exactly, and
their outcomes followed it — shelf (cantilever chain, degree 0) pass, table (portal, degree 3) pass,
building (two-storey setback, degree 9) the sole failure. A determinate frame yields to statics alone;
an indeterminate one requires the simultaneous stiffness system.

Instances are concentrated in the hard region on purpose, because there is no value in re-measuring
what the model already does: 14 of the 18 main instances sit at degree 9 or above, with an extension set
at 24 and 27. Manifests are written in `cad_astra_benchmark`'s own format, so its proven runner and
scorer are reused unchanged — member centrelines, joint gaps, dimensions, ux/uy/peak stress against FEM
at 2 %, and agreement between the JSON analysis and the visible SVG text. Every reference is admitted
only after a member-subdivision invariance check (1e-7) and a global equilibrium check, and eight
verification checks pass, including that the harness scores a drawing built from the reference itself
as a pass. [Main set](../data/eng-frame-bench/tasks.json), [extension set](../data/eng-frame-bench-xl/tasks.json).

## Results

42 completed samples, [aggregated here](../runs/eng-frame-aggregate.json) by
[`eng_frame_report.py`](../scripts/eng_frame_report.py), which separates *declining* from *computing a
wrong number* because the harness files both under `format_errors` and the admission rule then discards
the more interesting one.

| Members | Samples | Correct | Wrong | Declined | Decline rate |
|---:|---:|---:|---:|---:|---:|
| 3–13 | 25 | 25 | 0 | 0 | 0 % |
| 14 | 8 | 7 | 0 | 1 | 12 % |
| 18 | 2 | 2 | 0 | 0 | 0 % |
| 20 | 2 | 1 | 0 | 1 | 50 % |
| 21 | 5 | 2 | 0 | 3 | 60 % |

Below 20 members, 1 of 35 samples declined. At 20 members and above, 4 of 7 declined — 57 %, 95 %
Wilson interval 25–84 %, Fisher exact two-sided **p = 0.0015**.

When the model does answer it is accurate at every size tested, up to 21 members and indeterminacy 27:
`threebay_three_edit` returned peak 17.7 MPa against a reference of 17.6837, and ux 3.5 against 3.5119.
Accuracy does not decay with complexity. Willingness does.

The declines are explicit and honest. The model sets the contractually permitted
`status: "unavailable"`, returns nulls, and states why — *"the edited frame stiffness solution and
member-end force recovery have not been performed"*. It stops rather than fabricating, which is the
opposite of the 179 MPa outlier and is the behaviour a drawing pipeline should want.

## Limits

Seven samples above the boundary is a small sample; the 25–84 % interval is wide and the exact
threshold is not resolved — 18 members passed twice, 20 and 21 declined 4 of 7 times, so "about 20"
is the honest statement. The `twobay_four_generate` confirmation was cut off by credit exhaustion and
three of its samples are recorded as `excluded_api`; the runner will not re-bill them, so a fresh
output directory is needed to complete it. All runs used `gpt-6-astra` at medium reasoning effort; the
32,000-token cap was not the constraint, since declines finished cleanly at 6,600–8,100 completion
tokens. Whether a larger budget, higher effort, or solver access removes the decline is untested and is
the obvious next experiment — the decline is precisely the condition a solver-in-the-loop design would
be expected to fix, and it now has a measurable baseline to fix.

This measures one task family — planar rigid-jointed frame elevations under linear elastic,
small-displacement assumptions with nodal loads. It is not a statement about 3D CAD, about drafting
quality beyond the checked annotations, or about what the model could do with tools.

## Spend

This session used 115,455 input and 375,052 completion tokens, about **$19.91** at list prices; this is
token-price arithmetic, not an invoice. $1.18 of it went to the abandoned isotherm direction and $0.87
to a void run whose prompts omitted the `data-level` contract, kept at
`runs/VOID-polyheat-zeroshot-20260922-missing-status-line/`. The account reported
`credit_balance_exhausted` during the final confirmation.

## Reproduction

```sh
cd cvpr2027
PYTHONPATH=src ../.venv/bin/python scripts/eng_frame_bench.py build                    # main set
PYTHONPATH=src ../.venv/bin/python scripts/eng_frame_bench.py build --set xl --data data/eng-frame-bench-xl
PYTHONPATH=src ../.venv/bin/python scripts/eng_frame_bench.py verify
PYTHONPATH=src ../.venv/bin/python scripts/cad_astra_benchmark.py run   --data data/eng-frame-bench --output runs/<fresh> --samples 3   # billable
PYTHONPATH=src ../.venv/bin/python scripts/cad_astra_benchmark.py score --data data/eng-frame-bench --output runs/<fresh>
PYTHONPATH=src ../.venv/bin/python scripts/eng_frame_bench.py adjudicate --output runs/<fresh>
PYTHONPATH=src ../.venv/bin/python scripts/eng_frame_report.py
```
