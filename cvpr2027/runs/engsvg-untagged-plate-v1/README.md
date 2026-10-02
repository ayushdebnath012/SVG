# Untagged mechanical plate recovery v1

This run recovers a transformed four-hole mounting plate from ordinary SVG rectangles, circles, dimension lines and text. The drawing contains no semantic `data-*` geometry attributes.

The recovered common engineering model is checked for boundary crossings, hole overlap, minimum edge distance, minimum ligament, net area and material volume. These checks fit the drawing type; this fixture does not claim plate FEM.

Rebuild from the repository root:

```bash
PYTHONPATH=cvpr2027/scripts .venv/bin/python cvpr2027/scripts/engsvg_plate.py \
  --out cvpr2027/runs/engsvg-untagged-plate-v1
```

The authored and recovered engineering hashes must match, and all files are covered by `sha256-manifest.json`.
