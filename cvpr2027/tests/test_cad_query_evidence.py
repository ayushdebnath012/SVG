import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from cad_query_evidence import query_evidence, panel_example


class QueryEvidenceTests(unittest.TestCase):
    def test_ambiguous_design_has_identifiable_and_nonidentifiable_queries(self):
        d=panel_example();q=d['queries']
        self.assertEqual(q['pitch_mm']['status'],'identifiable')
        self.assertEqual(q['pitch_mm']['range'],[36.,36.])
        h=q['first_hole_x_mm']
        self.assertEqual(h['status'],'ambiguous')
        self.assertEqual(h['range'],[9.5,80.5])
        for x in h['witnesses']:
            np.testing.assert_allclose(np.array(d['A'])@x,d['b'])
        for cert in h['bound_certificates']:
            np.testing.assert_allclose(cert['minimized_cost'],
                np.array(d['A']).T@cert['equality_multipliers']+
                np.array(cert['lower_bound_multipliers'])+
                np.array(cert['upper_bound_multipliers']))
            self.assertLess(cert['primal_dual_gap'],1e-8)
        self.assertEqual(q['left_edge_clearance_mm']['check'],'satisfied_for_all')
        self.assertEqual(q['minimum_40mm_pitch']['check'],'violated_for_all')
        self.assertEqual(q['hole1_must_be_at_least_30mm_from_datum']['check'],'depends_on_interpretation')
        self.assertEqual(q['after_explicit_left_anchor']['range'],[18.,18.])

    def test_inconsistency_cannot_vacuously_certify(self):
        r=query_evidence([[1],[1]],[1,2],[(None,None)],[1],minimum=0)
        self.assertEqual(r['status'],'inconsistent')
        self.assertEqual(r['check'],'not_evaluated')

    def test_unbounded_is_not_a_finite_ambiguity_certificate(self):
        r=query_evidence([],[],[(None,None)],[1])
        self.assertEqual(r['status'],'unbounded')

    def test_negative_coordinates_not_silently_clamped(self):
        r=query_evidence([[1]],[-2],[(None,None)],[1])
        self.assertEqual(r['range'],[-2.,-2.])

    def test_bounds_can_make_query_identifiable_despite_rank_deficiency(self):
        r=query_evidence([],[],[(3,3)],[1])
        self.assertEqual(r['status'],'identifiable')
        self.assertEqual(r['range'],[3.,3.])


if __name__=='__main__':unittest.main()
