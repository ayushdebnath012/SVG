"""Package original web-source challenge candidates; deliberately no scoring admission."""
from pathlib import Path
import json,hashlib,shutil,zipfile
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/datasets/cadfem-challenges-v0.2'
DATA=ROOT/'data'
OUT.mkdir(parents=True,exist_ok=True)
records=[]; assets={}
def read(name):
 b=DATA/('web-cad-fem-'+name)
 return b,json.loads((b/'catalog.json').read_text())
def copy(b,rel,role):
 src=b/rel
 assert src.is_file(),src
 dst=OUT/'evaluator/source-assets'/b.name/rel
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 digest=hashlib.sha256(src.read_bytes()).hexdigest()
 assert digest==hashlib.sha256(dst.read_bytes()).hexdigest()
 key=str(dst.relative_to(OUT));assets[key]={'path':key,'source_local_path':str(src),'sha256':digest,'bytes':src.stat().st_size,'role':role}
 return key
def add(tid,b,d,title,physics,files,blockers,objective):
 paths=[copy(b,p,role) for p,role in files]
 paths.append(copy(b,'catalog.json','prior local source audit; not original FEM truth'))
 for p in b.iterdir():
  if p.is_file() and (p.name.lower().startswith(('license','notice')) or p.name=='README.md'):paths.append(copy(b,p.name,'source license/readme; verify scope before redistribution'))
 for p in b.glob('*manifest*.json'):paths.append(copy(b,p.name,'source provenance manifest'))
 records.append({'task_id':tid,'title':title,'status':'held_challenge_candidate','scored':False,'astra_outcome':'untested','difficulty_is_hypothesis':True,'physics':physics,'proposed_task':objective,'source_url':d.get('source'),'source_revision':d.get('revision_tree',d.get('source_revision',d.get('revision'))),'source_assets':paths,'admission_blockers':blockers,'reference_policy':'Use original tables/fields only after exact setup correspondence and convergence validation; no acceptance band assigned.','candidate_export_ready':False})
b,d=read('fcvm-breadth')
for name in ['Bar buckling','buckling_U100_3D','box girder','Plate_girder_EC3','Haltegriff_FEM_RC','IPE400_4']:
 r=next(x for x in d['records'] if x['name']==name)
 files=[(r['native_CAD'],'original native CAD'),(r['control_file'],'original solver controls'),(r['published_FEM_output'],'original published numerical output')]
 if r.get('original_VTK'):files.append((r['original_VTK']['path'],'original result fields'))
 for shape in r['native_shapes']:files.append((shape['extracted_path'],'unaltered native BREP member'))
 add('CH-NL-'+name.replace(' ','_'),b,d,name+' nonlinear load path',r['analysis_type'],files,r['grading_blockers']+['Do not use elastic eigenvalue as nonlinear collapse factor. Match source imperfection and continuation controls.'], 'Reproduce the published nonlinear load-displacement path and loss of load-carrying capacity using the supplied CAD and original material, support, imperfection and control definitions. Preserve the source displacement extraction convention.')
b,d=read('finray-contact')
files=[('01_geometry/source/real15.step','original component CAD'),(d['mesh'].split(' (')[0],'original assembly mesh')]
files += [(str(p.relative_to(b)),'original contact setup or result table') for folder in ['04_scripts','05_results/raw'] for p in (b/folder).rglob('*') if p.is_file() and p.suffix in ['.py','.csv','.txt']]
files.append((d['original_displacement_cache']['file'],'original author-exported displacement fields'))
add('CH-CONTACT-FINRAY',b,d,'Three-finger hyperelastic gripper','hyperelasticity; frictional contact; large deformation',files,d['limits'],'Reproduce the original closing and prescribed-pull reaction curves. Use the exact source direction and assembly transforms. Do not interpret held-load results as a measured release capacity.')
b,d=read('kresling-origami')
files=[(p,'original native CAD') for p in d['native_CAD']]+[(d['Abaqus_deck'],'original solver deck')]
files += [(str(p.relative_to(b)),'original material or FEM/experimental workbook; distinguish FEA columns') for p in (b/'extracted-original/Supporting_Materials_Zenodo/5_EXCEL').rglob('*.xlsx')]
add('CH-SNAP-KRESLING',b,d,'Kresling bistable cylinder','snap-through; viscoelasticity; hyperelastic creases',files,d['limitations'],'Reproduce the matched RF0.80 force-displacement and energy path, including the post-peak branch, after resolving the original CAD scale and material/time history.')
b,d=read('flange-contact');r=d['records'][0]; dd=dict(d,source=r['source'],revision=r['revision'])
add('CH-CONTACT-FLANGE',b,dd,'Thermally loaded bolted nozzle flange','bolt pretension; contact; thermal expansion',[(r['native_cad']['path'],'original native CAD'),(r['input'],'original solver deck'),(r['raw_rst'],'original binary FEM results')],d['limitations'],'Reproduce the published static pretension/loading/temperature stages using the source deck units and material cards; compare displacement and contact response. Do not treat stage labels as transient time.')
b,d=read('composite-pipe');r=d['raw_source_revisions'][0];rst=Path(r['raw_RST'])
add('CH-LAMINATE-PIPE',b,d,'Layered pipe pressure response','orthotropic layered shells; material orientation',[(d['original_IGES'],'original surface CAD'),(r['raw_RST'],'original binary FEM results'),(str(rst.with_name('ds.dat')),'original solver deck')],d['limits'],'Reproduce the archived 18.1 layered-shell pressure response using the full-length surface CAD and exact section/material cards; resolve ply axes and output conventions before defining any failure metric.')
# Batch 2: additional source families, original result bytes only.
b,d=read('composite-dynamics')
for r in d['records']:
 if r['id']=='fatigue':continue
 folder=b/'pydpf-composites'/r['id']; files=[]
 for p in folder.rglob('*'):
  if not p.is_file():continue
  if p.name.startswith('UNVERIFIED') or p.suffix=='.npz' or p.name in ['reader-log.txt','reader-audit.json','step-audit.json']:continue
  files.append((str(p.relative_to(b)),'original CAD/setup/result or published documentation; see source manifest'))
 dd=dict(d,source=d['source'])
 add('CH-COMPOSITE-'+r['id'].upper(),b,dd,r['description'],r['description'],files,d['limitations']+[r['status']], 'Reproduce the matched source response and ply-resolved results using the original layup, load history and recovery conventions. Validate native CAD and result decoding before scoring. '+('For impact, verify coordinates versus displacements and shell integration-point mapping.' if r['id']=='lsdyna_bird_strike' else ''))
 records[-1]['documentation_url']=r['documentation']
b,d=read('quadcopter-dynamics'); r=next(x for x in d['saved_systems'] if x['analysis']=='modal')
files=[(str(p.relative_to(b)),'original native assembly/part or dimensioned drawing') for p in (b/'01_SolidWorks_CAD').rglob('*') if p.is_file() and p.suffix.lower() in ['.sldasm','.sldprt','.pdf']]
files += [(r['source_RST'],'original modal result'),(r['deck'],'original modal setup')]
add('CH-MODAL-QUADCOPTER',b,d,'Quadcopter assembly modal response','assembly modes; concentrated masses; closely spaced eigenvalues',files,d['limits'],'Reconstruct the analysis assembly from the source CAD or drawing set, map the original point masses and supports, and reproduce the six published modes. Compare eigenspaces for near-degenerate frequencies rather than arbitrary mode order.')
b,d=read('titanium-wing');files=[(d['native_geometry'],'original native CAD')]
for r in d['records']:files += [(r['raw_RST'],'original static or prestressed modal result'),(r['original_deck'],'original static or modal deck')]
add('CH-PRESTRESS-WING',b,d,'Titanium wing prestressed modes','static prestress and modal restart',files,d['limits'],'Reproduce the original static prestress followed by modal analysis, using source pressure units and support scopes. Do not substitute a flutter calculation or realistic flight loads for the published setup.')
b,d=read('brake-thermal'); raw=Path(d['raw_result'])
add('CH-THERMAL-BRAKE',b,d,'Perforated brake rotor thermal field','temperature-dependent convection; perforated CAD', [('CAD Files/Disk.STEP','original STEP CAD'),(d['raw_result'],'original thermal result'),(str(raw.with_name('ds.dat')),'original thermal deck')],d['limitations'],'Reproduce the steady temperature field and minimum temperature with source temperature-dependent convection. The prescribed maximum temperature alone is not a meaningful accuracy target.')
b,d=read('pressure-vessel')
add('CH-PRESSURE-VESSEL',b,d,'Nozzled pressure vessel on saddles','pressure loading; support scoping; surface-to-volume correspondence',[('CIRCULAR.igs','original IGES surface CAD'),(d['raw_result'],'original structural result'),(d['source_input'],'original structural deck')],d['limitations'],'Match the circular-head geometry to the archived pressure solution and reproduce displacement and nonsingular stress measures under the original material and support definitions.')
for r in records:
 r['source_group']=next(x.split('/')[2] for x in r['source_assets'] if x.startswith('evaluator/source-assets/'))
 r['admission_blockers'] += ['This is an untested challenge hypothesis; solver availability and resource needs must be matched across models.']

(OUT/'evaluator').mkdir(exist_ok=True)
(OUT/'evaluator/challenge-candidates.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
(OUT/'evaluator/asset-manifest.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in assets.values()))
summary={'candidate_tasks':len(records),'added_this_batch':8,'previous_candidates':10,'active_scored_additions':0,'astra_tested':0,'original_asset_files_including_provenance':len(assets),'asset_bytes':sum(a['bytes'] for a in assets.values()),'source_collections':len({r['source_group'] for r in records}),'new_source_discoveries':0,'relationship':'New challenge-task registry curated from existing web-collected source library; not eighteen new independent geometry families.','base_release':'cadfem-bench-v1.7','model_calls':0,'locally_generated_CAD_or_FEM':0}
(OUT/'manifest.json').write_text(json.dumps(summary,indent=2)+'\n')
lines=['# CADFEM challenge candidates v0.2','','Eighteen harder task candidates added to the dataset collection. All remain held; none is a confirmed Astra failure or new scored primary task. These curate existing web-collected assets, not new source discoveries. Six tasks share the fcVM source; variants and overlapping CAD must be grouped in any evaluation split.','','All source CAD, controls and result evidence are evaluator-only: do not expose this entire folder to a model. Before candidate export, isolate geometry and complete setup from answers. Source scripts were copied, not executed. Original values were not regenerated. Native-only CAD and solver dependencies are explicit admission limitations. No COMSOL sources selected. Mixed licensing: local research package only.','','| Task | Physics |','|---|---|']
lines += ['| '+r['title']+' | '+r['physics']+' |' for r in records]
lines += ['','## Admission requirements','','Each record lists its specific blockers. Resolve CAD/result correspondence, material and boundary conditions, units, solver compatibility, and convergence; then freeze scoring tolerances before model evaluation. Use the same tool/reasoning/time limits across models. Retain passes as well as failures. This adaptively selected challenge set is not an unbiased estimate of general benchmark performance.','','Sources:']
lines += ['- '+s for s in sorted(set(r['source_url'] for r in records))]
(OUT/'README.md').write_text('\n'.join(lines)+'\n')
shutil.copy2(__file__,OUT/'build_challenge_candidates_v02.py')
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
(OUT/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(OUT))+'\n' for p in files))
archive=OUT.with_name(OUT.name+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
 for p in OUT.rglob('*'):
  if p.is_file():z.write(p,str(Path(OUT.name)/p.relative_to(OUT)))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps(summary,indent=2));print(archive)
