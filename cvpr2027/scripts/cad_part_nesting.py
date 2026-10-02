"""Irregular laser-cut part nesting with a certified feasible layout and clearance."""
import argparse,base64,hashlib,itertools,json,random,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
from svgpathtools import parse_path
import cad_trace_routing as r
DATA=r.ROOT/'data/cad-part-nesting'

def normalized(cells):
    x=min(p[0] for p in cells);y=min(p[1] for p in cells)
    return sorted((a-x,b-y) for a,b in cells)

def rotate(cells,degrees):
    if degrees not in (0,90,180,270):raise ValueError('Rotation must be 0,90,180 or 270')
    cells=[tuple(p) for p in cells]
    for _ in range(degrees//90):cells=[(-y,x) for x,y in cells]
    return normalized(cells)

def placed(cells,pose):
    if any(type(pose.get(k)) is not int for k in ('x','y','rotation')):raise ValueError('Integer x, y and rotation required')
    return [(x+pose['x'],y+pose['y']) for x,y in rotate(cells,pose['rotation'])]

def solid(cells):
    return unary_union([box(4*x,4*y,4*x+4,4*y+4) for x,y in cells]).buffer(-.2,join_style='mitre')

def grade(t,poses):
    bad=[];occupied={};polys={};parts={p['id']:p for p in t['parts']}
    for ident in set(poses)-set(parts):bad.append({'kind':'unknown_part','part':ident})
    for ident,p in parts.items():
        if ident not in poses:bad.append({'kind':'missing_part','part':ident});continue
        try:cells=placed(p['cells'],poses[ident])
        except Exception as e:bad.append({'kind':'invalid_pose','part':ident,'detail':str(e)});continue
        for c in cells:
            if not (0<=c[0]<t['width'] and 0<=c[1]<t['height']):bad.append({'kind':'outside_stock','part':ident,'cell':c})
            if c in occupied:bad.append({'kind':'overlap','part':ident,'other':occupied[c],'cell':c})
            occupied[c]=ident
        polys[ident]=solid(cells)
    for a,b in itertools.combinations(polys,2):
        dist=polys[a].distance(polys[b])
        if dist<.4-1e-8:bad.append({'kind':'physical_clearance','parts':[a,b],'actual_mm':dist,'required_mm':.4})
    return {'pass':not bad,'violation_count':len(bad),'violations':bad[:100],'placed_parts':len(polys),'scope':'Every unchanged irregular part once; quarter-turn rotations and 4 mm lattice translations only; stock bounds, no overlap, 0.4 mm minimum part gap. No hidden preferred layout. Geometry only, not cutting-process signoff.'}

def path_data(poly,ox,oy,scale):
    chunks=[]
    for ring in [poly.exterior,*poly.interiors]:
        coords=list(ring.coords);chunks.append('M '+' L '.join(f'{ox+scale*x:.8g},{oy+scale*y:.8g}' for x,y in coords)+' Z')
    return ' '.join(chunks)

def drawing(t,poses=None):
    poses=poses or {};parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1500" viewBox="0 0 1800 1500"><rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" font-size="16">','<text x="40" y="35" font-size="25">Irregular cut-part nesting | Stock 64 x 48 mm</text>','<text x="40" y="65">Place each part once. Gap at least 0.4 mm. Quarter turns and 4 mm grid translations only.</text>','<text x="40" y="90">Coordinates: x right, y down. Part outlines already include the 0.2 mm inward offset.</text>','<rect x="60" y="130" width="640" height="480" fill="#f7f9fa" stroke="#333"/>']
    for x in range(t['width']+1):parts.append(f'<text x="{56+40*x}" y="120">{x}</text>')
    for y in range(t['height']+1):parts.append(f'<text x="30" y="{136+40*y}">{y}</text>')
    for i,p in enumerate(t['parts']):
        ident=p['id'];color=r.COLORS[i%6]
        if ident in poses:
            poly=solid(placed(p['cells'],poses[ident]));d=path_data(poly,60,130,10);parts.append(f'<path data-piece="{ident}" d="{d}" fill="{color}" fill-opacity="0.32" stroke="{color}" stroke-width="1" fill-rule="evenodd"/>');point=poly.representative_point();parts.append(f'<text x="{60+10*point.x-12}" y="{130+10*point.y+5}">{ident}</text>')
        ox=45+(i%5)*350;oy=720+(i//5)*240;poly=solid(p['cells']);parts.append(f'<text x="{ox}" y="{oy-18}">{ident} | {len(p["cells"])} cells | local origin (0,0)</text>');parts.append(f'<path d="{path_data(poly,ox,oy,5)}" fill="{color}" fill-opacity=".25" stroke="{color}" fill-rule="evenodd"/>')
    parts+=['<text x="780" y="180">Piece gallery below uses half the stock drawing scale.</text>','<text x="780" y="210">Exact local cell coordinates and rotation rule are supplied in JSON.</text>','<text x="780" y="240">No reflection, scaling, trimming or omitted parts.</text>','<text x="40" y="1470">Research nesting layout; no material, cutter or production qualification is implied.</text>','</g></svg>'];return ''.join(parts)

def audit(t,path):
    polys={};bad=[];stock=box(0,0,4*t['width'],4*t['height'])
    for e in ET.parse(path).getroot().iter():
        ident=e.get('data-piece')
        if not ident:continue
        if ident in polys:bad.append({'kind':'duplicate_part','part':ident})
        rings=[]
        for sub in parse_path(e.attrib['d']).continuous_subpaths():
            coords=[sub[0].start]+[seg.end for seg in sub]
            rings.append([((z.real-60)/10,(z.imag-130)/10) for z in coords])
        poly=Polygon(rings[0],rings[1:]);polys[ident]=poly
        if not poly.is_valid or not stock.buffer(1e-8).covers(poly):bad.append({'kind':'invalid_or_outside','part':ident})
        part=next((p for p in t['parts'] if p['id']==ident),None)
        if part is None:bad.append({'kind':'unknown_part','part':ident});continue
        matches=[]
        from shapely.affinity import translate
        for deg in (0,90,180,270):
            original=solid(rotate(part['cells'],deg));dx=poly.bounds[0]-original.bounds[0];dy=poly.bounds[1]-original.bounds[1]
            if abs(dx/4-round(dx/4))<1e-8 and abs(dy/4-round(dy/4))<1e-8 and translate(original,dx,dy).symmetric_difference(poly).area<1e-7:matches.append(deg)
        if not matches:bad.append({'kind':'altered_part_or_invalid_pose','part':ident})
    for p in t['parts']:
        if p['id'] not in polys:bad.append({'kind':'missing_part','part':p['id']})
    gaps=[]
    for a,b in itertools.combinations(polys,2):
        gap=polys[a].distance(polys[b]);gaps.append(gap)
        if polys[a].intersection(polys[b]).area>1e-8 or gap<.4-1e-8:bad.append({'kind':'overlap_or_gap','parts':[a,b],'gap_mm':gap})
    return {'pass':not bad,'violations':bad,'minimum_part_gap_mm':min(gaps) if gaps else None,'scope':'Read actual exported SVG paths; check part shape under permitted rigid lattice poses, stock bounds and continuous polygon distances.'}

def build():
    if (DATA/'tasks.json').exists():raise ValueError('Frozen')
    for seed in range(4500,4600):
        rng=random.Random(seed);w,h=16,12;allcells=[(x,y) for x in range(w) for y in range(h)];seeds=rng.sample(allcells,14);regions=[{p} for p in seeds];used=set(seeds)
        while len(used)<w*h:
            options=[]
            for i,reg in enumerate(regions):
                frontier={(x+dx,y+dy) for x,y in reg for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)] if 0<=x+dx<w and 0<=y+dy<h and (x+dx,y+dy) not in used}
                options.extend((i,p) for p in sorted(frontier))
            size=min(len(regions[i]) for i,p in options);i,p=rng.choice([(i,p) for i,p in options if len(regions[i])==size]);regions[i].add(p);used.add(p)
        if min(map(len,regions))<7 or max(map(len,regions))>26:continue
        rng.shuffle(regions);parts=[];reference={}
        for i,reg in enumerate(regions):
            ident=f'P{i+1:02d}';cells=rotate(list(reg),rng.choice([0,90,180,270]));parts.append({'id':ident,'cells':[list(p) for p in cells]})
            deg=next(a for a in (0,90,180,270) if rotate(cells,a)==normalized(reg));reference[ident]={'x':min(p[0] for p in reg),'y':min(p[1] for p in reg),'rotation':deg}
        t={'id':'irregular_fourteen_part_nesting','width':w,'height':h,'cell_pitch_mm':4,'inset_mm':.2,'minimum_gap_mm':.4,'parts':parts,'reference_poses':reference,'generation_seed':seed}
        if any(solid(p['cells']).geom_type!='Polygon' or not solid(p['cells']).is_valid for p in parts):continue
        assert grade(t,reference)['pass'];r.write(DATA/'tasks.json',{'version':'part-nesting-v1','tasks':[t],'selection':'First valid connected 14-region seeded stock partition. Local orientations and identities scrambled before testing. No Astra result used in generation.','preflight':grade(t,reference),'admission':'Three fresh-context completed placement failures with high effort, 32000 output tokens/turn and four checker calls. Incomplete/truncation/interface/operational errors excluded.'})
        (DATA/'source.svg').write_text(drawing(t));(DATA/'reference.svg').write_text(drawing(t,reference));a=audit(t,DATA/'reference.svg');assert a['pass'];r.write(DATA/'reference-audit.json',a);r.render(DATA/'source.svg',DATA/'source.png',1850);r.render(DATA/'reference.svg',DATA/'reference.png',1850);print('Frozen nesting seed',seed,flush=True);return
    raise RuntimeError('No candidate')

SYSTEM='''Create a stock nesting CAD drawing of 14 irregular laser-cut parts. Return JSON {"placements":{"P01":{"x":0,"y":0,"rotation":90},...},"explanation":"..."}. Every part must appear once, unchanged, inside 64 x 48 mm stock with at least 0.4 mm gap to other parts. No scaling, reflection, trimming or omissions. Each supplied cell is a 4 x 4 mm square indexed by its top-left integer coordinate in page axes (x right, y down). A part is the union of its cells, offset inward 0.2 mm with mitred corners; this offset is already part of the specified shape, do not apply it again. Pose x,y are integer cell translations of the normalized rotated cell footprint. Rotation is 0,90,180 or 270: one 90-degree turn maps each cell index (x,y) to (-y,x), then subtract the minimum x and minimum y so the rotated footprint starts at (0,0), then add pose x,y. Thus non-overlapping in-bounds cell footprints guarantee the physical gap. A feasible full layout exists. Any valid layout passes, not just a hidden reference. You may call check_nesting up to four times on partial or complete candidates. It reports violations, not solution placements. No general code execution or packing solver is provided. Your placements are exported as physical-scale SVG part outlines and independently checked.'''
TOOL={'type':'function','name':'check_nesting','description':'Check proposed poses for missing parts, stock bounds, overlap and physical clearance. No solution placements are supplied.','parameters':{'type':'object','properties':{'placements':{'type':'object','additionalProperties':{'type':'object','properties':{'x':{'type':'integer'},'y':{'type':'integer'},'rotation':{'type':'integer','enum':[0,90,180,270]}},'required':['x','y','rotation']}}},'required':['placements']},'strict':False}

def run(out,sample):
    if out.exists():raise ValueError('Fresh output directory required')
    manifest=DATA/'tasks.json';t=json.loads(manifest.read_text())['tasks'][0];public={k:v for k,v in t.items() if k not in ('reference_poses','generation_seed')};key=r.api_key()
    r.write(out/'protocol.json',{'model':'gpt-6-astra','effort':'high','sample':sample,'max_output_tokens':32000,'max_checker_calls':4,'system':SYSTEM,'tool':TOOL,'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':[{'type':'input_text','text':json.dumps(public)},{'type':'input_image','image_url':'data:image/png;base64,'+base64.b64encode((DATA/'source.png').read_bytes()).decode(),'detail':'high'}]}];record={'id':t['id'],'sample':sample,'status':'started','usage':[]};calls=0;r.write(out/'result.json',record)
    try:
        for turn in range(5):
            payload={'model':'gpt-6-astra','input':messages,'reasoning':{'effort':'high'},'max_output_tokens':32000,'store':False,'include':['reasoning.encrypted_content']}
            if calls<4:payload.update(tools=[TOOL],parallel_tool_calls=False)
            r.write(out/f'request-{turn}.json',payload);req=urllib.request.Request(r.ENDPOINT,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
            with urllib.request.urlopen(req,timeout=1200) as response:raw=json.load(response)
            r.write(out/f'response-{turn}.json',raw);record['usage'].append(raw.get('usage',{}));messages.extend(raw['output'])
            if raw['status']!='completed':record['status']='incomplete_excluded';break
            fc=[v for v in raw['output'] if v['type']=='function_call']
            if fc:
                for c in fc:
                    result=grade(t,json.loads(c['arguments'])['placements']);r.write(out/f'tool-{calls}.json',result);calls+=1;messages.append({'type':'function_call_output','call_id':c['call_id'],'output':json.dumps(result)});print('checker',calls,'violations',result['violation_count'],flush=True)
            else:
                text=''.join(c['text'] for v in raw['output'] if v['type']=='message' for c in v['content'] if c['type']=='output_text');(out/'final.txt').write_text(text)
                if text.startswith('```'):text=text.split('\n',1)[1].rsplit('```',1)[0]
                answer=json.loads(text);r.write(out/'answer.json',answer);g=grade(t,answer['placements']);(out/'output.svg').write_text(drawing(t,answer['placements']));record.update(status='completed',grade=g);break
        if record['status']=='started':record['status']='no_final_excluded'
    except Exception as e:record.update(status='operational_error_excluded',error=str(e).replace(key,'[REDACTED]')[:500])
    record['checker_calls']=calls;r.write(out/'result.json',record);print(record['status'],record.get('grade',{}).get('pass'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','run']);p.add_argument('--output',type=Path);p.add_argument('--sample',type=int,default=0);a=p.parse_args()
    if a.command=='build':build()
    else:run(a.output,a.sample)
