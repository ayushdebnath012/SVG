# PolyHeat: isotherm drawing on procedurally generated rectilinear plates

PolyHeat turns a single recorded Astra failure into a benchmark with a difficulty axis, a
certified reference and a calibrated floor.

## Where it comes from

The [18 September screen](../../reports/ASTRA_HARD_TASKS_20260918.md) gave Astra twelve
engineering-physics drawing tasks. Six of ten scored tasks passed. The largest failure was
`c1_polygon_procedural`: a Laplace isotherm drawing on an eight-vertex rectilinear plate, where the
drawing was off by 4.5 pp of the field range on average against a 0.5 pp tolerance, and a 10 C
isotherm was drawn onto the 100 C edge. That task was labelled "procedural" but was a **single
hardcoded polygon**, so the result was one data point and was never repeated.

That plate is exactly a three-column *skyline*: column widths 0.2 / 0.4 / 0.4 carrying heights
0.6 / 1.0 / 0.4. The family therefore generalises by construction, and
`scripts/polyheat_bench.py` reproduces the original vertex ring and the original prompt
**character for character** (checked in `verify` and in `tests/test_polyheat_bench.py`). It is
pinned into the benchmark as `polyheat_medium_0`.

## The family

    domain = { (x, y) : x in column i, 0 <= y <= h_i },  bottom edge 100 C, every other edge 0 C

Columns are laid on fifths of the unit square; heights are 0.4, 0.6, 0.8 or 1.0, and adjacent
columns must differ so no column is redundant. A skyline is always simply connected and always
keeps the whole hot edge, so every sampled instance is well posed without a feasibility search.

Each height change contributes exactly one 270-degree interior angle, so the **re-entrant corner
count is the difficulty axis** and the one-column case is a real control rather than a different
problem.

| Tier | Columns | Re-entrant corners | Instances |
|---|---:|---:|---:|
| control | 1 | 0 | 2 |
| easy | 2 | 1 | 3 |
| medium | 3 | 2 | 3 (includes the 18 September plate) |
| hard | 4 | 3 | 3 |

The model is asked for the isotherms at 10, 20, 40, 60 and 80 C, with a fixed `viewBox` and a fixed
affine map from plate to drawing coordinates, exactly as in the original prompt.

## References, and why they are trustworthy

Each reference is red-black SOR on the shared `fd_reference` primitive at **320 nodes per unit**,
admitted only after agreeing with a **640 nodes per unit** solve. Across the eleven admitted
instances the worst refinement difference away from the singular neighbourhoods is **0.040 C**,
against an admission limit of 0.05 C and a scoring tolerance of 0.5 C.

Two kinds of point are declared singular and excluded from the deciding metric:

- the two corners `(0,0)` and `(1,0)`, where the boundary data jumps between 100 C and 0 C;
- **every re-entrant corner**, which carries an r^(2/3) gradient singularity. This is where finite
  differences lose second-order convergence: the 320-versus-640 difference reaches 0.49 C there,
  more than ten times its value anywhere else. Excluding them is not a convenience — the reference
  is only certified outside them.

## The metric, and a correction to the 18 September screen

The original screen scored every sample, including samples taken into the two hot/cold corners.
On this domain family that criterion is **unreachable**: a drawing built from the reference
isolines themselves scores **5.0003 pp** strictly, because every isotherm terminates where the
boundary data jumps 0 to 100 C, and a sample taken into that corner is charged up to half the
field range. The 90.0 pp maxima reported on 18 September for the polygon and L-shape are this
effect, not an independent finding.

PolyHeat therefore decides on the **certified metric**: the maximum sampled contour error with a
0.05 radius removed around every declared singular point. On the same perfect drawing that metric
reads **0.0146 pp**, a 34-fold headroom under the 0.5 pp tolerance. Removing those neighbourhoods
can only help the model, so a failure measured this way is conservative and cannot be charged to
the reference. The strict score is still recorded for continuity, and a wider 0.10 radius is
recorded as a robustness column.

A drawing passes when the certified maximum is within tolerance, no required level is missing,
every required level has measurable samples, and at most 5 % of its sampled points fall outside
the plate. The last two conditions stop a drawing from "passing" by putting its contours where
nothing can be measured. Explicit detection of a sub-100 C isotherm lying on the 100 C edge is
reported as a separate, physically impossible failure mode.

## Admission

An instance counts as Astra-hard only with **three or more completed samples that all exceed the
tolerance on the certified metric**. Truncated responses, API errors and outputs without an SVG are
excluded rather than counted as failures.

## Arms

- **Zero-shot** keeps the 18 September protocol unchanged: `gpt-6-astra`, medium reasoning effort,
  20,000-token cap, Chat Completions, the package's `generation_v1` drafting wrapper, `store=false`.
- **Tool-assisted** gives the same drawings a `probe_temperature` function, at most four calls of at
  most 256 points, returning the exact reference temperature at points the model chooses. Function
  tools require the Responses endpoint for this model. This arm exists because a zero-shot failure
  cannot separate *cannot compute this field* from *cannot draw it*; with the field readable on
  request, a drawing that is still wrong is wrong about geometry.

## Reproduction

```sh
cd cvpr2027
PYTHONPATH=src ../.venv/bin/python scripts/polyheat_bench.py generate     # references + certification
PYTHONPATH=src ../.venv/bin/python scripts/polyheat_bench.py verify       # 14 pre-flight checks
PYTHONPATH=src ../.venv/bin/python -m unittest discover -s tests -p 'test_polyheat_bench.py'
PYTHONPATH=src ../.venv/bin/python scripts/polyheat_bench.py run          --output runs/<fresh> --samples 3   # billable
PYTHONPATH=src ../.venv/bin/python scripts/polyheat_bench.py run-assisted --output runs/<fresh> --samples 3   # billable
PYTHONPATH=src ../.venv/bin/python scripts/polyheat_bench.py score        --output runs/<fresh>
PYTHONPATH=src ../.venv/bin/python scripts/polyheat_bench.py figures      --output runs/<fresh>
```

`generate` is deterministic given its seed. `run` and `run-assisted` resume without re-billing a
sample whose response is already stored, and refuse to write into a directory created under a
different protocol.

## Limits

This measures sampled geometric fidelity of contour paths against a grid-refinement-certified
finite-difference reference. It is not a rendered-image review: occlusion, labels, legends, units
and colour are not assessed, and numerical agreement along samples is not a mathematical
certificate. The structural model is two-dimensional steady Laplace with Dirichlet data only.
Results describe `gpt-6-astra` under the stated protocol and tool budget; they do not bound what
the model could do with a solver, a code executor or a different prompt.
