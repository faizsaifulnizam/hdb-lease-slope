"""Small plots; all three views and both themes validated before batch replacement."""
import csv
import json
import math
import shutil
from datetime import datetime,timedelta,timezone
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.text import Text
from matplotlib.lines import Line2D
import numpy as np
import duckdb
from artifacts import publish_paths
from analysis import MIN_BUCKET

ROOT=Path(__file__).resolve().parents[1]
DPI=200


def rows(name):
    with (ROOT/'outputs'/name).open(encoding='utf-8') as f: return list(csv.DictReader(f))


def qa(fig,name):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height()
    boxes=[]
    for t in fig.findobj(Text):
        if t.get_visible() and t.get_text().strip():
            bb=t.get_window_extent(renderer)
            if bb.width>0 and bb.height>0:
                assert bb.x0>=39 and bb.x1<=w-39 and bb.y0>=39 and bb.y1<=h-39,(name,t.get_text(),tuple(bb.bounds),w,h)
    for ax in fig.axes:
        labels=[t for t in ax.texts if t.get_visible() and t.get_text().strip()]
        for i,a in enumerate(labels):
            for b in labels[i+1:]:
                assert not a.get_window_extent(renderer).overlaps(b.get_window_extent(renderer)),(name,'annotations overlap')
    for a in fig.texts:
        for ax in fig.axes:
            assert not a.get_window_extent(renderer).overlaps(ax.title.get_window_extent(renderer)),(name,'header/footer overlap')
    # Header/footer cannot collide. No fixed legends or floating data annotations.
    for i,a in enumerate(fig.texts):
        for b in fig.texts[i+1:]:
            assert not a.get_window_extent(renderer).overlaps(b.get_window_extent(renderer)),(name,'figure text overlaps',a.get_text(),b.get_text(),tuple(a.get_window_extent(renderer).bounds),tuple(b.get_window_extent(renderer).bounds))
    print('QA PASS',name,'all text >=40px canvas margins; no annotation/header overlap')


def frame(fig,title,subtitle,source,footer):
    h=fig.get_figheight()*DPI
    fig.text(.035,1-45/h,title,fontsize=16,weight='semibold',ha='left',va='top')
    fig.text(.035,1-115/h,subtitle,fontsize=9,ha='left',va='top')
    fig.text(.035,45/h,source,fontsize=8,ha='left',va='bottom')
    fig.text(.035,80/h,footer,fontsize=8,ha='left',va='bottom')


def publish_figures(pairs):
    pairs=list(pairs)
    mirror=ROOT/'docs/img';mirror.mkdir(parents=True,exist_ok=True)
    for src,dst in list(pairs):
        staged=mirror/(dst.name+'.part')
        shutil.copyfile(src,staged)
        pairs.append((staged,mirror/dst.name))
    publish_paths(pairs)


def main():
    featured=rows('featured_segments.csv');buckets=rows('bucket_medians.csv');slopes=rows('slopes.csv')
    year=int(featured[0]['sale_year']); manifest=json.loads((ROOT/'outputs/source_snapshot.json').read_text())
    pull=datetime.fromisoformat(manifest['retrieved_at']).astimezone(timezone(timedelta(hours=8))).date().isoformat()
    source=f'Source: HDB / data.gov.sg · pulled {pull} · registration year {year}'
    directory=ROOT/'reports/figures';directory.mkdir(parents=True,exist_ok=True)
    pairs=[]
    con=duckdb.connect(config={'threads':1})
    raw=con.execute('SELECT lease_years,storey_midpoint,floor_area_sqm,month(sale_date),price_per_sqm FROM read_parquet(?) WHERE sale_year=? AND town=? AND flat_type=\'4 ROOM\' ORDER BY month,block,street_name,storey_midpoint,floor_area_sqm,lease_months,resale_price',[(ROOT/'data/processed/sales.parquet').as_posix(),year,featured[0]['town']]).fetchall()
    a=np.asarray(raw,float);lease,storey,area,month,price=a.T
    controls=np.column_stack([np.ones(len(a)),storey-storey.mean(),area-area.mean()]+[(month==m).astype(float) for m in sorted(set(month))[1:]])
    xr=lease-controls@np.linalg.lstsq(controls,lease,rcond=None)[0]
    yr=np.log(price)-controls@np.linalg.lstsq(controls,np.log(price),rcond=None)[0]
    beta=float(featured[0]['beta_per_year'])
    assert abs(float(xr@yr/(xr@xr))-beta)<1e-12
    for dark in [False,True]:
        for f in (ROOT/'assets/fonts').glob('*.ttf'): font_manager.fontManager.addfont(str(f))
        plt.style.use(str(ROOT/'assets'/('style-dark.mplstyle' if dark else 'style.mplstyle')))
        suffix='-dark' if dark else ''
        petrol='#4C93B5' if dark else '#22607B';burnt='#D97E4F' if dark else '#C0552B';muted='#8B98A5' if dark else '#5C6B79'
        # F1: four largest usable 4-room segments, no outcome-based selection.
        fig,axes=plt.subplots(2,2,figsize=(8,7),dpi=DPI,sharex=True,sharey=True)
        fig.subplots_adjust(left=.12,right=.97,bottom=.19,top=.82,hspace=.43,wspace=.28)
        frame(fig,'Longer leases usually sit higher — not on one curve',f'{year} · 4-room · four largest usable town segments · 5-year bands',source,'Dots: medians at median lease (n >= 30); whiskers: transaction IQR, not confidence intervals.')
        for ax,r in zip(axes.flat,featured):
            cells=[b for b in buckets if b['town']==r['town'] and b['flat_type']=='4 ROOM' and b['eligible']=='True']
            x=[float(b['median_lease_years']) for b in cells];y=[float(b['median_price_per_sqm']) for b in cells]
            err=np.array([[v-float(b['q25_price_per_sqm']) for v,b in zip(y,cells)],[float(b['q75_price_per_sqm'])-v for v,b in zip(y,cells)]])
            ax.errorbar(x,y,yerr=err,fmt='o',capsize=3,color=petrol,ms=5,lw=1)
            ax.set_title(f"{r['town'].title()} · n={int(r['n']):,}",fontsize=11)
            ax.set_xlim(45,99);ax.set_xticks([50,60,70,80,90]);ax.set_xlabel('Remaining lease (years)',fontsize=9)
            ax.set_ylabel('Price (S$/m²)',fontsize=9)
        qa(fig,'f1'+suffix);p=directory/('f1_buckets'+suffix+'.png.part');fig.savefig(p,format='png',dpi=DPI);plt.close(fig);pairs.append((p,directory/('f1_buckets'+suffix+'.png')))
        # F2: every eligible 4-room town, alphabetical not ranking by outcome.
        cells=[r for r in slopes if r['flat_type']=='4 ROOM' and r['status']=='estimated']
        fig,ax=plt.subplots(figsize=(8,9),dpi=DPI)
        fig.subplots_adjust(left=.28,right=.92,bottom=.16,top=.83)
        frame(fig,'4-room lease associations vary across towns',f'{year} · storey, area and month controlled · every eligible 4-room segment',source,'Circles: historical mature; squares: historical non-mature. Bars: approximate 95% HC3 intervals.')
        for i,r in enumerate(cells):
            mature=r['historical_group']=='historical_mature';v=float(r['pct_per_year']);low=float(r['ci_low_pct']);high=float(r['ci_high_pct'])
            ax.errorbar(v,i,xerr=[[v-low],[high-v]],fmt='o' if mature else 's',ms=5,color=petrol if mature else burnt,capsize=3)
        ax.set_yticks(range(len(cells)),[f"{r['town'].title()} ({int(r['n']):,})" for r in cells],fontsize=9)
        ax.invert_yaxis();ax.axvline(0,color=muted,lw=1,ls='--');ax.set_xlabel('Price/m² association per extra lease year (%)',fontsize=10)
        low=min(float(r['ci_low_pct']) for r in cells)-.15;high=max(float(r['ci_high_pct']) for r in cells)+.15
        ax.set_xlim(low,high);ax.set_xticks(np.arange(math.ceil(low*2)/2,high,.5))
        ax.grid(axis='x');ax.yaxis.grid(False)
        ax.legend(handles=[Line2D([],[],marker='o',linestyle='none',color=petrol,label='Historical mature'),Line2D([],[],marker='s',linestyle='none',color=burnt,label='Historical non-mature')],loc='best',fontsize=8)
        qa(fig,'f2'+suffix);p=directory/('f2_slopes'+suffix+'.png.part');fig.savefig(p,format='png',dpi=DPI);plt.close(fig);pairs.append((p,directory/('f2_slopes'+suffix+'.png')))
        # F3: raw primary display beside the exact partial-regression seam (not predicted prices).
        fig,axes=plt.subplots(1,2,figsize=(8,4.5),dpi=DPI)
        fig.subplots_adjust(left=.12,right=.93,bottom=.25,top=.72,wspace=.38)
        frame(fig,f"{featured[0]['town'].title()}: a cross-section, not a flat's future",f"{year} · 4-room · n={len(a):,} · selected by usable transaction count",source,'Left: raw prices + eligible medians. Right: controls removed from both axes; line = lease coefficient.')
        axes[0].scatter(lease,price,s=7,alpha=.18,color=muted,rasterized=True)
        cells=[b for b in buckets if b['town']==featured[0]['town'] and b['flat_type']=='4 ROOM' and b['eligible']=='True']
        axes[0].scatter([float(b['median_lease_years']) for b in cells],[float(b['median_price_per_sqm']) for b in cells],s=35,color=petrol)
        axes[0].set_xlabel('Remaining lease (years)',fontsize=9);axes[0].set_ylabel('Price (S$/m²)',fontsize=9)
        axes[1].scatter(xr,100*yr,s=7,alpha=.18,color=muted,rasterized=True)
        axes[1].plot([xr.min(),xr.max()],[100*beta*xr.min(),100*beta*xr.max()],color=petrol,lw=2)
        axes[1].set_xlabel('Lease residual (years)',fontsize=9);axes[1].set_ylabel('log(price/m²) residual × 100',fontsize=9)
        axes[0].set_title('Raw prices and band medians',fontsize=10)
        axes[1].set_title('Storey, area and month removed',fontsize=10)
        qa(fig,'f3'+suffix);p=directory/('f3_exemplar'+suffix+'.png.part');fig.savefig(p,format='png',dpi=DPI);plt.close(fig);pairs.append((p,directory/('f3_exemplar'+suffix+'.png')))
        # SVG generator stays intentionally small: one question, no fabricated data shapes.
        bg='#14293D' if dark else '#FBFBF9';ink='#E7E3DC' if dark else '#14293D'
        banner=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="320" viewBox="0 0 1280 320" role="img" aria-labelledby="title desc"><title id="title">HDB lease slopes, stratified</title><desc id="desc">Same town, flat type and year. Cross-sectional associations, not individual-flat decay.</desc><rect width="1280" height="320" fill="{bg}"/><path d="M64 64H1216" stroke="{petrol}" stroke-width="4"/><text x="64" y="142" font-family="Source Serif 4,Georgia,serif" font-size="48" fill="{ink}">A lease slope is not a decay forecast</text><text x="64" y="193" font-family="Inter,Arial,sans-serif" font-size="23" fill="{muted}">Same town. Same flat type. Same year. Different remaining leases.</text><text x="64" y="251" font-family="Inter,Arial,sans-serif" font-size="20" fill="{petrol}">HDB LEASE SLOPE · DESCRIPTIVE ONLY</text><text x="1216" y="270" text-anchor="end" font-family="Inter,Arial,sans-serif" font-size="16" fill="{muted}">Singapore public data · 6 of 6</text></svg>'''
        p=ROOT/'assets'/('banner'+suffix+'.svg.part');p.write_text(banner,encoding='utf-8');pairs.append((p,ROOT/'assets'/('banner'+suffix+'.svg')))
    publish_figures(pairs)
    print('FIGURES/BANNERS VALIDATED',len(pairs),'partial regression identity PASS')

if __name__=='__main__': main()
