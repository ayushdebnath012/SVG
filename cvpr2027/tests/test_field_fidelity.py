import unittest
import numpy as np
from svgpatchlab.eval.field_fidelity import (score_svg, transform_matrix, extract_contours,
    element_path, sample_segments, interpolate_grid)
from svgpatchlab.core.xml import parse_svg


class FieldFidelityTests(unittest.TestCase):
    def setUp(self):
        self.x = self.y = np.linspace(-2, 2, 161)
        self.X, self.Y = np.meshgrid(self.x, self.y)

    def score(self, body, field=None, **kwargs):
        return score_svg(f'<svg xmlns="http://www.w3.org/2000/svg">{body}</svg>',
                         self.x, self.y, self.X if field is None else field, **kwargs)

    def test_chord_midpoint_false_pass_is_caught(self):
        r = self.score('<path data-level="1" d="M1 0 L0 1"/>', self.X**2+self.Y**2)
        self.assertFalse(r['geometry_pass'])
        self.assertGreater(r['max_error_pp'], 6)
        self.assertGreater(r['per_level'][0]['points'], 100)

    def test_arc_follows_circle_instead_of_chord(self):
        r = self.score('<path data-level="1" d="M1 0 A1 1 0 0 1 0 1"/>', self.X**2+self.Y**2)
        self.assertTrue(r['geometry_pass'], r)
        self.assertLess(r['max_error_pp'], .01)

    def test_ancestor_transforms_and_order(self):
        r = self.score('<g transform="translate(1 0)"><g transform="scale(.5)"><path data-level="1.5" d="M1 -1 V1"/></g></g>')
        self.assertTrue(r['geometry_pass'], r)
        np.testing.assert_allclose(transform_matrix('translate(1,2) scale(2)') @ [1,1,1], [3,4,1])

    def test_rotation_about_center(self):
        r = self.score('<g transform="rotate(90 1 1)"><path data-level="1" d="M0 1 L2 1"/></g>')
        self.assertTrue(r['geometry_pass'], r)

    def test_skew_and_matrix(self):
        for text, expected in [('skewX(45)', [3,2,1]), ('skewY(45)', [1,3,1]),
                               ('matrix(1 2 3 4 5 6)', [12,16,1])]:
            np.testing.assert_allclose(transform_matrix(text) @ [1,2,1], expected)

    def test_outside_samples_never_disappear(self):
        r = self.score('<path data-level="1" d="M1 0 L1 3"/>')
        self.assertGreater(r['invalid_points'], 0)
        self.assertFalse(r['geometry_pass'])

    def test_masked_samples_never_disappear(self):
        f = self.X.copy(); f[(self.X>0)&(self.Y>0)] = np.nan
        r = self.score('<path data-level="1" d="M1 -1 V1"/>', f)
        self.assertGreater(r['invalid_points'], 0)
        self.assertFalse(r['geometry_pass'])

    def test_missing_required_level(self):
        r = self.score('<path data-level="1" d="M1 -1 V1"/>', expected_levels=[0, 1])
        self.assertEqual(r['missing_levels'], [0.])
        self.assertFalse(r['geometry_pass'])

    def test_hidden_ancestor(self):
        r = self.score('<g style="display:none"><path data-level="1" d="M1 -1 V1"/></g>')
        self.assertFalse(r['geometry_pass'])

    def test_definitions_are_not_visible_contours(self):
        r = self.score('<defs><path data-level="1" d="M1 -1 V1"/></defs>')
        self.assertFalse(r['geometry_pass'])

    def test_stylesheet_never_certified(self):
        r = self.score('<style>path {display:none}</style><path data-level="1" d="M1 -1 V1"/>')
        self.assertFalse(r['geometry_pass'])

    def test_unsupported_transform_never_ignored(self):
        r = self.score('<path transform="bogus(3)" data-level="1" d="M1 -1 V1"/>')
        self.assertFalse(r['geometry_pass'])

    def test_nested_viewport_is_explicitly_unsupported(self):
        r = self.score('<svg viewBox="0 0 10 10"><path data-level="1" d="M1 -1 V1"/></svg>')
        self.assertFalse(r['geometry_pass'])

    def test_single_quotes_and_exponent(self):
        self.assertTrue(self.score("<path data-level='1E+0' d='M1 -1 V1'/>")['geometry_pass'])

    def test_smooth_cubic_reflects_control(self):
        a = '<path d="M0 0 C0 1 1 1 1 0 S2 -1 2 0"/>'
        b = '<path d="M0 0 C0 1 1 1 1 0 C1 -1 2 -1 2 0"/>'
        p = [sample_segments(element_path(parse_svg('<svg>'+z+'</svg>')[0]), np.eye(3), .01)[0] for z in [a,b]]
        np.testing.assert_allclose(*p)

    def test_closed_edge_sampled(self):
        r = self.score('<path data-level="1" d="M1 0 L0 1 Z"/>', self.X**2+self.Y**2)
        self.assertFalse(r['geometry_pass'])

    def test_disjoint_paths_do_not_get_connecting_segments(self):
        r = self.score('<path data-level="1" d="M1 -1 V-.5 M1 .5 V1"/>')
        self.assertAlmostEqual(r['per_level'][0]['physical_length'], 1.)

    def test_polyline_interiors_sampled(self):
        r = self.score('<polyline data-level="1" points="1,0 0,1"/>', self.X**2+self.Y**2)
        self.assertFalse(r['geometry_pass'])

    def test_physical_mapping_and_normalization(self):
        r = self.score('<path data-level="2" d="M12 10 V14"/>', 2*self.X,
                       mapping=(2,10,2,12), field_range=200)
        self.assertTrue(r['geometry_pass'], r)
        self.assertFalse(r['full_drawing_verified'])

    def test_zero_weight_masked_neighbor_is_ignored(self):
        v = interpolate_grid([0,1], [0,1], [[1,np.nan],[1,np.nan]], [[0,.5]])
        self.assertEqual(v[0], 1)

    def test_empty_and_malformed_documents_fail(self):
        for text in ['', '<svg/>', '<svg><path', '<!DOCTYPE svg><svg/>']:
            self.assertFalse(score_svg(text,self.x,self.y,self.X)['geometry_pass'])

    def test_dense_subdivision_does_not_change_mean(self):
        a = self.score('<path data-level="0" d="M0 0 L1 0"/>')
        b = self.score('<path data-level="0" d="M0 0 L.1 0 L.2 0 L1 0"/>')
        self.assertAlmostEqual(a['mean_abs_err'], b['mean_abs_err'], places=10)


if __name__ == '__main__':
    unittest.main()
