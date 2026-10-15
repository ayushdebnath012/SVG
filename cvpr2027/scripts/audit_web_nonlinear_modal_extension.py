from pathlib import Path
import json,zipfile,xml.etree.ElementTree as E,struct,re,math
import numpy as np, vtk,cadquery as cq,openpyxl
from vtk.util.numpy_support import vtk_to_numpy
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
D=Path('cvpr2027/data/web-cad-fem-nonlinear-modal');P=D/'fcfem';A=Path('cvpr2027/data/web-cad-fem-aerospace');M=A/'morphing-modal';T=Path('cvpr2027/tmp/cad-fem-morphing-search')
def audit_shape(s):
 b=s.BoundingBox();return dict(valid=s.isValid(),solids=len(s.Solids()),faces=len(s.Faces()),bounds=[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],volume=sum(v.Volume() for v in s.Solids()))
def render_shape(s,p,elev=25):
 v,t=s.tessellate(.3);v=np.array([[q.x,q.y,q.z] for q in v]);fig=plt.figure(figsize=(7,3));ax=fig.add_subplot(111,projection='3d');ax.add_collection3d(Poly3DCollection(v[np.array(t)],facecolors='#9abed2',edgecolors='#475569',linewidths=.25));ax.auto_scale_xyz(*v.T);ax.set_box_aspect(np.maximum(np.ptp(v,axis=0),1));ax.view_init(elev,-65);ax.set_axis_off();fig.tight_layout();fig.savefig(p,dpi=180);plt.close(fig)
choices=[('Spanner','Body'),('Tubes','Fusion'),('Bulldozer_Example','Compound'),('Embankment_with_Ditch','Extrude'),('Stacked_Beam_Example','BooleanFragments')];records=[]
for name,obj in choices:
 f=P/('fcFEM_'+name+'.FCStd');z=zipfile.ZipFile(f);assert z.testzip() is None;r=E.fromstring(z.read('Document.xml'));gob=r.find(f'./ObjectData/Object[@name="{obj}"]');member=gob.find('./Properties/Property[@name="Shape"]/Part').attrib['file'];tmp=T/(name+'.brp');tmp.write_bytes(z.read(member));s=TopoDS_Shape();BRepTools.Read_s(s,str(tmp),BRep_Builder());s=cq.Shape.cast(s);gcheck=audit_shape(s);assert gcheck['valid'];render_shape(s,T/(name+'-cad.png'))
 external=[];embedded=[]
 for v in sorted(P.glob('fcFEM_'+name+'-*.vtk')):
  rd=vtk.vtkUnstructuredGridReader();rd.SetFileName(str(v));rd.ReadAllScalarsOn();rd.ReadAllVectorsOn();rd.ReadAllTensorsOn();rd.Update();g=rd.GetOutput();pts=vtk_to_numpy(g.GetPoints().GetData());assert np.isfinite(pts).all();fs={}
  for i in range(g.GetPointData().GetNumberOfArrays()):
   ar=g.GetPointData().GetArray(i);a=vtk_to_numpy(ar);assert len(a)==len(pts);finite=a[np.isfinite(a)];fs[ar.GetName()]=dict(shape=list(a.shape),nonfinite_values=int((~np.isfinite(a)).sum()),min=float(finite.min()) if finite.size else None,max=float(finite.max()) if finite.size else None)
  external.append(dict(file=str(v.relative_to(D)),points=len(pts),cells=g.GetNumberOfCells(),bounds=list(g.GetBounds()),fields=fs,all_finite=all(v['nonfinite_values']==0 for v in fs.values())))
  val=vtk_to_numpy(g.GetPointData().GetArray('Displacement Magnitude'));fig=plt.figure(figsize=(7,3));ax=fig.add_subplot(111,projection='3d');im=ax.scatter(*pts.T,c=val,s=2 if len(pts)>5000 else 5,cmap='viridis');fig.colorbar(im,ax=ax,shrink=.75,label='Saved displacement magnitude');ax.set_box_aspect(np.maximum(np.ptp(pts,axis=0),1));ax.view_init(25,-65);ax.set_axis_off();fig.tight_layout();fig.savefig(T/(v.stem+'.png'),dpi=180);plt.close(fig)
 for o in r.findall('./ObjectData/Object'):
  fp=o.find('./Properties/Property[@name="DisplacementLengths"]/FloatList')
  if fp is None or not fp.attrib.get('file'):continue
  b=z.read(fp.attrib['file']);n=struct.unpack('<I',b[:4])[0];a=np.frombuffer(b,dtype='<f8',offset=4).copy();assert len(a)==n
  embedded.append(dict(object=o.attrib['name'],nodes=n,nonfinite_values=int((~np.isfinite(a)).sum()),max_displacement=float(np.nanmax(a)),source_binary_member=fp.attrib['file']))
  if name=='Stacked_Beam_Example' and len(embedded)==36:
   mesh=o.find('./Properties/Property[@name="Mesh"]/Link').attrib['value'];mo=r.find(f'./ObjectData/Object[@name="{mesh}"]');unv=mo.find('./Properties/Property[@name="FemMesh"]/FemMesh').attrib['file'];lines=z.read(unv).decode().splitlines();i=next(j for j,l in enumerate(lines) if l.strip()=='2411')+1;coords={}
   while lines[i].strip()!='-1':coords[int(lines[i].split()[0])]=[float(x.replace('D','E')) for x in lines[i+1].split()];i+=2
   ids=[int(v.attrib['v']) for v in o.findall('./Properties/Property[@name="NodeNumbers"]/IntegerList/I')];pts=np.array([coords[n] for n in ids]);assert len(pts)==len(a)
   fig=plt.figure(figsize=(7,3));ax=fig.add_subplot(111,projection='3d');im=ax.scatter(*pts.T,c=a,s=9,cmap='viridis');fig.colorbar(im,ax=ax,shrink=.75,label='Saved displacement magnitude');ax.set_box_aspect(np.maximum(np.ptp(pts,axis=0),1));ax.set_axis_off();ax.view_init(25,-65);fig.tight_layout();fig.savefig(T/'Stacked_Beam_Example-fem.png',dpi=180);plt.close(fig)
 inp=(P/('fcFEM_'+name+'.inp')).read_text();output_control=float(inp.splitlines()[5].split('#')[0]);rec=dict(id='fcfem-'+name,source='https://github.com/HarryvL/fcFEM-basic',cad=str(f.relative_to(D)),cad_object=obj,geometry_audit=gcheck,external_results=external,embedded_results=embedded,original_parameters=str((P/('fcFEM_'+name+'.inp')).relative_to(D)),saved_displacement_interpretation='Original parameter file uses negative out_disp: incremental displacement requested; correspondence to each saved output requires review',parameter_out_disp=output_control,license='LGPL-2.0-or-later declared for program; separate source-data scope not established by native metadata',original_dimensioned_drawing=False,certified=False,limitations=['Original numerical arrays retained; output increment, load factor, solver/material and unit correspondence need validation before scoring.','No convergence study verified.','Different VTK exports / material parameters are variants of one case, not separate task families.','Collapse-analysis solver does not by itself certify that each saved snapshot is a converged collapse load.'])
 if name in ['Bulldozer_Example','Embankment_with_Ditch']:rec['domain']='Geomechanics; idealized soil bodies, not detailed machinery CAD'
 else:rec['domain']='Mechanical structures'
 records.append(rec)
# Read original workbook only; preserve all cached values/formulas untouched.
w=openpyxl.load_workbook(M/'1-1 Modal Test Experiment and Numerical Results.xlsx',data_only=True);s=w.active;wf=openpyxl.load_workbook(M/'1-1 Modal Test Experiment and Numerical Results.xlsx',data_only=False).active;starts=[r for r in range(1,s.max_row+1) if isinstance(s.cell(r,1).value,str) and re.match(r'Test\d+-1$',s.cell(r,1).value)];allowed={'Thick Shell','Thin Shell','Shear Beam','Euler Beam','Solid_Mesh_2','Solid_Mesh_1','Solid_Mesh_0.5','Thin-P=Euler-B','Thin-P=Thin-P','Euler-B=Euler-B'};modal=[]
for start in starts:
 test=re.match(r'Test(\d+)-1',s.cell(start,1).value).group(1);f=next((M/'FDM Stp Files').glob('Test'+test+' *.STEP'));shape=cq.importers.importStep(str(f)).val();check=audit_shape(shape);assert check['valid'];render_shape(shape,T/('morphing-Test'+test+'-cad.png'))
 targets=[];header=start+1
 for row in range(start+2,min(start+14,s.max_row+1)):
  mode=s.cell(row,1).value
  if not isinstance(mode,str) or not re.match(r'\d+-(B|T|FB)$',mode):continue
  for col in range(1,s.max_column+1):
   model=s.cell(header,col).value
   if model not in allowed:continue
   value=s.cell(row,col).value
   if not isinstance(value,(int,float)):continue
   assert math.isfinite(value) and value>0
   cell=s.cell(row,col).coordinate;targets.append(dict(mode=mode,model=model,frequency_hz=value,sheet=s.title,cell=cell,source_value_or_formula=wf.cell(row,col).value))
 modal.append(dict(id='morphing-Test'+test,source='https://data.mendeley.com/datasets/8jxw5533py/2',cad=str(f.relative_to(A)),geometry_audit=check,reference_workbook='morphing-modal/1-1 Modal Test Experiment and Numerical Results.xlsx',reference_type='Published FEM modal frequency table, not raw nodal fields',targets=targets,certified=False,original_dimensioned_drawing=False,limitations=['Simple uniform/stepped plate proxy, not full morphing-wing CAD.','Material/print orientation, nominal vs measured dimensions and FEM formulation must be matched before scoring.','Specimen IDs join source CAD/table; filename flexible fraction and nominal geometry need checking; Test4 filename says fef50 although table associates Test4 with fef75.','Source README names sheets Uniform/Stepped, but actual workbook has one Modal Test Result sheet; exact cell provenance retained.']))
assert len(modal)==9 and all(v['targets'] for v in modal)
# Inspect the complex wing model but hold it out where source geometry/scale correspondence is unclear.
wing=dict(id='aerospace-wingbox-held',source='https://github.com/myousufbaig/aerospace-wing-box-fea',cad='wingbox/Wing.iges',geometry_audit=json.loads((T/'wing-iges-audit.json').read_text()),reference_text='wingbox/Results/details.txt',reference_images='wingbox/FEA-Analysis/section 5',status='Original complex CAD and published FEM references collected; geometry/unit/setup correspondence unresolved; excluded from numerical CAD/reference pair count.',limitations=['IGES imports as 142 valid faces with no solid/shell; source README states 10.92m span but imported CAD Y extent is 9430 coordinate units.','APDL static macro comments declare section thickness 31.5m and selects tip at Y~10.92; no source scaling/geometry-import stage included in selected macros.','No raw .rst saved nodal field file found.','Mode-label filenames and rounded text differ from solver screenshot values; preserve both unchanged.'])
cat=dict(collection='Web nonlinear FEM examples and modal specimen references',date='2026-10-12',native_cad_saved_field_cases=len(records),native_cad_modal_table_candidates=len(modal),complex_cad_reference_held=1,certified_cases=0,solver_runs=0,model_calls=0,locally_generated_cad=0,fcfem_records=records,modal_records=modal,held=[wing]);(D/'catalog.json').write_text(json.dumps(cat,indent=2));print('CAD + fields',len(records),'CAD + modal tables',len(modal),'finite frequency targets',sum(len(r['targets']) for r in modal));print('FEM inventories',[(r['id'],len(r['embedded_results']),[(v['points'],v['all_finite']) for v in r['external_results']]) for r in records]);print('first modal refs',[(r['id'],r['targets'][0]['frequency_hz'],r['targets'][0]['cell']) for r in modal])
