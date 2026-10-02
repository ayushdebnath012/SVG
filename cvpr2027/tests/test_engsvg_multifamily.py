import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import engsvg_multifamily_benchmark as benchmark


class MultiFamilyBenchmarkTests(unittest.TestCase):
    def test_frozen_suite_has_30_recoveries_and_100_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            summary = benchmark.build(root)
            self.assertEqual(summary["recovery_cases"], 30)
            self.assertEqual(summary["recovery_success"], 30)
            self.assertEqual(summary["edit_cases"], 100)
            self.assertEqual(summary["families"], ["mechanical_part_2d", "truss2d"])
            manifest = json.loads((root / "manifest.json").read_text())
            self.assertEqual(len({row["id"] for row in manifest["recovery_cases"]}), 30)
            self.assertEqual(len({row["id"] for row in manifest["edit_cases"]}), 100)
            checksums = json.loads((root / "sha256-manifest.json").read_text())
            self.assertTrue(all(hashlib.sha256((root / name).read_bytes()).hexdigest() == value
                                for name, value in checksums.items()))
            with self.assertRaises(ValueError):
                benchmark.build(root)


if __name__ == "__main__":
    unittest.main()
