"""Single-layer grid PCB routing pilot with connectivity and clearance checks.

Abstract CAD routing geometry, not an electronic circuit or fabrication signoff.
The model may choose any compliant routing. No reference routing is exposed.
"""
import argparse,base64,collections,hashlib,itertools,json,math,random,time,urllib.request
from pathlib import Path
from cad_native_probe import api_key,write,ENDPOINT
from render_svg_gallery import render
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data/cad-trace-routing'
COLORS=['#bd303e','#1869ad','#247942','#985aba','#c17619','#13878c']

def bfs(start,end,blocked,w,h):
    q=collections.deque([start]);parent={start:None}
    while q:
        p=q.popleft()
        if p==end:
            path=[]
            while p is not None:path.append(list(p));p=parent[p]
            return path[::-1]
        for d in [(1,0),(0,1),(-1,0),(0,-1)]:
            n=(p[0]+d[0],p[1]+d[1])
            if 0<=n[0]<w and 0<=n[1]<h and n not in blocked and n not in parent:parent[n]=p;q.append(n)
    return None

def sequential(t,order):
    pads={tuple(p) for n in t['nets'] for p in (n['start'],n['end'])};used={tuple(p) for p in t['blocked']};routes={}
    for i in order:
        n=t['nets'][i];a,b=tuple(n['start']),tuple(n['end']);path=bfs(a,b,used|(pads-{a,b}),t['width'],t['height'])
        if path is None:return None
        routes[n['id']]=path;used.update(map(tuple,path))
    return routes

def expand(path):
    if not isinstance(path,list) or len(path)<2:raise ValueError('Each route needs at least two vertices')
    pts=[]
    for v in path:
        if len(v)!=2 or any(type(x) not in (int,float) or not math.isfinite(x) or int(x)!=x for x in v):raise ValueError('Integer grid coordinates required')
        pts.append(tuple(map(int,v)))
    out=[pts[0]]
    for a,b in zip(pts,pts[1:]):
        dx=b[0]-a[0];dy=b[1]-a[1]
        if dx and dy:raise ValueError('Only horizontal or vertical segments allowed')
        if abs(dx)+abs(dy)>1000:raise ValueError('Segment outside supported board range')
        count=abs(dx)+abs(dy)
        if count==0:continue
        out.extend((a[0]+j*(0 if dx==0 else 1 if dx>0 else -1),a[1]+j*(0 if dy==0 else 1 if dy>0 else -1)) for j in range(1,count+1))
    return out

def grade(t,routes):
    bad=[];occupied={};blocked=set(map(tuple,t['blocked']));pads={tuple(p):n['id'] for n in t['nets'] for p in (n['start'],n['end'])};length=0
    nets={n['id']:n for n in t['nets']}
    for extra in set(routes)-set(nets):bad.append({'kind':'unknown_net','net':extra})
    for ident,n in nets.items():
        if ident not in routes:bad.append({'kind':'missing_net','net':ident});continue
        try:ps=expand(routes[ident])
        except Exception as e:bad.append({'kind':'invalid_route','net':ident,'detail':str(e)});continue
        forward = ps[0] == tuple(n['start']) and ps[-1] == tuple(n['end'])
        backward = ps[-1] == tuple(n['start']) and ps[0] == tuple(n['end'])
        if not (forward or backward):bad.append({'kind':'wrong_endpoints','net':ident})
        length+=(len(ps)-1)*2
        for p in set(ps):
            if not (0<=p[0]<t['width'] and 0<=p[1]<t['height']):bad.append({'kind':'off_board','net':ident,'point':p})
            if p in blocked:bad.append({'kind':'keepout','net':ident,'point':p})
            if p in pads and pads[p]!=ident:bad.append({'kind':'foreign_pad','net':ident,'other':pads[p],'point':p})
            if p in occupied and occupied[p]!=ident:bad.append({'kind':'crossing_or_contact','net':ident,'other':occupied[p],'point':p})
            occupied[p]=ident
    return {'pass':not bad,'violation_count':len(bad),'violations':bad[:100],'total_trace_length_mm':length,'scope':'Orthogonal integer-grid routes, one copper layer, endpoint connectivity, board bounds, keepout and inter-net clearance. No optimal-length target. Grid pitch 2 mm, trace width 0.6 mm, pad diameter 1 mm, keepout square side 1.2 mm, minimum clearance 0.4 mm. Distinct neighboring grid routes retain at least 1.4 mm trace-edge gap.'}

def compress(ps):
    out=[ps[0]]
    for a,b,c in zip(ps,ps[1:],ps[2:]):
        if (b[0]-a[0],b[1]-a[1])!=(c[0]-b[0],c[1]-b[1]):out.append(b)
    out.append(ps[-1]);return out

def drawing(t,routes=None):
    routes=routes or {};s=35;ox=70;oy=130;W=760;H=760
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" font-size="12">',f'<text x="35" y="30" font-size="21">Single layer PCB trace routing | grid pitch 2 mm</text>','<text x="35" y="55">Route A to A, B to B, and so on. Gray squares are keepouts.</text>','<text x="35" y="76">Grid X increases right; Y increases down. No vias or trace crossings.</text>']
    parts.append(f'<rect x="{ox-20}" y="{oy-20}" width="{(t["width"]-1)*s+40}" height="{(t["height"]-1)*s+40}" fill="#f7faf7" stroke="#253b30"/>')
    for x in range(t['width']):
        parts.append(f'<text x="{ox+x*s-4}" y="{oy-30}">{x}</text>')
        for y in range(t['height']):parts.append(f'<circle cx="{ox+x*s}" cy="{oy+y*s}" r="1.2" fill="#b5c1b8"/>')
    for y in range(t['height']):parts.append(f'<text x="{ox-40}" y="{oy+y*s+4}">{y}</text>')
    for x,y in t['blocked']:parts.append(f'<rect x="{ox+x*s-10.5}" y="{oy+y*s-10.5}" width="21" height="21" fill="#777"/>')
    for i,n in enumerate(t['nets']):
        color=COLORS[i];ident=n['id']
        if ident in routes:
            points=' '.join(f'{ox+x*s},{oy+y*s}' for x,y in routes[ident]);parts.append(f'<polyline data-net="{ident}" points="{points}" fill="none" stroke="{color}" stroke-width="10.5" stroke-linejoin="round" stroke-linecap="round"/>')
        for x,y in (n['start'],n['end']):parts.append(f'<circle cx="{ox+x*s}" cy="{oy+y*s}" r="8.75" fill="white" stroke="{color}" stroke-width="2"/><text x="{ox+x*s-4}" y="{oy+y*s+4}" fill="{color}">{ident}</text>')
    parts+=['<text x="35" y="635">Trace width 0.6 mm | Pad diameter 1.0 mm | Minimum clearance 0.4 mm</text>','<text x="35" y="658">Orthogonal grid routes only. Gray keepouts are 1.2 x 1.2 mm.</text>','<text x="35" y="686">Research layout: geometry and connectivity only; no electrical performance claim.</text>','</g></svg>']
    return ''.join(parts)

def build():
    if (DATA/'tasks.json').exists():raise ValueError('Frozen task exists')
    # Generate feasible original instances; choose a case where simple routing order matters.
    for seed in range(1000,5000):
        rng=random.Random(seed);w,h=17,13;points=[(x,y) for x in range(w) for y in range(h)];ends=rng.sample(points,12)
        nets=[{'id':chr(65+i),'start':list(ends[2*i]),'end':list(ends[2*i+1])} for i in range(6)]
        if any(abs(a[0]-b[0])+abs(a[1]-b[1])<8 for a,b in zip(ends[::2],ends[1::2])):continue
        obstacles=rng.sample([p for p in points if p not in ends],35);t={'id':'crowded_connector_board','width':w,'height':h,'blocked':[list(p) for p in obstacles],'nets':nets}
        orders=list(itertools.permutations(range(6)));rng.shuffle(orders);solutions=[]
        for order in orders[:80]:
            route=sequential(t,order)
            if route is not None:solutions.append((order,route))
        if not (1<=len(solutions)<=5):continue
        order,route=solutions[0];route={k:compress(v) for k,v in route.items()};assert grade(t,route)['pass']
        t['reference_routes']=route;t['generation_seed']=seed
        write(DATA/'tasks.json',{'version':'pcb-grid-routing-v1','tasks':[t],'selection':'Chosen before model testing from feasible seeded boards where 1 to 5 of 80 sampled shortest-path routing orders succeed. This screens classical order sensitivity, not model failures.','preflight':{'reference_grade':grade(t,route),'successful_sequential_orders':len(solutions),'tested_orders':80,'reference_order':order},'admission':'Three independent completed high-effort routing failures, with geometric audit. Four checker calls, no arbitrary code execution; configuration-specific routing reliability, not proof that Astra cannot solve the task with a router or more tools.'})
        (DATA/'source.svg').write_text(drawing(t));(DATA/'reference.svg').write_text(drawing(t,route));render(DATA/'source.svg',DATA/'source.png',800);render(DATA/'reference.svg',DATA/'reference.png',800);print('Frozen seed',seed,'baseline success',len(solutions),'/80',flush=True);return
    raise RuntimeError('No suitable feasible instance found')

SYSTEM='''Create a single-layer PCB trace layout. Return JSON {"routes":{"A":[[x,y],...],...},"explanation":"..."}. Coordinates are integer grid coordinates; every segment must be horizontal or vertical. Intermediate collinear grid points may be omitted. Any valid routing passes: no hidden preferred shape or shortest length is required. Routes are exported to SVG polylines at physical scale and independently checked. Join each net's two pads; never touch another net's pad or route; avoid all blocked sites and stay within the grid. Grid spacing is 2 mm; trace width 0.6 mm; pad diameter 1 mm; square keepouts side 1.2 mm; clearance 0.4 mm. Under these stipulated orthogonal grid rules, using distinct unblocked grid sites and avoiding all foreign pads is sufficient for clearance. No vias or extra layers. A feasible complete routing exists. You may use check_routes four times to check candidate routings, including partial routings. It reports actual violations, never an optimal path or hidden reference. This tests planning with checker feedback; no arbitrary-code execution tool is available. Do not claim whole-circuit electrical correctness.'''
TOOL={'type':'function','name':'check_routes','description':'Check proposed PCB trace polylines for missing nets, endpoint errors, keepout violations, off-board vertices and cross-net contacts. No solution paths are supplied.','parameters':{'type':'object','properties':{'routes':{'type':'object','additionalProperties':{'type':'array','items':{'type':'array','items':{'type':'integer'}}}}},'required':['routes']},'strict':False}

def run(out,sample):
    if out.exists():raise ValueError('Use a fresh output directory')
    file=DATA/'tasks.json';t=json.loads(file.read_text())['tasks'][0];key=api_key();public={k:v for k,v in t.items() if k not in ('reference_routes','generation_seed')}
    write(out/'protocol.json',{'model':'gpt-6-astra','effort':'high','sample':sample,'max_output_tokens':16000,'max_checker_calls':4,'system':SYSTEM,'tool':TOOL,'manifest_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':[{'type':'input_text','text':json.dumps(public)},{'type':'input_image','image_url':'data:image/png;base64,'+base64.b64encode((DATA/'source.png').read_bytes()).decode(),'detail':'high'}]}];rec={'id':t['id'],'sample':sample,'status':'started','usage':[]};calls=0;write(out/'result.json',rec)
    try:
        for turn in range(5):
            payload={'model':'gpt-6-astra','input':messages,'reasoning':{'effort':'high'},'max_output_tokens':16000,'store':False,'include':['reasoning.encrypted_content']}
            if calls<4:payload.update(tools=[TOOL],parallel_tool_calls=False)
            write(out/f'request-{turn}.json',payload);req=urllib.request.Request(ENDPOINT,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
            with urllib.request.urlopen(req,timeout=900) as res:raw=json.load(res)
            write(out/f'response-{turn}.json',raw);rec['usage'].append(raw.get('usage',{}));messages.extend(raw['output'])
            if raw['status']!='completed':rec['status']='incomplete_excluded';break
            fc=[v for v in raw['output'] if v['type']=='function_call']
            if fc:
                for c in fc:
                    args=json.loads(c['arguments']);result=grade(t,args['routes']);write(out/f'tool-{calls}.json',result);calls+=1;messages.append({'type':'function_call_output','call_id':c['call_id'],'output':json.dumps(result)});print('checker',calls,'violations',result['violation_count'],flush=True)
            else:
                text=''.join(c['text'] for v in raw['output'] if v['type']=='message' for c in v['content'] if c['type']=='output_text');(out/'final.txt').write_text(text)
                if text.startswith('```'):text=text.split('\n',1)[1].rsplit('```',1)[0]
                ans=json.loads(text);write(out/'answer.json',ans);g=grade(t,ans['routes']);(out/'output.svg').write_text(drawing(t,ans['routes']));rec.update(status='completed',grade=g);break
        if rec['status']=='started':rec['status']='no_final_excluded'
    except Exception as e:rec.update(status='operational_error_excluded',error=str(e).replace(key,'[REDACTED]')[:500])
    rec['checker_calls']=calls;write(out/'result.json',rec);print(rec['status'],rec.get('grade',{}).get('pass'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','run']);p.add_argument('--output',type=Path);p.add_argument('--sample',type=int,default=0);a=p.parse_args()
    if a.command=='build':build()
    else:run(a.output,a.sample)
