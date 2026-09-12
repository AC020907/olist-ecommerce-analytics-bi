-- ============================================================================
-- 01_vw_executive_summary.sql
-- Single-row view with the top-line KPIs. Useful as a quick sanity check
-- and as a direct source for a simple export, but NOT what Power BI's
-- main model imports -- Power BI imports the star schema itself
-- (fact_orders, fact_order_items, fact_payments, dim_*) so DAX measures
-- and slicers can filter at row level (see docs/kpi_definitions.md for
-- why a pre-aggregated view can't support that).
--
-- "Net" revenue excludes canceled/unavailable orders (they don't
-- represent a completed sale, even though 461 canceled orders do have
-- item rows recorded, worth $95,235.27 -- see docs/kpi_definitions.md
-- for the full gross-vs-net discussion).
-- ============================================================================

CREATE OR REPLACE VIEW reporting.vw_executive_summary AS
SELECT
    COUNT(*)                                                       AS total_orders,
    COUNT(DISTINCT customer_unique_id)                                AS total_customers,
    ROUND(SUM(items_revenue) FILTER (
        WHERE order_status NOT IN ('canceled', 'unavailable')), 2)      AS net_revenue,
    ROUND(SUM(items_revenue), 2)                                          AS gross_revenue,
    ROUND(SUM(items_revenue) FILTER (
        WHERE order_status NOT IN ('canceled', 'unavailable'))
        / NULLIF(COUNT(*) FILTER (
            WHERE order_status NOT IN ('canceled', 'unavailable')), 0), 2) AS avg_order_value,
    ROUND(SUM(freight_total), 2)                                            AS total_freight,
    ROUND(100.0 * SUM(freight_total) / NULLIF(SUM(items_revenue), 0), 2)     AS freight_pct_of_revenue,
    ROUND(AVG(n_items), 2)                                                    AS avg_items_per_order,
    ROUND(AVG(delivery_days), 1)                                               AS avg_delivery_days,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_late)
        / NULLIF(COUNT(*) FILTER (WHERE has_valid_delivery_dates), 0), 2)       AS late_delivery_rate_pct,
    ROUND(AVG(avg_review_score), 2)                                              AS avg_review_score
FROM analytics.fact_orders;

COMMENT ON VIEW reporting.vw_executive_summary IS
'One row of headline KPIs, computed from analytics.fact_orders. Reference values only -- see docs/kpi_definitions.md.';
