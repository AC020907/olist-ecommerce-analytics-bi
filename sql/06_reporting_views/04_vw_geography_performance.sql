-- ============================================================================
-- 04_vw_geography_performance.sql
-- Revenue, orders and delivery time by customer state/region.
-- Geography here is the CUSTOMER's (where the order was shipped to),
-- not the seller's -- these are two different, equally valid "geographic
-- analysis" questions, and the column names say which one this is.
-- ============================================================================

CREATE OR REPLACE VIEW reporting.vw_customer_geography_performance AS
SELECT
    dg.region,
    dg.state,
    COUNT(*)                                                       AS orders,
    ROUND(SUM(fo.items_revenue), 2)                                  AS revenue,
    ROUND(AVG(fo.delivery_days), 1)                                    AS avg_delivery_days,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fo.is_late)
        / NULLIF(COUNT(*) FILTER (WHERE fo.has_valid_delivery_dates), 0), 2) AS late_delivery_rate_pct,
    ROUND(AVG(fo.avg_review_score), 2)                                   AS avg_review_score
FROM analytics.fact_orders fo
JOIN analytics.dim_customer dc ON dc.customer_unique_id = fo.customer_unique_id
JOIN analytics.dim_geography dg ON dg.zip_code_prefix = dc.zip_code_prefix
WHERE fo.order_status NOT IN ('canceled', 'unavailable')
GROUP BY dg.region, dg.state
ORDER BY revenue DESC;

COMMENT ON VIEW reporting.vw_customer_geography_performance IS
'Revenue, delivery time and satisfaction by customer state/region (shipping destination). See vw_seller_performance for the seller-side geography.';
