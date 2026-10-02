# Coupled routing edit: exact lengths and locked copper

This prompt adds exact geometric trace lengths and preservation of existing copper to the 24-net layout. Five routes are visible and locked; nineteen must be completed. All 24 routes must meet their specified centerline lengths, avoid obstacles and foreign copper, and remain simple paths without retracing. The exact coordinates and length targets are in `prompt.txt`, with `source.png` as the image input.

The reference satisfies all constraints. `reference-audit.json` checks actual SVG clearances, connectivity and centerline lengths. These are geometric length requirements, not verified impedance, signal timing or electrical functionality. No FEM claim is made. The locked traces provide useful input as well as constraints, so this variant is not assumed empirically harder until tested.

The protocol uses `gpt-6-astra`, high effort, 32,000 output tokens per turn, and four calls to the extended geometric checker. General code execution and automatic routing are not supplied. Partial checker submissions are allowed. Intermediate errors repaired in the final response do not count. Three fresh-context completed failures are required for repeatability; truncation, interface and operational errors are excluded.

Run from the repository root with a fresh directory:

```sh
.venv/bin/python cvpr2027/scripts/cad_timed_routing.py run --output cvpr2027/runs/NEW-RUN/trial-1 --sample 1
.venv/bin/python -m unittest discover -s cvpr2027/tests -p test_cad_timed_routing.py
```

The reference routes are hidden except the five explicitly stipulated locked traces. A model may return any valid geometry with the specified lengths; it need not reproduce the reference routes. Reversed traversal and equivalent collinear segmentation of locked copper are accepted. The source board is shared with the unconstrained 24-net fixture; this is not a new independent shape family.

Routing benchmarks already exist, notably [OmniRouting](https://arxiv.org/abs/2608.04434) and [PCBWorld](https://arxiv.org/abs/2607.05915). This diagnostic does not establish novelty. No training has been started on these cases.
