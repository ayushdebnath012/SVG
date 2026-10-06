"""Colab 3B QLoRA student for verifier-guided distillation: PLAN+PATCH targets, same recipe as the 3B run.

Identical to train_multisource_cad_colab.py (seed 17, NF4 base, rank 16, alpha 320, last 12 blocks, lr 1e-4,
effective batch 4, two epochs, final checkpoint, greedy test decoding) except: targets are PLAN+PATCH text
from build_distill_dataset.py, the target/generation cap is 1,024 tokens so the longer plans keep the same
training rows, the patch is read after "PATCH:", and the base model is not re-evaluated (its results are in
runs/multisource-cad-colab-20261002). Exact-patch metrics use the reference patch in target_patch.
"""
import argparse,hashlib,json,time
from pathlib import Path
from cad_edit_contracts import apply,target_match
from cad_edit_verifier import extract

CAP=1024
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--model',default='Qwen/Qwen2.5-Coder-3B-Instruct');p.add_argument('--revision',default='488639f1ff808d1d3d0ba301aef8c11461451ec5');p.add_argument('--epochs',type=int,default=2);a=p.parse_args()
 import torch,transformers,peft
 from transformers import AutoTokenizer,AutoModelForCausalLM,Trainer,TrainingArguments,set_seed,BitsAndBytesConfig
 from peft import LoraConfig,get_peft_model,PeftModel,prepare_model_for_kbit_training
 assert torch.cuda.is_available();free,_=torch.cuda.mem_get_info();assert free>8*2**30
 bf16=torch.cuda.is_bf16_supported();dtype=torch.bfloat16 if bf16 else torch.float16;batch=4 if free>25*2**30 else 1;accum=4//batch
 quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=dtype)
 if a.output.exists():raise ValueError('Fresh output directory required')
 a.output.mkdir(parents=True);set_seed(17);torch.set_num_threads(8)
 source=json.loads((a.data/'manifest.json').read_text());tokenizer=AutoTokenizer.from_pretrained(a.model,revision=a.revision);tokenizer.pad_token=tokenizer.eos_token
 model=AutoModelForCausalLM.from_pretrained(a.model,revision=a.revision,torch_dtype=dtype,quantization_config=quant,device_map={'':0},attn_implementation='sdpa')
 rows={};encoded={};omissions=[]
 def messages(r,answer=True):
  ms=[dict(role='system',content=source['system']),dict(role='user',content=r['input'])]+r.get('history',[])  # optional repair turns: earlier answer + checker feedback; loss stays on the final answer only
  if answer:ms.append(dict(role='assistant',content=r['target']))
  return ms
 for split in ['train','validation','test']:
  f=a.data/f'{split}.jsonl';assert hashlib.sha256(f.read_bytes()).hexdigest()==source['files'][split];rows[split]=[];encoded[split]=[]
  for r in map(json.loads,f.read_text().splitlines()):
   prefix=tokenizer.apply_chat_template(messages(r,False),tokenize=True,add_generation_prompt=True);full=tokenizer.apply_chat_template(messages(r),tokenize=True,add_generation_prompt=False)
   assert full[:len(prefix)]==prefix
   if len(full)>4096 or len(full)-len(prefix)>CAP:omissions.append(dict(id=r['id'],split=split,source=r['source'],full_tokens=len(full),target_tokens=len(full)-len(prefix)));continue
   rows[split].append(r);encoded[split].append(dict(input_ids=full,labels=[-100]*len(prefix)+full[len(prefix):]))
 dump(a.output/'omissions.json',omissions)
 manifest=dict(status='started',model=a.model,model_revision=a.revision,variant=source['variant'],source_manifest=source,counts={s:len(rs) for s,rs in rows.items()},origin_counts={s:{o:sum(r['target_origin']==o for r in rs) for o in ['template','teacher_verified']} for s,rs in rows.items()},epochs=a.epochs,gpu=torch.cuda.get_device_name(0),config=dict(seed=17,dtype=str(dtype),quantization='NF4 double-quantized',rank=16,lora_alpha=320,dropout=0,batch_size=batch,gradient_accumulation=accum,effective_batch_size=4,learning_rate=1e-4,blocks=12,max_sequence_tokens=4096,max_target_and_generation_tokens=CAP),packages=dict(torch=torch.__version__,transformers=transformers.__version__,peft=peft.__version__),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),runtime='Google Colab GPU')
 dump(a.output/'run_manifest.json',manifest)
 def evaluate(label,m):
  m.eval();m.config.use_cache=True;tokenizer.padding_side='left';result=[]
  for start in range(0,len(rows['test']),4):
   rs=rows['test'][start:start+4];prompts=[tokenizer.apply_chat_template(messages(r,False),tokenize=False,add_generation_prompt=True) for r in rs];inputs=tokenizer(prompts,add_special_tokens=False,padding=True,return_tensors='pt').to('cuda')
   with torch.inference_mode():generated=m.generate(**inputs,max_new_tokens=CAP,do_sample=False,pad_token_id=tokenizer.pad_token_id)[:,inputs.input_ids.shape[1]:]
   texts=tokenizer.batch_decode(generated,skip_special_tokens=True)
   for r,text,tokens in zip(rs,texts,generated):
    error=None;patch=None;match=False;code=None
    try:_,patch=extract(text);code=apply(r['code'],patch,r['representation']);match=target_match(code,r['edited_code'],r['representation'])
    except Exception as e:error=type(e).__name__+': '+str(e)[:250]
    result.append(dict(id=r['id'],source=r['source'],representation=r['representation'],component_id=r['component_id'],category=r['category'],prediction=text,applicable=error is None,exact_patch=patch==json.loads(r['target_patch']),target_match=match,error=error,predicted_code=code,reference_code=r['edited_code'],reference_step=r.get('reference_step'),reference_step_sha256=r.get('reference_step_sha256'),generation_cap_hit=not bool((tokens==tokenizer.eos_token_id).any().item())))
   print(label,len(result),'/',len(rows['test']),flush=True)
  (a.output/f'{label}-predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in result))
  def metrics(rs):return dict(n=len(rs),applicable=sum(r['applicable'] for r in rs),exact_patch=sum(r['exact_patch'] for r in rs),target_match=sum(r['target_match'] for r in rs),generation_cap_hits=sum(r['generation_cap_hit'] for r in rs))
  ms=metrics(result);ms['sources']={s:metrics([r for r in result if r['source']==s]) for s in ['BenchCAD','CAD-Editor']};dump(a.output/f'{label}-metrics.json',ms);print(label,ms,flush=True)
 blocks='|'.join(map(str,range(model.config.num_hidden_layers-12,model.config.num_hidden_layers)));target=rf'model\.layers\.({blocks})\.(self_attn|mlp)\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)'
 model=prepare_model_for_kbit_training(model,use_gradient_checkpointing=True);model=get_peft_model(model,LoraConfig(r=16,lora_alpha=320,lora_dropout=0,target_modules=target,task_type='CAUSAL_LM'));model.enable_input_require_grads();model.config.use_cache=False;tokenizer.padding_side='right';manifest['trainable_parameters'],manifest['total_parameters']=model.get_nb_trainable_parameters();dump(a.output/'run_manifest.json',manifest)
 def collate(batch):
  length=max(len(r['input_ids']) for r in batch)
  return dict(input_ids=torch.tensor([r['input_ids']+[tokenizer.pad_token_id]*(length-len(r['input_ids'])) for r in batch]),labels=torch.tensor([r['labels']+[-100]*(length-len(r['labels'])) for r in batch]),attention_mask=torch.tensor([[1]*len(r['input_ids'])+[0]*(length-len(r['input_ids'])) for r in batch]))
 args=TrainingArguments(output_dir=str(a.output/'checkpoints'),num_train_epochs=a.epochs,per_device_train_batch_size=batch,per_device_eval_batch_size=batch,gradient_accumulation_steps=accum,learning_rate=1e-4,lr_scheduler_type='constant',weight_decay=0,warmup_ratio=0,bf16=bf16,fp16=not bf16,gradient_checkpointing=True,gradient_checkpointing_kwargs={'use_reentrant':False},logging_steps=25,eval_strategy='epoch',save_strategy='epoch',save_total_limit=1,report_to='none',seed=17,data_seed=17,remove_unused_columns=False,label_names=['labels'],optim='paged_adamw_8bit')
 trainer=Trainer(model=model,args=args,train_dataset=encoded['train'],eval_dataset=encoded['validation'],data_collator=collate);start=time.monotonic();res=trainer.train();dump(a.output/'training-metrics.json',res.metrics);dump(a.output/'training-history.json',trainer.state.log_history);trainer.save_model(str(a.output/'adapter'));tokenizer.save_pretrained(a.output/'adapter');steps=trainer.state.global_step;del trainer,model;torch.cuda.empty_cache()
 base=AutoModelForCausalLM.from_pretrained(a.model,revision=a.revision,torch_dtype=dtype,quantization_config=quant,device_map={'':0},attn_implementation='sdpa');reloaded=PeftModel.from_pretrained(base,str(a.output/'adapter'));evaluate('trained',reloaded)
 manifest.update(status='completed',optimizer_steps=steps,training_and_final_eval_seconds=time.monotonic()-start,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),adapter_sha256=hashlib.sha256((a.output/'adapter/adapter_model.safetensors').read_bytes()).hexdigest());dump(a.output/'run_manifest.json',manifest)
if __name__=='__main__':main()
