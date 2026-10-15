"""Download pinned publisher bytes, never execute downloaded programs."""
from pathlib import Path
import json,requests,hashlib,zipfile
T=Path('cvpr2027/tmp/cad-fem-rotating-machinery-search');D=Path('cvpr2027/data')
for repo,folder in [('Zayannnnn/UAV-Frame-Structural-Analysis','web-cad-fem-uav-assembly'),('vinittakate19/Differential-Gear-Box-shaft','web-cad-fem-differential-shaft'),('yashps-74/FKDC-Rear-Axle','web-cad-fem-rear-axle'),('koolkingisone/composite-pipe-fea','web-cad-fem-composite-pipe'),('ayushwug24me-sketch/quadcopter-drone-cad-fea-analysis','web-cad-fem-quadcopter-dynamics')]:
 meta=json.loads((T/(repo.replace('/','--')+'-repo.json')).read_text());tree=json.loads((T/(repo.replace('/','--')+'-tree.json')).read_text());R=D/folder;R.mkdir(exist_ok=True);snapshot=T/(folder+'-original-snapshot.zip');url=f'https://codeload.github.com/{repo}/zip/refs/heads/{meta["default_branch"]}'
 if not snapshot.exists():
  r=requests.get(url,timeout=(7,45));r.raise_for_status();snapshot.write_bytes(r.content)
 with zipfile.ZipFile(snapshot) as z:
  assert z.testzip() is None;prefix=z.namelist()[0].split('/')[0]+'/';rows=[]
  for x in tree['tree']:
   if x['type']!='blob' or x['path'].lower().endswith(('.mp4','.stl','.lock')):continue
   b=z.read(prefix+x['path']);assert len(b)==x['size'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha'];p=R/x['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);rows.append({'path':x['path'],'bytes':len(b),'git_blob_sha1':x['sha'],'sha256':hashlib.sha256(b).hexdigest(),'source_blob_API':f'https://api.github.com/repos/{repo}/git/blobs/{x["sha"]}'})
 (R/'download-manifest.json').write_text(json.dumps({'source':'https://github.com/'+repo,'pinned_tree_revision':tree['sha'],'snapshot_download':url,'files':rows,'policy':'No downloaded script/macro/deck execution; no new CAD, mesh, solve or model call.'},indent=2)+'\n');print(folder,len(rows),sum(x['bytes'] for x in rows),flush=True)
