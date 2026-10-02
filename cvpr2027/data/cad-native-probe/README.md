# BenchCAD-derived native CAD discovery probe

Attribution: [BenchCAD authors and dataset](https://huggingface.co/datasets/BenchCAD/BenchCAD),
released under CC-BY-4.0. Source record IDs, code, download hashes and modifications
are retained in `tasks.json`. This is a four-case derivative discovery experiment,
not a reproduction of the official benchmark or a new training split.

The downloaded official **edit-bench / edit_bench** records are held-out evaluation
data. Do not train on these records or their generated drawings, edits or traces.
The retained source and target programs generate genuine kernel-projected SVG
drawings. Each view is independently fit; the sheets are inspection artifacts,
not production drawings with complete manufacturing dimensioning.

The heat-sink reference is explicitly corrected: six equally spaced fin centres
spanning 59.88 mm require spacing 11.976 mm. The upstream target used 13.3 mm,
which does not preserve the requested span. The other three target programs are
unchanged. The source hinge has four solids at tangential contacts; the edited
square knuckles merge it into one. A source-code/STEP subtraction anomaly in the
elbow is a **kernel inconsistency**, not established source data corruption;
see `upstream_step_code_audit.json`.

The manifest was frozen before calls. Geometry passes require valid topology,
the target solid count and relative symmetric-difference volume at most 1e-4.
An added Boolean volume-identity check rejects inconsistent evaluator results;
all four final outputs were regraded and still pass with zero difference.
This screen used high-effort Astra, up to three CadQuery execution calls, and
10,000 output tokens per API turn. No target geometry is exposed in tool feedback.
The execution interface is a restricted CAD AST, not a general Python environment.

Only a substantive, reviewed final failure can trigger two fresh confirmations.
Passing tasks, repaired intermediate errors, exhausted budgets, API errors,
kernel inconsistencies and unsupported interface constructs do not enter the
failure-only shape subset. All four final outputs passed; the subset is empty.

Run commands from the repository root:

```sh
# Runtime was installed with CadQuery 2.8.0 using uv in cvpr2027/tmp/cad-runtime.
python3 cvpr2027/scripts/cad_native_probe.py run NEW_OUTPUT_DIRECTORY
.venv/bin/python cvpr2027/scripts/review_cad_native.py
cvpr2027/tmp/cad-runtime/bin/python -m unittest discover -s cvpr2027/tests -p test_cad_native_probe.py -v
```

API attempts are never silently retried. A new output directory starts new paid
calls. Ground-truth comparisons are offline and are not feedback to the model.
