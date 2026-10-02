import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cad_flattened_multiview as f

class CompoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.t=json.loads((f.DATA/'tasks.json').read_text())['tasks'][0]
    def test_reference_and_unedited(self):
        self.assertEqual(f.score(self.t,f.oracle(self.t))['outcome'],'pass')
        self.assertFalse(f.score(self.t,[])['geometry_pass'])
    def test_subpath_order_irrelevant(self):
        ps=f.oracle(self.t)
        for p in ps:
            if 'd' in p['set']:
                path=f.parse_path(p['set']['d']);p['set']['d']=' '.join(q.d() for q in reversed(path.continuous_subpaths()))
        self.assertTrue(f.score(self.t,ps)['geometry_pass'])
    def test_missing_view_rejected(self):
        ps=f.oracle(self.t);eid=self.t['source_shape_ids'][-1];ps=[p for p in ps if p['id']!=eid]
        self.assertFalse(f.score(self.t,ps)['geometry_pass'])

if __name__=='__main__':unittest.main()
