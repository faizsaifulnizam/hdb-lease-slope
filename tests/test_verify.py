"""Offline regression for cross-platform headline verification; no raw data needed."""
import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import verify


class AnchorTests(unittest.TestCase):
    def test_linux_roundoff_passes_but_changed_headline_fails(self):
        with (ROOT / 'outputs/group_summaries.csv').open(encoding='utf-8') as f:
            groups = list(csv.DictReader(f))
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        # Independently reported Linux refit of the identical source byte hash.
        linux = [1.1984156884967616, 0.68926261637649,
                 1.196767927312738, 0.6745169869551015]
        for row, value in zip(groups, linux):
            row['median_pct_per_year'] = str(value)
        verify.check_group_anchors(list(reversed(groups)), readme)
        groups[0]['median_pct_per_year'] = str(linux[0] + 2e-9)
        with self.assertRaisesRegex(AssertionError, 'outside absolute tolerance'):
            verify.check_group_anchors(groups, readme)
        groups[0]['median_pct_per_year'] = 'nan'
        with self.assertRaises(AssertionError):
            verify.check_group_anchors(groups, readme)
        for invalid in [groups[:-1], groups + [groups[0]],
                        [{**r, 'sale_year': '2024'} for r in groups]]:
            with self.assertRaisesRegex(AssertionError, 'keys'):
                verify.check_group_anchors(invalid, readme)
        groups[0]['median_pct_per_year'] = str(linux[0])
        with self.assertRaisesRegex(AssertionError, 'README spot-check'):
            verify.check_group_anchors(groups, readme.replace('1.1984156885', '9.1984156885'))


if __name__ == '__main__':
    unittest.main()
