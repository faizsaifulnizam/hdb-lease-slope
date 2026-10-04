SELECT 'row_reconciliation' AS check_name,
 abs((SELECT count(*) FROM raw)-(SELECT count(*) FROM sales)-
 (SELECT count(*) FROM classified WHERE exclusion_reason<>'retained')) AS violations
UNION ALL SELECT 'positive_finite_values',count(*) FROM sales
 WHERE NOT isfinite(price_per_sqm) OR price_per_sqm<=0 OR floor_area_sqm<=0
UNION ALL SELECT 'lease_tolerance',count(*) FROM sales
 WHERE lease_offset_months NOT BETWEEN -12 AND 18 OR lease_months NOT BETWEEN 1 AND 1188
UNION ALL SELECT 'group_coverage',count(*) FROM sales WHERE historical_group IS NULL
UNION ALL SELECT 'required_fields',count(*) FROM sales
 WHERE sale_date IS NULL OR storey_midpoint IS NULL OR lease_years IS NULL;
