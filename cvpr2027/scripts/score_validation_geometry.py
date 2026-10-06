"""Strict-IoU scoring for validation predictions, whose rows carry no released STEP target.

Same contract as score_multisource_cad_geometry.py, except the CadQuery reference solid is obtained by
executing the reference program (edited_code); CAD-Editor references are reconstructed sequences as on test.
Optionally re-anchors PLAN bullets first (anchor_plan_patches.anchor).

  python score_validation_geometry.py PREDICTIONS.jsonl VALIDATION_ROWS.jsonl [--anchor]
"""
import argparse,concurrent.futures,json,subprocess,sys
from collections import Counter
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('predictions',type=Path);p.add_argument('rows',type=Path,nargs='?');p.add_argument('--anchor',action='store_true');p.add_argument('--row-index',type=int);a=p.parse_args()
 rs=list(map(json.loads,a.predictions.read_text().splitlines()))
 if a.row_index is not None:
  from verify_mechanical_cad_edits import execute
  from cad_editor_geometry import execute_sequence
  r=rs[a.row_index];run=execute if r['representation']=='cadquery' else execute_sequence
  out=dict(id=r['id'],source=r['source'],category=r['category'],reference_valid=False,executable=False,status='reference_error',volume_iou=None,match_strict=False)
  try:
   target=run(r['reference_code']);out.update(reference_valid=True,status='invalid_patch')
   if r['predicted_code'] is None:raise ValueError(r['error'])
   out['status']='execution_error';solid=run(r['predicted_code']);out['executable']=True;inter=solid.intersect(target).Volume();iou=max(0.,min(1.,inter/(solid.Volume()+target.Volume()-inter)));out.update(status='scored',volume_iou=iou,match_strict=iou>=.99999)
  except Exception as e:out['error']=type(e).__name__+': '+str(e)[:200]
  print(json.dumps(out));return
 if a.anchor:
  sys.path.insert(0,str(Path(__file__).resolve().parent))
  from anchor_plan_patches import anchor
  from cad_edit_contracts import apply,target_match
  rows={json.loads(l)['id']:json.loads(l) for l in a.rows.read_text().splitlines()}
  for q in rs:
   try:
    patch,moved=anchor(rows[q['id']]['code'],q['prediction'])
    if moved:code=apply(rows[q['id']]['code'],patch,q['representation']);q.update(applicable=True,error=None,predicted_code=code,target_match=target_match(code,q['reference_code'],q['representation']))
   except Exception:pass
  a.predictions=a.predictions.with_name(a.predictions.stem+'-anchored.jsonl');a.predictions.write_text(''.join(json.dumps(q)+'\n' for q in rs))
 def task(i):
  try:r=subprocess.run([sys.executable,__file__,str(a.predictions),'--row-index',str(i)],capture_output=True,text=True,timeout=60);return json.loads(r.stdout.splitlines()[-1])
  except Exception as e:return dict(id=rs[i]['id'],source=rs[i]['source'],status='timeout' if isinstance(e,subprocess.TimeoutExpired) else 'worker_error',match_strict=False,executable=None)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(task,range(len(rs))))
 a.predictions.with_name(a.predictions.stem+'-geometry.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in results))
 m=lambda rr:dict(n=len(rr),applicable=sum(q['applicable'] for q in rs if q['id'] in {r['id'] for r in rr}),executable=sum(r['executable'] is True for r in rr),match_strict=sum(r['match_strict'] for r in rr),statuses=dict(Counter(r['status'] for r in rr)))
 print(json.dumps(dict(all=m(results),**{s:m([r for r in results if r['source']==s]) for s in ['BenchCAD','CAD-Editor']})))
if __name__=='__main__':main()
