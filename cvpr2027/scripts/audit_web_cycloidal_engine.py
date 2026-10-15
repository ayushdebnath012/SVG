"""Read-only inspection of published BREP, FRD and thermal export values."""
from pathlib import Path
import json,hashlib,zipfile,struct,csv,xml.etree.ElementTree as E
import numpy as np,cadquery as cq,pymupdf
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.IGESControl import IGESControl_Reader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-machine-parts-search');R=D/'web-cad-fem-cycloidal-drive'
def audit(s):
 b=s.BoundingBox();return {'valid':s.isValid(),'solids':len(s.Solids()),'faces':len(s.Faces()),'bounds_mm':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],'volume_mm3':sum(v.Volume() for v in s.Solids())}
def render(s,p):
 verts,tris=s.tessellate(.3);v=np.array([[a.x,a.y,a.z] for a in verts]);fig=plt.figure(figsize=(8,4.3));ax=fig.add_subplot(111,projection='3d');ax.add_collection3d(Poly3DCollection(v[np.array(tris)],facecolors='#b5cedb',edgecolors='#526374',linewidths=.15));ax.auto_scale_xyz(*v.T);ax.set_box_aspect(np.maximum(np.ptp(v,axis=0),1));ax.view_init(25,-60);ax.set_axis_off();fig.tight_layout();fig.savefig(p,dpi=180);plt.close(fig)
def frd(p):
 # CalculiX GraphiX documented ASCII long format, 10-digit IDs and E12.5 fields.
 ls=p.read_text().splitlines();blocks=[];coords={};elements=0;i=0
 def row(line):return int(line[3:13]),[float(line[j:j+12]) for j in range(13,len(line),12) if line[j:j+12].strip()]
 while i<len(ls):
  s=ls[i]
  if s.startswith('    2C'):
   i+=1
   while ls[i].startswith(' -1'):n,v=row(ls[i]);coords[n]=v;i+=1
   assert ls[i].strip()=='-3'
  elif s.startswith('    3C'):
   i+=1
   while ls[i].strip()!='-3':elements+=ls[i].startswith(' -1');i+=1
  elif '100C' in s:
   header=s;i+=1;assert ls[i].startswith(' -4');name=ls[i].split()[1];i+=1;components=[]
   while ls[i].startswith(' -5'):components.append(ls[i].split()[1]);i+=1
   ids=[];values=[]
   while ls[i].startswith(' -1'):
    n,v=row(ls[i]);ids.append(n);values.append(v);i+=1
   assert ls[i].strip()=='-3';assert len(ids)==int(header.split()[3]);a=np.array(values);assert np.isfinite(a).all();assert len(ids)==len(set(ids));blocks.append({'name':name,'components':components,'header':header,'ids':np.array(ids,dtype=np.int64),'values':a})
  i+=1
 return coords,elements,blocks
def cload(p):
 vals={};on=False
 for line in p.read_text().splitlines():
  s=line.strip()
  if s.upper().startswith('*CLOAD'):on=True;continue
  if s.startswith('*') and not s.startswith('**'):on=False
  if on and s and not s.startswith('*'):
   a=s.split(',');key=(int(a[0]),int(a[1]));vals[key]=vals.get(key,0.0)+float(a[2])
 total=[sum(v for (n,d),v in vals.items() if d==i) for i in [1,2,3]]
 return vals,total
native=[];shapes={}
for f in sorted(R.rglob('*.FCStd')):
 with zipfile.ZipFile(f) as z:
  assert z.testzip() is None;doc=E.fromstring(z.read('Document.xml'));objects=[];sid=f.stem
  for o in doc.findall('./ObjectData/Object'):
   pr=o.find('./Properties/Property[@name="Shape"]/Part')
   if pr is not None:
    member=pr.attrib['file'];b=z.read(member);q=T/(hashlib.sha256(b).hexdigest()+'.brp');q.write_bytes(b);s=TopoDS_Shape();BRepTools.Read_s(s,str(q),BRep_Builder());s=cq.Shape.cast(s);objects.append({'object':o.attrib['name'],'member':member,'sha256':hashlib.sha256(b).hexdigest(),**audit(s)});shapes[str(f.relative_to(R))]=s
  mats=[{x.attrib['key']:x.attrib['value'] for x in m.findall('Item')} for m in doc.findall('./ObjectData/Object/Properties/Property[@name="Material"]/Map')]
  result_summaries=[]
  for o in doc.findall('./ObjectData/Object'):
   p=o.find('./Properties/Property[@name="vonMises"]/FloatList');u=o.find('./Properties/Property[@name="DisplacementLengths"]/FloatList')
   if p is not None and u is not None:
    def arr(member):
     b=z.read(member);n=struct.unpack('<I',b[:4])[0];a=np.frombuffer(b,dtype='<f8',offset=4);assert len(a)==n;return a
    vm=arr(p.attrib['file']);U=arr(u.attrib['file']);result_summaries.append({'object':o.attrib['name'],'rows':len(U),'max_translation_mm':float(U.max()),'max_von_mises_MPa':float(vm.max())})
  license=doc.find('./Properties/Property[@name="License"]/String')
  native.append({'file':str(f.relative_to(R)),'geometry':objects,'material':mats,'embedded_results':result_summaries,'native_license':license.attrib.get('value') if license is not None else 'not found'})
print('native CAD imported',len(native),flush=True)
assembly=cq.importers.importStep(str(R/'Cycloidal Drive - 3D Printable DIY.STEP')).val();assembly_audit=audit(assembly);render(assembly,T/'cycloidal-assembly-cad.png')
for key,out in [('fem/petg_cf/FEM_Disk_PETGCF/FEM_Disk_PETGCF.FCStd','cycloidal-disk-cad.png'),('fem/petg_cf/FEM_Housing_PETGCF/FEM_Housing_PETGCF.FCStd','cycloidal-housing-cad.png')]:render(shapes[key],T/out)
records=[];seen={};out=R/'extracted-original-fields';out.mkdir(exist_ok=True)
for f in sorted(R.rglob('*.frd')):
 digest=hashlib.sha256(f.read_bytes()).hexdigest()
 if digest in seen:records.append({'file':str(f.relative_to(R)),'duplicate_of':seen[digest],'sha256':digest,'counted_solution':False});continue
 seen[digest]=str(f.relative_to(R));coords,els,blocks=frd(f);rec={'file':str(f.relative_to(R)),'sha256':digest,'nodes':len(coords),'elements':els,'fields':[{'name':b['name'],'components':b['components'],'rows':len(b['ids']),'numeric_components':b['values'].shape[1],'header':b['header']} for b in blocks],'counted_solution':bool(blocks),'certified':False};deck=f.with_suffix('.inp')
 if deck.exists():
  loads,tot=cload(deck);rec['corrected_deck']=str(deck.relative_to(R));rec['CLOAD_resultant_N']=tot;rec['CLOAD_resultant_norm_N']=float(np.linalg.norm(tot));s=deck.read_text();i=s.find('*ELASTIC');rec['elastic_card']=s[i:i+100].splitlines()[:2]
  original=deck.with_name(deck.name.replace('_fixed',''))
  if original.exists() and original!=deck:
   ol,ot=cload(original);rec['uncorrected_CLOAD_norm_N']=float(np.linalg.norm(ot));rec['all_CLOAD_entries_corrected_1000x']=set(loads)==set(ol) and all(np.isclose(loads[k],ol[k]*1000,rtol=1e-10,atol=1e-12) for k in loads)
  dat=f.with_suffix('.dat')
  if dat.exists() and 'total force' in dat.read_text():
   reaction=np.array([float(x) for x in dat.read_text().splitlines()[-2].split()]) if dat.read_text().splitlines()[-1]=='' else np.array([float(x) for x in dat.read_text().splitlines()[-1].split()]);rec['fixed_reaction_N']=reaction.tolist();rec['reaction_balance_relative_norm']=float(np.linalg.norm(reaction+tot)/max(np.linalg.norm(tot),1e-30))
 if blocks:
  arrays={'mesh_node_ids':np.array(sorted(coords),dtype=np.int64),'mesh_xyz':np.array([coords[n] for n in sorted(coords)])}
  for b in blocks:arrays[b['name']+'_node_ids']=b['ids'];arrays[b['name']]=b['values'];assert set(b['ids'])==set(coords)
  U=next(b for b in blocks if b['name']=='DISP');assert U['values'].shape[1]==3;rec['max_translation_mm']=float(np.linalg.norm(U['values'],axis=1).max())
  st=next(b for b in blocks if b['name']=='STRESS');assert st['components']==['SXX','SYY','SZZ','SXY','SYZ','SZX'];xx,yy,zz,xy,yz,zx=st['values'].T;vm=np.sqrt(.5*((xx-yy)**2+(yy-zz)**2+(zz-xx)**2)+3*(xy**2+yz**2+zx**2));rec['derived_max_averaged_nodal_vm_MPa']=float(vm.max());arrays['derived_vm']=vm
  er=next(b for b in blocks if b['name']=='ERROR');rec['max_saved_ERROR']=float(er['values'].max());npz=out/(f.parent.name+'-'+f.stem+'.npz');np.savez_compressed(npz,**arrays);rec['exact_ascii_field_copy']=str(npz.relative_to(R))
 rec['primary_component_candidate']=bool(blocks) and f.name!='DiskPLA.frd' and f.name!='ShaftP2_fixed.frd';rec['reference_role']='Uncorrected underload result, excluded from primary targets' if f.name=='DiskPLA.frd' else ('Earlier axial cam result, secondary hypothesis only' if f.name=='ShaftP2_fixed.frd' else ('Corrected component source reference candidate' if blocks else 'Mesh only, excluded'));records.append(rec);print('FRD',f.stem,rec.get('max_translation_mm'),rec.get('derived_max_averaged_nodal_vm_MPa'),flush=True)
cat={'collection':'Published cycloidal-drive CAD and saved component FEM','source':'https://github.com/jagathsrujan/3d-printable-cycloidal-drive','revision':json.loads((R/'download-manifest.json').read_text())['revision'],'date':'2026-10-12','engineering_families':1,'assembly':assembly_audit,'native_models':native,'records':records,'unique_saved_solutions':sum(r['counted_solution'] for r in records),'primary_component_reference_candidates':sum(r.get('primary_component_candidate',False) for r in records),'original_result_files':len(records),'source_component_study_groups':15,'locally_generated_cad':0,'new_solver_runs':0,'frontier_model_calls':0,'certified_cases':0,'original_complete_dimensioned_drawings_verified':0,'license':'No repository license located; native FCStd says All rights reserved. Local research only; not a public-release dataset.','limitations':['Original author publishes component linear-static studies, not an assembled gearbox contact/dynamic solve. Purchased bearings and bolts not all solved.','PLA and PETG-CF modeled isotropically; no print anisotropy, creep, wear, fatigue or temperature solve. Generic material/yield assumptions require review.','One PLA disk FCStd contains stale underloaded embedded result: compare explicit corrected FRD, never choose first result object automatically.','Uncorrected vs corrected decks differ by 1000x CLOAD; both originals kept and independently summed. No local correction or rerun.','Incomplete Housing_fixed.frd contains mesh only and is excluded; Housing_lin_fixed is saved solved reference. Exact copies and alternative cam files are not new tasks.','Mesh convergence not demonstrated. Peak nodal stresses and idealized fixed-face singularities are not certified strength predictions.','Source nodal ERROR values retained. FreeCAD native/result and assembly component correspondence requires detailed topology/load mapping.','FRD ASCII output is rounded; NPZ retains unchanged saved decimal values with original IDs. Derived VM is labeled as read-only postprocessing.','Source README differs from process log on STEP origin; attribution to HowToMechatronics retained. No source generator executed.'],'format_documentation':'https://dhondt.de/cgx_2.19.pdf'}
(R/'catalog.json').write_text(json.dumps(cat,indent=2,allow_nan=False)+'\n')
# Engine coating: IGES files, original tabular transient exports and source report references.
R=D/'web-cad-fem-engine-tbc';iges=[]
for f in sorted((R/'CAD files').glob('*.iges')):
 rd=IGESControl_Reader();status=rd.ReadFile(str(f));rd.TransferRoots();s=cq.Shape.cast(rd.OneShape());rec={'file':str(f.relative_to(R)),**audit(s),'import_status':str(status)};iges.append(rec)
 if f.name=='0.2mm_Coated.iges':render(s,T/'engine-coated-cad.png')
exports=[];arrays={}
for i,f in enumerate(sorted((R/'output data').glob('*.xls'))):
 rows=list(csv.reader(f.read_text(encoding='utf-8-sig').splitlines(),delimiter='\t'));a=np.array([[float(x) for x in row if x.strip()] for row in rows[1:] if any(x.strip() for x in row)]);assert a.shape[1]==5 and np.isfinite(a).all() and np.all(np.diff(a[:,1])>0);arrays['table_'+str(i)]=a
 exports.append({'file':str(f.relative_to(R)),'headers':rows[0],'rows':len(a),'columns':['original_row_number','time_s','minimum','maximum','average'],'time_range_s':[float(a[0,1]),float(a[-1,1])],'highest_saved_maximum':float(a[:,3].max()),'final_maximum':float(a[-1,3]),'exact_npz_key':'table_'+str(i),'field_units':'Celsius' if 'temp' in f.name else 'W/mm^2','score_status':'Candidate source thermal history; source report/revision mapping requires review.'})
np.savez_compressed(R/'original-thermal-tables.npz',**arrays)
cat={'collection':'Engine piston thermal-barrier coating CAD and FEM reports','source':'https://github.com/AryaDuhan/HT-Project-main','revision':json.loads((R/'download-manifest.json').read_text())['revision'],'date':'2026-10-12','engineering_families':1,'CAD_exports':iges,'source_thermal_export_tables':exports,'report_references':[{'case':'0.2 mm coating','source':'ansys reports/0.2 mm report.pdf','physical_page':14,'table':22,'max_temperature_at_37_95_s_C':2513.5,'max_temperature_over_saved_history_C':2526.8,'max_flux_at_71_1_s_W_per_mm2':3.9665,'max_flux_over_saved_history_W_per_mm2':51.405},{'case':'thicker coating, exact export pairing held','source':'ansys reports/report.pdf','physical_page':14,'table':22,'max_temperature_display_C':2545.7,'temperature_result_state':'Obsolete','max_flux_at_40_s_W_per_mm2':19.65},{'case':'uncoated','source':'ansys reports/uncoated report.pdf','physical_pages':[16,17],'table':19,'max_temperature_at_37_s_C':2314.3,'max_flux_at_40_s_W_per_mm2':31.994,'max_temperature_over_saved_history_C':2526.8}],'source_structural_plot_targets':[{'image':'Images/IMG-20250608-WA0022.jpg','quantity':'equivalent stress','rounded_max_MPa':225.75},{'image':'Images/IMG-20250608-WA0024.jpg','quantity':'total deformation','rounded_max_mm':0.054303},{'image':'Images/IMG-20250608-WA0027.jpg','quantity':'equivalent stress','rounded_max_MPa':716.37},{'image':'Images/IMG-20250608-WA0028.jpg','quantity':'total deformation','rounded_max_mm':0.10778}],'published_configuration_candidates':3,'saved_raw_rst_rth_count':0,'complete_dimensioned_drawings_verified':0,'certified_cases':0,'new_solver_runs':0,'generated_cad':0,'frontier_model_calls':0,'license':'README asserts MIT; standalone LICENSE not found in tree. Local research collection.','excluded_as_FEM_ground_truth':['mock_tbc_data.csv','TBC_data.csv','generate_data.py thermodynamic cycle results','Python optimizer predictions and engine-cycle outputs','Fatigue-life plot without validated S-N/material and exact CAD/setup matching'],'limitations':['All 12 original IGES exports independently import as valid BREP: uncoated one solid, coated two solids. Exact report geometry revisions remain pending.','Coating thickness, exact export/report/result revision correspondence not yet certified. Filenames alone are insufficient.','README labels 2314.3 C as 0.2mm but uncoated report places it on uncoated case. Preserve source report values.','Thicker-coating report Temperature state is Obsolete. Flux history/table differs from image maxima; time/scoping/revision require matching.','Extreme thermal temperatures in linear material setup need physical-domain review; no certified real-engine prediction.','Only time extrema/averages and plots, not full nodal fields. 6 exports or hundreds of time rows are not extra CAD tasks.','Mock and optimizer CSVs excluded from numerical FEM scoring. No synthetic data or source code executed.']}
(R/'catalog.json').write_text(json.dumps(cat,indent=2,allow_nan=False)+'\n');print('Engine CAD',[(x['file'],x['solids'],x['faces']) for x in iges],flush=True);print('thermal',exports,flush=True)
R=D/'web-cad-fem-piston-drawing';cat={'collection':'Published piston-pin-connecting rod CAD/drawing and static FEM figures','source':'https://github.com/adhikaryharsha23-cpu/Piston-Connecting-Rod-FEA','revision':json.loads((R/'download-manifest.json').read_text())['revision'],'date':'2026-10-12','engineering_family':'Engine piston assembly, separate geometry from coated single piston','native_files':['PISTON AUTOCAD.dwg','PISTON DRAWING SHEET AUTOCAD 2D.dwg','PISTON SOLIDWORKS.SLDASM'],'DWG_header':'AC1032','drawing_dimension_completeness_verified':False,'assembly_dependency_status':'No referenced SLDPRT component files found in published tree; native DWG may provide geometry but independently importing it is pending.','source_plot_targets':[{'image':'FILE3.png','quantity':'equivalent stress','max_Pa':888010000.0,'equivalent_MPa':888.01},{'image':'file.png','quantity':'total deformation','max_m':0.00022122,'equivalent_mm':0.22122}],'README_conflicts':['README rounds stress to 880 MPa, source contour shows 8.8801e8 Pa.','README manifest describes SLDPRT parts, neutral CAD and CSV reaction log absent from actual published tree.','Source says linear elastic with yield280MPa, but stress far exceeds yield. It does not demonstrate computed plasticity.','Claimed convergence/equilibrium checks have no uploaded quantitative history/log evidence.'],'raw_FEM_fields':0,'wbpj_is_saved_result_archive':False,'conditional_plot_candidate':1,'certified_cases':0,'license':'No explicit data license found; local research only.','new_solver_runs':0,'generated_cad':0,'frontier_model_calls':0}
(R/'catalog.json').write_text(json.dumps(cat,indent=2)+'\n')
P=D/'web-complex-fem/selected-dataset.json';j=json.loads(P.read_text());j['cycloidal_engine_web_extension']={'catalogs':[str(D/x/'catalog.json') for x in ['web-cad-fem-cycloidal-drive','web-cad-fem-engine-tbc','web-cad-fem-piston-drawing','web-cad-fem-held-machine-leads']],'pdf':'cvpr2027/output/pdf/web-cad-fem-cycloidal-engine.pdf','zip':'cvpr2027/output/datasets/web-cad-fem-cycloidal-engine.zip','publisher_projects_with_reference_evidence':3,'broad_engineering_families':2,'cycloidal_component_study_groups':15,'cycloidal_unique_saved_solutions':sum(r['counted_solution'] for r in records),'cycloidal_primary_component_reference_candidates':sum(r.get('primary_component_candidate',False) for r in records),'coated_piston_published_configuration_candidates':3,'piston_assembly_conditional_plot_candidate':1,'verified_new_complete_dimensioned_drawing_packages':0,'certified_cases':0,'important_limit':'Component statics rather than gearbox assembly dynamics; engine CAD/report revision and thermal source conflicts held; piston native assembly references absent; turbine geometry mismatch excluded.'};P.write_text(json.dumps(j,indent=2)+'\n')
