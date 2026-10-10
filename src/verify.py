"""Independent raw medians, README anchors, relative links and artifact hashes."""
import csv
import hashlib
import json
import re
import statistics
import xml.etree.ElementTree as ET
from pathlib import Path
from build_dataset import parse_lease
from download import RAW,FILE,validate_stage
ROOT=Path(__file__).resolve().parents[1]


def check_group_anchors(groups, readme):
    anchors = {
        ('2025', 'all_types', 'historical_mature'): 1.198415688496771,
        ('2025', 'all_types', 'historical_non_mature'): 0.6892626163764862,
        ('2025', '4_room', 'historical_mature'): 1.1967679273127365,
        ('2025', '4_room', 'historical_non_mature'): 0.674516986955109,
    }
    keys = [(r['sale_year'], r['scope'], r['historical_group']) for r in groups]
    assert len(keys) == len(anchors) and set(keys) == set(anchors), 'Headline group keys differ; review year/group coverage'
    for row, key in zip(groups, keys):
        anchor = anchors[key]
        got = float(row['median_pct_per_year'])
        assert abs(got - anchor) < 1e-9, f'Headline {key}: {got} vs {anchor}, outside absolute tolerance 1e-9; compare input SHA-256 and model changes'
        assert f'{anchor:.10f}' in readme, f'README spot-check missing: {key} {anchor:.10f}'
    print('HEADLINE PASS: four keyed medians, absolute tolerance 1e-9')


def compare_reviewed():
    import io
    import math
    import zipfile
    floats=set(('median_lease_years median_price_per_sqm q25_price_per_sqm q75_price_per_sqm '
                'lease_min_years lease_max_years mean_price_per_sqm sd_price_per_sqm beta_per_year '
                'hc3_se ci_low_beta ci_high_beta pct_per_year ci_low_pct ci_high_pct '
                'residual_lease_sd_years lease_control_r2 condition_number leverage_max r2 '
                'residual_rmse_log residual_abs_p95_log residual_abs_fitted_corr '
                'median_pct_per_year min_pct_per_year max_pct_per_year').split())
    with zipfile.ZipFile(ROOT/'data/snapshots/reviewed-hdb.zip') as archive:
        expected=json.loads(archive.read('pull_manifest.json'))
        assert validate_stage()['sha256']==expected['sha256'], 'reviewed input identity differs'
        names=sorted(n for n in archive.namelist() if n.startswith('outputs/') and n.endswith('.csv'))
        assert {p.name for p in (ROOT/'outputs').glob('*.csv')}=={Path(n).name for n in names}, 'reviewed CSV coverage differs'
        for name in names:
            wanted=list(csv.reader(io.StringIO(archive.read(name).decode('utf-8'))))
            with (ROOT/name).open(encoding='utf-8',newline='') as file: got=list(csv.reader(file))
            message=f'reviewed CSV differs: {Path(name).name}'
            assert len(got)==len(wanted) and got[0]==wanted[0], message
            for actual,reference in zip(got[1:],wanted[1:]):
                assert len(actual)==len(reference),message
                for field,a,b in zip(wanted[0],actual,reference):
                    if a==b: continue
                    assert field in floats and a and b,message
                    try: x,y=float(a),float(b)
                    except ValueError: raise AssertionError(message)
                    assert math.isfinite(x) and math.isfinite(y) and math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-9),message
        print('REVIEWED CSV PASS',len(names),'complete tables; abs 1e-9 / rel 1e-12 numeric tolerance')


def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--compare-reviewed',action='store_true',help='compare all 12 tables with the frozen replay receipt')
    args=parser.parse_args()
    manifest=validate_stage()
    if args.compare_reviewed: compare_reviewed()
    with (RAW/FILE).open(encoding='utf-8',newline='') as f: raw=list(csv.DictReader(f))
    with (ROOT/'outputs/bucket_medians.csv').open() as f: buckets=list(csv.DictReader(f))
    for town in ['SENGKANG','TAMPINES','YISHUN']:
        bucket=next(b for b in buckets if b['town']==town and b['flat_type']=='4 ROOM' and b['eligible']=='True')
        values=[float(r['resale_price'])/float(r['floor_area_sqm']) for r in raw if r['month'].startswith(bucket['sale_year']+'-') and r['town']==town and r['flat_type']=='4 ROOM' and int(bucket['lease_band_low'])*12<=parse_lease(r['remaining_lease'])<int(bucket['lease_band_high'])*12]
        assert len(values)==int(bucket['n']) and abs(statistics.median(values)-float(bucket['median_price_per_sqm']))<1e-9
        print('RAW MEDIAN PASS',town,bucket['lease_band_low'],len(values),statistics.median(values))
    with (ROOT/'outputs/group_summaries.csv').open() as f:groups=list(csv.DictReader(f))
    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    check_group_anchors(groups, readme)
    broken=[];n=0
    for file in [ROOT/'README.md',ROOT/'data/raw/README.md',*list((ROOT/'docs').glob('*.md'))]:
        text=file.read_text(encoding='utf-8')
        links=re.findall(r'\]\(([^\s)]+)\)',text)+re.findall(r'(?:src|srcset)="([^"]+)"',text)
        for link in links:
            if link.startswith(('https:','http:','mailto:','#')):continue
            target=(file.parent/link.split('#')[0]).resolve();n+=1
            if not target.exists():broken.append((str(file),link))
    assert not broken,broken
    for suffix in ['','-dark']:
        # Generated local SVGs only; no untrusted remote XML is parsed.
        tree=ET.parse(ROOT/f'assets/banner{suffix}.svg');assert tree.getroot().attrib['viewBox']=='0 0 1280 320'
        assert len(tree.findall('{http://www.w3.org/2000/svg}text'))==4
        assert max(float(t.attrib['y']) for t in tree.findall('{http://www.w3.org/2000/svg}text'))<=270
    print('LINKS PASS',n,'relative links; zero broken; banner XML PASS')
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted([*list((ROOT/'outputs').glob('*.csv')),*list((ROOT/'reports/figures').glob('*.png')),*list((ROOT/'assets').glob('banner*.svg'))])}
    print('HASH RECEIPT',json.dumps(dict(input_sha256=manifest['sha256'],artifacts=hashes),sort_keys=True))

if __name__=='__main__':main()
