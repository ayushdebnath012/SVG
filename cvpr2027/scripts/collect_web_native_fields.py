"""Collect published bytes only. Do not execute publisher Python, macros or solvers."""
from pathlib import Path
import json,requests,hashlib,zipfile,concurrent.futures
T=Path('cvpr2027/tmp/cad-fem-native-fields-search');D=Path('cvpr2027/data')
repos=[('mist90/FreeCAD-FEM-examples','web-cad-fem-elmer-cooling'),('RanitDas21/structural-and-modal-analysis-wheel-rim','web-cad-fem-wheel-rim-fields'),('MarcusAdielsonGuichet/Test-Bench-Digital-Twin','web-cad-fem-testbench-fields')]
def collect(pair):
 repo,name=pair;m=json.loads((T/(repo.replace('/','--')+'-repo.json')).read_text());tr=json.loads((T/(repo.replace('/','--')+'-tree.json')).read_text());R=D/name;R.mkdir(exist_ok=True);rows=[]
 def selected(x):
  p=x['path']
  if x['type']!='blob' or p.lower().endswith(('.lock','desktop.ini','.mp4','.wmv','.exe')):return False
  if name=='web-cad-fem-testbench-fields':return p in ['README.md','Test Frame.FCStd'] or p.startswith('CCX Files/test_runs/')
  return not p.startswith('.') and not p.endswith('.project_cache')
 files=[x for x in tr['tree'] if selected(x)]
 # One pinned snapshot per small/medium repository avoids excessive individual requests.
 if name!='web-cad-fem-testbench-fields':
  snap=T/(name+'-source-snapshot.zip')
  if not snap.exists():
   with requests.get(f'https://codeload.github.com/{repo}/zip/refs/heads/{m["default_branch"]}',stream=True,timeout=(7,55)) as rr:
    rr.raise_for_status()
    with snap.open('wb') as f:
     for b in rr.iter_content(1024*1024):f.write(b)
  z=zipfile.ZipFile(snap);assert z.testzip() is None;prefix=z.namelist()[0].split('/')[0]+'/'
 else:z=None
 for x in files:
  if z:b=z.read(prefix+x['path'])
  else:
   rr=requests.get(f'https://raw.githubusercontent.com/{repo}/{m["default_branch"]}/{requests.utils.quote(x["path"],safe="/")}',timeout=(7,40));rr.raise_for_status();b=rr.content
  assert len(b)==x['size'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha'];f=R/x['path'];f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);rows.append({'path':x['path'],'bytes':len(b),'git_blob_sha1':x['sha'],'sha256':hashlib.sha256(b).hexdigest(),'source_blob_API':f'https://api.github.com/repos/{repo}/git/blobs/{x["sha"]}'})
 if z:z.close()
 (R/'download-manifest.json').write_text(json.dumps({'source':'https://github.com/'+repo,'pinned_tree_revision':tr['sha'],'files':rows,'selection_policy':'NativeCAD,originalresult/deck/assets; testbench onlyCAD+test_runs, excluding vendoredexecutables/manuals/co-simulationruns.','execution_policy':'No publisher program or solver execution; no new CAD or model call.'},indent=2)+'\n');print(name,len(rows),sum(x['bytes'] for x in rows),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as e:
 for _ in e.map(collect,repos):pass
