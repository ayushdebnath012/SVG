"""Download published CAD/FEM sources, keeping original bytes and provenance."""
from pathlib import Path
from urllib.parse import quote
import requests,json,hashlib,zipfile,concurrent.futures,time
T=Path('cvpr2027/tmp/cad-fem-new-machinery-search');D=Path('cvpr2027/data')
repo_map={'AakashNandy/Liquid-Rocket-Engine-Turbopump-Design-Optimization-Report-Code-':'web-cad-fem-rocket-turbopump','divyamshi-07/IC-engine-Solidworks':'web-cad-fem-engine-rod-drawing','ethanzelig6/ml-fea-surrogate-model':'web-drawing-fem-mounting-flange'}
for repo,folder in repo_map.items():
 R=D/folder;R.mkdir(exist_ok=True);tree=json.loads((T/(repo.replace('/','--')+'-tree.json')).read_text());blobs=[x for x in tree['tree'] if x['type']=='blob' and not x['path'].endswith(('.ipynb','.m'))]
 def f(x):
  url=f'https://raw.githubusercontent.com/{repo}/{tree["sha"]}/{quote(x["path"],safe="/")}';p=R/x['path'];p.parent.mkdir(parents=True,exist_ok=True)
  for i in range(3):
   try:
    b=p.read_bytes() if p.exists() else requests.get(url,timeout=50).content;assert len(b)==x['size'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha'];p.write_bytes(b);return {'path':x['path'],'source':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob_sha1':x['sha']}
   except Exception:
    if i==2:raise
    time.sleep(1)
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:rows=list(e.map(f,blobs))
 (R/'download-manifest.json').write_text(json.dumps({'source':'https://github.com/'+repo,'revision':tree['sha'],'files':rows,'omitted':'Source MATLAB and training notebooks omitted; no source program executed.'},indent=2)+'\n');print(folder,len(rows),sum(x['bytes'] for x in rows),flush=True)
 for zf in R.glob('*.zip'):
  with zipfile.ZipFile(zf) as z:
   assert z.testzip() is None;(R/'original-archive-inventory.json').write_text(json.dumps([{'member':x.filename,'bytes':x.file_size} for x in z.infolist()],indent=2));out=R/'extracted-original';out.mkdir(exist_ok=True)
   for item in z.infolist():
    if item.is_dir():continue
    p=out/item.filename;assert out.resolve() in p.resolve().parents;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(item))
R=D/'web-cad-fem-kresling-origami';R.mkdir(exist_ok=True);m=json.loads((T/'zenodo-kresling.json').read_text());(R/'source-metadata.json').write_text(json.dumps(m,indent=2));f=m['files'][0];url=f['links']['self'];p=R/f['key']
if not p.exists():r=requests.get(url,timeout=55);r.raise_for_status();p.write_bytes(r.content)
b=p.read_bytes();assert len(b)==f['size'];assert 'md5:'+hashlib.md5(b).hexdigest()==f['checksum'];(R/'download-manifest.json').write_text(json.dumps({'source':'https://zenodo.org/records/15118000','DOI':'10.5281/zenodo.15118000','files':[{'path':p.name,'source':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'publisher_checksum':f['checksum']}]},indent=2)+'\n')
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None;(R/'original-archive-inventory.json').write_text(json.dumps([{'member':x.filename,'bytes':x.file_size} for x in z.infolist()],indent=2));out=R/'extracted-original';out.mkdir(exist_ok=True)
 for item in z.infolist():
  if item.is_dir():continue
  q=out/item.filename;assert out.resolve() in q.resolve().parents;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(z.read(item))
print('Kresling',len(b),[(i['member'],i['bytes']) for i in json.loads((R/'original-archive-inventory.json').read_text())],flush=True)
