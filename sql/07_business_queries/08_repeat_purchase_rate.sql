-- Business question: ¿Qué porcentaje de clientes repite compra?
-- Uses customer_unique_id (real person), NOT customer_id -- see
-- data_quality_notes.md #1. Using customer_id here would silently
-- return 0%, since every customer_id by construction appears in
-- exactly one order.
-- Real result: 3.12% (2,997 of 96,096 real customers).
SELECT
    COUNT(*) AS total_customers,
    COUNT(*) FILTER (WHERE is_repeat_customer) AS repeat_customers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_repeat_customer) / COUNT(*), 2) AS repeat_rate_pct
FROM analytics.dim_customer;

-- Value comparison: repeat vs. one-time customers (see recommendations.md #4).
SELECT
    dc.is_repeat_customer,
    COUNT(*) AS customers,
    ROUND(AVG(cr.total_revenue), 2) AS avg_revenue_per_customer,
    ROUND(100.0 * SUM(cr.total_revenue) / SUM(SUM(cr.total_revenue)) OVER (), 2) AS pct_of_total_revenue
FROM analytics.dim_customer dc
JOIN (
    SELECT customer_unique_id, SUM(items_revenue) AS total_revenue
    FROM analytics.fact_orders
    WHERE order_status NOT IN ('canceled', 'unavailable')
    GROUP BY customer_unique_id
) cr USING (customer_unique_id)
GROUP BY dc.is_repeat_customer;
