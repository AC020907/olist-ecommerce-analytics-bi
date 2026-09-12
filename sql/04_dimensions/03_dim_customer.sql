-- ============================================================================
-- 03_dim_customer.sql
-- Grain: ONE ROW PER customer_unique_id (the real person), not per
-- customer_id (an order-level identifier -- see data_quality_notes.md #1).
-- This is the single most important modeling decision in this project:
-- getting it wrong silently breaks repeat-purchase-rate and any customer-
-- level KPI.
--
-- A customer's address can change between orders (verified: 39 of 96,096
-- customers show more than one state, 122 more than one city across their
-- orders). We resolve this the standard way: take the address from their
-- MOST RECENT order, i.e. their "current" known profile.
-- ============================================================================

DROP TABLE IF EXISTS analytics.dim_customer;

CREATE TABLE analytics.dim_customer AS
WITH customer_orders AS (
    -- Every (customer_unique_id, order) pair, so we can rank by recency.
    SELECT
        c.customer_unique_id,
        c.customer_id,
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state,
        o.order_purchase_timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY c.customer_unique_id
            ORDER BY o.order_purchase_timestamp DESC
        ) AS recency_rank
    FROM raw.customers c
    JOIN raw.orders o ON o.customer_id = c.customer_id
),
most_recent_address AS (
    SELECT customer_unique_id, customer_zip_code_prefix, customer_city, customer_state
    FROM customer_orders
    WHERE recency_rank = 1
),
first_and_last_order AS (
    SELECT
        customer_unique_id,
        MIN(order_purchase_timestamp) AS first_order_date,
        MAX(order_purchase_timestamp) AS most_recent_order_date,
        COUNT(*)                       AS lifetime_order_count
    FROM customer_orders
    GROUP BY customer_unique_id
)
SELECT
    a.customer_unique_id,
    a.customer_zip_code_prefix                  AS zip_code_prefix,
    a.customer_city                              AS city,
    a.customer_state                              AS state,
    f.first_order_date,
    f.most_recent_order_date,
    f.lifetime_order_count,
    (f.lifetime_order_count > 1)                    AS is_repeat_customer
FROM most_recent_address a
JOIN first_and_last_order f USING (customer_unique_id);

ALTER TABLE analytics.dim_customer ADD PRIMARY KEY (customer_unique_id);
CREATE INDEX ix_dim_customer_zip ON analytics.dim_customer (zip_code_prefix);

COMMENT ON TABLE analytics.dim_customer IS
'One row per customer_unique_id (real person). city/state/zip reflect their MOST RECENT order (39 customers changed state, 122 changed city across orders -- verified). lifetime_order_count and is_repeat_customer are computed once here, not re-derived per query, since they depend on the full order history per customer, not on any single fact grain.';
