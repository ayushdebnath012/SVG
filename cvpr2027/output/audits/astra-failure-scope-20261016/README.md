# Scope audit of Astra failure runs

Read-only inspection of the seven-page PDF, admitted cases manifest, frame source manifest, and all ten large-frame request/response records. No model calls. Original report unchanged.

Of 15 admitted observations: 11 are SVG structural-frame drawing plus unaided frame analysis; 3 are CadQuery editing without FEM; 1 is SVG hydraulic-network editing plus network analysis. One additional frame task is explicitly unconfirmed.

Frame finite elements are legitimate FEM, but the recorded Astra failure is computational abstention with no tools, not a failed CAD/mesh/FEM solver execution. The strongest observed pattern covers 10 task variants over 5 generated planar frame layouts, with 1 sample per variant. It does not show 10 independently repeated 3D CAD+FEM failures. The separately repeated 21-member frame abstained in 3 of 4 samples.

All ten large-frame raw responses end with finish_reason=stop and analysis.status=unavailable, with null displacements and stress. The prompt explicitly offers unavailable as an honest response option. The appropriate label is unassisted analysis abstention/incompletion, not incorrect numerical FEM output or safety refusal.

The 3 CAD edits test code/kernel/geometry output only. The hydraulic task uses a Darcy-Weisbach/Churchill network solver, not a finite-element simulation of mechanical CAD. The propeller reference also has a floating boss, and the twisted-bracket instruction is acknowledged ambiguous; these are unsuitable as clean FEM capability evidence.

Confirmed end-to-end 3D CAD+FEM execution failures established by this report: 0. This is scoped to the report and inspected package, not a claim about all possible Astra tasks. The PDF reports successful tool-assisted cases; their complete physical/workflow certification was not re-audited here.

Suggested summary wording: "Astra abstained on all 10 no-tool frame task variants tested (five layouts), while separate single-attempt CAD-edit and hydraulic errors were observed. These results do not establish persistent failure of tool-assisted 3D CAD-to-FEM workflows."
