"""Filleted mounting-plate CAD tasks: boundary geometry, clearances, area and mass.

These cases intentionally require no FEM. The reference is constructive geometry
with exact segment/arc area integration and dense boundary distance checks.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from svgpathtools import Arc, Line, Path as SVGPath
import cad_astra_benchmark as core

SYSTEM='''Return one JSON object with svg (a complete SVG string) and analysis (an object).
Produce a clean, dimensioned CAD top-view drawing of the specified physical mounting plate.
Use the specified coordinate map and viewBox. Draw the actual material outline and the actual cutouts,
not a physics field plot. Use one closed path or other closed SVG primitive per boundary, each tagged
with data-boundary="the requested ID". A circle is allowed for a circular hole. Use visible strokes;
show holes and the slot as cutouts, not extra solid material. All arcs must be circular with the specified radii.
Include dimensions, hole/slot labels, thickness and a clear unit legend. Do not use script, external images,
CSS stylesheets, use elements, clipping, masks, hidden boundaries or nested SVG. Ancestor transforms are allowed.
Return analysis with area_mm2 (net material area after all cutouts), mass_g, and min_clearance_mm
(minimum Euclidean edge-to-edge gap between any cutout and the outer boundary or another cutout),
and status (calculated, estimated or unavailable). Display the same three numeric results in text elements
with data-result="area_mm2", "mass_g" and "min_clearance_mm". Use at least 4 significant digits.
Use your own reasoning; no external tools are provided. Do not claim you ran an external solver.'''


def fillet(vertices,radii):
    v=np.array(vertices,dtype=float); pieces=[]; tangencies=[]
    for i,p in enumerate(v):
        before=p-v[i-1]; before/=np.linalg.norm(before)
        after=v[(i+1)%len(v)]-p; after/=np.linalg.norm(after)
        turn=math.atan2(float(before[0]*after[1]-before[1]*after[0]),float(before@after))
        r=radii[i]; d=r*math.tan(abs(turn)/2)
        start=p-before*d; end=p+after*d
        center=start+np.sign(turn)*r*np.array([-before[1],before[0]])
        tangencies.append((start,end,center,turn,r))
    area=0.0
    for i,(start,end,center,turn,r) in enumerate(tangencies):
        prev=tangencies[i-1][1]
        pieces.append(Line(complex(*prev),complex(*start)))
        pieces.append(Arc(complex(*start),complex(r,r),0,False,turn>0,complex(*end)))
        area+=float(prev[0]*start[1]-prev[1]*start[0])/2
        area+=(float(center[0]*(end-start)[1]-center[1]*(end-start)[0])+r*r*turn)/2
    return SVGPath(*pieces),area


def capsule(center,length,width,angle):
    c=np.array(center,dtype=float); r=width/2
    t=np.array([math.cos(math.radians(angle)),math.sin(math.radians(angle))]); n=np.array([-t[1],t[0]])
    a=c-(length-width)/2*t; b=c+(length-width)/2*t
    points=[a-r*n,b-r*n,b+r*n,a+r*n]
    p0,p1,p2,p3=[complex(*p) for p in points]
    return SVGPath(Line(p0,p1),Arc(p1,complex(r,r),0,False,True,p2),Line(p2,p3),Arc(p3,complex(r,r),0,False,True,p0))


def circle(c,r):
    p=complex(*c)
    return SVGPath(Arc(p+r,complex(r,r),0,False,True,p-r),Arc(p-r,complex(r,r),0,False,True,p+r))


def sample(path,step=0.12):
    arrays=[]
    for seg in path:
        n=max(12,math.ceil(seg.length()/step))
        z=np.array([seg.point(t) for t in np.linspace(0,1,n+1)])
        arrays.append(np.column_stack([z.real,z.imag]))
    return np.concatenate(arrays)


def reference(spec):
    outer,area=fillet(spec['vertices_mm'],spec['fillet_radii_mm'])
    paths={'outer':outer}
    for h in spec['holes']:
        paths[h['id']]=circle(h['center_mm'],h['diameter_mm']/2)
        area-=math.pi*(h['diameter_mm']/2)**2
    sl=spec['slot']; paths['slot']=capsule(sl['center_mm'],sl['length_mm'],sl['width_mm'],sl['angle_deg'])
    area-=(sl['length_mm']-sl['width_mm'])*sl['width_mm']+math.pi*(sl['width_mm']/2)**2
    clouds={k:sample(p) for k,p in paths.items()}
    gap=min(float(cKDTree(clouds[a]).query(clouds[b])[0].min()) for i,a in enumerate(clouds) for b in list(clouds)[i+1:])
    return paths,{'area_mm2':area,'mass_g':area*spec['thickness_mm']*spec['density_g_mm3'],'min_clearance_mm':gap}


def oracle_svg(spec):
    paths,values=reference(spec)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 850">','<rect width="1100" height="850" fill="white"/>',
           '<text x="35" y="40" font-size="24">Filleted slotted mounting plate — top view, mm</text>',
           '<g transform="translate(100,710) scale(3.5,-3.5)" stroke="#263d50" stroke-width="0.6">']
    for key,path in paths.items(): parts.append(f'<path data-boundary="{key}" d="{path.d()} Z" fill="'+('#e0e8ec' if key=='outer' else 'white')+'"/>')
    parts.append('</g>')
    for i,(k,v) in enumerate(values.items()): parts.append(f'<text x="{35+i*350}" y="790" font-size="16">{k}: <tspan data-result="{k}">{v:.6f}</tspan></text>')
    parts.append('</svg>')
    return '\n'.join(parts)


def build(out):
    base=dict(vertices_mm=[[0,0],[180,0],[180,40],[80,40],[80,150],[0,150]],fillet_radii_mm=[8,6,6,12,10,8],
              holes=[dict(id='hole_A',center_mm=[24,24],diameter_mm=12),dict(id='hole_B',center_mm=[152,20],diameter_mm=12),dict(id='hole_C',center_mm=[28,122],diameter_mm=14)],
              slot=dict(center_mm=[42,82],length_mm=48,width_mm=14,angle_deg=68),thickness_mm=6,density_g_mm3=0.00785)
    edit=copy.deepcopy(base)
    edit['vertices_mm']=[[0,0],[210,0],[210,40],[93,40],[93,165],[0,165]]
    edit['fillet_radii_mm'][3]=16; edit['holes'][1]['center_mm']=[182,20]; edit['holes'][2]['center_mm']=[28,137]
    edit['slot'].update(center_mm=[48,90],angle_deg=42)
    out.mkdir(parents=True,exist_ok=True); tasks=[]
    for mode,spec in [('generate',base),('edit',edit)]:
        _,ref=reference(spec)
        task=dict(id='slotted_plate_'+mode,kind='plate',family='filleted_slotted_plate',mode=mode,spec=spec,reference=ref)
        prompt=('Draw this L-shaped steel mounting plate in top view. Vertices define the sharp-corner polygon in counterclockwise order. '
                'Replace EVERY vertex by a circular tangent fillet using the corresponding radius in the list, including the concave re-entrant corner. '
                'Holes and slot go all the way through the plate. Slot length is TOTAL end-to-end length, with semicircular caps of radius width/2; '
                'angle is counterclockwise from physical +x. viewBox="0 0 1100 850"; mapping X=100+3.5*x, Y=710-3.5*y. '
                'Boundary IDs must be outer, hole_A, hole_B, hole_C, slot. All lengths mm. Compute area, mass and minimum clearance.\n')
        if mode=='generate': prompt+='Specification:\n'+json.dumps(base)
        else:
            prompt+='Original specification:\n'+json.dumps(base)+'\nOriginal SVG:\n'+oracle_svg(base)
            prompt+='\nEDIT: extend the arm right edge x=180 to x=210; move the inner vertical edge x=80 to x=93; raise the top edge y=150 to y=165. Change the concave fillet radius from 12 to 16. Move hole_B to (182,20), hole_C to (28,137), and the slot centre to (48,90); rotate the slot to 42 degrees. Preserve all other parameters and recompute the geometry and results.'
        task['prompt']=prompt; tasks.append(task)
        (out/(task['id']+'.reference.svg')).write_text(oracle_svg(spec))
    core.write_json(out/'tasks.json',dict(version='cad-plate-pilot-v1',system=SYSTEM,scope='Dimensioned filleted mounting plate, top view; constructive geometry and clearance/area/mass checks, no FEM.',
        criteria={'selection':'At least 3 evaluable samples, two high-effort confirmations, at least 2 failures including a high-effort failure; explicit visual/evidence review.',
                  'boundary_hausdorff_tolerance_mm':0.4,'area_and_mass_relative_tolerance':0.005,'clearance_absolute_tolerance_mm':0.1},tasks=tasks))
    print('Built 2 mounting-plate CAD tasks',flush=True)


def score(task,text):
    row={k:[] for k in ('geometry_errors','dimension_errors','analysis_errors','format_errors','visible_result_errors')}
    try:
        obj=core.read_response(text); root=ET.fromstring(obj['svg'])
        # Reuse the security/rendering subset validator (no data-member elements needed).
        core.svg_geometry(obj['svg'])
        curves={}; labels={}
        def walk(e,M,hidden=False):
            M=M@core.transform_matrix(e.get('transform',''))
            if e.get('style'):  # common inline stroke styles are fine; hidden must not be accepted
                st=dict(x.split(':',1) for x in e.get('style').split(';') if ':' in x)
            else: st={}
            hidden=hidden or e.tag.split('}')[-1]=='defs' or e.get('display',st.get('display'))=='none' or e.get('visibility',st.get('visibility'))=='hidden' or e.get('opacity',st.get('opacity'))=='0'
            key=e.get('data-boundary')
            if key:
                if key in curves or hidden: raise ValueError('duplicate or hidden boundary')
                path=core.element_path(e)
                if not len(path) or not path.isclosed(): raise ValueError('boundary is not closed')
                points=sample(path)
                points=np.einsum('ij,kj->ik',np.column_stack([points,np.ones(len(points))]),M)
                points[:,0]=(points[:,0]-100)/3.5; points[:,1]=(710-points[:,1])/3.5
                curves[key]=points[:,:2]
            if e.get('data-result'): labels[e.get('data-result')]=''.join(e.itertext())
            for child in e: walk(child,M,hidden)
        walk(root,np.eye(3))
        expected,_=reference(task['spec'])
        if set(curves)!=set(expected): raise ValueError('missing or extra boundary ID; review actual shape separately')
        for key,path in expected.items():
            target=sample(path); actual=curves[key]
            error=max(float(cKDTree(target).query(actual)[0].max()),float(cKDTree(actual).query(target)[0].max()))
            if error>0.4: row['geometry_errors'].append({'boundary':key,'hausdorff_mm':error})
        for key,val in task['reference'].items():
            actual=obj['analysis'].get(key)
            if not isinstance(actual,(int,float)) or isinstance(actual,bool) or not math.isfinite(actual):
                row['format_errors'].append('missing numeric analysis: '+key); continue
            tol=0.1 if key=='min_clearance_mm' else abs(val)*0.005
            if abs(actual-val)>tol: row['analysis_errors'].append({'quantity':key,'expected':val,'actual':actual,'absolute_error':abs(actual-val),'tolerance':tol})
            try:
                if abs(core.first_number(labels[key])-actual)>max(0.001*abs(actual),0.001): row['visible_result_errors'].append({'quantity':key,'json':actual,'svg':labels[key]})
            except (ValueError,KeyError): row['format_errors'].append('missing visible result: '+key)
        row['geometry_pass']=not row['geometry_errors']; row['analysis_pass']=not row['analysis_errors']
        row['outcome']='failure' if any(row[k] for k in ('geometry_errors','analysis_errors','visible_result_errors')) else ('unscored_format' if row['format_errors'] else 'pass')
    except (ValueError,TypeError,KeyError,ET.ParseError,AssertionError) as exc:
        row['format_errors'].append(str(exc)); row['outcome']='unscored_format'
    return row

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,default=core.ROOT/'data/cad-plate-pilot'); build(p.parse_args().output)
