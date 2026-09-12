-- ============================================================================
-- 01_fact_orders.sql
-- Grain: ONE ROW PER order_id. This is the fact table that answers most
-- executive-level KPIs (Total Orders, AOV, delivery time, late rate,
-- review score, repeat-rate-adjacent questions) WITHOUT ever touching
-- order_items or order_payments at their native grain -- which is
-- exactly how we avoid the fan-out/double-counting risk flagged in
-- Phase 1 (data_quality_notes.md #2).
--
-- Revenue and payment amounts are pre-aggregated to the order here
-- (SUM inside this build script, not at report time), so a Power BI
-- measure like [Total Revenue] can safely SUM(items_revenue) from this
-- table without any risk of a fan-out multiplying it.
--
-- review_count / avg_review_score collapse the rare multi-review-per-
-- order case (547 orders, data_quality_notes.md) to one number per
-- order via AVG(), instead of joining raw reviews and fanning out.
-- ============================================================================

DROP TABLE IF EXISTS analytics.fact_orders;

CREATE TABLE analytics.fact_orders AS
WITH items_agg AS (
    SELECT
        order_id,
        COUNT(*)              AS n_items,
        SUM(price)              AS items_revenue,
        SUM(freight_value)        AS freight_total
    FROM raw.order_items
    GROUP BY order_id
),
payments_agg AS (
    SELECT
        order_id,
        SUM(payment_value) AS payments_total
    FROM raw.order_payments
    GROUP BY order_id
),
reviews_agg AS (
    SELECT
        order_id,
        COUNT(*)             AS review_count,
        AVG(review_score)      AS avg_review_score
    FROM raw.order_reviews
    GROUP BY order_id
)
SELECT
    o.order_id,
    c.customer_unique_id,
    o.order_purchase_timestamp::date AS order_date_key,
    o.order_status,
    o.is_delivered,
    o.has_valid_delivery_dates,
    o.delivery_days,
    o.is_late,
    COALESCE(i.n_items, 0)              AS n_items,
    COALESCE(i.items_revenue, 0)          AS items_revenue,
    COALESCE(i.freight_total, 0)            AS freight_total,
    p.payments_total,
    r.review_count,
    r.avg_review_score
FROM staging.orders o
JOIN raw.customers c        ON c.customer_id = o.customer_id
LEFT JOIN items_agg i        ON i.order_id = o.order_id
LEFT JOIN payments_agg p      ON p.order_id = o.order_id
LEFT JOIN reviews_agg r        ON r.order_id = o.order_id;

ALTER TABLE analytics.fact_orders ADD PRIMARY KEY (order_id);
ALTER TABLE analytics.fact_orders
    ADD CONSTRAINT fk_fact_orders_customer FOREIGN KEY (customer_unique_id)
        REFERENCES analytics.dim_customer (customer_unique_id),
    ADD CONSTRAINT fk_fact_orders_date FOREIGN KEY (order_date_key)
        REFERENCES analytics.dim_date (date_day);
CREATE INDEX ix_fact_orders_customer ON analytics.fact_orders (customer_unique_id);
CREATE INDEX ix_fact_orders_date ON analytics.fact_orders (order_date_key);
CREATE INDEX ix_fact_orders_status ON analytics.fact_orders (order_status);

COMMENT ON TABLE analytics.fact_orders IS
'Grain: one row per order. items_revenue/freight_total/payments_total are pre-aggregated here specifically to prevent the order_items x order_payments fan-out. Use this table for Total Orders, AOV, delivery and review KPIs; use fact_order_items only when breaking down by product/category/seller.';
