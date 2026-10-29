-- Business question: ¿Cuál es el tiempo promedio de entrega? ¿Qué tan
-- frecuente es entregar tarde?
-- Real result: 12.6 days average delivery time; 6.77% late delivery
-- rate overall (6,533 of 96,446 delivered orders with valid dates).
-- Late = delivered on a later calendar day than the promised date.
SELECT
    ROUND(AVG(delivery_days), 1) AS avg_delivery_days,
    COUNT(*) FILTER (WHERE is_late IS NOT NULL) AS orders_with_valid_dates,
    COUNT(*) FILTER (WHERE is_late) AS late_orders,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_late)
        / NULLIF(COUNT(*) FILTER (WHERE is_late IS NOT NULL), 0), 2) AS late_rate_pct
FROM analytics.fact_orders;

-- Broken down by month, to see whether the rate is stable or event-driven
-- (it is NOT stable -- see finding #9 in recommendations.md: it spikes
-- to 12.40% in November 2017, the Black Friday month, and to 14.13% / 18.96%
-- in February / March 2018).
SELECT d.year_month,
    COUNT(*) FILTER (WHERE fo.is_late IS NOT NULL) AS valid_deliveries,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fo.is_late)
        / NULLIF(COUNT(*) FILTER (WHERE fo.is_late IS NOT NULL), 0), 2) AS late_rate_pct
FROM analytics.fact_orders fo
JOIN analytics.dim_date d ON d.date_day = fo.order_date_key
WHERE d.is_in_analysis_window
GROUP BY d.year_month
ORDER BY d.year_month;
