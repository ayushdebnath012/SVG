import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cad_multiview_probe as p

class MultiviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.tasks=json.loads((p.DATA/'tasks.json').read_text())['tasks']
    def test_oracles_pass(self):
        for t in self.tasks:self.assertEqual(p.score(t,p.oracle_patches(t))['outcome'],'pass')
    def test_equivalent_through_note(self):
        t=self.tasks[0];ps=p.oracle_patches(t)
        for patch in ps:
            if 'text' in patch:patch['text']=patch['text'].replace('THRU','THROUGH')
        self.assertEqual(p.score(t,ps)['outcome'],'pass')
    def test_wrong_diameter_note_is_not_normalized(self):
        t=self.tasks[0];ps=p.oracle_patches(t)
        for patch in ps:
            if 'text' in patch:patch['text']=patch['text'].replace('14','16')
        self.assertEqual(p.score(t,ps)['outcome'],'annotation_failure')
    def test_retained_blind_bottom_edges_fail(self):
        t=self.tasks[0];ps=[x for x in p.oracle_patches(t) if not x.get('remove')]
        self.assertEqual(p.score(t,ps)['outcome'],'geometry_failure')
    def test_incorrect_right_view_translation_fails(self):
        t=self.tasks[0];ps=p.oracle_patches(t)
        i=next(i for i,h in enumerate(t['hidden_features']) if h['kind']=='B')
        eid=p.ident(f'{i}rightside1')
        patch=next(x for x in ps if x['id']==eid)
        patch['set']['x1']+=12;patch['set']['x2']+=12
        self.assertEqual(p.score(t,ps)['outcome'],'geometry_failure')

if __name__=='__main__':unittest.main()
