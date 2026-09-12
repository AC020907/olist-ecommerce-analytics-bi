-- ============================================================================
-- 06_vw_payment_method_summary.sql
-- Payment method mix -- volume, value share and average installments.
-- Built from fact_payments alone (correct grain for this question; never
-- joined to fact_order_items here).
-- ============================================================================

CREATE OR REPLACE VIEW reporting.vw_payment_method_summary AS
SELECT
    payment_type,
    COUNT(*)                                                      AS payment_count,
    ROUND(SUM(payment_value), 2)                                    AS total_value,
    ROUND(100.0 * SUM(payment_value) / SUM(SUM(payment_value)) OVER (), 2) AS pct_of_total_value,
    ROUND(AVG(payment_installments), 2)                               AS avg_installments
FROM analytics.fact_payments
GROUP BY payment_type
ORDER BY total_value DESC;

COMMENT ON VIEW reporting.vw_payment_method_summary IS
'Payment method mix: count, total value, % of total value and average installments per payment_type.';
