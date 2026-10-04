"""Stdlib-only artifact smoke; the separate live-refit CI job reruns analysis."""
import csv,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(name):
    with (ROOT/'outputs'/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))

def main():
    slopes=read('slopes.csv');groups=read('group_summaries.csv');ledger=read('model_exclusions.csv');buckets=read('bucket_medians.csv')
    required={'sale_year','town','flat_type','n','status','beta_per_year','pct_per_year','residual_df','lease_min_years','lease_max_years'}
    assert required<=slopes[0].keys()
    for r in slopes:
        if r['status']=='estimated':
            beta=float(r['beta_per_year']);pct=float(r['pct_per_year'])
            assert abs(100*math.expm1(beta)-pct)<1e-10
            assert int(r['n'])>=100 and float(r['lease_max_years'])-float(r['lease_min_years'])>=10 and int(r['residual_df'])>=30
            assert float(r['ci_low_pct'])<=pct<=float(r['ci_high_pct'])
        else:
            assert all(r[k]=='' for k in ['beta_per_year','pct_per_year','hc3_se','ci_low_pct','ci_high_pct'])
    assert sum(int(r['n']) for r in slopes)==sum(int(r['n_transactions']) for r in ledger)
    for r in groups:
        selected=[s for s in slopes if s['status']=='estimated' and s['historical_group']==r['historical_group'] and (r['scope']=='all_types' or s['flat_type']=='4 ROOM')]
        assert len(selected)==int(r['n_segments'])
        assert abs(statistics.median(float(s['pct_per_year']) for s in selected)-float(r['median_pct_per_year']))<1e-10
        assert sum(int(s['n']) for s in selected)==int(r['n_transactions'])
    assert all((r['eligible']=='True')==(int(r['n'])>=30) for r in buckets)
    raw=json.loads((ROOT/'outputs/source_snapshot.json').read_text())
    exclusions=read('exclusions.csv')
    assert sum(int(r['n']) for r in exclusions)==raw['rows']
    assert raw['dataset_id']=='d_8b84c4ee58e3cfc0ece0d773c8ca6abc' and len(raw['sha256'])==64
    for stem in ['f1_buckets','f2_slopes','f3_exemplar']:
        for suffix in ['','-dark']:assert (ROOT/f'reports/figures/{stem}{suffix}.png').stat().st_size>15000
    for suffix in ['','-dark']:
        banner=ROOT/f'assets/banner{suffix}.svg'
        assert banner.is_file() and 'y="270" text-anchor="end"' in banner.read_text(encoding='utf-8')
    assert len(read('featured_segments.csv'))==4
    print('SMOKE PASS: transformation, guards, group medians, model/raw reconciliations, buckets, six figures + two banners')

if __name__=='__main__':main()
