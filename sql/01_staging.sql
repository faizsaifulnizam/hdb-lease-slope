-- Raw strings are never overwritten. Exclusive reasons make the ledger additive.
CREATE TABLE parsed AS
SELECT *, CASE WHEN regexp_full_match(month,'[0-9]{4}-(0[1-9]|1[0-2])')
               THEN try_strptime(month || '-01','%Y-%m-%d')::DATE END AS sale_date,
       try_cast(resale_price AS DOUBLE) AS price,
       try_cast(floor_area_sqm AS DOUBLE) AS area,
       CASE WHEN regexp_full_match(lease_commence_date,'[0-9]{4}')
            THEN try_cast(lease_commence_date AS INTEGER) END AS commence_year,
       CASE WHEN regexp_full_match(remaining_lease,'[0-9]{1,2} years?( [0-9]{1,2} months?)?')
                 AND coalesce(try_cast(nullif(regexp_extract(remaining_lease,' ([0-9]+) months?',1),'') AS INTEGER),0)<12
                 AND try_cast(regexp_extract(remaining_lease,'^([0-9]+)',1) AS INTEGER)*12
                     +coalesce(try_cast(nullif(regexp_extract(remaining_lease,' ([0-9]+) months?',1),'') AS INTEGER),0) BETWEEN 1 AND 1188
            THEN try_cast(regexp_extract(remaining_lease,'^([0-9]+)',1) AS INTEGER)*12
                 +coalesce(try_cast(nullif(regexp_extract(remaining_lease,' ([0-9]+) months?',1),'') AS INTEGER),0) END AS lease_months,
       CASE WHEN regexp_full_match(storey_range,'[0-9]{2} TO [0-9]{2}')
            THEN try_cast(substr(storey_range,1,2) AS INTEGER) END AS storey_low,
       CASE WHEN regexp_full_match(storey_range,'[0-9]{2} TO [0-9]{2}')
            THEN try_cast(substr(storey_range,7,2) AS INTEGER) END AS storey_high
FROM raw;
CREATE TABLE classified AS
SELECT *, lease_months - ((commence_year+99-year(sale_date))*12-(month(sale_date)-1)) AS lease_offset_months,
CASE
 WHEN sale_date IS NULL OR month<'2017-01' OR month>'$MAXMONTH' THEN 'invalid_month'
 WHEN town IS NULL OR town NOT IN (SELECT town FROM town_groups) THEN 'invalid_town'
 WHEN flat_type IS NULL OR flat_type NOT IN ('1 ROOM','2 ROOM','3 ROOM','4 ROOM','5 ROOM','EXECUTIVE','MULTI-GENERATION') THEN 'invalid_type'
 WHEN price IS NULL OR NOT isfinite(price) OR price<=0 THEN 'invalid_price'
 WHEN area IS NULL OR NOT isfinite(area) OR area<=0 THEN 'invalid_area'
 WHEN storey_low IS NULL OR storey_high IS NULL OR storey_low<1 OR storey_high<storey_low OR storey_high>99 THEN 'invalid_storey'
 WHEN commence_year IS NULL OR commence_year<1900 OR commence_year>year(sale_date) THEN 'invalid_commence_year'
 WHEN lease_months IS NULL THEN 'invalid_lease_text'
 WHEN lease_months - ((commence_year+99-year(sale_date))*12-(month(sale_date)-1)) NOT BETWEEN -12 AND 18 THEN 'lease_inconsistent'
 ELSE 'retained' END AS exclusion_reason
FROM parsed;
CREATE TABLE sales AS
SELECT month, sale_date, year(sale_date)::INTEGER AS sale_year, town, flat_type,
       block, street_name, flat_model, area AS floor_area_sqm, price AS resale_price,
       price/area AS price_per_sqm, (storey_low+storey_high)/2.0 AS storey_midpoint,
       commence_year, lease_months, lease_months/12.0 AS lease_years, lease_offset_months,
       floor(lease_months/60.0)::INTEGER*5 AS lease_band_low,
       historical_group
FROM classified JOIN town_groups USING(town) WHERE exclusion_reason='retained';
