"""One-shot FEM diagnostic runner: freeze, generate, isolated replay, compare.

Preparation, replay and score do not make API requests. API generation is explicit.
Numeric agreement alone never certifies a CAD/FEM pass. No automatic retries.
"""
from __future__ import annotations
import argparse,base64,hashlib,json,math,os,re,shutil,signal,subprocess,sys,tempfile,time
from pathlib import Path
from urllib import request,error

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'tmp/engineering-fem-v1'
DATA=ROOT/'data/engineering-fem-v1'
DEFAULT_RUNTIME=ROOT/'tmp/fenicsx/env/bin/python'

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def candidate(case,track):
    p=PACK/'candidate-inputs'/track/case
    task=load(p/'task.json')
    for f in task['files']:
        if sha(p/f['path'])!=f['sha256']:raise ValueError('Input hash mismatch: '+f['path'])
    return p,task

def prepare(case,track,out):
    src,task=candidate(case,track)
    if not out.resolve().is_relative_to((ROOT/'tmp').resolve()):raise ValueError('Candidate/source bytes must stay under git-ignored cvpr2027/tmp')
    if out.exists():raise ValueError('Output directory already exists; use a fresh run directory')
    out.mkdir(parents=True);work=out/'workspace';work.mkdir();(work/'home').mkdir();(work/'scratch').mkdir()
    for f in task['files']:shutil.copy2(src/f['path'],work/f['path'])
    system='You are solving an engineering problem using FEM. Return one JSON object with files mapping relative filenames to UTF-8 text. Include main.py and optionally helper files. main.py must execute the CAD/mesh/FEM workflow, not return recalled reference answers. Write the artifacts and numerical outputs requested by task.md. You may read supplied files in the working directory. Available runtime is Python with Gmsh 4.15.2, dolfinx 0.9.0, UFL, PETSc, MPI (single rank), NumPy, SciPy. No FeenoX/COMSOL executable is assumed. Network, source tutorials, project files, other tasks, reference models and labels are inaccessible. Do not attempt to fetch them. Use stdout and solver.log for diagnostics. No package installation. If inputs are inconsistent, report the issue rather than inventing data. No Markdown around the JSON.'
    text=(work/'task.md').read_text()
    for f in task['files']:
        p=work/f['path']
        if p.suffix.lower() in ['.geo','.json'] and p.name!='task.md':text+='\n\nFILE '+p.name+'\n'+p.read_text()
    content=[dict(type='text',text=text)]
    # Only input figures that were manually reviewed at curation time are attached.
    for f in task['files']:
        p=work/f['path']
        if p.suffix.lower() in ['.svg','.png','.jpg']:
            if p.suffix.lower()=='.svg':
                # Cairo in the installed local solver runtime; no vector bytes sent to the model.
                os.environ.setdefault('DYLD_FALLBACK_LIBRARY_PATH',str(ROOT/'tmp/fenicsx/env/lib'))
                import cairosvg
                image=cairosvg.svg2png(url=str(p),output_width=1400,background_color='white')
            else:image=p.read_bytes()
            content.append(dict(type='image_url',image_url=dict(url='data:image/png;base64,'+base64.b64encode(image).decode())))
    messages=[dict(role='system',content=system),dict(role='user',content=content)]
    save(out/'messages.json',messages)
    save(out/'protocol.json',dict(case=case,track=track,mode='one-shot-diagnostic',candidate_input_hash=sha(src/'task.json'),evaluator_contract_hash=sha(PACK/'evaluator-only'/case/'contract.json'),input_files=task['files'],required_outputs=task['required_outputs'],output_units=task['output_units'],status='prepared',joint_pass=None,scored_release=False,limits=['No independent physics/geometry/convergence certification exists yet.','Public-source contamination cannot be excluded.','Input figures are manually reviewed source assets; exact code/source provenance is evaluator-only.']))
    print('PREPARED',case,track,flush=True)

def key(variable):
    if os.environ.get(variable):return os.environ[variable]
    env=ROOT.parent/'.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith(variable+'='):return line.split('=',1)[1].strip().strip('\"\'')
    raise ValueError('Missing environment credential: '+variable)

def materialize(out,text):
    try:obj=json.loads(text)
    except json.JSONDecodeError:
        s=re.sub(r'^```(?:json)?\s*|\s*```$','',text.strip());obj=json.loads(s)
    files=obj.get('files')
    if not isinstance(files,dict) or not isinstance(files.get('main.py'),str) or not files['main.py'].strip():raise ValueError('Expected nonempty files.main.py')
    if len(files)>20:raise ValueError('Too many generated files')
    work=out/'workspace';reserved={f['path'] for f in load(out/'protocol.json')['input_files']}
    checked=[]
    for name,content in files.items():
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or len(p.parts)!=1 or name in reserved or name.startswith('.') or name in ['home','scratch']:raise ValueError('Invalid generated path or attempted input overwrite')
        if not isinstance(content,str) or len(content.encode())>2_000_000:raise ValueError('Invalid generated file contents')
        checked.append((work/name,content))
    for p,content in checked:p.write_text(content)
    save(out/'generated-files.json',[dict(path=p.name,sha256=sha(p)) for p,_ in checked])

def generate(out,provider,model,max_tokens,effort,budget):
    if (out/'attempt.json').exists():raise ValueError('Attempt already recorded; do not overwrite or retry silently')
    preflight=load(DATA/'runtime-preflight.json') if (DATA/'runtime-preflight.json').exists() else {}
    if not preflight.get('passed') or preflight.get('execution',{}).get('runtime_image')!=image_id():raise ValueError('Isolated runtime preflight must pass before a billable FEM attempt')
    messages=load(out/'messages.json');bodies={'openai':dict(model=model,messages=messages,max_completion_tokens=max_tokens,reasoning_effort=effort,store=False),'explabs':dict(model=model,messages=messages,max_tokens=max_tokens)}
    endpoints={'openai':('https://api.openai.com/v1/chat/completions','OPENAI_API_KEY'),'explabs':('https://api.experientiallabs.ai/v1/chat/completions','EXPLABS_API_KEY')}
    endpoint,var=endpoints[provider];credential=key(var);body=bodies[provider]
    # Deliberately restrict priced operation to the verified Astra rates. Adding a
    # new frontier model requires an explicit provider and price configuration.
    if model!='gpt-6-astra':raise ValueError('This priced adapter is configured for gpt-6-astra; add verified rates before another model')
    text_bytes=sum(len(json.dumps(m,ensure_ascii=False).encode()) for m in messages if m['role']=='system')
    images=0
    for m in messages:
        if isinstance(m['content'],list):
            for item in m['content']:
                if item['type']=='text':text_bytes+=len(item['text'].encode())
                else:images+=1
    reservation=((text_bytes+512+images*20000)*12.5+max_tokens*50)/1e6
    if reservation>budget:raise ValueError(f'Worst-case estimated reservation ${reservation:.3f} exceeds per-attempt cap ${budget:.2f}')
    attempt=dict(provider=provider,model=model,reasoning_effort=effort if provider=='openai' else 'provider-default',max_completion_tokens=max_tokens,budget_usd=budget,reservation_usd=reservation,status='started',joint_pass=None)
    save(out/'attempt.json',attempt);save(out/'request.json',body);started=time.monotonic()
    req=request.Request(endpoint,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+credential,'Content-Type':'application/json'})
    try:
        with request.urlopen(req,timeout=900) as response:raw=json.load(response)
        save(out/'response.json',raw);choice=raw['choices'][0];text=choice['message'].get('content') or '';(out/'response.txt').write_text(text)
        usage=raw.get('usage') or {};cached=(usage.get('prompt_tokens_details') or {}).get('cached_tokens',0)
        cost=(max(0,usage.get('prompt_tokens',0)-cached)*10+cached+usage.get('completion_tokens',0)*50)/1e6
        attempt.update(status='generated',finish_reason=choice.get('finish_reason'),usage=usage,estimated_cost_usd=cost,returned_model=raw.get('model'))
        if choice.get('finish_reason')=='length':attempt['status']='truncated'
        elif choice['message'].get('refusal'):attempt['status']='refused'
        else:
            try:materialize(out,text)
            except (ValueError,TypeError) as e:attempt.update(status='invalid_submission',error=str(e))
    except error.HTTPError as e:
        msg=e.read().decode(errors='replace').replace(credential,'[REDACTED]')[:2500]
        attempt.update(status='provider_error',http_status=e.code,error=msg)
    except Exception as e:attempt.update(status='transport_or_client_error',error_type=type(e).__name__,error=str(e).replace(credential,'[REDACTED]')[:1000])
    attempt['wall_seconds']=time.monotonic()-started;save(out/'attempt.json',attempt);print(attempt['status'],flush=True)

DOCKER_IMAGE='engineering-fem-runtime:0.9.0-gmsh4.15.2'

def image_id():
    if not shutil.which('docker'):raise ValueError('Docker unavailable; isolated solver replay is infrastructure-blocked')
    r=subprocess.run(['docker','image','inspect',DOCKER_IMAGE,'--format','{{.Id}}'],capture_output=True,text=True,timeout=30)
    if r.returncode:raise ValueError('Build the documented engineering-fem runtime image before replay')
    value=r.stdout.strip()
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',value):raise ValueError('Invalid Docker image identity')
    return value

def replay(out,runtime,timeout,entrypoint='main.py'):
    work=(out/'workspace').resolve()
    if not (work/entrypoint).is_file():raise ValueError('Generated entrypoint missing')
    try:identity=image_id()
    except ValueError as e:
        evidence=dict(status='infrastructure_blocked',error=str(e),joint_pass=None)
        save(out/'execution.json',evidence);return evidence
    name='engfem-'+hashlib.sha256(str(out.resolve()).encode()).hexdigest()[:20]
    cmd=['docker','run','--rm','--name',name,'--pull=never','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=128','--memory=8g','--memory-swap=8g','--cpus=2','--user',str(os.getuid())+':'+str(os.getgid()),'--mount','type=bind,src='+str(work)+',dst=/work','--tmpfs','/tmp:rw,nosuid,nodev,size=512m','--workdir','/work','--env','OMP_NUM_THREADS=1','--env','OPENBLAS_NUM_THREADS=1','--env','HOME=/tmp','--env','TMPDIR=/tmp',identity,'/work/'+entrypoint]
    started=time.monotonic();p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
    timed_out=False
    try:stdout,_=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out=True
        # Kill only this run's named container; killing the Docker client alone
        # would leave candidate processes running in the daemon.
        subprocess.run(['docker','kill',name],capture_output=True,timeout=20)
        os.killpg(p.pid,signal.SIGKILL);stdout,_=p.communicate()
    (out/'execution.log').write_bytes(stdout)
    evidence=dict(status='timeout' if timed_out else 'executed' if p.returncode==0 else 'execution_error',returncode=p.returncode,wall_seconds=time.monotonic()-started,network='none',runtime_image=identity,entrypoint_sha256=sha(work/entrypoint),joint_pass=None)
    save(out/'execution.json',evidence);return evidence

def compare(contract,results):
    qois=results.get('qois',{});rows=[]
    for ref in contract['qois']:
        key=ref['key'];pred=qois.get(key);row=dict(key=key,unit=ref['unit'],reference_kind=ref['reference_kind'],status='missing')
        if isinstance(pred,dict):value=pred.get('value');unit=pred.get('unit')
        else:value=None;unit=None
        if unit is not None and unit!=ref['unit']:row['status']='unit_mismatch'
        elif isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):row['status']='invalid_or_missing_number'
        elif unit is None:row['status']='missing_unit'
        else:
            absolute=abs(value-ref['value']);relative=absolute/abs(ref['value']) if ref['value']!=0 else None
            row.update(status='compared',prediction=value,reference=ref['value'],absolute_error=absolute,relative_error=relative,relative_bands={str(t):relative<=t if relative is not None else None for t in contract['diagnostic_relative_bands']})
            if 'source_absolute_tolerance' in ref:row['within_source_tolerance']=absolute<=ref['source_absolute_tolerance']
        rows.append(row)
    return dict(status='diagnostic-comparison',qois=rows,joint_pass=None,scored_release=False,physics_verified=False,geometry_verified=False,convergence_verified=False)

def score(out):
    protocol=load(out/'protocol.json');work=out/'workspace';execution=load(out/'execution.json') if (out/'execution.json').exists() else {}
    contract_path=PACK/'evaluator-only'/protocol['case']/'contract.json'
    if sha(contract_path)!=protocol['evaluator_contract_hash']:raise ValueError('Held-out contract changed after inputs were frozen')
    contract=load(contract_path)
    missing=[f for f in protocol['required_outputs'] if not (work/f).is_file() or not (work/f).stat().st_size]
    if not (work/'results.json').exists():result=dict(status='missing_results',joint_pass=None)
    else:
        try:result=compare(contract,load(work/'results.json'))
        except (ValueError,TypeError):result=dict(status='invalid_results',joint_pass=None)
    result.update(case=protocol['case'],track=protocol['track'],execution_status=execution.get('status','not_executed'),missing_required_artifacts=missing,provenance_note='Results alone do not prove a FEM solve; inspect actual replay, field artifacts and refinement logs.')
    if execution.get('status')!='executed':result['status']='not_scored_execution_unverified'
    save(out/'score.json',result);print(result['status'],flush=True)

def selfcheck(out,runtime):
    if out.exists():raise ValueError('Use fresh selfcheck folder')
    out.mkdir(parents=True);w=out/'workspace';w.mkdir();(w/'home').mkdir();(w/'scratch').mkdir()
    canary=out/'evaluator-canary.txt';canary.write_text('harmless evaluator canary')
    code='import json,os\nfrom pathlib import Path\nimport dolfinx,gmsh\nr={"dolfinx":dolfinx.__version__,"gmsh":gmsh.__version__,"api_key_absent":not any("API_KEY" in k for k in os.environ)}\n'
    code+='try:\n Path('+repr(str(canary.resolve()))+').read_text();r["reference_read_denied"]=False\nexcept (PermissionError,FileNotFoundError):r["reference_read_denied"]=True\n'
    code+='try:\n Path("/etc/engineering-fem-write-canary").write_text("bad");r["outside_write_denied"]=False\nexcept OSError:r["outside_write_denied"]=True\n'
    code+='r["network_denied"]=set(p.name for p in Path("/sys/class/net").iterdir())=={"lo"}\nPath("selfcheck.json").write_text(json.dumps(r))\n'
    (w/'main.py').write_text(code);evidence=replay(out,runtime,90)
    result=load(w/'selfcheck.json') if (w/'selfcheck.json').exists() else {'status':evidence['status']}
    ok=all(result.get(k) is True for k in ['api_key_absent','reference_read_denied','outside_write_denied','network_denied']) and result.get('dolfinx')=='0.9.0' and result.get('gmsh')=='4.15.2'
    report=dict(passed=ok,checks=result,execution=evidence)
    save(out/'selfcheck-result.json',report);save(DATA/'runtime-preflight.json',report);print(json.dumps(dict(passed=ok,checks=result)),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','generate','replay','score','selfcheck']);p.add_argument('--case',default='ENGFEM-LE1');p.add_argument('--track',choices=['cad_fem','analysis_fem'],default='analysis_fem');p.add_argument('--out',type=Path,required=True);p.add_argument('--provider',choices=['openai','explabs'],default='openai');p.add_argument('--model',default='gpt-6-astra');p.add_argument('--max-tokens',type=int,default=16000);p.add_argument('--effort',choices=['low','medium','high','xhigh','max'],default='high');p.add_argument('--budget',type=float,default=3);p.add_argument('--runtime',type=Path,default=DEFAULT_RUNTIME);p.add_argument('--timeout',type=int,default=900);a=p.parse_args()
    if a.action=='prepare':prepare(a.case,a.track,a.out)
    elif a.action=='generate':generate(a.out,a.provider,a.model,a.max_tokens,a.effort,a.budget)
    elif a.action=='replay':print(json.dumps(replay(a.out,a.runtime,a.timeout)))
    elif a.action=='score':score(a.out)
    else:selfcheck(a.out,a.runtime)
