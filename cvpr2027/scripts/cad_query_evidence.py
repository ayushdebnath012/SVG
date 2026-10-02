"""Bounded linear design queries with independently checkable witnesses.

Standard linear programming, not a new solver or general CAD interpreter.
Guarantees are conditional on the supplied constraint model and tolerances.
"""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog


def query_evidence(A, b, bounds, query, *, offset=0.0, minimum=None, tolerance=1e-7):
    """Range a linear quantity over A x=b and explicit variable bounds.

    Both extremizing designs are returned; a caller can verify feasibility and
    disagreement without trusting a model's explanation. No default x>=0 bound.
    """
    c = np.asarray(query, dtype=float)
    A = np.asarray(A, dtype=float).reshape((-1, len(c)))
    b = np.asarray(b, dtype=float)
    if len(bounds) != len(c) or len(b) != len(A):
        raise ValueError('constraint dimensions do not match')
    if not all(np.isfinite(v).all() for v in (A, b, c)):
        raise ValueError('nonfinite coefficients')
    solutions = [linprog(sign*c, A_eq=A if len(A) else None,
                         b_eq=b if len(A) else None, bounds=bounds,
                         method='highs') for sign in (1, -1)]
    if any(s.status == 2 for s in solutions):
        return {'status': 'inconsistent', 'check': 'not_evaluated'}
    if any(s.status == 3 for s in solutions):
        return {'status': 'unbounded', 'check': 'not_evaluated'}
    if any(not s.success for s in solutions):
        return {'status': 'solver_error', 'check': 'not_evaluated',
                'messages': [s.message for s in solutions]}
    witnesses = [s.x for s in solutions]
    residuals = []; certificates = []
    for sign, s in zip((1, -1), solutions):
        x = s.x
        residual = float(np.max(np.abs(A@x-b))) if len(A) else 0.0
        for value, (lo, hi) in zip(x, bounds):
            residual = max(residual, 0.0 if lo is None else lo-value,
                           0.0 if hi is None else value-hi)
        residuals.append(residual)
        # HiGHS marginals form a dual solution. Retain the dual equations so
        # the finite extrema have more evidence than feasible endpoints alone.
        y = np.asarray(s.eqlin.marginals)
        lo_dual = np.asarray(s.lower.marginals)
        hi_dual = np.asarray(s.upper.marginals)
        stationarity = sign*c - A.T@y - lo_dual - hi_dual
        dual_objective = float(b@y)
        sign_error = 0.0
        for (lo, hi), ld, hd in zip(bounds, lo_dual, hi_dual):
            sign_error = max(sign_error, -ld, hd)
            if lo is None:sign_error = max(sign_error, abs(ld))
            else:dual_objective += lo*ld
            if hi is None:sign_error = max(sign_error, abs(hd))
            else:dual_objective += hi*hd
        certificates.append({
            'minimized_cost': (sign*c).tolist(),
            'equality_multipliers': y.tolist(),
            'lower_bound_multipliers': lo_dual.tolist(),
            'upper_bound_multipliers': hi_dual.tolist(),
            'stationarity_residual': float(np.max(abs(stationarity))),
            'dual_sign_residual': float(sign_error),
            'primal_dual_gap': float(abs(sign*c@x-dual_objective)),
            'dual_objective_without_query_offset': float(dual_objective)})
    certificate_error = max(v[k] for v in certificates for k in
                            ('stationarity_residual','dual_sign_residual','primal_dual_gap'))
    if max(max(residuals),certificate_error) > tolerance:
        return {'status': 'numerically_unverified', 'check': 'not_evaluated',
                'residuals': residuals, 'bound_certificates': certificates}
    low, high = [float(c@x + offset) for x in witnesses]
    status = 'identifiable' if high-low <= tolerance else 'ambiguous'
    check = 'not_requested'
    if minimum is not None:
        check = ('satisfied_for_all' if low >= minimum-tolerance else
                 'violated_for_all' if high < minimum-tolerance else
                 'depends_on_interpretation')
    return {'status': status, 'range': [low, high], 'check': check,
            'witnesses': [x.tolist() for x in witnesses],
            'max_constraint_residuals': residuals, 'bound_certificates': certificates,
            'tolerance': tolerance}


def panel_example():
    # Edited panel: x = [left, hole1, ..., hole5, right]. The width and
    # 36 mm pitch are specified, but the edited hole-row anchorage is absent.
    # This is an authored constraint control, not automatic SVG extraction.
    A = [[1,0,0,0,0,0,0], [-1,0,0,0,0,0,1]]
    b = [0,234]
    for i in range(1,5):
        row = [0]*7; row[i]=-1; row[i+1]=1
        A.append(row); b.append(36)
    bounds = [(0,0)] + [(9.5,224.5)]*5 + [(234,234)]
    queries = {
        'width_mm': ([-1,0,0,0,0,0,1], 0, None),
        'first_hole_x_mm': ([0,1,0,0,0,0,0], 0, None),
        'pitch_mm': ([0,-1,1,0,0,0,0], 0, None),
        'left_edge_clearance_mm': ([0,1,0,0,0,0,0], -4.5, 5),
        'hole1_must_be_at_least_30mm_from_datum': ([0,1,0,0,0,0,0], 0, 30),
        'minimum_40mm_pitch': ([0,-1,1,0,0,0,0], 0, 40),
    }
    result = {name: query_evidence(A,b,bounds,c,offset=off,minimum=minimum)
              for name,(c,off,minimum) in queries.items()}
    # Adding one measured edit requirement removes this particular ambiguity.
    anchored_A = A + [[0,1,0,0,0,0,0]]
    result['after_explicit_left_anchor'] = query_evidence(
        anchored_A,b+[18],bounds,[0,1,0,0,0,0,0])
    return {'variables': ['left','hole1','hole2','hole3','hole4','hole5','right'],
            'A': A, 'b': b, 'bounds': bounds, 'queries': result,
            'scope': 'Authored linear constraint control; no Astra run; no automatic ambiguity extraction; no FEM claim.'}


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    path = root/'runs/astra-cad-intent-20260921/query-evidence.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(panel_example(),indent=2)+'\n')
    print(path)
