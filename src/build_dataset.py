"""Parse official lease text; DuckDB staging is added below."""
import re
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def stage(raw_path, max_month):
    import duckdb
    con=duckdb.connect(config={'threads':1})
    con.execute('CREATE TABLE raw AS SELECT * FROM read_csv(?,all_varchar=true)',[str(raw_path)])
    con.execute('CREATE TABLE town_groups AS SELECT * FROM read_csv(?)',[(ROOT/'outputs/town_groups.csv').as_posix()])
    con.execute((ROOT/'sql/01_staging.sql').read_text(encoding='utf-8').replace('$MAXMONTH',max_month))
    return con


def main():
    from download import RAW, FILE, validate_cache
    from artifacts import publish_paths, write_csv
    manifest=validate_cache()
    con=stage(RAW/FILE,manifest['month_max'])
    checks=con.execute((ROOT/'sql/05_checks.sql').read_text()).fetchall()
    for name,count in checks:
        print(f"{'PASS' if count==0 else 'FAIL'} {name}: {count}")
    if any(count for _,count in checks):
        raise ValueError('staging failed; existing artifacts untouched')
    raw_count=con.sql('SELECT count(*) FROM raw').fetchone()[0]
    retained=con.sql('SELECT count(*) FROM sales').fetchone()[0]
    assert raw_count==manifest['rows']
    con.execute((ROOT/'sql/03_metrics.sql').read_text())
    outputs=ROOT/'outputs'; processed=ROOT/'data/processed'
    outputs.mkdir(exist_ok=True); processed.mkdir(parents=True,exist_ok=True)
    pairs=[]
    for table,name in [('bucket_medians','bucket_medians_all.csv'),('segment_profile','segment_profile.csv')]:
        cur=con.execute(f'SELECT * FROM {table} ORDER BY sale_year,town,flat_type'+(',lease_band_low' if table=='bucket_medians' else ''))
        fields=[d[0] for d in cur.description]
        rows=[dict(zip(fields,r)) for r in cur.fetchall()]
        part=outputs/(name+'.part');write_csv(part,rows);pairs.append((part,outputs/name))
    reasons=['invalid_month','invalid_town','invalid_type','invalid_price','invalid_area','invalid_storey','invalid_commence_year','invalid_lease_text','lease_inconsistent','retained']
    counts=dict(con.sql('SELECT exclusion_reason,count(*) FROM classified GROUP BY 1').fetchall())
    rows=[dict(reason=r,n=counts.get(r,0)) for r in reasons]
    part=outputs/'exclusions.csv.part';write_csv(part,rows);pairs.append((part,outputs/'exclusions.csv'))
    cur=con.execute("SELECT month,town,flat_type,block,street_name,remaining_lease,lease_commence_date,lease_offset_months,exclusion_reason FROM classified WHERE exclusion_reason!='retained' ORDER BY month,town,block")
    fields=[d[0] for d in cur.description]
    part=outputs/'excluded_rows.csv.part';write_csv(part,[dict(zip(fields,r)) for r in cur.fetchall()],fields);pairs.append((part,outputs/'excluded_rows.csv'))
    part=processed/'sales.parquet.part'
    con.execute(f"COPY (SELECT * FROM sales ORDER BY month,town,flat_type,block,street_name,storey_midpoint,floor_area_sqm,lease_months,resale_price) TO '{part.as_posix()}' (FORMAT PARQUET)")
    pairs.append((part,processed/'sales.parquet'))
    # Keep the reviewed snapshot's first retrieval time when the byte identity is unchanged.
    # The ignored raw manifest still records each actual download time.
    receipt=dict(manifest)
    snapshot=outputs/'source_snapshot.json'
    if snapshot.exists():
        previous=json.loads(snapshot.read_text(encoding='utf-8'))
        if {k:v for k,v in previous.items() if k!='retrieved_at'}=={k:v for k,v in manifest.items() if k!='retrieved_at'}:
            receipt['retrieved_at']=previous['retrieved_at']
    part=outputs/'source_snapshot.json.part';part.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n');pairs.append((part,snapshot))
    publish_paths(pairs)
    print(f'RECONCILED raw={raw_count} retained={retained} excluded={raw_count-retained}')
    print('EXCLUSIONS',json.dumps(rows))


def lease_offset(months, commence_year, sale_month):
    year, month = map(int, sale_month.split('-'))
    return months - ((commence_year + 99 - year) * 12 - (month - 1))


def lease_consistent(offset):
    # Unknown start month, rounding/application lag, and year-only precision.
    return offset is not None and -12 <= offset <= 18


def parse_lease(text):
    match = re.fullmatch(r'(\d+) years?(?: (\d+) months?)?', str(text).strip())
    if not match:
        return None
    years, months = int(match[1]), int(match[2] or 0)
    value = years * 12 + months
    return value if 0 <= months < 12 and 0 < value <= 99 * 12 else None


if __name__=='__main__':
    main()
