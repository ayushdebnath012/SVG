# Detached engineering SVG controls

Original procedural mounting-panel drawings, generated locally on 21 September 2026. `tasks.json` is the frozen record used for the API screen. No third-party drawings or evaluation records are included in these fixtures. No external distribution license is assigned here.

One source design has two dimensional intentions (`chain`, `edge`) and two coordinate encodings (`plain`, `nested`): four conditions, not four independent designs. The width edit is 180→234 mm. Parenthesized values are explicitly defined as reference dimensions by the task. See [the project foundation](../../reports/PROJECT_FOUNDATION_20260921.md) for assumptions and limitations.

Source and target SVG files remain available in each case directory. The API received the source SVG and edit instruction, never `target_svg` or the full manifest. The hidden targets and `shape_ids` are evaluator-only. Opaque element IDs are shared between conditions and do not encode the dimensioning intention.

Both Astra and the handwritten SVG constraint baseline passed all four conditions. They are excluded from the failure-only benchmark and were not used for training. Nested transforms preserve page-space geometry, with a small difference in dash appearance; no claim of identical raster images is made.

The numerical ambiguity example is a separate authored constraint control in `runs/astra-cad-intent-20260921/query-evidence.json`; it was not sent to Astra and is not evidence of a model failure.
