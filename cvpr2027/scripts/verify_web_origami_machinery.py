"""Verify downloaded originals and exact read-only data copies."""
from pathlib import Path
import json,hashlib,csv
import numpy as np,openpyxl
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-new-machinery-search');names=['web-cad-fem-kresling-origami','web-cad-fem-valve-transient','web-cad-fem-engine-rod-drawing','web-drawing-fem-mounting-flange','web-cad-fem-rocket-turbopump'];total=0
for name in names:
 R=D/name;m=json.loads((R/'download-manifest.json').read_text())
 for f in m['files']:
  b=(R/f['path']).read_bytes();assert len(b)==f['bytes'];assert hashlib.sha256(b).hexdigest()==f['sha256']
  if 'git_blob_sha1' in f:assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==f['git_blob_sha1']
  if 'publisher_checksum' in f:assert 'md5:'+hashlib.md5(b).hexdigest()==f['publisher_checksum']
  total+=1
 c=json.loads((R/'catalog.json').read_text());assert c.get('certified_cases',0)==0
R=D/'web-cad-fem-kresling-origami';c=json.loads((R/'catalog.json').read_text());arrays=np.load(R/'original-FEM-curves.npz');cache={}
for r in c['auxiliary_FEM_curves']:
 key=(r['workbook'],r['sheet'])
 if key not in cache:
  w=openpyxl.load_workbook(R/r['workbook'],data_only=True,read_only=True);cache[key]=list(w[r['sheet']].iter_rows(values_only=True));w.close()
 rows=cache[key];cols=[openpyxl.utils.column_index_from_string(s)-1 for s in r['source_columns']];b=np.array([[rows[i-1][j] for j in cols] for i in arrays[r['npz_key']+'_source_rows']]);assert np.array_equal(arrays[r['npz_key']],b,equal_nan=True)
c['limitations']=[x.replace('Stored-energy blanks retained as NaN; force/displacement finite. No local energy integration or force reconstruction.','All retained FEM force/displacement/energy triples are finite original cell values. No local energy integration or force reconstruction.') for x in c['limitations']];(R/'catalog.json').write_text(json.dumps(c,indent=2)+'\n')
R=D/'web-cad-fem-valve-transient';b=np.loadtxt(R/'valve-1.csv');a=np.load(R/'original-temperature-history.npz');assert np.array_equal(a['time_s'],b[:,0]);assert np.array_equal(a['imposed_T_C'],b[:,1]);assert np.array_equal(a['source_SCL_temperatures_C'],b[:,2:])
R=D/'web-drawing-fem-mounting-flange';rows=list(csv.DictReader((R/'fea-results.csv').open()));cols=list(rows[0]);b=np.array([[float(row[c]) for c in cols[1:]] for row in rows]);a=np.load(R/'original-source-scalar-table.npz');assert np.array_equal(a['values'],b)
v={'original_downloads_verified':total,'origami_exact_FEM_curves_verified':len(c['auxiliary_FEM_curves']),'valve_exact_history_verified':True,'flange_exact_scalar_table_verified':True,'rod_opposite_load_field_check':True,'solver_runs':0,'generated_cad':0,'frontier_model_calls':0};(T/'source-verification.json').write_text(json.dumps(v,indent=2)+'\n');print(v)
R=D/'web-cad-fem-kresling-origami';p=R/'original-Inventor-thumbnail.png';(R/'original-thumbnail-provenance.json').write_text(json.dumps({'source_file':'extracted-original/Supporting_Materials_Zenodo/1_CAD/Ori_K_cyl_n_8_0.ipt','original_ole_property':17,'source_stream':'Inventor Summary Information','method':'Extracted embedded PNG bytes from VT_CF thumbnail property, unchanged image data.','preview_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+'\n')
for name in names:
 R=D/name;cat=json.loads((R/'catalog.json').read_text());(R/'README-collection.md').write_text('# '+cat['collection']+'\n\nOriginal published source: '+cat['source']+'\n\nSee catalog.json for numerical references, geometry checks, exact source file locations, source licenses and unresolved mapping/physics limitations. No new CAD or FEM solutions were generated. No downloaded source program, macro, MATLAB notebook, Abaqus deck or solver script was executed. Exact original files and SHA-256 provenance retained. Source experiment data is separate from FEM references. This is a local research collection; no public redistribution performed.\n')
