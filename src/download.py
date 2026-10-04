"""Independent official-source pull. Raw bytes stay ignored; cache must match its manifest."""
import argparse
import csv
import hashlib
import io
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from artifacts import publish_paths

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
FILE = 'hdb-resale-prices-2017-onwards.csv'
DATASET = 'd_8b84c4ee58e3cfc0ece0d773c8ca6abc'
URL = f'https://data.gov.sg/datasets/{DATASET}/view'
HEADER = 'month,town,flat_type,block,street_name,storey_range,floor_area_sqm,flat_model,lease_commence_date,remaining_lease,resale_price'.split(',')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0.0.0 Safari/537.36'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Referer': 'https://data.gov.sg/'})
    with urllib.request.urlopen(req, timeout=180) as response:
        return response.read()


def inspect_csv(data):
    rows = csv.reader(io.StringIO(data.decode('utf-8-sig'), newline=''))
    if next(rows, None) != HEADER:
        raise ValueError('unexpected HDB header')
    months = []
    for row in rows:
        if len(row) != len(HEADER):
            raise ValueError('malformed CSV record')
        month = row[0]
        if not re.fullmatch(r'20\d\d-(0[1-9]|1[0-2])', month) or month < '2017-01':
            raise ValueError('invalid registration month')
        months.append(month)
    if not months:
        raise ValueError('empty HDB file')
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), rows=len(months),
                month_min=min(months), month_max=max(months), months=len(set(months)))


def validate_cache():
    manifest = json.loads((RAW/'pull_manifest.json').read_text(encoding='utf-8'))
    info = inspect_csv((RAW/FILE).read_bytes())
    if manifest['dataset_id'] != DATASET or any(manifest.get(k) != v for k,v in info.items()):
        raise ValueError('cache differs from manifest; explicit --force required, provenance not rewritten')
    return manifest


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true')
    args=ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    if (RAW/FILE).exists() and (RAW/'pull_manifest.json').exists() and not args.force:
        print('CACHE VERIFIED', json.dumps(validate_cache(), sort_keys=True))
        return
    base=f'https://api-open.data.gov.sg/v1/public/api/datasets/{DATASET}'
    url=''
    try:
        url=(json.loads(get(base+'/poll-download')).get('data') or {}).get('url','')
    except Exception as exc:
        print('pre-initiate poll:',exc)
    if not url:
        get(base+'/initiate-download')
        for _ in range(15):
            time.sleep(2)
            url=(json.loads(get(base+'/poll-download')).get('data') or {}).get('url','')
            if url: break
    if not url:
        raise RuntimeError('no signed download URL')
    data=get(url)
    info=inspect_csv(data)
    # Reject suspiciously truncated complete-history downloads, not invalid analytic fields.
    if info['month_min']!='2017-01' or info['months']<96 or info['rows']<150000:
        raise ValueError('incomplete 2017-onward history')
    manifest=dict(dataset_id=DATASET,dataset_url=URL,file=FILE,
                  retrieved_at=datetime.now(timezone.utc).isoformat(timespec='seconds'), **info)
    part=RAW/(FILE+'.part'); part.write_bytes(data)
    mp=RAW/'pull_manifest.json.part'; mp.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    publish_paths([(part,RAW/FILE),(mp,RAW/'pull_manifest.json')])
    print('LIVE PULL VERIFIED',json.dumps(manifest,sort_keys=True))

if __name__=='__main__':
    main()
