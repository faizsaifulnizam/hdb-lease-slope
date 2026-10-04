"""Caller-facing parser checks. No raw data or third-party test framework."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

class LeaseTests(unittest.TestCase):
    def test_lease_parser(self):
        from build_dataset import parse_lease
        for s, expected in [('61 years 04 months',736),('62 years 01 month',745),('60 years',720),('1 year 2 months',14)]:
            self.assertEqual(parse_lease(s),expected)
        for s in ['', '62', '61 years 12 months','-1 year','100 years','60 years rubbish']:
            self.assertIsNone(parse_lease(s))

    def test_lease_tolerance(self):
        from build_dataset import lease_offset, lease_consistent
        self.assertEqual(lease_offset(736,1979,'2017-01'),4)
        for delta in [-12,0,11,18]:
            self.assertTrue(lease_consistent(delta))
        for delta in [-13,19,None]:
            self.assertFalse(lease_consistent(delta))

    def test_download_validation(self):
        from download import inspect_csv, HEADER
        import hashlib
        data = (','.join(HEADER)+'\n2025-01,BEDOK,4 ROOM,1,ROAD,01 TO 03,90,Model,1980,54 years,500000\n').encode()
        info = inspect_csv(data)
        self.assertEqual(info['rows'],1)
        self.assertEqual(info['sha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(info['month_min'],'2025-01')
        for broken in [b'',data.replace(b'2025-01',b'2025-13'),data.replace(b'500000',b'500000,extra')]:
            with self.assertRaises(ValueError):
                inspect_csv(broken)

    def test_publish_rolls_back(self):
        from artifacts import publish_paths
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); a=p/'a';b=p/'b';s=p/'new'
            a.write_bytes(b'old-a');b.write_bytes(b'old-b');s.write_bytes(b'new-a')
            with self.assertRaises(FileNotFoundError):publish_paths([(s,a),(p/'missing',b)])
            self.assertEqual(a.read_bytes(),b'old-a');self.assertEqual(b.read_bytes(),b'old-b')

    def test_cache_tamper_rejected(self):
        import download,tempfile,json
        from unittest.mock import patch
        data=(','.join(download.HEADER)+'\n2025-01,BEDOK,4 ROOM,1,ROAD,01 TO 03,90,Model,1980,54 years,500000\n').encode()
        with tempfile.TemporaryDirectory() as td,patch.object(download,'RAW',Path(td)):
            (Path(td)/download.FILE).write_bytes(data)
            (Path(td)/'pull_manifest.json').write_text(json.dumps(dict(dataset_id=download.DATASET,**download.inspect_csv(data))))
            self.assertEqual(download.validate_cache()['rows'],1)
            (Path(td)/download.FILE).write_bytes(data.replace(b'500000',b'600000'))
            with self.assertRaises(ValueError):download.validate_cache()

if __name__ == '__main__':
    unittest.main()
