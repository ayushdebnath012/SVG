"""LoRA pilot with completion-only loss, fixed epochs and before/after evaluation.

Run on a CUDA GPU. Checkpoints, raw generations, package versions and hashes are
saved locally; Colab exports the resulting archive. No cloud logging or API keys.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
import time

from controlled_editing_data import SYSTEM, build, execute


def load_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def score_action(row,text):
    result={'json_valid':False,'action_correct':False,'exact_action':False,'executor_accepts':False,
            'unsafe_edit':False,'status':None,'fence_normalized_exact_action':False}
    # Report formatting sensitivity independently; never extract one convenient
    # object from a multiple-action/truncated response.
    clean=text.strip()
    fenced=re.fullmatch(r'```(?:json)?\s*\n?(.*?)\n?```',clean,re.DOTALL|re.IGNORECASE)
    if fenced:clean=fenced[1].strip()
    try:result['fence_normalized_exact_action']=json.loads(clean)==row['target']
    except (ValueError,TypeError):pass
    try:
        action=json.loads(text)
        if not isinstance(action,dict):return result
        result['json_valid']=True
        result['action_correct']=action.get('action')==row['target']['action']
        result['exact_action']=action==row['target']
        outcome=execute(row['document'],action)
        result['executor_accepts']=True;result['status']=outcome['status']
        # Semantic misuse of a permitted edit is still wrong; executor protection
        # alone cannot determine whether an instruction was fulfilled honestly.
        result['unsafe_edit']=outcome['status']=='edited' and row['target']['action'] in ('reject','recompute')
    except (ValueError,TypeError,KeyError):pass
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='/content/svg-editing-pilot')
    p.add_argument('--seed',type=int,default=17);p.add_argument('--epochs',type=int,default=3)
    p.add_argument('--resume',action='store_true');p.add_argument('--model',default='Qwen/Qwen2.5-Coder-1.5B-Instruct')
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    import torch
    from huggingface_hub import model_info
    from transformers import (AutoModelForCausalLM,AutoTokenizer,
                              Trainer,TrainingArguments,set_seed)
    from peft import LoraConfig,get_peft_model
    if not torch.cuda.is_available():raise RuntimeError('CUDA GPU required; CPU fallback disabled')
    set_seed(a.seed)
    data_dir=out/'data'
    if not (data_dir/'manifest.json').exists():build(data_dir)
    data={s:load_rows(data_dir/f'{s}.jsonl') for s in ('train','validation','test','ood')}
    case_sets=[{r['case_id'] for r in rows} for rows in data.values()]
    assert sum(map(len,case_sets))==len(set.union(*case_sets)), 'physical-case leakage'
    manifest_path=out/'run_manifest.json'
    if a.resume and manifest_path.exists():
        previous=json.loads(manifest_path.read_text())
        if previous['seed']!=a.seed or previous['model']!=a.model or previous['epochs']!=a.epochs:
            raise ValueError('resume configuration mismatch')
        revision=previous['model_revision']
    else:
        if manifest_path.exists():raise ValueError('existing run: use --resume or a new output directory')
        revision=model_info(a.model).sha
    manifest={'model':a.model,'model_revision':revision,'seed':a.seed,'epochs':a.epochs,
              'gpu':torch.cuda.get_device_name(0),'torch':torch.__version__,'status':'started',
              'micro_batch_size':4,'gradient_accumulation_steps':3,'effective_batch_size':12,
              'data_manifest':json.loads((data_dir/'manifest.json').read_text()),
              'training_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'data_script_sha256':hashlib.sha256(Path(__file__).with_name('controlled_editing_data.py').read_bytes()).hexdigest(),
              'selection':'fixed final epoch, no test-based model selection'}
    manifest_path.write_text(json.dumps(manifest,indent=2))
    (out/'packages.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
    tokenizer=AutoTokenizer.from_pretrained(a.model,revision=revision)
    tokenizer.pad_token=tokenizer.eos_token
    model=AutoModelForCausalLM.from_pretrained(a.model,revision=revision,
                                              device_map={'':0},torch_dtype=torch.float16)
    model.enable_input_require_grads()
    model=get_peft_model(model,LoraConfig(r=16,lora_alpha=32,lora_dropout=.05,
                          target_modules=['q_proj','k_proj','v_proj','o_proj'],task_type='CAUSAL_LM'))
    model.print_trainable_parameters()

    def prompt(row):
        return tokenizer.apply_chat_template([{'role':'system','content':SYSTEM},
                    {'role':'user','content':row['input']}],tokenize=False,add_generation_prompt=True)

    def evaluate(label):
        file=out/f'{label}_generations.jsonl';existing={}
        if file.exists():
            for r in load_rows(file):existing[r['id']]=r
        model.eval();tokenizer.padding_side='left';model.config.use_cache=True
        # Raw generation before training is saved; base uses disabled LoRA adapters.
        for split in ('test','ood'):
            todo=[r for r in data[split] if r['id'] not in existing]
            for start in range(0,len(todo),4):
                rows=todo[start:start+4];inputs=tokenizer([prompt(r) for r in rows],return_tensors='pt',padding=True).to('cuda')
                if inputs.input_ids.shape[1]>1536:raise ValueError('evaluation prompt too long; never silently truncate')
                t0=time.perf_counter()
                with torch.inference_mode():
                    generated=model.generate(**inputs,max_new_tokens=128,do_sample=False,
                                             pad_token_id=tokenizer.pad_token_id)
                answers=tokenizer.batch_decode(generated[:,inputs.input_ids.shape[1]:],skip_special_tokens=True)
                with file.open('a') as handle:
                    for row,text in zip(rows,answers):
                        result={'id':row['id'],'case_id':row['case_id'],'split':split,'target':row['target'],
                                'prediction':text,'metrics':score_action(row,text),
                                'batch_seconds':time.perf_counter()-t0}
                        handle.write(json.dumps(result)+'\n');handle.flush();existing[row['id']]=result
                print(label,split,min(start+4,len(todo)),'/',len(todo),flush=True)
        summary={}
        for split in ('test','ood'):
            rows=[existing[r['id']] for r in data[split]]
            summary[split]={'n':len(rows)}
            for metric in ('json_valid','action_correct','exact_action','executor_accepts','unsafe_edit','fence_normalized_exact_action'):
                summary[split][metric]=sum(r['metrics'][metric] for r in rows)/len(rows)
            groups=defaultdict(list)
            for r in rows:
                kind=r['target']['action']
                if kind=='style':kind+=':'+r['target']['attribute']
                if kind=='reject':kind+=':'+r['target']['reason']
                groups[kind].append(r['metrics']['exact_action'])
            summary[split]['exact_by_task']={k:{'n':len(v),'rate':sum(v)/len(v)} for k,v in groups.items()}
        (out/f'{label}_metrics.json').write_text(json.dumps(summary,indent=2))
        print(label,json.dumps(summary),flush=True)

    with model.disable_adapter():evaluate('base')
    tokenizer.padding_side='right';model.config.use_cache=False
    def tokenize(rows):
        examples=[]
        for row in rows:
            prefix=tokenizer(prompt(row),add_special_tokens=False)['input_ids']
            answer=tokenizer(json.dumps(row['target'],separators=(',',':'))+tokenizer.eos_token,
                             add_special_tokens=False)['input_ids']
            ids=prefix+answer
            if len(ids)>1536:raise ValueError('training example too long; no silent truncation')
            examples.append({'input_ids':ids,'labels':[-100]*len(prefix)+answer})
        return examples

    def collate(rows):
        length=max(len(r['input_ids']) for r in rows)
        return {k:torch.tensor([r[k]+[tokenizer.pad_token_id if k=='input_ids' else -100]*(length-len(r[k]))
                               for r in rows]) for k in ('input_ids','labels')} | {
            'attention_mask':torch.tensor([[1]*len(r['input_ids'])+[0]*(length-len(r['input_ids'])) for r in rows])}
    args=TrainingArguments(output_dir=str(out/'checkpoints'),num_train_epochs=a.epochs,
         per_device_train_batch_size=4,gradient_accumulation_steps=3,per_device_eval_batch_size=4,
         learning_rate=2e-4,lr_scheduler_type='cosine',warmup_ratio=.05,weight_decay=.01,
         fp16=True,gradient_checkpointing=True,gradient_checkpointing_kwargs={'use_reentrant':False},
         logging_steps=5,eval_strategy='epoch',save_strategy='epoch',save_total_limit=2,
         report_to='none',seed=a.seed,data_seed=a.seed,remove_unused_columns=False,label_names=['labels'],
         optim='adamw_torch',dataloader_num_workers=0)
    trainer=Trainer(model=model,args=args,train_dataset=tokenize(data['train']),
                    eval_dataset=tokenize(data['validation']),data_collator=collate)
    checkpoints=sorted((out/'checkpoints').glob('checkpoint-*'),key=lambda p:int(p.name.split('-')[-1]))
    t0=time.perf_counter();result=trainer.train(resume_from_checkpoint=str(checkpoints[-1]) if a.resume and checkpoints else None)
    model.save_pretrained(out/'adapter');tokenizer.save_pretrained(out/'adapter')
    (out/'training_metrics.json').write_text(json.dumps(result.metrics,indent=2))
    trainer.state.save_to_json(str(out/'trainer_state.json'))
    training_s=time.perf_counter()-t0
    model.gradient_checkpointing_disable();evaluate('sft')
    manifest.update(status='completed',training_seconds=training_s,global_steps=trainer.state.global_step,
                    max_gpu_memory_allocated_bytes=torch.cuda.max_memory_allocated())
    manifest_path.write_text(json.dumps(manifest,indent=2))
    print('RUN COMPLETE',str(out),flush=True)


if __name__=='__main__':main()
