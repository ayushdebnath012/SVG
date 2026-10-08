"""Behavioral checks for graph control, isolation, budgets and native CAD/FEM."""
import json,tempfile,unittest,sys
from unittest.mock import patch
from io import BytesIO
from pathlib import Path
from adaptive_cad.core import Engine,Memory,Config,Node,pareto,task_input
from adaptive_cad.providers import ReplayPlanner,AstraPlanner
from adaptive_cad.verification import Verifier

TASK={'id':'t','component':'c','code':'source','instruction':'Increase box height','split':'heldout'}
def verdict(status='PASS',score=1,objectives=None):
 return {'status':status,'score':score,'objectives':objectives or [score,0,0],'diagnosis':[]}
class FakeVerifier:
 def __call__(self,task,candidate,phase='search'):
  return verdict('FAIL' if candidate=='bad' or (candidate=='fragile' and phase=='final') else 'PASS',1)

class Tests(unittest.TestCase):
 def test_final_failure_returns_to_graph(self):
  with tempfile.TemporaryDirectory() as d:
   task={**TASK,'candidate':'bad'}
   r=Engine(ReplayPlanner(['fragile','good']),FakeVerifier(),Memory(Path(d)/'memory.jsonl'),Config(max_expansions=2)).run(task)
   self.assertEqual(r['prediction'],'good');self.assertTrue(any(e['event']=='return_to_graph' for e in r['events']))
   self.assertEqual(r['status'],'PASS');self.assertTrue(Path(d,'memory.quarantine.jsonl').exists())
   self.assertFalse(Path(d,'memory.jsonl').exists())
 def test_unknown_is_not_success(self):
  class Unknown:
   def __call__(self,*a,**kw):return verdict('UNKNOWN')
  with tempfile.TemporaryDirectory() as d:
   r=Engine(ReplayPlanner(['x']),Unknown(),Memory(Path(d)/'m'),Config(max_expansions=1)).run(TASK)
   self.assertEqual(r['status'],'UNVERIFIED');self.assertIsNone(r['stored'])
 def test_path_backup_does_not_update_sibling(self):
  with tempfile.TemporaryDirectory() as d:
   engine=Engine(ReplayPlanner(['a','b','c','d']),FakeVerifier(),Memory(Path(d)/'m'),Config(max_expansions=4,max_width=2))
   r=engine.run(TASK)
   self.assertEqual(len(r['edges']),4)
   counts=[0]*len(r['edges'])
   for event in r['events']:
    if event['event']=='expand':
     for e in event['path']:counts[e]+=1
   self.assertEqual(counts,[e['visits'] for e in r['edges']])
   self.assertTrue(all(r['nodes'][e['child']]['depth']==r['nodes'][e['parent']]['depth']+1 for e in r['edges']))
 def test_graph_shared_child_has_separate_incoming_edges(self):
  with tempfile.TemporaryDirectory() as d:
   r=Engine(ReplayPlanner(['a','b','c','c']),FakeVerifier(),Memory(Path(d)/'m'),Config(max_expansions=4,max_width=2)).run(TASK)
   shared=[n for n in r['nodes'] if n['candidate']=='c']
   self.assertEqual(len(shared),1)
   incoming=[e for e in r['edges'] if e['child']==shared[0]['id']]
   self.assertEqual(len(incoming),2);self.assertEqual([e['visits'] for e in incoming],[1,1])
 def test_exact_merge_and_attempt_bound(self):
  with tempfile.TemporaryDirectory() as d:
   r=Engine(ReplayPlanner(['same']*8),FakeVerifier(),Memory(Path(d)/'m'),Config(max_expansions=8,max_depth=1,max_width=2)).run(TASK)
   self.assertEqual(len(r['nodes']),2);self.assertEqual(len(r['edges']),1)
   self.assertEqual(r['nodes'][0]['attempts'],2)
 def test_best_first_and_pareto(self):
  nodes=[Node(0,'',0,verdict(objectives=[1,0])),Node(1,'',0,verdict(objectives=[0,1])),Node(2,'',0,verdict(objectives=[0,0]))]
  self.assertEqual([n.id for n in pareto(nodes)],[0,1])
  with tempfile.TemporaryDirectory() as d:
   r=Engine(ReplayPlanner(['a','b']),FakeVerifier(),Memory(Path(d)/'m'),Config(algorithm='best-first',max_expansions=2)).run(TASK)
   self.assertEqual(r['status'],'PASS')
 def test_retrieval_isolation_and_snapshot(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'m'
   rows=[dict(task_id=i,component=c,split=s,instruction=TASK['instruction'],candidate='x',strategies=['repair'],status='PASS') for i,c,s in [('dev','other','development'),('held','other2','heldout'),('self','c','development')]]
   p.write_text(''.join(json.dumps(r)+'\n' for r in rows));m=Memory(p)
   self.assertEqual([r['task_id'] for r in m.retrieve(task_input(TASK))],['dev'])
   p.write_text('');self.assertEqual(len(m.retrieve(task_input(TASK))),1)
 def test_reference_whitelist(self):
  r=task_input({**TASK,'reference_code':'DO NOT USE','label':True,'match_strict':True})
  self.assertNotIn('reference_code',r);self.assertNotIn('label',r)
 def test_budget_stops_before_network(self):
  with tempfile.TemporaryDirectory() as d:
   p=AstraPlanner(d,budget=.000001,key='test-only')
   with self.assertRaises(StopIteration):p.call('test',{})
   self.assertEqual(p.accounting['api_calls'],0)
 def test_api_adapter_usage_and_no_retry(self):
  with tempfile.TemporaryDirectory() as d:
   provider=AstraPlanner(d,budget=1,key='test-only')
   reply={'usage':{'prompt_tokens':100,'completion_tokens':10,'prompt_tokens_details':{'cached_tokens':20,'cache_write_tokens':30}},'choices':[{'message':{'content':'{"steps": []}'},'finish_reason':'stop'}]}
   with patch('urllib.request.urlopen',return_value=BytesIO(json.dumps(reply).encode())) as mocked:
    self.assertEqual(provider.call('test',{})['steps'],[]);self.assertEqual(mocked.call_count,1)
   self.assertAlmostEqual(provider.accounting['cost_usd'],(50*10+20+30*12.5+10*50)/1e6)
   with patch('urllib.request.urlopen',side_effect=TimeoutError) as mocked:
    with self.assertRaises(TimeoutError):provider.call('test',{})
    self.assertEqual(mocked.call_count,1)
 def test_live_semantics_share_hard_budget(self):
  from adaptive_cad.live import Ledger,LivePlanner
  with tempfile.TemporaryDirectory() as d:
   ledger=Ledger(Path(d)/'ledger.json',.000001)
   planner=LivePlanner(Path(d)/'api',ledger,.000001,key='test-only')
   with patch('adaptive_cad.live.post') as post:
    with self.assertRaises(StopIteration):planner.request('semantic',[{'role':'user','content':'test'}],1000)
    post.assert_not_called()
   self.assertEqual(ledger.spent,0);self.assertEqual(ledger.outstanding,0)
 def test_astra_view_semantics(self):
  from adaptive_cad.live import ViewSemantic
  class Planner:
   def request(self,kind,messages,max_tokens,images=0):
    assert kind=='semantic' and images==1
    return '{"match":true,"confidence":0.9,"reason":"Requested shape change"}'
  with tempfile.TemporaryDirectory() as d:
   def render(source,code,path):Path(path).write_bytes(b'fixture-image');return True
   v=ViewSemantic(Planner(),d,render)
   self.assertEqual(v(TASK,'{"edits":[]}',{})['status'],'PASS')
 def test_native_cad_unknown_semantics_and_tool_limit(self):
  task=task_input({**TASK,'code':'import cadquery as cq\nresult = cq.Workplane("XY").box(10,10,10)\n'})
  v=Verifier(max_jobs=1)
  r=v(task,'{"edits":[]}');self.assertEqual(r['stages']['geometry']['status'],'PASS');self.assertEqual(r['status'],'UNKNOWN')
  r=v(task,'{"edits":[]}',phase='final');self.assertEqual(r['status'],'UNKNOWN');self.assertEqual(v.jobs,1)

if __name__=='__main__':unittest.main()
