# Precision toroidal-pipe section templates

These two tasks are a new, explicitly specified **0.05 mm inspection-template**
requirement. They were added adaptively after the original toroidal-pipe drawings
passed their 0.5 mm requirement. Those earlier results remain passes; this is not
retroactive threshold adjustment or evidence that the earlier tasks failed.
The new prompt, reference hashes, tolerance and policy were frozen before calls.

Generate or edit the oblique section of hollow curved pipe with a drilled port.
The output must have the actual non-conic section profile. No FEM/flow field is
requested. These are procedural geometry-discovery cases, not imported benchmark
samples or evidence of a novel CAD algorithm.

The scorer renders native SVG at 32 pixels/mm inside the declared inspection
window [-62.5,62.5]² mm. Physical tolerance is 0.05 mm, with a conservative one-
pixel allowance (0.03125 mm) for rasterization. Geometric disagreement must lie
beyond that band and exceed 0.05 mm² residual area. High-resolution output/reference
masks and overlays are saved for visual review. The mask assesses this window;
complete-sheet presentation requires separate visual review.

Before the first calls, both numerical contour exporters passed against the
independent implicit-solid membership mask at this resolution. A deliberately
shifted 0.25 mm profile failed. The torus generator also passes a closed-form
horizontal-section check and contour refinement check. The exporter simplifies
contours to 0.025 mm; measured reference-render differences were at most 0.0442 mm.

Screen: medium reasoning, 16,000 completion tokens, one independent sample.
Repeat only substantive failures twice at high reasoning, 32,000 tokens.
Selection requires three evaluable outputs, two high-effort samples, at least
two drawing failures including one high, and identified visual/evidence review.
Truncation and format/API outcomes cannot establish a shape failure.
