"""Download pinned original repository bytes only; never run source programs."""
from pathlib import Path
import requests,json,hashlib,zipfile,concurrent.futures
T=Path('cvpr2027/tmp/cad-fem-machine-variety-search');D=Path('cvpr2027/data')
pairs=[('Karthik-v202/Design-and-Finite-Element-Analysis-of-a-Rigid-Steel-Portal-Frame','web-cad-fem-portal-frame'),('Shass27/truss-analysis','web-cad-fem-bolted-truss'),('crsayan/NASA-CubeSat-Frame-analysis','web-cad-fem-cubesat-frame')]
def collect(pair):
 repo,name=pair;meta=json.loads((T/(repo.replace('/','--')+'-repo.json')).read_text());tree=json.loads((T/(repo.replace('/','--')+'-tree.json')).read_text());R=D/name;R.mkdir(exist_ok=True);snap=T/(name+'-snapshot.zip')
 r=requests.get(f'https://codeload.github.com/{repo}/zip/{tree["sha"]}',timeout=(10,50));r.raise_for_status();snap.write_bytes(r.content);rows=[]
 with zipfile.ZipFile(snap) as z:
  assert z.testzip() is None;prefix=z.namelist()[0].split('/')[0]+'/'
  for x in tree['tree']:
   p=x['path']
   if x['type']!='blob' or p.startswith('.') or p.lower().endswith(('.mp4','.mov','.heic','.trk','.m')):continue
   b=z.read(prefix+p);assert len(b)==x['size'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha'];f=R/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b);rows.append(dict(path=p,bytes=len(b),git_blob_sha1=x['sha'],sha256=hashlib.sha256(b).hexdigest(),source=f'https://github.com/{repo}/blob/{tree["sha"]}/{p}'))
 (R/'download-manifest.json').write_text(json.dumps(dict(source='https://github.com/'+repo,pinned_tree_revision=tree['sha'],files=rows,policy='Original CAD, drawings, reports and existing results only. Videos and analysis scripts omitted. No source program execution or new solve.'),indent=2)+'\n');print(name,len(rows),sum(x['bytes'] for x in rows),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as e:list(e.map(collect,pairs))
