# EngSVG dataset v2 audit

Date: 25 September 2026

## What changed

The earlier structured pilot trained a model to emit short JSON actions. It contained no SVG input or SVG target. This new dataset is a separate artifact built for direct drawing generation, drawing editing, drawing recovery and engineering analysis.

Each drawing is stored as real SVG XML. The task records embed the complete `<svg>...</svg>` string directly; they do not merely point to a filename or asset ID.

## Contents

| Item | Count |
|---|---:|
| Source engineering designs | 10,000 |
| SVG renderings stored with assets | 30,000 |
| Total task rows | 140,000 |
| Rows with a complete SVG in the prompt | 130,000 |
| Rows whose target is a complete SVG | 50,000 |
| Text-to-SVG rows | 10,000 |
| SVG-to-SVG edit rows | 40,000 |
| SVG-to-IR recovery rows | 10,000 |
| Engineering-analysis rows | 10,000 |
| Structured edit-action rows | 40,000 |
| Constrained-edit rows | 10,000 |
| Clarification rows | 10,000 |
| Rejection rows | 10,000 |

The source families are two truss topologies and two perforated-plate layouts. Each source design has canonical, monochrome and blueprint SVG styles. Sixteen unpacked sample SVG files and `sample-gallery.html` allow direct visual inspection.

## Verification

The complete generated dataset was streamed and checked row by row:

- all 53 manifest entries match their SHA-256 digest;
- all 10,000 canonical drawings round-trip through the bounded SVG importer;
- all 10,000 source designs pass their stated FEM equilibrium or manufacturing-geometry check;
- all 130,000 SVG prompts contain parseable SVG XML;
- all 50,000 SVG targets contain parseable standalone SVG XML;
- every lineage has exactly 14 tasks and occurs in only one split;
- the split contains 8,000 training, 1,000 validation and 1,000 test designs;
- none of the 10,000 engineering hashes overlaps the 2,030 excluded hashes from the frozen benchmark and earlier training set.

A later end-to-end SVG-edit audit reproduced all 40,000 stored SVG targets exactly after parsing, JSON patch round-trip, policy validation, application and re-import. All 20,008 truss revisions passed axial FEM equilibrium. Of 19,992 plate revisions, 699 faithfully applied hole edits violated the stated minimum edge-distance or ligament criteria. Keep their `target_verification.pass=false` labels for unsafe-design training, or exclude them from a safety-filtered generator split.

## Claim boundary

This is scalable procedural data, not evidence of broad real-world CAD coverage. It covers trusses and rectangular perforated plates. It does not yet contain buildings, furniture, multiview machine drawings, curves, arbitrary CAD imports or human-authored editing histories. Physics labels come from deterministic solvers and geometry checks. The current Colab LoRA run uses the earlier JSON-action dataset; a separate SVG-sequence run is required to measure this dataset.
