from pathlib import Path
import json, zipfile, struct, hashlib, csv, xml.etree.ElementTree as E
import numpy as np, cadquery as cq
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
D=Path('cvpr2027/data/web-cad-fem-manufacturing'); P=D/'codeaster-laminate';T=Path('cvpr2027/tmp/cad-fem-manufacturing-search');T.mkdir(exist_ok=True,parents=True)
source='https://github.com/FreeCAD/FreeCAD/pull/28380'
def arr(z,n,k=1):
 b=z.read(n);count=struct.unpack('<I',b[:4])[0];a=np.frombuffer(b,dtype='<f8',offset=4).copy();assert a.size==count*k and np.isfinite(a).all();return a.reshape(count,k) if k>1 else a
records=[]
for f in sorted(P.glob('*.FCStd')):
 z=zipfile.ZipFile(f);assert z.testzip() is None;r=E.fromstring(z.read('Document.xml'));comp='Comp' in f.stem
 shapes=[];body=None
 for n in ['Body.Shape.brp','Face004.Shape.brp']:
  q=T/(f.stem+'-'+n);q.write_bytes(z.read(n));s=TopoDS_Shape();BRepTools.Read_s(s,str(q),BRep_Builder());shape=cq.Shape.cast(s);assert shape.isValid();bb=shape.BoundingBox();shapes.append(dict(member=n,valid=True,solids=len(shape.Solids()),faces=len(shape.Faces()),bounds_mm=[bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax]));body=shape if n.startswith('Body') else body
 results=[]
 for ob in r.findall('./ObjectData/Object'):
  prop=ob.find('./Properties/Property[@name="DisplacementLengths"]/FloatList')
  if prop is None:continue
  a=arr(z,prop.attrib['file']);v=arr(z,ob.find('./Properties/Property[@name="DisplacementVectors"]/VectorList').attrib['file'],3);assert len(v)==len(a);assert np.allclose(np.linalg.norm(v,axis=1),a,rtol=1e-5,atol=1e-8)
  nr=ob.find('./Properties/Property[@name="Mesh"]/Link');mesh=nr.attrib.get('value') if nr is not None else None
  results.append(dict(object=ob.attrib['name'],nodes=len(a),max_displacement_source_units=float(a.max()),min_displacement_source_units=float(a.min()),component_min=v.min(axis=0).tolist(),component_max=v.max(axis=0).tolist(),all_finite=True,result_mesh=mesh))
  with (P/(f.stem+'-'+ob.attrib['name']+'-displacements.csv')).open('w') as out:
   w=csv.writer(out);w.writerow(['source_array_index','ux','uy','uz','magnitude']);w.writerows((i,*v[i],a[i]) for i in range(len(a)))
  # Original result mesh node coordinates, not generated geometry.
  mo=r.find(f'./ObjectData/Object[@name="{mesh}"]');unv=mo.find('./Properties/Property[@name="FemMesh"]/FemMesh').attrib['file']
  lines=z.read(unv).decode().splitlines();i=next(j for j,l in enumerate(lines) if l.strip()=='2411')+1;points=[];ids=[]
  while lines[i].strip()!='-1':
   ids.append(int(lines[i].split()[0]));points.append([float(x.replace('D','E')) for x in lines[i+1].split()]);i+=2
  points=np.array(points);assert len(points)==len(a)
  fig,ax=plt.subplots(figsize=(6.5,2.6));sc=ax.scatter(points[:,0],points[:,1],c=a,s=30 if len(a)<100 else 9,cmap='viridis');fig.colorbar(sc,ax=ax,label='Saved |u| (source units)');ax.set_aspect('equal');ax.set_xlabel('Source X coordinate');ax.set_ylabel('Source Y coordinate');fig.tight_layout();fig.savefig(T/(f.stem+'-'+ob.attrib['name']+'.png'),dpi=180);plt.close(fig)
 verts,tris=body.tessellate(.2);verts=np.array([[v.x,v.y,v.z] for v in verts]);fig=plt.figure(figsize=(6.5,2.6));ax=fig.add_subplot(111,projection='3d');ax.add_collection3d(Poly3DCollection(verts[np.array(tris)],facecolors='#94b7ce',edgecolors='#334155',linewidths=.3));ax.auto_scale_xyz(verts[:,0],verts[:,1],verts[:,2]);ax.set_box_aspect((100,50,10));ax.set_xlabel('X (mm)');ax.set_ylabel('Y (mm)');ax.set_zlabel('Z (mm)');ax.view_init(25,-65);ax.set_axis_off();fig.tight_layout();fig.savefig(T/(f.stem+'-cad.png'),dpi=180);plt.close(fig)
 touched=[o.attrib['name'] for o in r.findall('./Objects/Object') if o.attrib.get('Touched')=='1'];limitations=['Simple rectangular CAD; complex laminate physics does not imply complex drawing.','No original dimensioned drawing in this attachment.','Result units need solver-writer review: UNV metadata says SI meter, while saved CAD and mesh dimensions are 100 x 50 x 10.','Source attachment data license not established by repository code license; native document default metadata says All rights reserved.','No model accuracy scores measured; reference fields are published solver output.']
 if touched:limitations.append('Source solver, mesh and result objects marked Touched; saved solution correspondence needs verification before benchmark admission.')
 rec=dict(id='codeaster-laminate' if comp else 'codeaster-calculix-comparison',source=source,download='https://github.com/user-attachments/files/26033140/Scratch-shell-CA.zip',cad=str(f.relative_to(D)),author='TimSwait-AMRC',geometry_audit=shapes,results=results,touched_objects=touched,original_dimensioned_drawing=False,certified=False,limitations=limitations)
 if comp:rec['ply_orientations_deg']=arr(z,'Orientations').tolist();rec['ply_thicknesses_mm']=arr(z,'Thicknesses').tolist()
 else:rec['max_displacement_solver_difference_percent']=100*abs(results[0]['max_displacement_source_units']-results[1]['max_displacement_source_units'])/results[1]['max_displacement_source_units']
 records.append(rec)
cat=dict(collection='Published laminate CAD/FEM extension and manufacturing drawing lead',date='2026-10-12',downloaded_native_cad_with_saved_results=2,new_complex_physics_candidates=1,basic_solver_comparison_cases=1,certified_cases=0,locally_generated_cad=0,solver_runs=0,model_calls=0,records=records,held_leads=[dict(id='hannover-milling',source='https://data.uni-hannover.de/de/dataset/shape-errors-and-surface-roughnesses-of-specimens-with-support-and-stiffening-structures',doi='10.25835/z4qoeq0d',cad_archive='hannover-milling/cad-models.zip',original_step_models=5,original_drawing='hannover-milling/260320_balken_fertigteil_zeichnung.pdf',status='Original CAD and dimensioned drawing downloaded. Workbook and analysis PNGs contain measured scan/coordinate deviations; saved FEM numerical output not verified. Excluded from CAD/FEM pair count.',license='CC BY-NC 4.0')])
(D/'catalog.json').write_text(json.dumps(cat,indent=2));print(json.dumps(cat,indent=2))
(D/'README.md').write_text('''# Published CAD/FEM collection extension\n\nTwo original FreeCAD CAD documents with saved numerical FEM fields downloaded from TimSwait-AMRC’s FreeCAD pull request https://github.com/FreeCAD/FreeCAD/pull/28380. One unbalanced asymmetric two-ply laminate case (0/45 degrees, 1 mm each) and one basic isotropic Code_Aster/CalculiX comparison; three saved solutions, two cases. Native BREP validity and finite displacement arrays verified. CAD inspection figures tessellate original BREP; CSVs extract unchanged saved arrays by source array index (not verified node IDs). No CAD or FEM solution generated locally.\n\nThese are candidates, not admitted benchmark cases. The laminate source has touched solver/mesh/result flags. Review units and native model/result correspondence before scoring. Original attachment does not establish a standalone data license; file metadata has a default All rights reserved value. Preserve attribution and clarify public redistribution separately from local research collection.\n\nHannover milling source includes five STEP members, an original dimensioned drawing and measurement comparisons. Kept as a held lead, not FEM ground truth. Dataset source and license are recorded in catalog.json and original download metadata.\n\nDo not count solver outputs, plies, mesh nodes or measurement images as separate tasks. No frontier model trials or accuracy scores have been run.\n''')
selected=Path('cvpr2027/data/web-complex-fem/selected-dataset.json');j=json.loads(selected.read_text());j['laminate_and_manufacturing_web_extension']=dict(catalog=str(D/'catalog.json'),pdf='cvpr2027/output/pdf/web-cad-fem-laminate-extension.pdf',zip='cvpr2027/output/datasets/web-cad-fem-laminate-extension.zip',native_cad_saved_fem_candidates=2,complex_physics_cases=1,certified_cases=0,manufacturing_cad_drawing_leads=1);selected.write_text(json.dumps(j,indent=2)+'\n')
