# Remote compute batch

## Colab execution

The Colab batch completed on 2026-09-16 at 12:42 UTC; every stage passed and
the downloaded archive is unpacked in `runs/colab-a100-20260916/`. See
[the reproduction report](COLAB_REPRODUCTION_20260916.md) for results and
agreement checks. The runtime has been released; the notes below describe
how to rerun the same batch.

[The live run notebook](https://colab.research.google.com/drive/1rU8GcBO42E8GRq6FkhC0PVR-CPfcwtV2)
is configured for an A100. The local copy is
`notebooks/SVG_Colab_FEM_LoRA_20260916.ipynb`; its code is also available in
`scripts/colab_run.py`. Run the single code cell. It downloads repository
commit `cb3ab448ea0bca1e0c7b43db3a9e1d7f24270f1a`, installs the recorded
dependencies, checks the saved adapters, trains three seeds, checks the new
adapters, and runs the numerical references and rule baseline.

The cell displays the active stage and recent log output. Results are stored
under `/content/svg-colab-cb3ab448ea/results-<UTC timestamp>`. At completion,
an archive containing final adapters, predictions, logs, FEM fields and the
summary downloads through the browser. Download before the Colab runtime is
released; `/content` is temporary storage. Rerunning the cell in the same
runtime skips successful stages and resumes saved training checkpoints.

## Earlier SSH preparation

Prepared on 2026-09-16 for `iit@sn4622130673` through Serveo; authenticated and
launched on 2026-09-17 once the account password was supplied out of band (it is
never stored in this repository). Verified hardware: Ubuntu 24.04 (kernel 6.8),
48 CPU threads, 251 GB RAM, 3.4 TB free NVMe, one NVIDIA RTX PRO 6000 Blackwell
Workstation Edition (97,887 MiB), driver 580.105.08 / CUDA 13.0, Python 3.12.3
without `ensurepip` or `pip`. A desktop session holds about 2 GB on the only
GPU, so the idle-device heuristic in `remote_batch.py` would refuse it: launch
with `remote_compute.py launch --gpu 0`. `bootstrap_remote.sh` now creates the
virtual environment without pip and bootstraps pip from PyPA when the system
Python lacks `ensurepip`; no system package is installed.

Batch `svg-compute/20260917T153529557690Z` (bundle SHA-256 `c46f0017…`) was
launched on 2026-09-17 at 15:35 UTC and completed at 15:53 UTC after one
resume (torch pinned to 2.11.0; see [the remote reproduction
report](REMOTE_REPRODUCTION_20260917.md)). All nine stages passed; the
fetched results are versioned in `runs/blackwell-20260917/`.

From the repository root, authenticate once in an interactive terminal:

```sh
.venv/bin/python cvpr2027/scripts/remote_compute.py connect
# Alternatively, add --identity /absolute/path/to/authorized_private_key
.venv/bin/python cvpr2027/scripts/remote_compute.py launch --gpu 0
.venv/bin/python cvpr2027/scripts/remote_compute.py status
.venv/bin/python cvpr2027/scripts/remote_compute.py fetch
```

The bundle is already prepared; its location, SHA-256 and remote destination
are in `cvpr2027/tmp/remote-compute/latest.json`. Run `remote_compute.py prepare`
again after changing source files. Authentication uses an SSH control socket;
passwords and keys are never put in the bundle. The relay intentionally allows
interactive authentication because forcing batch mode caused the relay to
reject this connection. An ordinary SSH login in a different terminal does
not establish this helper's control socket; use the `connect` command above.

The launcher uploads an isolated copy, verifies the archive checksum, creates
a remote virtual environment, and starts the job with `nohup`. No API keys or
hosted-model calls are needed. Model weights and Python packages are downloaded
on the remote machine. Allow approximately 10 GB of disk for packages, model
weights, adapters and checkpoints. CUDA and a compatible NVIDIA driver are
required. The default GPU selection requires an idle device with at least
12 GB free. Bootstrap or runtime failures are recorded in the remote log;
`launch` only means the background process was started, not that training passed.

The stages are:

1. Evaluator and edit-policy regression tests.
2. Twenty-four FEM-Bench axial-bar solves, including physical load edits.
3. Robin heat-conduction FEM meshes at n=12, 24, 48, 96 and 192, with an
   analytical anchor, heat-balance checks and mesh-difference estimates.
4. Deterministic rule baseline on 60 test and 60 held-out-family examples.
5. Fresh inference reload of the three saved adapters: 18 action checks.
6. Three new Qwen2.5-Coder-1.5B LoRA runs, seeds 17/29/41, three epochs each,
   saving base/final predictions, validation loss, adapters and checkpoints.
7. Fresh inference reload of the three new adapters: 18 action checks.

Results live in the isolated remote `cvpr2027/results` folder: `status.json`,
`summary.json`, stage logs, FEM solutions and drawings, and training artifacts.
`fetch` downloads an archive without intermediate optimizer checkpoints;
those remain available on the remote host. Fetch after completion for a
consistent final snapshot. Historical project evidence is preserved.

To resume a failed batch on the remote host, enter its isolated `cvpr2027`
directory and run the following under `nohup` or a terminal multiplexer:

```sh
.venv-remote/bin/python scripts/remote_batch.py --output results --resume
```

Resume skips successful stages and checks source/data hashes. Training uses
the last saved optimizer checkpoint where available. A lock prevents concurrent
batch runners from sharing the same output directory. `--cpu-only` runs the
numerical stages alone; use a separate output directory. `--dry-run` prints the
commands without creating results.

Local preparation evidence is under `cvpr2027/tmp/remote-preparation`:
30 original regression tests passed; 24 actual FEM solves and both upstream
reference tests passed; maximum analytical displacement error was
1.952e-18 m and maximum relative force-balance error was 4.137e-14.
The rule baseline scored 60/60 on each evaluation split.
Three additional runner tests passed for failure recovery, rejecting changed
source on resume, and keeping dry runs free of result writes (33 tests total).

These are pipeline reproductions on the existing shared-template pilot.
They do not establish a learned advantage or complete the planned main
benchmark. The batch itself has since completed on Colab (see above); the SSH
host remains available for jobs longer than a Colab session once a login works.
