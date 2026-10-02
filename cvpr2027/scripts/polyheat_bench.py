"""PolyHeat: a procedural benchmark for drawing Laplace isotherms on rectilinear plates.

The 18 September screen found that Astra reproduces closed-form fields to solver
accuracy but degrades badly on *unseen* rectilinear geometry: `c1_polygon_procedural`
scored 4.46 pp mean / 10.60 pp max away from the singular corners against a 0.50 pp
tolerance, and placed a 10 C isotherm on the 100 C edge. That task was labelled
"procedural" but was a single hardcoded polygon, so the failure was a data point
rather than a benchmark.

This module turns it into one. The failing plate is exactly a three-column skyline
(widths 0.2/0.4/0.4, heights 0.6/1.0/0.4), so the family generalises by construction:

    domain = { (x,y) : x in column i, 0 <= y <= h_i },  bottom edge hot at 100 C,
    every other edge held at 0 C.

A skyline is always simply connected and always keeps the whole hot edge, so every
sampled instance is well posed. Each height change contributes exactly one 270-degree
interior angle, which makes the re-entrant-corner count a clean difficulty axis and
gives a genuine control tier (one column = plain square, classical series solution).

References are red-black SOR on the shared `fd_reference` primitive at 160 nodes per
unit, each certified against a 320-node solve before it may be used. Drawings are scored
by the same `field_fidelity.score_svg` at the same 0.5 pp tolerance as the original screen.

Subcommands: generate | verify | run (billable) | score.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import random
import re
import sys
import time
import urllib.error
import urllib.request

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from svgpatchlab.eval.field_fidelity import extract_contours, interpolate_grid, score_svg  # noqa: E402
from astra_hard_tasks import STATUS_LINE, fd_polygon  # noqa: E402

DATA = ROOT / 'data/polyheat-bench'
TEMPLATE = ROOT / 'src/svgpatchlab/prompt_templates/generation_v1.txt'
ENDPOINT = 'https://api.openai.com/v1/chat/completions'
PRICE_INPUT, PRICE_OUTPUT = 10.0, 50.0

LATTICE = 5                       # unit square divided into fifths, as in the original plate
HEIGHTS = (2, 3, 4, 5)            # column heights in lattice units; 1/5 would pinch the domain
FIELD = 'T'
LEVELS = [10, 20, 40, 60, 80]
FIELD_RANGE = 100
MAPPING = (800, 100, -800, 900)   # X = 100 + 800 x, Y = 900 - 800 y
TOLERANCE_PP = 0.5
HOT_COLD = [[0.0, 0.0], [1.0, 0.0]]   # the two corners where the 100 C edge meets a 0 C edge
COARSE, FINE = 320, 640               # scoring reference, and the grid that certifies it
EXCLUDE_R = 0.05                      # singular-neighbourhood radius for the certified metric


# ----------------------------------------------------------------------------- geometry
def num(v: Fraction) -> str:
    """Render a lattice coordinate the way the original prompt did: 0, 1, 0.4, 0.6."""
    f = float(v)
    return str(int(f)) if f == int(f) else f'{f:g}'


def vertices(columns):
    """Counter-clockwise vertex ring of a skyline given [(width_units, height_units), ...]."""
    edges, acc = [], Fraction(0)
    for w, _ in columns:
        acc += Fraction(w, LATTICE)
        edges.append(acc)
    hs = [Fraction(h, LATTICE) for _, h in columns]
    xs = [Fraction(0)] + edges
    ring = [(Fraction(0), Fraction(0)), (Fraction(1), Fraction(0)), (Fraction(1), hs[-1])]
    for i in range(len(columns) - 1, 0, -1):
        ring.append((xs[i], hs[i]))
        ring.append((xs[i], hs[i - 1]))
    ring.append((Fraction(0), hs[0]))
    return ring, xs, hs


def reentrant(columns):
    """The 270-degree interior corners: one per height change, on the lower side of the step."""
    _, xs, hs = vertices(columns)
    # Right to left, the order in which the vertex ring meets them.
    return [(xs[i], min(hs[i - 1], hs[i])) for i in range(len(columns) - 1, 0, -1) if hs[i] != hs[i - 1]]


def inside_predicate(columns):
    _, xs, hs = vertices(columns)
    lo, hi = [float(v) for v in xs[:-1]], [float(v) for v in xs[1:]]
    tops = [float(h) for h in hs]
    eps = 1e-9

    def inside(X, Y):
        m = np.zeros(X.shape, bool)
        for a, b, t in zip(lo, hi, tops):
            m |= (X >= a - eps) & (X <= b + eps) & (Y <= t + eps)
        return m
    return inside


def prompt_text(columns):
    ring, _, _ = vertices(columns)
    verts = ', '.join(f'({num(x)},{num(y)})' for x, y in ring)
    corners = reentrant(columns)
    words = {1: 'one', 2: 'two', 3: 'three', 4: 'four'}
    if corners:
        listed = ' and '.join(f'({num(x)}, {num(y)})' for x, y in corners)
        crowding = (f', with correct crowding at the {words[len(corners)]} re-entrant corner'
                    f'{"s" if len(corners) > 1 else ""} {listed}')
    else:
        crowding = ''
    levels = ', '.join(str(v) for v in LEVELS[:-1]) + f' and {LEVELS[-1]}'
    return ('Steady two-dimensional heat conduction (Laplace equation) in a rectilinear plate with vertices, '
            f'in order, {verts}. The bottom edge y = 0 is held at 100 C; every other edge is held at 0 C. '
            f'Draw the plate outline and the isotherms at {levels} C{crowding}. '
            'Use viewBox="0 0 1000 1000". Map plate coordinates to drawing coordinates as '
            'X = 100 + 800 x and Y = 900 - 800 y.')


def full_prompt(columns):
    """The manifest prompt: the drawing task plus the same data-level/data-status contract the
    18 September screen appended, without which no contour carries a level and nothing is scoreable."""
    return prompt_text(columns) + ' ' + STATUS_LINE.format(field=FIELD)


# ----------------------------------------------------------------------------- instances
def compositions(total, parts):
    """All ordered positive-integer compositions of `total` into `parts` terms."""
    if parts == 1:
        yield (total,)
        return
    for first in range(1, total - parts + 2):
        for rest in compositions(total - first, parts - 1):
            yield (first,) + rest


def candidates(n_columns):
    """Every skyline with `n_columns` columns, adjacent heights distinct (no redundant column)."""
    out = []
    for widths in compositions(LATTICE, n_columns):
        def walk(i, chosen):
            if i == n_columns:
                out.append(tuple(zip(widths, chosen)))
                return
            for h in HEIGHTS:
                if i and h == chosen[-1]:
                    continue
                walk(i + 1, chosen + [h])
        walk(0, [])
    return out


TIERS = [('control', 1, 2), ('easy', 2, 3), ('medium', 3, 3), ('hard', 4, 3)]
ORIGINAL = ((1, 3), (2, 5), (2, 2))   # the 18 September plate: 0.2/0.6, 0.4/1.0, 0.4/0.4


def build_instances(seed=20260922):
    """Sample the difficulty ladder, with the original failing plate pinned as medium/0."""
    rng = random.Random(seed)
    picked, seen = [], set()
    for tier, columns, count in TIERS:
        pool = [c for c in candidates(columns) if c not in seen]
        rng.shuffle(pool)
        take = []
        if tier == 'medium':
            take.append(ORIGINAL)
            pool = [c for c in pool if c != ORIGINAL]
        take += pool[:count - len(take)]
        for k, cols in enumerate(take):
            seen.add(cols)
            picked.append({'id': f'polyheat_{tier}_{k}', 'tier': tier, 'columns': [list(c) for c in cols],
                           'n_columns': columns, 'reentrant_corners': len(reentrant(cols)),
                           'is_original_failing_plate': cols == ORIGINAL})
    return picked


# ----------------------------------------------------------------------------- references
def solve(columns, n_per_unit):
    inside = inside_predicate(columns)
    x, y, f, meta = fd_polygon(inside, lambda X, Y: Y <= 0, n_per_unit=n_per_unit)
    return x, y, f, meta


def singular_points(columns):
    """Every point where the field or its gradient is singular, so no scored metric may rely on it.

    The two hot/cold corners carry a jump in the boundary data. Each re-entrant corner carries an
    r^(2/3) gradient singularity, where finite differences lose their second-order convergence: the
    320-vs-640 difference there reaches 0.49 C, ten times its value anywhere else.
    """
    return [list(p) for p in HOT_COLD] + [[float(a), float(b)] for a, b in reentrant(columns)]


def certify(columns, radius=EXCLUDE_R):
    """Solve at both grids; the scoring grid may be used only where it agrees with the finer one."""
    xc, yc, fc, mc = solve(columns, COARSE)
    xf, yf, ff, mf = solve(columns, FINE)
    step = FINE // COARSE
    sub = ff[::step, ::step]
    assert sub.shape == fc.shape, (sub.shape, fc.shape)
    both = np.isfinite(fc) & np.isfinite(sub)
    diff = np.abs(fc - sub)
    X, Y = np.meshgrid(xc, yc)
    away = both.copy()
    for sx, sy in singular_points(columns):
        away &= np.hypot(X - sx, Y - sy) > radius
    return (xc, yc, fc), {
        'scoring_nodes_per_unit': COARSE, 'certifying_nodes_per_unit': FINE,
        'scoring_sor_iterations': mc['sor_iterations'], 'certifying_sor_iterations': mf['sor_iterations'],
        'compared_nodes': int(both.sum()),
        'max_abs_difference_C': float(diff[both].max()),
        'max_abs_difference_C_excluding_singular': float(diff[away].max()),
        'mean_abs_difference_C': float(diff[both].mean()),
        'tolerance_pp': TOLERANCE_PP, 'field_range': FIELD_RANGE,
        'singular_radius': radius, 'singular_points': singular_points(columns),
        'note': ('Grid-refinement sensitivity of the reference itself, not a certified continuum '
                 'error bound. The reference is admitted only when the difference away from the two '
                 'hot/cold corners is far below the scoring tolerance.'),
    }


def generate(out=DATA, seed=20260922, margin=10.0, reuse=True):
    """Build instances, solve and certify every reference, write the frozen task manifest.

    With `reuse`, an instance whose reference file and admitted certification are already stored is
    not re-solved, so a change confined to the prompt text does not repeat eleven 640-node solves.
    """
    out.mkdir(parents=True, exist_ok=True)
    (out / 'reference').mkdir(exist_ok=True)
    limit = TOLERANCE_PP / 100 * FIELD_RANGE / margin     # reference must be 10x tighter than tolerance
    stored = {}
    if reuse and (out / 'reference-audit.json').exists():
        prior = json.loads((out / 'reference-audit.json').read_text())
        if prior.get('admission_limit_C') == limit:
            stored = {r['id']: r for r in prior['rows'] if r.get('admitted')}
    tasks, audits = [], []
    for inst in build_instances(seed):
        cols = [tuple(c) for c in inst['columns']]
        npz = out / 'reference' / f"{inst['id']}.npz"
        cached = stored.get(inst['id'])
        if cached and npz.exists() and cached.get('singular_points') == singular_points(cols):
            audit, ok, reused = dict(cached), True, True
        else:
            (xc, yc, fc), audit = certify(cols)
            ok = audit['max_abs_difference_C_excluding_singular'] <= limit
            audit.update(id=inst['id'], admitted=bool(ok), admission_limit_C=limit)
            reused = False
        audits.append(audit)
        print(f"{inst['id']:22s} corners={inst['reentrant_corners']} "
              f"refine_diff={audit['max_abs_difference_C_excluding_singular']:.5f} C "
              f"{'ADMIT' if ok else 'REJECT'}{' (reused)' if reused else ''}", flush=True)
        if not ok:
            continue
        if not reused:
            np.savez(npz, x=xc, y=yc, field=fc)
        ring, _, _ = vertices(cols)
        tasks.append(dict(inst, levels=LEVELS, range=FIELD_RANGE, mapping=list(MAPPING),
                          singular=singular_points(cols), lattice=LATTICE,
                          vertices=[[float(a), float(b)] for a, b in ring],
                          reentrant=[[float(a), float(b)] for a, b in reentrant(cols)],
                          reference_file=f'data/polyheat-bench/reference/{inst["id"]}.npz',
                          prompt=full_prompt(cols)))
    manifest = {'benchmark': 'polyheat-skyline-v1', 'seed': seed, 'tolerance_pp': TOLERANCE_PP,
                'field_range': FIELD_RANGE, 'levels': LEVELS, 'mapping': list(MAPPING),
                'lattice': LATTICE, 'heights_units': list(HEIGHTS), 'hot_cold_corners': HOT_COLD,
                'exclusion_radius': EXCLUDE_R,
                'primary_metric': ('max sampled contour error with every singular neighbourhood removed; '
                                   'the reference is certified only there'),
                'solver': 'red-black SOR (scripts/fd_reference.sor) via astra_hard_tasks.fd_polygon',
                'scorer': 'svgpatchlab.eval.field_fidelity.score_svg',
                'generated_utc': datetime.now(timezone.utc).isoformat(),
                'admitted': len(tasks), 'proposed': len(audits), 'tasks': tasks}
    (out / 'tasks.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (out / 'reference-audit.json').write_text(json.dumps({'admission_limit_C': limit, 'rows': audits}, indent=2) + '\n')
    print(f'\nadmitted {len(tasks)}/{len(audits)} instances -> {out / "tasks.json"}')
    return manifest


# ----------------------------------------------------------------------------- verification
def verify(out=DATA):
    """Self-checks that must hold before any billable call."""
    checks = []

    def check(name, ok, detail=''):
        checks.append({'check': name, 'pass': bool(ok), 'detail': detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}", flush=True)

    ring, _, _ = vertices(ORIGINAL)
    got = [(num(a), num(b)) for a, b in ring]
    want = [('0', '0'), ('1', '0'), ('1', '0.4'), ('0.6', '0.4'), ('0.6', '1'), ('0.2', '1'), ('0.2', '0.6'), ('0', '0.6')]
    check('generator reproduces the 18 September plate vertex-for-vertex', got == want, str(got))

    from astra_hard_tasks import tasks as hard_tasks, REF as HARD_REF
    original_prompt = next(t for t in hard_tasks() if t['id'] == 'c1_polygon_procedural')['prompt']
    check('generator reproduces the 18 September drawing task character-for-character',
          prompt_text(ORIGINAL) == original_prompt)

    # The decisive one: the prompt actually sent must match the one actually sent on 18 September,
    # including the data-level/data-status contract. Without it no contour carries a level and the
    # scorer sees nothing to measure.
    shipped = json.loads((HARD_REF / 'tasks.json').read_text())
    shipped_prompt = next(t for t in shipped['tasks'] if t['id'] == 'c1_polygon_procedural')['prompt']
    check('the manifest prompt matches the 18 September manifest prompt character-for-character',
          full_prompt(ORIGINAL) == shipped_prompt)
    check('every manifest prompt requests data-level and data-status',
          all('data-level' in t['prompt'] and 'data-status' in t['prompt']
              for t in json.loads((out / 'tasks.json').read_text())['tasks']))

    check('re-entrant corners match the original prompt',
          [(num(a), num(b)) for a, b in reentrant(ORIGINAL)] == [('0.6', '0.4'), ('0.2', '0.6')])

    manifest = json.loads((out / 'tasks.json').read_text())
    ids = [t['id'] for t in manifest['tasks']]
    check('instance ids are unique', len(ids) == len(set(ids)), f'{len(ids)} instances')
    check('the original failing plate is in the benchmark',
          any(t['is_original_failing_plate'] for t in manifest['tasks']))
    check('control tier has no re-entrant corner',
          all(t['reentrant_corners'] == 0 for t in manifest['tasks'] if t['tier'] == 'control'))
    check('difficulty axis is monotone in the tier',
          all(t['reentrant_corners'] == t['n_columns'] - 1 for t in manifest['tasks']))
    check('every re-entrant corner is declared singular, so no score depends on it',
          all(all(c in t['singular'] for c in t['reentrant']) for t in manifest['tasks']))
    check('both hot/cold corners are declared singular in every instance',
          all(all(c in t['singular'] for c in HOT_COLD) for t in manifest['tasks']))

    audit = json.loads((out / 'reference-audit.json').read_text())
    worst = max(r['max_abs_difference_C_excluding_singular'] for r in audit['rows'] if r['admitted'])
    check('every admitted reference is far tighter than the scoring tolerance',
          worst <= audit['admission_limit_C'], f'worst refinement difference {worst:.5f} C '
          f'vs limit {audit["admission_limit_C"]:.3f} C vs tolerance {TOLERANCE_PP / 100 * FIELD_RANGE} C')

    # The reference must reproduce the boundary conditions it claims.
    bad_hot, bad_cold = [], []
    for t in manifest['tasks']:
        z = np.load(ROOT / t['reference_file'])
        f, x, y = z['field'], z['x'], z['y']
        if abs(f[0, :].max() - 100) > 1e-9 or abs(f[0, :].min() - 100) > 1e-9:
            bad_hot.append(t['id'])
        top = np.nanmax(f[1:, :])
        if top > 100 + 1e-6:
            bad_cold.append(t['id'])
    check('every reference holds the bottom edge at exactly 100 C', not bad_hot, str(bad_hot))
    check('no reference exceeds the hot-edge temperature (maximum principle)', not bad_cold, str(bad_cold))

    # The scorer must call a perfect drawing perfect: emit reference isolines as an SVG and score them.
    worst_self, worst_strict = 0.0, 0.0
    for t in manifest['tasks']:
        z = np.load(ROOT / t['reference_file'])
        svg = reference_svg(z, t)
        worst_self = max(worst_self, diagnostics(svg, t, z)['certified_max_error_pp'])
        worst_strict = max(worst_strict, score_svg(svg, z['x'], z['y'], z['field'], tuple(t['mapping']),
                                                   t['levels'], tolerance_pp=TOLERANCE_PP,
                                                   field_range=t['range'])['max_error_pp'])
    check('the certified metric passes a drawing made from the reference isolines, with headroom',
          worst_self <= TOLERANCE_PP / 2,
          f'worst floor {worst_self:.4f} pp against a {TOLERANCE_PP} pp tolerance')
    check('the strict metric is unreachable here, which is why it does not decide the benchmark',
          worst_strict > TOLERANCE_PP,
          f'a perfect drawing scores {worst_strict:.4f} pp strictly, because isotherms end at the '
          f'corners where the boundary data jumps 0 to 100 C')

    ok = all(c['pass'] for c in checks)
    (out / 'verification.json').write_text(json.dumps({'all_pass': ok, 'checks': checks}, indent=2) + '\n')
    print(('\nALL CHECKS PASS' if ok else '\nVERIFICATION FAILED'))
    return ok


def reference_svg(z, task):
    """Render the reference isolines through the task's own mapping: a positive control for the scorer."""
    from fd_reference import marching_squares
    ax, bx, ay, by = task['mapping']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">',
             '<g data-field="T" data-status="solved">']
    for lv in task['levels']:
        for x0, y0, x1, y1 in marching_squares(z['x'], z['y'], z['field'], lv):
            parts.append(f'<polyline data-level="{lv}" fill="none" stroke="#b00" stroke-width="1" '
                         f'points="{bx + ax * x0:.4f},{by + ay * y0:.4f} {bx + ax * x1:.4f},{by + ay * y1:.4f}"/>')
    parts += ['</g>', '</svg>']
    return ''.join(parts)


# ----------------------------------------------------------------------------- api
def api_key():
    key = os.environ.get('OPENAI_API_KEY')
    if key:
        return key
    for line in (ROOT.parent / '.env').read_text().splitlines():
        if line.startswith('OPENAI_API_KEY='):
            return line.split('=', 1)[1].strip().strip('"\'')
    raise SystemExit('OPENAI_API_KEY is not set')


def run(out, model='gpt-6-astra', effort='medium', cap=20000, samples=3, workers=4, data=DATA):
    """Billable. Independent fresh-context samples per instance; resumes without re-billing."""
    key = api_key()
    manifest = json.loads((data / 'tasks.json').read_text())
    template = TEMPLATE.read_text()
    out.mkdir(parents=True, exist_ok=True)
    protocol = {'benchmark': manifest['benchmark'], 'model': model, 'endpoint': ENDPOINT,
                'reasoning_effort': effort, 'max_completion_tokens': cap, 'samples_per_task': samples,
                'template_sha256': hashlib.sha256(template.encode()).hexdigest(),
                'tasks_sha256': hashlib.sha256((data / 'tasks.json').read_bytes()).hexdigest(), 'store': False}
    path = out / 'protocol.json'
    if path.exists() and {k: json.loads(path.read_text()).get(k) for k in protocol} != protocol:
        raise SystemExit('Existing output used a different protocol; use a fresh --output')
    path.write_text(json.dumps(dict(protocol, created_utc=datetime.now(timezone.utc).isoformat()), indent=2) + '\n')

    jobs = [(t, s) for t in manifest['tasks'] for s in range(samples)]

    def one(job):
        task, sample = job
        folder = out / task['id'] / f'sample-{sample}'
        if (folder / 'result.json').exists() and json.loads((folder / 'result.json').read_text()).get('status') == 'completed':
            print('SKIP', task['id'], sample, flush=True)
            return
        folder.mkdir(parents=True, exist_ok=True)
        payload = {'model': model, 'messages': [{'role': 'user', 'content': template.replace('{prompt}', task['prompt'])}],
                   'reasoning_effort': effort, 'max_completion_tokens': cap, 'store': False}
        (folder / 'request.json').write_text(json.dumps(payload, indent=2) + '\n')
        result = {'id': task['id'], 'sample': sample, 'status': 'started',
                  'started_utc': datetime.now(timezone.utc).isoformat()}
        started = time.perf_counter()
        request = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
                                         headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        print('START', task['id'], sample, flush=True)
        try:
            with urllib.request.urlopen(request, timeout=1800) as response:
                raw = json.load(response)
            (folder / 'response.json').write_text(json.dumps(raw, indent=2) + '\n')
            choice = raw['choices'][0]
            text = choice['message'].get('content') or ''
            (folder / 'response.txt').write_text(text)
            svg = re.search(r'<svg\b.*?</svg>', text, re.DOTALL | re.IGNORECASE)
            if svg:
                (folder / 'output.svg').write_text(svg.group())
            result.update(status='completed', model=raw.get('model'), response_id=raw.get('id'),
                          usage=raw.get('usage'), finish_reason=choice.get('finish_reason'),
                          has_svg=bool(svg), output_chars=len(text))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors='replace').replace(key, '[REDACTED]')
            result.update(status='api_error', http_status=exc.code,
                          error=re.sub(r'sk-[A-Za-z0-9_-]+', '[REDACTED]', body)[:1000])
        except Exception as exc:
            result.update(status='client_error', error_type=type(exc).__name__,
                          error=str(exc).replace(key, '[REDACTED]')[:1000])
        result['wall_seconds'] = time.perf_counter() - started
        (folder / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print('END', task['id'], sample, result['status'], result.get('finish_reason'), result.get('has_svg'), flush=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, jobs))


RESPONSES_ENDPOINT = 'https://api.openai.com/v1/responses'
ASSIST_NOTE = ('\n\nYou may call probe_temperature at most {calls} times, with at most {probes} points per '
               'call, to read the exact steady-state temperature at plate points you choose. Points outside '
               'the plate return null. It never returns a contour or a solution path. Use the readings to '
               'place the isotherms, then output only the SVG document.')

PROBE_TOOL = {'type': 'function', 'name': 'probe_temperature',
              'description': ('Exact steady-state temperature in degrees C at chosen plate points. '
                              'Returns null outside the plate. No contours or solution paths are supplied.'),
              'parameters': {'type': 'object', 'required': ['points'],
                             'properties': {'points': {'type': 'array',
                                 'description': 'Plate coordinates [[x, y], ...].',
                                 'items': {'type': 'array', 'items': {'type': 'number'}}}}},
              'strict': False}


def run_assisted(out, model='gpt-6-astra', effort='medium', cap=20000, samples=3, workers=3,
                 calls=4, probes=256, data=DATA):
    """Billable second arm: the same drawings, but the model may read the field it has to draw.

    Zero-shot, a failure cannot separate "cannot compute this field" from "cannot draw it". Here the field
    is available on request, so a drawing that is still wrong is wrong about geometry, not about physics.
    Function tools require the Responses endpoint for this model, so this arm uses it; the zero-shot arm
    keeps the 18 September Chat Completions protocol unchanged for comparability.
    """
    key = api_key()
    manifest = json.loads((data / 'tasks.json').read_text())
    template = TEMPLATE.read_text()
    out.mkdir(parents=True, exist_ok=True)
    protocol = {'benchmark': manifest['benchmark'], 'arm': 'tool-assisted', 'model': model,
                'endpoint': RESPONSES_ENDPOINT, 'reasoning_effort': effort, 'max_output_tokens': cap,
                'samples_per_task': samples, 'tool_calls_allowed': calls, 'points_per_call': probes,
                'tool': PROBE_TOOL,
                'template_sha256': hashlib.sha256(template.encode()).hexdigest(),
                'tasks_sha256': hashlib.sha256((data / 'tasks.json').read_bytes()).hexdigest(), 'store': False}
    path = out / 'protocol.json'
    if path.exists() and {k: json.loads(path.read_text()).get(k) for k in protocol} != protocol:
        raise SystemExit('Existing output used a different protocol; use a fresh --output')
    path.write_text(json.dumps(dict(protocol, created_utc=datetime.now(timezone.utc).isoformat()), indent=2) + '\n')

    def one(job):
        task, sample = job
        folder = out / task['id'] / f'sample-{sample}'
        if (folder / 'result.json').exists() and json.loads((folder / 'result.json').read_text()).get('status') == 'completed':
            print('SKIP', task['id'], sample, flush=True)
            return
        folder.mkdir(parents=True, exist_ok=True)
        z = np.load(ROOT / task['reference_file'])
        prompt = template.replace('{prompt}', task['prompt']) + ASSIST_NOTE.format(calls=calls, probes=probes)
        messages = [{'role': 'user', 'content': prompt}]
        result = {'id': task['id'], 'sample': sample, 'status': 'started', 'tool_calls_used': 0,
                  'points_probed': 0, 'usage': {}, 'started_utc': datetime.now(timezone.utc).isoformat()}
        started, text, used = time.perf_counter(), '', 0
        print('START', task['id'], sample, flush=True)
        try:
            for turn in range(calls + 2):
                payload = {'model': model, 'input': messages, 'reasoning': {'effort': effort},
                           'max_output_tokens': cap, 'store': False,
                           'include': ['reasoning.encrypted_content']}
                if used < calls:
                    payload.update(tools=[PROBE_TOOL], parallel_tool_calls=False)
                (folder / f'request-{turn}.json').write_text(json.dumps(payload, indent=2) + '\n')
                request = urllib.request.Request(RESPONSES_ENDPOINT, data=json.dumps(payload).encode(),
                                                 headers={'Content-Type': 'application/json',
                                                          'Authorization': 'Bearer ' + key})
                with urllib.request.urlopen(request, timeout=1800) as response:
                    raw = json.load(response)
                (folder / f'response-{turn}.json').write_text(json.dumps(raw, indent=2) + '\n')
                for k, v in (raw.get('usage') or {}).items():
                    if isinstance(v, int):
                        result['usage'][k] = result['usage'].get(k, 0) + v
                if raw.get('status') != 'completed':
                    result.update(status='incomplete_excluded', finish_reason=raw.get('status'))
                    break
                messages.extend(raw['output'])
                requested = [v for v in raw['output'] if v['type'] == 'function_call']
                if not requested:
                    text = ''.join(c['text'] for v in raw['output'] if v['type'] == 'message'
                                   for c in v['content'] if c['type'] == 'output_text')
                    result['finish_reason'] = 'stop'
                    break
                for call in requested:
                    try:
                        pts = json.loads(call['arguments'] or '{}').get('points')
                    except json.JSONDecodeError:
                        pts = None
                    if used >= calls:
                        payload_out = {'error': f'tool budget of {calls} calls is exhausted; output the SVG now'}
                    elif not isinstance(pts, list) or not pts:
                        payload_out = {'error': 'arguments must be JSON with a non-empty points array'}
                    elif len(pts) > probes:
                        payload_out = {'error': f'at most {probes} points per call; {len(pts)} were sent'}
                    else:
                        arr = np.asarray(pts, float).reshape(-1, 2)
                        values = interpolate_grid(z['x'], z['y'], z['field'], arr)
                        payload_out = {'temperatures_C': [None if not np.isfinite(v) else round(float(v), 6)
                                                          for v in values]}
                        used += 1
                        result['points_probed'] += len(arr)
                    result['tool_calls_used'] = used
                    (folder / f'tool-{turn}-{used}.json').write_text(
                        json.dumps({'arguments': call['arguments'][:200000], 'result': payload_out}, indent=2) + '\n')
                    messages.append({'type': 'function_call_output', 'call_id': call['call_id'],
                                     'output': json.dumps(payload_out)})
            else:
                result['finish_reason'] = 'tool_loop_guard'
            if result['status'] == 'started':
                (folder / 'response.txt').write_text(text)
                svg = re.search(r'<svg\b.*?</svg>', text, re.DOTALL | re.IGNORECASE)
                if svg:
                    (folder / 'output.svg').write_text(svg.group())
                result.update(status='completed', model=raw.get('model'), response_id=raw.get('id'),
                              has_svg=bool(svg), output_chars=len(text))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors='replace').replace(key, '[REDACTED]')
            result.update(status='api_error', http_status=exc.code,
                          error=re.sub(r'sk-[A-Za-z0-9_-]+', '[REDACTED]', body)[:1000])
        except Exception as exc:
            result.update(status='client_error', error_type=type(exc).__name__,
                          error=str(exc).replace(key, '[REDACTED]')[:1000])
        result['wall_seconds'] = time.perf_counter() - started
        (folder / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print('END', task['id'], sample, result['status'], result.get('finish_reason'),
              result.get('has_svg'), f"probes={result['points_probed']}", flush=True)

    jobs = [(t, s) for t in manifest['tasks'] for s in range(samples)]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, jobs))


# ----------------------------------------------------------------------------- scoring
def diagnostics(svg, task, z):
    """Certified error with singular neighbourhoods removed, at the scoring radius and a wider one.

    Removing those neighbourhoods can only help the model, so a failure measured here is conservative:
    it cannot be attributed to the reference, which is certified by grid refinement exactly there.
    """
    ax, bx, ay, by = task['mapping']
    matrix = np.array([[1 / ax, 0, -bx / ax], [0, 1 / ay, -by / ay], [0, 0, 1.]])
    try:
        contours, _ = extract_contours(svg, matrix, min(np.diff(z['x']).min(), np.diff(z['y']).min()) / 2)
    except ValueError:
        return {}
    out = {'impossible_boundary_contact': []}
    for radius, key in ((EXCLUDE_R, 'certified'), (0.10, 'certified_r10')):
        worst, collected = 0.0, []
        kept_total, finite_total, per_level = 0, 0, {}
        for c in contours:
            if c.level not in task['levels']:
                continue
            pts = c.points
            keep = np.ones(len(pts), bool)
            for sx, sy in task['singular']:
                keep &= np.hypot(pts[:, 0] - sx, pts[:, 1] - sy) > radius
            values = interpolate_grid(z['x'], z['y'], z['field'], pts[keep])
            finite = np.isfinite(values)
            kept_total += int(keep.sum())
            finite_total += int(finite.sum())
            per_level[c.level] = per_level.get(c.level, 0) + int(finite.sum())
            if finite.any():
                err = np.abs(values[finite] - c.level) / task['range'] * 100
                worst = max(worst, float(err.max()))
                collected.append(err)
            if radius == EXCLUDE_R:
                # A sub-100 C isotherm may not touch the 100 C edge away from its two singular corners.
                near_hot = keep & (np.abs(pts[:, 1]) <= 0.005)
                if c.level < 100 and near_hot.any():
                    out['impossible_boundary_contact'].append(
                        {'level': c.level, 'points_on_hot_edge': int(near_hot.sum())})
        out[f'{key}_max_error_pp'] = worst if collected else None
        out[f'{key}_mean_error_pp'] = float(np.concatenate(collected).mean()) if collected else None
        out[f'{key}_samples'] = int(sum(len(e) for e in collected))
        if radius == EXCLUDE_R:
            # Samples that fall outside the plate are dropped by the interpolator, so a drawing could
            # otherwise "pass" by putting its contours where nothing can be measured. Track the share.
            out['certified_outside_domain_fraction'] = (
                float(1 - finite_total / kept_total) if kept_total else 1.0)
            out['certified_samples_per_level'] = {str(k): v for k, v in sorted(per_level.items())}
    return out


def score(run_dir, data=DATA):
    manifest = json.loads((data / 'tasks.json').read_text())
    rows = []
    for task in manifest['tasks']:
        z = np.load(ROOT / task['reference_file'])
        for folder in sorted((run_dir / task['id']).glob('sample-*')) if (run_dir / task['id']).exists() else []:
            result = json.loads((folder / 'result.json').read_text()) if (folder / 'result.json').exists() else {'status': 'missing'}
            svg = (folder / 'output.svg').read_text() if (folder / 'output.svg').exists() else ''
            row = {'id': task['id'], 'tier': task['tier'], 'reentrant_corners': task['reentrant_corners'],
                   'sample': int(folder.name.split('-')[1]), 'status': result.get('status'),
                   'finish_reason': result.get('finish_reason'), 'has_svg': bool(svg),
                   'usage': result.get('usage'), 'wall_seconds': result.get('wall_seconds'),
                   'data_status': sorted(set(re.findall(r'data-status="([^"]*)"', svg)))}
            if not svg:
                row['outcome'] = 'no_svg'
            elif result.get('status') != 'completed' or result.get('finish_reason') != 'stop':
                row['outcome'] = 'incomplete'          # truncation is excluded, never scored as a failure
            else:
                s = score_svg(svg, z['x'], z['y'], z['field'], tuple(task['mapping']), task['levels'],
                              tolerance_pp=TOLERANCE_PP, field_range=task['range'])
                row.update({k: s.get(k) for k in ('mean_error_pp', 'max_error_pp',
                                                  'invalid_points', 'missing_levels', 'issues')})
                row['strict_geometry_pass'] = s.get('geometry_pass')   # 18 September criterion, kept for continuity
                row.update(diagnostics(svg, task, z))
                # The benchmark decides on the certified metric only: singular neighbourhoods removed,
                # where grid refinement shows the reference is an order of magnitude inside tolerance.
                certified = row.get('certified_max_error_pp')
                measured = row.get('certified_samples_per_level') or {}
                # Not `invalid_points == 0`: every isotherm here legitimately ends at the two singular
                # corners, and the strict scorer flags those boundary-adjacent samples even on a drawing
                # made from the reference isolines. Require instead that the contours are measurable.
                row['certified_pass'] = bool(
                    certified is not None and certified <= TOLERANCE_PP
                    and not s.get('missing_levels')
                    and all(measured.get(str(float(lv)), measured.get(str(lv), 0)) > 0 for lv in task['levels'])
                    and (row.get('certified_outside_domain_fraction') or 0) <= 0.05)
                row['outcome'] = 'pass' if row['certified_pass'] else 'fail'
            rows.append(row)
            print(f"{row['id']:22s} s{row['sample']} {row['outcome']:6s} "
                  f"certMean={row.get('certified_mean_error_pp')} certMax={row.get('certified_max_error_pp')} "
                  f"strict={row.get('strict_geometry_pass')}", flush=True)

    scored = [r for r in rows if r['outcome'] in ('pass', 'fail')]
    by_tier = {}
    for r in scored:
        t = by_tier.setdefault(r['tier'], {'scored': 0, 'pass': 0, 'fail': 0, 'mean_error_pp': [],
                                           'reentrant_corners': r['reentrant_corners']})
        t['scored'] += 1
        t[r['outcome']] += 1
        t['mean_error_pp'].append(r['certified_mean_error_pp'])
    for t in by_tier.values():
        vals = [v for v in t.pop('mean_error_pp') if v is not None]
        t['median_certified_mean_error_pp'] = float(np.median(vals)) if vals else None

    # An instance is "confirmed hard" only with >=3 completed, scored, independently failing samples.
    confirmed = []
    for task in manifest['tasks']:
        got = [r for r in scored if r['id'] == task['id']]
        fails = [r for r in got if r['outcome'] == 'fail']
        if len(fails) >= 3 and len(fails) == len(got):
            confirmed.append({'id': task['id'], 'tier': task['tier'],
                              'reentrant_corners': task['reentrant_corners'],
                              'samples_scored': len(got), 'samples_failed': len(fails),
                              'median_certified_mean_error_pp': float(np.median(
                                  [r['certified_mean_error_pp'] for r in fails])),
                              'worst_certified_max_error_pp': max(
                                  (r['certified_max_error_pp'] or 0) for r in fails),
                              'worst_certified_max_error_pp_r10': max(
                                  (r['certified_r10_max_error_pp'] or 0) for r in fails),
                              'samples_with_impossible_boundary_contact': sum(
                                  1 for r in fails if r.get('impossible_boundary_contact'))})

    usage = {}
    for r in rows:
        for k, v in (r.get('usage') or {}).items():
            if isinstance(v, int):
                usage[k] = usage.get(k, 0) + v
    summary = {'benchmark': manifest['benchmark'], 'scorer': 'svgpatchlab.eval.field_fidelity.score_svg',
               'tolerance_pp': TOLERANCE_PP, 'attempts': len(rows), 'scored': len(scored),
               'incomplete_or_no_svg': sum(r['outcome'] in ('incomplete', 'no_svg') for r in rows),
               'geometry_pass': sum(r['outcome'] == 'pass' for r in scored),
               'geometry_fail': sum(r['outcome'] == 'fail' for r in scored),
               'by_tier': by_tier, 'confirmed_hard_instances': confirmed,
               'admission_rule': ('three or more completed samples, all exceeding the 0.5 pp tolerance on the '
                                  'certified metric; truncated, errored and SVG-less attempts are excluded rather '
                                  'than counted as failures'),
               'usage': usage,
               'estimated_cost_usd': round(usage.get('prompt_tokens', 0) / 1e6 * PRICE_INPUT
                                           + usage.get('completion_tokens', 0) / 1e6 * PRICE_OUTPUT, 4),
               'note': 'Sampled geometric contour audit against a refinement-certified reference; not a rendered-image review.',
               'rows': rows}
    (run_dir / 'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, indent=2))
    return summary


def figures(run_dir, out_dir, data=DATA):
    """Two panels: the error ladder against the certified floor, and the worst instance overlaid."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from fd_reference import marching_squares

    manifest = json.loads((data / 'tasks.json').read_text())
    summary = json.loads((run_dir / 'summary.json').read_text())
    by_id = {t['id']: t for t in manifest['tasks']}
    scored = [r for r in summary['rows'] if r['outcome'] in ('pass', 'fail')]
    out_dir.mkdir(parents=True, exist_ok=True)

    # Floor: the same metric applied to a drawing made from the reference isolines.
    floor = []
    for t in manifest['tasks']:
        z = np.load(ROOT / t['reference_file'])
        floor.append(diagnostics(reference_svg(z, t), t, z)['certified_mean_error_pp'])
    floor = float(np.max(floor))

    fig, (a, b) = plt.subplots(1, 2, figsize=(12.6, 5.0))
    xs = np.array([r['reentrant_corners'] for r in scored], float)
    ys = np.array([r['certified_mean_error_pp'] for r in scored], float)
    ok = np.array([r['outcome'] == 'pass' for r in scored])
    jitter = (np.arange(len(xs)) % 5 - 2) * 0.04
    a.scatter(xs[ok] + jitter[ok], ys[ok], s=46, c='#1a7f37', marker='o', label='pass', zorder=3)
    a.scatter(xs[~ok] + jitter[~ok], ys[~ok], s=52, c='#b3261e', marker='X', label='fail', zorder=3)
    for k in sorted(set(xs)):
        m = xs == k
        a.plot([k - 0.22, k + 0.22], [np.median(ys[m])] * 2, color='#333', lw=2.2, zorder=4)
    a.axhline(TOLERANCE_PP, color='#b3261e', ls='--', lw=1.3)
    a.axhline(floor, color='#1a7f37', ls=':', lw=1.3)
    a.text(0.02, TOLERANCE_PP * 1.12, f'tolerance {TOLERANCE_PP} pp', color='#b3261e', fontsize=9,
           transform=a.get_yaxis_transform())
    a.text(0.02, floor * 1.18, f'reference floor {floor:.4f} pp', color='#1a7f37', fontsize=9,
           transform=a.get_yaxis_transform())
    a.set_yscale('log'); a.set_xticks(sorted(set(int(v) for v in xs)))
    a.set_xlabel('re-entrant corners in the plate')
    a.set_ylabel('certified mean contour error (pp of field range)')
    a.set_title('Isotherm accuracy against domain complexity')
    a.legend(loc='upper left', frameon=False); a.grid(alpha=0.25, which='both')

    worst = max(scored, key=lambda r: r['certified_mean_error_pp'] or 0)
    task = by_id[worst['id']]
    z = np.load(ROOT / task['reference_file'])
    ax_, bx_, ay_, by_ = task['mapping']
    ring = np.array(task['vertices'] + [task['vertices'][0]], float)
    b.plot(ring[:, 0], ring[:, 1], color='#111', lw=1.6, zorder=5)
    for lv in task['levels']:
        segs = marching_squares(z['x'], z['y'], z['field'], lv)
        for x0, y0, x1, y1 in segs:
            b.plot([x0, x1], [y0, y1], color='#1a7f37', lw=1.0, zorder=2)
    svg = (run_dir / worst['id'] / f"sample-{worst['sample']}" / 'output.svg').read_text()
    matrix = np.array([[1 / ax_, 0, -bx_ / ax_], [0, 1 / ay_, -by_ / ay_], [0, 0, 1.]])
    contours, _ = extract_contours(svg, matrix, min(np.diff(z['x']).min(), np.diff(z['y']).min()) / 2)
    for c in contours:
        if c.level in task['levels']:
            b.plot(c.points[:, 0], c.points[:, 1], color='#b3261e', lw=1.0, alpha=0.85, zorder=3)
    for sx, sy in task['singular']:
        b.add_patch(plt.Circle((sx, sy), EXCLUDE_R, color='#888', alpha=0.22, zorder=1))
    b.set_aspect('equal'); b.set_xlim(-0.06, 1.06); b.set_ylim(-0.06, 1.06)
    b.set_title(f"{worst['id']} sample {worst['sample']}: reference (green) and Astra (red)")
    b.set_xlabel('grey discs are the excluded singular neighbourhoods')
    fig.tight_layout()
    path = out_dir / 'polyheat_results.png'
    fig.savefig(path, dpi=170); plt.close(fig)
    print('wrote', path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    g = sub.add_parser('generate')
    g.add_argument('--seed', type=int, default=20260922)
    g.add_argument('--force', action='store_true', help='re-solve every reference instead of reusing stored ones')
    sub.add_parser('verify')
    r = sub.add_parser('run')
    r.add_argument('--output', type=Path, required=True)
    r.add_argument('--model', default='gpt-6-astra')
    r.add_argument('--effort', default='medium')
    r.add_argument('--cap', type=int, default=20000)
    r.add_argument('--samples', type=int, default=3)
    r.add_argument('--workers', type=int, default=4)
    ra = sub.add_parser('run-assisted')
    ra.add_argument('--output', type=Path, required=True)
    ra.add_argument('--model', default='gpt-6-astra')
    ra.add_argument('--effort', default='medium')
    ra.add_argument('--cap', type=int, default=20000)
    ra.add_argument('--samples', type=int, default=3)
    ra.add_argument('--workers', type=int, default=3)
    ra.add_argument('--calls', type=int, default=4)
    ra.add_argument('--probes', type=int, default=256)
    s = sub.add_parser('score'); s.add_argument('--output', type=Path, required=True)
    fg = sub.add_parser('figures')
    fg.add_argument('--output', type=Path, required=True)
    fg.add_argument('--figures', type=Path, default=ROOT / 'paper/figures')
    a = p.parse_args()
    if a.cmd == 'generate':
        generate(seed=a.seed, reuse=not a.force)
    elif a.cmd == 'verify':
        raise SystemExit(0 if verify() else 1)
    elif a.cmd == 'run':
        run(a.output, a.model, a.effort, a.cap, a.samples, a.workers)
    elif a.cmd == 'run-assisted':
        run_assisted(a.output, a.model, a.effort, a.cap, a.samples, a.workers, a.calls, a.probes)
    elif a.cmd == 'figures':
        figures(a.output, a.figures)
    else:
        score(a.output)


if __name__ == '__main__':
    main()
