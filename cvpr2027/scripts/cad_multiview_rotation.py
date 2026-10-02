"""Prospective multiview pattern-edit discovery; references never enter API prompts."""
import argparse,ast,base64,copy,hashlib,json,math,time,urllib.request
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import cad_multiview_probe as mv
import cad_intent_probe as base
from cad_native_probe import api_key,write,ENDPOINT
from render_svg_gallery import render
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/cad-multiview-rotation'

def cloud(svg,shape_ids):
    points=[]
    for eid,v in base.inspect(svg).items():
        if eid not in shape_ids:continue
        p=np.asarray(v['points']);tag=v['tag']
        if tag=='circle':
            u,w=np.asarray(v['radius_vectors']);n=max(180,int(math.ceil(2*math.pi*max(np.linalg.norm(u),np.linalg.norm(w))/.1)))
            a=np.linspace(0,2*math.pi,n,endpoint=False);points.extend(p[0]+np.cos(a)[:,None]*u+np.sin(a)[:,None]*w)
        elif tag in ('line','rect'):
            pairs=[(p[0],p[1])] if tag=='line' else list(zip(p,np.roll(p,-1,axis=0)))
            for a,b in pairs:
                n=max(2,int(math.ceil(np.linalg.norm(a-b)/.1))+1);points.extend(a+np.linspace(0,1,n)[:,None]*(b-a))
    return np.asarray(points)

def score(t,patches):
    svg=mv.apply(t['svg'],patches);a=cloud(svg,t['source_shape_ids']);b=cloud(t['target_svg'],t['source_shape_ids'])
    if not len(a) or not len(b):raise ValueError('Empty geometry')
    ab=cKDTree(b).query(a)[0];ba=cKDTree(a).query(b)[0]
    error=float(max(ab.max(),ba.max()));detail=mv.score(t,patches)
    return {'outcome':'geometry_failure' if error>.45 else 'annotation_review' if detail['annotation_errors'] or detail['missing'] or detail['extra'] else 'pass',
            'max_boundary_error_mm':error/4,'geometry_pass':error<=.45,'id_based_diagnostic':detail,
            'scope':'Bidirectional sampled visible primitive boundaries, 0.1 mm requested tolerance plus 0.0125 mm sampling allowance. Duplicate/coincident hidden edges and reassigned geometric IDs do not create geometry failures. Notes/leaders reviewed separately.'}

def build():
    if (DATA/'tasks.json').exists():raise ValueError('Frozen manifest already exists')
    fs=[{'x':90+35*math.cos(math.radians(7+30*i)),'y':50+35*math.sin(math.radians(7+30*i)),'kind':'B','r':4,'depth':7} for i in range(12)]
    fs += [{'x':x,'y':y,'kind':'A','r':3,'depth':18} for x,y in [(20,20),(160,20),(20,80),(160,80)]]
    fs += [{'x':x,'y':50,'kind':'C','r':3,'depth':18} for x in (81,99)]
    target=copy.deepcopy(fs);theta=math.radians(23)
    for f in target:
        if f['kind']=='B':
            x,y=f['x']-90,f['y']-50;f.update(x=90+x*math.cos(theta)-y*math.sin(theta),y=50+x*math.sin(theta)+y*math.cos(theta),r=6,depth=18)
    source=mv.drawing(fs);dest=mv.drawing(target)
    root=mv.ET.fromstring(dest)
    for e in root.iter():
        if e.get('id')==mv.ident('note1'):e.text='B: DIA 12 THRU'
        if e.get('id')==mv.ident('note2'):e.text='C: DIA 6 THRU, COUNTERBORE DIA 14 DEPTH 9'
        for i,f in enumerate(target):
            if f['kind']=='C':
                for view in ('front','right'):
                    for sign in (-1,1):
                        if e.get('id')==mv.ident(f'{i}{view}cbside{sign}'):e.set('y2','9')
                        if e.get('id')==mv.ident(f'{i}{view}cbstep{sign}'):e.set('y1','9');e.set('y2','9')
    dest=mv.ET.tostring(root,encoding='unicode');inv=base.inspect(source)
    shapes=[k for k,v in inv.items() if v['tag'] in ('circle','rect','line') and float(v['attributes'].get('stroke-width',.25))<.7]
    instruction='Edit this 180 x 100 x 18 mm machining drawing. Rotate the entire B hole pattern +23 degrees counterclockwise in physical TOP XY about (90,50) mm. B hole IDs stay attached to their individual holes. At the new centers, change every B hole from DIA 8 BLIND DEPTH 7 to DIA 12 THROUGH. Also deepen each C counterbore from 4 to 9 mm, preserving C centers and both diameters. Preserve A holes and the plate. Update ALL TOP, FRONT and reflected RIGHT views, labels/leaders and affected notes; remove obsolete blind-bottom edges. Preserve sheet layout and unrelated annotations. Geometry tolerance is 0.1 mm. SVG coordinates and disclosed transforms give the exact input geometry. Hidden edges may coincide; evaluate the final geometry, not the internal identity of coincident lines. Return JSON patches to the existing elements, allowing remove:true. All holes are normal to TOP. This is a machining-feature change only; no structural load analysis is requested.'
    t={'id':'rotated_bore_pattern','svg':source,'target_svg':dest,'source_shape_ids':shapes,'shape_ids':shapes,'hidden_features':fs,'hidden_target_features':target,'instruction':instruction,'prompt':instruction+'\nSOURCE SVG:\n'+source,'image_path':str((DATA/'source.png').resolve())}
    # Verify independent physical checks before freezing the reference.
    min_clearance=1e9
    for i,a in enumerate(target):
        ra=7 if a['kind']=='C' else a['r']
        assert min(a['x']-ra,180-a['x']-ra,a['y']-ra,100-a['y']-ra)>0
        for b in target[i+1:]:
            rb=7 if b['kind']=='C' else b['r'];min_clearance=min(min_clearance,math.hypot(a['x']-b['x'],a['y']-b['y'])-ra-rb)
    assert min_clearance>0
    patches=mv.oracle_patches(t);check=score(t,patches);assert check['geometry_pass']
    assert not score(t,[])['geometry_pass']
    write(DATA/'tasks.json',{'version':'rotation-v1','tasks':[t],'preflight':{'min_material_between_holes_mm':min_clearance,'oracle':check,'oracle_patch_count':len(patches)},'admission':'Three independent completed high-effort geometry failures, audited against reference and visibility; annotation, API, truncation and interface failures excluded. Adaptive extension of the earlier passed translation-only fixture; not a new family.'})
    (DATA/'source.svg').write_text(source);(DATA/'target.svg').write_text(dest);render(DATA/'source.svg',DATA/'source.png',1550);render(DATA/'target.svg',DATA/'target.png',1550)
    print('Frozen',t['id'],len(patches),'patches; minimum material',min_clearance,flush=True)

def calculate(expressions):
    env={k:getattr(math,k) for k in ('sin','cos','tan','sqrt','radians','degrees','pi')}
    allowed=(ast.Expression,ast.BinOp,ast.UnaryOp,ast.Constant,ast.Name,ast.Load,ast.Call,ast.List,ast.Tuple,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Pow,ast.USub,ast.UAdd)
    out=[]
    if len(expressions)>100:raise ValueError('At most 100 expressions')
    for expression in expressions:
        if len(expression)>2000:raise ValueError('Expression too long')
        tree=ast.parse(expression,mode='eval')
        for n in ast.walk(tree):
            if not isinstance(n,allowed):raise ValueError('Arithmetic and trigonometry only')
            if isinstance(n,ast.Name) and n.id not in env:raise ValueError('Unknown name')
            if isinstance(n,ast.Pow):raise ValueError('Powers not supported')
        out.append(eval(compile(tree,'<arithmetic>','eval'),{'__builtins__':{}},env))
    return out

SYSTEM='''Edit the provided detached engineering SVG. Return JSON {"patches":[{"id":"...","set":{"x1":123},"text":"optional"},{"id":"...","remove":true}],"explanation":"..."}. Use numeric-coordinate patches for rect/circle/line/text, text changes, or deletion. Styles, transforms and IDs are fixed; do not add objects. Deleted blind-end lines are explicitly permitted. The input has exact coordinates, visible feature labels and view definitions. Correctly update the physical part across all views. You may use four calls total to inspect_svg and calculate. Inspection shows geometry after your patches, never a target answer. Calculate accepts up to 100 arithmetic expressions per call, including sin, cos, radians and pi. You may solve directly. Do not mistake page-axis directions for physical XY directions.'''
TOOLS=[copy.deepcopy(base.TOOLS[0]),{'type':'function','name':'calculate','description':'Evaluate numeric arithmetic/trigonometry expressions; list literals supported. No hidden geometry or reference.','parameters':{'type':'object','properties':{'expressions':{'type':'array','items':{'type':'string'}}},'required':['expressions'],'additionalProperties':False},'strict':True}]
TOOLS[0]['parameters']['properties']['patches']['items']['properties']['remove']={'type':'boolean'}

def run(out,sample):
    if out.exists():raise ValueError('Use a new trial output directory')
    taskfile=DATA/'tasks.json';t=json.loads(taskfile.read_text())['tasks'][0];key=api_key()
    write(out/'protocol.json',{'model':'gpt-6-astra','effort':'high','max_output_tokens':24000,'max_tool_calls':4,'sample':sample,'system':SYSTEM,'tools':TOOLS,'manifest_sha256':hashlib.sha256(taskfile.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':[{'type':'input_text','text':t['prompt']},{'type':'input_image','image_url':'data:image/png;base64,'+base64.b64encode(Path(t['image_path']).read_bytes()).decode(),'detail':'high'}]}]
    rec={'id':t['id'],'sample':sample,'status':'started','usage':[]};calls=0;write(out/'result.json',rec)
    try:
        for turn in range(5):
            payload={'model':'gpt-6-astra','input':messages,'reasoning':{'effort':'high'},'max_output_tokens':24000,'store':False,'include':['reasoning.encrypted_content']}
            if calls<4:payload.update(tools=TOOLS,parallel_tool_calls=False)
            write(out/f'request-{turn}.json',payload);req=urllib.request.Request(ENDPOINT,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
            with urllib.request.urlopen(req,timeout=900) as res:raw=json.load(res)
            write(out/f'response-{turn}.json',raw);rec['usage'].append(raw.get('usage',{}));messages.extend(raw['output'])
            if raw['status']!='completed':rec['status']='incomplete_excluded';break
            fc=[x for x in raw['output'] if x['type']=='function_call']
            if fc:
                for c in fc:
                    args=json.loads(c['arguments'])
                    try:r=base.inspect(mv.apply(t['svg'],args['patches'])) if c['name']=='inspect_svg' else calculate(args['expressions'])
                    except Exception as e:r={'interface_error':str(e)}
                    write(out/f'tool-{calls}.json',r);calls+=1;messages.append({'type':'function_call_output','call_id':c['call_id'],'output':json.dumps(r)});print('tool',calls,c['name'],flush=True)
            else:
                text=''.join(c['text'] for v in raw['output'] if v['type']=='message' for c in v['content'] if c['type']=='output_text');(out/'final.txt').write_text(text)
                if text.startswith('```'):text=text.split('\n',1)[1].rsplit('```',1)[0]
                obj=json.loads(text);write(out/'answer.json',obj);(out/'output.svg').write_text(mv.apply(t['svg'],obj['patches']));rec.update(status='completed',score=score(t,obj['patches']));break
        if rec['status']=='started':rec['status']='no_final_excluded'
    except Exception as e:rec.update(status='operational_error_excluded',error=str(e).replace(key,'[REDACTED]')[:500])
    rec['tool_calls']=calls;write(out/'result.json',rec);print(rec['status'],rec.get('score',{}).get('outcome'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','run']);p.add_argument('--output',type=Path);p.add_argument('--sample',type=int,default=0);a=p.parse_args()
    if a.command=='build':build()
    else:run(a.output,a.sample)
