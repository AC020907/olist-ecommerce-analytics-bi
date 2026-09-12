-- ============================================================================
-- 02_vw_monthly_revenue.sql
-- Monthly net revenue and orders, with MoM growth via LAG(), restricted
-- to the analysis window (2017-01 to 2018-08 -- see data_quality_notes.md
-- #4; 2016 and 2018-09/10 are truncated edges of the dataset).
-- ============================================================================

CREATE OR REPLACE VIEW reporting.vw_monthly_revenue AS
WITH monthly AS (
    SELECT
        d.year_month,
        MIN(d.date_day)     AS month_start,
        SUM(fo.items_revenue) FILTER (
            WHERE fo.order_status NOT IN ('canceled', 'unavailable')) AS net_revenue,
        COUNT(*) FILTER (
            WHERE fo.order_status NOT IN ('canceled', 'unavailable')) AS orders
    FROM analytics.fact_orders fo
    JOIN analytics.dim_date d ON d.date_day = fo.order_date_key
    WHERE d.is_in_analysis_window
    GROUP BY d.year_month
)
SELECT
    year_month,
    month_start,
    net_revenue,
    orders,
    ROUND(net_revenue / NULLIF(orders, 0), 2)                      AS avg_order_value,
    ROUND(
        100.0 * (net_revenue - LAG(net_revenue) OVER (ORDER BY month_start))
        / NULLIF(LAG(net_revenue) OVER (ORDER BY month_start), 0), 2
    )                                                                AS mom_revenue_growth_pct
FROM monthly
ORDER BY month_start;

COMMENT ON VIEW reporting.vw_monthly_revenue IS
'Monthly net revenue, orders, AOV and MoM growth %, restricted to the 2017-01/2018-08 analysis window.';
