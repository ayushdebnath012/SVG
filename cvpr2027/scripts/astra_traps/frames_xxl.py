"""Build larger dimensioned frame-elevation tasks (36-55 members) with eng_frame_bench's generator and verified solver.

Extends Astra's only reproducible failure: on unaided frame analysis it declined 3 of 4 samples at 21 members
(indeterminacy 27) and 1 of 35 below 20. Same prompt, protocol and reference checks as data/eng-frame-bench-xl.

  PYTHONPATH=src tmp/cq-env/bin/python scripts/astra_traps/frames_xxl.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import eng_frame_bench as E  # noqa: E402


def instances_xxl():
    return [
        ("fourbay_four", E.frame(4, 4, 3200, 2900, name="Four-bay four-storey frame elevation"), "shift_grid"),
        ("threebay_six", E.frame(3, 6, 3300, 2800, name="Three-bay six-storey frame elevation"), "raise_floor"),
        ("fivebay_five", E.frame(5, 5, 3200, 2800, name="Five-bay five-storey frame elevation"), "shift_grid"),
    ]


E.instances_xl = instances_xxl
E.build(out=ROOT / "data/eng-frame-bench-xxl", force=True, which="xl")
