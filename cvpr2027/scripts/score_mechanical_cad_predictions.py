"""Run predicted and reference mechanical CAD and compare their actual solids."""
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys


def main():
    path = Path(sys.argv[1])
    rows = [json.loads(x) for x in path.read_text().splitlines()]
    if len(sys.argv) == 3:
        from verify_mechanical_cad_edits import execute
        r = rows[int(sys.argv[2])]
        try:
            if r['predicted_code'] is None:
                raise ValueError('Unapplicable patch')
            predicted = execute(r['predicted_code'])
            reference = execute(r['reference_code'])
            intersection = predicted.intersect(reference).Volume()
            union = predicted.Volume() + reference.Volume() - intersection
            iou = max(0.0, min(1.0, intersection / union))
            result = dict(id=r['id'], valid=True, volume_iou=iou, geometry_match=iou >= 0.99999)
        except Exception as e:
            result = dict(id=r['id'], valid=False, volume_iou=None, geometry_match=False, error=str(e)[:250])
        print(json.dumps(result))
        return
    def task(i):
        try:
            r = subprocess.run([sys.executable, __file__, str(path), str(i)], capture_output=True, text=True, timeout=90)
            if r.returncode:
                raise ValueError(r.stderr[-200:])
            return json.loads(r.stdout.splitlines()[-1])
        except Exception as e:
            return dict(id=rows[i]['id'], valid=False, volume_iou=None, geometry_match=False, error=str(e)[:250])
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(task, range(len(rows))))
    output = path.with_name(path.stem + '-geometry.json')
    metrics = dict(n=len(results), executable=sum(r['valid'] for r in results),
                   geometry_match=sum(r['geometry_match'] for r in results),
                   fem='not_evaluated_missing_physical_specification', rows=results)
    output.write_text(json.dumps(metrics, indent=2) + '\n')
    print(json.dumps({k: v for k, v in metrics.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
