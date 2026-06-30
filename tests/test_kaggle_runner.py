from __future__ import annotations

import unittest

from scripts.run_kaggle_plans import build_parser


class KaggleRunnerTests(unittest.TestCase):
    def test_default_run_has_no_case_limit(self):
        args = build_parser().parse_args([])

        self.assertIsNone(args.limit)
        self.assertIsNone(args.limit_per_task)


if __name__ == "__main__":
    unittest.main()
