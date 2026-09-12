-- Business question: ¿Qué productos/categorías/vendedores combinan
-- alto revenue con bajo review score? (operational risk)
-- Real result: 639 of 3,053 active sellers (20.9%) are above the
-- median seller revenue (R$825) AND below the platform's average
-- review score (4.09) -- together representing 39.18% of seller-side
-- revenue. See recommendations.md #2.

WITH stats AS (
    SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY revenue) AS median_revenue
    FROM reporting.vw_seller_performance
)
SELECT sp.seller_id, sp.seller_state, sp.orders, sp.revenue,
       sp.late_delivery_rate_pct, sp.avg_review_score
FROM reporting.vw_seller_performance sp, stats s
WHERE sp.revenue > s.median_revenue
  AND sp.avg_review_score < 4.09
ORDER BY sp.revenue DESC;

-- Same lens applied to categories: any category above the median
-- category revenue with below-average review score.
WITH stats AS (
    SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY revenue) AS median_revenue
    FROM reporting.vw_category_performance
)
SELECT cp.category_name_en, cp.revenue, cp.avg_review_score
FROM reporting.vw_category_performance cp, stats s
WHERE cp.revenue > s.median_revenue
  AND cp.avg_review_score < 4.09
ORDER BY cp.revenue DESC;
