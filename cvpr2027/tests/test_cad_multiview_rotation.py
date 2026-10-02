import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cad_multiview_rotation as r

class RotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.t=json.loads((r.DATA/'tasks.json').read_text())['tasks'][0]
    def test_reference_and_stale(self):
        self.assertTrue(r.score(self.t,r.mv.oracle_patches(self.t))['geometry_pass'])
        self.assertFalse(r.score(self.t,[])['geometry_pass'])
    def test_front_view_omission_is_detected(self):
        ps=r.mv.oracle_patches(self.t);ids={r.mv.ident(f'{i}frontside{sign}') for i in range(12) for sign in (-1,1)}
        self.assertFalse(r.score(self.t,[p for p in ps if p['id'] not in ids])['geometry_pass'])
    def test_right_view_reflection_error_is_detected(self):
        ps=r.mv.oracle_patches(self.t)
        for p in ps:
            if p['id']==r.mv.ident('0rightside1'):
                p['set']['x1']+=2;p['set']['x2']+=2
        self.assertFalse(r.score(self.t,ps)['geometry_pass'])
    def test_swapping_equivalent_geometric_ids_passes(self):
        ps=r.mv.oracle_patches(self.t);a=r.mv.ident('0topcircle');b=r.mv.ident('1topcircle')
        for p in ps:
            if p['id']==a:p['id']=b
            elif p['id']==b:p['id']=a
        self.assertTrue(r.score(self.t,ps)['geometry_pass'])
    def test_numeric_tool_is_arithmetic_only(self):
        self.assertAlmostEqual(r.calculate(['cos(radians(60))'])[0],.5)
        with self.assertRaises(ValueError):r.calculate(['open("secret")'])
        with self.assertRaises(ValueError):r.calculate(['2**999999999'])

if __name__=='__main__':unittest.main()
