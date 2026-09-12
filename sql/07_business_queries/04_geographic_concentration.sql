-- Business question: ¿Qué estados/ciudades concentran más ventas?
-- Real result: SP alone generates 38.27% of net revenue; the top 3
-- states (SP, RJ, MG) combine for well over half of total revenue --
-- see insights/business_insights.md #5.
SELECT region, state, orders, revenue, avg_delivery_days,
       late_delivery_rate_pct, avg_review_score,
       ROUND(100.0 * revenue / SUM(revenue) OVER (), 2) AS pct_of_total_revenue
FROM reporting.vw_customer_geography_performance
ORDER BY revenue DESC;

-- Top 10 cities (finer grain than state).
SELECT dg.city, dg.state, COUNT(*) AS orders, ROUND(SUM(fo.items_revenue), 2) AS revenue
FROM analytics.fact_orders fo
JOIN analytics.dim_customer dc ON dc.customer_unique_id = fo.customer_unique_id
JOIN analytics.dim_geography dg ON dg.zip_code_prefix = dc.zip_code_prefix
WHERE fo.order_status NOT IN ('canceled', 'unavailable')
GROUP BY dg.city, dg.state
ORDER BY revenue DESC
LIMIT 10;
