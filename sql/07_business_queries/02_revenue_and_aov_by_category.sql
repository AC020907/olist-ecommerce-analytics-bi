-- Business question: ¿Qué categorías generan más revenue? ¿Cuáles
-- tienen mayor ticket promedio (avg_item_price)?
-- Real result: health_beauty leads total revenue (R$1,255,695.13), but
-- the highest average ticket is computers (R$1,098.34 per item,
-- R$222,963.13 total revenue) -- a low-volume, high-ticket category,
-- confirming that revenue leadership and ticket size are two different
-- rankings here, not the same category winning both.
SELECT category_name_en, items_sold, orders, revenue, avg_item_price, avg_review_score
FROM reporting.vw_category_performance
ORDER BY revenue DESC
LIMIT 20;

-- Same data, ranked by ticket size instead of total revenue.
SELECT category_name_en, revenue, avg_item_price
FROM reporting.vw_category_performance
ORDER BY avg_item_price DESC
LIMIT 10;
