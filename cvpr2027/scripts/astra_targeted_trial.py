"""One budget-reserved Astra generation/repair, clean sandbox replay, frozen scoring."""
from pathlib import Path
import argparse, ast, base64, datetime, hashlib, json, os, shutil, signal, subprocess, time
import urllib.request, urllib.error
from cadfem_api_route import load_route, read_credential, budget_status, redact

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT.parent/'cadfem-bench-v1.7'
PY=ROOT/'tmp/cq-env/bin/python'

def save(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')

def call(args):
    route=load_route();ledger=ROOT.parent/route['budget_ledger'];key=read_credential(route)
    task=next(x for x in map(json.loads,(PKG/'candidate/tasks.jsonl').read_text().splitlines()) if x['task_id']==args.task)
    out=ROOT/'runs/astra-targeted-20261016'/args.run
    out.mkdir(parents=True,exist_ok=True)
    if (out/'dispatch.json').exists():raise ValueError('Existing dispatch: no automatic retry')
    asset=PKG/'candidate/tasks'/args.task
    for f in task['inputs']:
        if hashlib.sha256((PKG/'candidate'/f['path']).read_bytes()).hexdigest()!=f['sha256']:
            raise ValueError('Input checksum mismatch')
    system='Solve the CAD+FEM task. Return only a complete runnable Python main.py, no markdown. Never fabricate geometry, fields, convergence or reference results. Your code will execute locally. Do not use recalled published results.'
    text=task['prompt']+'\nRUNTIME: Python cadquery (OCP), gmsh, numpy/scipy, meshio, skfem, and ccx (CalculiX 2.23). No FreeCAD or ANSYS. Read inputs from CADFEM_INPUT_DIR; write into CADFEM_OUTPUT_DIR. No network/evaluator access. Available inputs: '+json.dumps([Path(x['path']).name for x in task['inputs']])+'. 600 seconds, 2 CPU threads, 6000 MB RAM. Use feasible meshes, record honest refinement. main.py is preserved by evaluator. Request all required fields and retain solver logs. Do not hardcode target answers. Use supplied source drawing images for reconstruction, not hidden source CAD.'
    images=[]
    import fitz
    from PIL import Image
    for f in task['inputs']:
        path=PKG/'candidate'/f['path']
        if path.suffix.lower()=='.pdf':
            doc=fitz.open(path)
            for n,page in enumerate(doc):
                text+='\nInput PDF page '+str(n+1)+' extracted text:\n'+page.get_text()
                pix=page.get_pixmap(matrix=fitz.Matrix(1.8,1.8))
                target=out/'input-views'/(path.stem+f'-page-{n+1}.png');target.parent.mkdir(exist_ok=True)
                pix.save(target);images.append(target)
        elif path.suffix.lower() in ['.png','.jpg','.jpeg']:
            target=out/'input-views'/path.name;target.parent.mkdir(exist_ok=True)
            im=Image.open(path).convert('RGB');im.thumbnail((1800,1800));im.save(target);images.append(target)
        elif path.suffix.lower() in ['.json','.csv','.fee']:
            s=path.read_text()
            if len(s)<12000:text+='\nINPUT '+path.name+':\n'+s
    if args.repair:
        prev=Path(args.repair).resolve()
        text+='\nCURRENT_CODE:\n'+(prev/'submission/main.py').read_text()
        for name in ['replay/sandbox.log','replay/outputs/error.json','replay/outputs/solver.log']:
            f=prev/name
            if f.exists():text+='\nEXECUTION FEEDBACK '+name+':\n'+f.read_text(errors='replace')[-5000:]
        if args.feedback:text+='\nEVALUATOR FEEDBACK (reference values hidden):\n'+args.feedback
        text+='\nReturn the entire repaired main.py. No manual changes will be made to your solver.'
    content=[{'type':'text','text':text}]
    for f in images:
        content.append({'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(f.read_bytes()).decode(),'detail':'high'}})
    cap=12000
    # Byte-bound text tokens plus conservative image-token allowance; includes cache writes.
    bound=len((system+text).encode())+1024+len(images)*20000
    reservation=bound*25/1e6+cap*50/1e6
    budget=budget_status(route,reservation)
    payload={'model':route['model'],'messages':[{'role':'system','content':system},{'role':'user','content':content}],
             'reasoning_effort':'medium','max_completion_tokens':cap,'store':False}
    save(out/'request.json',payload)
    save(out/'protocol.json',{'task_id':args.task,'provider':route['provider'],'base_url':route['base_url'],
         'reasoning':'medium','token_cap':cap,'reservation_usd':reservation,'budget':budget,'image_count':len(images),
         'reference_values_sent':False,'repair_of':args.repair,'model_side_tools':False,
         'scope':'Selected/adaptive diagnostic; not an unbiased benchmark success-rate estimate.',
         'source_readiness':task['readiness']})
    # Reserve the maximum before dispatch. Interrupted/unknown calls retain this reservation.
    d=json.loads(ledger.read_text());d['session_cost_upper_bound_usd']+=reservation
    d['hunt_trials'].append({'task_id':args.task,'report':str(out/'README.md'),'status':'api_reserved',
                            'generation':{'cost_usd_conservative':reservation,'cost_status':'reserved_before_dispatch'}})
    save(ledger,d);save(out/'dispatch.json',{'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    start=time.monotonic();generation={'status':'unknown','cost_usd_conservative':reservation,'cost_status':'unknown_usage_reserved_maximum'}
    def deadline(*_):raise TimeoutError('API deadline exceeded; no automatic retry')
    signal.signal(signal.SIGALRM,deadline);signal.alarm(360)
    try:
        req=urllib.request.Request(route['base_url']+'/chat/completions',data=json.dumps(payload).encode(),
                                  headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=360) as response:
            raw=json.load(response)
        save(out/'response.json',raw)
        u=raw.get('usage') or {};details=u.get('prompt_tokens_details') or {}
        cached=details.get('cached_tokens',0) or 0;writes=details.get('cache_write_tokens',details.get('cache_creation_input_tokens',0)) or 0
        if 'prompt_tokens' in u and 'completion_tokens' in u:
            cost=((u['prompt_tokens']-cached)*12.5+cached+writes*12.5+u['completion_tokens']*50)/1e6
            generation.update(cost_usd_conservative=cost,cost_status='usage_based_conservative')
        c=raw['choices'][0];code=(c['message'].get('content') or '').strip()
        (out/'response.txt').write_text(code)
        generation.update(status='completed',model=raw.get('model'),usage=u,finish_reason=c.get('finish_reason'))
        if c.get('finish_reason')=='stop':
            if code.startswith('```') and code.endswith('```'):code='\n'.join(code.splitlines()[1:-1])
            ast.parse(code);(out/'submission').mkdir(exist_ok=True);(out/'submission/main.py').write_text(code+'\n')
            generation['code_sha256']=hashlib.sha256((code+'\n').encode()).hexdigest()
    except urllib.error.HTTPError as e:
        error_text=redact(e.read().decode(errors='replace'),key)
        generation.update(status='api_error',http_status=e.code,error=error_text[:1200])
        try:detail=json.loads(error_text).get('error',{})
        except json.JSONDecodeError:detail={}
        if (detail.get('code')=='credit_balance_exhausted'
                or str(detail.get('message','')).startswith('model_requires_purchase:')):
            generation.update(cost_usd_conservative=0,
                              cost_status='explicit_pre_inference_credit_rejection',
                              reservation_released_usd=reservation)
    except Exception as e:generation.update(status='client_or_code_error',error_type=type(e).__name__,error=redact(str(e),key)[:400])
    finally:signal.alarm(0)
    generation['elapsed_seconds']=time.monotonic()-start;save(out/'generation.json',generation)
    d=json.loads(ledger.read_text());d['session_cost_upper_bound_usd']+=generation['cost_usd_conservative']-reservation
    rec={'task_id':args.task,'report':str(out/'README.md'),'status':'generated','generation':generation,
         'repair_of':args.repair,'protocol':'medium reasoning with source input images, no model-side tools; hidden reference'}
    d['hunt_trials']=[rec if x['report']==rec['report'] else x for x in d['hunt_trials']];save(ledger,d)
    print(json.dumps({'task':args.task,'generation':generation,'accounted_total':d['session_cost_upper_bound_usd']}),flush=True)
    def run(command,log):
        with log.open('w') as stream:return subprocess.run(list(map(str,command)),stdout=stream,stderr=subprocess.STDOUT).returncode
    if not (out/'submission/main.py').exists():
        rec['status']='inconclusive_generation';save(out/'outcome.json',rec);return
    runner=PKG/'evaluator/sandbox_runner.py'
    rc=run([PY,runner,'prepare','--package',PKG,'--job',out/'replay','--task-id',args.task,'--submission',out/'submission','--model-id',route['model'],'--run-id',args.run,'--python',PY],out/'prepare.log')
    if rc:rec['status']='inconclusive_prepare_error'
    else:
        run([PY,runner,'replay','--package',PKG,'--job',out/'replay','--python',PY,'--extra-runtime',ROOT/'tmp/calculix-contact-env','--wall-seconds',600,'--cpu-seconds',600,'--ram-mb',6000],out/'replay.log')
        rec['execution']=json.loads((out/'replay/execution.json').read_text())
        score=out/'scoring';score.mkdir(exist_ok=True)
        shutil.copytree(out/'replay/outputs',score/'submissions'/args.task,dirs_exist_ok=True)
        shutil.copy2(out/'submission/main.py',score/'submissions'/args.task/'main.py')
        for name,src in [('tasks',PKG/'candidate/tasks.jsonl'),('references',PKG/'evaluator/references.jsonl')]:
            (score/(name+'.jsonl')).write_text(''.join(json.dumps(t)+'\n' for t in map(json.loads,src.read_text().splitlines()) if t['task_id']==args.task))
        ref=json.loads((score/'references.jsonl').read_text())
        if ref.get('geometry_check'):
            rel=Path(ref['geometry_check']['reference_step']);(score/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PKG/'evaluator'/rel,score/rel)
        run([PY,PKG/'evaluator/score.py','--refs',score/'references.jsonl','--tasks',score/'tasks.jsonl','--submissions',score/'submissions','--run-id',args.run,'--out',score/'score.json'],out/'score.log')
        rec['status']='awaiting_adjudication'
        if (score/'score.json').exists():rec['score']=json.loads((score/'score.json').read_text())['tasks'][0]
    save(out/'outcome.json',rec)
    d=json.loads(ledger.read_text());d['hunt_trials']=[rec if x['report']==rec['report'] else x for x in d['hunt_trials']];save(ledger,d)
    (out/'README.md').write_text('# '+args.task+' — selected Astra diagnostic\n\nStatus: '+rec['status']+'\n\nSee outcome.json, protocol.json, generation.json, replay/execution.json and scoring/score.json. No automatic API retries. Reference answers hidden. Source stress tolerance is provisional; missing human workflow review is not a model failure.\n')
    print(json.dumps({'status':rec['status'],'score':rec.get('score'),'execution_exit':rec.get('execution',{}).get('exit_code')}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--task',required=True);parser.add_argument('--run',required=True);parser.add_argument('--repair');parser.add_argument('--feedback')
    call(parser.parse_args())
