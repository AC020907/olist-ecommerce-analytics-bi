-- Business question: ¿Existe relación entre retrasos y review scores?
-- Real result: yes, the strongest relationship found in this project --
-- on-time orders average 4.29, late orders average 2.57 (a 1.72-point
-- gap on a 5-point scale). See insights/business_insights.md #1.
SELECT
    is_late,
    COUNT(*) AS orders,
    ROUND(AVG(avg_review_score), 2) AS avg_review_score
FROM analytics.fact_orders
WHERE has_valid_delivery_dates
GROUP BY is_late
ORDER BY is_late;
