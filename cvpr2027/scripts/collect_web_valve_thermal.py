"""Download original FeenoX valve BREP, setup and published FEM trajectories."""
from pathlib import Path
import json,requests,base64,hashlib,concurrent.futures
T=Path('cvpr2027/tmp/cad-fem-new-machinery-search');R=Path('cvpr2027/data/web-cad-fem-valve-transient');R.mkdir(exist_ok=True);repo='seamplex/feenox';d=json.loads((T/'seamplex--feenox-tree.json').read_text());prefix='doc/tutorials/320-thermal/';names=['README.md','asme-properties.fee','valve.brep','valve.fee','valve.geo','valve.ppl','valve-scl-coords.fee','valve-1.csv','valve-internal-1.csv','valve-1.svg','valve-1-zoom.svg','valve-materials.png','valve-surfaces.png'];bl=[x for x in d['tree'] if x['type']=='blob' and (x['path'] in [prefix+n for n in names] or x['path'] in ['COPYING','LICENSE'])]
def f(x):
 p=R/(x['path'].split('/')[-1]);url=f'https://api.github.com/repos/{repo}/git/blobs/{x["sha"]}'
 if p.exists():b=p.read_bytes()
 else:r=requests.get(url,timeout=(6,25));r.raise_for_status();b=base64.b64decode(r.json()['content'])
 assert len(b)==x['size'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha'];p.write_bytes(b);return {'path':p.name,'source':url,'original_repository_path':x['path'],'bytes':len(b),'git_blob_sha1':x['sha'],'sha256':hashlib.sha256(b).hexdigest()}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:rows=list(e.map(f,bl))
(R/'download-manifest.json').write_text(json.dumps({'source':'https://www.seamplex.com/feenox/doc/tutorials/320-thermal/','repository':'https://github.com/seamplex/feenox','revision':d['sha'],'files':rows,'policy':'No source .fee/.geo/.ppl code executed, no mesh/geometry generation, no solve.'},indent=2)+'\n');print('Valve downloads',len(rows),sum(x['bytes'] for x in rows),flush=True)
for p in ['valve.fee','valve.ppl','valve-internal-1.csv']:print(p,(R/p).read_text(),flush=True)
print('temperature CSV',(R/'valve-1.csv').read_text()[:600],flush=True)
