import json
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cad_torus_sections as t

class TorusTests(unittest.TestCase):
 def test_horizontal_section_reduces_to_known_annular_bands(self):
  s=dict(major_radius_mm=42,tube_outer_mm=17,tube_inner_mm=11,plane_origin_mm=[0,0,5],plane_u=[1,0,0],plane_v=[0,1,0],bores=[])
  r=np.linspace(0,70,7001)[None,:];inside=t.field(s,r,np.zeros_like(r))>=0
  lo=(17**2-5**2)**.5;hi=(11**2-5**2)**.5
  expected=((r>=42-lo)&(r<=42-hi))|((r>=42+hi)&(r<=42+lo))
  np.testing.assert_array_equal(inside,expected)
 def test_refined_profiles_and_rendered_export(self):
  tasks=json.loads((t.core.ROOT/'data/cad-torus-sections/tasks.json').read_text())['tasks']
  for task in tasks:
   for p in t.profile(task,.05):self.assertLess(abs(t.field(task['spec'],p[:,0][None,:],p[:,1][None,:])).max(),.04)
   self.assertLessEqual(t.h.compare(t.h.raster(t.h.isolate(t.oracle(task))),t.mask(task))['residual_mismatch_mm2'],2)
 def test_stale_section_detected(self):
  a,b=json.loads((t.core.ROOT/'data/cad-torus-sections/tasks.json').read_text())['tasks']
  self.assertGreater(t.h.compare(t.mask(a),t.mask(b))['residual_mismatch_mm2'],2)
if __name__=='__main__':unittest.main()
