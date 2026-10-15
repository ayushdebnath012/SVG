# CADFEM-Bench v{version} — published-source pilot

{n} active tasks: {a} supplied-geometry tasks (A), {b} drawing-to-CAD task (B). Both tracks are reported separately. This is a source-backed pilot with provisional tolerances, not a set of certified engineering solutions. Held tasks are not candidates and are not scored.

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
