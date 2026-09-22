"""Object-centred CAD SVG failure discovery. Commands: build, run, score, select.

No external solver tools are supplied to the unaided Astra baseline. References
are linear 2D Euler-Bernoulli frame FEM, not whole-object safety certification.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
from datetime import datetime, timezone
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from svgpatchlab.eval.field_fidelity import element_path, transform_matrix
from svgpathtools import Line

DATA = ROOT / 'data/cad-astra-pilot'
VERSION = 'cad-frame-pilot-v1'
ENDPOINT = 'https://api.openai.com/v1/chat/completions'
SYSTEM = '''Produce a precise, readable CAD-style SVG structural elevation of the requested object.
Return one JSON object with keys svg (a complete SVG string) and analysis (an object).
This is a dimensioned object drawing, not a field-contour plot. Follow the stated linear frame model.
Use your own reasoning; no external tools are provided. Do not claim you ran a solver.
All physical lengths use mm, forces N, moments N mm, stresses MPa, and E N/mm^2.
Draw each physical member as exactly one visible straight line, path or polyline with data-member="its ID";
paths/polylines may contain multiple collinear segments. The tagged line is the member centreline.
Use an explicit nonzero stroke. Keep the required viewBox and coordinate map. Ancestor transforms are allowed.
Do not use scripts, external assets, CSS style sheets, use elements, clipping, masks, nested SVG or hidden geometry.
Add readable node/member IDs, supports, load arrows, section notes and dimensions with extension/dimension lines.
Each requested dimension has one visible text element with data-dimension="its ID" and its numeric value in mm.
analysis must contain ux_mm, uy_mm at the specified probe node, peak_stress_mpa (maximum absolute extreme-fibre
normal stress |N|/A + |M|*(h/2)/I across all member ends), and status (calculated, estimated or unavailable).
Also show these three results as visible SVG text with data-result="ux_mm", "uy_mm", "peak_stress_mpa".
Those text elements must contain the numeric result followed by its unit; if unavailable write unavailable and use null in JSON.
Linear elasticity, small displacements, rigid joints, axial and Euler-Bernoulli bending only; omit shear deformation,
self-weight, buckling, out-of-plane behaviour and connection flexibility. Loads act only at the listed nodes.
A result below the task limit is a pass only for that named check, not a claim that the whole object is safe.'''


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def stiffness(a, b, E, width, height):
    dx, dy = np.array(b) - np.array(a)
    L = float(np.hypot(dx, dy))
    if L <= 1e-8:
        raise ValueError('zero-length member')
    A, I = width * height, width * height**3 / 12
    c, s = dx / L, dy / L
    T = np.zeros((6, 6))
    R = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
    T[:3, :3] = T[3:, 3:] = R
    k = np.zeros((6, 6))
    k[np.ix_([0, 3], [0, 3])] = E * A / L * np.array([[1, -1], [-1, 1]])
    k[np.ix_([1, 2, 4, 5], [1, 2, 4, 5])] = E * I / L**3 * np.array([
        [12, 6*L, -12, 6*L], [6*L, 4*L*L, -6*L, 2*L*L],
        [-12, -6*L, 12, -6*L], [6*L, 2*L*L, -6*L, 4*L*L]])
    return k, T, A, I


def solve(model, subdivisions=1):
    """Uniform sections, nodal loads; subdivision checks nodal response invariance."""
    coords = copy.deepcopy(model['nodes'])
    elements = []
    for member in model['members']:
        a, b = member['a'], member['b']
        chain = [a]
        for j in range(1, subdivisions):
            nid = f"__{member['id']}_{j}"
            coords[nid] = (np.array(coords[a]) + j / subdivisions * (np.array(coords[b]) - coords[a])).tolist()
            chain.append(nid)
        chain.append(b)
        elements.extend((member, i, j) for i, j in zip(chain[:-1], chain[1:]))
    ids = list(coords)
    index = {n: i for i, n in enumerate(ids)}
    nd = 3 * len(ids)
    K, f = np.zeros((nd, nd)), np.zeros(nd)
    assembly = []
    for member, a, b in elements:
        k, T, A, I = stiffness(coords[a], coords[b], member['E'], member['b_mm'], member['h_mm'])
        dofs = np.array([3*index[a]+j for j in range(3)] + [3*index[b]+j for j in range(3)])
        K[np.ix_(dofs, dofs)] += T.T @ k @ T
        assembly.append((member, dofs, k, T, A, I))
    for n, load in model['loads'].items():
        f[3*index[n]:3*index[n]+3] += load
    fixed = sorted({3*index[n]+d for n, ds in model['supports'].items() for d in ds})
    free = np.setdiff1d(np.arange(nd), fixed)
    u = np.zeros(nd)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], f[free])
    residual = np.einsum("ij,j->i", K, u) - f
    stress = 0.0
    member_stress = {}
    for member, dofs, k, T, A, I in assembly:
        q = k @ T @ u[dofs]
        peak = max(abs(q[0])/A + abs(q[2])*member['h_mm']/2/I,
                   abs(q[3])/A + abs(q[5])*member['h_mm']/2/I)
        stress = max(stress, peak)
        member_stress[member['id']] = max(member_stress.get(member['id'], 0), float(peak))
    p = index[model['probe']]
    reactions = {n: residual[3*index[n]:3*index[n]+3].tolist() for n in model['supports']}
    all_forces = (f + residual).reshape(-1, 3)
    xy = np.array(list(coords.values()))
    balance = [float(all_forces[:, 0].sum()), float(all_forces[:, 1].sum()),
               float((all_forces[:, 2] + xy[:, 0]*all_forces[:, 1] - xy[:, 1]*all_forces[:, 0]).sum())]
    return {'ux_mm': float(u[3*p]), 'uy_mm': float(u[3*p+1]), 'peak_stress_mpa': float(stress),
            'member_stress_mpa': member_stress, 'reactions': reactions, 'equilibrium_residual_N_Nmm': balance,
            'free_residual_max_N_Nmm': float(np.abs(residual[free]).max(initial=0))}


def cantilever_virtual_work(model):
    """Independent statics + unit-load energy integral for an unbranched shelf.

    Integrate N*n/(EA) + M*m/(EI) along each member. No global stiffness
    matrix is used. Exact for this linear beam model with node-only loads.
    """
    chain = model['members']
    if model['supports'] != {chain[0]['a']:[0,1,2]} or model['probe'] != chain[-1]['b']:
        raise ValueError('requires a single clamped, unbranched chain with tip probe')
    for left,right in zip(chain[:-1],chain[1:]):
        if left['b'] != right['a']: raise ValueError('not a chain')
    result = {'ux_mm':0.0, 'uy_mm':0.0, 'peak_stress_mpa':0.0}
    gauss, weights = np.polynomial.legendre.leggauss(3)
    tip = np.array(model['nodes'][model['probe']])
    for i,member in enumerate(chain):
        a,b = (np.array(model['nodes'][n],dtype=float) for n in (member['a'],member['b']))
        length = np.linalg.norm(b-a); tangent = (b-a)/length
        area = member['b_mm']*member['h_mm']; inertia=member['b_mm']*member['h_mm']**3/12
        downstream = {m['b'] for m in chain[i:]}
        forces = [(np.array(model['nodes'][n]), np.array(f)) for n,f in model['loads'].items() if n in downstream]
        def section(x):
            N = sum(float(f[:2] @ tangent) for _,f in forces)
            M = sum(float((p[0]-x[0])*f[1]-(p[1]-x[1])*f[0]+f[2]) for p,f in forces)
            return N,M
        for x in (a,b):
            N,M=section(x)
            result['peak_stress_mpa']=max(result['peak_stress_mpa'],abs(N)/area+abs(M)*member['h_mm']/2/inertia)
        for g,w in zip(gauss,weights):
            x=a+(g+1)/2*(b-a); N,M=section(x)
            for key,unit in [('ux_mm',np.array([1.,0.])),('uy_mm',np.array([0.,1.]))]:
                n=float(unit @ tangent); m=(tip[0]-x[0])*unit[1]-(tip[1]-x[1])*unit[0]
                result[key] += float(w*length/2*(N*n/(member['E']*area)+M*m/(member['E']*inertia)))
    return result


def member(mid, a, b, width, height, E=200000):
    return dict(id=mid, a=a, b=b, b_mm=width, h_mm=height, E=E)


def models():
    table = dict(name='Asymmetric steel worktable front frame',
        nodes={'A':[0,0], 'B':[0,720], 'C':[610,720], 'D':[1580,720], 'E':[1580,0]},
        members=[member('leg_L','A','B',35,35), member('top_L','B','C',30,55),
                 member('top_R','C','D',30,55), member('leg_R','D','E',35,35)],
        supports={'A':[0,1,2], 'E':[0,1,2]}, loads={'C':[180,-1350,0]}, probe='C',
        limits={'abs_uy_mm':3.0, 'peak_stress_mpa':150.0})
    table_edit = copy.deepcopy(table)
    table_edit['nodes']['D'][0] = table_edit['nodes']['E'][0] = 1970
    table_edit['nodes']['C'][0] = 760
    for m in table_edit['members']:
        if m['id'].startswith('top_'): m['h_mm'] = 42
    building = dict(name='Two-storey setback building frame elevation',
        nodes={'A':[0,0], 'B':[3400,0], 'C':[7700,0], 'D':[0,2900], 'E':[3400,2900],
               'F':[7700,2900], 'G':[0,6200], 'H':[3400,6200]},
        members=[member('col_AD','A','D',160,200), member('col_BE','B','E',160,200),
                 member('col_CF','C','F',140,180), member('beam_DE','D','E',140,260),
                 member('beam_EF','E','F',140,260), member('col_DG','D','G',140,180),
                 member('col_EH','E','H',140,180), member('beam_GH','G','H',120,240)],
        supports={'A':[0,1,2], 'B':[0,1,2], 'C':[0,1,2]},
        loads={'G':[12500,-28000,0], 'H':[0,-46000,0], 'F':[8500,-39000,0]}, probe='H',
        limits={'abs_uy_mm':10.0, 'peak_stress_mpa':160.0})
    building_edit = copy.deepcopy(building)
    for n in ('B','E','H'): building_edit['nodes'][n][0] = 4100
    for n in ('G','H'): building_edit['nodes'][n][1] = 6800
    building_edit['loads']['H'][1] = -61000
    shelf = dict(name='Cranked wall-mounted display shelf frame',
        nodes={'A':[0,0], 'B':[420,0], 'C':[690,240], 'D':[1180,240], 'E':[1430,80]},
        members=[member('arm_AB','A','B',25,38), member('riser_BC','B','C',25,32),
                 member('shelf_CD','C','D',25,38), member('lip_DE','D','E',25,30)],
        supports={'A':[0,1,2]}, loads={'C':[0,-170,0], 'E':[65,-430,0]}, probe='E',
        limits={'abs_uy_mm':8.0, 'peak_stress_mpa':180.0})
    shelf_edit = copy.deepcopy(shelf)
    shelf_edit['nodes']['C'] = [760,310]
    shelf_edit['nodes']['D'] = [1370,310]
    shelf_edit['nodes']['E'] = [1670,120]
    shelf_edit['members'][0]['h_mm'] = 44
    return [
        ('table',table,table_edit,'Extend the right leg x-position to 1970 mm, move the top load node C to x=760 mm, and reduce both top member section heights from 55 to 42 mm. Keep every other property and load unchanged.'),
        ('building',building,building_edit,'Move the middle column grid B/E/H from x=3400 to x=4100 mm, raise the upper floor G/H to y=6800 mm, and change the vertical load at H to -61000 N. Keep the right grid, lower floor, all sections and other loads unchanged.'),
        ('shelf',shelf,shelf_edit,'Move C to (760,310), D to (1370,310), E to (1670,120) mm and increase only member arm_AB section height to 44 mm. Keep A, B, all other sections and the node-attached loads unchanged.')]


def dimensions(model):
    result = {}
    for m in model['members']:
        a, b = np.array(model['nodes'][m['a']]), np.array(model['nodes'][m['b']])
        result['length_' + m['id']] = float(np.linalg.norm(b-a))
    return result


def mapping(model):
    xy = np.array(list(model['nodes'].values()))
    return min(800/max(xy[:,0].max(),1), 450/max(xy[:,1].max(),1)), 100, 610


def reference_svg(model, scale_map):
    s, ox, oy = scale_map
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 850" width="1100" height="850">',
             '<rect width="1100" height="850" fill="white"/>',
             f'<text x="35" y="40" font-size="23">{html.escape(model["name"])}</text>',
             '<text x="35" y="66" font-size="14">Structural centreline elevation — dimensions mm; sections b × h mm</text>']
    for i,m in enumerate(model['members']):
        a,b = [model['nodes'][n] for n in (m['a'],m['b'])]
        x1,y1,x2,y2 = ox+s*a[0],oy-s*a[1],ox+s*b[0],oy-s*b[1]
        length = dimensions(model)['length_'+m['id']]
        lines += [f'<line data-member="{m["id"]}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#1f3348" stroke-width="4"/>',
                  f'<text data-dimension="length_{m["id"]}" x="{(x1+x2)/2+8}" y="{(y1+y2)/2-10}" font-size="12">{length:.3f} mm</text>',
                  f'<text x="{35+(i%4)*265}" y="{695+(i//4)*22}" font-size="12">{m["id"]}: {m["b_mm"]} × {m["h_mm"]}</text>']
    for n,(x,y) in model['nodes'].items():
        X,Y = ox+s*x,oy-s*y
        lines += [f'<circle cx="{X}" cy="{Y}" r="4" fill="#1f3348"/>',
                  f'<text x="{X+8}" y="{Y+17}" font-size="13">{n}</text>']
        if n in model['supports']:
            lines.append(f'<path d="M{X-12},{Y+6} H{X+12} M{X-12},{Y+6} l-6,9 M{X},{Y+6} l-6,9 M{X+12},{Y+6} l-6,9" stroke="black" fill="none"/>')
    r=solve(model)
    for i,k in enumerate(('ux_mm','uy_mm','peak_stress_mpa')):
        unit='MPa' if k.endswith('mpa') else 'mm'
        lines.append(f'<text x="{35+i*345}" y="790" font-size="14">{k}: <tspan data-result="{k}">{r[k]:.6f} {unit}</tspan></text>')
    lines.append('</svg>')
    return '\n'.join(lines)


def build(out=DATA):
    if (out/'tasks.json').exists():
        raise ValueError('Frozen manifest already exists; choose a fresh --data directory to rebuild')
    out.mkdir(parents=True, exist_ok=True)
    tasks=[]
    for family,base,edited,instruction in models():
        common_map=mapping(edited)
        for mode,model in [('generate',base),('edit',edited)]:
            task=dict(id=f'{family}_{mode}',family=family,mode=mode,model=model,mapping=common_map,
                      dimensions=dimensions(model),limits=model['limits'])
            prompt=(f'Object: {model["name"]}. Make a dimensioned structural elevation. '
                    'All sections are solid rectangles; h is in the frame plane and b is out of plane. '
                    'The idealised table feet are clamped, not freely resting on a floor. '
                    'This task concerns only the stated 2D frame, not complete product/building validation. ')
            if mode=='generate': prompt += '\nPhysical model:\n'+json.dumps(base)
            else:
                source=reference_svg(base,common_map)
                task['source_model']=base
                task['source_svg']=source
                prompt += '\nOriginal physical model:\n'+json.dumps(base)+'\nOriginal SVG:\n'+source+'\nEDIT: '+instruction
            s,ox,oy=common_map
            prompt += (f'\nKeep viewBox="0 0 1100 850". Map physical (x,y) mm to SVG (X,Y) as '
                       f'X={ox}+{s:.15g}*x, Y={oy}-{s:.15g}*y. Draw exactly the listed members. '
                       'Retain member IDs. Required dimensions are the physical centreline length of every member, '
                       'tagged data-dimension="length_MEMBERID". Recompute dimensions and analysis after any edit. '
                       f'Report signed ux and uy at {model["probe"]}, plus peak extreme-fibre normal stress across member ends. '
                       'Give at least three significant digits. Check against the limits in the model; no other safety claims.')
            task['prompt']=prompt
            ref=solve(model)
            fine=solve(model,subdivisions=4)
            ref['subdivision_relative_difference']={k:abs(ref[k]-fine[k])/max(abs(ref[k]),1e-8) for k in ('ux_mm','uy_mm','peak_stress_mpa')}
            if max(ref['subdivision_relative_difference'].values())>1e-7: raise ValueError('reference refinement disagreement')
            task['validation_techniques']=['SVG geometry and connectivity constraints','dimension consistency','global force and moment equilibrium','linear frame FEM','member-subdivision reference check']
            if family=='shelf':
                independent=cantilever_virtual_work(model)
                discrepancies={k:abs(ref[k]-independent[k])/max(abs(independent[k]),1e-8) for k in independent}
                if max(discrepancies.values())>1e-7: raise ValueError('independent statics/energy reference disagreement')
                ref['independent_statics_virtual_work']=independent
                ref['independent_relative_difference']=discrepancies
                task['validation_techniques'].append('independent statics and analytical virtual-work beam solution')
            task['reference']=ref
            task['model_sha256']=digest(model)
            tasks.append(task)
            (out/(task['id']+'.reference.svg')).write_text(reference_svg(model,common_map))
    manifest=dict(version=VERSION,scope='Pilot: dimensioned structural elevations, 3 planar frame families, generation and editing. Not general 3D CAD.',
        criteria={'geometry_tolerance_mm':1.0,'dimension_tolerance_mm':1.0,'numeric_rtol':0.02,
                  'displacement_atol_mm':0.01,'stress_atol_mpa':0.05,
                  'selection':'At least 2 substantive failures across 3 completed non-truncated samples, including at least one high-effort confirmation; visual/evidence review required. Format-only, missing output, API and token-budget failures are excluded.'},
        tasks=tasks)
    write_json(out/'tasks.json',manifest)
    print('Built',len(tasks),'tasks with FEM references',flush=True)


def read_response(text):
    text=text.strip()
    if text.startswith('```'):
        text=re.sub(r'^```(?:json)?\s*','',text)
        text=re.sub(r'\s*```$','',text)
    obj=json.loads(text)
    if not isinstance(obj,dict) or not isinstance(obj.get('svg'),str) or not isinstance(obj.get('analysis'),dict):
        raise ValueError('Expected JSON svg string and analysis object')
    return obj


def svg_geometry(svg):
    """Extract actual rendered centreline geometry; unsupported rendering is unscored."""
    root=ET.fromstring(svg)
    if root.tag.split('}')[-1]!='svg': raise ValueError('not an SVG root')
    if [float(v) for v in re.split(r'[ ,]+',root.get('viewBox',''))] != [0,0,1100,850]:
        raise ValueError('wrong or absent viewBox')
    if '<!DOCTYPE' in svg.upper() or '<!ENTITY' in svg.upper(): raise ValueError('unsupported declaration')
    members={}; dims={}; results={}
    def walk(el,matrix,style,in_defs=False):
        tag=el.tag.split('}')[-1]
        if tag in ('script','image','foreignObject','use','style','clipPath','mask','filter'):
            raise ValueError('unsupported rendering: '+tag)
        if tag=='svg' and el is not root: raise ValueError('nested SVG')
        if any(k in el.attrib for k in ('clip-path','mask','filter')): raise ValueError('unsupported compositing')
        style=dict(style)
        for k in ('stroke','stroke-width','opacity','stroke-opacity','fill-opacity','display','visibility'):
            if k in el.attrib: style[k]=el.get(k)
        for entry in el.get('style','').split(';'):
            if ':' in entry:
                k,v=entry.split(':',1); style[k.strip()]=v.strip()
        if any(k in style for k in ('clip-path','mask','filter','transform')): raise ValueError('unsupported CSS geometry')
        matrix=matrix@transform_matrix(el.get('transform',''))
        hidden=(style.get('display')=='none' or style.get('visibility') in ('hidden','collapse')
                or float(style.get('opacity',1))==0 or in_defs or tag=='defs')
        # Hidden ancestor remains hidden even if a child overrides opacity.
        if hidden: style['__hidden']='true'
        hidden=hidden or style.get('__hidden')=='true'
        mid=el.get('data-member')
        if mid is not None:
            if mid in members: raise ValueError('duplicate member ID')
            if hidden or style.get('stroke','none') in ('none','transparent') or float(style.get('stroke-width',1))<=0 or float(style.get('stroke-opacity',1))<=0:
                raise ValueError('member is not visibly stroked')
            path=element_path(el)
            if not len(path) or any(not isinstance(seg,Line) for seg in path): raise ValueError('member must be straight segments')
            points=[]
            for seg in path:
                if points and abs(seg.start-points[-1])>1e-8: raise ValueError('disconnected member path')
                points.extend([seg.start,seg.end])
            pts=np.array([[p.real,p.imag,1] for p in points])@matrix.T
            if not np.isfinite(pts).all(): raise ValueError('nonfinite geometry')
            members[mid]=pts[:,:2]
        for attr,bag in [('data-dimension',dims),('data-result',results)]:
            key=el.get(attr)
            if key is not None:
                if key in bag or hidden or tag not in ('text','tspan'): raise ValueError('duplicate/hidden/nontext annotation')
                bag[key]=''.join(el.itertext()).strip()
        for child in el: walk(child,matrix,style,in_defs or tag=='defs')
    walk(root,np.eye(3),{})
    return members,dims,results


def first_number(text):
    match=re.search(r'(?<![\w])[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?',text.replace('−','-'))
    if not match: raise ValueError('no number')
    return float(match[0])


def score(task,text):
    if task.get("kind")=="precision_torus":
        from cad_precision_sections import score as score_precision
        return score_precision(task,text)
    if task.get("kind")=="torus_section":
        from cad_torus_sections import score as score_torus
        return score_torus(task,text)
    if task.get('kind')=='hard_geometry':
        from cad_hard_geometry import score as score_hard_geometry
        return score_hard_geometry(task,text)
    if task.get('kind')=='plate':
        from cad_part_cases import score as score_plate
        return score_plate(task,text)
    row={'geometry_errors':[], 'dimension_errors':[], 'analysis_errors':[], 'format_errors':[], 'visible_result_errors':[]}
    try:
        obj=read_response(text)
        drawn,dims,visible=svg_geometry(obj['svg'])
    except (ValueError,TypeError,KeyError,ET.ParseError,OverflowError) as exc:
        row['format_errors'].append(str(exc)); row['outcome']='unscored_format'; return row
    model=task['model']; expected={m['id']:m for m in model['members']}
    if set(drawn)!=set(expected):
        row['geometry_errors'].append({'member_set':{'missing':sorted(set(expected)-set(drawn)), 'extra':sorted(set(drawn)-set(expected))}})
    s,ox,oy=task['mapping']
    observations={n:[] for n in model['nodes']}
    for mid in set(drawn)&set(expected):
        m=expected[mid]; pts=drawn[mid].copy()
        pts[:,0]=(pts[:,0]-ox)/s; pts[:,1]=(oy-pts[:,1])/s
        a,b=np.array(model['nodes'][m['a']]),np.array(model['nodes'][m['b']])
        if np.linalg.norm(pts[0]-b)+np.linalg.norm(pts[-1]-a)<np.linalg.norm(pts[0]-a)+np.linalg.norm(pts[-1]-b): pts=pts[::-1]
        delta=b-a; t=np.clip(((pts-a)@delta)/(delta@delta),0,1)
        line_error=float(np.max(np.linalg.norm(pts-(a+t[:,None]*delta),axis=1)))
        endpoint_error=float(max(np.linalg.norm(pts[0]-a),np.linalg.norm(pts[-1]-b)))
        if max(line_error,endpoint_error)>1.0:
            row['geometry_errors'].append({'member':mid,'endpoint_error_mm':endpoint_error,'line_error_mm':line_error})
        observations[m['a']].append(pts[0]); observations[m['b']].append(pts[-1])
    for n,pts in observations.items():
        if len(pts)>1:
            gap=float(max(np.linalg.norm(a-b) for a in pts for b in pts))
            if gap>1.0: row['geometry_errors'].append({'node':n,'joint_gap_mm':gap})
    for key,expected_value in task['dimensions'].items():
        try:
            actual=first_number(dims[key])
            if abs(actual-expected_value)>1.0: row['dimension_errors'].append({'id':key,'expected_mm':expected_value,'actual_mm':actual})
            if not re.search(r'\bmm\b',dims[key]): row['format_errors'].append('missing mm unit: '+key)
        except (ValueError,KeyError): row['format_errors'].append('missing numeric dimension: '+key)
    for key in ('ux_mm','uy_mm','peak_stress_mpa'):
        v=obj['analysis'].get(key)
        if not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v):
            row['format_errors'].append('unavailable numeric analysis: '+key); continue
        expected_value=task['reference'][key]
        tol=max(0.02*abs(expected_value),0.05 if key.endswith('mpa') else 0.01)
        if abs(v-expected_value)>tol:
            row['analysis_errors'].append({'quantity':key,'expected':expected_value,'actual':v,'absolute_error':abs(v-expected_value),'tolerance':tol})
        try:
            if abs(first_number(visible[key])-v)>max(abs(v)*0.001,0.001):
                row['visible_result_errors'].append({'quantity':key,'json':v,'svg':visible[key]})
        except (KeyError,ValueError): row['format_errors'].append('missing visible result: '+key)
    if obj['analysis'].get('status') not in ('calculated','estimated','unavailable'):
        row['format_errors'].append('missing/invalid analysis status')
    row['analysis_status']=obj['analysis'].get('status')
    row['geometry_pass']=not row['geometry_errors']
    row['dimension_pass']=not row['dimension_errors'] and not any('dimension' in v for v in row['format_errors'])
    row['analysis_pass']=not row['analysis_errors'] and not any('analysis' in v for v in row['format_errors'])
    row['reference_checks']={'deflection':abs(task['reference']['uy_mm'])<=model['limits']['abs_uy_mm'],
                             'stress':task['reference']['peak_stress_mpa']<=model['limits']['peak_stress_mpa']}
    # Re-solve the actual extracted drawing only if all member endpoints exist and joints agree.
    if set(drawn)==set(expected) and all(observations.values()) and not any('joint_gap_mm' in e for e in row['geometry_errors']):
        reconstructed=copy.deepcopy(model)
        reconstructed['nodes']={n:np.mean(p,axis=0).tolist() for n,p in observations.items()}
        try:
            row['drawn_geometry_fem']=solve(reconstructed)
        except (ValueError,np.linalg.LinAlgError): row['drawn_geometry_fem_error']='invalid/singular drawn geometry'
    substantive=any(row[k] for k in ('geometry_errors','dimension_errors','analysis_errors','visible_result_errors'))
    row['outcome']='failure' if substantive else ('unscored_format' if row['format_errors'] else 'pass')
    return row


def api_key():
    key=os.environ.get('OPENAI_API_KEY')
    if key: return key
    env=ROOT.parent/'.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith('OPENAI_API_KEY='): return line.split('=',1)[1].strip().strip('\"\'')
    raise SystemExit('OPENAI_API_KEY unavailable; no calls made')


def run(args):
    manifest=json.loads((args.data/'tasks.json').read_text())
    tasks=[t for t in manifest['tasks'] if not args.ids or t['id'] in args.ids.split(',')]
    if not tasks: raise SystemExit('No matching tasks')
    key=api_key()
    system=manifest.get('system',SYSTEM)
    args.output.mkdir(parents=True,exist_ok=True)
    protocol=dict(version=VERSION,model=args.model,endpoint=ENDPOINT,effort=args.effort,cap=args.cap,
                  samples=args.samples,manifest_sha256=digest(manifest),system_sha256=digest(system),
                  task_ids=[t['id'] for t in tasks],tools=[],store=False)
    pp=args.output/'protocol.json'
    if pp.exists() and json.loads(pp.read_text())!=protocol: raise SystemExit('Protocol mismatch; use a fresh output directory')
    write_json(pp,protocol)
    def one(task,rep):
        folder=args.output/task['id']/f'sample-{rep}'
        # Never silently rebill an attempted sample, including ambiguous timeouts.
        if (folder/'result.json').exists(): print('SKIP',task['id'],rep,flush=True); return
        folder.mkdir(parents=True,exist_ok=True)
        payload=dict(model=args.model,messages=[{'role':'system','content':system},{'role':'user','content':task['prompt']}],
                     reasoning_effort=args.effort,max_completion_tokens=args.cap,store=False)
        write_json(folder/'request.json',payload)
        record=dict(id=task['id'],sample=rep,status='started',started_utc=datetime.now(timezone.utc).isoformat())
        write_json(folder/'result.json',record)
        started=time.perf_counter(); print('START',task['id'],rep,flush=True)
        req=urllib.request.Request(ENDPOINT,data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=900) as response: raw=json.load(response)
            write_json(folder/'response.json',raw)
            choice=raw['choices'][0]; content=choice['message'].get('content') or ''
            (folder/'response.txt').write_text(content)
            record.update(status='completed',model=raw.get('model'),response_id=raw.get('id'),
                          usage=raw.get('usage'),finish_reason=choice.get('finish_reason'),refusal=choice['message'].get('refusal'))
            try: (folder/'output.svg').write_text(read_response(content)['svg'])
            except (ValueError,KeyError,TypeError): pass
        except urllib.error.HTTPError as exc:
            body=exc.read().decode(errors='replace').replace(key,'[REDACTED]')
            record.update(status='api_error',http_status=exc.code,error=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',body)[:1000])
        except Exception as exc:
            record.update(status='client_error',error_type=type(exc).__name__,error=str(exc).replace(key,'[REDACTED]')[:500])
        record['wall_seconds']=time.perf_counter()-started
        write_json(folder/'result.json',record)
        print('END',task['id'],rep,record['status'],record.get('finish_reason'),flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda pair:one(*pair),[(t,i) for t in tasks for i in range(args.samples)]))
    score_run(args.data,args.output)


def score_run(data,out):
    manifest=json.loads((data/'tasks.json').read_text()); protocol=json.loads((out/'protocol.json').read_text())
    if digest(manifest)!=protocol['manifest_sha256']: raise ValueError('Manifest changed since run')
    rows=[]; usage={'prompt_tokens':0,'completion_tokens':0,'total_tokens':0}
    for task in manifest['tasks']:
        if task['id'] not in protocol['task_ids']: continue
        for i in range(protocol['samples']):
            folder=out/task['id']/f'sample-{i}'
            rec=json.loads((folder/'result.json').read_text()) if (folder/'result.json').exists() else {'status':'missing'}
            row=dict(id=task['id'],sample=i,status=rec['status'],effort=protocol['effort'],finish_reason=rec.get('finish_reason'),folder=str(folder.resolve().relative_to(ROOT)) if folder.resolve().is_relative_to(ROOT) else str(folder.resolve()))
            for k in usage: usage[k]+=(rec.get('usage') or {}).get(k,0)
            if rec['status']!='completed': row['outcome']='operational_error'
            elif rec.get('finish_reason')!='stop': row['outcome']='budget_or_incomplete'
            else: row.update(score(task,(folder/'response.txt').read_text()))
            rows.append(row)
    summary=dict(version=VERSION,scope=manifest['scope'],rows=rows,usage=usage,
                 counts={o:sum(r['outcome']==o for r in rows) for o in ('pass','failure','unscored_format','budget_or_incomplete','operational_error')})
    write_json(out/'summary.json',summary)
    print(json.dumps({'counts':summary['counts'],'usage':usage}),flush=True)
    return summary


def select(data,runs,output,review_path=None):
    manifest=json.loads((data/'tasks.json').read_text())
    rows=[]
    if len({r.resolve() for r in runs}) != len(runs): raise ValueError('duplicate run directory')
    for run_dir in runs:
        protocol=json.loads((run_dir/'protocol.json').read_text())
        if protocol['model'] != 'gpt-6-astra': raise ValueError('selection requires the specified Astra model')
        rows.extend(score_run(data,run_dir)['rows'])
    # Reviewer identity and evidence are explicit, never inferred from automated metrics.
    reviews=json.loads(review_path.read_text()) if review_path else {}
    policy=json.loads((data/'selection_policy.json').read_text()) if (data/'selection_policy.json').exists() else {'rule':manifest['criteria']['selection']}
    selected=[]; candidates=[]; controls=[]
    for task in manifest['tasks']:
        rs=[r for r in rows if r['id']==task['id']]
        eligible=[r for r in rs if r['outcome'] in ('pass','failure')]
        failures=[r for r in eligible if r['outcome']=='failure']
        shape_failures=[r for r in failures if r.get('geometry_errors') or r.get('dimension_errors')]
        physical_failures=[r for r in failures if r.get('analysis_errors') or r.get('visible_result_errors')]
        tracks=[]
        for name,fs in [('drawing',shape_failures),('physical_analysis',physical_failures)]:
            if len(eligible)>=3 and len(fs)>=2 and sum(r['effort']=='high' for r in eligible)>=2 and any(r['effort']=='high' for r in fs): tracks.append(name)
        entry=dict(id=task['id'],family=task['family'],mode=task['mode'],eligible_samples=len(eligible),
                   failures=len(failures),drawing_failures=len(shape_failures),physical_failures=len(physical_failures),tracks=tracks,
                   evidence=[r['folder'] for r in rs],review=reviews.get(task['id']))
        if (tracks and entry['review'] and entry['review'].get('confirmed') is True
                and entry['review'].get('reviewer_type') in ('human','assistant')
                and entry['review'].get('rationale') and entry['review'].get('checked_samples')):
            selected.append(entry)
        elif failures: candidates.append(entry)
        else: controls.append(entry)
    result=dict(version=VERSION,selection_rule=policy['rule'],selection_policy=policy,
                caveat='Astra-conditioned challenge set; cannot estimate general CAD success rates. Failures are conditional on the saved prompt/budget and unaided model. Physical-only failures do not establish inability to draw the shape.',
                selected=selected,candidates=candidates,excluded_or_controls=controls)
    write_json(output,result)
    # Explicit task manifest contains ONLY confirmed failed tasks, never controls/candidates.
    ids={s['id'] for s in selected}
    write_json(output.with_name('selected_tasks.json'),dict(version=VERSION,selection=result,tasks=[t for t in manifest['tasks'] if t['id'] in ids]))
    for track in ('drawing','physical_analysis'):
        track_ids={entry['id'] for entry in selected if track in entry['tracks']}
        write_json(output.with_name(f'selected_{track}_tasks.json'),dict(version=VERSION,track=track,tasks=[t for t in manifest['tasks'] if t['id'] in track_ids]))
    print('Selected',len(selected),'candidates',len(candidates),'controls/unresolved',len(controls),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['build','run','score','select'])
    p.add_argument('--data',type=Path,default=DATA)
    p.add_argument('--output',type=Path)
    p.add_argument('--model',default='gpt-6-astra')
    p.add_argument('--effort',choices=['low','medium','high'],default='medium')
    p.add_argument('--cap',type=int,default=16000)
    p.add_argument('--samples',type=int,default=1)
    p.add_argument('--workers',type=int,default=3)
    p.add_argument('--ids')
    p.add_argument('--runs',type=Path,nargs='+')
    p.add_argument('--review',type=Path)
    args=p.parse_args()
    if args.command=='build': build(args.data)
    elif not args.output: p.error('--output required')
    elif args.command=='run': run(args)
    elif args.command=='score': score_run(args.data,args.output)
    elif not args.runs: p.error('--runs required')
    else: select(args.data,args.runs,args.output,args.review)

if __name__=='__main__': main()
