"""Action-constrained, multi-step GRPO for a CAD verification agent (no value network)."""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, PeftModel, set_peft_model_state_dict
from safetensors.torch import load_file
from agentic_cad_policy import available, messages, model_logits, rollout

MODEL='Qwen/Qwen2.5-Coder-1.5B-Instruct'
REVISION='2e1fd397ee46e1388853d2af2c993145b0f1098a'


def load_model(adapter=None):
    tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION,local_files_only=True,padding_side='right')
    tokenizer.pad_token=tokenizer.eos_token
    base=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION,local_files_only=True,torch_dtype=torch.float32,attn_implementation='sdpa').to('cuda')
    if adapter:
        model=PeftModel.from_pretrained(base,adapter)
        set_peft_model_state_dict(model,load_file(str(Path(adapter)/'adapter_model.safetensors')))
    else:
        model=get_peft_model(base,LoraConfig(r=8,lora_alpha=16,lora_dropout=0,target_modules=['q_proj','k_proj','v_proj','o_proj'],task_type='CAUSAL_LM'))
    model.eval() # all dropout disabled; training enables checkpointing below
    model.config.use_cache=False
    ids=[tokenizer.encode(a,add_special_tokens=False) for a in 'ABCD']
    assert all(len(x)==1 for x in ids)
    return model,tokenizer,[x[0] for x in ids]


def encode(tokenizer,row):
    texts=[tokenizer.apply_chat_template(messages(row,s),tokenize=False,add_generation_prompt=True) for s in range(4)]
    encoded=tokenizer(texts,padding=True,return_tensors='pt',add_special_tokens=False)
    if encoded.input_ids.shape[1]>4096:
        raise ValueError('Full observation exceeds 4096 tokens; no truncation permitted')
    return encoded.to('cuda')


def distribution(model,encoded,ids):
    logits=model_logits(model,encoded,ids)
    mask=torch.tensor([[a in available(s) for a in range(4)] for s in range(4)],device=logits.device)
    p=torch.softmax((logits/1.5).masked_fill(~mask,-1e9),dim=-1)
    # Explicit exploration is part of the policy for both rollout and optimization.
    p=.9*p+.1*mask.float()/mask.sum(-1,keepdim=True)
    return p.clamp_min(1e-30).log()


def evaluate(model,tok,ids,rows,out):
    results=[]
    with torch.no_grad():
        for row in rows:
            probs=distribution(model,encode(tok,row),ids).exp().cpu().tolist()
            r=rollout(probs,row['label'])
            results.append(dict(id=row['id'],category=row['category'],label=row['label'],**r))
    out.write_text(''.join(json.dumps(r)+'\n' for r in results))
    tp=sum(r['accepted'] and r['label'] for r in results);tn=sum(not r['accepted'] and not r['label'] for r in results)
    fp=sum(r['accepted'] and not r['label'] for r in results);fn=sum(not r['accepted'] and r['label'] for r in results)
    return dict(n=len(results),true_accept=tp,true_reject=tn,false_accept=fp,false_reject=fn,accuracy=(tp+tn)/len(results),tool_calls=sum(len(r['trace'])-1 for r in results))


def main():
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--groups',type=int,default=600);p.add_argument('--seed',type=int,default=17)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if (a.out/'manifest.json').exists():raise SystemExit('Use a fresh output directory')
    torch.manual_seed(a.seed);random.seed(a.seed);rng=random.Random(a.seed)
    torch.set_num_threads(4)
    model,tok,ids=load_model()
    rows=[json.loads(l) for l in (a.data/'train.jsonl').read_text().splitlines()]
    dev=[json.loads(l) for l in (a.data/'dev.jsonl').read_text().splitlines()]
    # Verify every full prompt before the first optimizer update.
    for row in rows+dev:
        for state in range(4):
            tokens=tok.apply_chat_template(messages(row,state),tokenize=True,add_generation_prompt=True)
            if len(tokens)>4096:raise ValueError(f'Overlength {row["id"]}: {len(tokens)}')
    manifest=dict(model=MODEL,revision=REVISION,algorithm='constrained-action multi-step GRPO',seed=a.seed,groups=a.groups,group_size=8,optimization_passes=2,clip=.2,beta=.02,learning_rate=2e-5,temperature=1.5,uniform_exploration=.1,advantage_std_floor=.25,mandatory_first_tool=True,balanced_training_sampling=True,train_candidates=len(rows),dev_candidates=len(dev),train_sha256=hashlib.sha256((a.data/'train.jsonl').read_bytes()).hexdigest(),torch=torch.__version__,gpu=torch.cuda.get_device_name(),precision='float32',gradient_checkpointing=True,trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad))
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    start=time.monotonic();print('BASE_EVAL',flush=True)
    base=evaluate(model,tok,ids,dev,a.out/'base-dev.jsonl');print(json.dumps({'base_dev':base}),flush=True)
    optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=2e-5)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    model.enable_input_require_grads()
    model.train()
    for module in model.modules():
        if isinstance(module,torch.nn.Dropout):module.p=0.0
    rng.shuffle(rows);mixed=0;updates=0
    strata={label:[r for r in rows if r['label']==label] for label in (False,True)}
    with (a.out/'training.jsonl').open('w') as log:
        for step in range(a.groups):
            row=rng.choice(strata[bool(step%2)]);encoded=encode(tok,row)
            with torch.no_grad():
                old=distribution(model,encoded,ids).detach()
                with model.disable_adapter():reference=distribution(model,encoded,ids).detach()
            group=[rollout(old.exp().cpu().tolist(),row['label'],rng) for _ in range(8)]
            rewards=torch.tensor([g['reward'] for g in group],device='cuda')
            adv=(rewards-rewards.mean())/rewards.std(unbiased=False).clamp_min(.25)
            nonzero=rewards.std(unbiased=False).item()>1e-6
            mixed+=int(nonzero)
            losses=[]
            if nonzero:
                for _ in range(2):
                    current=distribution(model,encoded,ids)
                    loss=0
                    for i,g in enumerate(group):
                        terms=[]
                        for state,action in g['trace']:
                            ratio=(current[state,action]-old[state,action]).exp()
                            objective=torch.minimum(ratio*adv[i],ratio.clamp(.8,1.2)*adv[i])
                            kl=(current[state].exp()*(current[state]-reference[state])).sum()
                            terms.append(-objective+.02*kl)
                        loss=loss+torch.stack(terms).mean()/8
                    if not torch.isfinite(loss):raise FloatingPointError('Nonfinite loss before update')
                    optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0,error_if_nonfinite=True);optimizer.step();updates+=1;losses.append(loss.item())
            record=dict(group=step+1,id=row['id'],reward_mean=rewards.mean().item(),reward_std=rewards.std(unbiased=False).item(),mixed=nonzero,losses=losses,seconds=time.monotonic()-start)
            log.write(json.dumps(record)+'\n');log.flush()
            if (step+1)%5==0:print(json.dumps(record),flush=True)
    model.eval()
    model.save_pretrained(a.out/'adapter');tok.save_pretrained(a.out/'adapter')
    # Verify save/reload fidelity before final evaluation.
    check=encode(tok,dev[0])
    with torch.no_grad():expected=distribution(model,check,ids).cpu()
    model.load_adapter(a.out/'adapter',adapter_name='reloaded')
    set_peft_model_state_dict(model,load_file(str(a.out/'adapter/adapter_model.safetensors')),adapter_name='reloaded')
    model.set_adapter('reloaded');model.eval()
    with torch.no_grad():actual=distribution(model,check,ids).cpu()
    assert torch.allclose(expected,actual,atol=.01,rtol=.01)
    final=evaluate(model,tok,ids,dev,a.out/'grpo-dev.jsonl')
    summary=dict(base_dev=base,grpo_dev=final,groups=a.groups,mixed_groups=mixed,optimizer_updates=updates,seconds=time.monotonic()-start,peak_memory=torch.cuda.max_memory_allocated(),reload_verified=True)
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
