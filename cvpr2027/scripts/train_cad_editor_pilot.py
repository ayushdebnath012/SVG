"""Bounded CAD-Editor sequence-edit LoRA pilot; no geometry-success claims."""
import argparse
from contextlib import nullcontext
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def dump(p,x): p.write_text(json.dumps(x,indent=2)+'\n')
def rows(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--model',default='Qwen/Qwen2.5-Coder-1.5B-Instruct');p.add_argument('--eval-count',type=int,default=32)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    if (a.output/'run_manifest.json').exists(): raise ValueError('Use a fresh output directory; no silent overwrite')
    import torch, transformers, peft
    from transformers import AutoTokenizer,AutoModelForCausalLM,Trainer,TrainingArguments,set_seed
    from peft import LoraConfig,get_peft_model
    assert torch.cuda.is_available()
    set_seed(17); torch.set_num_threads(8)
    source=json.loads((a.data/'manifest.json').read_text())
    for split,h in source['files'].items(): assert hashlib.sha256((a.data/(split+'.jsonl')).read_bytes()).hexdigest()==h
    tokenizer=AutoTokenizer.from_pretrained(a.model,local_files_only=True)
    tokenizer.pad_token=tokenizer.eos_token
    model=AutoModelForCausalLM.from_pretrained(a.model,local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':0},attn_implementation='sdpa')
    revision=getattr(model.config,'_commit_hash',None)
    model=get_peft_model(model,LoraConfig(r=16,lora_alpha=32,lora_dropout=.05,target_modules=['q_proj','k_proj','v_proj','o_proj'],task_type='CAUSAL_LM'))
    model.enable_input_require_grads()
    def prompt(r):
        return tokenizer.apply_chat_template([{'role':'system','content':source['system']},{'role':'user','content':r['input']}],tokenize=False,add_generation_prompt=True)
    data={}; encoded={}; omissions=[]
    for split in ('train','validation','test'):
        data[split]=[];encoded[split]=[]
        for r in rows(a.data/(split+'.jsonl')):
            prefix=tokenizer(prompt(r),add_special_tokens=False)['input_ids']
            answer=tokenizer(r['target']+tokenizer.eos_token,add_special_tokens=False)['input_ids']
            if len(prefix)+len(answer)>3072 or len(answer)>1536:
                omissions.append(dict(id=r['id'],split=split,prompt_tokens=len(prefix),answer_tokens=len(answer)));continue
            data[split].append(r);encoded[split].append(dict(input_ids=prefix+answer,labels=[-100]*len(prefix)+answer))
    groups=[{r['component_id'] for r in rs} for rs in data.values()]
    assert all(not x&y for i,x in enumerate(groups) for y in groups[i+1:])
    manifest=dict(status='started',model=a.model,model_revision=revision,seed=17,epochs=1,source=source,
        counts={s:len(rs) for s,rs in data.items()},omissions=omissions,gpu=torch.cuda.get_device_name(0),
        packages=dict(torch=torch.__version__,transformers=transformers.__version__,peft=peft.__version__),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        config=dict(lora_rank=16,lora_alpha=32,learning_rate=2e-4,batch_size=4,gradient_accumulation=4,max_sequence_tokens=3072,max_generation_tokens=1536),
        evaluation='First 32 retained official-test rows in pre-shuffled manifest; fixed final epoch. Text sequence metrics only; no CAD execution, SVG accuracy, engineering correctness or geometric-generalization claim.')
    dump(a.output/'run_manifest.json',manifest)
    (a.output/'packages.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
    def evaluate(label):
        model.eval();model.config.use_cache=True;tokenizer.padding_side='left';results=[]
        rs=data['test'][:a.eval_count]
        with (model.disable_adapter() if label=='base' else nullcontext()):
            for start in range(0,len(rs),8):
                batch=rs[start:start+8];inputs=tokenizer([prompt(r) for r in batch],padding=True,return_tensors='pt').to('cuda')
                with torch.inference_mode(): result=model.generate(**inputs,max_new_tokens=1536,do_sample=False,pad_token_id=tokenizer.pad_token_id)
                predictions=tokenizer.batch_decode(result[:,inputs.input_ids.shape[1]:],skip_special_tokens=True)
                with (a.output/(label+'_generations.jsonl')).open('a') as f:
                    for r,pred,tokens in zip(batch,predictions,result[:,inputs.input_ids.shape[1]:]):
                        clean=' '.join(pred.split());target=' '.join(r['target'].split())
                        item=dict(id=r['id'],prediction=pred,target=r['target'],exact=clean==target,
                            text_similarity=difflib.SequenceMatcher(None,target,clean,autojunk=False).ratio(),
                            eos_seen=bool((tokens==tokenizer.eos_token_id).any().item()))
                        f.write(json.dumps(item)+'\n');results.append(item)
                print(label,len(results),'/',len(rs),flush=True)
        metric=dict(n=len(results),exact_rate=sum(r['exact'] for r in results)/len(results),mean_text_similarity=sum(r['text_similarity'] for r in results)/len(results),generation_cap_hits=sum(not r['eos_seen'] for r in results))
        dump(a.output/(label+'_metrics.json'),metric);print(label,metric,flush=True)
    evaluate('base')
    tokenizer.padding_side='right';model.config.use_cache=False
    def collate(batch):
        size=max(len(r['input_ids']) for r in batch)
        return dict(input_ids=torch.tensor([r['input_ids']+[tokenizer.pad_token_id]*(size-len(r['input_ids'])) for r in batch]),
            labels=torch.tensor([r['labels']+[-100]*(size-len(r['labels'])) for r in batch]),
            attention_mask=torch.tensor([[1]*len(r['input_ids'])+[0]*(size-len(r['input_ids'])) for r in batch]))
    args=TrainingArguments(output_dir=str(a.output/'checkpoints'),num_train_epochs=1,per_device_train_batch_size=4,
        gradient_accumulation_steps=4,per_device_eval_batch_size=4,learning_rate=2e-4,lr_scheduler_type='cosine',warmup_ratio=.05,
        bf16=True,gradient_checkpointing=True,gradient_checkpointing_kwargs={'use_reentrant':False},logging_steps=8,
        eval_strategy='epoch',save_strategy='epoch',save_total_limit=1,report_to='none',seed=17,data_seed=17,
        remove_unused_columns=False,label_names=['labels'],optim='adamw_torch',dataloader_num_workers=0)
    trainer=Trainer(model=model,args=args,train_dataset=encoded['train'],eval_dataset=encoded['validation'],data_collator=collate)
    t=time.perf_counter();result=trainer.train();dump(a.output/'training_metrics.json',result.metrics)
    trainer.save_model(str(a.output/'adapter'));tokenizer.save_pretrained(a.output/'adapter')
    dump(a.output/'training_history.json',trainer.state.log_history)
    evaluate('trained');manifest.update(status='completed',training_and_final_eval_seconds=time.perf_counter()-t)
    dump(a.output/'run_manifest.json',manifest)

if __name__=='__main__':main()
