"""Behavior checks for held-out contracts, malformed results and candidate delivery."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
S=Path(__file__).resolve().parents[1]/'scripts'
def module(name):
 spec=importlib.util.spec_from_file_location(name,S/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
runner=module('engineering_fem_runner');builder=module('build_engineering_fem_benchmark')
class BenchmarkChecks(unittest.TestCase):
 def setUp(self):
  self.contract={'qois':[{'key':'s','value':-5.38,'unit':'MPa','reference_kind':'published_benchmark'}],'diagnostic_relative_bands':[.01,.05]}
 def test_sign_error_is_not_hidden_by_magnitudes(self):
  r=runner.compare(self.contract,{'qois':{'s':{'value':5.38,'unit':'MPa'}}})
  self.assertEqual(r['qois'][0]['relative_error'],2);self.assertIsNone(r['joint_pass'])
 def test_unit_mismatch_rejected(self):
  r=runner.compare(self.contract,{'qois':{'s':{'value':-5.38e6,'unit':'Pa'}}});self.assertEqual(r['qois'][0]['status'],'unit_mismatch')
 def test_nonfinite_bool_and_missing_units(self):
  for v in [True,float('nan'),float('inf')]:
   self.assertEqual(runner.compare(self.contract,{'qois':{'s':{'value':v,'unit':'MPa'}}})['qois'][0]['status'],'invalid_or_missing_number')
  self.assertEqual(runner.compare(self.contract,{'qois':{'s':{'value':-5.38}}})['qois'][0]['status'],'missing_unit')
 def test_zero_reference_reports_absolute_error(self):
  self.contract['qois'][0]['value']=0
  r=runner.compare(self.contract,{'qois':{'s':{'value':.1,'unit':'MPa'}}})['qois'][0]
  self.assertEqual(r['absolute_error'],.1);self.assertIsNone(r['relative_error'])
 def test_exact_match_does_not_certify_physics(self):
  r=runner.compare(self.contract,{'qois':{'s':{'value':-5.38,'unit':'MPa'}}})
  self.assertFalse(r['physics_verified']);self.assertFalse(r['geometry_verified']);self.assertIsNone(r['joint_pass'])
 def test_path_traversal_and_input_overwrite_fail_before_writes(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t);(out/'workspace').mkdir();runner.save(out/'protocol.json',{'input_files':[{'path':'task.md'}]})
   for bad in ['../escape','/tmp/escape','task.md','home','a/b.py']:
    with self.assertRaises(ValueError):runner.materialize(out,json.dumps({'files':{'main.py':'print(1)',bad:'bad'}}))
    self.assertFalse((out/'workspace/main.py').exists())
 def test_candidate_tracks_do_not_receive_private_answers(self):
  catalog=runner.load(builder.DATA/'catalog.json')
  self.assertEqual(len(catalog['records']),14)
  for row in catalog['records']:
   p=builder.ROOT/row['candidate_manifest'];task=runner.load(p)
   self.assertFalse(task['scored_release']);self.assertNotIn('qois',task);self.assertNotIn('source_url',task)
   for f in task['files']:
    self.assertEqual(runner.sha(p.parent/f['path']),f['sha256']);self.assertNotEqual(Path(f['path']).suffix,'.fee')
    if row['track']=='cad_fem':self.assertNotIn(Path(f['path']).suffix,['.geo','.step'])
 def test_published_analytical_reference_constraints(self):
  case=next(c for c in builder.seeds() if c['id']=='ENGFEM-COUPLED');q={r['key']:r['value'] for r in builder.analytic_reference(case)}
  self.assertEqual(q['T_q1'],0);self.assertEqual(q['u_q0'],0);self.assertEqual(q['v_q0'],0);self.assertEqual(q['w_q0'],0)
  self.assertAlmostEqual(q['u_q2'],7.7);self.assertAlmostEqual(q['v_q2'],-.135);self.assertAlmostEqual(q['w_q2'],-.185)
if __name__=='__main__':unittest.main()
