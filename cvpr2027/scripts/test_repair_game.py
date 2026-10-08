"""Repair-game controls, counterexample feedback and native feature evidence."""
import json
import tempfile
import unittest
from pathlib import Path

from adaptive_cad.core import Config, Engine, Memory, task_input
from adaptive_cad.providers import ReplayPlanner
from adaptive_cad.repair_game import AdversarialVerifier, CATEGORIES, feature_graph
from adaptive_cad.verification import Verifier


class Planner:
    def __init__(self, answers):
        self.answers = iter(answers)
        self.calls = 0

    def call(self, *args):
        self.calls += 1
        return next(self.answers)


PASS = {'status': 'PASS', 'coverage': CATEGORIES, 'counterexamples': []}
FAIL = {'status': 'FAIL', 'coverage': CATEGORIES, 'counterexamples': [
    {'category': 'placement', 'reason': 'Hole is on the wrong face',
     'evidence': 'Candidate selects <Z; instruction asks for the upper face'}]}
TASK = {'id': 'game', 'code': 'import cadquery as cq\nresult = cq.Workplane("XY").box(10,10,10)',
        'instruction': 'Increase height to 20', 'constraints': [{'metric': 'bbox_z', 'equals': 20}],
        'semantics': {'mode': 'explicit_constraints', 'complete': True},
        'required': ['geometry', 'constraints', 'semantics']}


class Tests(unittest.TestCase):
    def test_feature_order_and_dependencies(self):
        graph = feature_graph('p = cq.Workplane("XY").box(10, 20, 30)\nresult = p.faces(">Z").workplane().hole(3)')
        self.assertEqual([r['operation'] for r in graph['calls']], ['Workplane', 'box', 'faces', 'workplane', 'hole'])
        self.assertIn(1, graph['calls'][2]['dependencies'])
        self.assertIn(3, graph['calls'][4]['dependencies'])
        self.assertEqual(graph['calls'][2]['parameters'], ["'>Z'"])
        self.assertEqual(feature_graph('result = (')['status'], 'FAIL')

    def test_fail_closed_and_fresh_final_attack(self):
        planner = Planner([PASS, FAIL])
        attack = AdversarialVerifier(planner)
        self.assertEqual(attack(TASK, 'patch', {'phase': 'search'})['status'], 'PASS')
        self.assertEqual(attack(TASK, 'patch', {'phase': 'search'})['status'], 'PASS')
        self.assertEqual(planner.calls, 1)
        self.assertEqual(attack(TASK, 'patch', {'phase': 'final'})['status'], 'FAIL')
        for malformed in [{'status': 'PASS', 'coverage': [], 'counterexamples': []},
                          {'status': 'PASS', 'coverage': CATEGORIES, 'counterexamples': 'none'},
                          {'status': 'FAIL', 'coverage': CATEGORIES, 'counterexamples': []}]:
            self.assertEqual(AdversarialVerifier(Planner([malformed]))(TASK, 'x', {})['status'], 'UNKNOWN')

    def test_counterexample_returns_to_repair_and_blocks_physics(self):
        class Native(Verifier):
            def native(self, task, candidate, phase, stage, export_path=None):
                self.assert_geometry(stage)
                return {'geometry': {'status': 'PASS', 'metrics': {'volume': 2000}},
                        'constraints': {'status': 'PASS'}, 'edited_lines': 1,
                        'features': {'candidate': feature_graph('result = cq.box(10,10,20)')}}

            def assert_geometry(self, stage):
                if stage != 'geometry': raise AssertionError('Physics ran before attack passed')

        class Repairs(ReplayPlanner):
            def generate(self, *args):
                self.feedback = args[-1]
                return super().generate(*args)

        def attack(task, candidate, tools):
            return FAIL if candidate == 'wrong' else PASS

        with tempfile.TemporaryDirectory() as directory:
            blocked = Native(adversarial=attack)(task_input({**TASK, 'fem': {'required': True}}), 'wrong')
            self.assertEqual(blocked['status'], 'FAIL')
            self.assertEqual(blocked['stages']['fem']['status'], 'UNKNOWN')
            planner = Repairs(['fixed'])
            result = Engine(planner, Native(adversarial=attack), Memory(Path(directory)/'memory'),
                            Config(max_expansions=1)).run({**TASK, 'candidate': 'wrong'})
            self.assertEqual(result['prediction'], 'fixed')
            self.assertEqual(planner.feedback[0]['counterexamples'][0]['category'], 'placement')
            self.assertEqual(result['status'], 'PASS')

    def test_native_pipeline(self):
        patch = json.dumps({'edits': [{'start': 1, 'delete': 1,
                            'insert': ['result = cq.Workplane("XY").box(10,10,20)']}]})
        verifier = Verifier(adversarial=AdversarialVerifier(Planner([PASS, PASS])))
        task = task_input(TASK)
        result = verifier(task, patch)
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual(verifier(task, patch, phase='final')['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
