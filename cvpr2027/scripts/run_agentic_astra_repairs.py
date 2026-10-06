"""One bounded Astra repair for frozen verifier rejections; references never enter requests."""
import argparse,json,os,time,urllib.request,urllib.error
from pathlib import Path
from agentic_cad_policy import ACTIONS
from prepare_agentic_cad_holdout import observe
ROOT=Path(__file__).resolve().parents[1]
SYSTEM='''Edit mechanical CAD. Return only a JSON object {"edits":[{"start":0,"delete":0,"insert":["replacement line"]}]}. Indices address zero-based ORIGINAL source lines; operations must be ordered, nonoverlapping and in bounds. Satisfy the instruction and preserve unrelated features. Reconsider the previous candidate using verifier feedback; the verifier can be wrong. Do not claim verification or invent physical results.'''

def main():
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--decisions',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--budget',type=float,default=15);a=p.parse_args()
 key=os.environ['OPENAI_API_KEY'];a.out.mkdir(parents=True,exist_ok=True)
 rows={r['id']:r for r in map(json.loads,a.data.read_text().splitlines())}
 decisions=list(map(json.loads,a.decisions.read_text().splitlines()))
 spent=sum(json.loads(p.read_text()).get('estimated_cost_usd',0) for p in a.out.glob('*/result.json'))
 for d in decisions:
  if d['accepted']:continue
  row=rows[d['id']];out=a.out/row['id'][:16];out.mkdir(exist_ok=True)
  if (out/'result.json').exists():continue
  feedback=[dict(tool=ACTIONS[action],result=row['tools'][ACTIONS[action]]) for _,action in d['trace'] if action<2]
  body=dict(instruction=row['instruction'],original_source=row['code'],previous_candidate=row['candidate'],verifier_verdict='reject; request repair',observations=feedback)
  request_body=dict(model='gpt-6-astra',messages=[dict(role='system',content=SYSTEM),dict(role='user',content=json.dumps(body))],reasoning_effort='low',max_completion_tokens=2500,store=False)
  # Conservative byte-count input bound plus max output allowance, at the repository's list-price estimate.
  worst=(len(json.dumps(request_body).encode())*10+2500*50)/1e6
  if spent+worst>a.budget:print('BUDGET_STOP',flush=True);break
  (out/'request.json').write_text(json.dumps(request_body,indent=2)+'\n')
  record=dict(id=row['id'],status='started',estimated_cost_usd=worst,cost_uncertain=True);(out/'result.json').write_text(json.dumps(record)+'\n')
  start=time.monotonic()
  try:
   req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=json.dumps(request_body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
   with urllib.request.urlopen(req,timeout=240) as response:raw=json.load(response)
   text=raw['choices'][0]['message'].get('content') or '';usage=raw.get('usage',{})
   cost=(usage.get('prompt_tokens',0)*10+usage.get('completion_tokens',0)*50)/1e6;spent+=cost
   (out/'response.txt').write_text(text)
   record.update(status='completed',usage=usage,estimated_cost_usd=cost,cost_uncertain=False,finish_reason=raw['choices'][0].get('finish_reason'),response_id=raw.get('id'),model=raw.get('model'))
   tools=observe(row,text)
   feature=dict(id=row['id'],category=row['category'],code=row['code'],instruction=row['instruction'],candidate=text,tools=tools)
   (out/'feature.json').write_text(json.dumps(feature)+'\n')
  except urllib.error.HTTPError as e:record.update(status='api_error',http_status=e.code) # no credential-bearing response body logged
  except Exception as e:record.update(status='client_error',error_type=type(e).__name__)
  if record.get('cost_uncertain'):spent+=worst
  record['seconds']=time.monotonic()-start;(out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
  print(row['id'][:12],record['status'],round(spent,4),flush=True)
  if record.get('http_status') in (401,403,429):break
 features=[json.loads(p.read_text()) for p in sorted(a.out.glob('*/feature.json'))]
 (a.out/'repair-features.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in features))
 print(json.dumps({'repairs_completed':len(features),'estimated_cost_usd':spent}),flush=True)
if __name__=='__main__':main()
