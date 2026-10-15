from pathlib import Path
import requests,json,concurrent.futures,hashlib,time,zipfile
from urllib.parse import quote
T=Path('cvpr2027/tmp/cad-fem-pressure-search');D=Path('cvpr2027/data')
repos={'Kevingd2k3/Mini-Project_Disc-Brake-Optimisation':'web-cad-fem-brake-thermal','sanjana-nishad/6-Axis-Robotic-Arm':'web-cad-fem-robot-arm'}
for repo,folder in repos.items():
 tree=json.loads((T/(repo.replace('/','--')+'-tree.json')).read_text());R=D/folder;R.mkdir(exist_ok=True)
 def choose(path):
  if '6-Axis' in repo:return not path.endswith('.wmv')
  return path.startswith('CAD Files/') or path in ['README.md','Project Report.pdf'] or path.endswith('.wbpj') or ('Coupled w CFD_files/dp0/SYS/' in path and not path.endswith('file.DSP')) or path.endswith('SYS-2/MECH/ObjectiveHistory.out') or path.endswith('SYS-2/MECH/file.topo') or path.endswith('SYS-2/MECH/structured_history.xml') or path.endswith('SYS-2/MECH/topo.out')
 blobs=[x for x in tree['tree'] if x['type']=='blob' and choose(x['path'])]
 def f(x):
  url=f'https://raw.githubusercontent.com/{repo}/{tree["sha"]}/{quote(x["path"])}';p=R/x['path'];p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists():
   for i in range(3):
    try:
     r=requests.get(url,timeout=45);r.raise_for_status();assert len(r.content)==x['size'];p.write_bytes(r.content);break
    except Exception:
     if i==2:raise
     time.sleep(1)
  assert p.stat().st_size==x['size']
  return {'path':x['path'],'source':url,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:rows=list(e.map(f,blobs))
 (R/'download-manifest.json').write_text(json.dumps({'source':'https://github.com/'+repo,'revision':tree['sha'],'license':'No explicit data license located; local research collection, no public release.','files':rows,'selection':'Thermal FEM and native CAD/report assets; Fluent CFD (finite volume) and intermediate topology iterations excluded. Robot lead skips video.'},indent=2)+'\n');print(repo,len(rows),sum(x['bytes'] for x in rows),flush=True)
 for p in R.glob('*.zip'):
  with zipfile.ZipFile(p) as z:
   assert z.testzip() is None;(R/'archive-inventory.json').write_text(json.dumps([{'member':i.filename,'bytes':i.file_size} for i in z.infolist()],indent=2));print([(i.filename,i.file_size) for i in z.infolist()],flush=True)
