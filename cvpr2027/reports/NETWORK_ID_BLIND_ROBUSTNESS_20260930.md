# Opaque SVG ID transfer control (2026-09-30)

## Question

Does the saved 7B id-addressed network editor still edit correctly when SVG `id`
attributes no longer contain component names? This tests the editor, not the
drawing-grounded verifier.

## Controlled input

- Base set: all 400 examples in `data/engsvg-network-edit-hard-v1/test.jsonl.gz`
  (200 circuit, 200 pipe).
- `scripts/network_id_robustness.py` replaces every source and target SVG `id`
  with a consistent, unique, opaque `eNNNN` token per example (seed 20270930).
  All other SVG bytes, including visible geometry and labels, are unchanged.
  Instructions and physical target models are unchanged.
- Gold patches were re-derived and verified. All 400 apply to their new sources,
  reproduce their targets, and recover and solve to the same target physics.
- Generated set: `data/engsvg-network-id-blind-hard-v1/test.jsonl.gz`;
  uncompressed SHA-256
  `9d8c8ed26cf9468791cd855f4fadc28c9f81496fcdfc46e7e6d4c5d7fbea563c`.
  The server input had the same uncompressed hash. The local gzip is deterministic
  (`mtime=0`), with SHA-256
  `897c26fdc02538c46ba7ba20b6184cf9d320fd38aaa289d31470bc0ca8aa5082`.

## Model and run

The saved Qwen2.5-Coder-7B-Instruct LoRA editor from
`runs/remote-network-h100-20260930/net-ids-qwen-coder-7b` was evaluated without
retraining, using `scripts/eval_patcher.py` with greedy decoding and batch size
8 on server `10.71.9.40` (H100 GPU 0). Model revision:
`c03e6d358207e414f1eca0bb1891e29f1db0e242`. The run completed at
2026-09-30 17:24:35 UTC. Downloaded predictions, metrics, and summary are in
`runs/network-id-blind-7b-20260930/`.

The same predictions were independently rescored locally with
`network_paper_results.ours(..., address="ids")`, the end-to-end scorer used by
the paper. Its edit and end-to-end counts both match the run's physics score.

| Hard tier | Original IDs | Opaque IDs |
|---|---:|---:|
| Circuit correct | 200/200 | 67/200 |
| Pipe correct | 198/200 | 87/200 |
| All correct | 398/400 (99.5%) | 154/400 (38.5%) |
| Valid patch | 400/400 | 334/400 |
| Valid JSON | 400/400 | 378/400 |

The largest drops occur for edits requiring removal or insertion: add pipe
39/41 to 0/41, parallel branch 50/50 to 0/50, remove pipe 50/50 to 0/50,
open branch 32/32 to 1/32, and polarity reversal 18/18 to 0/18. Diameter
changes remain 47/50 and pipe length changes 9/9.

## Interpretation

This is a zero-shot transfer test on an editor trained with meaningful SVG IDs.
It shows that the reported 99.5% hard-tier result depends strongly on the ID
naming distribution. It does not test a model trained with opaque IDs or an
editor that canonicalizes IDs before inference. The verifier's ID invariance is
not contradicted: every transformed gold drawing and patch passed the physical
check, and predicted edits were scored from the visible output drawing.
