# Data audit — HDB lease slope

Snapshot: live independent pull **2026-10-07 00:24:09 SGT**. [HDB dataset](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view), ID `d_8b84c4ee58e3cfc0ece0d773c8ca6abc`. Raw bytes are ignored, unchanged after acquisition. [Byte receipt](../outputs/source_snapshot.json): SHA-256 `945e09d75efb2eec1ab1618ce369c0d8eb885ef34158e29426f1af141d4000e4`, 23,940,111 bytes, 242,032 records, 118 months (2017-01–2026-10). The October 2026 data are partial, not a completed year.

The original build was reviewed on 2026-10-04. Exact-row multiset comparison against its preserved SHA-256 snapshot finds **114 additions in October 2026 and two removals (one July, one August 2026)**, net +112. There are **zero 2025 additions or removals**. No unique transaction ID is invented: the comparison uses all 11 source fields and retains multiplicity. The 2025 baseline, 2024 comparison and every sensitivity were recomputed; their CSV bytes remain unchanged.

## Profile before analysis

- All 11 source columns present; zero empty values in every column. 26 observed towns, seven flat types.
- Resale price: S$140,000–S$1,728,000. Floor area: 31–366.7 m². Lease commencement year: 1966–2023. Large areas are not automatically errors; no percentile trimming or winsorising.
- Lease formats: 222,181 records with years + months (including singular `01 month`); 19,851 years-only strings. Years-only values are stored as exact multiples of 12 months, not imputed midpoint values.
- 318 excess fully identical-looking records. **Retained:** there is no unit number or transaction ID in the public file. A repeat-looking record can describe different units or transactions. `block` × `street_name` is not a unique transaction key. No generated ID is represented as one.
- Live webpage column dictionary confirmed via the fetched HTML: month is Month (YYYY-MM); town/type/block/street/storey/model/lease commencement/remaining lease are Text; floor area is also published as Text and must be converted; resale price is Numeric. The original 2026-10-04 live page total was 241,920, matching that original independent CSV pull; the refreshed count here comes from the 2026-10-07 CSV, not a new webpage-total check. Seed metadata was used for initial reconnaissance only, not numeric results.

HDB's live notes say floor area includes purchased recess areas, upgrading space and roof terraces; transactions between relatives and part shares may be excluded by the provider; agreed prices depend on many factors and are indicative. These are provider exclusions, not counts this file can reconstruct.

## Lease consistency: a screen, not a correction

For January commencement in year C and registration in month M of year Y, baseline months = `12*(C+99-Y) - (M-1)`. Reported minus baseline = `lease_offset_months`. Only the commencement **year**, not its month/day, is supplied. An unknown start month can contribute 0–11 months; years-only reporting loses sub-year precision. Registration month and the lease-information reference date may differ.

Chosen before outcome estimates: retain offsets **−12 through +18 months inclusive**. The low end allows a year of coarse precision; the high end allows the unknown start month plus monthly rounding/reference-date slack. The six-month extra reference-date allowance is an **analyst QC choice**, not an HDB-published maximum delay. The current source dictionary gives no exact lease-reference-date/rounding rule; do not present secondary mirrors' definitions as an official current rule. A naive exact January-start check would discard valid records. Offsets 13–18 and small negatives stay in the primary population, with a stricter **0–12** screen as sensitivity.

Exactly **one** record is outside the wide interval: Jurong East, 3-room, Teban Gardens Road block 37, January 2025, `40 years 01 month`, commencement 1981, offset **−179** months. It is excluded as inconsistent with the 99-year assumption, **not proven erroneous**. An atypical lease or source issue is possible. Do not rewrite it as 55 years. [Excluded-row receipt](../outputs/excluded_rows.csv).

| Exclusive classification | Records |
|---|---:|
| Retained | 242,031 |
| Lease inconsistent | 1 |
| Invalid month / town / type / price / area / storey / commencement / text | 0 each |
| Raw total | 242,032 |

[Ledger](../outputs/exclusions.csv) reconciles retained + all exclusive exclusions = raw. Invalid finite/nonpositive numbers, reversed/unparseable storey ranges, impossible chronology and malformed lease components have runnable synthetic checks. Structural download failures abort before replacing the previous raw/manifest pair.

## Annual analytic population

Latest complete past calendar year with all 12 months = **2025**. Retained annual records **25,084**, across **129** town × flat-type cells. This is an observed-transactions population, not Singapore's housing stock.

- Primary: 639 five-year cells, 235 with n≥30 (20,766 transactions). 404 suppressed display cells contain 4,318 transactions. Suppression does not remove them from staging or automatically from the model.
- Secondary: 62 estimable segments / 22,048 transactions. 64 n<100 cells / 2,576 transactions withheld; three <10-year support cells / 460 transactions withheld. No primary cell reached a rank/variation/condition guard. [Model ledger](../outputs/model_exclusions.csv) totals 25,084.
- All 23 eligible 4-room town slopes are shown. Bukit Timah (17), Central Area (68) and Marine Parade (33) are below n=100. Tengah appears in the historical lookup but has no observed resale record; no zero slope invented.
- Four examples are the largest estimable 4-room cells with at least three n≥30 bands: Sengkang 940, Tampines 892, Woodlands 836, Yishun 825. Selection is by count/support, not slope or price.

## Model diagnostics and interpretation

Separate 2025 town × type regressions use intercept + centered lease years + centered storey midpoint + centered floor area + indicators for each observed registration month except the earliest (reference month). No numeric month trend substitutes for these time effects; the intercept plus 11 dummies has 15 total parameters with all 12 months. `lease_commence_year`/age/block fixed effects are not included: those would absorb the cross-sectional vintage variation or generate an age-period identity.

Across the 62 reported fits: residual df 86–925; control-residual lease SD 1.74–16.53 years; lease-on-controls R² 0.038–0.739; scaled-design condition number 5.39–9.86; maximum leverage 0.031–0.451. Lease therefore retains variation after sale month, storey and size controls, but this is **vintage/location variation between flats**, not identified aging of a flat. Rank-deficient cells and residual lease SD<0.5 years are withheld. Residual df≥30 and at least six observed months are also required.

Residual log-price RMSE ranges 0.040–0.132; correlation of absolute residuals with fitted values ranges −0.440–0.351, indicating heterogeneous scatter. HC3 covariance handles conditional heteroskedasticity using squared residuals / `(1-h_i)^2`; intervals use beta ±1.96×HC3 SE (large-sample normal approximation). They are not exact small-sample, clustered-block, simultaneous, causal or prediction intervals. Transactions in the same block may be dependent; **HC3 does not correct that**, and intervals can be too narrow. No p-value rankings or significance claims are made. Primary medians show nonlinearity (notably Sengkang), so a single log-linear coefficient is only a support-wide summary. Full diagnostics, support and intervals remain in [slopes.csv](../outputs/slopes.csv).

## Historical groups, not current classifications

[HDB Annex A](https://www.hdb.gov.sg/-/media/hdb-pulse/news/2023/new-plus-housing-model-with-more-subsidies/Annex-A1.pdf), attached to the **20 August 2023** announcement, was fetched directly as a PDF and its full list read: 15 mature and 12 non-mature towns/estates. [Lookup](../outputs/town_groups.csv) fixes this list. The only label mapping is `Kallang/ Whampoa` → the dataset's `KALLANG/WHAMPOA`; all other names case-map directly. This is not planning-area geography. Tengah is non-mature on Annex A and is in the lookup. This resale file has no Tengah rows, so no slope is estimated.

[HDB's new framework](https://www.hdb.gov.sg/about-us/news-and-publications/press-releases/New-Flat-Classification-Framework) applies Standard/Plus/Prime at the **project/location level from October 2024**, not a new mature-town list; classifications can differ inside one town. This analysis is explicitly a **historical-group comparison**. Group slopes are unweighted segment medians/ranges, not a pooled transaction coefficient. Mature fits contain 12 four-room, nine three-room, seven five-room and one executive cell; non-mature fits contain 11 four-room, eight three-room, 11 five-room, two executive and one two-room cell. The like-for-like 4-room summary is therefore the clearest group sensitivity.

## Independent receipts and originality

Stdlib CSV + `statistics.median` checks reproduced three primary cells directly from raw: Sengkang 70–<75 years **n=152, S$6,112.8608187134505/m²**; Tampines 55–<60 **n=211, S$6,179.885714285714/m²**; Yishun 55–<60 **n=175, S$5,659.340659340659/m²**. Synthetic regression oracle gives beta=[1,2], df=2, SSE=4, HC3 slope variance=100/49. Synthetic data are tests only, never analysis inputs.

2026-10-04 sweep: GitHub repository and code searches for `hdb lease` / `hdb lease decay`, web and Kaggle checks. Close neighbors: [weiyuet](https://github.com/weiyuet/hdb-resale-flat-prices) (0 stars, lease price/m² smoothing and Bayesian expected-price model); [Joanna Khek](https://github.com/Joanna-Khek/hdb_resale_prices) (3 stars, lease × town × flat-type explorer); [Kaggle prediction tutorial](https://www.kaggle.com/code/teyang/drivers-of-hdb-resale-price-and-prediction). Verdict **medium overlap**, not novel data or topic. Difference is town × type × **year** medians, audited lease precision/exclusions, guarded per-cell controlled slopes, historically sourced grouping, sensitivity, memo and reproducible receipt bundle. No estimator, forecast or first-ever claim. Recheck at publication.

## Engineering limits

Each producer stages its complete artifact batch and validates before replacement. Ordinary swap exceptions roll back; no cross-pipeline crash-atomicity or concurrent-reader guarantee. One writer required. CI's stdlib job checks committed receipts; a separate focused offline job executes parser, SQL invalid-row, synthetic math and headline-roundoff tests. A Linux live-refit job downloads HDB, requires the reviewed byte SHA-256, and runs staging, analysis, figures, smoke, `src/verify.py` and the mirror/rollback check. Official snapshot revisions require review rather than silently updating the headline. Raw is intentionally not vendored. Repeated hashes establish same-environment determinism, not cross-OS pixel identity. A future official revision changes results; compare the source byte hash before expecting identity.
