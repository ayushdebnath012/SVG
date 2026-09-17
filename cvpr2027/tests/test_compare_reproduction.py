"""Tolerance rules of the reproduction comparison, without any GPU artifacts."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    'compare_reproduction', Path(__file__).resolve().parents[1] / 'scripts/compare_reproduction.py')
compare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compare)


class CompareReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def pair(self, new, saved):
        paths = []
        for name, value in (('new.json', new), ('saved.json', saved)):
            path = Path(self.temp.name) / name
            path.write_text(json.dumps(value))
            paths.append(path)
        return paths

    def test_roundoff_and_timing_are_within_tolerance(self):
        new, saved = self.pair(
            {'residual': 2.3e-13, 'flux': [260.8156924367439, 'P2'], 'solve_seconds': 21.2},
            {'residual': 4.1e-13, 'flux': [260.8156924367440, 'P2'], 'solve_seconds': 0.9})
        report = compare.compare_reference(new, saved, set())
        self.assertTrue(report['within_tolerance'])
        self.assertEqual(report['outside_tolerance'], [])
        self.assertLess(report['max_absolute_difference'], 1e-9)

    def test_physical_change_is_outside_tolerance(self):
        new, saved = self.pair({'flux': 260.8}, {'flux': 259.9})
        report = compare.compare_reference(new, saved, set())
        self.assertFalse(report['within_tolerance'])
        self.assertEqual(report['outside_tolerance'], ['/flux'])

    def test_text_and_structure_must_match_exactly(self):
        new, saved = self.pair({'solver': 'P2', 'n': [1, 2]}, {'solver': 'P1', 'n': [1, 2]})
        with self.assertRaises(ValueError):
            compare.compare_reference(new, saved, set())
        new, saved = self.pair({'n': [1, 2]}, {'n': [1]})
        with self.assertRaises(ValueError):
            compare.compare_reference(new, saved, set())


if __name__ == '__main__':
    unittest.main()
