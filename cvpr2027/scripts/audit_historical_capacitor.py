"""Source-specific geometry check of the saved v2 capacitor SVG, not a PDE solver.

Known colors identify field/equipotential paths in this particular artifact.
Excludes definitions, arrows and legend strokes. Does not infer far-field truth.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from svgpathtools.path import transform
from svgpatchlab.core.xml import parse_svg, local_name
from svgpatchlab.eval.field_fidelity import element_path, transform_matrix


def audit(source):
    root = parse_svg(source); fields = []; potentials = []
    def walk(el, matrix, stroke=''):
        if local_name(el.tag) in ('defs', 'marker'): return
        matrix = matrix @ transform_matrix(el.get('transform', ''))
        stroke = el.get('stroke', stroke)
        if local_name(el.tag) == 'path' and stroke in ('#157047', '#b84d33', '#3264ae'):
            path = transform(element_path(el), matrix)
            if path.length() > 50:
                (fields if stroke == '#157047' else potentials).append(path)
        for child in el: walk(child, matrix, stroke)
    walk(root, np.eye(3))
    endpoints = []
    for i, path in enumerate(fields):
        endpoints.append({'index': i, 'start': [path.start.real, path.start.imag],
                          'end': [path.end.real, path.end.imag], 'closed': path.isclosed(),
                          'joins_plates': (abs(path.start.imag-390) < 1e-6 and
                              abs(path.end.imag-510) < 1e-6 and
                              300 <= path.start.real <= 900 and 300 <= path.end.real <= 900)})
    intersections = []; errors = []
    for i, field in enumerate(fields):
        for j, potential in enumerate(potentials):
            try:
                for (T1, seg1, t1), (T2, seg2, t2) in field.intersect(potential):
                    a, b = seg1.derivative(t1), seg2.derivative(t2)
                    dot = abs((a.conjugate()*b).real)/(abs(a)*abs(b))
                    deviation = float(np.degrees(np.arcsin(np.clip(dot, 0, 1))))
                    point = seg1.point(t1)
                    intersections.append({'field': i, 'potential': j, 'x': point.real, 'y': point.imag,
                                          'deviation_from_orthogonal_deg': deviation})
            except Exception as exc:
                errors.append({'field': i, 'potential': j, 'error': type(exc).__name__})
    texts = [''.join(el.itertext()) for el in root.iter() if local_name(el.tag) == 'text']
    return {'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
            'field_paths': len(fields), 'potential_paths': len(potentials),
            'closed_field_paths': sum(e['closed'] for e in endpoints), 'endpoints': endpoints,
            'intersections': intersections, 'intersection_errors': errors,
            'max_orthogonality_deviation_deg': max((r['deviation_from_orthogonal_deg'] for r in intersections), default=None),
            'disclosure_text': [t for t in texts if 'schematic' in t.lower()],
            'limitations': ['Artifact-specific color and plate-coordinate selection.',
                            'Curve intersection tangents are geometric diagnostics, not a full PDE reference.',
                            'Open potential-path endpoints do not establish behavior at infinity.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--svg', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); args = p.parse_args()
    report = audit(args.svg.read_text()); args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('field_paths', 'closed_field_paths',
        'max_orthogonality_deviation_deg', 'disclosure_text', 'intersection_errors')}))
