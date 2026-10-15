"""Use the existing local MLX QLoRA setup for a source-backed numerical warm-up."""
import argparse,gc,hashlib,importlib.metadata,json,math,subprocess,sys,time
from pathlib import Path

def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--data',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--model',type=Path,required=True);a.add_argument('--iters',type=int,default=256);x=a.parse_args()
 if x.output.exists():raise FileExistsError(x.output)
 x.output.mkdir(parents=True)
 import mlx.core as mx
 from mlx_lm import load,generate
 from mlx_lm.sample_utils import make_sampler
 source=json.loads((x.data/'manifest.json').read_text());rows={}
 for split in ['train','validation']:
  f=x.data/f'{split}.jsonl';assert sha(f)==source['files'][split];rows[split]=[json.loads(l) for l in f.read_text().splitlines()]
 assert not {r['geometry_group'] for r in rows['train']}&{r['geometry_group'] for r in rows['validation']}
 def messages(r):return [{'role':'system','content':source['system']},{'role':'user','content':r['input']}]
 manifest={'status':'started','objective':source['objective'],'model_repo':'mlx-community/Qwen2.5-Coder-1.5B-Instruct-4bit','model_path':str(x.model.resolve()),'model_revision':x.model.name,'source_manifest':source,'seed':17,'iterations':x.iters,'batch_size':1,'learning_rate':1e-4,'lora_layers':8,'max_sequence_length':1024,'runtime':'existing local MLX environment; remote GPUs unchanged','packages':{k:importlib.metadata.version(k) for k in ['mlx','mlx-lm','transformers']},'script_sha256':sha(Path(__file__)),'evaluation':'all16 original validation geometries; within-family numerical prediction, not benchmark workflow completion','model_selection':'fixed final iteration; no validation-based checkpoint or hyperparameter selection'}
 save(x.output/'run_manifest.json',manifest)
 def evaluate(label,m,tok):
  results=[]
  for i,r in enumerate(rows['validation']):
   prompt=tok.apply_chat_template(messages(r),tokenize=False,add_generation_prompt=True);t=time.monotonic();pred=generate(m,tok,prompt=prompt,max_tokens=128,sampler=make_sampler(temp=0),verbose=False);target=json.loads(r['target'])['outputs'];errors={};valid=False
   try:
    obj=json.loads(pred.strip());assert isinstance(obj,dict) and set(obj)=={'outputs'} and isinstance(obj['outputs'],dict) and set(obj['outputs'])==set(target)
    for k,truth in target.items():
     value=obj['outputs'][k];assert type(value) in [int,float] and math.isfinite(value);errors[k]=abs(value-truth)/max(abs(truth),1e-12)
    valid=True
   except (ValueError,AssertionError,TypeError,KeyError):pass
   results.append({'id':r['id'],'prediction':pred,'target':target,'JSON_valid':valid,'relative_errors':errors if valid else {},'seconds':time.monotonic()-t})
   print(label,i+1,'/',len(rows['validation']),flush=True)
  (x.output/f'{label}-predictions.jsonl').write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in results))
  valid=[r for r in results if r['JSON_valid']];metrics={'cases':len(results),'JSON_valid':len(valid),'all_outputs_within_10_percent':sum(r['JSON_valid'] and all(v<=0.1 for v in r['relative_errors'].values()) for r in results),'mean_relative_error_valid_predictions_only':{k:sum(r['relative_errors'][k] for r in valid)/len(valid) if valid else None for k in target},'metric_scope':'validation numerical surrogate accuracy; no CAD/FEM execution or workflow pass'}
  save(x.output/f'{label}-metrics.json',metrics);print(label,metrics,flush=True);return metrics
 try:
  m,tok=load(str(x.model));lengths=[]
  for split in rows:
   for r in rows[split]:
    n=len(tok.apply_chat_template(messages(r)+[{'role':'assistant','content':r['target']}],tokenize=True));assert n<=1024,(r['id'],n);lengths.append(n)
  manifest['maximum_actual_sequence_tokens']=max(lengths);manifest['base_validation']=evaluate('base',m,tok);del m,tok;gc.collect();mx.clear_cache()
  cmd=[sys.executable,'-m','mlx_lm','lora','--model',str(x.model),'--train','--mask-prompt','--data',str(x.data/'mlx'),'--adapter-path',str(x.output/'adapter'),'--iters',str(x.iters),'--batch-size','1','--num-layers','8','--learning-rate','0.0001','--max-seq-length','1024','--grad-checkpoint','--steps-per-report','16','--steps-per-eval','128','--val-batches','16','--save-every','128','--seed','17']
  manifest['command']=cmd;manifest['status']='training';save(x.output/'run_manifest.json',manifest);start=time.monotonic();subprocess.run(cmd,check=True)
  m,tok=load(str(x.model),adapter_path=str(x.output/'adapter'));manifest['trained_validation']=evaluate('trained',m,tok)
  manifest.update(status='completed',training_and_final_eval_seconds=time.monotonic()-start,adapter_sha256=sha(x.output/'adapter/adapters.safetensors'));save(x.output/'run_manifest.json',manifest)
 except BaseException as e:
  manifest.update(status='failed',error=f'{type(e).__name__}: {e}');save(x.output/'run_manifest.json',manifest);raise
if __name__=='__main__':main()
