# CADFEM-Bench v1.6 - published-source pilot

57 primary tasks: 51 supplied-CAD tasks (A), 6 drawing/specification-to-CAD tasks (B). Seven calibration cases, 63 reserved public-source cases and one related case are evaluator-only. Scores report both tracks and the 14-task independently reproduced subset separately.

Use only your task's prompt and input files. Sources are public, so prior exposure is possible. Do not look up answers or access evaluator files. Execute your own CAD/FEM workflow and report quantities in exactly the requested units. Some supplied CAD files are documented format/unit conversions of original source CAD.

For each task, submit a directory named by task_id with these eight nonempty files:

| File | Contract |
|---|---|
| results.json | Exactly `{"outputs": {"requested_key": number, ...}}`. All required keys and no extras. JSON numbers only; no strings, Boolean numbers, NaN or infinity. |
| main.py | Reproducible entry point for the analysis, including geometry construction for B. Document dependencies and invocation. |
| part.step | Valid analysis solid geometry, in millimetres and the specified coordinate frame. For a 2-D analysis, supply the physical solid and document the 2-D reduction. |
| mesh.msh | Actual mesh used for the reported analysis, exported as Gmsh MSH; preserve physical groups and node/element mapping. |
| fields.npz | Original computed arrays exported without pickle/object arrays; include node IDs, coordinates, units, displacements/stresses/temperatures or mode fields as applicable, times/frequencies and masks. Explain array meanings and mapping in environment.json. |
| solver.log | Solver output, versions, invocation, termination and diagnostics for the run. |
| refinement.json | At least two actual mesh resolutions, mesh sizes/counts and quantities at each, or a documented publisher-mesh-protocol reproduction with limitations. |
| environment.json | Solver/library versions, command, units, field schema, physical-group mapping, quantity-extraction definitions and modeling assumptions. |

Numerical accuracy is reported separately. Workflow completion requires trusted evaluator review of execution, geometry, setup, field extraction and numerical convergence. Merely creating files does not pass. Tasks with unresolved setup ambiguity cannot receive workflow approval.

For rigging reconstruction, keep the plate's length, width and thickness along the coordinate axes; any position and any of the 24 axis-aligned orientations is accepted: the evaluator aligns your part to the original CAD (bounding-box centres, proper axis rotations, no mirroring) before checking shape overlap, and reviews drawing features. Source licences differ, and some cases are local-research-only; consult each task's source metadata.

Replay reads CADFEM_INPUT_DIR and writes CADFEM_OUTPUT_DIR. The standardized serial runtime and budgets are supplied by the operator. Inputs and code are read-only, network access is disabled, and each attempt is isolated. No API credentials belong in submissions.

For the five FEMCAD specification tasks, retain analytic spherical and cylindrical surfaces in STEP. Their stated radii are checked within 0.01 mm, in addition to volume overlap and solid count. Alternative surface representations need a separately defined validator; do not claim they are supported by this automated gate.

For the SSLP311 fracture tasks, plate.step is a 2-D plane-stress domain extruded 0.1 mm along +z as an exchange convention. Analyse the z = 0 section in plane stress, report G per unit thickness, and submit the analysed domain as part.step (the extruded solids are accepted). For the plastic limit-load tasks, the curve of load factor against displacement must be part of fields.npz or refinement.json.
