/*
    Singular test: Ensure customers with plan_type 'enterprise'
    are in the 'enterprise' or 'professional' segment.
    Business rule validation.
*/

SELECT
    customer_id,
    segment,
    plan_type
FROM {{ ref('dim_customer') }}
WHERE is_current = true
  AND plan_type = 'enterprise'
  AND segment NOT IN ('enterprise', 'professional')
