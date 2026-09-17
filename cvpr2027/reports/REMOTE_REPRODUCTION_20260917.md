# Remote Blackwell reproduction batch, 2026-09-17

The packaged compute batch was run a third time, on the user-supplied Serveo SSH
host `iit@sn4622130673` (see [REMOTE_COMPUTE.md](REMOTE_COMPUTE.md)), which is a
different GPU architecture from the two earlier A100 runs. All nine stages
passed. Artifacts are versioned in `runs/blackwell-20260917/`; the fetched
archive (63,538,025 bytes) is kept locally as `runs/blackwell-20260917.tar.gz`,
and intermediate optimizer checkpoints remain on the host under
`svg-compute/20260917T153529557690Z/`.

Host: Ubuntu 24.04, 48 CPU threads, 251 GB RAM, one NVIDIA RTX PRO 6000
Blackwell Workstation Edition (97,887 MiB; compute capability 12.0), driver
580.105.08. Stack: Python 3.12.3, `torch==2.11.0+cu130`, `transformers==4.51.3`,
`peft==0.15.2`, `accelerate==1.6.0`, `scikit-fem==12.0.2`, `numpy==2.4.6`; the
complete list is `runs/blackwell-20260917/training/seed-17/packages.txt`. Source
bundle SHA-256 `c46f0017…`, uploaded and checksum-verified by
`scripts/remote_compute.py launch --gpu 0`.

## First attempt and fix

The bootstrap installed the current default `torch==2.14.0+cu130`. Its CPU
stages passed, but the first GPU stage failed inside Triton: torch 2.14 routes
some matmuls through Triton kernels, and Triton compiles a small C helper
against `Python.h` on first use. The host's minimal system Python has no
`python3-dev` headers (nor `ensurepip`/`pip`), so `gcc` failed with
`fatal error: Python.h: No such file or directory`
(`runs/blackwell-20260917/logs/saved-adapter-reload.log`, first section).

Rather than install system packages on the host, torch was pinned to `2.11.0`
— the version of both recorded A100 runs — in `scripts/bootstrap_remote.sh`,
installed into the existing virtual environment, and the batch was resumed with
`remote_batch.py --resume`, which skipped the four completed CPU stages.
`bootstrap_remote.sh` also now creates the virtual environment without pip and
bootstraps pip from PyPA when `ensurepip` is missing. Both logs are retained:
`launch.log` (first attempt) and `launch-resume.log`.

| Stage | Result | Wall time |
|---|---|---:|
| Regression tests | 30 passed | 0.3 s |
| FEM-Bench axial bar | 2 upstream tests, 24 solves; analytic error ≤ 5.3e-18 m, force balance ≤ 4.1e-14 | 0.1 s |
| Robin heat conduction, n = 12…192 | heat balance ≤ 3.4e-12; finest mesh solve 5.2 s (48 threads) | 7.6 s |
| Deterministic rule baseline | 60/60 test, 60/60 held-out family | 0.1 s |
| Saved-adapter inference reload (`runs/a100`) | 18/18 exact actions, 0 unsafe edits | 8.4 s |
| LoRA training, seed 17 | 90 steps; train loss 0.008446; 60/60 test, 60/60 OOD | 65.8 s |
| LoRA training, seed 29 | 90 steps; train loss 0.008165; 60/60 test, 60/60 OOD | 63.1 s |
| LoRA training, seed 41 | 90 steps; train loss 0.010510; 60/60 test, 60/60 OOD | 65.0 s |
| New-adapter inference reload | 18/18 exact actions, 0 unsafe edits | 8.2 s |

Training-only time inside each seed was 35.2, 34.4 and 35.8 seconds (A100:
95.1, 97.1, 93.8 s); the stage wall times include base and final evaluation.
Peak GPU memory was 6.93 GB, as on the A100. Reload stage times exclude the
one-off base-model download, which happened during the failed first attempt.

## Agreement with the saved A100 artifacts

`scripts/compare_reproduction.py` now reports two levels. Bitwise agreement
(adapter bytes, every prediction, loss history) is what the same-architecture
Colab run achieved. Across architectures, CUDA kernels round differently, so
weights are not expected to match bit for bit; the question is whether the
learned policy's behaviour changes. Output: `reports/blackwell_reproduction.json`
(`functionally_equivalent: true`, `all_identical_or_within_tolerance: false`).

- Every one of the 360 final-model predictions (120 per seed over test and
  held-out splits) is identical to the A100 run, and every score is 60/60.
- Adapter weights differ slightly: mean |Δw| 1.44e-4, 1.41e-4 and 1.80e-4 and
  maximum |Δw| 5.9e-3, 6.3e-3 and 5.9e-3 against a maximum |w| of about 3.1e-2;
  the minimum per-tensor cosine similarity to the A100 adapter is 0.9745,
  0.9827 and 0.9719 for seeds 17, 29 and 41.
- Final train losses 0.008446 / 0.008165 / 0.010510 versus 0.008447 / 0.008168 /
  0.010503 on the A100.
- Base-model (untrained) outputs differ in exactly 1 of 120 generations per seed;
  base strict and fence-normalised scores are unchanged (0/60 strict; 26/60 and
  25/60 fence-normalised).
- Data split hashes are identical. The FEM-Bench summary agrees to 6.3e-16 m and
  the Robin reference to 5.2e-10 °C, the same gaps as the Colab run.
- `reports/blackwell_training_verified.json` records the `summarize_training.py`
  verification (adapter structure, 720 rescored predictions, split hashes).

## Interpretation

The pilot's outcome is independent of the GPU vendor generation and of the
CUDA 12.8 versus 13.0 runtime: three hardware sessions (A100 twice, Blackwell
once) produce the same 60/60 policies and the same predictions. The
architecture-dependent weight differences are of the size expected from
non-associative floating-point accumulation over 90 optimizer steps and do not
change any decision on this task. As before, this validates the pipeline and
the packaging; it does not add independent test cases, and the perfect
deterministic rule baseline still means it establishes no learned advantage.

The host is now a working target for jobs longer than a Colab session. The
Serveo tunnel and password login are the only access path; the password is not
stored in this repository.

Recheck from `cvpr2027/`:

```sh
../.venv/bin/python scripts/summarize_training.py --runs runs/blackwell-20260917/training --output reports/blackwell_training_verified.json
../.venv/bin/python scripts/compare_reproduction.py --new runs/blackwell-20260917 \
    --saved-training runs/a100 --saved-fem runs/fem-bench-svg-anchor/summary.json \
    --saved-robin runs/robin-fem-reference/summary.json --output reports/blackwell_reproduction.json
```
