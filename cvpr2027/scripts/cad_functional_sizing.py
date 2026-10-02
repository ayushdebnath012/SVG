"""Finite-catalog structural drawing synthesis with exhaustive feasibility controls.

This is an explicitly idealized 2D frame design/search test, not a building-code
or product-safety certificate. Functional design failures are distinct from
incorrectly copied geometry and from an analysis-only numerical reporting error.
"""
import argparse,copy,hashlib,itertools,json,math,sys,time,urllib.request,urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import xml.etree.ElementTree as ET
import cad_astra_benchmark as fem
from cad_native_probe import api_key,write,ENDPOINT
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data/cad-functional-sizing'

def prepare(task):
    m=task['model'];ids=list(m['nodes']);nd=3*len(ids);ix={n:i for i,n in enumerate(ids)}
    fixed=sorted({3*ix[n]+d for n,ds in m['supports'].items() for d in ds});free=np.setdiff1d(np.arange(nd),fixed)
    F=np.zeros((nd,len(task['load_cases'])))
    for j,loads in enumerate(task['load_cases']):
        for n,f in loads.items():F[3*ix[n]:3*ix[n]+3,j]=f
    kernels=[]
    for v in m['members']:
        a,b=np.array(m['nodes'][v['a']]),np.array(m['nodes'][v['b']]);L=float(np.linalg.norm(b-a))
        k1,T,_,_=fem.stiffness(a,b,v['E'],v['b_mm'],1.)
        axial=np.zeros((6,6));axial[np.ix_([0,3],[0,3])]=v['E']*v['b_mm']/L*np.array([[1,-1],[-1,1]])
        bend=k1-axial;dofs=np.array([3*ix[v['a']]+i for i in range(3)]+[3*ix[v['b']]+i for i in range(3)])
        kernels.append((axial,bend,T,dofs,L))
    return ids,free,F,kernels

def evaluate(task,designs):
    ds=np.asarray(designs,dtype=int)
    if not np.array_equal(ds,np.asarray(designs)):raise ValueError('Catalog indices must be integers')
    if ds.ndim!=2 or ds.shape[1]!=len(task['model']['members']) or np.any(ds<0) or np.any(ds>=len(task['catalog_h_mm'])):raise ValueError('One valid catalog index per member is required')
    ids,free,F,kernels=prepare(task);n=len(ds);nd=len(F);m=task['model'];H=np.array(task['catalog_h_mm'])[ds]
    K=np.zeros((n,nd,nd));local=[];mass=np.zeros(n)
    for j,(ka,kb,T,dofs,L) in enumerate(kernels):
        h=H[:,j];k=ka[None]*h[:,None,None]+kb[None]*h[:,None,None]**3
        kg=np.einsum('ai,nab,bj->nij',T,k,T)
        for a,ga in enumerate(dofs):
            for b,gb in enumerate(dofs):K[:,ga,gb]+=kg[:,a,b]
        local.append(k);mass+=L*m['members'][j]['b_mm']*h*task['density_kg_mm3']
    U=np.zeros((n,nd,F.shape[1]));U[:,free,:]=np.linalg.solve(K[:,free][:,:,free],np.broadcast_to(F[free],(n,len(free),F.shape[1])))
    stress=np.zeros(n);buckling=np.zeros(n);per_stress=[];per_buckle=[]
    for j,(_,_,T,dofs,L) in enumerate(kernels):
        h=H[:,j];v=m['members'][j];q=np.einsum('nab,bc,ncl->nal',local[j],T,U[:,dofs,:]);A=v['b_mm']*h;I=v['b_mm']*h**3/12
        end1=np.abs(q[:,0,:])/A[:,None]+np.abs(q[:,2,:])*(h/2/I)[:,None]
        end2=np.abs(q[:,3,:])/A[:,None]+np.abs(q[:,5,:])*(h/2/I)[:,None]
        st=np.maximum(end1,end2).max(axis=1);comp=np.maximum(np.maximum(q[:,0,:],-q[:,3,:]),0).max(axis=1)
        bu=task['buckling_factor']*comp/(math.pi**2*v['E']*I/L**2)
        stress=np.maximum(stress,st);buckling=np.maximum(buckling,bu);per_stress.append(st);per_buckle.append(bu)
    ux=np.abs(U[:,0::3,:]).max(axis=(1,2));uy=np.abs(U[:,1::3,:]).max(axis=(1,2));lim=task['limits']
    ratios=np.stack([stress/lim['stress_mpa'],ux/lim['ux_mm'],uy/lim['uy_mm'],buckling],axis=1)
    return {'mass_kg':mass,'stress_mpa':stress,'ux_mm':ux,'uy_mm':uy,'buckling_utilization':buckling,'max_utilization':ratios.max(axis=1),'per_member_stress':np.stack(per_stress,axis=1),'per_member_buckling':np.stack(per_buckle,axis=1)}

def rows(task,designs):
    r=evaluate(task,designs);out=[]
    for i,d in enumerate(designs):
        v={k:float(a[i]) for k,a in r.items() if a.ndim==1};v.update(design=list(map(int,d)),structurally_feasible=v['max_utilization']<=1+1e-8)
        if 'mass_cap_kg' in task:v['all_constraints_pass']=v['structurally_feasible'] and v['mass_kg']<=task['mass_cap_kg']+1e-8
        out.append(v)
    return out

def exhaustive(task):
    dims=len(task['model']['members']);ncat=len(task['catalog_h_mm']);best=None;feasible=0;pool=[]
    combos=itertools.product(range(ncat),repeat=dims)
    while True:
        ds=list(itertools.islice(combos,512))
        if not ds:break
        for r in rows(task,ds):
            if r['structurally_feasible']:
                feasible+=1
                if best is None or r['mass_kg']<best['mass_kg']:best=r
                pool.append(r)
    if best is None:raise ValueError('No feasible design; do not release task')
    cap=round(best['mass_kg']*1.01,6)
    return {'best':best,'mass_cap_kg':cap,'feasible_before_mass_cap':feasible,'feasible_after_mass_cap':sum(r['mass_kg']<=cap for r in pool),'enumerated':ncat**dims}

def make_task(i):
    # All are related frame-layout families; do not claim cross-domain diversity.
    name,source,edited,_=fem.models()[1]
    m=copy.deepcopy(edited if i%2 else source)
    for v in m['members']:v['b_mm']=80.;v['h_mm']=100.
    if i>=2:
        m['nodes']['C'][0]=m['nodes']['F'][0]=8900
        m['nodes']['D'][1]=m['nodes']['E'][1]=m['nodes']['F'][1]=3200
    loads=[]
    for wind,gravity in [(1,1),(-.8,1.25),(.4,1.7)]:
        loads.append({n:[f[0]*4*wind,f[1]*4*gravity,f[2]] for n,f in m['loads'].items()})
    m={k:m[k] for k in ('nodes','members','supports')}
    for member in m['members']:member.pop('h_mm')
    t={'id':f'frame_catalog_{i+1}','model':m,'load_cases':loads,'catalog_h_mm':[120.,170.,240.,330.],
       'density_kg_mm3':7.85e-6,'buckling_factor':2.,'limits':{'stress_mpa':120.+i*10,'ux_mm':10.+i,'uy_mm':8.+i},
       'scope':'Idealized linear 2D rigid-jointed rectangular-section steel frame, nodal forces, all support DOFs clamped. No self-weight, shear deformation, connection compliance, global buckling, plasticity, out-of-plane behavior or code compliance. Euler member check uses K=1 and factor 2, independently from linear FEM.'}
    return t

def make_braced():
    t=make_task(0);t['id']='braced_frame_catalog_1'
    nodes={f'N{x}{y}':[x*3100.+y*110.,y*2700.] for y in range(3) for x in range(3)}
    edges=[(f'N{x}{y}',f'N{x}{y+1}') for y in range(2) for x in range(3)]
    edges += [(f'N{x}{y}',f'N{x+1}{y}') for y in (1,2) for x in range(2)]
    edges += [('N00','N11'),('N11','N22')]
    t['model']={'nodes':nodes,'supports':{f'N{x}0':[0,1,2] for x in range(3)},'members':[{'id':f'M{i+1}','a':a,'b':b,'E':200000.,'b_mm':60.} for i,(a,b) in enumerate(edges)]}
    t['catalog_h_mm']=[80.,140.,240.]
    t['load_cases']=[{'N02':[45000,-40000,0],'N12':[5000,-70000,0],'N22':[30000,-90000,0],'N21':[20000,-30000,0]},
                     {'N02':[-55000,-80000,0],'N12':[0,-90000,0],'N22':[-20000,-35000,0],'N01':[-15000,-60000,0]},
                     {'N02':[12000,-100000,0],'N12':[0,-150000,0],'N22':[8000,-80000,0]}]
    t['load_cases']=[{n:[4*v for v in f] for n,f in loads.items()} for loads in t['load_cases']]
    t['limits']={'stress_mpa':120.,'ux_mm':4.6,'uy_mm':2.}
    return t

def make_three_bay():
    t=make_task(0);t['id']='three_bay_catalog_1';xs=[0,2900,6600,9000];ys=[0,3100,6900]
    nodes={f'N{x}{y}':[float(xx+80*y),float(yy)] for y,yy in enumerate(ys) for x,xx in enumerate(xs)}
    edges=[(f'N{x}{y}',f'N{x}{y+1}') for y in range(2) for x in range(4)]
    edges += [(f'N{x}{y}',f'N{x+1}{y}') for y in (1,2) for x in range(3)]
    t['model']={'nodes':nodes,'supports':{f'N{x}0':[0,1,2] for x in range(4)},'members':[{'id':f'M{i+1}','a':a,'b':b,'E':200000.,'b_mm':80.} for i,(a,b) in enumerate(edges)]}
    t['catalog_h_mm']=[140.,240.,380.]
    t['load_cases']=[{'N02':[50000,-100000,0],'N12':[0,-180000,0],'N22':[0,-120000,0],'N32':[30000,-200000,0],'N31':[20000,-60000,0]},
                     {'N02':[-35000,-160000,0],'N12':[0,-200000,0],'N22':[0,-70000,0],'N32':[-45000,-90000,0],'N01':[-30000,-100000,0]},
                     {'N02':[12000,-210000,0],'N12':[0,-270000,0],'N22':[0,-100000,0],'N32':[8000,-300000,0]}]
    t['limits']={'stress_mpa':120.,'ux_mm':12.,'uy_mm':4.}
    return t

def drawing(t,design):
    m=t['model'];hs=[t['catalog_h_mm'][i] for i in design];xs=[p[0] for p in m['nodes'].values()];ys=[p[1] for p in m['nodes'].values()];sc=min(700/max(xs),530/max(ys));base=650
    height=max(850,90+len(hs)*68+150)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" data-render-version="2" width="1200" height="{height}" viewBox="0 0 1200 {height}"><rect width="1200" height="{height}" fill="white"/><g font-family="sans-serif" fill="#162d40">',f'<text x="30" y="30" font-size="19">{t["id"]} | idealized structural elevation and section schedule | mm</text>']
    for v,h in zip(m['members'],hs):
        a,b=m['nodes'][v['a']],m['nodes'][v['b']];x1,y1=35+a[0]*sc,base-a[1]*sc;x2,y2=35+b[0]*sc,base-b[1]*sc
        out.append(f'<line data-member="{v["id"]}" data-b-mm="{v["b_mm"]}" data-h-mm="{h}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#41718a" stroke-width="{h*sc}"/><text x="{(x1+x2)/2+8}" y="{(y1+y2)/2-8}" font-size="12" stroke="white" stroke-width="2" paint-order="stroke">{v["id"]}</text>')
    for n,(x,y) in m['nodes'].items():out.append(f'<circle cx="{35+x*sc}" cy="{base-y*sc}" r="3"/><text x="{35+x*sc+8}" y="{base-y*sc+14}" font-size="12" stroke="white" stroke-width="2" paint-order="stroke">{n}: ({x},{y})</text>')
    for j,(v,h) in enumerate(zip(m['members'],hs)):
        y=90+j*68;out.append(f'<rect data-section="{v["id"]}" x="820" y="{y}" width="{v["b_mm"]/5}" height="{h/5}" fill="none" stroke="#41718a"/><text x="880" y="{y+20}" font-size="13">{v["id"]}: {v["b_mm"]} x {h}</text>')
    out.extend([f'<text x="30" y="{height-120}" font-size="14">Base nodes clamped. Rigid joints. Load cases and verification assumptions: accompanying manifest.</text>',f'<text x="30" y="{height-92}" font-size="14">Mass cap {t.get("mass_cap_kg",0):.3f} kg. Geometry/section data generate both this SVG and the verification model.</text>',f'<text x="30" y="{height-62}" font-size="13">Research model only. Section rectangles use a separate scale. Not a construction or manufacturing drawing.</text></g></svg>'])
    return ''.join(out)

def read_drawing(t,svg):
    """Read actual visible line widths and section rectangles, not metadata values."""
    root=ET.fromstring(svg);m=t['model'];sc=700/max(max(p[0] for p in m['nodes'].values()),max(p[1] for p in m['nodes'].values()))
    if root.get('data-render-version')=='2':sc=min(700/max(p[0] for p in m['nodes'].values()),530/max(p[1] for p in m['nodes'].values()))
    lines={e.get('data-member'):e for e in root.iter() if e.tag.endswith('}line') and e.get('data-member')}
    sections={e.get('data-section'):e for e in root.iter() if e.tag.endswith('}rect') and e.get('data-section')}
    if set(lines)!=set(v['id'] for v in m['members']) or set(sections)!=set(lines):raise ValueError('Drawing member inventory mismatch')
    indices=[]
    for v in m['members']:
        line,rect=lines[v['id']],sections[v['id']];a,b=m['nodes'][v['a']],m['nodes'][v['b']]
        want=[35+a[0]*sc,650-a[1]*sc,35+b[0]*sc,650-b[1]*sc]
        if not np.allclose([float(line.get(k)) for k in ('x1','y1','x2','y2')],want,rtol=0,atol=1e-6):raise ValueError('Incorrect drawn centerline')
        h=float(line.get('stroke-width'))/sc
        if abs(float(rect.get('height'))*5-h)>1e-6 or abs(float(rect.get('width'))*5-v['b_mm'])>1e-6:raise ValueError('Section and elevation disagree')
        ix=int(np.argmin(np.abs(np.array(t['catalog_h_mm'])-h)))
        if abs(t['catalog_h_mm'][ix]-h)>1e-6:raise ValueError('Drawn height outside catalog')
        indices.append(ix)
    return indices

def build():
    if (DATA/'tasks.json').exists():raise ValueError('Frozen task pool exists')
    ts=[]
    for i in range(4):
        t=make_task(i);start=time.time();oracle=exhaustive(t);t['mass_cap_kg']=oracle['mass_cap_kg'];t['oracle']=oracle;ts.append(t)
        d=DATA/t['id'];d.mkdir(parents=True,exist_ok=True);(d/'feasible-reference.svg').write_text(drawing(t,oracle['best']['design']))
        print(t['id'],oracle['best']['design'],oracle['best']['mass_kg'],oracle['feasible_after_mass_cap'],'feasible near optimum',round(time.time()-start,1),'sec',flush=True)
    write(DATA/'tasks.json',{'version':'functional-sizing-v1','tasks':ts,'selection_policy':'Resource-bounded engineering design search, not a claim of permanent shape incapability. Completed final drawings failing an explicit functional constraint are candidates; 3 independent reviewed failures required. All four variants share a frame ancestry and do not meet the three-family training gate.'})

def build_braced(three_bay=False):
    if (DATA/'tasks.json').exists():raise ValueError('Frozen task pool exists')
    t=make_three_bay() if three_bay else make_braced();oracle=exhaustive(t);t['mass_cap_kg']=oracle['mass_cap_kg'];t['oracle']=oracle
    write(DATA/'tasks.json',{'version':'functional-sizing-three-bay-v1' if three_bay else 'functional-sizing-braced-v1','tasks':[t],'selection_policy':'Separate adaptive-discovery extension after earlier cases passed. Three fresh independent completed functional failures required, with no reference/interface defect. Resource bounded; not proof of permanent inability or a new shape class.'})
    (DATA/'feasible-reference.svg').write_text(drawing(t,oracle['best']['design']))
    print(t['id'],oracle,flush=True)

SYSTEM='''Design a dimensioned structural-frame SVG by choosing each member cross-section from the given finite catalog. Your chosen dimensions must meet ALL stated limits for ALL load cases, including the total mass cap. The exact geometry and sections you choose will be automatically exported to an SVG elevation plus section schedule, then independently re-analyzed. This is shape/design synthesis, not merely predicting an analysis number. A valid design exists. No particular hidden design is required: every design satisfying all constraints passes.
You have evaluate_designs to analyze designs. Four calls, at most 256 designs per call (1024 FEM design evaluations total). Use this budget strategically. Each call can evaluate explicit designs or a Cartesian grid: fix a base vector, give axes and the choices for those axes. Returned results include the best feasible designs by mass and best infeasible designs by maximum constraint utilization. No hidden reference, mass-optimal answer, or future samples are provided. Unreturned candidates count against the evaluation budget. Indices are 0-based. Use at least one call.
The tool executes the supplied idealized 2D frame model using linear Euler-Bernoulli frame FEM. Max absolute horizontal/vertical displacements are over all nodes and load cases. Stress is max end-fibre |N|/A+|M|h/(2I). The separate per-member Euler check is 2*N_compression/(pi^2*E*I/L^2)<=1. Member K=1, I=b*h^3/12, A=b*h, density as given. Changing h changes the physical section, not just a note.
Return JSON {"design":[catalog indices in member order],"explanation":"design/checks and any limitations"}. Do not claim whole-building safety. The mass cap is a requirement, not a request to prove global optimality.'''
TOOL={'type':'function','name':'evaluate_designs','description':'Analyze explicit designs or a Cartesian grid of catalog selections; 256 designs max per call. Use mode explicit with designs, or mode grid with base, axes and choices. Irrelevant arrays must be empty. Returns top 8 feasible and top 8 infeasible; no target answer.',
 'parameters':{'type':'object','properties':{'mode':{'type':'string','enum':['explicit','grid']},'designs':{'type':'array','items':{'type':'array','items':{'type':'integer'}}},'base':{'type':'array','items':{'type':'integer'}},'axes':{'type':'array','items':{'type':'integer'}},'choices':{'type':'array','items':{'type':'array','items':{'type':'integer'}}}},'required':['mode','designs','base','axes','choices'],'additionalProperties':False},'strict':True}

def tool_call(t,args):
    if args['mode']=='explicit':ds=args['designs']
    else:
        if len(set(args['axes']))!=len(args['axes']) or len(args['axes'])!=len(args['choices']):raise ValueError('unique axes and matching choices required')
        count=math.prod(len(v) for v in args['choices'])
        if count>256:raise ValueError('256 designs per call maximum')
        ds=[]
        for combo in itertools.product(*args['choices']):
            d=list(args['base'])
            for j,v in zip(args['axes'],combo):d[j]=v
            ds.append(d)
    if not 1<=len(ds)<=256:raise ValueError('1 to 256 designs required')
    rr=rows(t,ds);feas=sorted([r for r in rr if r['structurally_feasible']],key=lambda r:r['mass_kg']);bad=sorted([r for r in rr if not r['structurally_feasible']],key=lambda r:(r['max_utilization'],r['mass_kg']))
    return {'evaluations':len(rr),'all_constraints_pass_count':sum(r['all_constraints_pass'] for r in rr),'structurally_feasible_count':len(feas),'best_feasible_by_mass':feas[:8],'best_infeasible_by_utilization':bad[:8]}

def run(out,ids,sample,repair_interface=False):
    manifest=json.loads((DATA/'tasks.json').read_text());chosen=[t for t in manifest['tasks'] if not ids or t['id'] in ids.split(',')];key=api_key()
    system=SYSTEM+('\nInterface correction allowance: invalid tool arguments do not consume one of the four analysis calls or any design evaluations. At most two invalid requests may be corrected. All valid analyses remain limited to four calls and 1024 evaluated designs.' if repair_interface else '')
    protocol={'model':'gpt-6-astra','reasoning_effort':'high','max_output_tokens':16000,'max_tool_calls':4,'design_evaluations_per_call':256,'sample':sample,'system':system,'tool':TOOL,'task_sha256':hashlib.sha256((DATA/'tasks.json').read_bytes()).hexdigest(),'implementation_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'interface_correction_allowance':2 if repair_interface else 0,'ids':[t['id'] for t in chosen]}
    if (out/'protocol.json').exists():raise ValueError('Use a fresh output directory')
    write(out/'protocol.json',protocol)
    def one(t):
        d=out/t['id'];d.mkdir(parents=True,exist_ok=True)
        if (d/'result.json').exists():raise ValueError('Do not overwrite previous trial')
        public={k:v for k,v in t.items() if k!='oracle'};messages=[{'role':'system','content':system},{'role':'user','content':json.dumps(public)}];rec={'id':t['id'],'sample':sample,'status':'started','usage':[]};calls=0;attempts=0;errors=0;neval=0;write(d/'result.json',rec)
        try:
            for turn in range(7 if repair_interface else 5):
                payload={'model':'gpt-6-astra','input':messages,'reasoning':{'effort':'high'},'max_output_tokens':16000,'store':False,'include':['reasoning.encrypted_content']}
                if calls<4:payload.update(tools=[TOOL],tool_choice='required' if turn==0 else 'auto',parallel_tool_calls=False)
                write(d/f'request-{turn}.json',payload);req=urllib.request.Request(ENDPOINT,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
                with urllib.request.urlopen(req,timeout=900) as response:raw=json.load(response)
                write(d/f'response-{turn}.json',raw);rec['usage'].append(raw.get('usage',{}))
                if raw['status']!='completed':rec['status']='budget_or_incomplete';break
                messages.extend(raw['output']);fc=[v for v in raw['output'] if v['type']=='function_call']
                if fc:
                    for c in fc:
                        try:r=tool_call(t,json.loads(c['arguments']));neval+=r['evaluations'];calls+=1
                        except Exception as e:
                            r={'interface_error':str(e)};errors+=1
                            if not repair_interface:calls+=1
                        write(d/f'tool-{attempts}.json',r);attempts+=1;messages.append({'type':'function_call_output','call_id':c['call_id'],'output':json.dumps(r)});print(t['id'],'tool',attempts,r.get('all_constraints_pass_count'),flush=True)
                    if repair_interface and errors>2:rec['status']='interface_exhausted';break
                else:
                    text=''.join(c['text'] for v in raw['output'] if v['type']=='message' for c in v['content'] if c['type']=='output_text');(d/'final.txt').write_text(text)
                    if text.startswith('```'):text=text.split('\n',1)[1].rsplit('```',1)[0]
                    answer=json.loads(text);write(d/'answer.json',answer);svg=drawing(t,answer['design']);(d/'output.svg').write_text(svg);drawn=read_drawing(t,svg);grade=rows(t,[drawn])[0];rec.update(status='completed',grade=grade,svg_readback_design=drawn);break
            if rec['status']=='started':rec['status']='no_final'
        except Exception as e:rec.update(status='operational_error',error=str(e).replace(key,'[REDACTED]')[:500])
        rec.update(tool_calls=calls,tool_attempts=attempts,interface_errors=errors,design_evaluations=neval);write(d/'result.json',rec);print('END',t['id'],rec['status'],rec.get('grade',{}).get('all_constraints_pass'),flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(one,chosen))
    write(out/'summary.json',{'records':[json.loads(p.read_text()) for p in sorted(out.glob('*/result.json'))]})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','build-braced','build-three-bay','run']);p.add_argument('--output',type=Path);p.add_argument('--data',type=Path);p.add_argument('--ids');p.add_argument('--sample',type=int,default=0);p.add_argument('--repair-interface',action='store_true');a=p.parse_args()
    if a.data:DATA=a.data
    if a.command=='build':build()
    elif a.command=='build-braced':build_braced()
    elif a.command=='build-three-bay':build_braced(True)
    else:run(a.output,a.ids,a.sample,a.repair_interface)
