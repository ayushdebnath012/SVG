#!/bin/sh
# Regenerate the eng-svg benchmark and trainset deterministically, then train on a GPU.
# The trainset is not versioned: its generator and seed are, which is the stronger guarantee.
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH=src:scripts
python scripts/eng_svg_trainset.py build --n "${PAIRS:-400}"
python scripts/eng_svg_trainset.py verify
python scripts/colab_train_engsvg.py --arms "${ARMS:-text2svg}" --epochs "${EPOCHS:-2}" \
    --eval-count "${EVAL:-24}" --out "${OUT:-/content/engsvg-run}"
