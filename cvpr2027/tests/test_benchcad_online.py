import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'scripts/benchcad_online_edit_dataset.py'
spec = importlib.util.spec_from_file_location('online_dataset', path)
dataset = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dataset)


class PatchTests(unittest.TestCase):
    def test_multiple_edits_original_coordinates(self):
        before = 'a=1\nb=2\nc=3\nd=4'
        after = 'a=5\nb=2\nc=6\nd=4\ne=7'
        self.assertEqual(dataset.apply(before, dataset.patch(before, after)), after)

    def test_insert_and_delete(self):
        for before, after in [('a=1\nb=2', 'a=1'), ('a=1', 'x=3\na=1')]:
            self.assertEqual(dataset.apply(before, dataset.patch(before, after)), after)

    def test_overlap_rejected(self):
        with self.assertRaises(ValueError):
            dataset.apply('a=1\nb=2', {'edits':[{'start':0,'delete':2,'insert':[]}, {'start':1,'delete':0,'insert':[]}]})

    def test_negative_and_bool_coordinates_rejected(self):
        for start, delete in [(0, -1), (True, 1), (-1, 1), (99, 0)]:
            with self.assertRaises(ValueError):
                dataset.apply('a=1', {'edits':[{'start':start,'delete':delete,'insert':[]}]})

    def test_comments_removed_without_affecting_literals(self):
        self.assertEqual(dataset.canonical('x="# preserve" # remove\n\ny=2'), 'x="# preserve"\ny=2')


if __name__ == '__main__':
    unittest.main()
