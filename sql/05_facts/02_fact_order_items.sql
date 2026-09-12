-- ============================================================================
-- 02_fact_order_items.sql
-- Grain: ONE ROW PER (order_id, order_item_id) -- identical to raw.order_items,
-- no aggregation. This is the ONLY fact table that should be used for
-- product/category/seller breakdowns of revenue, precisely because
-- product and seller only exist at this grain.
--
-- Deliberately does NOT bring in payment_value or review_score: joining
-- either here would fan out (an order with 2 items and 2 payments would
-- produce 4 rows, double-counting both). If a report needs "revenue AND
-- payment method" together, it aggregates each fact independently to the
-- order grain first and joins on order_id -- never row-to-row.
-- ============================================================================

DROP TABLE IF EXISTS analytics.fact_order_items;

CREATE TABLE analytics.fact_order_items AS
SELECT
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    oi.seller_id,
    c.customer_unique_id,
    o.order_purchase_timestamp::date AS order_date_key,
    o.order_status,
    oi.price,
    oi.freight_value,
    oi.shipping_limit_date
FROM raw.order_items oi
JOIN raw.orders o     ON o.order_id = oi.order_id
JOIN raw.customers c  ON c.customer_id = o.customer_id;

ALTER TABLE analytics.fact_order_items ADD PRIMARY KEY (order_id, order_item_id);
ALTER TABLE analytics.fact_order_items
    ADD CONSTRAINT fk_foi_product  FOREIGN KEY (product_id)  REFERENCES analytics.dim_product (product_id),
    ADD CONSTRAINT fk_foi_seller   FOREIGN KEY (seller_id)   REFERENCES analytics.dim_seller (seller_id),
    ADD CONSTRAINT fk_foi_customer FOREIGN KEY (customer_unique_id) REFERENCES analytics.dim_customer (customer_unique_id),
    ADD CONSTRAINT fk_foi_date     FOREIGN KEY (order_date_key) REFERENCES analytics.dim_date (date_day);
CREATE INDEX ix_foi_product ON analytics.fact_order_items (product_id);
CREATE INDEX ix_foi_seller ON analytics.fact_order_items (seller_id);
CREATE INDEX ix_foi_date ON analytics.fact_order_items (order_date_key);

COMMENT ON TABLE analytics.fact_order_items IS
'Grain: one row per item within an order (identical grain to raw.order_items). Use for product/category/seller revenue breakdowns. Do NOT join to fact_payments or fact_orders review columns at this grain -- aggregate first.';
