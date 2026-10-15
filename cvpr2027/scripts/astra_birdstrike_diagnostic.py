"""One source-deck interpretation diagnostic. No FEM capability score or automatic retry."""
from pathlib import Path
import json,hashlib,time,urllib.request,urllib.error,re,os
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/astra-challenge-diagnostic-20261015';OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'dispatch.json').exists():raise SystemExit('Prior dispatch exists; no retry.')
src=ROOT/'data/web-cad-fem-composite-dynamics/pydpf-composites/lsdyna_bird_strike/input.k'
lines=src.read_text().splitlines()
def block(keyword):
 i=lines.index(keyword);j=i+1
 while j<len(lines) and not lines[j].startswith('*'):j+=1
 return '\n'.join(lines[i:j])
excerpt='\n\n'.join(block(k) for k in ['*CONTROL_TERMINATION','*INITIAL_VELOCITY_GENERATION','*DATABASE_EXTENT_BINARY','*MAT_NULL','*EOS_GRUNEISEN','*PART'])
system='You are auditing a published LS-DYNA composite-wing bird-strike setup. Read the provided original deck exactly. Return one JSON object, no markdown. No solver or web tools are available.'
prompt='''This is an interpretation diagnostic, not a request to invent FEM results. The excerpt is from the original source input.k. A downstream parser emitted warnings about a shell variable count mismatch (260 versus 314) and plastic-strain reshape failure. Its array named node_displacement equals the original node_coordinates in the initial state. No units card or coordinate-system definition is included in this excerpt.
Return JSON with keys:
end_time_raw, velocity_raw_xyz (list), velocity_coordinate_system_id, velocity_global_direction_verified (boolean), velocity_m_per_s_verified (boolean), maxint, neips, bird_material_id, bird_eos_id, bird_density_raw, bird_is_rigid (boolean), trust_parser_ply_stresses (boolean), initial_array_is_zero_displacement (boolean), certify_wing_survives_from_this_evidence (boolean), explanation (under 200 words).
Do not infer physical units or global velocity orientation without sufficient source evidence. Judge whether the listed parser fields support a certified survival claim.
ORIGINAL DECK EXCERPT:
'''+excerpt
payload={'model':'gpt-6-astra','messages':[{'role':'system','content':system},{'role':'user','content':prompt}],'reasoning_effort':'medium','max_completion_tokens':10000,'store':False}
# Conservative ASCII byte bound plus framing reserve; price ceiling from official model page.
input_bound=len((system+prompt).encode())+4096
ceiling=input_bound*12.5/1e6+10000*50/1e6
assert ceiling<0.75,(input_bound,ceiling)
protocol={'task_id':'CH-COMPOSITE-LSDYNA_BIRD_STRIKE','scope':'source_deck_interpretation_only','scored_forward_FEM':False,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'budget_usd':0.75,'input_token_upper_bound_with_reserve':input_bound,'max_output_tokens':10000,'conservative_maximum_cost_usd':ceiling,'api_calls_max':1,'tools':[],'units_verified':False}
(OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');(OUT/'request.json').write_text(json.dumps(payload,indent=2)+'\n')
# Credentials are read only from the explicitly configured local SVG_NEW file and never saved in run artifacts.
key=None
for line in (ROOT.parent/'.env.svg_new').read_text().splitlines():
 n,sep,v=line.strip().removeprefix('export ').partition('=')
 if sep and n=='OPENAI_API_KEY_SVG_NEW':key=v.strip().strip('\"').strip("'")
assert key,'SVG_NEW key unavailable'
(OUT/'dispatch.json').write_text(json.dumps({'started':time.time(),'one_request_only':True})+'\n')
r={'status':'started'};start=time.time()
try:
 req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=600) as resp:raw=json.load(resp)
 (OUT/'response.json').write_text(json.dumps(raw,indent=2)+'\n');c=raw['choices'][0];txt=c['message'].get('content') or '';(OUT/'response.txt').write_text(txt)
 u=raw.get('usage') or {};cached=(u.get('prompt_tokens_details') or {}).get('cached_tokens',0) or 0
 cost=((u.get('prompt_tokens',0)-cached)*12.5+cached+u.get('completion_tokens',0)*50)/1e6
 r.update(status='completed',model=raw.get('model'),usage=u,cost_usd_conservative=cost,finish_reason=c['finish_reason'])
 try:
  ans=json.loads(txt);truth={'end_time_raw':0.01,'velocity_raw_xyz':[125000,0,0],'velocity_coordinate_system_id':41,'velocity_global_direction_verified':False,'velocity_m_per_s_verified':False,'maxint':10,'neips':16,'bird_material_id':6,'bird_eos_id':6,'bird_density_raw':1e-9,'bird_is_rigid':False,'trust_parser_ply_stresses':False,'initial_array_is_zero_displacement':False,'certify_wing_survives_from_this_evidence':False}
  # The excerpt includes the first PART (stiffener), not the bird PART.
  # Exclude bird-linkage fields rather than punish missing evidence.
  for k in ['bird_material_id','bird_eos_id','bird_density_raw','bird_is_rigid']:truth.pop(k)
  checks={k:ans.get(k)==v for k,v in truth.items()}
  (OUT/'diagnostic-grade.json').write_text(json.dumps({'scope':'deck interpretation, not forward FEM','expected':truth,'answer':ans,'checks':checks,'passed':all(checks.values()),'source_reading_checks':len(checks)},indent=2)+'\n')
  r.update(diagnostic_passed=all(checks.values()),correct_checks=sum(checks.values()),total_checks=len(checks))
 except Exception as e:r.update(diagnostic_passed=False,parse_error=type(e).__name__)
except urllib.error.HTTPError as e:
 body=e.read().decode(errors='replace').replace(key,'[REDACTED]');body=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',body)
 r.update(status='api_error',http_status=e.code,error=body[:700],capability_failure=False)
except Exception as e:r.update(status='client_error',error_type=type(e).__name__,capability_failure=False)
r['elapsed_seconds']=round(time.time()-start,1);(OUT/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
