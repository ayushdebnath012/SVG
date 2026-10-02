"""Necessary dimension checks for public drawing 131; no full-shape verdict."""
import argparse,math
from pathlib import Path
import cadquery as cq
from cad_native_probe import write
from inspect_cad_features import inventory

def audit(shape):
    r=inventory(shape);m=r['metrics'];b=m['bbox_mm'];checks=[]
    checks.append({'requirement':'One valid connected solid','pass':m['valid'] and m['solids']==1})
    for axis,expected in [('x',145.32),('y',198.85),('z',50)]:
        observed=b[axis+'max']-b[axis+'min']
        checks.append({'requirement':f'Overall {axis.upper()} dimension','expected_mm':expected,'observed_mm':observed,'tolerance_mm':.05,'pass':abs(observed-expected)<.05})
    full=[s for s in r['surfaces'] if 'radius_mm' in s and abs(s['u_range'][1]-s['u_range'][0]-2*math.pi)<1e-4]
    for radius,lo,hi,count in [(5,27,50,2),(3,27,50,2),(40,10,40,1),(45,0,10,1),(45,40,50,1)]:
        hits=[s for s in full if abs(s['radius_mm']-radius)<1e-6 and abs(s['bbox_mm']['zmin']-lo)<1e-5 and abs(s['bbox_mm']['zmax']-hi)<1e-5]
        checks.append({'requirement':f'{count} complete bore faces R{radius}, Z{lo} to Z{hi}','observed_count':len(hits),'pass':len(hits)==count})
    angles=[]
    for s in r['surfaces']:
        if 'normal' not in s:continue
        nx,ny,nz=s['normal']
        if abs(ny)>.01 and .01<abs(nz)<.99:angles.append({'surface_id':s['index'],'angle_deg':math.degrees(math.atan(abs(nz/ny)))})
    for expected in [43.07,44.76]:
        nearest=min(angles,key=lambda a:abs(a['angle_deg']-expected))
        checks.append({'requirement':'Inclined plane YZ trace angle','expected_deg':expected,'observed':nearest,'tolerance_deg':.05,'pass':abs(nearest['angle_deg']-expected)<.05})
    return {'classification':'partial_checks_pass_full_shape_unscored' if all(c['pass'] for c in checks) else 'review_required','checks':checks,
      'scope':'Local dimensional evidence only, not official CADGenBench scoring. Surface counts are representation-dependent and any failure needs topology review. Full contour, pocket associations and lateral-window geometry remain unscored.',
      'protocol_annotation_correction':'Do not score the initial phrases "recess leaves 5 mm wall" or "8 mm lower wall and 15 mm upper walls" without resolving the section-view dimension attachments. Depth and retained thickness are not interchangeable. No model failure is inferred from those initial interpretations.',
      'selected_for_hard_subset':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('step',type=Path);p.add_argument('output',type=Path);a=p.parse_args();write(a.output,audit(cq.importers.importStep(str(a.step)).val()))
