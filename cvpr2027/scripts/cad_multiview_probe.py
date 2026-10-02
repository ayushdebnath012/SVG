"""Detached multi-view machining drawings. Hidden feature graph is evaluator-only."""
import argparse,base64,copy,hashlib,json,math,re,sys,urllib.request,urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import cad_intent_probe as base
from cad_native_probe import write
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/cad-multiview-probe'
NS='http://www.w3.org/2000/svg'
def ident(key):return 'e'+hashlib.sha256(key.encode()).hexdigest()[:10]
def drawing(features,updated=False,rotation=0):
    root=ET.Element('svg',dict(xmlns=NS,width='1500',height='1080',viewBox='0 0 1500 1080'))
    ET.SubElement(root,'rect',dict(width='1500',height='1080',fill='white'))
    def el(g,key,tag,attrs,text=None):
        n=ET.SubElement(g,tag,dict(id=ident(key),**{k:str(v) for k,v in attrs.items()}));n.text=text;return n
    textg=ET.SubElement(root,'g',{'font-family':'sans-serif','font-size':'16'})
    for i,line in enumerate(['MACHINED FIXTURE PLATE | mm | orthographic projections',
       'Plate 180 x 100 x 18. Datum X=0 at left, Y=0 at bottom of TOP; Z=0 at upper surface.',
       'TOP: right=+X, up=+Y. FRONT: right=+X, down=depth. RIGHT: right=-Y, down=depth.',
       'Hole IDs A/B/C identify individual features. All holes are normal to TOP. Dashed edges are hidden.']):
        el(textg,'header'+str(i),'text',dict(x=35,y=30+i*25,fill='#172b3a'),line)
    view_specs=[('top','translate(70,590) scale(4,-4)',[-0.,0.,180.,100.]),
                ('front','translate(70,690) scale(4,4)',[0.,0.,180.,18.]),
                ('right','translate(1350,690) scale(-4,4)',[0.,0.,100.,18.])]
    # Intentional independent drawing scales are disclosed; physical units are local coordinates.
    for view,transform,stock in view_specs:
        g=ET.SubElement(root,'g',{'transform':transform,'stroke':'#172b3a','stroke-width':'.25','fill':'none'})
        el(g,view+'stock','rect',dict(zip(['x','y','width','height'],stock)))
        for i,h in enumerate(features):
            x,y,r,d=h['x'],h['y'],h['r'],h['depth'];kind=h['kind']
            if updated and kind=='B':x+=12;r=7;d=18
            if view=='top':
                el(g,f'{i}topcircle','circle',dict(cx=x,cy=y,r=r))
                if kind=='C':el(g,f'{i}topouter','circle',dict(cx=x,cy=y,r=7))
            else:
                c=x if view=='front' else y
                for side in [-1,1]:el(g,f'{i}{view}side{side}','line',dict(x1=c+side*r,x2=c+side*r,y1=0,y2=d,**{'stroke-dasharray':'1.2,1'}))
                if d<18:el(g,f'{i}{view}bottom','line',dict(x1=c-r,x2=c+r,y1=d,y2=d,**{'stroke-dasharray':'1.2,1'}))
                if kind=='C':
                    for side in [-1,1]:
                        el(g,f'{i}{view}cbside{side}','line',dict(x1=c+side*7,x2=c+side*7,y1=0,y2=4,**{'stroke-dasharray':'1.2,1'}))
                        el(g,f'{i}{view}cbstep{side}','line',dict(x1=c+side*r,x2=c+side*7,y1=4,y2=4,**{'stroke-dasharray':'1.2,1'}))
    # Labels drawn in page space, with leaders to unambiguous hole centers.
    for i,h in enumerate(features):
        x,y=h['x'],h['y'];kind=h['kind']
        if updated and kind=='B':x+=12
        px,py=70+4*x,590-4*y
        el(textg,f'{i}label','text',dict(x=px+10,y=py-20,fill='#172b3a',**{'font-size':12}),kind+str(i+1))
        el(textg,f'{i}leader','line',dict(x1=px+9,y1=py-16,x2=px,y2=py,stroke='#172b3a',**{'stroke-width':'.7'}))
    for name,x,y in [('TOP (X,Y)',70,170),('FRONT (X,depth)',70,673),('RIGHT (-Y,depth)',990,673)]:
        el(textg,name,'text',dict(x=x,y=y,fill='#172b3a'),name)
    notes=['A: DIA 6 THRU','B: DIA 14 THRU' if updated else 'B: DIA 8 BLIND DEPTH 7','C: DIA 6 THRU, COUNTERBORE DIA 14 DEPTH 4','No countersinks, fillets or other features. All views are 4 page units per mm; RIGHT is reflected as labeled.']
    for i,note in enumerate(notes):el(textg,'note'+str(i),'text',dict(x=40,y=850+i*25,fill='#172b3a'),note)
    return ET.tostring(root,encoding='unicode')

def apply(svg,patches):
    root=ET.fromstring(svg);index={n.get('id'):n for n in root.iter() if n.get('id')}
    parents={c:p for p in root.iter() for c in p}
    for p in patches:
        n=index[p['id']]
        if p.get('remove'):
            parents[n].remove(n);continue
        tag=n.tag.split('}')[-1]
        for k,v in p.get('set',{}).items():
            if k not in base.GEOM[tag]:raise ValueError('Only numeric geometry attributes')
            v=float(v)
            if not math.isfinite(v):raise ValueError('nonfinite coordinate')
            n.set(k,f'{v:.12g}')
        if 'text' in p:
            if tag!='text':raise ValueError('text requires text node')
            n.text=str(p['text'])
    return ET.tostring(root,encoding='unicode')

def equivalent_note(text):
    """Normalize only the standard through-hole abbreviation; preserve numbers."""
    return re.sub(r'\bTHROUGH\b', 'THRU', text) if isinstance(text,str) else text

def score(t,patches):
    try:
        actual=base.inspect(apply(t['svg'],patches));target=base.inspect(t['target_svg'])
        missing=sorted(set(target)-set(actual));extra=sorted(set(actual)-set(target));geo=[];ann=[]
        for eid,v in target.items():
            if eid not in actual:continue
            a=actual[eid]
            err=float(np.max(abs(np.asarray(a['points'])-np.asarray(v['points']))))
            if 'radius_vectors' in v:err=max(err,float(np.max(abs(np.asarray(a['radius_vectors'])-np.asarray(v['radius_vectors'])))))
            if err>.25:(geo if eid in t['shape_ids'] else ann).append({'id':eid,'max_page_error_px':err})
            if equivalent_note(v.get('text'))!=equivalent_note(a.get('text')):ann.append({'id':eid,'expected_text':v.get('text'),'actual_text':a.get('text')})
        gmissing=[i for i in missing+extra if i in t['source_shape_ids']]
        return {'outcome':'geometry_failure' if geo or gmissing else 'annotation_failure' if missing or extra or ann else 'pass','geometry_errors':geo,'annotation_errors':ann,'missing':missing,'extra':extra,'scope':'Fixed-coordinate multiview primitive geometry, including obsolete blind-end edges; geometry tolerance 0.25 page pixels. Annotation-only errors reported separately.'}
    except Exception as e:return {'outcome':'unscored_format','error':str(e)}

def oracle_patches(t):
    a=base.inspect(t['svg']);b=base.inspect(t['target_svg']);patches=[]
    for eid,v in a.items():
        if eid not in b:patches.append({'id':eid,'remove':True});continue
        x={'id':eid,'set':{k:float(b[eid]['attributes'][k]) for k in base.GEOM[v['tag']] if k in v['attributes'] and v['attributes'][k]!=b[eid]['attributes'][k]}}
        if v.get('text')!=b[eid].get('text'):x['text']=b[eid]['text']
        if x['set'] or 'text' in x:patches.append(x)
    return patches

def build():
    if (DATA/'tasks.json').exists():raise ValueError('Frozen')
    layouts=[
      [(20,20,'A'),(49,25,'B'),(82,18,'C'),(123,22,'B'),(154,29,'A'),(28,72,'C'),(59,67,'B'),(91,78,'A'),(121,71,'C'),(153,66,'B')],
      [(19,23,'B'),(48,18,'C'),(82,28,'A'),(112,21,'B'),(148,26,'C'),(25,75,'A'),(57,69,'B'),(87,79,'C'),(118,72,'B'),(151,64,'A')]]
    tasks=[]
    for j,layout in enumerate(layouts):
        feat=[dict(x=x,y=y,kind=k,r=4 if k=='B' else 3,depth=7 if k=='B' else 18) for x,y,k in layout]
        a=drawing(feat);b=drawing(feat,True);aa=base.inspect(a);bb=base.inspect(b)
        shape=lambda z:[eid for eid,v in z.items() if v['tag'] in {'circle','rect','line'} and float(v['attributes'].get('stroke-width',.25))<.7]
        t=dict(id='fixture_plate_'+str(j+1),svg=a,target_svg=b,shape_ids=shape(bb),source_shape_ids=shape(aa),hidden_features=feat,
          instruction='Revise this existing machining drawing: every B-designated blind hole becomes a DIA 14 THROUGH hole, and its centre moves +12 mm in global X, with Y unchanged. Update ALL views, hole labels/leaders and the B hole note. Remove obsolete hidden blind-bottom lines. Keep the plate and every A/C hole unchanged. The source SVG and its rendered drawing contain the entire specification. Preserve all other elements and their positions. Return numeric-coordinate/text patches, with {\"id\":\"...\",\"remove\":true} to delete obsolete lines. Do not add or rename elements. All views must represent the same edited physical plate.')
        t['prompt']=t['instruction']+'\nSOURCE SVG:\n'+a
        t['image_path']=str((DATA/t['id']/'source.png').resolve())
        d=DATA/t['id'];d.mkdir(parents=True,exist_ok=True);(d/'source.svg').write_text(a);(d/'target.svg').write_text(b)
        if score(t,oracle_patches(t))['outcome']!='pass':raise ValueError('oracle fails')
        tasks.append(t)
    write(DATA/'tasks.json',{'version':'multiview-machining-v1','tasks':tasks,'criteria':{'geometry_tolerance_page_px':.25,'pixel_scale_range':[4,4],'confirmation':'Three completed high-effort independent failures, with reference/render/representation audit. Annotation-only failures excluded.'}})
    print('Built',len(tasks),'cases')

def run(out,ids=None):
    manifest=json.loads((DATA/'tasks.json').read_text());key=api_key();selected=[t for t in manifest['tasks'] if not ids or t['id'] in ids.split(',')]
    protocol=dict(model='gpt-6-astra',effort='high',cap=16000,max_api_turns=5,tools=TOOLS,system=SYSTEM,ids=[t['id'] for t in selected],manifest_sha256=hashlib.sha256((DATA/'tasks.json').read_bytes()).hexdigest())
    if (out/'protocol.json').exists() and json.loads((out/'protocol.json').read_text())!=protocol:raise ValueError('Protocol changed')
    write(out/'protocol.json',protocol)
    def one(t):
        d=out/t['id'];d.mkdir(parents=True,exist_ok=True)
        if (d/'result.json').exists():return
        rec=dict(id=t['id'],status='started',usage=[]);write(d/'result.json',rec)
        messages=[{'role':'system','content':SYSTEM},{'role':'user','content':[{'type':'input_text','text':t['prompt']},{'type':'input_image','image_url':'data:image/png;base64,'+base64.b64encode(Path(t['image_path']).read_bytes()).decode(),'detail':'high'}]}];counts={'inspect_svg':0,'solve_linear':0}
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
    if a.command=='build':build()
    else:
        base.DATA=DATA;base.apply=apply;base.score=score
        base.SYSTEM='You edit detached engineering SVG drawings. Interpret visible feature labels, leaders, view conventions and notes; no native CAD history is available.\nUse patches'+base.SYSTEM.split('Use patches',1)[1]
        base.SYSTEM=base.SYSTEM.replace('Preserve all existing objects.','Preserve objects except obsolete blind-bottom lines, which may be deleted with remove:true.')
        # Extend the existing generic inspection schema with deletion support.
        base.TOOLS[0]['parameters']['properties']['patches']['items']['properties']['remove']={'type':'boolean'}
        SYSTEM=base.SYSTEM;TOOLS=base.TOOLS;inspect=base.inspect;api_key=base.api_key
        run(a.output,a.ids)
