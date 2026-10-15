"""Inspect published archives and saved fields without running source code/solvers."""
from pathlib import Path
import zipfile,json,hashlib,subprocess,sys
import numpy as np
R=Path('cvpr2027/data/web-cad-fem-composite-dynamics'); B=R/'pydpf-composites'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if len(sys.argv)>1:
 from ansys.mapdl import reader
 case=sys.argv[1];p=B/case;r=reader.read_binary(p/'file.rst')
 meta={'reader':'ansys-mapdl-reader 0.56.0','reader_type':type(r).__name__,'nsets':r.nsets,'labels':r.time_values.tolist(),'mesh_nodes':r.mesh.n_node,'mesh_elements':r.mesh.n_elem,'analysis_code':int(r._resultheader['kan']),'binary_units':str(r._resultheader['units']),'states':[]}
 for i,label in enumerate(r.time_values):
  arrays={'mesh_ids':r.mesh.nnum,'mesh_coordinates':r.mesh.nodes}; state={'index':i,'source_label':float(label)}
  for method in ['nodal_displacement','nodal_stress','nodal_temperature']:
   try:
    ids,a=getattr(r,method)(i);arrays[method+'_ids']=ids;arrays[method]=a
    m=np.isfinite(a);info={'shape':list(a.shape),'finite_entries':int(m.sum()),'entries':a.size,'unique_ids':len(np.unique(ids))==len(ids)}
    if m.any():info.update(finite_min=float(a[m].min()),finite_max=float(a[m].max()))
    if method=='nodal_displacement':
     val=float(np.linalg.norm(a[:,:3],axis=1).max());info['maximum_translation_source_units']=val if np.isfinite(val) else None
    state[method]=info
   except Exception as e:state[method]={'error':str(e)}
  out=p/f"{'UNVERIFIED-' if case=='random_vibration' else ''}saved-reader-state-{i}.npz";np.savez_compressed(out,**arrays)
  with np.load(out) as z:
   for k,v in arrays.items():assert np.array_equal(z[k],v,equal_nan=True)
  state['npz']=out.name;state['sha256']=sha(out);meta['states'].append(state)
 (p/'reader-audit.json').write_text(json.dumps(meta,indent=2)+'\n');sys.exit(0)
records=[]
for p in sorted(B.iterdir()):
 w=next(p.glob('*.wbpz'));native=p/'extracted-native';native.mkdir(exist_ok=True)
 with zipfile.ZipFile(w) as z:
  assert z.testzip() is None
  inv=[{'member':i.filename,'bytes':i.file_size} for i in z.infolist()];(p/'archive-inventory.json').write_text(json.dumps(inv,indent=2))
  for i in z.infolist():
   if i.filename.lower().endswith(('.scdoc','.agdb','.stp','.step','.acph5','.xml','.wbpj')):
    q=native/Path(i.filename).name
    if not q.exists():q.write_bytes(z.read(i))
 cad=[]
 for sc in native.glob('*.scdoc'):
  with zipfile.ZipFile(sc) as z:
   g=[{'member':i.filename,'bytes':i.file_size} for i in z.infolist() if i.filename.endswith('.sab')]
   assert g and all(x['bytes']>100 for x in g)
   (native/'original-cad-thumbnail.png').write_bytes(z.read('docProps/thumbnail.png'))
   cad.append({'file':str(sc.relative_to(R)),'sha256':sha(sc),'serialized_acis_geometry':g,'independent_brep_import':False})
 rec={'id':p.name,'native_cad':cad,'original_dimensioned_drawing_verified':False,'raw_solver_result':[str(x.relative_to(R)) for x in p.glob('*.rst')]+[str(x.relative_to(R)) for x in p.glob('d3plot*')],'certified_cases':0}
 if (p/'file.rst').exists():
  proc=subprocess.run([sys.executable,__file__,p.name],capture_output=True,text=True,timeout=90)
  (p/'reader-log.txt').write_text(proc.stdout+proc.stderr)
  rec['reader_exit_code']=proc.returncode
  if proc.returncode==0:rec['reader_audit']=json.loads((p/'reader-audit.json').read_text())
  else:rec['reader_status']='Read-only parser failed; original RST retained. No trusted extracted fields.'
 if (native/'step-audit.json').exists():rec['neutral_step_audit']=json.loads((native/'step-audit.json').read_text())
 records.append(rec)
cat={'collection':'Published native CAD with composite impact, cyclic, thermal, vibration and fatigue-context results','source':'https://github.com/ansys/example-data','revision':'8ef505f6ef699eeec68a16001df91ba353342f40','date':'2026-10-12','license':'MIT, original LICENSE retained','source_project_candidates':len(records),'native_cad_saved_result_candidates':len(records),'complex_industrial_geometry_candidate_ids':['lsdyna_bird_strike'],'simple_geometry_complex_physics_candidate_ids':['cyclic_symmetry','thermal_solid','random_vibration','fatigue'],'certified_cases':0,'solver_runs':0,'frontier_model_calls':0,'locally_generated_cad':0,'records':records,'limitations':['Source Workbench archive and separate result siblings must still be checked for exact geometry/setup matching.','Native SpaceClaim files contain nonempty serialized ACIS geometry and original thumbnails; independent BREP validity is unverified except cyclic STEP.','Units, loads, layup integration-point mapping and convergence require review before numerical scoring.','No original dimensioned engineering drawings verified. Supplied-CAD and drawing-reconstruction tracks remain separate.','Fatigue-context RST is a static stress solution, not a verified stored fatigue-life field.','Cyclic reader extracts base-sector fields by default. Never compare with expanded sectors without mapping.','Nodal stresses recovered by legacy reader average element-nodal stress at shared nodes; preserve missing-data masks.','LS-DYNA lasso-python 2.0.4 reported shell-variable layout mismatch and a plastic-strain reshape failure. All its extracted arrays are exploratory and excluded from scoring until independently verified.','Random-vibration legacy-reader produced nonfinite/implausible displacements. All extracted vibration arrays are exploratory and excluded from scoring; original RST retained.','Finite parser values alone do not validate physical correctness.']}
(R/'catalog.json').write_text(json.dumps(cat,indent=2)+'\n')
p=B/'lsdyna_bird_strike'/'saved-d3plot-arrays.npz'
if p.exists():p.rename(p.with_name('UNVERIFIED-lasso-parser-arrays.npz'))
print(json.dumps({'records':[(r['id'],r.get('reader_exit_code'),len(r['native_cad'])) for r in records]}))
