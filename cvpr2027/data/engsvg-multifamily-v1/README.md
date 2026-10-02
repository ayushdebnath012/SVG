# EngSVG multi-family benchmark v1

This frozen benchmark contains:

- 30 detached SVG recovery cases: 15 transformed trusses and 15 transformed mechanical plates.
- 100 held-out natural-language edit requests: 50 truss and 50 plate edits.
- Authored and recovered common-IR records for every recovery drawing.
- Deterministic FEM or geometry/manufacturing verification attached to each recovered case.

The recovery cases are generated from distinct parameter combinations and are not training examples. All 30 authored/recovered engineering hashes match. Edit records include the source hash, request, expected structured action, complete target IR and target hash; model scores have not yet been added.

The benchmark remains synthetic and covers two object families. It is designed as a reproducible foundation for later model and Astra evaluation, not as evidence of broad real-world CAD performance.
