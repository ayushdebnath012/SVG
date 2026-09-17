"""Check failure recovery without running training or large numerical solves."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    'remote_batch', Path(__file__).resolve().parents[1] / 'scripts/remote_batch.py')
batch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(batch)


class RemoteBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / 'results'

    def run_batch(self, jobs, *extra):
        with patch.object(batch, 'ROOT', self.root), patch.object(batch, 'stages', return_value=jobs), \
                patch.object(sys, 'argv', ['remote_batch', '--output', str(self.out), '--cpu-only', *extra]):
            batch.main()

    def test_failure_resume_skips_successful_stages(self):
        count = self.root / 'counter'
        first = [sys.executable, '-c',
                 f'from pathlib import Path; p=Path({str(count)!r}); p.write_text(p.read_text()+"x" if p.exists() else "x")']
        failure = [sys.executable, '-c', 'raise SystemExit(7)']
        with self.assertRaisesRegex(RuntimeError, 'second exited 7'):
            self.run_batch([('first', first), ('second', failure)])
        report = json.loads((self.out / 'status.json').read_text())
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['stages']['second']['returncode'], 7)
        self.assertTrue((self.out / 'logs/second.log').exists())
        self.run_batch([('first', first), ('second', [sys.executable, '-c', 'pass'])], '--resume')
        self.assertEqual(count.read_text(), 'x')
        self.assertEqual(json.loads((self.out / 'status.json').read_text())['status'], 'completed')
        self.assertTrue((self.out / 'summary.json').exists())

    def test_resume_rejects_changed_source(self):
        scripts = self.root / 'scripts'
        scripts.mkdir()
        source = scripts / 'source.py'
        source.write_text('original')
        self.run_batch([])
        source.write_text('changed')
        with self.assertRaises(SystemExit):
            self.run_batch([], '--resume')

    def test_dry_run_does_not_create_results(self):
        self.run_batch([('example', [sys.executable, '-c', 'pass'])], '--dry-run')
        self.assertFalse(self.out.exists())


if __name__ == '__main__':
    unittest.main()
