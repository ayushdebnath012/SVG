"""Detached SVG edit pilot: equal initial geometry, different dimension intent.

Original procedural fixtures; no third-party evaluation records used for training.
The API sees SVG and generic inspection/algebra tools, never the hidden reference.
"""
import argparse,copy,hashlib,json,math,re,sys,urllib.request,urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from svgpatchlab.eval.field_fidelity import transform_matrix
from cad_native_probe import api_key,write
DATA=ROOT/'data/cad-intent-probe'
GEOM={'rect':('x','y','width','height'),'circle':('cx','cy','r'),'line':('x1','y1','x2','y2'),'text':('x','y')}

def make_svg(mode,encoded=False,edited=False):
    W=234 if edited else 180
    pitch=(W-36)/4 if mode=='edge' else 36
    xs=[18+i*pitch for i in range(5)]
    elements=[];counter=0
    def el(tag,attrs,text=None):
        nonlocal counter
        attrs={k:str(v) for k,v in attrs.items()};attrs['id']='e'+hashlib.sha256(str(counter).encode()).hexdigest()[:7];counter+=1
        if encoded:
            for k in GEOM.get(tag,()):
                if k in attrs:
                    v=float(attrs[k]);offset=17 if k in ('x','cx','x1','x2') else -9 if k in ('y','cy','y1','y2') else 0
                    attrs[k]=str((v-offset)/1.25)
            if 'font-size' in attrs:attrs['font-size']=str(float(attrs['font-size'])/1.25)
            if 'stroke-width' in attrs:attrs['stroke-width']=str(float(attrs['stroke-width'])/1.25)
        n=ET.Element(tag,attrs);n.text=text;elements.append(n)
    def line(x1,y1,x2,y2,**kw):el('line',dict(x1=x1,y1=y1,x2=x2,y2=y2,stroke='#172b3a',**kw))
    def txt(x,y,t,**kw):el('text',dict(x=x,y=y,fill='#172b3a',stroke='none',**{'font-size':3.4},**kw),t)
    def dim(a,b,y,value,reference=False):
        # End ticks and extension lines remain explicit; no hidden semantic metadata.
        line(a,40,a,y+2);line(b,40,b,y+2);line(a,y,b,y)
        line(a-1,y-1,a+1,y+1);line(b-1,y-1,b+1,y+1)
        txt((a+b)/2,y-1.5,('('+f'{value:g}'+')') if reference else f'{value:g}',**{'text-anchor':'middle'})
    txt(0,-8,'MOUNTING PANEL — TOP / FRONT — mm',**{'font-weight':'bold'})
    el('rect',dict(x=0,y=0,width=W,height=40,fill='none',stroke='#172b3a'))
    for x in xs:el('circle',dict(cx=x,cy=20,r=4.5,fill='none',stroke='#172b3a'))
    # Same physical holes in the front view, shown as hidden vertical edges.
    el('rect',dict(x=0,y=105,width=W,height=8,fill='none',stroke='#172b3a'))
    for x in xs:
        for dx in [-4.5,4.5]:line(x+dx,105,x+dx,113,**{'stroke-dasharray':'1,1'})
    values=[xs[0]]+[xs[i+1]-xs[i] for i in range(4)]+[W-xs[-1]]
    points=[0]+xs+[W]
    for i,(a,b,v) in enumerate(zip(points,points[1:],values)):
        dim(a,b,55,v,reference=(i in range(1,5) if mode=='edge' else i==5))
    dim(0,W,71,W)
    txt(0,86,'5 × DIA 9 THRU; panel height 40; thickness 8')
    txt(0,93,'Hole centres equally spaced' if mode=='edge' else 'Preserve each unbracketed chain dimension')
    txt(0,124,'Parenthesized dimensions are reference only; other dimensions drive the edit.')
    txt(0,131,'Front view shares the top-view X datum. Do not change height, thickness or diameters.')
    svg=ET.Element('svg',dict(xmlns='http://www.w3.org/2000/svg',width='850',height='540',viewBox='0 0 850 540'))
    ET.SubElement(svg,'rect',dict(width='850',height='540',fill='white'))
    g=ET.SubElement(svg,'g',{'transform':'translate(60,60) scale(3)','stroke-width':'0.3','font-family':'sans-serif'})
    if encoded:g=ET.SubElement(g,'g',{'transform':'translate(17,-9) scale(1.25)','stroke-width':'0.24'})
    g.extend(elements)
    return ET.tostring(svg,encoding='unicode')

def inspect(svg):
    root=ET.fromstring(svg);result={}
    def walk(n,M):
        M=M@transform_matrix(n.get('transform',''));tag=n.tag.split('}')[-1];eid=n.get('id')
        if eid:
            if eid in result:raise ValueError('duplicate ID')
            def p(x,y):return (M@np.array([float(x),float(y),1]))[:2].tolist()
            a=n.attrib;r={'tag':tag,'attributes':dict(a)}
            if tag=='line':r['points']=[p(a['x1'],a['y1']),p(a['x2'],a['y2'])]
            elif tag=='rect':
                x,y,w,h=map(float,[a['x'],a['y'],a['width'],a['height']]);r['points']=[p(x,y),p(x+w,y),p(x+w,y+h),p(x,y+h)]
            elif tag=='circle':r.update(points=[p(a['cx'],a['cy'])],radius_vectors=[(M[:2,:2]@np.array([float(a['r']),0])).tolist(),(M[:2,:2]@np.array([0,float(a['r'])])).tolist()])
            elif tag=='text':r.update(points=[p(a['x'],a['y'])],text=''.join(n.itertext()))
            result[eid]=r
        for child in n:walk(child,M)
    walk(root,np.eye(3));return result

def apply(svg,patches):
    root=ET.fromstring(svg);index={n.get('id'):n for n in root.iter() if n.get('id')}
    for p in patches:
        n=index[p['id']];tag=n.tag.split('}')[-1]
        for k,v in p.get('set',{}).items():
            if k not in GEOM[tag]:raise ValueError('Only numeric geometry attributes are editable')
            v=float(v)
            if not math.isfinite(v) or abs(v)>10000:raise ValueError('invalid coordinate')
            n.set(k,f'{v:.12g}')
        if 'text' in p:
            if tag!='text':raise ValueError('text edits require text element')
            n.text=str(p['text'])
    return ET.tostring(root,encoding='unicode')

def score(task,patches):
    try:
        actual=inspect(apply(task['svg'],patches));target=inspect(task['target_svg'])
        errors=[];shape_errors=[];annotation_errors=[]
        for eid,t in target.items():
            a=actual[eid];error=float(np.max(np.abs(np.array(a['points'])-np.array(t['points']))))/3
            if 'radius_vectors' in t:error=max(error,float(np.max(np.abs(np.array(a['radius_vectors'])-np.array(t['radius_vectors']))))/3)
            if error>0.05:
                issue={'id':eid,'error_mm':error};errors.append(issue)
                (shape_errors if eid in task['shape_ids'] else annotation_errors).append(issue)
            if t['tag']=='text' and a['text']!=t['text']:
                # Numeric formatting is immaterial; reference parentheses must survive.
                number=lambda s:float(s.strip('() '))
                try:equal=abs(number(a['text'])-number(t['text']))<0.01 and ('(' in a['text'])==('(' in t['text'])
                except ValueError:equal=False
                if not equal:annotation_errors.append({'id':eid,'expected':t['text'],'actual':a['text']})
        return dict(outcome='failure' if errors or annotation_errors else 'pass',geometry_errors=shape_errors,annotation_errors=annotation_errors,
                    scope='numeric edit and complete dimension/witness geometry; exact protected note preservation; no general rendering or safety certification')
    except Exception as e:return dict(outcome='unscored_format',error=str(e))

def oracle_patches(task):
    a=inspect(task['svg']);b=inspect(task['target_svg']);patches=[]
    for eid,t in b.items():
        fields={k:v for k,v in t['attributes'].items() if k in GEOM[t['tag']] and a[eid]['attributes'][k]!=v}
        p={'id':eid,'set':fields}
        if t.get('text')!=a[eid].get('text'):p['text']=t['text']
        if fields or 'text' in p:patches.append(p)
    return patches

def build():
    if (DATA/'tasks.json').exists():raise SystemExit('manifest frozen')
    tasks=[]
    for mode in ['chain','edge']:
        for encoded in [False,True]:
            t=dict(id=mode+('_nested' if encoded else '_plain'),mode=mode,encoded=encoded,
                   svg=make_svg(mode,encoded),target_svg=make_svg(mode,encoded,True))
            inv=inspect(t['svg']);t['shape_ids']=[k for k,v in inv.items() if v['tag'] in ['rect','circle'] or (v['tag']=='line' and 'stroke-dasharray' in v['attributes'])]
            t['prompt']='Increase the panel overall width from 180 to 234 mm, with its left datum fixed. Follow the driving/reference dimensions and notes in the drawing. Update the top and front views, all affected dimension text, dimension lines, witness lines and ticks. Preserve unrelated geometry and sheet layout. Return JSON patches, not a replacement model. Element IDs identify objects only; they do not encode engineering meaning.\n'+t['svg']
            p=DATA/t['id'];p.mkdir(parents=True,exist_ok=True);(p/'source.svg').write_text(t['svg']);(p/'target.svg').write_text(t['target_svg'])
            assert score(t,oracle_patches(t))['outcome']=='pass';tasks.append(t)
    write(DATA/'tasks.json',dict(version='intent-probe-v1',tasks=tasks,policy='Original procedural smoke test, not a real-data benchmark or a novelty claim. High-effort screen; confirm only substantive reviewed failures twice. Semantic errors separated from dimension-placement deviations. References frozen before calls.',tolerance_mm=0.05))

SYSTEM='''You edit detached engineering SVG drawings. Interpret visible dimensions, their extension-line attachments and the notes; no native CAD history is available. In these fixtures, parenthesized dimensions are reference values to recompute, and unparenthesized dimensions drive the edit except the explicitly requested width change.
Use patches to existing opaque element IDs. Format: {"patches":[{"id":"...","set":{"x1":123},"text":"optional text for a text element"}],"explanation":"..."}. set can modify only numeric geometry attributes of rect/circle/line/text, not IDs, styles or transforms. Preserve all existing objects. Text positions and dimension endpoints should follow their attached features. All physical edits are in mm; SVG ancestor transforms map them into page coordinates.
You may use inspect_svg up to two times and solve_linear up to two times. inspect_svg returns page-space numeric geometry after candidate patches; it does NOT have reference answers or engineering constraints. solve_linear is a generic linear algebra tool. You can also compute directly. Return the final JSON when done.'''
TOOLS=[{'type':'function','name':'inspect_svg','description':'Inspect resulting world/page-space SVG geometry after applying patches; no hidden target or constraint oracle.','parameters':{'type':'object','properties':{'patches':{'type':'array','items':{'type':'object','properties':{'id':{'type':'string'},'set':{'type':'object','additionalProperties':{'type':'number'}},'text':{'type':'string'}},'required':['id']}}},'required':['patches']},'strict':False},
{'type':'function','name':'solve_linear','description':'Solve a numeric linear system A x = b and report residual.','parameters':{'type':'object','properties':{'A':{'type':'array','items':{'type':'array','items':{'type':'number'}}},'b':{'type':'array','items':{'type':'number'}}},'required':['A','b'],'additionalProperties':False},'strict':True}]

def run(out,ids=None):
    manifest=json.loads((DATA/'tasks.json').read_text());key=api_key();selected=[t for t in manifest['tasks'] if not ids or t['id'] in ids.split(',')]
    protocol=dict(model='gpt-6-astra',effort='high',cap=16000,max_api_turns=5,tools=TOOLS,system=SYSTEM,ids=[t['id'] for t in selected],manifest_sha256=hashlib.sha256((DATA/'tasks.json').read_bytes()).hexdigest())
    if (out/'protocol.json').exists() and json.loads((out/'protocol.json').read_text())!=protocol:raise ValueError('Protocol changed')
    write(out/'protocol.json',protocol)
    def one(t):
        d=out/t['id'];d.mkdir(parents=True,exist_ok=True)
        if (d/'result.json').exists():return
        rec=dict(id=t['id'],status='started',usage=[]);write(d/'result.json',rec)
        messages=[{'role':'system','content':SYSTEM},{'role':'user','content':t['prompt']}];counts={'inspect_svg':0,'solve_linear':0}
        try:
            for turn in range(5):
                available=[tool for tool in TOOLS if counts[tool['name']]<2] if turn<4 else []
                payload=dict(model='gpt-6-astra',input=messages,reasoning={'effort':'high'},max_output_tokens=16000,store=False,include=['reasoning.encrypted_content'])
                if available:payload.update(tools=available,parallel_tool_calls=False)
                write(d/f'request-{turn}.json',payload)
                req=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
                with urllib.request.urlopen(req,timeout=900) as response:raw=json.load(response)
                write(d/f'response-{turn}.json',raw);rec['usage'].append(raw.get('usage',{}))
                if raw['status']!='completed':rec['status']='budget_or_incomplete';break
                messages.extend(raw['output']);calls=[v for v in raw['output'] if v['type']=='function_call']
                if calls:
                    for c in calls:
                        args=json.loads(c['arguments']);counts[c['name']]+=1
                        try:
                            if c['name']=='inspect_svg':result=inspect(apply(t['svg'],args['patches']))
                            else:
                                A=np.array(args['A']);b=np.array(args['b']);x=np.linalg.lstsq(A,b,rcond=None)[0];result={'x':x.tolist(),'residual':float(np.linalg.norm(A@x-b))}
                        except Exception as e:result={'error':str(e)}
                        write(d/f'tool-{turn}.json',result);messages.append({'type':'function_call_output','call_id':c['call_id'],'output':json.dumps(result)})
                else:
                    text=''.join(c['text'] for v in raw['output'] if v['type']=='message' for c in v['content'] if c['type']=='output_text');(d/'final.txt').write_text(text)
                    if text.startswith('```'):text=text.split('\n',1)[1].rsplit('```',1)[0]
                    obj=json.loads(text);write(d/'answer.json',obj);(d/'output.svg').write_text(apply(t['svg'],obj['patches']))
                    rec.update(status='completed',score=score(t,obj['patches']));break
            if rec['status']=='started':rec['status']='no_final'
        except urllib.error.HTTPError as e:rec.update(status='api_error',error=e.read().decode().replace(key,'[REDACTED]')[:1000])
        except Exception as e:rec.update(status='operational_error',error=str(e).replace(key,'[REDACTED]')[:500])
        rec['tool_calls']=counts;write(d/'result.json',rec);print(t['id'],rec['status'],rec.get('score',{}).get('outcome'),flush=True)
    with ThreadPoolExecutor(max_workers=2) as p:list(p.map(one,selected))
    rows=[json.loads(p.read_text()) for p in sorted(out.glob('*/result.json'))];write(out/'summary.json',dict(rows=rows,usage={k:sum(u.get(k,0) for r in rows for u in r['usage']) for k in ['input_tokens','output_tokens','total_tokens']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','run']);p.add_argument('--output',type=Path);p.add_argument('--ids');a=p.parse_args()
    build() if a.command=='build' else run(a.output,a.ids)
