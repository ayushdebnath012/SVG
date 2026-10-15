"""Migrate the archived v1.0 package to a conservative published-source v1.1 pilot.
No solver calls or geometry generation. Original v1.0 snapshot is mandatory.
"""
from pathlib import Path
import argparse, collections, hashlib, json, re, shutil, zipfile

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def jsonl(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(''.join(json.dumps(r)+'\n' for r in x))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);ap.add_argument('--package',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);a=ap.parse_args()
 w,p=a.workspace.resolve(),a.package.resolve();geo=w/'cvpr2027/output/geometry-references-v1.3';data=w/'cvpr2027/data';ev=p/'evaluator';held=p/'held'; held.mkdir(exist_ok=True)
 with zipfile.ZipFile(a.snapshot) as z:
  ts=[json.loads(x) for x in z.read('candidate/tasks.jsonl').decode().splitlines()];rs=[json.loads(x) for x in z.read('evaluator/references.jsonl').decode().splitlines()];regs=[json.loads(x) for x in z.read('evaluator/registry.jsonl').decode().splitlines()]
 oldr={x['task_id']:x for x in rs};active=[];refs=[];ht=[];hr=[]
 removed=[]
 for t in ts:
  r=oldr[t['task_id']];tid=t['task_id'];reason=None
  if t['track']=='C':reason='External design evaluator and environment not packaged; locally defined design variants excluded from published-source evaluation.'
  elif tid in ('A-SIMJEB-analysis-15','A-SIMJEB-analysis-120'):reason='Source STEP imports but fails OpenCASCADE BRepCheck validity; no silent repair.'
  elif t['track']=='B' and t['family']!='rigging-plate' and not (geo/(tid+'-reference.step')).exists():reason='Reconstruction geometry validator and linked workflow verification not validated; retained as unscored controls/specifications.'
  if reason:
   t['status']=r['status']='held';t['hold_reason']=r['hold_reason']=reason;ht.append(t);hr.append(r)
   src=p/'candidate/tasks'/tid;dest=held/'inputs'/tid
   if src.exists():
    if dest.exists():shutil.rmtree(dest)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(src),str(dest))
   continue
  t['status']=r['status']='active';t['tier']=r['tier']={'gold':'source_backed_pilot','silver':'figure_reference','control':'control'}[t['tier']]
  t['engineering_family']=r['engineering_family']='simjeb-bracket' if t['family'].startswith('simjeb') else t['family']
  t['readiness']={'independently_reproduced':False,'workflow_scoring':'trusted_review_required','tolerances':'provisional_source_protocol'}
  if t['family']=='simjeb-analysis':
   remove=[k for k,v in r['references'].items() if v['ref_class']=='verifier'];removed.append({'task_id':tid,'outputs':{k:r['references'].pop(k) for k in remove},'status':'excluded_local_solver_reference'})
   t['outputs']=[o for o in t['outputs'] if o['key'] not in remove]
   body=t['prompt'].split('Pass criterion:')[0]
   body+='The attached STEP is a published competition design. Compute the maximum displacement magnitude for each of the four load cases. Targets are the original published OptiStruct displacement maxima; no locally computed stress target or pass verdict is scored.\n'
   r['flags']=['Original published displacement targets only; source-model reproduction and tolerance remain provisional.']
  else:body=t['prompt'].split('\n\nOutputs:')[0]
  if t['family']=='cadworld-freecad-fem':
   r['references']['max_shear_stress_MPa']=r['references'].pop('max_tresca_MPa')
   for o in t['outputs']:
    if o['key']=='max_tresca_MPa':o.update(key='max_shear_stress_MPa',definition='maximum over nodes of (major principal stress - minor principal stress)/2; publisher CSV column Tresca Stress')
   body+='\nThe publisher column named Tresca Stress is maximum shear stress, (sigma1 - sigma3)/2. Report this half-difference as max_shear_stress_MPa, not the full principal-stress difference. This task reproduces the source linear model; it is not a validated physical strength assessment.'
  if t['track']=='B' and t['family']!='rigging-plate':
   body+={'B-NAFEMS-LE1':'\nLE1 is a 2-D plane-stress problem. For part.step, extrude the quarter membrane 100 mm along +z from z = 0 (an exchange convention only; analyse it in plane stress).',
          'B-NAFEMS-LE10':'\nThe drawing is dimensioned in metres; export part.step in millimetres.',
          'B-NAFEMS-LE11':'\nThe source geometry is given in metres; export part.step in millimetres (1 m = 1000 mm).'}.get(tid,'')
   body+='\nThe evaluator aligns part.step to a reference solid built from this specification (bounding-box centres, the 24 proper axis rotations; mirror images are not accepted) and requires a relative symmetric volume difference of at most 2 %; it separately reviews features, regions and boundary-condition faces.'
  if t['track']=='B' and t['family']=='rigging-plate':
   body+='\nModel the plate with its length, width and 12 mm thickness along the coordinate axes; any position and any of the 24 axis-aligned orientations is accepted: the evaluator aligns part.step to the original CAD (bounding-box centres, proper axis rotations; mirror images are not accepted) before measuring volume overlap, and separately reviews drawing features and boundary-condition mapping.'
  t['prompt']=body+'\n\nOutputs:\n'+'\n'.join('- '+o['key']+' ['+o['unit']+']: '+o['definition'] for o in t['outputs'])+'\n\nSubmit results.json containing exactly an outputs object with these numeric keys. Also submit main.py, part.step, mesh.msh, fields.npz, solver.log, refinement.json and environment.json. See candidate README for the artifact contract. Correct numerical answers alone do not establish workflow completion.'
  t['required_artifacts']=['results.json','main.py','part.step','mesh.msh','fields.npz','solver.log','refinement.json','environment.json']
  r['flags'].append('No independent FEM reproduction in this release; end-to-end pass requires evaluator-owned workflow review.')
  active.append(t);refs.append(r)
 jsonl(held/'tasks.jsonl',ht);jsonl(held/'references.jsonl',hr);jsonl(held/'excluded-local-targets.jsonl',removed)
 # Evidence store: copy originals, record exact bytes and original location. Never execute source files.
 manifest=[];by_path={};task_evidence=collections.defaultdict(list)
 def add(tid,src,dest=None,role='original_source'):
  src=Path(src)
  assert src.is_file(),src
  rel=dest or str(src.relative_to(w/'cvpr2027'))
  dst=ev/'evidence'/rel
  if rel not in by_path:
   dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
   rec={'path':str(dst.relative_to(ev)),'sha256':sha(dst),'bytes':dst.stat().st_size,'original_workspace_path':str(src.relative_to(w)),'role':role}
   manifest.append(rec);by_path[rel]=rec
  if by_path[rel]['path'] not in task_evidence[tid]:task_evidence[tid].append(by_path[rel]['path'])
 def metadata(tid,root):
  for name in ('catalog.json','download-manifest.json','source-metadata.json','README.md','README.txt','LICENSE','LICENSE.txt','COPYING'):
   f=root/name
   if f.exists():add(tid,f,role='source_metadata_or_notice')
 cats={k:json.loads((data/k/'catalog.json').read_text()) for k in ['web-agentfem-brackets','web-cad-fem-additions','web-cad-fem-cycloidal-drive']}
 gz=zipfile.ZipFile(data/'web-cad-fem-additions/geopinonet/GeoPINONet_Plate_with_a_hole_dataset_v2.zip')
 for t,r in zip(active,refs):
  tid=t['task_id'];fam=t['family']
  if fam=='simjeb-analysis':
   add(tid,w/'cvpr2027/tmp/simjeb/dl/f4639239','simjeb/published-metadata.csv')
  elif fam=='agentfem-bracket':
   root=data/'web-agentfem-brackets';rec=next(x for x in cats[root.name]['records'] if 'A-AGENTFEM-'+x['id']==tid)
   for key in ('source_summary','fem_fields','mesh','cad'):add(tid,root/rec[key])
   metadata(tid,root)
  elif fam=='geopinonet-holed-plate':
   root=data/'web-cad-fem-additions';rec=next(x for x in cats[root.name]['records'] if x['family']=='Plate_with_a_hole' and x['source_split']=='model_val' and 'A-GEOPINO-PLATE-'+x['source_case']==tid)
   for f in rec['fem']:
    member=f['archive_member'];b=gz.read(member);assert hashlib.sha256(b).hexdigest()==f['sha256']
    dst=ev/'evidence/geopinonet'/member;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    manifest.append({'path':str(dst.relative_to(ev)),'sha256':sha(dst),'bytes':len(b),'archive':'GeoPINONet_Plate_with_a_hole_dataset_v2.zip','archive_member':member,'role':'original_source'})
    task_evidence[tid].append(str(dst.relative_to(ev)))
   metadata(tid,root)
  elif fam=='cycloidal-drive-components':
   root=data/'web-cad-fem-cycloidal-drive';loc=r['references']['max_displacement_mm']['provenance'].split(' (')[0];frd=root/loc
   for f in [frd,frd.with_suffix('.inp'),*frd.parent.glob('*.FCStd')]:add(tid,f)
   metadata(tid,root)
  elif fam=='morphing-wing-plates':
   root=data/'web-cad-fem-aerospace/morphing-modal'
   for f in [*root.glob('*.xlsx'),*root.glob('ABAQUS inp Files/*.inp'),*root.glob('Nastran bdf Files/*.bdf')]:add(tid,f)
   metadata(tid,root)
  elif fam=='cadworld-freecad-fem':
   root=data/'web-cadworld-fem'
   for rel in ['evaluation_examples/fixtures/fem/freecad-fem-001.csv','evaluation_examples/fixtures/fem/freecad-fem-001.FCStd','evaluation_examples/fixtures/precondition/freecad-fem-001-precondition.FCStd','evaluation_examples/examples/fem/freecad-fem-001.json','desktop_env/evaluators/metrics/freecad_fem.py']:add(tid,root/rel)
   metadata(tid,root)
  elif fam=='feenox-valve-transient':
   root=data/'web-cad-fem-valve-transient'
   for name in ('valve-1.csv','valve.fee','valve.geo','valve-scl-coords.fee','valve-internal-1.csv','asme-properties.fee'):add(tid,root/name)
   metadata(tid,root)
  elif fam=='rigging-plate':
   root=data/'web-cad-fem-rigging-plate'
   rel=r['references']['max_von_mises_MPa']['provenance'].split(' legend ')[0]
   add(tid,root/rel);metadata(tid,root)
   if t['track']=='B':
    source=p/'candidate/tasks/A-RIGGING-test1/riggingplate.step';add(tid,source,'geometry/rigging-reference.step')
    r['geometry_check']={'reference_step':'evidence/geometry/rigging-reference.step','reference_sha256':sha(source),'relative_symmetric_difference_limit':0.02,'alignment':'bbox_centre_and_24_proper_axis_rotations','note':'Automated necessary gate, plus trusted feature/setup review. The drawing does not fix the source CAD frame, so the submission is aligned before comparison.'}
  elif fam=='nafems-calibration':
   root=w/'cvpr2027/tmp/published-fem-pilot-v1/evaluator-only'/tid.split('-',1)[1]
   for f in root.iterdir():
    if f.is_file():add(tid,f,role='source_or_prior_extraction')
  elif fam=='femcad-hard':
   root=data/'femcad-hard-v1'
   for f in (root/'tasks.jsonl',root/'README.md',w/'cvpr2027/scripts/build_femcad_hard_dataset.py'):add(tid,f,role='source_or_prior_extraction')
  elif fam=='fcvm-buckling':
   root=w/'cadfem-bench-v1.1-followup/published-source-expansion';study=w/'cvpr2027/output/fcvm-buckling-study'/tid[len('A-FCVM-'):]
   name=next(f.stem for f in (root/'freeCAD files').glob('*.FCStd') if f.stem.replace(' ','_')==tid[len('A-FCVM-'):])
   for f in (root/'freeCAD files'/(name+'.FCStd'),root/'control files'/(name+'.inp'),root/'output files'/(name+'.out')):add(tid,f,'fcvm/'+str(f.relative_to(root)))
   for f in ('README.md','catalog.json','download-manifest.json'):
    if (root/f).exists():add(tid,root/f,'fcvm/'+f,role='source_metadata_or_notice')
   for f in (study/'setup.json',study/'assessment.json',*sorted(study.glob('h-*/result.json')),*sorted(study.glob('coarse-h-*/result.json'))):add(tid,f,'fcvm-buckling-study/'+str(f.relative_to(study.parent)),role='tolerance_evidence')
   for f in ('scripts/fcvm_buckling_check.py','scripts/cadfem_bench/fam_fcvm.py','scripts/cadfem_bench/fcvm_extract.py'):add(tid,w/'cvpr2027'/f,'fcvm-buckling-study/code/'+Path(f).name,role='tolerance_evidence_code')
  else:raise ValueError(fam)
  if t['track']=='B' and fam!='rigging-plate':
   ref=geo/(tid+'-reference.step');add(tid,ref,'geometry/'+tid+'-reference.step',role='geometry_reference');add(tid,geo/'references.json','geometry/references.json',role='geometry_reference_validation')
   r['geometry_check']={'reference_step':'evidence/geometry/'+tid+'-reference.step','reference_sha256':sha(ref),'relative_symmetric_difference_limit':0.02,'alignment':'bbox_centre_and_24_proper_axis_rotations','note':'Evaluator-only reference solid built from the specification and checked against an independent volume; automated necessary gate plus trusted feature/setup review.'}
  r['evidence_files']=task_evidence[tid]
  assert r['evidence_files']
 gz.close()
 jsonl(ev/'references.jsonl',refs);jsonl(p/'candidate/tasks.jsonl',active);jsonl(ev/'evidence-manifest.jsonl',manifest)
 for reg in regs:
  if reg['status']=='admitted':
   rows=[t for t in active if t['family'] in reg['families']]
   reg['tasks']=len(rows)
   reg['status']='pilot' if rows else 'held'
   reg['readiness']='No independently reproduced or certified tasks'
   if not rows:reg['blocker']='No active tasks after v1.1 validation gates'
 jsonl(ev/'registry.jsonl',regs)
 counts={'version':'1.1','tasks':len(active),'graded_outputs':sum(len(r['references']) for r in refs),'by_track':dict(collections.Counter(t['track'] for t in active)),'by_family':dict(collections.Counter(t['family'] for t in active)), 'engineering_families':len(set(t['engineering_family'] for t in active)), 'held_tasks':len(ht),'excluded_local_targets':190,'reference_classes':dict(collections.Counter(v['ref_class'] for r in refs for v in r['references'].values())), 'independently_reproduced_tasks':0,'solver_runs_this_migration':0,'model_calls':0,'source_evidence_files':len(manifest),'source_evidence_bytes':sum(x['bytes'] for x in manifest),'original_snapshot_sha256':sha(a.snapshot)}
 dump(ev/'validation.json',counts)
 dump(ev/'task-hashes.json',{t['task_id']:hashlib.sha256(json.dumps(t,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest() for t in active})
 # Preserve original scripts outside the executable release; entry points below replace old generators.
 legacy=w/'cvpr2027/output/audits/cadfem-bench-v1/original-builders'
 if not legacy.exists():shutil.copytree(p/'scripts/cadfem_bench',legacy,ignore=shutil.ignore_patterns('__pycache__'))
 print(json.dumps(counts,indent=2))
if __name__=='__main__':main()
