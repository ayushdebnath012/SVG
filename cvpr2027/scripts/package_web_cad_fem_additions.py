"""Audit and package downloaded reference assets; never runs CAD or FEM generators."""
from pathlib import Path
import zipfile,json,hashlib,io,shutil,xml.etree.ElementTree as ET
import numpy as np
import cadquery as cq
from OCP.IGESControl import IGESControl_Reader
ROOT=Path(__file__).resolve().parents[1]; CACHE=ROOT/'tmp/cad-paired-search'; OUT=ROOT/'data/web-cad-fem-additions';OUT.mkdir(exist_ok=True,parents=True)
records=[]; fingerprints=set()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cad(p):
 s=cq.importers.importStep(str(p)).val();b=s.BoundingBox();bounds=[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
 return s,dict(valid=s.isValid(),solids=len(s.Solids()),faces=len(s.Faces()),bounds_mm=bounds,volume_mm3=s.Volume(),area_mm2=s.Area())
geo=OUT/'geopinonet';geo.mkdir(exist_ok=True)
shutil.copy2(CACHE/'geopinonet-zenodo.json',geo/'source-record.json');shutil.copy2(CACHE/'geopinonet/download-manifest.json',geo/'download-manifest.json')
shutil.copy2(CACHE/'geopinonet/Geo-PINO-Net_source_v3.zip',geo/'Geo-PINO-Net_source_v3.zip')
for archive in sorted((CACHE/'geopinonet').glob('*dataset_v2.zip')):
 target=geo/archive.name
 if not target.exists():shutil.copy2(archive,target)
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for n in sorted(n for n in z.namelist() if n.endswith('_solid.stp')):
   parts=n.split('/'); family=parts[-4];split=parts[-3];case=parts[-2];stem=n.rsplit('/',1)[0]+'/'+case
   cpath=geo/'cad'/family/split/f'{case}.stp';cpath.parent.mkdir(parents=True,exist_ok=True);cpath.write_bytes(z.read(n));shape,check=cad(cpath);assert check['valid'] and check['solids']==1
   fp=tuple(round(v,7) for v in check['bounds_mm'])+(round(check['volume_mm3'],5),round(check['area_mm2'],5));assert fp not in fingerprints;fingerprints.add(fp)
   fem=[]
   for load in ('compression','lateral_bending'):
    fn=stem+'_'+load+'.csv';blob=z.read(fn);a=np.loadtxt(io.BytesIO(blob),delimiter=',',skiprows=1);assert a.shape[1]==12 and np.isfinite(a).all()
    bounds=np.r_[a[:,:3].min(0),a[:,:3].max(0)];error=float(np.abs(bounds-np.array(check['bounds_mm'])/1000).max());assert error<1e-7,(fn,error)
    sx,sy,sz,txy,tyz,txz=a[:,6:].T;vm=np.sqrt(.5*((sx-sy)**2+(sy-sz)**2+(sz-sx)**2)+3*(txy*txy+tyz*tyz+txz*txz))
    fem.append(dict(load=load,archive_member=fn,rows=len(a),columns=blob.splitlines()[0].decode().split(','),sha256=hashlib.sha256(blob).hexdigest(),finite=True,cad_csv_bounds_max_difference_m=error,max_displacement_m=float(np.linalg.norm(a[:,3:6],axis=1).max()),max_von_mises_Pa=float(vm.max()),summary_origin='Computed by reading the published FEM CSV; no solver run. SI convention supported by source config/demo, not independently replayed.'))
   records.append(dict(id=f'geopinonet-{family}-{split}-{case}',source='https://zenodo.org/records/21483341',family=family,source_split=split,source_case=case,cad=str(cpath.relative_to(OUT)),cad_archive=archive.name,cad_archive_member=n,cad_sha256=sha(cpath),cad_validation=check,fem=fem,dimensioned_drawing_available=False,benchmark_admitted=False,limitations=['Parametric variation within one of two geometry families, not a new engineering problem family.','No published dimensioned drawing verified.','Original ANSYS solve not replayed; force/BC mapping and tolerances need benchmark review.']+(['Source README states plate thickness 20 mm; downloaded STEP and matching FEM CSV are 10 mm thick.'] if family=='Plate_with_a_hole' else [])))
  print(archive.name,'verified',len([r for r in records if r.get('family')==family]),flush=True)
# Valve original CAD, original dimensioned figures, original complete results archive.
v=OUT/'valve';v.mkdir(exist_ok=True);shutil.copy2(CACHE/'valve-supplement.zip',v/'original-supplement.zip');shutil.copy2(CACHE/'valve.xml',v/'article.xml')
for i in range(1,5):
 f=CACHE/'valve-figures'/f'figure-{i}-large.jpg'
 if not f.exists():f=CACHE/'valve-figures'/f'figure-{i}.jpg'
 if f.exists():shutil.copy2(f,v/f'figure-{i}.jpg')
with zipfile.ZipFile(v/'original-supplement.zip') as z:
 assert z.testzip() is None
 for n in z.namelist():
  if n.endswith(('.igs','.3dm','.inp','.for','.c','.m')):q=v/Path(n).relative_to('DataInBrief_TricuspidValveBenchmark');q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(z.read(n))
 r=IGESControl_Reader();r.ReadFile(str(v/'Idealized_Geometry/Idealized_TV.igs'));r.TransferRoots();s=cq.Shape.cast(r.OneShape());assert s.isValid() and len(s.Faces())>0
 frames=[]
 for i in range(5):
  base='DataInBrief_TricuspidValveBenchmark/';nn=base+f'Text_Files/00_run_Model_node_Frame{i}.txt';ne=base+f'Text_Files/00_run_Model_elem_Frame{i}.txt';a=np.loadtxt(io.BytesIO(z.read(nn)));assert np.isfinite(a).all();mx=0.;nstress=0;nstrain=0
  for line in z.read(ne).decode().splitlines():
   cols=line.split();vals=np.array([float(x) for x in cols[4:]]);assert np.isfinite(vals).all()
   if cols[0]=='Stress':nstress+=1;mx=max(mx,float(cols[-1]))
   elif cols[0]=='Strain':nstrain+=1
  frames.append(dict(frame=i,node_rows=len(a),stress_rows=nstress,strain_rows=nstrain,max_displacement_mm=float(np.linalg.norm(a[:,4:7],axis=1).max()),max_published_von_mises_MPa=mx,node_archive_member=nn,element_archive_member=ne,vtk_archive_member=base+f'ParaView_Visualization/00_run_Model_Frame{i}.vtk'))
 records.append(dict(id='tricuspid-valve-nonlinear',source='https://pmc.ncbi.nlm.nih.gov/articles/PMC8668829/',doi='10.1016/j.dib.2021.107664',family='Nonlinear anisotropic shell/contact biomechanics',cad='valve/Idealized_Geometry/Idealized_TV.igs',alternate_cad='valve/Idealized_Geometry/Idealized_TV.3dm',cad_validation=dict(valid=s.isValid(),faces=len(s.Faces()),edges=len(s.Edges()),solids=len(s.Solids()),type='IGES shell surface and construction curves; not a volumetric solid'),dimensioned_drawing_available=True,dimensioned_drawings=['valve/figure-1.jpg','valve/figure-2.jpg'],fem=dict(original_archive='valve/original-supplement.zip',solver='Abaqus/Explicit with published VUMAT',results=['ASCII nodal coordinates/displacements/reactions','ASCII element stress/strain','VTK result fields','ODB'],frames=frames,archive_sha256=sha(v/'original-supplement.zip')),license='CC BY 4.0 as stated in article supplement caption',benchmark_admitted=False,limitations=['One source problem, five frames are not five cases.','Abaqus required for direct original-model replay; TXT/VTK results can be read without Abaqus.','Large-deformation buckling/contact solution may vary; benchmark tolerances not certified.']))
# Optional selected UCSM files collected from original archive members.
u=OUT/'ucsm'
if (u/'download-manifest.json').exists():
 for cp in sorted(u.glob('*.step')):
  stem=cp.stem;sp=u/(stem+'_strains.json');mp=u/(stem+'.off');assert sp.exists() and mp.exists();s,check=cad(cp);assert check['valid'];raw=json.loads(sp.read_text())
  ids=np.array([int(k) for k in raw]);a=np.array([[v['minor_true_strain'],v['major_true_strain']] for v in raw.values()]);assert np.isfinite(a).all()
  with mp.open() as f:
   assert f.readline().strip()=='OFF';nv,nf,_=map(int,f.readline().split())
  assert ids.min()>=0 and ids.max()<nf
  coverage=dict(strain_rows=len(a),mesh_vertices=nv,mesh_faces=nf,missing_face_ids=nf-len(a),finite=True,fields=['minor_true_strain','major_true_strain'],minor_range=[float(a[:,0].min()),float(a[:,0].max())],major_range=[float(a[:,1].min()),float(a[:,1].max())],unit='dimensionless true strain',solver='LS-DYNA static implicit inverse analysis',mapping_status='IDs are in mesh face range; mapping semantics not solver-replayed')
  records.append(dict(id='ucsm-'+stem,source='https://zenodo.org/records/15327950',paper_doi='10.1016/j.cad.2025.103924',family='Sheet-metal inverse forming '+stem.split('_')[1],cad=str(cp.relative_to(OUT)),mesh=str(mp.relative_to(OUT)),strains=str(sp.relative_to(OUT)),cad_validation=check,dimensioned_drawing_available=False,benchmark_admitted=False,fem=coverage,limitations=['Published LS-DYNA static implicit inverse forming, not an explicit tool-contact forming trajectory.','Full material card/process solver input and output mapping still need review.','Some mesh faces have no strain row; coverage is recorded and missing values are not filled.','No per-case source dimensioned drawing verified.']))
(OUT/'catalog.json').write_text(json.dumps(dict(source_pairs=len(records),distinct_problem_families_note='160 GeoPINONet parameter instances in two families, one valve problem, plus selected UCSM parameter instances in four families. No new benchmark admissions.',records=records),indent=2))
print('CATALOG',len(records),flush=True)
