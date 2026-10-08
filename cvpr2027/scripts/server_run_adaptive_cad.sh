#!/usr/bin/env bash
set -euo pipefail
ADAPTIVE_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADAPTIVE_BUNDLE_DIR="$(dirname "$ADAPTIVE_SCRIPT_DIR")"
ADAPTIVE_CAD_PYTHON="${ADAPTIVE_CAD_PYTHON:-/home/trishita/svg-compute/cadq-venv/bin/python}"
export PYTHONPATH="$ADAPTIVE_BUNDLE_DIR/dependencies${PYTHONPATH:+:$PYTHONPATH}"
exec "$ADAPTIVE_CAD_PYTHON" "$ADAPTIVE_SCRIPT_DIR/run_adaptive_cad.py" --cad-python "$ADAPTIVE_CAD_PYTHON" "$@"
