"""Resolve publisher Git LFS archive and extract original files without execution."""
from pathlib import Path
import json,hashlib,requests,zipfile
R=Path('cvpr2027/data/web-cad-fem-quadcopter-dynamics');T=Path('cvpr2027/tmp/cad-fem-rotating-machinery-search');p=R/'02_ANSYS/04_Workbench_Archive/archive_DRONE.wbpz';s=p.read_text();lines=s.splitlines();expected=next(x.split(':',1)[1] for x in lines if x.startswith('oid sha256:'));size=int(next(x.split()[1] for x in lines if x.startswith('size ')));url='https://media.githubusercontent.com/media/ayushwug24me-sketch/quadcopter-drone-cad-fea-analysis/main/02_ANSYS/04_Workbench_Archive/archive_DRONE.wbpz';out=R/'original-LFS-archive_DRONE.wbpz'
if not out.exists():
 r=requests.get(url,stream=True,timeout=(7,50));r.raise_for_status();h=hashlib.sha256();nn=0
 with out.with_suffix('.download').open('wb') as f:
  for b in r.iter_content(4*1024*1024):h.update(b);f.write(b);nn+=len(b)
 assert nn==size and h.hexdigest()==expected;out.with_suffix('.download').rename(out)
h=hashlib.sha256()
with out.open('rb') as f:
 for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
assert out.stat().st_size==size and h.hexdigest()==expected
(R/'original-LFS-download-manifest.json').write_text(json.dumps({'file':out.name,'source_url':url,'bytes':size,'sha256':expected,'publisher_pointer':str(p.relative_to(R))},indent=2)+'\n')
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None;(R/'original-LFS-archive-inventory.json').write_text(json.dumps([{'member':i.filename,'bytes':i.file_size} for i in z.infolist()],indent=2)+'\n');dest=R/'extracted-original';dest.mkdir(exist_ok=True)
 for i in z.infolist():
  if i.is_dir():continue
  q=dest/i.filename;assert dest.resolve() in q.resolve().parents;q.parent.mkdir(parents=True,exist_ok=True)
  with z.open(i) as src,q.open('wb') as dst:
   for b in iter(lambda:src.read(8*1024*1024),b''):dst.write(b)
print('LFS bytes, SHA256 and archive CRC verified',size,flush=True)
