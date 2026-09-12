-- Business question: ¿Qué vendedores generan mayor volumen y revenue?
-- Real result: top seller (4869f7a5...) generated R$229,237.63 across
-- 1,131 orders. See recommendations.md #2: the top 20.9% of sellers by
-- this ranking, when also below-average on review score, account for
-- 39.18% of total seller-side revenue.
SELECT seller_id, seller_state, items_sold, orders, revenue,
       avg_delivery_days, late_delivery_rate_pct, avg_review_score
FROM reporting.vw_seller_performance
ORDER BY revenue DESC
LIMIT 20;
