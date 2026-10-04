-- Primary display cells are town x type x year, never pooled across price regimes.
CREATE TABLE bucket_medians AS
SELECT sale_year,town,flat_type,historical_group,lease_band_low,
       lease_band_low+5 AS lease_band_high,count(*) AS n,
       median(lease_years) AS median_lease_years,median(price_per_sqm) AS median_price_per_sqm,
       quantile_cont(price_per_sqm,0.25) AS q25_price_per_sqm,
       quantile_cont(price_per_sqm,0.75) AS q75_price_per_sqm
FROM sales GROUP BY ALL;
CREATE TABLE segment_profile AS
SELECT sale_year,town,flat_type,historical_group,count(*) AS n,
       min(lease_years) AS lease_min_years,max(lease_years) AS lease_max_years,
       count(distinct month) AS n_months,median(price_per_sqm) AS median_price_per_sqm,
       avg(price_per_sqm) AS mean_price_per_sqm,stddev_samp(price_per_sqm) AS sd_price_per_sqm
FROM sales GROUP BY ALL;
