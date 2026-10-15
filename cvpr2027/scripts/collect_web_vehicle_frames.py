"""Download original published vehicle CAD/FEM assets and audit archive contents."""
from pathlib import Path
from urllib.parse import quote
import requests,json,hashlib,zipfile,concurrent.futures,time
T=Path('cvpr2027/tmp/cad-fem-industrial-search');D=Path('cvpr2027/data');repos={'MohammadHaris13/Formula-SAE-Chassis-Structural-Analysis':'web-cad-fem-fsae-chassis','wingcraft7/go-kart-chassis-fea':'web-cad-fem-gokart-chassis'}
for repo,folder in repos.items():
 d=json.loads((T/(repo.replace('/','--')+'-tree.json')).read_text());R=D/folder;R.mkdir(exist_ok=True);bl=[x for x in d['tree'] if x['type']=='blob' and not x['path'].lower().endswith(('.mp4','.stl'))]
 def f(x):
  url=f'https://raw.githubusercontent.com/{repo}/{d["sha"]}/{quote(x["path"])}';p=R/x['path'];p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists():
   for i in range(3):
    try:
     res=requests.get(url,timeout=45);res.raise_for_status();p.write_bytes(res.content);break
    except Exception:
     if i==2:raise
     time.sleep(1)
  b=p.read_bytes();assert len(b)==x['size'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha'];return {'path':x['path'],'source':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:rows=list(e.map(f,bl))
 (R/'download-manifest.json').write_text(json.dumps({'source':'https://github.com/'+repo,'revision':d['sha'],'license_notice':(R/'LICENSE').read_text() if (R/'LICENSE').exists() else 'No explicit source data license found; local research only.','files':rows,'omitted':'STL geometry mesh and duplicate MP4 clips excluded from selected collection; STL is not native CAD.'},indent=2)+'\n');print(repo,len(rows),sum(x['bytes'] for x in rows),flush=True)
 for p in R.glob('*.wbpz'):
  with zipfile.ZipFile(p) as z:
   assert z.testzip() is None;(R/'archive-inventory.json').write_text(json.dumps([{'member':i.filename,'bytes':i.file_size} for i in z.infolist()],indent=2));print([(i.filename,i.file_size) for i in z.infolist() if i.filename.lower().endswith(('.scdoc','.scdocx','.agdb','.rst','.rth','.stp','.step'))],flush=True)
   out=R/'extracted-original';out.mkdir(exist_ok=True)
   for i in z.infolist():
    if i.is_dir():continue
    q=out/i.filename;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(z.read(i))
