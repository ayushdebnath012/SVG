"""One medium-reasoning model-authored repair; numerical references never sent."""
from pathlib import Path
import sys,json,hashlib,urllib.request,urllib.error,time,ast,re,signal
ROOT=Path(__file__).resolve().parents[1];PKG=ROOT.parent/'cadfem-bench-v1.7';tid=sys.argv[1];OUT=ROOT/'runs/astra-recheck-20261015'/tid;OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'dispatch.json').exists():raise SystemExit('No duplicate dispatch')
prev=ROOT/'runs/astra-failure-hunt-20261015'/tid
if tid=='A-FCVM-Plate_girder_EC3':prev=ROOT/'runs/astra-girder-repair-20261015'
t=next(t for t in map(json.loads,(PKG/'candidate/tasks.jsonl').read_text().splitlines()) if t['task_id']==tid)
source=(prev/'submission/main.py').read_text();logs=[]
for f in [prev/'replay/sandbox.log']:
 if f.exists():logs.append(f.name+':\n'+f.read_text(errors='replace')[-2400:])
for f in (prev/'replay/outputs').rglob('*'):
 if f.is_file() and f.name in ['solver.log']:
  logs.append(str(f.relative_to(prev))+':\n'+f.read_text(errors='replace')[-1800:])
 if f.is_file() and f.suffix=='.dat' and tid=='A-FCVM-Buckling':
  raw=f.read_text(errors='replace');lines=raw.splitlines();idx=next((i for i,line in enumerate(lines) if 'BUCKLING' in ''.join(line.upper().split())),None);excerpt='\n'.join(lines[max(0,idx-2):idx+24]) if idx is not None else raw[-1500:];logs.append('Native .dat output excerpt:\n'+excerpt)
feedback='Previous code failed during execution. Diagnose the actual code and logs; fix all issues needed for a complete solve.'
if tid=='A-FCVM-Plate_girder_EC3':feedback='Previous code executed, but independent numerical validation failed. No target values or error directions are disclosed. Review the physical setup, interface continuity, geometric stiffness, load application and mesh resolution. Improve it honestly; do not infer or hardcode the reference.'
system='You are repairing your CAD+FEM solver code after execution feedback. Return only JSON: {"edits":[{"old":"exact unique source substring","new":"replacement source substring"}],"reason":"brief explanation"}. Every old substring must occur exactly once in CURRENT_CODE; edits are applied sequentially. You may change any part of the solver. No markdown. Do not hardcode answers, bypass FEM, or fabricate outputs.'
prompt='ORIGINAL TASK:\n'+t['prompt']+'\nRUNTIME: Python numpy/scipy/gmsh/cadquery/meshio/skfem and ccx (CalculiX 2.23). CADFEM_INPUT_DIR contains '+json.dumps([Path(i['path']).name for i in t['inputs']])+'. Write into CADFEM_OUTPUT_DIR. No internet, evaluator access, FreeCAD or ANSYS. 600 seconds, two CPU threads, 6000 MB RAM. Full script will be rerun cleanly on the same input. main.py is preserved by evaluator. Never fabricate convergence.\nFEEDBACK:\n'+feedback+'\n'+'\n'.join(logs)+'\nCURRENT_CODE:\n'+source
cap=7000;bound=len((system+prompt).encode())+512;maximum=2*bound*12.5/1e6+cap*50/1e6
ledger=ROOT/'output/datasets/cadfem-challenge-trials/astra-recheck-20261015.json';d=json.loads(ledger.read_text());assert d['session_cost_upper_bound_usd']+maximum<=d['budget_usd'],(maximum,d['session_cost_upper_bound_usd'])
payload={'model':'gpt-6-astra','messages':[{'role':'system','content':system},{'role':'user','content':prompt}],'reasoning_effort':'medium','max_completion_tokens':cap,'store':False}
(OUT/'request.json').write_text(json.dumps(payload,indent=2)+'\n');(OUT/'protocol.json').write_text(json.dumps({'task_id':tid,'prior_run':str(prev),'reasoning':'medium','output_token_cap':cap,'input_bound_bytes_plus_framing':bound,'call_cost_upper_bound_including_possible_cache_write':maximum,'budget_usd':5,'reference_answers_disclosed':False,'method':'one model-authored repair with runtime feedback, mechanical exact replacement only','source_sha256':hashlib.sha256(source.encode()).hexdigest()},indent=2)+'\n')
key=None
for line in (ROOT.parent/'.env.svg_new').read_text().splitlines():
 n,sep,v=line.strip().removeprefix('export ').partition('=')
 if sep and n=='OPENAI_API_KEY_SVG_NEW':key=v.strip().strip('\"').strip("'")
assert key
(OUT/'dispatch.json').write_text(json.dumps({'started':time.time()})+'\n');start=time.time();r={}
def global_timeout(signum,frame):raise TimeoutError('API global deadline exceeded')
signal.signal(signal.SIGALRM,global_timeout);signal.alarm(360)
try:
 req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=600) as response:raw=json.load(response)
 (OUT/'response.json').write_text(json.dumps(raw,indent=2)+'\n');c=raw['choices'][0];txt=c['message'].get('content') or '';(OUT/'response.txt').write_text(txt)
 u=raw.get('usage') or {};det=u.get('prompt_tokens_details') or {};cached=det.get('cached_tokens',0) or 0;writes=det.get('cache_write_tokens',0) or 0
 cost=((u.get('prompt_tokens',0)-cached)*12.5+cached+writes*12.5+u.get('completion_tokens',0)*50)/1e6
 r.update(status='completed',model=raw.get('model'),usage=u,cost_usd_conservative=cost,finish_reason=c['finish_reason'])
 if c['finish_reason']=='stop':
  txt=txt.strip()
  if txt.startswith('```') and txt.endswith('```'):txt='\n'.join(txt.splitlines()[1:-1])
  patch=json.loads(txt);assert isinstance(patch['edits'],list) and 0<len(patch['edits'])<=30
  repaired=source
  for edit in patch['edits']:
   assert edit['old'] and repaired.count(edit['old'])==1,'Replacement not unique or absent'
   repaired=repaired.replace(edit['old'],edit['new'],1)
  ast.parse(repaired);(OUT/'submission').mkdir(exist_ok=True);(OUT/'submission/main.py').write_text(repaired)
  (OUT/'model-patch.json').write_text(json.dumps(patch,indent=2)+'\n');r.update(patch_applied=True,repaired_sha256=hashlib.sha256(repaired.encode()).hexdigest())
except urllib.error.HTTPError as e:r.update(status='api_error',http_status=e.code,error=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',e.read().decode(errors='replace').replace(key,'[REDACTED]'))[:500])
except Exception as e:r.update(status='repair_or_client_error',error_type=type(e).__name__,error=str(e)[:150])
signal.alarm(0)
r['elapsed_seconds']=round(time.time()-start,1);(OUT/'generation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
