"""Numerically scaled OLS, full-rank guard, explicit residual degrees of freedom, HC3 covariance."""
import numpy as np
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIN_BUCKET=30
MIN_SEGMENT=100
MIN_SUPPORT=10


def segment_model(lease,storey,area,month,price_per_sqm,min_n=MIN_SEGMENT,min_support=MIN_SUPPORT):
    lease,storey,area,month,price_per_sqm=[np.asarray(v,dtype=float) for v in (lease,storey,area,month,price_per_sqm)]
    n=len(lease)
    result=dict(n=n,lease_min_years=float(lease.min()),lease_max_years=float(lease.max()),n_months=len(set(month)))
    if n<min_n: return dict(result,status='small_n')
    if np.ptp(lease)<min_support: return dict(result,status='narrow_support')
    if len(set(month))<6: return dict(result,status='few_months')
    if not all(np.isfinite(v).all() for v in (lease,storey,area,month,price_per_sqm)) or np.any(price_per_sqm<=0):
        raise ValueError('invalid regression values')
    observed=sorted(set(month))
    controls=np.column_stack([np.ones(n),storey-storey.mean(),area-area.mean()]+[(month==m).astype(float) for m in observed[1:]])
    x=np.column_stack([controls[:,0],lease-lease.mean(),controls[:,1:]])
    if np.linalg.matrix_rank(x)!=x.shape[1]: return dict(result,status='rank_deficient')
    residual_lease=lease-controls@np.linalg.lstsq(controls,lease,rcond=None)[0]
    lease_sd=float(np.std(residual_lease))
    if lease_sd<0.5: return dict(result,status='weak_lease_variation')
    if n-x.shape[1]<30: return dict(result,status='low_residual_df')
    try: fit=fit_ols(x,np.log(price_per_sqm))
    except ValueError: return dict(result,status='ill_conditioned_or_leverage')
    beta=float(fit['coef'][1]); se=float(np.sqrt(fit['cov'][1,1]))
    y=np.log(price_per_sqm); sst=float(np.sum((y-y.mean())**2))
    residual=fit['residual']
    return dict(result,status='estimated',beta_per_year=beta,hc3_se=se,
                ci_low_beta=beta-1.96*se,ci_high_beta=beta+1.96*se,
                pct_per_year=100*math.expm1(beta),ci_low_pct=100*math.expm1(beta-1.96*se),ci_high_pct=100*math.expm1(beta+1.96*se),
                residual_df=fit['df'],residual_lease_sd_years=lease_sd,lease_control_r2=1-float(residual_lease@residual_lease)/float(np.sum((lease-lease.mean())**2)),
                condition_number=fit['condition_number'],leverage_max=fit['leverage_max'],r2=1-fit['sse']/sst,
                residual_rmse_log=math.sqrt(fit['sse']/fit['df']),
                residual_abs_p95_log=float(np.quantile(np.abs(residual),0.95)),
                residual_abs_fitted_corr=float(np.corrcoef(np.abs(residual),y-residual)[0,1]) if np.std(residual)>1e-12 else 0.0)


def fit_ols(x,y):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    if x.ndim!=2 or len(y)!=len(x) or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('invalid model inputs')
    n,p=x.shape
    if n<=p or np.linalg.matrix_rank(x)!=p:
        raise ValueError('no residual degrees of freedom or rank-deficient design')
    scale=np.linalg.norm(x,axis=0)
    z=x/scale
    if np.linalg.cond(z)>1e8:
        raise ValueError('ill-conditioned design')
    coef,_,rank,_=np.linalg.lstsq(z,y,rcond=None)
    residual=y-z@coef
    inv=np.linalg.inv(z.T@z)
    leverage=np.einsum('ij,jk,ik->i',z,inv,z)
    if np.max(leverage)>=1-1e-9:
        raise ValueError('unit leverage; HC3 undefined')
    meat=z.T@(((residual/(1-leverage))**2)[:,None]*z)
    covariance=(inv@meat@inv)/scale[:,None]/scale[None,:]
    return dict(coef=coef/scale,cov=covariance,df=int(n-rank),sse=float(residual@residual),
                leverage_max=float(leverage.max()),condition_number=float(np.linalg.cond(z)),residual=residual)


def complete_year(months,pull_year):
    years=defaultdict(set)
    for value in months:
        year,month=map(int,value.split('-')); years[year].add(month)
    eligible=[year for year,ms in years.items() if year<pull_year and ms==set(range(1,13))]
    if not eligible: raise ValueError('no complete past calendar year')
    return max(eligible)


def group_summary(rows,scope,year):
    result=[]
    for group in ['historical_mature','historical_non_mature']:
        cells=[r for r in rows if r['historical_group']==group and r['status']=='estimated' and (scope=='all_types' or r['flat_type']=='4 ROOM')]
        if not cells: raise ValueError('empty historical-group comparison')
        values=[r['pct_per_year'] for r in cells]
        result.append(dict(sale_year=year,scope=scope,historical_group=group,n_segments=len(cells),n_transactions=sum(r['n'] for r in cells),median_pct_per_year=float(np.median(values)),min_pct_per_year=min(values),max_pct_per_year=max(values)))
    return result


def models(con,year,min_n=MIN_SEGMENT,min_support=MIN_SUPPORT):
    months={r[0] for r in con.execute('SELECT DISTINCT month(sale_date) FROM sales WHERE sale_year=?',[year]).fetchall()}
    if months!=set(range(1,13)):
        raise ValueError(f'incomplete calendar year {year}: missing months {sorted(set(range(1,13))-months)}')
    cur=con.execute('SELECT town,flat_type,historical_group,lease_years,storey_midpoint,floor_area_sqm,month(sale_date),price_per_sqm FROM sales WHERE sale_year=? ORDER BY town,flat_type,month,block,street_name,storey_midpoint,floor_area_sqm,lease_months,resale_price',[year])
    cells=defaultdict(list)
    for town,kind,group,*values in cur.fetchall(): cells[(town,kind,group)].append(values)
    results=[]
    for (town,kind,group),rows in sorted(cells.items()):
        a=np.asarray(rows,float)
        results.append(dict(sale_year=year,town=town,flat_type=kind,historical_group=group,**segment_model(*a.T,min_n=min_n,min_support=min_support)))
    return results


def main():
    import duckdb
    from artifacts import publish_paths,write_csv
    from download import validate_stage
    manifest=validate_stage()
    sgt=timezone(timedelta(hours=8))
    pull_year=datetime.fromisoformat(manifest['retrieved_at']).astimezone(sgt).year
    con=duckdb.connect(config={'threads':1})
    con.execute('CREATE TABLE sales AS SELECT * FROM read_parquet(?)',[(ROOT/'data/processed/sales.parquet').as_posix()])
    year=complete_year([r[0] for r in con.sql('SELECT DISTINCT month FROM sales').fetchall()],pull_year)
    results=models(con,year)
    groups=group_summary(results,'all_types',year)+group_summary(results,'4_room',year)
    with (ROOT/'outputs/bucket_medians_all.csv').open() as f: buckets=list(csv.DictReader(f))
    buckets=[{**r,'eligible':int(r['n'])>=MIN_BUCKET} for r in buckets if int(r['sale_year'])==year]
    eligible_towns=defaultdict(int)
    for r in buckets:
        if r['flat_type']=='4 ROOM' and r['eligible']: eligible_towns[r['town']]+=1
    featured=sorted([r for r in results if r['flat_type']=='4 ROOM' and r['status']=='estimated' and eligible_towns[r['town']]>=3],key=lambda r:(-r['n'],r['town']))[:4]
    if len(featured)!=4: raise ValueError('fewer than four usable 4-room exemplars')
    sensitivity=[]
    variants=[('baseline',year,100,10),('n50',year,50,10),('n200',year,200,10),('support5',year,100,5),('support15',year,100,15),('previous_year',year-1,100,10),('strict_lease_check',year,100,10)]
    for label,y,min_n,support in variants:
        if label=='strict_lease_check':
            con.execute('ALTER TABLE sales RENAME TO sales_wide')
            con.execute('CREATE VIEW sales AS SELECT * FROM sales_wide WHERE lease_offset_months BETWEEN 0 AND 12')
        estimates=results if label=='baseline' else models(con,y,min_n,support)
        if label=='strict_lease_check':
            con.execute('DROP VIEW sales');con.execute('ALTER TABLE sales_wide RENAME TO sales')
        for scope in ['all_types','4_room']:
            for r in group_summary(estimates,scope,y): sensitivity.append(dict(variant=label,min_n=min_n,min_support_years=support,**r))
    bucket_receipts=[]
    for threshold in [20,30,50]:
        accepted=[r for r in buckets if int(r['n'])>=threshold]
        bucket_receipts.append(dict(sale_year=year,min_bucket_n=threshold,retained_buckets=len(accepted),suppressed_buckets=len(buckets)-len(accepted),retained_transactions=sum(int(r['n']) for r in accepted),suppressed_transactions=sum(int(r['n']) for r in buckets if int(r['n'])<threshold)))
    ledger=[]
    for status in sorted({r['status'] for r in results}):
        subset=[r for r in results if r['status']==status]
        ledger.append(dict(sale_year=year,status=status,n_segments=len(subset),n_transactions=sum(r['n'] for r in subset)))
    assert sum(r['n_transactions'] for r in ledger)==con.execute('select count(*) from sales where sale_year=?',[year]).fetchone()[0]
    fields=list(dict.fromkeys(k for r in results for k in r))
    for r in results:
        for k in fields: r.setdefault(k,'')
    outputs=ROOT/'outputs'; pairs=[]
    for name,rows,header in [('slopes.csv',results,fields),('group_summaries.csv',groups,None),('bucket_medians.csv',buckets,None),('featured_segments.csv',featured,None),('sensitivity.csv',sensitivity,None),('bucket_sensitivity.csv',bucket_receipts,None),('model_exclusions.csv',ledger,None)]:
        part=outputs/(name+'.part');write_csv(part,rows,header);pairs.append((part,outputs/name))
    publish_paths(pairs)
    print('POPULATION',year,'segments',len(results),'transactions',sum(r['n'] for r in results),'estimated',sum(r['status']=='estimated' for r in results))
    print('GROUPS',json.dumps(groups))
    print('FEATURED',json.dumps(featured))
    print('MODEL LEDGER',json.dumps(ledger))
    print('BUCKET LEDGER',json.dumps(bucket_receipts))

if __name__=='__main__': main()
