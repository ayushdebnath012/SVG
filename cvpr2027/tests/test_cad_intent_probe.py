import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cad_intent_probe as p

class IntentProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.tasks=json.loads((p.DATA/'tasks.json').read_text())['tasks']
    def test_oracles_pass(self):
        for t in self.tasks:self.assertEqual(p.score(t,p.oracle_patches(t))['outcome'],'pass')
    def test_same_initial_geometry_different_correct_edits(self):
        a,b=self.tasks[0],self.tasks[2]
        sa,sb=p.inspect(a['svg']),p.inspect(b['svg']);ta,tb=p.inspect(a['target_svg']),p.inspect(b['target_svg'])
        self.assertEqual([sa[k]['points'] for k in a['shape_ids']],[sb[k]['points'] for k in b['shape_ids']])
        self.assertNotEqual([ta[k]['points'] for k in a['shape_ids']],[tb[k]['points'] for k in b['shape_ids']])
    def test_nested_coordinates_preserve_world_geometry(self):
        for a,b in [(self.tasks[0],self.tasks[1]),(self.tasks[2],self.tasks[3])]:
            aa,bb=p.inspect(a['svg']),p.inspect(b['svg'])
            for eid in aa:
                import numpy as np
                self.assertLess(np.max(np.abs(np.array(aa[eid]['points'])-np.array(bb[eid]['points']))),1e-8)
    def test_wrong_intent_fails_geometry(self):
        t=self.tasks[2];wrong=p.oracle_patches(self.tasks[0])
        self.assertTrue(p.score(t,wrong)['geometry_errors'])
    def test_geometry_only_edit_leaves_annotation_errors(self):
        t=self.tasks[2];patches=[a for a in p.oracle_patches(t) if a['id'] in t['shape_ids']]
        result=p.score(t,patches);self.assertFalse(result['geometry_errors']);self.assertTrue(result['annotation_errors'])
    def test_visibility_cannot_be_changed_to_hide_failure(self):
        t=self.tasks[0]
        with self.assertRaises(ValueError):p.apply(t['svg'],[{'id':t['shape_ids'][0],'set':{'opacity':0}}])

if __name__=='__main__':unittest.main()
