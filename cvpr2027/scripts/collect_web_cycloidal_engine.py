"""Collect exact published mechanical CAD/FEM assets. Never execute source scripts."""
from pathlib import Path
from urllib.parse import quote
import requests,json,hashlib,concurrent.futures,time
T=Path('cvpr2027/tmp/cad-fem-machine-parts-search');D=Path('cvpr2027/data')
repos={'jagathsrujan/3d-printable-cycloidal-drive':'web-cad-fem-cycloidal-drive','AryaDuhan/HT-Project-main':'web-cad-fem-engine-tbc','adhikaryharsha23-cpu/Piston-Connecting-Rod-FEA':'web-cad-fem-piston-drawing'}
for repo,folder in repos.items():
 d=json.loads((T/(repo.replace('/','--')+'-tree.json')).read_text());R=D/folder;R.mkdir(exist_ok=True)
 if 'cycloidal' in repo:bl=[x for x in d['tree'] if x['type']=='blob' and (x['path'].lower().endswith(('.step','.fcstd','.frd','.inp','.sta','.cvg','.dat','.png','.md','.json')) or x['path']=='fem/fix_cload_units.py') and not x['path'].endswith('SESSION_PROMPT.md')]
 elif 'HT-Project' in repo:bl=[x for x in d['tree'] if x['type']=='blob' and (x['path'].startswith(('CAD files/','Images/','ansys reports/','output data/')) or x['path'] in ['README.md','TBC_data.csv','mock_tbc_data.csv','tbc_optimizer.py','generate_data.py','transient.py'])]
 else:bl=[x for x in d['tree'] if x['type']=='blob' and not x['path'].lower().endswith('.wmv')]
 def fetch(x):
  url=f'https://raw.githubusercontent.com/{repo}/{d["sha"]}/{quote(x["path"],safe="/")}';p=R/x['path'];p.parent.mkdir(parents=True,exist_ok=True)
  for i in range(3):
   try:
    if p.exists():b=p.read_bytes()
    else:r=requests.get(url,timeout=55);r.raise_for_status();b=r.content
    assert len(b)==x['size'],x['path'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha'],x['path'];p.write_bytes(b);return {'path':x['path'],'source':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob_sha1':x['sha']}
   except Exception:
    if i==2:raise
    time.sleep(1)
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as e:rows=list(e.map(fetch,bl))
 (R/'download-manifest.json').write_text(json.dumps({'source':'https://github.com/'+repo,'revision':d['sha'],'files':rows,'license_status':'Source notices preserved; no public redistribution authorization inferred. Local research only.','policy':'No source script executed, no generated CAD, no FEM solve, no model calls.'},indent=2)+'\n');print(repo,len(rows),sum(x['bytes'] for x in rows),flush=True)
# Explicitly unpaired turbine lead: retain only source notices and matching-limit evidence.
R=D/'web-cad-fem-held-machine-leads';R.mkdir(exist_ok=True)
held={'source':'https://github.com/Tanish0224/HPT-Internal-Cooling','revision':'201d27aaac11fefc66c47763e6ddb1e5311c3af6','status':'Excluded: published CAD is not the second-design geometry used for screening FEA; second-design model not published.','rights':'Assets all rights reserved; viewing/downloading for discussion permitted, reuse requires author permission. No CAD or figures packaged.','paired_candidates':0}
for p in ['ASSET_NOTICE.md','analysis_context--README.md','history--README.md']:(R/p).write_bytes((T/p).read_bytes())
(R/'catalog.json').write_text(json.dumps(held,indent=2)+'\n')
