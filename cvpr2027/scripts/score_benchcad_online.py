"""Execute all retained predictions against pinned upstream reference STEP solids."""
import argparse
from collections import Counter
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    sys.setrecursionlimit(10000)
    p = argparse.ArgumentParser()
    p.add_argument('predictions', type=Path)
    p.add_argument('--row-index', type=int)
    p.add_argument('--timeout', type=int, default=45)
    a = p.parse_args()
    rows = [json.loads(x) for x in a.predictions.read_text().splitlines()]
    if a.row_index is not None:
        import cadquery as cq
        from verify_mechanical_cad_edits import execute
        r = rows[a.row_index]
        result = dict(id=r['id'], category=r['category'], family=r['family'], reference_valid=False,
                      executable=False, volume_iou=None, match_95=False, match_strict=False,
                      status='reference_error')
        try:
            path = Path(r['reference_step'])
            assert hashlib.sha256(path.read_bytes()).hexdigest() == r['reference_step_sha256']
            reference = cq.importers.importStep(str(path)).val()
            if not reference.isValid() or not reference.Solids() or reference.Volume() <= 0:
                raise ValueError('Invalid upstream reference STEP')
            result['reference_valid'] = True
            result['status'] = 'invalid_patch'
            if r['predicted_code'] is None:
                raise ValueError(r['error'])
            result['status'] = 'execution_error'
            predicted = execute(r['predicted_code'])
            result['executable'] = True
            result['status'] = 'comparison_error'
            inter = predicted.intersect(reference).Volume()
            union = predicted.Volume() + reference.Volume() - inter
            iou = max(0.0, min(1.0, inter / union))
            result.update(status='scored', volume_iou=iou, match_95=iou >= 0.95, match_strict=iou >= 0.99999,
                          predicted_volume=predicted.Volume(), reference_volume=reference.Volume())
        except Exception as e:
            result['error'] = type(e).__name__ + ': ' + str(e)[:250]
        print(json.dumps(result))
        return
    def task(i):
        try:
            r = subprocess.run([sys.executable, __file__, str(a.predictions), '--row-index', str(i)],
                               capture_output=True, text=True, timeout=a.timeout)
            if r.returncode:
                raise RuntimeError(r.stderr[-200:])
            result = json.loads(r.stdout.splitlines()[-1])
        except subprocess.TimeoutExpired:
            result = dict(id=rows[i]['id'], family=rows[i]['family'], category=rows[i]['category'],
                          reference_valid=None, executable=None, volume_iou=None,
                          match_95=False, match_strict=False, status='timeout')
        except Exception as e:
            result = dict(id=rows[i]['id'], family=rows[i]['family'], category=rows[i]['category'],
                          reference_valid=None, executable=None, volume_iou=None,
                          match_95=False, match_strict=False, status='worker_error', error=str(e)[:250])
        return result
    results = []
    detail = a.predictions.with_name(a.predictions.stem + '-geometry.jsonl')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool, detail.open('w') as f:
        for r in pool.map(task, range(len(rows))):
            results.append(r)
            f.write(json.dumps(r) + '\n')
            f.flush()
            print('Scored', len(results), '/', len(rows), r['status'], flush=True)
    def metrics(rs):
        return dict(n=len(rs), reference_valid=sum(r['reference_valid'] is True for r in rs),
                    executable=sum(r['executable'] is True for r in rs),
                    match_95=sum(r['match_95'] for r in rs), match_strict=sum(r['match_strict'] for r in rs),
                    statuses=dict(Counter(r['status'] for r in rs)))
    summary = metrics(results)
    summary.update(timeout_seconds=a.timeout, fem='not_evaluated_missing_physical_specification',
                   categories={c:metrics([r for r in results if r['category']==c]) for c in sorted({r['category'] for r in results})},
                   rows=results)
    output = a.predictions.with_name(a.predictions.stem + '-geometry.json')
    output.write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('rows','categories')}))


if __name__ == '__main__':
    main()
