/*
    Singular test: Ensure every experiment has a control group.
    A/B tests require a control for comparison.
*/

WITH experiments_with_control AS (
    SELECT DISTINCT experiment_name
    FROM {{ ref('experiment_results') }}
    WHERE is_control = true
),

all_experiments AS (
    SELECT DISTINCT experiment_name
    FROM {{ ref('experiment_results') }}
)

SELECT e.experiment_name
FROM all_experiments e
LEFT JOIN experiments_with_control c
    ON e.experiment_name = c.experiment_name
WHERE c.experiment_name IS NULL
