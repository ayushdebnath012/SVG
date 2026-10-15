from pathlib import Path
import json,csv,zipfile,xml.etree.ElementTree as E
import numpy as np,vtk,cadquery as cq
from vtk.util.numpy_support import vtk_to_numpy
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
D=Path('cvpr2027/data/web-cad-fem-multiphysics');T=Path('cvpr2027/tmp/cad-fem-fracture-search')
def audit_vtu(p):
 r=vtk.vtkXMLUnstructuredGridReader();r.SetFileName(str(p));r.Update();g=r.GetOutput();assert g.GetNumberOfPoints()>0 and g.GetNumberOfCells()>0
 pts=vtk_to_numpy(g.GetPoints().GetData());assert np.isfinite(pts).all();fields={}
 for i in range(g.GetPointData().GetNumberOfArrays()):
  v=g.GetPointData().GetArray(i);a=vtk_to_numpy(v);assert len(a)==len(pts);finite=a[np.isfinite(a)];fields[v.GetName()]=dict(shape=list(a.shape),nonfinite_values=int((~np.isfinite(a)).sum()),min=float(finite.min()) if finite.size else None,max=float(finite.max()) if finite.size else None,max_vector_norm=float(np.nanmax(np.linalg.norm(a,axis=1))) if a.ndim==2 else None)
 return dict(file=str(p.relative_to(D)),points=len(pts),cells=g.GetNumberOfCells(),bounds=list(g.GetBounds()),fields=fields,all_finite=all(v['nonfinite_values']==0 for v in fields.values()))
records=[]
P=D/'capriccio-fracture'
for case in ['MD1e6','MD4e6']:
 frames=[audit_vtu(p) for p in sorted((P/case/'output').glob('*.vtu'),key=lambda p:int(p.stem.split('-')[-1]))];assert frames
 rec=dict(id='capriccio-'+case,source='https://zenodo.org/records/18355528',license='CC BY 4.0; Felix Weber',family='Coupled FEM/molecular-dynamics polymer fracture',geometry=f'capriccio-fracture/{case}/input/GTPm.cae',input_deck=f'capriccio-fracture/{case}/input/GTPm.inp',parameters=f'capriccio-fracture/{case}/input/GTPm.jl',cad_status='Original native Abaqus CAE downloaded; geometric CAD vs orphan-mesh content not independently inspected; no STEP/BREP verified',result_type='Published FE/MD coupled VTU point fields u, uforces and stress',frames=frames,count_as_one_task=True,limitations=['FE/MD coupled output, not pure structural FEM or pure MD reference.','Missing MD initial particle data, potentials and full trajectory archive in this selected download; not a complete replay package.','VTU output filenames are increment identifiers, not verified physical times.','CAE model requires compatible inspection; do not count as verified native CAD/BREP.','Units and FE/MD region mapping require parameter review before scoring.'],certified=False)
 records.append(rec)
P=D/'digimat-thermomechanical';rows=list(csv.DictReader((P/'30C14hr_80C10hr_FEA_data.csv').open()));a=np.array([[float(v) for v in row.values()] for row in rows]);assert np.isfinite(a).all();assert np.all(np.diff(a[:,1])>0)
records.append(dict(id='digimat-cure-cycle',source='https://zenodo.org/records/10025292',license='CC BY 4.0; Jesper Kjaer Jorgensen',family='Resin curing thermal strain and chemical shrinkage',geometry='digimat-thermomechanical/Box3D_TE.cae',cad_status='Original native Abaqus CAE file; basic box specimen; native geometry not independently inspected',results='digimat-thermomechanical/30C14hr_80C10hr_FEA_data.csv',rows=len(rows),columns=list(rows[0]),statistics={k:dict(min=float(a[:,i].min()),max=float(a[:,i].max()),last=float(a[-1,i])) for i,k in enumerate(rows[0])},all_finite=True,limitations=['Complex constitutive/cure task on a simple box, not a complex CAD drawing.','Abaqus plus Digimat material coupling needed for replay.','Reference scalar history sampled by source script at X1Y1 set, not complete nodal fields.','Native model filename TE differs from journal TVE; correspondence and material configuration require review.','Source extraction script includes an apparent range endpoint error; original CSV retained unchanged.'],certified=False))
P=D/'bimetal-transient';shapes=[]
with zipfile.ZipFile(P/'bimetalstrip_tutorial_without_results.FCStd') as z:
 doc=E.fromstring(z.read('Document.xml'));(P/'native-model-metadata.xml').write_bytes(z.read('Document.xml'))
 for n in z.namelist():
  if n.endswith('.brp'):
   p=T/n;p.write_bytes(z.read(n));s=TopoDS_Shape();BRepTools.Read_s(s,str(p),BRep_Builder());s=cq.Shape.cast(s);assert s.isValid();shapes.append(dict(member=n,valid=True,solids=len(s.Solids()),faces=len(s.Faces()),volume_mm3=sum(v.Volume() for v in s.Solids())))
frames=[audit_vtu(p) for p in sorted((P/'vtk-export').glob('*.vtu'))]
records.append(dict(id='bimetal-transient',source='https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Macro_export_transient_FEM_results.md',author='Luftschraube',family='Transient coupled thermomechanical bending of aluminium/steel',cad='bimetal-transient/bimetalstrip_tutorial_without_results.FCStd',solved_model='bimetal-transient/bimetalstrip_tutorial_with_results.FCStd',brep_checks=shapes,frames=frames,license='Source native FCStd metadata: All rights reserved; macro LGPL does not establish data license',redistribution=False,count_as_one_task=True,limitations=['Simple strip geometry; coupled thermal/mechanical physics, not a complex drawing.','Source data licensing requires clarification before redistribution or release.','Original VTU units must be reviewed; use original scalar field names without asserting SI conversion.'],certified=False))
held=[dict(id='tapered-spring',source='https://zenodo.org/records/14998785',status='Downloaded original 11.77MB ODB, all five CAD-building input scripts and experimental CSV; no prebuilt native CAD supplied. Scripts were not executed. ODB fields require Abaqus-compatible reader; experiment CSV is not FEM output.'),dict(id='sofa-soft-actuator',source='https://zenodo.org/records/7838026',status='Original ZIP has OBJ geometry, scripts and tutorial PDF; plot folder empty and no saved numerical FEM results. Not counted.')]
cat=dict(collection='Web-sourced multiphysics candidate extension',date='2026-10-12',native_cae_with_published_numerical_reference_candidates=3,strict_verified_native_cad_and_fem_pairs_redistributable=0,verified_native_cad_fem_pair_local_only=1,certified_cases=0,solver_runs=0,model_calls=0,local_geometry_generation=0,records=records,held_leads=held)
(D/'catalog.json').write_text(json.dumps(cat,indent=2));print('Finite VTU frames',[len(r.get('frames',[])) for r in records]);print('Cure CSV rows',len(rows));print('BREP',shapes);print('CSV stats',records[2]['statistics'])
