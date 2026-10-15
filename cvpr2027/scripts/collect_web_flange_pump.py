"""Fetch pinned published CAD/FEM assets only; never run downloaded code."""
from pathlib import Path
from urllib.parse import quote
import requests,concurrent.futures,json,hashlib,time
T=Path('cvpr2027/tmp/cad-fem-machinery-search');D=Path('cvpr2027/data')
repos={'spsvision/BoltedFlangeAnalysis':'web-cad-fem-flange-contact/spsvision','Prashantsk45/Saturn-V-F1-Nozzle-Joint-FEA':'web-cad-fem-flange-contact/saturn-nozzle','barissahilli/Parametric-Design-Analysis-and-Optimization-of-External-Gear-Pumps':'web-cad-fem-gear-pump'}
for repo,folder in repos.items():
 tree=json.loads((T/(repo.replace('/','--')+'-tree.json')).read_text());R=D/folder;R.mkdir(parents=True,exist_ok=True);blobs=[x for x in tree['tree'] if x['type']=='blob' and not x['path'].lower().endswith(('.mp4','.avi'))]
 def f(x):
  url=f'https://raw.githubusercontent.com/{repo}/{tree["sha"]}/{quote(x["path"])}';p=R/x['path'];p.parent.mkdir(parents=True,exist_ok=True)
  def valid():
   if not p.exists():return False
   b=p.read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha']
  if not valid():
   for i in range(3):
    try:
     r=requests.get(url,timeout=45);r.raise_for_status();p.write_bytes(r.content);assert valid();break
    except Exception:
     if i==2:raise
     time.sleep(1)
  return {'path':x['path'],'source':url,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:rows=list(e.map(f,blobs))
 license=(R/'LICENSE').read_text() if (R/'LICENSE').exists() else 'Unresolved: no explicit source dataset license located; local research only.'
 (R/'download-manifest.json').write_text(json.dumps({'source':'https://github.com/'+repo,'revision':tree['sha'],'license_notice':license,'files':rows,'video_duplicates_omitted':True},indent=2)+'\n');print(repo,len(rows),sum(x['bytes'] for x in rows),flush=True)
