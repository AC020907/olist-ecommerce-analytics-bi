-- ============================================================================
-- 04_vw_geography_performance.sql
-- Revenue, orders and delivery time by customer state/region.
-- Geography here is the CUSTOMER's (where the order was shipped to),
-- not the seller's -- these are two different, equally valid "geographic
-- analysis" questions, and the column names say which one this is.
--
-- LEFT JOIN to dim_geography, not an inner join: 272 net orders
-- (R$36,199.13, ~0.27% of net revenue) belong to customers whose
-- zip_code_prefix never appears in the raw geolocation dataset at all
-- (a real gap in Olist's source data, not a bug in dim_geography's
-- aggregation -- see data_quality_notes.md #13). An inner join here
-- would silently drop that revenue from every state/region total,
-- making this view's grand total disagree with Net Revenue everywhere
-- else in the project. Those orders are instead rolled into an explicit
-- 'Unknown' region/state, the same way Power BI would show them as a
-- "(Blank)" category rather than dropping them from a visual's total.
-- ============================================================================

CREATE OR REPLACE VIEW reporting.vw_customer_geography_performance AS
SELECT
    COALESCE(dg.region, 'Unknown') AS region,
    COALESCE(dg.state, 'Unknown')  AS state,
    COUNT(*)                                                       AS orders,
    ROUND(SUM(fo.items_revenue), 2)                                  AS revenue,
    ROUND(AVG(fo.delivery_days), 1)                                    AS avg_delivery_days,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fo.is_late)
        / NULLIF(COUNT(*) FILTER (WHERE fo.has_valid_delivery_dates), 0), 2) AS late_delivery_rate_pct,
    ROUND(AVG(fo.avg_review_score), 2)                                   AS avg_review_score
FROM analytics.fact_orders fo
JOIN analytics.dim_customer dc ON dc.customer_unique_id = fo.customer_unique_id
LEFT JOIN analytics.dim_geography dg ON dg.zip_code_prefix = dc.zip_code_prefix
WHERE fo.order_status NOT IN ('canceled', 'unavailable')
GROUP BY COALESCE(dg.region, 'Unknown'), COALESCE(dg.state, 'Unknown')
ORDER BY revenue DESC;

COMMENT ON VIEW reporting.vw_customer_geography_performance IS
'Revenue, delivery time and satisfaction by customer state/region (shipping destination). LEFT JOIN to dim_geography so orders with an unmapped zip prefix land in an explicit ''Unknown'' bucket instead of being silently dropped -- this view''s revenue total reconciles exactly to Net Revenue. See vw_seller_performance for the seller-side geography.';
