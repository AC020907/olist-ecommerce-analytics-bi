-- Business question: ¿Qué categorías tienen mejor/peor satisfacción?
-- Real result: pet_shop and stationery lead at 4.24. The absolute
-- lowest scores (security_and_services 2.50, pc_gamer 3.13) belong to
-- near-zero-revenue niche categories and are not business-relevant on
-- their own; among categories with substantial revenue, office_furniture
-- is the clear laggard at 3.62 on R$273,580.70 in revenue -- see
-- insights/business_insights.md #3.
SELECT category_name_en, revenue, avg_review_score
FROM reporting.vw_category_performance
ORDER BY avg_review_score DESC
LIMIT 10;

SELECT category_name_en, revenue, avg_review_score
FROM reporting.vw_category_performance
ORDER BY avg_review_score ASC
LIMIT 10;
