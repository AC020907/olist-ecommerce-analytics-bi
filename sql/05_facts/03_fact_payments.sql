-- ============================================================================
-- 03_fact_payments.sql
-- Grain: ONE ROW PER (order_id, payment_sequential) -- identical to
-- raw.order_payments. Use this fact ONLY for payment-method /
-- installments analysis. For "how much revenue did this order generate",
-- use fact_orders.items_revenue or fact_orders.payments_total, not a
-- join between this table and fact_order_items.
-- ============================================================================

DROP TABLE IF EXISTS analytics.fact_payments;

CREATE TABLE analytics.fact_payments AS
SELECT
    op.order_id,
    op.payment_sequential,
    c.customer_unique_id,
    o.order_purchase_timestamp::date AS order_date_key,
    o.order_status,
    op.payment_type,
    op.payment_installments,
    op.payment_value
FROM raw.order_payments op
JOIN raw.orders o     ON o.order_id = op.order_id
JOIN raw.customers c  ON c.customer_id = o.customer_id;

ALTER TABLE analytics.fact_payments ADD PRIMARY KEY (order_id, payment_sequential);
ALTER TABLE analytics.fact_payments
    ADD CONSTRAINT fk_fp_customer FOREIGN KEY (customer_unique_id) REFERENCES analytics.dim_customer (customer_unique_id),
    ADD CONSTRAINT fk_fp_date     FOREIGN KEY (order_date_key) REFERENCES analytics.dim_date (date_day);
CREATE INDEX ix_fp_date ON analytics.fact_payments (order_date_key);
CREATE INDEX ix_fp_type ON analytics.fact_payments (payment_type);

COMMENT ON TABLE analytics.fact_payments IS
'Grain: one row per payment transaction within an order. Use for payment-type/installments analysis only -- never join row-level to fact_order_items (fan-out risk, see data_quality_notes.md #2).';
