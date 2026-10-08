"""Persistent CadQuery reward worker for GRPO (runs in a CadQuery environment; one request per stdin line).

Request:  {"task": id, "representation": "cadquery"|"cad-editor-sequence", "reference": program, "candidate": program}
Reply:    {"task": id, "executable": bool, "iou": float|null, "error": str|null}
The reference solid of each task is executed once and cached. Training references only; never test/validation.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_mechanical_cad_edits import execute  # noqa: E402
from cad_editor_geometry import execute_sequence  # noqa: E402

REFERENCES: dict = {}


def iou(a, b) -> float:
    inter = a.intersect(b).Volume()
    union = a.Volume() + b.Volume() - inter
    return max(0.0, min(1.0, inter / union)) if union > 0 else 0.0


def handle(req: dict) -> dict:
    run = execute if req["representation"] == "cadquery" else execute_sequence
    out = dict(task=req["task"], executable=False, iou=None, error=None)
    try:
        if req["task"] not in REFERENCES:
            REFERENCES[req["task"]] = run(req["reference"])
        solid = run(req["candidate"])
        out.update(executable=True, iou=iou(solid, REFERENCES[req["task"]]))
    except Exception as e:  # noqa: BLE001 - every failure is a scored outcome
        out["error"] = type(e).__name__ + ": " + str(e)[:160]
    return out


for line in sys.stdin:
    print(json.dumps(handle(json.loads(line))), flush=True)
