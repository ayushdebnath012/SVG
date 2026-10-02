"""Transparent SVG-only baseline for the horizontal panel fixture grammar.

Reads visible numeric dimension text and line endpoints, builds linear
constraints, solves them, then moves attached geometry in original local frames.
No access to task mode, source generator or target SVG inside edit(). This is
deliberately domain-specific, not a learned/general drawing interpreter.
"""
import json,sys
from pathlib import Path
import numpy as np
from cad_intent_probe import inspect,apply,score,DATA,ROOT,write

def edit(svg,new_width):
    inv=inspect(svg);rects=[v for v in inv.values() if v['tag']=='rect']
    top=max(rects,key=lambda v:v['points'][2][1]-v['points'][0][1])
    left=top['points'][0][0];right=top['points'][1][0]
    circles=[v for v in inv.values() if v['tag']=='circle'];old=np.array([left]+sorted(v['points'][0][0] for v in circles)+[right])
    dims=[]
    horizontal=[v for v in inv.values() if v['tag']=='line' and abs(v['points'][0][1]-v['points'][1][1])<1e-8]
    for eid,v in inv.items():
        if v['tag']!='text':continue
        text=v['text']
        try:value=float(text.strip('() '))
        except ValueError:continue
        x,y=v['points'][0]
        candidates=[h for h in horizontal if h['points'][0][1]>y and abs((h['points'][0][0]+h['points'][1][0])/2-x)<1e-5]
        h=min(candidates,key=lambda h:h['points'][0][1]-y)
        a,b=[int(np.argmin(abs(old-pt[0]))) for pt in h['points']]
        dims.append(dict(id=eid,a=a,b=b,value=value,reference=text.startswith('(')))
    overall=next(d for d in dims if d['a']==0 and d['b']==len(old)-1)
    units=(right-left)/overall['value'];A=[];b=[]
    row=np.zeros(len(old));row[0]=1;A.append(row);b.append(0)
    for d in dims:
        if d['reference']:continue
        row=np.zeros(len(old));row[d['b']]=1;row[d['a']]=-1;A.append(row);b.append(new_width if d is overall else d['value'])
    if any('equally spaced' in v.get('text','') for v in inv.values()):
        for i in range(1,len(old)-3):
            row=np.zeros(len(old));row[i]=1;row[i+1]=-2;row[i+2]=1;A.append(row);b.append(0)
    A=np.array(A);b=np.array(b);solution=np.linalg.lstsq(A,b,rcond=None)[0]
    if np.linalg.matrix_rank(A)<len(old) or np.max(abs(A@solution-b))>1e-7:raise ValueError('underdetermined/inconsistent supported constraints')
    new=left+units*solution;delta=new-old;patches=[];dim_by_id={d['id']:d for d in dims}
    # These fixtures use positive uniform nested scales. Infer each local scale
    # from the outer root/inner group mapping once using a rectangle edge.
    local_scale=(right-left)/float(top['attributes']['width'])
    for eid,v in inv.items():
        tag=v['tag'];a=v['attributes'];p={'id':eid,'set':{}}
        if tag=='rect':p['set']['width']=float(a['width'])+(new[-1]-old[-1])/local_scale
        elif tag=='circle':
            i=int(np.argmin(abs(old-v['points'][0][0])));p['set']['cx']=float(a['cx'])+delta[i]/local_scale
        elif tag=='line':
            for j,key in enumerate(['x1','x2']):
                i=int(np.argmin(abs(old-v['points'][j][0])));p['set'][key]=float(a[key])+delta[i]/local_scale
        elif eid in dim_by_id:
            d=dim_by_id[eid];p['set']['x']=float(a['x'])+(delta[d['a']]+delta[d['b']])/2/local_scale
            value=solution[d['b']]-solution[d['a']];p['text']=('('+f'{value:g}'+')') if d['reference'] else f'{value:g}'
        p['set']={k:v for k,v in p['set'].items() if abs(v-float(a[k]))>1e-9}
        if p['set'] or 'text' in p:patches.append(p)
    return {'patches':patches,'constraints':{'A':A.tolist(),'b':b.tolist(),'solution_mm':solution.tolist(),'residual':float(np.max(abs(A@solution-b)))}}

if __name__=='__main__':
    rows=[];out=ROOT/'runs/astra-cad-intent-20260921/rule-baseline'
    for t in json.loads((DATA/'tasks.json').read_text())['tasks']:
        answer=edit(t['svg'],234);d=out/t['id'];write(d/'answer.json',answer);(d/'output.svg').write_text(apply(t['svg'],answer['patches']))
        result=score(t,answer['patches']);rows.append(dict(id=t['id'],**result));print(t['id'],result['outcome'])
    write(out/'summary.json',{'rows':rows,'scope':'SVG-only hand-coded parser for one fixture grammar; not general CAD recovery'})
