#!/usr/bin/env python3
"""Re-score SVG field contours; writes v2 results without overwriting old scores."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from svgpatchlab.eval.field_fidelity import (VERSION, extract_contours,
    interpolate_grid, sample_segments, score_svg)
from svgpathtools import parse_path

MAPPINGS = {
    "laplace_L_shape": (800, 100, -800, 900),
    "torsion_square_prandtl": (800, 100, -800, 900),
    "square_hole_plate": (800, 100, -800, 900),
    "channel_step_streamlines": (300, 50, -300, 700),
    "square_conductor_in_shell": (400, 500, -400, 500),
    "plate_convective_edges": (400, 100, -400, 700),
}


def sample_path(d, per_segment=8):
    points, _ = sample_segments(parse_path(d), np.eye(3), 1., min_intervals=per_segment)
    return [tuple(p) for p in points]


def contours_in_svg(svg):
    contours, issues = extract_contours(svg, np.eye(3), 1.)
    if issues or any(c.issues for c in contours):
        raise ValueError(f"SVG requires unsupported features: {issues}")
    for c in contours:
        yield c.level, [tuple(p) for p in c.points]


def interp(x, y, field, px, py):
    return float(interpolate_grid(x,y,field,[[px,py]])[0])


def overlay(svg, iso, mapping, target):
    ax,bx,ay,by = mapping
    paths = []
    for segs in iso.values():
        for x0,y0,x1,y1 in segs:
            paths.append(f'<path d="M{ax*x0+bx:.4f},{ay*y0+by:.4f} L{ax*x1+bx:.4f},{ay*y1+by:.4f}"/>')
    group = '<g stroke="#d00" stroke-width="2" stroke-dasharray="6 4" fill="none">'+''.join(paths)+'</g>'
    target.write_text(svg.replace('</svg>',group+'</svg>'))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run-dir',required=True)
    ap.add_argument('--reference-dir',default='runs/reference-v3')
    ap.add_argument('--prompts',default='configs/prompts/engineering_v3_fields.json')
    ap.add_argument('--output-dir')
    ap.add_argument('--render',action='store_true')
    args=ap.parse_args()
    run,ref=Path(args.run_dir),Path(args.reference_dir)
    out=Path(args.output_dir) if args.output_dir else run/'rescore-v2'
    out.mkdir(parents=True,exist_ok=True)
    cases={r['id']:r for r in json.loads(Path(args.prompts).read_text())['cases']}
    report=[]
    for line in (run/'results.jsonl').read_text().splitlines():
        r=json.loads(line); ident=r['id']
        base={'id':ident,'sample':r.get('sample',0),'finish_reason':r.get('finish_reason'),
              'source_sha256':hashlib.sha256((r.get('svg') or '').encode()).hexdigest()}
        if ident not in MAPPINGS:
            scored={'geometry_pass':False,'issues':['no_reference_mapping']}
        else:
            z=np.load(ref/f'{ident}.npz')
            scored=score_svg(r.get('svg') or '',z['x'],z['y'],z['field'],
                             MAPPINGS[ident],cases[ident]['levels'],field_range=100.)
        report.append(dict(base,**scored))
        print(ident,'mean_pp=',scored.get('mean_error_pp'),'max_pp=',scored.get('max_error_pp'),
              'invalid=',scored.get('invalid_points'),'geometry_pass=',scored['geometry_pass'])
        if args.render and r.get('svg') and ident in MAPPINGS:
            import cairosvg
            target=out/f'{ident}-{base["sample"]}.overlay.svg'
            overlay(r['svg'],json.loads((ref/f'{ident}.isolines.json').read_text()),MAPPINGS[ident],target)
            cairosvg.svg2png(url=str(target),write_to=str(target.with_suffix('.png')))
    (out/'results.jsonl').write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in report))
    summary={'version':VERSION,'attempted':len(report),'geometry_pass':sum(r['geometry_pass'] for r in report),
             'source_results_sha256':hashlib.sha256((run/'results.jsonl').read_bytes()).hexdigest(),
             'note':'Numerical geometry audit only; not a complete visual or semantic certificate.',
             'cases':report}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))
    print('Saved',out/'summary.json')


if __name__=='__main__':
    main()
