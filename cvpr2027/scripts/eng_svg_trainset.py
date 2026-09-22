"""Training-set generator: procedurally sampled frames drawn in randomised styles.

The deterministic exporter in `cad_astra_benchmark.reference_svg` emits one rigid template --- the same
element order, two stroke colours, four font sizes and a title at x=35,y=40 whether the frame has 3
members or 18. Training on it unmodified teaches a model to reproduce that template rather than to
draft, and the benchmark would then reward memorised coordinates.

So every target here is drawn in a randomised style: stroke colours and widths, element type for a
member (line, polyline or path), dimension text side and wording, node markers, support symbols, the
section-schedule corner, the results block, background tint, element order, and an optional ancestor
translate group. None of that touches the engineering content, and the checks are content-based ---
member centrelines to 1 mm, joint closure, dimension values, and the analysis --- so every randomised
drawing still has to verify. That is enforced: a pair is written only after the real scorer passes it.

The 48 benchmark frames are excluded by model hash, and frames are grouped by geometry so that near
duplicates cannot straddle the splits.

No external corpus is involved. MakerBench-HWE, the one downloaded source once recorded as holding CAD
SVGs, carries an explicit do-not-train canary and in fact contains no engineering drawings at all; see
its corrected record in `data/cad_sources.json`.

Subcommands: build | verify.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
from pathlib import Path
import random
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
import cad_astra_benchmark as B      # noqa: E402
import eng_frame_bench as F          # noqa: E402
import eng_svg_bench as S            # noqa: E402

OUT = ROOT / 'data/eng-svg-trainset'
BENCHMARKS = ('data/eng-svg-bench-text/tasks.json', 'data/eng-svg-bench-edit/tasks.json',
              'data/eng-frame-bench/tasks.json', 'data/eng-frame-bench-xl/tasks.json',
              'data/cad-astra-pilot/tasks.json')

INK = ['#1f3348', '#123', '#22303f', '#2b2b2b', '#14304a', '#333c44', '#0f2a3d']
ACCENT = ['#8a1f1f', '#7a4f00', '#1a5c3a', '#4a2a6a', '#8a1f1f']
FAMILIES = ['Arial, Helvetica, sans-serif', 'Helvetica, Arial, sans-serif',
            'system-ui, sans-serif', '"DejaVu Sans", Verdana, sans-serif']
TITLE_WORDS = ['Structural elevation', 'Frame elevation', 'Centreline elevation',
               'Structural centreline elevation', 'Rigid-jointed frame elevation']
SUBTITLES = ['dimensions in mm; sections b x h mm', 'all dimensions mm, sections b x h',
             'dimensions mm - member centrelines', 'centreline dimensions in mm; sections b x h mm']


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def frozen_hashes():
    out = set()
    for rel in BENCHMARKS:
        p = ROOT / rel
        if not p.exists():
            continue
        for t in json.loads(p.read_text())['tasks']:
            out.add(B.digest(t['model']))
            if t.get('source_model'):
                out.add(B.digest(t['source_model']))
    return out


def geometry_key(model):
    """Frames sharing this key are near duplicates and must stay in one split."""
    nodes = tuple(sorted((round(x), round(y)) for x, y in model['nodes'].values()))
    members = tuple(sorted((m['b_mm'], m['h_mm']) for m in model['members']))
    return digest([nodes, members])


def sample_params(rng):
    bays = rng.choice([1, 1, 2, 2, 2, 3, 3, 4])
    storeys = rng.choice([1, 2, 2, 2, 3, 3, 4])
    bay_mm = rng.randrange(2800, 4600, 100)
    storey_mm = rng.randrange(2600, 3500, 100)
    setback_after, drop = None, 1
    if storeys >= 2 and bays >= 2 and rng.random() < 0.35:
        setback_after = rng.randrange(1, storeys)
        drop = 1 if bays < 3 else rng.choice([1, 1, 2])
    return bays, storeys, bay_mm, storey_mm, setback_after, drop


# ----------------------------------------------------------------------------- randomised drawing
def fmt(value, rng):
    return rng.choice([f'{value:.3f}', f'{value:.1f}', f'{value:g}'])


def dim_text(length, rng):
    n = fmt(length, rng)
    return rng.choice([f'{n} mm', f'L = {n} mm', f'{n}mm', f'len {n} mm'])


def styled_svg(model, mapping, reference, rng):
    """A correct drawing of `model` in a randomised style. Content fixed, presentation varied."""
    s, ox, oy = mapping
    ink, accent = rng.choice(INK), rng.choice(ACCENT)
    family = rng.choice(FAMILIES)
    width = rng.choice([2, 3, 3, 4, 4, 5])
    f_title, f_dim, f_lab = rng.randrange(19, 27), rng.randrange(10, 14), rng.randrange(11, 15)
    tint = rng.choice(['#ffffff', '#ffffff', '#fdfdfb', '#fbfcfd'])
    shift = (rng.randrange(-30, 31), rng.randrange(-20, 21)) if rng.random() < 0.25 else None
    marker = rng.choice(['circle', 'rect', 'cross', 'none'])
    label_nodes = rng.random() < 0.8
    corner = rng.choice(['bl', 'br', 'tr'])

    def P(x, y):
        return ox + s * x - (shift[0] if shift else 0), oy - s * y - (shift[1] if shift else 0)

    body = []
    members, nodes = [], []
    for m in model['members']:
        a, b = model['nodes'][m['a']], model['nodes'][m['b']]
        x1, y1 = P(*a)
        x2, y2 = P(*b)
        kind = rng.choice(['line', 'polyline', 'path'])
        attrs = f'data-member="{m["id"]}" stroke="{ink}" stroke-width="{width}" fill="none"'
        if kind == 'line':
            members.append(f'<line {attrs} x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}"/>')
        elif kind == 'polyline':
            members.append(f'<polyline {attrs} points="{x1:.3f},{y1:.3f} {x2:.3f},{y2:.3f}"/>')
        else:
            members.append(f'<path {attrs} d="M {x1:.3f},{y1:.3f} L {x2:.3f},{y2:.3f}"/>')
        length = float(np.hypot(b[0] - a[0], b[1] - a[1]))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = rng.choice([(8, -8), (-8, -10), (6, 12), (10, 4), (-12, 6)])
        members.append(f'<text data-dimension="length_{m["id"]}" x="{mx + dx:.3f}" y="{my + dy:.3f}" '
                       f'font-size="{f_dim}" fill="{ink}">{dim_text(length, rng)}</text>')
    for name, (x, y) in model['nodes'].items():
        X, Y = P(x, y)
        if marker == 'circle':
            nodes.append(f'<circle cx="{X:.3f}" cy="{Y:.3f}" r="{rng.choice([3, 4, 5])}" fill="{ink}"/>')
        elif marker == 'rect':
            nodes.append(f'<rect x="{X - 3.5:.3f}" y="{Y - 3.5:.3f}" width="7" height="7" fill="{ink}"/>')
        elif marker == 'cross':
            nodes.append(f'<path d="M{X - 5:.3f},{Y:.3f} H{X + 5:.3f} M{X:.3f},{Y - 5:.3f} '
                         f'V{Y + 5:.3f}" stroke="{ink}" stroke-width="1.5" fill="none"/>')
        if label_nodes:
            nodes.append(f'<text x="{X + 7:.3f}" y="{Y + 16:.3f}" font-size="{f_lab}" fill="{ink}">{name}</text>')
        if name in model['supports']:
            nodes.append(f'<path d="M{X - 12:.3f},{Y + 6:.3f} H{X + 12:.3f} M{X - 12:.3f},{Y + 6:.3f} '
                         f'l-6,9 M{X:.3f},{Y + 6:.3f} l-6,9 M{X + 12:.3f},{Y + 6:.3f} l-6,9" '
                         f'stroke="{ink}" stroke-width="1.2" fill="none"/>')

    sched_x, sched_y = {'bl': (35, 700), 'br': (620, 700), 'tr': (700, 120)}[corner]
    schedule = []
    for i, m in enumerate(model['members']):
        schedule.append(f'<text x="{sched_x + (i % 3) * 150}" y="{sched_y + (i // 3) * 20}" '
                        f'font-size="{f_dim}" fill="{ink}">{m["id"]}: {m["b_mm"]} x {m["h_mm"]}</text>')
    results = []
    ry = rng.choice([780, 790, 800])
    for i, key in enumerate(('ux_mm', 'uy_mm', 'peak_stress_mpa')):
        unit = 'MPa' if key.endswith('mpa') else 'mm'
        results.append(f'<text x="{35 + i * 345}" y="{ry}" font-size="{f_lab}" fill="{accent}">{key}: '
                       f'<tspan data-result="{key}">{reference[key]:.6f} {unit}</tspan></text>')

    order = [members, nodes] if rng.random() < 0.7 else [nodes, members]
    body = [item for group in order for item in group] + schedule + results
    inner = '\n'.join(body)
    if shift:
        inner = f'<g transform="translate({shift[0]},{shift[1]})">\n{inner}\n</g>'
    title = f'{html.escape(model["name"])} - {rng.choice(TITLE_WORDS)}'
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 850" width="1100" height="850">\n'
            f'<rect width="1100" height="850" fill="{tint}"/>\n'
            f'<text x="35" y="{rng.randrange(34, 46)}" font-size="{f_title}" '
            f'font-family="{family}" fill="{ink}">{title}</text>\n'
            f'<text x="35" y="{rng.randrange(60, 72)}" font-size="{f_lab}" font-family="{family}" '
            f'fill="{ink}">{rng.choice(SUBTITLES)}</text>\n' + inner + '\n</svg>')


# ----------------------------------------------------------------------------- pairs
def make_pair(rng, arm, frozen):
    for _ in range(40):
        bays, storeys, bay_mm, storey_mm, setback_after, drop = sample_params(rng)
        base = F.frame(bays, storeys, bay_mm, storey_mm, setback_after=setback_after, drop=drop,
                       name=f'{bays}-bay {storeys}-storey frame')
        edited, instruction = F.edit_of(base, rng.choice(['shift_grid', 'raise_floor']))
        model = base if arm == 'text2svg' else edited
        if B.digest(model) in frozen or B.digest(base) in frozen:
            continue
        try:
            reference = F.verified_reference(model)
        except ValueError:
            continue
        if reference['peak_stress_mpa'] > model['limits']['peak_stress_mpa']:
            continue
        mapping = B.mapping(edited)
        target = styled_svg(model, mapping, reference, rng)
        task = dict(model=model, mapping=mapping, dimensions=B.dimensions(model),
                    limits=model['limits'], reference=reference)
        row = B.score(task, json.dumps({'svg': target, 'analysis': {
            'ux_mm': reference['ux_mm'], 'uy_mm': reference['uy_mm'],
            'peak_stress_mpa': reference['peak_stress_mpa'], 'status': 'calculated'}}))
        if any(row[k] for k in ('geometry_errors', 'dimension_errors', 'analysis_errors',
                                'format_errors', 'visible_result_errors')):
            continue                                   # a target that does not verify is a generator bug
        # The scorer records a FEM re-solve of the reconstructed drawn frame but does not gate on it,
        # so gate here: the physics of the drawing itself must match the reference, not merely its
        # coordinates. Without this a target could pass on geometry alone.
        drawn = row.get('drawn_geometry_fem')
        if not drawn:
            continue
        if abs(drawn['peak_stress_mpa'] - reference['peak_stress_mpa']) > 2e-3 * abs(reference['peak_stress_mpa']):
            continue
        if arm == 'text2svg':
            prompt = S.describe(base['name'], bays, storeys, bay_mm, storey_mm, setback_after, drop, base)
        else:
            prompt = ('Original SVG:\n' + styled_svg(base, mapping, F.verified_reference(base), rng)
                      + '\nEDIT: ' + instruction)
        return {'arm': arm, 'prompt': prompt, 'target': target,
                'model': model, 'mapping': mapping, 'dimensions': B.dimensions(model),
                'limits': model['limits'], 'reference_full': reference,
                'geometry_key': geometry_key(model), 'model_sha256': B.digest(model),
                'members': len(model['members']), 'indeterminacy': F.indeterminacy(model),
                'reference': {k: reference[k] for k in ('ux_mm', 'uy_mm', 'peak_stress_mpa')}}
    return None


def build(out=OUT, n=400, seed=20260923):
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    frozen = frozen_hashes()
    print(f'{len(frozen)} frozen benchmark geometries excluded', flush=True)
    rows, rejected = [], 0
    for arm in ('text2svg', 'svg2svg'):
        made = 0
        while made < n:
            pair = make_pair(rng, arm, frozen)
            if pair is None:
                rejected += 1
                continue
            rows.append(pair)
            made += 1
            if made % 50 == 0:
                print(f'  {arm}: {made}/{n}', flush=True)
    groups = sorted({r['geometry_key'] for r in rows})
    rng.shuffle(groups)
    cut_v, cut_t = int(0.8 * len(groups)), int(0.9 * len(groups))
    split = {g: ('train' if i < cut_v else 'validation' if i < cut_t else 'test')
             for i, g in enumerate(groups)}
    counts = {}
    for name in ('train', 'validation', 'test'):
        part = [r for r in rows if split[r['geometry_key']] == name]
        counts[name] = len(part)
        with (out / f'{name}.jsonl').open('w') as fh:
            for r in part:
                fh.write(json.dumps(r) + '\n')
    manifest = {'version': 'eng-svg-trainset-v1', 'seed': seed, 'per_arm': n,
                'pairs': len(rows), 'splits': counts, 'rejected_before_acceptance': rejected,
                'frozen_geometries_excluded': len(frozen),
                'split_rule': 'by geometry key, so near-duplicate frames cannot straddle splits',
                'acceptance': ('every target was scored by cad_astra_benchmark.score and written only if '
                               'clean, and only if a FEM re-solve of its reconstructed drawn geometry '
                               'matched the reference peak stress to 2e-3'),
                'style_randomisation': ['member element type (line/polyline/path)', 'ink and accent colour',
                                        'stroke width', 'three font sizes', 'font family',
                                        'dimension text wording, side and offset', 'node marker style',
                                        'node labels present or absent', 'support symbol weight',
                                        'section-schedule corner', 'results row position',
                                        'background tint', 'element order', 'optional translate group'],
                'external_data': 'none'}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2)[:900])
    return manifest


def verify(out=OUT):
    checks = []

    def check(name, ok, detail=''):
        checks.append({'check': name, 'pass': bool(ok), 'detail': detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}", flush=True)

    rows = []
    for name in ('train', 'validation', 'test'):
        rows += [json.loads(l) for l in (out / f'{name}.jsonl').read_text().splitlines()]
    check('pairs were produced', rows, f'{len(rows)} pairs')

    frozen = frozen_hashes()
    leak = [r['model_sha256'] for r in rows if r['model_sha256'] in frozen]
    check('no benchmark geometry appears in training data', not leak, f'{len(leak)} leaked')

    groups = {}
    for name in ('train', 'validation', 'test'):
        for line in (out / f'{name}.jsonl').read_text().splitlines():
            groups.setdefault(json.loads(line)['geometry_key'], set()).add(name)
    straddle = [g for g, s in groups.items() if len(s) > 1]
    check('no geometry group straddles a split', not straddle, f'{len(straddle)} straddling')

    # The point of the exercise: targets must not all look alike.
    import re
    sigs = set()
    for r in rows[:400]:
        t = r['target']
        sigs.add((tuple(sorted(set(re.findall(r'stroke="([^"]+)"', t))))[:2],
                  tuple(sorted(set(re.findall(r'font-size="([^"]+)"', t))))[:3],
                  bool(re.search(r'<polyline data-member', t)), bool(re.search(r'<path data-member', t)),
                  bool(re.search(r'<g transform=', t))))
    sampled = min(len(rows), 400)
    # A single template collapses to one signature, so judge the ratio rather than an absolute count.
    check('targets are stylistically varied, not one template', len(sigs) >= 0.6 * sampled,
          f'{len(sigs)} distinct style signatures across {sampled} targets '
          f'({len(sigs) / max(sampled, 1):.0%}; one template would give 1)')

    kinds = set()
    for r in rows[:400]:
        for k in ('line', 'polyline', 'path'):
            if re.search(rf'<{k} data-member', r['target']):
                kinds.add(k)
    check('members are drawn with all three element types', kinds == {'line', 'polyline', 'path'}, str(sorted(kinds)))

    # Re-score a sample of written targets, so acceptance is proven here and not merely asserted.
    bad = []
    for r in rows[:40]:
        model = json.loads(json.dumps(r['model'])) if 'model' in r else None
        if model is None:
            continue
        row = B.score(dict(model=model, mapping=r['mapping'], dimensions=r['dimensions'],
                           limits=r['limits'], reference=r['reference_full']),
                      json.dumps({'svg': r['target'], 'analysis': dict(r['reference'], status='calculated')}))
        if any(row[k] for k in ('geometry_errors', 'dimension_errors', 'analysis_errors',
                                'format_errors', 'visible_result_errors')):
            bad.append(row)
    check('a re-scored sample of written targets is still clean', not bad, f'{len(bad)} of 40 failed')

    spread = {r['members'] for r in rows}
    check('frames span a range of sizes', len(spread) >= 5 and max(spread) - min(spread) >= 6,
          f'{min(spread)}-{max(spread)} members, {len(spread)} distinct sizes')

    ok = all(c['pass'] for c in checks)
    (out / 'verification.json').write_text(json.dumps({'all_pass': ok, 'checks': checks}, indent=2) + '\n')
    print('\nALL CHECKS PASS' if ok else '\nVERIFICATION FAILED')
    return ok


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build')
    b.add_argument('--out', type=Path, default=OUT)
    b.add_argument('--n', type=int, default=400, help='pairs per arm')
    b.add_argument('--seed', type=int, default=20260923)
    v = sub.add_parser('verify')
    v.add_argument('--out', type=Path, default=OUT)
    a = p.parse_args()
    if a.cmd == 'build':
        build(a.out, a.n, a.seed)
    else:
        raise SystemExit(0 if verify(a.out) else 1)


if __name__ == '__main__':
    main()
