"""EngFrame: FEM-verified engineering elevations, concentrated where Astra actually fails.

The 20 September CAD pilot drew six dimensioned structural elevations. Five passed. One failed:
`building_edit`, where the drawing and the dimensions were correct, the model named the correct
governing member end (`col_EH, end E`) and stated the correct extreme-fibre formula, and then
printed **179 MPa** where an independent frame FEM gives **20.356 MPa**. Its displacements were
right to 0.3 %. The failure is the engineering claim on the drawing, not the drawing.

The three pilot families order exactly by degree of static indeterminacy, 3m + r - 3j:

    shelf  (cantilever chain)  0   pass      a determinate frame yields to statics alone
    table  (portal)            3   pass
    building (2-storey setback) 9  FAIL      an indeterminate frame needs the simultaneous system

So this module generates frames procedurally along that axis and puts nearly all of its instances
at indeterminacy 9 and above, because there is no reason to spend on the region the model already
solves. Edit mode is emphasised for the same reason: `building_generate` passed and
`building_edit` failed.

Manifests are written in `cad_astra_benchmark`'s own format, so its proven runner and scorer are
reused unchanged: member centrelines, joint gaps, dimensions, ux/uy/peak stress against FEM at 2 %,
and agreement between the JSON analysis and the visible SVG text.

Subcommands: build | verify.  Run and score with cad_astra_benchmark against --data.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import re
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
import cad_astra_benchmark as B  # noqa: E402

DATA = ROOT / 'data/eng-frame-bench'
VERSION = 'eng-frame-bench-v1'


def indeterminacy(model):
    """Degree of static indeterminacy of a plane frame: 3m + r - 3j."""
    m = len(model['members'])
    j = len(model['nodes'])
    r = sum(len(v) for v in model['supports'].values())
    return 3 * m + r - 3 * j


def name_node(col, floor):
    return f'N{col}_{floor}'


def frame(bays, storeys, bay_mm, storey_mm, setback_after=None, drop=1,
          loads=None, name='Frame elevation'):
    """A fixed-base rectilinear building frame, optionally stepped back above a floor.

    `setback_after=k` removes the `drop` rightmost column lines above floor k, which is how the
    pilot's two-storey building is shaped. Every base node is clamped.
    """
    columns_at = {}
    for floor in range(storeys + 1):
        n = bays + 1
        if setback_after is not None and floor > setback_after:
            n = max(2, bays + 1 - drop)
        columns_at[floor] = n

    nodes, members = {}, []
    for floor in range(storeys + 1):
        for col in range(columns_at[floor]):
            nodes[name_node(col, floor)] = [col * bay_mm, floor * storey_mm]
    for floor in range(storeys):
        # a column exists only where the line survives on both floors
        for col in range(min(columns_at[floor], columns_at[floor + 1])):
            hi = 200 - 20 * floor
            members.append(B.member(f'col_{col}_{floor}', name_node(col, floor),
                                    name_node(col, floor + 1), 140 + 20 * (floor == 0), hi))
        for col in range(columns_at[floor + 1] - 1):
            members.append(B.member(f'beam_{col}_{floor + 1}', name_node(col, floor + 1),
                                    name_node(col + 1, floor + 1), 140, 260 - 20 * floor))
    supports = {name_node(col, 0): [0, 1, 2] for col in range(columns_at[0])}
    top = storeys
    probe = name_node(columns_at[top] - 1, top)
    if loads is None:
        loads = {}
        for floor in range(1, storeys + 1):
            left = name_node(0, floor)
            right = name_node(columns_at[floor] - 1, floor)
            loads[left] = [9000 + 1500 * floor, -26000 - 4000 * floor, 0]
            loads[right] = [0, -38000 - 5000 * floor, 0]
    model = dict(name=name, nodes=nodes, members=members, supports=supports, loads=loads,
                 probe=probe, limits={'abs_uy_mm': 12.0, 'peak_stress_mpa': 180.0})
    return model


def edit_of(model, kind, index=0):
    """A geometry/load edit that forces every dimension and both analyses to be recomputed."""
    out = copy.deepcopy(model)
    cols = sorted({round(v[0]) for v in model['nodes'].values()})
    floors = sorted({round(v[1]) for v in model['nodes'].values()})
    if kind == 'shift_grid':
        old = cols[1 + index % max(1, len(cols) - 2)]
        new = old + 700
        for v in out['nodes'].values():
            if round(v[0]) == old:
                v[0] = new
        text = f'Move the column grid at x={old} mm to x={new} mm.'
    elif kind == 'raise_floor':
        old = floors[-1]
        new = old + 600
        for v in out['nodes'].values():
            if round(v[1]) == old:
                v[1] = new
        text = f'Raise the top floor from y={old} mm to y={new} mm.'
    else:
        raise ValueError(kind)
    target = out['probe']
    out['loads'].setdefault(target, [0, 0, 0])
    out['loads'][target] = [out['loads'][target][0], out['loads'][target][1] - 15000, 0]
    text += (f' Change the vertical load at {target} to {out["loads"][target][1]} N. '
             'Keep every other node, section and load unchanged.')
    return out, text


def instances():
    """The ladder. Two determinate/low controls, then everything in the failing region."""
    out = []
    out.append(('control_portal', frame(1, 1, 3600, 3000, name='Single-bay portal frame elevation'), 'shift_grid'))
    out.append(('control_twobay', frame(2, 1, 3400, 2900, name='Two-bay single-storey frame elevation'), 'shift_grid'))
    out.append(('setback_a', frame(2, 2, 3400, 2900, setback_after=1,
                                   name='Two-storey setback frame elevation'), 'raise_floor'))
    out.append(('setback_b', frame(2, 2, 3900, 3100, setback_after=1,
                                   name='Two-storey setback frame elevation, wide bays'), 'shift_grid'))
    out.append(('twostorey_a', frame(2, 2, 3400, 2900, name='Two-bay two-storey frame elevation'), 'raise_floor'))
    out.append(('twostorey_b', frame(2, 2, 3700, 2700, name='Two-bay two-storey frame elevation, low storeys'), 'shift_grid'))
    out.append(('threestorey', frame(1, 3, 3600, 2800, name='Single-bay three-storey frame elevation'), 'raise_floor'))
    out.append(('threebay', frame(3, 2, 3200, 2900, name='Three-bay two-storey frame elevation'), 'shift_grid'))
    out.append(('setback_tall', frame(3, 3, 3300, 2800, setback_after=1, drop=2,
                                      name='Three-storey double-setback frame elevation'), 'raise_floor'))
    return out


def instances_xl():
    """Past the screen's ceiling. The screen passed every instance up to indeterminacy 15 and
    declined the analysis at 18, so this set probes 24 and 27 to locate the boundary."""
    return [
        ('fourbay', frame(4, 2, 3200, 2900, name='Four-bay two-storey frame elevation'), 'shift_grid'),
        ('twobay_four', frame(2, 4, 3500, 2800, name='Two-bay four-storey frame elevation'), 'raise_floor'),
        ('threebay_three', frame(3, 3, 3300, 2800, name='Three-bay three-storey frame elevation'), 'shift_grid'),
    ]


def verified_reference(model):
    """Solve, and admit only if the mesh-invariance and equilibrium checks hold."""
    ref = B.solve(model)
    fine = B.solve(model, subdivisions=4)
    rel = {k: abs(ref[k] - fine[k]) / max(abs(ref[k]), 1e-8)
           for k in ('ux_mm', 'uy_mm', 'peak_stress_mpa')}
    if max(rel.values()) > 1e-7:
        raise ValueError(f'reference refinement disagreement: {rel}')
    ref['subdivision_relative_difference'] = rel
    # The residual is [Fx, Fy, Mz] in N, N and N*mm, so the force and moment parts need different
    # scales: dividing a moment residual by a force would reject a frame for being large, not wrong.
    fx, fy, mz = ref['equilibrium_residual_N_Nmm']
    force = max((abs(c) for load in model['loads'].values() for c in load[:2]), default=0.0) or 1.0
    span = max((max(abs(x), abs(y)) for x, y in model['nodes'].values()), default=0.0) or 1.0
    rel = max(abs(fx) / force, abs(fy) / force, abs(mz) / (force * span))
    if rel > 1e-9:
        raise ValueError(f'equilibrium residual too large: relative {rel:.3e} from {ref["equilibrium_residual_N_Nmm"]}')
    ref['equilibrium_relative_residual'] = rel
    return ref


def build(out=DATA, force=False, which='main'):
    if (out / 'tasks.json').exists() and not force:
        raise SystemExit('Frozen manifest already exists; pass --force or choose a fresh --data')
    out.mkdir(parents=True, exist_ok=True)
    tasks = []
    for family, base, edit_kind, in (instances() if which == 'main' else instances_xl()):
        edited, instruction = edit_of(base, edit_kind)
        common_map = B.mapping(edited)
        for mode, model in (('generate', base), ('edit', edited)):
            deg = indeterminacy(model)
            task = dict(id=f'{family}_{mode}', family=family, mode=mode, model=model,
                        mapping=common_map, dimensions=B.dimensions(model), limits=model['limits'],
                        indeterminacy=deg, members=len(model['members']))
            prompt = (f'Object: {model["name"]}. Make a dimensioned structural elevation. '
                      'All sections are solid rectangles; h is in the frame plane and b is out of plane. '
                      'The idealised column bases are clamped, not freely resting on a floor. '
                      'This task concerns only the stated 2D frame, not complete product/building validation. ')
            if mode == 'generate':
                prompt += '\nPhysical model:\n' + json.dumps(base)
            else:
                source = B.reference_svg(base, common_map)
                task['source_model'] = base
                task['source_svg'] = source
                prompt += ('\nOriginal physical model:\n' + json.dumps(base) + '\nOriginal SVG:\n'
                           + source + '\nEDIT: ' + instruction)
            s, ox, oy = common_map
            prompt += (f'\nKeep viewBox="0 0 1100 850". Map physical (x,y) mm to SVG (X,Y) as '
                       f'X={ox}+{s:.15g}*x, Y={oy}-{s:.15g}*y. Draw exactly the listed members. '
                       'Retain member IDs. Required dimensions are the physical centreline length of every member, '
                       'tagged data-dimension="length_MEMBERID". Recompute dimensions and analysis after any edit. '
                       f'Report signed ux and uy at {model["probe"]}, plus peak extreme-fibre normal stress across member ends. '
                       'Give at least three significant digits. Check against the limits in the model; no other safety claims.')
            task['prompt'] = prompt
            task['reference'] = verified_reference(model)
            task['validation_techniques'] = ['SVG geometry and connectivity constraints',
                                             'dimension consistency',
                                             'global force and moment equilibrium',
                                             'linear frame FEM',
                                             'member-subdivision reference check']
            task['model_sha256'] = B.digest(model)
            tasks.append(task)
            (out / (task['id'] + '.reference.svg')).write_text(B.reference_svg(model, common_map))
            print(f"{task['id']:28s} members={len(model['members']):3d} indeterminacy={deg:3d} "
                  f"peak={task['reference']['peak_stress_mpa']:9.4f} MPa "
                  f"uy={task['reference']['uy_mm']:8.4f} mm", flush=True)
    manifest = dict(
        version=VERSION,
        set=which,
        controls=('in this manifest' if which == 'main'
                  else 'in the companion main manifest; this set deliberately holds only the high '
                       'indeterminacy region and must be read alongside it'),
        scope=('Procedurally generated dimensioned structural elevations of planar building frames, '
               'generation and editing, ordered by degree of static indeterminacy. Not general 3D CAD.'),
        rationale=('Concentrated at indeterminacy 9 and above, where the 20 September pilot recorded its '
                   'only failure. The pilot families ordered 0 (pass), 3 (pass), 9 (fail).'),
        criteria={'geometry_tolerance_mm': 1.0, 'dimension_tolerance_mm': 1.0, 'numeric_rtol': 0.02,
                  'displacement_atol_mm': 0.01, 'stress_atol_mpa': 0.05,
                  'selection': ('Three completed non-truncated samples all showing the same substantive '
                                'analysis or geometry error. Format-only, missing output, API and '
                                'token-budget failures are excluded rather than counted as failures.')},
        tasks=tasks)
    (out / 'tasks.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'\nwrote {len(tasks)} tasks -> {out / "tasks.json"}')
    return manifest


def verify(out=DATA):
    checks = []

    def check(name, ok, detail=''):
        checks.append({'check': name, 'pass': bool(ok), 'detail': detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}", flush=True)

    # The generator must reproduce the pilot's own ordering of the three hand-made families.
    degs = {fam: indeterminacy(base) for fam, base, _, _ in B.models()}
    check('pilot families order by indeterminacy as shelf 0 < table 3 < building 9',
          (degs['shelf'], degs['table'], degs['building']) == (0, 3, 9), str(degs))

    manifest = json.loads((out / 'tasks.json').read_text())
    tasks = manifest['tasks']
    check('ids are unique', len({t['id'] for t in tasks}) == len(tasks), f'{len(tasks)} tasks')
    hard = [t for t in tasks if t['indeterminacy'] >= 9]
    check('most instances sit in the failing region (indeterminacy >= 9)',
          len(hard) >= 0.7 * len(tasks), f'{len(hard)} of {len(tasks)}')
    if manifest.get('set', 'main') == 'main':
        check('a determinate or low-indeterminacy control is present',
              any(t['indeterminacy'] <= 3 for t in tasks))
    else:
        main = DATA / 'tasks.json'
        have = (main.exists()
                and any(t['indeterminacy'] <= 3 for t in json.loads(main.read_text())['tasks']))
        check('this extension set carries no control, and the companion main set supplies one',
              have and not any(t['indeterminacy'] <= 3 for t in tasks),
              'controls belong to the main manifest by design')

    bad = []
    for t in tasks:
        model = t['model']
        if indeterminacy(model) != t['indeterminacy']:
            bad.append(t['id'])
        # every member must join two declared nodes, and every node must be used
        used = set()
        for m in model['members']:
            used.update((m['a'], m['b']))
            if m['a'] not in model['nodes'] or m['b'] not in model['nodes']:
                bad.append(t['id'])
        if used - set(model['nodes']) or set(model['nodes']) - used:
            bad.append(t['id'])
        if model['probe'] not in model['nodes']:
            bad.append(t['id'])
    check('every frame is well formed and its recorded indeterminacy is correct', not bad, str(sorted(set(bad))))

    # An edit must actually change the answer, or it tests nothing.
    inert = []
    for fam in {t['family'] for t in tasks}:
        gen = next(t for t in tasks if t['family'] == fam and t['mode'] == 'generate')
        edit = next(t for t in tasks if t['family'] == fam and t['mode'] == 'edit')
        same = all(abs(gen['reference'][k] - edit['reference'][k]) <= 1e-6
                   for k in ('ux_mm', 'uy_mm', 'peak_stress_mpa'))
        if same or gen['dimensions'] == edit['dimensions']:
            inert.append(fam)
    check('every edit changes both the dimensions and the analysis', not inert, str(inert))

    # The reference drawing must score as a pass, or the harness is measuring itself wrong.
    worst = []
    for t in tasks:
        svg = (out / (t['id'] + '.reference.svg')).read_text()
        row = B.score(t, json.dumps({'svg': svg, 'analysis': {
            'ux_mm': t['reference']['ux_mm'], 'uy_mm': t['reference']['uy_mm'],
            'peak_stress_mpa': t['reference']['peak_stress_mpa'], 'status': 'calculated'}}))
        if any(row[k] for k in ('geometry_errors', 'dimension_errors', 'analysis_errors',
                                'format_errors', 'visible_result_errors')):
            worst.append((t['id'], {k: row[k] for k in row if row[k] and k != 'outcome'}))
    check('the harness passes a drawing built from the reference itself', not worst,
          json.dumps(worst)[:400])

    # Stresses must be inside the stated limits, or the task is asking for an impossible design.
    over = [t['id'] for t in tasks
            if t['reference']['peak_stress_mpa'] > t['limits']['peak_stress_mpa']
            or abs(t['reference']['uy_mm']) > t['limits']['abs_uy_mm']]
    check('every reference design satisfies its own stated limits', not over, str(over))

    ok = all(c['pass'] for c in checks)
    (out / 'verification.json').write_text(json.dumps({'all_pass': ok, 'checks': checks}, indent=2) + '\n')
    print('\nALL CHECKS PASS' if ok else '\nVERIFICATION FAILED')
    return ok


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build')
    b.add_argument('--data', type=Path, default=DATA)
    b.add_argument('--force', action='store_true')
    b.add_argument('--set', dest='which', choices=['main', 'xl'], default='main')
    v = sub.add_parser('verify')
    v.add_argument('--data', type=Path, default=DATA)
    j = sub.add_parser('adjudicate')
    j.add_argument('--output', type=Path, required=True)
    j.add_argument('--data', type=Path, default=DATA)
    a = p.parse_args()
    if a.cmd == 'build':
        build(a.data, a.force, a.which)
    elif a.cmd == 'adjudicate':
        adjudicate(a.output, a.data)
    else:
        raise SystemExit(0 if verify(a.data) else 1)


# ----------------------------------------------------------------------------- adjudication
UNITS_NOTE = re.compile(r'dimensions?\s*(?:are\s*)?(?:in\s*)?(?:mm|millimet)', re.I)


def adjudicate(run_dir, data=DATA):
    """Reclassify per-label unit complaints when the drawing declares its units once, as drawings do.

    `cad_astra_benchmark.score` requires the literal string `mm` inside every `data-dimension` text.
    Stating units once in the drawing notes and leaving the dimension values bare is standard ISO/ASME
    practice, so that check rejects correct drafting. Three screen results were filed as
    `unscored_format` for this reason alone while carrying a note such as
    "Structural elevation - dimensions in mm - member centrelines". This pass restores them and
    records why; it never converts a failure into a pass, and every other error keeps its verdict.
    """
    manifest = json.loads((data / 'tasks.json').read_text())
    tasks = {t['id']: t for t in manifest['tasks']}
    summary = json.loads((run_dir / 'summary.json').read_text())
    rows = []
    for row in summary['rows']:
        note = dict(row)
        unit_only = [e for e in row.get('format_errors', []) if str(e).startswith('missing mm unit:')]
        others = [e for e in row.get('format_errors', []) if not str(e).startswith('missing mm unit:')]
        if unit_only and not others:
            folder = run_dir / row['id'] / f"sample-{row.get('sample', 0)}"
            text = (folder / 'response.txt').read_text() if (folder / 'response.txt').exists() else ''
            try:
                svg = B.read_response(text)['svg']
            except Exception:
                svg = ''
            declared = [t.strip() for t in re.findall(r'>([^<>]*)<', svg) if UNITS_NOTE.search(t)]
            if declared:
                rescored = B.score(tasks[row['id']], text)
                rescored['format_errors'] = [e for e in rescored.get('format_errors', [])
                                             if not str(e).startswith('missing mm unit:')]
                substantive = any(rescored[k] for k in ('geometry_errors', 'dimension_errors',
                                                        'analysis_errors', 'format_errors',
                                                        'visible_result_errors'))
                note['adjudicated_outcome'] = 'failure' if substantive else 'pass'
                note['adjudication_reason'] = (
                    'Units are declared once in the drawing: ' + declared[0][:120]
                    + '. Per-label "mm" is not required by drafting convention, so the unit-only '
                      'format complaint is withdrawn. All other checks were re-run unchanged.')
                note['withdrawn_format_errors'] = unit_only
            else:
                note['adjudicated_outcome'] = row['outcome']
                note['adjudication_reason'] = 'No drawing-level units note found; the complaint stands.'
        else:
            note['adjudicated_outcome'] = row['outcome']
        rows.append(note)
    counts = {}
    for r in rows:
        counts[r['adjudicated_outcome']] = counts.get(r['adjudicated_outcome'], 0) + 1
    out = {'source_summary': str(run_dir / 'summary.json'),
           'rule': ('A per-label unit complaint is withdrawn only when the drawing states its units and '
                    'no other check fails. Verdicts are never made stricter and never made looser for '
                    'any other reason.'),
           'adjudicated_counts': counts, 'rows': rows}
    (run_dir / 'adjudication.json').write_text(json.dumps(out, indent=2) + '\n')
    for r in rows:
        if r['adjudicated_outcome'] != r['outcome']:
            print(f"{r['id']:28s} {r['outcome']} -> {r['adjudicated_outcome']}", flush=True)
    print(json.dumps(counts, indent=2))
    return out

if __name__ == '__main__':
    main()
