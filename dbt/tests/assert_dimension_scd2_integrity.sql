/*
    Singular test: Ensure SCD Type 2 integrity for customer dimension.
    Each customer should have exactly one current record.
*/

SELECT
    customer_id,
    COUNT(*) as current_record_count
FROM {{ ref('dim_customer') }}
WHERE is_current = true
GROUP BY customer_id
HAVING COUNT(*) > 1
