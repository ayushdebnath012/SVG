"""Partial public-drawing audit, not the private CADGenBench scoring pipeline."""
import argparse,math,json
from pathlib import Path
import cadquery as cq
from inspect_cad_features import inventory
from cad_native_probe import write

def occupancy(shape,xyz):
    # A finite probe avoids a point exactly on a modeled boundary.
    probe=cq.Solid.makeSphere(.1,cq.Vector(*xyz))
    return shape.intersect(probe).Volume()/probe.Volume()

def audit(shape):
    evidence=inventory(shape)
    full=[s for s in evidence['surfaces'] if 'radius_mm' in s and abs(s['u_range'][1]-s['u_range'][0]-2*math.pi)<1e-4]
    checks=[]
    for radius,lo,hi,count in [(2.5,13,25,8),(4.5,0,16.4,4),(7.5,16.4,25,4),(5,0,25,4)]:
        hits=[s for s in full if abs(s['radius_mm']-radius)<1e-6 and abs(s['bbox_mm']['zmin']-lo)<1e-5 and abs(s['bbox_mm']['zmax']-hi)<1e-5]
        checks.append({'requirement':f'{count} complete bore faces of radius {radius}, Z{lo} to Z{hi}','observed_count':len(hits),'pass':len(hits)==count})
        for s in hits:
            x,y,_=s['location'];p=(x,y,(lo+hi)/2);v=occupancy(shape,p)
            checks.append({'requirement':'Bore interior is void','xyz':p,'occupied_fraction':v,'pass':v<.01})
            if radius==2.5:
                v=occupancy(shape,(x,y,10))
                checks.append({'requirement':'Blind-hole base retains material','xyz':(x,y,10),'occupied_fraction':v,'pass':v>.99})
    # Explicit 1 mm by 45 degree top edge chamfers. These locations avoid
    # holes, pockets, keys and workholding flats; no guessed bolt circle is used.
    for name,p in [('outer top chamfer',(74.75,0,24.5)),('bore top chamfer',(47.75*math.cos(math.pi/8),47.75*math.sin(math.pi/8),24.5))]:
        v=occupancy(shape,p);checks.append({'requirement':name,'xyz':p,'occupied_fraction':v,'pass':v<.01})
    for z,want in [(10,True),(20,False)]:
        p=(23,-65,z);v=occupancy(shape,p)
        checks.append({'requirement':'Pocket has retained base and removed upper material','xyz':p,'occupied_fraction':v,'pass':v>.99 if want else v<.01})
    m=evidence['metrics'];checks.extend([{'requirement':'One valid connected solid','pass':m['valid'] and m['solids']==1},{'requirement':'25 mm thickness','pass':abs(m['bbox_mm']['zmax']-m['bbox_mm']['zmin']-25)<1e-5}])
    return {'classification':'partial_checks_pass_full_shape_unscored' if all(c['pass'] for c in checks) else 'review_required',
      'checks':checks,'scope':'Public drawing necessary feature checks only. Full-circle surface count is representation-dependent; any failed count needs manual topology review. No private target comparison. Inferred pattern positions are not scored.',
      'selected_for_hard_subset':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('step',type=Path);p.add_argument('output',type=Path);a=p.parse_args();write(a.output,audit(cq.importers.importStep(str(a.step)).val()))
