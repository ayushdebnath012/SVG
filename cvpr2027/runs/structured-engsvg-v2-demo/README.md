# Structured EngSVG v2 deterministic demo

This directory contains two locally reproduced examples:

- `create/`: mixed-unit text creates a canonical design, SVG and fresh FEM result.
- `edit/`: one instruction widens the frame, raises the lateral load and lowers the vertical load. Only those three retained parameters change.
- `detached-input.svg`: the created SVG with its metadata element removed.
- `detached-edit/`: recovery from visible drawing evidence followed by an edit and fresh FEM analysis.

Each directory contains:

- `request-result.json`: source state, parsed action, visible change summary, final design and FEM result.
- `design.svg`: regenerated engineering SVG with an `engsvg-design-v1` metadata element.

Run a new creation from the repository root:

```bash
PYTHONPATH=cvpr2027/scripts .venv/bin/python cvpr2027/scripts/structured_engsvg.py request \
  --out cvpr2027/runs/my-engsvg-request \
  --request 'A 1.4 m wide and 85 cm tall table side frame uses a 5 cm by 9 cm section, E 200 GPa, 1.2 kN down and 0.15 kN right.'
```

For an edit, add `--source` with either canonical JSON or a path to a JSON design.

Import and edit a detached SVG:

```bash
PYTHONPATH=cvpr2027/scripts .venv/bin/python cvpr2027/scripts/structured_engsvg.py import-svg \
  --out cvpr2027/runs/my-detached-edit \
  --svg drawing.svg \
  --request 'Make it 0.2 m wider and remove the lateral load.'
```

If required engineering values are not visible, `import-result.json` reports every missing field. Supply independently known values with `--supplied '{"E_mpa":200000,...}'`; the importer does not invent them.

The scope remains one planar fixed-base portal topology. The FEM result is a linear frame analysis and is not a construction safety certification.
