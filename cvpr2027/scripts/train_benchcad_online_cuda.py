"""Fresh-base bf16 LoRA benchmark run on an explicitly selected CUDA device.

Uses the exact context-retained MLX chat rows, not another silently filtered split.
"""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from benchcad_online_edit_dataset import apply


def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')


def main():
    sys.setrecursionlimit(10000)
    p=argparse.ArgumentParser()
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--epochs',type=int,default=3)
    p.add_argument('--model',default='Qwen/Qwen2.5-Coder-1.5B-Instruct')
    a=p.parse_args()
    if a.output.exists():raise ValueError('Use a fresh output directory')
    import torch,transformers,peft
    from transformers import AutoTokenizer,AutoModelForCausalLM,Trainer,TrainingArguments,set_seed
    from peft import LoraConfig,get_peft_model,PeftModel
    assert torch.cuda.is_available()
    # Leave existing server jobs alone; refuse rather than overcommit memory.
    free,total=torch.cuda.mem_get_info()
    if free<8*1024**3:raise RuntimeError('Selected GPU has less than 8 GiB free; no training launched')
    torch.set_num_threads(4);set_seed(17)
    a.output.mkdir(parents=True)
    source=json.loads((a.data/'run_manifest.json').read_text())
    test=json.loads((a.data/'test-records.json').read_text())
    tokenizer=AutoTokenizer.from_pretrained(a.model)
    tokenizer.pad_token=tokenizer.eos_token
    model=AutoModelForCausalLM.from_pretrained(a.model,torch_dtype=torch.bfloat16,device_map={'':0},attn_implementation='sdpa')
    revision=model.config._commit_hash
    train_data={};encoded={}
    for split,name in [('train','train'),('validation','valid')]:
        train_data[split]=[json.loads(x) for x in (a.data/'data'/f'{name}.jsonl').read_text().splitlines()]
        encoded[split]=[]
        for row in train_data[split]:
            prefix=tokenizer.apply_chat_template(row['messages'][:-1],tokenize=True,add_generation_prompt=True)
            full=tokenizer.apply_chat_template(row['messages'],tokenize=True,add_generation_prompt=False)
            if full[:len(prefix)]!=prefix:raise ValueError('Chat-template prefix mismatch')
            if len(full)>3072:raise ValueError('Previously retained example exceeds context; do not silently truncate')
            encoded[split].append(dict(input_ids=full,labels=[-100]*len(prefix)+full[len(prefix):]))
        assert len(encoded[split])==source['counts'][split]
    manifest=dict(status='started',model=a.model,model_revision=revision,epochs=a.epochs,seed=17,
                  counts=source['counts'],source_run_sha256=hashlib.sha256((a.data/'run_manifest.json').read_bytes()).hexdigest(),
                  data_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (a.data/'data').glob('*.jsonl')},
                  gpu=torch.cuda.get_device_name(0),free_bytes_at_start=free,
                  packages=dict(torch=torch.__version__,transformers=transformers.__version__,peft=peft.__version__),
                  config=dict(dtype='bfloat16',quantization=None,rank=8,lora_alpha=160,dropout=0.0,blocks=8,
                              batch_size=1,learning_rate=1e-4,max_sequence_tokens=3072,max_generation_tokens=512),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  evaluation='Same 126 context-retained family/template-disjoint cases. Fresh base; final checkpoint only. No test-based selection.')
    dump(a.output/'run_manifest.json',manifest)
    def evaluate(label,m):
        m.eval();m.config.use_cache=True;tokenizer.padding_side='left';results=[]
        for start in range(0,len(test),8):
            batch=test[start:start+8]
            prompts=[tokenizer.apply_chat_template([dict(role='system',content=source['source_manifest']['system']),dict(role='user',content=r['input'])],tokenize=False,add_generation_prompt=True) for r in batch]
            inputs=tokenizer(prompts,add_special_tokens=False,padding=True,return_tensors='pt').to('cuda')
            with torch.inference_mode():tokens=m.generate(**inputs,max_new_tokens=512,do_sample=False,pad_token_id=tokenizer.pad_token_id)
            generated=tokens[:,inputs.input_ids.shape[1]:]
            predictions=tokenizer.batch_decode(generated,skip_special_tokens=True)
            for r,pred,tok in zip(batch,predictions,generated):
                patch=None;error=None;ast_match=False
                try:
                    text=pred.strip()
                    if text.startswith('```'):text='\n'.join(text.splitlines()[1:-1])
                    patch=json.loads(text);code=apply(r['code'],patch)
                    ast_match=ast.dump(ast.parse(code))==ast.dump(ast.parse(r['edited_code']))
                except Exception as e:error=str(e)[:250];code=None
                results.append(dict(id=r['id'],source_record_id=r['source_record_id'],family=r['family'],category=r['category'],
                                    prediction=pred,exact=patch==json.loads(r['target']),applicable=error is None,ast_match=ast_match,
                                    error=error,predicted_code=code,reference_code=r['edited_code'],
                                    reference_step=r['reference_step'],reference_step_sha256=r['reference_step_sha256'],
                                    generation_cap_hit=not bool((tok==tokenizer.eos_token_id).any().item())))
            print(label,len(results),'/',len(test),flush=True)
        (a.output/f'{label}-predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in results))
        metrics=dict(n=len(results),exact=sum(r['exact'] for r in results),applicable=sum(r['applicable'] for r in results),
                     ast_match=sum(r['ast_match'] for r in results),generation_cap_hits=sum(r['generation_cap_hit'] for r in results),
                     categories={c:dict(n=sum(r['category']==c for r in results),exact=sum(r['exact'] and r['category']==c for r in results),ast_match=sum(r['ast_match'] and r['category']==c for r in results)) for c in sorted({r['category'] for r in results})})
        dump(a.output/f'{label}-metrics.json',metrics);print(label,metrics,flush=True)
    evaluate('base',model)
    blocks=list(range(model.config.num_hidden_layers-8,model.config.num_hidden_layers))
    block_pattern='|'.join(map(str,blocks))
    target=rf'model\.layers\.({block_pattern})\.(self_attn|mlp)\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)'
    model=get_peft_model(model,LoraConfig(r=8,lora_alpha=160,lora_dropout=0.0,target_modules=target,task_type='CAUSAL_LM'))
    model.enable_input_require_grads();model.config.use_cache=False;tokenizer.padding_side='right'
    trainable,total_params=model.get_nb_trainable_parameters();manifest['trainable_parameters']=trainable;manifest['total_parameters']=total_params
    dump(a.output/'run_manifest.json',manifest)
    def collate(batch):
        size=max(len(r['input_ids']) for r in batch)
        return dict(input_ids=torch.tensor([r['input_ids']+[tokenizer.pad_token_id]*(size-len(r['input_ids'])) for r in batch]),
                    labels=torch.tensor([r['labels']+[-100]*(size-len(r['labels'])) for r in batch]),
                    attention_mask=torch.tensor([[1]*len(r['input_ids'])+[0]*(size-len(r['input_ids'])) for r in batch]))
    args=TrainingArguments(output_dir=str(a.output/'checkpoints'),num_train_epochs=a.epochs,per_device_train_batch_size=1,
                           gradient_accumulation_steps=1,per_device_eval_batch_size=1,learning_rate=1e-4,
                           lr_scheduler_type='constant',warmup_ratio=0.0,weight_decay=0.0,bf16=True,
                           gradient_checkpointing=True,gradient_checkpointing_kwargs={'use_reentrant':False},
                           logging_steps=50,eval_strategy='epoch',save_strategy='epoch',save_total_limit=1,
                           report_to='none',seed=17,data_seed=17,remove_unused_columns=False,label_names=['labels'],
                           optim='adamw_torch',dataloader_num_workers=0)
    trainer=Trainer(model=model,args=args,train_dataset=encoded['train'],eval_dataset=encoded['validation'],data_collator=collate)
    start=time.monotonic();result=trainer.train();dump(a.output/'training-metrics.json',result.metrics)
    trainer.save_model(str(a.output/'adapter'));tokenizer.save_pretrained(a.output/'adapter');dump(a.output/'training-history.json',trainer.state.log_history)
    trainer.save_state();del trainer,model;torch.cuda.empty_cache()
    base=AutoModelForCausalLM.from_pretrained(a.model,revision=revision,torch_dtype=torch.bfloat16,device_map={'':0},attn_implementation='sdpa')
    reloaded=PeftModel.from_pretrained(base,str(a.output/'adapter'))
    evaluate('trained',reloaded)
    adapter=a.output/'adapter/adapter_model.safetensors'
    manifest.update(status='completed',optimizer_steps=len(encoded['train'])*a.epochs,training_and_final_eval_seconds=time.monotonic()-start,
                    peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),adapter_sha256=hashlib.sha256(adapter.read_bytes()).hexdigest())
    dump(a.output/'run_manifest.json',manifest)


if __name__=='__main__':main()
