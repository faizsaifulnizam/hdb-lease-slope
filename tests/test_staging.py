"""DuckDB staging checks at the real producer seam, using synthetic invalid rows only."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

class StagingTests(unittest.TestCase):
    def test_identical_repull_preserves_committed_snapshot_receipt(self):
        import contextlib
        import io
        import json
        import shutil
        from unittest.mock import patch
        import build_dataset
        import download
        source=build_dataset.ROOT
        row=['2025-01','BEDOK','4 ROOM','1','ROAD','01 TO 03','90','Model','1980','54 years 04 months','500000']
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/'outputs').mkdir(); (root/'data/raw').mkdir(parents=True)
            shutil.copytree(source/'sql',root/'sql')
            shutil.copy(source/'outputs/town_groups.csv',root/'outputs/town_groups.csv')
            raw=root/'data/raw'/download.FILE
            with raw.open('w',newline='') as f:
                w=csv.writer(f);w.writerow(download.HEADER);w.writerow(row)
            manifest=dict(dataset_id=download.DATASET,dataset_url=download.URL,file=download.FILE,
                          retrieved_at='2026-10-04T00:00:00+00:00',**download.inspect_csv(raw.read_bytes()))
            mp=raw.parent/'pull_manifest.json'; mp.write_text(json.dumps(manifest))
            with patch.object(build_dataset,'ROOT',root),patch.object(download,'RAW',raw.parent),contextlib.redirect_stdout(io.StringIO()):
                build_dataset.main()
                receipt=(root/'outputs/source_snapshot.json').read_bytes()
                manifest['retrieved_at']='2026-10-05T01:00:00+00:00';mp.write_text(json.dumps(manifest))
                build_dataset.main()
                self.assertEqual((root/'outputs/source_snapshot.json').read_bytes(),receipt)
                with raw.open('a',newline='') as f:csv.writer(f).writerow(row)
                manifest.update(download.inspect_csv(raw.read_bytes()));mp.write_text(json.dumps(manifest))
                build_dataset.main()
                changed=json.loads((root/'outputs/source_snapshot.json').read_text())
                self.assertEqual(changed['retrieved_at'],manifest['retrieved_at'])
                self.assertEqual(changed['rows'],2)
                self.assertNotEqual(changed['sha256'],json.loads(receipt)['sha256'])

    def test_exclusion_reconciliation(self):
        from build_dataset import stage
        from download import HEADER
        row=['2025-01','BEDOK','4 ROOM','1','ROAD','01 TO 03','90','Model','1980','54 years 04 months','500000']
        rows=[row,row.copy()]
        for idx,value in [(0,'garbage'),(1,'UNKNOWN'),(2,'UNKNOWN'),(5,'09 TO 01'),(6,'nan'),(8,'2029'),(9,'54 years 12 months'),(10,'-1')]:
            r=row.copy(); r[idx]=value; rows.append(r)
        r=row.copy();r[9]='20 years';rows.append(r)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'raw.csv'
            with p.open('w',newline='') as f:
                w=csv.writer(f);w.writerow(HEADER);w.writerows(rows)
            con=stage(p,'2026-10')
            self.assertEqual(con.sql('select count(*) from sales').fetchone()[0],2)
            self.assertEqual(con.sql("select count(*) from classified where exclusion_reason!='retained'").fetchone()[0],9)
            self.assertAlmostEqual(con.sql('select price_per_sqm from sales limit 1').fetchone()[0],500000/90)
            self.assertEqual(con.sql('select storey_midpoint from sales limit 1').fetchone()[0],2)
            # Identical-looking transactions remain two observations, not a invented ID/dedup.
            self.assertEqual(con.sql('select count(distinct block) from sales').fetchone()[0],1)

if __name__=='__main__': unittest.main()
