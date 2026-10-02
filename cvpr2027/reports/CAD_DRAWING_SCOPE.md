# Scope correction: CAD-style SVG drawings

User clarification, 20 September 2026. This definition supersedes the
field-plot-centred target in the earlier proposal, overview, plain-language
summary, roadmap and `engineering_v4` plan. It defines intended work, not
implemented capabilities or new experimental results.

## Intended output

Generate and edit engineering drawings of physical objects: a building or
structural frame, a table, a bracket, or another designed part or assembly.
Deliver editable SVG plans, elevations, sections and dimensioned views as
appropriate. The main drawing describes the object and its construction.
Flow around a cylinder, temperature contours and other standalone physics
illustrations do not constitute the target task. Analysis overlays may
supplement an object drawing.

Retain the three input modes: text to drawing, reference image to drawing,
and edits to an existing SVG. A reference image without scale, depth or
material information cannot by itself specify a complete analysis model;
missing information must remain explicit.

## Drawing and analysis contract

Pair the SVG with a structured physical model containing real dimensions
and units, member or solid geometry, section properties or thickness,
materials, joints, supports, loads and load cases. Use persistent object IDs
to associate drawing elements and dimensions with this model. Drawing
coordinates and stroke widths must not silently become physical dimensions.
Multiple SVG views must derive from the same object model.

The proposed workflow is:

1. Extract or create the object model and record missing assumptions.
2. Generate dimensioned SVG views; check geometry, connectivity, dimensions,
   units and agreement across views.
3. Choose checks appropriate to the object and requested edit: geometric
   constraints, dimension and assembly consistency, clearance/collision checks,
   statics, analytical mechanics, stability checks, and numerical simulation
   including FEM where appropriate. FEM is one technique, not a requirement
   for every task. Record modelling assumptions and numerical diagnostics.
4. Compare computed quantities with explicitly specified acceptance criteria.
   Report each check as passed, failed, or not evaluated; solving successfully
   alone is not a design pass.
5. Apply edits to the shared model, update affected views, and repeat affected
   checks. Physical edits invalidate the previous analysis until recomputed.

FEM results are conditional on the stated model and load cases. An analysis
of a simplified building frame must be described as that, not as validation
of an entire building. A table requires explicit assumptions about its top,
legs, connections and support contact; a single drawn elevation does not
establish three-dimensional stability. Criteria and supported analysis types
must be declared per task rather than implied by an overall "verified" badge.

Pure presentation edits can reuse a result only when the physical model is
unchanged. Dimension text must remain bound to model values. A manually
changed dimension that disagrees with geometry is a consistency failure,
not merely a cosmetic edit. Store model identity, solver configuration and
result provenance so stale results can be detected.

## Initial object-based task families

These are proposed benchmark tasks; no measurements are claimed here.

| Object | Example generation or edit task | Checks to specify in the task |
|---|---|---|
| Table | Draw dimensioned views; increase span, reduce top thickness, move a leg, or add a brace | Dimensions and assembly consistency; deflection and stress under stated loads; stability and joint checks where modelled |
| Building frame | Draw a specified frame and floor layout; move a column, extend a bay, or change a beam section | View consistency and member connectivity; reactions, member response and drift under stated load cases; explicitly scoped stability checks |
| Bracket or plate | Draw a dimensioned part; move a hole, change thickness, or alter a fillet | Geometric validity and clearances; displacement and stress with specified material, supports and loading |

Include both feasible and deliberately failing edits, plus underspecified
requests. An edit can be geometrically valid while failing a physical check.
The system must report that distinction and must not silently alter unrelated
dimensions or loads to make a design pass.

## Evaluation and next implementation milestone

The user additionally requests an **Astra-conditioned failure benchmark**:
screen candidate object drawings and edits with Astra, verify the failures,
repeat them, and admit only confirmed failing tasks to the hard benchmark.
Retain passing cases and all screening outcomes in a separate audit pool.
Distinguish inability to draw the requested geometry from incorrect physical
analysis; neither API failures nor formatting-only failures establish shape
inability. The [first pilot](../data/cad-astra-pilot/README.md) implements this
discovery protocol for three planar object-frame families, with geometric,
statics, analytical-energy and FEM checks. Its measured status is recorded in
the run artifacts; broader CAD capabilities remain future work.

Evaluate drafting quality, instruction fulfilment, dimension and topology
consistency, agreement between SVG and the physical model, analysis accuracy,
correct classification against declared criteria, and invalidation of stale
results after edits. Contour fidelity is an optional analysis-overlay metric,
not the primary measure of an engineering drawing.

Start with one fully specified table or frame family and implement the full
generate–edit–analyse–verify cycle before scaling to diverse objects. Each
case needs initial and edited SVG views, structured models, declared load
cases and acceptance criteria, independently checked reference results, and
an explicit record of evaluated and unevaluated checks. Include a failing
physical edit and a presentation-only edit to test result invalidation.

Existing field-contour experiments remain useful numerical diagnostics.
The axial-bar edit/re-solve integration is a limited foundation. Neither
establishes an implemented CAD drawing system or validated table/building
design capability. The earlier PDFs and task lists need a subsequent rewrite
around this scope; their field-first future-work sections are superseded.
