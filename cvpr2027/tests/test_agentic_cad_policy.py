import importlib.util
import json
from pathlib import Path
import random
import unittest
p=Path(__file__).resolve().parents[1]/'scripts/agentic_cad_policy.py'
spec=importlib.util.spec_from_file_location('agentic',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class AgenticTests(unittest.TestCase):
 def test_reward_labels_never_enter_observation(self):
  row=dict(code='source',instruction='edit',candidate='patch',tools={'execute':{'gates':True},'numbers':[]},label=True,reference='SECRET',audit_iou=1,target='SECRET')
  before=[m.messages(row,s) for s in range(4)]
  row.update(label=False,reference='DIFFERENT',audit_iou=0,target='DIFFERENT')
  self.assertEqual(before,[m.messages(row,s) for s in range(4)])
  self.assertNotIn('SECRET',json.dumps(before))
 def test_tools_hidden_until_called(self):
  row=dict(code='',instruction='',candidate='',tools={'execute':'EXEC_OBS','numbers':'NUM_OBS'})
  self.assertNotIn('EXEC_OBS',json.dumps(m.messages(row,0)))
  self.assertIn('EXEC_OBS',json.dumps(m.messages(row,1)))
  self.assertNotIn('NUM_OBS',json.dumps(m.messages(row,1)))
 def test_no_repeat_and_termination(self):
  for seed in range(100):
   r=m.rollout([[.25]*4 for _ in range(4)],True,random.Random(seed))
   actions=[a for _,a in r['trace']]
   self.assertLessEqual(len(actions),3)
   self.assertIn(actions[-1],(2,3))
   self.assertEqual(len(actions[:-1]),len(set(actions[:-1])))
 def test_false_accept_penalty(self):
  self.assertEqual(m.reward(False,2,0),-2)
  self.assertEqual(m.reward(True,3,0),-1)
  self.assertLess(m.reward(True,2,2),m.reward(True,2,0))
if __name__=='__main__':unittest.main()
