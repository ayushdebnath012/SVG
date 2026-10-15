"""Audit original downloaded assets; never generate geometry or run source solvers."""
from pathlib import Path
import json,zipfile,hashlib,csv,numpy as np,cadquery as cq
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'data/web-agentfem-brackets'; cases=D/'cases';cases.mkdir(exist_ok=True)
sums=json.loads((D/'SHA256SUMS.json').read_text());checks=[]
for n,d in sums.items():
 got=hashlib.sha256((D/n).read_bytes()).hexdigest();checks.append(dict(file=n,match=got==d));assert got==d,n
for p in sorted(D.glob('*.zip')):
 if not p.name.startswith(('fields-','geometry-')):continue
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  for n in z.namelist():
   parts=Path(n).parts; assert len(parts)==3 and parts[0]=='fem' and '..' not in parts
   out=cases/parts[1]/parts[2];out.parent.mkdir(exist_ok=True);out.write_bytes(z.read(n))
rows=[]
for split in ['train','validation','test']:
 for row in csv.DictReader((D/(split+'.csv')).open()):
  cid=row['case_id']; folder=cases/cid;s=json.loads((folder/'summary.json').read_text());shape=cq.importers.importStep(str(folder/'geometry.step')).val();assert shape.isValid() and len(shape.Solids())==1,cid
  with np.load(folder/'fields.npz',allow_pickle=False) as a:
   pts=a['points'];u=a['displacement'];stress=a['stress'];tri=a['triangles'];n=len(pts)
   assert pts.shape==u.shape==(n,3) and stress.shape==(n,) and tri.shape[1]==3
   assert all(np.isfinite(a[k]).all() for k in a.files) and tri.min()>=0 and tri.max()<n
   fixed=np.isclose(pts[:,2],0,atol=1e-7);top=np.isclose(pts[:,2],.189,atol=1e-7);assert fixed.any() and top.any()
   assert np.abs(u[fixed]).max()<1e-12
   derived={'seat_mean_displacement_mm':float(-u[top,2].mean()*1000),'max_displacement_mm':float(np.linalg.norm(u,axis=1).max()*1000),'sampled_peak_stress_mpa':float(stress.max()/1e6),'sampled_p95_stress_mpa':float(np.percentile(stress,95)) /1e6}
   assert all(np.isclose(v,s[k],rtol=1e-7,atol=1e-10) for k,v in derived.items()),cid
   assert float(row['physical_load_N'])==s['load_N']
   # CSV source reports equivalent 10kN; audit relation only, preserve raw reference fields.
   assert np.isclose(float(row['seat_deflection_mm_at_10kN']),s['seat_mean_displacement_mm']*10000/s['load_N'],rtol=1e-6)
   b=shape.BoundingBox();cad_bounds=np.array([[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]])
   field_bounds=np.array([pts.min(axis=0),pts.max(axis=0)]);err=float(np.abs(cad_bounds-field_bounds).max());assert err<1e-6,(cid,err)
   rows.append(dict(id=cid,split=split,cad=f'cases/{cid}/geometry.step',mesh=f'cases/{cid}/geometry.msh',fem_fields=f'cases/{cid}/fields.npz',source_summary=f'cases/{cid}/summary.json',physical_load_N=s['load_N'],material=dict(young_modulus_Pa=70e9,poisson_ratio=.33,density_kg_m3=2700),boundary_conditions=dict(fixed_plane_m='z=0',traction_plane_m='z=0.189',traction_Pa=[0,0,-s['load_N']/(.068*.074)]),units=dict(cad='STEP declares mm, numeric geometry matches field metres; factor 1000 inconsistency',field_coordinates='m',displacement='m',stress='Pa'),geometry=dict(valid=True,solids=len(shape.Solids()),faces=len(shape.Faces()),cad_field_bounds_max_error_m=err),reference=derived,field_nodes=n,surface_nodes=len(np.unique(tri)),surface_triangles=len(tri),mesh_volume_relative_error=s['mesh_volume_relative_error']))
  if len(rows)%32==0: print('Audited',len(rows),flush=True)
assert len(rows)==176 and len(set(r['id'] for r in rows))==176
catalog=dict(collection='Published AgentFEM bracket CAD + FEM pairs',source='https://huggingface.co/datasets/HaomingLuo/AgentFEM-Bracket-Elasticity',revision='8b020d1f3ae22e1583dfa3f2e466627d38ebeab3',license='CC BY 4.0, Haoming Luo (2026)',collected_date='2026-10-12',paired_cases=len(rows),problem_families=1,splits={s:sum(r['split']==s for r in rows) for s in ['train','validation','test']},no_local_cad_or_fem_generation=True,solver_runs=0,model_calls=0,certified_benchmark_admissions=0,original_dimensioned_drawings_verified=0,limitations=['One parametric bracket family, not 176 different engineering task types.','STEP declares millimetres but its coordinate values match FEM metres without conversion: source scale inconsistency; raw source files retained, CAD units unresolved.','Linear elastic demonstrator, nominal 9 mm mesh; publisher explicitly states not mesh converged.','No bolt contact, plasticity, fracture, experimental validation or certified strength labels.','Reference exported at linear nodes from quadratic displacement FEM; surface metrics are not volume or energy metrics.','Drawing-to-CAD track incomplete: CAD inspection views do not replace original dimensioned drawings.','Public test data may be contaminated; full solver replay and tolerances not independently certified.','Publisher model errors in evaluation.json are separate from FEM ground truth.'],records=rows)
(D/'catalog.json').write_text(json.dumps(catalog,indent=2))
(D/'validation.json').write_text(json.dumps(dict(publisher_checksums=checks,paired_cases=176,valid_single_solid_cad=176,finite_npz_fields=176,summary_values_recomputed_from_original_arrays=176,cad_field_numeric_bounds_agree_with_metres_despite_mm_step_declaration=176,zero_fixed_face_displacement=176,source_load_and_csv_consistency=176,archive_crc_pass=True,source_code_read_only=True,solver_runs=0,model_calls=0),indent=2))
print('Verified 176 source pairs; 1 family; splits',catalog['splits'])
