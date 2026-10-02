"""Harder coupled routing edit: locked copper and exact trace lengths."""
import argparse,json,math,xml.etree.ElementTree as ET
from pathlib import Path
import cad_large_routing as large
r=large.r;DATA=r.ROOT/'data/cad-timed-routing';BASE_GRADE=r.grade

def grade(t,routes):
    result=BASE_GRADE(t,routes);extra=[]
    for ident,path in routes.items():
        if ident not in t['length_targets_mm']:continue
        try:points=r.expand(path)
        except Exception:continue
        if len(set(points))!=len(points):extra.append({'kind':'self_contact_or_retrace','net':ident})
        actual=2*(len(points)-1);target=t['length_targets_mm'][ident]
        if actual!=target:extra.append({'kind':'trace_length','net':ident,'actual_mm':actual,'required_mm':target})
        if ident in t['locked_routes']:
            reference=r.expand(t['locked_routes'][ident])
            if points!=reference and points!=reference[::-1]:extra.append({'kind':'changed_locked_trace','net':ident})
    result['violation_count']+=len(extra);result['violations']=(result['violations']+extra)[:100];result['pass']=result['pass'] and not extra
    result['scope']='One-layer orthogonal grid routing, connectivity and physical clearance, exact specified centerline lengths, no self-contact/retracing, and preservation of locked copper. No impedance or electrical timing simulation claim.'
    return result

def drawing(t,routes=None):
    svg=large.drawing(t,routes)
    svg=svg.replace('height="1370" viewBox="0 0 1600 1370"','height="1550" viewBox="0 0 1600 1550"')
    labels=['<text x="35" y="1335">Required centerline lengths (mm); locked traces must keep their exact route:</text>']
    for i,(ident,length) in enumerate(t['length_targets_mm'].items()):
        labels.append(f'<text x="{35+(i//6)*360}" y="{1360+(i%6)*22}">{ident}: {length} mm'+(' | LOCKED' if ident in t['locked_routes'] else '')+'</text>')
    return svg.replace('</g></svg>',''.join(labels)+'</g></svg>')

def audit(t,path):
    from audit_trace_routing import audit as continuous_audit
    result=continuous_audit(t,path);routes={};lengths={}
    for e in ET.parse(path).getroot().iter():
        if e.tag.split('}')[-1]!='polyline':continue
        ident=e.attrib['data-net'];pts=[tuple(map(float,p.split(','))) for p in e.attrib['points'].split()]
        routes[ident]=[[(x-70)/35,(y-130)/35] for x,y in pts]
        length=sum(math.dist(a,b)/17.5 for a,b in zip(pts,pts[1:]))
        lengths[ident]={'actual_svg_length_mm':length,'target_mm':t['length_targets_mm'].get(ident),'pass':abs(length-t['length_targets_mm'].get(ident,-1))<1e-9}
    timed=grade(t,routes);result.update(coupled_constraint_grade=timed,independent_svg_lengths=lengths)
    result['pass']=result['pass'] and timed['pass'] and all(v['pass'] for v in lengths.values())
    return result

def build():
    if (DATA/'tasks.json').exists():raise ValueError('Frozen')
    t=json.loads((large.DATA/'tasks.json').read_text())['tasks'][0];t['id']='length_constrained_routing_edit'
    t['length_targets_mm']={k:2*(len(r.expand(v))-1) for k,v in sorted(t['reference_routes'].items())}
    t['locked_routes']={k:t['reference_routes'][k] for k in ['C','I','L','N','X']}
    assert grade(t,t['reference_routes'])['pass']
    r.write(DATA/'tasks.json',{'version':'timed-routing-v1','tasks':[t],'selection':'Coupled-constraint variant frozen before Astra testing. The same constructive board reference meets all exact length targets. Five traces are explicitly given as existing locked copper; the other reference routes remain hidden. This is one paired task, not an independent layout family.','preflight':{'reference_grade':grade(t,t['reference_routes'])},'admission':'Three fresh-context completed geometric failures with high effort, 32000 output tokens per turn and four checker calls. Exclude incomplete, truncated, interface and operational responses. Configuration-specific only.'})
    (DATA/'source.svg').write_text(drawing(t,t['locked_routes']));(DATA/'reference.svg').write_text(drawing(t,t['reference_routes']));r.render(DATA/'source.svg',DATA/'source.png',1650);r.render(DATA/'reference.svg',DATA/'reference.png',1650)
    print('Frozen length targets and five locked traces',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','run']);p.add_argument('--output',type=Path);p.add_argument('--sample',type=int,default=0);a=p.parse_args()
    if a.command=='build':build()
    else:
        r.DATA=DATA;r.grade=grade;r.drawing=drawing
        r.SYSTEM+=' Additional mandatory constraints: every net has the exact centerline length specified in length_targets_mm. Repeated sites, self-contact, retracing and loops are forbidden. Five locked_routes are existing copper: include them unchanged, allowing reversed traversal or equivalent collinear segmentation only. Complete the other routes around them. The locked routes and all length targets are visible input. These are geometric length budgets, not claims about electrical timing. The checker also reports length errors and changes to locked traces. Use checker feedback when useful; you may submit partial candidates.'
        r.TOOL['description']+=' Also checks exact specified lengths, self-contact and preservation of locked traces.'
        r.run(a.output,a.sample,32000)
