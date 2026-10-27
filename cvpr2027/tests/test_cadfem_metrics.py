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

    def test_closest_point_on_triangle_matches_independent_formula(self):
        def segment(p,a,b):
            t=np.clip((p-a)@(b-a)/((b-a)@(b-a)),0,1);return np.linalg.norm(p-(a+t*(b-a)))
        def distance(p,a,b,c):
            n=np.cross(b-a,c-a);x=p-((p-a)@n)/(n@n)*n
            inside=all(np.cross(v1-v0,x-v0)@n>=0 for v0,v1 in ((a,b),(b,c),(c,a)))
            return np.linalg.norm(p-x) if inside else min(segment(p,a,b),segment(p,b,c),segment(p,c,a))
        rng=np.random.default_rng(3);a,b,c=(rng.normal(size=(2000,3)) for _ in range(3));p=rng.normal(scale=2,size=(2000,3))
        got=np.linalg.norm(m.closest_points_on_triangles(p,a,b,c)-p,axis=1)
        self.assertTrue(np.allclose(got,[distance(*x) for x in zip(p,a,b,c)],atol=1e-12))

    def test_surface_pruning_is_exact(self):
        rng=np.random.default_rng(5);tri=rng.uniform(0,10,size=(40,3,3));tri[:,:,2]*=.1
        surface=m.TriangleSurface(tri,1.5);p=rng.uniform(-5,15,size=(300,3))
        brute=np.min([np.linalg.norm(m.closest_points_on_triangles(p,*[np.repeat(t[None,k],len(p),0) for k in range(3)])-p,axis=1) for t in tri],axis=0)
        self.assertTrue(np.allclose(surface.closest(p)[0],brute,atol=1e-9))

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
            self.assertAlmostEqual(c['voxel_iou'],1);self.assertLess(c['cd_l1'],1e-9)

    def test_correct_part_outscores_wrong_part(self):
        # Point-to-point sampling once scored an identical plate (built another way) below a wrong hole.
        import cadquery as cq
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            ref=cq.Workplane('XY').box(100,60,20).faces('>Z').workplane().hole(12).val()
            same=cq.Workplane('XY').rect(100,60).extrude(10,both=True).cut(cq.Workplane('XY').circle(6).extrude(10,both=True)).val()
            wrong=cq.Workplane('XY').box(100,60,20).faces('>Z').workplane().hole(14).val()
            for name,shape in (('ref',ref),('same',same),('wrong',wrong)):cq.exporters.export(shape,str(p/(name+'.step')))
            good=m.geometry_metrics(p/'same.step',p/'ref.step',samples=5000)
            bad=m.geometry_metrics(p/'wrong.step',p/'ref.step',samples=5000)
            self.assertLess(good['cd_l1'],.01);self.assertEqual(good['surface_f1'],1)
            self.assertGreater(bad['cd_l1'],10*good['cd_l1']);self.assertLess(bad['surface_f1'],good['surface_f1'])
            self.assertGreater(bad['hausdorff'],.9)

    def test_extra_feature_does_not_shift_pose(self):
        import cadquery as cq
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);plate=cq.Workplane('XY').box(100,60,20)
            boss=plate.faces('>X').workplane().circle(5).extrude(20).val()
            cq.exporters.export(plate.val(),str(p/'plate.step'));cq.exporters.export(boss,str(p/'boss.step'))
            cq.exporters.export(boss.rotate((0,0,0),(0,0,1),90).translate((7,-3,0)),str(p/'moved.step'))
            fixed=m.geometry_metrics(p/'boss.step',p/'plate.step',samples=4000)
            posed=m.geometry_metrics(p/'moved.step',p/'plate.step',samples=4000,pose='translation_and_24_proper_rotations')
            self.assertAlmostEqual(posed['brep_volume_iou'],fixed['brep_volume_iou'],places=3)

    def test_multi_root_step_keeps_every_body(self):
        import cadquery as cq
        from OCP.STEPControl import STEPControl_Writer,STEPControl_AsIs
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);a=cq.Workplane('XY').box(10,10,10).val();b=a.translate((30,0,0))
            writer=STEPControl_Writer()
            for shape in (a,b):writer.Transfer(shape.wrapped,STEPControl_AsIs)
            writer.Write(str(p/'roots.step'));cq.exporters.export(cq.Compound.makeCompound([a,b]),str(p/'compound.step'))
            r=m.geometry_metrics(p/'roots.step',p/'compound.step',samples=1000)
            self.assertEqual(r['candidate_solids'],2);self.assertAlmostEqual(r['brep_volume_iou'],1,places=7)


if __name__=='__main__':unittest.main()
