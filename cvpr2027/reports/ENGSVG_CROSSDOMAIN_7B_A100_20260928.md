# Cross-domain SVG patcher: 7B A100 result

The downloaded Colab run in `../engsvg-crossdomain-7b-a100-run-artifacts/` completed on 28 September 2026. It trained `Qwen/Qwen2.5-Coder-7B-Instruct` (revision `c03e6d358207e414f1eca0bb1891e29f1db0e242`) for one epoch on 8,000 source-lineage-disjoint examples. The A100-SXM4-40GB completed 500 optimizer steps in 2,862 seconds (47.7 minutes). The evaluation used 100 balanced examples drawn from the 1,000-row held-out test split, with greedy decoding and exact normalized target-tree equality after applying the predicted patch.

| Metric | Base | Trained |
|---|---:|---:|
| Strict JSON | 0/100 | 100/100 |
| Valid patch | 0/100 | 100/100 |
| Exact patch | 0/100 | 59/100 |
| Target tree equal | 0/100 | 59/100 |
| Reference integrity | 0/100 | 100/100 |

| Family | Target tree equal |
|---|---:|
| Building plans | 4/20 |
| DC circuits | 20/20 |
| Furniture tables | 6/20 |
| Mechanical parts | 9/20 |
| Water piping | 20/20 |

The saved base and trained prediction files each contain 100 records with identical, unique IDs, all present in the held-out test split. Local rescoring of all trained predictions reproduced every stored JSON-valid, patch-valid, exact-patch, target-tree, and reference-integrity flag (zero mismatches). The final adapter and step-500 checkpoint have identical 40,400,200-byte safetensors files with SHA-256 `627b661e182c526a14ef9bde1d41de14125b426d02d4673d8dd99f5dfef32084`.

This run reports exact SVG tree matching, not physics equality: all 100 saved `physics_equal` fields are null. It covers 100 of 1,000 held-out cross-domain edits. These results are separate from the circuit-and-pipe network paper's 7B ID-addressed editor and must not be inserted into that paper's 7B rows.

## Additional drawing and verifier audit

`scripts/score_crossdomain_drawing.py` recovers family parameters from the produced SVG, reruns the procedural verifier, and checks whether the drawing matches the recovered model, allowing only small numeric formatting differences. Recovery was checked against all 1,000 gold test drawings before scoring predictions. On the original 100 predictions, it found 83/100 parameter-model matches, 64/100 internally consistent drawings, and 60/100 that met both criteria. The latter is one higher than exact tree equality because one consistent output differed only in numeric serialization. The full verifier report matched in 83/100, while the verifier's safe/violation Boolean matched in all 100; that Boolean alone is therefore too coarse to use as a success metric.

The failures are concentrated in geometry. Among the first 100, the recovered incorrect fields were `leg_inset_mm` (9), `leg_width_mm` (9), `partition_x_mm` (8), and `door_x_mm` (2). For mechanical parts, all 20 dimension-note parameter sets matched, but 11 drawings disagreed with the corresponding geometry. This explains why reading annotations alone overstates success. The circuit and pipe families were 20/20 on both model recovery and drawing consistency in this 100-example pilot. These checks still evaluate a synthetic, idealized drawing grammar; they are not an independent real-world engineering certification.

A direct comparison of failed SVGs shows the most frequent mismatches in table leg `x`, `y`, `width`, and `height` attributes; building-plan errors recur in the partition line, door leaf and swing path, and room-label positions. A useful next model change is to predict the edited design parameters once and rerender all dependent geometry, or to validate every linked shape after patch application. The current patch generator asks the model to reproduce multiple coupled floating-point coordinates independently.

The same Colab A100 notebook now contains a resumable full-test cell. It reuses the 100 recorded predictions and evaluates the remaining 900 in 25-example chunks, then writes combined predictions, metrics, and a run manifest. The complete results belong in this report after the Colab run finishes and its artifacts are downloaded.
