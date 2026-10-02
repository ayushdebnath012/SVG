"""Independent continuous geometry audit of exported PCB SVG polylines.

Axis-aligned segment distances use interval separation, not grid occupancy.
All distances are physical millimetres, including stroke and pad radii.
"""
import argparse,itertools,json,math,xml.etree.ElementTree as ET
from pathlib import Path
import cad_trace_routing as r

def gap(a,b,c,d):return max(0,min(a,b)-max(c,d),min(c,d)-max(a,b))
def distance(a,b,c,d):return math.hypot(gap(a[0],b[0],c[0],d[0]),gap(a[1],b[1],c[1],d[1]))

def audit(t,path):
    routes={};segments={};bad=[]
    for e in ET.parse(path).getroot().iter():
        if e.tag.split('}')[-1]!='polyline':continue
        ident=e.attrib['data-net']
        if ident in routes:bad.append({'kind':'duplicate_net','net':ident})
        pts=[tuple(map(float,p.split(','))) for p in e.attrib['points'].split()]
        routes[ident]=[[(x-70)/35,(y-130)/35] for x,y in pts]
        physical=[(x*2,y*2) for x,y in routes[ident]]
        segments[ident]=list(zip(physical,physical[1:]))
        if abs(float(e.attrib['stroke-width'])/17.5-.6)>1e-9:bad.append({'kind':'wrong_width','net':ident})
    minimum=float('inf')
    for i,j in itertools.combinations(segments,2):
        for (a,b),(c,d) in itertools.product(segments[i],segments[j]):
            clear=distance(a,b,c,d)-.6;minimum=min(minimum,clear)
            if clear<.4-1e-9:bad.append({'kind':'trace_clearance','nets':[i,j],'clearance_mm':clear,'segments_mm':[a,b,c,d]})
    for ident,segs in segments.items():
        for a,b in segs:
            for x,y in t['blocked']:
                c=(2*x-.6,2*y-.6);d=(2*x+.6,2*y+.6)
                clear=distance(a,b,c,d)-.3
                if clear<.4-1e-9:bad.append({'kind':'keepout_clearance','net':ident,'point_grid':[x,y],'clearance_mm':clear})
            for n in t['nets']:
                if n['id']==ident:continue
                for x,y in (n['start'],n['end']):
                    p=(2*x,2*y);clear=distance(a,b,p,p)-.8
                    if clear<.4-1e-9:bad.append({'kind':'pad_clearance','net':ident,'other':n['id'],'point_grid':[x,y],'clearance_mm':clear})
    grid=r.grade(t,routes)
    return {'pass':grid['pass'] and not bad,'svg_readback_grade':grid,'continuous_geometry_pass':not bad,'continuous_violation_count':len(bad),'continuous_violations':bad,'minimum_intertrace_edge_gap_mm':minimum if math.isfinite(minimum) else None,'scope':'Actual SVG coordinates and stroke widths; independent continuous axis-aligned segment/rectangle/pad distances, plus endpoint and board rules. Not an electrical or manufacturing signoff.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('svg',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    t=json.loads((r.DATA/'tasks.json').read_text())['tasks'][0];result=audit(t,a.svg);r.write(a.output,result);print(json.dumps(result,indent=2))
