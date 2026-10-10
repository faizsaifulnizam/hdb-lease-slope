"""Real CLI boundary regressions on the licensed frozen replay input; no network."""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILE = 'hdb-resale-prices-2017-onwards.csv'

class ConsumerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lease consumer ", dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'repo'; self.root.mkdir()
        for name in ['src', 'sql', 'outputs', 'assets', 'docs', 'reports']:
            shutil.copytree(ROOT/name, self.root/name)
        shutil.copyfile(ROOT/'README.md', self.root/'README.md')
        shutil.copyfile(ROOT/'LICENSE', self.root/'LICENSE')
        raw = self.root/'data/raw'; raw.mkdir(parents=True)
        shutil.copyfile(ROOT/'data/raw/README.md', raw/'README.md')
        archive = ROOT/'data/snapshots/reviewed-hdb.zip'
        if archive.exists():
            with zipfile.ZipFile(archive) as z:
                for name in [FILE, 'pull_manifest.json']: (raw/name).write_bytes(z.read(name))
        else:
            for name in [FILE, 'pull_manifest.json']: shutil.copyfile(ROOT/'data/raw'/name, raw/name)
        self.raw = raw/FILE
        self.original = self.raw.read_bytes()
        self.original_manifest = (raw/'pull_manifest.json').read_bytes()
        shutil.copytree(ROOT/'data/snapshots', self.root/'data/snapshots')
        self.assertEqual(hashlib.sha256(self.raw.read_bytes()).hexdigest(), '945e09d75efb2eec1ab1618ce369c0d8eb885ef34158e29426f1af141d4000e4')

    def run_cli(self, script, *args):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', MPLBACKEND='Agg')
        env.pop('PYTHONPATH', None); env.pop('PYTHONHOME', None)
        return subprocess.run([sys.executable, str(self.root/'src'/script), *args], cwd=self.tmp.name, env=env, capture_output=True, text=True)

    def stage(self):
        p = self.run_cli('build_dataset.py')
        self.assertEqual(p.returncode, 0, p.stdout+p.stderr)

    def mutate(self, transform):
        rows = list(csv.DictReader(io.StringIO(self.raw.read_text(encoding='utf-8-sig'))))
        fields = list(rows[0]); rows = transform(rows)
        with self.raw.open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n'); w.writeheader(); w.writerows(rows)
        sys.path.insert(0, str(ROOT/'src'))
        from download import inspect_csv
        mp = self.raw.parent/'pull_manifest.json'; manifest = json.loads(mp.read_text())
        manifest.update(inspect_csv(self.raw.read_bytes())); mp.write_text(json.dumps(manifest))

    def finals(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for folder, glob in [('outputs','*'), ('reports/figures','*.png'), ('docs/img','*.png')] for p in (self.root/folder).glob(glob) if p.is_file() and not p.name.endswith('.part')}

    def test_previous_year_missing_month_rejected_without_publication(self):
        for month in ['2024-01', '2024-11', '2024-12', '2024']:
            with self.subTest(month=month):
                # Restore the exact input before each independent missing-window fixture.
                self.raw.write_bytes(self.original)
                (self.raw.parent/'pull_manifest.json').write_bytes(self.original_manifest)
                self.mutate(lambda rows: [r for r in rows if not r['month'].startswith(month)])
                self.stage(); before = self.finals()
                p = self.run_cli('analysis.py')
                self.assertNotEqual(p.returncode, 0, 'incomplete previous year accepted')
                self.assertIn('incomplete calendar year 2024', p.stderr)
                self.assertEqual(self.finals(), before)

    def test_changed_raw_same_date_rejected_by_all_consumers(self):
        self.stage()
        before = self.finals()
        def changed(rows):
            row = next(r for r in rows if r['month']=='2025-01' and r['town']=='CLEMENTI' and r['flat_type']=='3 ROOM')
            row['resale_price'] = str(float(row['resale_price'])*2)
            return rows
        self.mutate(changed)
        for script in ['analysis.py', 'verify.py', 'figures.py']:
            with self.subTest(script=script):
                p = self.run_cli(script)
                self.assertNotEqual(p.returncode, 0, 'stale staging accepted')
                self.assertIn('raw differs from staged source', p.stderr)
                self.assertEqual(self.finals(), before)

    def test_apostrophe_unicode_path_external_cwd(self):
        target = self.root.with_name("stage's 雪 path")
        self.root.rename(target); self.root = target; self.raw = target/'data/raw'/FILE
        self.stage()
        import duckdb
        con = duckdb.connect()
        self.assertEqual(con.execute('SELECT count(*) FROM read_parquet(?)', [str(target/'data/processed/sales.parquet')]).fetchone()[0], 242031)
        for name in ['bucket_medians_all.csv', 'segment_profile.csv', 'exclusions.csv', 'excluded_rows.csv']:
            self.assertEqual((target/'outputs'/name).read_bytes(), (ROOT/'outputs'/name).read_bytes())
        con.close()

    def test_reviewed_comparator_detects_nonheadline_change(self):
        self.stage()
        p = self.run_cli('verify.py', '--compare-reviewed')
        self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
        path = self.root/'outputs/slopes.csv'
        rows = list(csv.DictReader(io.StringIO(path.read_text())))
        row = next(r for r in rows if r['status']=='estimated')
        row['hc3_se'] = str(float(row['hc3_se'])+0.1)
        with path.open('w', newline='') as f:
            w=csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
        p = self.run_cli('verify.py', '--compare-reviewed')
        self.assertNotEqual(p.returncode, 0, 'nonheadline change accepted')
        self.assertIn('reviewed CSV differs: slopes.csv', p.stderr)

    def test_frozen_replay_restores_exact_input_without_network(self):
        self.raw.unlink(); (self.raw.parent/'pull_manifest.json').unlink()
        p = self.run_cli('download.py', '--replay')
        self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
        self.assertEqual(self.raw.read_bytes(), self.original)
        self.assertEqual((self.raw.parent/'pull_manifest.json').read_bytes(), self.original_manifest)

    def test_frozen_replay_refuses_changed_source_before_writes(self):
        self.mutate(lambda rows: rows[1:])
        before = self.finals()
        raw = self.raw.read_bytes(); manifest = (self.raw.parent/'pull_manifest.json').read_bytes()
        p = self.run_cli('download.py', '--replay')
        self.assertNotEqual(p.returncode, 0, 'changed input overwritten')
        self.assertIn('replay source lock', p.stderr)
        self.assertEqual(self.raw.read_bytes(), raw)
        self.assertEqual((self.raw.parent/'pull_manifest.json').read_bytes(), manifest)
        self.assertEqual(self.finals(), before)

    def test_strict_filter_calendar_guard(self):
        def changed(rows):
            for r in rows:
                if r['month']=='2025-06':
                    months=(int(r['lease_commence_date'])+99-2025)*12-5-1
                    r['remaining_lease']=f'{months//12} years {months%12} months'
            return rows
        self.mutate(changed); self.stage(); before=self.finals()
        p=self.run_cli('analysis.py')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('incomplete calendar year 2025: missing months [6]',p.stderr)
        self.assertEqual(self.finals(),before)

    def test_changed_input_restage_has_real_model_influence(self):
        baseline=list(csv.DictReader(io.StringIO((self.root/'outputs/slopes.csv').read_text())))
        old=next(r for r in baseline if r['town']=='CLEMENTI' and r['flat_type']=='3 ROOM')
        def changed(rows):
            row=next(r for r in rows if r['month']=='2025-01' and r['town']=='CLEMENTI' and r['flat_type']=='3 ROOM')
            row['resale_price']=str(float(row['resale_price'])*2)
            return rows
        self.mutate(changed); self.stage()
        p=self.run_cli('analysis.py');self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        current=list(csv.DictReader(io.StringIO((self.root/'outputs/slopes.csv').read_text())))
        new=next(r for r in current if r['town']=='CLEMENTI' and r['flat_type']=='3 ROOM')
        self.assertEqual(new['n'],old['n'])
        original_target=next(r for r in csv.DictReader(io.StringIO(self.original.decode('utf-8-sig'))) if r['month']=='2025-01' and r['town']=='CLEMENTI' and r['flat_type']=='3 ROOM')
        self.assertEqual(original_target['resale_price'],'720000')
        self.assertGreater(abs(float(new['beta_per_year'])-float(old['beta_per_year'])),1e-6)
        self.assertEqual([r for r in current if r['town']!='CLEMENTI'],[r for r in baseline if r['town']!='CLEMENTI'])

    def test_timestamp_only_repull_accepts_consumers(self):
        self.stage()
        mp=self.raw.parent/'pull_manifest.json';manifest=json.loads(mp.read_text())
        manifest['retrieved_at']='2026-10-08T00:00:00+00:00';mp.write_text(json.dumps(manifest))
        for script in ['analysis.py','verify.py','figures.py']:
            p=self.run_cli(script);self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        p=self.run_cli('download.py','--replay')
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(json.loads(mp.read_text())['retrieved_at'],manifest['retrieved_at'])

    def test_reviewed_comparator_keeps_counts_exact(self):
        self.stage()
        path=self.root/'outputs/slopes.csv'
        rows=list(csv.DictReader(io.StringIO(path.read_text())))
        rows[0]['n']=str(int(rows[0]['n'])+1e-10)
        with path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
        p=self.run_cli('verify.py','--compare-reviewed')
        self.assertNotEqual(p.returncode,0,'fractional count accepted by float tolerance')
        self.assertIn('reviewed CSV differs: slopes.csv',p.stderr)

    def test_frozen_replay_rejects_wrong_dataset_before_promotion(self):
        self.raw.unlink()
        archive=self.root/'data/snapshots/reviewed-hdb.zip'
        with zipfile.ZipFile(archive) as z: members={n:z.read(n) for n in z.namelist()}
        manifest=json.loads(members['pull_manifest.json']);manifest['dataset_id']='wrong_dataset'
        members['pull_manifest.json']=json.dumps(manifest).encode()
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for name,data in members.items(): z.writestr(name,data)
        p=self.run_cli('download.py','--replay')
        self.assertNotEqual(p.returncode,0)
        self.assertFalse(self.raw.exists(),'invalid archive promoted source before failing')
        self.assertEqual((self.raw.parent/'pull_manifest.json').read_bytes(),self.original_manifest)

if __name__ == '__main__': unittest.main()
