# Circuit and pipe-network SVG edit dataset v1

Resistor networks (bridges, ladders, one or two sources) and looped water-distribution networks (one or two reservoirs, tees, elbows, dead ends), each with four text-guided edits. Every row has the source SVG, instruction, target SVG, a gold patch that reproduces the target exactly, and before/after engineering reports.

The reports are computed from the drawings, not from parameters: `scripts/engsvg_networks.py` reads wire and pipe endpoints, T-junctions and junction dots into nodes, reads component values from the labels, and solves the result (nodal analysis for circuits; Newton on flows and heads with Darcy-Weisbach/Churchill losses for pipes, cross-checked by Hardy Cross). A row is kept only if both drawings recover to the model they were drawn from.

Score a model's patch with `engsvg_networks.physics_match(edited_svg, family, target_model)`: a drawing that differs in markup but describes the same network still scores as correct.
