# Astra failure search — 2026-10-15

Re-scored existing hosted v1.5 submissions locally; no new model calls made. Six valid completed tasks pass their numerical targets, with successful recorded sandbox replays. This is not equivalent to human-reviewed full workflow certification. CADWORLD-001 is excluded because the prompt specified the wrong element order (see hosted-v1.5/SPEND.md). Wyk ring remains in progress at inspection; intermediate debugging crashes are not final failures.

## Historical CAD-editing failure examples

These are saved vanilla-draft failures in a different protocol, not demonstrated failures of the current CAD+FEM numerical benchmark. Original published FEM labels and admission suitability must be audited before including these as benchmark tasks. Selection is retrospective and does not estimate an overall failure rate.

| ID | Task | Observed failure | Saved geometry overlap |
|---|---|---|---|
| d000c8c09d558154 | Add a 16 mm diameter, 3 mm thick boss above a propeller hub | Invalid Python patch; saved check reports IndentationError; FEM not executed | No valid solid |
| b61bd7f12f1b5e94 | Drill four 4 mm holes through a connecting rod | Saved vanilla code drills along Y using the XZ workplane; historical audit identifies required direction as Z | Volume IoU 0.931831 |
| 277d8aa207505807 | Make twisted-bracket flange lengths twice their width while preserving end-relative hole positions | Dependent positions/hole offsets incorrectly propagated in the saved draft | Volume IoU 0.575084 |

The connecting-rod and bracket drafts pass basic geometry/FEM execution gates despite incorrect edits. This demonstrates why execution alone does not verify task semantics. The propeller draft fails before FEM. No claim is made that all attempts or stronger reasoning settings fail these tasks.

Evidence and exact saved candidate code are indexed in cases.json. The historical cases.json audit also contains rounding/reference defects and ambiguous instructions; these were not included in this shortlist. SFEM and reference-generation access-check runs produced no predictions and are not capability failures.
