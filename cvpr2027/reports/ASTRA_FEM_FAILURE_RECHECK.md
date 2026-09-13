# Astra engineering-physics failure recheck

13 September 2026. **The earlier report overstated the evidence for three general classes of Astra failure.** The historical Robin case did exhaust its token budget, but both new calls returned accurate contours under the present sampled metric. The capacitor's alleged closed field loops are not present in its saved paths. The bracket output explicitly discloses that its stress colors are illustrative rather than a solved FEM field.

This report supersedes the strong qualitative failure claims in the older overview/proposal. Original files remain intact for provenance. It does not assert that Astra reliably solves arbitrary FEM problems.

## Direct OpenAI API reruns

The existing local credential was verified against the direct OpenAI model endpoint. Calls used `gpt-6-astra`, the original task texts and generation wrapper, Chat Completions, `store=false`, and one sample per condition. No key is copied into these artifacts. Model access and parameters were checked against [official Astra documentation](https://developers.openai.com/api/docs/models/gpt-6-astra).

| Case | Effort / token cap | Finish | Completion / reasoning tokens | Wall time |
|---|---|---|---:|---:|
| Convective plate | medium / 16,000 | stop, SVG | 15,329 / 11,775 | 297.90 s |
| Convective plate | medium / 32,000 | stop, SVG | 17,697 / 14,660 | 334.30 s |
| Finite capacitor | low / 16,000 | stop, SVG | 3,120 / 512 | 48.83 s |
| L-bracket stress | low / 16,000 | stop, SVG | 3,439 / 512 | 63.23 s |

All four attempts, request payloads, response IDs, full responses and usage are retained in `runs/astra-api-recheck-20260913/`. The protocol was saved before calls. Total usage was 1,312 input and 39,585 completion tokens, approximately **$1.99** at the documented standard $10/$50 per million input/output tokens; this is a token-price estimate, not an invoice. [Pricing source](https://developers.openai.com/api/docs/models/gpt-6-astra).

The paired Robin conditions change the budget only. One sample each cannot isolate a budget effect statistically. A historical model alias may also resolve differently over time; no failure-rate or model-wide capability claim follows from these four calls.

## 1. Robin heat conduction: historical truncation, not reproduced

The original `plate_convective_edges` record contains 16,000 completion tokens, all reported as reasoning, `finish_reason=length`, and no SVG. This is a real completion failure for that call. It is not enough to conclude that Robin boundaries are beyond the model's capability.

The independent reference solves ∇²T=0 on [0,2] × [0,1], with T=100 °C on the left, ambient 0 °C and outward derivative ∂T/∂n=−5T on the other three edges. The P2 Galerkin weak form adds the Robin boundary integral `∫ 5 T v` to the stiffness form. Implementation uses [scikit-fem boundary forms](https://scikit-fem.readthedocs.io/en/stable/api.html).

Reference checks include an exact linear Robin anchor, discrete heat balance and five meshes from 576 to 147,456 triangles. The finest mesh has 296,065 degrees of freedom. The last two meshes differ by at most 0.02053 °C on the common regular grid, and by at most 0.00797 °C at the sampled model-contour points. These differences estimate numerical sensitivity; they are not certified continuum error bounds. The old first-order finite-difference reference differs from the fine FEM grid by up to 1.977 °C, so it should not be treated as exact ground truth.

The primary recheck evaluates temperature **directly in the FEM basis** along the transformed SVG paths, at maximum physical sampling step 0.002. The five required levels are present and no unsupported contour features were flagged.

| New response | Arc-length-weighted mean error | Maximum sampled error | Pass at 0.5 °C |
|---|---:|---:|---|
| 16,000-token cap | 0.00702 °C | 0.11074 °C | Yes |
| 32,000-token cap | 0.01247 °C | 0.37385 °C | Yes |

The separately retained regular-grid audit gives slightly larger maxima, 0.12698 and 0.38381 °C, because it adds interpolation error. Use the direct FEM scores above for the primary numerical comparison. Larger token budget did not improve the measured error in this pair; neither a benefit nor a disadvantage is established with one call per condition.

![Astra contours compared with FEM](../runs/astra-api-recheck-20260913/robin_fem_comparison.png)

These are geometric contour checks. They do not certify all rendered labels, occlusion, units, or the boundary-angle condition separately. Numerical agreement along samples is not a mathematical certificate.

## 2. Capacitor: retract the closed-loop claim

The historical artifact has 12 selected electric-field paths, **zero closed paths**, and every selected path joins the positive and negative plate. The source explicitly includes “End contours schematic.” The apparent circular lobes in the figure are open paths terminating on conductors. Its open equipotential endpoints also do not by themselves establish behavior at infinity.

A source-specific path-intersection diagnostic finds a maximum departure from perpendicularity of about 8.04 degrees at computed field/equipotential intersections, with no failed intersection pairs. This supports describing the rendering as approximate. It does not establish that the field is physically impossible, nor is it a substitute for an electrostatic solve. The new response again labels its end fringing as schematic.

Needed for a fair quantitative test: specify whether this is a 2-D cross-section or a 3-D finite plate, conductor thickness/width, the exterior/far-boundary treatment, and the field quantity to evaluate. Then use a converged FEM/BEM or independent electrostatic reference. Until then, numerical fidelity is **unverified**, not a demonstrated closed-loop failure.

Evidence: `runs/astra-historical-audit/capacitor_geometry.json`; reproducible source-specific checker: `scripts/audit_historical_capacitor.py`.

## 3. Bracket: disclosed approximation and under-specified peak stress

Both historical and fresh outputs give the approximately 122 MPa beam-theory nominal stress under the stated interpretation of 80 mm out-of-plane width, 8 mm thickness and 52 mm lever arm. Both illustrate a roughly 220 MPa hotspot using an assumed factor near 1.8 and disclose that this is not a solved FEM result.

The fresh SVG states that a finite peak requires a fillet radius, bolt/contact assumptions and a converged mesh. The original prompt asks for an expected field and estimated peak without specifying these inputs. Scoring the illustration as a numerically solved von Mises field would misrepresent both the prompt and the response. The legitimate gap is that the picture does not supply a solved, verifiable stress field.

A next test should prescribe complete geometry, plane-stress/3-D assumptions, material law, support/contact conditions, load distribution and fillet. Compare displacement, reactions and stress away from singular boundaries, then perform a convergence study for any peak claim. Reusing the infinite-plate Kirsch factor as exact truth for a finite square plate is also invalid; the earlier local FEM smoke results already show a finite-domain difference.

## What the project needs to address

1. **Completion reliability:** retain token use and empty/truncated attempts, with repeated cases and budgets. A single failure cannot define a PDE-class limit.
2. **Numerical reference quality:** mesh convergence, analytic anchors, physical balance and direct field evaluation before labeling model error.
3. **Honest claim status:** distinguish an approximation, a solved field, a verified geometry and a fully reviewed drawing. Treat disclosed approximations differently from undisclosed numerical claims.
4. **Physical edits:** rerun FEM when loads, material, geometry or boundary conditions change, then update the visible field, quantity, units and labels together.
5. **Stronger evaluation:** well-posed finite elasticity, multiphysics and sequential visual edits with repeated samples and independent references. The current evidence does not justify saying Astra generally fails at FEM.

The [FEM literature survey](FEM_LITERATURE_AND_EXTENSION.md) identifies the existing simulation and training systems to build on. The new FEM-Bench bridge performs actual solver reruns; the earlier Qwen action-policy training is retained as a separate infrastructure pilot.

Reproduction from `cvpr2027/`:

```sh
PYTHONPATH=src ../.venv/bin/python scripts/robin_fem_reference.py --output runs/robin-fem-reference --fd-reference runs/reference-v3/plate_convective_edges.npz
PYTHONPATH=src ../.venv/bin/python scripts/score_astra_robin_fem.py --runs runs/astra-api-recheck-20260913 --reference runs/robin-fem-reference
../.venv/bin/python scripts/fem_bench_svg_extension.py --output runs/fem-bench-svg-anchor
```
