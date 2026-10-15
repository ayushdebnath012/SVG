"""Budgeted single-shot code generation; separate sandbox execution and scoring."""
from pathlib import Path
import json,hashlib,urllib.request,urllib.error,re,time
ROOT=Path(__file__).resolve().parents[1];PKG=ROOT.parent/'cadfem-bench-v1.7';OUT=ROOT/'runs/astra-hard-single-shot-20261015';OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'dispatch.json').exists():raise SystemExit('Already dispatched; no retry')
t=next(json.loads(l) for l in (PKG/'candidate/tasks.jsonl').read_text().splitlines() if json.loads(l)['task_id']=='A-FCVM-Plate_girder_EC3')
f=json.loads((PKG/'candidate/tasks'/t['task_id']/'faces.json').read_text())
sample={k:v[:1] if isinstance(v,list) else v for k,v in f.items()}
sys='You are solving a CAD+FEM benchmark task. Return only a complete runnable Python main.py, with no markdown fences. No model-side tools are available; your code will run locally. Do not hardcode a guessed answer or use published reference results.'
prompt=t['prompt']+'\nRuntime: Python with numpy, scipy, gmsh, cadquery, meshio, skfem. Also ccx (CalculiX 2.23) available on PATH. No FreeCAD or ANSYS. Read CADFEM_INPUT_DIR/analysis.step and faces.json; write outputs into CADFEM_OUTPUT_DIR. main.py itself is preserved separately by the runner. Internet and evaluator data are blocked. 600 seconds, 2 CPU threads, 6000 MB RAM. Choose meshes feasible for these limits and record convergence honestly. Preserve exact distributed load set and support scopes; fragment/fuse interfaces as required.\nfaces.json schema example: '+json.dumps(sample)+'\nYou have one code-generation attempt, no repair feedback. Provide runnable code, not a plan. If computation fails, do not fabricate results.'
cap=8000;bound=len((sys+prompt).encode())+4096;maxcost=bound*12.5/1e6+cap*50/1e6
prior=json.loads((ROOT/'runs/astra-challenge-diagnostic-20261015/result.json').read_text())['cost_usd_conservative'];remaining=.75-prior;assert maxcost<remaining,(maxcost,remaining)
payload={'model':'gpt-6-astra','messages':[{'role':'system','content':sys},{'role':'user','content':prompt}],'reasoning_effort':'medium','max_completion_tokens':cap,'store':False}
(OUT/'request.json').write_text(json.dumps(payload,indent=2)+'\n')
protocol={'task_id':t['task_id'],'release':'v1.7','reasoning':'medium','protocol':'single-shot code generation plus sandbox execution; not comparable to multi-turn agent pilot','budget_total_usd':.75,'prior_spend_usd_conservative':prior,'remaining_before_call':remaining,'call_cost_upper_bound':maxcost,'output_token_cap':cap,'input_bound_including_framing_reserve':bound,'task_sha256':hashlib.sha256(json.dumps(t,sort_keys=True).encode()).hexdigest(),'selection':'Hard existing active source-backed task, independently reproduced; not a new web discovery','max_calls':1}
(OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
key=None
for line in (ROOT.parent/'.env.svg_new').read_text().splitlines():
 n,sep,v=line.strip().removeprefix('export ').partition('=')
 if sep and n=='OPENAI_API_KEY_SVG_NEW':key=v.strip().strip('\"').strip("'")
assert key
(OUT/'dispatch.json').write_text(json.dumps({'started':time.time()})+'\n');start=time.time();r={}
try:
 req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=600) as resp:raw=json.load(resp)
 (OUT/'response.json').write_text(json.dumps(raw,indent=2)+'\n');c=raw['choices'][0];txt=c['message'].get('content') or '';(OUT/'response.txt').write_text(txt)
 u=raw.get('usage') or {};cached=(u.get('prompt_tokens_details') or {}).get('cached_tokens',0) or 0;cost=((u.get('prompt_tokens',0)-cached)*12.5+cached+u.get('completion_tokens',0)*50)/1e6
 r.update(status='completed',model=raw.get('model'),usage=u,cost_usd_conservative=cost,finish_reason=c['finish_reason'])
 code=txt.strip()
 if code.startswith('```') and code.endswith('```'):code='\n'.join(code.splitlines()[1:-1])
 (OUT/'submission').mkdir(exist_ok=True);(OUT/'submission/main.py').write_text(code+'\n')
except urllib.error.HTTPError as e:r.update(status='api_error',http_status=e.code,error=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',e.read().decode(errors='replace').replace(key,'[REDACTED]'))[:600])
except Exception as e:r.update(status='client_error',error_type=type(e).__name__)
r['elapsed_seconds']=round(time.time()-start,1);(OUT/'generation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
