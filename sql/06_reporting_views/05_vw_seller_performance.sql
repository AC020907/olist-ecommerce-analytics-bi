-- ============================================================================
-- 05_vw_seller_performance.sql
-- Per-seller revenue, order volume, delivery performance and review score
-- -- deliberately built to surface the "high revenue, low satisfaction"
-- operational-risk pattern (business question #10 from Phase 1).
-- ============================================================================

CREATE OR REPLACE VIEW reporting.vw_seller_performance AS
WITH seller_revenue AS (
    SELECT
        foi.seller_id,
        COUNT(*)                    AS items_sold,
        COUNT(DISTINCT foi.order_id) AS orders,
        SUM(foi.price)                AS revenue
    FROM analytics.fact_order_items foi
    WHERE foi.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY foi.seller_id
),
seller_orders AS (
    -- Delivery/review metrics pulled from fact_orders (order grain) for
    -- the distinct set of orders each seller was involved in -- avoids
    -- counting the same order's review/delivery outcome once per item.
    SELECT
        foi.seller_id,
        fo.order_id,
        fo.delivery_days,
        fo.is_late,
        fo.has_valid_delivery_dates,
        fo.avg_review_score
    FROM (SELECT DISTINCT seller_id, order_id FROM analytics.fact_order_items) foi
    JOIN analytics.fact_orders fo ON fo.order_id = foi.order_id
)
SELECT
    sr.seller_id,
    ds.state                                                          AS seller_state,
    sr.items_sold,
    sr.orders,
    ROUND(sr.revenue, 2)                                                AS revenue,
    ROUND(AVG(so.delivery_days), 1)                                       AS avg_delivery_days,
    ROUND(100.0 * COUNT(*) FILTER (WHERE so.is_late)
        / NULLIF(COUNT(*) FILTER (WHERE so.has_valid_delivery_dates), 0), 2) AS late_delivery_rate_pct,
    ROUND(AVG(so.avg_review_score), 2)                                        AS avg_review_score
FROM seller_revenue sr
JOIN analytics.dim_seller ds ON ds.seller_id = sr.seller_id
JOIN seller_orders so ON so.seller_id = sr.seller_id
GROUP BY sr.seller_id, ds.state, sr.items_sold, sr.orders, sr.revenue
ORDER BY revenue DESC;

COMMENT ON VIEW reporting.vw_seller_performance IS
'Per-seller revenue, delivery performance and review score. Use to find sellers combining high revenue with poor delivery/satisfaction (operational risk).';
