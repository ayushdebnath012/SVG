# Untagged truss recovery v1

This fixture tests recovery without `data-member`, `data-dimension` or embedded engineering metadata.

- `untagged-truss.svg` contains seven ordinary structural lines, five node circles, visible dimensions, support notation, material, section and load text.
- `reference-ir.json` is the authored common engineering representation.
- `recovered-ir.json` is reconstructed from visible SVG geometry and text.
- `analysis.json` is produced by the independent planar axial-truss FEM solver.
- `summary.json` compares reference and recovered engineering hashes.
- `sha256-manifest.json` protects the saved evidence.

Rebuild from the repository root:

```bash
PYTHONPATH=cvpr2027/scripts .venv/bin/python cvpr2027/scripts/engsvg_truss.py \
  --out cvpr2027/runs/engsvg-untagged-truss-v1
```

Scope: one five-node triangular truss with a known drawing grammar. This is evidence that geometry and connectivity can be recovered without semantic SVG attributes; it is not general drawing recognition.
