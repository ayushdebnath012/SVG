"""Manufactured contour-corruption controls; not model-performance estimates."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import random
import xml.etree.ElementTree as ET

import numpy as np
from svgpathtools import parse_path
from svgpatchlab.core.xml import parse_svg,protected_geometry
from svgpatchlab.eval.field_fidelity import score_svg


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='runs/cvpr2027/contour-controls');a=p.parse_args()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True);rng=random.Random(2027)
    x=y=np.linspace(-2,2,401);xx,yy=np.meshgrid(x,y);field=xx**2+yy**2
    rows=[]
    for case in range(20):
        r=rng.uniform(.6,1.2);level=r*r
        source=f'<svg xmlns="http://www.w3.org/2000/svg"><g><path id="c" data-level="{level}" d="M {r} 0 A {r} {r} 0 0 1 0 {r}" stroke="#2563eb" fill="none"/></g><text>{level:g} units</text></svg>'
        root=parse_svg(source)
        for kind in ('unchanged','restyle','chord','ancestor_transform','wrong_level','hidden','missing','wrong_label'):
            trial=copy.deepcopy(root);curve=list(trial.iter())[2]
            if kind=='restyle':curve.set('stroke','#dc2626')
            if kind=='chord':curve.set('d',f'M {r} 0 L 0 {r}')
            if kind=='ancestor_transform':trial[0].set('transform','translate(0.25,0)')
            if kind=='wrong_level':curve.set('data-level',str(level+.2))
            if kind=='hidden':trial[0].set('opacity','0')
            if kind=='missing':trial[0].remove(curve)
            if kind=='wrong_label':trial[1].text='999 units'
            svg=ET.tostring(trial,encoding='unicode')
            audit=score_svg(svg,x,y,field,expected_levels=[level],field_range=8,tolerance_pp=.5)
            # Explicitly weak endpoint/local-coordinate baseline. Not represented
            # as an exact reproduction of the former historical evaluator.
            eps=[]
            for e in trial.iter():
                if 'data-level' in e.attrib:
                    for seg in parse_path(e.get('d','')):
                        eps.extend(abs(abs(z)**2-float(e.get('data-level'))) for z in (seg.start,seg.end))
            endpoint_pass=bool(eps) and max(eps)/8*100<=.5
            hash_pass=protected_geometry(root)==protected_geometry(trial)
            # A deliberately rigid freeze baseline; no claims about useful editing
            # beyond the one supported color change.
            frozen=copy.deepcopy(trial)
            for e in frozen.iter():
                if e.get('id')=='c':e.set('stroke','#2563eb')
            freeze_pass=ET.tostring(frozen)==ET.tostring(root)
            rows.append({'case':case,'variant':kind,'honest':kind in ('unchanged','restyle'),
                         'endpoint_pass':endpoint_pass,'path_hash_pass':hash_pass,
                         'numeric_pass':audit['geometry_pass'],'freeze_pass':freeze_pass,
                         'max_error_pp':audit['max_error_pp'],'issues':audit['issues']})
    summary={'scope':'20 manufactured quadratic fields, 8 variants each; simple controls, no learned-model results',
             'n':len(rows),'methods':{}}
    for method in ('endpoint_pass','path_hash_pass','numeric_pass','freeze_pass'):
        good=[r for r in rows if r['honest']];bad=[r for r in rows if not r['honest']]
        summary['methods'][method]={'honest_acceptance':sum(r[method] for r in good)/len(good),
                                    'corrupt_acceptance':sum(r[method] for r in bad)/len(bad),
                                    'accepted_corrupt_variants':sorted({r['variant'] for r in bad if r[method]})}
    (out/'results.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
