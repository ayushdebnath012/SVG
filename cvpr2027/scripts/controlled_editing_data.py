"""Synthetic solver-linked edit-policy pilot, NOT a full scientific SVG benchmark.

The model receives a compact DOM index and emits one action. A deterministic
executor owns geometry and labels. Train/test split by physical case; annuli are
held out. Natural-language templates are deliberately shared: this measures
case transfer, not human-instruction or language-template generalization.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import re
import xml.etree.ElementTree as ET

import numpy as np
from scipy.sparse import diags, eye, kron
from scipy.sparse.linalg import spsolve

SYSTEM = '''Return exactly one JSON object for an engineering SVG edit.
Allowed schemas:
{"action":"style","target":"contour-id","attribute":"stroke","value":"#rrggbb"}
{"action":"style","target":"contour-id","attribute":"stroke-width","value":number}
{"action":"move_label","target":"label-id","x":number,"y":number}
{"action":"recompute","parameter":"left_temperature","value":number}
{"action":"reject","reason":"numerical_claim"}
{"action":"reject","reason":"missing_required_contour"}
Preserve every required contour's numerical value, geometry and visibility.
Changing a physical boundary requires a new solve. Relabeling a contour to a
different physical value without changing geometry is forbidden. Labels can move
only inside the right annotation panel. Styling does not require a new solve.
Hex colors are copied verbatim. Do not include explanations or markdown.'''


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def solve_plate(width, height, left, right, n=25):
    """-Laplacian T=0, left/right prescribed; insulated top/bottom.

    FD on interior x nodes and all y nodes, zero-flux graph boundary on y.
    Exact solution is linear in x; check it independently on every instance.
    This simple manufactured control is not a challenging PDE benchmark.
    """
    x, y = np.linspace(0, width, n), np.linspace(0, height, n)
    nx, ny = n-2, n
    dx, dy = x[1], y[1]
    ax = diags([-np.ones(nx-1), 2*np.ones(nx), -np.ones(nx-1)], [-1,0,1])/dx**2
    diagonal = 2*np.ones(ny); diagonal[[0,-1]] = 1
    ay = diags([-np.ones(ny-1), diagonal, -np.ones(ny-1)], [-1,0,1])/dy**2
    matrix = kron(eye(ny), ax)+kron(ay, eye(nx))
    rhs = np.zeros((ny,nx)); rhs[:,0] += left/dx**2; rhs[:,-1] += right/dx**2
    interior = spsolve(matrix.tocsr(), rhs.ravel())
    field = np.column_stack([np.full(ny,left), interior.reshape(ny,nx), np.full(ny,right)])
    exact = left+(right-left)*x/width
    error = float(np.max(np.abs(field-exact)))
    assert error < 1e-8
    residual = float(np.max(np.abs(matrix@interior-rhs.ravel())) / max(np.max(np.abs(rhs)),1))
    return x,y,field,{'method':'finite-difference sparse solve', 'grid':[n,n],
                      'max_error_against_exact_K':error, 'relative_linear_residual':residual}


def make_document(case_id, rng, annulus=False):
    width,height = round(rng.uniform(.7,2.5),4),round(rng.uniform(.8,2.0),4)
    cold,hot = rng.randint(270,310),rng.randint(340,410)
    field = {'quantity':'temperature','unit':'K','left_temperature':hot,
             'right_temperature':cold,'width_m':width,'height_m':height,
             'family':'annulus' if annulus else 'insulated_rectangle'}
    levels = [round(cold+(hot-cold)*f,3) for f in (.25,.5,.75)]
    if annulus:
        # Analytic radial Laplace solution between concentric circles, hot inside.
        field.update(inner_radius_m=.25*width,outer_radius_m=width)
        reference = {'method':'analytic radial Laplace', 'formula':'cold+(hot-cold)*log(R/r)/log(R/a)'}
    else:
        _,_,_,reference = solve_plate(width,height,hot,cold)
    record = {'case_id':case_id,'physical_problem':field,'reference':reference}
    solution_id = digest(record)
    root = ET.Element('svg',xmlns='http://www.w3.org/2000/svg',viewBox='0 0 640 460')
    group = ET.SubElement(root,'g',id='field', **{'data-solution-id':solution_id})
    contours,labels = [],[]
    for level in levels:
        cid = 'c'+str(rng.randrange(1000,9999)); lid = 'l'+cid[1:]
        if annulus:
            radius = 180*math.exp(-(level-cold)/(hot-cold)*math.log(4))
            ET.SubElement(group,'circle',id=cid,cx='220',cy='230',r=f'{radius:.8f}',fill='none',stroke='#334155',
                          **{'stroke-width':'1.5','data-level':str(level)})
        else:
            xpos=40+360*(hot-level)/(hot-cold)
            ET.SubElement(group,'path',id=cid,d=f'M{xpos:.8f} 40 L{xpos:.8f} 420',fill='none',stroke='#334155',
                          **{'stroke-width':'1.5','data-level':str(level)})
        contours.append({'id':cid,'level':level,'unit':'K','required':True})
        label=ET.SubElement(root,'text',id=lid,x='470',y=str(100+80*len(labels)), **{'data-contour':cid})
        label.text=f'{level:g} K'
        labels.append({'id':lid,'contour':cid,'text':label.text})
    return {'solution_id':solution_id,'record':record,'contours':contours,'labels':labels,
            'svg':ET.tostring(root,encoding='unicode')}


def execute(document, action):
    """Whitelist executor for this generated schema; no arbitrary SVG accepted.

    Does not interpret natural language. A policy model can choose the wrong
    permitted action; semantic correctness is measured separately against target.
    Recompute only returns a pending request, never a newly verified solution.
    """
    if not isinstance(action,dict):
        raise ValueError('action must be object')
    original = copy.deepcopy(document)
    root=ET.fromstring(document['svg']); nodes={e.get('id'):e for e in root.iter() if e.get('id')}
    name=action.get('action')
    def keys(wanted):
        if set(action) != set(wanted.split()): raise ValueError('invalid action schema')
    def numeric(v):
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v): raise ValueError('finite number required')
    if name=='style':
        keys('action target attribute value')
        if action['target'] not in {c['id'] for c in document['contours']}: raise ValueError('unknown contour')
        attr,val=action['attribute'],action['value']
        if attr=='stroke':
            if not isinstance(val,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',val): raise ValueError('hex color required')
            # White/near-white cannot be allowed to make required curves disappear.
            if min(int(val[i:i+2],16) for i in (1,3,5))>220: raise ValueError('insufficient contrast')
        elif attr=='stroke-width':
            numeric(val)
            if not .5<=val<=4: raise ValueError('width outside visible bounds')
        else: raise ValueError('protected property')
        nodes[action['target']].set(attr,str(val))
    elif name=='move_label':
        keys('action target x y')
        if action['target'] not in {l['id'] for l in document['labels']}: raise ValueError('unknown label')
        numeric(action['x']);numeric(action['y'])
        if not (460<=action['x']<=540 and 30<=action['y']<=430): raise ValueError('label outside annotation panel')
        for attr in ('x','y'): nodes[action['target']].set(attr,str(action[attr]))
    elif name=='recompute':
        keys('action parameter value');numeric(action['value'])
        if action['parameter']!='left_temperature' or not 0<action['value']<2000: raise ValueError('unsupported physical input')
        return {'status':'requires_solver','document':original,'request':action}
    elif name=='reject':
        keys('action reason')
        if action['reason'] not in ('numerical_claim','missing_required_contour'): raise ValueError('unknown reason')
        return {'status':'rejected','document':original}
    else: raise ValueError('unknown action')
    original['svg']=ET.tostring(root,encoding='unicode')
    return {'status':'edited','document':original}


def examples(doc,rng,split):
    c=rng.choice(doc['contours']); l=next(l for l in doc['labels'] if l['contour']==c['id'])
    color=rng.choice(['#2563eb','#dc2626','#059669','#7c3aed','#d97706','#0e7490'])
    width=rng.choice([.75,1,2,2.5,3]); x=rng.randint(465,535);y=rng.randint(35,420)
    newtemp=rng.randint(330,450)
    tasks=[
        (rng.choice([f"Set contour {c['id']}'s stroke to {color}.",f"Use {color} for the line color of {c['id']}."]),
         {'action':'style','target':c['id'],'attribute':'stroke','value':color}),
        (rng.choice([f"Give {c['id']} a stroke width of {width}.",f"Change line thickness of contour {c['id']} to {width} SVG units."]),
         {'action':'style','target':c['id'],'attribute':'stroke-width','value':width}),
        (rng.choice([f"Move label {l['id']} to x={x}, y={y} in the annotation panel.",f"Place the text {l['id']} at ({x}, {y}); preserve its value and units."]),
         {'action':'move_label','target':l['id'],'x':x,'y':y}),
        (rng.choice([f"Change the hot boundary temperature to {newtemp} K and update the solution.",f"Solve the problem again with left_temperature={newtemp} K."]),
         {'action':'recompute','parameter':'left_temperature','value':newtemp}),
        (rng.choice([f"Keep the geometry but label the {c['level']} K curve as {c['level']+20:g} K.",f"Replace the value on {l['id']} with {c['level']+20:g} K without solving again."]),
         {'action':'reject','reason':'numerical_claim'}),
        (rng.choice([f"Hide required contour {c['id']} so the plot looks cleaner.",f"Remove the required curve {c['id']} from the displayed drawing."]),
         {'action':'reject','reason':'missing_required_contour'})]
    index={'physical_problem':doc['record']['physical_problem'],'contours':doc['contours'],'labels':doc['labels'],
           'annotation_panel':{'x':[460,540],'y':[30,430]}}
    rows=[]
    for i,(instruction,target) in enumerate(tasks):
        # An executor validity check is not a general physics correctness proof.
        execute(doc,target)
        rows.append({'id':f"{doc['record']['case_id']}-{i}",'case_id':doc['record']['case_id'],'split':split,
                     'instruction':instruction,'input':json.dumps(index,separators=(',',':'))+'\nRequest: '+instruction,
                     'target':target,'document':doc})
    return rows


def build(output,seed=2027,counts=(60,10,10,10)):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);rng=random.Random(seed)
    manifests={};all_cases=set()
    for split,count in zip(('train','validation','test','ood'),counts):
        rows=[]
        for i in range(count):
            case_id=f'{split}-{i:04d}';assert case_id not in all_cases;all_cases.add(case_id)
            doc=make_document(case_id,rng,annulus=split=='ood');rows.extend(examples(doc,rng,split))
        rng.shuffle(rows)
        content=''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows)
        (output/f'{split}.jsonl').write_text(content)
        manifests[split]={'cases':count,'examples':len(rows),'sha256':hashlib.sha256(content.encode()).hexdigest()}
    manifest={'version':'controlled-editing-pilot-v1','seed':seed,'splits':manifests,
              'limitations':['synthetic shared instruction templates','compact DOM index, not vision input',
                             'simple manufactured heat equations','recompute is routing only',
                             'not evidence of CVPR-level novelty or complete SVG verification']}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2));return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='runs/cvpr2027/controlled-editing-data')
    a=p.parse_args();print(json.dumps(build(a.output),indent=2))
