/*
    Singular test: Ensure MRR growth rate is within reasonable bounds.
    Catch data quality issues where growth appears impossibly high.
*/

SELECT
    month,
    mrr,
    previous_month_revenue,
    growth_rate_pct
FROM {{ ref('mrr_monthly') }}
WHERE growth_rate_pct IS NOT NULL
  AND (growth_rate_pct > 500 OR growth_rate_pct < -90)
