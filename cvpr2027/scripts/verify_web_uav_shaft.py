"""Check downloaded publisher hashes and source-reference copies."""
from pathlib import Path
import json,hashlib,zipfile,email
import numpy as np
from bs4 import BeautifulSoup
from ansys.mapdl import reader
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-rotating-machinery-search');names=['web-cad-fem-uav-assembly','web-cad-fem-quadcopter-dynamics','web-cad-fem-composite-pipe','web-cad-fem-differential-shaft','web-cad-fem-rear-axle'];n=0
for name in names:
 R=D/name;m=json.loads((R/'download-manifest.json').read_text())
 for r in m['files']:
  b=(R/r['path']).read_bytes();assert len(b)==r['bytes'];assert hashlib.sha256(b).hexdigest()==r['sha256'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['git_blob_sha1'];n+=1
 json.loads((R/'catalog.json').read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
R=D/names[1];lf=json.loads((R/'original-LFS-download-manifest.json').read_text());h=hashlib.sha256()
with (R/lf['file']).open('rb') as f:
 for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
assert h.hexdigest()==lf['sha256'] and (R/lf['file']).stat().st_size==lf['bytes']
with zipfile.ZipFile(R/lf['file']) as z:assert z.testzip() is None
z=np.load(R/'original-modal-frequency-references.npz');assert np.max(abs(z['source_RST_frequency_Hz']-z['source_rounded_report_frequency_Hz']))<.0005;r=reader.read_binary(str(R/'extracted-original/complete_analysis_drone_files/dp0/SYS-1/MECH/file.rst'),read_mesh=False);assert np.array_equal(r.time_values,z['source_RST_frequency_Hz'])
R=D/names[0];part=next(x for x in email.message_from_bytes((R/'report.mht').read_bytes()).walk() if x.get_content_type()=='text/html');html=part.get_payload(decode=True).decode('cp1252');assert html==(R/'original-report-extracted.html').read_bytes().decode('utf-8');soup=BeautifulSoup(html,'html.parser');tables=[[[c.get_text(' ',strip=True) for c in r.find_all(['th','td'],recursive=False)] for r in t.find_all('tr')] for t in soup.find_all('table')];z=np.load(R/'original-report-scalar-references.npz');assert np.array_equal(z['source_numeric_rows'],np.array([[float(x) for x in tables[i][1]] for i in [34,35,36,37]]))
R=D/names[2]
with zipfile.ZipFile(R/'composite pipe.wbpz') as z:
 assert z.testzip() is None
 for f in (R/'extracted-original').rglob('*'):
  if f.is_file():assert f.read_bytes()==z.read(str(f.relative_to(R/'extracted-original')))
z=np.load(R/'exploratory-archive-displacement-held.npz');assert np.isfinite(z['source_U_mm']).all() and z['source_U_mm'].shape==(255,3)
v={'original_repository_files_verified':n,'additional_publisher_LFS_archives_verified':1,'original_downloads_verified':n+1,'LFS_sha256_size_CRC_verified':True,'UAV_original_MHT_scalar_table_copies_verified':True,'quad_modal_frequencies_original_header_and_rounding_match':True,'pipe_archive_extraction_original_bytes_verified':True,'pipe_displacement_exploratory_not_scoring_admitted':True,'legacy_stress_decoder_failed_and_excluded':True,'new_solver_runs':0,'generated_cad':0,'model_calls':0,'certified_cases':0};(T/'source-verification.json').write_text(json.dumps(v,indent=2)+'\n');print(v,flush=True)
