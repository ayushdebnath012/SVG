"""Four first-attempt, source-assisted CAD/FEM generations; no hand-written candidate geometry."""
import base64
import concurrent.futures
import hashlib
import html
import json
from pathlib import Path
import re
import time
import sys
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/fem-open-model-pilot-20261010'

def main():
    raise SystemExit('Retired leakage-prone pilot: it sends full tutorials including answers and omits dependencies. Use the isolated packages documented in data/femcad-hard-v1/input-packaging-report.md. No request was sent.')
    hf = '--hf' in sys.argv
    moonshot = '--moonshot' in sys.argv
    tinker = '--tinker' in sys.argv
    out = OUT / 'huggingface' if hf else OUT
    if moonshot:out = OUT / 'moonshot-direct'
    if tinker:out = OUT / 'tinker-direct'
    if '--available' in sys.argv:out = out / 'available-models'
    if '--low' in sys.argv:out = out / 'low-reasoning'
    if '--nothink' in sys.argv:out = out / 'non-thinking'
    keys = {}
    for line in (ROOT.parent / '.env').read_text().splitlines():
        m = re.match(r'^\s*(?:export\s+)?(\w+)\s*=\s*(.*)$', line)
        if m:
            keys[m[1]] = m[2].strip().strip('\"\'')
    data = json.loads((ROOT / 'data/femcad-hard-v1/advanced-source-studies.json').read_text())
    out.mkdir(parents=True, exist_ok=True)
    if tinker:
        keys['TINKER_API_KEY']=sys.stdin.readline().strip()
        if not keys['TINKER_API_KEY']:raise ValueError('Missing Tinker key on standard input')
    if moonshot:
        keys['MOONSHOT_API_KEY'] = sys.stdin.readline().strip()
        if not keys['MOONSHOT_API_KEY']:raise ValueError('Missing key on standard input')
        inventory = requests.get('https://api.moonshot.ai/v1/models',
             headers={'Authorization':'Bearer '+keys['MOONSHOT_API_KEY']},timeout=30)
        check={'provider':'Moonshot official API','http_status':inventory.status_code}
        if inventory.ok:
            check['models']=[x['id'] for x in inventory.json().get('data',[])]
        else:
            try:
                error=inventory.json().get('error',{})
                message=str(error.get('message','') if isinstance(error,dict) else error)
                for secret in keys.values():
                    if secret:message=message.replace(secret,'[REDACTED]')
                check['message']=message[:500]
            except ValueError:pass
        (out/'access-check.json').write_text(json.dumps(check,indent=2)+'\n')
        print(json.dumps(check),flush=True)
        if not inventory.ok:return
        if '--available' not in sys.argv and 'kimi-k3' not in check.get('models',[]):
            probe=requests.post('https://api.moonshot.ai/v1/chat/completions',
                headers={'Authorization':'Bearer '+keys['MOONSHOT_API_KEY']},
                json={'model':'kimi-k3','messages':[{'role':'user','content':'Reply READY.'}],
                      'reasoning_effort':'low','max_completion_tokens':32},timeout=30)
            result={'requested_model':'kimi-k3','http_status':probe.status_code}
            if not probe.ok:
                try:
                    error=probe.json().get('error',{})
                    message=str(error.get('message','') if isinstance(error,dict) else error)
                    for secret in keys.values():
                        if secret:message=message.replace(secret,'[REDACTED]')
                    result['message']=message[:500]
                except ValueError:pass
            (out/'k3-access-probe.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps(result),flush=True)
            if not probe.ok:return
    def one(model, task_id):
        task = next(x for x in data['studies'] if x['id'] == task_id)
        page = next(x for x in data['pages'] if x['url'] == task['source_url'])
        source = html.unescape(re.sub('<[^>]+>', ' ', (ROOT / page['local']).read_text()))
        source = re.sub(r'\s+', ' ', source)
        prompt = ('Reproduce this EXISTING published engineering study. This is a first-attempt evaluation. '
                  'Use the source tutorial and original reference images below; no web retrieval or imported source CAD is available. '
                  'Return one JSON object with keys gmsh_python, fem_python, limitations. '
                  'gmsh_python must be a complete runnable Python script using only gmsh, numpy, math, json, pathlib. '
                  'Build the undeformed source geometry with Gmsh OCC, export part.step and mesh.msh. '
                  'Use the source dimensional formulation (2D surface mesh or 3D volume mesh), define physical groups for materials and boundaries. '
                  'fem_python must implement the source FEM analysis or prepare a runnable input for an identified solver, '
                  'preserving nonlinear material, contact, loading and cavity physics. State the solver dependency. '
                  'Do not replace nonlinear contact with linear elasticity, invent missing source dimensions, or fabricate results. '
                  'If exact reproduction is impossible with the supplied evidence, explicitly state missing information in limitations. '
                  'All files must be relative to the current directory. No network, subprocess, shell, environment access or arbitrary external file reads. '
                  'Do not launch a GUI. End Gmsh with gmsh.finalize().\n'
                  + json.dumps({k:task[k] for k in ['id','title','model_kind','analysis','outputs','source_url']})
                  + '\nSOURCE TUTORIAL:\n' + source)
        content = [{'type':'text','text':prompt}]
        for fig in task['figures']:
            b = (ROOT / fig['local']).read_bytes()
            content.append({'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(b).decode()}})
        remote_model = {'kimi-k3':'moonshotai/Kimi-K3','inkling':'thinkingmachines/Inkling'}[model] if hf else model
        if tinker:remote_model='thinkingmachines/Inkling'
        request = dict(model=remote_model,messages=[{'role':'user','content':content}],max_tokens=8000)
        if '--low' in sys.argv:request.update(reasoning_effort='low',max_tokens=24000)
        if '--nothink' in sys.argv:request.update(thinking={'type':'disabled'},max_tokens=16000)
        if moonshot:request['max_completion_tokens']=request.pop('max_tokens')
        if tinker:request['separate_reasoning']=True
        folder = out / model / task_id
        folder.mkdir(parents=True,exist_ok=True)
        (folder/'prompt.txt').write_text(prompt)
        meta = {'requested_model':model,'task_id':task_id,'source_url':task['source_url'],
                'protocol':'first attempt; full tutorial text and original image; no repair',
                'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'status':'dispatching'}
        meta['max_tokens']=request.get('max_tokens',request.get('max_completion_tokens'))
        meta['reasoning_effort']=request.get('reasoning_effort','provider default')
        meta['thinking']=request.get('thinking','provider default')
        started = time.monotonic()
        try:
            endpoint = 'https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1/chat/completions' if tinker else 'https://api.moonshot.ai/v1/chat/completions' if moonshot else 'https://router.huggingface.co/v1/chat/completions' if hf else 'https://api.experientiallabs.ai/v1/chat/completions'
            resp = requests.post(endpoint,json=request,
                                 headers={'Authorization':'Bearer '+keys['TINKER_API_KEY' if tinker else 'MOONSHOT_API_KEY' if moonshot else 'HF_TOKEN' if hf else 'EXPLABS_API_KEY']},timeout=240)
            meta['http_status'] = resp.status_code
            if not resp.ok:
                meta['status']='provider_rejected'
                try:
                    error_body=resp.json()
                    err=error_body.get('error',error_body.get('detail',{}))
                    safe=str(err.get('message','') if isinstance(err,dict) else err)
                    for secret in keys.values():
                        if secret:safe=safe.replace(secret,'[REDACTED]')
                    meta['provider_message']=safe[:600]
                except ValueError:pass
                return meta
            reply = resp.json()
            (folder/'response.json').write_text(json.dumps(reply,indent=2))
            meta.update(returned_model=reply.get('model'),usage=reply.get('usage'),
                        finish_reason=reply['choices'][0].get('finish_reason'))
            answer = reply['choices'][0]['message'].get('content') or ''
            (folder/'answer.txt').write_text(answer)
            if meta['finish_reason']=='length':
                meta['status']='token_limit_inconclusive'
                return meta
            clean = answer.strip()
            if clean.startswith('```'):clean='\n'.join(clean.splitlines()[1:-1])
            candidate = json.loads(clean)
            (folder/'candidate.json').write_text(json.dumps(candidate,indent=2))
            for key, name in [('gmsh_python','geometry.py'),('fem_python','fem.py')]:
                code = candidate.get(key)
                if isinstance(code,str) and code.strip(): (folder/name).write_text(code)
            meta['status']='generated'
        except Exception as exc:
            meta.update(status='error',error_type=type(exc).__name__)
        finally:
            meta['elapsed_seconds']=round(time.monotonic()-started,2)
            (folder/'attempt.json').write_text(json.dumps(meta,indent=2))
            print(json.dumps(meta),flush=True)
        return meta
    models = ['kimi-k3'] if moonshot else ['deepseek-v4.1-flash'] if '--deepseek' in sys.argv else ['kimi-k3','inkling']
    if tinker:models=['inkling']
    if moonshot and '--available' in sys.argv:models=[m for m in check['models'] if m in ['kimi-k2.6','kimi-k2.7-code']]
    jobs=[(m,t) for m in models for t in ['FEMCAD-ADV-011','FEMCAD-ADV-001']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda x:one(*x),jobs))
    (out/('deepseek-generation-summary.json' if '--deepseek' in sys.argv else 'generation-summary.json')).write_text(json.dumps(results,indent=2))

if __name__ == '__main__':main()
