"""Prepare original publisher training cases, with source and benchmark separation checks."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
import numpy as np

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def key(summary):return json.dumps({k:v for k,v in summary['design'].items() if k!='name'},sort_keys=True)
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
SYSTEM='Predict the original publisher discretized linear-elastic FEM displacement metrics for the supplied bracket parameters and physical load. Return only JSON with an outputs object containing seat_mean_displacement_mm and max_displacement_mm. This is numerical surrogate prediction; do not claim that you executed CAD or FEM.'

def build(source,benchmark,out):
 if out.exists():raise FileExistsError(out)
 cat=json.loads((source/'catalog.json').read_text());protocol=json.loads((source/'protocol.json').read_text());published=json.loads((source/'SHA256SUMS.json').read_text())
 archives=[f for f in sorted(source.glob('*.zip')) if f.name.startswith(('fields-train','fields-validation','geometry-train','geometry-validation'))]
 source_entries={}
 for f in archives:
  assert sha(f)==published[f.name],f
  with zipfile.ZipFile(f) as z:
   for n in z.namelist():
    if not n.endswith('/'):source_entries[n]=hashlib.sha256(z.read(n)).hexdigest()
 test_keys=set();test_ids=[]
 for row in cat['records']:
  if row['split']=='test':test_keys.add(key(json.loads((source/row['source_summary']).read_text())));test_ids.append(row['id'])
 benchmark_ids=set();benchmark_cad_hashes=set()
 for suite in ['primary','calibration','reserved-public','related-public']:
  for r in map(json.loads,(benchmark/f'evaluator/suites/{suite}/references.jsonl').read_text().splitlines()):
   for f in r['evidence_files']:
    if '/web-agentfem-brackets/cases/' in f:benchmark_ids.add(f.split('/cases/')[1].split('/')[0])
  for t in map(json.loads,(benchmark/f'evaluator/suites/{suite}/tasks.jsonl').read_text().splitlines()):
   benchmark_cad_hashes.update(i['sha256'] for i in t['inputs'] if i['role']=='cad')
 out.mkdir(parents=True);records={'train':[],'validation':[]};assets=[];keys={'train':set(),'validation':set()}
 by_id={r['id']:r for r in cat['records']}
 order={'train':protocol['train_order'],'validation':[r['id'] for r in cat['records'] if r['split']=='validation']}
 for split in records:
  for cid in order[split]:
   r=by_id[cid];assert r['split']==split and cid not in benchmark_ids and cid not in test_ids
   summary=json.loads((source/r['source_summary']).read_text());geometry_key=key(summary);assert geometry_key not in test_keys
   keys[split].add(geometry_key);folder=out/'cases'/cid;folder.mkdir(parents=True)
   for name in ['geometry.step','geometry.msh','fields.npz','summary.json']:
    src=source/'cases'/cid/name;h=sha(src);assert source_entries[f'fem/{cid}/{name}']==h
    if name=='geometry.step':assert h not in benchmark_cad_hashes
    shutil.copy2(src,folder/name);assets.append({'path':str((folder/name).relative_to(out)),'sha256':h,'bytes':src.stat().st_size})
   with np.load(folder/'fields.npz',allow_pickle=False) as f:
    xyz=f['points'];u=f['displacement'];assert xyz.shape==u.shape and xyz.shape[1]==3 and np.isfinite(xyz).all() and np.isfinite(u).all()
    assert np.isclose(np.linalg.norm(u,axis=1).max()*1000,summary['max_displacement_mm'],rtol=1e-9)
    seat=np.isclose(xyz[:,2],0.189,atol=1e-8);assert seat.any()
    assert np.isclose((-u[seat,2]).mean()*1000,summary['seat_mean_displacement_mm'],rtol=1e-8)
   params={k:v for k,v in summary['design'].items() if k!='name'}
   inputs={'bracket_family':'publisher symmetric double-arm support, 189 mm high','source_geometry_parameters':params,'parameter_length_unit':'m; waist is dimensionless','material':r['material'],'physical_load_N':summary['load_N'],'boundary_conditions':r['boundary_conditions'],'cad':'Original STEP numeric coordinates follow metres despite its millimetre header; file kept unchanged. Use field coordinates/parameters in metres.'}
   target=json.dumps({'outputs':{k:summary[k] for k in ['seat_mean_displacement_mm','max_displacement_mm']}},allow_nan=False)
   records[split].append({'id':cid,'family':'agentfem-bracket','source':cat['source'],'geometry_group':geometry_key,'input':json.dumps(inputs,sort_keys=True),'target':target,'cad_path':f'cases/{cid}/geometry.step','mesh_path':f'cases/{cid}/geometry.msh','fields_path':f'cases/{cid}/fields.npz','original_summary_path':f'cases/{cid}/summary.json','original_split':split})
 assert not keys['train']&keys['validation'];assert len(records['train'])==128 and len(records['validation'])==16
 hashes={}
 for split,rs in records.items():
  f=out/f'{split}.jsonl';f.write_text(''.join(json.dumps(r)+'\n' for r in rs));hashes[split]=sha(f)
  name='valid' if split=='validation' else split;d=out/'mlx';d.mkdir(exist_ok=True)
  (d/f'{name}.jsonl').write_text(''.join(json.dumps({'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':r['input']},{'role':'assistant','content':r['target']}]})+'\n' for r in rs))
 provenance=out/'source';provenance.mkdir()
 for name in ['LICENSE','README.md','protocol.json','environment.json','SHA256SUMS.json','train.csv','validation.csv']:
  shutil.copy2(source/name,provenance/name)
 manifest={'source':cat['source'],'revision':cat['revision'],'license':cat['license'],'attribution':'Haoming Luo, AgentFEM-Bracket-Elasticity (2026), CC BY 4.0','system':SYSTEM,'objective':'source-summary numerical surrogate warm-up; not CAD/FEM workflow SFT','counts':{k:len(v) for k,v in records.items()},'files':hashes,'asset_files':len(assets),'benchmark':str(benchmark),'benchmark_version':'1.7','benchmark_cases_excluded':len(benchmark_ids),'publisher_test_cases_excluded':len(test_ids),'exact_geometry_parameter_overlap_train_validation':0,'exact_geometry_parameter_overlap_with_publisher_test':0,'raw_asset_hashes_match_original_source_archives':True,'FEM_scalar_checks_against_original_fields':288,'new_CAD_generated':0,'new_FEM_results_generated':0,'new_target_values_generated':0,'limitations':['One bracket family; validation is within-family geometry generalization, not cross-family generalization.','Publisher mesh is not qualified as converged. Targets describe the published discretized solution.','This LLM input uses source geometry parameters, not direct STEP tokens or an image encoder.','No agent trajectory or independently verified CAD/FEM workflow label is trained.','Public-source exposure cannot be ruled out.']}
 save(out/'manifest.json',manifest);save(out/'asset-manifest.json',assets)
 (out/'README.md').write_text('# CADFEM training v1\n\n128 original publisher training cases and 16 original validation cases from AgentFEM (CC BY 4.0). The 32 publisher test cases and benchmark cases are excluded. Original STEP, mesh, fields and summaries are preserved; archive hashes and displacement metrics are checked.\n\nThe MLX chat data trains numerical surrogate prediction from source geometry parameters, material and physical load. It does not train a complete CAD/FEM agent. All target scalars come directly from original summaries at their recorded 1,000 or 10,000 N load; no load-normalized label is substituted.\n\nOriginal STEP headers have a scale inconsistency, documented in each input. Files remain unchanged; parameters and nodal coordinates use metres. Targets are the source discretized results, not independently converged engineering truth. Validation is within the same parametric family. Keep CADFEM-Bench v1.7 for evaluation.\n\nAttribution: Haoming Luo, AgentFEM-Bracket-Elasticity (2026), https://huggingface.co/datasets/HaomingLuo/AgentFEM-Bracket-Elasticity. Original license/notices are in source/.\n')
 return manifest
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--benchmark',type=Path,required=True);a.add_argument('--out',type=Path,required=True);x=a.parse_args();print(json.dumps(build(x.source.resolve(),x.benchmark.resolve(),x.out.resolve()),indent=2))
