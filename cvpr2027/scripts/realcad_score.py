"""RealCADBench-style Solid and Surface IoU (R = 96, 2 % padding; realcad_metrics.py) against released references.

Run with the CAD runtime. Input: a predictions JSONL with id, predicted_code and reference_step (as written for
score_multisource_cad_geometry.py). Output: <input>-realcad.jsonl with solid/surface IoU per task; a prediction
that does not execute scores 0 on both, as an unexecutable artifact does in RealCADBench.

  tmp/cad-runtime/bin/python scripts/realcad_score.py PREDICTIONS.jsonl [--workers 8]
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))


def one(row):
    from realcad_metrics import voxel_ious
    from verify_mechanical_cad_edits import execute
    import cadquery as cq
    out = dict(id=row["id"], solid=0.0, surface=0.0, executable=False)
    try:
        ref = cq.importers.importStep(row["reference_step"]).val()
    except Exception as e:  # noqa: BLE001
        return dict(out, status="reference_error", error=type(e).__name__)
    if not row.get("predicted_code"):
        return dict(out, status="no_prediction")
    try:
        pred = execute(row["predicted_code"])
    except Exception as e:  # noqa: BLE001
        return dict(out, status="execution_error", error=type(e).__name__)
    return dict(out, executable=True, status="scored", **voxel_ious(pred, ref))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("predictions", type=Path)
    p.add_argument("--workers", type=int, default=8)
    a = p.parse_args()
    rows = [json.loads(l) for l in a.predictions.read_text().splitlines() if l.strip()]
    with ProcessPoolExecutor(a.workers) as pool:
        res = list(pool.map(one, rows))
    out = a.predictions.with_name(a.predictions.stem + "-realcad.jsonl")
    out.write_text("".join(json.dumps(r) + "\n" for r in res))
    ok = [r for r in res if r["status"] != "reference_error"]
    print(json.dumps(dict(tasks=len(res), reference_valid=len(ok), executable=sum(r["executable"] for r in ok),
                          solid_mean=round(sum(r["solid"] for r in ok) / max(1, len(ok)), 4),
                          surface_mean=round(sum(r["surface"] for r in ok) / max(1, len(ok)), 4))))


if __name__ == "__main__":
    main()
