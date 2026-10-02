"""Bounded portal-frame pilot: model interprets requests; deterministic code draws/solves.
Not detached-SVG understanding or whole-table safety certification.
"""
import argparse, copy, hashlib, html, json, math, random, re
from pathlib import Path
import cad_astra_benchmark as B
import engsvg_rule_interpreter as R
import engsvg_detached_importer as D

FIELDS = ('width_mm','height_mm','section_b_mm','section_h_mm','E_mpa','vertical_load_N','horizontal_load_N')
SCHEMA = 'Return JSON only: {"action":"create","parameters":{...}} or {"action":"edit","changes":{...}} or {"action":"clarify","missing":[...]}. Fields: '+', '.join(FIELDS)+'. All fields are required for creation. Edits change only requested fields. Loads are positive magnitudes: downward vertical and rightward horizontal at top-right. This is a planar rigid-joint portal with fixed bases, uniform rectangular section, no self-weight. Never invent missing values. '

def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def validate(p):
    if set(p)!=set(FIELDS): raise ValueError('missing or extra parameters')
    for k,v in p.items():
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v): raise ValueError('nonfinite/nonnumeric parameter')
        if v < 0 or (k not in FIELDS[-2:] and v<=0): raise ValueError('invalid parameter range')
    if p['width_mm']>20000 or p['height_mm']>20000: raise ValueError('outside pilot envelope')

def execute(source, action):
    kind=action.get('action')
    if kind=='clarify':
        if set(action)!={'action','missing'} or not isinstance(action['missing'],list) or not action['missing'] or any(k not in FIELDS for k in action['missing']): raise ValueError('invalid clarification')
        return None
    if kind=='create' and source is None and set(action)=={'action','parameters'}: p=copy.deepcopy(action['parameters'])
    elif kind=='edit' and source is not None and set(action)=={'action','changes'}:
        if not isinstance(action['changes'],dict) or not action['changes'] or not set(action['changes'])<=set(FIELDS): raise ValueError('invalid changes')
        p=copy.deepcopy(source); p.update(action['changes'])
    else: raise ValueError('invalid action')
    validate(p)
    return p

def model(p):
    validate(p)
    w,h=p['width_mm'],p['height_mm']
    return dict(name='Table side-frame: fixed bases, rigid joints',nodes={'A':[0,0],'B':[w,0],'C':[0,h],'D':[w,h]},
      members=[B.member(i,a,b,p['section_b_mm'],p['section_h_mm'],p['E_mpa']) for i,a,b in [('left','A','C'),('right','B','D'),('top','C','D')]],
      supports={'A':[0,1,2],'B':[0,1,2]},loads={'D':[p['horizontal_load_N'],-p['vertical_load_N'],0]},probe='D')

def artifact(p):
    m=model(p); r=B.solve(m); svg=B.reference_svg(m,B.mapping(m))
    # Results are newly computed for this exact revision, never copied from a source drawing.
    import xml.etree.ElementTree as ET
    ET.fromstring(svg)
    note='Planar linear frame only; excludes buckling, tipping, joints and out-of-plane behaviour.'
    embedded = {
        'schema_version': 'engsvg-design-v1', 'parameters': p,
        'nodes': m['nodes'], 'members': [x['id'] for x in m['members']],
        'supports': m['supports'], 'loads': m['loads'],
    }
    metadata = html.escape(json.dumps(embedded, sort_keys=True, separators=(',', ':')))
    visible_parameters = (
        f'<text data-parameter="E_mpa" x="35" y="728" font-size="12">E: {p["E_mpa"]} MPa</text>'
        f'<text data-parameter="vertical_load_N" x="300" y="728" font-size="12">Vertical load: {p["vertical_load_N"]} N downward</text>'
        f'<text data-parameter="horizontal_load_N" x="700" y="728" font-size="12">Horizontal load: {p["horizontal_load_N"]} N rightward</text>'
    )
    svg=svg.replace('</svg>',visible_parameters+f'<metadata id="engsvg-design">{metadata}</metadata>'
                              f'<text x="35" y="825" font-size="12">{note}</text></svg>')
    ET.fromstring(svg)
    return {'design':p,'revision':digest(p),'analysis':r,'method':'2D Euler-Bernoulli frame FEM','scope':note},svg

def extract_embedded_design(svg):
    import xml.etree.ElementTree as ET
    root=ET.fromstring(svg)
    metadata=next((element for element in root.iter() if element.tag.endswith('metadata') and element.get('id')=='engsvg-design'),None)
    if metadata is None or not metadata.text: raise ValueError('missing engsvg design metadata')
    embedded=json.loads(metadata.text)
    if embedded.get('schema_version')!='engsvg-design-v1': raise ValueError('unsupported engsvg metadata version')
    validate(embedded['parameters'])
    return embedded

def process_request(request,source=None):
    """Interpret text, validate the action, rebuild the SVG, and rerun FEM."""
    action=R.interpret(request,source)
    summary=R.change_summary(source,action)
    design=execute(source,action)
    result={'request':request,'source':source,'action':action,'change_summary':summary,'design':design}
    if design is None: return result,None
    engineering,svg=artifact(design)
    assert extract_embedded_design(svg)['parameters']==design
    result['engineering']=engineering
    return result,svg

def save_request(out,request,source=None):
    out.mkdir(parents=True,exist_ok=True)
    result,svg=process_request(request,source)
    (out/'request-result.json').write_text(json.dumps(result,indent=2)+'\n')
    if svg is not None: (out/'design.svg').write_text(svg)
    return result

def process_detached_svg(svg,request=None,supplied=None):
    """Recover a detached SVG and optionally apply an edit to the recovered design."""
    recovered=D.import_svg(svg,supplied)
    result={'import':recovered}
    if recovered['status']!='recovered':
        result['action']={'action':'clarify','missing':recovered['missing'],
                          'ambiguities':recovered['ambiguities']}
        return result,None
    if request is None:
        engineering,rebuilt=artifact(recovered['design'])
        result.update(design=recovered['design'],engineering=engineering)
        return result,rebuilt
    edited,rebuilt=process_request(request,recovered['design'])
    result['edit']=edited
    return result,rebuilt

def save_detached_request(out,svg_path,request=None,supplied=None):
    out.mkdir(parents=True,exist_ok=True)
    source_svg=Path(svg_path).read_text()
    result,svg=process_detached_svg(source_svg,request,supplied)
    (out/'import-result.json').write_text(json.dumps(result,indent=2)+'\n')
    if svg is not None: (out/'recovered.svg').write_text(svg)
    return result

def sample(rng):
    return dict(zip(FIELDS,[rng.randrange(800,2401,25),rng.randrange(600,1201,25),rng.randrange(25,81,5),rng.randrange(40,121,5),rng.choice([70000,200000,210000]),rng.randrange(100,2001,50),rng.randrange(0,501,25)]))

def dataset(n=160,seed=71):
    rng=random.Random(seed); groups={'train':[],'validation':[],'test':[]}; seen=set()
    names={'width_mm':'width','height_mm':'height','section_b_mm':'section breadth','section_h_mm':'section depth','E_mpa':'elastic modulus','vertical_load_N':'downward load','horizontal_load_N':'rightward load'}
    for i in range(n):
        p=sample(rng)
        while digest(p) in seen: p=sample(rng)
        seen.add(digest(p)); split='train' if i<int(.75*n) else 'validation' if i<int(.875*n) else 'test'
        vals=', '.join(f'{names[k]} {v} '+('MPa' if k=='E_mpa' else 'N' if 'load' in k else 'mm') for k,v in p.items())
        requests=[('create',None,'Create a table side-frame with '+vals+'.',{'action':'create','parameters':p})]
        for k in rng.sample(list(FIELDS),3):
            v=sample(rng)[k]
            if v==p[k]: v+=25
            requests.append(('edit',p,f'Set {names[k]} to {v} '+('MPa' if k=='E_mpa' else 'N' if 'load' in k else 'mm')+'. Preserve everything else.',{'action':'edit','changes':{k:v}}))
        missing=rng.choice(list(FIELDS)); partial={k:v for k,v in p.items() if k!=missing}
        requests.append(('clarify',None,'Create a table side-frame. Supplied parameters: '+json.dumps(partial),{'action':'clarify','missing':[missing]}))
        for kind,source,request,target in requests:
            prompt=SCHEMA+'\nExisting design: '+json.dumps(source)+'\nRequest: '+request
            groups[split].append(dict(group=digest(p),kind=kind,source=source,prompt=prompt,target=json.dumps(target,separators=(',',':')),expected=execute(source,target)))
    # Round-robin task types for balanced bounded evaluation.
    for rows in groups.values(): rng.shuffle(rows)
    return groups

def assess(row,text):
    try:
        text=re.sub(r'^```(?:json)?\s*|\s*```$','',text.strip())
        a=json.loads(text); p=execute(row['source'],a); target=json.loads(row['target'])
        ok = a==target if p is None else p==row['expected']
        if p is not None:
            art,svg=artifact(p)
            ok=ok and max(abs(v) for v in art['analysis']['equilibrium_residual_N_Nmm'])<1e-3
        return {'valid_action':True,'success':bool(ok),'prediction':a}
    except Exception as e: return {'valid_action':False,'success':False,'error':str(e)[:250]}

def verify(out):
    import numpy as np
    p=sample(random.Random(8)); before=copy.deepcopy(p)
    q=execute(p,{'action':'edit','changes':{'width_mm':p['width_mm']+100}})
    assert p==before and all(q[k]==p[k] for k in FIELDS if k!='width_mm')
    a,svg=artifact(p); b,_=artifact(q); assert a['revision']!=b['revision']
    assert extract_embedded_design(svg)['parameters']==p
    for bad in [-1,float('nan'),True]:
        try: execute(p,{'action':'edit','changes':{'width_mm':bad}})
        except ValueError: pass
        else: raise AssertionError('invalid edit accepted')
    # Independent closed-form cantilever deflection/stress control.
    E,L,F,breadth,depth=200000,1000,500,40,80
    m=dict(nodes={'A':[0,0],'B':[L,0]},members=[B.member('beam','A','B',breadth,depth,E)],supports={'A':[0,1,2]},loads={'B':[0,-F,0]},probe='B')
    r=B.solve(m); I=breadth*depth**3/12
    assert np.isclose(r['uy_mm'],-F*L**3/(3*E*I),rtol=1e-9)
    assert np.isclose(r['peak_stress_mpa'],F*L*(depth/2)/I,rtol=1e-9)
    for p in [sample(random.Random(i)) for i in range(8)]:
        r=B.solve(model(p)); fine=B.solve(model(p),subdivisions=3)
        assert max(abs(v) for v in r['equilibrium_residual_N_Nmm'])<1e-3
        assert np.isclose(r['uy_mm'],fine['uy_mm'],rtol=1e-7,atol=1e-9)
    data=dataset(); sets=[{r['group'] for r in rows} for rows in data.values()]
    assert all(not sets[i]&sets[j] for i in range(3) for j in range(i))
    for rows in data.values():
        for row in rows: assert assess(row,row['target'])['success']
    row=next(r for r in data['test'] if r['kind']=='edit')
    assert not assess(row,json.dumps({'action':'create','parameters':row['source']}))['success']
    out.mkdir(parents=True,exist_ok=True)
    for split,rows in data.items(): (out/f'{split}.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
    (out/'before.svg').write_text(svg); (out/'after.svg').write_text(artifact(q)[1])
    (out/'demo.json').write_text(json.dumps({'before':a,'after':b},indent=2))
    print('VERIFIED: analytical controls, equilibrium, subdivision, immutable edits, invalid-input rejection, split separation, all target actions',flush=True)
    return data

def train(out,epochs=3):
    data=verify(out/'data')
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM,Trainer,TrainingArguments,set_seed
    from peft import LoraConfig,get_peft_model
    from colab_train_engsvg import training_arguments
    assert torch.cuda.is_available(),'CUDA GPU required'
    set_seed(71); name='Qwen/Qwen2.5-Coder-1.5B-Instruct'
    tok=AutoTokenizer.from_pretrained(name); tok.pad_token=tok.pad_token or tok.eos_token
    def prompt(row): return tok.apply_chat_template([{'role':'user','content':row['prompt']}],tokenize=False,add_generation_prompt=True)
    def encode(rows):
        result=[]
        for r in rows:
            p=tok(prompt(r),add_special_tokens=False)['input_ids']; t=tok(r['target']+tok.eos_token,add_special_tokens=False)['input_ids']
            assert len(p+t)<=2048,'No silent training truncation allowed'
            result.append({'input_ids':p+t,'labels':[-100]*len(p)+t})
        return result
    def collate(batch):
        n=max(len(x['input_ids']) for x in batch)
        return {k:torch.tensor([x[k]+[tok.pad_token_id if k=='input_ids' else -100]*(n-len(x[k])) for x in batch]) for k in ['input_ids','labels']} | {'attention_mask':torch.tensor([[1]*len(x['input_ids'])+[0]*(n-len(x['input_ids'])) for x in batch])}
    model_=AutoModelForCausalLM.from_pretrained(name,dtype=torch.bfloat16,device_map='cuda')
    test=[]
    for kind in ['create','edit','clarify']: test.extend([r for r in data['test'] if r['kind']==kind][:12])
    def evaluate(m,tag):
        m.eval(); m.config.use_cache=True
        if hasattr(m,'gradient_checkpointing_disable'): m.gradient_checkpointing_disable()
        records=[]
        for i,row in enumerate(test):
            inputs=tok(prompt(row),return_tensors='pt').to('cuda')
            with torch.inference_mode(): ids=m.generate(**inputs,max_new_tokens=220,do_sample=False,pad_token_id=tok.pad_token_id)
            text=tok.decode(ids[0][inputs['input_ids'].shape[1]:],skip_special_tokens=True)
            result=assess(row,text); result.update(kind=row['kind'],raw=text,group=row['group']); records.append(result)
            (out/f'{tag}-predictions.json').write_text(json.dumps(records,indent=2))
            print(tag,i+1,len(test),row['kind'],result['success'],flush=True)
        return {kind:{'n':sum(r['kind']==kind for r in records),'success':sum(r['success'] for r in records if r['kind']==kind)} for kind in ['create','edit','clarify']}
    before=evaluate(model_,'base')
    model_=get_peft_model(model_,LoraConfig(r=16,lora_alpha=32,lora_dropout=.05,target_modules=['q_proj','k_proj','v_proj','o_proj'],task_type='CAUSAL_LM'))
    model_.enable_input_require_grads(); model_.config.use_cache=False
    args=training_arguments(TrainingArguments,output_dir=str(out/'checkpoints'),num_train_epochs=epochs,per_device_train_batch_size=1,gradient_accumulation_steps=8,learning_rate=2e-4,lr_scheduler_type='cosine',logging_steps=20,eval_strategy='epoch',save_strategy='epoch',save_total_limit=2,bf16=True,report_to=[],seed=71,gradient_checkpointing=True,remove_unused_columns=False)
    trainer=Trainer(model=model_,args=args,train_dataset=encode(data['train']),eval_dataset=encode(data['validation']),data_collator=collate)
    history=trainer.train(); model_.save_pretrained(out/'adapter'); tok.save_pretrained(out/'adapter')
    after=evaluate(model_.merge_and_unload(),'trained')
    result=dict(model=name,gpu=torch.cuda.get_device_name(0),before=before,after=after,train_metrics=history.metrics,scope='Synthetic portal parameter/action pilot; no detached SVG recovery; no Astra claim',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'summary.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2),flush=True)
    import shutil
    # Trainer checkpoints contain optimizer state and make the portable artifact
    # several times larger.  The final adapter is sufficient for reproduction
    # and evaluation, while the training metrics remain in summary.json.
    shutil.rmtree(out/'checkpoints', ignore_errors=True)
    shutil.make_archive(str(out)+'-artifacts','zip',out)
    print('COMPLETED',out,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('command',choices=['verify','train','request','import-svg']); ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--request'); ap.add_argument('--source',help='Existing design as JSON text or a JSON file')
    ap.add_argument('--svg',type=Path,help='Detached SVG to import')
    ap.add_argument('--supplied',help='Known missing values as JSON text or a JSON file')
    a=ap.parse_args()
    if a.command=='verify': verify(a.out)
    elif a.command=='train': train(a.out)
    elif a.command=='request':
        if not a.request: ap.error('--request is required for request mode')
        source=None
        if a.source:
            candidate=Path(a.source)
            source=json.loads(candidate.read_text()) if candidate.exists() else json.loads(a.source)
        print(json.dumps(save_request(a.out,a.request,source),indent=2))
    else:
        if not a.svg: ap.error('--svg is required for import-svg mode')
        supplied=None
        if a.supplied:
            candidate=Path(a.supplied)
            supplied=json.loads(candidate.read_text()) if candidate.exists() else json.loads(a.supplied)
        print(json.dumps(save_detached_request(a.out,a.svg,a.request,supplied),indent=2))
