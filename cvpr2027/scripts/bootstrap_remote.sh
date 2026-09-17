#!/usr/bin/env bash
# Run inside the isolated uploaded cvpr2027 directory.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON=.venv-remote/bin/python
if [ ! -x "$PYTHON" ]; then
    if python3 -c 'import ensurepip' 2>/dev/null; then
        python3 -m venv --system-site-packages .venv-remote
    else
        # Hosts without python3-venv/pip packages: create the environment without
        # pip and bootstrap it from PyPA's installer, so no system package is touched.
        python3 -m venv --system-site-packages --without-pip .venv-remote
        curl -sSf https://bootstrap.pypa.io/get-pip.py | "$PYTHON"
    fi
fi
# Pinned to the version of the recorded A100/Colab runs. Newer torch (2.14) routes
# matmuls through Triton, which compiles against Python.h at first use and fails on
# hosts without python3-dev headers.
if ! "$PYTHON" -c 'import torch; assert torch.__version__.startswith("2.11.") and torch.cuda.is_available()' 2>/dev/null; then
    "$PYTHON" -m pip install 'torch==2.11.0'
fi
"$PYTHON" -m pip install -r requirements-local.txt -r requirements-colab.txt
"$PYTHON" -c 'import torch; assert torch.cuda.is_available(), "CUDA is unavailable; install the PyTorch build appropriate for this host before launching"; print(torch.__version__, torch.cuda.get_device_name(0))'
"$PYTHON" -m pip freeze > remote-packages.txt
echo 'Environment ready. Launch scripts/remote_batch.py in a detached process.'
