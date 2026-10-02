import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cad_trace_routing as r
import audit_trace_routing as audit
import tempfile

class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.t={'width':7,'height':7,'blocked':[], 'nets':[
            {'id':'A','start':[0,3],'end':[6,3]},
            {'id':'B','start':[3,0],'end':[3,6]}]}
    def test_crossing_between_vertices(self):
        g=r.grade(self.t,{'A':[[0,3],[6,3]],'B':[[3,0],[3,6]]})
        self.assertTrue(any(v['kind']=='crossing_or_contact' for v in g['violations']))
    def test_keepout_between_vertices(self):
        self.t['nets']=self.t['nets'][:1];self.t['blocked']=[[2,3]]
        self.assertFalse(r.grade(self.t,{'A':[[0,3],[6,3]]})['pass'])
    def test_reverse_and_collinear_are_valid(self):
        self.t['nets']=self.t['nets'][:1]
        self.assertTrue(r.grade(self.t,{'A':[[6,3],[4,3],[0,3]]})['pass'])
    def test_diagonal_rejected(self):
        with self.assertRaises(ValueError):r.expand([[0,0],[3,3]])
    def test_reference_and_missing_net(self):
        t=json.loads((r.DATA/'tasks.json').read_text())['tasks'][0]
        self.assertTrue(r.grade(t,t['reference_routes'])['pass'])
        routes=copy.deepcopy(t['reference_routes']);del routes['A']
        self.assertFalse(r.grade(t,routes)['pass'])
    def test_foreign_pad_and_endpoint(self):
        g=r.grade(self.t,{'A':[[0,3],[0,0],[3,0]]})
        self.assertTrue({'wrong_endpoints','foreign_pad','missing_net'} <= {v['kind'] for v in g['violations']})
    def test_continuous_audit_detects_crossing_from_svg(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'drawing.svg'
            p.write_text(r.drawing(self.t,{'A':[[0,3],[6,3]],'B':[[3,0],[3,6]]}))
            result=audit.audit(self.t,p)
            self.assertFalse(result['continuous_geometry_pass'])
            self.assertAlmostEqual(result['minimum_intertrace_edge_gap_mm'],-.6)
    def test_continuous_axis_segment_distances(self):
        self.assertEqual(audit.distance((0,0),(10,0),(5,-1),(5,1)),0)
        self.assertEqual(audit.distance((0,0),(10,0),(2,2),(8,2)),2)
        self.assertEqual(audit.distance((0,0),(1,0),(4,4),(4,6)),5)

if __name__=='__main__':unittest.main()
