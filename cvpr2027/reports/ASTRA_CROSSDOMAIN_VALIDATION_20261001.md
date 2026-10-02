# Cross-domain validation of saved Astra engineering drawings — 1 October 2026

## Decision

The saved structural frame evidence supports a **repeatable failure to complete the requested analysis**, not an incorrect structural safety claim. On one 21-member, three-storey frame edit, Astra returned geometrically correct, dimensioned SVGs but marked all three requested engineering quantities unavailable in **3 of 4 completed fresh-context attempts**. The fourth attempt returned values within the benchmark's 2% tolerance. An independent solve of each returned drawing gives approximately **ux = 3.5119 mm, uy = −0.1882 mm, peak stress = 17.6837 MPa**. The model did not assert a false pass in the three refusals.

The re-scored mechanical CAD cases provide **controls, not Astra failures**: 10/10 completed gear, cam, manifold and toroidal-section tasks pass their saved geometric checkers. Six completed functional frame-sizing designs also pass the SVG readback and FEM constraints; these used a deterministic SVG exporter, so they do not test free-form drawing. No Astra result exists for the separate 100-edit truss benchmark. Incomplete PCB serpentine and nesting trials, API errors and the single non-reproducing 179 MPa frame outlier are not admitted as confirmed hard cases.

## Structural example

The task moved the second grid line from x=3300 to 4000 mm and increased the downward load at N3_3 from 53,000 to 68,000 N. It has 16 joints, 21 members and degree of static indeterminacy 27. Astra received the explicit physical model and source SVG, without an external solver. The frame is idealised as planar, linear elastic and rigid jointed.

| Saved attempt | Edited geometry and dimensions | Astra analysis | Re-solve of returned SVG |
|---|---|---|---|
| XL screen, sample 0 | Pass | Unavailable | 3.5119 mm, −0.1882 mm, 17.6837 MPa |
| XL confirmation, sample 0 | Pass | Unavailable | 3.5119 mm, −0.1882 mm, 17.6837 MPa |
| XL confirmation, sample 1 | Pass | Unavailable | 3.5119 mm, −0.1882 mm, 17.6837 MPa |
| XL confirmation, sample 2 | Pass | 3.5 mm, −0.188 mm, 17.7 MPa | 3.5119 mm, −0.1882 mm, 17.6837 MPa |

All four calls completed with `finish_reason=stop`. The first three responses explicitly set `status="unavailable"` and the three numerical fields to null. Re-scoring the raw response and extracting the returned SVG produced no member, joint, dimension or visible-result discrepancies. The solver recovered the edited geometry from each returned SVG. One-element and four-element-per-member frame solves agree to better than 1e−7 relative error for the three reported quantities. This is independent of Astra's answers, but the two mesh resolutions share the same local FEM formulation; it is not a commercial-solver certification.

The [annotated returned SVG](../paper/network/figures/astra-frame-decline-annotated.svg) highlights the moved column and changed load in orange and the unavailable analysis in red. The [unmodified Astra SVG](../paper/network/figures/astra-frame-decline-raw.svg) is retained. Presentation marks were added after scoring.

## What was checked

- Re-read the saved Astra responses and recomputed scores against the frozen frame and CAD manifests, including manifest hashes for the 10 mechanical tasks.
- Solved the physical frame model at two mesh resolutions and re-solved all four returned SVG geometries. All four drawn-frame results agree with the frozen target to within 1e−6 in the three checked quantities.
- Re-scored all 10 saved mechanical hard-CAD tasks; all passed. Re-read and independently re-analysed all six saved functional sizing SVGs; all passed their stipulated constraints.
- Ran all eight EngFrame benchmark self-checks on each of the main and XL manifests, plus focused CAD scorer, frame and geometry tests (27 tests and 12 subtests passed).

Reproduce the saved-output audit without API calls:

```sh
cd cvpr2027
../.venv/bin/python scripts/validate_astra_crossdomain.py
```

The machine-readable [validation record](ASTRA_CROSSDOMAIN_VALIDATION_20261001.json) records per-attempt values and response/SVG hashes. The network paper's ReSolve tables remain limited to circuits and pipe networks: the structural frame uses a separate FEM harness and a prompt that supplies an explicit model. The structural result is a diagnostic example of an unmet analysis request, not evidence that ReSolve already verifies frames.
