"""Thin neutral-surface fabrication patterns; generic numerical SVG tool.
Reference masks use forward 3D distance, independently of candidate curve code.
"""
import argparse,ast,hashlib,json,math,os,subprocess,sys,urllib.request
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.ndimage import distance_transform_edt
from PIL import Image
from cad_native_probe import api_key,write,ENDPOINT
from render_svg_gallery import render
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/cad-development-probe'
SIZE=2600
EXTENT=130.
STEP=2*EXTENT/SIZE

def reference(task,n=SIZE):
    s=task['spec'];v=np.linspace(-EXTENT+EXTENT/n,EXTENT-EXTENT/n,n)
    x,y=np.meshgrid(v,v[::-1])
    if s['kind']=='cylinder':
        R=s['R'];theta=x/R+math.pi+s['seam_rad'];z=y+s['height']/2
        X=R*np.cos(theta);Y=R*np.sin(theta)
        stock=(abs(x)<=math.pi*R)&(z>=0)&(z<=s['height'])
    else:
        dr=s['r1']-s['r0'];L=math.hypot(s['height'],dr);sin_a=dr/L;cos_a=s['height']/L
        rho=np.hypot(x,y);phi=np.arctan2(y,x);theta=phi/sin_a+math.pi+s['seam_rad']
        z=(rho-s['r0']/sin_a)*cos_a;r=rho*sin_a
        X=r*np.cos(theta);Y=r*np.sin(theta)
        stock=(z>=0)&(z<=s['height'])&(abs(phi)<=math.pi*sin_a)
    material=stock.copy()
    for hole in s['bores']:
        d=np.array(hole['axis'],float);d/=np.linalg.norm(d)
        dx=X-hole['point'][0];dy=Y-hole['point'][1];dz=z-hole['point'][2]
        projection=dx*d[0]+dy*d[1]+dz*d[2]
        distance2=dx*dx+dy*dy+dz*dz-projection*projection
        material&=distance2>=hole['radius']**2
    if s.get('trim_plane'):
        a,b,c=s['trim_plane'];material&=z<=a+b*X+c*Y
    return material

def contour_svg(x,y,field):
    """Generic marching-squares vector export. No task/reference access."""
    from matplotlib.figure import Figure
    fig=Figure();ax=fig.subplots()
    cs=ax.contourf(np.asarray(x),np.asarray(y),np.asarray(field),levels=[0,np.inf])
    paths=[]
    for p in cs.get_paths():
        bits=[]
        for (px,py),code in zip(p.vertices,p.codes):
            if code==1:bits.append(f'M{px:.6f},{py:.6f}')
            elif code==2:bits.append(f'L{px:.6f},{py:.6f}')
            elif code==79:bits.append('Z')
            else:raise ValueError('nonlinear contour output unsupported')
        paths.append('<path fill-rule="evenodd" d="'+''.join(bits)+'"/>')
    return '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000" viewBox="-130 -130 260 260"><rect x="-130" y="-130" width="260" height="260" fill="white"/><g fill="black" stroke="none" transform="scale(1,-1)">'+''.join(paths)+'</g></svg>'

ALLOWED_ATTRIBUTES=set('pi sin cos tan asin acos atan atan2 sqrt hypot radians degrees exp log floor ceil fabs copysign isfinite arange linspace meshgrid array asarray zeros ones full zeros_like ones_like full_like sin cos tan arcsin arccos arctan arctan2 sqrt hypot abs minimum maximum clip where logical_and logical_or logical_not stack column_stack concatenate reshape ravel flatten astype sum min max any all shape size dtype float64 bool_ nan inf linalg norm dot cross T transpose append extend join format get items keys values copy tolist'.split())
def numeric_execute(code):
    tree=ast.parse(code)
    for n in ast.walk(tree):
        if isinstance(n,(ast.Import,ast.ImportFrom,ast.With,ast.AsyncWith,ast.ClassDef,ast.Global,ast.Nonlocal,ast.While)):
            raise ValueError('Use supplied math, np and contour_svg; imports/files/while loops unsupported')
        if isinstance(n,ast.Name) and n.id.startswith('_'):raise ValueError('private names prohibited')
        if isinstance(n,ast.Attribute) and n.attr not in ALLOWED_ATTRIBUTES:raise ValueError('unsupported numerical attribute '+n.attr)
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'open','eval','exec','compile','getattr','setattr','input','breakpoint'}:raise ValueError('non-numerical call prohibited')
    import builtins
    env={'np':np,'math':math,'contour_svg':contour_svg,'__builtins__':{k:getattr(builtins,k) for k in ['range','len','min','max','abs','sum','float','int','str','list','tuple','dict','zip','enumerate','round','sorted','bool','print']}}
    exec(compile(tree,'<numeric-svg>','exec'),env)
    svg=env['svg'];root=ET.fromstring(svg)
    for e in root.iter():
        if e.tag.split('}')[-1] not in {'svg','g','path','rect','circle','ellipse','polygon','polyline','line','defs','clipPath','title','desc'}:raise ValueError('Unsupported SVG element')
        if any(k.lower().startswith('on') or 'href' in k or 'url(' in v for k,v in e.attrib.items()):raise ValueError('External/active SVG unsupported')
    if root.get('viewBox')!='-130 -130 260 260':raise ValueError('Use fixed viewBox -130 -130 260 260')
    return svg

def execute(code,folder):
    folder.mkdir(parents=True,exist_ok=True);(folder/'candidate.py').write_text(code)
    env={k:v for k,v in os.environ.items() if k in {'PATH','HOME','TMPDIR','LANG'}}
    try:
        p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'worker','--folder',str(folder.resolve())],env=env,capture_output=True,text=True,timeout=90)
        (folder/'worker.log').write_text(p.stdout+p.stderr)
        return json.loads((folder/'execution.json').read_text())
    except subprocess.TimeoutExpired:return {'status':'execution_timeout'}

def score(task,svg,folder):
    root=ET.fromstring(svg);root.set('width',str(SIZE));root.set('height',str(SIZE))
    p=folder/'grade.svg';p.write_text(ET.tostring(root,encoding='unicode'));render(p,folder/'grade.png',SIZE)
    actual=np.asarray(Image.open(folder/'grade.png').convert('L'))<128
    target=reference(task);missing=target&~actual;extra=actual&~target
    inside=distance_transform_edt(target)*STEP;outside=distance_transform_edt(~target)*STEP
    tol=.15+math.sqrt(2)*STEP
    residual=(missing&(inside>tol))|(extra&(outside>tol))
    error=max(float(inside[missing].max(initial=0)),float(outside[extra].max(initial=0)))
    area=float(residual.sum()*STEP**2)
    return {'outcome':'pass' if area<=.25 else 'geometry_failure','residual_area_mm2':area,'max_intrusion_mm':error,'iou':float((target&actual).sum()/max(1,(target|actual).sum())),'physical_tolerance_mm':.15,'pixel_allowance_mm':math.sqrt(2)*STEP}

DESCRIPTION='''Make a fabrication SVG flat cutting pattern for the ideal THIN NEUTRAL SURFACE of the described rolled metal sleeve. This is a sheet part, not a field plot. Zero thickness for geometry, no stretch, kerf, springback or seam allowance. Cut out EVERY portion of that surface inside the stated infinite drilling cylinders (both sides where applicable); keep the remaining material. If supplied, remove surface above plane z=a+b*X+c*Y. XYZ are right handed, z is the sleeve axis; all lengths mm; angles radians. Drill axes need normalization. All inputs are complete; do not infer other geometry.
The sleeve has a vertical seam at global azimuth seam_rad. Opening that seam maps theta in [seam_rad,seam_rad+2*pi] into the flat. For a CYLINDER use flat Cartesian u in [-pi*R,pi*R] increasing with theta; v=z-height/2. For a CONICAL FRUSTUM r0 at z=0, r1>r0 at z=height, develop into the annular sector with its virtual cone apex at (u,v)=(0,0), centered about +u. The lower seam is the negative-angle radial edge; increasing theta increases flat polar angle. Use true developed neutral-surface distances, not a projection. There is no target curve formula supplied; derive it from the geometry.
SVG fixed viewBox="-130 -130 260 260", width=height=1000. Flat u points right and v up: use a scale(1,-1) group when writing geometric paths. White background; solid black retained material, white removed areas; no strokes/labels/images. Curves must be accurate to 0.15 mm. SVG paths/polygons are allowed, including sufficiently dense samples. A helper may export numerical contours as genuine vector paths.
Return JSON {"code":"Python that assigns the entire SVG string to svg", "explanation":"..."}. math and np (NumPy) are preloaded, ordinary functions/for loops/comprehensions allowed; no imports, files, external calls or private attributes. contour_svg(x,y,field) is available: x and y are monotonically increasing 1D physical coordinate arrays, field is 2D [len(y),len(x)], positive for black material, negative for white; returns SVG in the required coordinate convention using interpolated marching-squares vector paths. It contains no CAD knowledge or task data. Limit arrays to at most 2000 by 2000. You can also build native SVG paths yourself. Use evaluate_pattern to execute and check each candidate; up to 3 evaluations. It reports SVG compilation and inventory, not hidden target comparisons. Then return the final code.'''

def build():
    if (DATA/'tasks.json').exists():raise ValueError('Frozen pool exists')
    specs=[
      dict(id='rolled_sleeve_oblique_ports',kind='cylinder',R=29.,height=84.,seam_rad=.31,bores=[dict(point=[5,0,37],axis=[1,.37,.61],radius=12),dict(point=[-4,7,62],axis=[.24,1,-.32],radius=8)]),
      dict(id='conical_reducer_oblique_port',kind='cone',r0=18.,r1=46.,height=58.,seam_rad=.47,bores=[dict(point=[4,5,29],axis=[1,.35,.55],radius=14)]),
      dict(id='conical_reducer_trimmed_ports',kind='cone',r0=21.,r1=49.,height=61.,seam_rad=1.1,bores=[dict(point=[2,-3,38],axis=[1,.41,.72],radius=15),dict(point=[12,6,21],axis=[-.35,1,.18],radius=11)],trim_plane=[49,.27,-.18])]
    tasks=[]
    for s in specs:
        t={'id':s.pop('id'),'spec':s};t['prompt']=DESCRIPTION+'\nSPECIFICATION:\n'+json.dumps(s)
        t['reference_sha256']=hashlib.sha256(reference(t).tobytes()).hexdigest();tasks.append(t)
    write(DATA/'tasks.json',{'version':'development-screen-v1','scope':'Original rolled sheet neutral-surface fabrication patterns; generation only; no springback/finite-thickness validity claim','criteria':{'tolerance_mm':.15,'raster_size':SIZE,'residual_area_limit_mm2':.25,'confirmation':'Three completed high-effort attempts; execution/interface errors excluded; inspect reference and output before admission.'},'tasks':tasks})
    print('Built',len(tasks),'frozen tasks')

TOOL={'type':'function','name':'evaluate_pattern','description':'Run numerical SVG generator; returns execution and SVG inventory only; no target answer.','parameters':{'type':'object','properties':{'code':{'type':'string'}},'required':['code'],'additionalProperties':False},'strict':True}
def run(out,ids):
    manifest=json.loads((DATA/'tasks.json').read_text());key=api_key();tasks=[t for t in manifest['tasks'] if not ids or t['id'] in ids.split(',')]
    write(out/'protocol.json',dict(model='gpt-6-astra',effort='high',max_output_tokens=16000,max_tool_calls=3,manifest_sha256=hashlib.sha256((DATA/'tasks.json').read_bytes()).hexdigest(),tool=TOOL))
    for t in tasks:
        folder=out/t['id'];folder.mkdir(parents=True,exist_ok=True)
        if (folder/'result.json').exists():continue
        messages=[{'role':'user','content':t['prompt']}];record={'id':t['id'],'status':'started','usage':[]};calls=0
        try:
            for turn in range(4):
                payload={'model':'gpt-6-astra','input':messages,'reasoning':{'effort':'high'},'max_output_tokens':16000,'store':False,'include':['reasoning.encrypted_content']}
                if calls<3:payload.update(tools=[TOOL],tool_choice='required' if turn==0 else 'auto',parallel_tool_calls=False)
                write(folder/f'request-{turn}.json',payload)
                req=urllib.request.Request(ENDPOINT,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
                with urllib.request.urlopen(req,timeout=600) as r:raw=json.load(r)
                write(folder/f'response-{turn}.json',raw);record['usage'].append(raw.get('usage',{}));messages.extend(raw['output'])
                if raw['status']!='completed':record['status']='incomplete';break
                fc=[o for o in raw['output'] if o['type']=='function_call']
                if fc:
                    for call in fc:
                        code=json.loads(call['arguments'])['code'];result=execute(code,folder/f'tool-{calls}');calls+=1
                        messages.append({'type':'function_call_output','call_id':call['call_id'],'output':json.dumps(result)})
                        print(t['id'],'tool',calls,result,flush=True)
                else:
                    text=''.join(c['text'] for o in raw['output'] if o['type']=='message' for c in o['content'] if c['type']=='output_text')
                    (folder/'final.txt').write_text(text)
                    if text.startswith('~~~'):text=text.split('\n',1)[1].rsplit('~~~',1)[0]
                    answer=json.loads(text);write(folder/'answer.json',answer);result=execute(answer['code'],folder/'final')
                    record['execution']=result;record['status']='completed' if result['status']=='completed' else 'execution_error'
                    if result['status']=='completed':record['grade']=score(t,(folder/'final/output.svg').read_text(),folder/'final')
                    break
            if record['status']=='started':record['status']='no_final'
        except Exception as e:record.update(status='operational_error',error_type=type(e).__name__,error=str(e).replace(key,'[REDACTED]')[:500])
        record['tool_calls']=calls;write(folder/'result.json',record);print(t['id'],record['status'],record.get('grade'),flush=True)
    rows=[json.loads(p.read_text()) for p in out.glob('*/result.json')];write(out/'summary.json',{'rows':rows})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','run','worker']);p.add_argument('--output',type=Path);p.add_argument('--folder',type=Path);p.add_argument('--ids');a=p.parse_args()
    if a.command=='build':build()
    elif a.command=='run':run(a.output,a.ids)
    else:
        try:
            svg=numeric_execute((a.folder/'candidate.py').read_text());(a.folder/'output.svg').write_text(svg)
            root=ET.fromstring(svg);r={'status':'completed','svg_bytes':len(svg.encode()),'paths':sum(e.tag.split('}')[-1]=='path' for e in root.iter())}
        except Exception as e:r={'status':'execution_error','error_type':type(e).__name__,'error':str(e)[:800]}
        write(a.folder/'execution.json',r)

