# Cross-domain engineering SVG edit dataset v1

Every row contains a complete source SVG, edit instruction, complete target SVG, gold tree patch, source/target parametric models and deterministic before/after verification. Splits are assigned by source lineage, so four edits of one drawing never cross train, validation and test.

Families: building plans, furniture tables, machined parts, DC circuits and water piping. Open `samples/` for ordinary SVG files, raster PNG previews and their records.

Training objective: `source SVG + instruction -> target_patch`. Apply the prediction with the generic executor, parse the result again and run the family verifier before accepting it.
