"""Checks for audit admission, held-out labels and honest FEM result comparison."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

S = Path(__file__).resolve().parents[1] / 'scripts'

def module(name):
    spec = importlib.util.spec_from_file_location(name, S / (name + '.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

runner = module('published_fem_runner')
audit = module('audit_published_fem_benchmark')

class PublishedFEMChecks(unittest.TestCase):
    def setUp(self):
        self.contract = {'qois': [{'key': 'stress', 'value': -5.38, 'unit': 'MPa'}]}

    def test_signed_stress_and_equivalent_units(self):
        exact = runner.compare(self.contract, {'qois': {'stress': {'value': -5380000, 'unit': 'Pa'}}})[0]
        self.assertEqual(exact['relative_error'], 0)
        self.assertIsNone(exact['numerical_pass'])
        wrong = runner.compare(self.contract, {'qois': {'stress': {'value': 5.38, 'unit': 'MPa'}}})[0]
        self.assertEqual(wrong['relative_error'], 2)

    def test_malformed_values_and_incompatible_units(self):
        for val in [True, None, '5', float('inf'), float('nan'), 10**400]:
            row = runner.compare(self.contract, {'qois': {'stress': {'value': val, 'unit': 'MPa'}}})[0]
            self.assertEqual(row['status'], 'invalid_number')
        for unit in ['mm', None, 'stress', {}]:
            row = runner.compare(self.contract, {'qois': {'stress': {'value': 5, 'unit': unit}}})[0]
            self.assertEqual(row['status'], 'unit_mismatch')

        row = runner.compare(self.contract, {'qois': {'stress': {'value': 1e308, 'unit': 'GPa'}}})[0]
        self.assertEqual(row['status'], 'invalid_number')

    def test_zero_target_retains_absolute_error(self):
        self.contract['qois'][0]['value'] = 0
        row = runner.compare(self.contract, {'qois': {'stress': {'value': .1, 'unit': 'MPa'}}})[0]
        self.assertEqual(row['absolute_error'], .1); self.assertIsNone(row['relative_error'])

    def test_json_nonfinite_and_symlink_artifacts_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); (p/'bad.json').write_text('{"value": NaN}')
            with self.assertRaises(ValueError): runner.load(p/'bad.json')
            (p/'link').symlink_to('/etc/hosts')
            with self.assertRaises(ValueError): runner.asset_inventory(p)

    def test_ineligible_cases_cannot_be_prepared(self):
        for case in ['SFEM-00005_004_final', 'BATH-Circ_0', 'WING-Test1', 'MSHELL-31']:
            with self.assertRaises(ValueError): runner.choose(case, 'analysis_fem')

    def test_audit_and_candidates_use_only_admitted_cases(self):
        report = runner.load(audit.DATA/'audit.json'); catalog = runner.load(audit.DATA/'catalog.json')
        self.assertEqual(report['collection_case_count'], 100)
        self.assertEqual(report['admitted_source_complete_cases'], 3)
        self.assertEqual(report['certified_scored_cases'], 0)
        self.assertEqual(len(catalog['records']), 6)
        for row in catalog['records']:
            task = runner.load(audit.ROOT/row['candidate_manifest'])
            self.assertNotIn('reference_values', task)
            self.assertFalse(task['certified_scored_release'])
        audit.validate()

    def test_nastran_large_and_small_cards_are_both_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'sample.bdf'
            small = 'GRID'.ljust(8)+'1'.rjust(8)+'0'.rjust(8)+'0.'.rjust(8)+'2.-3'.rjust(8)+'0.'.rjust(8)+'\n'
            big = 'GRID*'.ljust(8)+'2'.rjust(16)+'0'.rjust(16)+'1.25'.rjust(16)+'0.'.rjust(16)+'\n'
            p.write_text(small+big+'*'.ljust(8)+'0.'.rjust(16)+'\n')
            data = audit.deck_bounds(p)
            self.assertEqual(data['node_count'], 2); self.assertEqual(data['bounds'][0], [0, 1.25])
            self.assertEqual(data['bounds'][1], [0, .002])

    def test_ingest_validates_all_paths_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); (p/'submission').mkdir(); runner.save(p/'protocol.json', {})
            for name in ['../escape.py', '/tmp/escape.py', '.secret.py', 'nested/helper.py']:
                response = p/'response.json'; runner.save(response, {'files': {'main.py': 'print(1)', name: 'bad'}})
                with self.assertRaises(ValueError): runner.ingest(p, response)
                self.assertFalse((p/'submission/main.py').exists())

    def test_report_separates_tracks_and_rejects_duplicate_attempts(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); files=[]
            for i, track in enumerate(['cad_fem', 'analysis_fem']):
                f=p/f'{i}.json';runner.save(f, dict(model='test-model', track=track, case_id='c', attempt=1,
                    family='test', status='infrastructure_blocked', qois=[]));files.append(f)
            r = runner.summarize(files)
            self.assertEqual(len(r['reports']), 2)
            self.assertIsNone(r['model_success_rate'])
            self.assertTrue(all(x['macro_family_relative_error'] is None for x in r['reports']))
            with self.assertRaises(ValueError): runner.summarize([files[0], files[0]])

    def test_exact_values_do_not_certify_execution_or_physics(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            for name in ['inputs','outputs','submission']: (p/name).mkdir()
            taskpath=p/'task.json';private=p/'contract.json';runner.save(taskpath,{})
            runner.save(private,self.contract)
            runner.save(p/'protocol.json',dict(case_id='test', track='analysis_fem', family='test', model='test', attempt=1,
                input_inventory=[], candidate_manifest_sha256=runner.sha(taskpath), evaluator_contract_sha256=runner.sha(private),
                required_artifacts=['results.json','main.py']))
            runner.save(p/'outputs/results.json',{'qois':{'stress':{'value':-5.38,'unit':'MPa'}}})
            with patch.object(runner,'choose',return_value={'candidate_manifest':str(taskpath),'private_contract':str(private)}):
                runner.score(p)
            report=runner.load(p/'score.json')
            self.assertEqual(report['qois'][0]['relative_error'],0)
            self.assertEqual(report['status'],'execution_unverified')
            self.assertIsNone(report['joint_pass']);self.assertIsNone(report['physical_validity'])

if __name__ == '__main__': unittest.main()
