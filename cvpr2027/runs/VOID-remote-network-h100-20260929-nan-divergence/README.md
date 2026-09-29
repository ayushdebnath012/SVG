# VOID: 7B network editor, H100 NVL, 2026-09-29 — training diverged

Loss 0.727 (step 10) -> 0.647 (step 20) -> 30287.85 with grad_norm NaN (step 30), NaN thereafter.
The saved adapter decodes to '!!!!…' and scores 0/1000 and 0/400. This is a broken run, not a
result, and must never be cited or fed to the paper tables.

The untrained-model (base) predictions in this directory are valid: they were produced before any
training step with the unmodified base weights.

Same code and settings trained cleanly on the RTX PRO 6000 Blackwell host. Diagnosis and the rerun
are recorded in the commit that follows this one.

## Diagnosis (2026-09-30)

Two 50-step trials with identical code, settings and data order (`trials/`):

| SDPA cuDNN kernel | outcome |
|---|---|
| disabled (`--disable-cudnn-attention`) | 50 steps, loss 0.555 -> 0.026, all gradient norms finite |
| enabled (as in the void run) | non-finite gradient norm at step 30, the same step as the void run |

The rerun uses `--disable-cudnn-attention`; the trainer now also stops at the first non-finite loss
or gradient norm instead of training a NaN model to completion.
