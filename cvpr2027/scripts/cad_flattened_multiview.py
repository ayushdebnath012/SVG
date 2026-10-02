"""Same machining edit after CAD-style compound-path export; paired representation control."""
import argparse,copy,hashlib,json,math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from svgpathtools import parse_path
import cad_multiview_rotation as r
base=r.base;mv=r.mv
DATA=r.ROOT/'data/cad-flattened-multiview'

def flatten(svg,shape_ids):
    inv=base.inspect(svg);root=mv.ET.fromstring(svg);parents={c:p for p in root.iter() for c in p}
    for e in list(root.iter()):
        if e.get('id') in shape_ids:parents[e].remove(e)
    groups={}
    def pair(p):return f'{p[0]:.10g},{p[1]:.10g}'
    for eid,v in inv.items():
        if eid not in shape_ids:continue
        pts=np.array(v['points']);view='top' if pts[:,1].min()<650 else 'front' if pts[:,0].mean()<850 else 'right'
        dashed='stroke-dasharray' in v['attributes'];key=(view,dashed)
        if v['tag']=='circle':
            cx,cy=pts[0];rad=float(np.linalg.norm(v['radius_vectors'][0]));d=f'M {cx+rad:.10g},{cy:.10g} A {rad:.10g},{rad:.10g} 0 1 0 {cx-rad:.10g},{cy:.10g} A {rad:.10g},{rad:.10g} 0 1 0 {cx+rad:.10g},{cy:.10g} Z'
        else:d='M '+pair(pts[0])+' '+' '.join('L '+pair(p) for p in pts[1:])+(' Z' if v['tag']=='rect' else '')
        groups.setdefault(key,[]).append(d)
    ids=[]
    for (view,dashed),paths in groups.items():
        eid='p'+hashlib.sha256(f'{view}:{dashed}'.encode()).hexdigest()[:10];ids.append(eid)
        attrs={'id':eid,'d':' '.join(paths),'fill':'none','stroke':'#172b3a','stroke-width':'1'}
        if dashed:attrs['stroke-dasharray']='4.8,4'
        root.append(mv.ET.Element('{'+mv.NS+'}path',attrs))
    return mv.ET.tostring(root,encoding='unicode'),ids

def apply(svg,patches):
    root=mv.ET.fromstring(svg);index={e.get('id'):e for e in root.iter() if e.get('id')};parents={c:p for p in root.iter() for c in p}
    for p in patches:
        e=index[p['id']];tag=e.tag.split('}')[-1]
        if p.get('remove'):parents[e].remove(e);continue
        for k,v in p.get('set',{}).items():
            if tag=='path' and k=='d':
                if not isinstance(v,str) or len(v)>100000:raise ValueError('Path d must be a bounded SVG path string')
                parse_path(v);e.set(k,v)
            elif k in base.GEOM.get(tag,()):
                number=float(v)
                if not math.isfinite(number):raise ValueError('Nonfinite geometry')
                e.set(k,f'{number:.12g}')
            else:raise ValueError('Only path d, numeric primitive coordinates, text and removal are allowed')
        if 'text' in p:
            if tag!='text':raise ValueError('Only text elements accept text')
            e.text=str(p['text'])
    return mv.ET.tostring(root,encoding='unicode')

def cloud(svg,ids):
    result=[]
    for e in mv.ET.fromstring(svg).iter():
        if e.get('id') not in ids:continue
        path=parse_path(e.get('d'))
        for seg in path:
            count=max(2,math.ceil(seg.length()/.1)+1)
            points=[seg.point(t) for t in np.linspace(0,1,count)]
            result.extend((p.real,p.imag) for p in points)
    return np.array(result)

def score(t,patches):
    svg=apply(t['svg'],patches);a=cloud(svg,t['source_shape_ids']);b=cloud(t['target_svg'],t['source_shape_ids'])
    if not len(a):raise ValueError('Empty geometry')
    error=float(max(cKDTree(b).query(a)[0].max(),cKDTree(a).query(b)[0].max()))
    aa=base.inspect(svg);bb=base.inspect(t['target_svg']);annotations=[]
    for eid,v in bb.items():
        if eid in t['source_shape_ids']:continue
        if eid not in aa:annotations.append({'id':eid,'reason':'missing'});continue
        q=aa[eid]
        if 'points' in v and np.max(np.abs(np.array(q['points'])-np.array(v['points'])))>.45:annotations.append({'id':eid,'reason':'position'})
        if mv.equivalent_note(q.get('text'))!=mv.equivalent_note(v.get('text')):annotations.append({'id':eid,'reason':'text'})
    return {'outcome':'geometry_failure' if error>.45 else 'annotation_review' if annotations else 'pass','geometry_pass':error<=.45,'max_boundary_error_mm':error/4,'annotation_errors':annotations,'scope':'Same 0.1 mm geometry tolerance and 0.0125 mm sampling allowance as the primitive fixture. Compound path decomposition and coincident subpaths do not affect geometry grading.'}

def oracle(t):
    a=base.inspect(t['svg']);b=base.inspect(t['target_svg']);ps=[]
    for eid,v in b.items():
        p={'id':eid,'set':{}}
        keys=('d',) if v['tag']=='path' else base.GEOM.get(v['tag'],())
        for k in keys:
            if a[eid]['attributes'].get(k)!=v['attributes'].get(k):p['set'][k]=v['attributes'][k] if k=='d' else float(v['attributes'][k])
        if a[eid].get('text')!=v.get('text'):p['text']=v['text']
        if p['set'] or 'text' in p:ps.append(p)
    return ps

def build():
    if (DATA/'tasks.json').exists():raise ValueError('Frozen')
    original=json.loads((r.DATA/'tasks.json').read_text())['tasks'][0];t=copy.deepcopy(original)
    t['id']='compound_path_bore_pattern';t['svg'],ids=flatten(original['svg'],original['source_shape_ids']);t['target_svg'],targetids=flatten(original['target_svg'],original['source_shape_ids']);assert ids==targetids
    t['source_shape_ids']=ids;t['shape_ids']=ids
    t['instruction']=original['instruction']+' This SVG is a flattened CAD export with compound paths. Path coordinates are in page units; the drawing defines 4 page units per mm. Edit a path using {"id":"...","set":{"d":"complete new SVG path string"}}. A compound path may contain multiple subpaths. Preserve its style and ID. Labels and leaders remain editable with numeric-coordinate/text patches. Geometry need not retain the same subpath order.'
    t['prompt']=t['instruction']+'\nSOURCE SVG:\n'+t['svg'];t['image_path']=str((DATA/'source.png').resolve())
    check=score(t,oracle(t));assert check['outcome']=='pass';assert not score(t,[])['geometry_pass']
    equivalence={}
    for name in ('svg','target_svg'):
        a=cloud(t[name],ids);b=r.cloud(original[name],original['source_shape_ids']);err=max(cKDTree(a).query(b)[0].max(),cKDTree(b).query(a)[0].max());assert err<.11;equivalence[name]=float(err/4)
    r.write(DATA/'tasks.json',{'version':'compound-path-v1','tasks':[t],'paired_task':original['id'],'preflight':{'oracle':check,'representation_boundary_difference_mm':equivalence},'admission':'Three independent completed high-effort geometry failures after reference, representation and grader audit. Same physical object as primitive fixture; representation sensitivity, not a new shape family.'})
    (DATA/'source.svg').write_text(t['svg']);(DATA/'target.svg').write_text(t['target_svg']);r.render(DATA/'source.svg',DATA/'source.png',1550);r.render(DATA/'target.svg',DATA/'target.png',1550);print('Frozen',t['id'],equivalence,flush=True)

def configure():
    r.DATA=DATA;r.score=score;r.mv.apply=apply
    r.SYSTEM=r.SYSTEM.replace('Use numeric-coordinate patches for rect/circle/line/text, text changes, or deletion.','Use numeric-coordinate patches for rect/circle/line/text, complete string-valued d patches for compound paths, text changes, or deletion. Path subpath order may change. All compound path coordinates are page units.')
    r.TOOLS[0]['parameters']['properties']['patches']['items']['properties']['set']['additionalProperties']={'type':['number','string']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','run']);p.add_argument('--output',type=Path);p.add_argument('--sample',type=int,default=0);a=p.parse_args()
    if a.command=='build':build()
    else:configure();r.run(a.output,a.sample)
