"""Read source FreeCAD archives, BREP topology and published nonlinear tables; never execute proxies."""
import sys,json,re,hashlib,zipfile
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent/'cadfem_bench'))
from fcstd import FCStd
import common as C
from render import render
root=Path(__file__).resolve().parents[1]/'data/web-cad-fem-fcvm-breadth'
man=json.loads((root/'download-manifest.json').read_text());rows=[]
for name in man['cases']:
 cad=root/'freeCAD files'/(name+'.FCStd');out=root/'output files'/(name+'.out');ctrl=root/'control files'/(name+'.inp')
 assert cad.exists() and out.exists() and ctrl.exists()
 d=FCStd(cad);assert d.zip.testzip() is None
 shapes=[]
 objs=list(dict.fromkeys(d.value(o,'Part') for o in d.data if 'Mesh' in o and d.value(o,'Part')))
 for obj in objs:
  try:member=d.shape_member(obj)
  except Exception:continue
  dest=root/'extracted-original'/name/(obj+'.brp');d.extract(member,dest)
  sh=C.read_shape(dest);audit=C.shape_summary(sh)
  shapes.append({'object':obj,'source_member':member,'extracted_path':str(dest.relative_to(root)),'sha256':C.sha256(dest),**audit})
  if audit['valid'] and audit['solids'] and len(shapes)==1:render(dest,root/'inspection'/f'{name}-CAD.png')
 properties=[]
 for obj in d.data:
  if 'Constraint' in obj or 'Material' in obj:
   properties.append({'object':obj,'type':d.types.get(obj),'references':d.links(obj),'properties':{k:v[1] for k,v in d.props(obj).items() if k not in ('ExpressionEngine','Label2','Proxy','Visibility','Scale','Points','Normals')}})
 text=out.read_text();line=next((i for i,s in enumerate(text.splitlines()) if s.strip().startswith('Gauss point')),None)
 table=[]
 if line is not None:
  for s in text.splitlines()[line+1:]:
   try:v=[float(x) for x in s.split()]
   except ValueError:continue
   if len(v)==12:table.append(v)
 assert table,name
 arr=np.array(table);assert np.isfinite(arr).all()
 labels=['gauss_point','x','y','z','load_factor','reported_displacement','peeq','pressure','svmises','triax','eps_cr','csr_max']
 # Exact rounded source table, no interpolation and no new solve.
 np.savez_compressed(root/'extracted-original'/name/'published-table.npz',table=arr,columns=np.array(labels))
 bc=root/'extracted-original'/name/'native-properties.json';bc.write_text(json.dumps(properties,indent=2))
 mode=re.search(r'analysis type:\s*([^\n]+)',text).group(1).strip();eigs=re.search(r'elastic buckling factors:\s*\[([^\]]*)\]',text)
 rec={'id':'FCVM-'+name.replace(' ','_'),'name':name,'source':'https://github.com/'+man['repo'],'revision_tree':man['revision_tree'],'native_CAD':str(cad.relative_to(root)),'published_FEM_output':str(out.relative_to(root)),'control_file':str(ctrl.relative_to(root)),'analysis_type':mode,'native_shapes':shapes,'published_table_rows':len(table),'published_columns':labels,'first_published_row':table[0],'last_published_row':table[-1],'maximum_published_load_factor':float(arr[:,4].max()),'published_buckling_factors':([float(x) for x in eigs.group(1).split()] if eigs else []),'status':'held_source_pair','grading_blockers':['Match the selected native analysis, controls and output revision; source model names alone do not prove correspondence.','Resolve displacement extraction, load-factor normalization, initial imperfection and material overrides from the source solver before defining a portable prompt.','No independent nonlinear replay/convergence validation; rounded output rows are not high-precision field truth.'],'original_dimensioned_drawing':False,'source_program_executed':False,'original_VTK':None}
 vtk=root/'output files'/(name+'.vtk')
 if vtk.exists():
  import pyvista as pv
  m=pv.read(vtk);rec['original_VTK']={'path':str(vtk.relative_to(root)),'points':m.n_points,'cells':m.n_cells,'bounds':list(m.bounds),'arrays':{k:{'shape':list(m[k].shape),'finite':bool(np.isfinite(m[k]).all())} for k in m.array_names}}
 rows.append(rec)
cat={'collection':'Published fcVM native CAD and nonlinear analysis expansion','source':'https://github.com/'+man['repo'],'revision_tree':man['revision_tree'],'source_pair_candidates':len(rows),'active_benchmark_admissions':0,'locally_generated_CAD':0,'new_reference_solves':0,'counting_note':'Named source pairs, not independent families; beam variants and transition revisions are not counted as new physics families.','records':rows}
(root/'catalog.json').write_text(json.dumps(cat,indent=2)+'\n');print(json.dumps({'pairs':len(rows),'valid_native_shapes':sum(s['valid'] for r in rows for s in r['native_shapes']),'shapes':sum(len(r['native_shapes']) for r in rows),'table_rows':sum(r['published_table_rows'] for r in rows),'VTK_pairs':sum(bool(r['original_VTK']) for r in rows)},indent=2))
