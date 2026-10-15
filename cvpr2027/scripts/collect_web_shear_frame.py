"""Collect original native models, drawings and numerical reference tables only."""
from pathlib import Path
import requests,json,hashlib,concurrent.futures,time
T=Path('cvpr2027/tmp/cad-fem-industrial-search');R=Path('cvpr2027/data/web-cad-fem-shear-frame');R.mkdir(exist_ok=True);rows=json.loads((T/'shear-selected-file-list.json').read_text());selected=[]
figs=['3D_Frame.png','Beam_col_geo.png','Bottom view.png','Columns (1).png','Plate.png','Top_bottom_view.png','joint_diagram (1).png','front face.png','side face.png','meshed frame.png','Acceleration_comparision.png','Real_Frame.jpg','300mm_Beam (1).png','350mm_Beam (1).png']
for row in rows:
 folder=row['folder']['name']
 for f in row['files']:
  if folder=='Figures Used' and f['filename'] not in figs:continue
  if folder=='MATERIALS' and f['filename'].lower().endswith(('.zip','.rar')):continue
  selected.append((folder,f))
def get(x):
 folder,f=x;c=f['content_details'];p=R/folder/f['filename'];p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  for i in range(3):
   try:
    r=requests.get(c['download_url'],timeout=40);r.raise_for_status();p.write_bytes(r.content);break
   except Exception:
    if i==2:raise
    time.sleep(1)
 b=p.read_bytes();assert len(b)==c['size'];assert hashlib.sha256(b).hexdigest()==c['sha256_hash'];return {'path':str(p.relative_to(R)),'source':c['download_url'],'bytes':len(b),'sha256':c['sha256_hash'],'original_file_id':f['id'],'original_folder_id':f.get('folder_id')}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:manifest=list(e.map(get,selected))
meta=json.loads((T/'shear-frame-meta.json').read_text());(R/'source-metadata.json').write_text(json.dumps(meta,indent=2));(R/'download-manifest.json').write_text(json.dumps({'source':'https://data.mendeley.com/datasets/bxmd7c78zf/3','doi':'10.17632/bxmd7c78zf.3','version':3,'license':'CC BY 4.0, original metadata retained','files':manifest,'selection':'Native Abaqus CAE/JNL damage models, numerical-reference XLSX/code text, selected original CAD/dimension and FEM/experiment figures. Experimental time-history archives and instrument photos omitted.'},indent=2)+'\n');print(len(manifest),sum(x['bytes'] for x in manifest),[(x['path'],x['bytes']) for x in manifest],flush=True)
