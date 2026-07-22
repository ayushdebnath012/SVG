from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from svgpatchlab.data import SVGEditBench
from svgpatchlab.data.svgeditbench import DatasetError


class DatasetTests(unittest.TestCase):
    def test_official_dataset_shape(self):
        summary = SVGEditBench("SVGEditBench").summary()
        self.assertEqual(summary["total_cases"], 600)
        self.assertEqual(summary["unique_emojis"], 100)
        self.assertEqual(set(summary["tasks"].values()), {100})

    def test_empty_task_directory_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "1_ChangeColor" / "query").mkdir(parents=True)
            (Path(tmp) / "1_ChangeColor" / "answer").mkdir(parents=True)
            with self.assertRaises(DatasetError) as raised:
                list(SVGEditBench(tmp).iter_cases(tasks=["change_color"]))
            self.assertIn("submodule", str(raised.exception))

    def test_missing_task_directory_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(DatasetError):
                list(SVGEditBench(tmp).iter_cases(tasks=["change_color"]))

    def test_limit_per_task_samples_each_task(self):
        cases = list(SVGEditBench("SVGEditBench").iter_cases(limit_per_task=2))
        self.assertEqual(len(cases), 12)
        self.assertEqual({task: sum(case.task == task for case in cases) for task in SVGEditBench("SVGEditBench").tasks}, {task: 2 for task in SVGEditBench("SVGEditBench").tasks})


if __name__ == "__main__":
    unittest.main()
