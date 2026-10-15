"""Second set of large frame-elevation tasks (39-42 members, different shapes), same generator, prompt and checks.

  PYTHONPATH=src ../.venv/bin/python scripts/astra_traps/frames_xxl2.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import eng_frame_bench as E  # noqa: E402


def instances():
    return [
        ("sixbay_three", E.frame(6, 3, 3000, 3000, name="Six-bay three-storey frame elevation"), "shift_grid"),
        ("twobay_eight", E.frame(2, 8, 3600, 2800, name="Two-bay eight-storey frame elevation"), "raise_floor"),
        ("fourbay_six_setback", E.frame(4, 6, 3200, 2900, setback_after=3, drop=2, name="Four-bay six-storey frame elevation, set back above the third floor"), "shift_grid"),
    ]


E.instances_xl = instances
E.build(out=ROOT / "data/eng-frame-bench-xxl2", force=True, which="xl")
