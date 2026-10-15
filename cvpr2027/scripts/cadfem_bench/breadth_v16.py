"""Bundle additional original complex CAD/FEM collections as unscored source review.
Retain original data and notices; avoid duplicating a 1.43GB RST already inside its source WBPZ.
"""
import json,hashlib,shutil
from pathlib import Path
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
CASES={
 'landing-gear':['CAD/Assembly/Assembly.STEP','Material/contact/load scopes require independent review; report scalars only, no published saved solution tree.'],
 'crank-multiphysics':['Assembly_SP_SW.STEP','Thermal boundary/result correspondence and multi-body contact/material scopes require review; report and plot figures are preserved.'],
 'connecting-rod':['Connecting Rod.STEP','Original STEP declares inches and imported envelope conflicts with the FEM model scale; conversion/setup correspondence unresolved.'],
 'finned-heatsink':['','Exact material conductivity and all thermal face scopes require confirmation; plot targets only, no saved fields.'],
 'composite-pipe':['composite pipe.IGS','Original archived and loose solution revisions use different section/material cards; original CAD surface scope and safe layered-field decoding unresolved.'],
 'pneumatic-gripper':['cad/final_a2_gripper.STEP','Original nonlinear 26-body contact/joint model and saved final solution retained; independent setup/field/replay/convergence verification not established.']}
def add(root,p):
 rows=[];dest=p/'evaluator/source-review/complex-engineering';dest.mkdir(parents=True,exist_ok=True)
 for name,(cad,reason) in CASES.items():
  src=root/('web-cad-fem-'+name);out=dest/name;out.mkdir(exist_ok=True)
  for f in src.rglob('*'):
   if not f.is_file() or '__pycache__' in f.parts or '.git' in f.parts:continue
   rel=f.relative_to(src)
   if name=='pneumatic-gripper' and rel.parts[0]=='extracted-original' and f.name!='ds.dat':continue
   d=out/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
  cat=json.loads((out/'catalog.json').read_text())
  if not cad:
   files=[f for f in out.rglob('*') if f.suffix.lower() in ['.step','.stp','.igs','.iges']];cad=str(files[0].relative_to(out)) if files else ''
  manifest=[]
  for f in sorted(out.rglob('*')):
   if f.is_file():manifest.append({'path':str(f.relative_to(out)),'bytes':f.stat().st_size,'sha256':sha(f)})
  (out/'package-source-files.json').write_text(json.dumps(manifest,indent=2)+'\n')
  rows.append({'collection_id':name,'title':cat.get('collection',name),'source':cat.get('source') or json.loads((out/'download-manifest.json').read_text()).get('source'),'cad_view':cad,'status':'source_review_not_scored','active_benchmark_tasks_added':0,'hold_reason':reason,'published_file_count':len(manifest),'source_details':'catalog.json','result_storage':'original WBPZ contains raw RST; duplicate extracted RST omitted' if name=='pneumatic-gripper' else 'original files, reports and available saved solutions retained','candidate_visibility':'evaluator_only'})
 (dest/'index.json').write_text(json.dumps(rows,indent=2)+'\n');return rows
if __name__=='__main__':
 import argparse;a=argparse.ArgumentParser();a.add_argument('--data',type=Path,required=True);a.add_argument('--package',type=Path,required=True);x=a.parse_args();print(json.dumps(add(x.data,x.package),indent=2))
