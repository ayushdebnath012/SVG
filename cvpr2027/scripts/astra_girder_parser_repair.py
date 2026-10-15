"""One model-authored parser repair, without reference answer or manual code repair."""
from pathlib import Path
import ast,json,time,urllib.request,urllib.error,re,hashlib
ROOT=Path(__file__).resolve().parents[1];PREV=ROOT/'runs/astra-hard-single-shot-20261015';OUT=ROOT/'runs/astra-girder-repair-20261015';OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'dispatch.json').exists():raise SystemExit('Already dispatched; no retry')
source=(PREV/'submission/main.py').read_text();tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='eigenvalues');func='\n'.join(source.splitlines()[node.lineno-1:node.end_lineno])
raw=(PREV/'replay/outputs/level_0/buckle.dat').read_text()
system='Return only Python code for one replacement function named eigenvalues(path). Available globals: Path, re, np. No markdown. This is a repair to your previously submitted solver script.'
prompt='The solver finished, but this parser raises No buckling factors found. Fix only the parser using the actual native output below. Preserve the function signature and return a numpy array of all factors, including negative factors if present. Do not hardcode the supplied sample numbers.\nCURRENT FUNCTION:\n'+func+'\nACTUAL OUTPUT:\n'+raw
payload={'model':'gpt-6-astra','messages':[{'role':'system','content':system},{'role':'user','content':prompt}],'reasoning_effort':'medium','max_completion_tokens':1800,'store':False}
r0=json.loads((PREV/'generation.json').read_text());r1=json.loads((ROOT/'runs/astra-challenge-diagnostic-20261015/result.json').read_text());spent=r0['cost_usd_including_cache_write_upper_bound']+r1['cost_usd_conservative'];bound=len((system+prompt).encode())+4096;maximum=2*bound*12.5/1e6+1800*50/1e6;assert spent+maximum<=.75,(spent,maximum)
(OUT/'protocol.json').write_text(json.dumps({'model':'gpt-6-astra','reasoning_effort':'medium','scope':'parser-only model-authored repair; unchanged solver physics','previous_spend_upper_bound':spent,'call_cost_upper_bound_including_possible_cache_write':maximum,'prior_attempt':str(PREV),'max_calls':1,'reference_answers_provided':False},indent=2)+'\n');(OUT/'request.json').write_text(json.dumps(payload,indent=2)+'\n')
key=None
for line in (ROOT.parent/'.env.svg_new').read_text().splitlines():
 n,sep,v=line.strip().removeprefix('export ').partition('=')
 if sep and n=='OPENAI_API_KEY_SVG_NEW':key=v.strip().strip('\"').strip("'")
assert key
(OUT/'dispatch.json').write_text(json.dumps({'started':time.time()})+'\n');start=time.time();result={}
try:
 req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=600) as response:rawresponse=json.load(response)
 (OUT/'response.json').write_text(json.dumps(rawresponse,indent=2)+'\n');c=rawresponse['choices'][0];text=c['message'].get('content') or '';(OUT/'response.txt').write_text(text)
 u=rawresponse.get('usage') or {};details=u.get('prompt_tokens_details') or {};cached=details.get('cached_tokens',0) or 0;writes=details.get('cache_write_tokens',0) or 0;cost=((u.get('prompt_tokens',0)-cached)*12.5+cached+writes*12.5+u.get('completion_tokens',0)*50)/1e6
 result.update(status='completed',model=rawresponse.get('model'),usage=u,cost_usd_upper_bound=cost,finish_reason=c['finish_reason'])
 code=text.strip()
 if code.startswith('```') and code.endswith('```'):code='\n'.join(code.splitlines()[1:-1])
 parsed=ast.parse(code);assert len(parsed.body)==1 and isinstance(parsed.body[0],ast.FunctionDef) and parsed.body[0].name=='eigenvalues','Response must define exactly one function'
 lines=source.splitlines();patched='\n'.join(lines[:node.lineno-1])+ '\n'+code+'\n'+'\n'.join(lines[node.end_lineno:])+'\n';ast.parse(patched)
 (OUT/'submission').mkdir(exist_ok=True);(OUT/'submission/main.py').write_text(patched)
 result.update(patch_applied=True,original_sha256=hashlib.sha256(source.encode()).hexdigest(),repaired_sha256=hashlib.sha256(patched.encode()).hexdigest())
except urllib.error.HTTPError as e:result.update(status='api_error',http_status=e.code,error=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',e.read().decode(errors='replace').replace(key,'[REDACTED]'))[:500])
except Exception as e:result.update(status='repair_or_client_error',error_type=type(e).__name__)
result['elapsed_seconds']=round(time.time()-start,1);(OUT/'generation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
