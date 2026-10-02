"""Offline readback/re-analysis of saved functional design trials; no API calls."""
import copy,hashlib,json
from pathlib import Path
import numpy as np
import cad_functional_sizing as s

def main():
    root=s.ROOT/'runs/astra-functional-sizing-20260921';tasks={};manifests={}
    for name in ('cad-functional-sizing','cad-functional-braced','cad-functional-three-bay'):
        p=s.ROOT/'data'/name/'tasks.json';manifest=json.loads(p.read_text());manifests[name]=hashlib.sha256(p.read_bytes()).hexdigest()
        tasks.update({t['id']:t for t in manifest['tasks']})
    records=[]
    for p in sorted(root.glob('*/*/result.json')):
        rec=json.loads(p.read_text());t=tasks[rec['id']]
        if rec['status']!='completed':records.append({'id':rec['id'],'status':rec['status'],'hard_eligible':False});continue
        svg=(p.parent/'output.svg').read_text();design=s.read_drawing(t,svg);grade=s.rows(t,[design])[0]
        m=copy.deepcopy(t['model'])
        for v,i in zip(m['members'],design):v['h_mm']=t['catalog_h_mm'][i]
        checks=[]
        for loads in t['load_cases']:
            m['loads']=loads
            for node in m['nodes']:
                m['probe']=node;checks.append(s.fem.solve(m,subdivisions=2))
        errors={k:abs(grade[k]-max(abs(r[source]) for r in checks)) for k,source in [('ux_mm','ux_mm'),('uy_mm','uy_mm'),('stress_mpa','peak_stress_mpa')]}
        assert max(errors.values())<1e-6
        assert design==rec['grade']['design'] and grade['all_constraints_pass']==rec['grade']['all_constraints_pass']
        request=json.loads((p.parent/'request-0.json').read_text());public=json.loads(request['input'][1]['content']);assert 'oracle' not in public
        protocol=json.loads((p.parent.parent/'protocol.json').read_text())
        assert protocol['task_sha256'] in manifests.values()
        tool_errors=sum('interface_error' in json.loads(q.read_text()) for q in p.parent.glob('tool-*.json'))
        presentation=s.drawing(t,design);assert s.read_drawing(t,presentation)==design;(p.parent/'presentation.svg').write_text(presentation)
        records.append({'id':rec['id'],'status':'completed','pass':grade['all_constraints_pass'],'grade':grade,'scalar_subdivision_max_errors':errors,'interface_errors':tool_errors,'design_evaluations':rec['design_evaluations'],'api_turns':len(rec['usage']),'reported_tokens':sum(u.get('total_tokens',0) for u in rec['usage']),'relative_trial':str(p.parent.relative_to(s.ROOT)),'svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'hard_eligible':False,'exclusion':'Completed functional pass; no hard-case confirmation needed.'})
    result={'audit_date':'2026-09-22','scope':'Idealized catalog section synthesis with deterministic SVG export; not free-form SVG generation or vision evaluation.','task_manifests_sha256':manifests,'records':records,'completed':len(records),'passes':sum(r.get('pass',False) for r in records),'api_turns':sum(r.get('api_turns',0) for r in records),'reported_tokens':sum(r.get('reported_tokens',0) for r in records),'enumerated_reference_designs':sum(t['oracle']['enumerated'] for t in tasks.values()),'hard_selection':[],'training_started':False}
    s.write(root/'audited-summary.json',result);s.write(root/'hard-selection.json',{'selected':[],'reason':'All six completed designs passed. Retain as separate controls; none admitted to the requested failure-only set.'})
    print(json.dumps({k:result[k] for k in ('completed','passes','api_turns','reported_tokens','enumerated_reference_designs')}))

if __name__=='__main__':main()
