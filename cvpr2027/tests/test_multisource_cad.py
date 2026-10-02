import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from cad_edit_contracts import apply,validate_sequence
from cad_editor_geometry import execute_sequence
import numpy as np
class NativeCADChecks(unittest.TestCase):
 def test_analytic_box_and_native_cut(self):
  p=Path(__file__).resolve().parents[1]/'data/cad-editor-pilot/train.jsonl';r=json.loads(p.read_text().splitlines()[0]);b=execute_sequence(r['original_sequence']);width=56/63*2*(24/63*1.4);height=28/63*2*(24/63*1.4);depth=2/63
  self.assertAlmostEqual(b.Volume(),width*height*depth,places=7)
  cut=execute_sequence(r['target']);self.assertTrue(cut.isValid());self.assertLess(cut.Volume(),b.Volume())
 def test_analytic_circle_extrusion(self):
  s='circle,1,31,61,31,31,1,31,61 <curve_end> <loop_end> <face_end> <sketch_end> add,0,63,31,31,31,1,0,0,0,1,0,0,0,1,63,31,31 <extrude_end>'
  b=execute_sequence(s);self.assertAlmostEqual(b.Volume(),np.pi*(60/63*1.4)**2*2,places=5)
 def test_bad_patch_and_nonintegral_syntax_rejected(self):
  with self.assertRaises(ValueError):apply('x=1\n',{'edits':[{'start':2,'delete':0,'insert':[]}]},'cadquery')
  with self.assertRaises(ValueError):validate_sequence('line,1.2,3 <curve_end> <extrude_end>')
if __name__=='__main__':unittest.main()
