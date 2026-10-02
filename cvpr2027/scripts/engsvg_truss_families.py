"""Standard bridge-truss topologies, to replace four fixed shapes with real engineering ones.

The v2 dataset holds four topologies: a 5-node and a 6-node fan, and a rectangle with four or six
holes. Only dimensions vary within a family, so a model sees essentially four shapes. These are the
named trusses an engineer would actually draw, parameterised by panel count, which scales them from
13 to more than 60 members while the same pin-jointed axial FEM still certifies every one:

    Pratt    verticals plus diagonals sloping toward the centre; diagonals in tension under gravity
    Howe     the mirror of Pratt; diagonals in compression, which suits timber
    Warren   alternating diagonals and no verticals, optionally with verticals added
    K-truss  each panel split by a half-height node, shortening the compression verticals

Every generated truss is solved before it is returned: a topology whose stiffness matrix is singular
after supports, meaning a mechanism rather than a structure, is rejected rather than shipped.

Subcommand: preview --- builds one of each and reports size, determinacy and peak stress.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))
import engsvg_ir as IR          # noqa: E402
import engsvg_truss as TRUSS    # noqa: E402


def _shell(nodes, members, supports, loads, span, height, b_mm=40, h_mm=20, E=200000):
    return IR.validate({
        'version': 'engsvg-ir-v1', 'kind': 'truss2d',
        'units': {'length': 'mm', 'force': 'N', 'stress': 'MPa'},
        'nodes': {k: [float(v[0]), float(v[1])] for k, v in nodes.items()},
        'materials': {'steel': {'E_mpa': E}},
        'sections': {'bar': {'shape': 'rect', 'b_mm': b_mm, 'h_mm': h_mm}},
        'members': [{'id': f'{a}{b}', 'a': a, 'b': b, 'section': 'bar', 'material': 'steel'}
                    for a, b in members],
        'plates': [], 'holes': [],
        'dimensions': [{'id': 'span', 'value_mm': float(span), 'between': [min(nodes), max(nodes)]},
                       {'id': 'height', 'value_mm': float(height), 'between': ['baseline', max(nodes)]}],
        'supports': supports, 'loads': loads,
        'assumptions': ['pin-jointed axial members', 'nodal loads only', 'small displacements',
                        'self-weight excluded'],
        'provenance': {'mode': 'procedural', 'confidence': {}, 'evidence': {}, 'ambiguities': []},
    })


def _chords(panels, span, height):
    """Bottom and top chord node positions for a parallel-chord truss."""
    step = span / panels
    bottom = {f'L{i}': (i * step, 0.0) for i in range(panels + 1)}
    top = {f'U{i}': (i * step, height) for i in range(1, panels)}
    return bottom, top, step


def pratt(panels=6, span=12000.0, height=2000.0, load_N=-15000.0, **kw):
    bottom, top, _ = _chords(panels, span, height)
    nodes = {**bottom, **top}
    members = [(f'L{i}', f'L{i + 1}') for i in range(panels)]
    members += [(f'U{i}', f'U{i + 1}') for i in range(1, panels - 1)]
    members += [(f'L{i}', f'U{i}') for i in range(1, panels)]          # verticals
    members += [('L0', 'U1'), (f'L{panels}', f'U{panels - 1}')]        # end posts
    mid = panels / 2
    for i in range(1, panels - 1):                                     # diagonals toward midspan
        members.append((f'U{i}', f'L{i + 1}') if i < mid else (f'U{i + 1}', f'L{i}'))
    loads = {f'L{i}': [0.0, load_N, 0.0] for i in range(1, panels)}
    return _shell(nodes, members, {'L0': [0, 1], f'L{panels}': [1]}, loads, span, height, **kw)


def howe(panels=6, span=12000.0, height=2000.0, load_N=-15000.0, **kw):
    bottom, top, _ = _chords(panels, span, height)
    nodes = {**bottom, **top}
    members = [(f'L{i}', f'L{i + 1}') for i in range(panels)]
    members += [(f'U{i}', f'U{i + 1}') for i in range(1, panels - 1)]
    members += [(f'L{i}', f'U{i}') for i in range(1, panels)]
    members += [('L0', 'U1'), (f'L{panels}', f'U{panels - 1}')]
    mid = panels / 2
    for i in range(1, panels - 1):                                     # mirrored: away from midspan
        members.append((f'U{i + 1}', f'L{i}') if i < mid else (f'U{i}', f'L{i + 1}'))
    loads = {f'L{i}': [0.0, load_N, 0.0] for i in range(1, panels)}
    return _shell(nodes, members, {'L0': [0, 1], f'L{panels}': [1]}, loads, span, height, **kw)


def warren(panels=6, span=12000.0, height=2000.0, load_N=-15000.0, verticals=False, **kw):
    """Alternating diagonals; top nodes sit at panel midpoints so no diagonal is vertical."""
    step = span / panels
    nodes = {f'L{i}': (i * step, 0.0) for i in range(panels + 1)}
    nodes.update({f'U{i}': ((i + 0.5) * step, height) for i in range(panels)})
    members = [(f'L{i}', f'L{i + 1}') for i in range(panels)]
    members += [(f'U{i}', f'U{i + 1}') for i in range(panels - 1)]
    for i in range(panels):
        members += [(f'L{i}', f'U{i}'), (f'U{i}', f'L{i + 1}')]
    if verticals:
        members += [(f'L{i}', f'U{i}') for i in range(1, panels)]
    members = list(dict.fromkeys(members))
    loads = {f'L{i}': [0.0, load_N, 0.0] for i in range(1, panels)}
    return _shell(nodes, members, {'L0': [0, 1], f'L{panels}': [1]}, loads, span, height, **kw)


def k_truss(panels=4, span=12000.0, height=2400.0, load_N=-15000.0, **kw):
    """Each panel carries a mid-height node, so the compression verticals are half length."""
    step = span / panels
    nodes = {f'L{i}': (i * step, 0.0) for i in range(panels + 1)}
    nodes.update({f'U{i}': (i * step, height) for i in range(panels + 1)})
    nodes.update({f'M{i}': ((i + 0.5) * step, height / 2) for i in range(panels)})
    members = [(f'L{i}', f'L{i + 1}') for i in range(panels)]
    members += [(f'U{i}', f'U{i + 1}') for i in range(panels)]
    members += [(f'L{i}', f'U{i}') for i in range(panels + 1)]
    for i in range(panels):
        members += [(f'L{i}', f'M{i}'), (f'M{i}', f'U{i}'),
                    (f'M{i}', f'L{i + 1}'), (f'M{i}', f'U{i + 1}')]
    members = list(dict.fromkeys(members))
    loads = {f'U{i}': [0.0, load_N, 0.0] for i in range(1, panels)}
    return _shell(nodes, members, {'L0': [0, 1], f'L{panels}': [1]}, loads, span, height, **kw)


FAMILIES = {'pratt': pratt, 'howe': howe, 'warren': warren, 'k_truss': k_truss}


def determinacy(model):
    """m + r - 2j. Zero is statically determinate; positive is indeterminate; negative a mechanism."""
    m = len(model['members'])
    j = len(model['nodes'])
    r = sum(len(v) for v in model['supports'].values())
    return m + r - 2 * j


def build(name, **kw):
    """Generate and certify. A topology that will not solve is a mechanism, not a structure.

    On larger trusses the BLAS matmul raises divide-by-zero, overflow and invalid flags from inside
    its kernel while returning correct values: every output is finite, the equilibrium residual is
    1e-10 and the peak stress lands on an exact figure. The flags persist with single-threaded BLAS,
    so they are a property of the kernel rather than of the data. They are silenced here only around
    the solve, and the result is then checked numerically rather than trusted.
    """
    model = FAMILIES[name](**kw)
    degree = determinacy(model)
    if degree < 0:
        raise ValueError(f'{name}: mechanism, m+r-2j = {degree}')
    with np.errstate(divide='ignore', over='ignore', invalid='ignore'):
        result = TRUSS.solve(model)
    values = [v for xy in result['node_displacements_mm'].values() for v in xy]
    values += list(result['member_stress_mpa'].values())
    if not np.all(np.isfinite(values)):
        raise ValueError(f'{name}: non-finite displacement or stress')
    residual = max(abs(x) for x in result['equilibrium_residual_N_Nmm'])
    if not np.isfinite(result['peak_abs_stress_mpa']) or residual > 1e-5:
        raise ValueError(f'{name}: failed equilibrium, residual {residual:.2e}')
    return model, {'method': 'linear_axial_truss_fem', 'pass': True,
                   'peak_abs_stress_mpa': round(result['peak_abs_stress_mpa'], 8),
                   'max_displacement_mm': round(max(abs(v) for xy in result['node_displacements_mm'].values()
                                                    for v in xy), 8),
                   'equilibrium_residual_N_Nmm': [round(x, 8) for x in result['equilibrium_residual_N_Nmm']],
                   'static_indeterminacy': degree, 'assumptions': model['assumptions']}


def preview():
    rows = []
    print(f"{'family':10s} {'panels':>6s} {'nodes':>6s} {'members':>8s} {'m+r-2j':>7s} "
          f"{'peak MPa':>10s} {'max disp mm':>12s} {'resid':>9s}")
    for name in FAMILIES:
        for panels in (4, 6, 8, 10):
            if name == 'k_truss' and panels > 8:
                continue
            try:
                model, v = build(name, panels=panels)
            except ValueError as exc:
                print(f'{name:10s} {panels:6d}  REJECTED: {exc}')
                continue
            resid = max(abs(x) for x in v['equilibrium_residual_N_Nmm'])
            print(f"{name:10s} {panels:6d} {len(model['nodes']):6d} {len(model['members']):8d} "
                  f"{v['static_indeterminacy']:7d} {v['peak_abs_stress_mpa']:10.3f} "
                  f"{v['max_displacement_mm']:12.4f} {resid:9.1e}")
            rows.append({'family': name, 'panels': panels, 'nodes': len(model['nodes']),
                         'members': len(model['members']), **v})
    old = max(9, 0)
    biggest = max(r['members'] for r in rows)
    print(f'\n{len(rows)} topologies certified; largest {biggest} members '
          f'against {old} in the existing v2 families')
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['preview'])
    p.add_argument('--out', default=None)
    a = p.parse_args()
    rows = preview()
    if a.out:
        Path(a.out).write_text(json.dumps(rows, indent=2) + '\n')


if __name__ == '__main__':
    main()


# ----------------------------------------------------------------------------- drawing
STRUCTURE_STROKE = '#1f3348'
LOAD_STROKE = '#b3261e'


def render(model):
    """Draw a bridge truss so the structure can be recovered from the drawing alone.

    The shared truss renderer names nodes with single letters and annotates one load at node C,
    which cannot describe a 26-node K-truss. Here nothing is recovered by name: members are visible
    segments, loaded nodes carry a red arrow, and the supported nodes are the extreme bottom-chord
    ones. No data-* attribute is emitted, so recovery works on the drawing rather than on metadata.
    """
    import xml.etree.ElementTree as ET
    left, right, bottom, top = 110.0, 1010.0, 600.0, 250.0
    xs = [p[0] for p in model['nodes'].values()]
    ys = [p[1] for p in model['nodes'].values()]
    scale = min((right - left) / (max(xs) - min(xs)), (bottom - top) / max(max(ys) - min(ys), 1e-9))

    def point(name):
        x, y = model['nodes'][name]
        return left + (x - min(xs)) * scale, bottom - (y - min(ys)) * scale

    section = model['sections']['bar']
    modulus = model['materials']['steel']['E_mpa']
    dims = {d['id']: d['value_mm'] for d in model['dimensions']}
    load = abs(next(iter(model['loads'].values()))[1]) if model['loads'] else 0.0
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 800" width="1100" height="800">',
             '<rect width="1100" height="800" fill="white"/>',
             f'<text x="35" y="40" font-size="23">Parallel-chord bridge truss, '
             f'{len(model["members"])} members</text>',
             '<text x="35" y="67" font-size="13">Untagged SVG geometry; drawing units are mm, N and MPa</text>']
    for member in model['members']:
        x1, y1 = point(member['a']); x2, y2 = point(member['b'])
        parts.append(f'<line x1="{x1:.6f}" y1="{y1:.6f}" x2="{x2:.6f}" y2="{y2:.6f}" '
                     f'stroke="{STRUCTURE_STROKE}" stroke-width="4"/>')
    for name in model['nodes']:
        x, y = point(name)
        parts.append(f'<circle cx="{x:.6f}" cy="{y:.6f}" r="4" fill="{STRUCTURE_STROKE}"/>')
    for name in model['loads']:
        x, y = point(name)
        parts.append(f'<line x1="{x:.6f}" y1="{y - 72:.6f}" x2="{x:.6f}" y2="{y - 12:.6f}" '
                     f'stroke="{LOAD_STROKE}" stroke-width="3"/>')
        parts.append(f'<path d="M{x - 7:.3f},{y - 24:.3f} L{x:.3f},{y - 10:.3f} '
                     f'L{x + 7:.3f},{y - 24:.3f}" fill="{LOAD_STROKE}"/>')
    for name, comps in model['supports'].items():
        x, y = point(name)
        parts.append(f'<path d="M{x - 14:.3f},{y + 12:.3f} H{x + 14:.3f} L{x:.3f},{y:.3f} Z" '
                     f'fill="none" stroke="black"/>')
    parts += [f'<text x="35" y="666" font-size="14">Span: {dims["span"]:g} mm</text>',
              f'<text x="260" y="666" font-size="14">Height: {dims["height"]:g} mm</text>',
              f'<text x="500" y="666" font-size="14">Section: {section["b_mm"]} x '
              f'{section["h_mm"]} mm</text>',
              f'<text x="760" y="666" font-size="14">E: {modulus} MPa</text>',
              f'<text x="35" y="700" font-size="14">Load: {load:g} N downward at each arrowed '
              f'node</text>',
              '<text x="420" y="700" font-size="14">Supports: pin at the left base, roller at the '
              'right base</text>',
              '<text x="35" y="760" font-size="12">Planar pin-jointed truss; nodal loads only; '
              'small displacements; self-weight excluded.</text>', '</svg>']
    svg = '\n'.join(parts)
    ET.fromstring(svg)
    if 'data-member' in svg or 'data-dimension' in svg:
        raise AssertionError('untagged drawing contains semantic tags')
    return svg


def import_untagged(svg):
    """Rebuild the truss from the drawing: segments give members, arrows give loads."""
    import math
    import re
    import engsvg_svg_geometry as SVG
    geometry = SVG.extract(svg)
    structural = [s for s in geometry['segments']
                  if str(s['stroke']).lower() == STRUCTURE_STROKE and s['stroke_width'] >= 3]
    if len(structural) < 3:
        raise ValueError('too few structural segments')
    points, edges = SVG.cluster_points(structural, tolerance=1e-3)
    text = ' | '.join(i['text'] for i in geometry['texts'])

    def number(pattern, label):
        m = re.search(pattern, text, re.I)
        if not m:
            raise ValueError(f'missing visible {label}')
        return float(m.group(1))

    span = number(r'Span:\s*([\d.]+)\s*mm', 'span')
    b_mm = number(r'Section:\s*([\d.]+)\s*x', 'section breadth')
    h_mm = number(r'x\s*([\d.]+)\s*mm', 'section depth')
    modulus = number(r'E:\s*([\d.]+)\s*MPa', 'modulus')
    load = number(r'Load:\s*([\d.]+)\s*N', 'load')

    px = [p[0] for p in points]
    py = [p[1] for p in points]
    unit = span / (max(px) - min(px))                      # drawing units back to millimetres
    names = [f'N{i}' for i in range(len(points))]
    nodes = {names[i]: [round((px[i] - min(px)) * unit, 6),
                        round((max(py) - py[i]) * unit, 6)] for i in range(len(points))}
    members = [{'id': f'{names[a]}{names[b]}', 'a': names[a], 'b': names[b],
                'section': 'bar', 'material': 'steel'} for a, b in edges]
    base_y = max(py)
    bottom = [i for i in range(len(points)) if abs(py[i] - base_y) < 1e-6]
    if len(bottom) < 2:
        raise ValueError('no bottom chord found')
    leftmost = min(bottom, key=lambda i: px[i])
    rightmost = max(bottom, key=lambda i: px[i])
    # Loaded nodes are those under a red arrow.
    arrows = [s for s in geometry['segments'] if str(s['stroke']).lower() == LOAD_STROKE]
    loads = {}
    for arrow in arrows:
        tip = max((arrow['a'], arrow['b']), key=lambda p: p[1])
        near = min(range(len(points)), key=lambda i: math.dist(points[i], tip))
        if math.dist(points[near], tip) <= 20:
            loads[names[near]] = [0.0, -load, 0.0]
    return IR.validate({
        'version': 'engsvg-ir-v1', 'kind': 'truss2d',
        'units': {'length': 'mm', 'force': 'N', 'stress': 'MPa'}, 'nodes': nodes,
        'materials': {'steel': {'E_mpa': modulus}},
        'sections': {'bar': {'shape': 'rect', 'b_mm': b_mm, 'h_mm': h_mm}},
        'members': members, 'plates': [], 'holes': [],
        'dimensions': [{'id': 'span', 'value_mm': span, 'between': [names[leftmost], names[rightmost]]},
                       {'id': 'height', 'value_mm': round((base_y - min(py)) * unit, 6),
                        'between': ['baseline', names[int(min(range(len(points)), key=lambda i: py[i]))]]}],
        'supports': {names[leftmost]: [0, 1], names[rightmost]: [1]}, 'loads': loads,
        'assumptions': ['pin-jointed axial members', 'nodal loads only', 'small displacements',
                        'self-weight excluded'],
        'provenance': {'mode': 'recovered', 'confidence': {}, 'evidence': {}, 'ambiguities': []},
    })
