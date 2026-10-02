"""Hard CAD profile discovery: involute gear, roller cam, oblique manifold section.

Numerical references are independent of SVG serialization. Chrome renders all
supported SVG geometry, including local use/clip/mask constructs; scoring does
not require a particular path decomposition. No FEM or shape-safety claim.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET
import numpy as np
from scipy.ndimage import distance_transform_edt
from matplotlib.path import Path as MPath
from PIL import Image
import cad_astra_benchmark as core
from render_svg_gallery import render

SIZE=1000; SCALE=4.; ORIGIN=500.
SYSTEM='''Return a JSON object with svg (a complete SVG string) and analysis (an object, may be empty).
Draw a precise CAD section/top view of the specified real mechanical part. This is geometry, not a field plot.
Use viewBox="0 0 1000 1000", width="1000", height="1000". Physical coordinates in mm are mapped to
SVG X=500+4*x, Y=500-4*y. Put the entire material silhouette in ONE direct child <g data-geometry="part">.
That group must display all solid material in black and all holes/removed material in white on a white background.
It must contain no dimensions, labels, axes, hatching, decorative strokes or construction curves. Curves should
be accurate within 0.5 mm; smooth Beziers or sufficiently fine polygon approximations are both acceptable.
Place readable dimensions, explanatory labels and centre marks OUTSIDE that geometry group. Give every required
numeric dimension a visible text element tagged data-dimension="its specified key", containing its value and mm.
Any native SVG shapes, transforms, local use references, clipping and masks are allowed. Definitions may be in defs.
No scripts, animation, raster images, foreignObject, external resources or CSS stylesheets. Inline styles are allowed.
The drawing must represent the actual specified profile, including intersecting features. Do not substitute a generic
symbolic gear/cam/section. No external tools are provided. Do not claim to have executed CAD or analysis software.'''


def grid():
    yy,xx=np.mgrid[:SIZE,:SIZE]
    return (xx+.5-ORIGIN)/SCALE,(ORIGIN-yy-.5)/SCALE

def inv(a): return np.tan(a)-a

def gear_radii(s):
    rp=s['module_mm']*s['teeth']/2;return rp,rp*math.cos(math.radians(s['pressure_deg'])),rp+s['module_mm'],rp-1.25*s['module_mm']

def gear_mask(s,x,y):
    rp,rb,ra,rf=gear_radii(s);r=np.hypot(x,y);pitch=2*math.pi/s['teeth']
    angle=np.arctan2(y,x)-math.radians(s['phase_deg']);delta=(angle+pitch/2)%pitch-pitch/2
    half=math.pi/(2*s['teeth'])+inv(math.radians(s['pressure_deg']))-inv(np.arccos(np.clip(rb/np.maximum(r,rb),-1,1)))
    mask=(r<=rf)|((r<=ra)&(np.abs(delta)<=half))
    mask &= r>=s['bore_radius_mm']
    mask &= ~((np.abs(x)<=s['key_width_mm']/2)&(y>=0)&(y<=s['key_top_mm']))
    return mask

def gear_points(s,n=32):
    rp,rb,ra,rf=gear_radii(s);pitch=2*math.pi/s['teeth'];phase=math.radians(s['phase_deg'])
    def half(r):return math.pi/(2*s['teeth'])+float(inv(math.radians(s['pressure_deg']))-inv(math.acos(min(1,rb/r))))
    pts=[]
    def add(r,a):pts.append((r*math.cos(a),r*math.sin(a)))
    for i in range(s['teeth']):
        c=phase+i*pitch;hb=half(rb);ha=half(ra)
        add(rf,c-hb)
        for r in np.linspace(max(rb,rf),ra,n):add(r,c-half(r))
        for a in np.linspace(c-ha,c+ha,8):add(ra,a)
        for r in np.linspace(ra,max(rb,rf),n):add(r,c+half(r))
        add(rf,c+hb)
        for a in np.linspace(c+hb,c+pitch-hb,8):add(rf,a)
    return np.array(pts)

def cam_curve(s,n=2400):
    t=np.linspace(0,2*math.pi,n,endpoint=False);a,b,c=map(math.radians,[s['rise_deg'],s['high_dwell_deg'],s['return_deg']]);h=s['lift_mm']
    lift=np.zeros_like(t);der=np.zeros_like(t)
    rise=t<a;u=t[rise]/a;lift[rise]=h*(u-np.sin(2*math.pi*u)/(2*math.pi));der[rise]=h/a*(1-np.cos(2*math.pi*u))
    dwell=(t>=a)&(t<a+b);lift[dwell]=h
    ret=(t>=a+b)&(t<a+b+c);u=(t[ret]-a-b)/c
    lift[ret]=h*(1-u+np.sin(2*math.pi*u)/(2*math.pi));der[ret]=-h/c*(1-np.cos(2*math.pi*u))
    r=s['base_radius_mm']+s['roller_radius_mm']+lift;rho=s['roller_radius_mm'];den=np.hypot(r,der)
    px=r*np.cos(t);py=r*np.sin(t)
    nx=(r*np.cos(t)+der*np.sin(t))/den;ny=(r*np.sin(t)-der*np.cos(t))/den
    return np.column_stack([px-rho*nx,py-rho*ny])

def basis(s):
    return np.array(s['plane_origin_mm']),np.column_stack([s['plane_u'],s['plane_v']])

def section_mask(s,x,y):
    origin,E=basis(s);p=origin[:,None,None]+E[:,0,None,None]*x+E[:,1,None,None]*y
    mask=np.ones(x.shape,dtype=bool)
    for k,length in enumerate(s['block_size_mm']):mask &= (p[k]>=0)&(p[k]<=length)
    for b in s['bores']:
        d=np.array(b['axis'],dtype=float);d/=np.linalg.norm(d);v=p-np.array(b['point_mm'])[:,None,None]
        projection=np.einsum('i,ijk->jk',d,v);dist2=np.einsum('ijk,ijk->jk',v,v)-projection**2
        mask &= dist2>=b['radius_mm']**2
    return mask

def section_polygon(s):
    origin,E=basis(s);poly=[[-300.,-300.],[300.,-300.],[300.,300.],[-300.,300.]]
    for axis,length in enumerate(s['block_size_mm']):
        for a,b in [(E[axis],length-origin[axis]),(-E[axis],origin[axis])]:
            output=[]
            for start,end in zip(poly,poly[1:]+poly[:1]):
                start=np.array(start);end=np.array(end);ds=float(start@a-b);de=float(end@a-b)
                if ds<=0:output.append(start.tolist())
                if (ds<=0)!=(de<=0):output.append((start+(end-start)*ds/(ds-de)).tolist())
            poly=output
    return np.array(poly)

def section_ellipses(s):
    origin,E=basis(s);answer=[]
    for b in s['bores']:
        d=np.array(b['axis'],dtype=float);d/=np.linalg.norm(d);Q=np.eye(3)-np.outer(d,d);v=origin-np.array(b['point_mm'])
        A=E.T@Q@E;linear=E.T@Q@v;center=-np.linalg.solve(A,linear);k=b['radius_mm']**2-float(v@Q@v)+float(linear@np.linalg.solve(A,linear))
        eig,V=np.linalg.eigh(A)
        assert k>0 and min(eig)>1e-6
        answer.append((center,np.sqrt(k/eig),V))
    return answer

def reference_mask(task):
    x,y=grid();s=task['spec'];family=task['family']
    if family=='involute_gear':return gear_mask(s,x,y)
    if family=='oblique_manifold_section':return section_mask(s,x,y)
    pts=cam_curve(s);mask=MPath(pts,closed=True).contains_points(np.column_stack([x.ravel(),y.ravel()])).reshape(x.shape)
    return mask & (x*x+y*y>=s['bore_radius_mm']**2)

def poly_path(pts):return 'M'+' L'.join(f'{x:.5f},{y:.5f}' for x,y in pts)+' Z'

def shape_svg(task):
    s=task['spec'];fam=task['family'];parts=[]
    if fam=='involute_gear':
        parts=[f'<path d="{poly_path(gear_points(s,12))}"/>',f'<circle r="{s["bore_radius_mm"]}" fill="white"/>',f'<rect x="{-s["key_width_mm"]/2}" y="0" width="{s["key_width_mm"]}" height="{s["key_top_mm"]}" fill="white"/>']
    elif fam=='roller_cam':
        parts=[f'<path d="{poly_path(cam_curve(s,360))}"/>',f'<circle r="{s["bore_radius_mm"]}" fill="white"/>']
    else:
        path=poly_path(section_polygon(s));parts=[f'<defs><clipPath id="stock"><path d="{path}"/></clipPath></defs>',f'<path d="{path}"/>','<g clip-path="url(#stock)" fill="white">']
        for c,r,V in section_ellipses(s):
            ang=math.degrees(math.atan2(V[1,0],V[0,0]));parts.append(f'<ellipse cx="0" cy="0" rx="{r[0]}" ry="{r[1]}" transform="translate({c[0]},{c[1]}) rotate({ang})"/>')
        parts.append('</g>')
    return '<g data-geometry="part" transform="translate(500,500) scale(4,-4)" fill="black">'+''.join(parts)+'</g>'

def oracle_svg(task):
    labels=''.join(f'<text x="30" y="{70+i*24}" font-size="17" data-dimension="{k}">{k}: {v:.6f} mm</text>' for i,(k,v) in enumerate(task['dimensions'].items()))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000" viewBox="0 0 1000 1000"><rect width="1000" height="1000" fill="white"/>{shape_svg(task)}<text x="30" y="30" font-size="21">{task["family"]} — {task["mode"]}</text>{labels}</svg>'

def dims(f,s):
    if f=='involute_gear':
        rp,rb,ra,rf=gear_radii(s);return dict(pitch_diameter=2*rp,tip_diameter=2*ra,root_diameter=2*rf,bore_diameter=2*s['bore_radius_mm'])
    if f=='roller_cam':return dict(base_diameter=2*s['base_radius_mm'],lift=s['lift_mm'],roller_diameter=2*s['roller_radius_mm'],bore_diameter=2*s['bore_radius_mm'])
    return {f'bore_{i+1}_diameter':2*b['radius_mm'] for i,b in enumerate(s['bores'])}

GEAR_DESC='''Ideal spur gear, zero profile shift/backlash, no root fillets or trochoids. Pitch radius rp=m*z/2, base rb=rp*cos(alpha), tip ra=rp+m, root rf=rp-1.25*m. Tooth k is centred on phase+360*k/z degrees. At radius r>=rb its half-thickness angle is pi/(2*z)+inv(alpha)-inv(acos(rb/r)), where inv(t)=tan(t)-t and angles in this formula are radians. The two flanks are exact involutes; connect them by a circular tip arc. Between rf and rb extend each base-end flank radially at its base angle; connect adjacent teeth by circular root arcs. Subtract the union of a centred circular bore and a keyway rectangle -key_width/2<=x<=key_width/2, 0<=y<=key_top. This explicitly defined ideal profile overrides other gear conventions.'''
CAM_DESC='''Plate cam for a translating roller follower. Construct the pitch curve p(theta)=r(theta)*(cos(theta),sin(theta)), r=base_radius+roller_radius+s(theta), over 0<=theta<360 degrees, CCW from +x. Start a cycloidal rise of lift h over rise_deg, then hold h for high_dwell_deg, then cycloidal return over return_deg, then hold zero for the remaining angle. For local fraction u in [0,1], rise s=h*(u-sin(2*pi*u)/(2*pi)); return s=h*(1-u+sin(2*pi*u)/(2*pi)). The actual cam contour is the inward normal offset of that pitch curve by roller_radius: p-R*(dy/dtheta,-dx/dtheta)/sqrt((dx/dtheta)^2+(dy/dtheta)^2). Draw the cam contour, NOT the roller-centre/pitch curve. Subtract the centred circular bore. Angles in differentiation are radians.'''
SECTION_DESC='''Oblique section A-A of a rectangular manifold block. The solid block is 0<=X<=Lx, 0<=Y<=Ly, 0<=Z<=Lz in global XYZ. Subtract the union of all given through-cylinders; each cylinder is the infinite line point_mm+t*axis with the stated perpendicular radius (normalize axis). The cutting plane uses orthonormal in-plane vectors u,v and origin O: global point=O+x*u+y*v. Draw the actual remaining-material cross-section in those local x,y coordinates. Correctly intersect the plane with the box and cylinders, trim overlapping holes at each other and at the stock boundary. A cylinder's oblique intersection generally is an ellipse, not a circle. Cylinder diameters in the dimension labels are their true global diameters, not ellipse diameters.'''

def build(out):
    if (out/'tasks.json').exists():raise ValueError('Frozen pool exists; choose another path')
    gear=dict(teeth=23,module_mm=4.,pressure_deg=25.,phase_deg=7.,bore_radius_mm=10.,key_width_mm=6.,key_top_mm=14.)
    ge=copy.deepcopy(gear);ge.update(teeth=29,module_mm=3.5,pressure_deg=20.,phase_deg=11.,bore_radius_mm=12.,key_width_mm=7.,key_top_mm=16.)
    cam=dict(base_radius_mm=30.,roller_radius_mm=7.,lift_mm=24.,rise_deg=110.,high_dwell_deg=50.,return_deg=140.,bore_radius_mm=8.)
    ce=copy.deepcopy(cam);ce.update(roller_radius_mm=10.,lift_mm=32.,rise_deg=95.,high_dwell_deg=65.,return_deg=150.)
    section=dict(block_size_mm=[120,90,70],plane_origin_mm=[60,45,35],plane_u=[.8,.6,0],plane_v=[-.36,.48,.8],bores=[dict(point_mm=[20,25,30],axis=[1,.35,.2],radius_mm=13),dict(point_mm=[80,0,25],axis=[-.2,1,.4],radius_mm=11),dict(point_mm=[55,48,0],axis=[0,0,1],radius_mm=9)])
    se=copy.deepcopy(section);se['plane_origin_mm']=[65,41,32];se['bores'][0]['radius_mm']=17;se['bores'][1]['axis']=[-.35,1,.55];se['bores'][2]['point_mm']=[68,52,0]
    tasks=[];out.mkdir(parents=True,exist_ok=True)
    for f,base,edit,desc in [('involute_gear',gear,ge,GEAR_DESC),('roller_cam',cam,ce,CAM_DESC),('oblique_manifold_section',section,se,SECTION_DESC)]:
        source=dict(family=f,spec=base,mode='original',dimensions=dims(f,base))
        for mode,spec in [('generate',base),('edit',edit)]:
            task=dict(id=f+'_'+mode,kind='hard_geometry',family=f,mode=mode,spec=spec,dimensions=dims(f,spec))
            prompt=desc+'\nAll lengths mm. Required named dimensions: '+', '.join(task['dimensions'])+'.\n'
            if mode=='generate':prompt+='Specification:\n'+json.dumps(spec)
            else:prompt+='Original specification:\n'+json.dumps(base)+'\nOriginal drawing:\n'+oracle_svg(source)+'\nEDIT: replace the parameter values with the following target specification, preserving every parameter that stays equal. Recompute all affected curves, intersections, and dimension labels.\n'+json.dumps(spec)
            task['prompt']=prompt;task['reference_mask_sha256']=hashlib.sha256(reference_mask(task).tobytes()).hexdigest();tasks.append(task)
            (out/(task['id']+'.reference.svg')).write_text(oracle_svg(task))
    core.write_json(out/'tasks.json',dict(version='cad-hard-geometry-v1',system=SYSTEM,scope='Mechanical CAD profiles and oblique sections; actual material geometry, not field plots. Unaided SVG output.',criteria=dict(boundary_tolerance_mm=.5,residual_mismatch_area_mm2=2.,dimension_tolerance_mm=.1,selection='Three evaluable independent samples including two high-effort; at least two drawing failures including a high-effort failure; identified visual/evidence review. Truncation, API, missing-layer and invalid-format outcomes excluded.'),tasks=tasks))
    print('Built',len(tasks),flush=True)

def isolate(svg):
    root=ET.fromstring(svg)
    if root.get('viewBox','').replace(',',' ').split()!=['0','0','1000','1000']:raise ValueError('wrong viewBox')
    for e in root.iter():
        tag=e.tag.split('}')[-1]
        if tag in ('script','image','foreignObject','animate','animateTransform','set','style'):raise ValueError('unsupported active/raster/stylesheet content')
        for k,v in e.attrib.items():
            if k.lower().startswith('on'):raise ValueError('event handler')
            if k.endswith('href') and not v.startswith('#'):raise ValueError('external reference')
            for url in re.findall(r'url\((.*?)\)',v):
                if not url.strip(' \"\'').startswith('#'):raise ValueError('external url')
    groups=[e for e in root if e.get('data-geometry')=='part']
    if len(groups)!=1:raise ValueError('one direct material geometry group required')
    g=groups[0]
    if any(e.tag.split('}')[-1]=='text' for e in g.iter()):raise ValueError('text inside material geometry')
    for e in list(root):
        if e is not g and e.tag.split('}')[-1]!='defs':root.remove(e)
    root.set('width','1000');root.set('height','1000')
    return ET.tostring(root,encoding='unicode')

def raster(svg):
    with tempfile.TemporaryDirectory(prefix='cad-geometry-') as d:
        path=Path(d)/'shape.svg';png=Path(d)/'shape.png';path.write_text(svg);render(path,png,SIZE)
        a=np.array(Image.open(png).convert('RGB'))
    if a.shape[:2]!=(SIZE,SIZE):raise ValueError('unexpected renderer dimensions')
    return np.mean(a,axis=2)<128

def compare(actual,target):
    missing=target&~actual;extra=actual&~target
    # Interior disagreement survives a physical 0.5 mm reference-boundary band.
    interior=distance_transform_edt(target);exterior=distance_transform_edt(~target)
    residual=(missing&(interior>SCALE*.5))|(extra&(exterior>SCALE*.5))
    return dict(iou=float((target&actual).sum()/max(1,(target|actual).sum())),symmetric_difference_mm2=float((target^actual).sum()/SCALE**2),residual_mismatch_mm2=float(residual.sum()/SCALE**2),max_intrusion_mm=float(max(np.max(interior[missing],initial=0),np.max(exterior[extra],initial=0))/SCALE))

def score(task,text,reference=None,render_fn=raster,compare_fn=compare):
    row={k:[] for k in ('geometry_errors','dimension_errors','analysis_errors','format_errors','visible_result_errors')}
    try:
        obj=core.read_response(text);svg=obj['svg'];actual=render_fn(isolate(svg));target=reference_mask(task) if reference is None else reference;metrics=compare_fn(actual,target);row['geometry_metrics']=metrics
        if not actual.any():raise ValueError('empty material geometry')
        if metrics['residual_mismatch_mm2']>task.get('residual_area_tolerance_mm2',2):row['geometry_errors'].append(metrics)
        root=ET.fromstring(svg);labels={e.get('data-dimension'):''.join(e.itertext()) for e in root.iter() if e.get('data-dimension')}
        for key,expected in task['dimensions'].items():
            try:
                # Named labels can contain digits; dimension text must end with numeric value plus mm.
                numbers=re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',labels[key]);value=float(numbers[-1])
                if abs(value-expected)>.1:row['dimension_errors'].append(dict(key=key,expected=expected,actual=value))
            except (KeyError,IndexError,ValueError):row['format_errors'].append('missing numeric dimension '+key)
        row['outcome']='failure' if row['geometry_errors'] or row['dimension_errors'] else ('unscored_format' if row['format_errors'] else 'pass')
    except (ValueError,KeyError,TypeError,ET.ParseError) as exc:row['format_errors'].append(str(exc));row['outcome']='unscored_format'
    return row

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=core.ROOT/'data/cad-hard-geometry');build(p.parse_args().output)
