from pathlib import Path
import json,csv,zipfile,struct,xml.etree.ElementTree as ET,numpy as np,cadquery as cq
from OCP.BRep import BRep_Builder
from OCP.BRepTools import BRepTools
from OCP.TopoDS import TopoDS_Shape
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/web-cadworld-fem';T=ROOT/'tmp/cad-benchmark-search/cadworld-brep';T.mkdir(exist_ok=True)
records=[]
for num in [1,2,3]:
 cid=f'freecad-fem-{num:03}';f=D/f'evaluation_examples/fixtures/fem/{cid}.FCStd';csvpath=D/f'evaluation_examples/fixtures/fem/{cid}.csv';task=json.loads((D/f'evaluation_examples/examples/fem/{cid}.json').read_text())
 with zipfile.ZipFile(f) as z:
  assert z.testzip() is None
  doc=ET.fromstring(z.read('Document.xml'));sname='Body.Shape.brp';out=T/(cid+'.brp');out.write_bytes(z.read(sname));sh=TopoDS_Shape();BRepTools.Read_s(sh,str(out),BRep_Builder());shape=cq.Shape.cast(sh);assert shape.isValid()
  data={}
  for k in ['DisplacementLengths','vonMises']:
   b=z.read(k);count=struct.unpack('<I',b[:4])[0];a=np.frombuffer(b[4:],dtype='<f8');assert count==len(a) and np.isfinite(a).all();data[k]=dict(count=count,min=float(a.min()),max=float(a.max()))
  material={};loads=[];refs=[]
  for obj in doc.findall('.//ObjectData/Object'):
   for prop in obj.findall('./Properties/Property'):
    name=prop.attrib.get('name')
    if name=='Material':material={x.attrib['key']:x.attrib['value'] for x in prop.findall('./Map/Item') if x.attrib['key'] in ['YoungsModulus','PoissonRatio','Density','Name']}
    if name=='Force':loads.append(dict(object=obj.attrib['name'],internal_force_kg_mm_s2=float(prop.find('Float').attrib['value']),force_N=float(prop.find('Float').attrib['value'])*.001))
    if name=='References' and obj.attrib['name'] in ['ConstraintFixed','ConstraintForce']:refs.append(dict(object=obj.attrib['name'],links=[x.attrib for x in prop.findall('./LinkSubList/Link')]))
  arrays={k:data[k] for k in data};members=z.namelist()
 with csvpath.open() as h:
  r=csv.reader(h);header=next(r);a=np.array([[float(v) for v in row] for row in r]);assert np.isfinite(a).all()
 assert len(a)==data['vonMises']['count']
 stats={n:dict(min=float(a[:,i].min()),max=float(a[:,i].max())) for i,n in enumerate(header)}
 assert np.isclose(stats['Displacement Magnitude']['max']*1000,data['DisplacementLengths']['max'],rtol=1e-5)
 assert np.isclose(stats['von Mises Stress']['max']/1e6,data['vonMises']['max'],rtol=1e-5)
 original_rules=task['evaluator']['expected'][1]['rules'];checks=[]
 for col,rules in original_rules['columns'].items():
  for key,x in rules.items():checks.append(dict(column=col,statistic=key,published_expected=x['expected'],measured=stats[col][key],within_source_5_percent=bool(np.isclose(stats[col][key],x['expected'],rtol=.05))))
 assert all(x['within_source_5_percent'] for x in checks)
 records.append(dict(id=cid,task_name={1:'Multi-feature mechanical part under end load',2:'Elliptical chain-link tension',3:'Basic stress-test sample'}[num],complexity={1:'Multi-feature geometry; linear statics',2:'Curved link geometry; linear statics, no link-link contact verified',3:'Basic specimen, retained separately from complex cases'}[num],cad=f'evaluation_examples/fixtures/fem/{cid}.FCStd',input_cad=f'evaluation_examples/fixtures/precondition/{cid}-precondition.FCStd',fem_csv=f'evaluation_examples/fixtures/fem/{cid}.csv',task_json=f'evaluation_examples/examples/fem/{cid}.json',instruction=task['instruction'],geometry=dict(valid=True,solids=len(shape.Solids()),faces=len(shape.Faces()),brep_member=sname),material=material,loads=loads,boundary_references=refs,csv_rows=len(a),csv_columns=header,csv_statistics=stats,source_native_arrays=arrays,csv_units=dict(coordinates='mm',displacement='m, corroborated by native FCStd displacement array in mm',stress='Pa, corroborated by native FCStd stress array in MPa'),publisher_evaluator_checks=checks,has_saved_fem_results=all(x in members for x in ['vonMises','DisplacementVectors','Data.vtu']),original_dimensioned_drawing_verified=False,source_image_available=num in [1,2],scoring_status='Held: independent replay, physical validity and drawing completeness review pending',limitations=['Publisher saved FEM arrays and CSV; no solver run performed locally.','Source evaluator uses 5% tolerance; this is a source software-workflow tolerance, not certified engineering accuracy.','Large elastic stress/displacement values require physical validity review; do not interpret as validated strength/failure labels.']+(['Not a complex engineering drawing/task; basic specimen.'] if num==3 else [])))
manifest=json.loads((D/'download-manifest.json').read_text());catalog=dict(collection='CADWorld original native CAD and saved CalculiX FEM references',source='https://github.com/Zdong104/CADWORLD',dataset_source='https://huggingface.co/datasets/Zihan1004/CADWORLD',revision=manifest['source_revision'],collected_date='2026-10-12',license='Apache-2.0 declared by publisher Hugging Face dataset metadata; material-card licenses remain embedded in original files',cad_reference_pairs=3,complex_geometry_candidates=2,basic_specimens=1,certified_benchmark_admissions=0,solver_runs=0,model_calls=0,no_local_cad_or_fem_generation=True,records=records)
(D/'catalog.json').write_text(json.dumps(catalog,indent=2));(D/'validation.json').write_text(json.dumps(dict(native_cad_valid=3,finite_csv_cases=3,finite_native_arrays_cases=3,total_csv_rows=sum(r['csv_rows'] for r in records),source_evaluator_reference_values_match=True,csv_native_unit_conversion_agrees=True,archive_crc_pass=True,solver_runs=0,model_calls=0,certified_admissions=0),indent=2));print('Audited CADWorld 3 saved FEM cases, 2 complex geometry candidates, 1 basic; no certified admissions')
