-- ============================================================================
-- 03_staging_orders.sql
-- Adds delivery-quality flags on top of raw.orders instead of computing
-- them inline in every downstream query. Encodes the decisions from
-- docs/data_quality_notes.md findings #3 and #10:
--   - delivery KPIs only make sense for delivered orders.
--   - 23 orders have order_delivered_customer_date < order_delivered_carrier_date,
--     which is logically impossible -- excluded from delivery_days/is_late
--     rather than silently producing a negative delivery time.
-- ============================================================================

CREATE OR REPLACE VIEW staging.orders AS
SELECT
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,

    (o.order_status = 'delivered')                             AS is_delivered,

    -- A delivery record is "valid" only if both dates exist AND the
    -- customer delivery isn't chronologically before the carrier handoff.
    (
        o.order_delivered_customer_date IS NOT NULL
        AND o.order_delivered_carrier_date IS NOT NULL
        AND o.order_delivered_customer_date >= o.order_delivered_carrier_date
    )                                                            AS has_valid_delivery_dates,

    -- NULL (not zero, not negative) when the order isn't delivered or the
    -- dates are invalid -- makes AVG()/aggregations correct by construction.
    CASE
        WHEN o.order_status = 'delivered'
             AND o.order_delivered_customer_date IS NOT NULL
             AND o.order_delivered_carrier_date IS NOT NULL
             AND o.order_delivered_customer_date >= o.order_delivered_carrier_date
        THEN ROUND(
                 EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp)) / 86400.0,
                 1
             )
        ELSE NULL
    END                                                          AS delivery_days,

    CASE
        WHEN o.order_status = 'delivered'
             AND o.order_delivered_customer_date IS NOT NULL
             AND o.order_delivered_carrier_date IS NOT NULL
             AND o.order_delivered_customer_date >= o.order_delivered_carrier_date
        THEN (o.order_delivered_customer_date > o.order_estimated_delivery_date)
        ELSE NULL
    END                                                          AS is_late

FROM raw.orders o;

COMMENT ON VIEW staging.orders IS
'raw.orders plus is_delivered / has_valid_delivery_dates / delivery_days / is_late. delivery_days and is_late are NULL for non-delivered orders and for the 23 orders with impossible date ordering (see data_quality_notes.md #10).';
