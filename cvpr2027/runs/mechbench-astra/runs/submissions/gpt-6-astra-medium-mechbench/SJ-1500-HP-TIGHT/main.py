import os, json, math, argparse, itertools, time
from pathlib import Path
import cadquery as cq
import numpy as np

DEFAULTS = dict(arm_pin_spacing_mm=195.0, rated_load_N=14710.0,
    height_min_mm=104.0, height_max_mm=385.0,
    arm_width_mm=22.0, arm_depth_mm=28.0, arm_wall_mm=2.2, arm_eye_wall_mm=4.0,
    arm_layer_y_mm=20.2, arm_hole_radius_mm=6.7,
    pivot_radius_mm=6.5, pivot_half_length_mm=32.0,
    base_pivot_height_mm=17.0, saddle_pivot_offset_mm=17.0,
    base_length_mm=90.0, base_width_mm=80.0, plate_thickness_mm=2.0,
    saddle_length_mm=60.0, saddle_width_mm=70.0,
    support_length_mm=24.0, support_width_mm=16.0,
    trunnion_radius_mm=11.5, trunnion_width_mm=17.0,
    screw_minor_diameter_mm=12.8, screw_bore_diameter_mm=13.1,
    screw_end_extra_mm=16.0, screw_drive_across_flats_mm=17.0,
    screw_collar_thickness_mm=5.0, screw_collar_clearance_mm=0.4,
    steel_density_kg_per_mm3=7.85e-6, elastic_modulus_MPa=210000.0,
    arm_yield_MPa=700.0, screw_yield_MPa=1080.0,
    yield_fs_required=1.5, buckling_fs_required=2.0, mass_budget_kg=2.620)

def box(x,y,z,origin):
    return cq.Solid.makeBox(x,y,z,cq.Vector(*origin))
def cy(r,l,o,axis=(0,1,0)):
    return cq.Solid.makeCylinder(r,l,cq.Vector(*o),cq.Vector(*axis))
def capsule(L,r,w):
    s=box(L,w,2*r,(0,-w/2,-r))
    return s.fuse(cy(r,w,(0,-w/2,0)),cy(r,w,(L,-w/2,0))).clean()
def arm_placement(s, a, b, y):
    ang=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
    return s.rotate((0,0,0),(0,1,0),-ang).translate((a[0],y,a[1]))

def build(p,h=None):
    h=p['height_min_mm'] if h is None else h
    L=p['arm_pin_spacing_mm']; z0=p['base_pivot_height_mm']; z1=h-p['saddle_pivot_offset_mm']
    v=(z1-z0)/2; a=math.sqrt(L*L-v*v); zm=(z0+z1)/2
    w=p['arm_width_mm']; d=p['arm_depth_mm']; t=p['arm_wall_mm']; rh=p['arm_hole_radius_mm']; rp=p['pivot_radius_mm']; yp=p['pivot_half_length_mm']; y=p['arm_layer_y_mm']
    arm=capsule(L,d/2,w).cut(capsule(L,d/2-t,w-2*t))
    # Integral eye doublers restore local bearing area without thickening the span.
    eye=p['arm_eye_wall_mm']
    for x in [0,L]:
        arm=arm.fuse(cy(d/2-t,eye,(x,-w/2,0)),cy(d/2-t,eye,(x,w/2-eye,0)))
        arm=arm.cut(cy(rh,w+2*t,(x,-w/2-t,0)))
    arm=arm.clean()
    B=(0,z0); T=(0,z1); A=(-a,zm); C=(a,zm)
    parts={}
    endpoints={'lower_left':(B,A,-y),'lower_right':(B,C,y),'upper_left':(A,T,y),'upper_right':(C,T,-y)}
    for name,(q,r,yy) in endpoints.items(): parts[name]=arm_placement(arm,q,r,yy)
    pt=p['plate_thickness_mm']; sl=p['support_length_mm']; sw=p['support_width_mm']
    bl=p['base_length_mm']; bw=p['base_width_mm']; tl=p['saddle_length_mm']; tw=p['saddle_width_mm']
    parts['base']=box(bl,bw,pt,(-bl/2,-bw/2,0)).fuse(box(sl,sw,z0-pt,(-sl/2,-sw/2,pt)),cy(rp,2*yp,(0,-yp,z0))).clean()
    parts['saddle']=box(tl,tw,pt,(-tl/2,-tw/2,h-pt)).fuse(box(sl,sw,h-pt-z1,(-sl/2,-sw/2,z1)),cy(rp,2*yp,(0,-yp,z1))).clean()
    tr=p['trunnion_radius_mm']; wt=p['trunnion_width_mm']; br=p['screw_bore_diameter_mm']/2
    for name,x in [('left_trunnion',-a),('right_trunnion',a)]:
        parts[name]=cy(tr,wt,(x,-wt/2,zm)).fuse(cy(rp,2*yp,(x,-yp,zm))).cut(cy(br,2*tr+2,(x-tr-1,0,zm),(1,0,0))).clean()
    # The screw is rigidly retained by the left trunnion and slides through the right.
    # Its physical length remains that at the collapsed configuration.
    v0=(p['height_min_mm']-p['saddle_pivot_offset_mm']-z0)/2
    a0=math.sqrt(L*L-v0*v0)
    extra=p['screw_end_extra_mm']; sr=p['screw_minor_diameter_mm']/2
    screw=cy(sr,2*a0+2*extra,(-a-extra,0,zm),(1,0,0))
    ct=p['screw_collar_thickness_mm']; cc=p['screw_collar_clearance_mm']
    # Integral hex drive/retaining head: a standard 17 mm hand wrench fits.
    hr=p['screw_drive_across_flats_mm']/math.sqrt(3)
    polygon=[(hr*math.cos(math.radians(30+60*k)),hr*math.sin(math.radians(30+60*k))) for k in range(6)]
    head=cq.Workplane('YZ',origin=(-a-tr-cc-ct,0,zm)).polyline(polygon).close().extrude(ct).val()
    screw=screw.fuse(head).clean()
    parts['lead_screw']=screw
    return parts, endpoints, (a,zm,v), arm

def assembly(p,parts,ends,geometry):
    a,zm,v=geometry; z0=p['base_pivot_height_mm']; h=p['height_min_mm']; z1=h-p['saddle_pivot_offset_mm']; L=p['arm_pin_spacing_mm']
    roles={n:('arm' if n in ends else {'base':'base','saddle':'saddle','left_trunnion':'trunnion','right_trunnion':'trunnion','lead_screw':'screw'}[n]) for n in parts}
    result={'units':'mm','ground':'base','parts':[{'name':n,'step':'parts/'+n+'.step','material':'12.9' if n=='lead_screw' else 'S700MC','role':roles[n]} for n in parts], 'joints':[]}
    joints=result['joints']
    connections={'lower_left':('base','left_trunnion'),'lower_right':('base','right_trunnion'),'upper_left':('left_trunnion','saddle'),'upper_right':('right_trunnion','saddle')}
    for n,(q,r,yy) in ends.items():
        for i,(point,other) in enumerate(zip([q,r],connections[n])):
            joints.append(dict(name=n+'_pivot_'+str(i),type='revolute',parts=[n,other],origin=[point[0],yy,point[1]]))
    joints.extend([
        dict(name='level_saddle',type='prismatic',parts=['base','saddle'],origin=[0,0,z0],axis=[0,0,1]),
        dict(name='screw_retention',type='fixed',parts=['left_trunnion','lead_screw']),
        dict(name='thread_translation',type='prismatic',parts=['lead_screw','right_trunnion'],origin=[a,0,zm],axis=[1,0,0]),
        dict(name='lead_screw_travel',type='distance',parts=['left_trunnion','right_trunnion'],point_a=[-a,0,zm],point_b=[a,0,zm])])
    vmax=(p['height_max_mm']-p['saddle_pivot_offset_mm']-z0)/2
    result['driver']='lead_screw_travel';result['driver_range_mm']=[2*a,2*math.sqrt(L*L-vmax*vmax)]
    return result

def section_properties(p,s):
    # Exact transverse section of the hollow capsule between its pin axes.
    # Integrate the rectangles remaining after the transverse cylindrical holes.
    L=p['arm_pin_spacing_mm'];w=p['arm_width_mm'];d=p['arm_depth_mm'];t=p['arm_wall_mm'];r=p['arm_hole_radius_mm']
    wi=w-2*t;di=d-2*t
    hole=0
    for pos in [0,L]:
        if abs(s-pos)<r: hole=max(hole,2*math.sqrt(r*r-(s-pos)**2))
    area=w*d-wi*di-2*t*hole
    Iz=(d*w**3-di*wi**3-hole*(w**3-wi**3))/12
    Iy=(w*d**3-wi*di**3-2*t*hole**3)/12
    extra=p['arm_eye_wall_mm']-t
    wr=w-2*p['arm_eye_wall_mm']
    for pos in [0,L]:
        if abs(s-pos)<di/2:
            chord=2*math.sqrt((di/2)**2-(s-pos)**2)
            hh=2*math.sqrt(r*r-(s-pos)**2) if abs(s-pos)<r else 0.
            area+=2*extra*(chord-hh)
            Iy+=2*extra*(chord**3-hh**3)/12
            Iz+=(chord-hh)*(wi**3-wr**3)/12
    return area,Iy,Iz

def analyze(p,parts):
    W=p['rated_load_N'];L=p['arm_pin_spacing_mm'];E=p['elastic_modulus_MPa'];sy=p['arm_yield_MPa']
    rows=[]
    for h in np.linspace(p['height_min_mm'],p['height_max_mm'],9):
        v=(h-p['saddle_pivot_offset_mm']-p['base_pivot_height_mm'])/2
        a=math.sqrt(L*L-v*v)
        rows.append(dict(saddle_height_mm=float(h),screw_tension_N=W*a/v,arm_compression_N=W*L/(2*v),driver_distance_mm=2*a))
    peak=max(x['arm_compression_N'] for x in rows); tension=max(x['screw_tension_N'] for x in rows)
    A,Iy,Iz=section_properties(p,0);I=min(Iy,Iz);rg=math.sqrt(I/A);lam=L/rg
    transition=math.sqrt(2*math.pi**2*E/sy)
    buckstress=sy*(1-sy*lam**2/(4*math.pi**2*E)) if lam<=transition else math.pi**2*E/lam**2
    buckload=A*buckstress
    armfs=sy*A/peak
    screwfs=p['screw_yield_MPa']*math.pi*p['screw_minor_diameter_mm']**2/4/tension
    pinfs=2*0.577*sy*math.pi*p['pivot_radius_mm']**2/peak
    masses={n:s.Volume()*p['steel_density_kg_per_mm3'] for n,s in parts.items()}
    mass=sum(masses.values());fs=min(armfs,screwfs,pinfs);bfs=buckload/peak
    report=dict(screw_tension_N=tension,max_arm_compression_N=peak,mass_kg=mass,min_yield_fs=fs,min_buckling_fs=bfs,
        verdict='meets' if fs>=p['yield_fs_required'] and bfs>=p['buckling_fs_required'] and mass<=p['mass_budget_kg'] else 'fails')
    details=dict(load_cases=rows,part_masses_kg=masses,minimum_section_area_mm2=A,minimum_I_mm4=I,section_centroid_eccentricity_mm=0,
                 arm_yield_fs=armfs,screw_yield_fs=screwfs,pin_double_shear_fs=pinfs,buckling_critical_load_N=buckload,
                 buckling_model='Johnson parabola below transition slenderness, otherwise pinned Euler; conservative minimum net section throughout length',
                 slenderness=lam,transition_slenderness=transition)
    return report,details

def check_collisions(p):
    worst=0.;collisions=[]
    L=p['arm_pin_spacing_mm'];offset=p['base_pivot_height_mm']+p['saddle_pivot_offset_mm']
    v0=(p['height_min_mm']-offset)/2;v1=(p['height_max_mm']-offset)/2
    distances=np.linspace(2*math.sqrt(L*L-v0*v0),2*math.sqrt(L*L-v1*v1),5)
    for distance in distances:
        h=offset+2*math.sqrt(L*L-(distance/2)**2)
        shapes,_,_,_=build(p,float(h))
        for (n,a),(m,b) in itertools.combinations(shapes.items(),2):
            ba=a.BoundingBox();bb=b.BoundingBox()
            if ba.xmax<=bb.xmin or bb.xmax<=ba.xmin or ba.ymax<=bb.ymin or bb.ymax<=ba.ymin or ba.zmax<=bb.zmin or bb.zmax<=ba.zmin: continue
            vol=a.intersect(b).Volume();worst=max(worst,vol)
            if vol>1e-5:collisions.append(dict(height_mm=float(h),parts=[n,m],volume_mm3=vol))
    return dict(max_intersection_mm3=worst,intersections=collisions,positions_checked=5)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params');ap.add_argument('--out',default='.');args=ap.parse_args()
    p=DEFAULTS.copy()
    if args.params:
        with open(args.params) as f:p.update(json.load(f))
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True);(out/'parts').mkdir(exist_ok=True)
    def dump(name,obj):
        with open(out/name,'w') as f:json.dump(obj,f,indent=2,allow_nan=False)
    dump('params.json',p)
    parts,ends,g,arm=build(p)
    for n,s in parts.items():
        assert s.isValid() and len(s.Solids())==1,(n,'invalid solid')
        cq.exporters.export(s,str(out/'parts'/f'{n}.step'))
    asm=assembly(p,parts,ends,g)
    dump('assembly.json',asm)
    report,details=analyze(p,parts)
    from verification import verify
    details.update(verify(p,arm,asm,box,section_properties))
    assert details['kinematics']['free_dof']==1
    assert details['kinematics']['free_dof_with_driver_locked']==0
    details['collision_check']=check_collisions(p)
    if details['collision_check']['max_intersection_mm3']>2:report['verdict']='fails'
    dump('analysis.json',report);dump('engineering_checks.json',details)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
