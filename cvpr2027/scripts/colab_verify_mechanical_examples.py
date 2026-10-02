"""Audit the NEW Colab adapter's six held-out illustrated predictions with real FEM."""
import argparse,json,subprocess,sys
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--run',type=Path,required=True);a=p.parse_args()
 rows={r['id']:r for r in map(json.loads,(a.run/'test-retained.jsonl').read_text().splitlines())};pred={r['id']:r for r in map(json.loads,(a.run/'trained-predictions.jsonl').read_text().splitlines())};cs=json.loads((a.root/'example-contracts.json').read_text());out=a.run/'fem-examples';out.mkdir(exist_ok=True);results=[]
 for c in cs:
  dest=out/c['source_record_id'];dest.mkdir(exist_ok=True);record=dict(id=c['id'],source_record_id=c['source_record_id'],model='new_completed_Colab_adapter')
  if c['id'] not in pred:record['status']='not_verified_token_omission'
  elif not pred[c['id']]['applicable']:record['status']='not_verified_invalid_patch';record['error']=pred[c['id']]['error']
  else:
   r=rows[c['id']];text=pred[c['id']]['prediction'].strip()
   if text.startswith('```'):text='\n'.join(text.splitlines()[1:-1])
   (dest/'source.py').write_text(r['code']);(dest/'patch.json').write_text(text)
   contract=dict(scenario=c['scope'],units=c['units'],material=c['material'],total_force_N=c['total_force_N'],axis=c['prediction_axis'],band_fraction=c['band_fraction'],mesh_sizes_mm=c['mesh_sizes_mm'],compliance_mesh_tolerance=.05,mesh_volume_tolerance=.03,geometry_iou_threshold=.99999,response_agreement_tolerance=.1)
   (dest/'contract.json').write_text(json.dumps(contract,indent=2))
   cmd=[sys.executable,str(a.root/'scripts/run_verified_cad_edit.py'),'--source',str(dest/'source.py'),'--patch',str(dest/'patch.json'),'--representation','cadquery','--contract',str(dest/'contract.json'),'--target-step',str(a.root/'references'/f"{c['id']}.step"),'--output',str(dest/'verification')]
   with (dest/'pipeline.log').open('w') as log:process=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
   if (dest/'verification/verification.json').exists():record.update(json.loads((dest/'verification/verification.json').read_text()))
   else:record['status']='not_verified_pipeline_failure'
  results.append(record);(out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print('FEM',len(results),'/',len(cs),record['source_record_id'],record['status'],flush=True)
if __name__=='__main__':main()
