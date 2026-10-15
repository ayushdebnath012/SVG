"""Correct the final v1.6 snapshot without modifying historical releases or runs."""
import argparse,collections,hashlib,json,shutil,urllib.request
from pathlib import Path

def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def lines(p,x):p.write_text(''.join(json.dumps(r)+'\n' for r in x))
def build(source,out,publisher_pages):
 if out.exists():raise FileExistsError(out)
 shutil.copytree(source,out)
 history=out/'evaluator/history/v1.6-final';history.mkdir(parents=True)
 for rel in ['README.md','evaluator/validation.json','evaluator/verification.json','evaluator/DATASET_CARD.md']:
  d=history/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(out/rel,d)
 for f in (out/'report').glob('*.pdf'):shutil.move(str(f),history/f.name)
 reasons={'B-FEMCAD-031':'Numerical target locally evaluated from capacitor formula; violates strict source-published-only rule.',
          'B-FEMCAD-058':'Three numerical targets locally evaluated from pressure-hull formulas; violates strict source-published-only rule.',
          'B-FEMCAD-057':'Original publisher output establishing 230.197 MPa not verified/bundled; held pending direct source-output evidence.'}
 ev=out/'evaluator';tasks=jl(out/'candidate/tasks.jsonl');refs=jl(ev/'references.jsonl');held=jl(out/'held/tasks.jsonl');heldrefs=jl(out/'held/references.jsonl')
 for t in tasks:
  if t['task_id'] in reasons:
   tid=t['task_id'];t['status']='held';t['hold_reason']=reasons[tid];held.append(t)
   r=next(r for r in refs if r['task_id']==tid);r['status']='held';r['hold_reason']=reasons[tid]
   for q in r['references'].values():q['graded']=False
   heldrefs.append(r);shutil.move(str(out/'candidate/tasks'/tid),str(out/'held/inputs'/tid))
 tasks=[t for t in tasks if t['task_id'] not in reasons];refs=[r for r in refs if r['task_id'] not in reasons]
 manifest=jl(ev/'evidence-manifest.jsonl')
 pages=[('B-FEMCAD-062','https://reference.wolfram.com/language/PDEModels/tutorial/StructuralMechanics/SolidMechanicsVerificationTests.html','referenceMaxVonMisesStress = 14.9','solid-mechanics-verification.html'),
        ('B-FEMCAD-067','https://reference.wolfram.com/language/PDEModels/tutorial/HeatTransfer/HeatTransferVerificationTests.html','TRef = 332.97','heat-transfer-verification.html')]
 snapshots=[]
 for tid,url,marker,name in pages:
  raw=(publisher_pages/name).read_bytes();text=raw.decode()
  # HTML code cells may split expressions across tags; numeric publication is
  # checked against the live official text as well as this original snapshot.
  value=marker.split('= ')[1];assert value in text
  rel='evidence/publisher-pages/'+name;f=ev/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw)
  entry={'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'source_url':url,'collected_date':'2026-10-14','role':'original publisher HTML with explicit reference value'}
  manifest.append(entry);snapshots.append({'task_id':tid,**entry})
  for r in refs:
   if r['task_id']==tid:r['evidence_files'].append(rel)
 lines(ev/'evidence-manifest.jsonl',manifest);save(ev/'publisher-evidence-v1.7.json',snapshots)
 lines(out/'candidate/tasks.jsonl',tasks);lines(ev/'references.jsonl',refs);lines(out/'held/tasks.jsonl',held);lines(out/'held/references.jsonl',heldrefs)
 for folder in [ev/'task-pool',ev/'suites/primary']:
  tt=[t for t in jl(folder/'tasks.jsonl') if t['task_id'] not in reasons]
  rr=[r for r in jl(folder/'references.jsonl') if r['task_id'] not in reasons]
  for r in rr:
   if r['task_id'] in {x['task_id'] for x in snapshots}:r['evidence_files']=next(q['evidence_files'] for q in refs if q['task_id']==r['task_id'])
  lines(folder/'tasks.jsonl',tt);lines(folder/'references.jsonl',rr)
 v=json.loads((ev/'validation.json').read_text());v.update(version='1.7',tasks=len(tasks),graded_outputs=sum(len(r['references']) for r in refs),held_tasks=len(held),by_track=dict(collections.Counter(t['track'] for t in tasks)),by_family=dict(collections.Counter(t['family'] for t in tasks)),by_engineering_family=dict(collections.Counter(t['engineering_family'] for t in tasks)),geometry_gate_tasks=sum(bool(r.get('geometry_check')) for r in refs),reference_classes=dict(collections.Counter(q['ref_class'] for r in refs for q in r['references'].values())),source_evidence_files=len(manifest),source_evidence_bytes=sum(x['bytes'] for x in manifest))
 v['suite_counts']['primary']=len(tasks);v['suite_counts']['full_source_backed_pool']-=3;v['v17_holds']=reasons
 save(ev/'validation.json',v);sm=json.loads((ev/'suite-manifest.json').read_text());sm.update(version='1.7',**v['suite_counts']);save(ev/'suite-manifest.json',sm)
 save(ev/'task-hashes.json',{t['task_id']:hashlib.sha256(json.dumps(t,sort_keys=True,separators=(',',':')).encode()).hexdigest() for t in tasks})
 registry=jl(ev/'registry.jsonl');pool=jl(ev/'task-pool/tasks.jsonl')
 for row in registry:
  url=row['source']['url'];row['primary_tasks']=sum(t['source']['url']==url for t in tasks);row['full_pool_tasks']=sum(t['source']['url']==url for t in pool)
 lines(ev/'registry.jsonl',registry)
 policy=json.loads((ev/'evaluation-protocol.json').read_text());policy.update(release='1.7',primary_suite='54 tasks, cap 8 per family');save(ev/'evaluation-protocol.json',policy)
 status=json.loads((ev/'limitations-status.json').read_text());status.update(reproduction='14 of 54 primary tasks; qualified subset separately scored',source_only_correction='4 locally computed outputs held; unresolved bracket reference held',geometry_registration='proper principal-inertia frame candidates plus axis fallback, checked by exact solid overlap; general rigging rotations tested; arbitrary degenerate shapes not universally certified');save(ev/'limitations-status.json',status)
 cov=out/'evaluator/source-library/coverage.json';coverage=json.loads(cov.read_text());coverage.update(release='CADFEM-Bench v1.7 corrected source-only pilot',primary_tasks=54,graded_outputs=118,source_pool_tasks=125,held_tasks=58);save(cov,coverage)
 for rel in ['README.md','candidate/README.md','evaluator/DATASET_CARD.md']:
  f=out/rel;s=f.read_text().replace('57 primary','54 primary').replace('57 tasks','54 tasks').replace('123 graded','118 graded').replace('123 published','118 published').replace('128-case','125-case').replace('55 held','58 held').replace('six drawing','three drawing').replace('6 reconstruction','3 reconstruction').replace('43 primary','40 primary').replace('43 do not','40 do not').replace('43 still','40 still').replace('v1.6','v1.7').replace('67-page','64-page').replace('Six reconstruction','Three reconstruction')
  f.write_text(s+'\n\nCorrection v1.7: two locally calculated-reference tasks and one unresolved publisher-output task are held. Source HTML for the two remaining FEMCAD reference values is bundled. The rigging gate tests principal inertia frames under proper rotations and confirms exact overlap. Existing GPU runs remain historical v1.5 pilots; numerical pass, verified replay and verified workflow are reported separately.\n')
 fixes={'128 active':'125 active','| Primary | 57 |':'| Primary | 54 |','| Held | 55 |':'| Held | 58 |','(42.1%)':'(44.4%)','five existing FEMCAD':'two active FEMCAD','six reconstruction gates':'three reconstruction gates','6 drawing/specification':'3 drawing/specification'}
 for rel in ['README.md','candidate/README.md','evaluator/DATASET_CARD.md']:
  f=out/rel;s=f.read_text()
  for old,new in fixes.items():s=s.replace(old,new)
  s=s.replace('Build from the preserved v1.5 and contact follow-up:', 'Historical v1.6 build chain (superseded for this release):')
  if rel=='README.md':
   s=s[:s.index('## Integrity and rebuilding')]+'''## Integrity and rebuilding

SHA256SUMS.txt covers this corrected package. Build a fresh folder with release_v17.py --source <cadfem-bench-final> --out <fresh-folder> --publisher-pages <snapshot-folder>. Record a fresh sandbox/export probe, then run report_v17.py, verify_v17.py and finalize_v17.py. The original v1.6/final packages and v1.5 GPU runs are preserved. Historical collection reports and inventory records remain evaluator-only and do not override current hold decisions.
'''
  f.write_text(s)
 shutil.copy2(out/'evaluator/DATASET_CARD.md',out/'RELEASE_README.md')
 records=json.loads((ev/'source-library/collections.json').read_text());active_ids={t['task_id'] for t in pool};primary_ids={t['task_id'] for t in tasks}
 for record in records:
  record['source_pool_task_ids']=[i for i in record['source_pool_task_ids'] if i in active_ids]
  record['primary_task_ids']=[i for i in record['primary_task_ids'] if i in primary_ids]
 save(ev/'source-library/collections.json',records)
 old_check=ev/'source-library/consolidation-check.json'
 if old_check.exists():shutil.move(str(old_check),history/'v16-consolidation-check.json')
 for dst in [ev/'score.py',out/'scripts/cadfem_bench/score.py']:shutil.copy2(Path(__file__).with_name('score.py'),dst)
 for name in ['release_v17.py','verify_v17.py','report_v17.py','finalize_v17.py']:
  f=Path(__file__).with_name(name)
  if f.exists():shutil.copy2(f,out/'scripts/cadfem_bench'/name)
 run_script=Path(__file__).with_name('openweight')/'score_openweight.py'
 dst=out/'scripts/cadfem_bench/openweight';dst.mkdir(exist_ok=True);shutil.copy2(run_script,dst/run_script.name)
 save(ev/'correction-v1.7.json',{'held':reasons,'historical_releases_and_GPU_runs_modified':False,'new_CAD_generated':0,'new_numerical_targets_generated':0})
 return v
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--publisher-pages',type=Path,required=True);x=a.parse_args();print(json.dumps(build(x.source.resolve(),x.out.resolve(),x.publisher_pages.resolve()),indent=2))
