"""Run budget-bounded Astra MCTS with remote frozen-verifier inference.

References are absent from search/API/RPC inputs. They are used by a separate
post-selection scoring script. Authentication stays in process memory.
"""
import argparse,getpass,hashlib,json,math,os,random,sys,threading,time
import urllib.request,urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sklearn.linear_model import LogisticRegression
from mcts_cad_search import Search
from prepare_agentic_cad_holdout import observe

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'experiments/agentic-verifier-grpo-20261006'
SYSTEM='''Edit mechanical CAD and preserve unrelated features. Return only a JSON object {"edits":[{"start":0,"delete":0,"insert":["replacement line"]}]}. Indices always address zero-based ORIGINAL source lines, even when revising a previous candidate. Operations must be ordered, nonoverlapping and in bounds. Use the request and target-free observations to reconsider the current candidate; tools and the verifier can be wrong. Produce an alternative complete patch. Do not invent verification results.'''

def load(path):return [json.loads(l) for l in path.read_text().splitlines()]
def logit(p):return math.log(max(1e-6,min(1-1e-6,p))/max(1e-6,1-min(1-1e-6,p)))
def numbers(tools):
    checks=tools.get('numbers',[])
    return sum(bool(c['ok']) for c in checks)/len(checks) if checks else .5
def whitelist(row):return {k:row[k] for k in ['code','instruction','candidate','tools']}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--budget',type=float,default=5);ap.add_argument('--calls-per-task',type=int,default=4)
    ap.add_argument('--prompt-api-key',action='store_true')
    ap.add_argument('--calibration',type=Path)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if (a.out/'manifest.json').exists():raise SystemExit('Use a fresh experiment directory; completed calls are not silently retried.')
    key=getpass.getpass('Astra API key: ') if a.prompt_api_key else None
    # Same Python version as the existing isolated SSH transport environment.
    sys.path.insert(0,str(ROOT/'tmp/agentic-transport/lib/python3.9/site-packages'))
    import paramiko
    password=getpass.getpass('Server password: ')
    client=paramiko.SSHClient();client.load_system_host_keys();client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect('10.71.9.40',username='trishita',password=password,look_for_keys=False,allow_agent=False,timeout=15)
    password=None
    remote='/home/trishita/svg-compute/agentic-verifier-grpo-20261006'
    command=f'cd {remote}/scripts && CUDA_VISIBLE_DEVICES=1 /home/trishita/miniconda3/envs/engsvg/bin/python -u mcts_verifier_worker.py {remote}/run-v4/adapter'
    stdin,stdout,stderr=client.exec_command(command)
    ready=stdout.readline()
    if not ready or not json.loads(ready).get('ready'):
        raise RuntimeError('Verifier worker did not start: '+stderr.read().decode()[-1200:])
    print('FROZEN_VERIFIER_READY',flush=True)
    rpc_lock=threading.Lock()
    def evaluate(rows):
        with rpc_lock:
            stdin.write(json.dumps({'rows':[whitelist(r) for r in rows]})+'\n');stdin.flush()
            line=stdout.readline()
            if not line:raise RuntimeError('Verifier worker disconnected')
            return json.loads(line)['results']
    try:
        dev=load(OLD/'dev.jsonl')
        if a.calibration:
            calibration=json.loads(a.calibration.read_text())
            assert calibration['n']==len(dev) and len(calibration['raw'])==len(dev)
            weight=calibration['numeric_weight'];threshold=calibration['threshold']
        else:
            dev=load(OLD/'dev.jsonl');raw=[]
            for i in range(0,len(dev),8):
                raw.extend(evaluate(dev[i:i+8]));print('CALIBRATION',min(i+8,len(dev)),'/',len(dev),flush=True)
            if any('error_type' in r for r in raw):raise RuntimeError('Development verifier evaluation failed')
            y=np.array([bool(r['label']) for r in dev]);x=np.array([[logit(r['p_accept'])] for r in raw])
            platt=LogisticRegression(C=1,solver='lbfgs',random_state=17).fit(x,y)
            calibrated=platt.predict_proba(x)[:,1]
            gates=np.array([bool(r['tools']['execute'].get('gates')) for r in dev])
            nums=np.array([numbers(r['tools']) for r in dev]);best=None
            for weight in [0.,.1,.2]:
                scores=(1-weight)*calibrated+weight*nums
                thresholds=sorted(set([0.,1.]+list(scores)))
                for threshold in thresholds:
                    pred=gates&(scores>=threshold)
                    bal=.5*(np.mean(pred[y])+np.mean(~pred[~y]))
                    # Deterministic ties prefer lower numeric weight, then fewer replacements.
                    ranking_key=(float(bal),-weight,threshold)
                    if best is None or ranking_key>best[0]:best=(ranking_key,weight,float(threshold),pred)
            _,weight,threshold,pred=best
            calibration=dict(method='L2 Platt logistic fit on component-disjoint development data',
                             coefficient=float(platt.coef_[0,0]),intercept=float(platt.intercept_[0]),
                             numeric_weight=weight,threshold=threshold,
                             development_in_sample_balanced_accuracy=best[0][0],
                             development_in_sample_accuracy=float(np.mean(pred==y)),
                             n=len(dev),raw=raw)
        (a.out/'calibration.json').write_text(json.dumps(calibration,indent=2)+'\n')
        print('CALIBRATION_FROZEN',json.dumps({k:v for k,v in calibration.items() if k!='raw'}),flush=True)
        def value(p,tools,depth=0):
            z=calibration['coefficient']*logit(p)+calibration['intercept']
            prob=1/(1+math.exp(-max(-50,min(50,z))))
            score=(1-weight)*prob+weight*numbers(tools)
            return score-.005*depth,bool(tools['execute'].get('gates')) and score>=threshold,prob
        # Load only fields needed for search. The label/reference fields are dropped.
        data={r['id']:{'id':r['id'],'category':r['category'],**whitelist(r)} for r in load(OLD/'heldout.jsonl')}
        decisions={r['id']:r for r in load(OLD/'grpo-heldout-decisions.jsonl')}
        assert len(data)==124 and set(data)==set(decisions)
        chosen=[id for id in data if not decisions[id]['accepted']]
        random.Random(17).shuffle(chosen)
        searches={}
        for id,row in data.items():
            p=decisions[id]['probabilities'][3];raw_p=p[2]/(p[2]+p[3])
            score,eligible,prob=value(raw_p,row['tools'])
            searches[id]=Search(row['candidate'],score,eligible,width=2,depth=2,exploration=.7)
            searches[id].root.metadata={'tools':row['tools'],'raw_p_accept':raw_p,'calibrated_p':prob,'origin':'saved_initial_Astra'}
        manifest=dict(algorithm='MCTS with UCT over complete original-index CAD patches',seed=17,
                      all_tasks=124,search_tasks=len(chosen),gating='same 60 initial verifier rejections as completed pilot',
                      max_new_api_calls_per_search_task=a.calls_per_task,width=2,max_depth=2,exploration=.7,
                      node_depth_penalty=.005,api_budget_usd=a.budget,api_workers=3,
                      model='gpt-6-astra',reasoning_effort='low',max_completion_tokens=2500,
                      price_estimate_per_million={'input':10,'output':50},
                      verifier_adapter=remote+'/run-v4/adapter',calibration_sha256=hashlib.sha256((a.out/'calibration.json').read_bytes()).hexdigest(),
                      heldout_features_sha256=hashlib.sha256((OLD/'heldout.jsonl').read_bytes()).hexdigest(),
                      tool_source_sha256=hashlib.sha256((ROOT/'scripts/cad_edit_verifier.py').read_bytes()).hexdigest(),
                      references_in_search=False,failed_api_attempts_retried=False,
                      rollout='one generated candidate, live target-free CAD tools, frozen verifier proxy; terminal values cached')
        (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        (a.out/'heldout-target-free.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in data.values()))
        key=key or os.environ.get('OPENAI_API_KEY')
        if not key:
            for line in (ROOT.parent/'.env').read_text().splitlines():
                if line.startswith('OPENAI_API_KEY='):key=line.split('=',1)[1].strip().strip('\"\'')
        if not key:raise RuntimeError('API credential is not configured')
        if not isinstance(key,str):raise TypeError('API credential must be a string before any request is sent')
        spent=0.;reserved=0.;budget_lock=threading.Lock();stop=threading.Event()
        started=time.monotonic()
        def one(id):
            nonlocal spent,reserved
            search=searches[id];row=data[id];parent=search.expansion_parent()
            if parent is None:return
            index=len(search.nodes)
            call_root=a.out/'calls'/id[:16]
            attempt=1+len(list(call_root.glob('*/result.json')))
            folder=call_root/str(attempt);folder.mkdir(parents=True,exist_ok=True)
            body=dict(instruction=row['instruction'],original_source=row['code'],previous_candidate=parent.candidate,
                      observations=parent.metadata['tools'],
                      verifier_proxy_probability=parent.metadata['calibrated_p'],
                      alternatives=[n.candidate for n in parent.children],
                      instruction_to_generator='Find a different minimal edit that satisfies the request. Recheck unrelated features; indices always refer to the original source.')
            request=dict(model='gpt-6-astra',messages=[{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(body)}],reasoning_effort='low',max_completion_tokens=2500,store=False)
            worst=(len(json.dumps(request).encode())*10+2500*50)/1e6
            with budget_lock:
                if stop.is_set() or spent+reserved+worst>a.budget:return
                reserved+=worst
            record=dict(id=id,node=index,attempt=attempt,parent=search.nodes.index(parent),depth=parent.depth+1,
                        status='started',estimated_cost_usd=worst,cost_uncertain=True)
            (folder/'request.json').write_text(json.dumps(request,indent=2)+'\n')
            (folder/'result.json').write_text(json.dumps(record)+'\n')
            actual=worst;api_dispatched=False
            try:
                req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=json.dumps(request).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
                api_dispatched=True
                with urllib.request.urlopen(req,timeout=240) as response:reply=json.load(response)
                candidate=reply['choices'][0]['message'].get('content') or '';usage=reply.get('usage',{})
                actual=(usage.get('prompt_tokens',0)*10+usage.get('completion_tokens',0)*50)/1e6
                record.update(status='completed',usage=usage,estimated_cost_usd=actual,cost_uncertain=False,
                              finish_reason=reply['choices'][0].get('finish_reason'),response_id=reply.get('id'),model=reply.get('model'))
                (folder/'response.txt').write_text(candidate)
                # Deterministic observation cache by exact original source + candidate + tool version.
                signature=hashlib.sha256((row['code']+'\0'+candidate).encode()).hexdigest()
                same=next((n for n in search.nodes if n.metadata.get('observation_key')==signature),None)
                tools=same.metadata['tools'] if same else observe(row,candidate)
                feature={**row,'candidate':candidate,'tools':tools}
                policy=evaluate([feature])[0]
                score,eligible,prob=value(policy['p_accept'],tools,parent.depth+1)
                if policy.get('error_type'):eligible=False
                meta=dict(tools=tools,raw_p_accept=policy['p_accept'],calibrated_p=prob,
                          policy_error=policy.get('error_type'),observation_key=signature,
                          origin=str(folder.relative_to(a.out)),api_node=index)
                search.add(parent,candidate,score,eligible,meta)
                (folder/'feature.json').write_text(json.dumps(feature)+'\n')
                (folder/'policy.json').write_text(json.dumps(policy)+'\n')
            except urllib.error.HTTPError as e:
                record.update(status='api_error',http_status=e.code)
                if e.code in [401,403,429]:stop.set()
            except Exception as e:
                record.update(status='client_error',error_type=type(e).__name__)
                if not api_dispatched:
                    actual=0.;record['cost_uncertain']=False;stop.set()
                if isinstance(e,RuntimeError) and 'worker' in str(e):stop.set()
            finally:
                with budget_lock:reserved-=worst;spent+=actual
                record['estimated_cost_usd']=actual;record['seconds']=time.monotonic()-started
                (folder/'result.json').write_text(json.dumps(record,indent=2)+'\n')
                print('CANDIDATE',id[:10],index,record['status'],'spent',round(spent,4),flush=True)
        for round_index in range(a.calls_per_task):
            if stop.is_set():break
            with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(one,chosen))
            print('ROUND_COMPLETE',round_index+1,'spent',round(spent,4),flush=True)
        selections=[]
        for id,search in searches.items():
            selected=search.selected()
            record=dict(id=id,category=data[id]['category'],prediction=selected.candidate,
                        selected_node=search.nodes.index(selected),selected_depth=selected.depth,
                        nodes=len(search.nodes),simulations=search.simulations,
                        replace_original=selected is not search.root,tree=search.trace())
            selections.append(record)
        (a.out/'selected.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in selections))
        summary=dict(tasks=len(selections),search_tasks=len(chosen),replacements=sum(r['replace_original'] for r in selections),
                     api_attempts=len(list((a.out/'calls').glob('*/*/result.json'))),
                     api_completed=sum(json.loads(p.read_text())['status']=='completed' for p in (a.out/'calls').glob('*/*/result.json')),
                     api_cost_estimate_usd=spent,seconds=time.monotonic()-started,stopped_on_api_error=stop.is_set())
        (a.out/'search-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('SEARCH_COMPLETE',json.dumps(summary),flush=True)
    finally:
        try:stdin.write(json.dumps({'close':True})+'\n');stdin.flush()
        except Exception:pass
        client.close()

if __name__=='__main__':main()
