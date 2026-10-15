"""Download pinned original public engineering assets; never execute source code."""
from pathlib import Path
import requests,json,concurrent.futures,hashlib,time
from urllib.parse import quote
T=Path('cvpr2027/tmp/cad-fem-pressure-search');D=Path('cvpr2027/data')
repos={'anithinvarma03-cyber/Pressure-Vessel-Analysis':'web-cad-fem-pressure-vessel','PooyaBaravati/double-wishbone-active-suspension':'web-cad-fem-active-suspension'}
for repo,folder in repos.items():
 tree=json.loads((T/(repo.replace('/','--')+'-tree.json')).read_text());R=D/folder;R.mkdir(exist_ok=True)
 blobs=[x for x in tree['tree'] if x['type']=='blob' and not x['path'].lower().endswith(('.mp4','.emf'))]
 def f(x):
  url=f'https://raw.githubusercontent.com/{repo}/{tree["sha"]}/{quote(x["path"])}';local=x['path']
  if local.startswith('carbon steel/'):local=local.replace('carbon steel/','carbon-steel-root-variant/',1)
  p=R/local;p.parent.mkdir(parents=True,exist_ok=True)
  def valid(p):
   if not p.exists():return False
   b=p.read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha']
  if not valid(p):
   for i in range(3):
    try:
     r=requests.get(url,timeout=45);r.raise_for_status();assert len(r.content)==x['size'];p.write_bytes(r.content);break
    except Exception:
     if i==2:raise
     time.sleep(1)
  assert p.stat().st_size==x['size'] and valid(p)
  return {'path':local,'original_path':x['path'],'source':url,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:rows=list(e.map(f,blobs))
 (R/'download-manifest.json').write_text(json.dumps({'source':'https://github.com/'+repo,'revision':tree['sha'],'license':'No explicit data license located; retained locally for research, no public release.','files':rows,'excluded_assets':'Original MP4 and EMF duplicates not needed for CAD/FEM reference evidence'},indent=2)+'\n');print(repo,len(rows),sum(x['bytes'] for x in rows),flush=True)
