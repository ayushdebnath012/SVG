"""Collect original web assets only. Inspection renders do not create geometry or solve FEM."""
from pathlib import Path
import json,shutil,hashlib,csv,tarfile,numpy as np,zipfile
ROOT=Path(__file__).resolve().parents[1]; TMP=ROOT/'tmp/cad-variety-search'; DATA=ROOT/'data/web-cad-fem-variety';DATA.mkdir(exist_ok=True)
def stage(folder,exclude=()):
 dest=DATA/folder;dest.mkdir(exist_ok=True)
 for f in (TMP/folder).iterdir():
  if f.is_file() and f.name not in exclude:shutil.copy2(f,dest/f.name)
 return dest
stage('hip-contact');stage('hirenasd');stage('fokker-f28');stage('turbine-blade',('FE_Reduced_Model-xpbwEk.mat','VIEW_MEASUREDandPROCESSED_DATA.m','BENDING_MODE_data_structure.xlsx'))
blade=json.loads((TMP/'blade-state.json').read_text())['dataset']['snapshot'];(DATA/'turbine-blade/source-metadata.json').write_text(json.dumps(blade,indent=2))
shutil.copy2(TMP/'7724227.json',DATA/'fokker-f28/source-metadata.json')
validation={'cad':json.loads((TMP/'cad-validation.json').read_text()),'additional':json.loads((TMP/'result-validation.json').read_text())}
for r in validation['cad']+validation['additional']['cad']:r['file']=r['file'].split('cad-variety-search/')[-1]
# Extract original CSV values; preserve complete original file as well.
rows=list(csv.reader((DATA/'hip-contact/Results.csv').open()));ref=[]
for i in range(4):
 ref.append({'wear_penetration_mm':float(rows[4+i][0]),'cup_outer_diameter_mm':40,'cup_angle_deg':45,'cup_peak_von_mises_MPa':float(rows[4+i][2]),'bearing_peak_contact_pressure_MPa':float(rows[4+i][16]),'cement_peak_von_mises_MPa':float(rows[14+i][2]),'cement_peak_max_principal_MPa':float(rows[24+i][2]),'cement_peak_shear_MPa':float(rows[34+i][2])})
assert all(np.isfinite(list(x.values())).all() for x in ref)
(DATA/'hip-contact/matched-reference-values.json').write_text(json.dumps(ref,indent=2));validation['hip_matched_reference_rows']=ref
# Original modal data rows, copied without rescaling, normalization or solver execution.
with tarfile.open(DATA/'hirenasd/modes_HIRENASD_coarse_Centaur.tar.gz') as t:
 f=t.extractfile('mode1_HIRENASD_coarse_Centaur.dat');headers=[f.readline().decode().strip() for _ in range(3)];sample=[f.readline().decode().strip() for _ in range(5)]
 (DATA/'hirenasd/mode1-original-five-row-excerpt.txt').write_text('\n'.join(headers+sample)+'\n')
records=[
 {'id':'hip-cement-contact','family':'Hip implant contact and cement fixation','source':'https://archive.researchdata.leeds.ac.uk/15/','doi':'10.5518/13','authors':'Xijin Hua and Zhongmin Jin, University of Leeds','license':'CC BY 4.0','cad':['hip-contact/'+f.name for f in (DATA/'hip-contact').glob('*.igs')],'solver_input':['hip-contact/FE_model_cemented_THR.inp'],'fem_results':['hip-contact/Results.csv'],'reference_type':'Published FEM scalar results, MPa','paired_configuration_count':4,'limitations':['Only 40 mm cup, 45 degree references match supplied component CAD; other CSV rows are not CAD-paired here.','Pelvis and cement are valid IGES surfaces, not closed solids; cups are solids.','No separate native femoral-head CAD verified; head geometry remains in solver deck.','Supplied input deck represents one configuration; mapping of all four wear states to an executable setup remains to audit.','No certified replay tolerance or original dimensioned drawing verified.']},
 {'id':'hirenasd-wing-modes','family':'Aircraft wing structural vibration / aeroelastic modal basis','source':'https://c3.ndc.nasa.gov/dashlink/resources/354/','supporting_source':'https://c3.ndc.nasa.gov/dashlink/resources/274/','authors':'HIRENASD / Aeroelastic Prediction Workshop contributors, NASA DASHlink distribution','license':'Public NASA download; dataset-specific redistribution license not stated on inspected pages.','cad':['hirenasd/hirenasd_AePW_DLR.igs'],'solver_input':['hirenasd/gridmod.bdf.zip','hirenasd/ms103_str_t293.bdf.zip'],'fem_results':['hirenasd/modes_HIRENASD_coarse_Centaur.tar.gz'],'reference_type':'Published interpolated structural mode-shape fields on Centaur grid; not stress or forced response','source_problem_count':1,'mode_count':10,'nodes_per_mode':159841,'limitations':['IGES surface CAD in mm; published field coordinates in m. Bounds agree after 1e-3 conversion.','Structural BDF coordinate systems differ; original coordinate-system PDF included. Explicit frame correspondence remains to audit.','Modal amplitude/sign and interpolation conventions must be resolved before scoring; normalization-invariant comparison needed.','Frequency reference file not downloaded; resource 400 reports private access. Do not claim frequency ground truth from this package.','Not a complete coupled aerodynamic FEM solution; no verified dimensioned drawing.']},
 {'id':'blade-dovetail-reduced-model','family':'Turbine mock-blade dovetail contact dynamics','source':'https://data.mendeley.com/datasets/xkssd7gr92/1','doi':'10.17632/xkssd7gr92.1','authors':'Daniele Botto and Matteo Glorioso, Politecnico di Torino','license':'CC BY 4.0','cad':['turbine-blade/Assembly.STEP','turbine-blade/DummyBlade.STEP','turbine-blade/Slot.STEP'],'fem_results':['turbine-blade/FE_Reduced_Model.mat'],'reference_type':'Published reduced FE mass/stiffness matrices and connectivity, not solved response fields','source_problem_count':1,'preload_count':16,'matrix_dimensions':{'M_GLOB':[1968,1968],'K_GLOB_SE':[1968,1968,16]},'units':{'mass':'tons (source worksheet)','stiffness':'N/mm','coordinates':'mm','preload':'N'},'limitations':['Experimental decay/frequency/loss-factor arrays are not FEM ground truth and were not downloaded.','No full FE solver deck verified; original FE operators can be used for operator/reduction evaluation, not direct full-stress reference scoring.','No stress/displacement result fields supplied in downloaded FE reduced-model file.','No certified response tolerance or verified dimensioned drawing.','Two MAT download entries share identical bytes; only one original copy packaged.']},
 {'id':'f28-fuselage-crash','family':'Aircraft fuselage crashworthiness and impact','source':'https://zenodo.org/records/7724227','doi':'10.5281/zenodo.7724227','authors':'Marco Desiderio et al., TU Delft','license':'CC BY 4.0','cad':['fokker-f28/CAD_F28_'+n+'FR.stp' for n in ['4','5','6']],'solver_input':['fokker-f28/Abaqus_20220906_F28_'+n+'FR_JOB1.inp' for n in ['4','5','6']],'fem_results':['fokker-f28/FIG_mean_accelerations_N_frames.pdf','fokker-f28/FIG_Average_accelerations_mesh_sensitivity.pdf','fokker-f28/FIG_DRIs_mesh_sensitivity.pdf'],'reference_type':'Published numerical FEM acceleration / dynamic-response-index plots; no machine-readable response arrays verified','paired_configuration_count':3,'source_problem_count':1,'limitations':['STEP CAD consists of shell surfaces, appropriate for source shell models; not volumetric solid CAD.','Plots also contain experimental curves; FEM and experiment must be separated during digitization.','No CSV, ODB, or full-field/time-history output in collected subset. Numerical auto-scoring needs reviewed digitization and uncertainty.','Only 4/5/6-frame no-friction/no-damage decks selected; source variant mapping discrepancy avoided.','Published source CAD/real comparison image included; no verified dimensioned drawing.']}
]
# Compare wing field and CAD extents only, without claiming complete mesh registration.
w=next(r for r in validation['cad'] if 'hirenasd' in r['file']);bounds=np.array(w['bounds'])*.001;mb=np.array(validation['additional']['wing_modes'][0]['coordinate_bounds']);validation['wing_bounds_max_error_m']=float(abs(bounds-mb).max());assert validation['wing_bounds_max_error_m']<1e-6
catalog={'collection':'Additional web-published CAD/FEM engineering varieties','collected_date':'2026-10-12','new_source_collections':4,'new_problem_families':4,'certified_benchmark_admissions':0,'no_local_cad_or_fem_generation':True,'solver_runs':0,'model_calls':0,'records':records}
(DATA/'catalog.json').write_text(json.dumps(catalog,indent=2));(DATA/'validation.json').write_text(json.dumps(validation,indent=2))
readme='''# Additional web CAD/FEM varieties

Four original source collections, four problem families. CAD and reference files are downloaded from publishers; no geometry, FEM solution or model answer generated. Inspection images render original CAD only. No COMSOL files. No frontier model calls or solver runs.

## What was collected

| Family | Original CAD | Published numerical reference | Status |
|---|---|---|---|
| Hip replacement contact / cement fixation | Six IGES component files | CSV peak cup stress, bearing pressure, cement stresses in MPa | Four wear states have corresponding 40 mm / 45 degree component CAD; one supplied solver setup |
| HIRENASD wing vibration | IGES surface CAD | Ten mode-shape fields, 159,841 nodes each | Modal references; not forced-response/stress fields |
| Turbine mock-blade dovetail | STEP assembly + blade + slot; IGES alternatives | 1968 x 1968 FE mass matrix, 16 stiffness matrices, connectivity | Reduced FE operators, not solved response references |
| Fokker F28 crashworthiness | Three STEP surface variants, paired Abaqus decks | Published acceleration and DRI plots | Plot references; automatic numerical scoring pending digitization |

See catalog.json for source URLs, attribution, license and per-family blockers. Original source files are unchanged; matched-reference-values.json and the five-row excerpt copy published values only. The original hip CSV includes other sizes/angles whose native CAD is not supplied. Do not count those as additional CAD-paired cases. Modes, preloads and frame counts do not increase the number of task families.

## Validation

All selected STEP and IGES geometries import and pass OpenCascade validity checks. Hip pelvis/cement, wing and fuselage are surfaces, not closed solids. Turbine assembly contains three solids. Ten modal arrays contain finite data; each has 159,841 seven-column nodal rows (x,y,z,node-ID,three mode components). Modal-coordinate bounds agree with IGES extents after converting mm to m; this alone does not prove complete registration. Blade matrices, connectivity and preload entries are finite; the mass matrix is symmetric. ZIP source archives pass CRC checks. Download manifests and package-manifest.json record SHA-256.

## Benchmark readiness

Zero new certified admissions. Hip scalar results are the closest addition to direct numerical scoring; executable wear-state mapping and convergence tolerances remain to audit. Wing modal comparison needs frame, normalization and mode pairing. Blade matrices support reduced-operator evaluation; experimental response is separate and not mislabeled as FEM. Crash plots need digitization with uncertainty. No verified dimensioned drawing in these four sources; supplied original geometry and CAD inspection views support the CAD-input track, while the drawing-input track remains incomplete.

## Rejected or quarantined leads

PHASMA satellite thermal repository: STEP/Elmer setups found, but no published solved temperature arrays verified. Machine-tool thermal data: numerical temperature references found but matching native CAD missing. Metal/resin lattice data: FEM pull-force spreadsheets but native CAD missing. CADWORLD: three FreeCAD/result-CSV cases downloaded in the research cache; excluded from this package pending stress-unit and elastic-validity review (source claims up to terapascal stresses). Mesh-only sources and COMSOL datasets excluded.

## License and attribution

Hip: Hua and Jin, University of Leeds, DOI 10.5518/13, CC BY 4.0. Blade: Botto and Glorioso, DOI 10.17632/xkssd7gr92.1, CC BY 4.0. F28: Desiderio et al., TU Delft, DOI 10.5281/zenodo.7724227, CC BY 4.0. NASA HIRENASD: public distribution; dataset-specific license not stated on inspected pages, retained as unresolved. License link: https://creativecommons.org/licenses/by/4.0/ .
'''
(DATA/'README.md').write_text(readme)
manifest=[]
for f in sorted(DATA.rglob('*')):
 if f.is_file() and f.name!='package-manifest.json':manifest.append({'file':str(f.relative_to(DATA)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(DATA/'package-manifest.json').write_text(json.dumps(manifest,indent=2))
sel=ROOT/'data/web-complex-fem/selected-dataset.json';obj=json.loads(sel.read_text());obj['additional_web_varieties']={'catalog':'cvpr2027/data/web-cad-fem-variety/catalog.json','validation':'cvpr2027/data/web-cad-fem-variety/validation.json','source_collections':4,'new_problem_families':4,'certified_benchmark_admissions':0,'status':'Original CAD and references collected; hip scalars, wing modal fields, blade reduced operators and crash plots reported separately.'};sel.write_text(json.dumps(obj,indent=2)+'\n')
print('STAGED',len(manifest),'files',sum(r['bytes'] for r in manifest),'bytes');print('HIP REFERENCES',ref)
