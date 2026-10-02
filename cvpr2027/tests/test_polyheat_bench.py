import json, sys, unittest
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))
import polyheat_bench as P                                        # noqa: E402
from fd_reference import marching_squares                          # noqa: E402
from svgpatchlab.eval.field_fidelity import score_svg              # noqa: E402

COARSE_TEST = 80   # a cheap grid; these tests check logic, not reference accuracy


def make_task(columns):
    return {'id': 'test', 'levels': P.LEVELS, 'range': P.FIELD_RANGE, 'mapping': list(P.MAPPING),
            'singular': P.singular_points(columns), 'reentrant': [[float(a), float(b)] for a, b in P.reentrant(columns)]}


def solved(columns, n=COARSE_TEST):
    x, y, f, _ = P.solve(columns, n)
    return {'x': x, 'y': y, 'field': f}


def isoline_svg(z, task, levels=None, relabel=None, shift=0.0):
    """Draw the reference isolines; `relabel` mislabels them and `shift` displaces them, for controls."""
    ax, bx, ay, by = task['mapping']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><g data-field="T" data-status="solved">']
    for lv in (levels or task['levels']):
        for x0, y0, x1, y1 in marching_squares(z['x'], z['y'], z['field'], lv):
            parts.append(f'<polyline data-level="{relabel if relabel is not None else lv}" fill="none" '
                         f'stroke="#b00" stroke-width="1" points="'
                         f'{bx + ax * (x0 + shift):.4f},{by + ay * y0:.4f} '
                         f'{bx + ax * (x1 + shift):.4f},{by + ay * y1:.4f}"/>')
    return ''.join(parts) + '</g></svg>'


class GeneratorTests(unittest.TestCase):
    def test_reproduces_the_september_failing_task_character_for_character(self):
        from astra_hard_tasks import tasks as hard_tasks
        original = next(t for t in hard_tasks() if t['id'] == 'c1_polygon_procedural')['prompt']
        self.assertEqual(P.prompt_text(P.ORIGINAL), original)
        ring, _, _ = P.vertices(P.ORIGINAL)
        self.assertEqual([(P.num(a), P.num(b)) for a, b in ring],
                         [('0', '0'), ('1', '0'), ('1', '0.4'), ('0.6', '0.4'),
                          ('0.6', '1'), ('0.2', '1'), ('0.2', '0.6'), ('0', '0.6')])

    def test_manifest_prompt_matches_the_september_manifest_prompt(self):
        """The prompt actually sent must carry the data-level contract, or nothing is scoreable.

        Without it the model returns a plausible drawing whose contours have no level attribute, the
        scorer finds nothing to measure, and the run is silently void rather than loudly broken.
        """
        from astra_hard_tasks import REF as HARD_REF
        shipped = json.loads((HARD_REF / 'tasks.json').read_text())
        want = next(t for t in shipped['tasks'] if t['id'] == 'c1_polygon_procedural')['prompt']
        self.assertEqual(P.full_prompt(P.ORIGINAL), want)
        for columns in (((5, 3),), P.ORIGINAL):
            self.assertIn('data-level', P.full_prompt(columns))
            self.assertIn('data-status', P.full_prompt(columns))

    def test_vertex_ring_is_a_simple_polygon_agreeing_with_the_domain_predicate(self):
        from shapely.geometry import Polygon, Point
        rng = np.random.default_rng(7)
        for columns in (P.ORIGINAL, ((5, 3),), ((1, 2), (1, 5), (1, 3), (1, 4), (1, 2))):
            ring, _, _ = P.vertices(columns)
            poly = Polygon([(float(a), float(b)) for a, b in ring])
            self.assertTrue(poly.is_valid, columns)
            self.assertTrue(poly.is_simple, columns)
            pts = rng.random((400, 2))
            inside = P.inside_predicate(columns)(pts[:, 0:1], pts[:, 1:2]).ravel()
            for (px, py), flag in zip(pts, inside):
                if abs(poly.exterior.distance(Point(px, py))) < 1e-3:
                    continue                                    # skip the boundary band
                self.assertEqual(poly.contains(Point(px, py)), bool(flag), (columns, px, py))

    def test_area_of_the_ring_matches_the_column_heights(self):
        from shapely.geometry import Polygon
        for columns in (P.ORIGINAL, ((2, 4), (3, 2)), ((1, 5), (2, 2), (2, 4))):
            ring, _, _ = P.vertices(columns)
            want = sum(w / P.LATTICE * h / P.LATTICE for w, h in columns)
            self.assertAlmostEqual(Polygon([(float(a), float(b)) for a, b in ring]).area, want, places=12)

    def test_reentrant_corners_are_the_height_changes_and_are_all_declared_singular(self):
        for columns in (P.ORIGINAL, ((5, 3),), ((1, 2), (1, 5), (1, 3), (1, 4))):
            changes = sum(1 for i in range(1, len(columns)) if columns[i][1] != columns[i - 1][1])
            corners = P.reentrant(columns)
            self.assertEqual(len(corners), changes, columns)
            singular = P.singular_points(columns)
            for a, b in corners:
                self.assertIn([float(a), float(b)], singular)
            for corner in P.HOT_COLD:
                self.assertIn(corner, singular)

    def test_candidate_pool_never_repeats_a_height(self):
        for n in (1, 2, 3, 4):
            for cols in P.candidates(n):
                self.assertEqual(sum(w for w, _ in cols), P.LATTICE)
                self.assertTrue(all(cols[i][1] != cols[i - 1][1] for i in range(1, len(cols))))

    def test_ladder_is_monotone_and_pins_the_original_plate(self):
        picked = P.build_instances()
        self.assertTrue(any(i['is_original_failing_plate'] for i in picked))
        self.assertEqual(len({i['id'] for i in picked}), len(picked))
        for inst in picked:
            self.assertEqual(inst['reentrant_corners'], inst['n_columns'] - 1)


class ReferenceTests(unittest.TestCase):
    def test_reference_satisfies_the_boundary_conditions_it_claims(self):
        z = solved(P.ORIGINAL)
        self.assertTrue(np.allclose(z['field'][0, :], 100.0))            # hot edge exactly 100 C
        self.assertLessEqual(np.nanmax(z['field'][1:, :]), 100.0 + 1e-9)  # maximum principle
        self.assertGreaterEqual(np.nanmin(z['field']), -1e-9)

    def test_refinement_difference_is_worst_at_a_declared_singular_point(self):
        xc, yc, fc, _ = P.solve(P.ORIGINAL, 160)
        _, _, ff, _ = P.solve(P.ORIGINAL, 320)
        diff = np.abs(fc - ff[::2, ::2])
        both = np.isfinite(fc) & np.isfinite(ff[::2, ::2])
        X, Y = np.meshgrid(xc, yc)
        j, i = np.unravel_index(np.nanargmax(np.where(both, diff, np.nan)), diff.shape)
        near = min(np.hypot(X[j, i] - sx, Y[j, i] - sy) for sx, sy in P.singular_points(P.ORIGINAL))
        self.assertLess(near, P.EXCLUDE_R)
        away = both.copy()
        for sx, sy in P.singular_points(P.ORIGINAL):
            away &= np.hypot(X - sx, Y - sy) > P.EXCLUDE_R
        self.assertLess(diff[away].max(), diff[both].max() / 5)


class ScorerTests(unittest.TestCase):
    def test_accepts_a_drawing_made_from_the_reference_isolines(self):
        """Positive control: the certified metric must call a perfect drawing perfect, with headroom."""
        task, z = make_task(P.ORIGINAL), solved(P.ORIGINAL)
        d = P.diagnostics(isoline_svg(z, task), task, z)
        self.assertLessEqual(d['certified_max_error_pp'], P.TOLERANCE_PP / 2)
        self.assertEqual(d['certified_outside_domain_fraction'], 0.0)
        self.assertEqual(d['impossible_boundary_contact'], [])
        for level in task['levels']:
            self.assertGreater(d['certified_samples_per_level'][str(float(level))], 0)

    def test_strict_metric_fails_even_a_perfect_drawing_so_the_benchmark_does_not_use_it(self):
        """Every isotherm here ends at the two corners where the boundary data jumps 0 <-> 100 C.

        Sampling a contour into those corners charges it an error of up to half the field range, so the
        strict 0.5 pp criterion of the 18 September screen is unreachable on this domain family. The
        benchmark therefore decides on the certified metric, which removes those neighbourhoods.
        """
        task, z = make_task(P.ORIGINAL), solved(P.ORIGINAL)
        svg = isoline_svg(z, task)
        s = score_svg(svg, z['x'], z['y'], z['field'], tuple(task['mapping']), task['levels'],
                      tolerance_pp=P.TOLERANCE_PP, field_range=task['range'])
        self.assertFalse(s['geometry_pass'])
        self.assertGreater(s['max_error_pp'], P.TOLERANCE_PP)
        self.assertEqual(s['invalid_points'], 0)
        self.assertEqual(s['missing_levels'], [])
        self.assertEqual([i for r in s['per_level'] for i in r['issues']], [])
        # ...and the certified metric on the same drawing is orders of magnitude inside tolerance.
        self.assertLess(P.diagnostics(svg, task, z)['certified_max_error_pp'], s['max_error_pp'] / 20)

    def test_rejects_a_mislabelled_contour(self):
        task, z = make_task(P.ORIGINAL), solved(P.ORIGINAL)
        svg = isoline_svg(z, task, levels=[40], relabel=60)      # 40 C isoline claimed to be 60 C
        d = P.diagnostics(svg, task, z)
        self.assertGreater(d['certified_max_error_pp'], 15.0)

    def test_rejects_a_displaced_contour(self):
        task, z = make_task(P.ORIGINAL), solved(P.ORIGINAL)
        clean = P.diagnostics(isoline_svg(z, task), task, z)['certified_max_error_pp']
        moved = P.diagnostics(isoline_svg(z, task, shift=0.05), task, z)['certified_max_error_pp']
        self.assertLessEqual(clean, P.TOLERANCE_PP)
        self.assertGreater(moved, P.TOLERANCE_PP)

    def test_detects_a_sub_hot_isotherm_lying_on_the_hot_edge(self):
        task, z = make_task(P.ORIGINAL), solved(P.ORIGINAL)
        ax, bx, ay, by = task['mapping']
        y0 = by + ay * 0.0
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><g data-field="T" data-status="solved">'
               f'<polyline data-level="10" fill="none" stroke="#b00" points="{bx + ax * 0.3:.1f},{y0:.1f} '
               f'{bx + ax * 0.7:.1f},{y0:.1f}"/></g></svg>')
        d = P.diagnostics(svg, task, z)
        self.assertTrue(d['impossible_boundary_contact'])
        self.assertEqual(d['impossible_boundary_contact'][0]['level'], 10)
        self.assertGreater(d['certified_max_error_pp'], 80.0)   # the edge is at 100 C, the label says 10 C

    def test_straight_segments_are_densified_not_sampled_at_endpoints_only(self):
        """PRIOR_ART.md records an older scorer that sampled only endpoints of L/H/V segments."""
        from svgpatchlab.eval.field_fidelity import extract_contours
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2 2">'
               '<path data-level="1" d="M 1 0 L 0 1" fill="none" stroke="#000"/></svg>')
        contours, _ = extract_contours(svg, np.eye(3), 0.01)
        pts = contours[0].points
        self.assertGreater(len(pts), 50)
        u = pts[:, 0] ** 2 + pts[:, 1] ** 2
        self.assertAlmostEqual(float(np.abs(u - 1).max()), 0.5, places=3)


if __name__ == '__main__':
    unittest.main()
