"""Independent raw medians, README anchors, relative links and artifact hashes."""
import csv
import hashlib
import json
import re
import statistics
import xml.etree.ElementTree as ET
from pathlib import Path
from build_dataset import parse_lease
from download import RAW,FILE,validate_cache
ROOT=Path(__file__).resolve().parents[1]


def main():
    manifest=validate_cache()
    with (RAW/FILE).open(encoding='utf-8',newline='') as f: raw=list(csv.DictReader(f))
    with (ROOT/'outputs/bucket_medians.csv').open() as f: buckets=list(csv.DictReader(f))
    for town in ['SENGKANG','TAMPINES','YISHUN']:
        bucket=next(b for b in buckets if b['town']==town and b['flat_type']=='4 ROOM' and b['eligible']=='True')
        values=[float(r['resale_price'])/float(r['floor_area_sqm']) for r in raw if r['month'].startswith(bucket['sale_year']+'-') and r['town']==town and r['flat_type']=='4 ROOM' and int(bucket['lease_band_low'])*12<=parse_lease(r['remaining_lease'])<int(bucket['lease_band_high'])*12]
        assert len(values)==int(bucket['n']) and abs(statistics.median(values)-float(bucket['median_price_per_sqm']))<1e-9
        print('RAW MEDIAN PASS',town,bucket['lease_band_low'],len(values),statistics.median(values))
    with (ROOT/'outputs/group_summaries.csv').open() as f:groups=list(csv.DictReader(f))
    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    for r in groups:assert str(float(r['median_pct_per_year'])) in readme,'README anchor differs from current analysis; review snapshot changes'
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
