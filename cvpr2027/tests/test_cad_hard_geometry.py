import json
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cad_hard_geometry as h

class GeometryOracleTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.tasks=json.loads((h.core.ROOT/'data/cad-hard-geometry/tasks.json').read_text())['tasks']
 def test_svg_exports_match_independent_material_membership(self):
  for task in self.tasks:
   with self.subTest(task=task['id']):
    measured=h.compare(h.raster(h.isolate(h.oracle_svg(task))),h.reference_mask(task))
    self.assertLessEqual(measured['residual_mismatch_mm2'],2,measured)
 def test_gear_pitch_thickness_and_tooth_count(self):
  s=self.tasks[0]['spec'];rp,rb,ra,rf=h.gear_radii(s);phase=np.deg2rad(s['phase_deg']);half=np.pi/(2*s['teeth'])
  angles=phase+np.array([half-.00001,half+.00001]);mask=h.gear_mask(s,rp*np.cos(angles),rp*np.sin(angles));self.assertEqual(mask.tolist(),[True,False])
  angles=np.linspace(0,2*np.pi,23000,endpoint=False);mask=h.gear_mask(s,(ra-.1)*np.cos(angles),(ra-.1)*np.sin(angles));self.assertEqual(np.count_nonzero(mask&~np.roll(mask,1)),s['teeth'])
 def test_cam_normal_offset_and_refinement(self):
  for task in self.tasks:
   if task['family']!='roller_cam':continue
   s=task['spec'];points=h.cam_curve(s,7200);pitch0=s['base_radius_mm']+s['roller_radius_mm']
   self.assertAlmostEqual(points[0,0],pitch0-s['roller_radius_mm']);self.assertAlmostEqual(points[0,1],0)
   coarse=h.cam_curve(s,360);from scipy.spatial import cKDTree
   # Common sample angles match exactly; export chord error separately checked by rendered reference.
   self.assertLess(cKDTree(points).query(coarse)[0].max(),1e-9)
 def test_section_ellipses_match_cylinder_distance(self):
  for task in self.tasks:
   if task['family']!='oblique_manifold_section':continue
   s=task['spec'];O,E=h.basis(s);np.testing.assert_allclose(E.T@E,np.eye(2),atol=1e-12)
   for (c,r,V),b in zip(h.section_ellipses(s),s['bores']):
    angles=np.linspace(0,2*np.pi,101);local=c[:,None]+V@(r[:,None]*np.array([np.cos(angles),np.sin(angles)]));p=O[:,None]+E@local
    d=np.array(b['axis'],dtype=float);d/=np.linalg.norm(d);v=p-np.array(b['point_mm'])[:,None];distance=np.sqrt((v*v).sum(axis=0)-(d@v)**2)
    np.testing.assert_allclose(distance,b['radius_mm'],atol=1e-9)
 def test_stale_and_pitch_curve_controls_fail(self):
  for original,edit in zip(self.tasks[::2],self.tasks[1::2]):
   self.assertGreater(h.compare(h.reference_mask(original),h.reference_mask(edit))['residual_mismatch_mm2'],2)
  task=self.tasks[2];actual=h.reference_mask(task);shift=np.roll(actual,8,axis=1)
  self.assertGreater(h.compare(shift,actual)['residual_mismatch_mm2'],2)
 def test_missing_geometry_and_external_assets_excluded(self):
  for svg in ['<svg viewBox="0 0 1000 1000"/>','<svg viewBox="0 0 1000 1000"><g data-geometry="part"><image href="https://example.com/a.png"/></g></svg>']:
   self.assertEqual(h.score(self.tasks[0],json.dumps(dict(svg=svg,analysis={})))['outcome'],'unscored_format')

if __name__=='__main__':unittest.main()
