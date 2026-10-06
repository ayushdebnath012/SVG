# Completed multi-source Colab CAD training — 2026-10-02

The supplied `multisource-cad-colab-results.zip` is a valid earlier export: training and geometry evaluation are complete, but its FEM summary contains only four records. It remains unchanged. `multisource-cad-colab-results-final.zip` is the later six-case export. Both contain the same adapter and predictions.

Fresh Qwen2.5-Coder-3B-Instruct, pinned revision `488639f1ff808d1d3d0ba301aef8c11461451ec5`, trained on Colab Tesla T4 for two epochs / 1,270 optimizer updates. Train/validation/test: 2,540/172/252. BenchCAD: 492/44/124; CAD-Editor: 2,048/128/128. NF4 double quantization; rank 16, alpha 320; last 12 blocks; effective batch 4; completion-only loss. Training runtime: 20,923.71 seconds; mean loss: 0.249468. The saved manifest records torch.bfloat16 computation on T4; native hardware BF16 acceleration is not established. Do not replace this provenance with a claimed FP16 run.

| Model | Applicable patches | Executed solids | IoU ≥ 0.95 | IoU ≥ 0.99999 |
|---|---:|---:|---:|---:|
| Fresh base | 39/252 | 7/252 | 2/252 | 1/252 |
| Final adapter | 173/252 | 139/252 | 52/252 | 39/252 (15.48%) |
| Final, BenchCAD | 91/124 | 65/124 | 32/124 | 25/124 (20.16%) |
| Final, CAD-Editor | 82/128 | 74/128 | 20/128 | 14/128 (10.94%) |

All held-out tasks remain in these denominators. Six target-reference errors and one final-model worker timeout are retained. The scorer's reference_valid count is 246 for base and 245 for final because the whole-worker timeout also prevents reference bookkeeping. It is not a model-independent validity denominator. BenchCAD uses released STEP references; CAD-Editor targets are locally reconstructed native sequences. This is a bounded local pilot, not either official leaderboard. Exact sequence components are isolated within source; cross-source equivalent geometry is not proven absent.

## Six-case new-adapter FEM audit

| Case | Audit status | Combined geometry/response pass | Compliance discrepancy (%) |
|---|---|---|---:|
| mounting_angle_box_x_f130 | completed | yes | 0.001123 |
| locator_block_box_y_f130 | completed | yes | 0.046691 |
| t3medplus_stepped_shaft_rot_diag60 | completed | yes | 0.009141 |
| propeller_bore_widen_compute | not_verified_invalid_patch | unverified | — |
| t5hard_pan_head_screw_U_a | not_verified_pipeline_failure | unverified | — |
| t5hard_round_flange_V_a | completed | yes | 0.013270 |

Four cases have saved prediction/target meshes and displacement/stress fields with numerical and compliance sensitivity checks. The propeller patch fails syntax validation. The original screw attempt left an incomplete output directory; resumption recorded pipeline failure rather than a solver result. The original cause is not established by saved solver evidence. No screw FEM pass is claimed.

Physical assumptions are diagnostic: mm/N/MPa, E=210,000 MPa, nu=0.3, total load 1 N, geometric end-band fixtures. FEM is external post-edit verification, not a training loss/reward. No operational safety or stress-convergence claim; the full 252-case benchmark lacks physical specifications. The older 1.5B H100 FEM audit remains separate.

## Artifact verification

- `multisource-cad-colab-results.zip`: ZIP CRC passed; 127 entries; SHA256 `ec70592280d7397944ca33d417d75b66d9b1d988324994ef88e7b6b8f1644017`.
- `multisource-cad-colab-results (1).zip`: ZIP CRC passed; 158 entries; SHA256 `693e38ea5bc5b62f05d22814b02f79d1bb5f9b8be0996bcec99723699c45f2b9`.

Adapter SHA256 `17ae7682e7a53a0ee063cf19b3adde3c7fb2314d5fedfbfeb9b3bb4e2a74433d` matches both manifests. All 168 tensors / 9,977,856 scalars are finite. Both prediction files contain 252 distinct IDs. Machine-readable checks: `runs/multisource-cad-colab-20261002/archive-check.json`.
