# CAD-Editor training feasibility subset

Derived from the official [CAD-Editor](https://github.com/microsoft/CAD-Editor)
processed archive. Archive SHA256, source URL, exact split rules and file hashes
are in `manifest.json`. Source totals: 120,000 training and 2,000 test records.
The bounded subset contains 2,048 training, 128 validation and 128 test pairs.

Every normalized source/target sequence belongs to a connected component. A
component touching official test is excluded from training and validation;
remaining components are deterministically split before seeded subsampling.
Native design IDs are unavailable, so geometrically equivalent sequences may
still overlap. This is not a final geometric-generalization evaluation.

The initial LoRA run uses Qwen2.5-Coder-1.5B-Instruct, one fixed epoch, completion-
only loss, rank 16 and seed 17. The runner records tokenizer-length exclusions
without truncating targets, base/final generations on 32 held-out rows, package
versions, source hashes, model revision and checkpoint. Exact sequence match and
text similarity are diagnostic metrics only. CAD execution, SVG generation and
physical correctness are not evaluated by this training run.

No Astra discovery or selected benchmark task enters this training subset.
Preserve upstream notices and underlying source-data terms when distributing
these derived records; the upstream code's MIT license alone does not settle
all original CAD model rights.

Completed-run results and limitations: [training report](../../reports/CAD_EDITOR_TRAINING_20260920.md).
