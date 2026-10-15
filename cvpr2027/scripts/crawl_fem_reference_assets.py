"""Inventory existing source assets; never solve or synthesize engineering data."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse
import hashlib,html,json,re,requests,zipfile
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/femcad-hard-v1'
CACHE=ROOT/'tmp/femcad-reference-assets'
CACHE.mkdir(exist_ok=True)
BASE='https://www.comsol.com'
EXTRA={
 'FEMCAD-ADV-001':BASE+'/model/contact-analysis-of-a-rubber-boot-seal-109791',
 'FEMCAD-ADV-002':BASE+'/model/piezoelectric-valve-21061',
 'FEMCAD-ADV-003':BASE+'/model/creep-analysis-of-a-turbine-stator-blade-102161',
 'FEMCAD-ADV-004':BASE+'/model/vibrations-in-a-compound-gear-train-36291',
 'FEMCAD-ADV-005':BASE+'/model/muffler-with-perforates-1843'}
def clean(x):return ' '.join(html.unescape(re.sub('<[^>]+>',' ',x)).split())
def one(t):
 folder=CACHE/t['id'];folder.mkdir(exist_ok=True)
 gallery=t.get('gallery_url') or EXTRA[t['id']]
 record={'id':t['id'],'title':t['title'],'gallery_url':gallery,'source_url':t['source_url'],'files':[],
 'ground_truth_status':'No numerical arrays, convergence certification or grading tolerance inferred from filenames.'}
 try:
  r=requests.post(BASE+'/models/get-the-files',data={'id':gallery.rsplit('-',1)[-1]},timeout=45);r.raise_for_status()
  (folder/'file-listing.json').write_text(r.text)
  record['listing_sha256']=hashlib.sha256(r.content).hexdigest()
  s=r.json()['data']['html']
  entries=[]
  for li in re.findall(r'<li\b[^>]*>.*?</li>',s,re.S):
   u=re.search(r'href="([^\"]*\/model\/download\/[^\"]+)"',li)
   v=re.search(r'\bcomsol(\d\d)\b',li)
   if not u:continue
   url=urljoin(BASE,html.unescape(u[1]));name=urlparse(url).path.rsplit('/',1)[-1]
   version=v[1][0]+'.'+v[1][1] if v else None
   size=re.search(r'-\s*([\d.]+)\s*(KB|MB|GB)',clean(li))
   mb=float(size[1])*{'KB':.001,'MB':1,'GB':1000}[size[2]] if size else None
   entries.append({'name':name,'url':url,'version':version,'listed_size_mb':mb})
  target=t['source_url'].split('/')[3]
  matching=[f for f in entries if f['version']==target]
  selected=matching or [f for f in entries if f['version']==max((a['version'] or '' for a in entries),default='')]
  record['tutorial_version']=target;record['exact_version_listing_found']=bool(matching)
  record['all_version_file_count']=len(entries)
  for f in selected:
   ext=Path(f['name']).suffix.lower()
   f['role']='solver_model' if ext=='.mph' and not any(k in f['name'] for k in ['geom','mesh']) else 'geometry_or_mesh_model' if ext=='.mph' else 'tutorial' if ext=='.pdf' else 'supporting_file'
   f['availability']='listed; not yet probed'
   if ext=='.pdf':f['availability']='listed tutorial';record['files'].append(f);continue
   limit=150_000_000 if t['id']=='FEMCAD-ADV-001' and f['name']=='rubber_boot_seal.mph' else 15_000_000 if f['role']=='solver_model' else 5_000_000
   save=f['listed_size_mb'] is not None and f['listed_size_mb']*1_000_000<limit
   resp=requests.get(f['url'],stream=True,timeout=45)
   f.update(http_status=resp.status_code,final_url=resp.url,content_type=resp.headers.get('Content-Type'))
   chunks=resp.iter_content(65536);first=next(chunks,b'')
   if resp.ok and (ext!='.mph' or first.startswith(b'PK')) and 'text/html' not in resp.headers.get('Content-Type',''):
    f['availability']='public download verified'
    if save:
     path=folder/f['name'];h=hashlib.sha256();length=0
     with path.open('wb') as out:
      for b in (first,):out.write(b);h.update(b);length+=len(b)
      for b in chunks:
       length+=len(b)
       if length>limit:break
       out.write(b);h.update(b)
     if length<=limit:
      f.update(local=str(path.relative_to(ROOT)),sha256=h.hexdigest(),downloaded_bytes=length)
      if ext in ['.mph','.zip'] and zipfile.is_zipfile(path):
       with zipfile.ZipFile(path) as z:
        names=z.namelist();(folder/(f['name']+'.archive-index.json')).write_text(json.dumps(names,indent=2))
        f['archive_entry_count']=len(names)
        f['solution_named_entries']=[n for n in names if re.search(r'(^|/)solution\w*\.mphbin$',n,re.I)][:30]
        f['mesh_named_entries']=[n for n in names if re.search(r'(^|/)x?mesh\w*\.mphbin$',n,re.I)][:15]
        f['solution_contents_validation']='Not opened in COMSOL; archive names alone do not establish physical accuracy or convergence.'
     else:path.unlink();f['download_note']='Exceeded bounded download size; public stream verified only'
   else:
    f['availability']='login/blocked/invalid download'
    f['response_preview']=first[:300].decode(errors='replace')
   resp.close();record['files'].append(f)
  (folder/'inventory.json').write_text(json.dumps(record,indent=2)+'\n')
  print(t['id'],len(record['files']),'files',sum(f['availability']=='public download verified' for f in record['files']),'public',flush=True)
 except Exception as e:
  record['error']=type(e).__name__+': '+str(e)
  print(t['id'],record['error'],flush=True)
 return record
if __name__=='__main__':
 d=json.loads((DATA/'advanced-source-studies.json').read_text())
 with ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(one,d['studies']))
 result={'crawled_utc':datetime.now(timezone.utc).isoformat(),'scope':'Only existing downloadable files from the exact 50 source studies; no simulated or generated FEM data','studies':rows}
 (DATA/'reference-assets.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Completed',len(rows),'studies',flush=True)
