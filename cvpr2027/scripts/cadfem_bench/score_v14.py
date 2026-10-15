"""Published-source pilot scorer: numerical accuracy and reviewed workflow completion.

Never executes candidate code. Trusted review JSONL must be evaluator-owned and
outside the submissions directory. Reviews are bound to task, run and artifact hashes.
They are human/isolated-runner attestations, not automatic proof from file presence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

REQUIRED = ('results.json', 'main.py', 'part.step', 'mesh.msh', 'fields.npz', 'solver.log', 'refinement.json', 'environment.json')
REVIEW_CHECKS = ('execution_verified', 'geometry_verified', 'setup_verified', 'field_outputs_verified', 'convergence_reviewed')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def canonical_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def strict_json(text):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError('duplicate JSON key: ' + k)
            out[k] = v
        return out
    def invalid(s):
        raise ValueError('nonfinite JSON number: ' + s)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def within(pred, ref):
    if ref['tol']['kind'] == 'bool':
        return type(pred) is bool and pred == ref['value'], None
    if type(pred) not in (int, float):
        return False, None
    try:
        p = float(pred)
    except (ValueError, OverflowError):
        return False, None
    if not math.isfinite(p):
        return False, None
    v, t = float(ref['value']), ref['tol']
    if t['kind'] == 'abs':
        err = abs(p - v)
    else:
        off = t.get('offset', 0.) if t['kind'] == 'rel_offset' else 0.
        err = abs(p - v) / max(abs(v - off), 1e-300)
    return err <= t['value'], err


def read_shape(step):
    from OCP.STEPControl import STEPControl_Reader
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.TopTools import TopTools_IndexedMapOfShape
    from OCP.TopExp import TopExp
    from OCP.TopAbs import TopAbs_SOLID
    r = STEPControl_Reader()
    if int(r.ReadFile(str(step))) != 1:
        raise ValueError('unreadable STEP')
    r.TransferRoots()
    s = r.OneShape()
    if s.IsNull() or not BRepCheck_Analyzer(s).IsValid():
        raise ValueError('invalid STEP topology')
    m = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(s, TopAbs_SOLID, m)
    if m.Extent() < 1:
        raise ValueError('STEP contains no solid')
    return s, m.Extent()


def _rotations():
    """The 24 proper rotations that map coordinate axes onto coordinate axes (no mirror images)."""
    import itertools
    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            m = [[0] * 3 for _ in range(3)]
            for i in range(3):
                m[i][perm[i]] = signs[i]
            det = (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                   + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
            if det == 1:
                out.append(m)
    return out


def geometry(step, chk, evaluator_dir):
    """Volume-overlap gate for the rigging drawing task, after alignment to the original CAD.

    The drawing does not fix the source CAD frame, so the submission is moved to the reference bounding-box centre
    and every proper axis rotation whose extents match is tried; the best relative symmetric difference is kept.
    This is a necessary automated shape gate; trusted review must still check drawing features, scopes and setup.
    """
    try:
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
        from OCP.BRepBndLib import BRepBndLib
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        from OCP.BRepGProp import BRepGProp
        from OCP.Bnd import Bnd_Box
        from OCP.GProp import GProp_GProps
        from OCP.gp import gp_Trsf
        s, n = read_shape(step)
        refpath = (evaluator_dir / chk['reference_step']).resolve()
        if not refpath.is_relative_to(evaluator_dir.resolve()) or digest(refpath) != chk['reference_sha256']:
            raise ValueError('reference CAD hash/path mismatch')
        rs, rn = read_shape(refpath)
        if n != rn:
            return False, {'error': 'solid count differs from reference', 'solids': n, 'reference_solids': rn}
        if chk.get('analytic_radius_tolerance_mm') is not None:
            from OCP.BRepAdaptor import BRepAdaptor_Surface
            from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Sphere
            from OCP.TopAbs import TopAbs_FACE
            from OCP.TopExp import TopExp_Explorer
            from OCP.TopoDS import TopoDS
            def radii(shape):
                values={'cylinder': [], 'sphere': []}
                exp=TopExp_Explorer(shape, TopAbs_FACE)
                while exp.More():
                    ad=BRepAdaptor_Surface(TopoDS.Face_s(exp.Current()), True)
                    typ=ad.GetType()
                    if typ==GeomAbs_Cylinder: values['cylinder'].append(ad.Cylinder().Radius())
                    elif typ==GeomAbs_Sphere: values['sphere'].append(ad.Sphere().Radius())
                    exp.Next()
                return {k: sorted({round(x, 6) for x in v}) for k,v in values.items()}
            expected, submitted=radii(rs),radii(s)
            tol=chk['analytic_radius_tolerance_mm']
            for typ in expected:
                if len(expected[typ])!=len(submitted[typ]) or any(abs(a-b)>tol for a,b in zip(expected[typ], submitted[typ])):
                    return False, {'error': 'analytic sphere/cylinder radius mismatch', 'surface_type':typ, 'expected_radii_mm':expected[typ], 'submitted_radii_mm':submitted[typ]}

        def vol(sh):
            g = GProp_GProps()
            BRepGProp.VolumeProperties_s(sh, g)
            return abs(g.Mass())

        def box(sh):
            b = Bnd_Box()
            BRepBndLib.AddOptimal_s(sh, b, False, False)
            x0, y0, z0, x1, y1, z1 = b.Get()
            return [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2], [x1 - x0, y1 - y0, z1 - z0]

        a, b_ = vol(s), vol(rs)
        if b_ <= 0:
            raise ValueError('reference volume is zero')
        cs, es = box(s)
        cr, er = box(rs)
        best = None
        for m in _rotations():
            ext = [sum(abs(m[i][j]) * es[j] for j in range(3)) for i in range(3)]
            if any(abs(ext[i] - er[i]) > 0.05 * er[i] for i in range(3)):
                continue
            t = [cr[i] - sum(m[i][j] * cs[j] for j in range(3)) for i in range(3)]
            tr = gp_Trsf()
            tr.SetValues(m[0][0], m[0][1], m[0][2], t[0], m[1][0], m[1][1], m[1][2], t[1], m[2][0], m[2][1], m[2][2], t[2])
            moved = BRepBuilderAPI_Transform(s, tr, True).Shape()
            common = BRepAlgoAPI_Common(moved, rs)
            if not common.IsDone():
                continue
            err = max(0., a + b_ - 2 * vol(common.Shape())) / b_
            best = err if best is None else min(best, err)
        if best is None:
            return False, {'error': 'no axis-aligned orientation matches the reference extents within 5 %', 'solids': n}
        return best <= chk['relative_symmetric_difference_limit'], {'relative_symmetric_difference': best, 'solids': n, 'reference_solids': rn}
    except Exception as e:
        return False, {'error': str(e)}


def task_score(r, task, root, review, run_id, evaluator_dir):
    tid = r['task_id']
    if Path(tid).name != tid or tid in ('.', '..'):
        raise ValueError('unsafe task ID')
    folder = (root / tid).resolve()
    rec = {'task_id': tid, 'track': r['track'], 'tier': r['tier'], 'family': r['family'],
           'engineering_family': r.get('engineering_family', r['family']), 'independently_reproduced': bool(task.get('readiness', {}).get('independently_reproduced')), 'passed': False,
           'numerical_passed': False, 'numerical_score': 0., 'workflow_verified': False}
    errors, checks, hashes = [], {}, {}
    if not folder.is_relative_to(root.resolve()):
        return rec | {'errors': ['submission path escapes root']}
    try:
        f = folder / 'results.json'
        if f.is_symlink():
            raise ValueError('symlink submission file')
        obj = strict_json(f.read_text())
        if not isinstance(obj, dict) or set(obj) != {'outputs'} or not isinstance(obj['outputs'], dict):
            raise ValueError('results must be an object containing an outputs object')
        outs = obj['outputs']
        expected = {k for k, v in r['references'].items() if v.get('graded', True)}
        if set(outs) != expected:
            raise ValueError('output keys must exactly match the task contract')
        for key in expected:
            ok, err = within(outs[key], r['references'][key])
            # Do not copy hidden reference values into a score artifact.
            checks[key] = {'ok': ok, 'error': err}
        rec['numerical_passed'] = bool(checks) and all(v['ok'] for v in checks.values())
        rec['numerical_score'] = sum(v['ok'] for v in checks.values()) / len(checks) if checks else 0.
    except (OSError, ValueError, TypeError, OverflowError) as e:
        errors.append('invalid numerical submission: ' + str(e))
    rec['checks'] = checks
    for name in REQUIRED:
        f = folder / name
        if not f.is_file() or f.is_symlink() or not f.resolve().is_relative_to(folder) or f.stat().st_size == 0:
            errors.append('missing/unsafe/empty artifact: ' + name)
        else:
            hashes[name] = digest(f)
    if len(hashes) == len(REQUIRED):
        try:
            _, solids = read_shape(folder / 'part.step')
            rec['submitted_solids'] = solids
        except Exception as e:
            errors.append('CAD validation: ' + str(e))
    if r.get('geometry_check') and 'part.step' in hashes:
        ok, detail = geometry(folder / 'part.step', r['geometry_check'], evaluator_dir)
        rec['geometry_check'] = {'ok': ok, **detail}
        if not ok:
            errors.append('reference geometry mismatch')
    if review is None:
        errors.append('trusted workflow review missing')
    else:
        if review.get('run_id') != run_id or review.get('task_sha256') != canonical_hash(task):
            errors.append('review run/task mismatch')
        if review.get('artifacts') != hashes or len(hashes) != len(REQUIRED):
            errors.append('review artifact hashes mismatch')
        if not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip():
            errors.append('reviewer missing')
        if not isinstance(review.get('evidence'), dict) or any(not isinstance(review['evidence'].get(k), str) or not review['evidence'][k].strip() for k in REVIEW_CHECKS):
            errors.append('review evidence notes missing')
        if any(review.get(k) is not True for k in REVIEW_CHECKS):
            errors.append('workflow review incomplete or rejected')
    rec['workflow_verified'] = not errors
    rec['passed'] = rec['numerical_passed'] and rec['workflow_verified']
    rec['errors'] = errors
    return rec


def aggregate(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r['engineering_family']].append(r)
    n = len(rows)
    return {'tasks': n, 'passed': sum(r['passed'] for r in rows),
            'numerical_passed': sum(r['numerical_passed'] for r in rows),
            'workflow_verified': sum(r['workflow_verified'] for r in rows),
            'pass_rate': sum(r['passed'] for r in rows)/n if n else None,
            'numerical_pass_rate': sum(r['numerical_passed'] for r in rows)/n if n else None,
            'engineering_family_macro_pass_rate': sum(sum(x['passed'] for x in g)/len(g) for g in groups.values())/len(groups) if groups else None}


def release_version(refs_path):
    """Release label from the nearest evaluator validation.json above the references (suites sit below evaluator/)."""
    for d in refs_path.resolve().parents:
        f = d / 'validation.json'
        if f.is_file():
            return str(json.loads(f.read_text()).get('version', 'unknown'))
    return 'unknown'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--refs', required=True)
    ap.add_argument('--tasks', required=True, help='candidate/tasks.jsonl')
    ap.add_argument('--submissions', required=True)
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--reviews', help='trusted evaluator-owned review JSONL, outside submissions')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    refs_path, root = Path(a.refs), Path(a.submissions).resolve()
    def lines(p):
        return [strict_json(x) for x in Path(p).read_text().splitlines() if x.strip()]
    refs, ts = lines(refs_path), lines(a.tasks)
    tasks = {t['task_id']: t for t in ts}
    if len(tasks) != len(ts) or len({r['task_id'] for r in refs}) != len(refs) or set(tasks) != {r['task_id'] for r in refs}:
        ap.error('task/reference IDs must be unique and match')
    if any(r.get('grader') != 'numeric' or r.get('status') != 'active' for r in refs):
        ap.error('only active numeric references are supported; held tasks cannot be scored')
    reviews = {}
    if a.reviews:
        rp = Path(a.reviews).resolve()
        if rp.is_relative_to(root):
            ap.error('review file must be trusted evaluator-owned input outside submissions')
        for v in lines(rp):
            if not isinstance(v, dict) or v.get('task_id') not in tasks or v['task_id'] in reviews:
                ap.error('invalid, duplicate or unknown review task ID')
            reviews[v['task_id']] = v
    rows = [task_score(r, tasks[r['task_id']], root, reviews.get(r['task_id']), a.run_id, refs_path.parent) for r in refs]
    groups = defaultdict(list)
    for r in rows:
        groups['all'].append(r)
        if r['independently_reproduced']:
            groups['reproduced_tasks_only'].append(r)
            groups['reproduced_tasks_only / track ' + r['track']].append(r)
        groups['track ' + r['track']].append(r)
        groups['track ' + r['track'] + ' / ' + r['tier']].append(r)
        groups['engineering family / ' + r['engineering_family']].append(r)
    result = {'version': release_version(refs_path), 'run_id': a.run_id, 'summary': {k:aggregate(v) for k,v in groups.items()}, 'tasks': rows,
              'note': 'Workflow verification requires trusted external review; file presence and correct scalar answers alone never pass.'}
    Path(a.out).write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result['summary']['all'], indent=2))


if __name__ == '__main__':
    main()
