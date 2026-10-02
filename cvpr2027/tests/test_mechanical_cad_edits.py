import importlib.util
import json
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/build_mechanical_cad_edits.py'
spec = importlib.util.spec_from_file_location('mechanical_builder', SCRIPT)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class MechanicalEditTests(unittest.TestCase):
    def row(self, code, difficulty='hard'):
        return dict(code=code, difficulty=difficulty)

    def test_exact_localized_edit_with_unicode(self):
        code = ('import cadquery as cq\n'
                'result = cq.Workplane("XY").box(20,30,10).union(cq.Workplane("XY").box(10,10,10))'
                '.faces(">Z").workplane().hole(4).faces("<Z").workplane().hole(2)\n'
                '# dimension µ unchanged')
        edits = builder.candidates(self.row(code))
        self.assertEqual(len(edits), 2)
        for edit in edits:
            patch = json.loads(edit['target'])
            lines = code.splitlines()
            self.assertEqual(lines[patch['line'] - 1], patch['old'])
            lines[patch['line'] - 1] = patch['new']
            self.assertEqual('\n'.join(lines), edit['edited_code'])
            self.assertIn('# dimension µ unchanged', edit['edited_code'])
            self.assertNotEqual(builder.normalized(code), builder.normalized(edit['edited_code']))

    def test_simple_primitive_excluded(self):
        self.assertEqual(builder.candidates(self.row('result=cq.Workplane("XY").box(10,10,10)')), [])

    def test_easy_excluded(self):
        self.assertEqual(builder.candidates(self.row('result=cq.Workplane("XY").hole(5)', 'easy')), [])

    def test_comments_not_geometry(self):
        self.assertEqual(builder.normalized('x=1 # before'), builder.normalized('x=1 # after'))


if __name__ == '__main__':
    unittest.main()
