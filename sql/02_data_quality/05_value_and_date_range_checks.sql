-- ============================================================================
-- 05_value_and_date_range_checks.sql
-- Logical / business-rule checks that CHECK constraints can't express
-- (e.g. "delivery date should never be before purchase date" spans two
-- columns and, in this dataset, is sometimes violated by the source
-- itself -- so it's a documented data quality finding, not a bug in
-- our schema).
-- ============================================================================

-- order_status distribution (drives which statuses count as "delivered"
-- for delivery-time KPIs in Phase 6/7).
SELECT order_status, COUNT(*) AS orders
FROM raw.orders
GROUP BY order_status
ORDER BY orders DESC;

-- Usable date range and the truncated-edges issue found in Phase 1.
SELECT
    MIN(order_purchase_timestamp) AS earliest_order,
    MAX(order_purchase_timestamp) AS latest_order
FROM raw.orders;

SELECT DATE_TRUNC('month', order_purchase_timestamp)::date AS order_month,
       COUNT(*) AS orders
FROM raw.orders
GROUP BY 1
ORDER BY 1;
-- Confirms: 2016 (329 orders total) and 2018-09/10 (20 orders total) are
-- truncated edges of the dataset, not real seasonality. Time-series
-- analysis (Phase 6 onward) filters to 2017-01 through 2018-08.

-- Logical date ordering violations. None of these are prevented by a
-- CHECK constraint because they compare two nullable columns whose
-- relationship depends on order_status.
SELECT
    COUNT(*) FILTER (WHERE order_delivered_customer_date < order_purchase_timestamp)
        AS delivered_before_purchase,
    COUNT(*) FILTER (WHERE order_approved_at < order_purchase_timestamp)
        AS approved_before_purchase,
    COUNT(*) FILTER (WHERE order_delivered_carrier_date < order_approved_at)
        AS shipped_before_approved,
    COUNT(*) FILTER (WHERE order_delivered_customer_date < order_delivered_carrier_date)
        AS delivered_before_shipped
FROM raw.orders;
-- Verified findings:
--   shipped_before_approved:   1,359 orders (avg gap 24.8h, max ~171 days
--                               -- mostly small end-of-day batch-approval
--                               artifacts, but a few large outliers)
--   delivered_before_shipped:     23 orders (up to 386h / ~16 days --
--                               logically impossible, a genuine source
--                               data error)
--   delivered_before_purchase:     0
--   approved_before_purchase:      0
-- Decision (Phase 4): delivery-time KPIs are computed only where
-- order_delivered_customer_date >= order_delivered_carrier_date, and the
-- 23 excluded rows are documented, not silently averaged in.

-- payment_installments = 0 (unusual for a non-voucher payment type).
SELECT payment_type, COUNT(*) AS rows_with_zero_installments
FROM raw.order_payments
WHERE payment_installments = 0
GROUP BY payment_type;
-- Verified: only 2 rows, both payment_type = 'credit_card'. Negligible
-- volume; documented, not "corrected" (we don't know the true value).

-- payment_value = 0 (a payment row with no monetary value).
SELECT payment_type, COUNT(*) AS rows_with_zero_value
FROM raw.order_payments
WHERE payment_value = 0
GROUP BY payment_type;
-- Verified: 3 'not_defined' + 6 'voucher' rows. Plausible for vouchers
-- combined with another payment row covering the full amount.

-- review_score distribution (context for the satisfaction KPIs).
SELECT review_score, COUNT(*) AS reviews
FROM raw.order_reviews
GROUP BY review_score
ORDER BY review_score;
