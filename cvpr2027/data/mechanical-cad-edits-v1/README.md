# Complex mechanical CAD edit pairs

150 executed, geometry-verified pairs from 76 BenchCAD parts / 40 families.
108 train, 22 validation, 20 test; whole-family holdout before augmentation.
Pipe/circuit families excluded. All source and edited solids are exported as
STEP and four SVG projections, with annotated before/after sheets in `sheets/`.

See `manifest.json` for provenance, `audit.json` for checks, and
[the completed training report](../../reports/MECHANICAL_CAD_DATA_AND_TRAINING_20261002.md).
The local model trained on 92 retained code-edit examples, not on drawing pixels.

FEM: not evaluated; material, load, support and physical unit contracts missing.
Geometry checks do not certify strength, manufacturing tolerances or standards.

Source: [BenchCAD, Zhang et al. 2026](https://huggingface.co/datasets/BenchCAD/BenchCAD),
CC-BY-4.0, pinned revision `5919f578ab09ec283603a082fab07c7639ab56eb`.
These are synthetic feature edits and CAD-derived views; they are not expert
before/after manufacturing blueprints. Official held-out edit templates were
excluded conservatively. Cross-dataset geometric equivalence is not proven.
