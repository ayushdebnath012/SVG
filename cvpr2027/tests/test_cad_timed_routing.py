import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cad_timed_routing as t

class TimedRoutingTests(unittest.TestCase):
    def test_reference(self):
        task=json.loads((t.DATA/'tasks.json').read_text())['tasks'][0]
        self.assertTrue(t.grade(task,task['reference_routes'])['pass'])
    def test_wrong_length(self):
        task={'width':5,'height':5,'blocked':[],'nets':[{'id':'A','start':[0,0],'end':[4,0]}],'length_targets_mm':{'A':12},'locked_routes':{}}
        self.assertFalse(t.grade(task,{'A':[[0,0],[4,0]]})['pass'])
        self.assertTrue(t.grade(task,{'A':[[0,0],[0,1],[4,1],[4,0]]})['pass'])
    def test_retrace_cannot_fake_length(self):
        task={'width':5,'height':5,'blocked':[],'nets':[{'id':'A','start':[0,0],'end':[4,0]}],'length_targets_mm':{'A':12},'locked_routes':{}}
        result=t.grade(task,{'A':[[0,0],[1,0],[0,0],[4,0]]})
        self.assertTrue(any(v['kind']=='self_contact_or_retrace' for v in result['violations']))
    def test_locked_reversal_and_change(self):
        task={'width':5,'height':5,'blocked':[],'nets':[{'id':'A','start':[0,1],'end':[4,1]}],'length_targets_mm':{'A':12},'locked_routes':{'A':[[0,1],[0,0],[4,0],[4,1]]}}
        self.assertTrue(t.grade(task,{'A':task['locked_routes']['A'][::-1]})['pass'])
        result=t.grade(task,{'A':[[0,1],[0,2],[4,2],[4,1]]})
        self.assertTrue(any(v['kind']=='changed_locked_trace' for v in result['violations']))

if __name__=='__main__':unittest.main()
