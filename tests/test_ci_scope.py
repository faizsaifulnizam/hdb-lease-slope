"""Frozen replay is the PR gate; changing official source is checked on request."""
from pathlib import Path
import unittest


class CIScopeTest(unittest.TestCase):
    def test_live_source_check_is_explicit_and_keeps_hash_guard(self):
        workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/ci.yml').read_text()
        self.assertIn('  workflow_dispatch:', workflow)
        self.assertIn("  live-refit:\n    if: github.event_name == 'workflow_dispatch'", workflow)
        self.assertIn("assert got == expected", workflow)
        self.assertIn('python src/download.py --replay', workflow)
        self.assertIn('python src/verify.py --compare-reviewed', workflow)


if __name__ == '__main__':
    unittest.main()
