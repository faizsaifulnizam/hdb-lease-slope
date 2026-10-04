# Sensitivity — what moves, and what remains a descriptive comparison

Baseline: 2025, model n≥100, lease support≥10 years, full-rank storey/area/month-controlled OLS; primary buckets n≥30. Values below are unweighted segment medians, **percentage association per extra lease year**, not annual price changes. [All values and ranges](../outputs/sensitivity.csv).

| Variant | All types historical mature | All types historical non-mature | 4-room mature | 4-room non-mature |
|---|---:|---:|---:|---:|
| Baseline | 1.198% | 0.689% | 1.197% | 0.675% |
| n≥50 | 1.195% | 0.675% | 1.197% | 0.675% |
| n≥200 | 1.195% | 0.690% | 1.209% | 0.682% |
| Support≥5 years | 1.197% | 0.689% | 1.197% | 0.675% |
| Support≥15 years | 1.203% | 0.689% | 1.197% | 0.675% |
| Previous year (2024) | 1.181% | 0.706% | 1.208% | 0.650% |
| Stricter offset 0–12 months | 1.199% | 0.691% | 1.197% | 0.675% |

The group-median ordering persists, but eligible-cell membership changes. n≥50 admits noisier/negative coefficients; ≥5-year support admits steeper short-support coefficients (maximum non-mature 2.64%). A stable median does not validate individual slope estimates or imply shared common support between groups. Ranges are segment heterogeneity, not confidence intervals for a group effect. There is no multiple-testing significance exercise.

4-room limits differences in flat-type composition, but different towns/vintages/support still remain. No matched-block comparison or causal group test is claimed. Individual β is converted with `100*expm1(β)` **before** segment median/range computation. A one-year-shorter comparison would be `100*expm1(-β)`, not simply the negative of the displayed longer-lease percentage, and is still cross-sectional.

Primary display suppression ([receipt](../outputs/bucket_sensitivity.csv)):

| Minimum bucket n | Eligible bands | Suppressed bands | Eligible transactions | Suppressed transactions |
|---|---:|---:|---:|---:|
| 20 | 308 | 331 | 22,518 | 2,566 |
| 30 | 235 | 404 | 20,766 | 4,318 |
| 50 | 159 | 480 | 17,887 | 7,197 |

Every row sums to 639 bands / 25,084 retained annual records. Primary charts keep n≥30; it is not lowered to make examples look smoother. Model fitting uses all valid transactions in eligible cells, not only the display bands. Missing bands are not zero prices or evidence of an absent housing stock.
