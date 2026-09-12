-- Business question: ¿Cuál es el tiempo promedio de entrega? ¿Qué tan
-- frecuente es entregar tarde?
-- Real result: 12.6 days average delivery time; 8.11% late delivery
-- rate overall (7,825 of 96,446 orders with a valid delivery record).
SELECT
    ROUND(AVG(delivery_days), 1) AS avg_delivery_days,
    COUNT(*) FILTER (WHERE has_valid_delivery_dates) AS orders_with_valid_dates,
    COUNT(*) FILTER (WHERE is_late) AS late_orders,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_late)
        / NULLIF(COUNT(*) FILTER (WHERE has_valid_delivery_dates), 0), 2) AS late_rate_pct
FROM analytics.fact_orders;

-- Broken down by month, to see whether the rate is stable or event-driven
-- (it is NOT stable -- see finding #9 in recommendations.md: it spikes
-- to 14.31% in November 2017, the Black Friday month).
SELECT d.year_month,
    COUNT(*) FILTER (WHERE fo.has_valid_delivery_dates) AS valid_deliveries,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fo.is_late)
        / NULLIF(COUNT(*) FILTER (WHERE fo.has_valid_delivery_dates), 0), 2) AS late_rate_pct
FROM analytics.fact_orders fo
JOIN analytics.dim_date d ON d.date_day = fo.order_date_key
WHERE d.is_in_analysis_window
GROUP BY d.year_month
ORDER BY d.year_month;
