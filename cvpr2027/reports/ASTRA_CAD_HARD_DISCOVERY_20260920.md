# Harder CAD drawing discovery: negative result

**Ten new prompt conditions produced ten complete passes and no qualifying
shape failures.** They cover generation/editing for four mechanical families,
plus a separate precision requirement on the toroidal-pipe family. They are not
ten independent design families. All are excluded from the requested failure-only
benchmark. No failed case was available for high-effort confirmation.

This is useful negative evidence: fully specified profiles and sections, even
with non-conic boundaries, have not exposed a repeatable gap under this setup.
It is not evidence that Astra solves all CAD, nor a reason to manufacture a hard
subset by silently tightening old thresholds.

| Task family | New prompts | Stated contour tolerance | Screening result |
|---|---:|---:|---|
| Involute gear, bore and keyway | Generate + edit | 0.5 mm | Both pass |
| Cycloidal roller cam, actual offset contour | Generate + edit | 0.5 mm | Both pass |
| Oblique manifold section, intersecting drilled bores | Generate + edit | 0.5 mm | Both pass |
| Toroidal hollow pipe section, non-conic boundaries and access port | Generate + edit | 0.5 mm | Both pass |
| Precision inspection template of toroidal-pipe section | Generate + edit | 0.05 mm + declared raster allowance | Both pass |

The first six used 40,292 tokens. The adaptive pipe-section round used 15,482.
The separately specified precision round used 22,372. **Total: 78,146 tokens**
(29,286 input; 48,860 completion, including reasoning). Every response finished
normally; none was truncated or excluded for format/API errors. No previously
passing table/building/shelf/simple-plate request was rerun.

## Fixed interfaces and adaptive discovery

Each round froze its prompts, references and tolerances before calls. Astra
(`gpt-6-astra`) received no external tools and used medium reasoning with a
16,000-completion-token cap. Native SVG paths, shapes, transforms, local reuse,
clipping and masks were allowed. This matters: Astra correctly used repeated
geometry and mask-based offset construction instead of manually transcribing
thousands of points.

The precision tasks were created only after the original curved-pipe tasks
passed. The new prompt explicitly requests a 0.05 mm inspection template, and
has a separate task ID/manifest. Old 0.5 mm tasks remain passes. This adaptive
search is development evidence, not a frozen generalization test.

The precision evaluator uses 32 pixels/mm with a declared one-pixel raster
allowance (0.03125 mm), and requires more than 0.05 mm² disagreement beyond that
band to fail. Both precision outputs have zero residual area and maximum
measured raster intrusion of 0.03125 mm. These are raster comparison quantities,
not an assertion of independently certified machining accuracy. The inspection
window is explicitly bounded; full drawing sheets were separately rendered.

## Verification and review

Twenty-five automated tests pass. Gear references use polar membership and
independent SVG serialization, with tooth-count/pitch-thickness checks. Cam
references check the analytical normal offset. Manifold references compare
3D solid membership against polygon/ellipse construction. Toroidal sections use
implicit-solid membership and refined numerical contours, with a closed-form
horizontal-section test. Deliberately stale/shifted geometry is detected.

Before the precision calls, both reference exports passed the finer evaluator;
a deliberate 0.25 mm shift failed. Their own reference-render discrepancy was
at most 0.0442 mm. The assistant reviewed reference/answer/overlay galleries;
this is not a human engineering sign-off. No fabricated error, label-only issue,
format failure or token limit was admitted as geometric inability.

## Evidence and reproducibility

- [Combined counts, per-case metrics and token usage](../runs/astra-cad-hard-20260920/discovery_summary.json)
- [Gear/cam/manifold gallery: reference, Astra, difference](../runs/astra-cad-hard-20260920/screen_gallery.png)
- [Toroidal section gallery](../runs/astra-cad-hard-20260920/torus_gallery.png)
- [Precision gallery and magnified differences](../runs/astra-cad-hard-20260920/precision_gallery.png)
- [Initial hard-pool protocol](../data/cad-hard-geometry/README.md)
- [Non-conic section protocol](../data/cad-torus-sections/README.md)
- [Separate precision protocol](../data/cad-precision-sections/README.md)
- [Verifier test log](../runs/astra-cad-hard-20260920/verifier_tests.log)
- [Empty selected drawing set](../runs/astra-cad-hard-20260920/selected_drawing_tasks.json)

Each run directory preserves requests, actual returned model IDs, raw responses,
usage and scored finish reasons. Geometry overlays are generated from the saved
SVGs. Subsets have their own selection manifests; all selected lists are empty.
The earlier [frame/plate pilot](ASTRA_CAD_PILOT_20260920.md) still has one
unconfirmed analysis-only candidate, which is not a drawing failure.

## Research decision

Do not train against these solved examples as evidence of a frontier-model gap.
No further training was started during this follow-up. Stop spending confirmation
calls on these passing cases. The [expanded overlap audit](CAD_NOVELTY_OVERLAP_20260920.md)
also finds that generic CAD editing plus FEM, SVG preservation, iterative repair
and cross-representation checks are already substantially anticipated.

Before a larger run, switch to a source-model experiment that tests intent-to-
feature mapping and edits across multiple linked views/annotations, with
requirements rather than a single mandatory geometry when designs are
underdetermined. Use released model/edit data and compare tool-using Astra and
existing CAD agents. A deterministic exporter should be included. This is a
recommended change of experimental question, not a completed method or a proven
novelty claim. The requested failure-only benchmark remains unpopulated.
