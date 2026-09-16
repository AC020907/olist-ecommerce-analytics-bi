-- ============================================================================
-- 03_vw_category_performance.sql
-- Revenue, volume and average review score per product category.
-- Joins fact_order_items (revenue, at item grain) to fact_orders
-- (review score, at order grain) through order_id, aggregating each
-- side independently first -- same fan-out-safe pattern as fact_orders
-- itself (see docs/star_schema_design.md).
-- ============================================================================

CREATE OR REPLACE VIEW reporting.vw_category_performance AS
WITH category_revenue AS (
    SELECT
        dp.category_name_en,
        COUNT(*)                 AS items_sold,
        COUNT(DISTINCT foi.order_id) AS orders,
        SUM(foi.price)              AS revenue,
        AVG(foi.price)                AS avg_item_price
    FROM analytics.fact_order_items foi
    JOIN analytics.dim_product dp ON dp.product_id = foi.product_id
    WHERE foi.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY dp.category_name_en
),
category_reviews AS (
    -- Average review score per category: distinct orders per category
    -- first, then join to fact_orders' already-collapsed review score --
    -- an order with 2 items in the same category is not double counted
    -- because we group by (category, order_id) before averaging.
    SELECT
        co.category_name_en,
        AVG(fo.avg_review_score) AS avg_review_score
    FROM (
        SELECT DISTINCT dp.category_name_en, foi.order_id
        FROM analytics.fact_order_items foi
        JOIN analytics.dim_product dp ON dp.product_id = foi.product_id
        WHERE foi.order_status NOT IN ('canceled', 'unavailable')
    ) co
    JOIN analytics.fact_orders fo ON fo.order_id = co.order_id
    GROUP BY co.category_name_en
)
SELECT
    r.category_name_en,
    r.items_sold,
    r.orders,
    ROUND(r.revenue, 2)         AS revenue,
    ROUND(r.avg_item_price, 2)   AS avg_item_price,
    ROUND(rv.avg_review_score, 2) AS avg_review_score
FROM category_revenue r
JOIN category_reviews rv USING (category_name_en)
ORDER BY revenue DESC;

COMMENT ON VIEW reporting.vw_category_performance IS
'Revenue, item volume and average review score per product category (English name). Excludes canceled/unavailable orders.';
