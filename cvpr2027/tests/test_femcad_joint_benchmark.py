"""Protocol tests only: byte fixtures are not engineering tasks or FEM results."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from inspect_femcad_joint_submission import inspect, REQUIRED


class SubmissionChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        artifacts={}
        for key in REQUIRED:
            p=self.root/(key+'.fixture');p.write_text('Protocol byte fixture for '+key)
            artifacts[key]={'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        self.manifest={'task_id':'FEMCAD-ADV-011','artifacts':artifacts,
          'lineage':{'mesh_parent_cad_sha256':artifacts['cad']['sha256'],
            'solver_parent_mesh_sha256':artifacts['mesh']['sha256'],
            'results_parent_solver_input_sha256':artifacts['solver_input']['sha256']},
          'formulation':'2d-plane-strain','units':{'length':'mm'},'solver':{'name':'protocol-fixture','version':'fixture'},
          'physical_regions':[{'name':'fixture','cad_entity_ids':['fixture'],'mesh_group_ids':['fixture']}],'reproduction_steps':['protocol fixture; not executable']}
        self.write()
    def write(self):(self.root/'submission.json').write_text(json.dumps(self.manifest))
    def tearDown(self):self.temp.cleanup()
    def test_consistent_hashes_never_become_fem_pass(self):
        r=inspect(self.root,'FEMCAD-ADV-011');self.assertEqual(r['status'],'artifact_consistency_verified');self.assertIsNone(r['joint_pass']);self.assertIsNone(r['solver_convergence'])
    def test_wrong_parent_mesh_rejected(self):
        self.manifest['lineage']['solver_parent_mesh_sha256']='0'*64;self.write()
        self.assertEqual(inspect(self.root)['status'],'invalid_submission')
    def test_tampered_artifact_rejected(self):
        (self.root/'results.fixture').write_text('modified');self.assertEqual(inspect(self.root)['status'],'invalid_submission')
    def test_path_escape_rejected(self):
        self.manifest['artifacts']['cad']['path']='../outside';self.write()
        self.assertEqual(inspect(self.root)['status'],'invalid_submission')
    def test_empty_submission_rejected(self):
        (self.root/'submission.json').write_text('{}');self.assertEqual(inspect(self.root)['status'],'invalid_submission')
    def test_task_swap_rejected(self):
        self.assertEqual(inspect(self.root,'FEMCAD-ADV-001')['status'],'invalid_submission')

if __name__=='__main__':unittest.main()
