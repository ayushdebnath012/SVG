"""Harder drawing tasks for direct Astra: build references, call the API, score, plot.

Twelve engineering_v4-style tasks in five classes (Dirichlet, Robin sweep,
unbounded, elasticity, ill-posed), each with an independent reference computed
here: analytic anchors, red-black SOR finite differences for the textbook and
procedural Dirichlet cases, and scikit-fem P2 for the Robin sweep. Drawings are
scored by the repaired sampled-contour evaluator with the same 0.5 pp tolerance
as the historical re-audit; ill-posed tasks are scored on disclosure.

Subcommands: references | run (billable) | score | figures. `run` resumes and
never re-bills a task whose response exists.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from svgpatchlab.eval.field_fidelity import extract_contours, score_svg  # noqa: E402
from fd_reference import grid as fd_grid, sor  # noqa: E402

REF = ROOT / 'runs/reference-v4'
TEMPLATE = ROOT / 'src/svgpatchlab/prompt_templates/generation_v1.txt'
ENDPOINT = 'https://api.openai.com/v1/chat/completions'
PRICE_INPUT, PRICE_OUTPUT = 10.0, 50.0
STATUS_LINE = ('Wrap every contour in one <g data-field="{field}" data-status="..."> group and set data-status '
               'honestly to one of solved, estimated, illustrative or ill-posed. Draw every contour as its own '
               '<path> or <polyline> carrying a data-level attribute with its numeric level and label it. '
               'Contours must satisfy the boundary conditions exactly.')


# ----------------------------------------------------------------------------- references
def analytic(x0, x1, y0, y1, n, func, mask=None):
    x, y = np.linspace(x0, x1, n), np.linspace(y0, y1, n)
    X, Y = np.meshgrid(x, y)
    f = func(X, Y).astype(float)
    if mask is not None:
        f[mask(X, Y)] = np.nan
    return x, y, f


def robin_square(bi, n=128, grid_n=321):
    """Unit square, left edge 100, other edges convective with Biot number bi (ambient 0), P2 FEM."""
    from skfem import MeshTri, Basis, FacetBasis, ElementTriP2, BilinearForm, asm, condense, solve
    from skfem.models.poisson import laplace
    mesh = MeshTri.init_tensor(np.linspace(0, 1, n + 1), np.linspace(0, 1, n + 1))
    basis = Basis(mesh, ElementTriP2())
    facets = mesh.facets_satisfying(lambda p: np.isclose(p[0], 1) | np.isclose(p[1], 0) | np.isclose(p[1], 1))
    boundary = FacetBasis(mesh, basis.elem, facets=facets)

    @BilinearForm
    def robin(u, v, w):
        return bi * u * v
    R = asm(robin, boundary)
    A = asm(laplace, basis) + R
    D = basis.get_dofs(lambda p: np.isclose(p[0], 0)).all()
    prescribed = basis.zeros()
    prescribed[D] = 100
    u = solve(*condense(A, basis.zeros(), x=prescribed, D=D))
    residual = A @ u
    balance = abs(float(np.sum(residual[D])) - float(np.sum(R @ u))) / max(abs(float(np.sum(R @ u))), 1e-30)
    x = y = np.linspace(0, 1, grid_n)
    X, Y = np.meshgrid(x, y)
    pts = np.vstack([X.ravel(), Y.ravel()])
    values = np.concatenate([basis.probes(pts[:, i:i + 512]) @ u for i in range(0, pts.shape[1], 512)])
    return x, y, values.reshape(X.shape), {'elements': int(mesh.nelements), 'dofs': int(basis.N),
                                           'discrete_heat_balance_relative': balance}


def fd_polygon(inside, hot, n_per_unit=160):
    """Laplace on a rectilinear polygon inside the unit square; `hot` marks the 100-degree boundary nodes."""
    x, y, X, Y, dx = fd_grid(0, 1, 0, 1, n_per_unit)
    domain = inside(X, Y)
    f = np.zeros_like(X)
    fixed = ~domain
    f[hot(X, Y) & domain] = 100.0
    fixed[hot(X, Y) & domain] = True
    # Every domain node adjacent to the exterior is boundary; those not hot stay at 0.
    exterior = ~domain
    edge = domain & (np.roll(exterior, 1, 0) | np.roll(exterior, -1, 0) | np.roll(exterior, 1, 1) | np.roll(exterior, -1, 1))
    edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
    fixed |= edge
    f, iterations = sor(f, fixed, np.zeros_like(f), dx)
    f[~domain] = np.nan
    return x, y, f, {'sor_iterations': int(iterations), 'grid_per_unit': n_per_unit}


def tasks():
    """Task definitions: prompt text, levels, drawing mapping, declared field range, reference builder."""
    T = []
    # Analytic fields stay valid on and beyond the boundaries, so only true singularities are masked;
    # a drawn boundary circle tagged with its level is then scored rather than counted invalid.
    ring = lambda X, Y: np.hypot(X, Y) < 0.02  # noqa: E731
    T.append(dict(id='c1_annulus_anchor', cls='C1 Dirichlet', tier='anchor', field='T', unit='C', levels=[20, 40, 60, 80], range=100,
        mapping=(400, 500, -400, 500), reference=lambda: analytic(-1, 1, -1, 1, 401,
            lambda X, Y: 100 * np.log(1 / np.maximum(np.hypot(X, Y), 1e-9)) / np.log(4), mask=ring),
        prompt='Steady two-dimensional heat conduction (Laplace equation) in an annular plate centred at the origin with inner radius 0.25 and outer radius 1. The inner circle is held at 100 C and the outer circle at 0 C. Draw both circles and the isotherms at 20, 40, 60 and 80 C. Use viewBox="0 0 1000 1000". Map plate coordinates to drawing coordinates as X = 500 + 400 x and Y = 500 - 400 y.'))
    T.append(dict(id='c1_sine_top_anchor', cls='C1 Dirichlet', tier='anchor', field='T', unit='C', levels=[10, 20, 40, 60, 80], range=100,
        mapping=(800, 100, -800, 900), reference=lambda: analytic(0, 1, 0, 1, 401,
            lambda X, Y: 100 * np.sinh(np.pi * Y) * np.sin(np.pi * X) / np.sinh(np.pi)),
        prompt='Steady two-dimensional heat conduction (Laplace equation) in the unit square plate [0,1]x[0,1]. The top edge y = 1 has the temperature distribution T = 100 sin(pi x) C; the left, right and bottom edges are held at 0 C. Draw the plate outline and the isotherms at 10, 20, 40, 60 and 80 C. Use viewBox="0 0 1000 1000". Map plate coordinates to drawing coordinates as X = 100 + 800 x and Y = 900 - 800 y.'))
    T.append(dict(id='c1_L_shape_textbook', cls='C1 Dirichlet', tier='textbook', field='T', unit='C', levels=[10, 20, 30, 40, 50, 60, 80], range=100, singular=[[0, 0], [0, 1]],
        mapping=(800, 100, -800, 900), reference=lambda: fd_polygon(lambda X, Y: ~((X > 0.5) & (Y > 0.5)), lambda X, Y: X <= 0),
        prompt="Steady two-dimensional heat conduction (Laplace's equation, no generation) in an L-shaped plate: the unit square [0,1]x[0,1] with the top-right quadrant [0.5,1]x[0.5,1] removed. The left edge x = 0 is held at 100 C; every other boundary, including the two re-entrant edges of the notch, is held at 0 C. Draw the plate outline and the isotherms at 10, 20, 30, 40, 50, 60 and 80 C, with correct crowding at the re-entrant corner (0.5, 0.5). Use viewBox=\"0 0 1000 1000\". Map plate coordinates to drawing coordinates as X = 100 + 800 x and Y = 900 - 800 y."))
    poly_inside = lambda X, Y: ~(((X > 0.6) & (Y > 0.4)) | ((X < 0.2) & (Y > 0.6)))  # noqa: E731
    T.append(dict(id='c1_polygon_procedural', cls='C1 Dirichlet', tier='procedural', field='T', unit='C', levels=[10, 20, 40, 60, 80], range=100, singular=[[0, 0], [1, 0]],
        mapping=(800, 100, -800, 900), reference=lambda: fd_polygon(poly_inside, lambda X, Y: Y <= 0),
        prompt='Steady two-dimensional heat conduction (Laplace equation) in a rectilinear plate with vertices, in order, (0,0), (1,0), (1,0.4), (0.6,0.4), (0.6,1), (0.2,1), (0.2,0.6), (0,0.6). The bottom edge y = 0 is held at 100 C; every other edge is held at 0 C. Draw the plate outline and the isotherms at 10, 20, 40, 60 and 80 C, with correct crowding at the two re-entrant corners (0.6, 0.4) and (0.2, 0.6). Use viewBox="0 0 1000 1000". Map plate coordinates to drawing coordinates as X = 100 + 800 x and Y = 900 - 800 y.'))
    for bi, levels in ((0.1, [92, 94, 96, 98]), (1.0, [50, 60, 70, 80, 90]), (10.0, [5, 10, 20, 40, 60, 80])):
        T.append(dict(id=f'c2_robin_bi{bi:g}'.replace('.', 'p'), cls='C2 Robin', tier='textbook', field='T', unit='C', levels=levels, range=100, singular=[[0, 0], [0, 1]],
            mapping=(800, 100, -800, 900), reference=lambda bi=bi: robin_square(bi),
            prompt=f'Steady two-dimensional heat conduction (Laplace equation) in the unit square plate [0,1]x[0,1] with thermal conductivity k. The left edge x = 0 is held at 100 C. The right, top and bottom edges lose heat by convection to an ambient at 0 C with heat transfer coefficient h, so that on those edges -k dT/dn = h T with outward normal n and Biot number h L / k = {bi:g} for the side length L = 1. Draw the plate outline and the isotherms at {", ".join(str(l) for l in levels)} C. Use viewBox="0 0 1000 1000". Map plate coordinates to drawing coordinates as X = 100 + 800 x and Y = 900 - 800 y.'))
    charges = lambda X, Y: (np.hypot(X - 0.5, Y) < 0.06) | (np.hypot(X + 0.5, Y) < 0.06)  # noqa: E731
    T.append(dict(id='c3_line_charges_anchor', cls='C3 Unbounded', tier='anchor', field='V', unit='V', levels=[-40, -20, -10, -5, 5, 10, 20, 40], range=80,
        view=[-2.4, 2.4, -2.4, 2.4], mapping=(300, 500, -300, 500), reference=lambda: analytic(-4.5, 4.5, -4.5, 4.5, 901,  # the +-5 V circles reach |x| = 4.0
            lambda X, Y: 20 * np.log(np.hypot(X + 0.5, Y) / np.maximum(np.hypot(X - 0.5, Y), 1e-9)), mask=charges),
        prompt='Two-dimensional electrostatics in free space: two infinitely long parallel line charges of equal magnitude and opposite sign, the positive one through (0.5, 0) and the negative one through (-0.5, 0), with potential V = 20 ln(r_minus / r_plus) volts, where r_plus and r_minus are the distances from the positive and negative lines. The domain is unbounded; the potential is zero on the line x = 0 and at infinity. Draw the equipotentials at -40, -20, -10, -5, 5, 10, 20 and 40 V inside the frame -5/3 <= x <= 5/3, -5/3 <= y <= 5/3, marking both line charges. Use viewBox="0 0 1000 1000". Map physical coordinates to drawing coordinates as X = 500 + 300 x and Y = 500 - 300 y.'))
    body = lambda X, Y: np.hypot(X, Y) < 0.235  # one grid cell inside the cylinder surface  # noqa: E731
    T.append(dict(id='c3_cylinder_flow_anchor', cls='C3 Unbounded', tier='anchor', field='psi', unit='m2/s', levels=[-0.8, -0.6, -0.4, -0.2, 0.2, 0.4, 0.6, 0.8], range=2,
        mapping=(300, 500, -300, 500), reference=lambda: analytic(-5 / 3, 5 / 3, -5 / 3, 5 / 3, 501,
            lambda X, Y: Y * (1 - 0.0625 / np.maximum(X**2 + Y**2, 1e-12)), mask=body),
        prompt='Ideal (potential) flow of a uniform stream of speed U = 1 m/s in the +x direction past a circular cylinder of radius a = 0.25 m centred at the origin, in an unbounded domain. The stream function is psi = U y (1 - a^2 / r^2). Draw the cylinder and the streamlines psi = -0.8, -0.6, -0.4, -0.2, 0.2, 0.4, 0.6 and 0.8 m^2/s inside the frame -5/3 <= x <= 5/3, -5/3 <= y <= 5/3. Streamlines may not cross the cylinder surface. Use viewBox="0 0 1000 1000". Map physical coordinates to drawing coordinates as X = 500 + 300 x and Y = 500 - 300 y.'))

    def kirsch(X, Y, a=0.5):
        r = np.maximum(np.hypot(X, Y), 1e-9)
        th = np.arctan2(Y, X)
        q = (a / r) ** 2
        srr = 0.5 * (1 - q) + 0.5 * (1 - 4 * q + 3 * q * q) * np.cos(2 * th)
        stt = 0.5 * (1 + q) - 0.5 * (1 + 3 * q * q) * np.cos(2 * th)
        srt = -0.5 * (1 + 2 * q - 3 * q * q) * np.sin(2 * th)
        c, s = np.cos(th), np.sin(th)
        sxx = srr * c * c + stt * s * s - 2 * srt * s * c
        syy = srr * s * s + stt * c * c + 2 * srt * s * c
        sxy = (srr - stt) * s * c + srt * (c * c - s * s)
        return np.sqrt(sxx * sxx - sxx * syy + syy * syy + 3 * sxy * sxy)
    T.append(dict(id='c4_kirsch_anchor', cls='C4 Elasticity', tier='anchor', field='sigma_vm', unit='sigma_inf', levels=[0.5, 1.0, 1.5, 2.0, 2.5], range=3,
        mapping=(200, 500, -200, 500), reference=lambda: analytic(-2.5, 2.5, -2.5, 2.5, 501, kirsch, mask=lambda X, Y: np.hypot(X, Y) < 0.48),
        prompt='Plane-stress linear elasticity: an infinite plate with a circular hole of radius a = 0.5 centred at the origin, under remote uniaxial tension sigma_inf applied in the x direction (the classical Kirsch problem). Use the exact Kirsch stress solution. Draw the hole and the contours of the von Mises stress normalised by sigma_inf at the levels 0.5, 1.0, 1.5, 2.0 and 2.5 inside the frame -2.5 <= x <= 2.5, -2.5 <= y <= 2.5, and label the peak stress concentration on the hole. Use viewBox="0 0 1000 1000". Map physical coordinates to drawing coordinates as X = 500 + 200 x and Y = 500 - 200 y.'))
    T.append(dict(id='c6_all_neumann_illposed', cls='C6 Ill-posed', tier='disclosure', field='T', unit='C', levels=[], range=100, mapping=(800, 100, -800, 900), reference=None,
        prompt='Steady two-dimensional heat conduction with no internal generation in the unit square plate [0,1]x[0,1], conductivity k = 1 W/(m K). The left edge receives a uniform heat flux of 200 W/m^2 into the plate, the right edge loses a uniform heat flux of 100 W/m^2, and the top and bottom edges are perfectly insulated. Draw the plate outline and the steady-state isotherms at 20, 40, 60 and 80 C. Use viewBox="0 0 1000 1000". Map plate coordinates to drawing coordinates as X = 100 + 800 x and Y = 900 - 800 y.'))
    T.append(dict(id='c6_overspecified_illposed', cls='C6 Ill-posed', tier='disclosure', field='T', unit='C', levels=[], range=100, mapping=(800, 100, -800, 900), reference=None,
        prompt='Steady two-dimensional heat conduction (Laplace equation) in the unit square plate [0,1]x[0,1], conductivity k = 1 W/(m K). The left edge x = 0 is held at 100 C and at the same time carries a prescribed uniform heat flux of 50 W/m^2 into the plate; the right edge is held at 0 C; the top and bottom edges are insulated. Draw the plate outline and the isotherms at 20, 40, 60 and 80 C satisfying every stated condition. Use viewBox="0 0 1000 1000". Map plate coordinates to drawing coordinates as X = 100 + 800 x and Y = 900 - 800 y.'))
    return T


def build_references(out=REF):
    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for t in tasks():
        entry = {k: t[k] for k in ('id', 'cls', 'tier', 'field', 'unit', 'levels', 'range', 'mapping')}
        entry['singular'] = t.get('singular', [])
        if t.get('view'):
            entry['view'] = t['view']
        entry['prompt'] = t['prompt'] + ' ' + STATUS_LINE.format(field=t['field'])
        if t['reference'] is not None:
            result = t['reference']()
            x, y, f = result[:3]
            meta = result[3] if len(result) > 3 else {'analytic': True}
            np.savez(out / f"{t['id']}.npz", x=x, y=y, field=f)
            entry['reference'] = dict(meta, file=f"runs/reference-v4/{t['id']}.npz", grid=list(f.shape),
                                      field_min=float(np.nanmin(f)), field_max=float(np.nanmax(f)))
            print(f"{t['id']:28s} grid {f.shape} range [{np.nanmin(f):.3f}, {np.nanmax(f):.3f}] {meta}", flush=True)
        else:
            entry['reference'] = None
            print(f"{t['id']:28s} disclosure task, no reference", flush=True)
        manifest.append(entry)
    # Convergence floor for the FEM sweep: coarser mesh against the reference mesh.
    floors = {}
    xs = np.linspace(0, 1, 321)
    X, Y = np.meshgrid(xs, xs)
    away = (np.hypot(X, Y) > 0.05) & (np.hypot(X, Y - 1) > 0.05)
    for bi in (0.1, 1.0, 10.0):
        _, _, fine, _ = robin_square(bi, n=128)
        _, _, finer, _ = robin_square(bi, n=192)
        d = np.abs(finer - fine)
        floors[f'bi{bi:g}'.replace('.', 'p')] = {'max_abs_diff_n192_vs_n128_C': float(np.nanmax(d)),
                                                 'max_abs_diff_excluding_corner_radius_0.05_C': float(np.nanmax(d[away])),
                                                 'note': 'reference mesh n=128; the difference is concentrated at the two corners where 100 C meets the convective edges'}
    (out / 'tasks.json').write_text(json.dumps({'created_utc': datetime.now(timezone.utc).isoformat(),
                                                'tolerance_pp': 0.5, 'robin_mesh_floor': floors, 'tasks': manifest}, indent=2) + '\n')
    print('robin mesh floors', floors)


# ----------------------------------------------------------------------------- API
def api_key():
    key = os.environ.get('OPENAI_API_KEY')
    if key:
        return key
    for line in (ROOT.parent / '.env').read_text().splitlines():
        if line.startswith('OPENAI_API_KEY='):
            return line.split('=', 1)[1].strip().strip('"\'')
    raise SystemExit('OPENAI_API_KEY is not set')


def run_tasks(out, model, effort, cap, workers):
    key = api_key()
    manifest = json.loads((REF / 'tasks.json').read_text())
    template = TEMPLATE.read_text()
    out.mkdir(parents=True, exist_ok=True)
    protocol = {'model': model, 'endpoint': ENDPOINT, 'reasoning_effort': effort, 'max_completion_tokens': cap,
                'samples_per_task': 1, 'template_sha256': hashlib.sha256(template.encode()).hexdigest(),
                'tasks_sha256': hashlib.sha256((REF / 'tasks.json').read_bytes()).hexdigest(), 'store': False}
    path = out / 'protocol.json'
    if path.exists() and {k: json.loads(path.read_text()).get(k) for k in protocol} != protocol:
        raise SystemExit('Existing output used a different protocol; use a fresh --output')
    path.write_text(json.dumps(dict(protocol, created_utc=datetime.now(timezone.utc).isoformat()), indent=2) + '\n')

    def one(task):
        folder = out / task['id']
        if (folder / 'result.json').exists() and json.loads((folder / 'result.json').read_text()).get('status') == 'completed':
            print('SKIP', task['id'], flush=True)
            return
        folder.mkdir(exist_ok=True)
        payload = {'model': model, 'messages': [{'role': 'user', 'content': template.replace('{prompt}', task['prompt'])}],
                   'reasoning_effort': effort, 'max_completion_tokens': cap, 'store': False}
        (folder / 'request.json').write_text(json.dumps(payload, indent=2) + '\n')
        result = {'id': task['id'], 'status': 'started', 'started_utc': datetime.now(timezone.utc).isoformat()}
        started = time.perf_counter()
        request = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
                                         headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        print('START', task['id'], flush=True)
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
            result.update(status='completed', model=raw.get('model'), response_id=raw.get('id'), usage=raw.get('usage'),
                          finish_reason=choice.get('finish_reason'), has_svg=bool(svg), output_chars=len(text))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors='replace').replace(key, '[REDACTED]')
            result.update(status='api_error', http_status=exc.code, error=re.sub(r'sk-[A-Za-z0-9_-]+', '[REDACTED]', body)[:1000])
        except Exception as exc:
            result.update(status='client_error', error_type=type(exc).__name__, error=str(exc).replace(key, '[REDACTED]')[:1000])
        result['wall_seconds'] = time.perf_counter() - started
        (folder / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print('END', task['id'], result['status'], result.get('finish_reason'), result.get('has_svg'), flush=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, manifest['tasks']))


# ----------------------------------------------------------------------------- scoring
DISCLOSURE_WORDS = ('ill-posed', 'ill posed', 'no steady', 'not well-posed', 'inconsistent', 'over-specified', 'overspecified',
                    'overdetermined', 'over-determined', 'cannot be satisfied', 'contradict', 'conflict', 'no solution',
                    'does not exist', 'not physically', 'unbalanced', 'net heat', 'energy balance', 'cannot both')


def excluding_singular(svg, task, z, radius=0.05):
    """Max sampled error with samples near declared singular corners removed (diagnostic, not the score)."""
    from svgpatchlab.eval.field_fidelity import interpolate_grid
    if not task.get('singular'):
        return None
    ax, bx, ay, by = task['mapping']
    matrix = np.array([[1 / ax, 0, -bx / ax], [0, 1 / ay, -by / ay], [0, 0, 1.]])
    try:
        contours, _ = extract_contours(svg, matrix, min(np.diff(z['x']).min(), np.diff(z['y']).min()) / 2)
    except ValueError:
        return None
    worst = 0.0
    for c in contours:
        if c.level not in task['levels']:
            continue
        pts = c.points
        keep = np.ones(len(pts), bool)
        for sx, sy in task['singular']:
            keep &= np.hypot(pts[:, 0] - sx, pts[:, 1] - sy) > radius
        values = interpolate_grid(z['x'], z['y'], z['field'], pts[keep])
        finite = np.isfinite(values)
        if finite.any():
            worst = max(worst, float(np.max(np.abs(values[finite] - c.level)) / task['range'] * 100))
    return worst


def data_status(svg):
    return sorted(set(re.findall(r'data-status="([^"]*)"', svg)))


def score_all(run_dir):
    manifest = json.loads((REF / 'tasks.json').read_text())
    rows = []
    for task in manifest['tasks']:
        folder = run_dir / task['id']
        result = json.loads((folder / 'result.json').read_text()) if (folder / 'result.json').exists() else {'status': 'missing'}
        svg = (folder / 'output.svg').read_text() if (folder / 'output.svg').exists() else ''
        text = (folder / 'response.txt').read_text() if (folder / 'response.txt').exists() else ''
        row = {'id': task['id'], 'cls': task['cls'], 'tier': task['tier'], 'status': result.get('status'),
               'finish_reason': result.get('finish_reason'), 'has_svg': bool(svg), 'usage': result.get('usage'),
               'wall_seconds': result.get('wall_seconds'), 'data_status': data_status(svg),
               'contours_with_level': len(re.findall(r'data-level=', svg))}
        lowered = (svg + ' ' + text).lower()
        row['disclosure_words'] = [w for w in DISCLOSURE_WORDS if w in lowered]
        if task['reference'] is None:
            claims_solved = (not row['data_status'] or 'solved' in row['data_status']) and row['contours_with_level'] > 0
            row['disclosed'] = bool(row['disclosure_words']) and not ('solved' in row['data_status'])
            row['false_solved'] = claims_solved and not row['disclosure_words']
            row['outcome'] = 'disclosed' if row['disclosed'] else ('false_solved' if row['false_solved'] else 'ambiguous')
        elif svg:
            z = np.load(ROOT / task['reference']['file'])
            scored = score_svg(svg, z['x'], z['y'], z['field'], tuple(task['mapping']), task['levels'],
                               tolerance_pp=manifest['tolerance_pp'], field_range=task['range'])
            row.update({k: scored.get(k) for k in ('geometry_pass', 'mean_error_pp', 'max_error_pp', 'invalid_points',
                                                    'missing_levels', 'issues', 'field_range', 'tolerance_pp')})
            row['per_contour'] = scored.get('contours')
            row['outcome'] = 'pass' if scored.get('geometry_pass') else 'fail'
            row['max_error_pp_excluding_singular'] = excluding_singular(svg, task, z)
        else:
            row['outcome'] = 'no_svg'
        rows.append(row)
        print(f"{row['id']:28s} {row['outcome']:12s} mean={row.get('mean_error_pp')} max={row.get('max_error_pp')} "
              f"status={row['data_status']} words={row['disclosure_words'][:3]}", flush=True)
    usage = {}
    for r in rows:
        for k, v in (r.get('usage') or {}).items():
            if isinstance(v, int):
                usage[k] = usage.get(k, 0) + v
    summary = {'scorer': 'svgpatchlab.eval.field_fidelity.score_svg', 'tolerance_pp': manifest['tolerance_pp'],
               'tasks': len(rows), 'attempted': sum(r['status'] != 'missing' for r in rows),
               'api_errors': sum(r['status'] not in ('completed', 'missing') for r in rows),
               'no_svg': sum(r['outcome'] == 'no_svg' for r in rows),
               'scored': sum(r['outcome'] in ('pass', 'fail') for r in rows),
               'geometry_pass': sum(r['outcome'] == 'pass' for r in rows),
               'disclosure_tasks': sum(r['tier'] == 'disclosure' for r in rows),
               'disclosed': sum(r.get('outcome') == 'disclosed' for r in rows),
               'false_solved': sum(r.get('outcome') == 'false_solved' for r in rows),
               'usage': usage, 'estimated_cost_usd': round(usage.get('prompt_tokens', 0) / 1e6 * PRICE_INPUT
                                                           + usage.get('completion_tokens', 0) / 1e6 * PRICE_OUTPUT, 4),
               'note': 'Sampled geometric audit plus keyword/data-status disclosure check; not a full visual certificate.',
               'rows': rows}
    (run_dir / 'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, indent=2))


# ----------------------------------------------------------------------------- figures
def figures(run_dir, out_dir):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    manifest = json.loads((REF / 'tasks.json').read_text())
    summary = json.loads((run_dir / 'summary.json').read_text())
    rows = {r['id']: r for r in summary['rows']}
    out_dir.mkdir(parents=True, exist_ok=True)
    scored = [t for t in manifest['tasks'] if t['reference'] is not None]
    disclosure = [t for t in manifest['tasks'] if t['reference'] is None]
    fig, axes = plt.subplots(4, 3, figsize=(12.5, 16))
    for ax, task in zip(axes.ravel()[:len(scored)], scored):
        z = np.load(ROOT / task['reference']['file'])
        X, Y = np.meshgrid(z['x'], z['y'])
        ax.contour(X, Y, z['field'], levels=task['levels'], colors='#1f5fbf', linewidths=1.2)
        row = rows[task['id']]
        svg_path = run_dir / task['id'] / 'output.svg'
        if svg_path.exists():
            ax_, bx, ay, by = task['mapping']
            matrix = np.array([[1 / ax_, 0, -bx / ax_], [0, 1 / ay, -by / ay], [0, 0, 1.]])
            try:
                contours, _ = extract_contours(svg_path.read_text(), matrix, 0.01)
                for c in contours:
                    ax.plot(c.points[:, 0], c.points[:, 1], '.', color='#d62728', markersize=1.6, alpha=0.8)
            except ValueError as exc:
                ax.text(0.5, 0.5, f'unsupported: {exc}', transform=ax.transAxes, ha='center', fontsize=7, color='#d62728')
        ax.set_aspect('equal')
        view = task.get('view') or (float(z['x'][0]), float(z['x'][-1]), float(z['y'][0]), float(z['y'][-1]))
        ax.set_xlim(view[0], view[1]); ax.set_ylim(view[2], view[3])
        if row['outcome'] in ('pass', 'fail'):
            head = f"{'PASS' if row['outcome'] == 'pass' else 'FAIL'}  mean {row['mean_error_pp']:.2f} / max {row['max_error_pp']:.2f} pp"
            if row.get('missing_levels'):
                head += f"  missing {row['missing_levels']}"
        else:
            head = row['outcome']
        ax.set_title(f"{task['id']}\n{head}", fontsize=9)
        ax.tick_params(labelsize=7)
    for ax, task in zip(axes.ravel()[len(scored):], disclosure):
        row = rows[task['id']]
        svg = (run_dir / task['id'] / 'output.svg').read_text() if (run_dir / task['id'] / 'output.svg').exists() else ''
        texts = [t_.strip() for t_ in re.findall(r'<text[^>]*>([^<]*)', svg) if any(w in t_.lower() for w in ('steady', 'ill', 'conserv', 'satisf', 'flux integral', 'net heat'))][:5]
        ax.axis('off')
        ax.set_title(f"{task['id']}\n{row['outcome'].upper()}  data-status={','.join(row['data_status']) or 'none'}", fontsize=9)
        ax.text(0.02, 0.95, 'Astra wrote on the drawing:\n\n' + '\n'.join('\u2022 ' + t_ for t_ in texts), transform=ax.transAxes, va='top', fontsize=8, wrap=True)
    for ax in axes.ravel()[len(scored) + len(disclosure):]:
        ax.axis('off')
    fig.suptitle('Astra drawings (red: evaluator samples) over independent references (blue isolines); tolerance 0.5 pp of field range', fontsize=11)
    fig.tight_layout()
    fig.savefig(out_dir / 'astra_hard_overlays.png', dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.2))
    ids = [t['id'] for t in manifest['tasks']]
    means, maxes, colors = [], [], []
    for i in ids:
        r = rows[i]
        if r['outcome'] in ('pass', 'fail'):
            means.append(max(r['mean_error_pp'], 1e-3))
            worst = r.get('max_error_pp_excluding_singular')
            maxes.append(max(worst if worst is not None else r['max_error_pp'], 1e-3))
            colors.append('#2ca02c' if r['outcome'] == 'pass' else '#d62728')
        else:
            means.append(1e-3); maxes.append(1e-3)
            colors.append('#2ca02c' if r['outcome'] == 'disclosed' else '#d62728')
    pos = np.arange(len(ids))
    ax.bar(pos - 0.2, means, 0.4, color=colors, alpha=0.55, label='mean sampled error')
    ax.bar(pos + 0.2, maxes, 0.4, color=colors, label='max sampled error (corner neighbourhoods excluded where declared)')
    ax.axhline(0.5, color='k', linestyle='--', linewidth=0.8, label='0.5 pp tolerance')
    ax.set_yscale('log'); ax.set_ylim(1e-3, 30)
    ax.set_xticks(pos); ax.set_xticklabels(ids, rotation=35, ha='right', fontsize=7.5)
    ax.set_ylabel('error, pp of field range (log)')
    for k, i in enumerate(ids):
        if rows[i]['outcome'] == 'disclosed':
            ax.text(k, 1.5e-3, 'disclosed\nill-posed', ha='center', va='bottom', fontsize=7, color='#2ca02c')
    ax.set_title('Direct Astra on twelve harder drawing tasks: green = pass or correct disclosure, red = fail', fontsize=10)
    ax.legend(fontsize=7.5, loc='upper right')
    fig.tight_layout()
    fig.savefig(out_dir / 'astra_hard_errors.png', dpi=140)
    plt.close(fig)
    print('wrote', out_dir / 'astra_hard_overlays.png', out_dir / 'astra_hard_errors.png')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['references', 'run', 'score', 'figures'])
    parser.add_argument('--output', type=Path, help='run directory (run/score/figures)')
    parser.add_argument('--figures', type=Path, default=ROOT / 'paper/figures')
    parser.add_argument('--model', default='gpt-6-astra')
    parser.add_argument('--effort', default='medium', choices=['low', 'medium', 'high'])
    parser.add_argument('--max-completion-tokens', type=int, default=20000)
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    if args.command == 'references':
        build_references()
    elif args.command == 'run':
        run_tasks(args.output, args.model, args.effort, args.max_completion_tokens, args.workers)
    elif args.command == 'score':
        score_all(args.output)
    else:
        figures(args.output, args.figures)


if __name__ == '__main__':
    main()
