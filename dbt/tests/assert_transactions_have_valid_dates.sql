/*
    Singular test: Ensure all transactions have dates within a reasonable range.
    Transactions should be between 2020 and the current date.
*/

SELECT
    transaction_id,
    transaction_date
FROM {{ ref('stg_transactions') }}
WHERE transaction_date < '2020-01-01'::date
   OR transaction_date > CURRENT_DATE
