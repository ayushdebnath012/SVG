"""Package existing source cases and observed trial evidence; no reference generation."""
from pathlib import Path
import json,shutil,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];PKG=ROOT.parent/'cadfem-bench-v1.7';BASE=ROOT/'output/datasets/cadfem-challenge-trials';OUT=ROOT/'output/datasets/cadfem-astra-failure-cases-v0.1';OUT.mkdir(parents=True,exist_ok=True)
listing=json.loads((BASE/'failure-list.json').read_text());cases=[x for x in listing['cases'] if x['count_as_distinct_failure']];ids={x['task_id'] for x in cases}
tasks=[t for t in map(json.loads,(PKG/'candidate/tasks.jsonl').read_text().splitlines()) if t['task_id'] in ids];refs=[t for t in map(json.loads,(PKG/'evaluator/references.jsonl').read_text().splitlines()) if t['task_id'] in ids]
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
for t in tasks:
 for inp in t['inputs']:copy(PKG/'candidate'/inp['path'],OUT/'candidate'/inp['path'])
for r in refs:
 for rel in r.get('evidence_files',[]):copy(PKG/'evaluator'/rel,OUT/'evaluator'/rel)
(OUT/'candidate/tasks.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in tasks));(OUT/'evaluator/references.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in refs))
for c in cases:
 tid=c['task_id'];run=ROOT/'runs/astra-failure-hunt-20261015'/tid
 if tid=='A-FCVM-Plate_girder_EC3':run=ROOT/'runs/astra-girder-repair-20261015'
 c['full_trial_directory']=str(run)
 for rel in ['README.md','outcome.json','failure-analysis.json','request.json','response.json','generation.json','protocol.json','submission/main.py','replay/execution.json','replay/protocol.json','replay/sandbox.log','scoring/score.json']:
  if (run/rel).is_file():copy(run/rel,OUT/'evaluator/trials'/tid/rel)
 for file in (run/'replay/outputs').rglob('*'):
  if file.is_file() and (file.suffix in ['.log','.stdout','.json']):copy(file,OUT/'evaluator/trials'/tid/'outputs'/file.relative_to(run/'replay/outputs'))
(OUT/'failure-list.json').write_text(json.dumps(listing,indent=2)+'\n');copy(BASE/'FAILURE_LIST.md',OUT/'FAILURE_LIST.md');copy(BASE/'astra-20261015.json',OUT/'all-trials-and-spend.json')
manifest={'name':'CADFEM Astra failure cases v0.1','base_release':'v1.7','distinct_failed_cases':len(cases),'families':sorted({t['engineering_family'] for t in tasks}),'source':'Existing web-sourced v1.7 cases; newly observed trials, not newly discovered engineering problems','protocol_limit':'Low-reasoning single-shot code generation, no model tools or repair; plate girder additionally has one parser-only repair. Not comparable to full agent evaluation.','pending_not_counted':['A-MORPHWING-Test7'],'redistribution':'Local research only; mixed source restrictions. Do not publish bundle.','complete_trial_mesh_and_field_outputs':'Preserved in full_trial_directory paths; compact subset includes original source evidence and trial logs/code/hash inventories.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(OUT/'README.md').write_text('# CADFEM Astra failure cases v0.1\n\n'+str(len(cases))+' distinct task failures observed under restricted protocols. This is a diagnostic subset of existing web-sourced CADFEM-Bench v1.7, not a fresh independent benchmark and not an estimate of overall Astra accuracy.\n\nCandidate inputs and prompts are in candidate/. Published numerical references, original source evidence and model trial evidence are evaluator-only. Do not expose evaluator/ or all-trials-and-spend.json to tested models. Mixed source licences restrict this bundle to local research.\n\nMost failures are script/mesh workflow failures; see FAILURE_LIST.md for exact causes. Repeated failure mechanisms across geometries are explicitly identified. The wing mismatch remains pending, token exhaustion is inconclusive, and successful trials remain in the ledger. Missing manual review does not count as a model failure.\n\nNo new CAD or numerical reference was invented for this subset. Source specification-derived geometry validators are inherited from v1.7 and labelled in reference metadata. Full model meshes and fields remain in original local run folders; execution.json contains their hashes.\n')
files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS'];(OUT/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(OUT))+'\n' for p in sorted(files)))
zpath=OUT.with_name(OUT.name+'.zip')
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,OUT.name+'/'+str(p.relative_to(OUT)))
with zipfile.ZipFile(zpath) as z:assert z.testzip() is None
print(json.dumps({'cases':len(cases),'files':len(files)+1,'zip_bytes':zpath.stat().st_size,'out':str(OUT)}))
