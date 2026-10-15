"""Decode one split with a trained distillation adapter (Colab GPU), exactly as train_distill_cad_colab.py decodes test.

  python decode_split_colab.py --data DATA_DIR --run RESULTS_DIR --split validation
writes RESULTS_DIR/<split>-predictions.jsonl (same fields as trained-predictions.jsonl).
"""
import argparse,hashlib,json
from pathlib import Path
from cad_edit_contracts import apply,target_match
from cad_edit_verifier import extract
from train_distill_cad_colab import CAP

def main():
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--split',default='validation');a=p.parse_args()
 import torch
 from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig
 from peft import PeftModel
 manifest=json.loads((a.run/'run_manifest.json').read_text());source=json.loads((a.data/'manifest.json').read_text())
 assert manifest['status']=='completed' and manifest['source_manifest']['files']==source['files'],'adapter was trained on different data'
 dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
 quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=dtype)
 tokenizer=AutoTokenizer.from_pretrained(manifest['model'],revision=manifest['model_revision']);tokenizer.pad_token=tokenizer.eos_token;tokenizer.padding_side='left'
 base=AutoModelForCausalLM.from_pretrained(manifest['model'],revision=manifest['model_revision'],torch_dtype=dtype,quantization_config=quant,device_map={'':0},attn_implementation='sdpa')
 model=PeftModel.from_pretrained(base,str(a.run/'adapter')).eval();model.config.use_cache=True
 f=a.data/f'{a.split}.jsonl';assert hashlib.sha256(f.read_bytes()).hexdigest()==source['files'][a.split]
 omitted={o['id'] for o in json.loads((a.run/'omissions.json').read_text()) if o['split']==a.split}
 rows=[r for r in map(json.loads,f.read_text().splitlines()) if r['id'] not in omitted];result=[]
 def prompt(r):return tokenizer.apply_chat_template([dict(role='system',content=source['system']),dict(role='user',content=r['input'])],tokenize=False,add_generation_prompt=True)
 for start in range(0,len(rows),4):
  rs=rows[start:start+4];inputs=tokenizer([prompt(r) for r in rs],add_special_tokens=False,padding=True,return_tensors='pt').to('cuda')
  with torch.inference_mode():generated=model.generate(**inputs,max_new_tokens=CAP,do_sample=False,pad_token_id=tokenizer.pad_token_id)[:,inputs.input_ids.shape[1]:]
  for r,text,tokens in zip(rs,tokenizer.batch_decode(generated,skip_special_tokens=True),generated):
   error=None;patch=None;match=False;code=None
   try:_,patch=extract(text);code=apply(r['code'],patch,r['representation']);match=target_match(code,r['edited_code'],r['representation'])
   except Exception as e:error=type(e).__name__+': '+str(e)[:250]
   result.append(dict(id=r['id'],source=r['source'],representation=r['representation'],component_id=r['component_id'],category=r['category'],prediction=text,applicable=error is None,exact_patch=patch==json.loads(r['target_patch']),target_match=match,error=error,predicted_code=code,reference_code=r['edited_code'],reference_step=None,reference_step_sha256=None,generation_cap_hit=not bool((tokens==tokenizer.eos_token_id).any().item())))
  print(a.split,len(result),'/',len(rows),flush=True)
 (a.run/f'{a.split}-predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in result))
 print(a.split,dict(n=len(result),applicable=sum(r['applicable'] for r in result),target_match=sum(r['target_match'] for r in result)),flush=True)
if __name__=='__main__':main()
