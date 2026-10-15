"""Execute held-out native predictions; distinguish downloaded and reconstructed references."""
import argparse,concurrent.futures,hashlib,json,subprocess,sys
from collections import Counter
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('predictions',type=Path);p.add_argument('--row-index',type=int);a=p.parse_args();rs=list(map(json.loads,a.predictions.read_text().splitlines()))
 if a.row_index is not None:
  import cadquery as cq
  from verify_mechanical_cad_edits import execute
  from cad_editor_geometry import execute_sequence
  r=rs[a.row_index];out=dict(id=r['id'],source=r['source'],category=r['category'],reference_valid=False,executable=False,status='reference_error',volume_iou=None,match_95=False,match_strict=False,fem='not_evaluated_no_operating_contract')
  try:
   if r['representation']=='cadquery':
    path=Path(r['reference_step']);assert hashlib.sha256(path.read_bytes()).hexdigest()==r['reference_step_sha256'];target=cq.importers.importStep(str(path)).val();out['reference_origin']='author_released_STEP'
   else:target=execute_sequence(r['reference_code']);out['reference_origin']='local_native_sequence_reconstruction_not_author_STEP'
   if not target.isValid() or not target.Solids() or target.Volume()<=0:raise ValueError('Invalid target solid')
   out['reference_valid']=True;out['status']='invalid_patch'
   if r['predicted_code'] is None:raise ValueError(r['error'])
   out['status']='execution_error';solid=execute(r['predicted_code']) if r['representation']=='cadquery' else execute_sequence(r['predicted_code']);out['executable']=True;out['status']='comparison_error';inter=solid.intersect(target).Volume();union=solid.Volume()+target.Volume()-inter;iou=max(0.,min(1.,inter/union));out.update(status='scored',volume_iou=iou,match_95=iou>=.95,match_strict=iou>=.99999,predicted_volume=solid.Volume(),reference_volume=target.Volume(),predicted_solid_count=len(solid.Solids()))
  except Exception as e:out['error']=type(e).__name__+': '+str(e)[:250]
  print(json.dumps(out));return
 def task(i):
  try:
   r=subprocess.run([sys.executable,__file__,str(a.predictions),'--row-index',str(i)],capture_output=True,text=True,timeout=45);assert r.returncode==0,r.stderr[-400:];return json.loads(r.stdout.splitlines()[-1])
  except Exception as e:return dict(id=rs[i]['id'],source=rs[i]['source'],category=rs[i]['category'],reference_valid=None,executable=None,status='timeout' if isinstance(e,subprocess.TimeoutExpired) else 'worker_error',error=str(e)[-400:],volume_iou=None,match_95=False,match_strict=False)
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool,a.predictions.with_name(a.predictions.stem+'-geometry.jsonl').open('w') as f:
  for r in pool.map(task,range(len(rs))):results.append(r);f.write(json.dumps(r)+'\n');f.flush();print('scored',len(results),'/',len(rs),r['status'],flush=True)
 def metrics(rr):return dict(n=len(rr),reference_valid=sum(r['reference_valid'] is True for r in rr),executable=sum(r['executable'] is True for r in rr),match_95=sum(r['match_95'] for r in rr),match_strict=sum(r['match_strict'] for r in rr),statuses=dict(Counter(r['status'] for r in rr)))
 m=metrics(results);m['sources']={s:metrics([r for r in results if r['source']==s]) for s in ['BenchCAD','CAD-Editor']};a.predictions.with_name(a.predictions.stem+'-geometry.json').write_text(json.dumps(m,indent=2)+'\n');print(m)
if __name__=='__main__':main()
