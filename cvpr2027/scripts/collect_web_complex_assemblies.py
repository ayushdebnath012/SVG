"""Download published CAD/FEM bytes only; never execute publisher scripts or solvers."""
from pathlib import Path
import json,requests,hashlib,zipfile
T=Path('cvpr2027/tmp/cad-fem-complex-assembly-search');D=Path('cvpr2027/data');repos=[('MohammadHaris13/Multiphysics-Structural-and-Thermal-FEA-of-a-Single-Cylinder-Engine-Crank-Assembly','web-cad-fem-crank-multiphysics'),('ayushwug24me-sketch/pipe-flange-fea','web-cad-fem-pipe-flange-comparison'),('HeehwanSoul/ansys-simulation-model-evaluation','web-cad-fem-shelf-pretension'),('gowtham-d-p/Knuckle-Joint-Assembly','web-cad-fem-knuckle-joint')]
for repo,folder in repos:
 m=json.loads((T/(repo.replace('/','--')+'-repo.json')).read_text());tr=json.loads((T/(repo.replace('/','--')+'-tree.json')).read_text());R=D/folder;R.mkdir(exist_ok=True);p=T/(folder+'-source-snapshot.zip');url=f'https://codeload.github.com/{repo}/zip/refs/heads/{m["default_branch"]}'
 if not p.exists():
  r=requests.get(url,timeout=(7,55));r.raise_for_status();p.write_bytes(r.content)
 rows=[]
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None;prefix=z.namelist()[0].split('/')[0]+'/'
  for x in tr['tree']:
   if x['type']!='blob' or x['path'].lower().endswith(('.gitkeep','.lock','.mp4','.wmv')):continue
   # Mesh-convergence teaching variants and unrelated thermal rod remain auxiliary manifests,
   # not extra complex cases. Preserve reports; download only bolted shelf archive.
   if folder=='web-cad-fem-shelf-pretension' and x['path'].endswith('.wbpz') and 'bolted_shelf' not in x['path']:continue
   b=z.read(prefix+x['path']);assert len(b)==x['size'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha'];q=R/x['path'];q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b);rows.append({'path':x['path'],'bytes':len(b),'git_blob_sha1':x['sha'],'sha256':hashlib.sha256(b).hexdigest(),'source_blob_API':f'https://api.github.com/repos/{repo}/git/blobs/{x["sha"]}'})
   if q.suffix.lower()=='.wbpz':
    with zipfile.ZipFile(q) as zz:
     assert zz.testzip() is None;inv=[{'member':i.filename,'bytes':i.file_size} for i in zz.infolist()];(R/(q.stem+'-original-inventory.json')).write_text(json.dumps(inv,indent=2)+'\n');out=R/'extracted-original'/q.stem;out.mkdir(parents=True,exist_ok=True)
     for i in zz.infolist():
      if i.is_dir():continue
      qq=out/i.filename;assert out.resolve() in qq.resolve().parents;qq.parent.mkdir(parents=True,exist_ok=True);qq.write_bytes(zz.read(i))
 (R/'download-manifest.json').write_text(json.dumps({'source':'https://github.com/'+repo,'pinned_tree_revision':tr['sha'],'snapshot':url,'files':rows,'policy':'No script/macro/journal execution, no local CAD/mesh generation or FEM solve, no model call.'},indent=2)+'\n');print(folder,len(rows),sum(x['bytes'] for x in rows),flush=True)
 for q in R.glob('*inventory.json'):
  inv=json.loads(q.read_text());print('archiveCAD/results',[(x['member'],x['bytes']) for x in inv if x['member'].lower().endswith(('.rst','.rth','.scdoc','.dsco','.agdb','.step','.stp','.png'))][:20],flush=True)
