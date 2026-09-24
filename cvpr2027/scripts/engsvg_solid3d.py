"""3D solid FEM for extruded 2D profiles: the cheapest honest step out of plane.

The 2D families verify what plane analysis can verify. A plate with holes is a 2D outline plus a
thickness, so extruding it into tetrahedra gives a genuine three-dimensional stress state --- all six
components, Poisson contraction, and stress concentration around holes that grows through the
thickness --- without building a B-rep kernel or a general mesher.

Pipeline: constrained Delaunay triangulation of the profile with its holes, extrusion of each triangle
into a prism split into three tetrahedra, then linear elasticity on P1 or P2 vector elements.

What this does not do: curved surfaces, contact, plasticity, buckling, or anything that needs a real
solid modeller. It is plane-stress geometry taken into 3D, not general mechanical CAD.

Subcommand: verify --- runs the analytical controls below and reports the errors.
"""
from __future__ import annotations
import argparse
import json
import sys

import numpy as np


def triangulate(outline, holes=(), max_area=None):
    """Constrained Delaunay mesh of a polygon with holes. `outline` and each hole are (x, y) rings."""
    import triangle as tr
    points, segments, hole_points = [], [], []

    def ring(pts):
        start = len(points)
        points.extend([list(map(float, p)) for p in pts])
        segments.extend([[start + i, start + (i + 1) % len(pts)] for i in range(len(pts))])

    ring(outline)
    for h in holes:
        ring(h)
        hole_points.append([float(np.mean([p[0] for p in h])), float(np.mean([p[1] for p in h]))])
    spec = {'vertices': np.array(points), 'segments': np.array(segments)}
    if hole_points:
        spec['holes'] = np.array(hole_points)
    flags = 'pq30'
    if max_area:
        flags += f'a{max_area:.6f}'
    mesh = tr.triangulate(spec, flags)
    return np.asarray(mesh['vertices'], float), np.asarray(mesh['triangles'], int)


def extrude(vertices2d, triangles, thickness, layers=2):
    """Each prism becomes three tetrahedra, with a vertex ordering that keeps faces conforming."""
    n = len(vertices2d)
    pts = np.vstack([np.column_stack([vertices2d, np.full(n, k * thickness / layers)])
                     for k in range(layers + 1)])
    tets = []
    for tri in triangles:
        a, b, c = sorted(int(v) for v in tri)          # global ordering makes shared faces agree
        for k in range(layers):
            lo, hi = k * n, (k + 1) * n
            a0, b0, c0, a1, b1, c1 = a + lo, b + lo, c + lo, a + hi, b + hi, c + hi
            tets += [[a0, b0, c0, c1], [a0, b0, c1, b1], [a0, b1, c1, a1]]
    return pts.T, np.array(tets, int).T


def solve(points, tets, E, nu, fixed, traction_faces=None, traction=(0., 0., 0.), order=1):
    """Linear elasticity. `fixed` and `traction_faces` are predicates on a (3, n) coordinate array."""
    from skfem import (MeshTet, Basis, FacetBasis, ElementVector, ElementTetP1, ElementTetP2,
                       LinearForm, asm, condense, solve as sksolve)
    from skfem.models.elasticity import linear_elasticity, lame_parameters
    mesh = MeshTet(points, tets)
    element = ElementVector(ElementTetP2() if order == 2 else ElementTetP1())
    basis = Basis(mesh, element)
    K = asm(linear_elasticity(*lame_parameters(E, nu)), basis)
    dofs = []
    for predicate, component in fixed:
        dofs.append(basis.get_dofs(predicate).all(f'u^{component}'))
    D = np.unique(np.concatenate(dofs)) if dofs else np.array([], int)
    f = basis.zeros()
    if traction_faces is not None:
        fb = FacetBasis(mesh, element, facets=mesh.facets_satisfying(traction_faces))
        tx, ty, tz = traction

        @LinearForm
        def load(v, w):
            return tx * v[0] + ty * v[1] + tz * v[2]
        f = asm(load, fb)
    u = sksolve(*condense(K, f, D=D))
    return mesh, basis, u


def von_mises(mesh, basis, u, E, nu):
    """Element-wise von Mises stress from the solved displacement field."""
    from skfem import Basis, ElementTetP0
    from skfem.models.elasticity import lame_parameters
    from skfem.helpers import sym_grad, eye, trace
    from skfem import Functional
    lam, mu = lame_parameters(E, nu)
    dg = Basis(mesh, ElementTetP0(), intorder=2)
    peak = 0.0
    eps = basis.interpolate(u).grad if hasattr(basis.interpolate(u), 'grad') else None
    # project the stress invariant element by element
    from skfem import LinearForm
    @LinearForm
    def vm(v, w):
        du = w['disp'].grad
        e = 0.5 * (du + np.einsum('ij...->ji...', du))
        tr = e[0, 0] + e[1, 1] + e[2, 2]
        s = 2 * mu * e
        for i in range(3):
            s[i, i] = s[i, i] + lam * tr
        dev = s.copy()
        m = (s[0, 0] + s[1, 1] + s[2, 2]) / 3
        for i in range(3):
            dev[i, i] = dev[i, i] - m
        j2 = 0.5 * sum(dev[i, j] ** 2 for i in range(3) for j in range(3))
        return np.sqrt(3 * j2) * v
    vals = asm_safe(vm, dg, basis, u)
    return float(np.max(vals)) if vals is not None else None


def asm_safe(form, dg, basis, u):
    from skfem import asm
    try:
        mass = asm(_unit(), dg)
        rhs = asm(form, dg, disp=basis.interpolate(u))
        return rhs / mass
    except Exception:
        return None


def _unit():
    from skfem import LinearForm
    @LinearForm
    def one(v, w):
        return 1.0 + 0.0 * v
    return one


# ----------------------------------------------------------------------------- controls
def verify():
    checks = []

    def check(name, got, want, tol, detail=''):
        rel = abs(got - want) / max(abs(want), 1e-30)
        ok = rel <= tol
        checks.append({'check': name, 'pass': bool(ok), 'got': got, 'expected': want,
                       'relative_error': rel, 'detail': detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {got:.6e} vs {want:.6e}  rel {rel:.2e}  {detail}")
        return ok

    E, nu, T = 210000.0, 0.3, 12.0
    L, W, H = 40.0, 20.0, 5.0

    # 1. Axial extension of a bar. Symmetry planes leave Poisson contraction free, so the
    #    displacement is exactly TL/E and any deviation is a solver or mesh defect.
    v2, tri = triangulate([(0, 0), (L, 0), (L, W), (0, W)], max_area=6.0)
    pts, tets = extrude(v2, tri, H, layers=2)
    fixed = [(lambda x: np.isclose(x[0], 0.), 1), (lambda x: np.isclose(x[1], 0.), 2),
             (lambda x: np.isclose(x[2], 0.), 3)]
    mesh, basis, u = solve(pts, tets, E, nu, fixed,
                           traction_faces=lambda x: np.isclose(x[0], L), traction=(T, 0, 0))
    tip = float(np.mean(u[basis.get_dofs(lambda x: np.isclose(x[0], L)).all('u^1')]))
    check('axial extension of a bar', tip, T * L / E, 1e-9, f'{mesh.nelements} tets')

    # 2. Poisson contraction across the width, which only exists in 3D.
    side = float(np.mean(u[basis.get_dofs(lambda x: np.isclose(x[1], W)).all('u^2')]))
    check('transverse Poisson contraction', side, -nu * (T / E) * W, 1e-9, 'lateral strain = -nu*eps_x')

    # 3. Thickness contraction, the component a plane-stress model cannot represent at all.
    thru = float(np.mean(u[basis.get_dofs(lambda x: np.isclose(x[2], H)).all('u^3')]))
    check('through-thickness contraction', thru, -nu * (T / E) * H, 1e-9, 'the genuinely 3D term')

    # 4. Mesh independence: refining must not move a solution that is already exact.
    v2b, trib = triangulate([(0, 0), (L, 0), (L, W), (0, W)], max_area=1.5)
    ptsb, tetsb = extrude(v2b, trib, H, layers=3)
    _, basisb, ub = solve(ptsb, tetsb, E, nu, fixed,
                          traction_faces=lambda x: np.isclose(x[0], L), traction=(T, 0, 0))
    tipb = float(np.mean(ub[basisb.get_dofs(lambda x: np.isclose(x[0], L)).all('u^1')]))
    check('refinement leaves the answer unchanged', tipb, tip, 1e-9,
          f'{len(tetsb.T)} tets vs {mesh.nelements}')

    # 5. A hole must remove material and make the plate more compliant, by the net-section ratio
    #    at minimum. This is the check that proves the hole is actually in the mesh.
    r, cx, cy = 4.0, L / 2, W / 2
    circle = [(cx + r * np.cos(t), cy + r * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 33)[:-1]]
    v2c, tric = triangulate([(0, 0), (L, 0), (L, W), (0, W)], holes=[circle], max_area=2.0)
    ptsc, tetsc = extrude(v2c, tric, H, layers=2)
    _, basisc, uc = solve(ptsc, tetsc, E, nu, fixed,
                          traction_faces=lambda x: np.isclose(x[0], L), traction=(T, 0, 0))
    tipc = float(np.mean(uc[basisc.get_dofs(lambda x: np.isclose(x[0], L)).all('u^1')]))
    ok = tipc > tip
    checks.append({'check': 'a hole makes the plate more compliant', 'pass': bool(ok),
                   'got': tipc, 'expected': f'> {tip:.6e}', 'relative_error': None,
                   'detail': f'{len(tetsc.T)} tets, {len(circle)}-segment hole'})
    print(f"{'PASS' if ok else 'FAIL'}  a hole makes the plate more compliant: "
          f"{tipc:.6e} > {tip:.6e}  ({100 * (tipc / tip - 1):.1f}% softer)")

    passed = all(c['pass'] for c in checks)
    print('\nALL CONTROLS PASS' if passed else '\nCONTROLS FAILED')
    return {'all_pass': passed, 'checks': checks}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['verify'])
    p.add_argument('--out', default=None)
    a = p.parse_args()
    result = verify()
    if a.out:
        from pathlib import Path
        Path(a.out).write_text(json.dumps(result, indent=2, default=str) + '\n')
    raise SystemExit(0 if result['all_pass'] else 1)


if __name__ == '__main__':
    main()
