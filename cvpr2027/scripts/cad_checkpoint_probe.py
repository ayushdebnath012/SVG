"""Extended protocol: one saved-state continuation after a token-limit response.

Original excluded runs are preserved. Fresh confirmations use the same conditional
checkpoint policy, four checker calls total and 32k output tokens per turn.
"""
import argparse,base64,hashlib,json,urllib.request
from pathlib import Path
import cad_serpentine_routing as s
import cad_part_nesting as n
r=s.r
CHECKPOINT='Your preceding response reached its per-turn output allowance. Continue from the saved state. Use the checker on your current best draft to obtain feedback; partial drafts are allowed. Continue using the remaining checker calls, then return final JSON with your best candidate and explain any constraints you could not satisfy. You need not claim success. Return the candidate even if it is imperfect, so its actual geometry can be evaluated.'

def run(kind,out,sample,parent=None,template=None):
    if out.exists():raise ValueError('Fresh output directory required')
    module=s if kind=='serpentine' else n;data=module.DATA;t=json.loads((data/'tasks.json').read_text())['tasks'][0]
    keyname='routes' if kind=='serpentine' else 'placements';grader=s.timed.grade if kind=='serpentine' else n.grade;draw=s.timed.drawing if kind=='serpentine' else n.drawing
    # Use the exact saved initial prompt/tool definition for both discovery and
    # fresh confirmations, rather than reconstructing or changing the task.
    source=parent or template
    if source is None:raise ValueError('Provide a parent run or frozen prompt template')
    initial=json.loads((source/'request-0.json').read_text());system=initial['input'][0]['content'];tool=initial['tools'][0]
    calls=0;continuations=0;usage=[]
    if parent:
        result=json.loads((parent/'result.json').read_text())
        if result['status']!='incomplete_excluded':raise ValueError('Only a token-limited run may be continued')
        files=sorted(parent.glob('request-*.json'),key=lambda p:int(p.stem.split('-')[-1]));last=files[-1];previous=json.loads((parent/last.name.replace('request-','response-')).read_text())
        if previous.get('incomplete_details',{}).get('reason')!='max_output_tokens':raise ValueError('Not a token-limit exclusion')
        messages=json.loads(last.read_text())['input']+previous['output']+[{'role':'user','content':CHECKPOINT}];calls=result['checker_calls'];usage=result['usage'];continuations=1
    else:messages=initial['input']
    rec={'id':t['id'],'sample':sample,'status':'started','parent':str(parent) if parent else None,'usage':list(usage),'inherited_usage_entries':len(usage),'initial_checker_calls':calls}
    protocol={'configuration_id':'high32k-fourchecks-onecheckpoint-v1','kind':kind,'model':'gpt-6-astra','effort':'high','max_output_tokens_per_turn':32000,'max_checker_calls_total':4,'max_token_limit_continuations':1,'checkpoint_message':CHECKPOINT,'initial_prompt_sha256':hashlib.sha256(json.dumps(initial['input'],sort_keys=True).encode()).hexdigest(),'manifest_sha256':hashlib.sha256((data/'tasks.json').read_bytes()).hexdigest(),'source_prompt_run':str(source),'system':system,'tool':tool,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    r.write(out/'protocol.json',protocol);r.write(out/'result.json',rec);key=r.api_key()
    try:
        for turn in range(6):
            payload={'model':'gpt-6-astra','input':messages,'reasoning':{'effort':'high'},'max_output_tokens':32000,'store':False,'include':['reasoning.encrypted_content']}
            if calls<4:payload.update(tools=[tool],parallel_tool_calls=False)
            r.write(out/f'request-{turn}.json',payload);req=urllib.request.Request(r.ENDPOINT,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
            with urllib.request.urlopen(req,timeout=1200) as response:raw=json.load(response)
            r.write(out/f'response-{turn}.json',raw);rec['usage'].append(raw.get('usage',{}));messages.extend(raw['output'])
            if raw['status']!='completed':
                if raw.get('incomplete_details',{}).get('reason')=='max_output_tokens' and continuations<1:
                    continuations+=1;messages.append({'role':'user','content':CHECKPOINT});print('Token limit: one saved-state checkpoint',flush=True);continue
                rec['status']='incomplete_excluded';break
            fc=[v for v in raw['output'] if v['type']=='function_call']
            if fc:
                for c in fc:
                    if calls>=4:raise ValueError('Unexpected excess checker call')
                    result=grader(t,json.loads(c['arguments'])[keyname]);r.write(out/f'checker-total-{calls+1}.json',result);calls+=1;messages.append({'type':'function_call_output','call_id':c['call_id'],'output':json.dumps(result)});print('checker total',calls,'violations',result['violation_count'],flush=True)
            else:
                text=''.join(c['text'] for v in raw['output'] if v['type']=='message' for c in v['content'] if c['type']=='output_text');(out/'final.txt').write_text(text)
                # Accept an unambiguous JSON candidate even with prose/fences.
                decoder=json.JSONDecoder();candidates=[]
                for i,char in enumerate(text):
                    if char!='{':continue
                    try:obj,end=decoder.raw_decode(text[i:])
                    except ValueError:continue
                    if isinstance(obj,dict) and keyname in obj:candidates.append(obj)
                if len(candidates)!=1:raise ValueError('No unambiguous final JSON candidate')
                ans=candidates[0];r.write(out/'answer.json',ans);g=grader(t,ans[keyname]);(out/'output.svg').write_text(draw(t,ans[keyname]));rec.update(status='completed',grade=g);break
        if rec['status']=='started':rec['status']='no_final_excluded'
    except Exception as e:
        rec.update(status='operational_error_excluded',error=str(e).replace(key,'[REDACTED]')[:500])
        if isinstance(e,urllib.error.HTTPError):
            body=e.read().decode(errors='replace').replace(key,'[REDACTED]')[:6000]
            rec['http_status']=e.code
            try:rec['error_response']=json.loads(body)
            except ValueError:rec['error_response']={'message':body}
    rec.update(checker_calls=calls,continuations=continuations);r.write(out/'result.json',rec);print(rec['status'],rec.get('grade',{}).get('pass'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['serpentine','nesting']);p.add_argument('--output',type=Path,required=True);p.add_argument('--sample',type=int,default=1);p.add_argument('--parent',type=Path);p.add_argument('--template',type=Path);a=p.parse_args();run(a.kind,a.output,a.sample,a.parent,a.template)
