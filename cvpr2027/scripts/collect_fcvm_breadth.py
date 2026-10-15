"""Download pinned original CAD and published nonlinear result files; never execute them."""
import json,hashlib,concurrent.futures
from pathlib import Path
import requests
repo='HarryvL/fcVM-workbench';tree=json.loads(Path('cvpr2027/tmp/breadth-followup/HarryvL-fcVM-workbench.json').read_text());rev=tree['sha']
out=Path('cvpr2027/data/web-cad-fem-fcvm-breadth');out.mkdir(parents=True,exist_ok=True)
cases=['Bar buckling','Buckling','buckling_U100_3D','tensile','Lug_Pressure_Example','barrier','box girder','train_bridge','transition','transition3','Plate_girder_EC3','Wyk_Rohrstoss_ring','Haltegriff_FEM_RC','IPE400_4']
paths={f'{folder}/{c}{ext}' for c in cases for folder,ext in [('freeCAD files','.FCStd'),('control files','.inp'),('output files','.out'),('output files','.vtk'),('output files','.avr')]}
paths|={'README.md','package.xml','documentation/fcVM_Manual_1.0.pdf','source code/fcVM.py','fcVM.ini'}
selected=[x for x in tree['tree'] if x['type']=='blob' and x['path'] in paths]
def get(x):
 url=f'https://raw.githubusercontent.com/{repo}/{rev}/'+requests.utils.quote(x['path'],safe='/');p=out/x['path'];p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  r=requests.get(url,timeout=50);r.raise_for_status();p.write_bytes(r.content)
 b=p.read_bytes();assert len(b)==x['size'];assert hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()==x['sha']
 return {'path':x['path'],'source_url':url,'git_blob_sha1':x['sha'],'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:man=list(pool.map(get,selected))
(out/'download-manifest.json').write_text(json.dumps({'repo':repo,'revision_tree':rev,'cases':cases,'files':man,'executed_source_files':0},indent=2)+'\n');print(len(man),'files',sum(x['bytes'] for x in man),'bytes',flush=True)
