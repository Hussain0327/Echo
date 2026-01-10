/*
    Singular test: Ensure conversions never exceed leads.
    This is a fundamental marketing funnel constraint.
*/

SELECT
    channel,
    total_leads,
    total_conversions,
    conversion_rate
FROM {{ ref('channel_performance') }}
WHERE total_conversions > total_leads
