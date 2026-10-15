"""Verify provenance and read-only copies against original source bytes/cells."""
from pathlib import Path
import hashlib,json,zipfile,csv
import numpy as np,openpyxl
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-additional-systems-search');names=['web-cad-fem-pneumatic-gripper','web-cad-fem-finray-contact','web-cad-fem-leafspring-modal','web-cad-fem-bistable-gripper-held'];n=0
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
for name in names:
 R=D/name;m=json.loads((R/'download-manifest.json').read_text())
 for r in m['files']:
  b=(R/r['path']).read_bytes();assert len(b)==r['bytes'];assert hashlib.sha256(b).hexdigest()==r['sha256'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['git_blob_sha1'];n+=1
 json.loads((R/'catalog.json').read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
R=D/names[0];a=json.loads((R/'release-download-manifest.json').read_text());assert sha(R/a['file'])==a['sha256'];assert 'sha256:'+a['sha256']==a['publisher_digest'];assert (R/a['file']).stat().st_size==a['bytes']
with zipfile.ZipFile(R/a['file']) as z:
 assert z.testzip() is None
 for f in (R/'extracted-original').rglob('*'):
  if f.is_file() and f.suffix.lower()!='.rst':assert f.read_bytes()==z.read(str(f.relative_to(R/'extracted-original')))
summary=list(csv.DictReader((R/'results/summary.csv').open()));z=np.load(R/'original-summary-values.npz');assert np.array_equal(z['values'],np.array([[float(r[c]) for c in z['columns']] for r in summary]))
w=openpyxl.load_workbook(R/'results/gripper_fea_results.xlsx',data_only=True)
for sheet,t in json.loads((R/'original-workbook-cell-references.json').read_text()).items():
 for cell,value in t['cells'].items():assert w[sheet][cell].value==value
R=D/names[1];cat=json.loads((R/'catalog.json').read_text());z=np.load(R/cat['original_displacement_cache']['file']);assert z['disp'].shape==(44,26470,3) and np.isfinite(z['disp']).all();mesh=np.load(R/'original-mesh-node-map.npz');assert np.array_equal(mesh['source_node_ids'],z['nnum'][:-1]);assert int(mesh['source_rigid_ball_pilot_id'])==int(z['nnum'][-1])
for t in cat['CSV_tables']:
 rr=list(csv.DictReader((R/t['file']).open(encoding='utf-8-sig')));assert len(rr)==t['rows'] and rr[0]==t['first_source_row'] and rr[-1]==t['last_source_row']
R=D/names[2]
with zipfile.ZipFile(R/'MECHANICAL VIBRATION.pptx') as z:
 for f in (R/'original-presentation-evidence').iterdir():assert f.read_bytes()==z.read('ppt/media/'+f.name)
v={'original_repository_files_verified':n,'original_release_verified':1,'original_downloads_verified':n+1,'publisher_release_sha256_verified':True,'raw_archive_CRC_verified':True,'pneumatic_summary_CSV_and_workbook_cells_verified':True,'FinRay_source_cache_finite_and_mesh_node_ID_mapping_verified':True,'FinRay_CSVs_checked':12,'FinRay_byte_unique_CSVs':cat['byte_unique_CSVs'],'original_PPT_media_roundtrip_verified':True,'new_solver_runs':0,'generated_cad':0,'model_calls':0,'certified_cases':0};(T/'source-verification.json').write_text(json.dumps(v,indent=2)+'\n');print(v,flush=True)
