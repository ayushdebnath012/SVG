"""Collect published original CAD and existing FEM references; never execute source code."""
from pathlib import Path
from urllib.parse import quote
import requests,json,hashlib,base64,zipfile,concurrent.futures,time
T=Path('cvpr2027/tmp/cad-fem-additional-systems-search');D=Path('cvpr2027/data');repo_map={'Tonylo-lab/pneumatic-gripper-fea':'web-cad-fem-pneumatic-gripper','9697psh/finray-gripper-fea':'web-cad-fem-finray-contact','Nihal606/Vibration-Project':'web-cad-fem-leafspring-modal','tomraven1/ansysCAD_bistable_gripper':'web-cad-fem-bistable-gripper-held'}
for repo,folder in repo_map.items():
 R=D/folder;R.mkdir(exist_ok=True);tree=json.loads((T/(repo.replace('/','--')+'-tree.json')).read_text());bl=[x for x in tree['tree'] if x['type']=='blob' and not x['path'].lower().endswith(('.gitkeep','.stl','.m'))]
 branch='master' if repo.startswith(('9697psh/','tomraven1/')) else 'main';snapshot_url=f'https://codeload.github.com/{repo}/zip/refs/heads/{branch}';snapshot=T/(folder+'-source-snapshot.zip')
 if not snapshot.exists():
  r=requests.get(snapshot_url,timeout=(6,45));r.raise_for_status();snapshot.write_bytes(r.content)
 source_zip=zipfile.ZipFile(snapshot);prefix=source_zip.namelist()[0].split('/')[0]+'/'
 def fetch(x):
  p=R/x['path'];p.parent.mkdir(parents=True,exist_ok=True);url=f'https://api.github.com/repos/{repo}/git/blobs/{x["sha"]}';raw=f'https://raw.githubusercontent.com/{repo}/{tree["sha"]}/{quote(x["path"],safe="/")}'
  for i in range(3):
   try:
    if p.exists():b=p.read_bytes()
    else:b=source_zip.read(prefix+x['path'])
    assert len(b)==x['size'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha'];p.write_bytes(b);return {'path':x['path'],'source':raw,'download_API':url,'bytes':len(b),'git_blob_sha1':x['sha'],'sha256':hashlib.sha256(b).hexdigest()}
   except Exception:
    if i==2:raise
    time.sleep(1)
 with concurrent.futures.ThreadPoolExecutor(max_workers=7) as e:rows=list(e.map(fetch,bl))
 (R/'download-manifest.json').write_text(json.dumps({'source':'https://github.com/'+repo,'revision':tree['sha'],'files':rows,'policy':'No source .py/.m/deck/macro execution, no CAD/mesh generation, no FEM solve or model call.'},indent=2)+'\n');print(folder,len(rows),sum(x['bytes'] for x in rows),flush=True)
 for p in R.glob('*.wbpz'):
  with zipfile.ZipFile(p) as z:
   assert z.testzip() is None;(R/(p.stem+'-archive-inventory.json')).write_text(json.dumps([{'member':i.filename,'bytes':i.file_size} for i in z.infolist()],indent=2)+'\n')
# Download pinned public release; preserve publisher SHA-256 and archive contents.
R=D/'web-cad-fem-pneumatic-gripper';release=json.loads((T/'pneumatic-gripper-release.json').read_text());(R/'release-source-metadata.json').write_text(json.dumps(release,indent=2)+'\n');asset=release['assets'][0];p=R/asset['name'];tmp=p.with_suffix('.download')
if not p.exists():
 r=requests.get(asset['browser_download_url'],timeout=(8,55),stream=True);r.raise_for_status();h=hashlib.sha256();size=0;last=0
 with tmp.open('wb') as f:
  for b in r.iter_content(4*1024*1024):
   f.write(b);h.update(b);size+=len(b)
   if size-last>150000000:print('release downloaded MB',round(size/1e6),flush=True);last=size
 assert size==asset['size'];assert 'sha256:'+h.hexdigest()==asset['digest'];tmp.rename(p)
h=hashlib.sha256()
with p.open('rb') as f:
 for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
assert p.stat().st_size==asset['size'];assert 'sha256:'+h.hexdigest()==asset['digest'];(R/'release-download-manifest.json').write_text(json.dumps({'source':release['html_url'],'release_id':release['id'],'asset_id':asset['id'],'file':p.name,'bytes':p.stat().st_size,'sha256':h.hexdigest(),'publisher_digest':asset['digest'],'download_url':asset['browser_download_url']},indent=2)+'\n')
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None;inventory=[{'member':i.filename,'bytes':i.file_size} for i in z.infolist()];(R/'release-archive-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n');print('release assets',[(x['member'],x['bytes']) for x in inventory if x['member'].lower().endswith(('.rst','.rth','.scdoc','.scdocx','.agdb','.step','.stp','.dat','.out'))],flush=True)
 out=R/'extracted-original';out.mkdir(exist_ok=True)
 for i in z.infolist():
  if i.is_dir() or not i.filename.lower().endswith(('.rst','.rth','.scdoc','.scdocx','.agdb','.dat','.out','.err','.xml','.txt','.wbpj')):continue
  q=out/i.filename;assert out.resolve() in q.resolve().parents;q.parent.mkdir(parents=True,exist_ok=True)
  with z.open(i) as src,q.open('wb') as dst:
   for b in iter(lambda:src.read(8*1024*1024),b''):dst.write(b)
print('Release downloaded, SHA256 and archive CRC verified',flush=True)
