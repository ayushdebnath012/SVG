# Verified SVG-to-SVG engineering edits

**1 October update:** the [current paper and example overview](ENGINEERING_EDITOR_OVERVIEW_20261001.md) incorporate this pipeline, with five re-imported edit examples. In the historical records below, `verified_safe` denotes the applicable checker pass; for trusses this is FEM equilibrium, not a material-strength or buckling certificate.

Date: 25 September 2026

## Implemented pipeline

```text
source SVG
  -> recover visible geometry and annotations into EngSVG IR
  -> parse a bounded edit request with explicit arithmetic
  -> create the intended engineering revision
  -> render the intended SVG
  -> derive the smallest tree patch
  -> serialize, parse and policy-check the patch
  -> apply the patch to the original SVG
  -> import the actual patched SVG again
  -> run the applicable engineering check on that recovered result
```

The final check uses the drawing actually produced, not the intended model kept in memory.

For trusses, the checker assembles and solves a linear axial finite-element model, reports member stress and displacement, and checks global equilibrium. For perforated plates, it checks boundary crossing, hole overlap, minimum edge distance, minimum ligament, net area and volume. These plate checks are manufacturing-geometry checks, not plate-stress FEM.

**Current implementation, 1 October:** the former panel-count regeneration path has been replaced by a parsed version-3 structural patch applied to the original SVG, followed by re-import and FEM. The 21-to-29-member example uses 53 operations including 16 insertions. The regeneration description below records the September implementation.

## Patch boundary

Parametric edits preserve the SVG element topology and use tree patches. Supported examples include load changes, section breadth/depth, material modulus, span/height, plate thickness, hole diameter and hole offset. The patch is serialized to JSON, parsed, policy-validated and applied before verification.

A panel-count edit changes the node/member graph. The current patch derivation cannot prove connectivity when adding elements, so these edits are routed to deterministic regeneration and then re-imported and solved. This prevents the previously observed singular partial patch.

## Full dataset audit

All 40,000 SVG-to-SVG rows in `engsvg-dataset-factory-v2` were streamed through the complete pipeline.

| Result | Count |
|---|---:|
| Patch/parser exceptions | 0 |
| Applied SVG exactly equals stored target tree | 40,000 / 40,000 |
| Edit-fidelity pass after re-import | 40,000 / 40,000 |
| Engineering check pass | 39,301 / 40,000 |
| Faithful edits with engineering violations | 699 / 40,000 |

All 20,008 truss edits passed FEM equilibrium. Of 19,992 plate edits, 19,293 passed the manufacturing criteria and 699 enlarged holes enough to violate the stated minimum edge-distance or ligament rule. Those 699 are correctly drawn but should be labelled unsafe or removed from a safety-filtered training split.

## Saved examples

The saved run contains three patch examples and one topology-regeneration example:

- a section-depth edit halves the recovered truss peak stress from 11.86094 to 5.93047 MPa;
- a six-hole plate diameter edit updates the circles and annotation and passes edge/ligament checks;
- doubling a bridge load doubles peak stress from 84.375 to 168.75 MPa;
- changing a Pratt bridge from six to eight panels regenerates the connected topology and passes FEM.

## Generic SVG-tree layer

A separate domain-independent layer now parses arbitrary safe SVGs into a scene graph, establishes source-target node correspondence and derives version 3 structural patches. It supports subtree insertion and complete path/polyline geometry replacement in addition to attribute, text and deletion operations. Building-plan, table, mechanical-part, circuit and piping examples all reproduced the target SVG tree exactly; no saved output had a dangling local reference or duplicate XML ID.

This makes parsing and editing reusable beyond trusses. The physics layer remains family-specific: additional drawing families require a semantic importer and an applicable verifier such as frame FEM, plate/shell FEM, buckling, thermal conduction, fluid-flow conservation, circuit analysis or machine-element checks. See `GENERIC_ENGINEERING_SVG_TREE_20260925.md` for the architecture, tests and current limits.
