"""Bounded BenchCAD-derived source edit probe with a CadQuery execution tool.

Not a general Python sandbox: accepts a small CAD AST, runs it in a separate
process with a timeout, and never gives generated code file/network primitives.
Ground truth is available only to the offline grader, not the execution tool.
"""
from __future__ import annotations
import argparse, ast, base64, hashlib, html, json, math, os
from pathlib import Path
import subprocess, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/cad-native-probe'
PYTHON = ROOT/'tmp/cad-runtime/bin/python'
SELF = Path(__file__).resolve()
ENDPOINT = 'https://api.openai.com/v1/responses'
METHODS = set('Workplane Vector Wire makeHelix box cylinder sphere circle rect polygon polyline moveTo lineTo threePointArc radiusArc spline close extrude twistExtrude revolve sweep loft union cut intersect transformed translate rotate faces edges vertices workplane center rarray polarArray pushPoints hole cboreHole cskHole cutThruAll cutBlind fillet chamfer mirrorX mirrorY slot2D add val vals size solids clean toTuple'.split())
NODES = (ast.Module, ast.Import, ast.alias, ast.Assign, ast.Expr, ast.Name, ast.Load,
         ast.Store, ast.Call, ast.Attribute, ast.Constant, ast.List, ast.Tuple,
         ast.keyword, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div,
         ast.USub, ast.UAdd, ast.For)

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')

def sha(text): return hashlib.sha256(text.encode()).hexdigest()

def build_shape(code):
    import cadquery as cq
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if not isinstance(node, NODES): raise ValueError('unsupported CAD syntax: '+type(node).__name__)
        if isinstance(node, ast.Import) and not (len(node.names)==1 and node.names[0].name=='cadquery' and node.names[0].asname=='cq'):
            raise ValueError('only import cadquery as cq is supported')
        if isinstance(node, ast.Attribute) and node.attr not in METHODS:
            raise ValueError('unsupported CAD method: '+node.attr)
        if isinstance(node, ast.Name) and '__' in node.id: raise ValueError('dunder names prohibited')
        if isinstance(node, ast.Assign) and any(not isinstance(t,ast.Name) or t.id in {'cq','show_object','range'} for t in node.targets):
            raise ValueError('only ordinary variable assignments supported')
        if isinstance(node, ast.Call) and isinstance(node.func,ast.Name) and node.func.id not in {'show_object','range'}:
            raise ValueError('unsupported function')
        if isinstance(node,ast.For) and not isinstance(node.iter,(ast.Tuple,ast.List)):
            raise ValueError('loops must use literal finite lists/tuples')
    tree.body=[n for n in tree.body if not isinstance(n,ast.Import)]
    env={'cq':cq,'show_object':lambda *a,**k:None,'__builtins__':{}}
    exec(compile(tree,'<cad-probe>','exec'),env)
    result=env['result']
    if isinstance(result,cq.Workplane): result=result.val()
    if not isinstance(result,cq.Shape): raise ValueError('result must be a CAD shape')
    return result

def metrics(shape):
    b=shape.BoundingBox()
    return dict(valid=shape.isValid(),solids=len(shape.Solids()),volume_mm3=shape.Volume(),
                bbox_mm={k:getattr(b,k) for k in ('xmin','xmax','ymin','ymax','zmin','zmax')},
                faces=len(shape.Faces()),edges=len(shape.Edges()))

def geometry_delta(a,b):
    removed=a.cut(b).Volume();added=b.cut(a).Volume()
    common=a.intersect(b).Volume()
    residual=max(abs(removed+common-a.Volume()),abs(added+common-b.Volume()))
    if residual>max(a.Volume(),b.Volume(),1)*1e-6:
        raise ArithmeticError('Inconsistent CAD Boolean volumes; evaluator cannot assign a geometric verdict')
    return dict(removed_mm3=removed,added_mm3=added,
                symmetric_difference_fraction=(removed+added)/max(a.Volume(),b.Volume(),1e-9),
                boolean_identity_residual_mm3=residual)

def sheet(shape, title):
    """Actual kernel hidden-line projections, not model-authored renderings."""
    import cadquery as cq
    parts=[]
    for i,(name,direction) in enumerate([('TOP',(0,0,1)),('FRONT',(0,-1,0)),('RIGHT',(1,0,0))]):
        svg=cq.exporters.getSVG(shape,{'width':330,'height':300,'marginLeft':25,'marginTop':25,
                                     'projectionDir':direction,'showAxes':False,'showHidden':True})
        root=ET.fromstring(svg); inner=''.join(ET.tostring(c,encoding='unicode') for c in root)
        parts.append(f'<g transform="translate({i*350},60)"><text x="25" y="-12" font-size="16">{name}</text>{inner}</g>')
    b=shape.BoundingBox()
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="430" viewBox="0 0 1050 430"><rect width="1050" height="430" fill="white"/><g font-family="sans-serif"><text x="25" y="25" font-size="17">{html.escape(title)}</text>'+''.join(parts)+f'<text x="25" y="390" font-size="14">Envelope X {b.xlen:.3f} mm | Y {b.ylen:.3f} mm | Z {b.zlen:.3f} mm</text><text x="25" y="414" font-size="12">Independent fit per view; dimensions in mm. Kernel projections; dashed hidden edges.</text></g></svg>'

def worker(inp,out):
    p=json.loads(inp.read_text())
    try:
        s=build_shape(p['code']);r=metrics(s)
        if p.get('target_code'):
            target=build_shape(p['target_code']);r['target_delta']=geometry_delta(target,s)
            r['geometry_pass']=r['valid'] and r['solids']==len(target.Solids()) and r['target_delta']['symmetric_difference_fraction']<=0.0001
        if p.get('source_code'):
            r['change_from_source']=geometry_delta(build_shape(p['source_code']),s)
        if p.get('svg'): Path(p['svg']).write_text(sheet(s,p.get('title','CAD edit')))
        if p.get('step'):
            import cadquery as cq
            cq.exporters.export(s,p['step'])
        r['status']='completed'
    except Exception as e:r=dict(status='execution_error',error_type=type(e).__name__,error=str(e)[:1200])
    write(out,r)

def execute(code,folder,**kw):
    folder.mkdir(parents=True,exist_ok=True);write(folder/'input.json',dict(code=code,**kw))
    (folder/'metrics.json').unlink(missing_ok=True)
    env={k:v for k,v in os.environ.items() if k in {'PATH','HOME','TMPDIR','LANG','LC_ALL','DYLD_LIBRARY_PATH'}}
    try:
        r=subprocess.run([str(PYTHON),str(SELF),'worker',str(folder/'input.json'),str(folder/'metrics.json')],env=env,capture_output=True,text=True,timeout=150)
        (folder/'execution.log').write_text(r.stdout+r.stderr)
        if (folder/'metrics.json').exists():return json.loads((folder/'metrics.json').read_text())
        return dict(status='runtime_error',returncode=r.returncode)
    except subprocess.TimeoutExpired:return dict(status='runtime_timeout')

def build():
    if (DATA/'tasks.json').exists():raise SystemExit('Frozen manifest already exists')
    rows=json.loads((ROOT/'tmp/benchcad-source/edits_650.json').read_text())['rows']
    selected=[2,3,5,26]; tasks=[]
    for i in selected:
        r=rows[i]['row'];target=r['gt_code'];instruction=r['instruction'];change=None
        if i==3:
            # Upstream 13.3 spacing changes the requested span: 3*19.96 != 5*13.3.
            target=target.replace('.rarray(1, 13.3, 1, 6)','.rarray(1, 11.976, 1, 6)')
            change='Corrected inconsistent upstream target spacing to 3*19.96/5 = 11.976 mm; derived task, not an official BenchCAD score.'
            instruction+=' Keep the two outer fin centre positions fixed (59.88 mm centre-to-centre span).'
        task=dict(id=r['record_id'],family=r['family'],source_record_id=r['record_id'],
                  source_row=650+i,instruction=instruction,source_code=r['orig_code'],target_code=target,
                  upstream_target_sha256=sha(r['gt_code']),target_change=change)
        folder=DATA/task['id'];folder.mkdir(parents=True,exist_ok=True)
        for name,code in [('source',task['source_code']),('target',target)]:
            (folder/(name+'.py')).write_text(code)
            result=execute(code,folder/(name+'-check'),svg=str(folder/(name+'.svg')),title=task['id']+' / '+name)
            if result.get('status')!='completed' or not result['valid']:raise ValueError((task['id'],name,result))
            task[name+'_metrics']=result
        control=execute(target,folder/'oracle-control',target_code=target,source_code=task['source_code'])
        if not control.get('geometry_pass'):raise ValueError(control)
        task['oracle_control']=control;tasks.append(task)
    write(DATA/'tasks.json',dict(version='native-cad-probe-v1',source='https://huggingface.co/datasets/BenchCAD/BenchCAD',
          split='edit-bench / edit_bench; discovery only, never training',license='CC-BY-4.0',
          source_download_sha256=hashlib.sha256((ROOT/'tmp/benchcad-source/edits_650.json').read_bytes()).hexdigest(),
          threshold=0.0001,policy='Screen once. Only completed, reviewed semantic failures warrant two fresh high-effort confirmations. Budget/runtime/restricted-interface failures are not shape inability.',tasks=tasks))
    print('Built',len(tasks),'audited cases',flush=True)

SYSTEM='''Edit the supplied CadQuery model to satisfy the instruction while preserving unrelated geometry. Units are mm.
You have a CadQuery 2.8 execution tool, evaluate_cad. Submit complete Python CAD code with result assigned.
The tool reports validity, solid count, envelope, volume and change relative to the source; it does NOT have the reference target.
It accepts import cadquery as cq, variables, numeric arithmetic, literal tuple/list loops and CadQuery modeling methods.
No filesystem, network, other imports, functions, comprehensions or introspection are supported. Unsupported syntax is an interface limitation, not a modeling failure.
Use evaluate_cad at least once, up to three times. The final deliverable must be JSON with code and explanation.
An automatic exporter will produce linked top/front/right SVG views and envelope dimensions from your final model.
Do not manually transcribe projection paths. Do not claim physical verification: no materials, loads or supports are specified.
The task is generation/editing of the physical part geometry and its drawing, not a fluid-flow field.'''
TOOL={'type':'function','name':'evaluate_cad','description':'Execute a CAD candidate and inspect actual geometry. Does not compare against a hidden target.','parameters':{'type':'object','properties':{'code':{'type':'string'}},'required':['code'],'additionalProperties':False},'strict':True}

def api_key():
    if os.environ.get('OPENAI_API_KEY'):return os.environ['OPENAI_API_KEY']
    for line in (ROOT.parent/'.env').read_text().splitlines():
        if line.startswith('OPENAI_API_KEY='):return line.split('=',1)[1].strip().strip('\"\'')
    raise RuntimeError('API key unavailable')

def run(out,ids=None,effort='high',sample=0):
    manifest=json.loads((DATA/'tasks.json').read_text());key=api_key()
    chosen=[t for t in manifest['tasks'] if not ids or t['id'] in ids.split(',')]
    protocol=dict(model='gpt-6-astra',endpoint=ENDPOINT,effort=effort,max_output_tokens=10000,max_tool_calls=3,
                  manifest_sha256=sha((DATA/'tasks.json').read_text()),task_ids=[t['id'] for t in chosen],
                  system=SYSTEM,tool=TOOL,sample=sample,feedback='No ground truth in tool',store=False)
    pp=out/'protocol.json'
    if pp.exists() and json.loads(pp.read_text())!=protocol:raise ValueError('protocol mismatch')
    write(pp,protocol)
    def one(task):
        folder=out/task['id'];folder.mkdir(parents=True,exist_ok=True)
        if (folder/'result.json').exists():print('SKIP',task['id'],flush=True);return
        record=dict(status='started',id=task['id'],usage=[],sample=sample);write(folder/'result.json',record)
        messages=[dict(role='system',content=SYSTEM),dict(role='user',content=task['instruction']+'\nSource CAD:\n'+task['source_code']+'\nSource measurements:\n'+json.dumps(task['source_metrics']))]
        started=time.perf_counter();calls=0
        try:
            for turn in range(4):
                payload=dict(model='gpt-6-astra',input=messages,reasoning={'effort':effort},max_output_tokens=10000,store=False,include=['reasoning.encrypted_content'])
                if calls<3:payload.update(tools=[TOOL],tool_choice='required' if turn==0 else 'auto',parallel_tool_calls=False)
                else: messages.append(dict(role='user',content='Tool budget is exhausted. Return the final JSON code and explanation now.'))
                write(folder/f'request-{turn}.json',payload)
                req=urllib.request.Request(ENDPOINT,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
                with urllib.request.urlopen(req,timeout=900) as response:raw=json.load(response)
                write(folder/f'response-{turn}.json',raw);record['usage'].append(raw.get('usage',{}))
                record['finish_reason']=raw['status']
                if raw['status']!='completed':record['status']='budget_or_incomplete';break
                messages.extend(raw['output'])
                tool_calls=[v for v in raw['output'] if v['type']=='function_call']
                if tool_calls:
                    for call in tool_calls:
                        code=json.loads(call['arguments'])['code'];tool_dir=folder/f'tool-{calls}'
                        result=execute(code,tool_dir,source_code=task['source_code'])
                        messages.append(dict(type='function_call_output',call_id=call['call_id'],output=json.dumps(result)))
                        calls+=1;print('TOOL',task['id'],calls,result.get('status'),flush=True)
                else:
                    text=''.join(c['text'] for v in raw['output'] if v['type']=='message' for c in v['content'] if c['type']=='output_text');(folder/'final.txt').write_text(text)
                    if text.startswith('```'):text=text.split('\n',1)[1].rsplit('```',1)[0]
                    final=json.loads(text);(folder/'final.py').write_text(final['code'])
                    result=execute(final['code'],folder/'grade',target_code=task['target_code'],source_code=task['source_code'],svg=str(folder/'final.svg'),title=task['id']+' / Astra')
                    record.update(status='completed',grade=result);break
            if record['status']=='started':record['status']='no_final'
        except urllib.error.HTTPError as exc:record.update(status='operational_error',error_type=type(exc).__name__,error=exc.read().decode().replace(key,'[REDACTED]')[:1200])
        except Exception as exc:record.update(status='operational_error',error_type=type(exc).__name__,error=str(exc).replace(key,'[REDACTED]')[:700])
        record.update(tool_calls=calls,wall_seconds=time.perf_counter()-started);write(folder/'result.json',record)
        print('END',task['id'],record['status'],record.get('grade',{}).get('geometry_pass'),flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(one,chosen))
    summarize(out)

def summarize(out):
    records=[json.loads(p.read_text()) for p in sorted(out.glob('*/result.json'))]
    usage={k:sum(u.get(k,0) for r in records for u in r.get('usage',[])) for k in ['input_tokens','output_tokens','total_tokens']}
    write(out/'summary.json',dict(records=records,usage=usage));print(json.dumps(usage),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='cmd',required=True)
    sub.add_parser('build');p=sub.add_parser('worker');p.add_argument('input',type=Path);p.add_argument('output',type=Path)
    p=sub.add_parser('run');p.add_argument('output',type=Path);p.add_argument('--ids');p.add_argument('--effort',default='high');p.add_argument('--sample',type=int,default=0)
    a=parser.parse_args()
    if a.cmd=='build':build()
    elif a.cmd=='worker':worker(a.input,a.output)
    elif a.cmd=='run':run(a.output,a.ids,a.effort,a.sample)
