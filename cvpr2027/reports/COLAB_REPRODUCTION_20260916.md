# Colab A100 reproduction batch, 2026-09-16

One Colab A100 session executed the full compute batch prepared in
[REMOTE_COMPUTE.md](REMOTE_COMPUTE.md) against repository commit
`cb3ab448ea0bca1e0c7b43db3a9e1d7f24270f1a`. All nine stages returned zero and
the run finished at 12:42:02 UTC, 15.6 minutes after the cell started. The
browser download `results-20260916T122720Z.tar.gz` (63,149,333 bytes, SHA-256
`e9be960f7a774c6cf6965ae0072a118856a91be45bdb0dbfb1be070e87ebd61a`) matches
the checksum printed in the notebook (executed copy with outputs, account
metadata removed: `notebooks/SVG_Colab_FEM_LoRA_20260916_executed.ipynb`); its contents are versioned in
`runs/colab-a100-20260916/` and the archive itself is kept as a local ignored
file. Hardware: NVIDIA A100-SXM4-40GB, `torch==2.11.0+cu128`,
`transformers==4.51.3`, `peft==0.15.2`, `scikit-fem==12.0.2`; the complete
package list is `runs/colab-a100-20260916/packages.txt`.

| Stage | Result | Wall time |
|---|---|---:|
| Regression tests | 30 passed | 20 s |
| Saved-adapter inference reload (`runs/a100`) | 18/18 exact actions, 0 unsafe edits | 60 s |
| LoRA training, seed 17 | 90 steps, train loss 0.008447, eval loss 6e-5 | 220 s |
| LoRA training, seed 29 | 90 steps, train loss 0.008168, eval loss 6e-5 | 240 s |
| LoRA training, seed 41 | 90 steps, train loss 0.010503, eval loss 1.1e-4 | 220 s |
| New-adapter inference reload | 18/18 exact actions, 0 unsafe edits | 40 s |
| FEM-Bench axial bar | 2 upstream tests, 24 solves, analytic error ≤ 5.3e-18 m, force balance ≤ 4.1e-14 | 20 s |
| Robin heat conduction, n = 12…192 | heat balance ≤ 3.4e-12, outflow/k 260.816 → 259.918 | 40 s |
| Deterministic rule baseline | 60/60 test, 60/60 held-out family | 20 s |

Stage times are rounded up by the 20-second polling loop; training-only time
inside each seed was 95.1, 97.1 and 93.8 seconds. Peak GPU memory was 6.93 GB.

## Agreement with the saved artifacts

`scripts/compare_reproduction.py` compares this batch with the run recorded in
[TRAINING_RESULTS.md](TRAINING_RESULTS.md) and the saved numerical references;
its output is `reports/colab_reproduction.json`.

- The three new `adapter_model.safetensors` files are byte-identical to
  `runs/a100/seed-*/adapter/adapter_model.safetensors` (same SHA-256,
  17,462,432 bytes, 4,358,144 parameters each).
- All 720 raw base and final predictions are identical to the saved run; only
  the `batch_seconds` timing field differs.
- Data split hashes, trainer loss histories and run manifests are identical
  apart from timing fields.
- The FEM-Bench bar summary agrees to a maximum absolute gap of 6.3e-16 m;
  solution identifiers differ because they hash roundoff-level floats.
- The Robin reference agrees to a maximum absolute gap of 5.2e-10 °C across
  the five meshes, the mesh-difference estimates and the historical
  finite-difference comparison.

Training on this stack is therefore deterministic across two separate A100
sessions. The inference reload check, which was prepared but unexecuted when
the earlier session disconnected, has now run twice: once on the versioned
`runs/a100` adapters and once on the freshly trained adapters. Both passed all
eighteen held-out actions.

## What this does and does not establish

This is a pipeline reproduction on the existing shared-template pilot, with
ten independent physical cases per evaluation split. Identical outputs do not
add independent test cases, and the perfect deterministic rule baseline still
means the result validates the pipeline rather than showing that learning is
needed. The main well-posed benchmark, published solver-agent comparison and
multimodal contribution listed in `RUN_INDEX.json` remain outstanding.

The Serveo SSH host `iit@sn4622130673` was probed again on 2026-09-16 with an
empty password; the server answered `Permission denied (publickey,password)`,
so that host still requires an interactive login before
`scripts/remote_compute.py launch` can be used for future heavier jobs.

Recheck from `cvpr2027/`:

```sh
../.venv/bin/python scripts/summarize_training.py --runs runs/colab-a100-20260916/training --output reports/colab_training_verified.json
../.venv/bin/python scripts/compare_reproduction.py --new runs/colab-a100-20260916 \
    --saved-training runs/a100 --saved-fem runs/fem-bench-svg-anchor/summary.json \
    --saved-robin runs/robin-fem-reference/summary.json --output reports/colab_reproduction.json
```
