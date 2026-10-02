# Irregular cut-part nesting prompt

Fit fourteen unchanged irregular parts into 64 × 48 mm stock. Every part must be present once, with no overlaps and at least 0.4 mm part-to-part clearance. Only quarter-turn rotations and translations on the 4 mm lattice are permitted. Reflection, trimming and scaling are forbidden. The exact pose convention is given in `prompt.txt`.

Shapes are original connected regions from a seeded partition of the stock, then normalized and randomly oriented. Each union of 4 mm cells is offset inward by 0.2 mm with mitred corners to provide the cutting gap. This offset is part of the supplied shape. Seed 4500 was selected before model testing. The hidden reference certifies feasibility, but any valid layout passes.

`source.png` shows the empty stock and the part gallery. `prompt.txt` gives the exact visible cell coordinates; no reference placements are included. The model chooses placements, and the harness exports actual SVG outlines. `reference-audit.json` verifies those paths using continuous polygon geometry, shape preservation, permitted rigid poses, bounds and clearance. This is a geometric nesting experiment, not production qualification.

Protocol: `gpt-6-astra`, high effort, 32,000 output tokens per turn, four calls to `check_nesting`. Partial and complete candidates are allowed. No automatic nesting solver or code executor is exposed. A hard-case admission requires three fresh-context completed failures; incomplete/truncated responses, interface problems and API errors are excluded. Repaired intermediate errors do not count.

```sh
.venv/bin/python cvpr2027/scripts/cad_part_nesting.py run --output cvpr2027/runs/NEW-RUN/trial-1 --sample 1
.venv/bin/python -m unittest discover -s cvpr2027/tests -p test_cad_part_nesting.py
```

The local environment uses Shapely 2.1.2 for polygon checks. Five tests cover the reference, missing/out-of-bounds parts, overlap, rotation conventions and tampering with exported SVG coordinates.

Nesting is established prior work: [SVGnest](https://github.com/Jack000/SVGnest), [Sparrow](https://arxiv.org/abs/2509.13329), and [geometry-aware RL for nesting](https://arxiv.org/abs/2606.10611). This local fixture does not establish novelty. No external nesting dataset was downloaded and no training was started.
