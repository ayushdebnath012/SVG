"""Numerical and geometry regression checks; test solids are not benchmark data."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cadfem_metrics as m


class MetricTests(unittest.TestCase):
    def test_chamfer_conventions(self):
        p=np.array([[0.,0.,0.],[0.,10.,0.]])
        r=m.surface_metrics(p,p+[2,0,0],10,threshold_fraction=.1)
        self.assertAlmostEqual(r['cd_l1'],2)
        self.assertAlmostEqual(r['cd_l2_squared'],4)
        self.assertAlmostEqual(r['cd_l1_over_reference_diagonal'],.2)
        self.assertEqual(r['surface_f1'],0)

    def test_surface_identical(self):
        p=np.array([[0,0,0],[1,2,3]])
        d=m.surface_metrics(p,p,4)
        self.assertEqual(d['cd_l1'],0);self.assertEqual(d['surface_f1'],1)

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):m.surface_metrics([[np.nan,0,0]],[[0,0,0]],1)
        with self.assertRaises(ValueError):m.field_metrics([np.inf],[0],[1])

    def test_edit_noop_and_perfect(self):
        self.assertEqual(m.edit_headroom(.8,.8),0)
        self.assertEqual(m.edit_headroom(1,.8),1)
        self.assertIsNone(m.edit_headroom(1,1))

    def test_feature_f1(self):
        self.assertAlmostEqual(m.feature_prf(2,3,2)['f1'],.8)
        self.assertIsNone(m.feature_prf(0,0,0)['f1'])

    def test_operation_recall(self):
        self.assertEqual(m.essential_operation_recall(['extrude'],['extrude','sweep']),.5)

    def test_qoi_near_zero(self):
        self.assertTrue(m.qoi_metrics(.001,0,atol=.002,rtol=.01)['within_tolerance'])
        self.assertFalse(m.qoi_metrics(.003,0,atol=.002,rtol=.01)['within_tolerance'])
        self.assertIsNone(m.qoi_metrics(-2,2,atol=.1,rtol=.01)['positive_log_ratio_error'])
        with self.assertRaises(ValueError):m.qoi_metrics(True,1,atol=0,rtol=.1)
        with self.assertRaises(ValueError):m.qoi_metrics('1',1,atol=0,rtol=.1)

    def test_weighted_field_not_node_average(self):
        r=m.field_metrics([2,1],[1,1],[1,9])
        self.assertAlmostEqual(r['weighted_relative_l2'],np.sqrt(.1))
        with self.assertRaises(ValueError):m.field_metrics([1,2],[1,2],[1,0])

    def test_zero_field_relative_undefined(self):
        r=m.field_metrics([1],[0],[1])
        self.assertIsNone(r['weighted_relative_l2']);self.assertEqual(r['weighted_absolute_l2'],1)

    def test_energy_norm(self):
        r=m.energy_error([2,2],[1,1],np.diag([2,3]))
        self.assertAlmostEqual(r['relative_energy_error'],1)
        with self.assertRaises(np.linalg.LinAlgError):m.energy_error([1],[1],[[-1]])

    def test_force_and_moment(self):
        r=m.force_moment_balance([[0,0,0],[1,0,0]],[[1,0,0],[-1,0,0]],np.zeros((2,3)),1)
        self.assertEqual(r['relative_force_imbalance'],0);self.assertEqual(r['relative_moment_imbalance'],0)
        r=m.force_moment_balance([[0,0,0],[1,0,0]],[[0,1,0],[0,-1,0]],np.zeros((2,3)),1)
        self.assertGreater(r['relative_moment_imbalance'],0)

    def test_mac_sign_and_scale(self):
        self.assertAlmostEqual(m.modal_assurance([2,4],[-1,-2]),1)
        self.assertEqual(m.modal_assurance([1,0],[0,1]),0)

    def test_gci_is_not_certification(self):
        r=m.convergence_diagnostic([4,2,1],[17,5,2])
        self.assertAlmostEqual(r['observed_order'],2)
        self.assertFalse(r['convergence_certified'])
        self.assertFalse(m.convergence_diagnostic([4,2,1],[1,2,1])['richardson_assumptions_met'])

    def test_missing_review_never_passes(self):
        r=m.joint_verdict({'geometry':True},['geometry','workflow'],reference_ready=True)
        self.assertFalse(r['joint_pass']);self.assertEqual(r['status'],'unverified')
        self.assertFalse(m.joint_verdict({'geometry':False},['geometry'],reference_ready=True)['joint_pass'])
        self.assertIsNone(m.joint_verdict({},['geometry'],reference_ready=False)['joint_pass'])
        with self.assertRaises(ValueError):m.joint_verdict({'x':'true'},['x'],reference_ready=True)

    def test_family_balance(self):
        rows=[{'eligible':True,'engineering_family':'bracket','joint_pass':True} for _ in range(10)]
        rows.append({'eligible':True,'engineering_family':'contact','joint_pass':False})
        r=m.family_macro(rows)
        self.assertEqual(r['family_macro'],.5);self.assertAlmostEqual(r['task_micro'],10/11)

    def test_weighted_stress_percentile(self):
        self.assertEqual(m.weighted_quantile([1,100],[99,1],.95),1)

    def test_cube_rotations(self):
        rotations=list(m.proper_rotations());self.assertEqual(len(rotations),24)
        self.assertTrue(all(np.isclose(np.linalg.det(x),1) for x in rotations))

    def test_benchcad2_terms_are_separate_from_engineering_pass(self):
        r=m.benchcad2_part_terms(.75,.5,[1,0,0],[1,0,0])
        self.assertAlmostEqual(r['part_v1_from_supplied_terms'],.6)
        self.assertIsNone(r['engineering_pass'])
        self.assertFalse(r['official_geometry_pipeline_reproduced'])
        self.assertAlmostEqual(m.benchcad2_part_terms(1,.5,[1,0,0],[1,1,0])['topology_count_score'],.25)
        self.assertEqual(m.benchcad2_part_terms(1,1,[1,0,0],[1,0,0])['part_v1_from_supplied_terms'],1)
        with self.assertRaises(ValueError):m.benchcad2_part_terms(1,.5,[1,True,0],[1,0,0])


class GeometryTests(unittest.TestCase):
    def test_scale_error_not_aligned_away(self):
        import cadquery as cq
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);ref=cq.Workplane('XY').box(10,20,30).val()
            cq.exporters.export(ref,str(p/'ref.step'))
            cq.exporters.export(ref.scale(1.03),str(p/'scaled.step'))
            r=m.geometry_metrics(p/'scaled.step',p/'ref.step',samples=500,pose='translation_and_24_proper_rotations')
            self.assertLess(r['brep_volume_iou'],.92)
            self.assertGreater(r['relative_volume_error'],.09)

    def test_identity_and_allowed_pose(self):
        import cadquery as cq
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);ref=cq.Workplane('XY').box(10,20,30).val()
            cq.exporters.export(ref,str(p/'ref.step'))
            rotated=ref.rotate((0,0,0),(0,0,1),90).translate((40,60,2))
            cq.exporters.export(rotated,str(p/'rotated.step'))
            a=m.geometry_metrics(p/'rotated.step',p/'ref.step',samples=500,pose='fixed')
            b=m.geometry_metrics(p/'rotated.step',p/'ref.step',samples=500,pose='translation_and_24_proper_rotations')
            self.assertAlmostEqual(a['brep_volume_iou'],0)
            self.assertAlmostEqual(b['brep_volume_iou'],1,places=7)
            c=m.geometry_metrics(p/'ref.step',p/'ref.step',samples=500,voxel_resolution=6)
            self.assertAlmostEqual(c['voxel_iou'],1);self.assertEqual(c['cd_l1'],0)


if __name__=='__main__':unittest.main()
