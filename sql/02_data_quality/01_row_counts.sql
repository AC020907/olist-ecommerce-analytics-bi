-- ============================================================================
-- 01_row_counts.sql
-- Sanity check: row counts per raw table, compared against the source CSVs
-- profiled in Phase 1. If these don't match, the load in
-- scripts/load_raw_data.sql silently dropped or duplicated rows.
--
-- Expected (verified against the CSVs directly, Phase 1):
--   customers               99,441
--   products                32,951
--   sellers                  3,095
--   product_category_...       71
--   geolocation          1,000,163
--   orders                  99,441
--   order_items            112,650
--   order_payments         103,886
--   order_reviews           99,224
-- ============================================================================

SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM raw.customers
UNION ALL
SELECT 'products', COUNT(*) FROM raw.products
UNION ALL
SELECT 'sellers', COUNT(*) FROM raw.sellers
UNION ALL
SELECT 'product_category_name_translation', COUNT(*) FROM raw.product_category_name_translation
UNION ALL
SELECT 'geolocation', COUNT(*) FROM raw.geolocation
UNION ALL
SELECT 'orders', COUNT(*) FROM raw.orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM raw.order_items
UNION ALL
SELECT 'order_payments', COUNT(*) FROM raw.order_payments
UNION ALL
SELECT 'order_reviews', COUNT(*) FROM raw.order_reviews
ORDER BY table_name;
