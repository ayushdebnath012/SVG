"""Two-arm engineering-drawing benchmark: text to SVG, and SVG to SVG, both checked by FEM.

Arm 1, `text2svg`: the model receives a *parametric prose* description of a plane frame --- bays,
storeys, spacings, setback, sections by role, loads by position, and an explicit naming convention ---
and must derive every node coordinate and every member itself before drawing. No JSON is supplied.

Arm 2, `svg2svg`: the model receives only the source drawing and a natural-language edit, and must
recover the geometry from the SVG itself. No JSON is supplied here either.

Both arms are checked the same way: the scorer reconstructs node positions from the *drawn* member
centrelines and re-solves that reconstructed frame with the same linear frame FEM used to build the
reference, so the physics of what was actually drawn is verified rather than what was claimed.

This is deliberately harder than `eng_frame_bench`, where the physical model was handed over as JSON.
Astra's 42-sample record there was earned with coordinates supplied and does not transfer here.

Subcommands: build | verify.  Run and score with cad_astra_benchmark against --data.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
import cad_astra_benchmark as B          # noqa: E402
import eng_frame_bench as F              # noqa: E402

DATA = ROOT / 'data/eng-svg-bench'
VERSION = 'eng-svg-bench-v1'

# 24 frames spanning the ladder. Each is (name, bays, storeys, bay_mm, storey_mm, setback_after, drop).
LADDER = [
    ('portal_a',        1, 1, 3600, 3000, None, 1), ('portal_b',        1, 1, 4200, 3300, None, 1),
    ('twobay_a',        2, 1, 3400, 2900, None, 1), ('twobay_b',        2, 1, 3800, 3100, None, 1),
    ('threebay_flat',   3, 1, 3200, 2900, None, 1), ('twostorey_a',     1, 2, 3600, 2800, None, 1),
    ('twostorey_b',     1, 2, 4000, 3000, None, 1), ('setback_a',       2, 2, 3400, 2900, 1, 1),
    ('setback_b',       2, 2, 3900, 3100, 1, 1),    ('setback_c',       2, 2, 3300, 2700, 1, 1),
    ('twobay_two_a',    2, 2, 3400, 2900, None, 1), ('twobay_two_b',    2, 2, 3700, 2700, None, 1),
    ('threestorey_a',   1, 3, 3600, 2800, None, 1), ('threestorey_b',   1, 3, 3300, 3000, None, 1),
    ('setback_tall_a',  3, 3, 3300, 2800, 1, 2),    ('setback_tall_b',  3, 2, 3500, 2900, 1, 1),
    ('threebay_two_a',  3, 2, 3200, 2900, None, 1), ('threebay_two_b',  3, 2, 3600, 2700, None, 1),
    ('fourbay_a',       4, 2, 3200, 2900, None, 1), ('fourbay_b',       4, 2, 3000, 3100, None, 1),
    ('twobay_four_a',   2, 4, 3500, 2800, None, 1), ('twobay_four_b',   2, 4, 3200, 3000, None, 1),
    ('threebay_three_a', 3, 3, 3300, 2800, None, 1), ('threebay_three_b', 3, 3, 3600, 2600, None, 1),
]
EDIT_KIND = {i: ('raise_floor' if i % 2 else 'shift_grid') for i in range(len(LADDER))}


def counts(model):
    return len(model['nodes']), len(model['members'])


def describe(name, bays, storeys, bay_mm, storey_mm, setback_after, drop, model):
    """Parametric prose. States the rules; the model derives coordinates and the member list."""
    nodes, members = counts(model)
    lines = []
    lines.append(
        f'A {bays}-bay, {storeys}-storey rigid-jointed plane steel frame, drawn as a structural '
        f'centreline elevation. Column lines are spaced {bay_mm} mm apart horizontally, starting at '
        f'x = 0. Floor levels are spaced {storey_mm} mm apart vertically, starting at y = 0 at the bases.')
    if setback_after is not None:
        lines.append(
            f'Above floor level {setback_after} the frame steps back: the {drop} rightmost column '
            f'line{"s" if drop > 1 else ""} do{"" if drop > 1 else "es"} not continue upward. A column '
            f'exists between two consecutive floor levels only where its column line is present at both '
            f'levels. A beam exists at a floor level between two adjacent column lines only where both '
            f'are present at that level.')
    lines.append(
        'Name the node on column line c at floor level f as N{c}_{f}, with column lines numbered from 0 '
        'at the left and floor levels from 0 at the bases. Name the column rising from floor f to floor '
        'f+1 on line c as col_{c}_{f}. Name the beam at floor level f spanning from column line c to '
        'line c+1 as beam_{c}_{f}.')
    lines.append(
        'All sections are solid rectangles, b x h mm, with h in the frame plane and b out of plane. '
        'Columns rising from floor level 0 are 160 x 200 mm; every column above that is 140 x 180 mm at '
        'floor level 1, 140 x 160 mm at level 2, and so on, losing 20 mm of depth per level. Beams at '
        'floor level 1 are 140 x 260 mm, at level 2 are 140 x 240 mm, and so on, likewise losing 20 mm '
        'of depth per level. Young\'s modulus is 200000 N/mm^2 for every member.')
    lines.append(
        'Every node at floor level 0 is a clamped base: both translations and the rotation are fixed. '
        'The idealised bases are clamped, not freely resting on a floor.')
    load_bits = []
    for floor in range(1, storeys + 1):
        left = F.name_node(0, floor)
        right = next(n for n in model['loads'] if n != left and n.endswith(f'_{floor}'))
        lx, ly, _ = model['loads'][left]
        _, ry, _ = model['loads'][right]
        load_bits.append(
            f'at {left}, {lx} N horizontal in +x together with {ly} N vertical; '
            f'at {right}, {ry} N vertical')
    lines.append('Loads act only at nodes: ' + '; '.join(load_bits) + '. No other loads act.')
    lines.append(
        f'Derived correctly this frame has exactly {nodes} nodes and {members} members. '
        f'Report signed ux and uy at node {model["probe"]}.')
    return ' '.join(lines)


def build(out=DATA, arm='text2svg', force=False):
    if (out / 'tasks.json').exists() and not force:
        raise SystemExit('Frozen manifest exists; pass --force or choose a fresh --data')
    out.mkdir(parents=True, exist_ok=True)
    tasks = []
    for index, (name, bays, storeys, bay_mm, storey_mm, setback_after, drop) in enumerate(LADDER):
        base = F.frame(bays, storeys, bay_mm, storey_mm, setback_after=setback_after, drop=drop,
                       name=f'{name.replace("_", " ").title()} frame elevation')
        edited, instruction = F.edit_of(base, EDIT_KIND[index])
        mapping = B.mapping(edited)
        model = base if arm == 'text2svg' else edited
        deg = F.indeterminacy(model)
        task = dict(id=f'{name}_{arm}', family=name, mode='generate' if arm == 'text2svg' else 'edit',
                    arm=arm, model=model, mapping=mapping, dimensions=B.dimensions(model),
                    limits=model['limits'], indeterminacy=deg, members=len(model['members']))
        head = ('Make a dimensioned structural elevation of the frame described below. '
                'This task concerns only the stated 2D frame, not complete product or building validation.')
        if arm == 'text2svg':
            body = '\n' + describe(name, bays, storeys, bay_mm, storey_mm, setback_after, drop, base)
        else:
            source = B.reference_svg(base, mapping)
            task['source_model'] = base
            task['source_svg'] = source
            head = ('The SVG below is an existing dimensioned structural centreline elevation of a '
                    'rigid-jointed plane steel frame. Read its geometry, sections, supports and loads '
                    'from the drawing itself; no separate model is supplied. Apply the stated edit and '
                    'return the complete edited drawing. This task concerns only the stated 2D frame, '
                    'not complete product or building validation.')
            body = ('\nOriginal SVG:\n' + source + '\nEDIT: ' + instruction
                    + f'\nAfter the edit, report signed ux and uy at node {model["probe"]}.')
        s, ox, oy = mapping
        tail = (f'\nKeep viewBox="0 0 1100 850". Map physical (x,y) mm to SVG (X,Y) as '
                f'X={ox}+{s:.15g}*x, Y={oy}-{s:.15g}*y. Draw exactly the members of the frame, each as '
                'one visible straight element carrying data-member with its ID. Required dimensions are '
                'the physical centreline length of every member, tagged data-dimension="length_MEMBERID". '
                'Recompute every dimension and the analysis for the frame you draw. Report the peak '
                'extreme-fibre normal stress across member ends. Give at least three significant digits. '
                'Check against the limits stated in the task; make no other safety claim.')
        task['prompt'] = head + body + tail
        task['reference'] = F.verified_reference(model)
        task['validation_techniques'] = ['SVG geometry and connectivity constraints', 'dimension consistency',
                                         'global force and moment equilibrium', 'linear frame FEM',
                                         'member-subdivision reference check',
                                         'FEM re-solve of the reconstructed drawn geometry']
        task['model_sha256'] = B.digest(model)
        tasks.append(task)
        (out / (task['id'] + '.reference.svg')).write_text(B.reference_svg(model, mapping))
        print(f"{task['id']:30s} members={len(model['members']):3d} indeterminacy={deg:3d} "
              f"nodes={len(model['nodes']):3d} prompt={len(task['prompt']):6d} ch", flush=True)
    manifest = dict(
        version=VERSION, arm=arm,
        scope=('Engineering structural elevations. text2svg: parametric prose to SVG. '
               'svg2svg: existing SVG plus a natural-language edit to SVG. No JSON model is supplied in '
               'either arm; the model must derive or recover the geometry itself.'),
        criteria={'geometry_tolerance_mm': 1.0, 'dimension_tolerance_mm': 1.0, 'numeric_rtol': 0.02,
                  'displacement_atol_mm': 0.01, 'stress_atol_mpa': 0.05,
                  'selection': ('Three completed non-truncated samples all showing the same substantive '
                                'error. Truncated, errored and SVG-less attempts are excluded rather '
                                'than counted as failures.')},
        tasks=tasks)
    (out / 'tasks.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'\nwrote {len(tasks)} {arm} tasks -> {out / "tasks.json"}')
    return manifest


def verify(out=DATA):
    checks = []

    def check(name, ok, detail=''):
        checks.append({'check': name, 'pass': bool(ok), 'detail': detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}", flush=True)

    manifest = json.loads((out / 'tasks.json').read_text())
    tasks, arm = manifest['tasks'], manifest['arm']
    check('ids are unique', len({t['id'] for t in tasks}) == len(tasks), f'{len(tasks)} tasks')
    check('the ladder spans a wide complexity range',
          min(t['members'] for t in tasks) <= 3 and max(t['members'] for t in tasks) >= 18,
          f"{min(t['members'] for t in tasks)}-{max(t['members'] for t in tasks)} members, "
          f"indeterminacy {min(t['indeterminacy'] for t in tasks)}-{max(t['indeterminacy'] for t in tasks)}")

    # The point of this benchmark: no JSON model anywhere in the prompt.
    leaked = [t['id'] for t in tasks if '"nodes"' in t['prompt'] or '"members"' in t['prompt']
              or '"b_mm"' in t['prompt']]
    check('no prompt leaks a JSON physical model', not leaked, str(leaked[:4]))
    if arm == 'text2svg':
        coords = [t['id'] for t in tasks if 'N0_0 at (' in t['prompt']]
        check('text2svg states rules rather than enumerating node coordinates', not coords, str(coords[:4]))
        bad = [t['id'] for t in tasks
               if f"exactly {len(t['model']['nodes'])} nodes and {len(t['model']['members'])} members"
               not in t['prompt']]
        check('every description carries a correct node/member checksum', not bad, str(bad[:4]))
    else:
        missing = [t['id'] for t in tasks if 'Original SVG:' not in t['prompt'] or 'EDIT:' not in t['prompt']]
        check('every svg2svg prompt carries the source drawing and an edit', not missing, str(missing[:4]))
        inert = [t['id'] for t in tasks
                 if B.dimensions(t['source_model']) == t['dimensions']]
        check('every edit changes the dimensions', not inert, str(inert[:4]))

    bad = [t['id'] for t in tasks if F.indeterminacy(t['model']) != t['indeterminacy']]
    check('recorded indeterminacy is correct for every frame', not bad, str(bad[:4]))
    over = [t['id'] for t in tasks if t['reference']['peak_stress_mpa'] > t['limits']['peak_stress_mpa']
            or abs(t['reference']['uy_mm']) > t['limits']['abs_uy_mm']]
    check('every reference design satisfies its own stated limits', not over, str(over[:4]))

    # Positive control: the exporter's own drawing must pass every check, including the drawn-geometry FEM.
    worst = []
    for t in tasks:
        svg = (out / (t['id'] + '.reference.svg')).read_text()
        row = B.score(t, json.dumps({'svg': svg, 'analysis': {
            'ux_mm': t['reference']['ux_mm'], 'uy_mm': t['reference']['uy_mm'],
            'peak_stress_mpa': t['reference']['peak_stress_mpa'], 'status': 'calculated'}}))
        if any(row[k] for k in ('geometry_errors', 'dimension_errors', 'analysis_errors',
                                'format_errors', 'visible_result_errors')):
            worst.append((t['id'], {k: row[k] for k in row if row[k] and k != 'outcome'}))
    check('the harness passes the exporter drawing for every task', not worst, json.dumps(worst)[:300])

    # And that control must also survive the FEM re-solve of its own reconstructed geometry.
    drift = []
    for t in tasks:
        svg = (out / (t['id'] + '.reference.svg')).read_text()
        row = B.score(t, json.dumps({'svg': svg, 'analysis': {
            'ux_mm': t['reference']['ux_mm'], 'uy_mm': t['reference']['uy_mm'],
            'peak_stress_mpa': t['reference']['peak_stress_mpa'], 'status': 'calculated'}}))
        got = row.get('drawn_geometry_fem')
        if not got:
            drift.append((t['id'], 'no drawn-geometry FEM'))
            continue
        rel = abs(got['peak_stress_mpa'] - t['reference']['peak_stress_mpa']) / t['reference']['peak_stress_mpa']
        if rel > 2e-3:
            drift.append((t['id'], rel))
    check('FEM of the reconstructed drawn geometry matches the reference, for every task',
          not drift, f'{len(tasks)} tasks checked; ' + str(drift[:3]))

    ok = all(c['pass'] for c in checks)
    (out / 'verification.json').write_text(json.dumps({'all_pass': ok, 'arm': arm, 'checks': checks}, indent=2) + '\n')
    print('\nALL CHECKS PASS' if ok else '\nVERIFICATION FAILED')
    return ok


def regrade(run_dir, data=DATA, tolerance=2e-3):
    """Apply the drawn-geometry FEM gate to a scored run.

    `cad_astra_benchmark.score` computes a FEM re-solve of the frame reconstructed from the drawn
    member centrelines, but records it without letting it decide the outcome: the verdict rests on
    member coordinates, dimensions and the claimed analysis. This pass makes the re-solve decide as
    well, so a drawing whose own physics disagrees with the reference cannot pass on coordinates.

    It can only turn a pass into a failure. Nothing is ever relaxed here.
    """
    manifest = json.loads((data / 'tasks.json').read_text())
    tasks = {t['id']: t for t in manifest['tasks']}
    summary = json.loads((run_dir / 'summary.json').read_text())
    rows, changed = [], 0
    for row in summary['rows']:
        out = dict(row)
        task = tasks.get(row['id'])
        drawn = row.get('drawn_geometry_fem')
        if task and row.get('outcome') == 'pass':
            if not drawn:
                out['regraded_outcome'] = 'failure'
                out['regrade_reason'] = (row.get('drawn_geometry_fem_error')
                                         or 'the drawn frame could not be re-solved, so its physics is unverified')
                changed += 1
            else:
                ref = task['reference']
                rel = {k: abs(drawn[k] - ref[k]) / max(abs(ref[k]), 1e-9)
                       for k in ('ux_mm', 'uy_mm', 'peak_stress_mpa')}
                if max(rel.values()) > tolerance:
                    out['regraded_outcome'] = 'failure'
                    out['regrade_reason'] = (f'FEM of the drawn frame disagrees with the reference: '
                                             f'{max(rel, key=rel.get)} off by {max(rel.values()):.3e}')
                    changed += 1
                else:
                    out['regraded_outcome'] = 'pass'
                    out['drawn_geometry_relative_error'] = rel
        else:
            out['regraded_outcome'] = row.get('outcome')
        rows.append(out)
    counts = {}
    for r in rows:
        counts[r['regraded_outcome']] = counts.get(r['regraded_outcome'], 0) + 1
    result = {'source': str(run_dir / 'summary.json'), 'tolerance': tolerance,
              'rule': ('a pass is withdrawn when the FEM re-solve of the reconstructed drawn frame '
                       'disagrees with the reference, or cannot be performed. Nothing is ever relaxed.'),
              'verdicts_changed': changed, 'counts': counts, 'rows': rows}
    (run_dir / 'regrade.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'{changed} verdict(s) changed by the drawn-geometry FEM gate')
    print(json.dumps(counts, indent=2))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build')
    b.add_argument('--data', type=Path, default=DATA)
    b.add_argument('--arm', choices=['text2svg', 'svg2svg'], default='text2svg')
    b.add_argument('--force', action='store_true')
    v = sub.add_parser('verify')
    v.add_argument('--data', type=Path, default=DATA)
    g = sub.add_parser('regrade')
    g.add_argument('--output', type=Path, required=True)
    g.add_argument('--data', type=Path, default=DATA)
    a = p.parse_args()
    if a.cmd == 'build':
        build(a.data, a.arm, a.force)
    elif a.cmd == 'regrade':
        regrade(a.output, a.data)
    else:
        raise SystemExit(0 if verify(a.data) else 1)


if __name__ == '__main__':
    main()
